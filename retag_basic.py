"""
retag_basic.py
Reads the 11 old-domain basic question files from JustinQuestionsDatabase,
remaps them to the 9 new EPPP domain codes, and writes per-domain JSON files
to mastery-page/data/ as {CODE}_basic.json.

Domain mapping (same logic as retag_questions.py):
  Simple 1:1
    ETH → PETH
    LIF → LDEV
    ORG → WDEV
    PHY → BPSY
    PPA → CPAT
    RMS → PMET
    SOC → SOCU
    PAS → CASS

  Split by subdomain
    CLI:
      Cross-Cultural* → SOCU
      everything else → PTHE
    LEA:
      Memory*          → BPSY
      Classical/Operant Conditioning (non-intervention) → PMET
      Interventions*   → PTHE
    TES:
      Test Score Interpretation → CASS
      everything else  → PMET
"""

import json, os, pathlib

SRC = pathlib.Path(r"C:\Users\mcdan\JustinQuestionsDatabase\data\domains")
DST = pathlib.Path(r"C:\Users\mcdan\mastery-page\data")
DST.mkdir(parents=True, exist_ok=True)

NEW_DOMAIN_NAMES = {
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

# Simple 1:1 mappings
SIMPLE = {
    "ETH": "PETH",
    "LIF": "LDEV",
    "ORG": "WDEV",
    "PHY": "BPSY",
    "PPA": "CPAT",
    "RMS": "PMET",
    "SOC": "SOCU",
    "PAS": "CASS",
}

def map_question(q, legacy_code, legacy_name):
    """Return (new_domain_code, question_dict_with_tags)."""
    subdomain = q.get("subdomain", "")
    sub_lower = subdomain.lower()

    if legacy_code in SIMPLE:
        new_code = SIMPLE[legacy_code]
    elif legacy_code == "CLI":
        if "cross-cultural" in sub_lower:
            new_code = "SOCU"
        else:
            new_code = "PTHE"
    elif legacy_code == "LEA":
        if "memory" in sub_lower:
            new_code = "BPSY"
        elif "intervention" in sub_lower:
            new_code = "PTHE"
        else:
            new_code = "PMET"  # Classical/Operant Conditioning (pure theory)
    elif legacy_code == "TES":
        if "score interpretation" in sub_lower:
            new_code = "CASS"
        else:
            new_code = "PMET"  # Item Analysis, Reliability, Validity
    else:
        raise ValueError(f"Unknown legacy code: {legacy_code}")

    tagged = dict(q)
    tagged["domain_code"]        = new_code
    tagged["domain_name"]        = NEW_DOMAIN_NAMES[new_code]
    tagged["legacy_domain_code"] = legacy_code
    tagged["legacy_domain_name"] = legacy_name
    return new_code, tagged

# ── Load and remap all questions ──────────────────────────────────────────────
buckets = {code: [] for code in NEW_DOMAIN_NAMES}

for fname in sorted(SRC.glob("*.json")):
    old_code = fname.stem  # e.g. "CLI"
    try:
        with open(fname, encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(fname, encoding="utf-8-sig") as f:
            data = json.load(f)

    legacy_name = data.get("domain_name", old_code)
    questions   = data.get("questions", [])
    print(f"  {old_code}: {len(questions)} questions")

    for q in questions:
        new_code, tagged = map_question(q, old_code, legacy_name)
        buckets[new_code].append(tagged)

# ── Write per-domain output files ─────────────────────────────────────────────
total = 0
print("\nOutput:")
for code, questions in buckets.items():
    out = {
        "domain_code":  code,
        "domain_name":  NEW_DOMAIN_NAMES[code],
        "total_questions": len(questions),
        "questions":    questions,
    }
    path = DST / f"{code}_basic.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    total += len(questions)
    print(f"  {code}_basic.json  {len(questions)} questions")

print(f"\nTotal: {total} questions written to {DST}")
