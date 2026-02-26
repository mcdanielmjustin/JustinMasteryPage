"""
extract_passages.py

Parses all 129 lecture HTML files in content/domain1-9/ and extracts
meaningful text passages (paragraphs, definition boxes, clinical notes).

Output: data/{DOMAIN_CODE}_passages.json per domain

Passage selection criteria:
  - Minimum 120 characters after stripping HTML
  - Maximum 600 characters (readable unit)
  - Must come from the main content area (not nav/sidebar/action buttons)
  - Must be plain-text extractable (not pure table or list-only nodes)
  - Skips citations, chapter-action sections
"""

import json, re, pathlib
from bs4 import BeautifulSoup

SRC  = pathlib.Path("content")
DST  = pathlib.Path("data")
DST.mkdir(exist_ok=True)

DOMAIN_MAP = {
    "domain1": ("PMET", "Psychometrics & Research Methods"),
    "domain2": ("LDEV", "Lifespan & Developmental Stages"),
    "domain3": ("CPAT", "Clinical Psychopathology (DSM-5)"),
    "domain4": ("PTHE", "Psychotherapy Models, Interventions & Prevention"),
    "domain5": ("SOCU", "Social & Cultural Psychology"),
    "domain6": ("WDEV", "Workforce Development & Leadership"),
    "domain7": ("BPSY", "Biopsychology"),
    "domain8": ("CASS", "Clinical Assessment & Interpretation"),
    "domain9": ("PETH", "Psychopharmacology & Ethics"),
}

MIN_CHARS = 120
MAX_CHARS = 600


def clean_text(text: str) -> str:
    """Collapse whitespace and strip common noise."""
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove lone citation-style fragments
    text = re.sub(r'\([A-Z][a-z]+ et al\.,? \d{4}[^)]*\)', '', text)
    text = re.sub(r'\([A-Z][a-z]+,? \d{4}[^)]*\)', '', text)
    text = re.sub(r'https?://\S+', '', text)
    return text.strip(' .,;')


def extract_chapter_title(soup: BeautifulSoup) -> str:
    h1 = soup.select_one('main h1, .main-content h1')
    return h1.get_text(strip=True) if h1 else ''


def extract_current_section(tag) -> str:
    """Walk backwards to find the nearest h2/h3 heading before this tag."""
    for sib in tag.find_all_previous(['h2', 'h3']):
        t = sib.get_text(strip=True)
        if t:
            return t
    return ''


def extract_passages_from_file(html_path: pathlib.Path, domain_code: str,
                                domain_name: str) -> list[dict]:
    with open(html_path, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Only look inside main content — skip sidebar, nav, action buttons
    main = soup.select_one('main.main-content, .main-content')
    if not main:
        main = soup.body

    # Remove noise elements before scanning
    for sel in ['nav', 'aside', '.chapter-actions', '.action-btn',
                '.nav-buttons', '.upgrade-modal', 'script', 'style',
                '.citation', 'header.chapter-header', '.chapter-meta',
                '.chapter-badge']:
        for el in main.select(sel):
            el.decompose()

    chapter_title = extract_chapter_title(
        BeautifulSoup(open(html_path, encoding='utf-8').read(), 'html.parser')
    )

    passages = []
    seen_texts = set()

    # ── 1. Definition boxes ──────────────────────────────────────────────────
    for box in main.select('.definition-box'):
        text = clean_text(box.get_text(' ', strip=True))
        if MIN_CHARS <= len(text) <= MAX_CHARS and text not in seen_texts:
            seen_texts.add(text)
            passages.append({
                "domain_code":   domain_code,
                "domain_name":   domain_name,
                "chapter_file":  html_path.name,
                "chapter_title": chapter_title,
                "section":       extract_current_section(box),
                "passage_type":  "definition",
                "passage":       text,
            })

    # ── 2. Clinical notes ────────────────────────────────────────────────────
    for box in main.select('.clinical-note'):
        text = clean_text(box.get_text(' ', strip=True))
        if MIN_CHARS <= len(text) <= MAX_CHARS and text not in seen_texts:
            seen_texts.add(text)
            passages.append({
                "domain_code":   domain_code,
                "domain_name":   domain_name,
                "chapter_file":  html_path.name,
                "chapter_title": chapter_title,
                "section":       extract_current_section(box),
                "passage_type":  "clinical_note",
                "passage":       text,
            })

    # ── 3. Example boxes ─────────────────────────────────────────────────────
    for box in main.select('.example-box'):
        text = clean_text(box.get_text(' ', strip=True))
        if MIN_CHARS <= len(text) <= MAX_CHARS and text not in seen_texts:
            seen_texts.add(text)
            passages.append({
                "domain_code":   domain_code,
                "domain_name":   domain_name,
                "chapter_file":  html_path.name,
                "chapter_title": chapter_title,
                "section":       extract_current_section(box),
                "passage_type":  "example",
                "passage":       text,
            })

    # ── 4. Standalone paragraphs (not inside boxes already captured) ─────────
    captured_boxes = set()
    for box in main.select('.definition-box, .clinical-note, .example-box'):
        captured_boxes.add(id(box))

    for p in main.find_all('p'):
        # Skip if inside an already-captured box
        if any(id(anc) in captured_boxes for anc in p.parents):
            continue
        text = clean_text(p.get_text(' ', strip=True))
        if MIN_CHARS <= len(text) <= MAX_CHARS and text not in seen_texts:
            seen_texts.add(text)
            passages.append({
                "domain_code":   domain_code,
                "domain_name":   domain_name,
                "chapter_file":  html_path.name,
                "chapter_title": chapter_title,
                "section":       extract_current_section(p),
                "passage_type":  "paragraph",
                "passage":       text,
            })

    return passages


# ── Main ─────────────────────────────────────────────────────────────────────
buckets = {code: [] for code, _ in DOMAIN_MAP.values()}
domain_names = {code: name for code, name in DOMAIN_MAP.values()}

total_files = 0
for dname, (code, dname_full) in DOMAIN_MAP.items():
    domain_dir = SRC / dname
    if not domain_dir.exists():
        print(f"  SKIP (not found): {domain_dir}")
        continue
    html_files = sorted(f for f in domain_dir.glob('*.html')
                        if f.name != 'index.html')
    for html_file in html_files:
        passages = extract_passages_from_file(html_file, code, dname_full)
        buckets[code].extend(passages)
        total_files += 1

print(f"\nExtracted from {total_files} HTML files:\n")
grand_total = 0
for code, passages in buckets.items():
    # Add sequential IDs
    for i, p in enumerate(passages, 1):
        p['id'] = f"{code}-{i:04d}"

    out = {
        "domain_code":     code,
        "domain_name":     domain_names[code],
        "total_passages":  len(passages),
        "passages":        passages,
    }
    path = DST / f"{code}_passages.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  {code}_passages.json  {len(passages)} passages")
    grand_total += len(passages)

print(f"\nTotal: {grand_total} passages written to data/")
