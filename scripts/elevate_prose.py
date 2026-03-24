"""
elevate_prose.py

Reads prose_quality_inventory.json and calls Claude (claude-opus-4-6) to rewrite
each flagged h2 section with Pearson-textbook-level pedagogy.

Output: scripts/data/prose_rewrites.json

Run:
  python scripts/elevate_prose.py --domain PMET          # one domain
  python scripts/elevate_prose.py --domain PMET --resume  # resume after interruption
  python scripts/elevate_prose.py --all                   # all domains
"""

import json, pathlib, argparse, time, sys, os, re, threading
import concurrent.futures
import anthropic

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
INVENTORY_FILE = DATA_DIR / "prose_quality_inventory.json"
OUTPUT_FILE = DATA_DIR / "prose_rewrites.json"
ANCHORS_FILE = DATA_DIR / "anchors_parsed.json"

DOMAIN_NAMES = {
    "PMET": "Psychometrics & Research Methods",
    "LDEV": "Lifespan & Developmental Stages",
    "CPAT": "Clinical Psychopathology (DSM-5)",
    "PTHE": "Psychotherapy Models, Interventions & Prevention",
    "SOCU": "Social & Cultural Psychology",
    "WDEV": "Workforce Development & Leadership",
    "BPSY": "Biopsychology",
    "CASS": "Clinical Assessment & Interpretation",
    "PETH": "Psychopharmacology & Ethics",
}

# Same patterns as scanner — used for validation
BARE_DEF_PATTERNS = [
    re.compile(r"^.{1,80}\bis\s+the\s+process\s+(?:by\s+which|of|through\s+which)", re.I | re.S),
    re.compile(r"^.{1,80}\boccurs?\s+when\s+", re.I | re.S),
    re.compile(r"^.{1,80}\brefers?\s+to\s+", re.I | re.S),
    re.compile(r"^.{1,80}\bis\s+defined\s+as\s+", re.I | re.S),
    re.compile(r"^.{1,80}\binvolves?\s+(?:the|a|an)\s+", re.I | re.S),
    re.compile(r"^.{1,80}\bis\s+(?:a|an)\s+(?:process|procedure|technique|method|mechanism|phenomenon|principle|concept|theory|approach|strategy|type|form|pattern|behavior|response|stage|phase|measure|term)\b", re.I | re.S),
]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior textbook editor rewriting sections of an EPPP (Examination for \
Professional Practice in Psychology) study textbook. Your goal is to transform \
dictionary-like prose into Pearson-textbook-level pedagogy — warm, narrative, \
clinically grounded, and memorable.

PEDAGOGICAL VOICE:
- Open with WHY the concept matters, not WHAT it is. Provide a contextual hook — \
  a clinical scenario, a vivid everyday example, a surprising fact — before any \
  formal definition.
- Definitions should emerge from narrative, never dropped bare. Instead of \
  "Punishment is the process by which...", lead with a concrete scenario that \
  illustrates the concept, then introduce the term.
- Use active voice. Ground concepts in clinical examples and everyday scenarios.
- Every key concept earns at least one concrete scenario (clinical vignette, \
  classroom situation, everyday life) that makes it tangible and memorable.
- Bridge naturally from the preceding section — acknowledge what was just covered \
  and set up why this new topic follows.
- Build conceptual understanding before introducing technical terminology.
- Maintain a warm, authoritative tone — like a brilliant mentor explaining concepts \
  to a motivated graduate student.

STRUCTURAL PRESERVATION (NON-NEGOTIABLE — violations cause hard failure):
1. Preserve ALL heading tags (h2, h3, h4) with their EXACT original text. \
   Do not rename, reorder, add, or remove any heading.
2. Preserve ALL <div class="definition-box"> containers. Keep the opening and \
   closing div tags. Keep every <strong>Term:</strong> pattern VERBATIM inside \
   them. You may enrich the explanatory <p> text within definition-boxes.
3. Preserve ALL <div class="example-box"> and <div class="clinical-note"> \
   containers with their h4 headings. You may enrich content inside these boxes.
4. Preserve ALL <table> elements and their contents exactly as-is.
5. CRITICAL: Preserve ALL <span class="key-term">Term</span> spans with the EXACT \
   same term text. Every key-term span in the original MUST appear in your output. \
   When you move or rewrite a sentence that contains a key-term span, carry the span \
   with it. You may add NEW key-term spans, but never drop or rename existing ones.
6. Preserve ALL <!-- anchor:... --> and <!-- /anchor:... --> comment markers \
   exactly as-is. Do not move content into or out of anchor blocks.
7. Preserve ALL <div class="citation"> blocks exactly as-is.
8. Every <p> tag MUST contain at least 120 characters of text. This is a hard \
   system constraint for downstream passage extraction.
9. If a definition-box is currently the first element after a heading, INSERT \
   narrative paragraphs BEFORE it — do NOT delete the definition-box.
10. Maintain the general ordering of structural elements (headings, boxes, tables, \
    anchors, citations). You may reorder paragraphs and add new paragraphs.
11. Preserve the original indentation style (typically 8 spaces for content elements).
12. NEVER add new <h3>, <h4>, <div class="example-box">, <div class="clinical-note">, \
    or <div class="definition-box"> elements that do not exist in the original. You may \
    enrich content INSIDE existing boxes but must not create new ones.

LENGTH GUIDANCE:
- For short sections (under ~2000 chars): enriching with hooks and examples will \
  naturally expand the text. Aim for 200-350% of the original length.
- For longer sections (over ~5000 chars): focus on improving the opening and \
  transitions. Keep expansion moderate — aim for 120-180% of original.
- Never pad with filler. Every added sentence should teach something or ground a \
  concept in a memorable example.

OUTPUT FORMAT:
- Return ONLY the rewritten section HTML.
- Start with the <h2> heading tag and end with the last content element.
- Do NOT include <section class="content-section"> wrapper tags.
- Do NOT wrap output in markdown code fences.
- Do NOT include any commentary before or after the HTML."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    """Resolve API key: env var > .env file."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for p in [pathlib.Path(".env"), pathlib.Path.home() / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError(
        "No API key found. Set ANTHROPIC_API_KEY or create a .env file."
    )


def strip_tags(html: str) -> str:
    """Remove all HTML tags."""
    return re.sub(r"<[^>]+>", "", html).strip()


def load_anchors() -> dict[str, list[dict]]:
    """Load anchors_parsed.json grouped by domain code. Returns empty dict if missing."""
    if not ANCHORS_FILE.exists():
        return {}
    data = json.loads(ANCHORS_FILE.read_text(encoding="utf-8"))
    by_domain: dict[str, list[dict]] = {}
    for anchor in data:
        code = anchor.get("domain_code", "")
        by_domain.setdefault(code, []).append(anchor)
    return by_domain


def find_relevant_anchors(
    section_html: str, domain_anchors: list[dict], max_anchors: int = 5
) -> list[str]:
    """Find anchor points referenced in the section HTML by comment markers."""
    # Extract anchor IDs from <!-- anchor:XXX --> comments
    anchor_ids = set(re.findall(r"<!--\s*anchor:(\S+)", section_html))
    if not anchor_ids or not domain_anchors:
        return []

    relevant = []
    for anchor in domain_anchors:
        aid = str(anchor.get("anchor_id", anchor.get("id", "")))
        if aid in anchor_ids:
            text = anchor.get("question_text", anchor.get("text", ""))
            if text:
                relevant.append(text[:300])
    return relevant[:max_anchors]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_rewrite(original_html: str, rewritten_html: str, lenient: bool = False) -> list[str]:
    """Validate structural preservation. Returns list of error strings (empty = pass)."""
    errors = []

    # 1. Heading preservation — exact text match for all h2/h3/h4
    orig_headings = re.findall(
        r"<(h[2-4])[^>]*>(.*?)</\1>", original_html, re.DOTALL | re.I
    )
    new_headings = re.findall(
        r"<(h[2-4])[^>]*>(.*?)</\1>", rewritten_html, re.DOTALL | re.I
    )
    orig_ht = [(t.lower(), strip_tags(txt)) for t, txt in orig_headings]
    new_ht = [(t.lower(), strip_tags(txt)) for t, txt in new_headings]
    if orig_ht != new_ht:
        errors.append(f"Heading mismatch: expected {len(orig_ht)} headings {orig_ht}, got {len(new_ht)} {new_ht}")

    # 2. definition-box count
    orig_n = len(re.findall(r'class="definition-box"', original_html))
    new_n = len(re.findall(r'class="definition-box"', rewritten_html))
    if orig_n != new_n:
        errors.append(f"definition-box count: {orig_n} → {new_n}")

    # 3. example-box count
    orig_n = len(re.findall(r'class="example-box"', original_html))
    new_n = len(re.findall(r'class="example-box"', rewritten_html))
    if orig_n != new_n:
        errors.append(f"example-box count: {orig_n} → {new_n}")

    # 4. clinical-note count
    orig_n = len(re.findall(r'class="clinical-note"', original_html))
    new_n = len(re.findall(r'class="clinical-note"', rewritten_html))
    if orig_n != new_n:
        errors.append(f"clinical-note count: {orig_n} → {new_n}")

    # 5. <strong>Term:</strong> patterns in definition-boxes
    orig_strongs = re.findall(r"<strong>([^<]+)</strong>", original_html)
    new_strongs = re.findall(r"<strong>([^<]+)</strong>", rewritten_html)
    for s in orig_strongs:
        if s not in new_strongs:
            errors.append(f"Missing <strong> pattern: {s!r}")

    # 6. key-term spans — fail if >30% missing (lenient: 50%)
    kt_threshold = 0.5 if lenient else 0.3
    orig_kt = set(re.findall(r'<span class="key-term">(.*?)</span>', original_html, re.DOTALL))
    new_kt = set(re.findall(r'<span class="key-term">(.*?)</span>', rewritten_html, re.DOTALL))
    missing_kt = orig_kt - new_kt
    if orig_kt and len(missing_kt) > max(1, len(orig_kt) * kt_threshold):
        errors.append(f"Missing key-term spans ({len(missing_kt)}/{len(orig_kt)}): {missing_kt}")

    # 7. table count
    orig_n = len(re.findall(r"<table", original_html, re.I))
    new_n = len(re.findall(r"<table", rewritten_html, re.I))
    if orig_n != new_n:
        errors.append(f"table count: {orig_n} → {new_n}")

    # 8. Paragraph min-length (fail below 100, warn-only 100-119)
    #    Exempt formula paragraphs (math symbols, sub/sup tags) and list-header paragraphs
    new_paras = re.findall(r"<p[^>]*>(.*?)</p>", rewritten_html, re.DOTALL)
    for para in new_paras:
        plain = strip_tags(para)
        if 0 < len(plain) < 100:
            # Exempt formula paragraphs (contain math notation or sub/sup tags)
            if re.search(r'<su[bp]>|[=×÷±²³σμρ∑]', para):
                continue
            # Exempt short bold-only labels like "<strong>Where:</strong>"
            if re.search(r'^\s*<strong>[^<]{1,30}</strong>\s*$', para):
                continue
            # Exempt list-header paragraphs (end with ":" and < 80 chars)
            if len(plain) < 80 and plain.rstrip().endswith(':'):
                continue
            # Exempt citation paragraphs (contain author-year patterns)
            if re.search(r'\(\d{4}\)', plain):
                continue
            # Exempt paragraphs preserved verbatim from the original
            if plain in strip_tags(original_html):
                continue
            errors.append(f"Paragraph too short ({len(plain)} chars): {plain[:60]}...")

    # 9. Output length ratio — sliding scale (short sections expand more)
    orig_len = len(original_html)
    new_len = len(rewritten_html)
    if orig_len > 0:
        ratio = new_len / orig_len
        # Tiny sections (<1K) need room — allow up to 800%
        # Short sections (<3K) get narrative + examples → allow up to 500%
        # Medium sections (3-8K) → up to 250%
        # Large sections (>8K) → up to 200%
        # Lenient mode: 1.5x all limits
        if orig_len < 1000:
            max_ratio = 8.0
        elif orig_len < 3000:
            max_ratio = 5.0
        elif orig_len < 8000:
            max_ratio = 2.5
        else:
            max_ratio = 2.0
        if lenient:
            max_ratio *= 1.5
        if ratio < 0.8:
            errors.append(f"Output too short: {ratio:.0%} of original ({new_len} vs {orig_len} chars)")
        if ratio > max_ratio:
            errors.append(f"Output too long: {ratio:.0%} of original ({new_len} vs {orig_len} chars, max {max_ratio:.0%})")

    # 10. No bare-definition opener in rewrite
    first_p = re.search(
        r"</h2>\s*(?:<!--.*?-->\s*)*<p[^>]*>(.*?)</p>",
        rewritten_html, re.DOTALL | re.I,
    )
    if first_p:
        plain = strip_tags(first_p.group(1))
        for pat in BARE_DEF_PATTERNS:
            if pat.match(plain):
                errors.append(f"Still has bare-definition opener: {plain[:80]}...")
                break

    # 11. citation preservation
    orig_n = len(re.findall(r'class="citation"', original_html))
    new_n = len(re.findall(r'class="citation"', rewritten_html))
    if orig_n != new_n:
        errors.append(f"citation count: {orig_n} → {new_n}")

    # 12. anchor comment preservation
    orig_anchors = re.findall(r"<!--\s*/?anchor:\S+.*?-->", original_html)
    new_anchors = re.findall(r"<!--\s*/?anchor:\S+.*?-->", rewritten_html)
    if len(orig_anchors) != len(new_anchors):
        errors.append(f"anchor comment count: {len(orig_anchors)} → {len(new_anchors)}")

    # 13. Basic HTML well-formedness — check tag balance for key tags
    for tag in ["div", "table", "ul", "ol"]:
        orig_opens = len(re.findall(rf"<{tag}[\s>]", original_html, re.I))
        orig_closes = len(re.findall(rf"</{tag}>", original_html, re.I))
        new_opens = len(re.findall(rf"<{tag}[\s>]", rewritten_html, re.I))
        new_closes = len(re.findall(rf"</{tag}>", rewritten_html, re.I))
        if new_opens != new_closes:
            errors.append(f"Unbalanced <{tag}>: {new_opens} opens vs {new_closes} closes")

    return errors


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_user_prompt(item: dict, anchor_texts: list[str] | None = None) -> str:
    """Build the user prompt for a single section rewrite."""
    parts = [
        f"Domain: {item['domain_name']}",
        f"Chapter: {item['chapter_title']}",
        "",
    ]

    if item.get("prev_heading_text"):
        parts.append(f"PRECEDING SECTION HEADING: {item['prev_heading_text']}")
    if item.get("prev_last_paragraph"):
        # Truncate very long previous paragraphs
        prev = item["prev_last_paragraph"]
        if len(prev) > 600:
            prev = prev[:600] + "..."
        parts.append(f"LAST PARAGRAPH OF PRECEDING SECTION:\n{prev}")
    parts.append("")

    if item.get("next_heading_text"):
        parts.append(f"NEXT SECTION HEADING: {item['next_heading_text']}")
        parts.append("")

    if anchor_texts:
        parts.append("RELEVANT EXAM ANCHOR POINTS (preserve factual accuracy):")
        for a in anchor_texts:
            parts.append(f"  - {a}")
        parts.append("")

    parts.append(f"FLAGGED PROBLEM: {item['problem_type']}")
    parts.append("")
    parts.append("SECTION TO REWRITE:")
    parts.append(item["section_html"])

    return "\n".join(parts)


def generate_rewrite(
    client: anthropic.Anthropic,
    item: dict,
    anchor_texts: list[str] | None = None,
    retries: int = 3,
    lenient: bool = False,
) -> str | None:
    """Generate a rewritten section. Returns HTML string or None on failure."""
    user_prompt = build_user_prompt(item, anchor_texts)

    # Estimate needed output tokens (generous: 2x input section length / 4 chars per token)
    section_chars = len(item["section_html"])
    max_tokens = max(4096, min(16384, int(section_chars * 2 / 3)))

    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = msg.content[0].text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                first_nl = text.index("\n")
                text = text[first_nl + 1:]
            if text.endswith("```"):
                text = text[:-3].rstrip()

            # Validate
            errors = validate_rewrite(item["section_html"], text, lenient=lenient)
            if errors:
                error_summary = "; ".join(errors[:3])
                raise ValueError(f"Validation failed: {error_summary}")

            return text

        except anthropic.RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s...")
            time.sleep(wait)
        except ValueError as e:
            print(f"    Validation error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"    API error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(3)

    return None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_existing(domain_code: str | None = None) -> dict[str, dict]:
    """Load already-generated rewrites keyed by file_path:heading_line.
    When domain_code is given, scan ALL matching files to pick up work from
    any prior sequential or parallel agent for that domain."""
    merged: dict[str, dict] = {}
    if domain_code:
        for f in DATA_DIR.glob(f"prose_rewrites*{domain_code}*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            for r in data:
                merged[f"{r['file_path']}:{r['heading_line']}"] = r
        # Also check base file (PMET pilot lives here)
        base = DATA_DIR / "prose_rewrites.json"
        if base.exists():
            data = json.loads(base.read_text(encoding="utf-8"))
            for r in data:
                if r.get("domain_code") == domain_code:
                    merged[f"{r['file_path']}:{r['heading_line']}"] = r
    elif OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        merged = {f"{r['file_path']}:{r['heading_line']}": r for r in data}
    return merged


def save_results(results: list[dict]):
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global OUTPUT_FILE

    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Elevate prose quality via Claude API")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Process all domains")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    parser.add_argument("--resume", action="store_true", help="Skip already-generated items")
    parser.add_argument("--workers", type=int, default=1, help="Parallel API workers (default 1)")
    parser.add_argument("--lenient", action="store_true",
                        help="Relaxed validation: 1.5x max_ratio, 50%% key-term miss allowed")
    args = parser.parse_args()

    # Per-domain output file for parallel safety
    # Workers > 1 get a _w suffix to avoid cross-process file corruption
    if args.domain:
        code = args.domain.upper()
        if args.workers > 1:
            OUTPUT_FILE = DATA_DIR / f"prose_rewrites_{code}_w.json"
        else:
            OUTPUT_FILE = DATA_DIR / f"prose_rewrites_{code}.json"

    if not INVENTORY_FILE.exists():
        print(f"ERROR: {INVENTORY_FILE} not found. Run scan_prose_quality.py first.")
        sys.exit(1)

    inventory = json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))

    if args.domain:
        if code not in DOMAIN_NAMES:
            print(f"ERROR: Unknown domain {code}")
            sys.exit(1)
        inventory = [item for item in inventory if item["domain_code"] == code]

    if not inventory:
        print("No items to process.")
        return

    # Resume support — scan all related files for the domain
    domain_code = code if args.domain else None
    existing = load_existing(domain_code) if args.resume else {}
    results = list(existing.values()) if args.resume else []

    todo = []
    for item in inventory:
        key = f"{item['file_path']}:{item['heading_line']}"
        if args.resume and key in existing:
            continue
        todo.append(item)

    if not todo:
        print("All items already generated (--resume). Nothing to do.")
        return

    print(f"Generating rewrites for {len(todo)} sections "
          f"({len(existing)} already done)...\n")

    # Load API + anchors
    api_key = load_api_key()
    client = anthropic.Anthropic(api_key=api_key)
    anchors_by_domain = load_anchors()

    succeeded = 0
    failed = 0
    lock = threading.Lock()

    def process_one(i: int, item: dict):
        nonlocal succeeded, failed
        key = f"{item['file_path']}:{item['heading_line']}"
        print(f"[{i}/{len(todo)}] {item['file_path']}:{item['heading_line']}")
        print(f"  h2: {item['heading_text']}")
        print(f"  problem: {item['problem_type']}")

        domain_anchors = anchors_by_domain.get(item["domain_code"], [])
        anchor_texts = find_relevant_anchors(item["section_html"], domain_anchors)

        rewrite = generate_rewrite(client, item, anchor_texts, lenient=args.lenient)

        if rewrite:
            record = {**item, "rewritten_html": rewrite}
            with lock:
                results.append(record)
                save_results(results)
                succeeded += 1
            plain_preview = strip_tags(rewrite)[:120]
            print(f"  \u2713 {plain_preview}...")
        else:
            with lock:
                failed += 1
            print(f"  \u2717 FAILED after retries")

    if args.workers > 1:
        print(f"Using {args.workers} parallel workers\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(process_one, i, item)
                       for i, item in enumerate(todo, 1)]
            concurrent.futures.wait(futures)
    else:
        for i, item in enumerate(todo, 1):
            process_one(i, item)

    total_done = len([r for r in results if "rewritten_html" in r])
    print(f"\nDone. {succeeded} succeeded, {failed} failed.")
    print(f"Total rewrites saved: {total_done}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
