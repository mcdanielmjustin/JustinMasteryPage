"""
generate_brain_questions.py
Generates EPPP-grounded, high-difficulty brain-pathology questions
for the Brain Pathology 3.0 module.

Sources:
  - EPPP-Domain-Design anchor points (Domain 7 Biopsychology, Domain 3 Clinical)
  - JustinQuestionsDatabase domain JSON files (PHY, PPA, CLI, LIF, PAS, LEA)

Output:
  - JustinQuestionsDatabase/data/brain/brain_pathology_30.json  (canonical store)
  - mastery-page/data/brain_data.js                             (synced questions)

Usage:
  python generate_brain_questions.py              # generate 20 questions
  python generate_brain_questions.py --count 60   # generate 60 questions
  python generate_brain_questions.py --dry-run    # preview prompt only
"""

import argparse, json, os, random, re, sys

# ── Paths ─────────────────────────────────────────────────────────────────────
API_KEY_FILE   = r"C:\Users\mcdan\JustinQuestionsDatabase\api_key.txt"
BRAIN_DATA_JS  = r"C:\Users\mcdan\mastery-page\data\brain_data.js"
CANON_OUT      = r"C:\Users\mcdan\JustinQuestionsDatabase\data\brain\brain_pathology_30.json"
DOMAINS_DIR    = r"C:\Users\mcdan\JustinQuestionsDatabase\data\domains"
ANCHOR_D7      = r"C:\Users\mcdan\Desktop\EPPP_Domain_Design\anchor_points_by_domain\Domain_7_Biopsychology.txt"
ANCHOR_D3      = r"C:\Users\mcdan\Desktop\EPPP_Domain_Design\anchor_points_by_domain\Domain_3_Clinical_Psychopathology.txt"
MODEL          = "claude-sonnet-4-6"

# ── Valid brain region keys (must match brain_regions_manifest.json) ──────────
BRAIN_REGIONS = [
    "frontal_lobe", "prefrontal_cortex", "brocas_area", "motor_cortex",
    "parietal_lobe", "somatosensory_cortex", "temporal_lobe", "wernickes_area",
    "occipital_lobe", "insula", "cingulate_gyrus", "medial_frontal",
    "thalamus", "hippocampus", "amygdala", "caudate", "putamen",
    "globus_pallidus", "nucleus_accumbens", "brainstem", "midbrain",
    "pons", "medulla", "hypothalamus", "substantia_nigra", "vta",
    "pituitary", "olfactory_bulb", "corpus_callosum", "cerebellum",
]

# Regions that need more coverage (currently zero or very low)
PRIORITY_REGIONS = [
    "pons", "medulla", "vta", "globus_pallidus", "pituitary",
    "nucleus_accumbens", "putamen", "medial_frontal", "cingulate_gyrus", "insula",
]

CATEGORIES = [
    "aphasia", "motor", "memory", "visual", "sensory", "executive",
    "vascular", "subcortical", "neurotransmitter", "psychiatric",
    "developmental", "assessment", "learning",
]

DOMAIN_CONFIG = {
    "PHY.json": {"angle": "neuroanatomy, neurotransmitters, vascular syndromes, neurological disorders", "n": 6},
    "PPA.json": {"angle": "schizophrenia (PFC/dopamine), OCD (caudate/orbitofrontal), depression (amygdala/vmPFC/cingulate), PTSD (amygdala/hippocampus/vmPFC), ADHD (PFC/caudate), addiction (VTA/nucleus accumbens), autism (amygdala)", "n": 6},
    "CLI.json": {"angle": "stroke, TBI, neurocognitive disorders, aphasia syndromes, apraxia, agnosia", "n": 3},
    "LIF.json": {"angle": "Alzheimer's (entorhinal/hippocampus), neurodevelopmental (ADHD/autism brain changes), brain aging", "n": 2},
    "PAS.json": {"angle": "neuropsychological tests localizing lesions: WCST→PFC, Trail Making→frontal, Rey-O→parietal/temporal, digit span→working memory", "n": 2},
    "LEA.json": {"angle": "brain circuits for learning: hippocampus (declarative), cerebellum (conditioned responses), striatum (habit/procedural), amygdala (fear conditioning)", "n": 2},
}

NEURO_KW = [
    "brain","neuron","cortex","lobe","hippo","amygdala","cerebel","thalamus",
    "hypothal","dopamine","serotonin","gaba","acetylcholine","striatum",
    "basal ganglia","limbic","prefrontal","neurotransmit","stroke","aphasia",
    "seizure","memory","frontal","temporal","parietal","occipital","insula",
    "caudate","putamen","substantia","schizophreni","alzheimer","parkinson",
    "dementia","lesion","atrophy","addiction","reward","nucleus accumbens",
    "depression","anxiety","neuroimaging","fmri","neuropsycholog","executive",
    "working memory","motor cortex","sensory","cerebell","corpus callosum",
    "cingulate","medial temporal","wernicke","broca","ptsd","ocd","autism",
    "adhd","tourette","huntington","lewy","frontotempora",
]

# ── Loaders ───────────────────────────────────────────────────────────────────

def load_api_key():
    return open(API_KEY_FILE).read().strip()

def load_anchor_points():
    """Extract brain-pathology relevant anchor points from Domain 7 and 3."""
    out = []
    for path in [ANCHOR_D7, ANCHOR_D3]:
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        # Extract lines that contain EPPP anchor points (bracketed IDs)
        lines = [l.strip() for l in text.splitlines() if re.match(r'\[', l.strip())]
        # Filter for brain-pathology relevance
        brain_lines = [l for l in lines if any(k in l.lower() for k in NEURO_KW)]
        out.extend(brain_lines)
    random.shuffle(out)
    return out[:80]  # cap to avoid prompt overflow

def load_domain_sample():
    """Load brain-relevant questions from each domain."""
    blocks = []
    for fname, cfg in DOMAIN_CONFIG.items():
        path = os.path.join(DOMAINS_DIR, fname)
        if not os.path.exists(path):
            continue
        qs = json.load(open(path, encoding="utf-8")).get("questions", [])
        relevant = [q for q in qs if any(k in (q.get("question","") + q.get("explanation","")).lower() for k in NEURO_KW)]
        random.shuffle(relevant)
        sample = relevant[:cfg["n"]]
        for q in sample:
            ans = q.get("options", {}).get(q.get("correct_answer",""), "")
            blocks.append(f"[{fname}] Q: {q['question'][:160]} | A: {ans[:120]}")
    return "\n".join(blocks)

def get_existing():
    """Parse existing questions from brain_data.js for dedup and ID tracking."""
    content = open(BRAIN_DATA_JS, encoding="utf-8").read()
    blocks  = re.findall(r'\{\s*\"id\":\s*\"BRAIN-\d+\".*?\}(?=\s*[,\]])', content, re.DOTALL)
    ids     = set(re.findall(r'"(BRAIN-\d+)"', content))
    # Summarise existing targets to avoid repetition
    targets = []
    for b in blocks:
        m = re.search(r'"target_region":\s*"([^"]+)"', b)
        if m: targets.append(m.group(1))
    from collections import Counter
    return ids, Counter(targets)

def next_id_num(existing_ids):
    nums = [int(re.search(r'\d+', i).group()) for i in existing_ids if re.search(r'\d+', i)]
    return max(nums) + 1 if nums else 106

# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(count, start_num, anchor_points, domain_samples, target_counter):
    regions_str     = json.dumps(BRAIN_REGIONS, indent=2)
    categories_str  = ", ".join(CATEGORIES)
    priority_str    = ", ".join(PRIORITY_REGIONS)
    anchor_str      = "\n".join(f"  • {a}" for a in anchor_points[:60])
    overused        = [r for r, n in target_counter.items() if n >= 5]
    overused_str    = ", ".join(overused) if overused else "none"

    return f"""You are writing HARD brain-pathology quiz questions for psychology doctoral candidates preparing for the EPPP exam.

Each question presents a clinical scenario and the student must identify the specific brain region most responsible. Questions must be genuinely difficult — EPPP mastery-level, not introductory.

## Available brain region keys (use ONLY these exact strings):
{regions_str}

## Priority: Give extra questions to these under-covered regions:
{priority_str}

## Avoid over-using these already well-covered regions:
{overused_str}

## Question types:
- **deficit_to_location**: Clinical deficit/symptom pattern → student identifies damaged region
- **case_to_location**: Full clinical vignette → student identifies affected region

## Category options: {categories_str}

## EPPP Anchor Points (factual grounding — your questions MUST be consistent with these):
{anchor_str}

## Domain source material for clinical scenarios:
{domain_samples}

## DIFFICULTY REQUIREMENTS — Every question must use at least one of:
1. **Syndrome disambiguation**: Two clinically similar syndromes localize to different regions (e.g., transcortical motor aphasia vs Broca's — both nonfluent, but repetition is intact only in transcortical)
2. **Double dissociation**: Patient A has X but not Y; Patient B has Y but not X — use to localize
3. **Vascular + deficit combination**: Specific artery territory + specific deficit pattern together
4. **Neuropsychological test localization**: Test performance pattern (WCST, Trail Making, Rey-O, digit span, verbal fluency, confrontation naming) → lesion site
5. **Psychiatric brain-change question**: A psychiatric disorder's specific neuroanatomical correlate (not just "which region is abnormal in depression" — require knowing the direction and clinical consequence)
6. **Neurotransmitter-region-disorder triple**: Requires knowing neurotransmitter + brain region + clinical consequence together
7. **Lateralization specificity**: Left vs right hemisphere consequences of the same lesion type
8. **Cross-domain integration**: Combine knowledge from two different EPPP domains to answer

## Output — a JSON array of exactly {count} question objects:
```
[
  {{
    "id": "BRAIN-{start_num:03d}",
    "type": "case_to_location",
    "category": "psychiatric",
    "domain_source": "PPA",
    "difficulty": "hard",
    "question": "...",
    "target_region": "caudate",
    "distractor_regions": ["prefrontal_cortex", "amygdala", "putamen"],
    "explanation": "..."
  }},
  ...
]
```

## Rules:
- All region keys must be from the available list — no exceptions
- Exactly 3 distractor_regions per question, all from the available list
- Distractors must be PLAUSIBLE — regions that could be confused with the target
- Do NOT repeat a target_region more than 3 times across this batch
- Prioritize the under-covered regions listed above
- Explanations: 2–3 concise sentences (under 65 words total) — why target is correct and why the most tempting distractor is wrong
- Add `"difficulty": "hard"` and `"domain_source"` to every question
- Number IDs sequentially from BRAIN-{start_num:03d}
- Output ONLY the raw JSON array — no markdown fences, no preamble
"""

# ── API call ──────────────────────────────────────────────────────────────────

def call_claude(api_key, prompt):
    import urllib.request
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())["content"][0]["text"]

# ── Output ────────────────────────────────────────────────────────────────────

def save_to_canon(new_qs):
    """Append new questions to canonical JSON store in JustinQuestionsDatabase."""
    os.makedirs(os.path.dirname(CANON_OUT), exist_ok=True)
    existing = []
    if os.path.exists(CANON_OUT):
        existing = json.load(open(CANON_OUT, encoding="utf-8"))
    existing_ids = {q["id"] for q in existing}
    added = [q for q in new_qs if q["id"] not in existing_ids]
    combined = existing + added
    with open(CANON_OUT, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"Canonical store: {CANON_OUT}")
    print(f"  Total questions: {len(combined)} ({len(added)} new added)")
    return combined

def sync_to_brain_data(all_canon_qs):
    """Replace the questions array in brain_data.js with all canonical questions."""
    with open(BRAIN_DATA_JS, encoding="utf-8") as f:
        content = f.read()

    # Build the new questions JSON
    new_json = ",\n".join(
        "    " + json.dumps(q, indent=4).replace("\n", "\n    ")
        for q in all_canon_qs
    )

    # Replace the questions array
    new_content = re.sub(
        r'"questions":\s*\[.*?\]',
        f'"questions": [\n{new_json}\n  ]',
        content,
        flags=re.DOTALL,
        count=1,
    )
    with open(BRAIN_DATA_JS, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Synced {len(all_canon_qs)} questions to brain_data.js")

def inject_to_brain_data(new_qs):
    """Append-only: add new questions to brain_data.js without full replacement."""
    with open(BRAIN_DATA_JS, encoding="utf-8") as f:
        content = f.read()
    insert_marker = "\n  ]\n};"
    if insert_marker not in content:
        print("ERROR: Could not find injection point")
        sys.exit(1)
    new_json = ",\n".join(
        "    " + json.dumps(q, indent=4).replace("\n", "\n    ")
        for q in new_qs
    )
    replacement = ",\n" + new_json + "\n  ]\n};"
    with open(BRAIN_DATA_JS, "w", encoding="utf-8") as f:
        f.write(content.replace(insert_marker, replacement, 1))
    print(f"Appended {len(new_qs)} questions to brain_data.js")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count",   type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key        = load_api_key()
    anchor_points  = load_anchor_points()
    domain_samples = load_domain_sample()
    existing_ids, target_counter = get_existing()
    start_num      = next_id_num(existing_ids)

    print(f"Existing questions  : {len(existing_ids)}")
    print(f"Anchor points loaded: {len(anchor_points)}")
    print(f"Generating          : {args.count} new hard questions (from BRAIN-{start_num:03d})")
    print(f"Priority regions    : {', '.join(PRIORITY_REGIONS)}")

    prompt = build_prompt(args.count, start_num, anchor_points, domain_samples, target_counter)

    if args.dry_run:
        print("\n--- PROMPT PREVIEW ---")
        print(prompt[:5000].encode("ascii", errors="replace").decode())
        return

    print("Calling Claude API...")
    raw = call_claude(api_key, prompt)

    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        print("ERROR: No JSON array found in response")
        print(raw[:600])
        sys.exit(1)

    try:
        new_qs = json.loads(match.group())
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(raw[:800])
        sys.exit(1)

    # Validate
    valid, skipped = [], []
    for q in new_qs:
        if q.get("target_region") not in BRAIN_REGIONS:
            skipped.append(f"  SKIP {q.get('id')}: bad target '{q.get('target_region')}'")
            continue
        bad_d = [d for d in q.get("distractor_regions", []) if d not in BRAIN_REGIONS]
        if bad_d:
            skipped.append(f"  SKIP {q.get('id')}: bad distractor(s) {bad_d}")
            continue
        valid.append(q)

    for s in skipped: print(s)
    print(f"Valid: {len(valid)}/{len(new_qs)}")
    if not valid:
        sys.exit(1)

    # Save canonical + inject to brain_data.js
    save_to_canon(valid)
    inject_to_brain_data(valid)

    from collections import Counter
    print(f"\nBy domain   : {dict(Counter(q.get('domain_source','?') for q in valid))}")
    print(f"By category : {dict(Counter(q.get('category','?') for q in valid))}")
    print(f"By target   : {dict(Counter(q.get('target_region') for q in valid))}")
    print("\nDone.")

if __name__ == "__main__":
    main()
