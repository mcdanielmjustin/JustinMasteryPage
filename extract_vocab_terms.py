#!/usr/bin/env python3
"""
Extract all <span class="key-term"> text from every HTML chapter file
in content/domain1 through content/domain9.

Outputs vocab_terms.json with structure:
{
  "domain1/classical-conditioning": {
    "domain": "PMET",
    "chapter_title": "How Associations Form - Classical Conditioning",
    "terms": ["neutral stimulus", "unconditioned stimulus", ...]
  },
  ...
}
"""

import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path

CONTENT_DIR = Path(r"C:\Users\Admin\JustinMasteryPage\content")
OUTPUT_FILE = Path(r"C:\Users\Admin\vocab_terms.json")

DOMAIN_CODES = {
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


class KeyTermExtractor(HTMLParser):
    """Extract text from <span class="key-term"> and from <h1>/<title> tags."""

    def __init__(self):
        super().__init__()
        self.terms = []
        self._seen = set()
        self._in_key_term = False
        self._in_h1 = False
        self._in_title = False
        self._current_text = []
        self.h1_text = None
        self.title_text = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "span" and attrs_dict.get("class") == "key-term":
            self._in_key_term = True
            self._current_text = []
        elif tag == "h1" and self.h1_text is None:
            self._in_h1 = True
            self._current_text = []
        elif tag == "title" and self.title_text is None:
            self._in_title = True
            self._current_text = []

    def handle_endtag(self, tag):
        if tag == "span" and self._in_key_term:
            self._in_key_term = False
            term = " ".join("".join(self._current_text).split()).strip()
            if term:
                lower = term.lower()
                if lower not in self._seen:
                    self._seen.add(lower)
                    self.terms.append(term)
            self._current_text = []
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            self.h1_text = " ".join("".join(self._current_text).split()).strip()
            self._current_text = []
        elif tag == "title" and self._in_title:
            self._in_title = False
            self.title_text = " ".join("".join(self._current_text).split()).strip()
            self._current_text = []

    def handle_data(self, data):
        if self._in_key_term or self._in_h1 or self._in_title:
            self._current_text.append(data)


def extract_from_file(filepath):
    """Parse one HTML file, return (chapter_title, terms_list)."""
    parser = KeyTermExtractor()
    with open(filepath, "r", encoding="utf-8") as f:
        parser.feed(f.read())
    title = parser.h1_text or parser.title_text or ""
    # Clean title: strip trailing " | Domain N | MasteryPage" from <title> content
    title = re.sub(r"\s*\|.*$", "", title).strip()
    # Normalize em-dash
    title = title.replace("\u2014", " - ")
    return title, parser.terms


def main():
    result = {}
    domain_counts = {}
    zero_term_chapters = []
    total_terms = 0

    for domain_dir in sorted(CONTENT_DIR.iterdir()):
        if not domain_dir.is_dir() or not domain_dir.name.startswith("domain"):
            continue
        domain_name = domain_dir.name  # e.g. "domain1"
        if domain_name not in DOMAIN_CODES:
            continue
        code = DOMAIN_CODES[domain_name]
        count = 0

        html_files = sorted(domain_dir.glob("*.html"))
        for html_file in html_files:
            if html_file.name == "index.html":
                continue
            slug = html_file.stem  # filename without .html
            key = f"{domain_name}/{slug}"
            title, terms = extract_from_file(html_file)
            result[key] = {
                "domain": code,
                "chapter_title": title,
                "terms": terms,
            }
            n = len(terms)
            count += n
            total_terms += n
            if n == 0:
                zero_term_chapters.append(key)

        domain_counts[f"{domain_name} ({code})"] = count

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"Output written to: {OUTPUT_FILE}")
    print(f"Total chapters: {len(result)}")
    print(f"Total unique terms: {total_terms}")
    print()
    print("Per-domain counts:")
    for domain, cnt in domain_counts.items():
        print(f"  {domain}: {cnt}")
    print()
    if zero_term_chapters:
        print(f"Chapters with 0 terms ({len(zero_term_chapters)}):")
        for ch in zero_term_chapters:
            print(f"  {ch}")
    else:
        print("All chapters have at least 1 term.")


if __name__ == "__main__":
    main()
