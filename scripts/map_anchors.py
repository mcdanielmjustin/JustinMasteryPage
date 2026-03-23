"""
map_anchors.py  (Phase 2)

Map each anchor point to a specific chapter HTML file.
Uses deterministic subdomain→chapter mapping for ~80% of anchors,
keyword-based content routing for multi-chapter subdomains,
and optional Claude API fallback for any remaining unresolved.

Output: scripts/data/anchor_chapter_map.json

Run:
  python scripts/map_anchors.py
  python scripts/map_anchors.py --domain PMET
"""

import json, pathlib, re, sys, argparse

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR / "data"
ANCHORS_FILE = DATA_DIR / "anchors_parsed.json"
OUTPUT_FILE = DATA_DIR / "anchor_chapter_map.json"

DOMAIN_CODES = {
    1: "PMET", 2: "LDEV", 3: "CPAT", 4: "PTHE",
    5: "SOCU", 6: "WDEV", 7: "BPSY", 8: "CASS", 9: "PETH",
}

# ── Direct 1:1 subdomain → chapter mapping ──────────────────────────────────
# Key: (domain_num, "SUBDOMAIN_CODE: Subdomain Name")
# Value: chapter filename (without domain dir prefix)

DIRECT_MAP = {
    # Domain 1 — Psychometrics & Research Methods
    (1, "LEA: Classical Conditioning"): "classical-conditioning.html",
    (1, "LEA: Operant Conditioning"): "operant-conditioning.html",
    (1, "RMS: Correlation and Regression"): "correlation-regression.html",
    (1, "RMS: Inferential Statistical Tests"): "inferential-statistics.html",
    (1, "RMS: Internal/External Validity"): "research-validity.html",
    (1, "RMS: Overview of Inferential Statistics"): "inferential-statistics.html",
    (1, "RMS: Research - Internal/External Validity"): "research-validity.html",
    (1, "RMS: Research - Single-Subject and Group Designs"): "research-designs.html",
    (1, "RMS: Types of Variables and Data"): "variables-data.html",
    (1, "TES: Item Analysis and Test Reliability"): "reliability.html",
    (1, "TES: Test Validity - Content and Construct Validity"): "validity.html",
    (1, "TES: Test Validity - Criterion-Related Validity"): "criterion-validity.html",

    # Domain 2 — Lifespan Development
    (2, "LIF: Cognitive Development"): "cognitive-development.html",
    (2, "LIF: Early Influences on Development - Nature vs. Nurture"): "nature-nurture.html",
    (2, "LIF: Early Influences on Development - Prenatal Development"): "prenatal-development.html",
    (2, "LIF: Language Development"): "language-development.html",
    (2, "LIF: Physical Development"): "physical-development.html",
    (2, "LIF: School and Family Influences"): "family-influences.html",
    (2, "LIF: Socioemotional Development - Attachment, Emotions, and Social Relationships"): "attachment.html",
    (2, "LIF: Socioemotional Development - Moral Development"): "moral-development.html",
    (2, "LIF: Socioemotional Development - Temperament and Personality"): "temperament.html",

    # Domain 3 — Clinical Psychopathology
    (3, "PPA: Anxiety Disorders and Obsessive-Compulsive Disorder"): "anxiety-ocd.html",
    (3, "PPA: Bipolar and Depressive Disorders"): "mood-disorders.html",
    (3, "PPA: Disruptive, Impulse-Control, and Conduct Disorders"): "conduct-disorders.html",
    (3, "PPA: Feeding/Eating, Elimination, and Sleep-Wake Disorders"): "eating-sleep.html",
    (3, "PPA: Neurodevelopmental Disorders"): "neurodevelopmental.html",
    (3, "PPA: Personality Disorders"): "personality-disorders.html",
    (3, "PPA: Schizophrenia Spectrum/Other Psychotic Disorders"): "schizophrenia.html",
    (3, "PPA: Sexual Dysfunctions, Gender Dysphoria, and Paraphilic Disorders"): "sexual-disorders.html",
    (3, "PPA: Substance-Related and Addictive Disorders"): "substance-disorders.html",
    (3, "PPA: Trauma/Stressor-Related, Dissociative, and Somatic Symptom Disorders"): "trauma-dissociative.html",
    (3, "PPY: Anxiety Disorders and Obsessive-Compulsive Disorders"): "anxiety-ocd.html",

    # Domain 4 — Psychotherapy (1 multi-chapter subdomain handled below)
    (4, "CLI: Brief Therapies"): "motivation.html",
    (4, "CLI: Cognitive-Behavioral Therapies"): "cognition.html",
    (4, "CLI: Family Therapies and Group Therapies"): "systems.html",
    (4, "CLI: Family and Group Therapies"): "systems.html",
    (4, "CLI: Prevention, Consultation, and Psychotherapy Research"): "evidence.html",
    (4, "LEA: Interventions Based on Classical Conditioning"): "conditioning.html",
    (4, "LEA: Interventions Based on Operant Conditioning"): "conditioning.html",

    # Domain 5 — Social & Cultural
    (5, "CLI: Cross-Cultural Issues - Identity Development Models"): "identity-models.html",
    (5, "CLI: Cross-Cultural Issues - Terms and Concepts"): "cultural-concepts.html",
    (5, "SOC: Affiliation, Attraction, and Intimacy"): "attraction.html",
    (5, "SOC: Attitudes and Attitude Change"): "attitudes.html",
    (5, "SOC: Persuasion"): "persuasion.html",
    (5, "SOC: Persuasion and Behavioral Economics"): "biases-heuristics.html",
    (5, "SOC: Prosocial Behavior and Prejudice/Discrimination"): "prosocial-prejudice.html",
    (5, "SOC: Social Cognition - Causal Attributions"): "attribution.html",
    (5, "SOC: Social Cognition - Errors, Biases, and Heuristics"): "biases-heuristics.html",
    (5, "SOC: Social Influence - Group Influences"): "group-influence.html",
    (5, "SOC: Social Influence - Types of Influence"): "group-influence.html",

    # Domain 6 — Workforce Development
    (6, "ORG: Career Choice and Development"): "career-development.html",
    (6, "ORG: Employee Selection - Evaluation of Techniques"): "selection-evaluation.html",
    (6, "ORG: Employee Selection - Techniques"): "selection-techniques.html",
    (6, "ORG: Job Analysis and Performance Assessment"): "job-analysis.html",
    (6, "ORG: Organizational Change and Development"): "org-change.html",
    (6, "ORG: Organizational Decision-Making"): "decision-making.html",
    (6, "ORG: Organizational Leadership"): "leadership.html",
    (6, "ORG: Organizational Theories"): "organizational-theories.html",
    (6, "ORG: Satisfaction, Commitment, and Stress"): "satisfaction-stress.html",
    (6, "ORG: Theories of Motivation"): "motivation.html",
    (6, "ORG: Training Methods and Evaluation"): "training.html",

    # Domain 7 — Biopsychology (1 multi-chapter subdomain)
    (7, "LEA: Memory and Forgetting"): "memory-forgetting.html",
    (7, "PHY: Brain Regions/Functions - Cerebral Cortex"): "cerebral-cortex.html",
    (7, "PHY: Brain Regions/Functions - Hindbrain, Midbrain, and Subcortical Forebrain Structures"): "subcortical.html",
    (7, "PHY: Emotions and Stress"): "emotion-stress.html",
    (7, "PHY: Memory and Sleep"): "memory-sleep.html",
    (7, "PHY: Nervous System, Neurons, and Neurotransmitters"): "neurons-neurotransmitters.html",
    (7, "PHY: Sensation and Perception"): "sensation-perception.html",
    (7, "PPA: Neurocognitive Disorders"): "neurocognitive.html",

    # Domain 8 — Clinical Assessment (1 multi-chapter subdomain)
    (8, "ETH: APA Ethics Code Standards 9 and 10"): "assessment-ethics.html",
    (8, "PAS: Clinical Tests"): "clinical-tests.html",
    (8, "PAS: Interest Inventories"): "interest-inventories.html",
    (8, "PAS: MMPI-2"): "mmpi.html",
    (8, "PAS: Other Measures of Cognitive Ability"): "cognitive-measures.html",
    (8, "PAS: Other Measures of Personality"): "personality-measures.html",
    (8, "PAS: Stanford-Binet and Wechsler Tests"): "wechsler-sb.html",
    (8, "PPA: Anxiety Disorders and Obsessive-Compulsive Disorder"): "ch10-ebt-anxiety-trauma.html",
    (8, "PPA: Anxiety Disorders and Obsessive-Compulsive Disorders"): "ch10-ebt-anxiety-trauma.html",
    (8, "PPA: Bipolar and Depressive Disorders"): "ch11-ebt-mood-personality.html",
    (8, "PPA: Disruptive, Impulse-Control, and Conduct Disorders"): "ch12-ebt-substance-developmental.html",
    (8, "PPA: Feeding/Eating and Sleep-Wake Disorders"): "ch11-ebt-mood-personality.html",
    (8, "PPA: Feeding/Eating, Elimination, and Sleep-Wake Disorders"): "ch11-ebt-mood-personality.html",
    (8, "PPA: Neurodevelopmental Disorders"): "ch12-ebt-substance-developmental.html",
    (8, "PPA: Personality Disorders"): "ch11-ebt-mood-personality.html",
    (8, "PPA: Sexual Dysfunctions, Gender Dysphoria, and Paraphilic Disorders"): "ebp-treatment.html",
    (8, "PPA: Substance-Related and Addictive Disorders"): "ch12-ebt-substance-developmental.html",
    (8, "PPA: Trauma/Stressor-Related, Dissociative, and Somatic Symptom Disorders"): "ch10-ebt-anxiety-trauma.html",
    (8, "TES: Test Score Interpretation"): "score-interpretation.html",

    # Domain 9 — direct-mapped subdomains only
    (9, "PHY: Psychopharmacology: Antipsychotics and Antidepressants"): "antipsychotics.html",
    (9, "PPA: Anxiety Disorders and Obsessive-Compulsive Disorder"): "anxiolytics-sedatives.html",
    (9, "PPA: Feeding/Eating, Elimination, and Sleep-Wake Disorders"): "anxiolytics-sedatives.html",
    (9, "PPA: Neurodevelopmental Disorders"): "stimulants-adhd.html",
    (9, "PPA: Schizophrenia Spectrum/Other Psychotic Disorders"): "antipsychotics.html",
    (9, "PPA: Sexual Dysfunctions, Gender Dysphoria, and Paraphilic Disorders"): "pharma-foundations.html",
    (9, "PPA: Substance-Related and Addictive Disorders"): "pharma-foundations.html",
    (9, "PPY: Neurodevelopmental Disorders"): "stimulants-adhd.html",
}


# ── Multi-chapter keyword routing ────────────────────────────────────────────
# For subdomains where anchors may belong to different chapters.
# Each entry: list of (chapter_filename, keywords, fallback_priority)
# Anchor content is scored against each chapter's keywords; highest score wins.
# On tie, fallback_priority (lower = preferred) breaks it.

KEYWORD_ROUTES = {
    # Domain 4: Psychodynamic & Humanistic Therapies
    (4, "CLI: Psychodynamic and Humanistic Therapies"): [
        ("insight.html", [
            "freud", "psychoanalysis", "psychoanalytic", "psychodynamic",
            "ego psychology", "object relations", "self psychology", "kohut",
            "transference", "countertransference", "defense mechanism",
            "free association", "unconscious", "ego", "superego",
            "adler", "jung", "resistance", "interpretation", "working through",
            "brief psychodynamic", "attachment theory",
        ], 0),
        ("relationship.html", [
            "rogers", "person-centered", "client-centered", "humanistic",
            "maslow", "self-actualization", "gestalt", "perls",
            "unconditional positive regard", "empathy", "congruence",
            "genuineness", "phenomenological", "here and now",
            "therapeutic alliance", "therapeutic relationship",
        ], 1),
    ],

    # Domain 7: Neurological and Endocrine Disorders
    (7, "PHY: Neurological and Endocrine Disorders"): [
        ("neurological-disorders.html", [
            "epilepsy", "seizure", "parkinson", "huntington",
            "multiple sclerosis", "stroke", "cerebrovascular",
            "traumatic brain injury", "tbi", "aphasia", "broca",
            "wernicke", "brain injury", "hemiplegia", "ataxia",
            "als", "amyotrophic", "myasthenia",
        ], 0),
        ("endocrine-neuroimaging.html", [
            "endocrine", "thyroid", "adrenal", "pituitary",
            "cushing", "addison", "hormone", "cortisol",
            "neuroimaging", "ct scan", "mri", "fmri", "pet scan",
            "spect", "eeg", "evoked potential",
        ], 1),
    ],

    # Domain 8: Professional Issues
    (8, "ETH: Professional Issues"): [
        ("ch8-legal-forensic.html", [
            "malpractice", "liability", "forensic", "competency to stand trial",
            "insanity", "duty to warn", "duty to protect", "tarasoff",
            "expert testimony", "civil commitment", "involuntary",
            "daubert", "frye", "custody", "court", "legal",
        ], 0),
        ("ch9-supervision-training.html", [
            "supervision", "supervisor", "supervisee", "training",
            "licensure", "certification", "scope of practice",
            "professional development", "self-care", "burnout",
            "continuing education", "internship", "postdoctoral",
        ], 1),
        ("ch7-therapeutic-relationships.html", [
            "therapeutic alliance", "boundary", "boundaries",
            "dual relationship", "multiple relationship",
            "sexual", "bartering", "termination", "abandonment",
            "informed consent", "fees", "transference",
        ], 2),
    ],

    # Domain 9: Ethics Standards 1 and 2
    (9, "ETH: APA Ethics Code Overview and Standards 1 and 2"): [
        ("ethics-overview.html", [
            "general principle", "aspirational", "beneficence",
            "nonmaleficence", "fidelity", "responsibility", "integrity",
            "justice", "respect", "ethics code", "overview",
            "enforceable", "structure", "apa may take action",
            "pro bono", "expelled", "suspended", "felony",
        ], 0),
        ("resolving-ethical-issues.html", [
            "resolving", "ethical violation", "informal resolution",
            "ethics committee", "filing", "complaint", "reporting",
            "conflict between ethics", "legal requirements",
            "standard 1", "1.04", "1.05", "1.06", "1.07", "1.08",
        ], 1),
        ("competence.html", [
            "competence", "boundaries of competence", "emergency",
            "maintaining competence", "delegation", "personal problems",
            "consultation", "unfamiliar population", "limited experience",
            "standard 2", "2.01", "2.02", "2.03", "2.04", "2.05", "2.06",
        ], 2),
    ],

    # Domain 9: Ethics Standards 3 and 4
    (9, "ETH: APA Ethics Code Standards 3 and 4"): [
        ("human-relations.html", [
            "discrimination", "harassment", "sexual harassment",
            "multiple relationship", "avoiding harm", "conflict of interest",
            "third-party", "exploitative", "informed consent",
            "standard 3", "3.01", "3.02", "3.03", "3.04", "3.05",
            "3.06", "3.07", "3.08", "3.10", "3.11", "3.12",
            "interpreter", "couples", "family therapy",
        ], 0),
        ("privacy-confidentiality.html", [
            "confidentiality", "privacy", "confidential information",
            "limits of confidentiality", "disclosures", "release",
            "tarasoff", "hipaa", "mandatory reporting", "mandated",
            "standard 4", "4.01", "4.02", "4.03", "4.04", "4.05",
            "4.06", "4.07", "minor", "group therapy confidentiality",
        ], 1),
    ],

    # Domain 9: Ethics Standards 5 and 6
    (9, "ETH: APA Ethics Code Standards 5 and 6"): [
        ("advertising.html", [
            "advertising", "public statement", "testimonial",
            "media", "solicitation", "in-person solicitation",
            "standard 5", "5.01", "5.02", "5.03", "5.04", "5.05", "5.06",
        ], 0),
        ("record-keeping-fees.html", [
            "record keeping", "records", "fees", "financial",
            "bartering", "referral fees", "documentation",
            "standard 6", "6.01", "6.02", "6.03", "6.04", "6.05",
            "6.06", "6.07", "withholding records",
        ], 1),
    ],

    # Domain 9: Ethics Standards 7 and 8
    (9, "ETH: APA Ethics Code Standards 7 and 8"): [
        ("education-training.html", [
            "education", "training", "student", "program design",
            "course", "teaching", "mandatory therapy",
            "standard 7", "7.01", "7.02", "7.03", "7.04",
            "7.05", "7.06", "7.07", "graduate",
        ], 0),
        ("research-publication.html", [
            "research", "publication", "institutional approval",
            "informed consent for research", "deception", "debriefing",
            "animal", "plagiarism", "publication credit", "authorship",
            "sharing data", "reviewer", "peer review",
            "standard 8", "8.01", "8.02", "8.03", "8.04", "8.05",
            "8.06", "8.07", "8.08", "8.09", "8.10", "8.11",
            "8.12", "8.13", "8.14", "8.15",
        ], 1),
    ],

    # Domain 9: Pharma — Antipsychotics and Antidepressants
    (9, "PHY: Psychopharmacology - Antipsychotics and Antidepressants"): [
        ("antipsychotics.html", [
            "antipsychotic", "neuroleptic", "dopamine",
            "chlorpromazine", "haloperidol", "risperidone",
            "olanzapine", "clozapine", "quetiapine", "aripiprazole",
            "extrapyramidal", "tardive dyskinesia", "eps",
            "neuroleptic malignant syndrome", "typical antipsychotic",
            "atypical antipsychotic", "first-generation", "second-generation",
            "schizophrenia", "psychotic", "metabolic syndrome",
        ], 0),
        ("antidepressants.html", [
            "antidepressant", "ssri", "snri", "tca", "tricyclic",
            "maoi", "monoamine oxidase", "fluoxetine", "sertraline",
            "paroxetine", "citalopram", "escitalopram", "venlafaxine",
            "duloxetine", "amitriptyline", "imipramine", "nortriptyline",
            "phenelzine", "tranylcypromine", "bupropion", "mirtazapine",
            "serotonin syndrome", "black box warning", "depression",
            "selective serotonin",
        ], 1),
    ],

    # Domain 9: Pharma — Other Psychoactive Drugs
    (9, "PHY: Psychopharmacology - Other Psychoactive Drugs"): [
        ("anxiolytics-sedatives.html", [
            "benzodiazepine", "buspirone", "diazepam", "alprazolam",
            "lorazepam", "clonazepam", "anxiolytic", "sedative",
            "gaba", "anxiety", "insomnia", "sleep",
            "cholinesterase", "donepezil", "memantine", "dementia medication",
        ], 0),
        ("mood-stabilizers.html", [
            "lithium", "valproate", "valproic", "carbamazepine",
            "lamotrigine", "mood stabilizer", "bipolar", "mania",
            "manic", "anticonvulsant",
        ], 1),
        ("stimulants-adhd.html", [
            "methylphenidate", "ritalin", "adderall", "amphetamine",
            "stimulant", "adhd", "atomoxetine", "strattera",
            "attention deficit", "dextroamphetamine",
        ], 2),
    ],

    # Domain 9: PPA — Bipolar/Depressive (pharma context)
    (9, "PPA: Bipolar and Depressive Disorders"): [
        ("antidepressants.html", [
            "antidepressant", "ssri", "snri", "tca", "maoi",
            "depression", "depressive", "major depressive",
            "serotonin", "norepinephrine",
        ], 0),
        ("mood-stabilizers.html", [
            "lithium", "bipolar", "mania", "manic", "mood stabilizer",
            "valproate", "carbamazepine", "lamotrigine", "cyclothymic",
        ], 1),
    ],
}


def score_keywords(text: str, keywords: list[str]) -> int:
    """Count how many keywords appear in the text (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)


def route_by_keywords(content: str, routes: list[tuple]) -> tuple[str, str]:
    """Route an anchor to a chapter using keyword scoring.
    Returns (chapter_file, method).
    """
    scores = []
    for chapter, keywords, priority in routes:
        score = score_keywords(content, keywords)
        scores.append((score, -priority, chapter))  # negate priority so lower = better on tie

    scores.sort(reverse=True)

    if scores[0][0] > 0:
        return scores[0][2], "keyword"

    # No keyword matches — use lowest priority (fallback)
    return routes[0][0], "fallback"


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Map anchors to chapter files")
    parser.add_argument("--domain", type=str, help="Single domain code (e.g. PMET)")
    args = parser.parse_args()

    if not ANCHORS_FILE.exists():
        print(f"ERROR: {ANCHORS_FILE} not found. Run parse_anchors.py first.")
        sys.exit(1)

    anchors = json.loads(ANCHORS_FILE.read_text(encoding="utf-8"))

    if args.domain:
        code = args.domain.upper()
        anchors = [a for a in anchors if a["domain_code"] == code]

    if not anchors:
        print("No anchors to process.")
        return

    results = []
    stats = {"deterministic": 0, "keyword": 0, "fallback": 0, "unresolved": 0}

    for anchor in anchors:
        key = (anchor["domain_num"],
               f"{anchor['subdomain_code']}: {anchor['subdomain_name']}")
        domain_dir = f"domain{anchor['domain_num']}"

        if key in DIRECT_MAP:
            chapter = DIRECT_MAP[key]
            method = "deterministic"
        elif key in KEYWORD_ROUTES:
            chapter, method = route_by_keywords(anchor["content"], KEYWORD_ROUTES[key])
        else:
            chapter = None
            method = "unresolved"

        stats[method] += 1

        record = {
            **anchor,
            "chapter_file": f"{domain_dir}/{chapter}" if chapter else None,
            "mapping_method": method,
        }
        results.append(record)

    # Report
    print(f"\nMapping results:")
    for method, count in stats.items():
        if count > 0:
            print(f"  {method}: {count}")
    print(f"  total: {len(results)}")

    # Show unresolved
    unresolved = [r for r in results if r["mapping_method"] == "unresolved"]
    if unresolved:
        print(f"\nUnresolved anchors ({len(unresolved)}):")
        for r in unresolved:
            print(f"  D{r['domain_num']} [{r['anchor_id']}] "
                  f"{r['subdomain_code']}: {r['subdomain_name']}")

    # Per-domain summary
    print("\nPer-domain breakdown:")
    for dnum in sorted(set(r["domain_num"] for r in results)):
        domain_results = [r for r in results if r["domain_num"] == dnum]
        code = DOMAIN_CODES[dnum]
        chapters = set(r["chapter_file"] for r in domain_results if r["chapter_file"])
        print(f"  D{dnum} ({code}): {len(domain_results)} anchors → {len(chapters)} chapters")

    # Show keyword routing breakdown for multi-chapter subdomains
    keyword_routed = [r for r in results if r["mapping_method"] in ("keyword", "fallback")]
    if keyword_routed:
        print("\nMulti-chapter routing breakdown:")
        by_sub = {}
        for r in keyword_routed:
            sub_key = f"D{r['domain_num']} {r['subdomain_code']}: {r['subdomain_name']}"
            by_sub.setdefault(sub_key, {})
            ch = r["chapter_file"]
            by_sub[sub_key][ch] = by_sub[sub_key].get(ch, 0) + 1
        for sub, chapters in sorted(by_sub.items()):
            print(f"  {sub}:")
            for ch, count in sorted(chapters.items(), key=lambda x: -x[1]):
                print(f"    {ch}: {count}")

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved {len(results)} mappings to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
