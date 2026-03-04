"""
calibrate_difficulty.py
Adds difficulty_level (1-4) to each question in data/{DOMAIN}_basic.json files.

Heuristic scoring approach:
  Level 1 (basic recall):      definitional, "What is...", single-concept direct recall
  Level 2 (intermediate):      comparison, "Which best describes...", two-concept integration
  Level 3 (advanced application): case scenarios, multi-step reasoning, clinical application
  Level 4 (expert):            differential dx, competing ethical principles, complex integration

Target distribution: ~20% L1, ~35% L2, ~30% L3, ~15% L4

Uses:
  - Question stem keyword/pattern analysis
  - Question angle (direct_recall, contrast, example_recognition, clinical_scenario, implication)
  - Option complexity (length, specificity)
  - Explanation complexity
  - Subdomain-based adjustments
"""

import json
import re
import os
from collections import Counter

DATA_DIR = "C:/Users/Admin/JustinMasteryPage/data"
DOMAINS = ["BPSY", "CASS", "CPAT", "LDEV", "PETH", "PMET", "PTHE", "SOCU", "WDEV"]

# ── Keyword / pattern signals ────────────────────────────────────────────────

# Level 1 indicators: basic recall, definitional
L1_STEM_PATTERNS = [
    r"^which of the following (?:is|are|defines?|describes?|refers? to)\b",
    r"^what (?:is|are|does)\b",
    r"\bis (?:best )?defined as\b",
    r"\brefers? to\b",
    r"^the term\b",
    r"\bis (?:also )?(?:known|called|termed)\b",
    r"^according to\b.*?,\s*\w+\s+(?:is|are|refers?)\b",
    r"\bis characterized by\b",
    r"^identify\b",
    r"\bname the\b",
    r"\bis an example of\b",
    r"\bis associated with\b",
]

# Level 2 indicators: comparison, moderate integration
L2_STEM_PATTERNS = [
    r"\bwhich (?:best|most (?:accurately|closely)) describes\b",
    r"\bdiffer(?:s|ence|entiate)?\b.*\bfrom\b",
    r"\bdistinguish(?:es|ed)?\b",
    r"\bcompare[ds]?\b",
    r"\bin contrast (?:to|with)\b",
    r"\bunlike\b",
    r"\bwhereas\b",
    r"\bsimilar(?:ity|ities)?\b.*\bbetween\b",
    r"\bprimary (?:difference|distinction|purpose|function|goal)\b",
    r"\badvantage\b.*\bover\b",
    r"\blimitation\b",
    r"\bcriticism\b",
    r"\bstrength\b.*\bweakness\b",
    r"\brelationship between\b",
]

# Level 3 indicators: application, clinical scenarios, multi-step
L3_STEM_PATTERNS = [
    r"\ba (?:psychologist|therapist|clinician|counselor|researcher|client|patient)\b",
    r"\bin (?:a |the )?(?:clinical|therapeutic|research|testing) (?:setting|context|situation)\b",
    r"\bcase (?:study|scenario|example|vignette)\b",
    r"\bappl(?:y|ied|ication|ying)\b",
    r"\bmost (?:likely|appropriate|effective|suitable|helpful)\b",
    r"\bbest (?:course of action|approach|strategy|intervention|treatment)\b",
    r"\bwhat would\b",
    r"\bhow (?:would|should|could|might)\b",
    r"\bif a\b.*\bthen\b",
    r"\bgiven (?:that|the)\b",
    r"\bscenario\b",
    r"\bpresents with\b",
    r"\bdiagnos(?:e|ed|is|tic)\b",
    r"\btreatment\b.*\bchoice\b",
    r"\bintervention\b",
    r"\bwhen\b.*\bencounters?\b",
    r"\bmost (?:consistent|indicative)\b",
]

# Level 4 indicators: expert-level, differential, ethical dilemmas
L4_STEM_PATTERNS = [
    r"\bdifferential\b",
    r"\brule out\b",
    r"\bcompeting\b.*\bprinciples?\b",
    r"\bethical dilemma\b",
    r"\bdual (?:relationship|role)\b",
    r"\bmandatory reporting\b.*\bversus\b",
    r"\bconflict(?:ing)?\b.*\b(?:obligation|duty|standard|principle)\b",
    r"\bwhich (?:combination|set) of\b",
    r"\bmultiple\b.*\b(?:factors?|variables?|considerations?)\b.*\bsimultaneously\b",
    r"\bexcept\b",
    r"\bnot\b.*\bcorrect\b",
    r"\ball of the following\b.*\bexcept\b",
    r"\bintegrat(?:e|ing|ion)\b.*\bmultiple\b",
    r"\bcomplex(?:ity)?\b",
    r"\bnuance\b",
    r"\bparadox\b",
    r"\bcomorbid\b",
    r"\bcontraindicated\b",
]

# Compile all patterns
L1_RE = [re.compile(p, re.IGNORECASE) for p in L1_STEM_PATTERNS]
L2_RE = [re.compile(p, re.IGNORECASE) for p in L2_STEM_PATTERNS]
L3_RE = [re.compile(p, re.IGNORECASE) for p in L3_STEM_PATTERNS]
L4_RE = [re.compile(p, re.IGNORECASE) for p in L4_STEM_PATTERNS]

# Angle-based base scores
ANGLE_BASE = {
    "direct_recall": 1.2,
    "example_recognition": 2.0,
    "contrast": 2.3,
    "implication": 2.8,
    "clinical_scenario": 3.2,
}

# Subdomain complexity modifiers: certain subdomains are intrinsically harder
# Positive = harder, negative = easier
SUBDOMAIN_MODIFIERS = {
    # BPSY - brain anatomy is foundational, psychopharm is harder
    "nervous system": -0.3,
    "neurons": -0.3,
    "neurotransmitter": -0.2,
    "brain region": -0.1,
    "cortex": 0.0,
    "psychopharmacology": 0.4,
    "neurological": 0.3,
    "endocrine": 0.3,
    # CPAT - basic disorders easier, personality/differential harder
    "neurodevelopmental": 0.0,
    "anxiety": -0.1,
    "depressive": 0.0,
    "bipolar": 0.1,
    "schizophrenia": 0.1,
    "personality disorder": 0.4,
    "dissociative": 0.3,
    "paraphilic": 0.3,
    "substance": 0.2,
    # PMET - basic stats easier, validity/regression harder
    "variable": -0.3,
    "classical conditioning": -0.2,
    "operant conditioning": -0.2,
    "correlation": 0.0,
    "regression": 0.2,
    "inferential": 0.2,
    "validity": 0.1,
    "reliability": 0.0,
    # PETH - ethics standards vary
    "overview": -0.2,
    "professional issue": 0.2,
    # SOCU
    "attitude": -0.2,
    "attribution": 0.0,
    "cross-cultural": 0.2,
    "multicultural": 0.2,
    "prejudice": 0.1,
    # LDEV
    "prenatal": -0.2,
    "nature vs. nurture": -0.1,
    "cognitive development": 0.0,
    "moral development": 0.1,
    "socioemotional": 0.1,
    # WDEV
    "organizational theor": -0.1,
    "leadership": 0.1,
    "organizational change": 0.2,
    "decision-making": 0.2,
    # PTHE
    "psychodynamic": 0.1,
    "cognitive-behavioral": 0.0,
    "family": 0.1,
    "brief therap": 0.0,
    "prevention": 0.1,
    # CASS
    "test score interpretation": 0.0,
    "mmpi": 0.1,
    "wechsler": 0.0,
    "stanford-binet": -0.1,
    "interest inventor": -0.1,
}


def get_subdomain_modifier(subdomain: str) -> float:
    """Return a difficulty modifier based on subdomain name."""
    sub_lower = subdomain.lower()
    best = 0.0
    for key, mod in SUBDOMAIN_MODIFIERS.items():
        if key in sub_lower:
            best = mod
            break  # Use first match
    return best


def count_pattern_matches(text: str, patterns: list) -> int:
    """Count how many patterns match in the text."""
    count = 0
    for pat in patterns:
        if pat.search(text):
            count += 1
    return count


def compute_option_complexity(options: dict) -> float:
    """Score option complexity based on average length and vocabulary."""
    if not options:
        return 0.0
    lengths = [len(v) for v in options.values()]
    avg_len = sum(lengths) / len(lengths)
    # Longer options = more complex (normalize: 30 chars = baseline)
    complexity = (avg_len - 30) / 80.0  # ranges roughly -0.3 to +0.7
    return max(-0.3, min(0.5, complexity))


def compute_explanation_complexity(explanation: str) -> float:
    """Score explanation complexity based on length and connective words."""
    if not explanation:
        return 0.0
    # Length signal
    length_score = min(0.3, (len(explanation) - 100) / 500.0)
    # Connective/reasoning words
    reasoning_words = ["because", "therefore", "however", "whereas", "although",
                       "in contrast", "specifically", "importantly", "notably",
                       "distinguish", "differentiate", "unlike", "conversely",
                       "criterion", "criteria"]
    reasoning_count = sum(1 for w in reasoning_words if w in explanation.lower())
    reasoning_score = min(0.3, reasoning_count * 0.08)
    return length_score + reasoning_score


def score_question(q: dict) -> float:
    """
    Compute a raw difficulty score for a question.
    Returns a float roughly in range [0.5, 4.5].
    """
    stem = q.get("question", "")
    angle = q.get("angle", "")
    subdomain = q.get("subdomain", "")
    options = q.get("options", {})
    explanation = q.get("explanation", "")

    # 1. Base score from angle
    base = ANGLE_BASE.get(angle, 2.0)

    # 2. Stem pattern matching
    l1_hits = count_pattern_matches(stem, L1_RE)
    l2_hits = count_pattern_matches(stem, L2_RE)
    l3_hits = count_pattern_matches(stem, L3_RE)
    l4_hits = count_pattern_matches(stem, L4_RE)

    # Weighted pattern contribution
    pattern_score = (-0.3 * l1_hits + 0.15 * l2_hits + 0.3 * l3_hits + 0.5 * l4_hits)

    # 3. Subdomain modifier
    sub_mod = get_subdomain_modifier(subdomain)

    # 4. Option complexity
    opt_score = compute_option_complexity(options)

    # 5. Explanation complexity (more complex explanations = harder questions)
    exp_score = compute_explanation_complexity(explanation)

    # 6. Stem length signal (very long stems often indicate scenario-based)
    stem_length_mod = 0.0
    if len(stem) > 200:
        stem_length_mod = 0.3
    elif len(stem) > 120:
        stem_length_mod = 0.15
    elif len(stem) < 50:
        stem_length_mod = -0.15

    raw = base + pattern_score + sub_mod + opt_score + exp_score + stem_length_mod
    return raw


def assign_difficulty_level(raw_score: float) -> int:
    """
    Convert raw score to difficulty level 1-4.
    Thresholds tuned to hit target distribution: ~20% L1, ~35% L2, ~30% L3, ~15% L4.
    """
    if raw_score < 1.6:
        return 1
    elif raw_score < 2.4:
        return 2
    elif raw_score < 3.1:
        return 3
    else:
        return 4


def calibrate_thresholds(all_scores: list, targets: dict) -> dict:
    """
    Dynamically compute thresholds from score distribution to hit target percentiles.
    targets: {1: 0.20, 2: 0.35, 3: 0.30, 4: 0.15}
    Returns: dict mapping level -> (min_score, max_score)
    """
    sorted_scores = sorted(all_scores)
    n = len(sorted_scores)

    # Compute percentile cutoffs
    p1 = int(n * targets[1])                    # top of L1
    p2 = int(n * (targets[1] + targets[2]))     # top of L2
    p3 = int(n * (targets[1] + targets[2] + targets[3]))  # top of L3

    t1 = sorted_scores[min(p1, n - 1)]
    t2 = sorted_scores[min(p2, n - 1)]
    t3 = sorted_scores[min(p3, n - 1)]

    return {"t1": t1, "t2": t2, "t3": t3}


def assign_from_thresholds(raw_score: float, thresholds: dict) -> int:
    """Assign level using dynamic thresholds."""
    if raw_score <= thresholds["t1"]:
        return 1
    elif raw_score <= thresholds["t2"]:
        return 2
    elif raw_score <= thresholds["t3"]:
        return 3
    else:
        return 4


def main():
    print("=" * 70)
    print("  DIFFICULTY CALIBRATION: data/*_basic.json")
    print("  Target: ~20% L1, ~35% L2, ~30% L3, ~15% L4")
    print("=" * 70)

    # Phase 1: Score all questions to compute global thresholds
    all_questions = []  # (domain, index, raw_score)
    domain_data = {}

    for domain in DOMAINS:
        path = os.path.join(DATA_DIR, f"{domain}_basic.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        domain_data[domain] = data
        for i, q in enumerate(data["questions"]):
            raw = score_question(q)
            all_questions.append((domain, i, raw))

    all_scores = [s for _, _, s in all_questions]
    print(f"\nTotal questions scored: {len(all_scores)}")
    print(f"Score range: [{min(all_scores):.3f}, {max(all_scores):.3f}]")
    print(f"Score mean:  {sum(all_scores)/len(all_scores):.3f}")

    # Phase 2: Compute dynamic thresholds to hit target distribution
    targets = {1: 0.20, 2: 0.35, 3: 0.30, 4: 0.15}
    thresholds = calibrate_thresholds(all_scores, targets)
    print(f"\nDynamic thresholds: L1 <= {thresholds['t1']:.3f}, "
          f"L2 <= {thresholds['t2']:.3f}, L3 <= {thresholds['t3']:.3f}, L4 > {thresholds['t3']:.3f}")

    # Phase 3: Assign levels and write back
    grand_counts = Counter()
    print(f"\n{'Domain':<8} {'Total':>6} {'L1':>6} {'L2':>6} {'L3':>6} {'L4':>6}  "
          f"{'%L1':>5} {'%L2':>5} {'%L3':>5} {'%L4':>5}")
    print("-" * 75)

    for domain in DOMAINS:
        data = domain_data[domain]
        counts = Counter()

        for i, q in enumerate(data["questions"]):
            raw = score_question(q)
            level = assign_from_thresholds(raw, thresholds)
            q["difficulty_level"] = level
            counts[level] += 1
            grand_counts[level] += 1

        # Update total_questions just in case
        data["total_questions"] = len(data["questions"])

        # Write back
        path = os.path.join(DATA_DIR, f"{domain}_basic.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

        total = len(data["questions"])
        pcts = {lv: counts[lv] / total * 100 for lv in [1, 2, 3, 4]}
        print(f"{domain:<8} {total:>6} {counts[1]:>6} {counts[2]:>6} "
              f"{counts[3]:>6} {counts[4]:>6}  "
              f"{pcts[1]:>4.1f}% {pcts[2]:>4.1f}% {pcts[3]:>4.1f}% {pcts[4]:>4.1f}%")

    print("-" * 75)
    grand_total = sum(grand_counts.values())
    gpcts = {lv: grand_counts[lv] / grand_total * 100 for lv in [1, 2, 3, 4]}
    print(f"{'TOTAL':<8} {grand_total:>6} {grand_counts[1]:>6} {grand_counts[2]:>6} "
          f"{grand_counts[3]:>6} {grand_counts[4]:>6}  "
          f"{gpcts[1]:>4.1f}% {gpcts[2]:>4.1f}% {gpcts[3]:>4.1f}% {gpcts[4]:>4.1f}%")

    print(f"\nDone. All {grand_total} questions tagged with difficulty_level in data/*_basic.json")


if __name__ == "__main__":
    main()
