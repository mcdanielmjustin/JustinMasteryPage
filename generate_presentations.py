"""
generate_presentations.py

Generates clinical patient encounter scenarios for the Patient Encounter module.
Each encounter has 3–5 phases + 1–2 questions per encounter.

Usage:
  python generate_presentations.py --domain CPAT --count 30
  python generate_presentations.py --all --count 30 --resume
  python generate_presentations.py --domain CPAT --preview
  python generate_presentations.py --domain CPAT --count 30 --resume
"""

import json, pathlib, argparse, time, random, sys, os, re
from datetime import datetime, timezone
import anthropic

# ─── Paths ────────────────────────────────────────────────────────────────────

DATA = pathlib.Path("data")

# ─── Constants ────────────────────────────────────────────────────────────────

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
    "CPAT": [
        "Mood Disorders",
        "Anxiety Disorders",
        "Psychotic Disorders",
        "Trauma- and Stressor-Related Disorders",
        "Personality Disorders",
        "Neurodevelopmental Disorders",
        "Substance Use Disorders",
        "Somatic Symptom and Related Disorders",
        "Eating and Feeding Disorders",
        "Sleep-Wake Disorders",
    ],
    "PTHE": [
        "Cognitive-Behavioral Therapy",
        "Psychodynamic and Psychoanalytic Approaches",
        "Humanistic and Person-Centered Therapy",
        "Family Systems Therapy",
        "Dialectical Behavior Therapy",
        "Acceptance and Commitment Therapy",
        "Motivational Interviewing",
        "Group Therapy",
        "Crisis Intervention",
        "Child and Play Therapy",
    ],
    "BPSY": [
        "Neurotransmitter Systems",
        "Psychopharmacology",
        "Brain Structures and Functions",
        "Genetics and Epigenetics",
        "Endocrine and Immune Interactions",
        "Sleep Physiology",
        "Psychophysiology",
        "Substance Neurobiology",
    ],
    "PMET": [
        "Reliability",
        "Validity",
        "Standardization and Norms",
        "Norm-Referenced vs. Criterion-Referenced Assessment",
        "Test Bias and Fairness",
        "Statistical Concepts in Measurement",
        "Item Analysis",
        "Diagnostic Accuracy and Decision Theory",
    ],
    "LDEV": [
        "Infancy and Toddlerhood",
        "Early Childhood",
        "Middle Childhood",
        "Adolescence",
        "Early Adulthood",
        "Middle Adulthood",
        "Late Adulthood",
        "Cognitive Development Across the Lifespan",
        "Social-Emotional Development",
        "Attachment Theory and Patterns",
    ],
    "SOCU": [
        "Cultural Competence and Multicultural Practice",
        "Health Disparities and Social Determinants",
        "Group Dynamics and Social Influence",
        "Attitudes, Attribution, and Stereotyping",
        "Conformity, Obedience, and Persuasion",
        "Community Psychology",
        "Rural and Underserved Populations",
        "Immigration and Acculturation",
    ],
    "WDEV": [
        "Supervision Models and Processes",
        "Consultation",
        "Professional Development and Competence",
        "Organizational Behavior",
        "Work Motivation and Job Satisfaction",
        "Leadership and Management",
        "Team Dynamics",
        "Burnout, Self-Care, and Wellness",
    ],
    "CASS": [
        "Clinical Interview Techniques",
        "Intelligence and Cognitive Testing",
        "Personality Assessment",
        "Behavioral Assessment",
        "Neuropsychological Assessment",
        "Risk Assessment",
        "Diagnostic Formulation",
        "Cultural Considerations in Assessment",
    ],
    "PETH": [
        "Informed Consent",
        "Confidentiality and Privilege",
        "Dual Relationships and Boundaries",
        "Competence and Scope of Practice",
        "APA Ethics Code Application",
        "Mandatory Reporting",
        "Termination and Abandonment",
        "Documentation and Record-Keeping",
        "Telehealth Ethics",
        "Supervision Ethics",
    ],
}

AVATAR_EMOTIONS = [
    "idle", "speaking", "flat_affect", "distressed",
    "tearful", "anxious", "agitated", "guarded", "hopeful", "confused",
]

QUESTION_TYPES = [
    "primary_diagnosis",
    "differential_diagnosis",
    "immediate_intervention",
    "treatment_planning",
    "risk_assessment",
    "dsm_criteria",
    "cultural_consideration",
    "assessment_tool",
]

CHART_CATEGORIES = [
    "Chief Complaint",
    "History of Present Illness",
    "Mental Status Examination",
    "Psychosocial History",
    "Collateral / Context",
    "Labs / Observations",
]

ENCOUNTER_SETTINGS = [
    "Outpatient mental health clinic",
    "Inpatient psychiatric unit",
    "Community mental health center",
    "University counseling center",
    "Hospital emergency department",
    "Primary care physician's office",
    "School-based counseling office",
    "Private practice therapy office",
    "Residential treatment facility",
    "Veterans Affairs outpatient clinic",
    "Court-ordered evaluation setting",
    "Telehealth session",
]

# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) \
content author. You generate clinical patient encounter scenarios for an interactive \
licensure exam preparation tool called "Patient Encounter."

## Your Task
Generate exactly 5 clinical patient encounter objects as a valid JSON array. Each encounter \
must be a realistic, clinically coherent patient presentation that tests a licensed \
psychologist-level clinical judgment skill.

## Core Principles
- Encounters must simulate a real clinical session, not a textbook case vignette.
- Patient dialogue must sound authentic — conversational, emotionally genuine, and colloquial. \
  Do NOT write dialogue that sounds like a DSM symptom checklist recited by the patient.
- Diagnostic uncertainty should be maintained throughout the phases. The diagnosis should not \
  be obvious until the student has seen all phases and reflected on the full picture.
- Each encounter must stand alone — no references to "previous sessions" unless they're part \
  of the case context.
- All patient names must be initials only (e.g., "J.T.") or omitted; never full names.

## Required JSON Schema

Output a JSON array of exactly 5 objects. Each object MUST follow this exact schema:

{
  "id": "CP-{DOMAIN}-{NNNN}",
  "domain_code": "{DOMAIN}",
  "subdomain": "...",
  "difficulty_level": 1–4,
  "encounter": {
    "setting": "...",
    "referral_context": "...",
    "patient": {
      "label": "Adult Male, 52" (or Female, or Adolescent, or Child — include age),
      "appearance_tags": ["..."] (1–3 brief physical/presentation descriptors),
      "initial_avatar_state": one of: idle | speaking | flat_affect | distressed | tearful | anxious | agitated | guarded | hopeful | confused
    },
    "phases": [
      {
        "phase_id": "chief_complaint" | "history" | "mse" | "psychosocial" | "collateral" | "additional",
        "phase_label": "Chief Complaint" (human-readable label for the phase indicator),
        "dialogue": "Patient's spoken words (or parent/guardian words for pediatric cases)",
        "avatar_emotion": one of the 10 allowed values,
        "behavioral_tags": ["..."] (0–4 brief observational tags, empty array if none),
        "chart_reveals": [
          {
            "category": one of: "Chief Complaint" | "History of Present Illness" | "Mental Status Examination" | "Psychosocial History" | "Collateral / Context" | "Labs / Observations",
            "label": "brief label",
            "value": "brief value"
          }
        ],
        "clinician_prompt": null or "Brief therapist question/probe that precedes the dialogue"
      }
    ]
  },
  "questions": [
    {
      "question_id": "q1",
      "type": one of: "primary_diagnosis" | "differential_diagnosis" | "immediate_intervention" | "treatment_planning" | "risk_assessment" | "dsm_criteria" | "cultural_consideration" | "assessment_tool",
      "prompt": "The clinical question stem (1–2 sentences)",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "correct_answer": "A" | "B" | "C" | "D",
      "explanation": "Full explanation of the correct answer (2–4 sentences)",
      "distractor_rationale": {
        "A": "Why A is wrong (or omit if A is correct)",
        "B": "Why B is wrong (or omit if B is correct)",
        ...
      }
    }
  ]
}

## Phase Guidelines
- Minimum 3 phases, maximum 5 phases per encounter.
- Phase IDs must be from: chief_complaint, history, mse, psychosocial, collateral, additional.
- Do NOT repeat the same phase_id in a single encounter.
- Phases must progress logically (chief_complaint first, mse or psychosocial later).
- Each phase must have at least 1 chart_reveal item.
- avatar_emotion should change meaningfully across phases (not the same for every phase).
- behavioral_tags accumulate clinical picture — pick observations that are diagnostically \
  significant but not telegraphically obvious.

## Question Guidelines
- 1–2 questions per encounter. Generate 2 when the case supports testing different skills.
- correct_answer should be roughly balanced across A/B/C/D across the 5 encounters in a batch.
- distractor_rationale must explain why each wrong option is wrong. Omit only the correct answer \
  from distractor_rationale.
- Options must be clinically plausible — not obviously wrong.
- For primary_diagnosis questions, options must all be DSM-5-TR diagnoses.
- For immediate_intervention questions, prioritize clinical safety decision-making.
- difficulty_level 1 = straightforward presentation, 4 = complex/atypical.

## Strict Validation Rules
- Every id must be unique and match pattern CP-{DOMAIN}-{NNNN} where NNNN is padded 4 digits.
- avatar_emotion must be one of the 10 allowed values exactly.
- question type must be one of the 8 allowed values exactly.
- chart_reveals category must be one of the 6 allowed category strings exactly.
- correct_answer must be one of A/B/C/D and must exist as a key in options.
- distractor_rationale must NOT include the correct_answer as a key.
- All string values must be properly JSON-escaped.

## Output Format
Respond with ONLY a valid JSON array. No markdown code fences. No commentary before or after. \
Start your response with [ and end with ]."""

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_api_key(args_key: str | None) -> str:
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


def extract_json_array(text: str) -> list:
    """Extract the first complete JSON array from text."""
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array found in response")
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("No complete JSON array found in response")


def validate_encounter(enc: dict, domain_code: str) -> list[str]:
    """Validate an encounter object. Returns list of error strings (empty = valid)."""
    errors = []

    # Top-level required fields
    for field in ("id", "domain_code", "subdomain", "difficulty_level", "encounter", "questions"):
        if field not in enc:
            errors.append(f"Missing top-level field: {field}")

    if errors:
        return errors  # can't validate further without structure

    # ID format
    id_pattern = rf"^CP-{domain_code}-\d{{4}}$"
    if not re.match(id_pattern, enc.get("id", "")):
        errors.append(f"id '{enc.get('id')}' does not match pattern CP-{domain_code}-NNNN")

    # difficulty_level
    dl = enc.get("difficulty_level")
    if not isinstance(dl, int) or not (1 <= dl <= 4):
        errors.append(f"difficulty_level must be int 1–4, got: {dl!r}")

    # encounter structure
    enc_data = enc.get("encounter", {})
    if not isinstance(enc_data, dict):
        errors.append("encounter must be a dict")
        return errors

    for field in ("setting", "patient", "phases"):
        if field not in enc_data:
            errors.append(f"encounter missing field: {field}")

    # patient
    patient = enc_data.get("patient", {})
    init_state = patient.get("initial_avatar_state", "")
    if init_state not in AVATAR_EMOTIONS:
        errors.append(f"patient.initial_avatar_state '{init_state}' not in allowed list")

    # phases
    phases = enc_data.get("phases", [])
    if not isinstance(phases, list) or not (3 <= len(phases) <= 5):
        errors.append(f"phases must be a list of 3–5 items, got: {len(phases) if isinstance(phases, list) else type(phases)}")
    else:
        seen_phase_ids = set()
        for pi, phase in enumerate(phases):
            if not isinstance(phase, dict):
                errors.append(f"phase[{pi}] is not a dict")
                continue
            for pf in ("phase_id", "phase_label", "dialogue", "avatar_emotion", "chart_reveals"):
                if pf not in phase:
                    errors.append(f"phase[{pi}] missing field: {pf}")

            pid = phase.get("phase_id", "")
            if pid in seen_phase_ids:
                errors.append(f"Duplicate phase_id '{pid}'")
            seen_phase_ids.add(pid)

            emotion = phase.get("avatar_emotion", "")
            if emotion not in AVATAR_EMOTIONS:
                errors.append(f"phase[{pi}].avatar_emotion '{emotion}' not in allowed list")

            reveals = phase.get("chart_reveals", [])
            if not isinstance(reveals, list) or len(reveals) == 0:
                errors.append(f"phase[{pi}].chart_reveals must be non-empty list")
            else:
                for ri, rev in enumerate(reveals):
                    cat = rev.get("category", "")
                    if cat not in CHART_CATEGORIES:
                        errors.append(f"phase[{pi}].chart_reveals[{ri}].category '{cat}' not in allowed list")

    # questions
    questions = enc.get("questions", [])
    if not isinstance(questions, list) or not (1 <= len(questions) <= 2):
        errors.append(f"questions must be list of 1–2 items, got: {len(questions) if isinstance(questions, list) else type(questions)}")
    else:
        for qi, q in enumerate(questions):
            if not isinstance(q, dict):
                errors.append(f"questions[{qi}] is not a dict")
                continue
            for qf in ("question_id", "type", "prompt", "options", "correct_answer", "explanation"):
                if qf not in q:
                    errors.append(f"questions[{qi}] missing field: {qf}")

            qtype = q.get("type", "")
            if qtype not in QUESTION_TYPES:
                errors.append(f"questions[{qi}].type '{qtype}' not in allowed list")

            opts = q.get("options", {})
            if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
                errors.append(f"questions[{qi}].options must have exactly keys A,B,C,D")

            ca = q.get("correct_answer", "")
            if ca not in ("A", "B", "C", "D"):
                errors.append(f"questions[{qi}].correct_answer '{ca}' must be A/B/C/D")
            elif isinstance(opts, dict) and ca not in opts:
                errors.append(f"questions[{qi}].correct_answer '{ca}' not in options")

            dr = q.get("distractor_rationale", {})
            if isinstance(dr, dict) and ca in dr:
                errors.append(f"questions[{qi}].distractor_rationale must NOT include correct_answer '{ca}'")

    return errors


def build_batch_prompt(
    domain_code: str,
    subdomains: list[str],
    difficulty_levels: list[int],
    required_emotions: list[str],
    required_q_types: list[str],
    start_id: int,
    batch_size: int = 5,
) -> str:
    """Build the user prompt for a batch of encounters."""
    subdomain_str = " and ".join(f'"{s}"' for s in subdomains)
    difficulty_str = ", ".join(str(d) for d in difficulty_levels)
    emotion_str = ", ".join(required_emotions)
    qtype_str = ", ".join(required_q_types)
    id_examples = ", ".join(
        f"CP-{domain_code}-{str(start_id + i).zfill(4)}"
        for i in range(batch_size)
    )

    domain_name = DOMAIN_NAMES[domain_code]

    # Domain-specific encounter framing guidance
    framing = DOMAIN_FRAMING.get(domain_code, "")

    prompt = f"""Generate exactly {batch_size} patient encounter objects for the domain:
  Domain: {domain_code} — {domain_name}
  Subdomains to cover: {subdomain_str}
  Difficulty levels to use in this batch: {difficulty_str} (distribute across the {batch_size} encounters)

Required constraints for this batch:
  - Avatar emotions to include (must appear at least once each): {emotion_str}
  - Question types to include (must appear at least once each): {qtype_str}
  - IDs to use (in order): {id_examples}
  - Each encounter must be set in a different clinical setting

{framing}

Return a JSON array of exactly {batch_size} encounter objects. No extra text."""

    return prompt


# Domain-specific framing instructions injected into user prompt
DOMAIN_FRAMING = {
    "PMET": """Domain framing — Psychometrics & Research Methods:
These encounters are ASSESSMENT or INTAKE sessions, not therapy sessions.
The "patient" is presenting for psychological or educational testing.
Phases should include: reason for referral, behavioral observations during interview,
relevant background for test selection, parent/teacher report (for pediatric cases).
Questions should test: test selection rationale, interpreting psychometric properties,
understanding of reliability/validity in a clinical context, base rate reasoning.""",

    "LDEV": """Domain framing — Lifespan Development:
Patient age MUST match the subdomain's developmental stage. Examples:
  - Infancy/Toddlerhood: Parent is the primary informant (baby cannot speak)
  - Adolescence: Teen may be guarded or resistant; parent provides collateral
  - Late Adulthood: Geriatric presentations; cognitive changes may be present
Include developmental context in the chart (developmental milestones, age-expected vs. delayed).
Phases should reflect who is speaking (parent, child, adult patient).
For pediatric cases, the clinician_prompt in early phases addresses the parent/guardian.""",

    "SOCU": """Domain framing — Social & Cultural Psychology:
Cultural identity, socioeconomic context, and systemic factors must be explicitly surfaced.
At least one phase should include a culturally significant disclosure or behavior.
Behavioral tags should include culturally relevant observations (e.g., "indirect communication style",
"somatic presentation of distress", "collectivist framing of problem").
Questions should test: cultural conceptualization of distress, cultural humility,
culturally adapted interventions, acculturation stress recognition.""",

    "WDEV": """Domain framing — Workforce Development & Leadership:
These encounters are NOT traditional patient encounters. Instead, they represent:
  - A supervision session (supervisee presenting a clinical dilemma or professional struggle)
  - An organizational consultation (organizational conflict, team dysfunction, leadership challenge)
  - A professional development scenario (competence concerns, role conflict, boundary issues)
The "patient" field represents the supervisee, employee, or consultee.
Dialogue is between supervisor/consultant and the person seeking support.
Settings should be: supervision office, organizational consultation, peer consultation.""",

    "CASS": """Domain framing — Clinical Assessment & Interpretation:
Encounters represent assessment sessions. Phases should mirror an assessment process:
  Phase 1 (Referral/Chief Complaint): Why is testing being requested?
  Phase 2 (Interview): Clinical interview revealing relevant history
  Phase 3 (Behavioral Observations): Observable behaviors during testing (not the test results)
  Phase 4 (Collateral/History): Informant report, records review findings
Questions should test: appropriate test battery selection, interpreting psychometric data,
integrating multiple data sources, diagnostic formulation from assessment data.""",

    "PETH": """Domain framing — Psychopharmacology & Ethics:
These encounters surface ethical dilemmas or psychopharmacology-related clinical decisions.
Ethics encounters: The situation unfolds to reveal an ethical complexity (confidentiality breach,
dual relationship emerging, informed consent ambiguity, mandatory reporting threshold, etc.)
Psychopharmacology encounters: Patient presenting with medication side effects, questions about
their psychiatric medication, or a clinical scenario requiring pharmacology knowledge.
Questions should test: APA ethics code application, ethical decision-making, medication
mechanisms and clinical indications, recognizing adverse effects.""",
}


# ─── Core Generation ──────────────────────────────────────────────────────────

def generate_batch(
    client: anthropic.Anthropic,
    domain_code: str,
    subdomains: list[str],
    difficulty_levels: list[int],
    required_emotions: list[str],
    required_q_types: list[str],
    start_id: int,
    batch_size: int = 5,
    retries: int = 3,
) -> list[dict]:
    """Generate a batch of encounters. Returns validated encounters (may be < batch_size)."""
    prompt = build_batch_prompt(
        domain_code, subdomains, difficulty_levels,
        required_emotions, required_q_types, start_id, batch_size
    )

    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()

            batch = extract_json_array(raw)

            if not isinstance(batch, list):
                raise ValueError(f"Expected JSON array, got {type(batch)}")

            # Validate each encounter; keep valid ones
            valid = []
            for i, enc in enumerate(batch):
                errs = validate_encounter(enc, domain_code)
                if errs:
                    print(f"    [enc {i+1}] INVALID: {'; '.join(errs[:3])}")
                else:
                    valid.append(enc)

            if valid:
                return valid
            else:
                raise ValueError("No valid encounters in batch after validation")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"    Parse/validation error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(3)
        except anthropic.RateLimitError:
            wait = 20 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s...")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            print(f"    API error (attempt {attempt+1}): {e.status_code} {e.message}")
            if attempt < retries - 1:
                time.sleep(5)
        except Exception as e:
            print(f"    Unexpected error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(3)

    return []


# ─── File I/O ─────────────────────────────────────────────────────────────────

def load_existing_file(path: pathlib.Path) -> dict:
    """Load existing output file. Returns full file dict with encounters list."""
    if not path.exists():
        return {"encounters": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_file(path: pathlib.Path, domain_code: str, encounters: list[dict]) -> None:
    """Write the full presentations JSON file."""
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


# ─── Domain Processing ────────────────────────────────────────────────────────

def process_domain(
    client: anthropic.Anthropic,
    domain_code: str,
    target_count: int,
    resume: bool,
    preview: bool = False,
) -> None:
    dst = DATA / f"{domain_code}_presentations.json"
    existing_data = load_existing_file(dst)
    existing_encounters = existing_data.get("encounters", [])

    if resume:
        encounters = list(existing_encounters)
        existing_ids = {e["id"] for e in encounters}
        already_have = len(encounters)
        need = max(0, target_count - already_have)
        if need == 0:
            print(f"  {domain_code}: already have {already_have}/{target_count} — nothing to do")
            return
        # Calculate next ID number from existing
        id_nums = []
        for e in encounters:
            m = re.search(r"-(\d{4})$", e.get("id", ""))
            if m:
                id_nums.append(int(m.group(1)))
        next_id = max(id_nums, default=0) + 1
    else:
        encounters = []
        existing_ids = set()
        need = target_count
        next_id = 1

    subdomains = DOMAIN_SUBDOMAINS[domain_code]
    subdomain_idx = 0  # cycles through subdomains across batches

    # Emotion and question type cycling for variety
    emotion_pool = list(AVATAR_EMOTIONS)
    qtype_pool = list(QUESTION_TYPES)
    random.shuffle(emotion_pool)
    random.shuffle(qtype_pool)
    emotion_cycle_idx = 0
    qtype_cycle_idx = 0

    batch_size = 5
    total_generated = 0
    total_failed = 0
    batches_needed = (need + batch_size - 1) // batch_size

    print(f"\n  {domain_code}: need {need} more encounters "
          f"({len(encounters)} existing), {batches_needed} batches...")

    for batch_num in range(batches_needed):
        remaining = need - total_generated
        this_batch = min(batch_size, remaining)
        if this_batch <= 0:
            break

        # Pick 2 subdomains for this batch (adjacent in cycle)
        batch_subdomains = [
            subdomains[subdomain_idx % len(subdomains)],
            subdomains[(subdomain_idx + 1) % len(subdomains)],
        ]
        subdomain_idx += 2

        # Pick 2–3 emotions to require in this batch
        batch_emotions = [
            emotion_pool[emotion_cycle_idx % len(emotion_pool)],
            emotion_pool[(emotion_cycle_idx + 1) % len(emotion_pool)],
        ]
        emotion_cycle_idx += 2

        # Pick 2 question types to require in this batch
        batch_qtypes = [
            qtype_pool[qtype_cycle_idx % len(qtype_pool)],
            qtype_pool[(qtype_cycle_idx + 1) % len(qtype_pool)],
        ]
        qtype_cycle_idx += 2

        # Difficulty levels for batch (distribute 1–4 across batches)
        diff_base = ((batch_num * 2) % 4) + 1
        batch_difficulties = [diff_base, min(diff_base + 1, 4)]

        print(f"    Batch {batch_num+1}/{batches_needed}: "
              f"subdomains={batch_subdomains}, "
              f"diff={batch_difficulties}, "
              f"id_start={next_id}...",
              end=" ", flush=True)

        batch_result = generate_batch(
            client,
            domain_code=domain_code,
            subdomains=batch_subdomains,
            difficulty_levels=batch_difficulties,
            required_emotions=batch_emotions,
            required_q_types=batch_qtypes,
            start_id=next_id,
            batch_size=this_batch,
        )

        if batch_result:
            # Deduplicate by ID (in case model reused an ID)
            new_encounters = []
            for enc in batch_result:
                if enc["id"] not in existing_ids:
                    existing_ids.add(enc["id"])
                    new_encounters.append(enc)
                    next_id = max(next_id, int(enc["id"].split("-")[-1]) + 1)

            encounters.extend(new_encounters)
            total_generated += len(new_encounters)
            failed_in_batch = this_batch - len(batch_result)
            total_failed += failed_in_batch
            print(f"OK ({len(new_encounters)} valid)")

            if preview:
                print("\n--- PREVIEW: First encounter ---")
                print(json.dumps(encounters[0], indent=2, ensure_ascii=False))
                print("--- END PREVIEW ---")
                return

            # Write incrementally after each successful batch
            write_file(dst, domain_code, encounters)
        else:
            total_failed += this_batch
            print("FAILED (all invalid)")

        # Brief pause between batches
        time.sleep(1.0)

    print(f"\n  {domain_code} complete: {len(encounters)} total encounters "
          f"({total_generated} new, {total_failed} failed)")


# ─── Summary ──────────────────────────────────────────────────────────────────

def print_summary(domain_code: str) -> None:
    """Print validation summary for a generated domain file."""
    dst = DATA / f"{domain_code}_presentations.json"
    if not dst.exists():
        print(f"  {domain_code}: file not found")
        return

    with open(dst, encoding="utf-8") as f:
        data = json.load(f)

    encounters = data.get("encounters", [])
    total = len(encounters)

    # Count by subdomain
    subdomain_counts: dict[str, int] = {}
    emotion_counts: dict[str, int] = {}
    qtype_counts: dict[str, int] = {}
    diff_counts: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}

    for enc in encounters:
        sd = enc.get("subdomain", "Unknown")
        subdomain_counts[sd] = subdomain_counts.get(sd, 0) + 1

        dl = enc.get("difficulty_level", 0)
        if isinstance(dl, int) and 1 <= dl <= 4:
            diff_counts[dl] += 1

        enc_data = enc.get("encounter", {})
        for phase in enc_data.get("phases", []):
            em = phase.get("avatar_emotion", "")
            emotion_counts[em] = emotion_counts.get(em, 0) + 1

        for q in enc.get("questions", []):
            qt = q.get("type", "")
            qtype_counts[qt] = qtype_counts.get(qt, 0) + 1

    print(f"\n  {domain_code} Summary — {total} encounters")
    print(f"    Difficulty: {diff_counts}")
    print(f"    Subdomains: {dict(sorted(subdomain_counts.items()))}")
    print(f"    Avatar emotions used: {dict(sorted(emotion_counts.items()))}")
    print(f"    Question types used: {dict(sorted(qtype_counts.items()))}")

    # Check coverage
    missing_emotions = set(AVATAR_EMOTIONS) - set(emotion_counts.keys())
    missing_qtypes = set(QUESTION_TYPES) - set(qtype_counts.keys())
    if missing_emotions:
        print(f"    WARNING: Missing avatar emotions: {missing_emotions}")
    if missing_qtypes:
        print(f"    WARNING: Missing question types: {missing_qtypes}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Patient Encounter data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--domain", help="Single domain code (e.g. CPAT)")
    group.add_argument("--all", action="store_true", help="Process all 9 domains")
    parser.add_argument("--count", type=int, default=30,
                        help="Target encounter count per domain (default: 30)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-generated encounters")
    parser.add_argument("--preview", action="store_true",
                        help="Generate first batch only, print result, no file write")
    parser.add_argument("--summary", action="store_true",
                        help="Print validation summary for existing files (no generation)")
    parser.add_argument("--api-key", default=None,
                        help="Anthropic API key (overrides env / .env)")
    args = parser.parse_args()

    if args.all:
        domains = list(DOMAIN_NAMES.keys())
    else:
        if args.domain not in DOMAIN_NAMES:
            print(f"Unknown domain: {args.domain}")
            print(f"Valid codes: {', '.join(DOMAIN_NAMES)}")
            sys.exit(1)
        domains = [args.domain]

    if args.summary:
        for code in domains:
            print_summary(code)
        return

    api_key = load_api_key(args.api_key)
    client = anthropic.Anthropic(api_key=api_key)

    for code in domains:
        process_domain(
            client,
            domain_code=code,
            target_count=args.count,
            resume=args.resume,
            preview=args.preview,
        )

    if not args.preview and not args.summary:
        print("\n--- Final Summaries ---")
        for code in domains:
            print_summary(code)

    print("\nDone.")


if __name__ == "__main__":
    main()
