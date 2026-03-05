"""
Fix over-specialized questions in brain_data.js
"""
import re

BRAIN_DATA_JS = r"C:\Users\mcdan\mastery-page\data\brain_data.js"

with open(BRAIN_DATA_JS, encoding="utf-8") as f:
    content = f.read()

# Helper: replace field value for a given question ID
def replace_field(content, qid, field, new_value):
    """Replace the string value of a JSON field inside the question with qid."""
    # Find the question block
    qid_idx = content.find(f'"id": "{qid}"')
    if qid_idx == -1:
        qid_idx = content.find(f'"id":"{qid}"')
    if qid_idx == -1:
        print(f"  {qid}: id not found!")
        return content
    # Find the field after qid_idx
    field_idx = content.find(f'"{field}":', qid_idx)
    next_id_idx = content.find('"id":', qid_idx + 10)
    if field_idx == -1 or (next_id_idx != -1 and field_idx > next_id_idx):
        print(f"  {qid}/{field}: field not found!")
        return content
    # Find the opening quote of the value
    colon_idx = content.index(':', field_idx)
    val_start = content.index('"', colon_idx) + 1
    # Find closing quote (skip escaped quotes)
    pos = val_start
    while pos < len(content):
        c = content[pos]
        if c == '\\':
            pos += 2
            continue
        if c == '"':
            break
        pos += 1
    val_end = pos
    old_val = content[val_start:val_end]
    content = content[:val_start] + new_value + content[val_end:]
    print(f"  {qid}/{field}: replaced ({len(old_val)} -> {len(new_value)} chars)")
    return content

changes = []

# ── BRAIN-102: Remove "pretectal nuclei" from explanation ────────────────────
# Just do a simple string replace in the explanation
old_102_phrase = "the superior colliculus and pretectal nuclei that control vertical gaze and pupillary light responses"
new_102_phrase = "the dorsal midbrain structures that coordinate vertical gaze and pupillary light responses"
if old_102_phrase in content:
    content = content.replace(old_102_phrase, new_102_phrase)
    print("BRAIN-102/explanation: phrase replaced OK")
else:
    print("BRAIN-102/explanation: phrase not found!")

# ── BRAIN-075: Full rewrite ───────────────────────────────────────────────────
new_075_q = (
    "A 58-year-old woman suffers bilateral posterior cerebral artery strokes affecting both "
    "occipital lobes. She reports complete loss of vision, yet insists to nursing staff that her "
    "eyesight is \\u2018perfectly fine.\\u2019 She collides with furniture while walking and "
    "confabulates visual experiences when questioned, denying any blindness. Bilateral damage to "
    "which region best explains both the visual loss and the denial of blindness?"
)
new_075_exp = (
    "Bilateral destruction of the primary visual cortex (occipital lobes) causes cortical blindness "
    "\\u2014 complete loss of conscious vision despite structurally intact eyes and optic nerves. "
    "Anton\\u2019s syndrome is the striking variant in which the patient denies being blind and "
    "confabulates visual experiences, because the cortical regions responsible for both visual "
    "processing and metacognitive awareness of deficit are simultaneously destroyed. Unilateral "
    "occipital damage produces a contralateral homonymous hemianopia without total blindness. The "
    "parietal lobe mediates spatial attention and neglect; the temporal lobe mediates object "
    "recognition \\u2014 bilateral damage to either does not produce blindness with denial."
)
content = replace_field(content, "BRAIN-075", "question", new_075_q)
content = replace_field(content, "BRAIN-075", "explanation", new_075_exp)

# ── BRAIN-108: Rewrite rat microinjection → human clinical ───────────────────
new_108_q = (
    "A 26-year-old man recovering from cocaine dependence reports profound anhedonia during "
    "abstinence \\u2014 he no longer experiences pleasure from food, music, or socializing that he "
    "previously enjoyed. PET imaging shows blunted dopamine release in a subcortical ventral "
    "striatal structure during reward anticipation tasks. This same region shows peak dopamine "
    "activation during acute cocaine intoxication in healthy controls. Which structure\\u2019s "
    "functional impairment most directly underlies his post-withdrawal anhedonia?"
)
new_108_exp = (
    "The nucleus accumbens (ventral striatum) is the primary terminal of the mesolimbic dopamine "
    "pathway and serves as the reward-computation hub. Repeated cocaine use depletes dopamine "
    "receptor sensitivity here, producing post-withdrawal anhedonia \\u2014 inability to experience "
    "pleasure from natural rewards. The VTA is the origin of mesolimbic dopamine projections, not "
    "the terminal reward-computation site. The caudate (dorsal striatum) drives habitual motor "
    "sequences rather than hedonic reward. The amygdala modulates emotional salience but the "
    "specific anticipatory reward deficit localizes to the nucleus accumbens."
)
content = replace_field(content, "BRAIN-108", "question", new_108_q)
content = replace_field(content, "BRAIN-108", "explanation", new_108_exp)

# ── BRAIN-114: Rewrite optogenetic rodent → conceptual clinical ──────────────
new_114_q = (
    "A psychopharmacologist explains that one dopaminergic pathway originating in the midbrain "
    "projects specifically to the prefrontal cortex and anterior cingulate, modulating working "
    "memory and mood. A separate pathway from a nearby midbrain structure projects primarily to "
    "the caudate and putamen, controlling motor initiation. In schizophrenia, the prefrontal "
    "pathway is hypoactive (producing negative symptoms and cognitive deficits) while the limbic "
    "pathway is hyperactive (producing positive symptoms). Which midbrain structure is the origin "
    "of the prefrontal dopamine projection implicated in cognitive symptoms?"
)
new_114_exp = (
    "The VTA (ventral tegmental area) gives rise to both the mesocortical pathway (projecting to "
    "PFC and anterior cingulate, mediating cognition, working memory, and mood) and the mesolimbic "
    "pathway (projecting to the nucleus accumbens, mediating reward and motivation). In "
    "schizophrenia, mesocortical hypoactivity underlies negative and cognitive symptoms, while "
    "mesolimbic hyperactivity underlies positive symptoms like hallucinations and delusions. The "
    "substantia nigra projects via the nigrostriatal pathway to the dorsal striatum (caudate and "
    "putamen), controlling motor function \\u2014 its degeneration causes Parkinson\\u2019s disease, "
    "not cognitive-affective symptoms."
)
content = replace_field(content, "BRAIN-114", "question", new_114_q)
content = replace_field(content, "BRAIN-114", "explanation", new_114_exp)

# ── BRAIN-070: Simplify from colloid-cyst to fornix TBI ──────────────────────
new_070_q = (
    "A 35-year-old man sustains a traumatic brain injury that damages the fiber bundle connecting "
    "his hippocampus to the mammillary bodies. Post-injury he is fully alert, speaks clearly, and "
    "scores in the average range on IQ testing. However, he cannot remember what he ate for "
    "breakfast, forgets appointments made hours earlier, and is unable to form any new long-term "
    "memories. Remote memories from before the injury are largely intact. Which structure\\u2019s "
    "functional disconnection best explains this selective anterograde amnesia?"
)
new_070_exp = (
    "The fornix carries hippocampal output to the mammillary bodies and thalamus (key nodes of "
    "the Papez circuit). Damage to the fornix functionally disconnects the hippocampus from its "
    "diencephalic relays, producing anterograde amnesia nearly identical to direct hippocampal "
    "damage \\u2014 new declarative memories cannot be consolidated because hippocampal signals "
    "cannot reach their downstream targets. IQ and procedural memory are spared (as in H.M.\\u2019s "
    "case) because these depend on different neural systems. The thalamus and hypothalamus are "
    "downstream relays in the Papez circuit; the thalamic variant produces Korsakoff syndrome, but "
    "here the primary locus of disconnection is the hippocampus itself."
)
content = replace_field(content, "BRAIN-070", "question", new_070_q)
content = replace_field(content, "BRAIN-070", "explanation", new_070_exp)

with open(BRAIN_DATA_JS, "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone. All changes saved to brain_data.js")
