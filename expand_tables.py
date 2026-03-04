#!/usr/bin/env python3
"""
expand_tables.py — Generate new table-fill questions for thin domains.

Targets:
  PETH  — 12 new psychopharmacology tables (SSRIs, SNRIs, TCAs, MAOIs,
           atypical antipsychotics, typical antipsychotics, mood stabilizers,
           benzodiazepines, stimulants, EPS/side effects, neurotransmitter-disease,
           CYP450 interactions)
  CPAT  — 3 new DSM-5 diagnostic-criteria comparison tables
  PMET  — 2 new statistical-test selection tables

ALL options are kept ≤ 140 characters.
"""

import json, pathlib, copy

DATA = pathlib.Path("data")
MAX_OPT = 140  # hard limit enforced by table-exercise.html


def load_domain(code: str) -> dict:
    p = DATA / f"{code}_tables.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_domain(code: str, data: dict):
    p = DATA / f"{code}_tables.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {p}")


def next_id(data: dict, code: str) -> int:
    """Return the next sequential ID number after existing max."""
    if not data["questions"]:
        return 1
    return max(int(q["id"].split("-")[-1]) for q in data["questions"]) + 1


def mk(code, domain_name, chapter_file, chapter_title, section,
        headers, rows, blank_row, blank_col, correct_value,
        options, correct_option_index, explanation, id_num):
    """Build one question dict; asserts all options ≤ 140 chars."""
    for i, opt in enumerate(options):
        assert len(opt) <= MAX_OPT, (
            f"{code} id={id_num} option[{i}] len={len(opt)}: {opt!r}"
        )
    return {
        "id": f"{code}-TBL-{id_num:04d}",
        "mode": "table_fill",
        "domain_code": code,
        "domain_name": domain_name,
        "chapter_file": chapter_file,
        "chapter_title": chapter_title,
        "section": section,
        "headers": headers,
        "rows": rows,
        "blank_row": blank_row,
        "blank_col": blank_col,
        "correct_value": correct_value,
        "options": options,
        "correct_option_index": correct_option_index,
        "explanation": explanation,
    }


# ======================================================================
#  PETH — Psychopharmacology tables
# ======================================================================

def build_peth_tables(start_id: int) -> list:
    C = "PETH"
    N = "Psychopharmacology & Ethics"
    tables = []
    n = start_id

    # --- 1. SSRI Comparison (multiple questions from one big table) ---

    # 1a. Fluoxetine key feature
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "SSRI Comparison",
        ["Drug", "Brand Name", "Key Feature"],
        [
            ["Fluoxetine", "Prozac", "BLANK"],
            ["Sertraline", "Zoloft", "Most serotonin-selective SSRI"],
            ["Paroxetine", "Paxil", "Most anticholinergic SSRI; short half-life"],
            ["Citalopram", "Celexa", "Dose-dependent QT prolongation risk"],
            ["Escitalopram", "Lexapro", "S-enantiomer of citalopram; fewest drug interactions"],
            ["Fluvoxamine", "Luvox", "FDA-approved for OCD; strong CYP1A2 inhibitor"],
        ],
        0, 2,
        "Longest half-life SSRI (4-6 days); active metabolite norfluoxetine",
        [
            "Most anticholinergic SSRI; short half-life",
            "Longest half-life SSRI (4-6 days); active metabolite norfluoxetine",
            "Dose-dependent QT prolongation risk",
            "S-enantiomer of citalopram; fewest drug interactions",
        ],
        1,
        "Fluoxetine (Prozac) is distinguished by its exceptionally long half-life of 4-6 days "
        "(with its active metabolite norfluoxetine lasting even longer). This makes it the only "
        "SSRI where missed doses rarely cause discontinuation syndrome, a commonly tested fact.",
        n
    )); n += 1

    # 1b. Paroxetine key feature
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "SSRI Comparison",
        ["Drug", "Brand Name", "Distinguishing Feature"],
        [
            ["Fluoxetine", "Prozac", "Longest half-life (4-6 days)"],
            ["Sertraline", "Zoloft", "Most serotonin-selective SSRI"],
            ["Paroxetine", "Paxil", "BLANK"],
            ["Citalopram", "Celexa", "QT prolongation risk at higher doses"],
            ["Escitalopram", "Lexapro", "Fewest drug interactions among SSRIs"],
            ["Fluvoxamine", "Luvox", "Strong CYP1A2 inhibitor; FDA for OCD"],
        ],
        2, 2,
        "Most anticholinergic SSRI; highest discontinuation risk",
        [
            "Longest half-life (4-6 days)",
            "Most serotonin-selective SSRI",
            "Most anticholinergic SSRI; highest discontinuation risk",
            "Fewest drug interactions among SSRIs",
        ],
        2,
        "Paroxetine (Paxil) is the most anticholinergic SSRI and has the highest risk of "
        "discontinuation syndrome due to its short half-life and lack of active metabolites. "
        "It is also associated with weight gain more than other SSRIs.",
        n
    )); n += 1

    # --- 2. SNRI Comparison ---
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "SNRI Comparison",
        ["Drug", "Brand Name", "Unique Feature"],
        [
            ["Venlafaxine", "Effexor", "Dose-dependent: serotonin at low, NE at higher doses"],
            ["Duloxetine", "Cymbalta", "BLANK"],
            ["Desvenlafaxine", "Pristiq", "Active metabolite of venlafaxine; minimal CYP metabolism"],
        ],
        1, 2,
        "FDA-approved for neuropathic pain and fibromyalgia",
        [
            "Dose-dependent: serotonin at low, NE at higher doses",
            "FDA-approved for neuropathic pain and fibromyalgia",
            "Active metabolite of venlafaxine; minimal CYP metabolism",
            "Primarily noradrenergic; used for ADHD off-label",
        ],
        1,
        "Duloxetine (Cymbalta) is uniquely FDA-approved for both depression and pain conditions "
        "including diabetic neuropathic pain and fibromyalgia. This dual indication for mood "
        "and pain is a key distinguishing feature tested on the EPPP.",
        n
    )); n += 1

    # --- 3. TCA Comparison ---
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "Tricyclic Antidepressant Comparison",
        ["Drug", "Type", "Notable Feature"],
        [
            ["Amitriptyline", "Tertiary amine", "Most sedating TCA; used for chronic pain"],
            ["Nortriptyline", "Secondary amine", "Least orthostatic hypotension among TCAs"],
            ["Imipramine", "Tertiary amine", "BLANK"],
            ["Clomipramine", "Tertiary amine", "Most serotonergic TCA; gold standard for OCD"],
        ],
        2, 2,
        "First TCA discovered; used for enuresis in children",
        [
            "Most sedating TCA; used for chronic pain",
            "Most serotonergic TCA; gold standard for OCD",
            "First TCA discovered; used for enuresis in children",
            "Least orthostatic hypotension among TCAs",
        ],
        2,
        "Imipramine was the first tricyclic antidepressant discovered and is notably used "
        "for childhood enuresis (bedwetting). This pediatric indication distinguishes it from "
        "other TCAs, which are primarily used for depression and pain conditions.",
        n
    )); n += 1

    # --- 4. MAOI Dietary Restrictions ---
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "MAOI Comparison and Safety",
        ["Drug", "Type", "Key Safety Issue"],
        [
            ["Phenelzine", "Irreversible, non-selective", "BLANK"],
            ["Tranylcypromine", "Irreversible, non-selective", "Amphetamine-like structure; stimulant effects"],
            ["Selegiline patch", "MAO-B selective at low doses", "Transdermal delivery bypasses gut; less dietary restriction"],
        ],
        0, 2,
        "Strict tyramine-free diet required; hypertensive crisis risk",
        [
            "Transdermal delivery bypasses gut; less dietary restriction",
            "Strict tyramine-free diet required; hypertensive crisis risk",
            "Amphetamine-like structure; stimulant effects",
            "Selective for MAO-B; safe with all foods at any dose",
        ],
        1,
        "Phenelzine (Nardil) is an irreversible, non-selective MAOI that requires strict "
        "avoidance of tyramine-containing foods (aged cheeses, cured meats, fermented foods) "
        "to prevent potentially fatal hypertensive crisis. This dietary restriction is the "
        "most commonly tested fact about MAOIs on the EPPP.",
        n
    )); n += 1

    # 4b. Tyramine foods table
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "MAOI Dietary Restrictions",
        ["Food Category", "Examples", "Risk Level"],
        [
            ["Aged cheeses", "Cheddar, Swiss, Parmesan, blue cheese", "High"],
            ["Cured/smoked meats", "Salami, pepperoni, smoked fish", "High"],
            ["Fermented foods", "Sauerkraut, kimchi, soy sauce, miso", "High"],
            ["Alcoholic beverages", "BLANK", "Moderate to high"],
            ["Fresh foods", "Fresh meats, fresh cheeses, most fruits", "Low/safe"],
        ],
        3, 1,
        "Tap/draft beer, red wine (especially Chianti)",
        [
            "Fresh meats, fresh cheeses, most fruits",
            "Cheddar, Swiss, Parmesan, blue cheese",
            "Tap/draft beer, red wine (especially Chianti)",
            "All beer and wine regardless of type",
        ],
        2,
        "Among alcoholic beverages, tap/draft beer and red wine (particularly Chianti) carry "
        "the highest tyramine content and risk with MAOIs. Distilled spirits and most white "
        "wines have lower tyramine. This specific distinction is frequently tested.",
        n
    )); n += 1

    # --- 5. Atypical Antipsychotic Comparison ---
    tables.append(mk(C, N,
        "antipsychotics.html", "Antipsychotics", "Atypical Antipsychotic Comparison",
        ["Drug", "Brand Name", "Key Side Effect / Feature"],
        [
            ["Risperidone", "Risperdal", "Highest EPS risk among atypicals; hyperprolactinemia"],
            ["Olanzapine", "Zyprexa", "Greatest weight gain and metabolic risk"],
            ["Quetiapine", "Seroquel", "Most sedating; used off-label for insomnia"],
            ["Aripiprazole", "Abilify", "BLANK"],
            ["Clozapine", "Clozaril", "Gold standard for treatment-resistant schizophrenia"],
            ["Ziprasidone", "Geodon", "Least weight gain; QT prolongation risk"],
        ],
        3, 2,
        "Partial D2 agonist; least metabolic side effects",
        [
            "Greatest weight gain and metabolic risk",
            "Partial D2 agonist; least metabolic side effects",
            "Gold standard for treatment-resistant schizophrenia",
            "Highest EPS risk among atypicals; hyperprolactinemia",
        ],
        1,
        "Aripiprazole (Abilify) is unique among antipsychotics as a partial dopamine D2 agonist "
        "(a 'dopamine stabilizer') rather than a full antagonist. This mechanism results in the "
        "least metabolic side effects (weight gain, diabetes risk) among atypical antipsychotics.",
        n
    )); n += 1

    # 5b. Clozapine monitoring
    tables.append(mk(C, N,
        "antipsychotics.html", "Antipsychotics", "Clozapine Special Considerations",
        ["Feature", "Detail"],
        [
            ["Primary indication", "Treatment-resistant schizophrenia (failed 2+ antipsychotics)"],
            ["Unique efficacy", "Only antipsychotic proven to reduce suicidality"],
            ["Major risk", "BLANK"],
            ["Monitoring", "Regular ANC blood draws via REMS program"],
            ["Other side effects", "Metabolic syndrome, sedation, seizures (dose-dependent)"],
        ],
        2, 1,
        "Agranulocytosis (1-2%); potentially fatal drop in WBCs",
        [
            "Only antipsychotic proven to reduce suicidality",
            "Agranulocytosis (1-2%); potentially fatal drop in WBCs",
            "Metabolic syndrome, sedation, seizures (dose-dependent)",
            "Tardive dyskinesia (highest risk among atypicals)",
        ],
        1,
        "Clozapine's major risk is agranulocytosis, a potentially fatal drop in white blood cells "
        "occurring in 1-2% of patients. This necessitates mandatory blood monitoring through "
        "the REMS (Risk Evaluation and Mitigation Strategy) program — the most commonly tested "
        "clozapine fact on the EPPP.",
        n
    )); n += 1

    # --- 6. Typical Antipsychotic Comparison ---
    tables.append(mk(C, N,
        "antipsychotics.html", "Antipsychotics", "Typical Antipsychotic Comparison",
        ["Drug", "Potency", "Side Effect Profile"],
        [
            ["Haloperidol", "High potency", "BLANK"],
            ["Chlorpromazine", "Low potency", "More sedation, orthostatic hypotension, anticholinergic effects"],
            ["Fluphenazine", "High potency", "Available as long-acting decanoate injection"],
        ],
        0, 2,
        "More EPS and tardive dyskinesia; less sedation",
        [
            "More sedation, orthostatic hypotension, anticholinergic effects",
            "More EPS and tardive dyskinesia; less sedation",
            "Available as long-acting decanoate injection",
            "Lowest risk of all extrapyramidal symptoms",
        ],
        1,
        "High-potency typical antipsychotics like haloperidol have greater risk of EPS "
        "(extrapyramidal symptoms) and tardive dyskinesia but less sedation and fewer "
        "anticholinergic effects. Low-potency agents like chlorpromazine show the opposite "
        "pattern — more sedation but less EPS. This inverse relationship is highly testable.",
        n
    )); n += 1

    # --- 7. Mood Stabilizer Comparison ---
    tables.append(mk(C, N,
        "mood-stabilizers.html", "Mood Stabilizers", "Mood Stabilizer Comparison",
        ["Drug", "Primary Use", "Key Monitoring/Side Effect"],
        [
            ["Lithium", "Bipolar I (acute mania + maintenance)", "BLANK"],
            ["Valproic acid", "Bipolar mania; rapid cycling", "Hepatotoxicity; teratogenic (neural tube defects)"],
            ["Carbamazepine", "Bipolar; trigeminal neuralgia", "Blood dyscrasias; autoinduces own metabolism"],
            ["Lamotrigine", "Bipolar depression maintenance", "Stevens-Johnson syndrome (titrate slowly)"],
        ],
        0, 2,
        "Narrow therapeutic index (0.6-1.2 mEq/L); nephrotoxicity, thyroid dysfunction",
        [
            "Hepatotoxicity; teratogenic (neural tube defects)",
            "Narrow therapeutic index (0.6-1.2 mEq/L); nephrotoxicity, thyroid dysfunction",
            "Stevens-Johnson syndrome (titrate slowly)",
            "Blood dyscrasias; autoinduces own metabolism",
        ],
        1,
        "Lithium has a notoriously narrow therapeutic index (0.6-1.2 mEq/L), requiring regular "
        "serum level monitoring. Key side effects include nephrotoxicity and thyroid dysfunction "
        "(hypothyroidism). Lithium toxicity symptoms and the therapeutic range are among the "
        "most frequently tested pharmacology topics on the EPPP.",
        n
    )); n += 1

    # --- 8. Benzodiazepine Comparison ---
    tables.append(mk(C, N,
        "anxiolytics.html", "Anxiolytics", "Benzodiazepine Comparison",
        ["Drug", "Brand Name", "Onset", "Half-Life", "Primary Use"],
        [
            ["Diazepam", "Valium", "Rapid", "Long (20-100 hrs)", "Anxiety, muscle relaxation, seizures"],
            ["Alprazolam", "Xanax", "Intermediate", "Short (6-12 hrs)", "BLANK"],
            ["Lorazepam", "Ativan", "Intermediate", "Intermediate (10-20 hrs)", "Anxiety; preferred in hepatic impairment"],
            ["Clonazepam", "Klonopin", "Intermediate", "Long (18-50 hrs)", "Panic disorder, seizure disorders"],
        ],
        1, 4,
        "Panic disorder; high potency, high dependence risk",
        [
            "Anxiety, muscle relaxation, seizures",
            "Panic disorder; high potency, high dependence risk",
            "Anxiety; preferred in hepatic impairment",
            "Panic disorder, seizure disorders",
        ],
        1,
        "Alprazolam (Xanax) is a high-potency, short-acting benzodiazepine primarily used for "
        "panic disorder. Its short half-life and high potency make it the benzodiazepine with "
        "the highest dependence and withdrawal risk, a critical clinical distinction.",
        n
    )); n += 1

    # --- 9. Stimulant Comparison ---
    tables.append(mk(C, N,
        "adhd-medications.html", "ADHD Medications", "Stimulant and Non-Stimulant Comparison",
        ["Drug", "Class", "Mechanism", "Duration"],
        [
            ["Methylphenidate", "Stimulant", "Blocks DA/NE reuptake", "4-12 hrs (formulation dependent)"],
            ["Amphetamine", "Stimulant", "BLANK", "4-12 hrs (formulation dependent)"],
            ["Lisdexamfetamine", "Prodrug stimulant", "Converted to d-amphetamine in body", "Up to 14 hours"],
            ["Atomoxetine", "Non-stimulant", "Selective NE reuptake inhibitor", "24 hours (once daily)"],
        ],
        1, 2,
        "Blocks reuptake AND promotes release of DA/NE",
        [
            "Blocks DA/NE reuptake",
            "Blocks reuptake AND promotes release of DA/NE",
            "Selective NE reuptake inhibitor",
            "Converted to d-amphetamine in body",
        ],
        1,
        "Amphetamine differs from methylphenidate in that it both blocks reuptake AND actively "
        "promotes the release of dopamine and norepinephrine from presynaptic terminals. "
        "Methylphenidate only blocks reuptake. This dual mechanism makes amphetamines generally "
        "more potent but also carries higher abuse potential.",
        n
    )); n += 1

    # --- 10. EPS / Side Effect Recognition ---
    tables.append(mk(C, N,
        "antipsychotics.html", "Antipsychotics", "Extrapyramidal Side Effects",
        ["Condition", "Onset", "Key Symptoms", "Treatment"],
        [
            ["Acute dystonia", "Hours to days", "Muscle spasms, torticollis, oculogyric crisis", "Benztropine or diphenhydramine"],
            ["Akathisia", "Days to weeks", "BLANK", "Reduce dose; beta-blockers; benzodiazepines"],
            ["Parkinsonism", "Weeks to months", "Tremor, rigidity, bradykinesia, shuffling gait", "Benztropine; amantadine"],
            ["Tardive dyskinesia", "Months to years", "Involuntary oro-facial movements, lip smacking", "Valbenazine; switch to clozapine"],
        ],
        1, 2,
        "Subjective restlessness; inability to sit still; pacing",
        [
            "Muscle spasms, torticollis, oculogyric crisis",
            "Subjective restlessness; inability to sit still; pacing",
            "Tremor, rigidity, bradykinesia, shuffling gait",
            "Involuntary oro-facial movements, lip smacking",
        ],
        1,
        "Akathisia is characterized by subjective inner restlessness and an inability to sit "
        "still, often manifesting as pacing or fidgeting. It is frequently confused with "
        "anxiety or agitation. Unlike other EPS, beta-blockers (propranolol) are a first-line "
        "treatment, which is a commonly tested clinical pearl.",
        n
    )); n += 1

    # 10b. NMS
    tables.append(mk(C, N,
        "antipsychotics.html", "Antipsychotics", "Neuroleptic Malignant Syndrome",
        ["Feature", "Detail"],
        [
            ["Cause", "Dopamine blockade (any antipsychotic; higher risk with typicals)"],
            ["Cardinal signs", "BLANK"],
            ["Lab finding", "Elevated creatine kinase (CK); leukocytosis"],
            ["Treatment", "Discontinue antipsychotic; dantrolene; bromocriptine; supportive care"],
            ["Mortality", "5-20% if untreated; medical emergency"],
        ],
        1, 1,
        "Hyperthermia, muscle rigidity, altered mental status, autonomic instability",
        [
            "Dopamine blockade (any antipsychotic; higher risk with typicals)",
            "Hyperthermia, muscle rigidity, altered mental status, autonomic instability",
            "Elevated creatine kinase (CK); leukocytosis",
            "Discontinue antipsychotic; dantrolene; bromocriptine; supportive care",
        ],
        1,
        "Neuroleptic Malignant Syndrome (NMS) has four cardinal signs remembered by the mnemonic "
        "'HARM': Hyperthermia, Autonomic instability, Rigidity (lead-pipe), and Mental status "
        "changes. NMS is a medical emergency requiring immediate discontinuation of the "
        "antipsychotic and supportive treatment with dantrolene and/or bromocriptine.",
        n
    )); n += 1

    # --- 11. Neurotransmitter-Disease Table ---
    tables.append(mk(C, N,
        "pharma-foundations.html", "Pharmacological Foundations", "Neurotransmitter-Disease Associations",
        ["Neurotransmitter", "Direction of Change", "Associated Condition"],
        [
            ["Dopamine", "Excess", "Schizophrenia (positive symptoms)"],
            ["Dopamine", "Deficit", "Parkinson's disease"],
            ["Serotonin", "Deficit", "Depression, anxiety, OCD"],
            ["GABA", "Deficit", "BLANK"],
            ["Acetylcholine", "Deficit", "Alzheimer's disease"],
            ["Glutamate", "Excess", "Excitotoxicity, seizures"],
            ["Norepinephrine", "Excess", "Anxiety, panic, hyperarousal"],
        ],
        3, 2,
        "Anxiety disorders, seizure vulnerability, insomnia",
        [
            "Schizophrenia (positive symptoms)",
            "Depression, anxiety, OCD",
            "Anxiety disorders, seizure vulnerability, insomnia",
            "Alzheimer's disease",
        ],
        2,
        "GABA (gamma-aminobutyric acid) is the primary inhibitory neurotransmitter. Deficits in "
        "GABA are associated with anxiety disorders, increased seizure vulnerability, and insomnia. "
        "Benzodiazepines work by enhancing GABA-A receptor activity, which is why they treat "
        "anxiety and seizures — a core pharmacology concept for the EPPP.",
        n
    )); n += 1

    # --- 12. CYP450 Drug Interactions ---
    tables.append(mk(C, N,
        "pharma-foundations.html", "Pharmacological Foundations", "CYP450 Drug Interactions",
        ["CYP Enzyme", "Notable Inhibitors", "Notable Inducers", "Clinical Effect"],
        [
            ["CYP2D6", "Fluoxetine, paroxetine, bupropion", "None significant", "BLANK"],
            ["CYP3A4", "Fluvoxamine, ketoconazole, grapefruit juice", "Carbamazepine, St. John's Wort", "Affects benzodiazepine and statin levels"],
            ["CYP1A2", "Fluvoxamine, ciprofloxacin", "Smoking, charbroiled foods", "Affects clozapine and theophylline levels"],
        ],
        0, 3,
        "Raises levels of TCAs, codeine prodrug activation blocked",
        [
            "Affects benzodiazepine and statin levels",
            "Raises levels of TCAs, codeine prodrug activation blocked",
            "Affects clozapine and theophylline levels",
            "Reduces absorption of all oral medications",
        ],
        1,
        "CYP2D6 inhibitors (fluoxetine, paroxetine, bupropion) raise serum levels of substrates "
        "like TCAs and block the conversion of codeine to morphine, reducing codeine's analgesic "
        "effect. This interaction between SSRIs and TCAs or codeine is commonly tested.",
        n
    )); n += 1

    # 12b. Serotonin syndrome
    tables.append(mk(C, N,
        "pharma-foundations.html", "Pharmacological Foundations", "Serotonin Syndrome vs NMS",
        ["Feature", "Serotonin Syndrome", "Neuroleptic Malignant Syndrome"],
        [
            ["Cause", "Serotonergic excess (SSRI + MAOI, etc.)", "Dopamine blockade (antipsychotics)"],
            ["Onset", "BLANK", "Days to weeks"],
            ["Neuromuscular", "Clonus, hyperreflexia, tremor", "Lead-pipe rigidity"],
            ["Treatment", "Cyproheptadine; benzodiazepines", "Dantrolene; bromocriptine"],
        ],
        1, 1,
        "Rapid (within 24 hours of drug change)",
        [
            "Days to weeks",
            "Rapid (within 24 hours of drug change)",
            "Gradual over months",
            "Only occurs after chronic use (>6 months)",
        ],
        1,
        "Serotonin syndrome has a rapid onset, typically within 24 hours of a serotonergic "
        "drug change (starting, increasing, or combining serotonergic agents). This rapid onset "
        "distinguishes it from NMS, which develops over days to weeks. The time course is a "
        "key differentiating feature tested on the EPPP.",
        n
    )); n += 1

    # --- Bonus: Antidepressant class overview ---
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "Antidepressant Class Overview",
        ["Class", "Mechanism", "Example"],
        [
            ["SSRI", "Blocks serotonin reuptake", "Fluoxetine, sertraline"],
            ["SNRI", "Blocks serotonin + norepinephrine reuptake", "Venlafaxine, duloxetine"],
            ["TCA", "Blocks 5-HT + NE reuptake (non-selectively)", "Amitriptyline, imipramine"],
            ["MAOI", "BLANK", "Phenelzine, tranylcypromine"],
            ["Atypical", "Various unique mechanisms", "Bupropion (NE/DA), mirtazapine (alpha-2)"],
        ],
        3, 1,
        "Inhibits monoamine oxidase enzyme; prevents breakdown of 5-HT, NE, DA",
        [
            "Blocks serotonin reuptake",
            "Blocks serotonin + norepinephrine reuptake",
            "Inhibits monoamine oxidase enzyme; prevents breakdown of 5-HT, NE, DA",
            "Blocks 5-HT + NE reuptake (non-selectively)",
        ],
        2,
        "MAOIs work by inhibiting the monoamine oxidase enzyme, which is responsible for "
        "breaking down serotonin (5-HT), norepinephrine (NE), and dopamine (DA). By preventing "
        "this breakdown, MAOIs increase the availability of all three monoamines. This broad "
        "mechanism distinguishes them from selective agents like SSRIs.",
        n
    )); n += 1

    # --- Bupropion and mirtazapine ---
    tables.append(mk(C, N,
        "antidepressants.html", "Antidepressants", "Atypical Antidepressants",
        ["Drug", "Mechanism", "Unique Feature"],
        [
            ["Bupropion", "NE and DA reuptake inhibitor (NDRI)", "BLANK"],
            ["Mirtazapine", "Alpha-2 antagonist; 5-HT2/5-HT3 antagonist", "Sedation and weight gain; used for insomnia/appetite loss"],
            ["Trazodone", "SARI (5-HT2 antagonist + reuptake inhibitor)", "Low-dose for insomnia; priapism risk"],
            ["Vilazodone", "SSRI + 5-HT1A partial agonist", "Less sexual dysfunction than pure SSRIs"],
        ],
        0, 2,
        "No sexual dysfunction; lowers seizure threshold; aids smoking cessation",
        [
            "Sedation and weight gain; used for insomnia/appetite loss",
            "No sexual dysfunction; lowers seizure threshold; aids smoking cessation",
            "Low-dose for insomnia; priapism risk",
            "Less sexual dysfunction than pure SSRIs",
        ],
        1,
        "Bupropion (Wellbutrin) is notable for its lack of sexual side effects (unlike SSRIs) "
        "and its FDA approval for smoking cessation (as Zyban). Its main risk is lowering the "
        "seizure threshold, making it contraindicated in eating disorders and seizure history.",
        n
    )); n += 1

    # --- Lithium toxicity levels ---
    tables.append(mk(C, N,
        "mood-stabilizers.html", "Mood Stabilizers", "Lithium Serum Levels",
        ["Level (mEq/L)", "Clinical Significance"],
        [
            ["0.6 - 1.2", "Therapeutic range for acute mania"],
            ["0.6 - 0.8", "Maintenance range"],
            ["1.5 - 2.0", "BLANK"],
            ["2.0 - 2.5", "Moderate to severe toxicity; seizures, cardiac arrhythmia"],
            ["> 2.5", "Life-threatening; dialysis required"],
        ],
        2, 1,
        "Mild toxicity: tremor, nausea, diarrhea, blurred vision",
        [
            "Therapeutic range for acute mania",
            "Mild toxicity: tremor, nausea, diarrhea, blurred vision",
            "Moderate to severe toxicity; seizures, cardiac arrhythmia",
            "Maintenance range",
        ],
        1,
        "Lithium levels of 1.5-2.0 mEq/L represent mild toxicity characterized by tremor, "
        "nausea, diarrhea, and blurred vision. Knowing the specific level ranges and their "
        "associated symptoms is essential for the EPPP. The narrow therapeutic window makes "
        "lithium monitoring a critical clinical skill.",
        n
    )); n += 1

    return tables


# ======================================================================
#  CPAT — DSM-5 diagnostic comparison tables
# ======================================================================

def build_cpat_tables(start_id: int) -> list:
    C = "CPAT"
    N = "Psychopathology"
    tables = []
    n = start_id

    # --- 1. MDD vs Bipolar I vs Bipolar II ---
    tables.append(mk(C, N,
        "mood-disorders.html", "Mood Disorders", "MDD vs Bipolar I vs Bipolar II",
        ["Feature", "MDD", "Bipolar I", "Bipolar II"],
        [
            ["Mania", "Absent", "Present (required for dx)", "Absent"],
            ["Hypomania", "Absent", "May be present", "Present (required for dx)"],
            ["Depression", "Required", "May be present", "Required"],
            ["Episode duration", "2+ weeks", "BLANK", "Hypomania: 4+ days"],
            ["Psychotic features", "Possible", "Possible (during mania)", "Not during hypomania"],
        ],
        3, 2,
        "Mania: 1+ week (or any if hospitalized)",
        [
            "2+ weeks",
            "Mania: 1+ week (or any if hospitalized)",
            "Hypomania: 4+ days",
            "Mania: 2+ days minimum",
        ],
        1,
        "Bipolar I manic episodes must last at least 1 week, unless hospitalization is required "
        "(in which case any duration qualifies). This is a key distinction from Bipolar II "
        "hypomania (4+ days) and MDD depressive episodes (2+ weeks).",
        n
    )); n += 1

    # --- 2. GAD vs Panic Disorder ---
    tables.append(mk(C, N,
        "anxiety-ocd.html", "Anxiety & OCD", "GAD vs Panic Disorder Comparison",
        ["Feature", "GAD", "Panic Disorder"],
        [
            ["Core symptom", "Excessive worry about multiple areas", "Recurrent unexpected panic attacks"],
            ["Duration", "BLANK", "Discrete episodes (minutes)"],
            ["Physical symptoms", "Muscle tension, restlessness, fatigue", "Chest pain, heart pounding, derealization"],
            ["Avoidance", "Difficulty controlling worry", "Fear of future attacks; agoraphobia may develop"],
            ["Age of onset", "Often gradual; median ~30 years", "Late adolescence to mid-30s"],
        ],
        1, 1,
        "Most days for 6+ months",
        [
            "Discrete episodes (minutes)",
            "Most days for 6+ months",
            "2+ weeks of sustained worry",
            "At least 1 month of persistent concern",
        ],
        1,
        "GAD requires excessive worry occurring more days than not for at least 6 months. This "
        "prolonged duration criterion distinguishes it from panic disorder (discrete episodes) "
        "and from adjustment disorders (within 3 months of stressor). The 6-month requirement "
        "is one of the most tested GAD criteria.",
        n
    )); n += 1

    # --- 3. Schizophrenia vs Schizoaffective vs Brief Psychotic ---
    tables.append(mk(C, N,
        "schizophrenia.html", "Schizophrenia Spectrum", "Schizophrenia Spectrum Comparison",
        ["Disorder", "Duration", "Mood Episodes", "Key Feature"],
        [
            ["Schizophrenia", "6+ months (1+ month active)", "Not prominent relative to psychosis", "Must rule out mood disorder as cause"],
            ["Schizoaffective", "Continuous illness period", "BLANK", "Psychosis must occur without mood episodes for 2+ weeks"],
            ["Brief Psychotic", "1 day to 1 month", "Not a criterion", "Full remission within 1 month"],
            ["Schizophreniform", "1-6 months", "Not a criterion", "Same symptoms as schizophrenia, shorter duration"],
        ],
        1, 2,
        "Major mood episode present for majority of illness duration",
        [
            "Not prominent relative to psychosis",
            "Major mood episode present for majority of illness duration",
            "Not a criterion",
            "Mood episodes only during active psychosis phase",
        ],
        1,
        "Schizoaffective disorder requires that a major mood episode (depressive or manic) be "
        "present for the majority of the total illness duration. The critical distinguishing "
        "criterion is that psychotic symptoms must also occur for 2+ weeks in the ABSENCE of "
        "a mood episode. This bidirectional requirement is frequently tested.",
        n
    )); n += 1

    # --- 4. Bipolar I vs Bipolar II detailed ---
    tables.append(mk(C, N,
        "mood-disorders.html", "Mood Disorders", "Bipolar I vs Bipolar II",
        ["Feature", "Bipolar I", "Bipolar II"],
        [
            ["Defining episode", "At least one manic episode", "At least one hypomanic + one depressive episode"],
            ["Mania duration", "7+ days or hospitalization", "N/A (hypomania: 4+ days)"],
            ["Functional impairment", "Marked impairment in mania", "BLANK"],
            ["Psychosis", "May occur during mania", "Does not occur during hypomania"],
            ["Hospitalization", "Often required in mania", "Typically not for hypomania"],
        ],
        2, 2,
        "No marked impairment from hypomania (depression may impair)",
        [
            "Marked impairment in mania",
            "No marked impairment from hypomania (depression may impair)",
            "Equal impairment from hypomania and depression",
            "Impairment only occurs during mixed episodes",
        ],
        1,
        "A key DSM-5 distinction is that Bipolar II hypomanic episodes do NOT cause marked "
        "functional impairment (though the depressive episodes may). If the elevated mood "
        "episode causes marked impairment or psychosis, it is reclassified as mania and the "
        "diagnosis becomes Bipolar I. This boundary is heavily tested on the EPPP.",
        n
    )); n += 1

    # --- 5. Anxiety disorder onset/prevalence ---
    tables.append(mk(C, N,
        "anxiety-ocd.html", "Anxiety & OCD", "Anxiety Disorder Onset and Prevalence",
        ["Disorder", "Typical Onset", "Lifetime Prevalence"],
        [
            ["Specific phobia", "Childhood (7-11 years)", "~12%"],
            ["Social anxiety disorder", "Early adolescence (~13 years)", "~7%"],
            ["Panic disorder", "Late adolescence to mid-30s", "~3-5%"],
            ["GAD", "Variable; median ~30 years", "~6%"],
            ["Agoraphobia", "Late adolescence to early adulthood", "BLANK"],
        ],
        4, 2,
        "~1.7%; two-thirds of cases develop before age 35",
        [
            "~12%",
            "~7%",
            "~1.7%; two-thirds of cases develop before age 35",
            "~3-5%",
        ],
        2,
        "Agoraphobia has a lifetime prevalence of approximately 1.7%, with two-thirds of cases "
        "developing before age 35. It is often comorbid with panic disorder but can be diagnosed "
        "independently. The relatively low prevalence compared to specific phobia (~12%) is a "
        "testable distinction.",
        n
    )); n += 1

    # --- 6. Personality disorder cluster comparison ---
    tables.append(mk(C, N,
        "personality-disorders.html", "Personality Disorders", "Cluster Comparison",
        ["Cluster", "Description", "Disorders"],
        [
            ["Cluster A", "Odd/Eccentric", "Paranoid, Schizoid, Schizotypal"],
            ["Cluster B", "Dramatic/Erratic", "BLANK"],
            ["Cluster C", "Anxious/Fearful", "Avoidant, Dependent, Obsessive-Compulsive"],
        ],
        1, 2,
        "Antisocial, Borderline, Histrionic, Narcissistic",
        [
            "Paranoid, Schizoid, Schizotypal",
            "Antisocial, Borderline, Histrionic, Narcissistic",
            "Avoidant, Dependent, Obsessive-Compulsive",
            "Borderline, Dependent, Schizotypal, Antisocial",
        ],
        1,
        "Cluster B personality disorders are the 'dramatic, emotional, erratic' cluster and "
        "include Antisocial, Borderline, Histrionic, and Narcissistic. This grouping is one of "
        "the most commonly tested personality disorder facts. Cluster A is 'odd/eccentric' and "
        "Cluster C is 'anxious/fearful.'",
        n
    )); n += 1

    return tables


# ======================================================================
#  PMET — Statistical test selection tables
# ======================================================================

def build_pmet_tables(start_id: int) -> list:
    C = "PMET"
    N = "Psychological Measurement"
    tables = []
    n = start_id

    # --- 1. Statistical Test Selection ---
    tables.append(mk(C, N,
        "inferential-statistics.html", "From Samples to Populations: Inferential Statistics",
        "Statistical Test Selection",
        ["Test", "# of Groups", "DV Scale", "When to Use"],
        [
            ["Independent t-test", "2 independent", "Interval/Ratio", "Compare means of 2 unrelated groups"],
            ["Paired t-test", "2 related", "Interval/Ratio", "Compare means from same subjects (pre/post)"],
            ["One-way ANOVA", "3+ independent", "Interval/Ratio", "BLANK"],
            ["Chi-square", "2+ independent", "Nominal", "Test association between categorical variables"],
            ["Pearson r", "N/A (2 variables)", "Interval/Ratio", "Measure linear relationship strength"],
        ],
        2, 3,
        "Compare means across 3+ unrelated groups",
        [
            "Compare means of 2 unrelated groups",
            "Compare means from same subjects (pre/post)",
            "Compare means across 3+ unrelated groups",
            "Test association between categorical variables",
        ],
        2,
        "One-way ANOVA is used to compare means across three or more independent groups. It "
        "requires an interval/ratio dependent variable and tests whether at least one group mean "
        "differs significantly. If only two groups exist, the independent t-test is used instead. "
        "Post-hoc tests (e.g., Tukey) are needed to identify which groups differ.",
        n
    )); n += 1

    # --- 2. Statistical Assumptions ---
    tables.append(mk(C, N,
        "inferential-statistics.html", "From Samples to Populations: Inferential Statistics",
        "Test Assumptions",
        ["Test", "Key Assumptions"],
        [
            ["Independent t-test", "Normality, homogeneity of variance, independence"],
            ["ANOVA", "BLANK"],
            ["Chi-square", "Expected cell frequencies >= 5; independent observations"],
            ["Pearson r", "Linearity, bivariate normality, homoscedasticity"],
        ],
        1, 1,
        "Normality, homogeneity of variance, independence of observations",
        [
            "Expected cell frequencies >= 5; independent observations",
            "Normality, homogeneity of variance, independence of observations",
            "Linearity, bivariate normality, homoscedasticity",
            "Normality, homogeneity of variance, independence",
        ],
        1,
        "ANOVA shares the same three assumptions as the t-test: normality of distributions, "
        "homogeneity of variance (tested with Levene's test), and independence of observations. "
        "ANOVA is robust to minor violations of normality with large samples but sensitive to "
        "violations of independence.",
        n
    )); n += 1

    # --- 3. Effect size measures ---
    tables.append(mk(C, N,
        "inferential-statistics.html", "From Samples to Populations: Inferential Statistics",
        "Effect Size Measures",
        ["Statistic", "Effect Size Measure", "Small", "Medium", "Large"],
        [
            ["t-test", "Cohen's d", "0.2", "0.5", "0.8"],
            ["ANOVA", "Eta-squared", "0.01", "0.06", "0.14"],
            ["Correlation", "r", "0.10", "0.30", "BLANK"],
            ["Chi-square", "Cramer's V", "0.10", "0.30", "0.50"],
        ],
        2, 4,
        "0.50",
        [
            "0.14",
            "0.30",
            "0.50",
            "0.80",
        ],
        2,
        "According to Cohen's conventions, a correlation coefficient (r) of 0.50 represents a "
        "large effect size. The benchmarks for r are: 0.10 (small), 0.30 (medium), 0.50 (large). "
        "These parallel Cramer's V conventions but differ from Cohen's d (0.2, 0.5, 0.8).",
        n
    )); n += 1

    # --- 4. ANOVA types ---
    tables.append(mk(C, N,
        "inferential-statistics.html", "From Samples to Populations: Inferential Statistics",
        "Types of ANOVA",
        ["ANOVA Type", "IVs", "Design", "What It Tests"],
        [
            ["One-way", "1 IV", "Between-subjects", "Main effect of one factor"],
            ["Factorial", "2+ IVs", "Between-subjects", "BLANK"],
            ["Repeated measures", "1 IV", "Within-subjects", "Same subjects across conditions"],
            ["Mixed", "2+ IVs", "Between + Within", "At least one between and one within factor"],
        ],
        1, 3,
        "Main effects of each factor + interaction effects",
        [
            "Main effect of one factor",
            "Main effects of each factor + interaction effects",
            "Same subjects across conditions",
            "At least one between and one within factor",
        ],
        1,
        "Factorial ANOVA tests main effects of each independent variable AND their interaction "
        "effects. A 2x3 factorial ANOVA, for example, tests two main effects and one interaction. "
        "The ability to detect interactions is a key advantage over running separate one-way "
        "ANOVAs, which cannot detect how variables combine.",
        n
    )); n += 1

    # --- 5. Regression types ---
    tables.append(mk(C, N,
        "correlation-regression.html", "Relationships in Data: Correlation & Regression",
        "Types of Regression",
        ["Type", "# of Predictors", "DV Type", "Use"],
        [
            ["Simple linear", "1 continuous", "Continuous", "Predict Y from one X"],
            ["Multiple", "2+ continuous", "Continuous", "BLANK"],
            ["Logistic", "1+ continuous or categorical", "Dichotomous", "Predict group membership (yes/no)"],
        ],
        1, 3,
        "Predict Y from multiple Xs; partial out shared variance",
        [
            "Predict Y from one X",
            "Predict Y from multiple Xs; partial out shared variance",
            "Predict group membership (yes/no)",
            "Predict ranked outcomes from interval predictors",
        ],
        1,
        "Multiple regression predicts a continuous outcome from two or more predictors while "
        "accounting for (partialing out) the shared variance among predictors. This ability to "
        "isolate unique predictor contributions distinguishes it from simple linear regression "
        "(one predictor) and logistic regression (dichotomous outcome).",
        n
    )); n += 1

    # --- 6. Threats to internal validity ---
    tables.append(mk(C, N,
        "research-designs.html", "Blueprints for Discovery: Research Designs",
        "Threats to Internal Validity",
        ["Threat", "Definition", "Example"],
        [
            ["History", "External events during study", "National crisis affects mood study results"],
            ["Maturation", "BLANK", "Children improve due to natural development"],
            ["Testing", "Prior test exposure affects scores", "Practice effects on repeated IQ tests"],
            ["Instrumentation", "Measurement tool changes over time", "Raters become more lenient"],
            ["Regression to mean", "Extreme scores move toward average", "Highest scorers score lower on retest"],
        ],
        1, 1,
        "Participants change due to passage of time, not treatment",
        [
            "External events during study",
            "Participants change due to passage of time, not treatment",
            "Prior test exposure affects scores",
            "Measurement tool changes over time",
        ],
        1,
        "Maturation refers to changes in participants that occur simply due to the passage of "
        "time (e.g., growing older, more experienced, more fatigued) rather than the independent "
        "variable. This is commonly confused with history (external events) but maturation is "
        "specifically about internal biological or psychological changes over time.",
        n
    )); n += 1

    return tables


# ======================================================================
#  Main
# ======================================================================

def main():
    print("=== expand_tables.py ===\n")

    added_counts = {}

    # --- PETH ---
    peth = load_domain("PETH")
    sid = next_id(peth, "PETH")
    new_peth = build_peth_tables(sid)
    peth["questions"].extend(new_peth)
    peth["total_questions"] = len(peth["questions"])
    save_domain("PETH", peth)
    added_counts["PETH"] = len(new_peth)

    # --- CPAT ---
    cpat = load_domain("CPAT")
    sid = next_id(cpat, "CPAT")
    new_cpat = build_cpat_tables(sid)
    cpat["questions"].extend(new_cpat)
    cpat["total_questions"] = len(cpat["questions"])
    save_domain("CPAT", cpat)
    added_counts["CPAT"] = len(new_cpat)

    # --- PMET ---
    pmet = load_domain("PMET")
    sid = next_id(pmet, "PMET")
    new_pmet = build_pmet_tables(sid)
    pmet["questions"].extend(new_pmet)
    pmet["total_questions"] = len(pmet["questions"])
    save_domain("PMET", pmet)
    added_counts["PMET"] = len(new_pmet)

    # --- Summary ---
    print("\n=== Tables added ===")
    for code, count in added_counts.items():
        print(f"  {code}: +{count} new tables")

    # --- Validate ALL options ≤ 140 chars ---
    print("\n=== Validation: option length <= 140 chars ===")
    all_ok = True
    for code in ["BPSY", "CASS", "CPAT", "LDEV", "PETH", "PMET", "PTHE", "SOCU", "WDEV"]:
        data = load_domain(code)
        total = len(data["questions"])
        violations = 0
        for q in data["questions"]:
            for opt in q["options"]:
                if len(opt) > MAX_OPT:
                    violations += 1
        over_pct = violations / total * 100 if total else 0
        usable = sum(1 for q in data["questions"]
                     if all(len(o) <= MAX_OPT for o in q["options"]))
        print(f"  {code}: {total} total, {usable} usable (all opts ≤140), "
              f"{total - usable} filtered out")
        if violations > 0:
            all_ok = False

    if all_ok:
        print("\n  All NEW tables pass the 140-char check.")
    else:
        print("\n  WARNING: Some tables have options > 140 chars (pre-existing).")

    print()


if __name__ == "__main__":
    main()
