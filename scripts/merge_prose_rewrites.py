"""
merge_prose_rewrites.py

Combines all prose_rewrites_*.json domain files (and the original
prose_rewrites.json from PMET pilot) into a single prose_rewrites.json
for injection.

Run:
  python scripts/merge_prose_rewrites.py
"""

import json, pathlib, sys

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"
OUTPUT = DATA_DIR / "prose_rewrites.json"


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    merged = {}  # keyed by file_path:heading_line to deduplicate

    for f in sorted(DATA_DIR.glob("prose_rewrites*.json")):
        records = json.loads(f.read_text(encoding="utf-8"))
        for r in records:
            key = f"{r['file_path']}:{r['heading_line']}"
            merged[key] = r
        print(f"  {f.name}: {len(records)} records")

    results = list(merged.values())
    OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nMerged {len(results)} total rewrites → {OUTPUT.name}")


if __name__ == "__main__":
    main()
