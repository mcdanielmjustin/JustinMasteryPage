"""
recalibrate_streak.py
Recalibrates the `difficulty` field in content/questions/*.json files.

Current state: 91.2% hard, 8.8% moderate, 0% easy
Target:        ~25% easy, ~40% moderate, ~35% hard

Heuristic approach:
  1. Score each question based on stem complexity, option complexity, tag signals
  2. Use percentile-based thresholds to hit target distribution
  3. Write back recalibrated difficulty to each file
"""

import json
import re
import os
from collections import Counter

QUESTIONS_DIR = "C:/Users/Admin/JustinMasteryPage/content/questions"

# ── Stem complexity patterns ─────────────────────────────────────────────────

# Easy indicators: definitional, single concept, recall
EASY_PATTERNS = [
    re.compile(r"^which of the following\b", re.I),
    re.compile(r"\bis (?:best )?defined as\b", re.I),
    re.compile(r"\brefers? to\b", re.I),
    re.compile(r"^what (?:is|are|does)\b", re.I),
    re.compile(r"\bis (?:known|called|termed)\b", re.I),
    re.compile(r"\bis an example of\b", re.I),
    re.compile(r"\bis characterized by\b", re.I),
    re.compile(r"^the term\b", re.I),
    re.compile(r"^identify\b", re.I),
    re.compile(r"\bprimary (?:purpose|function|goal) of\b", re.I),
    re.compile(r"\bis associated with\b", re.I),
    re.compile(r"\bfundamental\b", re.I),
    re.compile(r"\bbasic (?:principle|concept|tenet|assumption)\b", re.I),
]

# Moderate indicators: comparison, application, two-concept
MODERATE_PATTERNS = [
    re.compile(r"\bdiffer(?:s|ence|entiate)?\b.*\bfrom\b", re.I),
    re.compile(r"\bdistinguish\b", re.I),
    re.compile(r"\bcompare\b", re.I),
    re.compile(r"\bin contrast\b", re.I),
    re.compile(r"\bunlike\b", re.I),
    re.compile(r"\bwhereas\b", re.I),
    re.compile(r"\brelationship between\b", re.I),
    re.compile(r"\badvantage\b.*\bover\b", re.I),
    re.compile(r"\blimitation\b", re.I),
    re.compile(r"\bwhich (?:best|most (?:accurately|closely)) describes\b", re.I),
    re.compile(r"\bprimary (?:difference|distinction)\b", re.I),
    re.compile(r"\bmost (?:likely|appropriate|effective|suitable)\b", re.I),
    re.compile(r"\bhow (?:would|should|could)\b", re.I),
    re.compile(r"\bappl(?:y|ied|ication|ying)\b", re.I),
    re.compile(r"\bwhat would\b", re.I),
]

# Hard indicators: multi-step, differential, complex scenario
HARD_PATTERNS = [
    re.compile(r"\bdifferential\b", re.I),
    re.compile(r"\brule out\b", re.I),
    re.compile(r"\bethical dilemma\b", re.I),
    re.compile(r"\bcompeting\b.*\bprinciples?\b", re.I),
    re.compile(r"\bconflict(?:ing)?\b.*\b(?:obligation|duty|standard)\b", re.I),
    re.compile(r"\bdual (?:relationship|role)\b", re.I),
    re.compile(r"\bcomorbid\b", re.I),
    re.compile(r"\bcontraindicated\b", re.I),
    re.compile(r"\bexcept\b", re.I),
    re.compile(r"\ball of the following\b.*\bexcept\b", re.I),
    re.compile(r"\bintegrat(?:e|ing|ion)\b.*\bmultiple\b", re.I),
    re.compile(r"\bparadox\b", re.I),
    re.compile(r"\bcomplex\b", re.I),
    re.compile(r"\bnuance\b", re.I),
    re.compile(r"\bwhich (?:combination|set) of\b", re.I),
    re.compile(r"\bmandatory reporting\b.*\bversus\b", re.I),
    re.compile(r"\bsimultaneously\b", re.I),
]

# Tags that indicate easier content
EASY_TAG_KEYWORDS = {
    "definition", "basic", "recall", "identification", "overview",
    "fundamental", "introduction", "terminology", "structure",
    "classification", "simple", "primary", "general",
}

# Tags that indicate harder content
HARD_TAG_KEYWORDS = {
    "differential", "comorbid", "atypical", "complex", "integration",
    "interaction", "multifactorial", "paradox", "ethical dilemma",
    "competing", "controversy", "critique", "limitation",
    "advanced", "nuance", "exception", "contraindication",
}

# Domain-level file complexity: certain subdomain files are inherently harder
DOMAIN_FILE_MODIFIERS = {
    # Domain 1 - Research methods
    "correlation-regression": 0.1,
    "inferential-stats": 0.2,
    "research-designs": 0.1,
    "variables-data": -0.2,
    "operant-conditioning": -0.1,
    "test-reliability": 0.0,
    "test-validity": 0.1,
    "criterion-validity": 0.1,
    "psychometrics": 0.0,
    "research-validity": 0.1,
    # Domain 2 - Development
    "conception-prenatal": -0.2,
    "awakening-infancy": -0.1,
    "discovering-early-childhood": -0.1,
    "building-competence": 0.0,
    "transformation-adolescence": 0.0,
    "long-horizon-adulthood": 0.1,
    "architecture-development": 0.0,
    # Domain 3 - Psychopathology
    "neurodevelopmental": 0.0,
    "anxiety": -0.1,
    "depressive": 0.0,
    "bipolar": 0.1,
    "schizophrenia": 0.1,
    "personality": 0.2,
    "dissociative": 0.2,
    "paraphilic": 0.1,
    "substance": 0.1,
    "obsessive": 0.1,
    "trauma": 0.1,
    "somatic": 0.1,
    "feeding-eating": 0.0,
    "elimination": -0.1,
    "sleep-wake": -0.1,
    "sexual-dysfunctions": 0.0,
    "gender-dysphoria": 0.0,
    "disruptive-impulse": 0.0,
    # Domain 4 - Treatment
    "cognitive-restructuring": 0.0,
    "conditioning-learning": -0.1,
    "acceptance-mindfulness": 0.0,
    "motivation-change": 0.0,
    "relationship-humanistic": 0.0,
    "unconscious-insight": 0.1,
    "system-family": 0.1,
    "evidence-outcomes": 0.1,
    # Domain 5 - Social/Cultural
    "attitudes-dissonance": -0.1,
    "attribution-biases": 0.0,
    "group-dynamics": 0.0,
    "persuasion-influence": 0.0,
    "prejudice-conflict": 0.1,
    "attraction-helping": -0.1,
    "cultural-identity": 0.1,
    "multicultural-practice": 0.2,
    # Domain 6 - I/O
    "organizational-theories": -0.1,
    "theories-of-motivation": 0.0,
    "organizational-leadership": 0.1,
    "organizational-change": 0.2,
    "organizational-decision": 0.1,
    "job-analysis": 0.0,
    "employee-selection-techniques": 0.0,
    "employee-selection-evaluation": 0.1,
    "satisfaction-commitment": 0.0,
    "training-methods": 0.0,
    "career-choice": 0.0,
    "workforce-leadership": 0.1,
    # Domain 7 - Biopsych/Neuro
    "neurons-signaling": -0.1,
    "brain-structure": -0.1,
    "sensation-perception": 0.0,
    "emotion-arousal": 0.0,
    "memory-architecture": 0.0,
    "memory-neuroscience": 0.1,
    "learning-encoding": 0.0,
    "retrieval-forgetting": 0.0,
    "sleep-architecture": 0.0,
    "endocrine-neuroimaging": 0.2,
    "cerebrovascular": 0.2,
    "neurocognitive": 0.2,
    "neurodegenerative": 0.2,
    # Domain 8 - Assessment/Ethics
    "intelligence-cognitive": 0.0,
    "personality-assessment": 0.0,
    "neuropsych-screening": 0.1,
    "test-score-interpretation": 0.0,
    "assessment-ethics": 0.1,
    "legal-forensic": 0.2,
    "supervision-training": 0.1,
    "therapeutic-relationships": 0.0,
    "vocational-interest": -0.1,
    "ebt-anxiety-trauma": 0.1,
    "ebt-mood-personality": 0.1,
    "ebt-substance": 0.1,
    # Domain 9 - Ethics/Pharma
    "ethics-overview": -0.1,
    "general-principles": -0.1,
    "standard-1": 0.0,
    "standard-2": 0.0,
    "standard-3": 0.1,
    "standard-4": 0.1,
    "standard-5": 0.0,
    "standard-6": 0.0,
    "standard-7": 0.0,
    "standard-8": 0.0,
    "standard-9": 0.1,
    "standard-10": 0.1,
    "professional-practice": 0.1,
    "antidepressants": 0.1,
    "antipsychotics": 0.1,
    "anxiolytics": 0.0,
    "mood-stabilizers": 0.1,
    "stimulants": 0.0,
}


def get_file_modifier(filename: str) -> float:
    """Get domain file difficulty modifier from filename."""
    base = filename.replace(".json", "").lower()
    # Strip domain prefix like "domain-1-"
    parts = base.split("-", 2)
    if len(parts) >= 3:
        topic = parts[2]
    else:
        topic = base

    for key, mod in DOMAIN_FILE_MODIFIERS.items():
        if key in topic:
            return mod
    return 0.0


def count_matches(text: str, patterns: list) -> int:
    """Count how many compiled regex patterns match in text."""
    return sum(1 for p in patterns if p.search(text))


def compute_option_complexity(options) -> float:
    """Score option complexity for streak format. Handles multiple formats:
       - list of dicts with 'text' key
       - list of strings
       - dict with letter keys -> string values
       - empty / other
    """
    if not options:
        return 0.0

    lengths = []
    if isinstance(options, list):
        for opt in options:
            if isinstance(opt, dict):
                lengths.append(len(opt.get("text", "")))
            elif isinstance(opt, str):
                lengths.append(len(opt))
    elif isinstance(options, dict):
        for v in options.values():
            if isinstance(v, str):
                lengths.append(len(v))

    if not lengths:
        return 0.0

    avg_len = sum(lengths) / len(lengths)
    # Normalize: 40 chars = baseline
    return max(-0.3, min(0.5, (avg_len - 40) / 100.0))


def compute_tag_signal(tags: list) -> float:
    """Score based on tag content: easy tags pull down, hard tags pull up."""
    if not tags:
        return 0.0

    tag_text = " ".join(tags).lower()
    easy_hits = sum(1 for kw in EASY_TAG_KEYWORDS if kw in tag_text)
    hard_hits = sum(1 for kw in HARD_TAG_KEYWORDS if kw in tag_text)

    return (hard_hits * 0.15) - (easy_hits * 0.15)


def score_streak_question(q: dict, file_modifier: float) -> float:
    """
    Compute a raw difficulty score for a streak question.
    Returns a float roughly in range [0.5, 5.0].
    """
    stem = q.get("stem", "")
    options = q.get("options", [])
    tags = q.get("tags", [])
    explanation = q.get("explanation", "")

    # 1. Base score (start at 2.5 = middle)
    base = 2.5

    # 2. Stem pattern analysis
    easy_hits = count_matches(stem, EASY_PATTERNS)
    moderate_hits = count_matches(stem, MODERATE_PATTERNS)
    hard_hits = count_matches(stem, HARD_PATTERNS)

    pattern_score = (-0.25 * easy_hits + 0.1 * moderate_hits + 0.25 * hard_hits)

    # 3. Stem length (longer = more complex)
    stem_len_mod = 0.0
    if len(stem) > 300:
        stem_len_mod = 0.4
    elif len(stem) > 200:
        stem_len_mod = 0.25
    elif len(stem) > 150:
        stem_len_mod = 0.1
    elif len(stem) < 80:
        stem_len_mod = -0.2
    elif len(stem) < 100:
        stem_len_mod = -0.1

    # 4. Option complexity
    opt_score = compute_option_complexity(options)

    # 5. Tag signals
    tag_score = compute_tag_signal(tags)

    # 6. Number of tags (more tags = more concepts = harder)
    tag_count_mod = min(0.2, (len(tags) - 3) * 0.05)

    # 7. Explanation length (complex explanations = harder question)
    exp_mod = 0.0
    if explanation:
        if len(explanation) > 400:
            exp_mod = 0.2
        elif len(explanation) > 250:
            exp_mod = 0.1
        elif len(explanation) < 100:
            exp_mod = -0.1

    # 8. Scenario detection (case-based stems)
    scenario_mod = 0.0
    scenario_re = re.compile(
        r"\ba (?:psychologist|therapist|clinician|counselor|researcher|client|patient|supervisor)\b",
        re.I
    )
    if scenario_re.search(stem):
        scenario_mod = 0.2

    # 9. File-level modifier
    raw = base + pattern_score + stem_len_mod + opt_score + tag_score + tag_count_mod + exp_mod + scenario_mod + file_modifier

    return raw


def calibrate_thresholds(all_scores: list, targets: dict) -> dict:
    """
    Compute percentile-based thresholds.
    targets: {"easy": 0.25, "moderate": 0.40, "hard": 0.35}
    """
    sorted_scores = sorted(all_scores)
    n = len(sorted_scores)

    p_easy = int(n * targets["easy"])
    p_moderate = int(n * (targets["easy"] + targets["moderate"]))

    t_easy = sorted_scores[min(p_easy, n - 1)]
    t_moderate = sorted_scores[min(p_moderate, n - 1)]

    return {"t_easy": t_easy, "t_moderate": t_moderate}


def assign_difficulty(score: float, thresholds: dict) -> str:
    """Assign easy/moderate/hard from score and thresholds."""
    if score <= thresholds["t_easy"]:
        return "easy"
    elif score <= thresholds["t_moderate"]:
        return "moderate"
    else:
        return "hard"


def main():
    print("=" * 70)
    print("  STREAK QUESTION RECALIBRATION: content/questions/*.json")
    print("  Target: ~25% easy, ~40% moderate, ~35% hard")
    print("=" * 70)

    # Phase 1: Load all questions and compute scores
    file_data = {}  # filename -> (data, [(index, score), ...])
    all_scores = []
    before_counts = Counter()

    files = sorted(f for f in os.listdir(QUESTIONS_DIR) if f.endswith(".json"))
    print(f"\nFiles to process: {len(files)}")

    for fname in files:
        path = os.path.join(QUESTIONS_DIR, fname)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        file_mod = get_file_modifier(fname)
        scored = []
        for i, q in enumerate(data["questions"]):
            before_counts[q.get("difficulty", "MISSING")] += 1
            score = score_streak_question(q, file_mod)
            scored.append((i, score))
            all_scores.append(score)

        file_data[fname] = (data, scored)

    total = len(all_scores)
    print(f"Total questions: {total}")
    print(f"\nBEFORE distribution:")
    for diff in ["easy", "moderate", "hard"]:
        cnt = before_counts.get(diff, 0)
        print(f"  {diff:<10} {cnt:>6} ({cnt/total*100:.1f}%)")

    print(f"\nScore range: [{min(all_scores):.3f}, {max(all_scores):.3f}]")
    print(f"Score mean:  {sum(all_scores)/len(all_scores):.3f}")

    # Phase 2: Compute global thresholds
    targets = {"easy": 0.25, "moderate": 0.40, "hard": 0.35}
    thresholds = calibrate_thresholds(all_scores, targets)
    print(f"\nDynamic thresholds: easy <= {thresholds['t_easy']:.3f}, "
          f"moderate <= {thresholds['t_moderate']:.3f}, hard > {thresholds['t_moderate']:.3f}")

    # Phase 3: Assign and write
    after_counts = Counter()
    per_domain_before = {}  # domain_num -> Counter
    per_domain_after = {}

    for fname in files:
        data, scored = file_data[fname]

        # Extract domain number from filename
        parts = fname.split("-")
        domain_key = parts[1] if len(parts) >= 2 else "?"

        if domain_key not in per_domain_before:
            per_domain_before[domain_key] = Counter()
            per_domain_after[domain_key] = Counter()

        for i, score in scored:
            q = data["questions"][i]
            old_diff = q.get("difficulty", "MISSING")
            new_diff = assign_difficulty(score, thresholds)
            q["difficulty"] = new_diff
            after_counts[new_diff] += 1
            per_domain_after[domain_key][new_diff] += 1
            per_domain_before[domain_key][old_diff] += 1

        # Update questionCount if present
        data["questionCount"] = len(data["questions"])

        # Write back
        path = os.path.join(QUESTIONS_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Phase 4: Report
    print(f"\nAFTER distribution:")
    for diff in ["easy", "moderate", "hard"]:
        cnt = after_counts.get(diff, 0)
        print(f"  {diff:<10} {cnt:>6} ({cnt/total*100:.1f}%)")

    print(f"\n{'Domain':<10} {'easy':>6} {'mod':>6} {'hard':>6}  "
          f"{'%easy':>6} {'%mod':>6} {'%hard':>6}")
    print("-" * 55)
    for dk in sorted(per_domain_after.keys()):
        ac = per_domain_after[dk]
        dtotal = sum(ac.values())
        if dtotal == 0:
            continue
        print(f"Domain {dk:<4} {ac['easy']:>6} {ac['moderate']:>6} {ac['hard']:>6}  "
              f"{ac['easy']/dtotal*100:>5.1f}% {ac['moderate']/dtotal*100:>5.1f}% "
              f"{ac['hard']/dtotal*100:>5.1f}%")

    print("-" * 55)
    print(f"{'TOTAL':<10} {after_counts['easy']:>6} {after_counts['moderate']:>6} "
          f"{after_counts['hard']:>6}  "
          f"{after_counts['easy']/total*100:>5.1f}% "
          f"{after_counts['moderate']/total*100:>5.1f}% "
          f"{after_counts['hard']/total*100:>5.1f}%")

    print(f"\nDone. All {total} streak questions recalibrated in content/questions/*.json")


if __name__ == "__main__":
    main()
