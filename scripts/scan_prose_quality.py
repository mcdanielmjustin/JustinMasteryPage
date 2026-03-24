"""
scan_prose_quality.py

Scans all content HTML and identifies h2 sections with definitional writing
problems: bare-definition openers, definition-box-as-opener, passive-voice-heavy.

Output: scripts/data/prose_quality_inventory.json

Run:
  python scripts/scan_prose_quality.py           # scan all domains
  python scripts/scan_prose_quality.py --domain PMET  # scan one domain
"""

import json, pathlib, re, argparse, sys

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CONTENT_DIR = SCRIPTS_DIR.parent / "content"
OUTPUT = DATA_DIR / "prose_quality_inventory.json"

DOMAIN_MAP = {
    "domain1": "PMET", "domain2": "LDEV", "domain3": "CPAT",
    "domain4": "PTHE", "domain5": "SOCU", "domain6": "WDEV",
    "domain7": "BPSY", "domain8": "CASS", "domain9": "PETH",
}

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

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Bare-definition openers: "X is the process by which...", "X occurs when...", etc.
# .{1,80} allows a subject phrase (the term being defined) up to ~80 chars
BARE_DEF_PATTERNS = [
    re.compile(r"^.{1,80}\bis\s+the\s+process\s+(?:by\s+which|of|through\s+which)", re.I | re.S),
    re.compile(r"^.{1,80}\boccurs?\s+when\s+", re.I | re.S),
    re.compile(r"^.{1,80}\brefers?\s+to\s+", re.I | re.S),
    re.compile(r"^.{1,80}\bis\s+defined\s+as\s+", re.I | re.S),
    re.compile(r"^.{1,80}\binvolves?\s+(?:the|a|an)\s+", re.I | re.S),
    re.compile(r"^.{1,80}\bis\s+(?:a|an)\s+(?:process|procedure|technique|method|mechanism|phenomenon|principle|concept|theory|approach|strategy|type|form|pattern|behavior|response|stage|phase|measure|term)\b", re.I | re.S),
]

# Passive-voice pattern: "is/are/was/were [adverb?] past-participle"
PASSIVE_RE = re.compile(
    r"\b(?:is|are|was|were)\s+(?:\w+ly\s+)?"
    r"(?:\w+ed|given|shown|known|taken|made|found|set|kept|told|sent|"
    r"written|driven|chosen|spoken|broken|seen|done|held|run|put|left|"
    r"born|worn|drawn|grown|thrown|frozen|hidden|bitten|eaten|beaten)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_tags(html: str) -> str:
    """Remove all HTML tags from text."""
    return re.sub(r"<[^>]+>", "", html).strip()


def extract_chapter_title(html_text: str) -> str:
    """Extract <h1> text from HTML."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.DOTALL | re.IGNORECASE)
    return strip_tags(m.group(1)) if m else ""


def find_h2_positions(lines: list[str]) -> list[tuple[int, str]]:
    """Return list of (0-based line index, heading text) for all h2 tags."""
    results = []
    for i, line in enumerate(lines):
        m = re.search(r"<h2[^>]*>(.*?)</h2>", line, re.DOTALL | re.IGNORECASE)
        if m:
            results.append((i, strip_tags(m.group(1))))
    return results


def extract_paragraph_text(lines: list[str], start_idx: int, end_idx: int) -> str:
    """Extract full HTML of a <p> tag starting at start_idx (may span lines)."""
    result = []
    for i in range(start_idx, min(end_idx, len(lines))):
        result.append(lines[i])
        if "</p>" in lines[i]:
            break
    return "".join(result)


def find_section_content_end(lines: list[str], h2_idx: int, next_h2_idx: int | None) -> int:
    """Find the exclusive end index of h2 section content.

    Ends at </section> or next h2 (whichever first), trimming trailing
    blank lines and <section> open tags.
    """
    search_end = next_h2_idx if next_h2_idx is not None else len(lines)

    # Look for </section> between h2 and next boundary
    for i in range(h2_idx + 1, search_end):
        if lines[i].strip() == "</section>":
            return i  # exclusive — does not include </section>

    # No </section> found — trim trailing blanks / <section> tags from end
    end = search_end
    while end > h2_idx + 1:
        stripped = lines[end - 1].strip()
        if not stripped or stripped.startswith("<section"):
            end -= 1
        else:
            break
    return end


def find_last_paragraph_text(lines: list[str], start_idx: int, end_idx: int) -> str | None:
    """Return plain text of the last <p> in the given line range."""
    last_p = None
    i = start_idx
    while i < end_idx:
        if re.search(r"<p[\s>]", lines[i], re.IGNORECASE):
            para = extract_paragraph_text(lines, i, end_idx)
            plain = strip_tags(para)
            if plain:
                last_p = plain
        i += 1
    return last_p


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_problem(lines: list[str], after_h2_idx: int, section_end_idx: int) -> str | None:
    """Detect prose quality problems in the first content element after h2.

    Returns problem type string or None.
    """
    for i in range(after_h2_idx, section_end_idx):
        stripped = lines[i].strip()

        # Skip blank lines and HTML comments
        if not stripped or stripped.startswith("<!--"):
            continue

        # definition-box as first content element
        if 'class="definition-box"' in stripped:
            return "definition-box-as-opener"

        # h3/h4 — section goes directly to sub-headings (separate issue)
        if re.match(r"<h[34]", stripped, re.IGNORECASE):
            return None

        # <p> tag — check its text
        if re.search(r"<p[\s>]", stripped, re.IGNORECASE):
            para_html = extract_paragraph_text(lines, i, section_end_idx)
            plain = strip_tags(para_html)

            # Check bare-definition patterns
            if any(pat.match(plain) for pat in BARE_DEF_PATTERNS):
                return "bare-definition-opener"

            # Check passive-voice density (2+ in first ~500 chars)
            if len(PASSIVE_RE.findall(plain[:500])) >= 2:
                return "passive-voice-heavy"

            return None  # first paragraph exists and is fine

        # Any other content element (ul, ol, table, non-definition div)
        if re.match(r"<(?:ul|ol|table|div|blockquote)", stripped, re.IGNORECASE):
            return None

    return None


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_file(html_file: pathlib.Path, domain_code: str) -> list[dict]:
    """Scan a single HTML file for prose quality issues at the h2 level."""
    text = html_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    chapter_title = extract_chapter_title(text)

    h2s = find_h2_positions(lines)
    if not h2s:
        return []

    results = []

    for idx, (h2_idx, h2_text) in enumerate(h2s):
        next_h2_idx = h2s[idx + 1][0] if idx + 1 < len(h2s) else None
        content_end = find_section_content_end(lines, h2_idx, next_h2_idx)

        problem = detect_problem(lines, h2_idx + 1, content_end)
        if not problem:
            continue

        section_html = "".join(lines[h2_idx:content_end])

        # Previous section context
        prev_heading = h2s[idx - 1][1] if idx > 0 else None
        prev_start = h2s[idx - 1][0] if idx > 0 else 0
        prev_last_p = find_last_paragraph_text(lines, prev_start, h2_idx) if idx > 0 else None

        # Next heading
        next_heading = h2s[idx + 1][1] if idx + 1 < len(h2s) else None

        results.append({
            "domain_code": domain_code,
            "domain_name": DOMAIN_NAMES.get(domain_code, domain_code),
            "chapter_file": html_file.name,
            "chapter_title": chapter_title,
            "heading_text": h2_text,
            "heading_line": h2_idx + 1,           # 1-based for display
            "section_end_line": content_end,       # 0-based exclusive (internal)
            "problem_type": problem,
            "section_html": section_html,
            "prev_heading_text": prev_heading,
            "prev_last_paragraph": prev_last_p,
            "next_heading_text": next_heading,
            "file_path": str(html_file.relative_to(CONTENT_DIR.parent)),
        })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Scan prose quality in content HTML")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Scan all domains (default)")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    args = parser.parse_args()

    # Default to --all
    if not args.all and not args.domain:
        args.all = True

    inventory = []

    for domain_dir in sorted(CONTENT_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name not in DOMAIN_MAP:
            continue
        domain_code = DOMAIN_MAP[domain_dir.name]

        if args.domain and domain_code != args.domain.upper():
            continue

        for html_file in sorted(domain_dir.glob("*.html")):
            if html_file.name == "index.html":
                continue
            results = scan_file(html_file, domain_code)
            inventory.extend(results)

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Report
    print(f"Found {len(inventory)} sections with prose quality issues:\n")

    by_domain: dict[str, int] = {}
    by_problem: dict[str, int] = {}
    for item in inventory:
        by_domain[item["domain_code"]] = by_domain.get(item["domain_code"], 0) + 1
        by_problem[item["problem_type"]] = by_problem.get(item["problem_type"], 0) + 1

    print("By domain:")
    for code in sorted(by_domain):
        print(f"  {code}: {by_domain[code]}")

    print("\nBy problem type:")
    for ptype in sorted(by_problem):
        print(f"  {ptype}: {by_problem[ptype]}")

    print(f"\nDetails:")
    for i, item in enumerate(inventory, 1):
        print(f"  {i:3d}. [{item['problem_type']:<25s}] "
              f"{item['file_path']}:{item['heading_line']}  "
              f"\u201c{item['heading_text']}\u201d")

    print(f"\nInventory saved to {OUTPUT}")


if __name__ == "__main__":
    main()
