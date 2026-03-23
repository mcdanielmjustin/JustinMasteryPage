"""
scan_empty_h3.py

Scans all chapter HTML files for <h3> tags that are immediately followed by
<h4> tags with no introductory content (<p>, <ul>, <ol>, <table>, <div>)
between them.

Output: scripts/data/empty_h3_inventory.json

Run:
  python scripts/scan_empty_h3.py
"""

import json, pathlib, re
from html.parser import HTMLParser

CONTENT_DIR = pathlib.Path(__file__).resolve().parent.parent / "content"
OUTPUT = pathlib.Path(__file__).resolve().parent / "data" / "empty_h3_inventory.json"

DOMAIN_MAP = {
    "domain1": "PMET", "domain2": "LDEV", "domain3": "CPAT",
    "domain4": "PTHE", "domain5": "SOCU", "domain6": "WDEV",
    "domain7": "BPSY", "domain8": "CASS", "domain9": "PETH",
}

# Tags that count as "content" between h3 and h4
CONTENT_TAGS = {"p", "ul", "ol", "table", "div"}


class H3H4GapFinder(HTMLParser):
    """Finds h3 tags immediately followed by h4 with no content between."""

    def __init__(self, source_lines):
        super().__init__()
        self.source_lines = source_lines
        self.gaps = []

        # State tracking
        self._in_h3 = False
        self._h3_text = ""
        self._h3_line = 0
        self._awaiting_h4 = False  # True after we close an h3

        # For collecting h4 children of a gapped h3
        self._collecting_h4s = False
        self._current_gap = None
        self._in_h4 = False
        self._h4_text = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        line = self.getpos()[0]

        if tag == "h3":
            # Finalize any in-progress gap before resetting state
            if self._collecting_h4s and self._current_gap and self._current_gap["h4_children"]:
                self.gaps.append(self._current_gap)
            self._in_h3 = True
            self._h3_text = ""
            self._h3_line = line
            self._awaiting_h4 = False
            self._collecting_h4s = False
            self._current_gap = None
            return

        if self._awaiting_h4:
            if tag == "h4":
                # Found the gap! Start collecting h4 children
                self._collecting_h4s = True
                self._current_gap = {
                    "h3_text": self._h3_text.strip(),
                    "h3_line": self._h3_line,
                    "h4_children": [],
                }
                self._awaiting_h4 = False
                self._in_h4 = True
                self._h4_text = ""
            elif tag in CONTENT_TAGS:
                # Content tag found between h3 and h4 — no gap
                self._awaiting_h4 = False
            # Ignore whitespace-only text nodes — handled in handle_data

        elif self._collecting_h4s:
            if tag == "h4":
                self._in_h4 = True
                self._h4_text = ""
            elif tag in ("h2", "h3"):
                # New section — finalize current gap
                if self._current_gap and self._current_gap["h4_children"]:
                    self.gaps.append(self._current_gap)
                self._collecting_h4s = False
                self._current_gap = None
                if tag == "h3":
                    self._in_h3 = True
                    self._h3_text = ""
                    self._h3_line = line

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "h3" and self._in_h3:
            self._in_h3 = False
            self._awaiting_h4 = True
        elif tag == "h4" and self._in_h4:
            self._in_h4 = False
            if self._current_gap is not None:
                self._current_gap["h4_children"].append(self._h4_text.strip())

    def handle_data(self, data):
        if self._in_h3:
            self._h3_text += data
        elif self._in_h4:
            self._h4_text += data
        elif self._awaiting_h4 and data.strip():
            # Non-whitespace text between h3 and h4 → not a gap
            self._awaiting_h4 = False

    def finalize(self):
        """Call after feeding all data to capture any trailing gap."""
        if self._collecting_h4s and self._current_gap and self._current_gap["h4_children"]:
            self.gaps.append(self._current_gap)


def extract_chapter_title(html_text: str) -> str:
    """Extract <h1> text from HTML."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.DOTALL | re.IGNORECASE)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


def scan_all():
    inventory = []

    for domain_dir in sorted(CONTENT_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name not in DOMAIN_MAP:
            continue
        domain_code = DOMAIN_MAP[domain_dir.name]

        for html_file in sorted(domain_dir.glob("*.html")):
            text = html_file.read_text(encoding="utf-8")
            lines = text.splitlines()
            chapter_title = extract_chapter_title(text)

            parser = H3H4GapFinder(lines)
            parser.feed(text)
            parser.finalize()

            for gap in parser.gaps:
                inventory.append({
                    "domain_code": domain_code,
                    "domain_dir": domain_dir.name,
                    "chapter_file": html_file.name,
                    "chapter_title": chapter_title,
                    "h3_text": gap["h3_text"],
                    "h3_line": gap["h3_line"],
                    "h4_children": gap["h4_children"],
                    "file_path": str(html_file.relative_to(CONTENT_DIR.parent)),
                })

    return inventory


def main():
    import sys
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("Scanning for h3 -> h4 gaps (no intro content)...")
    inventory = scan_all()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nFound {len(inventory)} h3 → h4 gaps:")
    for i, item in enumerate(inventory, 1):
        print(f"  {i:2d}. {item['file_path']}:{item['h3_line']}  "
              f"\u201c{item['h3_text']}\u201d -> \u201c{item['h4_children'][0]}\u201d")

    print(f"\nInventory saved to {OUTPUT}")


if __name__ == "__main__":
    main()
