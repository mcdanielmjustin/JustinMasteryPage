"""
generate_visual_aids.py

Generates visual-aid HTML blocks for chapter files using the Claude API.
Uses 14+ CSS layout types defined in chapter-enhancements.css.

Run:
  python scripts/generate_visual_aids.py --all
  python scripts/generate_visual_aids.py --domain PMET
  python scripts/generate_visual_aids.py --all --resume
  python scripts/generate_visual_aids.py --all --max-per-chapter 2
"""

import json, pathlib, argparse, time, re, sys, os, datetime
import anthropic

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
OUTPUT_FILE = DATA_DIR / "visual_aids_generated.json"
DEFAULT_CONTENT_DIR = pathlib.Path("C:/Users/Admin/JustinMasteryPage/content")

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

DEFAULT_MODEL = "claude-sonnet-4-6"

VA_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
    'stroke-width="1.5" stroke="currentColor">'
    '<path stroke-linecap="round" stroke-linejoin="round" '
    'd="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 '
    '0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 '
    '0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 '
    '9v3.75m3-6v6.75"/></svg>'
)

# ══════════════════════════════════════════════════════════════════════
# Layout type HTML template reference (for system prompt)
# ══════════════════════════════════════════════════════════════════════

LAYOUT_REFERENCE = r"""
## va-compare — Side-by-side comparison columns (2-4 columns)
```html
<div class="va-compare">
  <div class="va-compare-col">
    <h5>Column Title</h5>
    <ul>
      <li>Point one</li>
      <li>Point two</li>
    </ul>
  </div>
  <div class="va-compare-col">
    <h5>Column Title</h5>
    <ul>
      <li>Point one</li>
      <li>Point two</li>
    </ul>
  </div>
</div>
```
Best for: comparing theories, disorders, approaches, treatments side by side.

## va-tree — Hierarchy / org-chart
```html
<div class="va-tree">
  <div class="va-tree-node va-root">Root Concept<div class="va-tree-node-sub">Optional subtitle</div></div>
  <div class="va-tree-children">
    <div class="va-tree-node">Child 1<div class="va-tree-node-sub">Detail</div></div>
    <div class="va-tree-node">Child 2<div class="va-tree-node-sub">Detail</div></div>
    <div class="va-tree-children">
      <div class="va-tree-node">Grandchild</div>
    </div>
  </div>
</div>
```
Best for: taxonomies, classification systems, diagnostic hierarchies.

## va-matrix — Grid table (set columns via inline style)
```html
<div class="va-matrix" style="grid-template-columns: repeat(4, 1fr)">
  <div class="va-matrix-cell va-matrix-header"></div>
  <div class="va-matrix-cell va-matrix-header">Col 1</div>
  <div class="va-matrix-cell va-matrix-header">Col 2</div>
  <div class="va-matrix-cell va-matrix-header">Col 3</div>
  <div class="va-matrix-cell va-matrix-label">Row 1</div>
  <div class="va-matrix-cell">Data</div>
  <div class="va-matrix-cell">Data</div>
  <div class="va-matrix-cell">Data</div>
</div>
```
Best for: multi-dimensional comparisons, score tables, decision matrices.

## va-timeline — Chronological / sequential events
```html
<div class="va-timeline">
  <div class="va-timeline-item">
    <div class="va-timeline-label">Stage/Year</div>
    <div class="va-timeline-content">Description of this stage</div>
  </div>
  <div class="va-timeline-item">
    <div class="va-timeline-label">Stage/Year</div>
    <div class="va-timeline-content">Description of this stage</div>
  </div>
</div>
```
Best for: developmental stages, historical progressions, treatment phases.

## va-cycle — Circular process (items connected by arrows, last arrow uses ↩)
```html
<div class="va-cycle">
  <div class="va-cycle-step"><div class="va-cycle-step-label">Phase 1</div>Description</div>
  <div class="va-cycle-arrow">→</div>
  <div class="va-cycle-step"><div class="va-cycle-step-label">Phase 2</div>Description</div>
  <div class="va-cycle-arrow">→</div>
  <div class="va-cycle-step"><div class="va-cycle-step-label">Phase 3</div>Description</div>
  <div class="va-cycle-arrow">↩</div>
</div>
```
Best for: feedback loops, recurring processes, cyclical models.

## va-steps — Numbered sequential steps (vertical with connecting line)
```html
<div class="va-steps">
  <div class="va-step">
    <div class="va-step-num">1</div>
    <div class="va-step-title">Step Title</div>
    <div class="va-step-desc">Brief description</div>
  </div>
  <div class="va-step">
    <div class="va-step-num">2</div>
    <div class="va-step-title">Step Title</div>
    <div class="va-step-desc">Brief description</div>
  </div>
</div>
```
Best for: procedures, protocols, assessment sequences, treatment steps.

## va-flow — Horizontal process flow (items with arrows between)
```html
<div class="va-flow">
  <div class="va-flow-step">
    <div class="va-flow-step-label">Input</div>
    <div class="va-flow-step-content">Main text</div>
    <div class="va-flow-step-sub">Optional detail</div>
  </div>
  <div class="va-flow-arrow">→</div>
  <div class="va-flow-step">
    <div class="va-flow-step-label">Process</div>
    <div class="va-flow-step-content">Main text</div>
  </div>
  <div class="va-flow-arrow">→</div>
  <div class="va-flow-step">
    <div class="va-flow-step-label">Output</div>
    <div class="va-flow-step-content">Main text</div>
  </div>
</div>
```
Best for: stimulus-response chains, information processing, causal pathways.

## va-pyramid — Hierarchy pyramid (widest at bottom)
```html
<div class="va-pyramid">
  <div class="va-pyramid-layer">Top Level<div class="va-pyramid-layer-sub">Description</div></div>
  <div class="va-pyramid-layer">Middle Level</div>
  <div class="va-pyramid-layer">Base Level</div>
</div>
```
Best for: Maslow's hierarchy, needs models, tiered systems. Max 5-6 layers.

## va-split — Two-panel comparison with "vs" divider
```html
<div class="va-split">
  <div class="va-split-left">
    <h5>Concept A</h5>
    <ul><li>Feature 1</li><li>Feature 2</li></ul>
  </div>
  <div class="va-split-divider"></div>
  <div class="va-split-right">
    <h5>Concept B</h5>
    <ul><li>Feature 1</li><li>Feature 2</li></ul>
  </div>
</div>
```
Best for: direct two-item contrasts (Type I vs Type II, CBT vs psychodynamic).

## va-hub — Central concept with surrounding spokes
```html
<div class="va-hub">
  <div class="va-hub-spoke"><h5>Factor 1</h5><p>Detail</p></div>
  <div class="va-hub-spoke"><h5>Factor 2</h5><p>Detail</p></div>
  <div class="va-hub-center">Central Concept</div>
  <div class="va-hub-spoke"><h5>Factor 3</h5><p>Detail</p></div>
  <div class="va-hub-spoke"><h5>Factor 4</h5><p>Detail</p></div>
</div>
```
Best for: multi-factor models, components of a construct, related subtypes.

## va-spectrum — Gradient spectrum bar with labeled markers
```html
<div class="va-spectrum">
  <div class="va-spectrum-bar"></div>
  <div class="va-spectrum-markers">
    <div class="va-spectrum-marker">
      <div class="va-spectrum-marker-label">Low</div>
      <div class="va-spectrum-marker-desc">Description</div>
    </div>
    <div class="va-spectrum-marker">
      <div class="va-spectrum-marker-label">Medium</div>
      <div class="va-spectrum-marker-desc">Description</div>
    </div>
    <div class="va-spectrum-marker">
      <div class="va-spectrum-marker-label">High</div>
      <div class="va-spectrum-marker-desc">Description</div>
    </div>
  </div>
</div>
```
Best for: severity ranges, scales, dimensional models (introversion-extraversion).

## va-cards — Horizontal scrollable card row
```html
<div class="va-cards">
  <div class="va-card-item"><h5>Card Title</h5><p>Brief content</p></div>
  <div class="va-card-item"><h5>Card Title</h5><p>Brief content</p></div>
  <div class="va-card-item"><h5>Card Title</h5><p>Brief content</p></div>
</div>
```
Best for: key terms, theorist summaries, test instruments at a glance.

## va-bridge — Before / Intervention / After (three-panel)
```html
<div class="va-bridge">
  <div class="va-bridge-panel"><h5>Before</h5><ul><li>Symptom/state</li></ul></div>
  <div class="va-bridge-arrow">→</div>
  <div class="va-bridge-panel va-bridge-center"><h5>Intervention</h5><ul><li>Technique</li></ul></div>
  <div class="va-bridge-arrow">→</div>
  <div class="va-bridge-panel"><h5>After</h5><ul><li>Outcome</li></ul></div>
</div>
```
Best for: treatment outcomes, before/after comparisons, intervention models.

## va-checklist — Check/cross items
```html
<div class="va-checklist">
  <div class="va-check-item check">Correct/included item</div>
  <div class="va-check-item cross">Incorrect/excluded item</div>
  <div class="va-check-item check">Another correct item</div>
</div>
```
Best for: diagnostic criteria (present/absent), inclusion/exclusion criteria, common misconceptions.
"""

SYSTEM_PROMPT = f"""You are an expert educational content designer for EPPP (Examination for Professional Practice in Psychology) study materials, specializing in differentiated instruction and visual learning.

Your task: Given a chapter's HTML content, generate 2-3 visual-aid graphic organizers that help students understand key concepts in clinical practice exam through DIVERSE visual representations.

SELECTION RULES:
1. Only create visual aids where they GENUINELY help — comparisons, processes, hierarchies, timelines, classifications, spectrums, flowcharts
2. Each visual aid must be 100% factually accurate based on the chapter content
3. Prefer concepts that are clinically important
4. Do NOT create visual aids for simple definitions or single facts
5. If a chapter has very few organizable concepts, return just 1 or even 0 visual aids

LAYOUT DIVERSITY — CRITICAL:
- AVOID overusing va-matrix. Use it only when a true multi-dimensional grid is the best representation.
- PREFER these underused but powerful layouts:
  * va-tree — for classification systems, diagnostic hierarchies, theory taxonomies
  * va-timeline — for developmental stages, historical progressions, treatment phases, onset patterns
  * va-flow — for causal pathways, stimulus-response chains, neural circuits, information processing models
  * va-spectrum — for severity continua, dimensional models, personality traits, dose-response curves
  * va-cycle — for feedback loops, maintenance cycles (e.g., anxiety cycle, addiction cycle)
  * va-pyramid — for hierarchical models (Maslow, Bloom's, evidence hierarchies)
  * va-bridge — for treatment before/after comparisons, intervention models
- Use va-compare and va-split for genuine two-way contrasts, not as a default
- Each chapter's visual aids should use DIFFERENT layout types from each other

DIFFERENTIATED INSTRUCTION:
- Design visual aids that serve multiple learning styles: visual-spatial learners (trees, flows, hubs), sequential learners (timelines, steps, cycles), comparative thinkers (splits, spectrums)
- When a concept has both a process AND a classification aspect, choose the representation that is HARDER to glean from reading prose alone
- Prioritize visual aids that reveal relationships, sequences, or hierarchies that are implicit in the text but not visually obvious

HTML RULES:
1. Use ONLY the CSS classes listed in the layout reference below
2. Do NOT add any inline styles except grid-template-columns on va-matrix
3. Do NOT use any custom classes or IDs
4. Keep all text concise — short phrases, not sentences
5. Use plain text only — no markdown, no HTML entities except &amp; and &mdash;

{LAYOUT_REFERENCE}

RESPONSE FORMAT:
Return ONLY a valid JSON array — no markdown fences, no explanation, no preamble.
Each element must have exactly these fields:
{{
  "title": "Concise descriptive title (3-8 words)",
  "layout_type": "va-compare|va-tree|va-matrix|va-timeline|va-cycle|va-steps|va-flow|va-pyramid|va-split|va-hub|va-spectrum|va-cards|va-bridge|va-checklist",
  "anchor_heading": "Exact text of an h2 or h3 heading in the chapter (must match precisely)",
  "inner_html": "The layout HTML content — everything that goes INSIDE the visual-aid div, AFTER the title div"
}}

If no good visual aids can be made for this chapter, return an empty array: []
"""


# ══════════════════════════════════════════════════════════════════════
# API key loading (matches existing pipeline pattern)
# ══════════════════════════════════════════════════════════════════════

def load_api_key(args_key=None):
    if args_key:
        return args_key
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for p in [pathlib.Path(".env"), pathlib.Path.home() / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or pass --api-key.")


# ══════════════════════════════════════════════════════════════════════
# Content extraction
# ══════════════════════════════════════════════════════════════════════

def extract_chapter_content(html_text):
    """Extract main content from chapter HTML, stripping boilerplate."""
    # Find main-content div
    m = re.search(r'<div\s+class="main-content"[^>]*>', html_text, re.IGNORECASE)
    if m:
        start = m.end()
    else:
        # Fallback: start from first h1
        m2 = re.search(r'<h1', html_text, re.IGNORECASE)
        start = m2.start() if m2 else 0

    # End before scripts
    m_end = re.search(r'<script[\s>]', html_text[start:], re.IGNORECASE)
    if m_end:
        end = start + m_end.start()
    else:
        end = len(html_text)

    content = html_text[start:end]

    # Strip inline style blocks
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Strip upgrade modal
    content = re.sub(r'<div[^>]*id="upgradeModal".*?</div>\s*</div>\s*</div>',
                     '', content, flags=re.DOTALL | re.IGNORECASE)

    return content.strip()


def list_headings(content):
    """Extract h2/h3 heading texts for reference."""
    headings = []
    for m in re.finditer(r'<(h[23])[^>]*>(.*?)</\1>', content, re.DOTALL | re.IGNORECASE):
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        text = re.sub(r'\s+', ' ', text)
        if text:
            headings.append(text)
    return headings


# ══════════════════════════════════════════════════════════════════════
# Wrap generated inner_html into full visual-aid block
# ══════════════════════════════════════════════════════════════════════

def build_visual_aid_html(va_id, title, inner_html):
    """Build the complete visual-aid HTML block with markers."""
    lines = [
        f'<!-- visual-aid:{va_id} -->',
        '<div class="visual-aid">',
        '  <div class="visual-aid-title">',
        f'    {VA_ICON}',
        f'    {title}',
        '  </div>',
    ]
    # Indent inner_html
    for line in inner_html.strip().split('\n'):
        stripped = line.strip()
        if stripped:
            lines.append(f'  {stripped}')
        else:
            lines.append('')
    lines.append('</div>')
    lines.append(f'<!-- /visual-aid:{va_id} -->')
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════
# Chapter file discovery
# ══════════════════════════════════════════════════════════════════════

def discover_chapters(content_dir, domain_filter=None):
    """Find all chapter HTML files, grouped by domain."""
    chapters = []
    for domain_dir in sorted(content_dir.iterdir()):
        if not domain_dir.is_dir() or not domain_dir.name.startswith("domain"):
            continue
        domain_code = DOMAIN_MAP.get(domain_dir.name)
        if not domain_code:
            continue
        if domain_filter and domain_code != domain_filter:
            continue
        for html_file in sorted(domain_dir.glob("*.html")):
            if html_file.name == "index.html":
                continue
            rel_path = f"{domain_dir.name}/{html_file.name}"
            chapters.append({
                "path": html_file,
                "rel_path": rel_path,
                "domain_code": domain_code,
                "domain_dir": domain_dir.name,
            })
    return chapters


# ══════════════════════════════════════════════════════════════════════
# Generation
# ══════════════════════════════════════════════════════════════════════

def generate_for_chapter(client, model, chapter_info, max_per_chapter):
    """Call Claude API to generate visual aids for one chapter."""
    html_text = chapter_info["path"].read_text(encoding="utf-8")
    content = extract_chapter_content(html_text)
    headings = list_headings(content)

    if not headings:
        return []

    # Truncate content if extremely long (>80K chars ~ 20K tokens)
    if len(content) > 80000:
        content = content[:80000] + "\n\n[... content truncated ...]"

    domain_name = DOMAIN_NAMES.get(chapter_info["domain_code"], "")
    chapter_name = chapter_info["path"].stem.replace("-", " ").title()

    user_prompt = (
        f"Domain: {chapter_info['domain_code']} — {domain_name}\n"
        f"Chapter: {chapter_name}\n"
        f"File: {chapter_info['rel_path']}\n\n"
        f"Available h2/h3 headings (use these EXACTLY for anchor_heading):\n"
    )
    for h in headings:
        user_prompt += f"  - {h}\n"
    user_prompt += (
        f"\nGenerate up to {max_per_chapter} visual aids for this chapter.\n\n"
        f"--- CHAPTER CONTENT ---\n{content}"
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            break
        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"\n    Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
            wait = 10 * (attempt + 1)
            print(f"\n    Network error ({type(e).__name__}), retry in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 15
                print(f"\n    Error ({type(e).__name__}: {e}), retry in {wait}s...")
                time.sleep(wait)
            else:
                print(f"\n    Failed after {max_retries} attempts: {e}")
                return []
    else:
        print(f"\n    Failed after {max_retries} retries")
        return []

    raw = response.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```\s*$', '', raw)

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"    JSON parse error: {e}")
        print(f"    Raw response (first 300 chars): {raw[:300]}")
        return []

    if not isinstance(items, list):
        print(f"    Expected list, got {type(items).__name__}")
        return []

    return items[:max_per_chapter]


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate visual aids for chapter files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    parser.add_argument("--resume", action="store_true", help="Skip already-generated chapters")
    parser.add_argument("--max-per-chapter", type=int, default=2, help="Max visual aids per chapter")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--api-key", type=str)
    parser.add_argument("--content-dir", type=str, default=str(DEFAULT_CONTENT_DIR))
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between API calls")
    args = parser.parse_args()

    content_dir = pathlib.Path(args.content_dir).resolve()
    if not content_dir.is_dir():
        print(f"ERROR: content dir {content_dir} not found")
        sys.exit(1)

    api_key = load_api_key(args.api_key)
    client = anthropic.Anthropic(api_key=api_key)

    # Load existing output for resume
    existing = []
    existing_chapters = set()
    if OUTPUT_FILE.exists():
        existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing_chapters = {va["chapter_file"] for va in existing}

    domain_filter = args.domain.upper() if args.domain else None
    chapters = discover_chapters(content_dir, domain_filter)
    print(f"Found {len(chapters)} chapter files" +
          (f" (domain={domain_filter})" if domain_filter else "") +
          f", model={args.model}\n")

    total_generated = 0
    all_vas = list(existing)  # Start with existing if resuming

    for i, ch in enumerate(chapters, 1):
        rel = ch["rel_path"]

        if args.resume and rel in existing_chapters:
            n_exist = sum(1 for v in existing if v["chapter_file"] == rel)
            print(f"  [{i}/{len(chapters)}] {rel}: SKIP (resume, {n_exist} existing)")
            continue

        print(f"  [{i}/{len(chapters)}] {rel} ({ch['domain_code']})...", end=" ", flush=True)

        items = generate_for_chapter(client, args.model, ch, args.max_per_chapter)

        if not items:
            print("0 visual aids")
            continue

        chapter_slug = ch["path"].stem
        chapter_vas = []

        for j, item in enumerate(items):
            required = {"title", "layout_type", "anchor_heading", "inner_html"}
            if not required.issubset(item.keys()):
                missing = required - set(item.keys())
                print(f"\n    WARNING: item {j} missing keys: {missing}")
                continue

            va_id = f"va-{ch['domain_code']}-{chapter_slug}-{j+1:03d}"
            full_html = build_visual_aid_html(va_id, item["title"], item["inner_html"])

            va_record = {
                "id": va_id,
                "chapter_file": rel,
                "domain_code": ch["domain_code"],
                "anchor_heading": item["anchor_heading"],
                "title": item["title"],
                "layout_type": item["layout_type"],
                "html": full_html,
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            chapter_vas.append(va_record)

        # If not resuming, remove old entries for this chapter before adding new
        if not args.resume:
            all_vas = [v for v in all_vas if v["chapter_file"] != rel]
        all_vas.extend(chapter_vas)

        print(f"{len(chapter_vas)} visual aid(s)")
        total_generated += len(chapter_vas)

        # Save after each chapter for safety
        OUTPUT_FILE.write_text(
            json.dumps(all_vas, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        if args.delay > 0 and i < len(chapters):
            time.sleep(args.delay)

    # Final stats
    by_domain = {}
    for va in all_vas:
        by_domain.setdefault(va["domain_code"], []).append(va)

    print(f"\nGeneration complete: {total_generated} new visual aids")
    print(f"Total in manifest: {len(all_vas)}")
    for dc in sorted(by_domain):
        print(f"  {dc}: {len(by_domain[dc])}")
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
