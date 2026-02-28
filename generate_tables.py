"""
generate_tables.py

Extracts comparison tables from domain HTML files, calls Claude to identify
the most testable cell and generate 3 plausible distractors, then writes
{DOMAIN}_tables.json to data/.

Run:
  python generate_tables.py --domain BPSY --count 50
  python generate_tables.py --domain LDEV --count 50
  python generate_tables.py --domain PETH --count 50
  python generate_tables.py --all --count 50
  python generate_tables.py --all --resume

Options:
  --domain CODE   Single domain (BPSY | LDEV | PETH)
  --all           Run all three domains sequentially
  --count N       Max tables per domain (default 50)
  --resume        Skip tables already present in output JSON
  --api-key KEY   Anthropic API key (overrides env / .env)
"""

import json, pathlib, argparse, time, random, sys, os, re
import anthropic
from bs4 import BeautifulSoup

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA = pathlib.Path("data")

DOMAIN_DIRS = {
    "BPSY": pathlib.Path("content/domain7"),
    "LDEV": pathlib.Path("content/domain2"),
    "PETH": pathlib.Path("content/domain9"),
}

DOMAIN_NAMES = {
    "BPSY": "Biopsychology",
    "LDEV": "Lifespan & Developmental Stages",
    "PETH": "Psychopharmacology & Ethics",
}

# ── Glossary-like table headers to skip ───────────────────────────────────────
GLOSSARY_HEADERS = {
    frozenset(["term", "definition"]),
    frozenset(["term", "description"]),
    frozenset(["key term", "definition"]),
    frozenset(["concept", "definition"]),
    frozenset(["word", "definition"]),
}

# ── Claude system prompt ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert EPPP (Examination for Professional Practice in Psychology) content creator.
You receive a comparison table from a psychology study guide. Your task is to turn it into a fill-in-the-blank drill question.

Instructions:
1. Identify the single MOST TESTABLE cell — choose a cell that is:
   - Factually specific (not vague or generic)
   - Likely to be confused with adjacent values in the same column
   - Clinically or conceptually important for the EPPP exam
2. Generate exactly 3 plausible DISTRACTORS. Distractors must:
   - Come from the same column's other values, OR closely related domain content
   - Be distinct from the correct answer and from each other
   - Sound plausible enough to cause real confusion
3. Write a clear 1-2 sentence explanation of why the correct answer is correct.

Return ONLY valid JSON (no markdown, no extra text):
{
  "blank_row": <0-based row index in rows array>,
  "blank_col": <0-based column index in headers array>,
  "correct_value": "<exact text from the cell>",
  "options": ["correct", "distractor1", "distractor2", "distractor3"],
  "correct_option_index": 0,
  "explanation": "<clear explanation>"
}

Rules:
- options[correct_option_index] MUST equal correct_value exactly.
- Shuffle the correct answer position — don't always put it at index 0.
- All 4 options must be distinct strings.
- blank_row and blank_col must be valid indices.
- correct_value must match the cell text exactly (same case, same punctuation)."""


# ── HTML extraction ────────────────────────────────────────────────────────────
def get_section(tag) -> str:
    """Return the nearest preceding h2 or h3 text before `tag`."""
    for sibling in tag.find_all_previous(['h2', 'h3']):
        text = sibling.get_text(separator=' ', strip=True)
        if text:
            return text
    return ''


def cell_text(td) -> str:
    """Return clean text from a td/th element."""
    return td.get_text(separator=' ', strip=True)


def extract_tables_from_file(filepath: pathlib.Path, domain_code: str,
                              chapter_title: str) -> list[dict]:
    """Parse all valid tables from an HTML file and return table dicts."""
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    tables = []
    for table_el in soup.find_all('table'):
        rows = table_el.find_all('tr')
        if not rows:
            continue

        # Extract headers from first row (th or td)
        header_cells = rows[0].find_all(['th', 'td'])
        headers = [cell_text(c) for c in header_cells]

        # Skip tables with fewer than 2 columns
        if len(headers) < 2:
            continue

        # Extract data rows (skip header row)
        data_rows = []
        for tr in rows[1:]:
            cells = tr.find_all(['td', 'th'])
            if not cells:
                continue
            row = [cell_text(c) for c in cells]
            # Pad/trim to match header count
            while len(row) < len(headers):
                row.append('')
            row = row[:len(headers)]
            data_rows.append(row)

        # Skip if < 2 data rows
        if len(data_rows) < 2:
            continue

        section = get_section(table_el)

        tables.append({
            'chapter_file':  filepath.name,
            'chapter_title': chapter_title,
            'section':       section,
            'domain_code':   domain_code,
            'domain_name':   DOMAIN_NAMES[domain_code],
            'headers':       headers,
            'rows':          data_rows,
        })

    return tables


def get_chapter_title(filepath: pathlib.Path) -> str:
    """Extract page title or first h1 from an HTML file."""
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    title_tag = soup.find('title')
    if title_tag:
        text = title_tag.get_text(strip=True)
        # Strip common suffixes like " | MasteryPage"
        text = re.sub(r'\s*[|—–-].*$', '', text).strip()
        if text:
            return text
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    return filepath.stem.replace('-', ' ').title()


def collect_all_tables(domain_code: str) -> list[dict]:
    """Walk domain directory and collect all valid tables."""
    content_dir = DOMAIN_DIRS[domain_code]
    if not content_dir.exists():
        print(f"  SKIP: {content_dir} not found")
        return []

    all_tables = []
    for html_file in sorted(content_dir.glob('*.html')):
        if html_file.name == 'index.html':
            continue
        chapter_title = get_chapter_title(html_file)
        file_tables = extract_tables_from_file(html_file, domain_code, chapter_title)
        if file_tables:
            print(f"    {html_file.name}: {len(file_tables)} tables")
        all_tables.extend(file_tables)

    return all_tables


# ── Claude API call ────────────────────────────────────────────────────────────
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
        "Set ANTHROPIC_API_KEY in your environment, create a .env file with\n"
        "  ANTHROPIC_API_KEY=sk-ant-...\n"
        "or pass --api-key sk-ant-..."
    )


def extract_json(text: str) -> dict:
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


def build_user_prompt(table: dict) -> str:
    """Build the prompt string for a single table."""
    headers_str = ' | '.join(table['headers'])
    rows_str = '\n'.join(
        ' | '.join(row) for row in table['rows']
    )
    return (
        f"Domain: {table['domain_name']}\n"
        f"Chapter: {table['chapter_title']}\n"
        f"Section: {table['section']}\n\n"
        f"Table headers: {headers_str}\n\n"
        f"Table rows:\n{rows_str}\n\n"
        "Generate a fill-in-the-blank question for this table."
    )


def validate_result(result: dict, table: dict) -> None:
    """Raise AssertionError if result is invalid."""
    headers = table['headers']
    rows    = table['rows']

    br = result.get('blank_row', -1)
    bc = result.get('blank_col', -1)
    assert isinstance(br, int) and 0 <= br < len(rows), \
        f"blank_row {br} out of range [0, {len(rows)-1}]"
    assert isinstance(bc, int) and 0 <= bc < len(headers), \
        f"blank_col {bc} out of range [0, {len(headers)-1}]"

    cv = result.get('correct_value', '').strip()
    cell = rows[br][bc].strip()
    assert cv.lower() == cell.lower(), \
        f"correct_value {cv!r} does not match cell {cell!r}"

    options = result.get('options', [])
    assert len(options) == 4, f"Expected 4 options, got {len(options)}"
    assert len(set(options)) == 4, "Options must all be distinct"

    coi = result.get('correct_option_index', -1)
    assert 0 <= coi <= 3, f"correct_option_index {coi} out of range"
    assert options[coi].strip() == cv, \
        f"options[{coi}]={options[coi]!r} != correct_value={cv!r}"

    assert result.get('explanation', '').strip(), "Explanation must not be empty"


def generate_question(client: anthropic.Anthropic, table: dict,
                      retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            msg = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": build_user_prompt(table)}],
                system=SYSTEM_PROMPT,
            )
            raw = msg.content[0].text.strip()
            result = extract_json(raw)
            validate_result(result, table)
            return result

        except (json.JSONDecodeError, AssertionError, KeyError, ValueError) as e:
            print(f"    Parse/validation error (attempt {attempt+1}): {e}")
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


# ── Resume key ────────────────────────────────────────────────────────────────
def resume_key(q: dict) -> tuple:
    return (q['chapter_file'], q['blank_row'], q['blank_col'])


def table_key(table: dict, br: int, bc: int) -> tuple:
    return (table['chapter_file'], br, bc)


# ── Domain processing ─────────────────────────────────────────────────────────
def process_domain(client: anthropic.Anthropic, domain_code: str,
                   count: int, resume: bool):
    print(f"\n-- {domain_code} ({DOMAIN_NAMES[domain_code]}) --")

    # Collect tables from HTML
    print("  Scanning HTML files...")
    all_tables = collect_all_tables(domain_code)
    print(f"  Found {len(all_tables)} valid tables total")

    if not all_tables:
        print("  Nothing to process.")
        return

    dst = DATA / f"{domain_code}_tables.json"

    # Load existing questions
    existing_questions: list[dict] = []
    if dst.exists():
        with open(dst, encoding='utf-8') as f:
            existing_data = json.load(f)
        existing_questions = existing_data.get('questions', [])

    if resume:
        done_keys = {resume_key(q) for q in existing_questions}
        questions = list(existing_questions)
    else:
        done_keys = set()
        questions = []

    # Filter to tables not yet done
    todo = []
    for t in all_tables:
        # We don't know blank_row/bc yet, so check by chapter_file for resume
        # (a more precise filter happens after generation — this just avoids re-running same file)
        # Actually we need to match by chapter_file + blank_row + blank_col post-generation.
        # For now filter by chapter_file only when resuming to avoid duplicates from same file.
        pass  # collect all, dedup after

    # For resume: track which (file, row, col) combos are done
    todo = list(all_tables)

    # Shuffle for variety
    random.shuffle(todo)

    # Cap
    todo = todo[:max(count * 3, 150)]  # over-sample to account for failures + skips

    needed = count - len(questions) if resume else count

    print(f"  Generating up to {needed} new questions...")
    seq_n = len(existing_questions) + 1 if resume else 1
    errors = 0
    generated = 0

    for i, table in enumerate(todo, 1):
        if generated >= needed:
            break

        print(f"    [{i}/{len(todo)}] {table['chapter_file']} / {table['section'][:40] or 'n/a'}...",
              end=' ', flush=True)

        result = generate_question(client, table)
        if not result:
            errors += 1
            print("FAILED")
            time.sleep(0.3)
            continue

        # Check for duplicate (same file + blank_row + blank_col)
        rk = table_key(table, result['blank_row'], result['blank_col'])
        if rk in done_keys:
            print("SKIP (duplicate)")
            continue
        done_keys.add(rk)

        # Build rows with BLANK substituted for display
        display_rows = [list(row) for row in table['rows']]
        display_rows[result['blank_row']][result['blank_col']] = 'BLANK'

        q = {
            "id":                   f"{domain_code}-TBL-{seq_n:04d}",
            "mode":                 "table_fill",
            "domain_code":          domain_code,
            "domain_name":          DOMAIN_NAMES[domain_code],
            "chapter_file":         table['chapter_file'],
            "chapter_title":        table['chapter_title'],
            "section":              table['section'],
            "headers":              table['headers'],
            "rows":                 display_rows,
            "blank_row":            result['blank_row'],
            "blank_col":            result['blank_col'],
            "correct_value":        result['correct_value'],
            "options":              result['options'],
            "correct_option_index": result['correct_option_index'],
            "explanation":          result['explanation'],
        }
        questions.append(q)
        seq_n += 1
        generated += 1
        print("OK")
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

    print(f"  -> {dst.name}: {len(questions)} questions written ({errors} failures)")


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--domain', choices=list(DOMAIN_DIRS.keys()),
                       help='Single domain (BPSY | LDEV | PETH)')
    group.add_argument('--all', action='store_true', help='All three domains')
    parser.add_argument('--count', type=int, default=50,
                        help='Max questions per domain (default 50)')
    parser.add_argument('--resume', action='store_true',
                        help='Skip tables already in output JSON')
    parser.add_argument('--api-key', default=None,
                        help='Anthropic API key (overrides env / .env)')
    args = parser.parse_args()

    api_key = load_api_key(args.api_key)
    client = anthropic.Anthropic(api_key=api_key)

    domains = list(DOMAIN_DIRS.keys()) if args.all else [args.domain]

    for code in domains:
        process_domain(client, code, args.count, args.resume)

    print("\nRebuilding table_data.js bundle...")
    import subprocess
    subprocess.run([sys.executable, 'build_table_bundle.py'], check=False)

    print("\nDone.")


if __name__ == '__main__':
    main()
