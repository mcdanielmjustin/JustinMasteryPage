"""
parse_anchors.py  (Phase 1)

Parse all 9 anchor-point txt files into structured JSON.
No API calls — pure text parsing.

Output: scripts/data/anchors_parsed.json

Run:
  python scripts/parse_anchors.py
"""

import json, pathlib, re, sys

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
ANCHOR_DIR = pathlib.Path("C:/Users/Admin/EPPP-Domain-Design/anchor_points_by_domain")

DOMAIN_CODE_MAP = {
    1: "PMET", 2: "LDEV", 3: "CPAT", 4: "PTHE",
    5: "SOCU", 6: "WDEV", 7: "BPSY", 8: "CASS", 9: "PETH",
}

EXPECTED_COUNTS = {
    1: 193, 2: 174, 3: 134, 4: 168,
    5: 153, 6: 172, 7: 192, 8: 190, 9: 191,
}

# Regex patterns
SECTION_RE = re.compile(r'^([A-Z]{2,}): (.+?) \((\d+) items?\)$')
ANCHOR_RE = re.compile(r'^\[([^\]]+)\]\s+(.*)')
DOMAIN_HEADER_RE = re.compile(r'^DOMAIN (\d+):')
TOTAL_RE = re.compile(r'^Total Anchor Points: (\d+)')


def find_domain_files():
    """Find all Domain_*.txt files, sorted by number."""
    files = sorted(ANCHOR_DIR.glob("Domain_*.txt"),
                   key=lambda p: int(re.search(r'Domain_(\d+)', p.name).group(1)))
    return files


def parse_domain_file(filepath):
    """Parse a single domain file into a list of anchor records."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    domain_num = int(re.search(r'Domain_(\d+)', filepath.name).group(1))
    domain_code = DOMAIN_CODE_MAP[domain_num]

    anchors = []
    current_subdomain_code = None
    current_subdomain_name = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip border lines
        if line.startswith("===") or line.startswith("---"):
            continue

        # Skip domain header and total lines
        if DOMAIN_HEADER_RE.match(line) or TOTAL_RE.match(line):
            continue

        # Check for section header
        section_match = SECTION_RE.match(line)
        if section_match:
            current_subdomain_code = section_match.group(1)
            current_subdomain_name = section_match.group(2)
            continue

        # Check for anchor point
        anchor_match = ANCHOR_RE.match(line)
        if anchor_match and current_subdomain_code:
            anchor_id = anchor_match.group(1)
            content = anchor_match.group(2).strip()
            anchors.append({
                "domain_num": domain_num,
                "domain_code": domain_code,
                "subdomain_code": current_subdomain_code,
                "subdomain_name": current_subdomain_name,
                "anchor_id": anchor_id,
                "content": content,
            })

    return anchors


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    files = find_domain_files()
    if len(files) != 9:
        print(f"ERROR: Expected 9 domain files, found {len(files)}")
        sys.exit(1)

    all_anchors = []
    errors = []

    print("Parsing anchor point files...\n")

    for filepath in files:
        anchors = parse_domain_file(filepath)
        domain_num = anchors[0]["domain_num"] if anchors else "?"
        domain_code = anchors[0]["domain_code"] if anchors else "?"

        expected = EXPECTED_COUNTS.get(domain_num, 0)
        actual = len(anchors)
        status = "OK" if actual == expected else f"MISMATCH (expected {expected})"

        if actual != expected:
            errors.append(f"Domain {domain_num} ({domain_code}): {actual} vs expected {expected}")

        print(f"  Domain {domain_num} ({domain_code}): {actual} anchors  [{status}]")

        # Show subdomain breakdown
        by_sub = {}
        for a in anchors:
            key = f"{a['subdomain_code']}: {a['subdomain_name']}"
            by_sub[key] = by_sub.get(key, 0) + 1
        for sub, count in by_sub.items():
            print(f"    {sub}: {count}")

        all_anchors.extend(anchors)

    total = len(all_anchors)
    print(f"\nTotal: {total} anchor points")

    if total != 1567:
        errors.append(f"Total: {total} vs expected 1567")

    if errors:
        print(f"\nWARNINGS:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All counts match expected values.")

    # Save
    output_file = DATA_DIR / "anchors_parsed.json"
    output_file.write_text(
        json.dumps(all_anchors, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
