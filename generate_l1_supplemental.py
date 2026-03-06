"""
generate_l1_supplemental.py

Generates additional Level 1 (Foundational) patient encounters for all 9 domains,
grounded in anchor-point content summaries from the JustinQuestionsDatabase.

Target: 12 L1 encounters per domain (currently 5 each → adds 7 per domain = 63 total).

Usage:
  python generate_l1_supplemental.py                    # all domains
  python generate_l1_supplemental.py --domain CPAT      # single domain
  python generate_l1_supplemental.py --preview          # dry-run first batch
  python generate_l1_supplemental.py --target 15        # override per-domain target
"""

import json, pathlib, argparse, time, random, sys, os, re
from datetime import datetime, timezone
from collections import defaultdict
import anthropic

# ─── Paths ────────────────────────────────────────────────────────────────────

DATA   = pathlib.Path("data")
JQD    = pathlib.Path("C:/Users/mcdan/JustinQuestionsDatabase/data/domains")

# ─── Domain definitions (copied from main generator) ──────────────────────────

DOMAIN_NAMES = {
    "PMET": "Psychometrics & Research Methods",
    "LDEV": "Lifespan & Developmental Stages",
    "CPAT": "Clinical Psychopathology (DSM-5-TR)",
    "PTHE": "Psychotherapy Models, Interventions & Prevention",
    "SOCU": "Social & Cultural Psychology",
    "WDEV": "Workforce Development & Leadership",
    "BPSY": "Biopsychology",
    "CASS": "Clinical Assessment & Interpretation",
    "PETH": "Psychopharmacology & Ethics",
}

DOMAIN_SUBDOMAINS = {
    "CPAT": ["Mood Disorders","Anxiety Disorders","Psychotic Disorders",
             "Trauma- and Stressor-Related Disorders","Personality Disorders",
             "Neurodevelopmental Disorders","Substance Use Disorders",
             "Somatic Symptom and Related Disorders","Eating and Feeding Disorders"],
    "PTHE": ["Cognitive-Behavioral Therapy","Psychodynamic and Psychoanalytic Approaches",
             "Humanistic and Person-Centered Therapy","Family Systems Therapy",
             "Dialectical Behavior Therapy","Acceptance and Commitment Therapy",
             "Motivational Interviewing","Group Therapy","Crisis Intervention"],
    "BPSY": ["Neurotransmitter Systems","Psychopharmacology","Brain Structures and Functions",
             "Genetics and Epigenetics","Endocrine and Immune Interactions",
             "Sleep Physiology","Psychophysiology","Substance Neurobiology"],
    "PMET": ["Reliability","Validity","Standardization and Norms",
             "Norm-Referenced vs. Criterion-Referenced Assessment","Test Bias and Fairness",
             "Statistical Concepts in Measurement","Item Analysis",
             "Diagnostic Accuracy and Decision Theory"],
    "LDEV": ["Infancy and Toddlerhood","Early Childhood","Middle Childhood","Adolescence",
             "Early Adulthood","Middle Adulthood","Late Adulthood",
             "Cognitive Development Across the Lifespan","Social-Emotional Development",
             "Attachment Theory and Patterns"],
    "SOCU": ["Cultural Competence and Multicultural Practice","Health Disparities and Social Determinants",
             "Group Dynamics and Social Influence","Attitudes, Attribution, and Stereotyping",
             "Conformity, Obedience, and Persuasion","Community Psychology",
             "Rural and Underserved Populations","Immigration and Acculturation"],
    "WDEV": ["Supervision Models and Processes","Consultation","Professional Development and Competence",
             "Organizational Behavior","Work Motivation and Job Satisfaction",
             "Leadership and Management","Team Dynamics","Burnout, Self-Care, and Wellness"],
    "CASS": ["Clinical Interview Techniques","Intelligence and Cognitive Testing",
             "Personality Assessment","Behavioral Assessment","Neuropsychological Assessment",
             "Risk Assessment","Diagnostic Formulation","Cultural Considerations in Assessment"],
    "PETH": ["Informed Consent","Confidentiality and Privilege","Dual Relationships and Boundaries",
             "Competence and Scope of Practice","APA Ethics Code Application",
             "Mandatory Reporting","Termination and Abandonment",
             "Documentation and Record-Keeping","Telehealth Ethics","Supervision Ethics"],
}

AVATAR_EMOTIONS = [
    "idle","speaking","flat_affect","distressed",
    "tearful","anxious","agitated","guarded","hopeful","confused",
]

QUESTION_TYPES = [
    "primary_diagnosis","differential_diagnosis","immediate_intervention",
    "treatment_planning","risk_assessment","dsm_criteria",
    "cultural_consideration","assessment_tool",
]

# Remap model-invented near-miss types to the nearest valid type
TYPE_ALIASES = {
    "conceptual_knowledge":     "dsm_criteria",
    "conceptual_understanding": "dsm_criteria",
    "developmental_milestone":  "dsm_criteria",
    "developmental_stage":      "dsm_criteria",
    "psychopharmacology":      "treatment_planning",
    "pharmacology":            "treatment_planning",
    "diagnosis":               "primary_diagnosis",
    "diagnosis_selection":     "primary_diagnosis",
    "ethical_dilemma":         "treatment_planning",
    "ethical_decision":        "treatment_planning",
    "ethics_application":      "treatment_planning",
    "case_conceptualization":  "differential_diagnosis",
    "intervention_selection":  "immediate_intervention",
    "clinical_intervention":   "immediate_intervention",
}

CHART_CATEGORIES = [
    "Chief Complaint","History of Present Illness","Mental Status Examination",
    "Psychosocial History","Collateral / Context","Labs / Observations",
]

# ─── JQD Domain Mapping ────────────────────────────────────────────────────────
# Maps mastery domain codes → JQD domain file codes to source anchor content

JQD_DOMAIN_MAP = {
    "CPAT": ["PPA", "CLI"],          # Psychopathology + Clinical
    "PMET": ["RMS", "TES"],          # Research Methods + Testing & Measurement
    "BPSY": ["PHY"],                 # Biological/Physiological
    "LDEV": ["LIF"],                 # Lifespan Development
    "SOCU": ["SOC"],                 # Social Psychology
    "WDEV": ["ORG"],                 # Industrial/Organizational
    "CASS": ["PAS", "TES"],          # Psychological Assessment + Testing
    "PETH": ["ETH"],                 # Ethics
    "PTHE": ["CLI", "LEA"],          # Clinical + Learning (therapy models rooted in learning theory)
}

# ─── Domain-specific framing (L1 version) ─────────────────────────────────────

DOMAIN_FRAMING_L1 = {
    "PMET": """Domain framing — Psychometrics & Research Methods (Level 1 — Foundational):
These are assessment or intake referral sessions. The patient is presenting for testing.
At L1, the psychometric concepts should appear clearly and directly in the scenario.
The anchor concept must be clearly testable — e.g., a clinician choosing a test for a
stated reason, or a patient questioning test results in a way that surfaces a reliability concept.
Questions should test direct recall: test selection, interpreting basic scores, recognizing
what a reliability coefficient means in practice.""",

    "LDEV": """Domain framing — Lifespan Development (Level 1 — Foundational):
Patient age MUST match the subdomain's developmental stage.
At L1, the developmental concept should be clearly illustrated by the patient's presentation.
The anchor concept (e.g., attachment pattern, milestone delay, temperament-fit) should be
directly observable in the dialogue. Questions test direct recognition of the concept.""",

    "SOCU": """Domain framing — Social & Cultural Psychology (Level 1 — Foundational):
Cultural identity and systemic factors must be surfaced explicitly.
At L1, the cultural or social concept should be textbook-clear. The clinician's appropriate
response to cultural context should be unambiguous. Questions test recognition of culturally
competent practice principles.""",

    "WDEV": """Domain framing — Workforce Development & Leadership (Level 1 — Foundational):
These are supervision sessions, organizational consultations, or professional development scenarios.
At L1, the supervisory or organizational concept should be clearly illustrated.
The anchor concept (burnout sign, supervision model, leadership behavior) should be
directly observable. Questions test direct recognition of the concept.""",

    "CASS": """Domain framing — Clinical Assessment & Interpretation (Level 1 — Foundational):
Encounters are assessment sessions. At L1, test selection rationale or interpretation of
results should be straightforward. The anchor concept (validity of a specific instrument,
appropriate use of a test) should be clearly illustrated. Questions test direct recall.""",

    "PETH": """Domain framing — Psychopharmacology & Ethics (Level 1 — Foundational):
Ethics encounters: clear ethical dilemma with a textbook-correct resolution (no genuine
ambiguity at L1). Psychopharmacology: patient presenting with a common medication scenario
where the correct clinical response is unambiguous. Questions test direct APA code recall
or medication mechanism knowledge.""",
}

# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) \
content author. You generate Level 1 (Foundational) clinical patient encounter scenarios for an \
interactive licensure exam preparation tool called "Patient Encounter."

## Level 1 — Foundational Definition
Level 1 encounters present clean, textbook-level clinical pictures where:
- The primary diagnosis or clinical concept is discernible by Phase 2 of 3
- Behavioral tags and chart reveals explicitly support the anchor concept
- The patient dialogue is authentic and colloquial — NOT a DSM checklist recitation
- Distractors in questions are plausible but clearly distinguishable from the correct answer
- The encounter teaches a fundamental EPPP concept through immersive simulation

## Your Task
Generate clinical patient encounter objects as a valid JSON array. Each encounter MUST have
difficulty_level: 1 and must be grounded in the anchor concept(s) provided in the user message.

## Core Principles
- The anchor concept must be the clinical core of the encounter — testable through both phases and questions
- Patient dialogue must sound authentic — conversational, emotionally genuine, and colloquial
- Each encounter must stand alone — no references to "previous sessions" unless part of the case context
- All patient names must be initials only (e.g., "J.T.") or omitted; never full names
- At Level 1, diagnostic clarity should emerge naturally by the third phase

## Required JSON Schema

Output a JSON array of exactly the number of objects specified. Each object MUST follow:

{
  "id": "CP-{DOMAIN}-{NNNN}",
  "domain_code": "{DOMAIN}",
  "subdomain": "...",
  "difficulty_level": 1,
  "encounter": {
    "setting": "...",
    "referral_context": "...",
    "patient": {
      "label": "Adult Male, 52" (or Female, Adolescent, Child — include age),
      "appearance_tags": ["..."] (1–3 brief physical/presentation descriptors),
      "initial_avatar_state": one of: idle | speaking | flat_affect | distressed | tearful | anxious | agitated | guarded | hopeful | confused
    },
    "phases": [
      {
        "phase_id": "chief_complaint" | "history" | "mse" | "psychosocial" | "collateral" | "additional",
        "phase_label": "Chief Complaint",
        "dialogue": "Patient's spoken words",
        "avatar_emotion": one of the 10 allowed values,
        "behavioral_tags": ["..."] (0–4 brief observational tags),
        "chart_reveals": [
          {
            "category": one of: "Chief Complaint" | "History of Present Illness" | "Mental Status Examination" | "Psychosocial History" | "Collateral / Context" | "Labs / Observations",
            "label": "brief label",
            "value": "brief value"
          }
        ],
        "clinician_prompt": null or "Brief therapist question/probe"
      }
    ]
  },
  "questions": [
    {
      "question_id": "q1",
      "type": one of the 8 allowed types,
      "prompt": "Clinical question stem (1–2 sentences)",
      "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct_answer": "A" | "B" | "C" | "D",
      "explanation": "Full explanation of correct answer (2–4 sentences). May use <strong> for key terms and <em> for clinical terms.",
      "distractor_rationale": { "B": "...", "C": "...", "D": "..." }
    }
  ]
}

## Phase Guidelines
- Exactly 3 phases per encounter (chief_complaint, history, mse or psychosocial)
- Phase IDs must be unique within the encounter
- Each phase must have at least 1 chart_reveal item
- avatar_emotion should change meaningfully across phases

## Question Guidelines
- Exactly 2 questions per encounter at L1
- correct_answer balanced across A/B/C/D across the batch
- distractor_rationale must explain why each wrong option is wrong; omit the correct answer key
- Options must be clinically plausible, not obviously wrong

## Strict Validation Rules
- difficulty_level MUST be 1 for every encounter
- avatar_emotion must be one of exactly 10 allowed values
- question type must be one of exactly 8 allowed values
- chart_reveals category must be one of exactly 6 allowed strings
- correct_answer must be A/B/C/D and exist in options
- distractor_rationale must NOT include the correct_answer key
- All string values must be properly JSON-escaped

## Output Format
Respond with ONLY a valid JSON array. No markdown. No commentary. Start with [ and end with ]."""


# ─── Anchor Loading ────────────────────────────────────────────────────────────

def load_anchors(mastery_domain: str) -> dict[str, list[str]]:
    """
    Load unique source_summary strings from JQD domain files.
    Returns { subdomain_keyword: [summary, ...] } for loose matching,
    plus a flat list under key '_all'.
    """
    jqd_codes = JQD_DOMAIN_MAP.get(mastery_domain, [])
    all_summaries: list[str] = []
    by_subdomain: dict[str, list[str]] = defaultdict(list)

    for code in jqd_codes:
        fpath = JQD / f"{code}.json"
        if not fpath.exists():
            print(f"  [anchor] WARNING: {fpath} not found — skipping")
            continue
        data = json.load(open(fpath, encoding="utf-8"))
        seen = set()
        for q in data.get("questions", []):
            summary = q.get("source_summary", "").strip()
            subdomain = q.get("subdomain", "").strip()
            if summary and summary not in seen:
                seen.add(summary)
                all_summaries.append(summary)
                by_subdomain[subdomain].append(summary)

    by_subdomain["_all"] = all_summaries
    return by_subdomain


def pick_anchors(anchors: dict[str, list[str]], subdomain: str, n: int = 4) -> list[str]:
    """Pick n anchor summaries, preferring ones that match the subdomain keyword."""
    # Try loose keyword match on JQD subdomain names
    subdomain_lower = subdomain.lower()
    candidates: list[str] = []

    for jqd_sub, summaries in anchors.items():
        if jqd_sub == "_all":
            continue
        # Check for word overlap
        jqd_words = set(jqd_sub.lower().split())
        mastery_words = set(subdomain_lower.split())
        if jqd_words & mastery_words:
            candidates.extend(summaries)

    if len(candidates) < n:
        # Fall back to all anchors
        candidates = anchors.get("_all", [])

    if not candidates:
        return []

    return random.sample(candidates, min(n, len(candidates)))


# ─── Helpers (from main generator) ───────────────────────────────────────────

def load_api_key(args_key=None) -> str:
    if args_key:
        return args_key
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    for p in [pathlib.Path(".env"), pathlib.Path.home() / ".env",
              pathlib.Path("C:/Users/mcdan/JustinQuestionsDatabase/api_key.txt")]:
        if p.exists():
            text = p.read_text().strip()
            if text.startswith("sk-"):
                return text
            for line in text.splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or pass --api-key.")


def extract_json_array(text: str) -> list:
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array found in response")
    depth = 0; in_string = False; escape = False
    for i, ch in enumerate(text[start:], start):
        if escape: escape = False; continue
        if ch == "\\" and in_string: escape = True; continue
        if ch == '"': in_string = not in_string; continue
        if in_string: continue
        if ch == "[": depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i+1])
    raise ValueError("No complete JSON array found")


def validate_encounter(enc: dict, domain_code: str) -> list[str]:
    errors = []
    for field in ("id","domain_code","subdomain","difficulty_level","encounter","questions"):
        if field not in enc:
            errors.append(f"Missing: {field}")
    if errors: return errors

    if not re.match(rf"^CP-{domain_code}-\d{{4}}$", enc.get("id","")):
        errors.append(f"id format wrong: {enc.get('id')}")
    if enc.get("difficulty_level") != 1:
        errors.append(f"difficulty_level must be 1, got {enc.get('difficulty_level')}")

    enc_data = enc.get("encounter", {})
    patient = enc_data.get("patient", {})
    if patient.get("initial_avatar_state","") not in AVATAR_EMOTIONS:
        errors.append(f"bad avatar state: {patient.get('initial_avatar_state')}")

    phases = enc_data.get("phases", [])
    if not isinstance(phases, list) or not (3 <= len(phases) <= 5):
        errors.append(f"phases count must be 3-5, got {len(phases) if isinstance(phases,list) else '?'}")
    else:
        seen_ids = set()
        for pi, phase in enumerate(phases):
            pid = phase.get("phase_id","")
            if pid in seen_ids: errors.append(f"duplicate phase_id {pid}")
            seen_ids.add(pid)
            if phase.get("avatar_emotion","") not in AVATAR_EMOTIONS:
                errors.append(f"phase[{pi}] bad emotion: {phase.get('avatar_emotion')}")
            reveals = phase.get("chart_reveals",[])
            if not reveals: errors.append(f"phase[{pi}] empty chart_reveals")
            for ri, rev in enumerate(reveals):
                if rev.get("category","") not in CHART_CATEGORIES:
                    errors.append(f"phase[{pi}].reveals[{ri}] bad category: {rev.get('category')}")

    questions = enc.get("questions", [])
    if not isinstance(questions, list) or not (1 <= len(questions) <= 2):
        errors.append(f"questions count must be 1-2, got {len(questions) if isinstance(questions,list) else '?'}")
    else:
        for qi, q in enumerate(questions):
            # Normalize near-miss type names before validation
            raw_type = q.get("type", "")
            if raw_type not in QUESTION_TYPES and raw_type in TYPE_ALIASES:
                q["type"] = TYPE_ALIASES[raw_type]
            if q.get("type","") not in QUESTION_TYPES:
                errors.append(f"q[{qi}] bad type: {q.get('type')}")
            opts = q.get("options",{})
            if set(opts.keys()) != {"A","B","C","D"}:
                errors.append(f"q[{qi}] options must have A,B,C,D")
            ca = q.get("correct_answer","")
            if ca not in ("A","B","C","D"):
                errors.append(f"q[{qi}] correct_answer must be A-D, got {ca}")
            dr = q.get("distractor_rationale",{})
            if isinstance(dr,dict) and ca in dr:
                errors.append(f"q[{qi}] distractor_rationale must not include correct answer {ca}")
    return errors


# ─── Batch Prompt ─────────────────────────────────────────────────────────────

def build_l1_prompt(
    domain_code: str,
    subdomains: list[str],
    anchor_summaries: list[str],
    required_emotions: list[str],
    required_q_types: list[str],
    start_id: int,
    batch_size: int,
) -> str:
    domain_name = DOMAIN_NAMES[domain_code]
    subdomain_str = " and ".join(f'"{s}"' for s in subdomains)
    emotion_str = ", ".join(required_emotions)
    qtype_str = ", ".join(required_q_types)
    id_examples = ", ".join(
        f"CP-{domain_code}-{str(start_id+i).zfill(4)}" for i in range(batch_size)
    )
    framing = DOMAIN_FRAMING_L1.get(domain_code, "")

    anchor_block = ""
    if anchor_summaries:
        lines = "\n".join(f"  - {s}" for s in anchor_summaries)
        anchor_block = f"""
Anchor concepts (from EPPP exam content — ground at least {min(2, len(anchor_summaries))} \
of your encounters in these):
{lines}

Each anchor concept you use should be the clinical core of the encounter: it must appear
naturally in the patient dialogue, surface in chart reveals, and be directly tested by
at least one question. The explanation field must reference the anchor concept by name.
"""

    return f"""Generate exactly {batch_size} Level 1 (Foundational) patient encounter objects.

Domain: {domain_code} — {domain_name}
Subdomains to cover: {subdomain_str}
ALL encounters must have difficulty_level: 1

Required constraints:
  - Avatar emotions to include (at least once each): {emotion_str}
  - Question types to include (at least once each): {qtype_str}
  - IDs to use (in order): {id_examples}
  - Each encounter must be set in a different clinical setting
  - Exactly 3 phases per encounter
  - Exactly 2 questions per encounter
{anchor_block}
{framing}

Return a JSON array of exactly {batch_size} encounter objects. No extra text."""


# ─── Generation ───────────────────────────────────────────────────────────────

def generate_batch(
    client: anthropic.Anthropic,
    domain_code: str,
    subdomains: list[str],
    anchors: dict,
    required_emotions: list[str],
    required_q_types: list[str],
    start_id: int,
    batch_size: int,
    retries: int = 3,
) -> list[dict]:
    anchor_summaries = pick_anchors(anchors, subdomains[0], n=4)
    prompt = build_l1_prompt(
        domain_code, subdomains, anchor_summaries,
        required_emotions, required_q_types, start_id, batch_size
    )

    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            batch = extract_json_array(raw)

            valid = []
            for i, enc in enumerate(batch):
                errs = validate_encounter(enc, domain_code)
                if errs:
                    print(f"\n    [enc {i+1}] INVALID: {'; '.join(errs[:3])}")
                else:
                    valid.append(enc)

            if valid:
                return valid
            raise ValueError("No valid encounters after validation")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"\n    Parse error (attempt {attempt+1}): {e}")
            if attempt < retries - 1: time.sleep(3)
        except anthropic.RateLimitError:
            wait = 20 * (attempt + 1)
            print(f"\n    Rate limit — waiting {wait}s...")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            print(f"\n    API error (attempt {attempt+1}): {e.status_code} {e.message}")
            if attempt < retries - 1: time.sleep(5)
        except Exception as e:
            print(f"\n    Error (attempt {attempt+1}): {e}")
            if attempt < retries - 1: time.sleep(3)

    return []


def load_existing(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"encounters": []}
    return json.load(open(path, encoding="utf-8"))


def write_file(path: pathlib.Path, domain_code: str, encounters: list[dict]) -> None:
    out = {
        "domain_code": domain_code,
        "domain_name": DOMAIN_NAMES[domain_code],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "total_encounters": len(encounters),
        "encounters": encounters,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def process_domain(
    client: anthropic.Anthropic,
    domain_code: str,
    l1_target: int,
    preview: bool,
) -> None:
    dst = DATA / f"{domain_code}_presentations.json"
    existing_data = load_existing(dst)
    all_encounters = list(existing_data.get("encounters", []))

    # Count current L1
    current_l1 = [e for e in all_encounters if e.get("difficulty_level") == 1]
    need = max(0, l1_target - len(current_l1))

    if need == 0:
        print(f"  {domain_code}: already has {len(current_l1)} L1 encounters (target {l1_target}) — skip")
        return

    print(f"\n  {domain_code}: {len(current_l1)} L1 -> target {l1_target} (+{need} needed)")

    # Next available ID
    id_nums = [int(m.group(1)) for e in all_encounters
               if (m := re.search(r"-(\d{4})$", e.get("id","")))]
    next_id = max(id_nums, default=0) + 1
    existing_ids = {e["id"] for e in all_encounters}

    # Load anchor summaries from JQD
    anchors = load_anchors(domain_code)
    print(f"    Loaded {len(anchors.get('_all',[]))} unique anchor summaries from JQD")

    subdomains = DOMAIN_SUBDOMAINS[domain_code]
    subdomain_idx = 0
    emotion_pool = list(AVATAR_EMOTIONS)
    qtype_pool = list(QUESTION_TYPES)
    random.shuffle(emotion_pool)
    random.shuffle(qtype_pool)
    emotion_idx = 0; qtype_idx = 0

    batch_size = 3
    batches_needed = (need + batch_size - 1) // batch_size
    total_new = 0

    for batch_num in range(batches_needed):
        remaining = need - total_new
        this_batch = min(batch_size, remaining)
        if this_batch <= 0: break

        batch_subdomains = [
            subdomains[subdomain_idx % len(subdomains)],
            subdomains[(subdomain_idx + 1) % len(subdomains)],
        ]
        subdomain_idx += 2

        batch_emotions = [
            emotion_pool[emotion_idx % len(emotion_pool)],
            emotion_pool[(emotion_idx + 1) % len(emotion_pool)],
        ]
        emotion_idx += 2

        batch_qtypes = [
            qtype_pool[qtype_idx % len(qtype_pool)],
            qtype_pool[(qtype_idx + 1) % len(qtype_pool)],
        ]
        qtype_idx += 2

        print(f"    Batch {batch_num+1}/{batches_needed}: "
              f"subdomains={batch_subdomains}, id_start={next_id}...",
              end=" ", flush=True)

        result = generate_batch(
            client, domain_code, batch_subdomains, anchors,
            batch_emotions, batch_qtypes, next_id, this_batch,
        )

        if result:
            new_encs = []
            for enc in result:
                if enc["id"] not in existing_ids:
                    existing_ids.add(enc["id"])
                    new_encs.append(enc)
                    next_id = max(next_id, int(enc["id"].split("-")[-1]) + 1)
            all_encounters.extend(new_encs)
            total_new += len(new_encs)
            print(f"OK ({len(new_encs)} valid)")

            if preview:
                print("\n--- PREVIEW: First generated encounter ---")
                print(json.dumps(result[0], indent=2, ensure_ascii=False)[:1200])
                print("--- END PREVIEW ---")
                return

            write_file(dst, domain_code, all_encounters)
        else:
            print("FAILED")

        time.sleep(1.0)

    # Final L1 count
    final_l1 = sum(1 for e in all_encounters if e.get("difficulty_level") == 1)
    print(f"\n  {domain_code} done: {final_l1} L1 encounters total ({total_new} new), "
          f"{len(all_encounters)} total encounters")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate L1 supplemental encounters grounded in JQD anchors")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--domain", help="Single domain code (e.g. CPAT)")
    group.add_argument("--all", action="store_true", default=True, help="All 9 domains (default)")
    parser.add_argument("--target", type=int, default=12,
                        help="Target L1 count per domain (default: 12)")
    parser.add_argument("--preview", action="store_true",
                        help="Generate first batch only, print, no file write")
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    domains = [args.domain] if args.domain else list(DOMAIN_NAMES.keys())

    if args.domain and args.domain not in DOMAIN_NAMES:
        print(f"Unknown domain: {args.domain}. Valid: {', '.join(DOMAIN_NAMES)}")
        sys.exit(1)

    api_key = load_api_key(args.api_key)
    client = anthropic.Anthropic(api_key=api_key)

    print(f"Generating L1 supplemental encounters")
    print(f"  Target: {args.target} L1 per domain")
    print(f"  Domains: {', '.join(domains)}")
    print(f"  Anchor source: JustinQuestionsDatabase\n")

    for code in domains:
        process_domain(client, code, args.target, args.preview)

    print("\nDone.")


if __name__ == "__main__":
    main()
