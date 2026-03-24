"""
generate_anchor_content.py  (Phase 3 — REVISED)

Generate textbook content for partial/missing anchors.
Uses Anthropic Message Batches API (50% discount).
Batches anchors per API call per chapter for efficiency.
Includes validation pass: comment markers, word count, no verbatim text, CSS classes.

Output: scripts/data/anchor_content_generated.json

Run:
  python scripts/generate_anchor_content.py --all
  python scripts/generate_anchor_content.py --domain PMET
  python scripts/generate_anchor_content.py --resume
  python scripts/generate_anchor_content.py --targets data/direct_gap_targets.json --direct
"""

import json, pathlib, re, sys, argparse, time, os, math
import anthropic

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CONTENT_DIR = SCRIPTS_DIR.parent / "content"
AUDIT_FILE = DATA_DIR / "coverage_audit.json"
OUTPUT_FILE = DATA_DIR / "anchor_content_generated.json"
BATCH_STATE_FILE = DATA_DIR / "generate_batch_state.json"

ANCHORS_PER_CALL = 4  # batch 3-5 anchors per API call

SYSTEM_PROMPT = """\
You are enriching EPPP (Examination for Professional Practice in Psychology) study \
material by writing original textbook content.

CRITICAL IP RULE: The anchor point summaries provided are PROPRIETARY exam content \
and must NEVER be quoted verbatim. Write original textbook content that TEACHES the \
same concept using different words, examples, and framing. Do NOT copy phrases longer \
than 4 consecutive words from any anchor summary.

You will receive anchor points that need enrichment in a specific chapter context. \
For each anchor, generate HTML content to be injected into the chapter.

For "missing" anchors — write a full content package:
- A passage (150-300 words) explaining the concept in textbook voice
- Optionally ONE example-box or clinical-note (not both)
- Optionally a comparison table if the concept has natural contrasts

For "partial" anchors — write a targeted expansion:
- A single paragraph (60-150 words) adding the specific missing depth/detail
- Do NOT repeat what the chapter already covers — only add what is missing

ALLOWED CSS CLASSES (use ONLY these):
- <span class="key-term">term</span> for key vocabulary
- <div class="definition-box"><h4>Title</h4><p>content</p></div> for definitions
- <div class="example-box"><h4>Example</h4><p>content</p></div> for examples
- <div class="clinical-note"><h4>Clinical Note</h4><p>content</p></div> for applications
- Standard <table> with <thead>/<tbody> for comparison tables

Wrap each anchor's content with comment markers:
<!-- anchor:ANCHOR_ID coverage:COVERAGE_TYPE -->
<p>Content here...</p>
<!-- /anchor:ANCHOR_ID -->

RULES:
- 8-space indentation for all HTML
- Authoritative, concise textbook voice
- No filler phrases ("It is important to note", "In summary", "As mentioned")
- Match existing chapter tone and depth

Respond with ONLY valid JSON:
{
    "content": [
        {
            "anchor_id": "020",
            "generated_html": "<!-- anchor:020 coverage:missing -->\\n        <p>Content...</p>\\n        <!-- /anchor:020 -->"
        }
    ]
}"""

# Variant system prompt for --targets mode: Claude must also determine inject_after heading
SYSTEM_PROMPT_WITH_INJECT = SYSTEM_PROMPT.rsplit("Respond with ONLY valid JSON:", 1)[0] + """\
ADDITIONAL RULE — inject_after:
For each anchor, also determine the best existing heading (h2 or h3) in the
chapter context after which this content should be injected. Return the heading
text exactly as it appears in the chapter (e.g. "### Higher-Order Conditioning").
Choose the heading whose section is most topically relevant to the anchor concept.

Respond with ONLY valid JSON:
{
    "content": [
        {
            "anchor_id": "020",
            "inject_after": "### Higher-Order Conditioning",
            "generated_html": "<!-- anchor:020 coverage:partial -->\\n        <p>Content...</p>\\n        <!-- /anchor:020 -->"
        }
    ]
}"""

ALLOWED_CSS_CLASSES = {'key-term', 'definition-box', 'example-box', 'clinical-note',
                       'key-concepts', 'citation'}


def load_api_key():
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']
    for p in [pathlib.Path('.env'), pathlib.Path.home() / '.env']:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('ANTHROPIC_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or create a .env file.")


def extract_chapter_context(html_path, max_chars=30000):
    """Extract chapter text for context (shorter than audit — just enough for tone)."""
    html = html_path.read_text(encoding="utf-8")
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... truncated ...]"
    return text


def build_user_prompt(chapter_context, anchors_batch):
    """Build user prompt for generating content for a batch of anchors."""
    anchor_list = "\n\n".join(
        f"ANCHOR [{a['anchor_id']}] (coverage: {a['coverage']})\n"
        f"Concept: {a['content']}\n"
        f"Inject after heading: {a.get('inject_after', 'nearest relevant heading')}"
        for a in anchors_batch
    )
    return (
        f"CHAPTER CONTEXT (for tone and style matching):\n{chapter_context}\n\n"
        f"---\n\n"
        f"Generate enrichment content for these {len(anchors_batch)} anchor points:\n\n"
        f"{anchor_list}"
    )


def poll_and_collect(client, batch_id):
    """Poll batch until complete, return raw results."""
    print("Polling for batch completion...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
        print(f"  {batch.processing_status} | "
              f"done={counts.succeeded} processing={counts.processing} "
              f"errored={counts.errored} / {total}")
        if batch.processing_status == "ended":
            break
        time.sleep(30)

    results = {}
    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if m:
                    data = json.loads(m.group(1))
                else:
                    print(f"  WARNING: Could not parse JSON for {result.custom_id}")
                    continue

            for item in data.get("content", []):
                results[f"{result.custom_id}:{item['anchor_id']}"] = item
        else:
            print(f"  ERROR: {result.custom_id} — {result.result.type}")

    return results


def direct_generate(client, by_chapter, anchors_per_call=ANCHORS_PER_CALL,
                    system_prompt=None):
    """Send individual API requests instead of batch (fallback when batch API is down)."""
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT
    raw_results = {}
    anchors_index = {}
    total_chapters = len(by_chapter)
    req_num = 0

    for ch_idx, (chapter_file, chapter_anchors) in enumerate(sorted(by_chapter.items()), 1):
        html_path = CONTENT_DIR / chapter_file
        if not html_path.exists():
            print(f"  WARNING: {html_path} not found, skipping")
            continue

        chapter_context = extract_chapter_context(html_path)
        n_batches = math.ceil(len(chapter_anchors) / anchors_per_call)

        for batch_idx in range(n_batches):
            start = batch_idx * anchors_per_call
            end = start + anchors_per_call
            anchors_batch = chapter_anchors[start:end]
            custom_id = (chapter_file.replace("/", "_").replace(".html", "")
                         + f"_b{batch_idx}")
            req_num += 1

            for a in anchors_batch:
                anchors_index[f"{custom_id}:{a['anchor_id']}"] = {
                    **a, "custom_id": custom_id,
                }

            aids = ",".join(a["anchor_id"] for a in anchors_batch)
            print(f"  [{req_num}] {chapter_file} [{aids}]...", end="", flush=True)

            try:
                msg = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=16384,
                    system=system_prompt,
                    messages=[{"role": "user",
                               "content": build_user_prompt(chapter_context, anchors_batch)}],
                )
                text = msg.content[0].text
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                    if m:
                        data = json.loads(m.group(1))
                    else:
                        print(f" PARSE ERROR")
                        continue

                for item in data.get("content", []):
                    raw_results[f"{custom_id}:{item['anchor_id']}"] = item
                print(f" {len(data.get('content', []))} generated")

            except Exception as e:
                print(f" ERROR: {e}")

    return anchors_index, raw_results


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate anchor enrichment content")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    group.add_argument("--resume", action="store_true")
    group.add_argument("--targets", type=str,
                        help="JSON file with target anchors (bypasses coverage_audit.json)")
    parser.add_argument("--direct", action="store_true",
                        help="Use direct API calls instead of batch (fallback)")
    args = parser.parse_args()

    api_key = load_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    # ── Resume mode ──────────────────────────────────────────────────────
    if args.resume:
        if not BATCH_STATE_FILE.exists():
            print("ERROR: No batch state found.")
            sys.exit(1)
        state = json.loads(BATCH_STATE_FILE.read_text(encoding="utf-8"))
        raw_results = poll_and_collect(client, state["batch_id"])
        merge_results(state["anchors_index"], raw_results, state.get("domain_filter"))
        return

    # ── Load targets ─────────────────────────────────────────────────────
    targets_mode = bool(args.targets)

    if targets_mode:
        targets_path = pathlib.Path(args.targets)
        if not targets_path.is_absolute():
            targets_path = SCRIPTS_DIR / args.targets
        if not targets_path.exists():
            print(f"ERROR: {targets_path} not found.")
            sys.exit(1)
        todo = json.loads(targets_path.read_text(encoding="utf-8"))
        # All targets treated as partial (concept is covered, just missing anchor block)
        for a in todo:
            a.setdefault("coverage", "partial")
        print(f"Loaded {len(todo)} targets from {targets_path.name}")
    else:
        if not AUDIT_FILE.exists():
            print(f"ERROR: {AUDIT_FILE} not found. Run audit_coverage.py first.")
            sys.exit(1)

        audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
        todo = [a for a in audit if a.get("coverage") in ("partial", "missing")]

        if args.domain:
            todo = [a for a in todo if a["domain_code"] == args.domain.upper()]

    if not todo:
        print("No anchors to process.")
        return

    # Group by chapter
    by_chapter = {}
    for a in todo:
        by_chapter.setdefault(a["chapter_file"], []).append(a)

    print(f"Generating content for {len(todo)} anchors across {len(by_chapter)} chapters...")

    # Choose system prompt
    active_prompt = SYSTEM_PROMPT_WITH_INJECT if targets_mode else SYSTEM_PROMPT

    # ── Direct mode (bypass batch API) ───────────────────────────────────
    if args.direct:
        print(f"\nDirect mode: sending individual requests...")
        anchors_index, raw_results = direct_generate(
            client, by_chapter, system_prompt=active_prompt)
        merge_results(anchors_index, raw_results,
                      args.domain if not targets_mode else None,
                      targets_mode=targets_mode)
        return

    # ── Build batch requests (3-5 anchors per call) ──────────────────────
    batch_requests = []
    anchors_index = {}  # custom_id:anchor_id → full anchor record

    for chapter_file, chapter_anchors in sorted(by_chapter.items()):
        html_path = CONTENT_DIR / chapter_file
        if not html_path.exists():
            print(f"  WARNING: {html_path} not found, skipping")
            continue

        chapter_context = extract_chapter_context(html_path)
        n_batches = math.ceil(len(chapter_anchors) / ANCHORS_PER_CALL)

        for batch_idx in range(n_batches):
            start = batch_idx * ANCHORS_PER_CALL
            end = start + ANCHORS_PER_CALL
            anchors_batch = chapter_anchors[start:end]

            custom_id = (chapter_file.replace("/", "_").replace(".html", "")
                         + f"_b{batch_idx}")

            batch_requests.append({
                "custom_id": custom_id,
                "params": {
                    "model": "claude-opus-4-6",
                    "max_tokens": 16384,
                    "system": active_prompt,
                    "messages": [{"role": "user",
                                  "content": build_user_prompt(chapter_context, anchors_batch)}],
                },
            })

            for a in anchors_batch:
                anchors_index[f"{custom_id}:{a['anchor_id']}"] = {
                    **a,
                    "custom_id": custom_id,
                }

    print(f"\nSubmitting batch with {len(batch_requests)} requests "
          f"(~{len(todo)} anchors in batches of {ANCHORS_PER_CALL})...")

    batch = client.messages.batches.create(requests=batch_requests)
    print(f"  Batch ID: {batch.id}")

    # Save state
    state = {
        "batch_id": batch.id,
        "domain_filter": args.domain or "all",
        "anchors_index": anchors_index,
        "request_count": len(batch_requests),
    }
    BATCH_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Poll and collect ─────────────────────────────────────────────────
    raw_results = poll_and_collect(client, batch.id)
    merge_results(anchors_index, raw_results,
                  args.domain if not targets_mode else None,
                  targets_mode=targets_mode)


def validate_generated(record):
    """
    Validate a single generated HTML block.
    Returns (is_valid, issues_list).
    """
    html = record.get("generated_html", "")
    anchor_id = record["anchor_id"]
    coverage = record["coverage"]
    issues = []

    if not html.strip():
        return False, ["empty generated_html"]

    # 1. Comment markers present (open + close)
    open_marker = f"<!-- anchor:{anchor_id} coverage:{coverage} -->"
    close_marker = f"<!-- /anchor:{anchor_id} -->"
    if open_marker not in html:
        issues.append(f"missing open marker: {open_marker}")
    if close_marker not in html:
        issues.append(f"missing close marker: {close_marker}")

    # 2. Word count in bounds
    text_only = re.sub(r'<[^>]+>', ' ', html)
    text_only = re.sub(r'<!--.*?-->', ' ', text_only)
    words = text_only.split()
    word_count = len(words)

    if coverage == "missing" and (word_count < 50 or word_count > 500):
        issues.append(f"missing anchor word count {word_count} outside 50-500 range")
    elif coverage == "partial" and (word_count < 20 or word_count > 250):
        issues.append(f"partial anchor word count {word_count} outside 20-250 range")

    # 3. No verbatim anchor text (check for 5+ consecutive word overlap)
    anchor_text = record.get("content", "")
    if anchor_text:
        anchor_words = anchor_text.lower().split()
        gen_lower = text_only.lower()
        for i in range(len(anchor_words) - 4):
            phrase = " ".join(anchor_words[i:i+5])
            if phrase in gen_lower:
                issues.append(f"verbatim overlap: '{phrase}'")
                break

    # 4. CSS classes from allowed list only
    found_classes = re.findall(r'class="([^"]+)"', html)
    for cls_str in found_classes:
        for cls in cls_str.split():
            if cls not in ALLOWED_CSS_CLASSES:
                issues.append(f"disallowed CSS class: {cls}")

    return len(issues) == 0, issues


def merge_results(anchors_index, raw_results, domain_filter=None,
                   targets_mode=False):
    """Merge generated content with anchor metadata, validate, and save."""
    results = []
    matched = 0
    validation_warnings = 0

    for key, anchor in anchors_index.items():
        item = None
        if key in raw_results:
            item = raw_results[key]
        else:
            # Try partial key match (custom_id might differ)
            aid = anchor["anchor_id"]
            for rkey, rval in raw_results.items():
                if rkey.endswith(f":{aid}"):
                    item = rval
                    break

        if item is None:
            print(f"  WARNING: No generated content for [{anchor['anchor_id']}]")
            continue

        # In targets mode, Claude provides inject_after in its response
        inject_after = anchor.get("inject_after")
        if targets_mode and item.get("inject_after"):
            inject_after = item["inject_after"]
            # Strip markdown heading prefixes (### / ##) if present
            inject_after = re.sub(r'^#{1,4}\s*', '', inject_after).strip()

        record = {
            "anchor_id": anchor["anchor_id"],
            "domain_num": anchor["domain_num"],
            "domain_code": anchor["domain_code"],
            "chapter_file": anchor["chapter_file"],
            "coverage": anchor["coverage"],
            "inject_after": inject_after,
            "content": anchor["content"],
            "embed_eligible": anchor.get("embed_eligible", True),
            "generated_html": item.get("generated_html", ""),
        }

        # Validation pass
        is_valid, issues = validate_generated(record)
        record["validation_passed"] = is_valid
        if not is_valid:
            record["validation_issues"] = issues
            validation_warnings += 1
            print(f"  VALIDATION [{anchor['anchor_id']}]: {'; '.join(issues)}")

        results.append(record)
        matched += 1

    # Merge mode: preserve existing results not in this batch
    if targets_mode and OUTPUT_FILE.exists():
        # Replace matching (anchor_id, domain_num) entries, preserve everything else
        new_keys = set((r["anchor_id"], r["domain_num"]) for r in results)
        existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        kept = [r for r in existing
                if (r["anchor_id"], r["domain_num"]) not in new_keys]
        results = kept + results
    elif domain_filter and domain_filter != "all" and OUTPUT_FILE.exists():
        existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing = [r for r in existing if r.get("domain_code") != domain_filter.upper()]
        results = existing + results

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    by_cov = {}
    for r in results:
        c = r["coverage"]
        by_cov[c] = by_cov.get(c, 0) + 1

    print(f"\nGeneration complete: {matched}/{len(anchors_index)} anchors")
    for cov, count in sorted(by_cov.items()):
        print(f"  {cov}: {count}")
    if validation_warnings:
        print(f"  ⚠ {validation_warnings} validation warning(s) — review before injecting")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
