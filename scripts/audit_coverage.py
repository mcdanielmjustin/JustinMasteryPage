"""
audit_coverage.py  (Phase 2 — REVISED)

Audit how well each chapter covers its mapped anchor points.
Reads from anchors_classified.json, filters to embed_eligible only.
Uses keyword pre-filtering + Anthropic Message Batches API (50% discount).

Output: scripts/data/coverage_audit.json

Run:
  python scripts/audit_coverage.py --all
  python scripts/audit_coverage.py --domain PMET
  python scripts/audit_coverage.py --pilot          # alias for --domain PMET
  python scripts/audit_coverage.py --resume
  python scripts/audit_coverage.py --all --direct   # bypass batch API
"""

import json, pathlib, re, sys, argparse, time, os
import anthropic

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CONTENT_DIR = SCRIPTS_DIR.parent / "content"
CLASSIFIED_FILE = DATA_DIR / "anchors_classified.json"
OUTPUT_FILE = DATA_DIR / "coverage_audit.json"
BATCH_STATE_FILE = DATA_DIR / "audit_batch_state.json"

PREFILTER_THRESHOLD = 0.90

SYSTEM_PROMPT = """\
You are auditing an EPPP (psychology licensing exam) textbook chapter for content coverage.

CRITICAL CONTEXT: The textbook was written by an author who used these anchor points as a \
reference guide. The author deliberately teaches the same concepts using DIFFERENT terminology, \
examples, and framing. A concept is "covered" if a student reading this chapter would learn \
what the anchor tests, regardless of wording.

You will receive:
1. The full text of a textbook chapter (with ## and ### heading markers)
2. A list of anchor points (exam-testable concepts) that should be covered

For EACH anchor point, determine:
- "covered" — concept IS taught in the chapter (even if using completely different words, \
  examples, or framing than the anchor)
- "partial" — concept is touched on but missing a crucial detail the anchor specifically tests
- "missing" — concept is genuinely absent; a student would NOT learn it from this chapter

When uncertain between "covered" and "partial", lean toward "covered". \
The goal is to find genuine GAPS, not generate unnecessary additions.

For "partial" and "missing" anchors, identify the best h2 or h3 heading after which \
new content should be inserted. Choose the most topically relevant heading.

Respond with ONLY valid JSON:
{
    "ratings": [
        {"anchor_id": "020", "coverage": "covered", "inject_after": null, "reasoning": "Chapter explains spontaneous recovery in detail under Classical Conditioning"},
        {"anchor_id": "009", "coverage": "missing", "inject_after": "Basic Principles", "reasoning": "Concept of X not addressed anywhere in the chapter"}
    ]
}"""


def load_api_key():
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']
    for p in [pathlib.Path('.env'), pathlib.Path.home() / '.env']:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('ANTHROPIC_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or create a .env file.")


def extract_text_with_headings(html):
    """Strip HTML to plain text, preserving heading structure."""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def keyword_coverage(anchor_content, chapter_text):
    """Fraction of anchor's significant words that appear in chapter text."""
    stop = {'that', 'this', 'with', 'from', 'they', 'their', 'have', 'been',
            'were', 'when', 'which', 'than', 'them', 'into', 'also', 'more',
            'most', 'only', 'other', 'such', 'each', 'will', 'would', 'about',
            'does', 'because', 'being', 'some', 'could', 'should', 'between'}
    words = set(w.lower() for w in re.findall(r'\b[a-z]{4,}\b', anchor_content.lower())) - stop
    if len(words) < 3:
        return 0.0
    chapter_lower = chapter_text.lower()
    found = sum(1 for w in words if w in chapter_lower)
    return found / len(words)


def build_user_prompt(chapter_text, anchors):
    """Build user prompt for a single chapter audit."""
    anchor_list = "\n".join(f"[{a['anchor_id']}] {a['content']}" for a in anchors)
    max_len = 60000
    if len(chapter_text) > max_len:
        chapter_text = chapter_text[:max_len] + "\n\n[... chapter truncated ...]"
    return (
        f"CHAPTER TEXT:\n{chapter_text}\n\n"
        f"---\n\n"
        f"ANCHOR POINTS TO AUDIT ({len(anchors)} total):\n{anchor_list}"
    )


def poll_and_collect(client, batch_id, anchor_lookup):
    """Poll batch until complete, then collect results."""
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

    results = []
    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id
        parts = custom_id.split("_", 1)
        chapter_file = f"{parts[0]}/{parts[1]}.html" if len(parts) == 2 else custom_id

        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if m:
                    data = json.loads(m.group(1))
                else:
                    print(f"  WARNING: Could not parse JSON for {custom_id}")
                    continue

            for rating in data.get("ratings", []):
                aid = rating["anchor_id"]
                key = f"{chapter_file}:{aid}"
                anchor = anchor_lookup.get(key, {})
                if not anchor:
                    print(f"  WARNING: No anchor found for {key}")
                    continue
                results.append({
                    **anchor,
                    "coverage": rating.get("coverage", "missing"),
                    "inject_after": rating.get("inject_after"),
                    "audit_method": "api",
                    "audit_reasoning": rating.get("reasoning", ""),
                })
        else:
            print(f"  ERROR: {custom_id} — {result.result.type}")

    return results


def direct_audit(client, chapters_for_api, anchor_lookup):
    """Send individual API requests instead of batch (fallback when batch API is down)."""
    results = []
    total = len(chapters_for_api)
    for idx, (chapter_file, data) in enumerate(sorted(chapters_for_api.items()), 1):
        custom_id = chapter_file.replace("/", "_").replace(".html", "")
        n_anchors = len(data["anchors"])
        print(f"  [{idx}/{total}] {chapter_file} ({n_anchors} anchors)...", end="", flush=True)

        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user",
                           "content": build_user_prompt(data["chapter_text"], data["anchors"])}],
            )
            text = msg.content[0].text
            try:
                resp = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if m:
                    resp = json.loads(m.group(1))
                else:
                    print(f" PARSE ERROR")
                    continue

            count = 0
            for rating in resp.get("ratings", []):
                aid = rating["anchor_id"]
                key = f"{chapter_file}:{aid}"
                anchor = anchor_lookup.get(key, {})
                if not anchor:
                    continue
                results.append({
                    **anchor,
                    "coverage": rating.get("coverage", "missing"),
                    "inject_after": rating.get("inject_after"),
                    "audit_method": "api_direct",
                    "audit_reasoning": rating.get("reasoning", ""),
                })
                count += 1
            print(f" {count} rated")

        except Exception as e:
            print(f" ERROR: {e}")

    return results


def save_results(results, domain_filter=None):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Merge mode: preserve results from other domains
    if domain_filter and domain_filter != "all" and OUTPUT_FILE.exists():
        existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing = [r for r in existing if r.get("domain_code") != domain_filter.upper()]
        results = existing + results

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    by_cov = {}
    for r in results:
        c = r.get("coverage", "unknown")
        by_cov[c] = by_cov.get(c, 0) + 1
    print(f"\nAudit complete: {len(results)} anchors")
    for cov, count in sorted(by_cov.items()):
        print(f"  {cov}: {count}")
    print(f"Saved to {OUTPUT_FILE}")


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Audit anchor coverage in chapters")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    group.add_argument("--pilot", action="store_true", help="Alias for --domain PMET")
    group.add_argument("--resume", action="store_true", help="Poll existing batch")
    parser.add_argument("--direct", action="store_true",
                        help="Use direct API calls instead of batch (fallback)")
    args = parser.parse_args()

    if args.pilot:
        args.domain = "PMET"

    api_key = load_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    # Build anchor lookup for result parsing — read from classified file
    if not CLASSIFIED_FILE.exists():
        print(f"ERROR: {CLASSIFIED_FILE} not found. Run classify_anchors.py first.")
        sys.exit(1)

    all_anchors = json.loads(CLASSIFIED_FILE.read_text(encoding="utf-8"))
    anchor_lookup = {}
    for a in all_anchors:
        if a.get("chapter_file"):
            key = f"{a['chapter_file']}:{a['anchor_id']}"
            anchor_lookup[key] = a

    # ── Resume mode ──────────────────────────────────────────────────────
    if args.resume:
        if not BATCH_STATE_FILE.exists():
            print("ERROR: No batch state found.")
            sys.exit(1)
        state = json.loads(BATCH_STATE_FILE.read_text(encoding="utf-8"))
        api_results = poll_and_collect(client, state["batch_id"], anchor_lookup)
        all_results = state.get("pre_filter_results", []) + api_results
        save_results(all_results, state.get("domain_filter"))
        return

    # ── Load and filter anchors (embed_eligible only) ────────────────────
    anchors = [a for a in all_anchors
               if a.get("chapter_file") and a.get("embed_eligible", False)]
    if args.domain:
        anchors = [a for a in anchors if a["domain_code"] == args.domain.upper()]

    if not anchors:
        print("No anchors to audit.")
        return

    by_chapter = {}
    for a in anchors:
        by_chapter.setdefault(a["chapter_file"], []).append(a)

    print(f"Auditing {len(anchors)} anchors across {len(by_chapter)} chapters...\n")

    # ── Pre-filter pass ──────────────────────────────────────────────────
    pre_filter_results = []
    chapters_for_api = {}

    for chapter_file, chapter_anchors in sorted(by_chapter.items()):
        html_path = CONTENT_DIR / chapter_file
        if not html_path.exists():
            print(f"  WARNING: {html_path} not found, skipping")
            continue

        html = html_path.read_text(encoding="utf-8")
        chapter_text = extract_text_with_headings(html)

        api_anchors = []
        pre_count = 0
        for anchor in chapter_anchors:
            cov = keyword_coverage(anchor["content"], chapter_text)
            if cov >= PREFILTER_THRESHOLD:
                pre_filter_results.append({
                    **anchor,
                    "coverage": "covered",
                    "inject_after": None,
                    "audit_method": "pre_filter",
                    "keyword_coverage": round(cov, 3),
                })
                pre_count += 1
            else:
                api_anchors.append(anchor)

        status = f"{pre_count} pre-filtered, {len(api_anchors)} need API"
        print(f"  {chapter_file}: {status}")

        if api_anchors:
            chapters_for_api[chapter_file] = {
                "chapter_text": chapter_text,
                "anchors": api_anchors,
            }

    api_anchor_count = sum(len(c['anchors']) for c in chapters_for_api.values())
    print(f"\nPre-filtered: {len(pre_filter_results)} covered")
    print(f"Need API audit: {api_anchor_count} anchors across {len(chapters_for_api)} chapters")

    if not chapters_for_api:
        save_results(pre_filter_results, args.domain)
        return

    # ── Direct mode (bypass batch API) ───────────────────────────────────
    if args.direct:
        print(f"\nDirect mode: sending {len(chapters_for_api)} individual requests...")
        api_results = direct_audit(client, chapters_for_api, anchor_lookup)
        all_results = pre_filter_results + api_results
        save_results(all_results, args.domain)
        return

    # ── Build and submit batch ───────────────────────────────────────────
    batch_requests = []
    for chapter_file, data in sorted(chapters_for_api.items()):
        custom_id = chapter_file.replace("/", "_").replace(".html", "")
        batch_requests.append({
            "custom_id": custom_id,
            "params": {
                "model": "claude-opus-4-6",
                "max_tokens": 8192,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user",
                              "content": build_user_prompt(data["chapter_text"], data["anchors"])}],
            },
        })

    print(f"\nSubmitting batch with {len(batch_requests)} requests...")
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"  Batch ID: {batch.id}")

    # Save state for resume
    state = {
        "batch_id": batch.id,
        "domain_filter": args.domain or "all",
        "pre_filter_results": pre_filter_results,
    }
    BATCH_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Poll and collect ─────────────────────────────────────────────────
    api_results = poll_and_collect(client, batch.id, anchor_lookup)
    all_results = pre_filter_results + api_results
    save_results(all_results, args.domain)


if __name__ == "__main__":
    main()
