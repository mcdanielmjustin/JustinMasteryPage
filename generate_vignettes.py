"""
generate_vignettes.py

Reads source questions from the PassEPPP question bank, calls Claude to generate
clinical vignette question sets (L1–L5), and appends to {DOMAIN}_vignettes.json.

Each source question produces 5 vignettes (one per difficulty level). Each vignette
has a unique scenario, difficulty-calibrated hint words, 4 MCQ options with per-option
explanations, and a correct answer.

Run:
  python generate_vignettes.py --domain CASS --count 50 --resume
  python generate_vignettes.py --domain CASS --resume
  python generate_vignettes.py --domain CASS --subdomains intelligence neuropsych

Options:
  --domain CODE         Domain to generate for (currently: CASS)
  --count N             Max source questions to process (default: all)
  --resume              Skip source questions already in the output file
  --subdomains S [S..]  Only process specific subdomain files (e.g. intelligence neuropsych)
  --api-key KEY         Anthropic API key (overrides env / .env)
"""

import json, pathlib, argparse, time, sys, os, re
import anthropic

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA       = pathlib.Path("data")
QUESTIONS  = pathlib.Path("../PassEPPP-website/content/questions")

# ── Domain → source files mapping ─────────────────────────────────────────────
# Only include files whose content genuinely belongs to the domain.
# EBT, supervision, and therapeutic-relationships files are omitted from CASS
# as they belong more to PTHE.
DOMAIN_FILES = {
    "CASS": [
        "domain-8-assessment-ethics.json",
        "domain-8-intelligence-cognitive.json",
        "domain-8-legal-forensic.json",
        "domain-8-neuropsych-screening.json",
        "domain-8-personality-assessment.json",
        "domain-8-test-score-interpretation.json",
        "domain-8-vocational-interest.json",
    ],
}

DOMAIN_NAMES = {
    "CASS": "Clinical Assessment & Interpretation",
}

LEGACY_CODES = {
    "CASS": ("CASS", "Clinical Assessment & Interpretation"),
}

LEVEL_LABELS = {
    1: "Easy",
    2: "Medium",
    3: "Hard",
    4: "Extremely Hard",
    5: "Almost Impossible",
}

# ── API key loader ─────────────────────────────────────────────────────────────
def load_api_key(args_key):
    if args_key:
        return args_key
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for p in [pathlib.Path(".env"), pathlib.Path.home() / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError(
        "No API key found.\n"
        "Set ANTHROPIC_API_KEY in your environment, create a .env file with\n"
        "  ANTHROPIC_API_KEY=sk-ant-...\n"
        "or pass --api-key sk-ant-..."
    )

# ── Load / save vignettes JSON ─────────────────────────────────────────────────
def load_vignettes(domain):
    path = DATA / f"{domain}_vignettes.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "domain_code":  domain,
        "domain_name":  DOMAIN_NAMES.get(domain, domain),
        "question_type": "vignette",
        "total": 0,
        "questions": [],
    }

def save_vignettes(domain, data):
    data["total"] = len(data["questions"])
    path = DATA / f"{domain}_vignettes.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _update_manifest(domain, data)

def _update_manifest(domain, data):
    """Keep data/vignette_stats.json current after each save."""
    manifest_path = DATA / "vignette_stats.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    except Exception:
        manifest = {}
    qs = data["questions"]
    anchors = len(set(q.get("source_question_id", "") for q in qs))
    manifest[domain] = {"anchors": anchors, "vignettes": len(qs)}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

# ── Load source questions ──────────────────────────────────────────────────────
def load_source_questions(domain, subdomain_filter=None):
    """Returns list of (source_question_id, subdomain, question_dict).
    Only includes question types that have a standard options array (single_choice,
    multiple_choice). Interactive types (matrix, bowtie, drag_drop, etc.) are skipped
    because they cannot be cleanly converted to vignette format.
    """
    SUPPORTED_TYPES = {"single_choice", "multiple_choice"}
    files = DOMAIN_FILES.get(domain, [])
    questions = []
    skipped = 0
    for fname in files:
        path = QUESTIONS / fname
        if not path.exists():
            print(f"  [WARN] Source file not found: {path}", file=sys.stderr)
            continue
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        subdomain = d["subdomain"]
        # Apply subdomain filter if set
        if subdomain_filter:
            key = subdomain.lower()
            if not any(filt.lower() in key for filt in subdomain_filter):
                continue
        for q in d["questions"]:
            if q.get("type") not in SUPPORTED_TYPES:
                skipped += 1
                continue
            questions.append((q["id"], subdomain, q))
    if skipped:
        print(f"  [INFO] Skipped {skipped} non-standard question type(s) (matrix/bowtie/drag-drop etc.)")
    return questions

# ── Check already-generated ────────────────────────────────────────────────────
def already_generated_ids(vignettes_data):
    """Return set of source_question_ids that already have all 5 levels.
    Partial sets (< 5 records) are removed from the data to allow clean regeneration."""
    counts = {}
    for q in vignettes_data["questions"]:
        sid = q.get("source_question_id", "")
        counts[sid] = counts.get(sid, 0) + 1

    partial = {sid for sid, n in counts.items() if 0 < n < 5}
    if partial:
        # Strip partial records so the anchor gets regenerated cleanly
        vignettes_data["questions"] = [
            q for q in vignettes_data["questions"]
            if q.get("source_question_id") not in partial
        ]
        print(f"  [INFO] Removed {len(partial)} partial anchor(s) for clean regeneration: {partial}")

    return {sid for sid, n in counts.items() if n >= 5}

# ── Next source ID ─────────────────────────────────────────────────────────────
def next_source_id(vignettes_data):
    """Return an integer one higher than the max numeric source_question_id."""
    max_n = 0
    for q in vignettes_data["questions"]:
        sid = q.get("source_question_id", "")
        # Accept PassEPPP-format IDs as-is (non-numeric); skip for max calc
        try:
            max_n = max(max_n, int(sid))
        except (ValueError, TypeError):
            pass
    return max_n + 1

# ── Claude prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert EPPP exam question writer. You generate clinical vignette \
multiple-choice questions for psychology licensing exam preparation.

Given a source question (stem, correct answer, explanation, tags), you generate \
exactly 5 vignette-based MCQ items — one per difficulty level (L1 through L5). \
Each item tests the SAME underlying knowledge point but in a progressively harder scenario.

DIFFICULTY LEVELS:
L1 Easy            — 3 hint words embedded naturally in the vignette. Clean textbook scenario. \
                     Correct answer is unmistakable once you identify the hint words.
L2 Medium          — 2 hint words. Mild clinical noise (comorbidities, extra context). \
                     Correct answer requires connecting the hints to the concept.
L3 Hard            — 1 hint word. Deliberate red herrings that make a plausible wrong answer \
                     seem tempting. Requires careful reasoning beyond surface-level recall.
L4 Extremely Hard  — 1 indirect hint (clinical behavior rather than terminology). \
                     Scenario is written to appear as though a wrong answer is correct.
L5 Almost Impossible — 0 hint words. Pure behavioral/observational description. \
                       All four answer choices are plausible. Only deep conceptual \
                       understanding distinguishes the correct answer.

ANSWER CHOICES:
- Always exactly 4 options (A, B, C, D). Only one is correct.
- Distractors must be conceptually adjacent (not obviously wrong). Each should be \
  something a test-taker with partial knowledge might reasonably choose.
- Each option must have an explanation (1–3 sentences) that explains WHY it is \
  correct or specifically why it is incorrect — not just "incorrect."

VIGNETTE REQUIREMENTS:
- Each level uses a DIFFERENT scenario (different patient, setting, context).
- Vignettes should be 100–220 words (longer for harder levels).
- Write in third-person clinical style (no bullet points, no headers).
- Do NOT use the exact source question stem as the vignette — transform it into a scenario.

OUTPUT FORMAT — respond with ONLY a valid JSON array of 5 objects, no preamble:
[
  {
    "difficulty_level": 1,
    "hint_words": ["word1", "word2", "word3"],
    "vignette": "...",
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "correct_answer": "B",
    "option_explanations": {"A": "...", "B": "...", "C": "...", "D": "..."}
  },
  ... (levels 2–5)
]
"""

def build_user_message(source_q, subdomain, domain_name):
    opts = source_q.get("options", [])
    correct_items = [o["text"] for o in opts if o.get("isCorrect")]
    # For multiple_choice, list all correct answers; for single_choice, just the one
    correct_text = "; ".join(correct_items) if correct_items else "(see explanation)"
    tags = ", ".join(source_q.get("tags", []))
    return (
        f"Domain: {domain_name}\n"
        f"Subdomain: {subdomain}\n\n"
        f"SOURCE QUESTION STEM:\n{source_q['stem']}\n\n"
        f"CORRECT ANSWER: {correct_text}\n\n"
        f"EXPLANATION: {source_q['explanation']}\n\n"
        f"TAGS: {tags}\n\n"
        "Generate the 5-level vignette set for this knowledge point."
    )

# ── Parse Claude response ──────────────────────────────────────────────────────
def parse_response(text):
    """Extract JSON array from Claude's response, tolerating minor formatting issues."""
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text.strip(), flags=re.MULTILINE)
    # Find first '[' to last ']'
    start = text.find("[")
    end   = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in response")
    return json.loads(text[start : end + 1])

# ── Build vignette records ─────────────────────────────────────────────────────
def build_records(items, source_id, source_q, subdomain, domain_code):
    legacy_code, legacy_name = LEGACY_CODES.get(domain_code, (domain_code, ""))
    # Derive a clean source summary from the explanation (first sentence)
    exp = source_q.get("explanation", "")
    summary = exp.split(".")[0].strip() + "." if exp else source_q["stem"][:120]

    records = []
    for item in items:
        lvl = item["difficulty_level"]
        vid = f"JQ-{domain_code}-{source_id}-vignette-L{lvl}"
        records.append({
            "id":                   vid,
            "source_question_id":   source_id,
            "source_summary":       summary,
            "domain_code":          domain_code,
            "domain_name":          DOMAIN_NAMES.get(domain_code, domain_code),
            "subdomain":            subdomain,
            "question_type":        "vignette",
            "difficulty_level":     lvl,
            "difficulty_label":     LEVEL_LABELS[lvl],
            "hint_words":           item.get("hint_words", []),
            "vignette":             item["vignette"],
            "question":             item["question"],
            "options":              item["options"],
            "correct_answer":       item["correct_answer"],
            "option_explanations":  item.get("option_explanations", {}),
            "legacy_domain_code":   legacy_code,
            "legacy_domain_name":   legacy_name,
        })
    return records

# ── Validate a parsed set ──────────────────────────────────────────────────────
def validate_items(items):
    if not isinstance(items, list) or len(items) != 5:
        raise ValueError(f"Expected 5 items, got {len(items) if isinstance(items, list) else type(items)}")
    levels = sorted(item.get("difficulty_level") for item in items)
    if levels != [1, 2, 3, 4, 5]:
        raise ValueError(f"Expected levels [1,2,3,4,5], got {levels}")
    for item in items:
        for field in ("vignette", "question", "options", "correct_answer"):
            if not item.get(field):
                raise ValueError(f"Missing field '{field}' in level {item.get('difficulty_level')}")
        if item["correct_answer"] not in item["options"]:
            raise ValueError(f"correct_answer '{item['correct_answer']}' not in options keys")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate clinical vignettes from PassEPPP question bank.")
    parser.add_argument("--domain",      required=True, help="Domain code, e.g. CASS")
    parser.add_argument("--count",       type=int, default=None, help="Max source questions to process")
    parser.add_argument("--resume",      action="store_true", help="Skip questions already in output file")
    parser.add_argument("--subdomains",  nargs="+", default=None, help="Filter by subdomain keyword(s)")
    parser.add_argument("--api-key",     default=None, help="Anthropic API key")
    args = parser.parse_args()

    domain = args.domain.upper()
    if domain not in DOMAIN_FILES:
        sys.exit(f"Unknown domain '{domain}'. Available: {list(DOMAIN_FILES.keys())}")

    api_key = load_api_key(args.api_key)
    client  = anthropic.Anthropic(api_key=api_key)

    # Load existing output
    vdata    = load_vignettes(domain)
    done_ids = already_generated_ids(vdata) if args.resume else set()
    next_id  = next_source_id(vdata)

    # Load source questions
    src_qs = load_source_questions(domain, args.subdomains)
    print(f"Source questions loaded: {len(src_qs)}")
    print(f"Already generated (resume): {len(done_ids)}")

    # Filter to unprocessed
    to_process = [
        (pid, sub, q) for pid, sub, q in src_qs
        if pid not in done_ids
    ]
    if args.count:
        to_process = to_process[:args.count]
    print(f"To process: {len(to_process)}\n")

    generated = 0
    errors    = 0

    for i, (passeppp_id, subdomain, source_q) in enumerate(to_process, 1):
        source_id = passeppp_id  # Use PassEPPP ID directly as source_question_id
        print(f"[{i}/{len(to_process)}] {source_id} | {subdomain[:45]}", end=" ... ", flush=True)

        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": build_user_message(source_q, subdomain, DOMAIN_NAMES.get(domain, domain))
                }],
            )
            raw = msg.content[0].text
            items = parse_response(raw)
            validate_items(items)
            # Sort by level
            items.sort(key=lambda x: x["difficulty_level"])
            records = build_records(items, source_id, source_q, subdomain, domain)
            vdata["questions"].extend(records)
            generated += 1
            print(f"OK ({len(records)} records)")

            # Save after every question to preserve progress
            save_vignettes(domain, vdata)

        except Exception as e:
            errors += 1
            print(f"ERROR: {e}")
            time.sleep(2)
            continue

        # Respect rate limits
        time.sleep(0.5)

    print(f"\nDone. Generated: {generated} anchors ({generated * 5} vignettes). Errors: {errors}")
    print(f"Total {domain} vignettes now: {len(vdata['questions'])}")

if __name__ == "__main__":
    main()
