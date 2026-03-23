"""
generate_h3_intros.py

Reads empty_h3_inventory.json and calls Claude to generate 1-2 sentence
introductory paragraphs for each h3 → h4 gap.

Output: scripts/data/h3_intros_generated.json

Run:
  python scripts/generate_h3_intros.py --all
  python scripts/generate_h3_intros.py --domain PMET
  python scripts/generate_h3_intros.py --all --resume
"""

import json, pathlib, argparse, time, sys, os
import anthropic

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
INVENTORY_FILE = DATA_DIR / "empty_h3_inventory.json"
OUTPUT_FILE = DATA_DIR / "h3_intros_generated.json"

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

SYSTEM_PROMPT = """\
You are a psychology textbook editor writing introductory sentences for \
section headings in EPPP (Examination for Professional Practice in Psychology) \
study materials.

You will receive:
- The domain name
- The chapter title
- An <h3> heading that currently jumps straight to <h4> subsections with no introduction
- The list of <h4> subheadings that follow

Your task: Write 1-2 concise sentences that introduce the subsections and provide \
a framing context. The sentences will be inserted as a <p> tag immediately after the <h3>.

Rules:
- Write in an authoritative, concise textbook voice
- Frame what the subsections cover and why they matter
- Do NOT begin with "In this section" or "This section" or "Below" or similar meta-references
- Do NOT use bullet points or HTML — plain text only
- Keep between 60 and 500 characters
- 1-2 sentences only

Respond with ONLY the introductory text — no quotes, no JSON, no markdown."""


def load_api_key() -> str:
    """Resolve API key: env var > .env file."""
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']
    for p in [pathlib.Path('.env'), pathlib.Path.home() / '.env']:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('ANTHROPIC_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError(
        "No API key found. Set ANTHROPIC_API_KEY or create a .env file."
    )


def generate_intro(client: anthropic.Anthropic, item: dict, retries: int = 3) -> str | None:
    """Generate a 1-2 sentence intro for one h3 → h4 gap."""
    domain_name = DOMAIN_NAMES.get(item["domain_code"], item["domain_code"])
    h4_list = "\n".join(f"  - {h4}" for h4 in item["h4_children"])

    user_prompt = (
        f"Domain: {domain_name}\n"
        f"Chapter: {item['chapter_title']}\n"
        f"Section heading (h3): {item['h3_text']}\n"
        f"Subsection headings (h4):\n{h4_list}"
    )

    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = msg.content[0].text.strip()

            # Strip any accidental quotes
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1].strip()

            # Validate
            char_count = len(text)
            if char_count < 60:
                raise ValueError(f"Too short ({char_count} chars): {text!r}")
            if char_count > 500:
                raise ValueError(f"Too long ({char_count} chars)")
            if "<" in text or ">" in text:
                raise ValueError("Contains HTML tags")

            sentence_count = text.count(". ") + text.count(".\u201d") + (1 if text.endswith(".") else 0)
            if sentence_count > 3:
                raise ValueError(f"Too many sentences ({sentence_count})")

            banned_starts = ["in this section", "this section", "below,", "below ", "the following"]
            if any(text.lower().startswith(b) for b in banned_starts):
                raise ValueError(f"Starts with banned phrase: {text[:40]}")

            return text

        except anthropic.RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"    Rate limit — waiting {wait}s...")
            time.sleep(wait)
        except (ValueError, KeyError, IndexError) as e:
            print(f"    Validation error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
        except Exception as e:
            print(f"    API error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(3)

    return None


def load_existing() -> dict:
    """Load already-generated intros keyed by file_path:h3_line."""
    if OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        return {f"{r['file_path']}:{r['h3_line']}": r for r in data}
    return {}


def save_results(results: list):
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    # Force utf-8 stdout on Windows
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate h3 intro sentences")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Process all domains")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    parser.add_argument("--resume", action="store_true", help="Skip already-generated items")
    args = parser.parse_args()

    if not INVENTORY_FILE.exists():
        print(f"ERROR: {INVENTORY_FILE} not found. Run scan_empty_h3.py first.")
        sys.exit(1)

    inventory = json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))

    if args.domain:
        code = args.domain.upper()
        if code not in DOMAIN_NAMES:
            print(f"ERROR: Unknown domain {code}")
            sys.exit(1)
        inventory = [item for item in inventory if item["domain_code"] == code]

    if not inventory:
        print("No items to process.")
        return

    existing = load_existing() if args.resume else {}
    results = list(existing.values()) if args.resume else []

    todo = []
    for item in inventory:
        key = f"{item['file_path']}:{item['h3_line']}"
        if args.resume and key in existing:
            continue
        todo.append(item)

    if not todo:
        print("All items already generated (--resume). Nothing to do.")
        return

    print(f"Generating intros for {len(todo)} h3 → h4 gaps...")

    api_key = load_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    for i, item in enumerate(todo, 1):
        key = f"{item['file_path']}:{item['h3_line']}"
        print(f"\n[{i}/{len(todo)}] {item['file_path']}:{item['h3_line']}")
        print(f"  h3: {item['h3_text']}")
        print(f"  h4s: {', '.join(item['h4_children'][:4])}")

        intro = generate_intro(client, item)

        if intro:
            record = {
                **item,
                "generated_intro": intro,
            }
            results.append(record)
            save_results(results)
            print(f"  ✓ {intro[:80]}{'...' if len(intro) > 80 else ''}")
        else:
            print(f"  ✗ FAILED after retries")

    generated = len([r for r in results if "generated_intro" in r])
    print(f"\nDone. {generated} intros saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
