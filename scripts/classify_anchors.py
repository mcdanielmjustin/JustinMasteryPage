"""
classify_anchors.py  (Phase 1 — NEW)

Classify each anchor point and determine embed-eligibility.
Three-pass approach:
  Pass 1: Regex heuristics (~85% classified with high confidence)
  Pass 2: API batch for ambiguous anchors (claude-sonnet, cheap classification)
  Pass 3: ASPPB KN cross-reference for embed eligibility

Output: scripts/data/anchors_classified.json

Run:
  python scripts/classify_anchors.py --all
  python scripts/classify_anchors.py --domain PMET
  python scripts/classify_anchors.py --regex-only
  python scripts/classify_anchors.py --resume
"""

import json, pathlib, re, sys, argparse, time, os, math
import anthropic

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
MAP_FILE = DATA_DIR / "anchor_chapter_map.json"
OUTPUT_FILE = DATA_DIR / "anchors_classified.json"
BATCH_STATE_FILE = DATA_DIR / "classify_batch_state.json"
ASPPB_FILE = pathlib.Path("C:/Users/mcdan/PassEPPP-website/js/asppb-subareas.js")

CLASSIFY_BATCH_SIZE = 25  # anchors per API request


# ══════════════════════════════════════════════════════════════════════
# Regex patterns
# ══════════════════════════════════════════════════════════════════════

# Exam strategy: test-answer framing language
EXAM_STRATEGY_RES = [re.compile(p, re.IGNORECASE) for p in [
    r'would be un(?:ethical|acceptable|professional)',
    r'is (?:not )?acceptable\b.*?\b(?:as long as|because|if|since|only)',
    r'(?:acted|behaved) (?:un)?ethically (?:only if|because|when)',
    r'\bis not acceptable\b',
    r'\bviolated? (?:ethical|the ethics|standard)',
    r'\bviolation of\b',
    r'\bis un(?:ethical|acceptable|professional)\b',
    r'\bhas acted (?:un)?ethically',
    r'would (?:not )?be (?:a )?violation',
    r'would (?:not )?be (?:considered )?(?:un)?ethical',
    r'\bthis is (?:not )?(?:ethical|acceptable)\b',
    r'\bmost (?:appropriate|ethical) (?:course of action|response)\b',
    r'\bbest course of action\b',
]]

# Named character: Dr./Mr./Mrs./Ms. + capitalized name
NAMED_CHAR_RE = re.compile(
    r'\b(?:Dr|Mr|Mrs|Ms)\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
)

# Famous researchers — references to these are educational, not scenarios.
# Only names commonly cited WITH a title prefix in psych literature.
FAMOUS_NAMES = {
    'pavlov', 'piaget', 'freud', 'skinner', 'bandura', 'rogers', 'maslow',
    'erikson', 'kohlberg', 'vygotsky', 'ainsworth', 'bowlby', 'beck',
    'ellis', 'jung', 'adler', 'wechsler', 'binet', 'rorschach',
    'cattell', 'eysenck', 'allport', 'milgram', 'zimbardo', 'asch',
    'festinger', 'seligman', 'wolpe', 'thorndike', 'watson', 'harlow',
    'chomsky', 'broca', 'wernicke', 'luria', 'sperry', 'kahneman',
    'tversky', 'damasio', 'lazarus', 'selye', 'cannon', 'darwin',
    'holland', 'super', 'roe', 'lewin', 'fiedler', 'hersey', 'blanchard',
    'minuchin', 'haley', 'satir', 'bowen', 'kerr', 'yalom', 'frankl',
    'perls', 'linehan', 'hayes', 'meichenbaum', 'mahoney', 'kohut',
    'winnicott', 'klein', 'bion', 'horney', 'sullivan', 'may',
    'wundt', 'james', 'titchener', 'fechner', 'weber', 'helmholtz',
    'galton', 'stern', 'terman', 'thurstone', 'guilford', 'spearman',
    'gardner', 'sternberg', 'goleman', 'cronbach', 'campbell',
    'rosenthal', 'barnum', 'kuder', 'richardson',
}

# Standard concept: definitional / conceptual language
STANDARD_CONCEPT_RES = [re.compile(p, re.IGNORECASE) for p in [
    r'\brefers to\b',
    r'\bis defined as\b',
    r'\boccurs when\b',
    r'\bis the term (?:for|used)',
    r'\bis (?:also )?(?:called|known as|referred to as)\b',
    r'\bis characterized by\b',
    r'\bis based on (?:the )?(?:premise|assumption|principle|idea|concept)\b',
    r'\bis associated with\b',
    r'\bis a (?:type|form|kind|measure|method|model|theory|component|process|function) of\b',
    r'\baccording to\b.*?\b(?:theory|model|principle|hypothesis)\b',
    r'\bthe most (?:effective|common|likely|appropriate|important|reliable|valid)\b',
    r'\binvolves? (?:the |a )?(?:use|process|presentation|pairing|administration)\b',
    r'\b(?:predicts?|suggests?|indicates?|demonstrates?) that\b',
    r'\bresults? (?:in|from)\b',
    r'\bleads? to\b',
    r'\bis (?:most )?(?:likely|commonly|often|closely|typically)\b',
    r'\b(?:increases?|decreases?) (?:when|as|with|the)\b',
    r'\b(?:positive|negative) (?:reinforcement|punishment|correlation|relationship)\b',
    r'\bconditioned (?:stimulus|response)\b',
    r'\bunconditioned (?:stimulus|response)\b',
]]

# Domain → ASPPB KN fallback (when chapter-level match fails)
DOMAIN_TO_KN = {
    'PMET': ['KN6', 'KN7', 'KN8', 'KN9', 'KN10', 'KN34', 'KN35', 'KN36', 'KN37', 'KN38'],
    'LDEV': ['KN17', 'KN18', 'KN19', 'KN20', 'KN21'],
    'CPAT': ['KN26', 'KN27'],
    'PTHE': ['KN28', 'KN29', 'KN30', 'KN31', 'KN32', 'KN33'],
    'SOCU': ['KN11', 'KN12', 'KN13', 'KN14', 'KN15'],
    'WDEV': ['KN16'],
    'BPSY': ['KN1', 'KN4', 'KN5'],
    'CASS': ['KN22', 'KN23', 'KN24', 'KN25', 'KN26'],
    'PETH': ['KN2', 'KN3', 'KN39', 'KN40', 'KN41', 'KN42', 'KN43', 'KN44'],
}


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════

def load_api_key():
    if os.environ.get('ANTHROPIC_API_KEY'):
        return os.environ['ANTHROPIC_API_KEY']
    for p in [pathlib.Path('.env'), pathlib.Path.home() / '.env']:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('ANTHROPIC_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY or create a .env file.")


def has_non_famous_name(content):
    """True if content has Dr./Mr./Mrs./Ms. + a name NOT in the famous-researchers list."""
    for m in NAMED_CHAR_RE.finditer(content):
        full_name = m.group(1)
        surname = full_name.split()[-1].lower()
        if surname not in FAMOUS_NAMES:
            return True
        # Even a famous surname in scenario-action context → scenario
        after = content[m.end():]
        if re.match(r'\s+(?:should|will|is to|agrees?|decides?|refuses?|may|can|tells|asks)',
                     after, re.IGNORECASE):
            return True
        if re.match(r"'s\s+(?:client|patient|decision|evaluation|requirement|practice)",
                     after, re.IGNORECASE):
            return True
    return False


def classify_regex(content, domain_code):
    """
    Classify anchor by regex heuristics.
    Returns (classification, classification_method).
    """
    has_named = has_non_famous_name(content)
    has_exam = any(p.search(content) for p in EXAM_STRATEGY_RES)
    has_definitional = any(p.search(content) for p in STANDARD_CONCEPT_RES)

    # Priority 1: Named non-famous character → scenario_vignette
    if has_named:
        return 'scenario_vignette', 'regex_name'

    # Priority 2: Exam-strategy framing (no names) → exam_strategy
    if has_exam:
        return 'exam_strategy', 'regex_exam'

    # Priority 3: Clear definitional / conceptual language → standard_concept
    if has_definitional:
        return 'standard_concept', 'regex_definitional'

    # Priority 4: Ethics domains without clear markers → ambiguous (need API)
    if domain_code in ('PETH', 'CASS'):
        return 'ambiguous', 'regex_ethics_unclear'

    # Priority 5: Non-ethics, no scenario signals → standard_concept
    return 'standard_concept', 'regex_default'


# ══════════════════════════════════════════════════════════════════════
# ASPPB KN mapping (Pass 3)
# ══════════════════════════════════════════════════════════════════════

def slugify_chapter(name):
    """Convert ASPPB chapter name → slug matching HTML filenames."""
    s = name.lower()
    s = s.replace(' - ', '-').replace('/', '-').replace('&', 'and')
    s = re.sub(r'[^a-z0-9-]', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def parse_asppb_kn_mapping():
    """Parse ASPPB JS file → {chapter_slug: [KN codes]}."""
    if not ASPPB_FILE.exists():
        print(f"  WARNING: {ASPPB_FILE} not found, using domain-level KN fallback only")
        return {}

    js_text = ASPPB_FILE.read_text(encoding='utf-8')
    slug_to_kn = {}

    kn_re = re.compile(
        r"'(KN\d+)':\s*\{.*?passepppChapters:\s*\[(.*?)\]",
        re.DOTALL
    )
    for m in kn_re.finditer(js_text):
        kn_code = m.group(1)
        chapters_str = m.group(2)
        for name in re.findall(r"'([^']+)'", chapters_str):
            slug = slugify_chapter(name)
            slug_to_kn.setdefault(slug, [])
            if kn_code not in slug_to_kn[slug]:
                slug_to_kn[slug].append(kn_code)

    return slug_to_kn


def get_chapter_slug(chapter_file):
    """'domain1/classical-conditioning.html' → 'classical-conditioning'."""
    if not chapter_file:
        return ''
    return chapter_file.split('/')[-1].replace('.html', '')


def assign_kn_codes(anchor, slug_to_kn):
    """KN codes for an anchor: chapter-level match first, domain fallback second."""
    slug = get_chapter_slug(anchor.get('chapter_file', ''))
    kn_codes = []

    # Exact slug match
    if slug and slug in slug_to_kn:
        kn_codes = list(slug_to_kn[slug])
    else:
        # Fuzzy: check substring containment
        for asppb_slug, kn_list in slug_to_kn.items():
            if slug and (asppb_slug in slug or slug in asppb_slug):
                kn_codes = list(kn_list)
                break

    # Domain-level fallback
    if not kn_codes:
        kn_codes = list(DOMAIN_TO_KN.get(anchor.get('domain_code', ''), []))

    return sorted(set(kn_codes))


# ══════════════════════════════════════════════════════════════════════
# API classification (Pass 2)
# ══════════════════════════════════════════════════════════════════════

CLASSIFY_SYSTEM_PROMPT = """\
You are classifying EPPP (psychology licensing exam) anchor points into three categories.

Categories:
1. **standard_concept** — A generic psychology concept any standard textbook covers. \
Includes: definitions, theories, research findings, brain structures, statistical methods, \
therapy techniques, ethical principles stated as general rules (e.g. "psychologists should \
obtain informed consent").

2. **scenario_vignette** — Contains named characters or specific clinical/professional \
situations that reveal exam question structure. Examples: "Dr. X should...", specific \
person-situation combinations, applied ethics with named individuals.

3. **exam_strategy** — Test-answer framing language that tells how to choose the correct \
option. Examples: "would be unacceptable", "is acceptable as long as", "acted ethically \
only if", "violation of Standard X".

KEY DISTINCTIONS:
- Ethics rules stated generically = standard_concept
- Ethics rules applied to named characters = scenario_vignette
- Famous researcher references (Pavlov, Piaget) = standard_concept
- Test-framing language without named characters = exam_strategy

Each anchor has a compound ID like "PMET:020". Preserve this ID exactly in your response.

Respond with ONLY valid JSON:
{
    "classifications": [
        {"anchor_id": "PMET:020", "classification": "standard_concept", "reasoning": "Defines spontaneous recovery in general terms"}
    ]
}"""


def build_classify_prompt(anchors_batch):
    """Build user prompt for API classification batch."""
    lines = [f"Classify these {len(anchors_batch)} anchor points:\n"]
    for a in anchors_batch:
        key = f"{a['domain_code']}:{a['anchor_id']}"
        lines.append(f"[{key}] {a['content']}")
    return "\n".join(lines)


def poll_and_collect_classify(client, batch_id):
    """Poll batch → {compound_id: {classification, reasoning}}."""
    print("Polling for batch completion...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = (counts.processing + counts.succeeded + counts.errored
                 + counts.canceled + counts.expired)
        print(f"  {batch.processing_status} | "
              f"done={counts.succeeded} processing={counts.processing} "
              f"errored={counts.errored} / {total}")
        if batch.processing_status == "ended":
            break
        time.sleep(30)

    results = {}
    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if m:
                    data = json.loads(m.group(1))
                else:
                    print(f"  WARNING: Could not parse JSON for {result.custom_id}")
                    continue

            for item in data.get("classifications", []):
                aid = item["anchor_id"]
                results[aid] = {
                    "classification": item["classification"],
                    "reasoning": item.get("reasoning", ""),
                }
        else:
            print(f"  ERROR: {result.custom_id} — {result.result.type}")

    return results


# ══════════════════════════════════════════════════════════════════════
# Output
# ══════════════════════════════════════════════════════════════════════

def save_results(results, label="Classification"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    by_class = {}
    eligible = 0
    for r in results:
        c = r.get("classification", "unknown")
        by_class[c] = by_class.get(c, 0) + 1
        if r.get("embed_eligible"):
            eligible += 1

    print(f"\n{label} complete: {len(results)} anchors")
    for cls, count in sorted(by_class.items()):
        print(f"  {cls}: {count}")
    print(f"  embed_eligible: {eligible}")
    print(f"Saved to {OUTPUT_FILE}")


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def finalize_results(classified, ambiguous_resolved, slug_to_kn):
    """Assign KN codes and embed_eligible to all results."""
    results = classified + ambiguous_resolved
    for r in results:
        r["kn_codes"] = assign_kn_codes(r, slug_to_kn)
        r["embed_eligible"] = (
            r["classification"] == "standard_concept"
            and len(r["kn_codes"]) > 0
        )
    return results


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Classify anchor points")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    group.add_argument("--regex-only", action="store_true",
                       help="Run regex pass only (no API calls)")
    group.add_argument("--resume", action="store_true", help="Poll existing batch")
    args = parser.parse_args()

    if not MAP_FILE.exists():
        print(f"ERROR: {MAP_FILE} not found. Run map_anchors.py first.")
        sys.exit(1)

    all_anchors = json.loads(MAP_FILE.read_text(encoding="utf-8"))

    if args.domain:
        all_anchors = [a for a in all_anchors if a["domain_code"] == args.domain.upper()]

    # ── Parse ASPPB KN mapping ────────────────────────────────────────
    slug_to_kn = parse_asppb_kn_mapping()
    if slug_to_kn:
        print(f"Loaded {len(slug_to_kn)} ASPPB chapter→KN mappings")

    # ── Resume mode ───────────────────────────────────────────────────
    if args.resume:
        if not BATCH_STATE_FILE.exists():
            print("ERROR: No batch state found.")
            sys.exit(1)

        api_key = load_api_key()
        client = anthropic.Anthropic(api_key=api_key)
        state = json.loads(BATCH_STATE_FILE.read_text(encoding="utf-8"))

        api_results = poll_and_collect_classify(client, state["batch_id"])
        classified = state["regex_results"]
        ambiguous_lookup = {
            f"{a['domain_code']}:{a['anchor_id']}": a
            for a in state["ambiguous_anchors"]
        }

        resolved = []
        for compound_id, cls_data in api_results.items():
            if compound_id in ambiguous_lookup:
                anchor = ambiguous_lookup.pop(compound_id)
                anchor["classification"] = cls_data["classification"]
                anchor["classification_method"] = "api"
                anchor["classification_reasoning"] = cls_data.get("reasoning", "")
                resolved.append(anchor)

        # Remaining unresolved → default to standard_concept
        for compound_id, anchor in ambiguous_lookup.items():
            print(f"  WARNING: No API result for [{compound_id}], defaulting to standard_concept")
            anchor["classification"] = "standard_concept"
            anchor["classification_method"] = "api_default"
            resolved.append(anchor)

        results = finalize_results(classified, resolved, slug_to_kn)
        save_results(results)
        return

    # ── Require anchors ───────────────────────────────────────────────
    if not all_anchors:
        print("No anchors to classify.")
        return

    # ══════════════════════════════════════════════════════════════════
    # Pass 1: Regex classification
    # ══════════════════════════════════════════════════════════════════
    print(f"Pass 1: Regex classification of {len(all_anchors)} anchors...\n")

    classified = []
    ambiguous = []

    for anchor in all_anchors:
        cls, method = classify_regex(anchor["content"], anchor["domain_code"])
        record = {**anchor, "classification": cls, "classification_method": method}
        if cls == "ambiguous":
            ambiguous.append(record)
        else:
            classified.append(record)

    by_class = {}
    for r in classified:
        by_class[r["classification"]] = by_class.get(r["classification"], 0) + 1

    print(f"  Regex classified: {len(classified)}")
    for cls, count in sorted(by_class.items()):
        print(f"    {cls}: {count}")
    print(f"  Ambiguous (need API): {len(ambiguous)}")

    by_domain = {}
    for a in ambiguous:
        by_domain[a["domain_code"]] = by_domain.get(a["domain_code"], 0) + 1
    if by_domain:
        print(f"  Ambiguous by domain: {dict(sorted(by_domain.items()))}")

    # ── Regex-only mode ───────────────────────────────────────────────
    if args.regex_only:
        results = finalize_results(classified, ambiguous, slug_to_kn)
        save_results(results, "Regex-only classification")
        return

    # ── No ambiguous → done ───────────────────────────────────────────
    if not ambiguous:
        print("\nNo ambiguous anchors — skipping API pass.")
        results = finalize_results(classified, [], slug_to_kn)
        save_results(results)
        return

    # ══════════════════════════════════════════════════════════════════
    # Pass 2: API batch for ambiguous anchors
    # ══════════════════════════════════════════════════════════════════
    api_key = load_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    n_batches = math.ceil(len(ambiguous) / CLASSIFY_BATCH_SIZE)
    batch_requests = []

    for batch_idx in range(n_batches):
        start = batch_idx * CLASSIFY_BATCH_SIZE
        end = start + CLASSIFY_BATCH_SIZE
        batch_anchors = ambiguous[start:end]

        batch_requests.append({
            "custom_id": f"classify_b{batch_idx}",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "system": CLASSIFY_SYSTEM_PROMPT,
                "messages": [{"role": "user",
                              "content": build_classify_prompt(batch_anchors)}],
            },
        })

    print(f"\nPass 2: Submitting batch — {len(batch_requests)} requests "
          f"({len(ambiguous)} ambiguous anchors)...")

    batch = client.messages.batches.create(requests=batch_requests)
    print(f"  Batch ID: {batch.id}")

    # Save state for --resume
    state = {
        "batch_id": batch.id,
        "domain_filter": args.domain or "all",
        "regex_results": classified,
        "ambiguous_anchors": ambiguous,
    }
    BATCH_STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── Poll and collect ──────────────────────────────────────────────
    api_results = poll_and_collect_classify(client, batch.id)

    ambiguous_lookup = {
        f"{a['domain_code']}:{a['anchor_id']}": a for a in ambiguous
    }

    resolved = []
    for compound_id, cls_data in api_results.items():
        if compound_id in ambiguous_lookup:
            anchor = ambiguous_lookup.pop(compound_id)
            anchor["classification"] = cls_data["classification"]
            anchor["classification_method"] = "api"
            anchor["classification_reasoning"] = cls_data.get("reasoning", "")
            resolved.append(anchor)

    for compound_id, anchor in ambiguous_lookup.items():
        print(f"  WARNING: No API result for [{compound_id}], defaulting to standard_concept")
        anchor["classification"] = "standard_concept"
        anchor["classification_method"] = "api_default"
        resolved.append(anchor)

    # ══════════════════════════════════════════════════════════════════
    # Pass 3: KN cross-reference + embed eligibility
    # ══════════════════════════════════════════════════════════════════
    print("\nPass 3: ASPPB KN cross-reference...")
    results = finalize_results(classified, resolved, slug_to_kn)
    save_results(results)


if __name__ == "__main__":
    main()
