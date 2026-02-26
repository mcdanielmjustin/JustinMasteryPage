"""
supplement_passages.py

Appends VERBATIM passages to existing {DOMAIN}_passages.json files by
extracting content that the original extract_passages.py missed:

  - Individual <li> items that are >= 80 chars (verbatim, not joined)
  - Short <p> tags (40-119 chars) that were below the original 120-char min
    (extracted AS-IS, no heading prepended)

Tables are skipped — they cannot be represented verbatim in prose form.

Run after trimming back to originals if the previous non-verbatim run was done:
  python supplement_passages.py --revert      # trim to original counts first
  python supplement_passages.py --all         # then re-extract verbatim

Usage:
  python supplement_passages.py               # all thin chapters
  python supplement_passages.py --domain PETH # single domain thin chapters
  python supplement_passages.py --all         # all chapters all domains
  python supplement_passages.py --revert      # revert to original counts
"""

import json
import pathlib
import argparse
import re
from bs4 import BeautifulSoup

CONTENT_DIR = pathlib.Path("content")
DATA_DIR    = pathlib.Path("data")

DOMAIN_MAP = {
    "domain1": "PMET",
    "domain2": "LDEV",
    "domain3": "CPAT",
    "domain4": "PTHE",
    "domain5": "SOCU",
    "domain6": "WDEV",
    "domain7": "BPSY",
    "domain8": "CASS",
    "domain9": "PETH",
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

# The original passage counts produced by extract_passages.py
# (before any supplemental additions)
ORIGINAL_COUNTS = {
    "PMET": 407,
    "LDEV": 326,
    "CPAT": 246,
    "PTHE": 162,
    "SOCU": 414,
    "WDEV": 229,
    "BPSY": 333,
    "CASS": 549,
    "PETH": 318,
}

THIN_THRESHOLD = 12

NOISE_SELECTORS = [
    'nav', 'aside', '.chapter-actions', '.action-btn',
    '.nav-buttons', '.upgrade-modal', 'script', 'style',
    '.citation', 'header.chapter-header', '.chapter-meta',
    '.chapter-badge', '.chapter-list', '.nav-list', '.back-link',
]


def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def nearest_h_section(tag) -> str:
    """Nearest h2/h3/h4 heading before this tag — used only for metadata."""
    for sib in tag.find_all_previous(['h2', 'h3', 'h4']):
        t = clean(sib.get_text())
        if t:
            return t
    return ''


def in_noise(tag, special_box_ids: set) -> bool:
    noise_classes = {
        'chapter-actions', 'nav-buttons', 'upgrade-modal',
        'chapter-header', 'chapter-badge', 'chapter-meta',
        'nav-list', 'chapter-list', 'sidebar', 'top-nav',
        'coming-soon-container',
    }
    for parent in tag.parents:
        if id(parent) in special_box_ids:
            return True
        cls = set(getattr(parent, 'get', lambda *a: [])(('class',) or []) or [])
        if hasattr(parent, 'get'):
            cls = set(parent.get('class', []))
        if cls & noise_classes:
            return True
        if getattr(parent, 'name', None) in ('nav', 'aside', 'header', 'footer'):
            return True
    return False


def extract_verbatim_passages(html_path: pathlib.Path,
                               domain_code: str, domain_name: str,
                               existing_texts: set) -> list:
    """
    Extract verbatim passages from html_path not already in existing_texts.

    Sources (all verbatim — text lifted directly from the HTML):
      1. Individual <li> items >= 80 chars
      2. Short <p> tags (40-119 chars) not inside special boxes
    """
    soup = BeautifulSoup(html_path.read_text(encoding='utf-8'), 'html.parser')

    h1 = soup.select_one('main h1, .main-content h1')
    chapter_title = clean(h1.get_text()) if h1 else \
        html_path.stem.replace('-', ' ').title()

    main = soup.select_one('main.main-content, .main-content') or soup.body
    for sel in NOISE_SELECTORS:
        for el in main.select(sel):
            el.decompose()

    # IDs of elements already captured verbatim by original script
    special_box_ids: set[int] = set()
    for box in main.select('.definition-box, .clinical-note, .example-box'):
        special_box_ids.add(id(box))
        for desc in box.descendants:
            special_box_ids.add(id(desc))

    new_passages = []

    def add(text: str, ptype: str, section: str):
        if text in existing_texts:
            return
        # Near-dedup: skip if an existing passage starts the same way
        key = text[:90]
        if any(p.startswith(key) for p in existing_texts):
            return
        existing_texts.add(text)
        new_passages.append({
            "domain_code":   domain_code,
            "domain_name":   domain_name,
            "chapter_file":  html_path.name,
            "chapter_title": chapter_title,
            "section":       section,
            "passage_type":  ptype,
            "passage":       text,
        })

    # ── 1. Individual <li> items (verbatim) ─────────────────────────────────
    for li in main.find_all('li'):
        if in_noise(li, special_box_ids):
            continue
        text = clean(li.get_text())
        if len(text) < 80:
            continue
        section = nearest_h_section(li)
        # Classify: EPPP/clinical/tip headings -> clinical_note
        low = section.lower()
        ptype = 'clinical_note' if any(w in low for w in
            ['eppp', 'tip', 'key take', 'clinical implication',
             'exam focus', 'takeaway']) else 'paragraph'
        add(text, ptype, section)

    # ── 2. Short <p> tags missed by original (40-119 chars) ─────────────────
    for p in main.find_all('p'):
        if in_noise(p, special_box_ids):
            continue
        text = clean(p.get_text())
        if 40 <= len(text) < 120:
            section = nearest_h_section(p)
            add(text, 'paragraph', section)

    return new_passages


def next_id_counter(domain_code: str, passages: list) -> int:
    prefix = f"{domain_code}-"
    nums = [int(p['id'][len(prefix):])
            for p in passages
            if p.get('id', '').startswith(prefix)
            and p['id'][len(prefix):].isdigit()]
    return max(nums, default=0) + 1


def domain_folder(domain_code: str) -> pathlib.Path | None:
    for folder, code in DOMAIN_MAP.items():
        if code == domain_code:
            return CONTENT_DIR / folder
    return None


# ── Revert ───────────────────────────────────────────────────────────────────

def revert_domain(domain_code: str):
    """Trim passages back to ORIGINAL_COUNTS[domain_code]."""
    orig = ORIGINAL_COUNTS.get(domain_code)
    if orig is None:
        print(f"  {domain_code}: no original count recorded, skipping")
        return

    json_path = DATA_DIR / f"{domain_code}_passages.json"
    if not json_path.exists():
        print(f"  SKIP: {json_path} not found")
        return

    data = json.loads(json_path.read_text(encoding='utf-8'))
    passages = data['passages']
    before = len(passages)

    # Keep only passages whose numeric ID <= orig count
    prefix = f"{domain_code}-"
    kept = [p for p in passages
            if not p.get('id', '').startswith(prefix)
            or (p['id'][len(prefix):].isdigit()
                and int(p['id'][len(prefix):]) <= orig)]

    removed = before - len(kept)
    data['passages'] = kept
    data['total_passages'] = len(kept)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                         encoding='utf-8')
    print(f"  {domain_code}: {before} -> {len(kept)} (removed {removed} non-verbatim passages)")


# ── Process ──────────────────────────────────────────────────────────────────

def process_domain(domain_code: str,
                   force_all: bool = False,
                   target_chapter: str | None = None):
    json_path = DATA_DIR / f"{domain_code}_passages.json"
    if not json_path.exists():
        print(f"  SKIP: {json_path} not found")
        return

    data = json.loads(json_path.read_text(encoding='utf-8'))
    passages = data['passages']
    existing_texts = set(p['passage'] for p in passages)

    ch_counts: dict[str, int] = {}
    for p in passages:
        ch_counts[p['chapter_file']] = ch_counts.get(p['chapter_file'], 0) + 1

    dfolder = domain_folder(domain_code)
    if not dfolder or not dfolder.exists():
        print(f"  SKIP: content folder not found for {domain_code}")
        return

    html_files = sorted(f for f in dfolder.glob('*.html')
                        if f.name != 'index.html')

    to_process = []
    for hf in html_files:
        if target_chapter and hf.name != target_chapter:
            continue
        count = ch_counts.get(hf.name, 0)
        if not force_all and not target_chapter and count >= THIN_THRESHOLD:
            continue
        to_process.append(hf)

    if not to_process:
        print(f"  {domain_code}: no chapters to process")
        return

    id_ctr = next_id_counter(domain_code, passages)
    total_added = 0

    for hf in to_process:
        old_count = ch_counts.get(hf.name, 0)
        new = extract_verbatim_passages(
            hf, domain_code, DOMAIN_NAMES[domain_code], existing_texts)
        for p in new:
            p['id'] = f"{domain_code}-{id_ctr:04d}"
            id_ctr += 1
            passages.append(p)
        total_added += len(new)
        new_count = old_count + len(new)
        print(f"  {hf.name}: {old_count} -> {new_count} (+{len(new)})")

    if total_added > 0:
        data['passages'] = passages
        data['total_passages'] = len(passages)
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding='utf-8')
        print(f"  OK {json_path.name}: {len(passages)} total (+{total_added} new)")
    else:
        print(f"  {domain_code}: 0 new passages found")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revert', action='store_true',
                        help='Trim all JSONs back to original passage counts')
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument('--domain', help='Single domain code (e.g. PETH)')
    grp.add_argument('--all-domains', action='store_true')
    parser.add_argument('--chapter',
                        help='Target a specific chapter (e.g. stimulants-adhd.html)')
    parser.add_argument('--all', action='store_true',
                        help='Process all chapters, not just thin ones')
    args = parser.parse_args()

    if args.domain and args.domain not in DOMAIN_NAMES:
        print(f"Unknown domain: {args.domain}. Valid: {', '.join(DOMAIN_NAMES)}")
        return

    domains = [args.domain] if args.domain else list(DOMAIN_NAMES.keys())

    if args.revert:
        print("Reverting to original passage counts...")
        for code in domains:
            revert_domain(code)
        print("Done.")
        return

    for code in domains:
        print(f"\n{code}:")
        process_domain(code, force_all=args.all, target_chapter=args.chapter)

    print("\nDone.")


if __name__ == '__main__':
    main()
