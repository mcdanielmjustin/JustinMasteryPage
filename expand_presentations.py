#!/usr/bin/env python3
"""Expand clinical presentation encounters for thin subdomains."""
import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_file(domain):
    path = os.path.join(DATA_DIR, f"{domain}_presentations.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_file(domain, data):
    path = os.path.join(DATA_DIR, f"{domain}_presentations.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path} ({data['total_encounters']} encounters)")


def append_encounters(domain, new_encounters):
    data = load_file(domain)
    existing_ids = {enc["id"] for enc in data["encounters"]}
    added = 0
    for enc in new_encounters:
        if enc["id"] not in existing_ids:
            data["encounters"].append(enc)
            added += 1
    if added > 0:
        data["total_encounters"] = len(data["encounters"])
        save_file(domain, data)
    else:
        print(f"  No new encounters to add for {domain} (all already present)")
    return data["total_encounters"], added


# ============================================================
# CPAT: 2 new encounters
# ============================================================
CPAT_NEW = [
    {
        "id": "CP-CPAT-0031",
        "domain_code": "CPAT",
        "subdomain": "Depressive Disorders",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Emergency department psychiatric consultation",
            "referral_context": "ED physician requests psych consult for 19-year-old college student brought in by roommate after 3 days of not leaving dorm room, refusing food, and expressing hopelessness.",
            "patient": {
                "label": "Young Adult Male, 19",
                "appearance_tags": ["unkempt", "weight loss visible", "withdrawn posture", "avoids eye contact"],
                "initial_avatar_state": "flat_affect"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "I don't know why I'm here. My roommate overreacted. I just... I don't see the point in anything anymore. College was supposed to be this great thing but I can't focus, I can't sleep, I can't even eat. I've been like this since the semester started.",
                    "avatar_emotion": "flat_affect",
                    "behavioral_tags": ["anhedonia", "hopelessness", "insomnia", "appetite loss", "social withdrawal"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Primary concern", "value": "Pervasive hopelessness, functional decline over 8 weeks since semester onset"},
                        {"category": "Chief Complaint", "label": "Precipitant", "value": "First semester away from home; no identified acute stressor beyond transition"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "History of Present Illness",
                    "dialogue": "I haven't slept more than 3 hours a night in weeks. I lost about 20 pounds since September. I stopped going to class three weeks ago. I used to love playing guitar but I haven't touched it. My mom calls every day and I just let it ring. I feel guilty about that too.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["initial insomnia", "significant weight loss", "academic decline", "anhedonia", "guilt", "social withdrawal"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Sleep", "value": "Initial insomnia — 3 hrs/night for ~6 weeks"},
                        {"category": "History of Present Illness", "label": "Weight", "value": "20 lb weight loss over 8 weeks; decreased appetite"},
                        {"category": "History of Present Illness", "label": "Functioning", "value": "Stopped attending classes 3 weeks ago; ceased all leisure activities"},
                        {"category": "History of Present Illness", "label": "Family hx", "value": "Mother with history of recurrent MDD; maternal uncle completed suicide age 34"}
                    ],
                    "clinician_prompt": "Can you tell me more about your sleep and appetite changes?"
                },
                {
                    "phase_id": "mental_status",
                    "phase_label": "Mental Status Examination",
                    "dialogue": "Honestly? Sometimes I think about driving my car into a bridge abutment. I haven't done it. But the thought is there. I don't have a plan exactly... it's more like I wouldn't care if something happened to me. I feel like I'm already gone.",
                    "avatar_emotion": "flat_affect",
                    "behavioral_tags": ["active SI with method", "no specific plan", "passive death wish", "flat affect", "psychomotor retardation"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Suicidality", "value": "Active SI with identified method (car/bridge); no specific plan or timeline; passive death wish present"},
                        {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Mood: 'empty'; Affect: flat, constricted range, congruent"},
                        {"category": "Mental Status Examination", "label": "Cognition", "value": "Attention impaired; oriented x4; speech slow, low volume"},
                        {"category": "Mental Status Examination", "label": "Insight/Judgment", "value": "Fair insight — recognizes change; impaired judgment — minimizes severity"}
                    ],
                    "clinician_prompt": "Have you had any thoughts about hurting yourself or ending your life?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial Context",
                    "dialogue": "I'm the first in my family to go to college. Everyone's counting on me. My dad works two jobs to pay tuition. If I drop out, I'll have failed everyone. I can't tell them how bad it is. I have no friends here. My roommate barely knows me.",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["performance pressure", "social isolation", "family obligation guilt", "first-generation student stress"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Social support", "value": "Minimal — no established peer network; estranged from family emotionally"},
                        {"category": "Psychosocial Context", "label": "Stressors", "value": "First-generation college student; financial pressure; cultural expectation to succeed"},
                        {"category": "Psychosocial Context", "label": "Protective factors", "value": "Family connection (though avoidant); roommate noticed and intervened; no substance use"}
                    ],
                    "clinician_prompt": "Tell me about your support system here at school and back home."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "risk_assessment",
                "prompt": "This patient reports active suicidal ideation with an identified method but no specific plan. Given the full clinical picture, what is the most appropriate disposition?",
                "options": {
                    "A": "Discharge with outpatient therapy referral and safety plan",
                    "B": "Voluntary inpatient psychiatric admission with safety monitoring",
                    "C": "Discharge with SSRI prescription and 1-week follow-up",
                    "D": "Hold for 72-hour involuntary observation regardless of patient willingness"
                },
                "correct_answer": "B",
                "explanation": "This patient presents with active SI with an identified method, significant functional decline, severe neurovegetative symptoms, social isolation, family history of completed suicide, and impaired judgment. These cumulative risk factors — particularly active SI with method identification — elevate risk beyond what outpatient safety planning alone can manage. Voluntary inpatient admission allows stabilization, medication initiation under monitoring, and comprehensive safety assessment.",
                "distractor_rationale": {
                    "A": "Outpatient referral alone is insufficient given active SI with method, severe functional impairment, and no social support system at college. This underestimates risk.",
                    "C": "Starting an SSRI in an ED without monitoring is inappropriate given suicide risk — SSRIs carry a black-box warning for increased suicidality in patients under 25 during initiation.",
                    "D": "Involuntary hold is not indicated when a patient is willing to engage voluntarily. The patient has not refused treatment. Involuntary commitment requires imminent danger AND refusal of voluntary treatment."
                }
            },
            {
                "question_id": "q2",
                "type": "primary_diagnosis",
                "prompt": "Which DSM-5-TR diagnosis is BEST supported by this clinical presentation?",
                "options": {
                    "A": "Adjustment Disorder with Depressed Mood",
                    "B": "Major Depressive Disorder, Single Episode, Severe without Psychotic Features",
                    "C": "Persistent Depressive Disorder (Dysthymia)",
                    "D": "Unspecified Depressive Disorder"
                },
                "correct_answer": "B",
                "explanation": "The patient meets criteria for MDD: depressed mood, anhedonia, insomnia, significant weight loss, psychomotor retardation, guilt, impaired concentration, and recurrent suicidal ideation — well over 5 symptoms for more than 2 weeks with marked functional impairment. Severity is 'severe' given active SI with method, near-total functional collapse, and multiple neurovegetative symptoms. No psychotic features are present. No prior episodes are reported, supporting 'single episode.'",
                "distractor_rationale": {
                    "A": "Adjustment Disorder is only diagnosed when full criteria for another disorder (like MDD) are NOT met. This patient clearly meets full MDD criteria with 8+ symptoms.",
                    "C": "Dysthymia requires depressed mood more days than not for at least 2 years. This episode is 8 weeks in duration.",
                    "D": "Unspecified Depressive Disorder is used when criteria for a specific depressive disorder are not fully met. This patient meets full MDD criteria."
                }
            }
        ]
    },
    {
        "id": "CP-CPAT-0032",
        "domain_code": "CPAT",
        "subdomain": "Eating and Feeding Disorders",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Outpatient eating disorders specialty clinic",
            "referral_context": "Referred by college health center after routine physical revealed BMI of 16.2, bradycardia (HR 48), and lanugo. Patient is a 20-year-old competitive cross-country runner.",
            "patient": {
                "label": "Young Adult Female, 20",
                "appearance_tags": ["emaciated", "lanugo on arms", "layered clothing", "brittle hair", "cold extremities"],
                "initial_avatar_state": "guarded"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "I'm not sure why they sent me here. I eat fine. I'm an athlete — I need to stay lean for competition. My coach says my times are dropping but that's because of the stress of school, not my weight. I feel fine. Maybe a little tired.",
                    "avatar_emotion": "guarded",
                    "behavioral_tags": ["denial of illness", "minimization", "body image distortion", "rationalization"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Primary concern", "value": "Patient denies concern; referral source notes BMI 16.2, bradycardia, physical signs of malnutrition"},
                        {"category": "Chief Complaint", "label": "Patient perspective", "value": "Attributes weight to athletic identity; denies restriction"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "History of Present Illness",
                    "dialogue": "I run about 70 miles a week. I eat what I need — mostly vegetables, egg whites, rice cakes. I haven't had my period in about eight months but my coach said that's normal for female athletes. I do count calories — around 800 a day — but that's just being disciplined.",
                    "avatar_emotion": "guarded",
                    "behavioral_tags": ["excessive exercise", "caloric restriction", "amenorrhea", "food rules", "calorie counting"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Dietary intake", "value": "Self-reported 800 kcal/day with rigid food rules; high exercise volume (70 mi/wk running)"},
                        {"category": "History of Present Illness", "label": "Menstrual status", "value": "Secondary amenorrhea x 8 months — consistent with female athlete triad / RED-S"},
                        {"category": "History of Present Illness", "label": "Vitals", "value": "BMI 16.2 (severely underweight); HR 48 bpm; BP 88/56; temp 96.1F"},
                        {"category": "History of Present Illness", "label": "Medical concerns", "value": "Lanugo, brittle hair, cold intolerance, orthostatic dizziness"}
                    ],
                    "clinician_prompt": "Can you walk me through what you typically eat in a day?"
                },
                {
                    "phase_id": "mental_status",
                    "phase_label": "Mental Status Examination",
                    "dialogue": "I'm not underweight — I'm lean. There's a difference. My teammates weigh less than me and no one's sending them here. If I gain weight, I'll lose my scholarship. You don't understand what it takes. I know exactly what I'm doing.",
                    "avatar_emotion": "angry",
                    "behavioral_tags": ["body image distortion", "overvaluation of thinness", "poor insight", "intellectualization", "competitive comparison"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Body image", "value": "Marked distortion — perceives severely underweight frame as 'lean'; intense fear of weight gain"},
                        {"category": "Mental Status Examination", "label": "Insight", "value": "Poor — denies illness; ego-syntonic restriction; rationalizes symptoms as athletic discipline"},
                        {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Mood: 'fine'; Affect: irritable when challenged, constricted range"},
                        {"category": "Mental Status Examination", "label": "Cognition", "value": "Concrete thinking around food/body; rigid cognitive style; concentration grossly intact"}
                    ],
                    "clinician_prompt": "How do you feel about your current weight and body shape?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial Context",
                    "dialogue": "My mom was always dieting when I was growing up. She used to comment on what I ate. My dad left when I was 12 and things got worse after that — my mom focused even more on appearance. Running was the one thing I was good at. I can't lose that.",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["family modeling of disordered eating", "parental criticism of body", "early adversity", "identity enmeshed with athletics"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Family history", "value": "Mother with likely disordered eating; critical comments about patient's food intake throughout childhood"},
                        {"category": "Psychosocial Context", "label": "Developmental", "value": "Parental divorce age 12; restriction behaviors began ~age 14"},
                        {"category": "Psychosocial Context", "label": "Identity", "value": "Self-worth entirely enmeshed with athletic performance and body control"},
                        {"category": "Psychosocial Context", "label": "Social", "value": "Teammates are primary social network; fears being removed from team if gains weight or if diagnosed"}
                    ],
                    "clinician_prompt": "Tell me about your relationship with food growing up."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "primary_diagnosis",
                "prompt": "Based on this clinical presentation, which DSM-5-TR diagnosis is MOST supported?",
                "options": {
                    "A": "Anorexia Nervosa, Restricting Type",
                    "B": "Avoidant/Restrictive Food Intake Disorder (ARFID)",
                    "C": "Atypical Anorexia Nervosa (Other Specified Feeding or Eating Disorder)",
                    "D": "Body Dysmorphic Disorder"
                },
                "correct_answer": "A",
                "explanation": "This patient meets all three DSM-5-TR criteria for Anorexia Nervosa, Restricting Type: (1) restriction of energy intake relative to requirements leading to significantly low body weight (BMI 16.2); (2) intense fear of gaining weight (fears losing scholarship if weight increases); (3) disturbance in body image (perceives emaciated frame as 'lean'). The restricting subtype is specified because there is no binge-purge behavior reported — weight loss is achieved through dietary restriction and excessive exercise.",
                "distractor_rationale": {
                    "A": None,
                    "B": "ARFID involves food avoidance due to sensory characteristics, fear of aversive consequences of eating, or lack of interest in food — NOT body image distortion or fear of fatness. This patient has clear body image disturbance.",
                    "C": "Atypical AN is diagnosed when all AN criteria are met EXCEPT the individual is not underweight. This patient IS significantly underweight (BMI 16.2), so full AN criteria are met.",
                    "D": "BDD involves preoccupation with perceived defects in appearance not better explained by an eating disorder. Body image distortion specific to weight/shape in the context of restriction and low weight is diagnostic of AN."
                }
            },
            {
                "question_id": "q2",
                "type": "immediate_intervention",
                "prompt": "Given this patient's vital signs (HR 48, BP 88/56, BMI 16.2), what is the MOST clinically urgent next step?",
                "options": {
                    "A": "Begin outpatient CBT-E (enhanced cognitive-behavioral therapy for eating disorders)",
                    "B": "Refer to higher level of care for medical stabilization",
                    "C": "Start nutritional counseling with gradual caloric increase",
                    "D": "Prescribe fluoxetine to address body image disturbance"
                },
                "correct_answer": "B",
                "explanation": "This patient presents with medical instability: bradycardia (HR 48), hypotension (88/56), hypothermia (96.1F), and BMI 16.2. These vital sign abnormalities indicate cardiovascular compromise secondary to malnutrition and warrant medical stabilization, typically in a hospital or residential eating disorder facility. Outpatient treatment alone is insufficient when medical instability is present. APA Practice Guidelines recommend hospitalization when HR <50, systolic BP <90, or BMI <15 (some programs use <16).",
                "distractor_rationale": {
                    "A": "CBT-E is an evidence-based outpatient treatment for AN but requires medical stability as a prerequisite. This patient's vital signs preclude safe outpatient treatment.",
                    "C": "Nutritional rehabilitation is essential but must occur under medical monitoring given her cardiac compromise. Refeeding syndrome (potentially fatal electrolyte shifts) is a risk when refeeding severely malnourished patients without medical oversight.",
                    "D": "SSRIs have not demonstrated efficacy for AN in the underweight state. Pharmacotherapy is not a first-line intervention, and this patient needs medical stabilization before any psychiatric medication trial."
                }
            }
        ]
    }
]

# ============================================================
# PTHE: 2 new encounters (Child and Play Therapy)
# ============================================================
PTHE_NEW = [
    {
        "id": "CP-PTHE-0031",
        "domain_code": "PTHE",
        "subdomain": "Child and Play Therapy",
        "difficulty_level": 2,
        "encounter": {
            "setting": "Community child and family therapy center",
            "referral_context": "6-year-old referred by school counselor after repeated aggressive outbursts in kindergarten. Mother reports behavioral changes since witnessing domestic violence 4 months ago.",
            "patient": {
                "label": "Child Male, 6",
                "appearance_tags": ["hypervigilant", "clings to mother", "avoids eye contact with clinician", "tense posture"],
                "initial_avatar_state": "anxious"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Child is initially silent, clutching a stuffed animal. Mother speaks) He won't talk about what happened. At school he hits other kids or hides under his desk. At home he has nightmares almost every night. He used to be such a happy kid.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["selective mutism in session", "hypervigilance", "aggression at school", "nightmares", "regression"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Primary concern", "value": "Aggressive outbursts at school and nightmares following witnessed domestic violence"},
                        {"category": "Chief Complaint", "label": "Onset", "value": "4 months ago; behavioral changes coincided with DV incident"},
                        {"category": "Chief Complaint", "label": "Collateral", "value": "Mother reports child witnessed father physically assaulting her; father no longer in home (restraining order)"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "collateral",
                    "phase_label": "Collateral and Developmental History",
                    "dialogue": "(Mother) He was meeting all his milestones before this. Now he wets the bed again — he'd been dry since age 3. He won't let me out of his sight. If I go to the bathroom he panics. He told his grandmother 'the bad man is coming back.'",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["enuresis regression", "separation anxiety", "trauma re-experiencing", "developmental regression"],
                    "chart_reveals": [
                        {"category": "Developmental History", "label": "Pre-trauma", "value": "Meeting milestones; toilet trained at 3; socially engaged; no prior behavioral concerns"},
                        {"category": "History of Present Illness", "label": "Regression", "value": "Secondary enuresis (bed-wetting); separation anxiety; hypervigilance"},
                        {"category": "History of Present Illness", "label": "Re-experiencing", "value": "Nightmares; verbal statements about 'bad man coming back'; trauma-themed play at school"},
                        {"category": "History of Present Illness", "label": "Avoidance", "value": "Refuses to enter room where assault occurred; avoids male authority figures at school"}
                    ],
                    "clinician_prompt": "Has he shown any changes in behaviors he had already mastered, like toileting or sleeping alone?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Play-Based Assessment",
                    "dialogue": "(During unstructured play, child arranges toy figures. A large figure repeatedly knocks down a small figure. Child whispers) He's bad. She's scared. The little one hides. (Child pushes all figures off table and retreats to mother's lap.)",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["trauma reenactment in play", "symbolic representation", "emotional dysregulation", "proximity seeking"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Play themes", "value": "Repetitive trauma reenactment: aggressor figure attacks smaller figure; child identifies with 'little one'"},
                        {"category": "Mental Status Examination", "label": "Affect regulation", "value": "Rapidly overwhelmed; limited capacity to modulate distress; seeks proximity to mother"},
                        {"category": "Mental Status Examination", "label": "Verbal expression", "value": "Minimal spontaneous speech; whispered narration during play; no formal thought disorder"},
                        {"category": "Mental Status Examination", "label": "Motor behavior", "value": "Hypervigilant to sounds; startled when door closed in hallway; fine motor intact in play"}
                    ],
                    "clinician_prompt": "Can you tell me about the people you made with the toys?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial Context",
                    "dialogue": "(Mother) I feel so guilty. I should have left sooner. His father was never violent toward him directly but he saw everything. We're living with my sister now. He won't go to his dad's for visitation — he screams. The school is threatening suspension for the hitting.",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["maternal guilt", "housing instability", "visitation conflict", "school discipline risk"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Living situation", "value": "Currently with maternal aunt; stable but temporary; restraining order against father"},
                        {"category": "Psychosocial Context", "label": "School", "value": "At risk for suspension due to aggression; school unaware of DV history"},
                        {"category": "Psychosocial Context", "label": "Protective factors", "value": "Strong maternal bond; mother engaged in treatment; stable temporary housing; no substance abuse in home"},
                        {"category": "Psychosocial Context", "label": "Risk factors", "value": "Ongoing custody/visitation conflict; housing instability; limited family resources"}
                    ],
                    "clinician_prompt": "What does your living situation look like right now, and how is the school handling his behavior?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "treatment_planning",
                "prompt": "Which therapeutic approach is MOST appropriate as the primary treatment for this 6-year-old with trauma symptoms?",
                "options": {
                    "A": "Trauma-Focused Cognitive Behavioral Therapy (TF-CBT) with caregiver involvement",
                    "B": "Individual psychodynamic psychotherapy without parental involvement",
                    "C": "Applied Behavior Analysis (ABA) targeting aggressive behaviors",
                    "D": "Immediate EMDR processing of the traumatic memory"
                },
                "correct_answer": "A",
                "explanation": "TF-CBT is the gold-standard, evidence-based treatment for childhood PTSD, with the strongest empirical support for children ages 3-18 who have experienced trauma. It incorporates caregiver involvement as a core component (the PRACTICE model includes conjoint parent-child sessions), which is essential given this child's separation anxiety and the mother's role as primary attachment figure. TF-CBT integrates gradual exposure, cognitive processing, and relaxation skills in a developmentally appropriate, structured format.",
                "distractor_rationale": {
                    "B": "Excluding the caregiver from treatment is contraindicated — caregiver involvement is essential for young children with trauma. The child's separation anxiety and developmental stage require a caregiver-inclusive model.",
                    "C": "ABA targets behavioral contingencies and is primarily indicated for autism spectrum disorder. It does not address the underlying trauma that is driving this child's aggression and does not process traumatic experiences.",
                    "D": "While EMDR has evidence for childhood trauma, immediate trauma processing without stabilization is inappropriate. This child requires rapport-building, psychoeducation, and coping skills before any direct trauma processing."
                }
            },
            {
                "question_id": "q2",
                "type": "assessment_tool",
                "prompt": "Which of the following would be MOST useful for assessing this child's trauma symptom severity?",
                "options": {
                    "A": "Beck Depression Inventory-II (BDI-II)",
                    "B": "UCLA PTSD Reaction Index for DSM-5 (Child/Caregiver version)",
                    "C": "Conners Rating Scale (parent form)",
                    "D": "Children's Apperception Test (CAT)"
                },
                "correct_answer": "B",
                "explanation": "The UCLA PTSD Reaction Index is the most widely used and well-validated measure of trauma exposure and PTSD symptoms in children ages 6 and older. It has both child-report and caregiver-report versions, maps directly to DSM-5 PTSD criteria, and provides severity scores for each symptom cluster (intrusion, avoidance, negative cognitions/mood, arousal). It is the standard assessment in TF-CBT and trauma-focused research.",
                "distractor_rationale": {
                    "A": "The BDI-II is a depression measure validated for ages 13+. It is not appropriate for a 6-year-old and does not assess trauma-specific symptoms.",
                    "C": "The Conners measures ADHD and behavioral symptoms. While this child shows behavioral problems, the primary concern is trauma — the Conners would not assess re-experiencing, avoidance, or hyperarousal as trauma symptoms.",
                    "D": "The CAT is a projective test that may reveal thematic content but lacks the psychometric rigor, standardized scoring, and trauma-specific focus needed for symptom severity measurement."
                }
            }
        ]
    },
    {
        "id": "CP-PTHE-0032",
        "domain_code": "PTHE",
        "subdomain": "Child and Play Therapy",
        "difficulty_level": 2,
        "encounter": {
            "setting": "Private practice — child therapy office equipped with play materials",
            "referral_context": "Parents seek therapy for 8-year-old daughter with selective mutism. She speaks normally at home but has not spoken at school for 2 years despite average intelligence and no speech/language disorder.",
            "patient": {
                "label": "Child Female, 8",
                "appearance_tags": ["frozen posture", "wide eyes", "whispers only to mother", "holds mother's hand tightly"],
                "initial_avatar_state": "anxious"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Child is silent, eyes scanning the room. Mother speaks) She literally does not say a word at school. She communicates by nodding or pointing. Her teacher says she's bright — her written work is excellent — but she won't speak to anyone outside our family. It's been like this since first grade.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["selective mutism", "nonverbal communication", "social anxiety", "context-dependent speech"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Primary concern", "value": "Consistent failure to speak in school setting for 2 years; speaks freely at home"},
                        {"category": "Chief Complaint", "label": "Duration", "value": "Onset in first grade (age 6); currently in 3rd grade"},
                        {"category": "Chief Complaint", "label": "Academics", "value": "Written work at or above grade level; participation grades suffer due to no verbal output"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "History and Developmental Context",
                    "dialogue": "(Mother) She hit all her speech milestones on time. At home she's chatty and even bossy with her little brother. But the minute we leave the house, she shuts down. Birthday parties, restaurants, the doctor — she won't speak. She had a speech evaluation and everything was normal.",
                    "avatar_emotion": "neutral",
                    "behavioral_tags": ["normal speech development", "context-specific mutism", "social inhibition across settings", "family system contrast"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Speech development", "value": "All milestones met; speech-language evaluation WNL; articulation, fluency, receptive/expressive language all intact"},
                        {"category": "History of Present Illness", "label": "Pattern", "value": "Speaks to parents, sibling, grandparents; mute with teachers, peers, unfamiliar adults, and in public settings"},
                        {"category": "History of Present Illness", "label": "Social functioning", "value": "Has one friend from neighborhood who she whispers to; no friends at school"},
                        {"category": "History of Present Illness", "label": "Family history", "value": "Father describes himself as 'painfully shy' as child; maternal grandmother had social anxiety"}
                    ],
                    "clinician_prompt": "Can you tell me about the settings where she does and doesn't speak?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Play-Based Assessment",
                    "dialogue": "(Clinician offers art materials. Child draws carefully. When clinician asks 'Can you tell me about your drawing?' child looks at floor. Mother whispers encouragement. Child whispers to mother, who relays: 'She says it's her classroom and she's the one sitting alone.')",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["communicates through art", "whisper chain through parent", "social isolation theme", "compliant but nonverbal"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Communication", "value": "Nonverbal with clinician; whispers to mother as intermediary; engaged through art and drawing"},
                        {"category": "Mental Status Examination", "label": "Affect", "value": "Anxious; constricted; hyperaware of clinician's attention; no oppositional behavior"},
                        {"category": "Mental Status Examination", "label": "Cognition", "value": "Drawing detail suggests age-appropriate cognitive and fine motor functioning; thematic content shows self-awareness of social difficulty"},
                        {"category": "Mental Status Examination", "label": "Behavioral", "value": "No disruptive behavior; cooperative nonverbally; separates from mother briefly to draw but returns quickly"}
                    ],
                    "clinician_prompt": "Would you like to draw something while we talk? You can show me anything you'd like."
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial Context",
                    "dialogue": "(Mother) Her teacher thinks she's being defiant. She got detention once for 'refusing to answer.' I was furious — she's not being oppositional, she's terrified. I've tried everything — bribing her, punishing her. Nothing works. I'm afraid she'll never have friends.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["school misperception as defiance", "parental frustration", "punitive approaches failed", "social isolation concern"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "School response", "value": "Teacher interprets silence as defiance; punitive discipline applied; no accommodations in place"},
                        {"category": "Psychosocial Context", "label": "Parental attempts", "value": "Rewards, punishments, verbal reassurance — all ineffective; parental pressure may increase anxiety"},
                        {"category": "Psychosocial Context", "label": "Peer relationships", "value": "One neighborhood friend; no school friendships; excluded from group activities due to silence"},
                        {"category": "Psychosocial Context", "label": "Strengths", "value": "Strong family relationships; engaged parents; academic capability; no comorbid behavioral issues"}
                    ],
                    "clinician_prompt": "How has the school responded to her silence, and what have you tried at home?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "primary_diagnosis",
                "prompt": "Which DSM-5-TR diagnosis BEST explains this child's presentation?",
                "options": {
                    "A": "Social Anxiety Disorder (Social Phobia)",
                    "B": "Selective Mutism",
                    "C": "Autism Spectrum Disorder, Level 1",
                    "D": "Oppositional Defiant Disorder"
                },
                "correct_answer": "B",
                "explanation": "Selective Mutism is characterized by consistent failure to speak in specific social situations where speech is expected (school) despite speaking in other situations (home). Duration exceeds 1 month beyond the first month of school, it interferes with academic and social functioning, and it is not attributable to a communication disorder, ASD, or psychotic disorder. This child meets all criteria: speaks normally at home, mute at school for 2 years, normal speech development, and significant functional impairment. Note: Selective Mutism is classified under Anxiety Disorders in DSM-5-TR.",
                "distractor_rationale": {
                    "A": "While selective mutism is often comorbid with social anxiety (and classified in the same chapter), SAD alone does not account for the complete absence of speech in specific contexts. Selective mutism is the more specific and accurate diagnosis.",
                    "C": "ASD Level 1 involves deficits in social communication across contexts and restricted/repetitive behaviors. This child communicates normally at home and shows no restricted interests or repetitive behaviors. Her social difficulty is anxiety-driven, not a pervasive developmental difference.",
                    "D": "ODD involves angry/irritable mood, argumentative/defiant behavior, and vindictiveness. This child is compliant and cooperative — her silence is driven by anxiety, not opposition. The teacher's misperception of defiance is a common error."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "Which therapeutic approach has the STRONGEST evidence base for treating selective mutism in children?",
                "options": {
                    "A": "Behavioral interventions including stimulus fading and shaping with contingency management",
                    "B": "Intensive psychodynamic play therapy exploring unconscious conflict",
                    "C": "Social skills training group to increase peer interaction",
                    "D": "Forcing the child to speak by withholding preferred activities until she verbalizes"
                },
                "correct_answer": "A",
                "explanation": "Behavioral and cognitive-behavioral approaches have the strongest evidence for selective mutism. Stimulus fading involves gradually introducing feared stimuli (e.g., new people) while the child is already speaking in a comfortable context. Shaping reinforces successive approximations toward speech (e.g., mouthing words, whispering, then speaking aloud). Contingency management reinforces brave speaking behaviors without pressuring or punishing. The Brave Program and the Integrated Behavioral Treatment for Selective Mutism are well-supported protocols.",
                "distractor_rationale": {
                    "B": "Psychodynamic play therapy lacks empirical support as a primary treatment for selective mutism. While play is used therapeutically, the mechanism of change in SM is behavioral exposure, not insight into unconscious conflict.",
                    "C": "Social skills training assumes a skills deficit. This child has adequate social and communication skills (demonstrated at home) — the barrier is anxiety-based inhibition, not a skills gap.",
                    "D": "Coercive approaches are contraindicated — forcing speech increases anxiety, reinforces the mutism cycle, and damages the therapeutic relationship. This approach reflects the common misconception that SM is volitional defiance."
                }
            }
        ]
    }
]

# ============================================================
# LDEV: 2 new encounters (Attachment Theory)
# ============================================================
LDEV_NEW = [
    {
        "id": "CP-LDEV-0031",
        "domain_code": "LDEV",
        "subdomain": "Attachment Theory and Patterns",
        "difficulty_level": 2,
        "encounter": {
            "setting": "Infant-parent psychotherapy clinic",
            "referral_context": "Pediatrician referred 14-month-old and mother after noting infant's failure to thrive and mother's flat affect during well-child visits. Mother has history of postpartum depression.",
            "patient": {
                "label": "Infant, 14 months (with Mother, 29)",
                "appearance_tags": ["infant: low weight-for-age", "infant: minimal vocalization", "mother: flat affect", "mother: holds infant away from body"],
                "initial_avatar_state": "flat_affect"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Mother, speaking in monotone) The doctor said she's too small. I feed her. I don't know what else to do. She doesn't seem to want me anyway — she doesn't reach for me, she doesn't cry when I leave. Maybe she's just independent.",
                    "avatar_emotion": "flat_affect",
                    "behavioral_tags": ["maternal emotional withdrawal", "misattribution of infant behavior", "depressive symptoms", "attachment disruption"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Referral concern", "value": "Failure to thrive (weight <5th percentile); flat maternal affect; disrupted mother-infant interaction"},
                        {"category": "Chief Complaint", "label": "Maternal perspective", "value": "Interprets infant's avoidance as 'independence' rather than insecure attachment"},
                        {"category": "Chief Complaint", "label": "PPD history", "value": "Diagnosed with postpartum depression at 3 months; treated briefly with sertraline; discontinued at 6 months"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Developmental and Attachment History",
                    "dialogue": "(Mother) I was so depressed after she was born. I couldn't bond with her. My mother helped for the first few months but then she left. I went back to work at 8 weeks. She's been in three different daycares. I know I should feel more connected but I just feel numb.",
                    "avatar_emotion": "flat_affect",
                    "behavioral_tags": ["disrupted early bonding", "caregiver inconsistency", "maternal depression", "emotional unavailability"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Early bonding", "value": "Disrupted by severe PPD; mother reports inability to bond in first 6 months"},
                        {"category": "History of Present Illness", "label": "Caregiver stability", "value": "3 different daycares in 14 months; no consistent secondary attachment figure"},
                        {"category": "Developmental History", "label": "Milestones", "value": "Gross motor: on track; Language: delayed (no words, minimal babbling); Social: limited social referencing"},
                        {"category": "Developmental History", "label": "Temperament", "value": "Described as 'easy — never cries'; may reflect learned suppression of attachment needs"}
                    ],
                    "clinician_prompt": "Can you tell me about those early months after she was born?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Dyadic Observation",
                    "dialogue": "(During separation-reunion observation: Mother leaves room. Infant shows no distress, continues playing without looking up. Mother returns. Infant does not approach, does not make eye contact, turns slightly away. When examiner offers toy, infant engages readily with stranger but ignores mother's attempts.)",
                    "avatar_emotion": "neutral",
                    "behavioral_tags": ["no separation distress", "avoidance on reunion", "stranger preference", "gaze aversion toward caregiver"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Attachment behavior", "value": "Consistent with insecure-avoidant (Type A) attachment: no distress at separation, active avoidance on reunion, preferential engagement with stranger"},
                        {"category": "Mental Status Examination", "label": "Affect regulation", "value": "Infant shows constricted affect; no crying, no reaching, minimal vocalization throughout session"},
                        {"category": "Mental Status Examination", "label": "Dyadic quality", "value": "Low maternal sensitivity — mother does not follow infant's cues, holds infant at distance, minimal vocalization to infant"},
                        {"category": "Mental Status Examination", "label": "Cognitive", "value": "Appropriate object exploration; cause-effect understanding in play; deficit appears relational, not cognitive"}
                    ],
                    "clinician_prompt": "I'd like to observe you and your daughter playing together for a few minutes."
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial and Intergenerational Context",
                    "dialogue": "(Mother) My own mother wasn't exactly warm. She was there but she wasn't... present. I always told myself I'd be different. But now I hear myself saying the same things — 'She's fine, she doesn't need me.' I know that's not right but I don't know how to be different.",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["intergenerational transmission of attachment", "reflective functioning emerging", "internal working model awareness", "desire for change"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Intergenerational pattern", "value": "Mother describes own childhood attachment as avoidant — emotionally present but not attuned; recognizes repetition"},
                        {"category": "Psychosocial Context", "label": "Reflective capacity", "value": "Emerging — can identify parallel between her experience and daughter's; limited ability to mentalize infant's internal states"},
                        {"category": "Psychosocial Context", "label": "Support", "value": "Single parent; limited social support; financial stress; no current mental health treatment"},
                        {"category": "Psychosocial Context", "label": "Strengths", "value": "Insight into intergenerational pattern; motivation to change; engaged in referral process"}
                    ],
                    "clinician_prompt": "What was your own experience of being parented like?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "Based on the separation-reunion observation, this infant's attachment pattern is MOST consistent with which classification from Ainsworth's Strange Situation?",
                "options": {
                    "A": "Secure attachment (Type B)",
                    "B": "Insecure-Avoidant attachment (Type A)",
                    "C": "Insecure-Resistant/Ambivalent attachment (Type C)",
                    "D": "Disorganized attachment (Type D)"
                },
                "correct_answer": "B",
                "explanation": "This infant demonstrates the hallmark behaviors of insecure-avoidant (Type A) attachment: no visible distress during separation, active avoidance of the caregiver on reunion (turning away, no approach, gaze aversion), and equal or preferential engagement with strangers. Avoidant infants have learned to suppress attachment behaviors because their caregivers are consistently emotionally unavailable or rejecting of proximity-seeking. This is an organized strategy — the infant minimizes attachment behavior to maintain proximity to an emotionally distant caregiver.",
                "distractor_rationale": {
                    "A": "Securely attached infants (Type B) show distress at separation and actively seek proximity on reunion, using the caregiver as a secure base. This infant showed neither separation distress nor reunion approach.",
                    "C": "Resistant/Ambivalent (Type C) infants show intense distress at separation AND difficulty being soothed on reunion — they approach but resist comfort, showing anger mixed with contact-seeking. This infant was notably non-distressed and avoidant.",
                    "D": "Disorganized (Type D) attachment involves contradictory behaviors — approaching while looking away, freezing, apprehension toward caregiver, behavioral collapse. This infant's behavior was consistent and organized around an avoidant strategy."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "Which intervention is MOST appropriate for this mother-infant dyad?",
                "options": {
                    "A": "Infant-Parent Psychotherapy (IPP) focusing on the caregiving relationship",
                    "B": "Individual CBT for the mother's depression only",
                    "C": "Placing the infant in a therapeutic foster care setting",
                    "D": "Parent education classes on child development milestones"
                },
                "correct_answer": "A",
                "explanation": "Infant-Parent Psychotherapy (developed by Selma Fraiberg and expanded by Alicia Lieberman) directly addresses disrupted attachment relationships by working with the dyad together. It targets the mother's 'ghosts in the nursery' — how her own attachment history interferes with her ability to respond sensitively to her infant. IPP has strong evidence for improving attachment security, maternal sensitivity, and infant outcomes when the primary concern is a disrupted caregiving relationship, particularly in the context of maternal depression and intergenerational transmission of insecure attachment.",
                "distractor_rationale": {
                    "B": "While treating maternal depression is essential, individual therapy alone does not address the relational disruption. Improving mood without changing interaction patterns may not alter the infant's attachment trajectory. Dyadic work is needed.",
                    "C": "Removal from the home is not indicated — this mother is not abusive or neglectful in a way that warrants separation. She is emotionally unavailable due to depression and her own attachment history, both treatable within the dyad.",
                    "D": "Parent education provides information but does not address the emotional and relational barriers to sensitive caregiving. This mother knows what she 'should' do but cannot access the emotional availability needed — education alone is insufficient."
                }
            }
        ]
    },
    {
        "id": "CP-LDEV-0032",
        "domain_code": "LDEV",
        "subdomain": "Attachment Theory and Patterns",
        "difficulty_level": 3,
        "encounter": {
            "setting": "University psychology training clinic — adult intake",
            "referral_context": "Self-referred 32-year-old woman seeking therapy after third relationship ended. Reports pattern of intense but short-lived romantic relationships. Previous therapist described 'attachment issues.'",
            "patient": {
                "label": "Adult Female, 32",
                "appearance_tags": ["well-groomed", "animated initially", "rapid speech", "frequent eye contact seeking"],
                "initial_avatar_state": "anxious"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "Every relationship I have follows the same pattern. I fall fast, I need constant reassurance, and then when they pull back even slightly I panic. My last boyfriend said I was 'too much.' I know I am. But I can't help it — when someone doesn't text back, I spiral. I've been told I have attachment issues but no one's really explained what that means.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["anxious attachment style", "reassurance seeking", "abandonment fear", "relationship pattern recognition"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Primary concern", "value": "Recurrent pattern of intense, unstable romantic relationships with abandonment fears"},
                        {"category": "Chief Complaint", "label": "Pattern", "value": "Rapid attachment formation; excessive reassurance seeking; panic at perceived withdrawal; relationship duration 3-8 months"},
                        {"category": "Chief Complaint", "label": "Insight", "value": "Good — recognizes pattern; limited understanding of developmental origins"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "History of Present Illness",
                    "dialogue": "When I'm in a relationship, I'm constantly monitoring — are they pulling away? Did that text seem cold? If they don't respond in an hour, I assume they're losing interest. I've driven past an ex's house. I've sent 20 texts in a row. I know it's not normal. Between relationships I feel empty, like I don't exist without someone.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["hypervigilance to rejection cues", "protest behaviors", "identity diffusion outside relationships", "monitoring behavior"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Attachment behaviors", "value": "Hyperactivated attachment system — protest behaviors (excessive contact), monitoring, difficulty self-soothing"},
                        {"category": "History of Present Illness", "label": "Self-concept", "value": "Identity feels contingent on relationship status; emptiness when single"},
                        {"category": "History of Present Illness", "label": "Emotion regulation", "value": "Intense anxiety triggered by perceived rejection; uses reassurance-seeking as primary regulation strategy"},
                        {"category": "History of Present Illness", "label": "Prior treatment", "value": "2 years of supportive therapy in 20s; therapist identified 'anxious attachment' but no targeted intervention"}
                    ],
                    "clinician_prompt": "When you notice these patterns in yourself, what does that feel like internally?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Mental Status Examination",
                    "dialogue": "I actually feel anxious right now — like, will you think I'm crazy? My last therapist seemed uncomfortable when I told her about the texting. Am I too much for therapy too? (Laughs nervously) I really need this to work. Please don't give up on me.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["therapeutic relationship anxiety", "fear of rejection by clinician", "preoccupied attachment in session", "reassurance seeking from therapist"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Therapeutic stance", "value": "Immediate activation of attachment system in therapeutic relationship; seeks reassurance from clinician"},
                        {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Mood: anxious; Affect: labile — shifts between animated, tearful, and nervous; full range but poorly modulated"},
                        {"category": "Mental Status Examination", "label": "Thought process", "value": "Linear but preoccupied with relational themes; catastrophic interpretations of ambiguous social cues"},
                        {"category": "Mental Status Examination", "label": "Insight/Judgment", "value": "Good insight into patterns; limited capacity to interrupt them; judgment impaired by anxiety in relational contexts"}
                    ],
                    "clinician_prompt": "I notice you're checking in with me about how I'm responding. What's that like for you?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial and Developmental Context",
                    "dialogue": "My mother was unpredictable. Some days she was the best mom in the world — baking, laughing, cuddling. Other days she'd lock herself in her room and not come out. I never knew which mom I'd get. My dad traveled for work and wasn't around. I learned early that if I was good enough, cute enough, she'd come back. I'm still doing that.",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["inconsistent caregiving history", "parentification", "earned insight", "preoccupied internal working model"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Early attachment", "value": "Inconsistent maternal availability — caregiver responsive when emotionally regulated, withdrawn during depressive episodes; father absent"},
                        {"category": "Psychosocial Context", "label": "Internal working model", "value": "Self: unworthy unless performing; Others: unreliable but desperately needed — consistent with anxious-preoccupied adult attachment"},
                        {"category": "Psychosocial Context", "label": "Adult functioning", "value": "Professional success (marketing director); friendships stable but secondary to romantic relationships; no substance use"},
                        {"category": "Psychosocial Context", "label": "Strengths", "value": "Reflective capacity; motivated for change; stable employment; no Axis I comorbidity beyond anxiety"}
                    ],
                    "clinician_prompt": "What was your mother like when you were growing up?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "This patient's relational pattern is MOST consistent with which adult attachment classification?",
                "options": {
                    "A": "Secure/Autonomous",
                    "B": "Dismissing/Avoidant",
                    "C": "Preoccupied/Anxious",
                    "D": "Unresolved/Disorganized"
                },
                "correct_answer": "C",
                "explanation": "This patient demonstrates a preoccupied/anxious adult attachment style (corresponding to Ainsworth's Type C insecure-resistant/ambivalent in childhood). Key features: hyperactivation of the attachment system (excessive proximity-seeking, protest behaviors), preoccupation with relationship status, difficulty self-regulating without a partner, and catastrophic interpretation of ambiguous cues as rejection. Her developmental history of inconsistent caregiving (mother sometimes available, sometimes withdrawn) maps directly to the formation of anxious/preoccupied attachment — the child learns that attachment behaviors must be amplified to get an inconsistently responsive caregiver's attention.",
                "distractor_rationale": {
                    "A": "Secure/Autonomous adults can reflect coherently on attachment experiences, tolerate closeness and separateness, and regulate emotions without excessive reliance on a partner. This patient's relational functioning is marked by anxiety and dysregulation, not security.",
                    "B": "Dismissing/Avoidant adults deactivate the attachment system — they minimize emotional needs, avoid intimacy, and emphasize self-reliance. This patient's pattern is the opposite: she hyperactivates attachment, seeking excessive closeness and reassurance.",
                    "D": "Unresolved/Disorganized attachment is associated with unresolved trauma or loss and involves contradictory approach-avoidance behaviors, dissociative episodes, and frightened/frightening caregiving. This patient's pattern is coherently organized around anxiety, not disorganized."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "Which therapeutic approach would MOST directly address this patient's attachment-related difficulties?",
                "options": {
                    "A": "Emotionally Focused Therapy (EFT) or attachment-based individual therapy",
                    "B": "Exposure and Response Prevention (ERP) for relationship anxiety",
                    "C": "Assertiveness training to establish better boundaries",
                    "D": "Brief solution-focused therapy targeting the most recent breakup"
                },
                "correct_answer": "A",
                "explanation": "Emotionally Focused Therapy (Johnson) and attachment-based approaches directly target insecure attachment patterns by helping patients access underlying attachment emotions (fear of abandonment), understand their developmental origins, and develop new relational strategies. For individual therapy, approaches informed by Bowlby's attachment theory focus on the therapeutic relationship as a secure base from which to explore internal working models and develop earned security. The therapeutic relationship itself becomes a corrective attachment experience.",
                "distractor_rationale": {
                    "B": "ERP treats OCD and specific anxiety disorders through habituation to feared stimuli. While this patient has anxiety, her difficulty is a relational pattern rooted in attachment, not a discrete anxiety disorder amenable to exposure-based treatment.",
                    "C": "Assertiveness training addresses behavioral skills deficits. This patient's issue is not a lack of assertiveness but a hyperactivated attachment system driven by fear of abandonment. Skills training without addressing the underlying attachment schema would be superficial.",
                    "D": "Brief solution-focused therapy focuses on present-oriented problem-solving and is not designed to address longstanding relational patterns rooted in developmental attachment experiences. The recurrent nature of this pattern requires deeper exploration."
                }
            }
        ]
    }
]

# ============================================================
# PETH: 8 new encounters (2 Supervision + 6 Psychopharmacology)
# ============================================================
PETH_NEW = [
    # --- Supervision Ethics #1 ---
    {
        "id": "CP-PETH-0031",
        "domain_code": "PETH",
        "subdomain": "Supervision Ethics",
        "difficulty_level": 2,
        "encounter": {
            "setting": "University training clinic — supervision meeting room",
            "referral_context": "Practicum student requests urgent meeting with clinical supervisor after discovering supervisee-client boundary issue during case review.",
            "patient": {
                "label": "Practicum Student (Supervisee), 27",
                "appearance_tags": ["anxious demeanor", "fidgeting with papers", "avoids direct answers initially"],
                "initial_avatar_state": "anxious"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "I need to tell you something. One of my clients — the college student with depression — I ran into her at a party last weekend. We ended up talking for a while. She asked for my personal number and I... I gave it to her. She's texted me twice since then about non-therapy things. I know I shouldn't have but she seemed so lonely.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["boundary crossing disclosure", "rationalizing dual relationship", "emotional reasoning", "seeking supervisor guidance"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Boundary issue", "value": "Supervisee provided personal phone number to client; engaged in social contact outside therapy"},
                        {"category": "Chief Complaint", "label": "Supervisee reasoning", "value": "Rationalized action based on client's loneliness; difficulty maintaining professional boundaries"},
                        {"category": "Chief Complaint", "label": "Timeline", "value": "Social contact began 5 days ago; 2 non-therapy text exchanges since"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Supervision Context",
                    "dialogue": "She's my age and we have a lot in common. I felt like I could really help her as a friend too. I know the ethics code says something about dual relationships but this doesn't feel exploitative. I genuinely care about her wellbeing. And she's doing so much better in therapy — I don't want to disrupt that.",
                    "avatar_emotion": "guarded",
                    "behavioral_tags": ["identification with client", "minimization of ethical violation", "blurred role boundaries", "therapeutic progress concern"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Dual relationship", "value": "Developing social relationship with current therapy client; supervisee and client are age-peers"},
                        {"category": "History of Present Illness", "label": "Ethical awareness", "value": "Supervisee aware of APA Ethics Code but rationalizes exception; difficulty applying general principle to specific case"},
                        {"category": "History of Present Illness", "label": "Transference/countertransference", "value": "Likely countertransference — over-identification with client based on shared demographics and life circumstances"},
                        {"category": "History of Present Illness", "label": "Client vulnerability", "value": "Client is in treatment for depression, inherently a vulnerable position; power differential present regardless of age similarity"}
                    ],
                    "clinician_prompt": "Help me understand what led to the decision to share your personal number."
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Ethical Analysis Discussion",
                    "dialogue": "I guess I didn't think of it as a big deal in the moment. But now I'm worried — could I get in trouble? Could this hurt her? I was reading Standard 3.05 and I see the point about multiple relationships impairing objectivity. I just... I wanted to be there for her.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["emerging ethical awareness", "anxiety about consequences", "beginning to recognize client harm potential"],
                    "chart_reveals": [
                        {"category": "Ethical Analysis", "label": "APA Standard 3.05", "value": "Multiple Relationships — psychologists refrain from entering relationships that could impair objectivity or risk exploitation"},
                        {"category": "Ethical Analysis", "label": "Impairment risk", "value": "Social relationship compromises clinical objectivity, blurs therapeutic frame, and may impair supervisee's professional judgment"},
                        {"category": "Ethical Analysis", "label": "Client risk", "value": "Client may experience confusion about role boundaries; therapeutic gains may be compromised; termination becomes more complex"},
                        {"category": "Ethical Analysis", "label": "Supervisor responsibility", "value": "APA 7.06 — Supervisors must monitor supervisees' competence and ethical conduct; must take action when boundary violations occur"}
                    ],
                    "clinician_prompt": "What do you think the impact on your client could be?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Remediation Planning",
                    "dialogue": "I want to fix this. I don't want to hurt her or my training. Should I just stop texting her? Do I need to tell her what happened? I'm afraid if I bring it up in session it'll damage the relationship. And honestly, I'm embarrassed. I feel like I should have known better.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["remediation motivation", "shame", "avoidance of direct conversation with client", "professional development need"],
                    "chart_reveals": [
                        {"category": "Remediation", "label": "Immediate steps", "value": "Cease personal contact; discuss boundary reset in therapy session with supervisor guidance; process in supervision"},
                        {"category": "Remediation", "label": "Supervisory actions", "value": "Increase supervision frequency; monitor countertransference; consider whether transfer of client is needed"},
                        {"category": "Remediation", "label": "Documentation", "value": "Supervisor must document boundary issue, remediation plan, and supervisee's response in supervision notes"},
                        {"category": "Remediation", "label": "Developmental framing", "value": "Boundary violations in trainees are opportunities for professional growth when addressed transparently in supervision"}
                    ],
                    "clinician_prompt": "Let's think together about the steps we need to take. What feels most urgent?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "primary_diagnosis",
                "prompt": "Which APA Ethics Code standard is MOST directly relevant to this supervisee's boundary violation?",
                "options": {
                    "A": "Standard 2.01 — Boundaries of Competence",
                    "B": "Standard 3.05 — Multiple Relationships",
                    "C": "Standard 10.05 — Sexual Intimacies With Current Therapy Clients",
                    "D": "Standard 4.01 — Maintaining Confidentiality"
                },
                "correct_answer": "B",
                "explanation": "APA Ethics Code Standard 3.05 (Multiple Relationships) is most directly applicable. A multiple relationship occurs when a psychologist is in a professional role with a person AND also in another role with that person (social). The standard states psychologists shall refrain from entering multiple relationships if they could reasonably be expected to impair objectivity, competence, or effectiveness, or risk exploitation or harm. Giving a personal number and engaging in social texting with a current therapy client creates a multiple relationship that risks impairing clinical objectivity.",
                "distractor_rationale": {
                    "A": "Standard 2.01 addresses practicing within one's competence. While the supervisee's judgment was poor, the core issue is the dual relationship, not a competence boundary per se.",
                    "C": "Standard 10.05 addresses sexual intimacies. There is no indication of sexual contact or romantic intent — this is a social boundary crossing, not a sexual violation.",
                    "D": "Standard 4.01 addresses confidentiality. While social contact creates confidentiality risks, the primary ethical violation here is the multiple relationship itself."
                }
            },
            {
                "question_id": "q2",
                "type": "immediate_intervention",
                "prompt": "As the clinical supervisor, what is the MOST appropriate immediate response to this disclosure?",
                "options": {
                    "A": "Terminate the supervisee from the practicum immediately as the violation is irreparable",
                    "B": "Document the boundary issue, develop a remediation plan, increase supervision, and address the therapeutic frame with the client",
                    "C": "Advise the supervisee to maintain the friendship since ending it abruptly would harm the client",
                    "D": "Report the supervisee to the state licensing board for an ethics violation"
                },
                "correct_answer": "B",
                "explanation": "The supervisor's responsibility (APA 7.06) is to monitor supervisee conduct and take corrective action. For a trainee boundary crossing (as opposed to a boundary violation with exploitative intent), the appropriate response is developmental: document the issue, create a structured remediation plan, increase supervision intensity, and guide the supervisee in addressing the therapeutic frame with the client. The goal is professional development, not punishment, when the trainee shows insight, discloses voluntarily, and demonstrates capacity for growth.",
                "distractor_rationale": {
                    "A": "Immediate termination is disproportionate for a trainee's first boundary crossing, particularly one disclosed voluntarily. Ethical training involves helping trainees learn from mistakes. Termination would be considered for repeated violations, exploitation, or refusal to remediate.",
                    "C": "Maintaining the social relationship would perpetuate the ethics violation. The dual relationship must be addressed, not accommodated. The therapeutic frame must be restored.",
                    "D": "Reporting to the licensing board is premature for a trainee who is not yet licensed and who voluntarily disclosed the issue. Supervision is the appropriate corrective mechanism at this training stage."
                }
            }
        ]
    },
    # --- Supervision Ethics #2 ---
    {
        "id": "CP-PETH-0032",
        "domain_code": "PETH",
        "subdomain": "Supervision Ethics",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Community mental health center — supervisor's office",
            "referral_context": "Licensed psychologist supervisor becomes aware that a post-doctoral supervisee has been providing therapy services outside their competence area without consultation.",
            "patient": {
                "label": "Post-Doctoral Supervisee, 30",
                "appearance_tags": ["defensive posture", "arms crossed", "direct eye contact", "controlled voice"],
                "initial_avatar_state": "guarded"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "I don't understand why this is an issue. A client was assigned to me with an eating disorder. I've done the reading. I've watched training videos. I'm not going to turn away someone who needs help just because it wasn't specifically in my doctoral program.",
                    "avatar_emotion": "angry",
                    "behavioral_tags": ["defensiveness", "minimization of competence gap", "rationalization", "resistance to supervisory feedback"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Issue", "value": "Supervisee treating eating disorder patient without training, experience, or supervisory approval in this specialty area"},
                        {"category": "Chief Complaint", "label": "Supervisee position", "value": "Believes self-study (reading, videos) constitutes sufficient preparation; resists competence boundary"},
                        {"category": "Chief Complaint", "label": "Discovery", "value": "Supervisor discovered during chart review — supervisee had not brought case to supervision for 6 weeks"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Supervision History",
                    "dialogue": "I've been treating her for 6 weeks. She's doing fine — she gained 3 pounds. I'm using CBT which I AM trained in. I just applied it to the eating disorder. I didn't bring it to supervision because I knew you'd tell me to transfer her, and she's already built rapport with me. Transferring would be harmful.",
                    "avatar_emotion": "guarded",
                    "behavioral_tags": ["concealment from supervisor", "overconfidence", "client welfare rationalization", "boundary of competence violation"],
                    "chart_reveals": [
                        {"category": "History", "label": "Concealment", "value": "Deliberately withheld case from supervision for 6 weeks to avoid transfer recommendation"},
                        {"category": "History", "label": "Treatment approach", "value": "Applying general CBT to ED without specialized training (CBT-E, FBT, or other ED-specific protocols)"},
                        {"category": "History", "label": "Competence gap", "value": "No coursework, practicum, or supervised experience in eating disorders; no ED-specific training whatsoever"},
                        {"category": "History", "label": "Client risk", "value": "Eating disorders have highest mortality rate of any psychiatric condition; inadequate treatment carries medical risk"}
                    ],
                    "clinician_prompt": "Help me understand why you chose not to bring this case to our supervision sessions."
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Ethical and Competence Assessment",
                    "dialogue": "Fine. Maybe I should have told you. But I was trying to help. Every other therapist in this clinic has a 3-month waitlist. What was supposed to happen to her? And honestly, I resent the implication that I'm incompetent. I'm a good therapist.",
                    "avatar_emotion": "angry",
                    "behavioral_tags": ["systemic barrier rationalization", "ego defensiveness", "conflating general competence with specialty competence"],
                    "chart_reveals": [
                        {"category": "Ethical Analysis", "label": "APA 2.01a", "value": "Psychologists provide services only within the boundaries of their competence based on education, training, supervised experience, or professional experience"},
                        {"category": "Ethical Analysis", "label": "APA 2.01b", "value": "When services are needed in areas lacking competence, psychologists obtain training, supervision, or consultation — or refer"},
                        {"category": "Ethical Analysis", "label": "Supervision violation", "value": "Concealing cases from supervisor is a serious supervisory frame violation that undermines the gatekeeping function"},
                        {"category": "Ethical Analysis", "label": "Risk assessment", "value": "ED patients require medical monitoring, nutritional expertise, and suicide risk assessment specific to ED — general CBT insufficient"}
                    ],
                    "clinician_prompt": "I hear that you felt caught between wanting to help and the system's limitations. Let's talk about what the ethics require here."
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Remediation and Gatekeeping",
                    "dialogue": "(After processing) I hear what you're saying. I didn't think of it as an ethics issue — I thought of it as a practical problem. I see now that my reading doesn't equal training. What happens to the client, though? And what happens to me?",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["beginning acceptance", "concern for consequences", "emerging insight", "focus on remediation"],
                    "chart_reveals": [
                        {"category": "Remediation", "label": "Immediate", "value": "Transfer client to ED-specialized clinician with warm handoff; medical evaluation if not current"},
                        {"category": "Remediation", "label": "Supervisory action", "value": "Formal remediation plan documenting competence boundary violation and concealment; increased supervision"},
                        {"category": "Remediation", "label": "Gatekeeping", "value": "Supervisor must evaluate whether supervisee demonstrates capacity for ethical practice; repeated concealment could warrant training program notification"},
                        {"category": "Remediation", "label": "Documentation", "value": "Incident report; remediation plan with measurable goals; timeline for completion; signed by both parties"}
                    ],
                    "clinician_prompt": "Let's talk about the path forward — for both you and your client."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "primary_diagnosis",
                "prompt": "Which ethical issue is MOST serious in this scenario?",
                "options": {
                    "A": "The supervisee's defensiveness during the supervision meeting",
                    "B": "The supervisee practicing outside their competence AND concealing cases from the supervisor",
                    "C": "The waitlist at the community mental health center",
                    "D": "The client's 3-pound weight gain suggesting inadequate treatment"
                },
                "correct_answer": "B",
                "explanation": "Two compounding ethical violations are present: (1) practicing outside competence boundaries (APA 2.01) by treating an eating disorder without training, and (2) deliberately concealing the case from the supervisor for 6 weeks, which undermines the supervisory relationship and gatekeeping function. The concealment transforms what might have been a correctable competence overreach into a more serious integrity issue (APA 5.01 — Avoidance of False or Deceptive Statements, and the supervisory frame violation). Together, these create significant risk to the client.",
                "distractor_rationale": {
                    "A": "Defensiveness is a common supervisee response and a process issue to address in supervision, but it is not itself an ethical violation.",
                    "C": "System-level access barriers are real but do not justify practicing outside one's competence. Ethical obligations exist regardless of systemic limitations.",
                    "D": "Weight gain direction (3 lbs) may appear positive but is insufficient to evaluate treatment adequacy for an ED — and the supervisee lacks the specialized knowledge to determine whether this is clinically meaningful."
                }
            },
            {
                "question_id": "q2",
                "type": "immediate_intervention",
                "prompt": "As the supervisor, which action is MOST ethically required regarding the client currently in treatment?",
                "options": {
                    "A": "Allow the supervisee to continue treating the client under closer supervision since rapport exists",
                    "B": "Transfer the client to a clinician with eating disorder competence and ensure medical stability is assessed",
                    "C": "Discharge the client from the clinic since there are no ED-competent clinicians available",
                    "D": "Continue current treatment but add a nutritional counseling referral"
                },
                "correct_answer": "B",
                "explanation": "The supervisor has an ethical and legal obligation (vicarious liability) to ensure the client receives competent care. Given that eating disorders have the highest mortality rate of any psychiatric disorder and require specialized assessment (medical monitoring, suicide risk, refeeding protocol awareness), the client must be transferred to a competent provider. A warm handoff preserves the therapeutic alliance as much as possible while ensuring appropriate care. Medical stability must be assessed given the 6-week delay in appropriate treatment.",
                "distractor_rationale": {
                    "A": "Allowing continued treatment under closer supervision is insufficient — the supervisee lacks the foundational training to provide ED-specific care, and no amount of supervision can substitute for the specialized knowledge required. This would expose the client to continued risk.",
                    "C": "Discharging the client is abandonment. The clinic has an obligation to arrange appropriate referral even if internal resources are limited.",
                    "D": "Adding nutritional counseling without transferring care leaves the unqualified supervisee as the primary therapist for a high-risk condition. This is insufficient to address the competence gap."
                }
            }
        ]
    },
    # --- Psychopharm #1: Tardive Dyskinesia ---
    {
        "id": "CP-PETH-0033",
        "domain_code": "PETH",
        "subdomain": "Psychopharmacology",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Community mental health center — psychology consultation",
            "referral_context": "Psychiatrist requests psychology consultation for a patient on long-term haloperidol who has developed involuntary facial and tongue movements.",
            "patient": {
                "label": "Adult Female, 58",
                "appearance_tags": ["involuntary lip smacking", "tongue protrusion", "grimacing", "appears embarrassed"],
                "initial_avatar_state": "distressed"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "My face won't stop moving. My tongue keeps sticking out and I can't control it. People stare at me. I've been on haloperidol for 12 years for my schizophrenia and this started about a year ago. It's getting worse. I'm afraid to leave my apartment.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["involuntary movements", "social withdrawal", "medication side effect distress", "self-consciousness"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Primary concern", "value": "Involuntary orofacial movements: lip smacking, tongue protrusion, grimacing — progressive over 12 months"},
                        {"category": "Chief Complaint", "label": "Medication history", "value": "Haloperidol 10mg daily x 12 years; no dosage changes in 5 years"},
                        {"category": "Chief Complaint", "label": "Functional impact", "value": "Social isolation due to embarrassment; avoiding public settings; difficulty eating in front of others"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Medication and Symptom History",
                    "dialogue": "The haloperidol works well for my voices — I haven't heard them in years. But nobody warned me this could happen. My psychiatrist mentioned something called AIMS and said I have 'tardive dyskinesia.' Is this permanent? Will it get worse if I stop the medication?",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["concern about permanence", "medication dilemma", "adequate psychotic symptom control", "informed consent concerns"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Diagnosis", "value": "Tardive Dyskinesia (TD) — onset after 11 years of continuous haloperidol use"},
                        {"category": "History of Present Illness", "label": "AIMS score", "value": "Abnormal Involuntary Movement Scale: moderate severity (score 14/28 orofacial items)"},
                        {"category": "History of Present Illness", "label": "Psychotic symptoms", "value": "Schizophrenia well-controlled on current regimen; no positive symptoms in 8+ years"},
                        {"category": "History of Present Illness", "label": "Risk factors for TD", "value": "Female sex, older age, long duration of typical antipsychotic use, high potency agent"}
                    ],
                    "clinician_prompt": "When did you first notice these movements, and have they changed over time?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Mental Status Examination",
                    "dialogue": "I feel like my body is betraying me. I controlled the voices but now I can't control my own face. I feel ashamed. My daughter says she doesn't notice but I know she does. I've stopped going to church, stopped having dinner with friends. What's the point if everyone is staring?",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["grief over loss of control", "shame", "social withdrawal", "depression secondary to TD"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Depressed, tearful; affect congruent; grief reaction to loss of physical autonomy"},
                        {"category": "Mental Status Examination", "label": "Movement exam", "value": "Continuous orofacial dyskinesia — lip smacking, tongue protrusion, jaw movements; no trunk or limb involvement"},
                        {"category": "Mental Status Examination", "label": "Cognition", "value": "Intact orientation, memory, and reasoning; no thought disorder; insight excellent"},
                        {"category": "Mental Status Examination", "label": "Psychosis screen", "value": "No hallucinations, delusions, or disorganized thinking currently"}
                    ],
                    "clinician_prompt": "How has this affected your daily life and relationships?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial Context and Treatment Planning",
                    "dialogue": "I live alone. My daughter visits on weekends. I used to volunteer at the food bank but I stopped. I'm worried — if they switch my medication, will the voices come back? I can't go through that again. But I also can't live like this.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["medication change anxiety", "relapse fear", "functional decline", "treatment dilemma"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Support", "value": "Daughter visits weekly; previously active in church and volunteer work; now isolated"},
                        {"category": "Psychosocial Context", "label": "Treatment dilemma", "value": "Patient fears psychotic relapse with medication change; also distressed by TD symptoms"},
                        {"category": "Treatment Planning", "label": "Options", "value": "VMAT2 inhibitors (valbenazine, deutetrabenazine) are FDA-approved for TD; switch from typical to atypical antipsychotic; gradual haloperidol taper with monitoring"},
                        {"category": "Treatment Planning", "label": "Psychology role", "value": "Address secondary depression, social isolation, coping with chronic movement disorder; psychoeducation; support through medication transition"}
                    ],
                    "clinician_prompt": "What are your biggest concerns about changing your medication?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "Tardive dyskinesia is caused by which pharmacological mechanism?",
                "options": {
                    "A": "Serotonin receptor supersensitivity from chronic SSRI use",
                    "B": "Dopamine receptor supersensitivity in the nigrostriatal pathway from chronic D2 blockade",
                    "C": "GABA depletion in the cerebellum from benzodiazepine withdrawal",
                    "D": "Norepinephrine excess in the locus coeruleus from stimulant use"
                },
                "correct_answer": "B",
                "explanation": "Tardive dyskinesia results from chronic blockade of D2 dopamine receptors in the nigrostriatal pathway (basal ganglia motor circuit). Prolonged D2 blockade leads to dopamine receptor upregulation and supersensitivity — when dopamine does reach these receptors, the response is exaggerated, producing involuntary hyperkinetic movements. Risk factors include long duration of treatment, high-potency typical antipsychotics (like haloperidol), older age, and female sex. TD may be irreversible even after medication discontinuation.",
                "distractor_rationale": {
                    "A": "SSRIs do not cause tardive dyskinesia. Serotonergic agents can cause movement side effects (serotonin syndrome, akathisia) but not the dopamine receptor supersensitivity mechanism of TD.",
                    "C": "Benzodiazepine withdrawal causes GABAergic symptoms (seizures, anxiety, tremor) but not tardive dyskinesia, which is a dopaminergic phenomenon.",
                    "D": "Stimulant-related norepinephrine effects do not produce tardive dyskinesia. Stimulants can cause motor tics but through a different mechanism."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "Which FDA-approved medication class is the first-line pharmacological treatment specifically for tardive dyskinesia?",
                "options": {
                    "A": "Anticholinergic agents (e.g., benztropine)",
                    "B": "Benzodiazepines (e.g., clonazepam)",
                    "C": "VMAT2 inhibitors (e.g., valbenazine, deutetrabenazine)",
                    "D": "Beta-blockers (e.g., propranolol)"
                },
                "correct_answer": "C",
                "explanation": "VMAT2 (vesicular monoamine transporter 2) inhibitors — valbenazine (Ingrezza) and deutetrabenazine (Austedo) — are the only FDA-approved treatments specifically for tardive dyskinesia. They work by decreasing dopamine release from presynaptic vesicles, reducing the excessive dopaminergic stimulation at supersensitive receptors. Clinical trials demonstrated significant reduction in AIMS scores compared to placebo.",
                "distractor_rationale": {
                    "A": "Anticholinergics (benztropine, trihexyphenidyl) treat acute EPS (dystonia, parkinsonism) but may actually WORSEN tardive dyskinesia by further disrupting the dopamine-acetylcholine balance in the basal ganglia.",
                    "B": "Benzodiazepines have been used off-label for symptom relief but are not FDA-approved for TD, carry dependence risk, and do not address the underlying mechanism.",
                    "D": "Beta-blockers treat akathisia (restlessness) but have no efficacy for tardive dyskinesia."
                }
            }
        ]
    },
    # --- Psychopharm #2: Neuroleptic Malignant Syndrome ---
    {
        "id": "CP-PETH-0034",
        "domain_code": "PETH",
        "subdomain": "Psychopharmacology",
        "difficulty_level": 3,
        "encounter": {
            "setting": "General hospital — psychiatry liaison consultation",
            "referral_context": "Internal medicine team requests urgent psychiatric consultation for a 35-year-old male transferred from a psychiatric facility 2 days after haloperidol initiation, presenting with high fever, rigidity, and altered mental status.",
            "patient": {
                "label": "Adult Male, 35",
                "appearance_tags": ["diaphoretic", "rigid posture", "confused", "tremulous"],
                "initial_avatar_state": "confused"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Patient is confused and minimally verbal. Nurse provides collateral) He was admitted to the psych unit 3 days ago for acute psychosis. They started haloperidol 10mg IM. Yesterday he spiked a fever of 104.2, became extremely rigid, and stopped responding coherently. His CK is over 10,000. We're concerned about NMS.",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["altered consciousness", "severe rigidity", "hyperthermia", "autonomic instability"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Presentation", "value": "High fever (104.2F), 'lead-pipe' muscle rigidity, altered mental status, diaphoresis — onset 48 hours after haloperidol initiation"},
                        {"category": "Chief Complaint", "label": "Labs", "value": "CK: 10,400 (normal <200); WBC: 14,000; metabolic panel: elevated LDH, myoglobinuria"},
                        {"category": "Chief Complaint", "label": "Vitals", "value": "T: 104.2F, HR: 128, BP: 180/110 (labile), RR: 24; autonomic instability"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Medication and Clinical History",
                    "dialogue": "(Chart review and nursing report) He was on no psychiatric medications prior to this admission. This was his first psychotic episode. Haloperidol 10mg IM was given on day 1, repeated day 2. The rigidity started yesterday afternoon. By last night he wasn't making sense. He's been on IV fluids since arrival.",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["first antipsychotic exposure", "rapid onset after high-potency typical", "medical emergency"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Medication timeline", "value": "Haloperidol 10mg IM day 1 and day 2; symptoms began ~36 hours after first dose"},
                        {"category": "History of Present Illness", "label": "Prior medications", "value": "No prior psychiatric medications — antipsychotic-naive patient"},
                        {"category": "History of Present Illness", "label": "NMS risk factors", "value": "Antipsychotic-naive; high-potency typical agent; IM route; rapid dose escalation; dehydration; agitation on admission"},
                        {"category": "History of Present Illness", "label": "Current management", "value": "IV fluids, cooling blankets, haloperidol discontinued; ICU transfer pending"}
                    ],
                    "clinician_prompt": "What medications was he started on and when did symptoms begin?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Medical and Neurological Status",
                    "dialogue": "(Patient mumbles incoherently when addressed. Cannot follow commands. Extremities rigid on passive movement — described as 'lead-pipe rigidity.' Profuse diaphoresis. Tremor noted in upper extremities. Eyes open but gaze unfocused.)",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["encephalopathy", "lead-pipe rigidity", "autonomic dysfunction", "medical emergency"],
                    "chart_reveals": [
                        {"category": "Neurological Exam", "label": "Motor", "value": "Severe generalized 'lead-pipe' rigidity — cardinal feature of NMS; distinguishes from serotonin syndrome (hyperreflexia/clonus instead)"},
                        {"category": "Neurological Exam", "label": "Mental status", "value": "Encephalopathy — confused, minimally verbal, cannot follow simple commands"},
                        {"category": "Neurological Exam", "label": "Autonomic", "value": "Diaphoresis, tachycardia (128), hypertension (180/110), hyperthermia (104.2F)"},
                        {"category": "Labs", "label": "Key findings", "value": "CK 10,400 (rhabdomyolysis risk); WBC 14,000 (leukocytosis common in NMS); myoglobinuria (renal injury risk)"}
                    ],
                    "clinician_prompt": "Can you describe the rigidity and his level of consciousness?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Treatment and Recovery Planning",
                    "dialogue": "(Patient's wife, speaking with the team) Is he going to be okay? He just went in for hearing voices and now he's in the ICU. Nobody told us this could happen. Will he ever be able to take medication for the psychosis again? We're terrified.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["family distress", "informed consent failure", "prognosis questions", "future treatment planning"],
                    "chart_reveals": [
                        {"category": "Treatment", "label": "Acute NMS management", "value": "Discontinue offending agent; aggressive hydration; cooling; dantrolene (muscle relaxant) and/or bromocriptine (dopamine agonist); ICU monitoring"},
                        {"category": "Treatment", "label": "Mortality", "value": "NMS mortality: 5-20% historically; lower with early recognition and treatment; renal failure from rhabdomyolysis is leading cause of death"},
                        {"category": "Treatment", "label": "Rechallenge", "value": "After NMS resolution (minimum 2 weeks), rechallenge with low-potency atypical antipsychotic at lowest dose with careful monitoring may be considered"},
                        {"category": "Prognosis", "label": "Recovery", "value": "Most patients recover fully within 1-2 weeks with appropriate treatment; some have residual symptoms"}
                    ],
                    "clinician_prompt": "I understand how frightening this is. Let me explain what's happening and what the treatment plan looks like."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "primary_diagnosis",
                "prompt": "Which set of findings is MOST characteristic of Neuroleptic Malignant Syndrome (NMS)?",
                "options": {
                    "A": "Hyperthermia, lead-pipe rigidity, altered mental status, autonomic instability, and elevated CK",
                    "B": "Hyperthermia, clonus, hyperreflexia, diarrhea, and mydriasis",
                    "C": "Hypothermia, flaccid paralysis, respiratory depression, and pinpoint pupils",
                    "D": "Fever, rash, lymphadenopathy, and transaminitis"
                },
                "correct_answer": "A",
                "explanation": "The classic tetrad of NMS is: (1) hyperthermia (often >104F), (2) severe muscular rigidity ('lead-pipe'), (3) altered mental status (confusion to coma), and (4) autonomic instability (tachycardia, labile BP, diaphoresis). Elevated creatine kinase (CK) from muscle breakdown (rhabdomyolysis) is a characteristic lab finding. NMS is caused by sudden dopamine D2 receptor blockade, most commonly from high-potency typical antipsychotics, and is a medical emergency with 5-20% mortality.",
                "distractor_rationale": {
                    "B": "This describes Serotonin Syndrome — which features clonus, hyperreflexia, diarrhea, and mydriasis. The key distinguishing feature: NMS has lead-pipe rigidity; serotonin syndrome has clonus and hyperreflexia. NMS has 'lead-pipe'; SS has 'clonus.'",
                    "C": "This describes opioid overdose — hypothermia, flaccid muscles, respiratory depression, and pinpoint pupils are classic. NMS features hyperthermia and rigidity, the opposite pattern.",
                    "D": "This describes Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS) or other drug hypersensitivity — a different type of medication adverse reaction."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "Which pharmacological intervention is MOST appropriate for acute NMS management?",
                "options": {
                    "A": "Increase haloperidol dose to address underlying psychosis",
                    "B": "Dantrolene for muscle rigidity and/or bromocriptine as a dopamine agonist",
                    "C": "Cyproheptadine as a serotonin antagonist",
                    "D": "Lorazepam for sedation and symptom control as the sole treatment"
                },
                "correct_answer": "B",
                "explanation": "Acute NMS management includes immediately discontinuing the offending antipsychotic plus specific pharmacotherapy: dantrolene sodium (a direct-acting skeletal muscle relaxant that reduces rigidity and hyperthermia by blocking calcium release from the sarcoplasmic reticulum) and/or bromocriptine (a dopamine agonist that counteracts the D2 blockade causing NMS). Aggressive IV hydration and cooling measures are essential supportive care. ICU monitoring is required.",
                "distractor_rationale": {
                    "A": "Increasing the offending agent would worsen NMS and could be fatal. The antipsychotic MUST be immediately discontinued — it is the causative agent.",
                    "C": "Cyproheptadine is the specific antidote for serotonin syndrome, not NMS. NMS is a dopaminergic crisis, not a serotonergic one.",
                    "D": "While benzodiazepines may be used adjunctively (particularly for agitation or mild cases), lorazepam alone is insufficient for moderate-to-severe NMS with CK >10,000 and hyperthermia. Specific treatment (dantrolene/bromocriptine) is required."
                }
            }
        ]
    },
    # --- Psychopharm #3: Serotonin Syndrome ---
    {
        "id": "CP-PETH-0035",
        "domain_code": "PETH",
        "subdomain": "Psychopharmacology",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Emergency department — psychiatric consultation",
            "referral_context": "ED physician requests psychiatric consultation for a 42-year-old woman brought in by husband after sudden onset of agitation, tremor, and diarrhea. Patient recently started a new antidepressant while still taking another serotonergic medication.",
            "patient": {
                "label": "Adult Female, 42",
                "appearance_tags": ["agitated", "diaphoretic", "tremulous", "dilated pupils"],
                "initial_avatar_state": "anxious"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Patient is agitated and restless, speaking rapidly) I feel like I'm jumping out of my skin. My heart is racing. I can't stop shaking. Everything started a few hours after I took my new medication. My husband says I'm not making sense but I feel like I'm thinking too fast.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["agitation", "tremor", "tachycardia", "confusion", "rapid speech"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Presentation", "value": "Acute agitation, tremor, diaphoresis, diarrhea, and mental status changes — onset hours after new medication"},
                        {"category": "Chief Complaint", "label": "Vitals", "value": "T: 101.8F, HR: 118, BP: 155/95, RR: 22; pupils dilated bilaterally"},
                        {"category": "Chief Complaint", "label": "Medication change", "value": "Started tramadol 50mg for back pain 6 hours ago; already taking fluoxetine 40mg and trazodone 100mg"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Medication History",
                    "dialogue": "(Husband provides history) She's been on Prozac for years — 40mg. She also takes trazodone for sleep. Her primary care doctor gave her tramadol yesterday for a back injury. She took her first dose this morning with her Prozac. Within a few hours she was pacing, sweating, and having diarrhea. She normally never acts like this.",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["polypharmacy serotonergic", "temporal medication correlation", "collateral confirms acute change"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Serotonergic medications", "value": "Fluoxetine (SSRI) + trazodone (SARI/5-HT antagonist-reuptake inhibitor) + tramadol (opioid with serotonin reuptake inhibition)"},
                        {"category": "History of Present Illness", "label": "Mechanism", "value": "Triple serotonergic combination; fluoxetine also inhibits CYP2D6, reducing tramadol metabolism and increasing serotonergic load"},
                        {"category": "History of Present Illness", "label": "Timeline", "value": "Symptom onset ~4-6 hours after adding tramadol to existing SSRI regimen"},
                        {"category": "History of Present Illness", "label": "Baseline", "value": "No prior psychiatric emergency; stable on fluoxetine + trazodone for 2 years"}
                    ],
                    "clinician_prompt": "Can you tell me exactly which medications she takes and when the new one was added?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Neurological and Mental Status",
                    "dialogue": "(On examination, patient is restless, cannot sit still. Lower extremity clonus elicited bilaterally. Hyperreflexia noted throughout. Patient oriented to person but confused about date and location. Bowel sounds hyperactive. Skin warm and diaphoretic.)",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["clonus", "hyperreflexia", "agitation", "GI hyperactivity", "neuromuscular excitability"],
                    "chart_reveals": [
                        {"category": "Neurological Exam", "label": "Key finding: Clonus", "value": "Bilateral lower extremity clonus — hallmark of serotonin syndrome; ABSENT in NMS (which has rigidity instead)"},
                        {"category": "Neurological Exam", "label": "Reflexes", "value": "Hyperreflexia throughout — another distinguishing feature from NMS (normal/decreased reflexes)"},
                        {"category": "Mental Status Examination", "label": "Cognition", "value": "Agitated delirium; oriented to person only; pressured but coherent speech"},
                        {"category": "Physical Exam", "label": "GI/Autonomic", "value": "Hyperactive bowel sounds, diarrhea, diaphoresis, mydriasis, tachycardia — all serotonergic features"}
                    ],
                    "clinician_prompt": "I'm going to check your reflexes and do a brief neurological exam."
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Treatment and Education",
                    "dialogue": "(After initial stabilization, patient is calmer) I had no idea tramadol could interact with my Prozac. The urgent care doctor didn't even ask what other medications I was on. Will this happen again? I still need something for my back pain.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["prescriber communication failure", "medication reconciliation gap", "patient education need"],
                    "chart_reveals": [
                        {"category": "Treatment", "label": "Acute management", "value": "Discontinue tramadol; supportive care; benzodiazepines for agitation; cyproheptadine (serotonin antagonist) if severe"},
                        {"category": "Treatment", "label": "Prognosis", "value": "Serotonin syndrome typically resolves within 24-72 hours after removal of offending agent; mortality rare with treatment"},
                        {"category": "Education", "label": "Prevention", "value": "Avoid combining serotonergic agents; common culprits: SSRIs + MAOIs, SSRIs + tramadol, SSRIs + St. John's Wort, SSRIs + triptans"},
                        {"category": "Education", "label": "Communication", "value": "Emphasize importance of complete medication lists with all prescribers; pharmacist medication reconciliation recommended"}
                    ],
                    "clinician_prompt": "Let me explain what happened and how we can prevent this in the future."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "differential_diagnosis",
                "prompt": "Which clinical finding BEST distinguishes serotonin syndrome from neuroleptic malignant syndrome?",
                "options": {
                    "A": "Presence of hyperthermia",
                    "B": "Clonus and hyperreflexia (serotonin syndrome) versus lead-pipe rigidity (NMS)",
                    "C": "Elevated white blood cell count",
                    "D": "Altered mental status"
                },
                "correct_answer": "B",
                "explanation": "The key distinguishing neuromuscular feature is: serotonin syndrome presents with clonus (rhythmic involuntary muscle contractions, especially in lower extremities) and hyperreflexia, while NMS presents with lead-pipe rigidity and normal-to-decreased reflexes. Both conditions share hyperthermia, altered mental status, and autonomic instability, making these features non-specific. The neuromuscular examination is the most reliable differentiator. Additional distinguishing features: serotonin syndrome has rapid onset (hours) and diarrhea/hyperactive bowel sounds; NMS has slower onset (days) and normal-to-decreased bowel sounds.",
                "distractor_rationale": {
                    "A": "Both serotonin syndrome and NMS can cause hyperthermia — this finding does not distinguish between them.",
                    "C": "Leukocytosis can occur in both conditions and is non-specific.",
                    "D": "Altered mental status is present in both conditions and does not help differentiate them."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "Which medication is the specific pharmacological treatment for moderate-to-severe serotonin syndrome?",
                "options": {
                    "A": "Dantrolene",
                    "B": "Bromocriptine",
                    "C": "Cyproheptadine",
                    "D": "Naloxone"
                },
                "correct_answer": "C",
                "explanation": "Cyproheptadine is the specific antidote for serotonin syndrome. It is a nonspecific serotonin receptor antagonist (5-HT1A and 5-HT2A) that directly counteracts the excess serotonergic activity causing the syndrome. It is administered orally (12mg initial dose, then 2mg every 2 hours as needed). Combined with discontinuation of the offending agent, benzodiazepines for agitation, and supportive care, cyproheptadine addresses the underlying mechanism.",
                "distractor_rationale": {
                    "A": "Dantrolene is used for NMS (and malignant hyperthermia) — it reduces muscle rigidity by blocking calcium release. It does not address serotonergic excess.",
                    "B": "Bromocriptine is a dopamine agonist used in NMS to counteract dopamine blockade. Serotonin syndrome involves serotonin excess, not dopamine deficiency.",
                    "D": "Naloxone reverses opioid overdose. While tramadol has opioid properties, the serotonin syndrome component requires serotonin-targeted treatment, not opioid reversal."
                }
            }
        ]
    },
    # --- Psychopharm #4: SSRI-Triggered Manic Episode ---
    {
        "id": "CP-PETH-0036",
        "domain_code": "PETH",
        "subdomain": "Psychopharmacology",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Outpatient psychiatry — urgent follow-up visit",
            "referral_context": "Patient's wife calls requesting urgent appointment. Patient started sertraline 50mg for depression 2 weeks ago. Wife reports dramatic behavioral changes: decreased sleep, excessive spending, grandiose statements.",
            "patient": {
                "label": "Adult Male, 28",
                "appearance_tags": ["brightly dressed", "rapid speech", "elevated energy", "difficulty sitting still"],
                "initial_avatar_state": "hopeful"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "I feel INCREDIBLE. I haven't felt this good in years. I don't know why my wife made this appointment — I'm finally better! I've been sleeping maybe 3 hours a night but I have so much energy. I started a new business this week. I've got plans. Big plans.",
                    "avatar_emotion": "hopeful",
                    "behavioral_tags": ["euphoria", "decreased sleep", "grandiosity", "pressured speech", "increased goal-directed activity", "poor insight"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Presentation", "value": "Euphoric mood, decreased sleep (3 hrs/night x 5 days), grandiose plans, pressured speech — onset 10 days after sertraline initiation"},
                        {"category": "Chief Complaint", "label": "Patient perception", "value": "Believes he is 'finally better'; no recognition of manic symptoms; denies need for concern"},
                        {"category": "Chief Complaint", "label": "Collateral", "value": "Wife reports personality change, reckless spending ($8,000 in 4 days), hypersexuality, irritability when confronted"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Medication and Psychiatric History",
                    "dialogue": "The Zoloft is working perfectly — why would I stop? Before this I was in bed all day for months. Now I'm alive again. My wife doesn't understand. I bought equipment for my new business — a food truck. I've never run a restaurant but I know I'll be great at it. I also wrote a 40-page business plan in one night.",
                    "avatar_emotion": "hopeful",
                    "behavioral_tags": ["grandiose business plan", "reckless financial decisions", "flight of ideas", "impaired judgment", "poor insight into impairment"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Medication timeline", "value": "Sertraline 50mg started 14 days ago for MDD; mood elevation began day 10; no prior antidepressant trials"},
                        {"category": "History of Present Illness", "label": "Manic symptoms", "value": "Decreased sleep, grandiosity, pressured speech, increased goal-directed activity, reckless spending, possible hypersexuality"},
                        {"category": "History of Present Illness", "label": "Duration", "value": "Symptoms present for at least 4 days at current intensity — meets duration criterion for manic episode"},
                        {"category": "History of Present Illness", "label": "Family history", "value": "Mother with Bipolar I (diagnosed age 30, lithium-responsive); maternal grandfather with 'manic depression'"}
                    ],
                    "clinician_prompt": "Tell me more about what the last two weeks have been like since starting the medication."
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Mental Status Examination",
                    "dialogue": "You know, I think I could help other patients here. I've always been good with people. Maybe I should go to medical school — I could probably finish in half the time. (Stands, paces room) I can't sit still. My mind is going a million miles an hour. Ideas just keep coming. This is what GENIUS feels like.",
                    "avatar_emotion": "hopeful",
                    "behavioral_tags": ["grandiosity", "psychomotor agitation", "flight of ideas", "poor insight", "pressured speech"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Mood: 'incredible'; Affect: euphoric, expansive, labile (irritable when challenged); incongruent with situation"},
                        {"category": "Mental Status Examination", "label": "Thought process", "value": "Flight of ideas; tangential; pressured speech; racing thoughts endorsed"},
                        {"category": "Mental Status Examination", "label": "Thought content", "value": "Grandiose ideation (genius, medical school); no psychotic features; no SI/HI"},
                        {"category": "Mental Status Examination", "label": "Insight/Judgment", "value": "Insight: absent — attributes mania to recovery; Judgment: severely impaired — $8K spending, impulsive business venture"}
                    ],
                    "clinician_prompt": "How much sleep have you been getting, and how does your thinking feel right now?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial and Treatment Planning",
                    "dialogue": "(Wife speaking privately to clinician) This is NOT him. He was depressed for 6 months, barely functioning. Now he's the opposite extreme. His mother was bipolar — could this be that? He spent our savings. He's talking about quitting his job. He doesn't think anything is wrong. What do we do?",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["spouse distress", "family history recognition", "financial harm", "occupational risk", "treatment urgency"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Functional impact", "value": "Depleted savings; may quit stable job; marital conflict; wife considering temporary separation for safety"},
                        {"category": "Treatment Planning", "label": "Immediate", "value": "Discontinue sertraline; initiate mood stabilizer (lithium or valproate); assess for inpatient if refuses treatment"},
                        {"category": "Treatment Planning", "label": "Diagnostic revision", "value": "SSRI-triggered manic episode with family history → reclassify from MDD to Bipolar I Disorder per DSM-5-TR"},
                        {"category": "Treatment Planning", "label": "Education", "value": "Antidepressant monotherapy is contraindicated in Bipolar I; future treatment requires mood stabilizer with or without antidepressant"}
                    ],
                    "clinician_prompt": "Has anyone in his family had similar episodes?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "primary_diagnosis",
                "prompt": "Based on this presentation, what is the MOST appropriate diagnostic revision?",
                "options": {
                    "A": "Major Depressive Disorder with treatment response — continue SSRI",
                    "B": "Bipolar I Disorder, Current Episode Manic — SSRI-triggered mood switch",
                    "C": "Substance/Medication-Induced Bipolar Disorder — will resolve when SSRI stopped",
                    "D": "ADHD with hyperactivity — stimulant trial warranted"
                },
                "correct_answer": "B",
                "explanation": "Per DSM-5-TR, a full manic episode that emerges during antidepressant treatment AND persists beyond the physiological effect of the medication is diagnosed as Bipolar I Disorder — not merely a medication side effect. This patient has a full manic syndrome (7+ days of elevated mood with 4+ manic symptoms: decreased sleep, grandiosity, pressured speech, flight of ideas, increased goal-directed activity, reckless behavior) plus a strong family history of bipolar disorder. The SSRI 'unmasked' a bipolar diathesis. The diagnosis should be revised from MDD to Bipolar I.",
                "distractor_rationale": {
                    "A": "This is not a treatment response — this is a manic episode. MDD treatment response involves mood normalization, not mood reversal into mania. Continuing the SSRI would be dangerous.",
                    "C": "DSM-5-TR clarifies: if the manic episode meets full criteria and persists, it counts as Bipolar I even if triggered by an antidepressant. 'Substance-induced' is reserved for cases that are clearly limited to the pharmacological effect.",
                    "D": "While psychomotor agitation and distractibility overlap with ADHD, the acute onset, euphoric mood, grandiosity, decreased need for sleep, and temporal correlation with SSRI initiation are diagnostic of mania, not ADHD."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "What is the MOST appropriate pharmacological management for this patient?",
                "options": {
                    "A": "Increase sertraline to 100mg to fully treat the depression",
                    "B": "Discontinue sertraline and start a mood stabilizer (lithium or valproate)",
                    "C": "Add a benzodiazepine for agitation while continuing sertraline",
                    "D": "Switch to a different SSRI (e.g., fluoxetine) that is less likely to cause mania"
                },
                "correct_answer": "B",
                "explanation": "Antidepressant monotherapy must be immediately discontinued in the context of a manic episode. The first-line pharmacological treatment for acute mania is a mood stabilizer (lithium or valproate) or an atypical antipsychotic (e.g., quetiapine, olanzapine). Given this patient's strong family history of lithium-responsive bipolar disorder (mother), lithium would be a particularly rational choice. Antidepressant monotherapy is contraindicated in Bipolar I as it can trigger or worsen mania.",
                "distractor_rationale": {
                    "A": "Increasing the SSRI would worsen mania. Antidepressant dose escalation in a manic patient is contraindicated and potentially dangerous.",
                    "C": "Adding a benzodiazepine addresses agitation symptomatically but does not treat mania. Continuing the sertraline would maintain the serotonergic drive fueling the manic episode.",
                    "D": "All SSRIs carry risk of manic switching in bipolar patients. The class effect is the issue, not the specific agent. No SSRI should be used as monotherapy in Bipolar I."
                }
            }
        ]
    },
    # --- Psychopharm #5: Lithium Toxicity ---
    {
        "id": "CP-PETH-0037",
        "domain_code": "PETH",
        "subdomain": "Psychopharmacology",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Emergency department — medical/psychiatric",
            "referral_context": "Brought by family to ED with vomiting, coarse tremor, and confusion. Patient is on lithium 1200mg daily for Bipolar I. Family reports patient had a GI illness with diarrhea and vomiting for 3 days and was unable to keep fluids down.",
            "patient": {
                "label": "Adult Male, 52",
                "appearance_tags": ["coarse tremor", "ataxic gait", "confused", "nauseated appearance"],
                "initial_avatar_state": "confused"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Patient is confused, speech slurred) I've been so sick... throwing up for days. Everything is spinning. My hands won't stop shaking. I can barely walk straight. I forgot to check... my levels. I think something's wrong with my lithium.",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["coarse tremor", "ataxia", "slurred speech", "nausea/vomiting", "partial insight"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Presentation", "value": "Coarse tremor, ataxia, slurred speech, nausea/vomiting, confusion in setting of lithium use and dehydration"},
                        {"category": "Chief Complaint", "label": "Lithium level", "value": "STAT lithium level: 2.4 mEq/L (therapeutic range: 0.6-1.2 mEq/L; toxic >1.5)"},
                        {"category": "Chief Complaint", "label": "Context", "value": "3-day GI illness → dehydration → decreased renal clearance of lithium → accumulation"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Medication and Medical History",
                    "dialogue": "(Son provides history) He's been on lithium for 20 years. He's usually religious about his blood draws. He caught a stomach bug and has been vomiting and having diarrhea for 3 days. He kept taking his lithium because he was afraid to miss doses. He barely drank any water. His last lithium level was 0.9 three months ago.",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["medication adherence despite illness", "dehydration", "renal lithium accumulation", "caregiver providing history"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Lithium history", "value": "Lithium 1200mg/day x 20 years; last level 0.9 mEq/L (3 months ago); well-controlled Bipolar I"},
                        {"category": "History of Present Illness", "label": "Precipitant", "value": "Viral gastroenteritis → dehydration → sodium depletion → decreased renal lithium clearance → toxicity"},
                        {"category": "History of Present Illness", "label": "Mechanism", "value": "Lithium is renally excreted; reabsorbed in proximal tubule competing with sodium. Dehydration/sodium loss → increased lithium reabsorption → elevated levels"},
                        {"category": "History of Present Illness", "label": "Comorbidities", "value": "Hypertension (lisinopril 10mg); hypothyroidism (likely lithium-induced, on levothyroxine)"}
                    ],
                    "clinician_prompt": "Did he continue taking his lithium during the illness? How much fluid has he been able to drink?"
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Medical and Neurological Exam",
                    "dialogue": "(Patient increasingly confused, responds to name but cannot answer questions coherently. Coarse tremor visible at rest and with movement. Gait severely ataxic — unable to walk unassisted. Deep tendon reflexes hyperactive. No seizure activity observed.)",
                    "avatar_emotion": "confused",
                    "behavioral_tags": ["worsening encephalopathy", "coarse tremor", "severe ataxia", "hyperreflexia"],
                    "chart_reveals": [
                        {"category": "Neurological Exam", "label": "Tremor", "value": "Coarse, irregular tremor at rest and with intention — distinct from fine lithium tremor at therapeutic doses"},
                        {"category": "Neurological Exam", "label": "Gait/Coordination", "value": "Severe cerebellar ataxia — cannot walk unassisted; past-pointing on finger-to-nose"},
                        {"category": "Neurological Exam", "label": "Mental status", "value": "Encephalopathy — confusion, disorientation, slurred speech; GCS 12"},
                        {"category": "Labs", "label": "Critical values", "value": "Lithium: 2.4 mEq/L; BUN: 38; Creatinine: 1.8 (elevated — renal impairment); Na: 131 (hyponatremia); K: 3.2 (low)"}
                    ],
                    "clinician_prompt": "We need to check his coordination and reflexes right away."
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Treatment and Prevention",
                    "dialogue": "(Son, after stabilization begins) He's been on lithium forever and this has never happened. Is this permanent? He seems to be getting worse, not better. What should he do in the future if he gets sick?",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["family education need", "prognosis concern", "prevention planning"],
                    "chart_reveals": [
                        {"category": "Treatment", "label": "Acute management", "value": "Hold lithium; aggressive IV normal saline (restores sodium/volume); monitor lithium levels q2-4h; nephrology consult; consider hemodialysis if level >2.5 or worsening despite hydration"},
                        {"category": "Treatment", "label": "Hemodialysis criteria", "value": "Indicated for lithium >2.5, renal failure, seizures, coma, or failure to improve with conservative measures"},
                        {"category": "Prevention", "label": "Sick day rules", "value": "HOLD lithium during any illness causing dehydration; increase fluid intake; check lithium level; contact prescriber immediately"},
                        {"category": "Prognosis", "label": "Recovery", "value": "Most neurological symptoms resolve with level normalization; cerebellar damage can be permanent with severe or prolonged toxicity (SILENT syndrome)"}
                    ],
                    "clinician_prompt": "Let me explain what happened and what we're doing to treat it."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "Which mechanism BEST explains why this patient developed lithium toxicity during a GI illness?",
                "options": {
                    "A": "Lithium is metabolized by the liver, and GI illness impaired hepatic function",
                    "B": "Dehydration and sodium depletion decreased renal lithium clearance, causing accumulation",
                    "C": "Vomiting directly increased lithium absorption from the GI tract",
                    "D": "The GI illness caused lithium to cross the blood-brain barrier more easily"
                },
                "correct_answer": "B",
                "explanation": "Lithium is almost entirely renally excreted (not metabolized by the liver). In the proximal renal tubule, lithium is reabsorbed in competition with sodium. When a patient becomes dehydrated and sodium-depleted (from vomiting and diarrhea), the kidneys aggressively reabsorb sodium — and lithium is reabsorbed along with it, dramatically reducing lithium clearance. This causes lithium to accumulate to toxic levels even though the patient took their usual dose. This is why 'sick day rules' (hold lithium during dehydrating illness) are essential patient education.",
                "distractor_rationale": {
                    "A": "Lithium is NOT hepatically metabolized — it is excreted unchanged by the kidneys. This is a fundamental pharmacokinetic fact for EPPP preparation.",
                    "C": "Vomiting does not increase lithium absorption. In fact, vomiting might decrease absorption of a recently taken oral dose. The mechanism is renal, not gastrointestinal.",
                    "D": "Blood-brain barrier permeability is not significantly altered by GI illness. The toxicity results from elevated serum lithium levels, not changes in CNS penetration."
                }
            },
            {
                "question_id": "q2",
                "type": "immediate_intervention",
                "prompt": "At a lithium level of 2.4 mEq/L with neurological symptoms and renal impairment, which intervention is MOST critical?",
                "options": {
                    "A": "Reduce lithium dose by 50% and recheck in one week",
                    "B": "Discontinue lithium, aggressive IV normal saline, and monitor for hemodialysis indication",
                    "C": "Administer activated charcoal to reduce lithium absorption",
                    "D": "Start a thiazide diuretic to increase renal lithium clearance"
                },
                "correct_answer": "B",
                "explanation": "At 2.4 mEq/L with neurological symptoms (encephalopathy, ataxia) and renal impairment (creatinine 1.8), lithium must be completely discontinued and aggressive IV normal saline (0.9% NaCl) initiated to restore volume, correct sodium depletion, and enhance renal lithium excretion. Hemodialysis should be considered given the level approaches 2.5, renal function is compromised, and neurological symptoms are present. Serial lithium levels every 2-4 hours guide management. This is a medical emergency.",
                "distractor_rationale": {
                    "A": "Dose reduction is grossly insufficient for a level of 2.4 with active neurological symptoms. This is a medical emergency requiring complete discontinuation and aggressive intervention.",
                    "C": "Activated charcoal does NOT bind lithium — this is a high-yield pharmacology fact. Lithium is a small monovalent cation that is not adsorbed by charcoal. Whole bowel irrigation may be used for acute lithium ingestion, but this is chronic toxicity.",
                    "D": "Thiazide diuretics INCREASE lithium levels by promoting sodium loss in the distal tubule, causing compensatory proximal reabsorption of sodium (and lithium). Thiazides are a well-known cause of lithium toxicity."
                }
            }
        ]
    },
    # --- Psychopharm #6: Benzodiazepine Dependence/Withdrawal ---
    {
        "id": "CP-PETH-0038",
        "domain_code": "PETH",
        "subdomain": "Psychopharmacology",
        "difficulty_level": 2,
        "encounter": {
            "setting": "Primary care — behavioral health integration",
            "referral_context": "PCP refers patient to embedded psychologist after patient requests early refill of alprazolam (Xanax) for the third consecutive month. Patient has been on alprazolam 1mg TID for 4 years.",
            "patient": {
                "label": "Adult Female, 45",
                "appearance_tags": ["anxious", "restless", "fidgeting", "tremor in hands"],
                "initial_avatar_state": "anxious"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "I just need my Xanax refilled early. I know it looks bad but I've been more anxious lately. I run out a few days early every month. I've been taking an extra one at night because I can't sleep. Without it, I feel terrible — shaky, nauseous, my heart races. It's the only thing that works.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["dose escalation", "early refill requests", "withdrawal symptoms when doses missed", "psychological dependence"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Presenting issue", "value": "Early refill request x 3 months; self-escalated dose from 1mg TID to approximately 4mg/day"},
                        {"category": "Chief Complaint", "label": "Withdrawal symptoms", "value": "Tremor, nausea, tachycardia, insomnia when doses delayed — consistent with physiological dependence"},
                        {"category": "Chief Complaint", "label": "Duration of use", "value": "Alprazolam 1mg TID x 4 years; originally prescribed for panic disorder"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Medication History",
                    "dialogue": "I was started on Xanax four years ago after my panic attacks. It was a lifesaver at first. But now I need more to get the same effect. If I try to skip even one dose, I feel like I'm going to die — sweating, shaking, my thoughts race. I tried to stop on my own once and had a seizure. That terrified me.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["tolerance", "withdrawal seizure history", "fear of withdrawal", "self-discontinuation attempt"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Tolerance", "value": "Progressive dose escalation over 4 years; same dose no longer provides anxiolytic effect"},
                        {"category": "History of Present Illness", "label": "Withdrawal history", "value": "Seizure during unsupervised abrupt discontinuation 6 months ago — medically dangerous"},
                        {"category": "History of Present Illness", "label": "Mechanism", "value": "Chronic benzodiazepine use → GABA-A receptor downregulation → CNS hyperexcitability when drug withdrawn"},
                        {"category": "History of Present Illness", "label": "Original diagnosis", "value": "Panic disorder — adequately treated initially; current anxiety likely interdose withdrawal, not panic recurrence"}
                    ],
                    "clinician_prompt": "Tell me about that time you tried to stop on your own."
                },
                {
                    "phase_id": "mse",
                    "phase_label": "Mental Status Examination",
                    "dialogue": "I'm not addicted — I have a medical condition that requires this medication. My doctor prescribed it. I just need a little more. But honestly, I'm scared. I can't imagine my life without it. And I can't go through withdrawal again. Is there any way to get off this safely?",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["ambivalence about dependence", "medication identity", "withdrawal fear", "readiness for change emerging"],
                    "chart_reveals": [
                        {"category": "Mental Status Examination", "label": "Mood/Affect", "value": "Mood: anxious; Affect: labile, restless; fine tremor bilateral hands"},
                        {"category": "Mental Status Examination", "label": "Thought content", "value": "Preoccupied with medication access; fears withdrawal; ambivalent about dependence label"},
                        {"category": "Mental Status Examination", "label": "Insight", "value": "Partial — recognizes escalation pattern and physical dependence; resists 'addiction' framing; amenable to 'physical dependence'"},
                        {"category": "Mental Status Examination", "label": "Cognition", "value": "Subtle cognitive slowing consistent with chronic benzodiazepine use; word-finding difficulty noted"}
                    ],
                    "clinician_prompt": "How do you see the role of Xanax in your life right now?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Taper Planning and Psychosocial Context",
                    "dialogue": "I'm a single mom with two kids. I can't afford to be sick. I work full-time. If I have another seizure, I could lose my kids. But I also know this isn't sustainable — I'm taking more and more and I'm still anxious. Can you help me get off this without it being dangerous?",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["parenting responsibilities", "employment concerns", "safety awareness", "help-seeking"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Functional demands", "value": "Single mother of two; full-time employment; cannot tolerate significant withdrawal-related impairment"},
                        {"category": "Treatment Planning", "label": "Taper protocol", "value": "Cross-taper to equivalent long-acting benzodiazepine (diazepam/chlordiazepoxide), then gradual 10-25% reduction every 1-2 weeks over months"},
                        {"category": "Treatment Planning", "label": "Adjuncts", "value": "CBT for panic disorder during taper; gabapentin or hydroxyzine for transitional anxiety; avoid abrupt discontinuation"},
                        {"category": "Treatment Planning", "label": "Safety", "value": "NEVER abrupt discontinuation — benzodiazepine withdrawal can cause seizures and death; medical supervision essential"}
                    ],
                    "clinician_prompt": "We can absolutely help you do this safely. Let me walk you through what a safe taper looks like."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "This patient's interdose symptoms (tremor, nausea, tachycardia) are BEST explained by which pharmacological mechanism?",
                "options": {
                    "A": "Serotonin depletion from chronic anxiolytic use",
                    "B": "GABA-A receptor downregulation leading to CNS hyperexcitability when benzodiazepine levels drop",
                    "C": "Dopamine receptor supersensitivity in the mesolimbic pathway",
                    "D": "Acetylcholine excess from cholinergic rebound"
                },
                "correct_answer": "B",
                "explanation": "Chronic benzodiazepine use causes neuroadaptation: GABA-A receptors downregulate (decrease in number and sensitivity) in response to continuous positive allosteric modulation. When benzodiazepine levels drop between doses, the reduced GABA-A receptor function results in inadequate inhibitory tone, producing CNS hyperexcitability — manifesting as anxiety, tremor, tachycardia, insomnia, and in severe cases, seizures. This is the same mechanism underlying alcohol withdrawal, as both substances act on GABA-A receptors.",
                "distractor_rationale": {
                    "A": "Benzodiazepines act on GABA-A receptors, not serotonergic systems. Serotonin depletion is not the mechanism of benzodiazepine withdrawal.",
                    "C": "Dopamine receptor supersensitivity is the mechanism of tardive dyskinesia from antipsychotics, not benzodiazepine withdrawal.",
                    "D": "Cholinergic rebound occurs in anticholinergic withdrawal (e.g., stopping tricyclic antidepressants abruptly). Benzodiazepine withdrawal is a GABAergic phenomenon."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "What is the SAFEST approach to discontinuing this patient's alprazolam?",
                "options": {
                    "A": "Abrupt discontinuation with close monitoring in an outpatient setting",
                    "B": "Gradual taper, often cross-tapering to a long-acting benzodiazepine, reduced by 10-25% every 1-2 weeks",
                    "C": "Switch to an SSRI immediately and stop alprazolam the same day",
                    "D": "Maintain current dose indefinitely since the patient has a legitimate anxiety disorder"
                },
                "correct_answer": "B",
                "explanation": "The evidence-based approach to benzodiazepine discontinuation after chronic use is a gradual taper. Cross-tapering to an equivalent dose of a longer-acting benzodiazepine (e.g., diazepam, which has a half-life of 20-100 hours vs. alprazolam's 6-12 hours) smooths out interdose withdrawal. The dose is then reduced by 10-25% every 1-2 weeks, with the taper slowing as doses decrease. This approach minimizes withdrawal severity and seizure risk. CBT for the underlying anxiety disorder should be initiated concurrently.",
                "distractor_rationale": {
                    "A": "Abrupt discontinuation after 4 years of high-dose benzodiazepine use is medically dangerous — this patient already had a withdrawal seizure. Benzodiazepine and alcohol withdrawal are the two substance withdrawal syndromes that can be fatal.",
                    "C": "While an SSRI may be appropriate long-term treatment for panic disorder, stopping alprazolam the same day is equivalent to abrupt discontinuation. SSRIs do not prevent benzodiazepine withdrawal seizures. The taper must be gradual.",
                    "D": "Indefinite maintenance at escalating doses is not sustainable — the patient is developing tolerance, cognitive effects, and functional impairment. Guidelines recommend reassessing long-term benzodiazepine use and attempting taper when clinically feasible."
                }
            }
        ]
    }
]

# ============================================================
# BPSY: 2 new encounters (Neurotransmitter/Psychopharmacology)
# ============================================================
BPSY_NEW = [
    {
        "id": "CP-BPSY-0031",
        "domain_code": "BPSY",
        "subdomain": "Neurotransmitter Systems / Psychopharmacology",
        "difficulty_level": 3,
        "encounter": {
            "setting": "Neuropsychology consultation clinic",
            "referral_context": "Psychiatrist requests neuropsychological consultation for a 40-year-old patient with treatment-resistant depression. Patient has failed three SSRI trials and an SNRI trial. Psychiatrist is considering ketamine/esketamine and wants cognitive baseline.",
            "patient": {
                "label": "Adult Male, 40",
                "appearance_tags": ["fatigued", "slow movements", "flat affect", "adequate grooming"],
                "initial_avatar_state": "flat_affect"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "Nothing works. I've tried four different antidepressants over three years. They either do nothing or the side effects are unbearable. My psychiatrist mentioned ketamine — something about glutamate and a different pathway. I'm skeptical but desperate.",
                    "avatar_emotion": "flat_affect",
                    "behavioral_tags": ["treatment resistance", "medication fatigue", "hopelessness about treatment", "openness to novel intervention"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Treatment history", "value": "Failed adequate trials of sertraline, fluoxetine, escitalopram (SSRIs) and venlafaxine (SNRI) — meets criteria for treatment-resistant depression (TRD)"},
                        {"category": "Chief Complaint", "label": "Current symptoms", "value": "Persistent MDD: anhedonia, fatigue, concentration impairment, hopelessness; PHQ-9 score: 22 (severe)"},
                        {"category": "Chief Complaint", "label": "Proposed treatment", "value": "Esketamine (Spravato) nasal spray — FDA-approved for TRD; works via NMDA glutamate receptor antagonism"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Neurotransmitter and Treatment History",
                    "dialogue": "My psychiatrist explained that SSRIs work on serotonin but that might not be the whole picture for me. She said there's a glutamate theory — that depression might involve too much glutamate excitotoxicity or something, and ketamine blocks those receptors. It sounds like a drug of abuse to me. Is this legitimate?",
                    "avatar_emotion": "guarded",
                    "behavioral_tags": ["monoamine hypothesis limitations awareness", "glutamate theory curiosity", "abuse potential concern", "informed patient"],
                    "chart_reveals": [
                        {"category": "History of Present Illness", "label": "Monoamine hypothesis", "value": "Standard antidepressants target monoamines (5-HT, NE, DA); 30% of MDD patients don't respond → monoamine hypothesis insufficient"},
                        {"category": "History of Present Illness", "label": "Glutamate hypothesis", "value": "Emerging evidence: glutamate system dysregulation in depression; NMDA receptor antagonism (ketamine) produces rapid antidepressant effect (hours vs. weeks)"},
                        {"category": "History of Present Illness", "label": "Mechanism", "value": "Ketamine blocks NMDA receptors → increases BDNF → enhances synaptic plasticity → rapid formation of new synaptic connections via AMPA receptor activation"},
                        {"category": "History of Present Illness", "label": "Safety profile", "value": "Esketamine: FDA-approved; REMS program required; administered in clinic with 2-hour monitoring; dissociative effects, BP elevation possible"}
                    ],
                    "clinician_prompt": "What has your psychiatrist explained about how this treatment differs from your previous medications?"
                },
                {
                    "phase_id": "neuropsych",
                    "phase_label": "Neuropsychological Baseline",
                    "dialogue": "My thinking has been terrible. I used to be sharp — I'm a software engineer. Now I can't debug code that used to be easy. My memory is shot. I read something and five minutes later it's gone. Is that the depression or the medications? Will the ketamine make my thinking worse?",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["cognitive complaints", "occupational impairment", "medication vs. depression attribution question"],
                    "chart_reveals": [
                        {"category": "Neuropsychological Context", "label": "Cognitive profile", "value": "Testing reveals: slowed processing speed, impaired working memory, reduced verbal fluency — pattern consistent with MDD cognitive symptoms"},
                        {"category": "Neuropsychological Context", "label": "Depression vs. medication effects", "value": "MDD itself causes executive dysfunction, memory impairment, and processing speed reduction; SSRIs may contribute to cognitive dulling (emotional blunting)"},
                        {"category": "Neuropsychological Context", "label": "Ketamine cognitive effects", "value": "Acute: transient dissociation, perceptual changes; Long-term therapeutic use: cognitive improvements observed as depression remits; chronic recreational use: memory impairment"},
                        {"category": "Neuropsychological Context", "label": "Baseline purpose", "value": "Establish pre-treatment cognitive profile to monitor for improvement or deterioration during esketamine treatment"}
                    ],
                    "clinician_prompt": "How has your thinking and memory changed since the depression started?"
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Psychosocial and Decision-Making Context",
                    "dialogue": "My wife is supportive but exhausted. I've been on medical leave for two months. If this doesn't work, I don't know what's left. My psychiatrist mentioned maybe TMS or even ECT down the line. I just want to feel something again. Anything.",
                    "avatar_emotion": "tearful",
                    "behavioral_tags": ["caregiver burnout", "occupational disability", "treatment as last hope", "anhedonia"],
                    "chart_reveals": [
                        {"category": "Psychosocial Context", "label": "Functioning", "value": "Medical leave x 2 months; marriage strained; social withdrawal; ADLs maintained but effortful"},
                        {"category": "Psychosocial Context", "label": "Other TRD options", "value": "rTMS (repetitive transcranial magnetic stimulation); ECT (electroconvulsive therapy — most effective for severe TRD); psilocybin (investigational)"},
                        {"category": "Psychosocial Context", "label": "Support", "value": "Supportive spouse; employer accommodating leave; health insurance covers esketamine"},
                        {"category": "Psychosocial Context", "label": "Risk assessment", "value": "Passive SI (hopelessness, 'what's the point'); no plan or intent; safety plan in place; weekly psychiatry visits"}
                    ],
                    "clinician_prompt": "What would it mean for you if this treatment helped?"
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "Ketamine's rapid antidepressant effect is primarily mediated through which neurotransmitter system?",
                "options": {
                    "A": "Serotonin — ketamine is a potent serotonin reuptake inhibitor like SSRIs but faster-acting",
                    "B": "Glutamate — ketamine blocks NMDA receptors, leading to increased BDNF and synaptic plasticity via AMPA receptor activation",
                    "C": "GABA — ketamine enhances GABAergic inhibition similar to benzodiazepines",
                    "D": "Dopamine — ketamine stimulates the mesolimbic reward pathway producing euphoria that mimics remission"
                },
                "correct_answer": "B",
                "explanation": "Ketamine is an NMDA (N-methyl-D-aspartate) glutamate receptor antagonist. Its antidepressant mechanism involves: (1) blocking NMDA receptors on GABAergic interneurons, which (2) disinhibits glutamate release onto AMPA receptors, leading to (3) activation of intracellular signaling cascades including mTOR and (4) increased BDNF (brain-derived neurotrophic factor) release, which (5) promotes rapid synaptogenesis and synaptic plasticity in the prefrontal cortex and hippocampus. This produces antidepressant effects within hours — fundamentally different from the weeks-long timeline of monoamine-based antidepressants.",
                "distractor_rationale": {
                    "A": "Ketamine does not primarily act on the serotonin system. While it may have minor serotonergic effects, its antidepressant mechanism is glutamatergic, not serotonergic.",
                    "C": "Ketamine does not enhance GABAergic transmission like benzodiazepines. It acts on glutamate (excitatory) receptors, not GABA (inhibitory) receptors.",
                    "D": "While ketamine may have secondary dopaminergic effects contributing to its abuse potential, the primary antidepressant mechanism is glutamate-mediated synaptic plasticity, not reward pathway activation."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "A patient meets criteria for treatment-resistant depression. Which treatment has the STRONGEST evidence for efficacy in TRD?",
                "options": {
                    "A": "Switching to another SSRI at maximum dose",
                    "B": "Adding a benzodiazepine for persistent anxiety symptoms",
                    "C": "Electroconvulsive therapy (ECT)",
                    "D": "Doubling the dose of the current failed SSRI"
                },
                "correct_answer": "C",
                "explanation": "ECT remains the most effective treatment for treatment-resistant depression, with response rates of 50-70% in TRD populations who have failed multiple medication trials. It works across neurotransmitter systems, promoting neuroplasticity, BDNF release, and normalization of HPA axis function. While esketamine, rTMS, and augmentation strategies (lithium, atypical antipsychotics) also have evidence for TRD, ECT has the longest track record and highest response rates for severe, treatment-resistant cases.",
                "distractor_rationale": {
                    "A": "Switching between SSRIs after multiple SSRI failures has diminishing returns. The STAR*D trial showed progressively lower remission rates with each successive switch within the same class.",
                    "B": "Benzodiazepines treat anxiety symptoms but have no antidepressant efficacy. Adding a benzodiazepine does not address TRD and carries dependence risk.",
                    "D": "If a patient has failed an adequate trial at therapeutic doses, simply increasing the dose of the same failed medication is unlikely to produce remission and increases side effect burden."
                }
            }
        ]
    },
    {
        "id": "CP-BPSY-0032",
        "domain_code": "BPSY",
        "subdomain": "Neurotransmitter Systems / Psychopharmacology",
        "difficulty_level": 2,
        "encounter": {
            "setting": "Pediatric neuropsychology clinic",
            "referral_context": "Pediatrician refers 9-year-old boy for neuropsychological evaluation prior to starting stimulant medication for ADHD. Parents want to understand how the medication works and are concerned about long-term brain effects.",
            "patient": {
                "label": "Child Male, 9",
                "appearance_tags": ["fidgeting in chair", "touching everything on desk", "interrupts frequently", "bright and engaging"],
                "initial_avatar_state": "neutral"
            },
            "phases": [
                {
                    "phase_id": "chief_complaint",
                    "phase_label": "Chief Complaint",
                    "dialogue": "(Mother speaks) His teacher says he can't sit still, doesn't finish assignments, and blurts out answers. He's smart — his testing shows above-average IQ — but his grades don't match. His pediatrician diagnosed ADHD and wants to start Adderall. We want to understand what it does to his brain before we agree.",
                    "avatar_emotion": "neutral",
                    "behavioral_tags": ["parental medication concern", "achievement-ability discrepancy", "ADHD behavioral symptoms", "informed decision-seeking"],
                    "chart_reveals": [
                        {"category": "Chief Complaint", "label": "Diagnosis", "value": "ADHD, Combined Presentation — diagnosed by pediatrician based on Vanderbilt scales (parent + teacher), clinical interview"},
                        {"category": "Chief Complaint", "label": "Proposed medication", "value": "Mixed amphetamine salts (Adderall) — stimulant medication; parents requesting psychoeducation before consent"},
                        {"category": "Chief Complaint", "label": "Cognitive profile", "value": "WISC-V: FSIQ 115; Processing Speed: 92; Working Memory: 88 — relative weaknesses consistent with ADHD"}
                    ],
                    "clinician_prompt": None
                },
                {
                    "phase_id": "history",
                    "phase_label": "Neurotransmitter Psychoeducation Context",
                    "dialogue": "(Father) I've read that Adderall is basically an amphetamine. How is that different from giving my kid speed? And I've heard it affects dopamine. Isn't dopamine for reward? Won't it make him feel high? I need to understand the neuroscience before I'm comfortable.",
                    "avatar_emotion": "guarded",
                    "behavioral_tags": ["amphetamine stigma", "dopamine mechanism questions", "informed consent", "neuroscience literacy gap"],
                    "chart_reveals": [
                        {"category": "History / Psychoeducation", "label": "ADHD neurobiology", "value": "ADHD involves hypofunction of catecholamine systems (dopamine and norepinephrine) in prefrontal cortex → impaired executive function, attention, and inhibition"},
                        {"category": "History / Psychoeducation", "label": "Stimulant mechanism", "value": "Amphetamines increase dopamine and NE in PFC by blocking reuptake (DAT/NET) and promoting vesicular release → normalizes PFC underactivity → improves attention and impulse control"},
                        {"category": "History / Psychoeducation", "label": "Therapeutic vs. recreational", "value": "At therapeutic doses in ADHD: stimulants INCREASE PFC regulation (top-down control); at recreational doses: flood mesolimbic reward pathway → euphoria and addiction"},
                        {"category": "History / Psychoeducation", "label": "Evidence", "value": "Stimulants are the most studied and most effective pharmacological treatment for ADHD; effect sizes 0.8-1.0 (large); MTA study supports medication for core ADHD symptoms"}
                    ],
                    "clinician_prompt": "Those are really important questions. Let me walk you through how this medication works in the brain."
                },
                {
                    "phase_id": "neuropsych",
                    "phase_label": "Neuropsychological Assessment",
                    "dialogue": "(During CPT-3, child makes frequent omission and commission errors; variable reaction times. On Tower of London, impulsive first moves with poor planning. On CVLT-C, poor initial learning but normal delayed recall — encoding vs. retrieval distinction.) The child says: I tried really hard but my brain keeps jumping around.",
                    "avatar_emotion": "distressed",
                    "behavioral_tags": ["sustained attention deficit", "impulsive responding", "planning difficulty", "encoding weakness with intact storage"],
                    "chart_reveals": [
                        {"category": "Neuropsychological Testing", "label": "Attention (CPT-3)", "value": "Omissions (inattention) and commissions (impulsivity) both elevated; high variability in response time — classic ADHD profile"},
                        {"category": "Neuropsychological Testing", "label": "Executive function", "value": "Tower of London: impulsive, poor planning; Trails B: slow with errors; consistent with PFC hypofunction"},
                        {"category": "Neuropsychological Testing", "label": "Memory", "value": "CVLT-C: poor initial learning trials (encoding deficit), normal delayed free recall — attention-dependent encoding problem, not storage deficit"},
                        {"category": "Neuropsychological Testing", "label": "Implications", "value": "Profile confirms PFC-mediated attentional and executive deficits; predicts likely medication responsiveness for attention/impulse control tasks"}
                    ],
                    "clinician_prompt": "You're doing a great job trying. Let's take a quick break and then do one more task."
                },
                {
                    "phase_id": "psychosocial",
                    "phase_label": "Treatment Decision-Making",
                    "dialogue": "(Mother) So if I understand correctly — his prefrontal cortex isn't getting enough dopamine, and the medication fills that gap? Will he always need it? What about his personality — will it change who he is? His creativity is the best thing about him.",
                    "avatar_emotion": "anxious",
                    "behavioral_tags": ["parental understanding emerging", "personality change fear", "long-term treatment questions", "creativity concern"],
                    "chart_reveals": [
                        {"category": "Treatment Planning", "label": "Medication trial", "value": "Recommend structured stimulant trial with baseline and follow-up behavioral ratings; start low, titrate; monitor for side effects"},
                        {"category": "Treatment Planning", "label": "Common concerns", "value": "Personality/creativity: addressed by proper dosing; Growth: monitor height/weight; Dependence: therapeutic use does not increase addiction risk (may be protective)"},
                        {"category": "Treatment Planning", "label": "Multimodal", "value": "Medication + behavioral interventions (parent training, classroom accommodations, organizational skills training) superior to medication alone long-term"},
                        {"category": "Treatment Planning", "label": "Psychology role", "value": "Neuropsychological monitoring; behavioral intervention; parent consultation; school accommodation recommendations (504 plan)"}
                    ],
                    "clinician_prompt": "Those are concerns I hear from many parents. Let me address each one."
                }
            ]
        },
        "questions": [
            {
                "question_id": "q1",
                "type": "dsm_criteria",
                "prompt": "Stimulant medications for ADHD (e.g., amphetamines, methylphenidate) primarily work by increasing which neurotransmitter(s) in which brain region?",
                "options": {
                    "A": "Serotonin in the raphe nuclei — improving mood regulation",
                    "B": "Dopamine and norepinephrine in the prefrontal cortex — enhancing executive function and attention",
                    "C": "GABA in the amygdala — reducing anxiety and hyperarousal",
                    "D": "Acetylcholine in the hippocampus — improving memory formation"
                },
                "correct_answer": "B",
                "explanation": "ADHD is characterized by hypofunction of catecholamine neurotransmission (dopamine and norepinephrine) in the prefrontal cortex (PFC). Stimulant medications increase dopamine via DAT (dopamine transporter) blockade and vesicular release, and norepinephrine via NET (norepinephrine transporter) blockade. This normalizes PFC activity, enhancing top-down executive control over attention, working memory, impulse inhibition, and planning. The therapeutic effect is frontal-cortical, not limbic-reward based at appropriate doses.",
                "distractor_rationale": {
                    "A": "Stimulants do not primarily target serotonin or the raphe nuclei. SSRIs target serotonin and are used for depression/anxiety, not ADHD.",
                    "C": "GABA-enhancing drugs (benzodiazepines) are anxiolytics and sedatives. Stimulants have the opposite mechanism — they are activating, not inhibitory. They do not act on GABAergic systems.",
                    "D": "Cholinergic enhancement in the hippocampus is the mechanism of drugs for Alzheimer's disease (e.g., donepezil). Stimulants target catecholamines in the PFC."
                }
            },
            {
                "question_id": "q2",
                "type": "treatment_planning",
                "prompt": "According to the NIMH MTA study, which treatment approach produced the BEST outcomes for core ADHD symptoms?",
                "options": {
                    "A": "Behavioral treatment alone",
                    "B": "Medication management alone (carefully titrated stimulant)",
                    "C": "Combined medication and behavioral treatment",
                    "D": "Community care (treatment as usual)"
                },
                "correct_answer": "B",
                "explanation": "The landmark MTA (Multimodal Treatment of ADHD) study found that carefully managed medication (systematic titration, monthly monitoring) was superior to behavioral treatment alone and community care for core ADHD symptoms (inattention, hyperactivity, impulsivity). Combined treatment (medication + behavioral) was NOT significantly better than medication alone for core symptoms but DID show advantages for comorbid conditions (anxiety, oppositional behavior, social skills, parent-child relationships, academic achievement). This finding supports medication as the primary treatment for core symptoms while highlighting the added value of multimodal approaches for broader functioning.",
                "distractor_rationale": {
                    "A": "Behavioral treatment alone was less effective than medication management for core ADHD symptoms in the MTA study. However, it was effective for comorbid problems and is essential for comprehensive treatment.",
                    "C": "Combined treatment was equivalent to medication alone for core symptoms but showed benefits for comorbid issues. For the specific question about 'core ADHD symptoms,' medication management alone was sufficient.",
                    "D": "Community care (treatment as usual) produced the poorest outcomes, highlighting the importance of systematic, carefully managed treatment versus routine care."
                }
            }
        ]
    }
]


# ============================================================
# MAIN EXECUTION
# ============================================================
def main():
    results = {}
    for domain, encounters in [
        ("CPAT", CPAT_NEW),
        ("PTHE", PTHE_NEW),
        ("LDEV", LDEV_NEW),
        ("PETH", PETH_NEW),
        ("BPSY", BPSY_NEW),
    ]:
        print(f"Processing {domain}: adding {len(encounters)} encounters...")
        total, added = append_encounters(domain, encounters)
        results[domain] = {"added": added, "total": total}

    print("\n=== Summary ===")
    for domain, info in results.items():
        print(f"  {domain}: +{info['added']} encounters -> {info['total']} total")

    # Verify JSON validity
    print("\n=== Verification ===")
    for domain in results:
        path = os.path.join(DATA_DIR, f"{domain}_presentations.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        actual = len(data["encounters"])
        declared = data["total_encounters"]
        status = "OK" if actual == declared else "MISMATCH"
        print(f"  {domain}: {actual} encounters, total_encounters={declared} [{status}]")

        # Check only NEW encounters have required fields
        new_ids = {e["id"] for e in [CPAT_NEW, PTHE_NEW, LDEV_NEW, PETH_NEW, BPSY_NEW]
                   for e_list in [[CPAT_NEW, PTHE_NEW, LDEV_NEW, PETH_NEW, BPSY_NEW]]
                   for e in e_list if isinstance(e, list) for e in e}
        # Simpler: collect new IDs per domain
        new_id_sets = {
            "CPAT": {e["id"] for e in CPAT_NEW},
            "PTHE": {e["id"] for e in PTHE_NEW},
            "LDEV": {e["id"] for e in LDEV_NEW},
            "PETH": {e["id"] for e in PETH_NEW},
            "BPSY": {e["id"] for e in BPSY_NEW},
        }
        for enc in data["encounters"]:
            if enc["id"] in new_id_sets.get(domain, set()):
                assert "id" in enc, f"Missing id in {domain}"
                assert "encounter" in enc, f"Missing encounter in {enc['id']}"
                assert "questions" in enc, f"Missing questions in {enc['id']}"
                assert len(enc["encounter"]["phases"]) >= 4, f"<4 phases in {enc['id']}"
                assert len(enc["questions"]) >= 2, f"<2 questions in {enc['id']}"

    print("\nAll verifications passed!")


if __name__ == "__main__":
    main()
