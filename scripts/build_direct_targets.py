"""
build_direct_targets.py

Cross-references anchors_parsed.json + anchors_classified.json to build
a JSON list of 49 DIRECT-tier anchor points that are missing from the textbook.

These are anchors in subdomains explicitly named by ASPPB KN statements
that either: (a) were marked "covered" by the audit but have no anchor block,
or (b) had generated content that failed validation.

Output: scripts/data/direct_gap_targets.json

Run:
  python scripts/build_direct_targets.py
"""

import json, pathlib, sys

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
CLASSIFIED_FILE = DATA_DIR / "anchors_classified.json"
AUDIT_FILE = DATA_DIR / "coverage_audit.json"
OUTPUT_FILE = DATA_DIR / "direct_gap_targets.json"

# 54 (domain_num, anchor_id) pairs identified by the honest audit.
# These DIRECT-tier anchors are in subdomains explicitly named in ASPPB
# KN statements but have no <!-- anchor:XXX --> block in the textbook.
HONEST_AUDIT_TARGETS = [
    # Domain 1 — PMET (26 entries, 4 excluded below)
    (1, "217"), (1, "113"), (1, "094"), (1, "102"), (1, "068"),
    (1, "005-1"), (1, "016-1"), (1, "016-2"), (1, "027-1"), (1, "027-2"),
    (1, "038-1"), (1, "038-2"), (1, "049-1"), (1, "049-2"), (1, "073"),
    (1, "041-1"), (1, "041-2"), (1, "052"), (1, "092"), (1, "36"),
    (1, "026"), (1, "052"),       # second 052 = duplicate
    (1, "060-1"), (1, "060-2"), (1, "060-3"), (1, "104"),
    # Domain 5 — SOCU (14 entries)
    (5, "13"), (5, "113"), (5, "154"), (5, "28-1"), (5, "28-2"), (5, "28-3"),
    (5, "128"), (5, "173"), (5, "217"), (5, "24-3"), (5, "104"), (5, "14-1"),
    (5, "143"), (5, "4"),
    # Domain 6 — WDEV (5 entries)
    (6, "108"), (6, "122"), (6, "133"), (6, "14-1"), (6, "141"),
    # Domain 7 — BPSY (9 entries, 1 duplicate)
    (7, "129"), (7, "13-3"), (7, "136-1"), (7, "14-1"), (7, "158"),
    (7, "3"), (7, "12"), (7, "139"), (7, "14-1"),  # second 14-1 = duplicate
]

# 3 ineligible anchors (scenario_vignette / exam_strategy classification)
INELIGIBLE = {(1, "102"), (1, "005-1"), (1, "052")}


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    # Dedup and remove ineligible
    target_keys = list(set(HONEST_AUDIT_TARGETS) - INELIGIBLE)
    target_keys.sort()

    # Load classified data for metadata
    classified = json.loads(CLASSIFIED_FILE.read_text(encoding="utf-8"))
    classified_lookup = {}
    for a in classified:
        key = (a["domain_num"], a["anchor_id"])
        # Keep the first embed_eligible entry for each key
        if key not in classified_lookup or (
            not classified_lookup[key].get("embed_eligible")
            and a.get("embed_eligible")
        ):
            classified_lookup[key] = a

    # Load audit data for inject_after hints (some targets may have one)
    audit_lookup = {}
    if AUDIT_FILE.exists():
        audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
        for a in audit:
            key = (a["domain_num"], a["anchor_id"])
            if key not in audit_lookup:
                audit_lookup[key] = a

    # Build target list
    targets = []
    missing = []
    for dnum, aid in target_keys:
        key = (dnum, aid)
        if key not in classified_lookup:
            missing.append(f"[{aid}] d{dnum}")
            continue

        c = classified_lookup[key]
        au = audit_lookup.get(key, {})

        targets.append({
            "anchor_id": aid,
            "domain_num": dnum,
            "domain_code": c["domain_code"],
            "subdomain_name": c["subdomain_name"],
            "content": c["content"],
            "chapter_file": au.get("chapter_file") or c["chapter_file"],
            "coverage": "partial",
            "embed_eligible": True,
        })

    if missing:
        print(f"WARNING: {len(missing)} anchor(s) not found in classified data:")
        for m in missing:
            print(f"  {m}")

    OUTPUT_FILE.write_text(
        json.dumps(targets, indent=2, ensure_ascii=False), encoding="utf-8")

    # Summary
    by_domain = {}
    for t in targets:
        d = t["domain_code"]
        by_domain[d] = by_domain.get(d, 0) + 1

    print(f"DIRECT-tier gap targets: {len(targets)}")
    for code, count in sorted(by_domain.items()):
        print(f"  {code}: {count}")
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
