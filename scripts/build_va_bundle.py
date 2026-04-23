#!/usr/bin/env python3
"""
build_va_bundle.py — Build per-domain VA JS bundles from visual_aids_generated.json.

Reads:  mastery-page/scripts/data/visual_aids_generated.json
Writes: PassEPPP-website/js/va-data/domain{1-9}.js
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path

DOMAIN_MAP = {
    'PMET': 'domain1', 'LDEV': 'domain2', 'CPAT': 'domain3',
    'PTHE': 'domain4', 'SOCU': 'domain5', 'WDEV': 'domain6',
    'BPSY': 'domain7', 'CASS': 'domain8', 'PETH': 'domain9',
}

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR / 'data' / 'visual_aids_generated.json'
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / 'PassEPPP-website' / 'js' / 'va-data'

# Regex to strip comment markers
COMMENT_RE = re.compile(r'<!--\s*/?\s*visual-aid:[^\s]+\s*-->\n?')


def clean_html(html: str) -> str:
    """Strip visual-aid comment markers from HTML."""
    return COMMENT_RE.sub('', html).strip()


def build_bundles():
    with open(INPUT_FILE, encoding='utf-8') as f:
        entries = json.load(f)

    # Group by domain number
    by_domain = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        domain = DOMAIN_MAP.get(entry['domain_code'])
        if not domain:
            print(f"  WARNING: unknown domain_code '{entry['domain_code']}', skipping")
            continue
        # chapter key: "domain1/classical-conditioning" (strip .html)
        chapter_file = entry['chapter_file']
        chapter_key = chapter_file.replace('.html', '')
        by_domain[domain][chapter_key].append({
            'anchor': entry['anchor_heading'],
            'title': entry['title'],
            'html': clean_html(entry['html']),
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for domain in sorted(by_domain.keys()):
        chapters = by_domain[domain]
        # Build JS content
        lines = ['(function() {']
        lines.append('  if (!window.VA_DATA) window.VA_DATA = {};')

        for chapter_key in sorted(chapters.keys()):
            vas = chapters[chapter_key]
            json_str = json.dumps(vas, ensure_ascii=False)
            lines.append(f"  window.VA_DATA['{chapter_key}'] = {json_str};")
            total += len(vas)

        lines.append('})();')

        out_path = OUTPUT_DIR / f'{domain}.js'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

        count = sum(len(v) for v in chapters.values())
        print(f"  {domain}.js — {count} VAs across {len(chapters)} chapters")

    print(f"\nTotal: {total} visual aids bundled into {len(by_domain)} files")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == '__main__':
    build_bundles()
