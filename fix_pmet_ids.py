"""
fix_pmet_ids.py

Fixes anchor ID collisions in PMET_vignettes.json.

Problem: 91 unique source_question_id values but 124 true anchors.
Different knowledge-point anchors were assigned the same numeric ID
with different zero-padding (e.g., '001', '01', '1' are 3 distinct anchors).

Fix: Group by (source_question_id, source_summary) to identify true anchors,
then assign sequential zero-padded 3-digit IDs ('001' through '124').
"""

import json, pathlib, sys

DATA = pathlib.Path("data")
PMET_FILE = DATA / "PMET_vignettes.json"
STATS_FILE = DATA / "vignette_stats.json"

def fix_pmet_ids(dry_run=False):
    with open(PMET_FILE, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    print(f"Total questions: {len(questions)}")

    # Group by (source_question_id, source_summary) preserving file order
    from collections import OrderedDict
    anchor_map = OrderedDict()
    for q in questions:
        key = (q.get("source_question_id", ""), q.get("source_summary", ""))
        if key not in anchor_map:
            anchor_map[key] = []
        anchor_map[key].append(q)

    print(f"True unique anchors: {len(anchor_map)}")

    # Validate all anchors have exactly 5 records
    bad = [(k, len(v)) for k, v in anchor_map.items() if len(v) != 5]
    if bad:
        print(f"ERROR: {len(bad)} anchors don't have exactly 5 records:")
        for k, n in bad:
            print(f"  {k}: {n} records")
        sys.exit(1)

    # Assign sequential zero-padded 3-digit IDs
    new_questions = []
    for new_idx, (key, records) in enumerate(anchor_map.items(), 1):
        new_sid = f"{new_idx:03d}"
        for q in records:
            old_sid = q["source_question_id"]
            lvl = q["difficulty_level"]
            # Determine legacy domain code from existing id
            old_id = q.get("id", "")
            # id format: JQ-{legacy_code}-{sid}-vignette-L{lvl}
            parts = old_id.split("-")
            legacy_code = parts[1] if len(parts) >= 4 else "PMET"
            new_id = f"JQ-{legacy_code}-{new_sid}-vignette-L{lvl}"
            q = dict(q)
            q["source_question_id"] = new_sid
            q["id"] = new_id
            new_questions.append(q)

    # Validate result
    unique_sids = set(q["source_question_id"] for q in new_questions)
    unique_ids = set(q["id"] for q in new_questions)
    print(f"After fix - unique source IDs: {len(unique_sids)}")
    print(f"After fix - total questions: {len(new_questions)}")
    print(f"After fix - unique vignette IDs: {len(unique_ids)}")
    print(f"Duplicate vignette IDs: {len(new_questions) - len(unique_ids)}")

    sid_counts = {}
    for q in new_questions:
        s = q["source_question_id"]
        sid_counts[s] = sid_counts.get(s, 0) + 1
    bad_counts = [s for s, n in sid_counts.items() if n != 5]
    print(f"IDs with != 5 records: {len(bad_counts)}")

    if dry_run:
        print("\n[DRY RUN] No files written.")
        return

    # Write fixed file
    data["questions"] = new_questions
    data["total"] = len(new_questions)
    with open(PMET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {PMET_FILE}")

    # Update manifest
    try:
        manifest = json.loads(STATS_FILE.read_text(encoding="utf-8")) if STATS_FILE.exists() else {}
    except Exception:
        manifest = {}
    manifest["PMET"] = {"anchors": len(unique_sids), "vignettes": len(new_questions)}
    STATS_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Updated {STATS_FILE}: PMET anchors={len(unique_sids)}, vignettes={len(new_questions)}")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    fix_pmet_ids(dry_run=dry_run)
