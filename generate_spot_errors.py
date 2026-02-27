"""
generate_spot_errors.py

Reads {DOMAIN}_passages.json files, calls Claude to generate "spot the error"
questions, and writes {DOMAIN}_spot.json to data/.

Modes:
  mc             (default) Multiple-choice — pick the option naming the error
  passage_click  Click the sentence containing the error
  sentence_click Click the wrong phrase within a single sentence
  vocab          Click the vocab card with a flawed definition

Run:
  python3 generate_spot_errors.py --domain PMET --count 50
  python3 generate_spot_errors.py --domain PMET --mode passage_click --count 50
  python3 generate_spot_errors.py --all --count 40   # 40 per domain
  python3 generate_spot_errors.py --all              # all passages

Options:
  --domain CODE   Single domain code (e.g. PMET)
  --all           Process all 9 domains
  --count N       Max passages per domain (default: all)
  --resume        Skip passages already written to output file
  --mode MODE     Question mode: mc | passage_click | sentence_click | vocab
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

PASSAGE_CLICK_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) content creator.
Your task is to create "Spot the Error — Click the Sentence" questions from psychology study passages.

For each passage you receive, you will:
1. Split the passage into individual sentences (aim for 3–8 sentences).
2. Introduce EXACTLY ONE subtle but clear factual error into one of those sentences.
3. Return the full sentence list (with the modified sentence in place), the target index, the original sentence, and error details.

Error types to use (vary them):
- Key term substitution (e.g., "CS" for "US", "reinforcement" for "punishment")
- Name swap (e.g., "Watson" instead of "Pavlov", "Beck" instead of "Ellis")
- Number/value change (e.g., "-55 mV" instead of "-70 mV", "30%" instead of "50%")
- Concept reversal (e.g., "increases" instead of "decreases")
- Wrong disorder/condition name (e.g., "histrionic" instead of "borderline")
- Wrong test/scale name (e.g., "WAIS" instead of "MMPI")

Rules:
- sentences[] contains the MODIFIED text (with the error already present in the target sentence).
- error_original must appear verbatim in sentences[target_sentence_index].
- original_sentence is the correct (unmodified) version of the target sentence.
- The error must be subtle but clearly wrong; one definitive answer only.
- Each element of sentences[] is one complete sentence — do not split mid-sentence.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{
  "sentences": ["First sentence.", "Second sentence with error.", "Third sentence."],
  "target_sentence_index": 1,
  "original_sentence": "Second sentence original (correct version).",
  "error_original": "the wrong text as it appears in the modified sentence",
  "error_correct": "what the text should actually say",
  "explanation": "Clear explanation of the error and the correct information."
}"""

SENTENCE_CLICK_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) content creator.
Your task is to create "Spot the Error — Click the Phrase" questions from psychology study passages.

STEP 1 — SELECT THE RIGHT SENTENCE
From the passage, pick the single sentence that:
- Is at least 20 words long
- Contains 2 or more distinct, verifiable factual claims
- Has natural split points (commas, conjunctions, relative clauses) that produce 4 meaningful chunks
If no single sentence meets all criteria, combine 2 adjacent sentences from the passage.

STEP 2 — SPLIT INTO EXACTLY 4 PHRASES
Splitting rules (strictly enforced):
- Split ONLY at complete grammatical boundaries: end of a clause, before a coordinating
  conjunction ("and", "but", "or", "while"), or at a comma that separates full ideas
- NEVER cut mid-clause. Every phrase must be a grammatically self-contained unit.
  Bad: "...and is appropriate when both variables are measured on" (ends mid-clause)
  Good: "...and is appropriate when both variables are measured on interval or ratio scales"
- Every phrase must be 6–18 words. If any phrase would fall under 6 words, pick a
  different sentence or different split points.
- phrases[] joined together must equal modified_sentence exactly, character-for-character.

STEP 3 — INTRODUCE THE ERROR
- Place the error in phrase index 1 or 2 ONLY (middle phrases — never first or last).
- The error must be embedded inside a substantive phrase of at least 6 words.
- Error types (vary these — do NOT always use simple reversals):
    • Wrong researcher name (e.g., "Bandura" instead of "Skinner")
    • Wrong scale or test name (e.g., "WAIS" instead of "MMPI-2")
    • Wrong numerical value (e.g., "80%" instead of "95%", "-65 mV" instead of "-70 mV")
    • Wrong mechanism (e.g., "GABA" instead of "glutamate")
    • Wrong associated disorder or condition
    • Wrong direction only when genuinely non-obvious in context
- Avoid generic, well-known swaps like "positive/negative reinforcement" — the error
  should require specific factual recall, not pattern matching.
- error_original must appear verbatim in phrases[target_phrase_index].

Respond ONLY with valid JSON (no markdown, no extra text):
{
  "modified_sentence": "The full modified sentence as one string.",
  "phrases": ["Complete clause one,", " complete clause two containing the error,", " complete clause three,", " and complete clause four."],
  "target_phrase_index": 1,
  "error_original": "the wrong text as it appears verbatim in the target phrase",
  "error_correct": "what it should actually say",
  "explanation": "Clear explanation of why this is wrong and what the correct information is."
}"""

VOCAB_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) content creator.
Your task is to create "Spot the Error — Vocab Card" questions from psychology study passages.

For each passage you receive, you will:
1. Identify the single most important key term defined or described in the passage.
2. Write a concise definition (2–3 sentences) for that term with EXACTLY ONE subtle factual error.
3. Write 3 distractor entries: closely related terms from the SAME domain/category, each with a
   CORRECT definition of similar length. Distractors should be similar enough to cause genuine
   confusion (e.g., if target is "dopamine", use "serotonin", "norepinephrine", "acetylcholine").

Error types for the target definition:
- Swapped number or value, wrong mechanism, wrong associated researcher/name,
  reversed relationship, wrong associated condition or scale

Rules:
- Shuffle the target position — don't always put it at index 0.
- All 4 definitions should be similar in length and style.
- Distractors must be plausible vocab from the same domain — not obscure or unrelated terms.
- error_original must appear verbatim in entries[target_entry_index].definition.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{
  "entries": [
    {"term": "Target Term", "definition": "Definition with exactly one subtle error.", "is_target": true},
    {"term": "Similar Term A", "definition": "Correct definition of similar length.", "is_target": false},
    {"term": "Similar Term B", "definition": "Correct definition of similar length.", "is_target": false},
    {"term": "Similar Term C", "definition": "Correct definition of similar length.", "is_target": false}
  ],
  "target_entry_index": 0,
  "error_original": "the wrong text as it appears in the target definition",
  "error_correct": "what the text should actually say",
  "explanation": "Clear explanation of the error and the correct information."
}"""

MODE_ID_PREFIXES = {
    'passage_click': 'PC',
    'sentence_click': 'SC',
    'vocab':          'VD',
}


def extract_json(text: str) -> dict:
    """Extract the first complete JSON object from text that may have preamble or suffix."""
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("No complete JSON object in response")


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
            result = extract_json(raw)

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

        except (json.JSONDecodeError, AssertionError, KeyError, ValueError) as e:
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


def generate_passage_click(client: anthropic.Anthropic, passage: dict,
                           retries: int = 3) -> dict | None:
    """Returns mode-specific result dict (no id/metadata) or None on failure."""
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": build_user_prompt(passage)}],
                system=PASSAGE_CLICK_PROMPT,
            )
            result = extract_json(msg.content[0].text)

            assert 'sentences' in result and isinstance(result['sentences'], list)
            assert len(result['sentences']) >= 2
            tsi = result.get('target_sentence_index', -1)
            assert 0 <= tsi < len(result['sentences']), "target_sentence_index out of range"
            assert 'original_sentence' in result
            assert 'error_original' in result
            assert result['error_original'] in result['sentences'][tsi], \
                f"error_original not found in target sentence"
            assert 'error_correct' in result
            assert 'explanation' in result

            return result

        except (json.JSONDecodeError, AssertionError, KeyError, ValueError) as e:
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


def generate_sentence_click(client: anthropic.Anthropic, passage: dict,
                            retries: int = 3) -> dict | None:
    """Returns mode-specific result dict (no id/metadata) or None on failure."""
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": build_user_prompt(passage)}],
                system=SENTENCE_CLICK_PROMPT,
            )
            result = extract_json(msg.content[0].text)

            assert 'modified_sentence' in result
            assert 'phrases' in result and isinstance(result['phrases'], list)
            assert len(result['phrases']) == 4, \
                f"expected 4 phrases, got {len(result['phrases'])}"
            tpi = result.get('target_phrase_index', -1)
            assert 1 <= tpi <= 3, \
                f"target_phrase_index must be 1–3 (not the first phrase), got {tpi}"
            assert 'error_original' in result
            assert result['error_original'] in result['phrases'][tpi], \
                "error_original not found in target phrase"
            # No phrase should be fewer than 4 words
            for idx, ph in enumerate(result['phrases']):
                wc = len(ph.split())
                assert wc >= 4, \
                    f"phrase {idx} too short ({wc} words): {ph!r}"
            # Phrases must reassemble to modified_sentence exactly
            assert ''.join(result['phrases']) == result['modified_sentence'], \
                "phrases do not concatenate to modified_sentence"
            assert 'error_correct' in result
            assert result['error_original'].strip() != result['error_correct'].strip(), \
                "error_original equals error_correct — model failed to introduce a real error"
            assert 'explanation' in result

            return result

        except (json.JSONDecodeError, AssertionError, KeyError, ValueError) as e:
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


def generate_vocab(client: anthropic.Anthropic, passage: dict,
                   retries: int = 3) -> dict | None:
    """Returns mode-specific result dict (no id/metadata) or None on failure."""
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": build_user_prompt(passage)}],
                system=VOCAB_PROMPT,
            )
            result = extract_json(msg.content[0].text)

            assert 'entries' in result and isinstance(result['entries'], list)
            assert len(result['entries']) == 4
            assert all('term' in e and 'definition' in e and 'is_target' in e
                       for e in result['entries'])
            tei = result.get('target_entry_index', -1)
            assert 0 <= tei < 4, "target_entry_index out of range"
            assert result['entries'][tei]['is_target'] is True
            assert 'error_original' in result
            assert result['error_original'] in result['entries'][tei]['definition'], \
                "error_original not found in target definition"
            assert 'error_correct' in result
            assert 'explanation' in result

            return result

        except (json.JSONDecodeError, AssertionError, KeyError, ValueError) as e:
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


MODE_GENERATORS = {
    'passage_click': generate_passage_click,
    'sentence_click': generate_sentence_click,
    'vocab':          generate_vocab,
}


def load_existing(path: pathlib.Path) -> dict:
    """Return {id: question} for already-generated questions."""
    if not path.exists():
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {q['id']: q for q in data.get('questions', [])}


def get_mode(q: dict) -> str:
    """Return the mode of a question (defaults to 'mc' for legacy questions)."""
    return q.get('mode', 'mc')


def process_domain(client: anthropic.Anthropic, domain_code: str,
                   count: int | None, resume: bool, mode: str = 'mc'):
    src = DATA / f"{domain_code}_passages.json"
    if not src.exists():
        print(f"  SKIP: {src} not found")
        return

    with open(src, encoding='utf-8') as f:
        data = json.load(f)
    passages = data['passages']

    dst = DATA / f"{domain_code}_spot.json"

    # Always load all existing questions to preserve them when appending
    all_existing: list = []
    if dst.exists():
        with open(dst, encoding='utf-8') as f:
            existing_data = json.load(f)
        all_existing = existing_data.get('questions', [])

    if resume:
        # Determine which passages for this mode are already done
        same_mode = [q for q in all_existing if get_mode(q) == mode]
        questions = list(all_existing)  # start with everything

        if mode == 'mc':
            done_ids = {q['id'] for q in same_mode}
            todo = [p for p in passages if p['id'] not in done_ids]
        else:
            done_passage_ids = {q['source_passage_id'] for q in same_mode
                                if 'source_passage_id' in q}
            todo = [p for p in passages if p['id'] not in done_passage_ids]
    else:
        # Start fresh for this mode; preserve questions of other modes
        other_mode_qs = [q for q in all_existing if get_mode(q) != mode]
        questions = list(other_mode_qs)
        todo = list(passages)

    # Sequential ID counter for new modes
    seq_n = 1
    if mode != 'mc':
        existing_mode_count = sum(1 for q in questions if get_mode(q) == mode)
        seq_n = existing_mode_count + 1

    if count:
        random.shuffle(todo)
        todo = todo[:count]

    if not todo:
        print(f"  {domain_code} [{mode}]: nothing to do ({len(all_existing)} total existing)")
        return

    generate_fn = generate_question if mode == 'mc' else MODE_GENERATORS[mode]

    print(f"\n  {domain_code} [{mode}]: generating {len(todo)} questions "
          f"(+{len(all_existing)} existing)...")

    errors = 0

    for i, passage in enumerate(todo, 1):
        print(f"    [{i}/{len(todo)}] {passage['chapter_title'][:50]}...", end=' ', flush=True)
        result = generate_fn(client, passage)
        if result:
            if mode == 'mc':
                # generate_question returns a complete question dict with id
                questions.append(result)
            else:
                prefix = MODE_ID_PREFIXES[mode]
                q = {
                    "id":                f"{domain_code}-{prefix}-{seq_n:04d}",
                    "mode":              mode,
                    "domain_code":       passage['domain_code'],
                    "domain_name":       passage['domain_name'],
                    "chapter_file":      passage['chapter_file'],
                    "chapter_title":     passage['chapter_title'],
                    "section":           passage.get('section', ''),
                    "passage_type":      passage['passage_type'],
                    "source_passage_id": passage['id'],
                    **result,
                }
                questions.append(q)
                seq_n += 1
            print("OK")
        else:
            errors += 1
            print("FAILED")
        # Brief pause to avoid hammering rate limits
        time.sleep(0.3)

    # Write output
    out = {
        "domain_code":     domain_code,
        "domain_name":     DOMAIN_NAMES[domain_code],
        "total_questions": len(questions),
        "questions":       questions,
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
    parser.add_argument('--mode', default='mc',
                        choices=['mc', 'passage_click', 'sentence_click', 'vocab'],
                        help='Question mode to generate (default: mc)')
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
        process_domain(client, code, args.count, args.resume, args.mode)

    print("\nDone.")


if __name__ == '__main__':
    main()
