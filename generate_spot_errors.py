"""
generate_spot_errors.py

Reads {DOMAIN}_passages.json files, calls Claude to generate "spot the error"
questions, and writes {DOMAIN}_spot.json to data/.

Each question:
  - Takes a passage from the book
  - Introduces exactly ONE factual error
  - Provides 4 MC options: one correctly identifies the error; three are
    plausible-sounding but wrong (describe changes that weren't made)
  - Provides an explanation

Run:
  python3 generate_spot_errors.py --domain PMET --count 50
  python3 generate_spot_errors.py --all --count 40   # 40 per domain
  python3 generate_spot_errors.py --all              # all passages

Options:
  --domain CODE   Single domain code (e.g. PMET)
  --all           Process all 9 domains
  --count N       Max passages per domain (default: all)
  --resume        Skip passages already written to output file
"""

import json, pathlib, argparse, time, random, sys, os
import anthropic

def load_api_key(args_key: str | None) -> str:
    """Resolve API key: CLI arg > env var > .env file."""
    if args_key:
        return args_key
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']
    # Try .env file in cwd or home
    for p in [pathlib.Path('.env'), pathlib.Path.home() / '.env']:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('ANTHROPIC_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError(
        "No API key found.\n"
        "Set ANTHROPIC_API_KEY in your environment, create a .env file with\n"
        "  ANTHROPIC_API_KEY=sk-ant-...\n"
        "or pass --api-key sk-ant-..."
    )

DATA = pathlib.Path("data")

DOMAIN_NAMES = {
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

SYSTEM_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) content creator.
Your task is to create "Spot the Error" questions from psychology study passages.

For each passage you receive, you will:
1. Introduce EXACTLY ONE subtle but clear factual error (change a key term, swap two concepts, use the wrong person's name, alter a number, reverse a relationship, or substitute a wrong condition/disorder name).
2. Create 4 multiple-choice options. EXACTLY ONE option correctly identifies the error that was introduced. The other three are plausible-sounding distractors that describe changes that were NOT made.
3. Write a clear explanation of what was wrong and what the correct information is.

Error types to use (vary them):
- Key term substitution (e.g., "CS" for "US", "reinforcement" for "punishment")
- Name swap (e.g., "Watson" instead of "Pavlov", "Beck" instead of "Ellis")
- Number/value change (e.g., "-55 mV" instead of "-70 mV", "30%" instead of "50%")
- Concept reversal (e.g., "increases" instead of "decreases")
- Wrong disorder/condition name (e.g., "histrionic" instead of "borderline")
- Wrong test/scale name (e.g., "WAIS" instead of "MMPI")

Rules:
- The error must be factually verifiable from the passage context.
- The error must be subtle enough to test careful reading but clear enough to have a definitive answer.
- Distractors must sound plausible (describe something that COULD be an error in this passage topic) but must NOT be errors that were actually introduced.
- Options should be stated as: "The passage incorrectly states [X]; it should say [Y]."
- Keep the modified passage clearly readable — only change the ONE error word/phrase.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{
  "modified_passage": "The passage text with exactly one error introduced",
  "error_original": "the incorrect text as it appears in the modified passage",
  "error_correct": "what the text should actually say",
  "options": [
    "The passage incorrectly states [A]; it should say [B]",
    "The passage incorrectly states [C]; it should say [D]",
    "The passage incorrectly states [E]; it should say [F]",
    "The passage incorrectly states [G]; it should say [H]"
  ],
  "correct_option_index": 0,
  "explanation": "Clear explanation of why the change was wrong and what the correct information is."
}

The correct_option_index is 0-based (0 = first option is correct, 1 = second, etc.).
Shuffle the correct answer position — don't always put it first."""


def build_user_prompt(passage: dict) -> str:
    return f"""Domain: {passage['domain_name']}
Chapter: {passage['chapter_title']}
Section: {passage.get('section', '')}
Passage type: {passage['passage_type']}

Original passage:
{passage['passage']}

Generate a spot-the-error question from this passage."""


def generate_question(client: anthropic.Anthropic, passage: dict,
                      retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": build_user_prompt(passage)}
                ],
                system=SYSTEM_PROMPT,
            )
            raw = msg.content[0].text.strip()
            # Strip any accidental markdown fences
            raw = raw.lstrip('`').lstrip('json').rstrip('`').strip()
            result = json.loads(raw)

            # Basic validation
            assert 'modified_passage' in result
            assert 'options' in result and len(result['options']) == 4
            assert 0 <= result.get('correct_option_index', -1) <= 3

            return {
                "id":                passage['id'],
                "domain_code":       passage['domain_code'],
                "domain_name":       passage['domain_name'],
                "chapter_file":      passage['chapter_file'],
                "chapter_title":     passage['chapter_title'],
                "section":           passage.get('section', ''),
                "passage_type":      passage['passage_type'],
                "original_passage":  passage['passage'],
                "modified_passage":  result['modified_passage'],
                "error_original":    result.get('error_original', ''),
                "error_correct":     result.get('error_correct', ''),
                "options":           result['options'],
                "correct_option_index": result['correct_option_index'],
                "explanation":       result['explanation'],
            }

        except (json.JSONDecodeError, AssertionError, KeyError) as e:
            print(f"    Parse error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
        except anthropic.RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s...")
            time.sleep(wait)
        except Exception as e:
            print(f"    API error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(3)

    return None


def load_existing(path: pathlib.Path) -> dict:
    """Return {id: question} for already-generated questions."""
    if not path.exists():
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {q['id']: q for q in data.get('questions', [])}


def process_domain(client: anthropic.Anthropic, domain_code: str,
                   count: int | None, resume: bool):
    src = DATA / f"{domain_code}_passages.json"
    if not src.exists():
        print(f"  SKIP: {src} not found")
        return

    with open(src, encoding='utf-8') as f:
        data = json.load(f)
    passages = data['passages']

    dst = DATA / f"{domain_code}_spot.json"
    existing = load_existing(dst) if resume else {}

    # Filter to passages not yet done
    todo = [p for p in passages if not resume or p['id'] not in existing]
    if count:
        # Sample evenly across chapters
        random.shuffle(todo)
        todo = todo[:count]

    if not todo:
        print(f"  {domain_code}: nothing to do ({len(existing)} already done)")
        return

    print(f"\n  {domain_code}: generating {len(todo)} questions "
          f"(+{len(existing)} existing)...")

    questions = list(existing.values())
    errors = 0

    for i, passage in enumerate(todo, 1):
        print(f"    [{i}/{len(todo)}] {passage['chapter_title'][:50]}...", end=' ', flush=True)
        q = generate_question(client, passage)
        if q:
            questions.append(q)
            print("OK")
        else:
            errors += 1
            print("FAILED")
        # Brief pause to avoid hammering rate limits
        time.sleep(0.3)

    # Write output
    out = {
        "domain_code":   domain_code,
        "domain_name":   DOMAIN_NAMES[domain_code],
        "total_questions": len(questions),
        "questions":     questions,
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"  -> {dst.name}: {len(questions)} questions written "
          f"({errors} failures)")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--domain', help='Single domain code (e.g. PMET)')
    group.add_argument('--all', action='store_true', help='All 9 domains')
    parser.add_argument('--count', type=int, default=None,
                        help='Max passages per domain')
    parser.add_argument('--resume', action='store_true',
                        help='Skip already-generated questions')
    parser.add_argument('--api-key', default=None,
                        help='Anthropic API key (overrides env / .env)')
    args = parser.parse_args()

    api_key = load_api_key(args.api_key)
    client = anthropic.Anthropic(api_key=api_key)

    if args.all:
        domains = list(DOMAIN_NAMES.keys())
    else:
        if args.domain not in DOMAIN_NAMES:
            print(f"Unknown domain: {args.domain}")
            print(f"Valid codes: {', '.join(DOMAIN_NAMES)}")
            sys.exit(1)
        domains = [args.domain]

    for code in domains:
        process_domain(client, code, args.count, args.resume)

    print("\nDone.")


if __name__ == '__main__':
    main()
