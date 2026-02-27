"""
build_spot_bundle.py

Reads all {DOMAIN}_spot.json files and writes data/spot_data.js —
a JavaScript file that sets window.__SPOT_DATA so the exercise and
settings pages can load question data without fetch/XHR (which are
blocked on file:// protocol in Firefox and some Chrome configs).

Run after any question generation:
  python build_spot_bundle.py
"""

import json, pathlib

DATA    = pathlib.Path("data")
DOMAINS = ["PMET","LDEV","CPAT","PTHE","SOCU","WDEV","BPSY","CASS","PETH"]

entries = []
for code in DOMAINS:
    src = DATA / f"{code}_spot.json"
    if src.exists():
        with open(src, encoding='utf-8') as f:
            data = json.load(f)
        entries.append(f'  "{code}": {json.dumps(data, ensure_ascii=False)}')
        print(f"  {code}: {len(data.get('questions', []))} questions")
    else:
        print(f"  {code}: not found, skipping")

dst = DATA / "spot_data.js"
with open(dst, 'w', encoding='utf-8') as f:
    f.write("window.__SPOT_DATA = {\n")
    f.write(",\n".join(entries))
    f.write("\n};\n")

print(f"\nWritten {dst} ({dst.stat().st_size:,} bytes)")
