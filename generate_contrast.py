"""
generate_contrast.py

Generates "This or That" contrast question pairs for thin EPPP domains and
appends them to the existing data/{DOMAIN}_contrast.json files.

Usage:
  python generate_contrast.py --domain WDEV
  python generate_contrast.py --domain CASS --domain PTHE
  python generate_contrast.py --all

Options:
  --domain CODE   One or more domain codes (repeatable)
  --all           Expand all domains that are below --target count
  --target N      Minimum pairs per domain to reach (default: 30)
  --api-key KEY   Anthropic API key (overrides env / .env)
"""

import json, pathlib, argparse, time, sys, os
import anthropic

DATA = pathlib.Path(__file__).parent / "data"

DOMAIN_NAMES = {
    "PMET": "Learning, Conditioning & Research Methods",
    "LDEV": "Lifespan & Developmental Stages",
    "CPAT": "Clinical Psychopathology (DSM-5)",
    "PTHE": "Psychotherapy Models, Interventions & Prevention",
    "SOCU": "Social & Cultural Psychology",
    "WDEV": "Workforce Development & Leadership",
    "BPSY": "Biopsychology",
    "CASS": "Clinical Assessment & Interpretation",
    "PETH": "Psychopharmacology & Ethics",
}

# ---------------------------------------------------------------------------
# Concept pair topic lists — (item_x, item_y, subdomain)
# Ordered by pedagogical importance; generator skips already-present pairs.
# ---------------------------------------------------------------------------
DOMAIN_TOPICS = {

    "WDEV": [
        ("Job enlargement", "Job enrichment", "Job Design"),
        ("Role conflict", "Role ambiguity", "Satisfaction, Commitment, and Stress"),
        ("Affective commitment", "Continuance commitment", "Satisfaction, Commitment, and Stress"),
        ("Person-job fit", "Person-organization fit", "Employee Selection - Techniques"),
        ("Realistic job preview", "Traditional recruitment", "Employee Selection - Techniques"),
        ("Assessment center", "Work sample test", "Employee Selection - Evaluation of Techniques"),
        ("360-degree feedback", "Upward feedback", "Job Analysis and Performance Assessment"),
        ("Proximal goals", "Distal goals", "Theories of Motivation"),
        ("Coaching", "Mentoring", "Training Methods and Evaluation"),
        ("Gainsharing", "Profit sharing", "Theories of Motivation"),
        ("Formal organizational structure", "Informal organizational structure", "Organizational Theories"),
        ("Centralized decision-making", "Decentralized decision-making", "Organizational Theories"),
        ("Organizational socialization", "Employee onboarding", "Training Methods and Evaluation"),
        ("Burnout", "Engagement", "Satisfaction, Commitment, and Stress"),
        ("Voluntary turnover", "Involuntary turnover", "Satisfaction, Commitment, and Stress"),
        ("Succession planning", "Workforce planning", "Organizational Leadership"),
        ("Laissez-faire leadership", "Servant leadership", "Organizational Leadership"),
        ("Normative commitment", "Affective commitment", "Satisfaction, Commitment, and Stress"),
    ],

    "CASS": [
        ("Test reliability", "Test validity", "Psychometric Foundations"),
        ("Test-retest reliability", "Alternate-form reliability", "Psychometric Foundations"),
        ("Internal consistency reliability", "Inter-rater reliability", "Psychometric Foundations"),
        ("Sensitivity (clinical test)", "Specificity (clinical test)", "Clinical Decision-Making"),
        ("Positive predictive value", "Negative predictive value", "Clinical Decision-Making"),
        ("Base rate", "Hit rate", "Clinical Decision-Making"),
        ("Structured clinical interview", "Semi-structured clinical interview", "Clinical Interviewing"),
        ("Projective personality tests", "Objective personality tests", "Personality Assessment"),
        ("Behavioral observation assessment", "Self-report assessment", "Behavioral Assessment"),
        ("Neuropsychological screening", "Comprehensive neuropsychological evaluation", "Neuropsychological Assessment"),
        ("DSM-5 categorical diagnosis", "DSM-5 dimensional assessment", "Diagnostic Systems"),
        ("Intellectual disability", "Specific learning disorder", "Diagnostic Systems"),
        ("Malingering", "Factitious disorder", "Response Style Assessment"),
        ("Standard error of measurement", "Standard error of the mean", "Psychometric Foundations"),
        ("Floor effect", "Ceiling effect", "Psychometric Foundations"),
    ],

    "PTHE": [
        ("Primary prevention", "Secondary prevention", "Levels of Prevention"),
        ("Behavioral activation", "Cognitive restructuring", "Cognitive-Behavioral Therapies"),
        ("Systematic desensitization", "Flooding (in vivo exposure)", "Behavioral Therapies"),
        ("Acceptance (ACT)", "Commitment (ACT)", "Third-Wave Behavioral Therapies"),
        ("Psychodynamic clarification", "Psychodynamic interpretation", "Psychodynamic Therapies"),
        ("Supportive therapy", "Insight-oriented therapy", "Therapy Orientations"),
        ("Cognitive processing therapy (CPT)", "Prolonged exposure (PE)", "Trauma Therapies"),
        ("Mindfulness-based stress reduction (MBSR)", "Mindfulness-based cognitive therapy (MBCT)", "Third-Wave Behavioral Therapies"),
        ("Functional family therapy (FFT)", "Multisystemic therapy (MST)", "Family and Systems Therapies"),
        ("Harm reduction approach", "Abstinence-based treatment", "Substance Use Treatment"),
        ("Motivational interviewing", "Brief advice intervention", "Motivational Approaches"),
        ("DBT validation strategies", "DBT change strategies", "Dialectical Behavior Therapy"),
        ("Schema therapy", "Standard CBT", "Cognitive-Behavioral Therapies"),
        ("Gottman couples therapy", "Emotionally focused therapy (EFT)", "Couples Therapies"),
    ],

    "PETH": [
        ("SSRI mechanism of action", "SNRI mechanism of action", "Psychopharmacology - Antidepressants"),
        ("Typical antipsychotics (first-generation)", "Atypical antipsychotics (second-generation)", "Psychopharmacology - Antipsychotics"),
        ("Lithium (mood stabilizer)", "Valproate (mood stabilizer)", "Psychopharmacology - Mood Stabilizers"),
        ("Benzodiazepines", "Buspirone (non-benzodiazepine anxiolytic)", "Psychopharmacology - Anxiolytics"),
        ("MAOIs (monoamine oxidase inhibitors)", "Tricyclic antidepressants (TCAs)", "Psychopharmacology - Antidepressants"),
        ("Stimulant ADHD medication", "Non-stimulant ADHD medication", "Psychopharmacology - ADHD"),
        ("Tardive dyskinesia", "Drug-induced Parkinsonism", "Psychopharmacology - Side Effects"),
        ("Informed consent", "Assent (minors)", "Ethical Principles"),
        ("Confidentiality", "Privilege (testimonial)", "Ethical Principles"),
        ("Mandatory reporting obligation", "Duty to warn / protect (Tarasoff)", "Legal and Ethical Obligations"),
        ("Multiple relationship (ethics)", "Boundary crossing (ethics)", "Professional Ethics"),
        ("Competency to stand trial", "Criminal responsibility (insanity defense)", "Forensic Ethics"),
        ("Reasonable suspicion (child abuse)", "Confirmed abuse standard", "Mandatory Reporting"),
        ("Ethics complaint (APA)", "Malpractice lawsuit (civil)", "Professional Ethics"),
    ],

    "LDEV": [
        ("Assimilation (Piaget)", "Accommodation (Piaget)", "Cognitive Development"),
        ("Separation anxiety", "Stranger anxiety", "Social-Emotional Development"),
        ("Authoritative parenting", "Authoritarian parenting", "Parenting Styles"),
        ("Crystallized intelligence", "Fluid intelligence", "Cognitive Aging"),
        ("Primary aging", "Secondary aging", "Aging and Adulthood"),
        ("Preoperational stage", "Concrete operational stage", "Cognitive Development"),
        ("Secure attachment", "Anxious-ambivalent attachment", "Attachment Theory"),
        ("Identity foreclosure (Marcia)", "Identity diffusion (Marcia)", "Identity Development"),
    ],

    "SOCU": [
        ("Obedience (Milgram)", "Conformity (Asch)", "Social Influence"),
        ("Informational social influence", "Normative social influence", "Social Influence"),
        ("Explicit attitudes", "Implicit attitudes", "Attitude Formation and Change"),
        ("Stereotype threat", "Self-fulfilling prophecy", "Social Cognition"),
        ("Scapegoating", "Discrimination", "Prejudice and Discrimination"),
        ("Prosocial behavior", "Altruism", "Helping Behavior"),
    ],
}

# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) content creator specializing in concept discrimination questions.

You will be given two related psychology concepts (item_x and item_y) that EPPP candidates commonly confuse. Your task is to write a high-quality contrast question pair distinguishing them.

Respond ONLY with valid JSON — no markdown, no extra text — in this exact format:
{
  "subdomain": "Topic category name (as provided)",
  "item_x": "First concept name exactly as provided",
  "item_y": "Second concept name exactly as provided",
  "question": "What is the difference between [item_x] and [item_y]?",
  "answer": "Detailed 4-6 sentence answer covering both concepts. Describe each concept clearly, provide a concrete clinical or applied example for each, and highlight the definitive distinguishing feature. Maintain EPPP exam relevance throughout.",
  "key_distinction": "item_x = brief defining phrase (5-12 words); item_y = brief defining phrase (5-12 words).",
  "commonly_confused_because": "1-2 sentence explanation of exactly why students confuse these two concepts — the specific shared feature or superficial similarity that misleads them."
}

CRITICAL formatting rules for key_distinction:
- MUST use this exact pattern: "ConceptX = brief; ConceptY = brief."
- Separate the two halves with a semicolon
- The concept name before = must match item_x and item_y as closely as possible
- Keep each description to 5-12 words — crisp and memorable
- End the whole string with a period

Quality standards:
- The answer should be detailed enough that a student reading it would fully understand both concepts and never confuse them again
- Include at least one concrete example or clinical vignette reference per concept
- The key_distinction should be a genuine mnemonic anchor — the most important single fact about each concept
- commonly_confused_because should name the SPECIFIC shared feature, not just say "they are similar\""""


def load_api_key(args_key: str | None) -> str:
    if args_key:
        return args_key
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']
    for p in [pathlib.Path('.env'), pathlib.Path.home() / '.env']:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('ANTHROPIC_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError(
        "No API key found.\n"
        "Set ANTHROPIC_API_KEY in your environment, or create a .env file with\n"
        "  ANTHROPIC_API_KEY=sk-ant-..."
    )


def extract_json(text: str) -> dict:
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON object in response")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("No complete JSON object in response")


def load_existing(path: pathlib.Path) -> tuple[list, set]:
    """Returns (questions_list, existing_pair_set).
    existing_pair_set contains frozensets of (item_x.lower(), item_y.lower())."""
    if not path.exists():
        return [], set()
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    questions = data.get('questions', [])
    pairs = set()
    for q in questions:
        pairs.add(frozenset([q['item_x'].lower(), q['item_y'].lower()]))
    return questions, pairs


def next_id(domain_code: str, questions: list) -> str:
    """Generate the next sequential ID for a domain."""
    prefix = f"{domain_code}_CONT_"
    existing_nums = []
    for q in questions:
        qid = q.get('id', '')
        if qid.startswith(prefix):
            try:
                existing_nums.append(int(qid[len(prefix):]))
            except ValueError:
                pass
    n = max(existing_nums, default=0) + 1
    return f"{prefix}{n:03d}"


def generate_one(client: anthropic.Anthropic, domain_code: str, domain_name: str,
                 item_x: str, item_y: str, subdomain: str,
                 retries: int = 3) -> dict | None:
    user_msg = (
        f"Domain: {domain_name}\n"
        f"Subdomain: {subdomain}\n"
        f"item_x: {item_x}\n"
        f"item_y: {item_y}\n\n"
        f"Generate a contrast question pair distinguishing these two concepts."
    )
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            result = extract_json(msg.content[0].text.strip())

            # Validate required fields
            for field in ('question', 'answer', 'key_distinction', 'commonly_confused_because'):
                assert field in result and result[field].strip(), f"Missing or empty field: {field}"

            # Validate key_distinction has semicolon separator (parser requirement)
            assert ';' in result['key_distinction'], \
                "key_distinction must contain ';' separator"

            # Normalize item names to exactly what was requested
            result['item_x']    = item_x
            result['item_y']    = item_y
            result['subdomain'] = subdomain

            return result

        except (json.JSONDecodeError, AssertionError, KeyError, ValueError) as e:
            print(f"    Parse error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
        except anthropic.RateLimitError:
            wait = 20 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s...")
            time.sleep(wait)
        except Exception as e:
            print(f"    API error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(3)

    return None


def process_domain(client: anthropic.Anthropic, domain_code: str, target: int):
    domain_name = DOMAIN_NAMES[domain_code]
    topics = DOMAIN_TOPICS.get(domain_code)
    if not topics:
        print(f"  {domain_code}: no topic list defined — skipping")
        return

    dst = DATA / f"{domain_code}_contrast.json"
    questions, existing_pairs = load_existing(dst)

    current = len(questions)
    if current >= target:
        print(f"  {domain_code}: already at {current} pairs (target {target}) — skipping")
        return

    todo = [
        (x, y, sub) for (x, y, sub) in topics
        if frozenset([x.lower(), y.lower()]) not in existing_pairs
    ]

    needed = target - current
    todo = todo[:needed]

    if not todo:
        print(f"  {domain_code}: no new topic pairs left to generate ({current} existing)")
        return

    print(f"\n  {domain_code}: generating {len(todo)} new pairs "
          f"({current} existing, target {target})...")

    errors = 0
    for i, (item_x, item_y, subdomain) in enumerate(todo, 1):
        print(f"    [{i}/{len(todo)}] {item_x} vs {item_y}...", end=' ', flush=True)
        result = generate_one(client, domain_code, domain_name, item_x, item_y, subdomain)
        if result:
            qid = next_id(domain_code, questions)
            questions.append({
                "id":                       qid,
                "domain_code":              domain_code,
                "domain_name":              domain_name,
                "subdomain":                result['subdomain'],
                "item_x":                   result['item_x'],
                "item_y":                   result['item_y'],
                "question":                 result['question'],
                "answer":                   result['answer'],
                "key_distinction":          result['key_distinction'],
                "commonly_confused_because": result['commonly_confused_because'],
            })
            print("OK")
        else:
            errors += 1
            print("FAILED")
        time.sleep(0.4)

    # Write back
    out = {
        "domain_code":   domain_code,
        "domain_name":   domain_name,
        "question_type": "contrast",
        "total":         len(questions),
        "questions":     questions,
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"  -> {dst.name}: {len(questions)} pairs total ({errors} failures)")


def main():
    parser = argparse.ArgumentParser(
        description='Generate contrast question pairs for EPPP domains.'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--domain', action='append', metavar='CODE',
                       help='Domain code(s) to expand (repeatable)')
    group.add_argument('--all', action='store_true',
                       help='Expand all domains below --target')
    parser.add_argument('--target', type=int, default=30,
                        help='Minimum pairs per domain (default: 30)')
    parser.add_argument('--api-key', default=None,
                        help='Anthropic API key (overrides env / .env)')
    args = parser.parse_args()

    api_key = load_api_key(args.api_key)
    client  = anthropic.Anthropic(api_key=api_key)

    if args.all:
        domains = list(DOMAIN_NAMES.keys())
    else:
        for code in args.domain:
            if code not in DOMAIN_NAMES:
                print(f"Unknown domain code: {code}")
                print(f"Valid codes: {', '.join(DOMAIN_NAMES)}")
                sys.exit(1)
        domains = args.domain

    for code in domains:
        process_domain(client, code, args.target)

    print("\nDone.")


if __name__ == '__main__':
    main()
