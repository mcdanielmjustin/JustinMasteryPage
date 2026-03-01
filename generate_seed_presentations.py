"""
generate_seed_presentations.py

Writes hand-crafted seed encounters for all 9 domains so the Patient Encounter
module is fully testable without an API key.

Each domain file gets 2 clinically accurate encounters covering distinct
subdomains, difficulty levels 2 and 3.

Usage:
    python generate_seed_presentations.py
"""

import json, pathlib
from datetime import datetime, timezone

DATA = pathlib.Path("data")
DATA.mkdir(exist_ok=True)

TS = "2026-03-01T00:00:00Z"


# ─── PTHE — Psychotherapy Models, Interventions & Prevention ─────────────────

PTHE = {
    "domain_code": "PTHE",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-PTHE-0001",
            "domain_code": "PTHE",
            "subdomain": "Cognitive-Behavioral Therapy",
            "difficulty_level": 2,
            "encounter": {
                "setting": "Outpatient CBT clinic — first treatment session",
                "referral_context": "Referred by PCP after 6 months of panic attacks. Full cardiac and thyroid workup negative.",
                "patient": {
                    "label": "Adult Male, 34",
                    "appearance_tags": ["restless movement", "shallow breathing", "hypervigilant scanning"],
                    "initial_avatar_state": "anxious"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "These panic attacks are destroying my life. I had to leave work twice last week. I thought I was having a heart attack — my heart was pounding, I couldn't breathe. Now I'm scared to go anywhere crowded in case it happens again.",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["panic attacks", "agoraphobic avoidance", "health anxiety"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Primary concern", "value": "Recurrent panic attacks with avoidance of public spaces"},
                            {"category": "Chief Complaint", "label": "Duration", "value": "6 months; escalating frequency and severity"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History of Present Illness",
                        "dialogue": "It starts with this sense of doom, then my heart races, I sweat, my hands tingle. Peaks in maybe 10 minutes. Afterward I'm exhausted. Between attacks I'm constantly worried the next one is coming. I've stopped taking the subway, stopped going to malls. My wife is getting frustrated.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["anticipatory anxiety", "physical symptoms", "safety behaviors", "functional impairment"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Attack characteristics", "value": "Palpitations, diaphoresis, paresthesias, sense of impending doom; peaks ~10 min"},
                            {"category": "History of Present Illness", "label": "Interictal anxiety", "value": "Persistent anticipatory anxiety between attacks"},
                            {"category": "History of Present Illness", "label": "Avoidance", "value": "Subway, malls, crowded venues — progressive restriction over 6 months"},
                            {"category": "History of Present Illness", "label": "Functional impact", "value": "Missed 2 work days last week; marital tension"}
                        ],
                        "clinician_prompt": "Can you walk me through what happens during a typical attack and how you cope afterward?"
                    },
                    {
                        "phase_id": "cognitive_assessment",
                        "phase_label": "Cognitive Assessment",
                        "dialogue": "When my heart races I think 'this is it — I'm going to die or lose control.' I know logically the doctors said it's not my heart. But in the moment I completely believe it. Afterward I feel stupid for believing it, but the next attack comes and I believe it all over again.",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["catastrophic cognitions", "poor in-vivo insight", "metacognitive awareness"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Thought content", "value": "Catastrophic appraisals during panic: 'I am dying / losing control / going crazy'"},
                            {"category": "Mental Status Examination", "label": "Insight", "value": "Good inter-episode insight; absent during acute panic state — dual-level belief"},
                            {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Anxious mood; congruent affect; no depressive features"}
                        ],
                        "clinician_prompt": "What thoughts go through your mind during the worst moment of an attack?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "treatment_planning",
                    "prompt": "This patient has Panic Disorder with agoraphobic avoidance. Which CBT component is MOST critical for long-term recovery and must not be omitted?",
                    "options": {
                        "A": "Relaxation training and diaphragmatic breathing to manage somatic symptoms",
                        "B": "Interoceptive exposure and in vivo situational exposure to avoided contexts",
                        "C": "Cognitive restructuring of catastrophic beliefs without behavioral exposure",
                        "D": "Psychoeducation about the fight-or-flight response only"
                    },
                    "correct_answer": "B",
                    "explanation": "The gold standard for Panic Disorder is CBT with exposure — specifically interoceptive exposure (deliberately inducing feared sensations) and in vivo situational exposure (confronting avoided contexts). Without behavioral exposure, avoidance is maintained, perpetuating the disorder. Cognitive restructuring and psychoeducation are valuable adjuncts but insufficient alone. Relaxation strategies can become safety behaviors that suppress extinction learning if used as escape.",
                    "distractor_rationale": {
                        "A": "Breathing techniques can inadvertently function as safety behaviors that prevent extinction learning and maintain avoidance if used as coping escapes during exposure.",
                        "C": "Cognitive restructuring alone has weaker evidence than combined CBT. Avoidance behavior maintains the anxiety cycle regardless of cognitive change.",
                        "D": "Psychoeducation is a necessary starting point but produces minimal symptom reduction when used in isolation without active exposure components."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "The patient has good inter-episode insight but loses it entirely during panic. What is the best CBT strategy to update his 'hot' (in-the-moment) belief that panic causes death?",
                    "options": {
                        "A": "Grounding techniques to restore reality contact during dissociative states",
                        "B": "Behavioral experiments — induce panic sensations and test specific predictions",
                        "C": "Purely verbal cognitive restructuring during calm, non-aroused states",
                        "D": "Bibliotherapy about the physiology of panic before any exposure work"
                    },
                    "correct_answer": "B",
                    "explanation": "The patient shows 'dual representation' — intellectually accepting medical reassurance but emotionally believing catastrophic thoughts during panic. In CBT, this is addressed through behavioral experiments: deliberately inducing panic-like sensations (interoceptive exposure) while testing specific predictions (e.g., 'I will have a heart attack') in a controlled setting. Repeated disconfirmation during an aroused state updates the emotional 'hot' belief, not just the intellectual 'cold' belief.",
                    "distractor_rationale": {
                        "A": "Grounding targets depersonalization/derealization — a dissociative experience not described here. The issue is catastrophic appraisal, not reality contact.",
                        "C": "Verbal restructuring in calm states only updates 'cold' beliefs accessible when not anxious. Beliefs during panic are encoded in a different arousal state and require exposure-based updating.",
                        "D": "Bibliotherapy builds conceptual understanding but does not update in-the-moment emotional beliefs. Active behavioral work is required for exposure learning."
                    }
                }
            ]
        },
        {
            "id": "CP-PTHE-0002",
            "domain_code": "PTHE",
            "subdomain": "Dialectical Behavior Therapy",
            "difficulty_level": 3,
            "encounter": {
                "setting": "Intensive outpatient program (IOP) — weekly individual DBT session",
                "referral_context": "Enrolled in DBT IOP after discharge from inpatient unit for superficial self-harm. Diagnosis: Borderline Personality Disorder.",
                "patient": {
                    "label": "Young Adult Female, 26",
                    "appearance_tags": ["visible self-harm scars on forearms", "intense eye contact", "rapid mood shifts"],
                    "initial_avatar_state": "agitated"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "Last week was a disaster. My roommate said one thing and I went from fine to rage in about 30 seconds. I scratched myself. It wasn't bad. I didn't want to die.",
                        "avatar_emotion": "agitated",
                        "behavioral_tags": ["emotional dysregulation", "self-harm", "interpersonal sensitivity", "impulsivity"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Presenting crisis", "value": "Superficial self-harm (scratching) following interpersonal conflict with roommate"},
                            {"category": "Chief Complaint", "label": "Intent", "value": "Denies suicidal intent; self-harm functioned as affect regulation"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "skills_review",
                        "phase_label": "DBT Skills Review",
                        "dialogue": "I know what I was supposed to do. TIPP — change body temperature. I put ice on my wrist for like 20 seconds and then gave up. In the moment, scratching felt like it would work faster. And it did. Now I feel disgusted with myself.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["skills knowledge without implementation", "shame cycle", "short-term relief vs. long-term harm"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Crisis skills attempted", "value": "Brief TIPP attempt (ice ~20 sec) — abandoned before effect; self-harm followed"},
                            {"category": "History of Present Illness", "label": "Contingency", "value": "Self-harm provided rapid affect regulation; followed by shame and disgust"},
                            {"category": "Mental Status Examination", "label": "Affect", "value": "Labile; rapid shame-to-anger oscillation during session"}
                        ],
                        "clinician_prompt": "Walk me through what happened — from the moment your roommate said that to when you scratched."
                    },
                    {
                        "phase_id": "interpersonal",
                        "phase_label": "Interpersonal Context",
                        "dialogue": "She said I was 'too sensitive' and I immediately thought — she hates me, she wants me to leave, everyone thinks I'm too much. And then I wanted to hurt myself to make her feel bad, and also to feel better. I know that's contradictory.",
                        "avatar_emotion": "tearful",
                        "behavioral_tags": ["splitting", "mind-reading", "interpersonal function of self-harm", "emerging insight"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Thought content", "value": "Catastrophic interpersonal interpretation — 'she hates me'; mind-reading"},
                            {"category": "Mental Status Examination", "label": "Insight", "value": "Emerging — patient identifies contradictory functions of self-harm; limited in-moment"},
                            {"category": "Psychosocial History", "label": "Interpersonal pattern", "value": "Intense unstable relationships; hypersensitivity to rejection; fear of abandonment"}
                        ],
                        "clinician_prompt": "What did that thought — 'she wants me to leave' — feel like in your body?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "treatment_planning",
                    "prompt": "In the DBT hierarchy of treatment targets, which behavior takes priority in the next session given this week's events?",
                    "options": {
                        "A": "Therapy-interfering behaviors — her resistance to fully using skills",
                        "B": "Quality-of-life behaviors — addressing the roommate conflict with DEAR MAN",
                        "C": "Life-threatening behaviors — completing a chain analysis of the self-harm",
                        "D": "Skill building — reteaching the full TIPP skill with correct duration"
                    },
                    "correct_answer": "C",
                    "explanation": "DBT organizes treatment targets in a strict hierarchy: (1) Life-threatening behaviors — any suicidal or self-harm behaviors; (2) Therapy-interfering behaviors; (3) Quality-of-life behaviors; (4) Skill acquisition. Despite the patient's low lethality self-harm, it is a Tier 1 target and must be addressed before other targets. The chain analysis — examining antecedents, links, and consequences — is the primary tool for identifying and interrupting the self-harm pathway.",
                    "distractor_rationale": {
                        "A": "Therapy-interfering behaviors (Tier 2) are important, but the DBT hierarchy places any life-threatening behavior at Tier 1, which must be addressed first regardless of lethality level.",
                        "B": "Quality-of-life issues (Tier 3) such as interpersonal skills practice are addressed only after Tier 1 and 2 targets. Bypassing the hierarchy undermines the DBT model.",
                        "D": "Skill building is essential but cannot substitute for chain analysis of the self-harm behavior. The chain analysis identifies exactly where skills failed and where to insert new solutions."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "The patient abandoned TIPP after 20 seconds because self-harm 'worked faster.' Which DBT principle explains why brief skill use is insufficient, and why the skill must be sustained?",
                    "options": {
                        "A": "Radical acceptance — the patient must accept the urge before acting on it",
                        "B": "Opposite action — she must act contrary to the urge's behavioral impulse",
                        "C": "Urge surfing — emotional urges peak and naturally decrease if not acted upon",
                        "D": "Wise mind — she must integrate emotional and rational thinking before responding"
                    },
                    "correct_answer": "C",
                    "explanation": "Urge surfing is the DBT principle that emotional urges and subjective distress follow a natural arc — they intensify, peak, then decrease on their own without action if the person does not feed them. Twenty seconds of TIPP is insufficient because the emotional peak has not passed. The therapist should help the patient understand that distress tolerance skills must be sustained through the urge peak (typically 15–30 minutes). Self-harm 'working faster' means the urge had not yet peaked, not that the skill was ineffective.",
                    "distractor_rationale": {
                        "A": "Radical acceptance addresses suffering that comes from resisting painful reality — it does not explain the temporal arc of urge intensity or why skill duration matters.",
                        "B": "Opposite action is an emotion regulation strategy (acting counter to the emotion's action urge) that is relevant here, but it doesn't explain the neurobiological/temporal reason why skills must be sustained.",
                        "D": "Wise mind is a core dialectical concept balancing emotion and reason — foundational to DBT but does not address the dynamics of urge attenuation over time."
                    }
                }
            ]
        }
    ]
}


# ─── BPSY — Biopsychology ────────────────────────────────────────────────────

BPSY = {
    "domain_code": "BPSY",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-BPSY-0001",
            "domain_code": "BPSY",
            "subdomain": "Neurotransmitter Systems",
            "difficulty_level": 2,
            "encounter": {
                "setting": "Neurology-psychiatry consultation clinic",
                "referral_context": "Parkinson's disease patient referred to psychology after new-onset visual hallucinations following initiation of pramipexole (dopamine agonist).",
                "patient": {
                    "label": "Adult Male, 64",
                    "appearance_tags": ["resting tremor", "masked facies", "bradykinesia", "shuffling gait"],
                    "initial_avatar_state": "confused"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "My hands shake less with this new medicine but now I'm seeing things. Last night I saw people in my bedroom that weren't there. My wife thinks I'm losing my mind. But I feel mentally sharp. Is this the medication?",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["visual hallucinations", "insight preserved", "medication side effect concern"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Primary concern", "value": "New-onset visual hallucinations following pramipexole initiation"},
                            {"category": "Chief Complaint", "label": "Motor status", "value": "Tremor improved since starting dopamine agonist"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "Medication and Symptom History",
                        "dialogue": "The neurologist started me on pramipexole three weeks ago. The hallucinations began a week later. I know they aren't real — I can tell it's not a real person. But it's frightening at night. I haven't had confusion, memory problems, or any of that.",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["good insight into hallucinations", "temporal link to medication", "no cognitive decline"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Medication timeline", "value": "Pramipexole started 3 weeks ago; hallucinations began ~1 week post-initiation"},
                            {"category": "History of Present Illness", "label": "Hallucination character", "value": "Visual — people/figures; non-threatening; patient recognizes as unreal (good insight)"},
                            {"category": "History of Present Illness", "label": "Cognition", "value": "Self-reported and collateral: no memory decline, no confusion; MoCA pending"}
                        ],
                        "clinician_prompt": "Can you describe what you see and how long these episodes last?"
                    },
                    {
                        "phase_id": "neuropsych",
                        "phase_label": "Neuropsychological Context",
                        "dialogue": "I've had Parkinson's for four years. I know about the dopamine. But I don't understand why fixing my movement is causing me to see things. I thought dopamine was a good thing.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["treatment dilemma", "neurobiological confusion", "good insight", "teachable moment"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "PD duration", "value": "4 years; previously managed with levodopa/carbidopa"},
                            {"category": "Collateral / Context", "label": "Pathway context", "value": "Nigrostriatal pathway: dopamine deficit → motor symptoms; Mesolimbic pathway: dopamine excess → psychosis"},
                            {"category": "Labs / Observations", "label": "MoCA", "value": "Pending — to screen for Parkinson's disease dementia (PDD) vs. medication-induced psychosis"}
                        ],
                        "clinician_prompt": "Can you tell me what your neurologist explained about how this medication works?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "dsm_criteria",
                    "prompt": "Why do dopamine agonists like pramipexole cause psychotic symptoms in some Parkinson's patients, even while improving motor function?",
                    "options": {
                        "A": "Dopamine agonists are non-selective — they enhance dopamine in both the nigrostriatal and mesolimbic pathways, and mesolimbic excess causes psychosis",
                        "B": "Dopamine agonists cross the blood-brain barrier and cause serotonin depletion, which triggers hallucinations",
                        "C": "Motor improvement releases cognitive resources previously used for movement, paradoxically causing psychiatric symptoms",
                        "D": "Dopamine agonists activate glutamate receptors in the prefrontal cortex, producing visual hallucinations"
                    },
                    "correct_answer": "A",
                    "explanation": "Dopamine agonists are not pathway-selective. The nigrostriatal pathway (substantia nigra → striatum) is depleted in Parkinson's, causing motor symptoms; dopaminergic stimulation of this pathway improves movement. However, the same drugs also stimulate the mesolimbic pathway (VTA → nucleus accumbens/limbic system), where dopamine excess is the leading neurochemical hypothesis for psychosis. This creates a pharmacological dilemma: treating motor symptoms risks inducing psychiatric side effects via mesolimbic overdrive.",
                    "distractor_rationale": {
                        "B": "Serotonin depletion is not the mechanism — pramipexole acts primarily at D2/D3 dopamine receptors, not on serotonergic systems.",
                        "C": "No evidence supports a 'cognitive resource redistribution' mechanism. Hallucinations are a direct neurochemical effect, not an indirect consequence of motor improvement.",
                        "D": "Glutamate receptor activation is not the primary mechanism of dopamine agonist side effects. The NMDA/glutamate hypothesis is associated with ketamine/PCP-induced psychosis, not dopamine agonists."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "treatment_planning",
                    "prompt": "Which antipsychotic is safest to use if pharmacological treatment of hallucinations becomes necessary in this Parkinson's patient?",
                    "options": {
                        "A": "Haloperidol — high-potency D2 blocker with robust antipsychotic evidence",
                        "B": "Risperidone — atypical antipsychotic with better EPS profile than typicals",
                        "C": "Quetiapine or clozapine — low D2 affinity minimizes worsening of motor symptoms",
                        "D": "Aripiprazole — partial D2 agonism makes it ideal for dopaminergic conditions"
                    },
                    "correct_answer": "C",
                    "explanation": "Most antipsychotics work by blocking D2 receptors. In Parkinson's patients, D2 blockade in the nigrostriatal pathway worsens motor symptoms (the same pathway the dopamine agonist is trying to support). Quetiapine and clozapine have very low D2 receptor affinity, making them far less likely to exacerbate parkinsonism while still reducing mesolimbic dopamine excess. Clozapine has the strongest evidence for PD psychosis; quetiapine is often used first due to easier monitoring. Typical antipsychotics are contraindicated.",
                    "distractor_rationale": {
                        "A": "Haloperidol is a high-potency D2 blocker — it would dramatically worsen Parkinson's motor symptoms by blocking the very pathway that needs dopaminergic support.",
                        "B": "Risperidone has intermediate D2 affinity and clinically worsens parkinsonism in PD patients — it is considered unsafe for this population.",
                        "D": "Aripiprazole's partial D2 agonism theoretically sounds appealing, but clinical evidence shows it can destabilize motor symptoms in PD; it is generally avoided in this population."
                    }
                }
            ]
        },
        {
            "id": "CP-BPSY-0002",
            "domain_code": "BPSY",
            "subdomain": "Sleep Physiology",
            "difficulty_level": 3,
            "encounter": {
                "setting": "Behavioral sleep medicine clinic — initial consultation",
                "referral_context": "Referred by internist for chronic insomnia unresponsive to sleep hygiene education. Patient declined sleep medication. Requesting non-pharmacological approaches.",
                "patient": {
                    "label": "Adult Female, 47",
                    "appearance_tags": ["dark circles under eyes", "fatigued appearance", "tense posture"],
                    "initial_avatar_state": "distressed"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "I fall asleep fine — that's never the problem. But I wake up at 3 AM every single night and then I just lie there for two or three hours. My mind races. By the time I fall back asleep it's almost time to get up. I'm exhausted all day.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["sleep maintenance insomnia", "early morning awakening", "rumination", "daytime fatigue"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Insomnia subtype", "value": "Sleep maintenance insomnia with early morning awakening (~3 AM nightly)"},
                            {"category": "Chief Complaint", "label": "Duration", "value": "~14 months; began after job promotion and increased work stress"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History of Present Illness",
                        "dialogue": "Once I'm awake at 3, my mind goes immediately to work problems. Deadlines, emails I forgot to send, what I need to do tomorrow. It's like my brain shifts into work mode. I've tried melatonin — it doesn't help because I'm not having trouble falling asleep. I watch the clock and it makes it worse.",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["rumination", "clock-watching", "cognitive hyperarousal", "compensatory behaviors"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Wake content", "value": "Work-related cognitive hyperarousal; anticipatory planning and problem-solving"},
                            {"category": "History of Present Illness", "label": "Maladaptive behaviors", "value": "Clock-watching; attempted melatonin (ineffective for maintenance insomnia)"},
                            {"category": "History of Present Illness", "label": "Precipitant", "value": "Promotion 14 months ago; increased responsibility and anticipatory anxiety"}
                        ],
                        "clinician_prompt": "What goes through your mind when you wake up at 3 AM?"
                    },
                    {
                        "phase_id": "sleep_architecture",
                        "phase_label": "Sleep Architecture Assessment",
                        "dialogue": "I've never had a sleep study. I don't snore. My partner says I don't stop breathing. The exhaustion is the worst part — I feel like I'm moving through fog all day, but at my 4 PM slump I suddenly feel awake again. Then I'm alert at bedtime, which makes no sense.",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["hyperarousal at bedtime", "afternoon alertness", "circadian disruption", "second wind phenomenon"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Sleep architecture clue", "value": "Wakes at ~3 AM (REM-dominant period); no snoring or apnea symptoms"},
                            {"category": "History of Present Illness", "label": "Circadian pattern", "value": "'Second wind' at 4 PM and bedtime hyperarousal suggest HPA axis/cortisol dysregulation"},
                            {"category": "Labs / Observations", "label": "Polysomnography", "value": "Not indicated (no apnea symptoms); Actigraphy + sleep diary ordered"}
                        ],
                        "clinician_prompt": "Tell me about what time of day you feel most alert versus most exhausted."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "dsm_criteria",
                    "prompt": "This patient wakes at 3 AM with racing thoughts. Which sleep architecture principle explains why stress most commonly causes awakening in the second half of the night?",
                    "options": {
                        "A": "NREM Stage 3 (slow-wave sleep) dominates the second half, and stress hormones preferentially disrupt slow waves",
                        "B": "REM sleep predominates in the second half of the night, and cortisol/stress arousal disrupts REM disproportionately",
                        "C": "The circadian pacemaker reaches its nadir at 3 AM, creating a vulnerability window regardless of stress",
                        "D": "Adenosine clearance is complete by 3 AM, removing the homeostatic sleep drive and causing spontaneous awakening"
                    },
                    "correct_answer": "B",
                    "explanation": "Sleep architecture follows a predictable ultradian pattern across the night. Slow-wave sleep (SWS/Stage N3) dominates the first third of the night (homeostatic recovery), while REM sleep cycles extend and become more dominant in the final third (approximately 4–6 AM). Psychological stress activates the HPA axis, elevating cortisol, which is a potent REM suppressant and arousal activator. Because the 3–5 AM window is REM-dominant, stress hormones preferentially disrupt this stage, causing awakening. This also explains why the patient's 'second wind' emerges in the late afternoon — cortisol follows a diurnal pattern.",
                    "distractor_rationale": {
                        "A": "SWS dominates the first half of the night (first 2–3 cycles), not the second half. Stress-induced cortisol would be more disruptive to the REM-rich second half.",
                        "C": "The circadian temperature nadir (~4 AM) does create a sleep-promoting window, but it does not specifically cause stress-related awakening — it actually promotes sleep continuity.",
                        "D": "Adenosine (homeostatic sleep pressure) builds during waking and dissipates during sleep continuously — it does not clear by 3 AM. Describing adenosine as 'complete' is inaccurate."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "treatment_planning",
                    "prompt": "Which CBT-I (Cognitive Behavioral Therapy for Insomnia) component is most directly targeted at this patient's pattern of clock-watching and bedtime hyperarousal?",
                    "options": {
                        "A": "Sleep restriction therapy — limiting time in bed to consolidate sleep and rebuild sleep drive",
                        "B": "Stimulus control — reassociating the bed/bedroom with sleep rather than wakefulness and arousal",
                        "C": "Sleep hygiene education — eliminating caffeine, alcohol, and irregular sleep schedules",
                        "D": "Relaxation training — progressive muscle relaxation before bed to reduce somatic tension"
                    },
                    "correct_answer": "B",
                    "explanation": "Stimulus control is the CBT-I component most directly targeting conditioned arousal — the process by which the bed and bedroom become associated with wakefulness, worry, and frustration through repeated pairing. Rules include: use the bed only for sleep and sex; get out of bed if unable to sleep within 20 minutes; return only when sleepy; maintain consistent wake times. This breaks the conditioned hyperarousal the patient experiences at bedtime. Clock-watching is directly targeted by removing clocks from view. Stimulus control has the strongest individual component evidence base in CBT-I.",
                    "distractor_rationale": {
                        "A": "Sleep restriction is effective for sleep efficiency but primarily targets homeostatic sleep drive — it reduces time in bed to consolidate sleep and is often uncomfortable initially. It does not primarily target conditioned arousal.",
                        "C": "Sleep hygiene is necessary but not sufficient — it has the weakest evidence of any CBT-I component when used alone and does not address the conditioned arousal maintaining this patient's insomnia.",
                        "D": "Relaxation training addresses somatic arousal (muscle tension, physiological activation) — relevant for some patients, but this patient describes cognitive hyperarousal (racing thoughts) as the primary maintaining factor."
                    }
                }
            ]
        }
    ]
}


# ─── PMET — Psychometrics & Research Methods ────────────────────────────────

PMET = {
    "domain_code": "PMET",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-PMET-0001",
            "domain_code": "PMET",
            "subdomain": "Reliability",
            "difficulty_level": 2,
            "encounter": {
                "setting": "Peer consultation — outpatient assessment practice",
                "referral_context": "Doctoral-level psychologist consulting a colleague about a client whose MMPI-2 profile changed dramatically between two administrations two years apart. Seeking guidance before writing the report.",
                "patient": {
                    "label": "Psychologist (Consultant), Adult Female, 39",
                    "appearance_tags": ["professional attire", "concerned expression", "holding printed reports"],
                    "initial_avatar_state": "confused"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Consultation Question",
                        "dialogue": "I'm confused about something. My client took the MMPI-2 two years ago with her previous therapist. When I re-administered it last month, several scales shifted dramatically — her Depression scale dropped from 78T to 55T. Her previous therapist says her mood is much better. But I'm not sure if I should trust that the change is real or if it's measurement error.",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["test-retest reliability concern", "clinical change vs. measurement error", "consultation seeking"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Consultation focus", "value": "Interpretation of MMPI-2 scale change (T=78 → T=55 on Depression scale over 2 years)"},
                            {"category": "Chief Complaint", "label": "Context", "value": "Client reports significant mood improvement; change confirmed by collateral therapist"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "reliability_context",
                        "phase_label": "Reliability Analysis",
                        "dialogue": "How much would the score need to change before I could say it's a real change and not just the test being inconsistent? I know MMPI-2 is reliable, but I don't know exactly what that means for individual scores in practice.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["standard error of measurement", "reliable change index", "clinical judgment"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Scale shift magnitude", "value": "Depression (Scale 2): T=78 to T=55 — a 23-point decrease over 2 years"},
                            {"category": "History of Present Illness", "label": "MMPI-2 reliability", "value": "Test-retest reliabilities for MMPI-2 clinical scales: r = .67–.92 depending on scale and interval"},
                            {"category": "Labs / Observations", "label": "SEM context", "value": "With r=.80 (typical for Scale 2) and SD=10 (T-score), SEM ≈ 4.5 T-points; 95% CI ≈ ±9 points"}
                        ],
                        "clinician_prompt": "What's your main concern — that the score dropped too much, or that it might not have dropped enough to be meaningful?"
                    },
                    {
                        "phase_id": "validity_context",
                        "phase_label": "Validity and Interpretation",
                        "dialogue": "She had the same L, F, K profile both times — no obvious validity issues. She wasn't faking or exaggerating symptoms. And clinically she really does seem different — more engaged, not crying, back at work. So is a 23-point drop meaningful?",
                        "avatar_emotion": "hopeful",
                        "behavioral_tags": ["validity scale consistency", "convergent validity", "clinical significance"],
                        "chart_reveals": [
                            {"category": "Labs / Observations", "label": "Validity scales", "value": "L/F/K profiles consistent across both administrations — response style stable"},
                            {"category": "Labs / Observations", "label": "Convergent data", "value": "Clinical observation and collateral report consistent with score improvement"},
                            {"category": "Mental Status Examination", "label": "Current presentation", "value": "Engaged, euthymic, employed — consistent with T=55 range (within normal limits)"}
                        ],
                        "clinician_prompt": "Tell me what her validity scales looked like both times."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "assessment_tool",
                    "prompt": "A 23-point T-score drop on MMPI-2 Scale 2 (Depression) occurred over 2 years. The scale's test-retest reliability is r = .80. Using the Reliable Change Index (RCI) framework, how do you determine whether this change is statistically reliable?",
                    "options": {
                        "A": "Any change > 1 standard deviation (10 T-points) is automatically considered reliable",
                        "B": "The RCI compares the obtained score difference to the Standard Error of the Difference (SE_diff); changes exceeding ±1.96 × SE_diff are reliable",
                        "C": "Clinical significance is established if the new score crosses into the normative range, regardless of the magnitude of change",
                        "D": "Test-retest reliability above r = .70 guarantees that any observed change is clinically meaningful"
                    },
                    "correct_answer": "B",
                    "explanation": "The Reliable Change Index (Jacobson & Truax, 1991) determines whether score change exceeds what would be expected by measurement error alone. SE_diff = SD × √(2(1 − r)) = 10 × √(2 × 0.20) = 10 × √0.4 ≈ 6.3. RCI = 23 / 6.3 ≈ 3.65, which far exceeds 1.96 (p < .05). This 23-point change is statistically reliable — it is very unlikely to reflect measurement error. Combined with convergent clinical data (euthymic presentation, employment, collateral report), this represents genuine clinical improvement.",
                    "distractor_rationale": {
                        "A": "Using 1 SD (10 T-points) as the threshold ignores the specific reliability of the scale. A less reliable scale would require a larger change to reach the same confidence level.",
                        "C": "Clinical significance (normative criterion) and statistical reliability (RCI criterion) are separate questions. A score can cross into the normal range via measurement error, or fail to do so despite a genuinely reliable change.",
                        "D": "High reliability reduces — but does not eliminate — measurement error. Even r = .80 produces meaningful error; SEM = SD × √(1 − r) = 10 × √0.20 ≈ 4.5 T-points for individual scores."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "differential_diagnosis",
                    "prompt": "The validity scales (L, F, K) were virtually identical across both administrations. What does this consistency tell you about interpretation of the scale change?",
                    "options": {
                        "A": "Identical validity scales confirm the client answered both times with the same response style — the substantive scale change is not an artifact of differing test-taking attitudes",
                        "B": "Identical validity scales indicate the test was re-administered too soon and the client remembered her previous answers",
                        "C": "L, F, K consistency means the clinical scales cannot have changed meaningfully — changes must reflect administration error",
                        "D": "Validity scale consistency is irrelevant to interpreting change on clinical scales across administrations"
                    },
                    "correct_answer": "A",
                    "explanation": "MMPI-2 validity scales assess the response style and test-taking attitude: L (Lie) detects naive denial; F (Infrequency) detects atypical symptom endorsement or random responding; K (Defensiveness) measures subtle defensiveness. If validity scales are stable across administrations, it confirms that the client approached both tests with the same openness and consistency. This rules out response style as an explanation for the clinical scale change — the Depression scale drop reflects genuine psychological change, not a shift from symptom exaggeration to underreporting.",
                    "distractor_rationale": {
                        "B": "Two years is far beyond the memory contamination window for MMPI-2. Memory effects for specific item responses are negligible over this interval.",
                        "C": "Validity scale stability does not constrain clinical scale variability — clinical scales and validity scales measure independent constructs. Clinical change while validity is stable is the ideal outcome.",
                        "D": "Validity scale data is directly relevant to confidence in clinical scale interpretation across time — it is not irrelevant."
                    }
                }
            ]
        },
        {
            "id": "CP-PMET-0002",
            "domain_code": "PMET",
            "subdomain": "Diagnostic Accuracy and Decision Theory",
            "difficulty_level": 3,
            "encounter": {
                "setting": "School psychology conference — multidisciplinary eligibility meeting",
                "referral_context": "8-year-old referred for Specific Learning Disability evaluation. Teacher reports struggles with reading despite average classroom intelligence. Parents report the child 'reads perfectly at home.'",
                "patient": {
                    "label": "School Psychologist (Presenting), Adult Male, 44",
                    "appearance_tags": ["professional attire", "presenting test protocols", "confident posture"],
                    "initial_avatar_state": "speaking"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Assessment Findings Presentation",
                        "dialogue": "I administered the WISC-V and the WIAT-4 reading subtests. His Full-Scale IQ is 98 — solidly average. But his Basic Reading composite is at the 18th percentile. His phonological processing on the CTOPP-2 is at the 9th percentile. The team is asking whether this meets criteria for SLD in reading.",
                        "avatar_emotion": "speaking",
                        "behavioral_tags": ["cognitive-achievement discrepancy", "processing deficit", "SLD eligibility"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Assessment question", "value": "Does the psychometric profile support an SLD-Reading diagnosis per IDEA 2004 criteria?"},
                            {"category": "Labs / Observations", "label": "WISC-V FSIQ", "value": "98 (45th percentile) — average range"},
                            {"category": "Labs / Observations", "label": "WIAT-4 Basic Reading", "value": "82 (18th percentile) — low average; statistically below FSIQ"},
                            {"category": "Labs / Observations", "label": "CTOPP-2 Phonological Processing", "value": "75 (5th percentile) — well below average; key processing deficit"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "norm_reference",
                        "phase_label": "Normative Interpretation",
                        "dialogue": "A team member is asking: 'The 18th percentile is not that low — why is that a problem?' I want to explain why the combination of scores — not just the absolute reading score — is the key to this evaluation.",
                        "avatar_emotion": "speaking",
                        "behavioral_tags": ["relative vs. absolute deficit", "norm-referenced interpretation", "processing deficit model"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Discrepancy analysis", "value": "FSIQ 98 vs. Reading 82 — 16-point difference; statistically significant (p<.05) and uncommon (<15% of population)"},
                            {"category": "History of Present Illness", "label": "Processing deficit", "value": "Phonological processing deficit (CTOPP-2, 5th %ile) — specific underlying cognitive deficit"},
                            {"category": "Collateral / Context", "label": "Exclusionary criteria review", "value": "No sensory impairment, no limited English proficiency, no inadequate instruction — SLD criteria partially met"}
                        ],
                        "clinician_prompt": "Can you walk the team through why we don't just look at the absolute reading score in isolation?"
                    },
                    {
                        "phase_id": "base_rate",
                        "phase_label": "Base Rate and Decision Analysis",
                        "dialogue": "One parent is worried that the phonological processing test might be flagging a lot of normal kids as having problems. I want to explain sensitivity and specificity — but in plain language for a multidisciplinary team.",
                        "avatar_emotion": "speaking",
                        "behavioral_tags": ["diagnostic accuracy", "base rate sensitivity", "parent psychoeducation", "test interpretation"],
                        "chart_reveals": [
                            {"category": "Labs / Observations", "label": "CTOPP-2 diagnostic accuracy", "value": "Sensitivity ~.80, Specificity ~.85 for detecting phonological processing deficits in SLD"},
                            {"category": "Labs / Observations", "label": "Base rate", "value": "SLD-Reading prevalence ~5–15% school-age population; positive predictive value context dependent"},
                            {"category": "Labs / Observations", "label": "Decision synthesis", "value": "Convergent data across WIAT-4, CTOPP-2, and teacher/parent observation supports SLD-Reading eligibility"}
                        ],
                        "clinician_prompt": "Can you explain to the team what the phonological processing score means for the probability that this child truly has a reading disability?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "assessment_tool",
                    "prompt": "The CTOPP-2 phonological processing score is at the 5th percentile. With sensitivity = .80 and specificity = .85 for detecting SLD, what happens to the Positive Predictive Value (PPV) if the base rate of SLD in the general school population is 10%?",
                    "options": {
                        "A": "PPV is approximately 37% — the majority of children scoring this low do not have SLD",
                        "B": "PPV is approximately 80% — equal to the test's sensitivity",
                        "C": "PPV is approximately 95% — high specificity ensures most positives are true positives",
                        "D": "PPV cannot be calculated without knowing the student's IQ score"
                    },
                    "correct_answer": "A",
                    "explanation": "Using Bayes' theorem with sensitivity=.80, specificity=.85, base rate=.10: True Positives = .80 × .10 = .08; False Positives = .15 × .90 = .135; PPV = .08 / (.08 + .135) = .08 / .215 ≈ 37%. This means in a general school population, only ~37% of students who score at the 5th percentile on the CTOPP-2 actually have SLD — because the base rate is low. This illustrates why single tests are insufficient and why convergent data (WIAT, teacher observation, exclusionary criteria) is essential. In high-risk referred samples, the base rate is higher and PPV improves substantially.",
                    "distractor_rationale": {
                        "B": "PPV is not equal to sensitivity. PPV depends critically on base rate — the same sensitivity yields very different PPV values at different prevalence rates.",
                        "C": "High specificity reduces false positives, but with a 10% base rate, there are still many more true negatives (normal students) than true positives, so false positives remain substantial.",
                        "D": "IQ score is not required to calculate PPV. Bayes' theorem requires only sensitivity, specificity, and base rate (prior probability)."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "differential_diagnosis",
                    "prompt": "Under IDEA 2004, which model for SLD identification is most consistent with the approach described in this evaluation?",
                    "options": {
                        "A": "Ability-Achievement Discrepancy model — the IQ-achievement gap alone qualifies the student",
                        "B": "Response to Intervention (RTI) — the student must first fail two tiers of evidence-based reading instruction",
                        "C": "Patterns of Strengths and Weaknesses (PSW) — convergent cognitive, achievement, and processing data supporting a specific deficit pattern",
                        "D": "Medical model — a psychiatrist must confirm dyslexia before the team can determine eligibility"
                    },
                    "correct_answer": "C",
                    "explanation": "The evaluation described uses the Patterns of Strengths and Weaknesses (PSW) approach: convergent data shows average general ability (FSIQ=98), below-expectation achievement (WIAT-4 Basic Reading=82), and a specific processing deficit (CTOPP-2 Phonological Processing=75, 5th %ile). PSW identifies a specific cognitive processing weakness that explains the academic deficit, supported by the IQ-achievement discrepancy but not relying on it alone. IDEA 2004 permits — but does not mandate — any specific model; states vary in approach.",
                    "distractor_rationale": {
                        "A": "The simple IQ-achievement discrepancy model has been substantially criticized and is no longer sufficient alone under IDEA 2004. It identifies statistical discrepancy but not processing deficits.",
                        "B": "RTI (now often called MTSS — Multi-Tiered System of Supports) is a valid identification pathway, but this evaluation used comprehensive psychometric testing, not a treatment response framework.",
                        "D": "SLD is an educational classification, not a medical diagnosis. Psychiatrists do not determine school eligibility under IDEA 2004; multidisciplinary educational teams make this determination."
                    }
                }
            ]
        }
    ]
}


# ─── LDEV — Lifespan & Developmental Stages ─────────────────────────────────

LDEV = {
    "domain_code": "LDEV",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-LDEV-0001",
            "domain_code": "LDEV",
            "subdomain": "Adolescence",
            "difficulty_level": 2,
            "encounter": {
                "setting": "High school counseling center — student self-referral",
                "referral_context": "16-year-old referred himself after an argument with parents about college plans. Teacher noted recent withdrawal from extracurriculars.",
                "patient": {
                    "label": "Adolescent Male, 16",
                    "appearance_tags": ["casual attire", "avoids eye contact initially", "fidgeting", "tentatively engaged"],
                    "initial_avatar_state": "guarded"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "My parents have this whole plan for my life — pre-med, their university, same career as my dad. But I don't want that. I want to study art. They say I'm 'going through a phase.' I feel like I don't even know who I am anymore.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["identity exploration", "parental conflict", "emerging autonomy", "identity diffusion risk"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Presenting concern", "value": "Identity conflict — own emerging values vs. parental expectations for career/education"},
                            {"category": "Chief Complaint", "label": "Duration", "value": "Intensified over past 6 months; coincides with junior year college planning discussions"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History and Social Context",
                        "dialogue": "I've always been the 'good kid' — straight A's, sports, debate. But this year I dropped debate and I've been spending more time drawing. I feel guilty. My parents say I'm being selfish. My friends mostly just want to talk about SAT scores.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["role commitment shifting", "peer comparison", "guilt", "internalized expectations"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Previous identity", "value": "High-achieving, compliant — externally defined identity aligned with parental expectations"},
                            {"category": "History of Present Illness", "label": "Emerging identity", "value": "Artistic interests; voluntarily left extracurricular activities aligned with parental plan"},
                            {"category": "Psychosocial History", "label": "Peer context", "value": "Peers focused on academic achievement; limited peer support for emerging interests"}
                        ],
                        "clinician_prompt": "It sounds like something shifted for you this year. What changed?"
                    },
                    {
                        "phase_id": "identity_assessment",
                        "phase_label": "Identity and Mood Assessment",
                        "dialogue": "I'm not depressed — I want to be clear about that. I'm not sad all the time. I just feel... lost. Like everyone else knows who they are and I'm the only one questioning everything. Is that normal?",
                        "avatar_emotion": "hopeful",
                        "behavioral_tags": ["normalization seeking", "identity moratorium", "differentiation from depression", "good insight"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Non-depressed; euthymic; affect full and congruent"},
                            {"category": "Mental Status Examination", "label": "Insight", "value": "Good — accurately distinguishes identity questioning from clinical depression"},
                            {"category": "Mental Status Examination", "label": "Cognitive", "value": "Abstract reasoning emerging; increased capacity for hypothetical thinking about future selves"}
                        ],
                        "clinician_prompt": "Can you help me understand what 'lost' feels like — is it more sadness, more confusion, or something else?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "primary_diagnosis",
                    "prompt": "According to Erikson's psychosocial stages, what is the central developmental conflict this adolescent is navigating, and what is the healthy resolution?",
                    "options": {
                        "A": "Industry vs. Inferiority — he must develop competence through achievement to avoid feelings of inadequacy",
                        "B": "Identity vs. Role Confusion — he must explore and ultimately commit to a coherent sense of self",
                        "C": "Intimacy vs. Isolation — he must form close relationships to avoid social withdrawal",
                        "D": "Autonomy vs. Shame and Doubt — he must develop independence from parental control"
                    },
                    "correct_answer": "B",
                    "explanation": "Erikson's fifth stage — Identity vs. Role Confusion — is the central psychosocial task of adolescence (approximately ages 12–20). The healthy resolution involves active exploration of values, beliefs, and roles (what Marcia called 'moratorium') followed by commitment to a coherent identity. This patient is in moratorium — actively exploring, not yet committed. The absence of clinical depression, the context of normative adolescent development, and the identity-focused content all point to this stage. Healthy resolution does not require adopting parental expectations.",
                    "distractor_rationale": {
                        "A": "Industry vs. Inferiority is the Stage 4 task (approximately ages 6–12/school age). At 16, this stage has already been largely navigated.",
                        "C": "Intimacy vs. Isolation is Erikson's Stage 6 (young adulthood, approximately ages 20–40) — the stage that follows identity formation. Intimacy cannot be achieved without first establishing identity.",
                        "D": "Autonomy vs. Shame and Doubt is Erikson's Stage 2 (approximately ages 18 months–3 years). Toddler-level autonomy development is not the relevant conflict for a 16-year-old."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "Using James Marcia's identity status framework, how would you classify this adolescent's current identity status, and what is the most developmentally supportive counseling approach?",
                    "options": {
                        "A": "Identity foreclosure — validate his current commitments and help him commit to a definitive career path",
                        "B": "Identity diffusion — provide structured guidance and assign definitive life directions to reduce confusion",
                        "C": "Identity moratorium — support ongoing exploration without premature closure; explore values and strengths",
                        "D": "Identity achievement — affirm that he has successfully committed to his identity and needs no further support"
                    },
                    "correct_answer": "C",
                    "explanation": "Identity moratorium describes an adolescent actively exploring alternatives without yet committing — exactly this patient's status (exploring art, questioning pre-med, not yet decided). The developmentally appropriate counseling response is to support the exploration process rather than push toward premature commitment. This includes exploring his values, interests, and strengths; normalizing the process; and helping him communicate his needs to his parents — not resolving the conflict for him. Premature closure (foreclosure) forecloses exploration and often leads to identity crises later.",
                    "distractor_rationale": {
                        "A": "Identity foreclosure describes individuals who have made commitments without exploration — typically adopting parental or societal expectations uncritically. This patient is actively questioning, not foreclosed.",
                        "B": "Identity diffusion involves neither exploration nor commitment, often with apathy or avoidance. This patient is actively engaged in exploration — the opposite of diffusion. Providing directive answers would be inappropriate.",
                        "D": "Identity achievement requires both active exploration AND commitment. This patient is still exploring — commitment has not been made. Labeling him as achieved would be clinically inaccurate."
                    }
                }
            ]
        },
        {
            "id": "CP-LDEV-0002",
            "domain_code": "LDEV",
            "subdomain": "Late Adulthood",
            "difficulty_level": 3,
            "encounter": {
                "setting": "Outpatient neuropsychology clinic — memory concerns evaluation",
                "referral_context": "Referred by PCP for memory concerns. Patient's daughter accompanied him and raised concerns about increasing forgetfulness, but patient minimizes.",
                "patient": {
                    "label": "Older Adult Male, 74",
                    "appearance_tags": ["well-groomed", "hearing aid", "uses notes on phone", "intermittently distracted"],
                    "initial_avatar_state": "guarded"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "I'm here because my daughter insisted. I forget some things — everyone does at my age. Last week I forgot where I put my phone, but it was in my pocket. I drove here by myself. I still read every day, I manage my finances. I think this is all a bit of an overreaction.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["minimization", "preserved functional independence", "good verbal fluency", "defensiveness about cognition"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Patient's stated concern", "value": "Minimizes memory complaints; attributes to normal aging; drove independently to appointment"},
                            {"category": "Chief Complaint", "label": "Collateral concern (daughter)", "value": "Repeats questions within same conversation; missed two medical appointments; left stove on twice"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History of Present Illness",
                        "dialogue": "I retired five years ago. My wife passed two years ago — that was hard. Since then I've been living alone. I cook, I walk every day, I'm in a book club. My daughter says I repeat myself, but she repeats herself too. My doctor said my last blood tests were fine.",
                        "avatar_emotion": "speaking",
                        "behavioral_tags": ["bereavement history", "social engagement maintained", "collateral discrepancy", "social isolation risk"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Functional status", "value": "IADLs largely intact — cooking, finances, driving; two recent errors (stove, appointments)"},
                            {"category": "History of Present Illness", "label": "Psychosocial factors", "value": "Bereavement (spouse, 2 yrs ago); living alone; social engagement maintained (book club, walking)"},
                            {"category": "Labs / Observations", "label": "Medical workup", "value": "Recent labs: CBC, metabolic panel, thyroid — within normal limits"}
                        ],
                        "clinician_prompt": "Can you tell me about your typical day and what kinds of things you've noticed yourself forgetting?"
                    },
                    {
                        "phase_id": "cognitive_screen",
                        "phase_label": "Cognitive Screening",
                        "dialogue": "The date? It's... March. The year is 2026. The words you told me... apple, table, and... I'm not sure about the third. I know that's not great. The clock — does that look right? [draws clock correctly]. Counting backward by 7s... 100, 93, 86, 79...",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["delayed recall deficit", "intact executive function", "preserved orientation", "anxiety about performance"],
                        "chart_reveals": [
                            {"category": "Labs / Observations", "label": "MoCA screening", "value": "Score: 23/30 — below cutoff (≥26); delayed recall deficit (1/5 words); visuospatial intact"},
                            {"category": "Mental Status Examination", "label": "Orientation", "value": "Fully oriented to date, place, person"},
                            {"category": "Mental Status Examination", "label": "Executive function", "value": "Serial 7s intact; clock drawing normal — frontal systems preserved"},
                            {"category": "Mental Status Examination", "label": "Language/Fluency", "value": "Verbal fluency and naming intact; no word-finding pauses"}
                        ],
                        "clinician_prompt": "I'm going to ask you to remember three words. Later I'll ask you to recall them."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "differential_diagnosis",
                    "prompt": "The patient has a MoCA of 23/30, a delayed recall deficit with intact executive function and orientation, and collateral-confirmed functional lapses. What is the most appropriate diagnostic consideration at this stage?",
                    "options": {
                        "A": "Normal age-related cognitive decline — MoCA scores below 26 are typical for adults over 70",
                        "B": "Mild Cognitive Impairment (MCI) — cognitive decline beyond expected aging with preserved overall function",
                        "C": "Major Neurocognitive Disorder (dementia) — the functional lapses confirm significant impairment",
                        "D": "Pseudodementia (depression-related cognitive impairment) — grief is the primary explanation"
                    },
                    "correct_answer": "B",
                    "explanation": "Mild Cognitive Impairment (MCI) is characterized by: (1) subjective and/or collateral-confirmed cognitive complaint; (2) objective evidence of cognitive decline beyond normal aging (MoCA 23, delayed recall deficit); (3) preserved overall independence in daily activities (drives, manages finances, cooks) despite occasional errors. MCI does NOT meet criteria for Major Neurocognitive Disorder (dementia), which requires significant functional impairment. The amnestic MCI profile (delayed recall as primary deficit with intact executive function) carries elevated risk for Alzheimer's conversion. Longitudinal follow-up is required.",
                    "distractor_rationale": {
                        "A": "While some education and age corrections apply to MoCA norms, a score of 23 with collateral-confirmed functional lapses and a clear delayed recall deficit exceeds typical aging. Normal aging produces slowed processing speed, not memory deficits that disrupt daily functioning.",
                        "C": "Major NCD requires that cognitive deficits substantially interfere with independence in everyday activities. This patient retains most complex ADLs (driving, finances, cooking) — the lapses are notable but not yet sufficient for Major NCD.",
                        "D": "Pseudodementia (cognitive effects of depression) is a valid consideration given recent bereavement, and depression workup is warranted. However, the objective cognitive profile (consistent with amnestic MCI) suggests a primary cognitive process, not purely mood-driven impairment."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "treatment_planning",
                    "prompt": "After completing the neuropsychological evaluation, what is the most evidence-based recommendation for this patient's cognitive trajectory and wellbeing?",
                    "options": {
                        "A": "Prescribe a cholinesterase inhibitor immediately given the MCI diagnosis",
                        "B": "Recommend cognitive rehabilitation — intensive cognitive training to reverse memory deficits",
                        "C": "Recommend aerobic exercise, social engagement, cognitive stimulation, and depression screening with annual cognitive monitoring",
                        "D": "Advise the patient to immediately cease driving and managing finances given cognitive decline"
                    },
                    "correct_answer": "C",
                    "explanation": "For MCI, the strongest evidence supports modifiable lifestyle factors: aerobic exercise (reduces AD risk, supports neuroplasticity), maintained social engagement (protective against cognitive decline), and cognitively stimulating activities. Depression screening is essential given recent bereavement — depression exacerbates cognitive complaints and is treatable. Annual neuropsychological monitoring tracks progression and guides future recommendations. Cholinesterase inhibitors (FDA approved for dementia, not MCI) have not shown benefit in MCI. Restrictions on driving/finances are premature given intact current function.",
                    "distractor_rationale": {
                        "A": "Cholinesterase inhibitors (donepezil, rivastigmine) are FDA-approved for Alzheimer's dementia — not MCI. Clinical trials have not demonstrated significant benefit for MCI, and side effects are meaningful.",
                        "B": "Cognitive rehabilitation is an active area of research, but evidence for reversing memory deficits in MCI is insufficient. Current evidence supports prevention and slowing rather than reversal.",
                        "D": "Premature functional restrictions are harmful to independence, wellbeing, and quality of life without clear safety necessity. A focused driving evaluation is appropriate if specific concerns emerge, but blanket restrictions based on MCI diagnosis alone are not supported."
                    }
                }
            ]
        }
    ]
}


# ─── SOCU — Social & Cultural Psychology ─────────────────────────────────────

SOCU = {
    "domain_code": "SOCU",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-SOCU-0001",
            "domain_code": "SOCU",
            "subdomain": "Cultural Competence and Multicultural Practice",
            "difficulty_level": 2,
            "encounter": {
                "setting": "Community mental health center — initial evaluation",
                "referral_context": "Self-referred for depression. Patient immigrated from the Philippines 3 years ago. Primary language: Tagalog/English bilingual. No prior mental health treatment.",
                "patient": {
                    "label": "Adult Female, 34",
                    "appearance_tags": ["formal attire", "deferential posture", "careful word selection", "indirect eye contact"],
                    "initial_avatar_state": "guarded"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "I'm not sure this is the right place for me. In my family, we don't talk about feelings like this. My husband said I should come because I've been tired and not myself. I don't want to seem weak. I don't want to be a burden.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["stigma around help-seeking", "collectivist values", "face concerns", "somatization of distress"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Presenting concern", "value": "Fatigue and low mood; husband-initiated referral; patient ambivalent about treatment"},
                            {"category": "Chief Complaint", "label": "Cultural context", "value": "Filipino immigrant; collectivist values; stigma around mental health treatment; 'not wanting to be a burden'"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History and Cultural Formulation",
                        "dialogue": "I've been tired for maybe a year. I have headaches, my chest feels tight sometimes. I miss home. I video call my mother every day but it's not the same. My children are doing well in school here, and my husband has a good job, so I feel I shouldn't be unhappy. What right do I have to be sad when everything is okay?",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["somatic presentation", "acculturation stress", "acculturative loss", "self-invalidation", "cultural idiom of distress"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Symptom presentation", "value": "Fatigue, headaches, chest tightness — somatic idiom of distress; low mood secondary in patient's framing"},
                            {"category": "History of Present Illness", "label": "Acculturation stressors", "value": "3 years post-immigration; separation from extended family; cultural isolation"},
                            {"category": "Psychosocial History", "label": "Cultural worldview", "value": "Collectivist framing — suffering deemed invalid if family's material needs are met; emotion expression as weakness"}
                        ],
                        "clinician_prompt": "Can you tell me more about the chest tightness and headaches — when do they tend to happen?"
                    },
                    {
                        "phase_id": "cultural_formulation",
                        "phase_label": "Cultural Formulation Exploration",
                        "dialogue": "At home, when someone is sad, we say they have 'tampo' — it's like longing or withdrawal, but it's not sickness. I'm not sure if what I have is tampo or something else. I don't know the right word in English. My husband says I should just be grateful.",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["cultural idiom of distress", "explanatory model exploration", "language gap", "invalidating home environment"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Explanatory model", "value": "Patient uses 'tampo' (Filipino cultural concept: longing/withdrawal) to describe her experience"},
                            {"category": "Mental Status Examination", "label": "Affect", "value": "Restricted; tearful when discussing family separation; no laughing or range observed"},
                            {"category": "Psychosocial History", "label": "Support system", "value": "Husband present but minimizing; extended family support geographically unavailable"}
                        ],
                        "clinician_prompt": "Tell me more about tampo — I want to understand how you think about what you're experiencing."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "cultural_consideration",
                    "prompt": "The patient presents with somatic symptoms as her primary complaint and minimizes psychological distress. What is the most culturally informed interpretation of this presentation?",
                    "options": {
                        "A": "The patient is somatizing — her somatic complaints are defense mechanisms against insight into her depression",
                        "B": "The somatic presentation reflects a culturally mediated idiom of distress; somatization in this context is a legitimate and culturally congruent expression of psychological suffering",
                        "C": "The somatic symptoms indicate a medical condition requiring workup; psychological factors are secondary",
                        "D": "The patient lacks psychological-mindedness and requires psychoeducation about the mind-body connection before therapy can proceed"
                    },
                    "correct_answer": "B",
                    "explanation": "Many collectivist and non-Western cultures express psychological distress primarily through somatic channels — this is not a defense mechanism or sign of limited insight, but a culturally congruent idiom of distress. The DSM-5-TR Cultural Formulation Interview acknowledges that individuals from many backgrounds first experience and communicate distress through physical symptoms (headaches, fatigue, chest tightness) rather than emotional language. Labeling this as 'somatization' (a Western psychoanalytic construct implying defense) imposes an etic framework that may be clinically inaccurate and therapeutically harmful. The appropriate approach is to meet the patient within her explanatory model.",
                    "distractor_rationale": {
                        "A": "Framing somatic presentation as a defense mechanism pathologizes a culturally normative expression of distress. This interpretation imposes a Western psychodynamic framework without cultural foundation.",
                        "C": "While medical workup is reasonable to rule out primary medical causes, dismissing psychological factors given the clear psychosocial context (acculturation, loss, depression symptoms) would be clinically shortsighted.",
                        "D": "Describing the patient as lacking psychological-mindedness is an ethnocentric judgment. She is expressing distress in a culturally coherent way; psychoeducation that invalidates her explanatory model would likely damage the therapeutic alliance."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "The patient uses the cultural concept 'tampo' to describe her experience. What is the most culturally responsive therapeutic approach to this in the first session?",
                    "options": {
                        "A": "Explain that 'tampo' is not a clinical diagnosis and introduce DSM-5-TR depression criteria immediately",
                        "B": "Explore the patient's understanding of 'tampo' as a starting point, building the formulation from her explanatory model",
                        "C": "Avoid discussing 'tampo' to prevent reinforcing non-clinical illness beliefs",
                        "D": "Recommend referral to a Filipino-speaking therapist before proceeding with any treatment"
                    },
                    "correct_answer": "B",
                    "explanation": "Culturally responsive practice begins with the patient's explanatory model — her understanding of the problem, its causes, and its appropriate remedies. The DSM-5-TR Cultural Formulation Interview explicitly recommends exploring what the patient calls her condition, what she thinks caused it, and what kind of help she expects. 'Tampo' provides a culturally grounded entry point for the therapeutic alliance. The clinician can then gently build a shared formulation that respects her framework while introducing additional perspectives. Immediately replacing her explanatory model with DSM language would be invalidating and likely drive disengagement.",
                    "distractor_rationale": {
                        "A": "Immediately replacing the patient's explanatory model with diagnostic criteria ignores the cultural formulation imperative and risks damaging rapport in a patient already ambivalent about treatment.",
                        "C": "Avoiding culturally meaningful concepts closes off the therapeutic relationship. Cultural concepts provide a bridge — not a barrier — to therapeutic work when explored respectfully.",
                        "D": "Language concordance and cultural matching can be valuable but are not always available or necessary. A culturally competent clinician of any background can work effectively with this patient by engaging her explanatory model with curiosity and respect."
                    }
                }
            ]
        },
        {
            "id": "CP-SOCU-0002",
            "domain_code": "SOCU",
            "subdomain": "Immigration and Acculturation",
            "difficulty_level": 3,
            "encounter": {
                "setting": "College counseling center — intake appointment",
                "referral_context": "International student from South Korea, first year in U.S. graduate program. Self-referred for anxiety, academic difficulties, and social isolation.",
                "patient": {
                    "label": "Young Adult Male, 24",
                    "appearance_tags": ["formal business casual attire", "carries notebook", "rigid posture", "minimal spontaneous speech"],
                    "initial_avatar_state": "anxious"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "I have anxiety. In my country I was always top student. Here I feel... average. My English is not perfect. In seminars, I stay quiet because I fear to say wrong thing. My advisor said I must 'speak up more' and I feel ashamed.",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["acculturative stress", "academic identity threat", "language anxiety", "cultural value conflict"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Presenting concern", "value": "Anxiety, social withdrawal, academic self-efficacy loss in U.S. graduate program"},
                            {"category": "Chief Complaint", "label": "Cultural conflict", "value": "Collectivist-trained deference vs. U.S. academic expectation of assertive participation"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "acculturation",
                        "phase_label": "Acculturation and Adjustment",
                        "dialogue": "In Korea, the student listens and respects the professor. To speak without certainty is to show disrespect — to the professor and yourself. Here I feel I am expected to talk even when I do not know. My classmates seem comfortable with being wrong. I am not.",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["cultural value conflict", "collectivist vs. individualist norms", "perfectionism", "honor/shame culture"],
                        "chart_reveals": [
                            {"category": "Psychosocial History", "label": "Cultural value system", "value": "High-context, collectivist background; deference and certainty norms conflict with U.S. individualist academic culture"},
                            {"category": "Psychosocial History", "label": "Acculturation strategy", "value": "Separation orientation — maintains Korean cultural practices; limited integration with U.S. peer culture"},
                            {"category": "History of Present Illness", "label": "Stressors", "value": "Language performance anxiety; academic identity threat; social isolation; unfamiliar norms"}
                        ],
                        "clinician_prompt": "Can you help me understand what speaking up in class means to you, versus what it means here?"
                    },
                    {
                        "phase_id": "social_context",
                        "phase_label": "Social Support and Isolation",
                        "dialogue": "I have no close friends here. I speak to my mother every day in Korean. My Korean friends from home say I should come back — the master's degree is not worth this suffering. But I cannot give up. That would shame my family. I feel caught between two worlds.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["bicultural identity stress", "social isolation", "family obligation", "acculturation gap"],
                        "chart_reveals": [
                            {"category": "Psychosocial History", "label": "Support system", "value": "Primarily family in Korea (remote); no local social network; transnational identity conflict"},
                            {"category": "Mental Status Examination", "label": "Affect", "value": "Anxious; sad; some hopelessness about integration; denies SI"},
                            {"category": "Mental Status Examination", "label": "Insight", "value": "Good — able to articulate cultural conflict cognitively; difficulty with behavioral navigation"}
                        ],
                        "clinician_prompt": "What would it mean for your family if you went home?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "cultural_consideration",
                    "prompt": "Using Berry's acculturation framework, which acculturation strategy does this student appear to be using, and what are its likely psychological consequences?",
                    "options": {
                        "A": "Assimilation — adopting U.S. culture while abandoning Korean identity; typically high psychological stress from identity loss",
                        "B": "Separation — maintaining Korean cultural identity while limiting engagement with U.S. culture; variable outcomes depending on community support",
                        "C": "Marginalization — rejecting both Korean and U.S. cultural identities; associated with the poorest psychological outcomes",
                        "D": "Integration — maintaining Korean identity while also engaging with U.S. culture; associated with best psychological outcomes"
                    },
                    "correct_answer": "B",
                    "explanation": "Berry's acculturation framework describes four strategies along two dimensions: maintaining heritage culture and participating in the host culture. This student is using separation — he actively maintains Korean cultural practices and values (daily contact with mother in Korean, strong Korean peer network, deference norms) while limiting integration into U.S. academic and social culture. Separation can preserve identity and cultural continuity, but in contexts that demand integration (a U.S. graduate program), it creates acculturative stress and social isolation. Psychological wellbeing is better in integration strategies, though separation within a cohesive ethnic community can be protective.",
                    "distractor_rationale": {
                        "A": "Assimilation involves adopting the host culture while abandoning the heritage culture. This student shows no signs of abandoning Korean identity — he is maintaining it strongly.",
                        "C": "Marginalization involves rejecting both cultures — typically associated with identity confusion and the poorest mental health outcomes. This student retains a strong Korean identity.",
                        "D": "Integration combines maintenance of heritage culture with active participation in host culture. This student is not yet engaging with or participating in U.S. cultural practices."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "The student's advisor tells him to 'speak up more' without cultural context. What is the most culturally sensitive therapeutic goal for the initial phase of treatment?",
                    "options": {
                        "A": "Help the student assimilate U.S. academic norms by practicing assertive communication in session and challenging collectivist beliefs as maladaptive",
                        "B": "Validate the cultural conflict, support bicultural competence, and collaboratively develop strategies for navigating academic expectations without wholesale identity abandonment",
                        "C": "Refer the student to a Korean-speaking therapist because the cultural distance between therapist and client is too large",
                        "D": "Focus exclusively on anxiety symptoms using exposure therapy, setting aside cultural factors as secondary"
                    },
                    "correct_answer": "B",
                    "explanation": "Bicultural competence — the ability to navigate multiple cultural contexts while maintaining a coherent identity — is the goal of culturally responsive therapy in acculturation cases. The therapeutic approach should validate the legitimacy of both cultural value systems without privileging one as superior, then collaboratively develop behavioral strategies for specific high-demand contexts (graduate seminars) without requiring the student to abandon his core values. This might include psychoeducation about U.S. academic norms as contextual rather than universal, graduated exposure to participation, and explicit reframing of 'speaking under uncertainty' as contextually appropriate rather than disrespectful.",
                    "distractor_rationale": {
                        "A": "Challenging collectivist beliefs as 'maladaptive' imposes cultural imperialism — these beliefs are adaptive in their original cultural context. The goal is contextual flexibility, not value replacement.",
                        "C": "Language-concordant or culture-matched therapy is a valid preference but not a prerequisite. A culturally competent therapist can work effectively with culturally diverse clients without shared cultural background.",
                        "D": "Cultural factors are not secondary — they are primary to understanding and treating this presentation. Anxiety without cultural context misses the central etiological and maintaining factors."
                    }
                }
            ]
        }
    ]
}


# ─── WDEV — Workforce Development & Leadership ───────────────────────────────

WDEV = {
    "domain_code": "WDEV",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-WDEV-0001",
            "domain_code": "WDEV",
            "subdomain": "Supervision Models and Processes",
            "difficulty_level": 2,
            "encounter": {
                "setting": "Weekly individual supervision — community mental health agency",
                "referral_context": "Doctoral intern (3rd year practicum) presenting a complex clinical case involving a boundary concern. Supervisor is licensed psychologist.",
                "patient": {
                    "label": "Doctoral Intern (Supervisee), Adult Female, 28",
                    "appearance_tags": ["professional attire", "nervous energy", "holding case notes", "avoids direct eye contact initially"],
                    "initial_avatar_state": "anxious"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Supervisory Concern Presentation",
                        "dialogue": "I have something uncomfortable to bring up. My client — the one with borderline PD — friended me on Instagram last week. I didn't accept, but she messaged me and said she 'just wanted to follow my journey.' I didn't respond but now she's brought it up twice in session and she seems really hurt.",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["boundary challenge", "social media contact", "BPD relational dynamics", "supervisee distress"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Presenting scenario", "value": "Client (BPD diagnosis) attempted social media contact via Instagram follow request + direct message"},
                            {"category": "Chief Complaint", "label": "Intern's response", "value": "Did not accept follow; did not respond to message; did not yet address in session"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "clinical_reasoning",
                        "phase_label": "Clinical Reasoning and Formulation",
                        "dialogue": "I didn't know what to do in the moment, so I froze. Part of me wanted to respond to explain, but I thought that might make it worse. I'm worried I've damaged the therapeutic alliance. She keeps saying in session that 'I must think I'm better than her.'",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["countertransference awareness", "therapeutic alliance concern", "paralysis in boundary situation", "insight into avoidance"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Intern's decision-making", "value": "Chose non-response to avoid reinforcing contact; did not yet address limit in session"},
                            {"category": "Mental Status Examination", "label": "Supervisee affect", "value": "Anxious; some shame about handling; motivated for guidance"},
                            {"category": "Collateral / Context", "label": "Client's in-session behavior", "value": "Testing rejection sensitivity theme: 'I must think I'm better than her' — characteristic BPD relational pattern"}
                        ],
                        "clinician_prompt": "What made you freeze — what were you most afraid of getting wrong?"
                    },
                    {
                        "phase_id": "supervision_plan",
                        "phase_label": "Supervision Planning",
                        "dialogue": "I want to address it next session but I don't know how. I don't want to lecture her about boundaries. She'll feel judged and shut down. But I also know I can't just ignore it. Is there a way to talk about it therapeutically, not as a 'rule'?",
                        "avatar_emotion": "hopeful",
                        "behavioral_tags": ["alliance-sensitive intervention planning", "boundary psychoeducation vs. therapeutic use", "self-disclosure decision", "growth in supervision"],
                        "chart_reveals": [
                            {"category": "Psychosocial History", "label": "Supervisee learning goal", "value": "Develop framework for addressing boundary limits therapeutically — without shaming the client"},
                            {"category": "History of Present Illness", "label": "Proposed approach", "value": "Seeking supervisor guidance on therapeutic framing of the Instagram incident in next session"}
                        ],
                        "clinician_prompt": "What do you think the client is really seeking through this contact, in terms of her therapy goals?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "treatment_planning",
                    "prompt": "According to Integrated Developmental Model (IDM) supervision theory, how should the supervisor respond to this intern's anxiety and uncertainty?",
                    "options": {
                        "A": "Provide direct instruction and a scripted response because Stage 1 trainees need high structure and low autonomy",
                        "B": "Step back entirely to preserve the intern's autonomy since over-guidance creates dependency",
                        "C": "Assess the intern's developmental level on this specific competency and calibrate support accordingly — high structure and support for this new situation",
                        "D": "Refer the clinical case to a senior clinician because the intern demonstrated inadequate judgment"
                    },
                    "correct_answer": "C",
                    "explanation": "The Integrated Developmental Model (IDM; Stoltenberg, McNeill, & Delworth) asserts that supervisee development is not uniform across all competencies — an intern may be Stage 3 in some domains and Stage 1 in others. Encountering a boundary violation situation with a personality disorder client is likely a Stage 1 experience for this intern: high anxiety, self-focus, motivation, and limited autonomous confidence. At Stage 1, the supervisor provides high structure (guidance, frameworks, modeling) combined with high support (validation, normalization). As competence in this area grows, structure decreases and autonomy increases.",
                    "distractor_rationale": {
                        "A": "While this intern demonstrates some Stage 1 features on this specific issue, IDM emphasizes competency-specific assessment, not a global Stage 1 label. Scripted responses without rationale also limit learning.",
                        "B": "Withdrawing support entirely is appropriate at Stage 3 (masterful, autonomous) — not for a supervisee presenting with high anxiety and limited framework for this situation.",
                        "D": "Referring the case would be abandoning the supervisory role and denying the intern a crucial learning opportunity. Supervision exists precisely for these situations."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "How should the intern address the Instagram incident therapeutically in the next session with the BPD client?",
                    "options": {
                        "A": "Avoid raising it directly and redirect whenever the client mentions it, to prevent reinforcing the behavior",
                        "B": "Bring it up first, acknowledge the client's wish for connection, and use it therapeutically to explore the relationship and limit-setting themes",
                        "C": "Provide a formal verbal warning that further contact attempts will result in termination",
                        "D": "Accept the follow request to preserve the therapeutic alliance and then discuss appropriate boundaries afterward"
                    },
                    "correct_answer": "B",
                    "explanation": "With BPD clients, limit-setting is most effective when it is therapeutically integrated — not delivered as a rule violation. The intern should proactively bring up the Instagram contact, validate the client's underlying wish for connection ('I noticed you reached out — I want to understand what that was about for you'), set the limit clearly without shaming ('I keep our relationship in the therapy space'), and use the interaction as material for therapy ('This might connect to things you've talked about — feeling close to people and worried about rejection'). This approach maintains alliance, addresses the boundary, and turns a potential rupture into therapeutic work.",
                    "distractor_rationale": {
                        "A": "Avoiding the incident allows it to fester and communicates that the topic is too dangerous to discuss — reinforcing the client's rejection fears and abandoning a valuable therapeutic opportunity.",
                        "C": "A formal warning framing would be experienced as punitive by a BPD client, likely triggering abandonment fears and destabilizing the therapeutic relationship without therapeutic benefit.",
                        "D": "Accepting the follow request would constitute a boundary violation — it blurs professional and personal roles, creates dual relationship concerns, and would significantly complicate treatment."
                    }
                }
            ]
        },
        {
            "id": "CP-WDEV-0002",
            "domain_code": "WDEV",
            "subdomain": "Burnout, Self-Care, and Wellness",
            "difficulty_level": 3,
            "encounter": {
                "setting": "EAP (Employee Assistance Program) consultation — voluntary self-referral",
                "referral_context": "Licensed clinical psychologist, 12 years post-licensure, self-referred. Reports 'feeling like a different person' over the past year.",
                "patient": {
                    "label": "Licensed Psychologist, Adult Male, 44",
                    "appearance_tags": ["disheveled by personal standards", "dark circles", "flat affect", "guarded around emotional content"],
                    "initial_avatar_state": "flat_affect"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "I don't feel anything anymore. About my clients, I mean. I go in, I do the sessions, I write my notes, I go home. I used to care deeply about this work. Now I sit across from someone in crisis and I'm... calculating the time until session ends. I hate that I do that.",
                        "avatar_emotion": "flat_affect",
                        "behavioral_tags": ["depersonalization", "emotional exhaustion", "cynicism", "loss of empathy", "self-disgust"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Primary concern", "value": "Emotional detachment from clinical work; loss of empathy; time-watching in sessions"},
                            {"category": "Chief Complaint", "label": "Duration", "value": "~12 months of progressive disengagement; no acute precipitant identified"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History of Present Illness",
                        "dialogue": "After COVID I took on more clients because the need was so great. My caseload went from 25 to 45. I haven't taken a real vacation in three years. My supervision peer group dissolved. I've been isolated professionally. And personally — my marriage is under strain. My wife says I'm 'emotionally absent.'",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["caseload overload", "professional isolation", "work-life imbalance", "secondary traumatic stress risk"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Work context", "value": "Caseload expanded from 25 to 45 post-COVID; no vacation in 3 years; peer consultation discontinued"},
                            {"category": "History of Present Illness", "label": "Personal impact", "value": "Marital strain — spouse reports emotional absence; social withdrawal"},
                            {"category": "Psychosocial History", "label": "Professional history", "value": "12 years licensed; previously high satisfaction; no prior burnout episodes"}
                        ],
                        "clinician_prompt": "When did you first notice that something felt different in your work?"
                    },
                    {
                        "phase_id": "competence_concern",
                        "phase_label": "Competence and Ethical Concern",
                        "dialogue": "I'm worried about my clients. I'm not providing the same quality of care. I'm more irritable in sessions — I can feel it. Last week I cut off a client mid-sentence. I'm ashamed of that. But I don't know how to stop. I can't just close my practice — people depend on me.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["competence concern", "ethical obligation awareness", "help-seeking ambivalence", "client welfare concern"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Affect", "value": "Flat to distressed; shame-laden; appropriate to content"},
                            {"category": "Mental Status Examination", "label": "Insight", "value": "Excellent — identifies impact on clinical competence; motivated to change"},
                            {"category": "Psychosocial History", "label": "Ethical awareness", "value": "Self-identifies potential APA Ethics Code concern (Principle A: Beneficence — competent care)"}
                        ],
                        "clinician_prompt": "You mentioned worrying about your clients' care. Can you say more about what you've noticed?"
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "primary_diagnosis",
                    "prompt": "Using the Maslach Burnout Inventory (MBI) framework, which burnout dimension does this psychologist's presentation most comprehensively illustrate?",
                    "options": {
                        "A": "Emotional exhaustion only — he reports feeling depleted and unable to give emotionally to his work",
                        "B": "Depersonalization only — his detachment and time-watching indicate cynicism toward clients",
                        "C": "All three MBI dimensions — emotional exhaustion, depersonalization, and reduced personal accomplishment",
                        "D": "Reduced personal accomplishment only — his competence concerns suggest declining self-efficacy"
                    },
                    "correct_answer": "C",
                    "explanation": "The Maslach Burnout Inventory assesses three dimensions: (1) Emotional Exhaustion — feeling emotionally depleted and drained by one's work ('I don't feel anything anymore'); (2) Depersonalization — cynical, callous, or detached responses to recipients of one's service ('calculating the time until session ends,' cutting off clients, reduced empathy); (3) Reduced Personal Accomplishment — feelings of incompetence and low achievement in one's work ('I'm not providing the same quality of care,' shame, loss of prior satisfaction). This clinician demonstrates all three dimensions, indicating full burnout syndrome.",
                    "distractor_rationale": {
                        "A": "Emotional exhaustion alone describes one MBI dimension. This clinician also clearly demonstrates depersonalization and reduced personal accomplishment — all three dimensions are present.",
                        "B": "Depersonalization alone does not capture the full picture. His emotional depletion and explicit competence concerns map onto the other two MBI dimensions.",
                        "D": "Reduced personal accomplishment describes competence concerns and loss of satisfaction. The clinician also demonstrates profound emotional exhaustion (12-month progressive decline, no vacations) and depersonalization (emotional detachment from clients)."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "The psychologist expresses concern about his clinical competence but says he cannot stop seeing clients because 'people depend on him.' Under the APA Ethics Code, what is the most appropriate response?",
                    "options": {
                        "A": "Support his decision to continue working at full capacity while teaching stress management strategies",
                        "B": "Immediately mandate that he cease all clinical practice until burnout is fully resolved",
                        "C": "Acknowledge the ethical tension, explore immediate caseload reduction, and address the 'indispensable' belief as a maintaining factor",
                        "D": "Report him to the state licensing board for practicing outside his current competence"
                    },
                    "correct_answer": "C",
                    "explanation": "APA Ethics Code Principle A (Beneficence and Nonmaleficence) and Standard 2.06 (Personal Problems and Conflicts) require psychologists to recognize when personal difficulties are compromising competent service delivery and to take appropriate action. However, the immediate therapeutic response is not reporting or mandated cessation — it is collaborative ethical exploration. The belief that he is 'indispensable' is a cognitive distortion that maintains the unsafe caseload and reflects a common burnout feature (over-responsibility). The consultation should address: immediate caseload reduction, return to peer supervision/consultation, and possibly personal therapy — while planning thoughtful transitions for client welfare rather than abrupt abandonment.",
                    "distractor_rationale": {
                        "A": "Continuing at full capacity while adding stress management ignores the active ethical concern (compromised competence) and the unsustainable systemic factors. Stress management alone is insufficient.",
                        "B": "Immediate cessation of all clinical practice without a transition plan would constitute abandonment (APA Standard 3.12) of clients who depend on continuity of care. An abrupt stop also fails to address the organizational and cognitive factors driving burnout.",
                        "D": "EAP consultation is a protected voluntary help-seeking resource. Reporting a voluntary self-referral to a licensing board would violate the confidentiality of that consultation and would deter future help-seeking among impaired professionals — producing worse outcomes at a systems level."
                    }
                }
            ]
        }
    ]
}


# ─── CASS — Clinical Assessment & Interpretation ─────────────────────────────

CASS = {
    "domain_code": "CASS",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-CASS-0001",
            "domain_code": "CASS",
            "subdomain": "Intelligence and Cognitive Testing",
            "difficulty_level": 2,
            "encounter": {
                "setting": "School psychology — parent feedback session after psychoeducational evaluation",
                "referral_context": "9-year-old girl evaluated for suspected learning disability. Parents were told she 'tested at the 50th percentile' but are confused because her teacher says she is 'clearly very bright.'",
                "patient": {
                    "label": "Parent (Mother), Adult Female, 38",
                    "appearance_tags": ["professional attire", "holding printed report", "concerned expression", "engaged and inquisitive"],
                    "initial_avatar_state": "confused"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Parent Concern",
                        "dialogue": "I'm confused. The previous psychologist said Emma scored at the 50th percentile on IQ — which sounds average. But her teacher says she's clearly above average. And Emma struggles with reading despite being good at math and science. How can she be average and also struggling?",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["test interpretation confusion", "parent advocacy", "discrepancy concern", "IQ vs. achievement gap"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Parent concern", "value": "Discrepancy between FSIQ (50th %ile) and teacher's perception of above-average ability; concurrent reading struggles"},
                            {"category": "Chief Complaint", "label": "Assessment history", "value": "Prior WISC-V administered 6 months ago; parent never received complete interpretation session"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "test_results",
                        "phase_label": "Test Result Review",
                        "dialogue": "The report shows something called 'VCI' at the 84th percentile, 'VSI' at the 91st percentile, and 'PSI' at the 16th percentile. The Full Scale IQ was 100. Those seem very different to me — how can all these scores average to 100?",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["index score variability", "FSIQ validity concern", "relative strengths and weaknesses", "parent curiosity"],
                        "chart_reveals": [
                            {"category": "Labs / Observations", "label": "WISC-V Verbal Comprehension (VCI)", "value": "114 (84th %ile) — High Average; strong language and verbal reasoning"},
                            {"category": "Labs / Observations", "label": "WISC-V Visual Spatial (VSI)", "value": "118 (88th %ile) — High Average; strong nonverbal and spatial reasoning"},
                            {"category": "Labs / Observations", "label": "WISC-V Processing Speed (PSI)", "value": "82 (12th %ile) — Low; significant relative weakness"},
                            {"category": "Labs / Observations", "label": "WISC-V Full Scale IQ (FSIQ)", "value": "100 (50th %ile) — but high index score variability limits interpretive validity of FSIQ"}
                        ],
                        "clinician_prompt": "Let me show you what the different scores mean — the Full Scale IQ doesn't tell the whole story."
                    },
                    {
                        "phase_id": "reading_connection",
                        "phase_label": "Connecting Assessment to Reading Difficulty",
                        "dialogue": "So she's actually strong in language and visual reasoning, but something about her processing speed is low? Could that be why she reads slowly? She's not slow in thinking — she just takes forever to get her thoughts on paper or to read a full page.",
                        "avatar_emotion": "hopeful",
                        "behavioral_tags": ["connecting psychometric data to behavior", "growing understanding", "parent insight", "processing speed and reading link"],
                        "chart_reveals": [
                            {"category": "Collateral / Context", "label": "Academic observation", "value": "Slow written output and reading rate despite strong verbal and reasoning ability — consistent with PSI deficit"},
                            {"category": "Labs / Observations", "label": "WIAT-4 Reading Rate", "value": "75 (5th %ile) — significantly below FSIQ and VCI; consistent with processing speed weakness"},
                            {"category": "Labs / Observations", "label": "Formulation", "value": "Profile consistent with processing speed weakness as primary deficit underlying reading rate difficulty"}
                        ],
                        "clinician_prompt": "Exactly — that's a very insightful connection. Let me explain why the Full Scale IQ number alone was misleading."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "assessment_tool",
                    "prompt": "Emma's WISC-V shows index scores ranging from 82 to 118. What is the correct interpretation of her Full Scale IQ of 100, given this variability?",
                    "options": {
                        "A": "The FSIQ of 100 is valid because it is the most reliable composite score and should guide all diagnostic and placement decisions",
                        "B": "The FSIQ has limited interpretive validity due to extreme index score variability — the index profile (VCI, VSI, PSI) provides more clinically useful information",
                        "C": "The FSIQ confirms average ability — the index variability is normal and expected in all children",
                        "D": "The FSIQ should be discarded and the highest index score (VSI=118) should be used as the true ability estimate"
                    },
                    "correct_answer": "B",
                    "explanation": "When significant intra-individual variability exists across WISC-V index scores (typically a 1.5 SD / 23-point range is clinically significant), the Full Scale IQ becomes a misleading summary statistic — it averages very different abilities into a single number that does not represent any one cognitive domain accurately. WISC-V interpretation guidelines recommend reporting and interpreting index scores as the primary level of analysis when variability is high, because each index measures a distinct cognitive ability. In Emma's case, the VCI (114) and VSI (118) reflect genuine high-average ability, while the PSI (82) reflects a specific processing deficit — FSIQ of 100 obscures this important diagnostic information.",
                    "distractor_rationale": {
                        "A": "FSIQ reliability is not the issue — the issue is construct validity. A reliable average of unequal abilities is still a misleading representation of cognitive functioning when abilities are discrepant.",
                        "C": "A 36-point range (82 to 118) across index scores represents clinically significant variability. Research shows this level of scatter is uncommon in the normative population and warrants index-level interpretation.",
                        "D": "Selecting the highest score as 'true ability' is not a standardized interpretive approach. The PSW model and other frameworks use the full profile — not a cherry-picked peak."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "differential_diagnosis",
                    "prompt": "Which assessment-based classification best fits Emma's profile: strong VCI/VSI, weak PSI, slow reading rate?",
                    "options": {
                        "A": "Intellectual Disability — FSIQ of 100 is not consistent with this, but the processing speed deficit indicates global limitation",
                        "B": "Gifted with Twice Exceptionality (2e) — high cognitive ability coexisting with a specific learning disability in reading",
                        "C": "ADHD, Predominantly Inattentive — processing speed deficits always indicate attention problems",
                        "D": "Developmental Coordination Disorder — processing speed deficits reflect motor coordination problems"
                    },
                    "correct_answer": "B",
                    "explanation": "Twice exceptionality (2e) describes students with high intellectual ability in some domains who simultaneously demonstrate a specific learning disability or developmental condition. Emma's profile shows genuine cognitive strengths (VCI=114, VSI=118 — above average language and spatial reasoning) alongside a specific processing speed deficit (PSI=82) that undermines reading rate despite strong cognitive resources. This is a classic 2e presentation. The 'average' FSIQ masked her strengths, which explains why the teacher's observations ('clearly bright') and the test results ('50th percentile') seemed contradictory.",
                    "distractor_rationale": {
                        "A": "Intellectual Disability requires FSIQ ≤70 across multiple cognitive domains, adaptive behavior deficits, and onset in the developmental period. Emma's profile shows strong abilities in multiple areas.",
                        "C": "Processing speed deficits are associated with ADHD but are not pathognomonic — they occur in SLD, TBI, anxiety, and 2e profiles. A full attention evaluation would be needed before concluding ADHD.",
                        "D": "Developmental Coordination Disorder involves motor skills — the PSI deficit could have a motor component (written output), but DCD requires a thorough motor evaluation and does not explain the reading rate deficit."
                    }
                }
            ]
        },
        {
            "id": "CP-CASS-0002",
            "domain_code": "CASS",
            "subdomain": "Neuropsychological Assessment",
            "difficulty_level": 3,
            "encounter": {
                "setting": "Rehabilitation neuropsychology clinic — outpatient evaluation",
                "referral_context": "Adult male referred 8 weeks post-mild traumatic brain injury (mTBI) from a motor vehicle accident. Reports persistent cognitive symptoms despite normal CT scan at time of injury.",
                "patient": {
                    "label": "Adult Male, 41",
                    "appearance_tags": ["sunglasses indoors", "fatigue evident", "slow response latency", "self-reports light sensitivity"],
                    "initial_avatar_state": "distressed"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "I can't go back to work. I'm an attorney — I argue cases, I read briefs all day. Since the accident, I can't concentrate for more than 10 minutes. Bright lights give me a migraine. My wife says I'm irritable and I fly off the handle. The ER said the CT was negative. My boss thinks I'm malingering.",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["post-concussion syndrome", "concentration impairment", "photophobia", "irritability", "work disability"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Cognitive symptoms", "value": "Sustained concentration impairment; reading difficulty; 10-minute attention cap"},
                            {"category": "Chief Complaint", "label": "Physical symptoms", "value": "Photophobia, headaches (post-exertional), fatigue"},
                            {"category": "Chief Complaint", "label": "Behavioral changes", "value": "Irritability; emotional lability; behavioral dyscontrol per spouse"},
                            {"category": "Labs / Observations", "label": "Neuroimaging", "value": "CT scan at injury: negative — structural brain injury not detected; does not rule out mTBI"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "history",
                        "phase_label": "History of Present Illness",
                        "dialogue": "I was rear-ended. My head hit the headrest hard. I didn't lose consciousness — at least I don't think so. There was maybe a minute where things were foggy. The paramedics cleared me at the scene. But the next day I had a splitting headache and felt completely off.",
                        "avatar_emotion": "confused",
                        "behavioral_tags": ["brief LOC unclear", "post-traumatic amnesia", "day-after symptom onset", "classic mTBI mechanism"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Injury mechanism", "value": "Rear-end MVA; head contact with headrest; no windshield or airbag impact"},
                            {"category": "History of Present Illness", "label": "Acute presentation", "value": "Brief confusion/foggy period (< 1 min); no confirmed LOC; GCS 15 at scene"},
                            {"category": "History of Present Illness", "label": "Post-acute course", "value": "Symptom onset day 1 post-injury; 8 weeks persistent — meets criteria for Persistent Post-Concussion Symptoms"},
                            {"category": "Psychosocial History", "label": "Pre-morbid", "value": "Attorney; high premorbid functioning; no prior head injury or neuropsychiatric history"}
                        ],
                        "clinician_prompt": "Walk me through what you remember from right before impact to the next morning."
                    },
                    {
                        "phase_id": "validity_consideration",
                        "phase_label": "Symptom Validity and Emotional Factors",
                        "dialogue": "I understand I need to take some memory tests. I want to be clear — I'm not exaggerating. I have everything to gain by going back to work. I have active cases, clients depending on me. I just physically cannot do what I need to do right now.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["secondary gain concern raised by referral source", "patient denies malingering", "high-stakes evaluation", "symptom validity testing needed"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Motivation concerns", "value": "Referral note mentions 'possible malingering'; patient explicitly denies; has active litigant status"},
                            {"category": "Mental Status Examination", "label": "Behavioral observations", "value": "Appropriate frustration; no inconsistency between stated and observed symptoms"},
                            {"category": "Labs / Observations", "label": "SVT plan", "value": "Embedded and standalone symptom validity tests (e.g., TOMM, MSVT) included in battery as standard protocol"}
                        ],
                        "clinician_prompt": "I want to explain that symptom validity testing is a routine part of any neuropsychological evaluation — it actually protects you as a patient."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "assessment_tool",
                    "prompt": "Why is a normal CT scan at time of injury NOT sufficient to rule out mild TBI and its cognitive sequelae?",
                    "options": {
                        "A": "CT scans cannot detect injury if administered within 24 hours of the accident",
                        "B": "CT scans detect gross structural pathology (hemorrhage, fracture) but cannot detect diffuse axonal injury, microhemorrhages, or neurometabolic changes that underlie mTBI symptoms",
                        "C": "The CT scan may have been incorrectly read — a repeat CT with contrast would be definitive",
                        "D": "Normal CT scans confirm that symptoms are functional (psychogenic) rather than neurological"
                    },
                    "correct_answer": "B",
                    "explanation": "mTBI pathophysiology primarily involves diffuse axonal injury (DAI) — stretching and shearing of axonal connections from rotational/acceleration-deceleration forces — and neurometabolic dysfunction (ionic flux, glutamate excitotoxicity, mitochondrial dysfunction). CT scans detect gross structural lesions (hemorrhage, contusion, skull fracture) with high sensitivity but are insensitive to DAI and neurometabolic changes. MRI (particularly susceptibility-weighted imaging, SWI, and diffusion tensor imaging, DTI) is more sensitive, but many mTBI cases have normal structural MRI despite real pathophysiology measurable on functional imaging and neuropsychological testing.",
                    "distractor_rationale": {
                        "A": "CT scan sensitivity is not meaningfully affected by time-of-administration in the acute window. Timing is not the reason for limited sensitivity to mTBI.",
                        "C": "CT with contrast enhances vascular structures — it does not improve detection of diffuse axonal injury or neurometabolic changes. Contrast CT is not the appropriate next imaging step for mTBI.",
                        "D": "A normal CT does not establish a functional (psychogenic) etiology. This conclusion is not neurologically supported and risks dismissing real neurophysiological injury."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "risk_assessment",
                    "prompt": "The referral note suggests malingering. What is the neuropsychologist's most appropriate approach to symptom validity in this evaluation?",
                    "options": {
                        "A": "Skip formal SVT because the patient denies malingering and appears credible",
                        "B": "Include embedded and standalone symptom validity tests as standard protocol; interpret performance in context of the full clinical picture",
                        "C": "Use only the MMPI-2 validity scales as the primary measure of symptom credibility",
                        "D": "Assume malingering given the active litigation status and recommend denial of disability claim"
                    },
                    "correct_answer": "B",
                    "explanation": "Symptom validity testing (SVT) is a professional and ethical standard in neuropsychological evaluations — not a test used only when malingering is suspected. Standalone SVTs (e.g., TOMM, MSVT, WMT) and embedded performance validity indicators (PVTs within standard tests) should be administered routinely in all forensic and high-stakes clinical evaluations. The neuropsychologist then interprets SVT performance in context: below-chance performance suggests non-credible effort; results within normal limits provide evidentiary support for the credibility of other cognitive findings. Active litigation status alone does not establish malingering — base rates of malingering vary widely and require convergent evidence.",
                    "distractor_rationale": {
                        "A": "Clinician impression of credibility is insufficient to replace objective SVT. Credible-appearing patients occasionally show non-credible performance; skeptical-appearing patients often show valid effort. SVT is a scientific safeguard, not a character judgment.",
                        "C": "MMPI-2 validity scales assess self-report personality and symptom endorsement — they are not designed as primary neuropsychological performance validity measures. MMPI-2 can complement SVT but does not substitute for cognitive performance validity testing.",
                        "D": "Assuming malingering based on litigation status is ethically impermissible (APA Standards 9.01, 9.06) and scientifically indefensible. Litigation does not significantly increase base rates of malingering beyond what SVTs are designed to detect."
                    }
                }
            ]
        }
    ]
}


# ─── PETH — Psychopharmacology & Ethics ──────────────────────────────────────

PETH = {
    "domain_code": "PETH",
    "generated_at": TS,
    "encounters": [
        {
            "id": "CP-PETH-0001",
            "domain_code": "PETH",
            "subdomain": "Confidentiality and Privilege",
            "difficulty_level": 2,
            "encounter": {
                "setting": "Outpatient individual therapy — 12th session",
                "referral_context": "Patient has been in therapy for anger management after workplace conflict. No prior safety concerns. Disclosure arises unexpectedly mid-session.",
                "patient": {
                    "label": "Adult Male, 35",
                    "appearance_tags": ["tense jaw", "clenched fists", "raised voice at start", "calms mid-session"],
                    "initial_avatar_state": "agitated"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Session Disclosure",
                        "dialogue": "I can't take it anymore. My supervisor — Jake — he's been making my life hell. He wrote me up for something I didn't do. I've been lying awake thinking about what I want to do to him. I'm not going to sit back and let him destroy my career.",
                        "avatar_emotion": "agitated",
                        "behavioral_tags": ["anger", "grievance", "vague threat language", "rumination", "requires clarification"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Disclosure", "value": "Patient expresses intense anger at named supervisor; vague statement about 'what I want to do to him'"},
                            {"category": "Chief Complaint", "label": "Context", "value": "12 sessions of anger management; no prior safety concerns; current anger triggered by workplace write-up"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "risk_clarification",
                        "phase_label": "Risk Clarification",
                        "dialogue": "What do I mean? I mean I want to punch him in the face. I've imagined it clearly — walking into his office, hitting him. I've never done anything like that. I know I won't. But I want to. I feel like I'm about to explode.",
                        "avatar_emotion": "agitated",
                        "behavioral_tags": ["explicit ideation", "identifiable victim", "clear mental imagery", "no stated plan or intent to act", "emotional venting vs. threat"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Ideation", "value": "Explicit violent ideation — imagines hitting supervisor; imagery is clear and detailed"},
                            {"category": "Mental Status Examination", "label": "Intent", "value": "Explicitly denies intent to act: 'I know I won't' — statement of intent ambiguous; requires structured assessment"},
                            {"category": "Mental Status Examination", "label": "Means", "value": "No mention of weapons; planned confrontation is physical (punch)"}
                        ],
                        "clinician_prompt": "I want to make sure I understand — when you say 'what I want to do,' can you tell me more specifically what you mean?"
                    },
                    {
                        "phase_id": "assessment_context",
                        "phase_label": "Risk and Protective Factor Assessment",
                        "dialogue": "I have a family. I'm not going to throw everything away over this guy. My anger management has actually helped — a year ago I would have already confronted him. I'm calmer than I was. I just needed to say this out loud. But he's really pushed me. If he writes me up again...",
                        "avatar_emotion": "distressed",
                        "behavioral_tags": ["strong protective factors", "treatment engagement", "conditional threat element", "emotional regulation growth"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Protective factors", "value": "Family, job, progress in treatment cited as deterrents; motivated in therapy"},
                            {"category": "Mental Status Examination", "label": "Risk factors", "value": "Conditional threat element ('if he writes me up again'); intense grievance; identifiable victim"},
                            {"category": "Mental Status Examination", "label": "Risk level", "value": "Low-to-moderate — detailed ideation, identifiable victim, conditional language; mitigated by strong protective factors and treatment engagement"}
                        ],
                        "clinician_prompt": "You mentioned your family — tell me more about what keeps you from acting on these thoughts."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "risk_assessment",
                    "prompt": "Under the Tarasoff v. Regents of the University of California (1976) duty-to-protect standard, what conditions must typically be met before a therapist has a legal and ethical obligation to warn or protect a third party?",
                    "options": {
                        "A": "Any expression of anger toward another person, regardless of specificity or intent",
                        "B": "A credible, serious threat of physical harm toward an identifiable victim",
                        "C": "Any disclosure the therapist judges to be more concerning than 50% likely to result in harm",
                        "D": "Passive ideation without intent, if the victim is a public figure or employer"
                    },
                    "correct_answer": "B",
                    "explanation": "Tarasoff established the duty to protect when a therapist determines — or should determine — that a patient presents a serious, credible threat of physical harm to an identifiable third party. Key elements vary by state but typically include: (1) serious threat (not vague or hypothetical); (2) credibility based on clinical assessment (means, intent, plan, history); (3) identifiable victim. In this case, the patient names Jake, expresses explicit violent imagery, and has conditional threat language ('if he writes me up again'), but explicitly denies intent, demonstrates strong protective factors, and reports treatment progress. A thorough risk assessment — not an automatic warning — is the appropriate next step.",
                    "distractor_rationale": {
                        "A": "Any expression of anger does not meet the Tarasoff threshold. Anger expression in therapy is protected therapeutic content. The duty arises from a credible, specific threat — not general hostility.",
                        "C": "There is no '50% likelihood' legal standard. The threshold is 'serious and credible threat' — a professional judgment based on clinical assessment of risk factors, not a probability estimate.",
                        "D": "Public figures or employers as targets do not change the Tarasoff threshold. The identifiable victim element is met, but seriousness and credibility of the threat still require clinical assessment."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "After conducting a structured risk assessment and determining the risk is low-to-moderate with strong protective factors, what is the most clinically appropriate immediate response?",
                    "options": {
                        "A": "Immediately contact Jake (the supervisor) to warn him, given the named target",
                        "B": "Involuntarily hospitalize the patient given any violent ideation toward an identifiable person",
                        "C": "Continue therapy, document the assessment thoroughly, develop a safety plan, and increase session frequency",
                        "D": "Terminate therapy immediately because the patient's workplace is outside the scope of outpatient anger management"
                    },
                    "correct_answer": "C",
                    "explanation": "When risk assessment concludes low-to-moderate risk with strong protective factors, the appropriate clinical response is a stepwise, proportionate intervention: document the risk assessment in detail (clinical reasoning, factors weighed, decision made); develop or revisit a safety plan with the patient (including what he will do if the urge becomes more urgent); consider increasing session frequency during this high-stress period; and monitor for escalation. Immediate warning or hospitalization is not clinically indicated when risk is assessed as manageable with outpatient interventions and the patient explicitly denies intent and identifies strong deterrents.",
                    "distractor_rationale": {
                        "A": "Warning Jake is a Tarasoff duty-to-protect option, but it is not automatically triggered by any violent ideation toward a named person. The clinical assessment determines the proportionality of response. Warning is one option — usually alongside other interventions — when risk is determined to be serious and credible.",
                        "B": "Involuntary hospitalization requires imminent danger that cannot be managed less restrictively. This patient has strong protective factors, explicit denial of intent, and engagement in treatment — the least restrictive effective intervention is appropriate.",
                        "D": "Workplace grievances are directly relevant to anger management treatment goals. Terminating treatment for a patient with active violent ideation would constitute abandonment and remove a critical protective and monitoring resource."
                    }
                }
            ]
        },
        {
            "id": "CP-PETH-0002",
            "domain_code": "PETH",
            "subdomain": "Informed Consent",
            "difficulty_level": 3,
            "encounter": {
                "setting": "Collaborative care psychiatric evaluation — following psychologist referral",
                "referral_context": "Psychologist referring patient for medication consultation for OCD. Patient has been in ERP therapy for 6 months with partial response. Psychiatrist is evaluating for SSRI augmentation.",
                "patient": {
                    "label": "Adult Female, 29",
                    "appearance_tags": ["organized notes in hand", "careful about touching objects in office", "deliberate speech", "perfectionistic self-presentation"],
                    "initial_avatar_state": "anxious"
                },
                "phases": [
                    {
                        "phase_id": "chief_complaint",
                        "phase_label": "Chief Complaint",
                        "dialogue": "My therapist thinks I should try medication. I'm not opposed to it, but I've read a lot about SSRIs. I've read they can cause emotional blunting and make it hard to feel things. I've also read they cause weight gain and sexual side effects. I need to understand exactly what I'd be getting into before I agree to anything.",
                        "avatar_emotion": "anxious",
                        "behavioral_tags": ["informed decision-making", "research-informed patient", "side effect concerns", "OCD ego-syntonic research behavior"],
                        "chart_reveals": [
                            {"category": "Chief Complaint", "label": "Consultation question", "value": "Evaluating SSRI for OCD (partial ERP response); patient requesting comprehensive informed consent before deciding"},
                            {"category": "Chief Complaint", "label": "Patient knowledge", "value": "Independently researched SSRIs; aware of emotional blunting, weight gain, and sexual side effect concerns"}
                        ],
                        "clinician_prompt": None
                    },
                    {
                        "phase_id": "medication_discussion",
                        "phase_label": "Medication Information and Informed Consent",
                        "dialogue": "If I start sertraline and it doesn't work or I have side effects, can I stop? What happens if I stop suddenly? And I also want to know — what happens if I don't take medication? My therapist said ERP alone might eventually work but will take longer.",
                        "avatar_emotion": "guarded",
                        "behavioral_tags": ["treatment alternatives request", "discontinuation concerns", "decision-making autonomy", "right to refuse"],
                        "chart_reveals": [
                            {"category": "History of Present Illness", "label": "Informed consent elements requested", "value": "Benefits, risks, alternatives, right to discontinue — all explicitly requested by patient"},
                            {"category": "History of Present Illness", "label": "Treatment alternatives", "value": "ERP monotherapy (slow response), SSRI monotherapy, combined ERP + SSRI (highest evidence base)"},
                            {"category": "Labs / Observations", "label": "Current clinical status", "value": "Partial ERP response at 6 months; Y-BOCS score 22 (moderate-severe); functioning impaired"}
                        ],
                        "clinician_prompt": "Those are exactly the right questions. Let me walk through each one carefully."
                    },
                    {
                        "phase_id": "decision_capacity",
                        "phase_label": "Decisional Capacity Assessment",
                        "dialogue": "I understand the risk-benefit information. Combined treatment gives me the best odds. But I'm not ready to take medication yet. I want two more months of ERP alone. I understand the risks of waiting. Can I come back to this decision?",
                        "avatar_emotion": "hopeful",
                        "behavioral_tags": ["intact decisional capacity", "autonomous choice", "right to refuse evidence-based treatment", "shared decision-making"],
                        "chart_reveals": [
                            {"category": "Mental Status Examination", "label": "Decisional capacity", "value": "Intact — understands, appreciates, reasons, and communicates a consistent choice"},
                            {"category": "Mental Status Examination", "label": "Patient decision", "value": "Declines SSRI at this time; chooses intensified ERP for 2 months before reassessing"},
                            {"category": "Collateral / Context", "label": "Clinician response", "value": "Patient's right to refuse respected; plan documented; follow-up scheduled; Y-BOCS to be tracked"}
                        ],
                        "clinician_prompt": "You've clearly thought about this carefully. Let's talk about what would make you feel ready to reconsider."
                    }
                ]
            },
            "questions": [
                {
                    "question_id": "q1",
                    "type": "dsm_criteria",
                    "prompt": "Which of the following elements are required for legally and ethically valid informed consent to psychiatric medication treatment?",
                    "options": {
                        "A": "Diagnosis disclosure, treatment rationale, benefits, risks, and alternatives — including the alternative of no treatment",
                        "B": "Patient signature on a standardized form and verbal agreement from a family member",
                        "C": "Physician attestation that the patient has read and understood the medication insert",
                        "D": "Benefits and risks only — alternatives need only be discussed if the patient asks"
                    },
                    "correct_answer": "A",
                    "explanation": "Valid informed consent requires the clinician to disclose: (1) the diagnosis and clinical indication for treatment; (2) the nature of the proposed treatment (what it is, how it works); (3) the material risks of the proposed treatment; (4) the expected benefits; (5) available alternatives — including the option of no treatment and what would likely happen without treatment; (6) the patient's right to withdraw consent at any time. Informed consent is a process, not merely a document — ongoing dialogue is required. This patient is actively exercising her right to request all elements, and the clinician is ethically obligated to provide them.",
                    "distractor_rationale": {
                        "B": "Family member agreement is not a component of informed consent for an adult with intact decisional capacity. Family involvement may be appropriate in some contexts but does not substitute for patient consent.",
                        "C": "Medication inserts are not a legally or ethically sufficient informed consent mechanism. The clinician must engage the patient in individualized discussion tailored to the specific clinical situation.",
                        "D": "Alternatives — including no treatment — must be proactively disclosed, not withheld until the patient asks. Failing to disclose alternatives constitutes inadequate informed consent."
                    }
                },
                {
                    "question_id": "q2",
                    "type": "immediate_intervention",
                    "prompt": "The patient declines SSRI medication despite understanding that combined treatment is most evidence-based. She demonstrates intact decisional capacity. What is the ethically correct response?",
                    "options": {
                        "A": "Override her decision and prescribe the SSRI because the clinician has an obligation to provide the most effective treatment",
                        "B": "Refer her to another psychiatrist who might be more persuasive in securing medication agreement",
                        "C": "Respect her autonomous decision, document thoroughly, adjust the ERP plan, and establish clear reassessment criteria",
                        "D": "Require her to sign a document acknowledging she is refusing standard of care before continuing treatment"
                    },
                    "correct_answer": "C",
                    "explanation": "APA Ethical Principle E (Respect for People's Rights and Dignity) and Standard 3.10 (Informed Consent) recognize that adults with intact decisional capacity have the right to refuse treatment, including evidence-based treatment. The clinician's role is to ensure the decision is truly informed (which it is) and autonomous (which it appears to be), then to respect it. The appropriate response is to document the consent discussion and the patient's decision clearly, adjust the ERP plan to maximize its effectiveness during the two-month trial, and set clear reassessment criteria. Refusing to treat a patient who declines medication, or coercing consent through referral to a 'more persuasive' colleague, would be ethically impermissible.",
                    "distractor_rationale": {
                        "A": "Overriding a competent adult's informed refusal constitutes battery regardless of clinical intent. Beneficence does not override patient autonomy in a competent adult.",
                        "B": "Referring to achieve a different outcome is a form of ethical manipulation — using clinical authority to circumvent a patient's autonomous choice rather than respecting it.",
                        "D": "While documentation of refusal is appropriate, requiring a patient to sign a 'refusing standard of care' document creates coercive pressure and misrepresents the ethical and clinical situation. The patient is making an informed, autonomous choice — not refusing care itself."
                    }
                }
            ]
        }
    ]
}


# ─── Write all files ──────────────────────────────────────────────────────────

DOMAINS = {
    "PTHE": PTHE,
    "BPSY": BPSY,
    "PMET": PMET,
    "LDEV": LDEV,
    "SOCU": SOCU,
    "WDEV": WDEV,
    "CASS": CASS,
    "PETH": PETH,
}

for code, data in DOMAINS.items():
    path = DATA / f"{code}_presentations.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    count = len(data["encounters"])
    print(f"  OK {path}  ({count} encounter{'s' if count != 1 else ''})")

print(f"\nSeed data written for {len(DOMAINS)} domains.")
print("Run 'python generate_presentations.py --all --count 30 --resume' with an API key to expand to full 30 encounters.")
