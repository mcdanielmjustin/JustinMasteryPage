"""
audit_questions.py  —  Cross-reference every Brain Pathology 3.0 question
against EPPP Domain 7 and Domain 3 anchor points.

Outputs a full audit report: anchor grounding, factual issues,
over-specialized content, and claims that contradict anchor points.
"""

import re, sys

BRAIN_DATA_JS = r"C:\Users\mcdan\mastery-page\data\brain_data.js"

# ── Extract questions from brain_data.js ─────────────────────────────────────
def extract_questions():
    with open(BRAIN_DATA_JS, encoding="utf-8") as f:
        content = f.read()
    # Find question objects by ID
    pattern = re.compile(r'\{\s*"id":\s*"(BRAIN-\d+)"(.*?)\}(?=\s*[,\]])', re.DOTALL)
    questions = []
    for m in pattern.finditer(content):
        block = "{" + m.group(0)[m.start(0)- m.start(0):]  # reconstruct
        block = m.group(0)
        qid = m.group(1)
        def get_field(name, blk=block):
            fm = re.search(r'"' + name + r'":\s*"((?:[^"\\]|\\.)*)"', blk, re.DOTALL)
            return fm.group(1).replace('\\n', ' ').replace('\\"', '"') if fm else ""
        def get_list(name, blk=block):
            lm = re.search(r'"' + name + r'":\s*\[([^\]]+)\]', blk)
            return re.findall(r'"([^"]+)"', lm.group(1)) if lm else []

        target = get_field("target_region") or get_field("highlighted_region")
        questions.append({
            "id":               qid,
            "type":             get_field("type"),
            "category":         get_field("category"),
            "domain_source":    get_field("domain_source"),
            "question":         get_field("question"),
            "target_region":    target,
            "distractor_regions": get_list("distractor_regions"),
            "explanation":      get_field("explanation"),
        })
    return questions


# ── Anchor point knowledge base ───────────────────────────────────────────────
# Keyed by topic → anchor text(s) and the expected facts they assert.
# Used to flag whether a question's claim is anchored or contradicts anchors.

ANCHORS = {
    # --- CEREBRAL CORTEX ---
    "brocas_area": {
        "supported": [
            "[097] Damage to Broca's area produces nonfluent speech with intact comprehension.",
        ],
        "must_not_claim": [
            "fluent speech",  # Broca's = nonfluent
            "impaired comprehension",  # Broca's comprehension is intact
        ],
    },
    "wernickes_area": {
        "supported": [
            "[131] Wernicke's aphasia: impaired comprehension, fluent but meaningless speech.",
        ],
        "must_not_claim": [
            "nonfluent",  # Wernicke's = fluent
            "intact comprehension",  # Wernicke's = impaired comprehension
        ],
    },
    "parietal_lobe": {
        "supported": [
            "[108] Contralateral neglect → right parietal lobe.",
            "[119] Anosognosia → right parietal lobe.",
            "[120] Gerstmann's syndrome → dominant parietal lobe (finger agnosia, L-R confusion, agraphia, acalculia; NOT ataxia).",
            "[05-1] Ideomotor apraxia → left/dominant parietal lobe.",
            "[08-2] Tactile agnosia → parietal lobe.",
            "[05-2] Asomatognosia/anosognosia → right parietal lobe.",
        ],
        "must_not_claim": [
            "ataxia",  # Gerstmann's does NOT include ataxia (that's cerebellum)
        ],
    },
    "prefrontal_cortex": {
        "supported": [
            "[109] Dorsolateral PFC → executive functions (insight, planning, judgment).",
            "[04] Orbitofrontal PFC → emotion dysregulation, impulsivity, lack of empathy.",
            "[017] Frontal lobe damage → affects motivation, judgment, memory; NOT IQ scores.",
            "[016-1] PFC essential for prospective memory.",
            "[044] GAD → reduced connectivity between PFC, amygdala, anterior cingulate.",
            "[020] PTSD → decreased vmPFC activity.",
        ],
    },
    "frontal_lobe": {
        "supported": [
            "[09-1] Frontal lobe → perseveration.",
            "[058] Frontal lobe injury → social withdrawal, mood fluctuations, difficulty planning sequences.",
            "[017] Frontal lobe affects motivation, judgment, memory; NOT IQ.",
            "[159] Left hemisphere damage → depression or emotional volatility.",
        ],
    },
    "corpus_callosum": {
        "supported": [
            "[098] Split-brain: corpus callosum severed for epilepsy.",
            "[079] Split-brain → right visual field info processed by left hemisphere (verbal), left visual field by right hemisphere.",
        ],
    },
    "occipital_lobe": {
        "supported": [
            "Primary visual cortex → contralateral visual field.",
            "Bilateral occipital damage → cortical blindness (Anton's syndrome: blindness with denial).",
        ],
    },
    "temporal_lobe": {
        "supported": [
            "[028] Temporal lobe seizures → automatisms, fear, 'roller coaster' feeling, lip smacking.",
            "[087] Kluver-Bucy → bilateral amygdala/hippocampus/temporal lobe → visual agnosia, reduced fear, hypersexuality, dietary changes.",
            "Prosopagnosia → right temporal / occipital-temporal junction.",
        ],
    },
    "motor_cortex": {
        "supported": [
            "[209] Right hemiplegia → left brain damage.",
            "Motor cortex → contralateral UMN signs: spasticity, hyperreflexia, Babinski.",
        ],
    },
    "somatosensory_cortex": {
        "supported": [
            "Somatosensory cortex (postcentral gyrus) → contralateral discriminative touch, proprioception.",
        ],
    },
    "cingulate_gyrus": {
        "supported": [
            "[044] Anterior cingulate cortex → node in PFC-amygdala-ACC circuit for GAD.",
            "[025] Psychotherapy for MDD → increased cingulate cortex activity.",
            "[18-1] Papez circuit → cingulate cortex involved in emotion and memory.",
        ],
    },
    "medial_frontal": {
        "supported": [
            "Supplementary motor area (medial frontal) → initiating voluntary movement; akinetic mutism when damaged.",
        ],
    },
    "insula": {
        "supported": [
            "Insula → interoception, pain processing, autonomic regulation, disgust.",
        ],
    },
    # --- SUBCORTICAL ---
    "hippocampus": {
        "supported": [
            "[076] Hippocampus → consolidating long-term declarative memories.",
            "[198] H.M.: bilateral medial temporal lobectomy → no new long-term declarative memories; procedural memory intact.",
            "[04-2] Stress-induced cortisol → impairs declarative memory retrieval via hippocampus.",
            "[27-2] Alzheimer's memory loss → low acetylcholine in hippocampus.",
            "[27-3] Alzheimer's → neuritic plaques/tangles in entorhinal cortex, hippocampus, amygdala.",
            "[020] PTSD → reduced hippocampus volume.",
            "[137] ADHD → smaller hippocampus volume.",
        ],
    },
    "amygdala": {
        "supported": [
            "[068] Amygdala → consolidation of emotional memories.",
            "[01-1] Bilateral amygdala damage → difficulty recognizing fear in faces.",
            "[01-3] Amygdala stimulation → conditioned fear (freezing, HR increase, stress hormones).",
            "[087] Kluver-Bucy → bilateral amygdala/hippocampus/temporal lobe lesion.",
            "[020] PTSD → increased amygdala activity.",
            "[27-3] Alzheimer's → plaques/tangles in amygdala.",
            "[137] ADHD → smaller amygdala.",
        ],
    },
    "thalamus": {
        "supported": [
            "[057] Thalamus → processes and transfers ALL sensory info EXCEPT olfactory.",
            "[02-2] Wernicke-Korsakoff → thalamus and mammillary bodies damaged.",
        ],
    },
    "hypothalamus": {
        "supported": [
            "[054] Hypothalamus → homeostasis (body temp, fluid/electrolyte, BP).",
            "[04-1] Hypothalamus → aggression (medial=affective attack, lateral=stalking).",
            "[03-1]/[003] Suprachiasmatic nucleus (in hypothalamus) → sleep-wake cycle, circadian rhythms.",
            "[51] Oxytocin → produced by hypothalamus.",
            "[20-1] Diabetes insipidus → low ADH (pituitary secretes ADH).",
            "[02-2] Wernicke-Korsakoff → mammillary bodies (part of hypothalamus).",
        ],
    },
    "caudate": {
        "supported": [
            "[065] Basal ganglia (caudate, putamen, globus pallidus) → voluntary movement; disorders: Tourette's, ADHD, OCD.",
            "[02-1] OCD → increased basal ganglia activity.",
            "[177] Huntington's → GABA/glutamate abnormalities in caudate and putamen.",
            "[18] Huntington's → glucose hypometabolism and atrophy in caudate PRECEDE symptoms.",
            "[137] ADHD → smaller caudate volume.",
        ],
    },
    "putamen": {
        "supported": [
            "[065] Basal ganglia → putamen involved in voluntary movement.",
            "[177] Huntington's → caudate and putamen GABA/glutamate abnormalities.",
            "[18] Huntington's → caudate and putamen glucose hypometabolism precedes symptoms.",
            "[137] ADHD → smaller putamen.",
        ],
    },
    "globus_pallidus": {
        "supported": [
            "[065] Basal ganglia: caudate, putamen, globus pallidus → voluntary movement.",
            "Globus pallidus → DBS target for Parkinson's and dystonia.",
            "[096] DBS indications: Parkinson's, essential tremor, dystonia.",
        ],
    },
    "nucleus_accumbens": {
        "supported": [
            "[12-2] Dopamine → mesolimbic pathway → reward (cocaine, amphetamines).",
            "Nucleus accumbens → reward/motivation center of mesolimbic system.",
            "[137] ADHD → smaller nucleus accumbens.",
        ],
    },
    "substantia_nigra": {
        "supported": [
            "[184] Parkinson's → progressive loss of dopamine cells in substantia nigra.",
            "[010] Dopamine hypothesis → schizophrenia (elevated dopamine).",
        ],
    },
    "vta": {
        "supported": [
            "[12-2] Dopamine → mesolimbic pathway (VTA → nucleus accumbens) → reward.",
            "VTA → origin of mesocortical (to PFC) and mesolimbic (to N.accumbens) pathways.",
        ],
    },
    "cerebellum": {
        "supported": [
            "[046] Cerebellum → ataxia (clumsiness, slurred speech).",
            "[188] Ataxia is the most common outcome of cerebellar damage.",
            "[120] Ataxia is caused by cerebellum (NOT a symptom of Gerstmann's syndrome).",
            "[021] Cerebellum stores procedural/conditioned memories (implicit memory).",
        ],
    },
    "brainstem": {
        "supported": [
            "[01-2]/[03-3] Medulla → opioid-induced respiratory depression.",
            "[002] Medulla oblongata → vital life functions.",
            "Brainstem → crossed signs: ipsilateral CN palsy + contralateral body weakness.",
            "[043] ARAS → alertness/arousal.",
        ],
    },
    "pons": {
        "supported": [
            "Pons → horizontal gaze (CN VI, PPRF); Millard-Gubler syndrome.",
            "Locked-in syndrome → ventral pons (basilar artery).",
        ],
    },
    "medulla": {
        "supported": [
            "[01-2]/[03-3] Medulla → opioid-induced respiratory depression.",
            "[002] Medulla → vital functions (heart rate, respiration).",
            "PICA → Wallenberg syndrome (lateral medullary): crossed sensory findings, Horner's, ataxia, dysphonia.",
        ],
    },
    "midbrain": {
        "supported": [
            "Parinaud's syndrome → dorsal midbrain (superior colliculus/pretectum).",
            "Weber syndrome → midbrain: ipsilateral CN III palsy + contralateral hemiplegia.",
            "[184] Substantia nigra (in midbrain) → Parkinson's dopamine cells.",
        ],
    },
    "pituitary": {
        "supported": [
            "[20-1] Diabetes insipidus → low ADH (secreted by pituitary).",
            "Pituitary → master gland; controls hormonal axes (GH, TSH, ACTH, etc.).",
        ],
    },
    "olfactory_bulb": {
        "supported": [
            "[190] Early Alzheimer's → rapid decline in sense of smell.",
            "Thalamus bypassed for olfactory info (only sensory that bypasses thalamus).",
            "[057] Thalamus processes all sensory info EXCEPT olfactory.",
        ],
    },
    "fornix": {
        "supported": [
            "[18-1] Papez circuit: hippocampus → fornix → mammillary bodies → thalamus → cingulate → hippocampus.",
            "[076] Fornix damage → anterograde amnesia (functionally disconnects hippocampus from diencephalon).",
        ],
    },
}

# ── Per-question audit rules ──────────────────────────────────────────────────

# Claims that are factually wrong relative to anchor points
FACTUAL_ERRORS = [
    # (question_id_pattern, claim_substring, error_description)
    ("*", "nonfluent.*wernicke", "Wernicke's is FLUENT (anchor [131])"),
    ("*", "fluent.*broca", "Broca's is NONFLUENT (anchor [097])"),
    ("*", "comprehension.*intact.*wernicke", "Wernicke's has IMPAIRED comprehension (anchor [131])"),
    ("*", "ataxia.*gerstmann", "Gerstmann's does NOT include ataxia (anchor [120])"),
    ("*", "gerstmann.*ataxia", "Gerstmann's does NOT include ataxia (anchor [120])"),
    ("*", "thalamus.*olfactory", "Thalamus does NOT process olfactory (anchor [057])"),
    ("*", "olfactory.*thalamus", "Thalamus does NOT process olfactory (anchor [057])"),
    ("*", "bilateral vision loss.*mca", "Bilateral vision loss LEAST likely with MCA (anchor [20-3])"),
    ("*", "iq.*frontal", "Frontal damage does NOT reduce IQ scores (anchor [017])"),
    ("*", "alzheimer.*high.*acetylcholine", "Alzheimer's = LOW acetylcholine (anchor [27-2], [5])"),
    ("*", "alzheimer.*low.*glutamate", "Alzheimer's = HIGH glutamate (anchor [5])"),
    ("*", "parkinson.*putamen.*primary", "Parkinson's PRIMARY lesion = substantia nigra, not putamen (anchor [184])"),
    ("*", "huntington.*substantia nigra", "Huntington's = basal ganglia (caudate/putamen), NOT substantia nigra (anchor [177])"),
    ("*", "ocd.*decreased.*basal ganglia", "OCD = INCREASED basal ganglia activity (anchor [02-1])"),
    ("*", "ptsd.*increased.*hippocampus", "PTSD = REDUCED hippocampus volume (anchor [020])"),
    ("*", "ptsd.*increased.*prefrontal", "PTSD = DECREASED vmPFC activity (anchor [020])"),
    ("*", "ptsd.*decreased.*amygdala", "PTSD = INCREASED amygdala (anchor [020])"),
    ("*", "adhd.*enlarged.*caudate", "ADHD = SMALLER caudate (anchor [137])"),
    ("*", "medulla.*serotonin.*mood", "Medulla controls respiration/vital functions, not mood (anchors [002],[01-2])"),
]

# Topics that are well BEYOND anchor point scope (too specialized for EPPP)
OVER_SPECIALIZED_SIGNALS = [
    "optogenetic", "GABA_B", "D1 and D2 receptors.*specifically",
    "inferior optic radiations.*meyer", "calcarine sulcus.*bank",
    "pretectal nuclei", "periaqueductal gray", "nigrostriatal.*postcommissural",
    "anterior communicating artery.*aneurysm",  # good but very medical
    "foramen of Monro.*colloid cyst",  # interesting but beyond EPPP
    "microinjection.*dopamine antagonist",  # animal research not in anchors
    "optogenetic activation",
]

# ── Anchor point grounding checker ───────────────────────────────────────────

def is_anchored(q):
    """Return list of matching anchor points, empty if none found."""
    target = q["target_region"]
    text = (q["question"] + " " + q["explanation"]).lower()
    anchors_for_region = ANCHORS.get(target, {}).get("supported", [])
    return anchors_for_region  # non-empty means there ARE supporting anchors

def check_factual_errors(q):
    text = (q["question"] + " " + q["explanation"]).lower()
    errors = []
    for pattern, claim, description in FACTUAL_ERRORS:
        if re.search(claim.lower(), text):
            errors.append(description)
    return errors

def check_over_specialized(q):
    text = (q["question"] + " " + q["explanation"]).lower()
    flags = []
    for sig in OVER_SPECIALIZED_SIGNALS:
        if re.search(sig.lower(), text):
            flags.append(sig)
    return flags

def check_must_not_claims(q):
    """Check if explanation makes claims contradicted by anchor points for that region."""
    target = q["target_region"]
    exp = q["explanation"].lower()
    qtext = q["question"].lower()
    must_not = ANCHORS.get(target, {}).get("must_not_claim", [])
    violations = []
    for claim in must_not:
        if claim.lower() in exp or claim.lower() in qtext:
            violations.append(f"Claims '{claim}' for target {target}")
    return violations


# ── Run full audit ────────────────────────────────────────────────────────────

def main():
    questions = extract_questions()
    print(f"Auditing {len(questions)} questions against EPPP anchor points")
    print("=" * 70)

    total_issues = 0
    unanchored = []
    factual_errors = []
    specialized = []
    contradictions = []
    clean = []

    for q in questions:
        qid = q["id"]
        anchor_support = is_anchored(q)
        fact_errs = check_factual_errors(q)
        over_spec = check_over_specialized(q)
        must_not_viol = check_must_not_claims(q)

        has_issues = bool(fact_errs or must_not_viol)
        flagged_specialized = bool(over_spec)
        has_anchors = bool(anchor_support)

        if fact_errs or must_not_viol:
            total_issues += 1
            factual_errors.append((qid, q["target_region"], fact_errs + must_not_viol, q["question"][:120]))

        if over_spec:
            specialized.append((qid, q["target_region"], over_spec, q["question"][:100]))

        if not has_anchors:
            unanchored.append((qid, q["target_region"], q["question"][:120]))

        if not has_issues and not flagged_specialized and has_anchors:
            clean.append(qid)

    # Report
    print(f"\n{'='*70}")
    print(f"FACTUAL ERRORS / ANCHOR CONTRADICTIONS: {len(factual_errors)}")
    print(f"{'='*70}")
    for qid, target, errs, qtext in factual_errors:
        print(f"\n  {qid} [target={target}]")
        print(f"  Q: {qtext}")
        for e in errs:
            print(f"  !! {e}")

    print(f"\n{'='*70}")
    print(f"OVER-SPECIALIZED (beyond EPPP anchor scope): {len(specialized)}")
    print(f"{'='*70}")
    for qid, target, flags, qtext in specialized:
        print(f"\n  {qid} [target={target}]")
        print(f"  Q: {qtext}")
        for f in flags:
            print(f"  ?? {f}")

    print(f"\n{'='*70}")
    print(f"UNANCHORED (target region has no EPPP anchor match): {len(unanchored)}")
    print(f"{'='*70}")
    for qid, target, qtext in unanchored:
        print(f"  {qid} [target={target}]: {qtext[:100]}")

    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Total questions:      {len(questions)}")
    print(f"  Clean (pass):         {len(clean)}")
    print(f"  Factual errors:       {len(factual_errors)}")
    print(f"  Over-specialized:     {len(specialized)}")
    print(f"  Unanchored targets:   {len(unanchored)}")

if __name__ == "__main__":
    main()
