# Clinical Presentation Module — Complete Vision & Technical Roadmap

## Mandate

This module is the most experiential and clinically immersive tool on MasteryPage. Where other
modules test knowledge retrieval, this module simulates the actual experience of sitting across
from a patient. A test taker watches an animated patient present their symptoms, observes their
affect and behavior, reads their chart fill in progressively, and then must make clinical
judgments — diagnosis, differential, intervention priority, treatment approach — exactly as they
would in practice and on the EPPP.

Do not build a glorified vignette reader. Build a patient encounter simulator. The animation is
not decoration; it is the pedagogical mechanism. Every chunk must be executed at full fidelity.
No placeholders, no stub screens, no "future work" deferred polish. When each chunk is done, it
must be shippable.

---

## Module Identity

| Property | Value |
|---|---|
| Module name | Patient Encounter |
| Settings page | `clinical-presentation-settings.html` |
| Exercise page | `clinical-presentation-exercise.html` |
| Data generator | `generate_presentations.py` |
| Data file pattern | `data/{DOMAIN}_presentations.json` |
| Accent color | `#6366f1` (indigo) |
| Accent light | `#818cf8` |
| Accent dark | `#4f46e5` |
| Index card icon | `⚕` |
| Index card label | `IMMERSIVE` |
| Index card title | `Patient Encounter` |
| Index card desc | `Animated cases. Real clinical judgment.` |
| localStorage key prefix | `encounter_` |

---

## Architecture Overview

```
index.html
    └── Patient Encounter card → clinical-presentation-settings.html
            │
            └── Start Session → clinical-presentation-exercise.html
                    ?domains=CPAT,PTHE&levels=2,3&count=10
                    &order=shuffled&speed=normal&show_tags=1&show_chart=1

clinical-presentation-exercise.html
    ├── #screen-loading  (spinner + fetching encounters)
    ├── #screen-encounter (core animated patient encounter)
    │       ├── .patient-stage  (SVG avatar + speech bubble + tags)
    │       ├── .chart-panel    (progressive chart reveal)
    │       └── .phase-controls (advance button / auto timer)
    ├── #screen-question (question card overlay)
    │       ├── .question-prompt
    │       ├── .options-grid   (A/B/C/D cards)
    │       └── .feedback-panel (explanation + distractor rationale)
    └── #screen-results  (score ring + domain breakdown + encounter replay)

data/CPAT_presentations.json
data/PTHE_presentations.json
data/BPSY_presentations.json
data/PMET_presentations.json
data/LDEV_presentations.json
data/SOCU_presentations.json
data/WDEV_presentations.json
data/CASS_presentations.json
data/PETH_presentations.json
```

---

## Data Schema — `{DOMAIN}_presentations.json`

Every presentations file follows this top-level structure:

```json
{
  "domain_code": "CPAT",
  "domain_name": "Clinical Psychopathology",
  "generated_at": "2026-03-01T00:00:00Z",
  "version": "1.0",
  "encounters": [ ...EncounterObject[] ]
}
```

### EncounterObject

```json
{
  "id": "CP-CPAT-0001",
  "domain_code": "CPAT",
  "subdomain": "Mood Disorders",
  "difficulty_level": 2,
  "encounter": {
    "setting": "Outpatient mental health clinic",
    "referral_context": "Self-referred after urging from spouse",
    "patient": {
      "label": "Adult Female, 34",
      "appearance_tags": ["disheveled", "underweight"],
      "initial_avatar_state": "distressed"
    },
    "phases": [ ...PhaseObject[] ]
  },
  "questions": [ ...QuestionObject[] ]
}
```

### PhaseObject

Each phase represents one segment of the clinical encounter. Phases are displayed sequentially.

```json
{
  "phase_id": "chief_complaint",
  "phase_label": "Chief Complaint",
  "dialogue": "I just can't do anything anymore. I sleep all day but I'm still exhausted.",
  "avatar_emotion": "flat_affect",
  "behavioral_tags": ["psychomotor retardation", "flat affect", "poor eye contact"],
  "chart_reveals": [
    { "category": "Chief Complaint", "label": "Chief Complaint", "value": "Fatigue, inability to function" }
  ],
  "clinician_prompt": null
}
```

`avatar_emotion` must be one of the defined animation states (see Animation State Machine below).

`clinician_prompt` — optional string that shows a brief italicized therapist question/probe
before the patient's dialogue. Example: `"What brings you in today?"` Renders with a different
visual treatment (greyed, left-aligned) before the patient speech bubble.

`chart_reveals` — an array of chart line items revealed during this phase. The category groups
items in the chart panel (Chief Complaint, HPI, MSE, History, Collateral, Labs/Observations).

### QuestionObject

```json
{
  "question_id": "q1",
  "type": "primary_diagnosis",
  "prompt": "Based on this presentation, which diagnosis is most appropriate?",
  "options": {
    "A": "Persistent Depressive Disorder (Dysthymia)",
    "B": "Major Depressive Disorder, Single Episode, Moderate",
    "C": "Bipolar II Disorder, Current Episode Depressed",
    "D": "Adjustment Disorder with Depressed Mood"
  },
  "correct_answer": "B",
  "explanation": "The presentation meets full MDD criteria: depressed mood, anhedonia, hypersomnia, weight gain, fatigue, and passive SI for 4 months. Severity is moderate given functional impairment without psychosis or melancholic features.",
  "distractor_rationale": {
    "A": "Dysthymia requires ≥2 years of chronic depressed mood at a lower severity threshold.",
    "C": "No hypomanic or manic episodes are reported in the history.",
    "D": "No identifiable precipitating stressor; duration exceeds typical adjustment period."
  }
}
```

### Question Types

All questions must use one of these `type` values. The UI renders a type badge alongside the prompt.

| type | Badge label | Color |
|---|---|---|
| `primary_diagnosis` | Diagnosis | Indigo |
| `differential_diagnosis` | Differential | Blue |
| `immediate_intervention` | Urgent Care | Red |
| `treatment_planning` | Treatment | Green |
| `risk_assessment` | Risk | Orange |
| `dsm_criteria` | DSM-5-TR | Purple |
| `cultural_consideration` | Cultural | Teal |
| `assessment_tool` | Assessment | Gold |

### Allowed `avatar_emotion` Values

| Value | Visual behavior |
|---|---|
| `idle` | Default breathing, neutral expression |
| `speaking` | Jaw oscillation, slight head nod |
| `flat_affect` | Near-still, no expression animation |
| `distressed` | Head slightly bowed, slower breathing, tense posture |
| `tearful` | Tear path animation down cheeks, broken voice (typewriter pauses) |
| `anxious` | Increased fidget animation (hand/foot), faster breathing |
| `agitated` | Head micro-shakes, rapid fidget, leaning forward |
| `guarded` | Arms crossed position, averted gaze animation |
| `hopeful` | Slight upright posture, slight smile path morph |
| `confused` | Head tilt, furrowed brow |

---

## File Inventory

All files to be created from scratch:

| File | Chunk | Description |
|---|---|---|
| `generate_presentations.py` | 0 | Python script using Claude API to generate encounter data |
| `data/CPAT_presentations.json` | 0 | Generated data for Clinical Psychopathology |
| `data/PTHE_presentations.json` | 0 | Generated data for Psychological Therapeutics |
| `data/BPSY_presentations.json` | 0 | Generated data for Biological Bases of Behavior |
| `data/PMET_presentations.json` | 0 | Generated data for Psychological Measurement |
| `data/LDEV_presentations.json` | 0 | Generated data for Lifespan Development |
| `data/SOCU_presentations.json` | 0 | Generated data for Social and Cultural Bases |
| `data/WDEV_presentations.json` | 0 | Generated data for Workforce Development |
| `data/CASS_presentations.json` | 0 | Generated data for Clinical Assessment |
| `data/PETH_presentations.json` | 0 | Generated data for Psychotherapy Ethics |
| `clinical-presentation-settings.html` | 1 | Settings/configuration page |
| `clinical-presentation-exercise.html` | 2–6 | Core exercise engine (all screens) |

Files to be modified:

| File | Chunk | Change |
|---|---|---|
| `index.html` | 7 | Add Patient Encounter module card |

---

## CSS System

### Color Variables (exercise page `<style>`)

```css
:root {
  --bg: #0d0d12;
  --surface: #13131a;
  --surface2: #1a1a24;
  --border: rgba(255,255,255,.07);
  --text: #e8e8f0;
  --text2: #8888aa;
  --accent: #6366f1;
  --accent-light: #818cf8;
  --accent-dark: #4f46e5;
  --accent-glow: rgba(99,102,241,.18);
  --gold: #d4a054;
  --red: #f87171;
  --green: #34d399;
  --orange: #fb923c;
}
```

### Avatar Animation Keyframes

```css
@keyframes breathe {
  0%,100% { transform: scaleY(1.000); }
  50%      { transform: scaleY(1.012); }
}
@keyframes breatheFast {
  0%,100% { transform: scaleY(1.000); }
  50%      { transform: scaleY(1.018); }
}
@keyframes jawSpeak {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(3px); }
}
@keyframes tearFall {
  0%   { opacity:0; transform: translateY(0); }
  20%  { opacity:.8; }
  100% { opacity:0; transform: translateY(28px); }
}
@keyframes fidgetHand {
  0%,100% { transform: rotate(0deg); }
  30%     { transform: rotate(-4deg); }
  70%     { transform: rotate(4deg); }
}
@keyframes headTilt {
  0%,100% { transform: rotate(0deg); }
  50%     { transform: rotate(-6deg); }
}
@keyframes microShake {
  0%,100% { transform: translateX(0); }
  25%     { transform: translateX(-2px); }
  75%     { transform: translateX(2px); }
}
@keyframes postureBow {
  0%   { transform: translateY(0) rotate(0deg); }
  100% { transform: translateY(4px) rotate(-3deg); }
}
@keyframes gazeAvert {
  0%,100% { transform: translateX(0); }
  50%     { transform: translateX(-4px); }
}
```

### Shared Utility Keyframes

```css
@keyframes fadeInUp    { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
@keyframes fadeIn      { from { opacity:0; } to { opacity:1; } }
@keyframes pop         { 0% { transform:scale(0.6); opacity:0; } 70% { transform:scale(1.08); } 100% { transform:scale(1); opacity:1; } }
@keyframes typewriter  { /* driven by JS interval, not CSS */ }
@keyframes chartReveal { from { opacity:0; transform:translateX(-8px); } to { opacity:1; transform:none; } }
@keyframes shimmer     { 0% { background-position: -400px 0; } 100% { background-position: 400px 0; } }
@keyframes spin        { to { transform:rotate(360deg); } }
@keyframes correctPulse { 0%,100%{box-shadow:0 0 0 0 rgba(52,211,153,0);}50%{box-shadow:0 0 0 8px rgba(52,211,153,.3);} }
@keyframes wrongShake  { 0%,100%{transform:translateX(0);}20%,60%{transform:translateX(-6px);}40%,80%{transform:translateX(6px);} }
@keyframes phaseSlideIn { from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:none;} }
@keyframes questionSlide { from{opacity:0;transform:scale(.95);}to{opacity:1;transform:scale(1);} }
@keyframes tagPop      { 0%{transform:scale(0);opacity:0;}60%{transform:scale(1.1);}100%{transform:scale(1);opacity:1;} }
@keyframes dotBlink    { 0%,80%,100%{opacity:0;}40%{opacity:1;} }
@keyframes scoreRingFill { from{stroke-dashoffset:var(--ring-full);} to{stroke-dashoffset:var(--ring-offset);} }
```

### Avatar State CSS Classes

```css
/* Applied to #avatar-root SVG element */
.state-idle     .avatar-body   { animation: breathe 4s ease-in-out infinite; }
.state-speaking .avatar-jaw    { animation: jawSpeak .3s ease-in-out infinite; }
.state-speaking .avatar-body   { animation: breathe 3s ease-in-out infinite; }
.state-distressed .avatar-body { animation: postureBow .8s ease forwards, breathe 5s ease-in-out infinite; }
.state-tearful .avatar-tear    { animation: tearFall 2.4s ease-in-out infinite; }
.state-tearful .avatar-body    { animation: breathe 6s ease-in-out infinite; }
.state-anxious .avatar-body    { animation: breatheFast 1.8s ease-in-out infinite; }
.state-anxious .avatar-hand    { animation: fidgetHand .6s ease-in-out infinite alternate; }
.state-agitated .avatar-head   { animation: microShake .4s ease-in-out infinite; }
.state-agitated .avatar-body   { animation: breatheFast 1.2s ease-in-out infinite; }
.state-guarded .avatar-eyes    { animation: gazeAvert 3s ease-in-out infinite; }
.state-guarded .avatar-body    { animation: breathe 5s ease-in-out infinite; }
.state-flat_affect .avatar-body{ animation: breathe 8s ease-in-out infinite; }
.state-confused .avatar-head   { animation: headTilt 2s ease-in-out infinite; }
```

---

## JavaScript State Design

### Global State Object (`clinical-presentation-exercise.html`)

```javascript
const CFG = {
  domains:    [],    // ['CPAT','PTHE']
  levels:     [],    // [1,2,3]
  count:      10,    // number of encounters
  order:      'shuffled',  // 'shuffled'|'sequential'|'weakest'
  speed:      'normal',    // 'slow'|'normal'|'fast'|'manual'
  showTags:   true,
  showChart:  true,
};

const state = {
  pool:          [],   // loaded EncounterObjects after filter+sort
  encIdx:        0,    // current encounter index in pool
  phaseIdx:      0,    // current phase index within encounter
  qIdx:          0,    // current question index within encounter
  answered:      false,
  phaseRunning:  false,
  typewriterInt: null,
  autoAdvanceInt:null,
  avatarState:   'idle',
  domainScores:  {},   // { CPAT: { correct:0, total:0 } }
  typeScores:    {},   // { primary_diagnosis: { correct:0, total:0 } }
  sessionAnswers:[],   // [ { encId, qId, type, correct, domain } ]
};
```

### Screen State Machine

```
showScreen('loading')
  → fetch all domains → build pool → showScreen('encounter')

showScreen('encounter')
  → render patient info + setting
  → reset chart + behavioral tags
  → phaseIdx = 0
  → startPhase(0)

startPhase(idx)
  → set avatar emotion class
  → if clinician_prompt: show probe text first, then patient dialogue
  → typewriter dialogue into speech bubble
  → after typewriter: revealChartItems(), revealBehavioralTags()
  → if speed !== 'manual': start auto-advance timer
  → else: show "Next →" button

advancePhase()
  → phaseIdx++
  → if phaseIdx >= phases.length: transitionToQuestion()
  → else: startPhase(phaseIdx)

transitionToQuestion()
  → fade out encounter stage
  → showScreen('question')
  → qIdx = 0
  → renderQuestion(0)

renderQuestion(idx)
  → populate prompt, type badge, options A/B/C/D
  → if qIdx > 0: show "Question 2 of 2" indicator
  → animate questionSlide in

selectAnswer(letter)
  → lock all options
  → if correct: mark correct, state.domainScores[domain].correct++
  → mark selected option correct/wrong
  → dim unchosen wrong options
  → reveal explanation panel (slide down)
  → reveal distractor rationale for all options
  → show "Next Question →" or "See Results →"

nextQuestion()
  → qIdx++
  → if qIdx < questions.length: renderQuestion(qIdx)
  → else: nextEncounter() or showScreen('results')

showScreen('results')
  → render score ring (animated SVG)
  → render type breakdown table
  → render domain breakdown bars
  → render encounter replay list
```

---

## SVG Patient Avatar — Specification

The patient is rendered as a single inline SVG element (`viewBox="0 0 200 320"`) inside
`.patient-stage`. The avatar represents a seated adult patient in a clinical chair. It must
be anatomically proportioned but intentionally simplified — vector-art clinical illustration
style, not photorealistic.

### SVG Element Groups (in render order)

| Group ID | Contains | Animated Parts |
|---|---|---|
| `#chair` | Chair frame, seat cushion, armrests | Static |
| `#avatar-legs` | Thighs, lower legs, feet | Static / fidget foot |
| `#avatar-body` | Torso, shoulders, neck, clothing | Breathe scale |
| `#avatar-arms` | Upper arms, forearms | Hand fidget |
| `#avatar-hands` | Hands folded in lap | Fidget |
| `#avatar-head` | Head silhouette | Head tilt / micro-shake |
| `#avatar-hair` | Hair shape | Moves with head |
| `#avatar-face` | Eyes, nose, mouth | Gaze avert, jaw |
| `#avatar-jaw` | Lower jaw only | jawSpeak animation |
| `#avatar-eyes` | Iris paths, lids | gazeAvert |
| `#avatar-brow` | Eyebrow paths | Furrow (confused) |
| `#avatar-tear` | 2 teardrop paths | tearFall (tearful) |
| `#avatar-root` | Root group (all above) | Animation state class |

### Color Palette (Avatar)

```
Chair frame:       #2a2a38
Chair cushion:     #3a3a50 (subtle warm upholstery)
Skin (neutral):    #c8956c (default warm mid-tone; not race-specific)
Clothing:          #3d4a5c (muted blue-grey, clinical neutral)
Hair:              #2c1f14 (dark brown default)
Eye iris:          #4a3728
Eyebrow:           #2c1f14
Tear:              rgba(180,210,255,.8)
```

### Avatar Responsive Sizing

The stage container `.patient-stage` sets `width: 200px; height: 320px` on desktop.
On mobile (< 640px), scale to `width: 150px; height: 240px` using `transform: scale(.75)`.

---

## Speech Bubble — Specification

```html
<div id="speech-bubble" class="speech-bubble hidden">
  <div class="bubble-tail"></div>
  <div class="clinician-probe" id="clinician-probe"></div>
  <div class="bubble-dots" id="bubble-dots">
    <span></span><span></span><span></span>
  </div>
  <div class="bubble-text" id="bubble-text"></div>
</div>
```

**Bubble tail:** A CSS triangle pointing left-down toward the patient's mouth area.
Positioned absolutely at bottom-left of the bubble.

**Thinking dots:** Three `<span>` elements with staggered `dotBlink` animation.
Show for 800ms before typewriter begins, then hide.

**Typewriter:** JS `setInterval` at speed-dependent intervals:
- Slow: 50ms/char
- Normal: 30ms/char
- Fast: 12ms/char
- Manual: 30ms/char (same as normal, but no auto-advance after)

**Clinician probe:** If phase has `clinician_prompt`, render it in italicized grey text
above the patient dialogue. Apply a 400ms delay before switching to patient dialogue.
Example display:
```
Clinician: "What brings you in today?"
```
Then patient speech bubble below.

---

## Medical Chart Panel — Specification

```html
<div id="chart-panel" class="chart-panel">
  <div class="chart-header">
    <span class="chart-icon">📋</span>
    <span class="chart-title">Clinical Chart</span>
  </div>
  <div id="chart-body" class="chart-body">
    <!-- Chart sections injected dynamically -->
  </div>
</div>
```

Chart categories (in display order):
1. Chief Complaint
2. History of Present Illness (HPI)
3. Mental Status Examination (MSE)
4. Psychosocial History
5. Collateral / Context
6. Labs / Observations

Each category renders as:
```html
<div class="chart-section">
  <div class="chart-section-label">Chief Complaint</div>
  <div class="chart-row" style="animation-delay: Nms">
    <span class="chart-key">Chief Complaint</span>
    <span class="chart-val">Fatigue, inability to function</span>
  </div>
  ...
</div>
```

Chart items enter with `chartReveal .35s ease forwards` animation.
Items from the same phase get staggered delays (0ms, 80ms, 160ms...).
The chart panel scrolls independently if content overflows.

---

## Behavioral Tags — Specification

```html
<div id="tag-overlay" class="tag-overlay">
  <!-- Tags injected dynamically per phase -->
</div>
```

Tags are absolutely positioned over the patient stage area, appearing near the patient.
Each tag:
```html
<span class="behavior-tag tag-{color}" style="--delay: Nms">flat affect</span>
```

Tag color categories:
- `tag-red` (#f87171): Risk flags (SI, HI, self-harm, agitation, substance use)
- `tag-orange` (#fb923c): Diagnostic symptoms (anhedonia, psychomotor retardation, grandiosity)
- `tag-blue` (#60a5fa): Observational (eye contact, speech rate, cooperation)
- `tag-purple` (#a78bfa): Cognitive/perceptual (thought disorganization, hallucination)

Tags appear with `tagPop .3s cubic-bezier(.34,1.56,.64,1) forwards` animation.
Each new tag from a phase appears 150ms after the previous one.
Tags accumulate across all phases (not cleared between phases).
If more than 8 tags are visible, older tags fade to 50% opacity but remain.

---

## Phase Controls — Specification

```html
<div id="phase-controls" class="phase-controls">
  <div class="phase-indicator">
    <span class="phase-num" id="phase-label">Chief Complaint</span>
    <div class="phase-dots" id="phase-dots">
      <!-- One dot per phase, filled = completed -->
    </div>
  </div>
  <button id="btn-advance" class="btn-advance" onclick="advancePhase()">
    Next <span class="arrow">→</span>
  </button>
</div>
```

In `speed !== 'manual'` mode: the advance button is hidden and a progress bar animates
across the bottom of the screen, completing after the typewriter finishes + a 1.5s pause.
The bar is a `<div class="auto-bar"><div class="auto-bar-fill"></div></div>` absolutely
positioned at the bottom of `.encounter-layout`.

Phase dots: `◉` (current) vs `◦` (pending) vs `●` (completed).

---

## Screen Layouts

### `#screen-encounter` Layout

```
┌──────────────────────────────────────────────────────────────┐
│  nav (back + breadcrumb + progress fraction)                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  │
│  │  patient-stage           │  │  chart-panel             │  │
│  │  ┌─────────────────────┐ │  │  📋 Clinical Chart       │  │
│  │  │  [SVG avatar]       │ │  │  ─────────────────────── │  │
│  │  └─────────────────────┘ │  │  Chief Complaint         │  │
│  │  [speech bubble above]   │  │    CC: Fatigue...        │  │
│  │  [tag-overlay]           │  │  HPI                     │  │
│  │                          │  │    Duration: 4 months    │  │
│  │  .patient-info-bar       │  │    ...                   │  │
│  │  "Adult Female, 34"      │  │                          │  │
│  │  "Outpatient clinic"     │  │                          │  │
│  └──────────────────────────┘  └──────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  phase-controls: [Chief Complaint  ◉◦◦◦] [Next →]       │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### `#screen-question` Layout

```
┌──────────────────────────────────────────────────────────────┐
│  nav (back to encounter | progress: Q2/3 of 10 encounters)   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  .question-card  (max-width: 720px, centered)                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  [TYPE BADGE: Diagnosis]  [Encounter 3 of 10]            │ │
│  │                                                          │ │
│  │  Based on this presentation, which diagnosis is most...  │ │
│  │                                                          │ │
│  │  ┌──────────────┐  ┌──────────────┐                      │ │
│  │  │ A  Dysthymia │  │ B  MDD...    │                      │ │
│  │  └──────────────┘  └──────────────┘                      │ │
│  │  ┌──────────────┐  ┌──────────────┐                      │ │
│  │  │ C  Bipolar.. │  │ D  Adj Dis.. │                      │ │
│  │  └──────────────┘  └──────────────┘                      │ │
│  │                                                          │ │
│  │  [feedback panel — hidden until answer selected]         │ │
│  │  ✓ Correct! The presentation meets full MDD criteria...  │ │
│  │  ─────────────────────────────────────────────────────── │ │
│  │  Why not A? Dysthymia requires ≥2 years...               │ │
│  │  Why not C? No hypomanic episodes...                     │ │
│  │  Why not D? No precipitating stressor...                 │ │
│  │                                                          │ │
│  │              [Review Encounter] [Next Question →]        │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### `#screen-results` Layout

```
┌──────────────────────────────────────────────────────────────┐
│  nav (back to settings)                                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  .results-header                                             │
│  [SVG score ring: XX%]  Session Complete                     │
│  N correct of M total questions                              │
│                                                              │
│  .type-breakdown   (question type performance table)         │
│  Diagnosis        ████████░░  8/10                           │
│  Immediate Care   ████████████  6/6                          │
│  Treatment Plan   ██████░░░░  4/7                            │
│                                                              │
│  .domain-breakdown (per-domain bars)                         │
│  CPAT  ██████████  10/12                                     │
│  PTHE  ████░░░░░░   4/8                                      │
│                                                              │
│  .encounter-replay                                           │
│  Replay cases:                                               │
│  ✓ Adult Female, 34 — Mood Disorders      [Review]           │
│  ✗ Adult Male, 52 — Psychotic Disorders   [Review]           │
│                                                              │
│  [New Session]   [Try Again]                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Python Generator — `generate_presentations.py`

### Overview

Generates `{DOMAIN}_presentations.json` files by calling the Claude API (claude-opus-4-6)
with domain-specific prompting. Supports `--domain CPAT`, `--all`, and `--resume` (skips
already-generated entries). Target: 30 encounters per domain, 1–2 questions per encounter.

### Command Interface

```bash
python generate_presentations.py --domain CPAT --count 30
python generate_presentations.py --all --count 30 --resume
python generate_presentations.py --domain CPAT --preview   # print first encounter, no file write
```

### API Call Strategy

Generate 5 encounters per API call (not 1, not 30). Each batch specifies:
- Target domain + subdomain (cycle through subdomains to ensure coverage)
- Difficulty level distribution (mix of 1–4)
- Required avatar_emotion diversity
- Required question type variety (at least 2 types per batch)

### Subdomain Coverage Requirements

Each domain must have encounters distributed across its major subdomains.
Minimum 2 encounters per subdomain. Generator cycles through subdomains across batches.

#### CPAT subdomains:
Mood Disorders, Anxiety Disorders, Psychotic Disorders, Trauma/Stressor-Related,
Personality Disorders, Neurodevelopmental Disorders, Substance Use Disorders,
Somatic Symptom Disorders, Eating Disorders, Sleep-Wake Disorders

#### PTHE subdomains:
CBT, Psychodynamic/Psychoanalytic, Humanistic/Person-Centered, Family Systems,
DBT, ACT, Motivational Interviewing, Group Therapy, Crisis Intervention, Child/Play Therapy

#### BPSY subdomains:
Neurotransmitter Systems, Psychopharmacology, Brain Structures/Functions,
Genetics and Epigenetics, Endocrine/Immune Interactions, Sleep Physiology,
Psychophysiology, Substance Neurobiology

#### PMET subdomains:
Reliability, Validity, Standardization, Norm-Referenced vs. Criterion-Referenced,
Test Bias, Statistical Concepts, Item Analysis, Diagnostic Accuracy

#### LDEV subdomains:
Infancy/Toddlerhood, Early Childhood, Middle Childhood, Adolescence,
Early Adulthood, Middle Adulthood, Late Adulthood, Cognitive Development,
Social-Emotional Development, Attachment

#### SOCU subdomains:
Cultural Competence, Health Disparities, Social Determinants, Group Dynamics,
Attitudes/Attribution, Conformity/Influence, Community Psychology,
Rural/Underserved Populations

#### WDEV subdomains:
Supervision Models, Consultation, Professional Development, Organizational Behavior,
Work Motivation, Leadership, Team Dynamics, Burnout/Self-Care

#### CASS subdomains:
Clinical Interview, Intelligence Testing, Personality Assessment, Behavioral Assessment,
Neuropsychological Assessment, Risk Assessment, Diagnosis Formulation,
Cultural Considerations in Assessment

#### PETH subdomains:
Informed Consent, Confidentiality, Dual Relationships, Competence, APA Ethics Code,
Mandatory Reporting, Termination, Documentation, Telehealth, Supervision Ethics

### System Prompt (abridged — full version in script)

```
You are an expert EPPP preparation content author. Generate clinical patient encounter scenarios
for the Patient Encounter module of a psychology licensure exam prep tool.

Each encounter must:
- Present a realistic, clinically coherent patient case
- Progress through 3–5 distinct phases (Chief Complaint, HPI, MSE, etc.)
- Include authentic patient dialogue that feels natural, not textbook-recited
- Have behavioral observations and chart reveals that emerge organically from the dialogue
- Pair with 1–2 clinically rigorous questions testing different competencies
- Be set in a realistic clinical context (outpatient, inpatient, ER, school, etc.)
- Avoid leading or telegraphed presentations — maintain diagnostic uncertainty until after answer

Output strictly valid JSON matching the EncounterObject schema. No commentary outside JSON.
```

### Validation

After generation, validate each encounter against schema:
- `id` matches pattern `CP-{DOMAIN}-{NNNN}`
- `avatar_emotion` is one of the 10 allowed values
- `question.type` is one of the 8 allowed types
- Each `chart_reveals` has `category` that matches the 6 allowed categories
- `correct_answer` is one of A/B/C/D and exists in `options`
- `difficulty_level` is 1–4

---

## Chunk-by-Chunk Implementation Plan

---

### Chunk 0 — Data Architecture & Initial Generation

**Goal:** Build the data generator and produce a valid, usable dataset for 3 test domains
(CPAT, PTHE, BPSY) so all subsequent chunks can be built against real data.

**Deliverables:**
1. `generate_presentations.py` — complete, working generator script
2. `data/CPAT_presentations.json` — 30 encounters
3. `data/PTHE_presentations.json` — 30 encounters
4. `data/BPSY_presentations.json` — 30 encounters

**Implementation notes:**
- Use `anthropic` Python library with `claude-opus-4-6` (matches existing generator pattern)
- Read `generate_spot_errors.py` for API call pattern, retry logic, file write conventions
- Batch: 5 encounters per API call
- Implement `--resume`: read existing file, collect existing IDs, skip if already have N
- Implement subdomain cycling: generate a list of all subdomains, iterate with index % len
- Write incrementally (append to file after each batch, not just at end)
- Validate schema inline after each batch, log any mismatches
- Include a `--preview` flag to test 1 encounter without writing

**Completion criteria:**
- All 3 JSON files parse without errors
- Each file has ≥ 25 valid encounters (some may fail validation, that's ok)
- At least 6 of the 10 avatar_emotion values appear across all encounters
- At least 5 of the 8 question types appear across all encounters
- All difficulty levels (1–4) appear in each file

---

### Chunk 1 — Settings Page

**Goal:** Build `clinical-presentation-settings.html` — the full configuration page.

**Deliverables:**
1. `clinical-presentation-settings.html` — complete, styled, functional

**Implementation notes:**
- Copy the structure from `clinical-settings.html` as the architectural base
- Replace all gold color references with indigo (`#6366f1`, `#818cf8`, `#4f46e5`)
- Settings sections (in order):
  1. **Difficulty Levels** — Cards 1–4 (not 1–5 like vignettes; presentations top out at 4)
  2. **Domain Selection** — All 9 domains in 3-col grid + Mixed Domains option
  3. **Encounters** — Count buttons: 5, 10, 15, 20 + custom input
  4. **Presentation Speed** — 4 radio cards:
     - Slow (50ms/char, 3s hold before auto-advance)
     - Normal (30ms/char, 1.5s hold) — default, marked "(Recommended)"
     - Fast (12ms/char, 0.5s hold)
     - Manual (click to advance each phase)
  5. **Display Options** — Two toggle checkboxes (both on by default):
     - Show Behavioral Tags
     - Show Clinical Chart
  6. **Question Order** — Shuffled / Sequential / Weakest First (same as clinical)
- Summary bar shows: difficulty count, domain count (or "Mixed"), encounter count, speed, options
- Start button: indigo gradient, click → `clinical-presentation-exercise.html` with URLSearchParams:
  `?levels=1,2&domains=CPAT,PTHE&count=10&order=shuffled&speed=normal&tags=1&chart=1`
- Validation: require at least 1 level AND (mixed OR at least 1 domain)

**Completion criteria:**
- Page renders without errors
- All 9 domains selectable
- Mixed domains toggle works
- Speed setting persists to URL params correctly
- Summary bar updates live
- Start button correctly encodes all params and navigates

---

### Chunk 2 — Exercise Page Skeleton, Loading Screen, Data Pipeline

**Goal:** Build the exercise page shell with working data loading, URL param parsing, and
a polished loading screen. No encounter animation yet — just get the data flowing.

**Deliverables:**
1. `clinical-presentation-exercise.html` — shell with:
   - `#screen-loading` (complete, polished)
   - `#screen-encounter` (empty div — filled in Chunk 3+)
   - `#screen-question` (empty div — filled in Chunk 5)
   - `#screen-results` (empty div — filled in Chunk 6)
   - All CSS variables and keyframe animations defined
   - URL param parsing into CFG
   - Async data loader that fetches all domain JSONs, validates, filters, sorts, slices
   - Console logs confirming correct pool construction

**Loading screen spec:**
```html
<div id="screen-loading" class="screen active">
  <div class="loader-card">
    <div class="loader-icon">⚕</div>
    <div class="loader-spinner"></div>
    <div class="loader-status" id="loader-status">Loading encounters...</div>
    <div class="loader-bar-track">
      <div class="loader-bar-fill" id="loader-fill"></div>
    </div>
    <div class="loader-detail" id="loader-detail">Preparing patient cases</div>
  </div>
</div>
```

The bar advances incrementally as each domain JSON is fetched (1 domain = 1/N of progress).

**Data pipeline:**

```javascript
async function loadEncounters() {
  const pool = [];
  for (let i = 0; i < CFG.domains.length; i++) {
    updateLoading(`Loading ${CFG.domains[i]}...`, (i+1)/CFG.domains.length);
    try {
      const r = await fetch(`data/${CFG.domains[i]}_presentations.json`);
      if (!r.ok) continue;
      const data = await r.json();
      const filtered = data.encounters.filter(e =>
        CFG.levels.includes(e.difficulty_level)
      );
      pool.push(...filtered);
    } catch(e) { console.warn('Failed to load', CFG.domains[i], e); }
  }
  if (pool.length === 0) { showError('No encounters match your settings.'); return; }
  state.pool = sortPool(pool); // shuffled | sequential | weakest
  state.pool = state.pool.slice(0, CFG.count);
  showScreen('encounter');
}
```

**Sort strategies:**
- `shuffled`: Fisher-Yates shuffle
- `sequential`: sort by domain_code, then id
- `weakest`: sort by domain accuracy from localStorage (lowest first)

**Completion criteria:**
- Loading screen appears and animates
- All 3 test-domain JSONs load correctly
- Pool is correctly filtered by difficulty and sorted by order
- Pool is correctly sliced to CFG.count
- Console shows pool size, domain distribution
- `showScreen('encounter')` is called (empty screen shows, no crash)

---

### Chunk 3 — SVG Patient Avatar + Animation System

**Goal:** Build the complete SVG patient avatar with all 10 animation states.
This is the visual heart of the module.

**Deliverables:**
1. The inline SVG avatar code inside `#screen-encounter`
2. Complete CSS animation system (all keyframes + state classes)
3. `setAvatarState(emotion)` JS function
4. Visual demonstration: cycle through all 10 states on a test button (dev only)

**Avatar SVG construction notes:**

The SVG is `viewBox="0 0 200 320"`. All paths are hand-crafted bezier curves.
No traced images — drawn from scratch using approximate anatomy.

Chair (drawn first, lowest z-order):
- Chair back: rounded rectangle path `M 60,160 Q 58,80 100,75 Q 142,80 140,160 Z`
  (approximate — adjust for visual correctness)
- Seat: ellipse at y≈200
- Armrests: two thin rectangles extending left/right from seat

Body groups (all nested inside `<g id="avatar-root">`):
- Each animatable sub-group gets its own `<g id="avatar-{part}">` with `transform-origin`
  set to the anatomically correct pivot point (e.g., jaw pivots at top of jaw, not center)

The complete SVG structure:
```svg
<svg id="avatar-root" viewBox="0 0 200 320" class="state-idle">
  <defs>
    <radialGradient id="skin-grad">...</radialGradient>
    <radialGradient id="cloth-grad">...</radialGradient>
    <filter id="avatar-shadow">...</filter>
  </defs>
  <g id="chair">...</g>
  <g id="avatar-legs">...</g>
  <g id="avatar-body" style="transform-origin: 100px 200px;">...</g>
  <g id="avatar-arms">
    <g id="avatar-hand-l">...</g>
    <g id="avatar-hand-r">...</g>
  </g>
  <g id="avatar-head" style="transform-origin: 100px 130px;">
    <g id="avatar-hair">...</g>
    <g id="avatar-face">
      <g id="avatar-eyes">...</g>
      <g id="avatar-brow">...</g>
      <g id="avatar-jaw" style="transform-origin: 100px 165px;">...</g>
      <g id="avatar-tear">...</g>
    </g>
  </g>
</svg>
```

The avatar uses two radial gradients: one for skin tones and one for clothing.
A subtle `filter="url(#avatar-shadow)"` drop-shadow on the root group grounds it.

`setAvatarState(emotion)`:
```javascript
function setAvatarState(emotion) {
  const root = document.getElementById('avatar-root');
  root.className = root.className.replace(/state-\S+/g, '').trim();
  root.classList.add('state-' + emotion);
  state.avatarState = emotion;
}
```

For `tearful` state, also dynamically restart tear animations:
```javascript
if (emotion === 'tearful') {
  document.querySelectorAll('.avatar-tear path').forEach(p => {
    p.style.animation = 'none';
    p.offsetHeight; // reflow
    p.style.animation = '';
  });
}
```

**Completion criteria:**
- All 10 animation states visually distinct and correct
- `idle` breathing is subtle and lifelike (not jarring)
- `speaking` jaw movement is timed (not too fast, not too slow)
- `tearful` tear paths animate correctly and restart properly
- `anxious` hand fidget and faster breathing work together
- Avatar renders correctly at 200x320 and scaled to 150x240 (mobile)
- No CSS/SVG errors in console

---

### Chunk 4 — Encounter Presentation Engine

**Goal:** Bring the encounter screen fully to life. Patient speaks, chart fills in,
behavioral tags appear, phases advance.

**Deliverables:**
1. Complete `#screen-encounter` HTML structure
2. `startEncounter(enc)` and `startPhase(idx)` functions
3. Typewriter system with thinking-dots pre-animation
4. Chart panel with progressive category/item reveal
5. Behavioral tag overlay system
6. Phase dots indicator
7. Auto-advance timer bar
8. Manual advance button
9. `transitionToQuestion()` function (calls `showScreen('question')`)

**`startEncounter(enc)` spec:**
```javascript
function startEncounter(enc) {
  // Set patient info bar: label, setting
  document.getElementById('patient-label').textContent = enc.encounter.patient.label;
  document.getElementById('patient-setting').textContent = enc.encounter.setting;

  // Clear chart body, build section containers
  document.getElementById('chart-body').innerHTML = '';
  buildChartSections(enc); // creates empty section divs with correct category headers

  // Clear behavioral tags
  document.getElementById('tag-overlay').innerHTML = '';

  // Build phase dots
  buildPhaseDots(enc.encounter.phases.length);

  // Set initial avatar state
  setAvatarState(enc.encounter.patient.initial_avatar_state || 'idle');

  // Reset phase index
  state.phaseIdx = 0;
  state.phaseRunning = false;

  // Start phase 0
  startPhase(enc.encounter.phases[0]);
}
```

**Typewriter implementation:**
```javascript
function typewriter(text, speed, onComplete) {
  const el = document.getElementById('bubble-text');
  el.textContent = '';
  let i = 0;
  const interval = setInterval(() => {
    el.textContent += text[i++];
    if (i >= text.length) {
      clearInterval(interval);
      if (onComplete) onComplete();
    }
  }, speed);
  state.typewriterInt = interval;
}
```

**Clinician probe sequence:**
If `phase.clinician_prompt` exists:
1. Show probe text (fade in): `Clinician: "..."`
2. Wait 800ms
3. Show thinking dots in speech bubble for 600ms
4. Hide dots, start typewriter for patient dialogue

If no clinician prompt:
1. Show thinking dots for 600ms
2. Start typewriter

**Chart reveal:**
After typewriter completes, inject chart rows from `phase.chart_reveals` into the
corresponding category section, with 80ms stagger between items.

**Behavioral tags:**
After chart rows injected, inject tags from `phase.behavioral_tags` into `#tag-overlay`,
with 150ms stagger. Tags use `position: absolute` and are distributed across the stage
area using predefined offset positions (rotate through 6-8 positions to avoid overlap).

**Phase dot update:**
Current phase dot → filled. Previous phase dot → completed marker.

**Auto-advance timer:**
After typewriter + chart + tags complete, if speed !== 'manual':
- Show `.auto-bar` at bottom of encounter layout
- Animate `.auto-bar-fill` from 0% to 100% width over `holdTime` ms
  (slow: 3000ms, normal: 1500ms, fast: 500ms)
- On complete: call `advancePhase()`

**`advancePhase()` spec:**
```javascript
function advancePhase() {
  if (state.phaseRunning) return;
  clearAutoAdvance();
  state.phaseIdx++;
  const enc = state.pool[state.encIdx];
  if (state.phaseIdx >= enc.encounter.phases.length) {
    transitionToQuestion();
  } else {
    startPhase(enc.encounter.phases[state.phaseIdx]);
  }
}
```

**`transitionToQuestion()`:**
- Hide advance button / stop auto bar
- Add `.fading-out` class to `#screen-encounter` (opacity 0, 400ms transition)
- After 400ms: showScreen('question')

**Completion criteria:**
- Full 3-phase encounter plays end-to-end with no user interaction (auto mode)
- Chart fills in correctly per phase (no cross-contamination between categories)
- Behavioral tags appear and stack without overlapping the avatar
- Phase dots update correctly (current / completed)
- Auto-advance timer bar is smooth (CSS transition, not JS interval)
- Manual mode: Next button advances phases correctly
- `transitionToQuestion()` transitions cleanly
- Works with 1-phase and 5-phase encounters

---

### Chunk 5 — Question, Answer Selection & Feedback

**Goal:** Build the complete question screen: rendering, answer selection, locking,
feedback reveal, distractor rationale, multi-question support, navigation.

**Deliverables:**
1. Complete `#screen-question` HTML structure
2. `renderQuestion(q)` function
3. `selectAnswer(letter)` function
4. Feedback panel with explanation + per-option distractor rationale
5. "Review Encounter" button (returns to encounter at last phase, read-only)
6. "Next Question →" / "See Results →" button
7. Question type badge system (8 types × colors)

**`renderQuestion(q)` spec:**
```javascript
function renderQuestion(q) {
  const enc = state.pool[state.encIdx];

  // Type badge
  const badgeConf = TYPE_BADGE_MAP[q.type]; // { label, color }
  document.getElementById('q-type-badge').textContent = badgeConf.label;
  document.getElementById('q-type-badge').style.background = badgeConf.color + '22';
  document.getElementById('q-type-badge').style.color = badgeConf.color;

  // Encounter counter
  document.getElementById('q-counter').textContent =
    `Encounter ${state.encIdx+1} of ${state.pool.length}`;

  // If multiple questions in encounter
  if (enc.questions.length > 1) {
    document.getElementById('q-multi').textContent =
      `Question ${state.qIdx+1} of ${enc.questions.length}`;
    document.getElementById('q-multi').style.display = 'block';
  }

  // Prompt
  document.getElementById('q-prompt').textContent = q.prompt;

  // Options
  const optGrid = document.getElementById('q-options');
  optGrid.innerHTML = '';
  ['A','B','C','D'].forEach(letter => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.dataset.letter = letter;
    btn.onclick = () => selectAnswer(letter);
    btn.innerHTML = `<span class="option-letter">${letter}</span><span class="option-text">${q.options[letter]}</span>`;
    optGrid.appendChild(btn);
  });

  // Hide feedback
  document.getElementById('feedback-panel').classList.add('hidden');
  state.answered = false;

  // Animate in
  document.querySelector('.question-card').style.animation = 'questionSlide .35s ease forwards';
}
```

**`selectAnswer(letter)` spec:**
```javascript
function selectAnswer(letter) {
  if (state.answered) return;
  state.answered = true;

  const enc = state.pool[state.encIdx];
  const q = enc.questions[state.qIdx];
  const correct = q.correct_answer;
  const isCorrect = letter === correct;

  // Lock all buttons
  document.querySelectorAll('.option-btn').forEach(btn => {
    btn.disabled = true;
    const l = btn.dataset.letter;
    if (l === correct) btn.classList.add('correct');
    else if (l === letter) btn.classList.add('wrong');
    else btn.classList.add('dimmed');
  });

  // Update scores
  const domain = enc.domain_code;
  state.domainScores[domain] = state.domainScores[domain] || {correct:0,total:0};
  state.domainScores[domain].total++;
  state.typeScores[q.type] = state.typeScores[q.type] || {correct:0,total:0};
  state.typeScores[q.type].total++;
  if (isCorrect) {
    state.domainScores[domain].correct++;
    state.typeScores[q.type].correct++;
  }

  state.sessionAnswers.push({ encId: enc.id, qId: q.question_id, type: q.type, correct: isCorrect, domain });

  // Show feedback
  showFeedback(q, isCorrect);

  // Persist to localStorage
  persistScores();
}
```

**Feedback panel spec:**
```html
<div id="feedback-panel" class="feedback-panel hidden">
  <div class="feedback-header" id="feedback-header">
    <!-- ✓ Correct! or ✗ Incorrect — displayed with animation -->
  </div>
  <div class="feedback-explanation" id="feedback-explanation">
    <!-- full explanation text -->
  </div>
  <div class="feedback-distractors" id="feedback-distractors">
    <!-- why not A / why not B / etc. for each wrong option -->
  </div>
  <div class="feedback-actions">
    <button onclick="reviewEncounter()" class="btn-secondary">Review Encounter</button>
    <button onclick="nextQuestion()" class="btn-primary" id="btn-next-q">Next Question →</button>
  </div>
</div>
```

The feedback panel slides down with:
```css
.feedback-panel { max-height: 0; overflow: hidden; transition: max-height .4s ease; }
.feedback-panel.visible { max-height: 600px; }
```

Distractor rationale rows (for all incorrect options):
```html
<div class="distractor-row">
  <span class="distractor-letter">Why not A?</span>
  <span class="distractor-text">Dysthymia requires ≥2 years...</span>
</div>
```

**`reviewEncounter()` spec:**
- Store current encounter's phase states (chart, tags already rendered)
- Switch to `#screen-encounter`
- Set to last phase (all phases completed, all chart items shown)
- Show a "Return to Question →" button in phase-controls area
- Avatar is idle (read-only, no auto-advance)

**`nextQuestion()` spec:**
```javascript
function nextQuestion() {
  const enc = state.pool[state.encIdx];
  state.qIdx++;
  if (state.qIdx < enc.questions.length) {
    renderQuestion(enc.questions[state.qIdx]);
  } else {
    nextEncounter();
  }
}

function nextEncounter() {
  state.encIdx++;
  state.qIdx = 0;
  if (state.encIdx >= state.pool.length) {
    showScreen('results');
  } else {
    showScreen('encounter');
    startEncounter(state.pool[state.encIdx]);
  }
}
```

**If encounter has only 1 question:** "Next Question →" button reads "Next Encounter →" for the last question.
**If this is the last encounter's last question:** button reads "See Results →".

**Option CSS states:**
```css
.option-btn.correct { border-color: var(--green); background: rgba(52,211,153,.1); }
.option-btn.correct { animation: correctPulse .6s ease; }
.option-btn.wrong   { border-color: var(--red); background: rgba(248,113,113,.1); animation: wrongShake .4s ease; }
.option-btn.dimmed  { opacity: .4; }
.option-btn:not(:disabled):hover { border-color: var(--accent-light); background: var(--accent-glow); }
```

**Completion criteria:**
- All 8 question types render with correct badge colors
- Correct answer always highlighted green
- Selected wrong answer highlighted red + shake
- Unchosen wrong answers dimmed
- Explanation text displays correctly for all sample data
- Distractor rationale appears for all 3 non-correct options
- Review Encounter button returns to last-phase view, no re-animation
- Multi-question encounters (2 questions) progress through both questions
- `nextEncounter()` correctly transitions to next case
- Final encounter last question → results screen

---

### Chunk 6 — Results Screen & localStorage

**Goal:** Build the complete results screen with score ring, type breakdown, domain
breakdown, encounter replay list, and full localStorage persistence.

**Deliverables:**
1. Complete `#screen-results` HTML structure
2. Animated SVG score ring
3. Question type performance table
4. Domain breakdown bar chart
5. Encounter replay list (with ✓/✗ outcomes)
6. `persistScores()` and `loadScores()` functions
7. "New Session" (→ settings) and "Try Again" (→ reload) buttons

**Score Ring SVG:**
```html
<svg class="score-ring" viewBox="0 0 120 120">
  <circle class="ring-bg" cx="60" cy="60" r="50"
    fill="none" stroke="rgba(255,255,255,.06)" stroke-width="10"/>
  <circle class="ring-fill" cx="60" cy="60" r="50"
    fill="none" stroke="var(--accent)" stroke-width="10"
    stroke-linecap="round"
    stroke-dasharray="314"
    stroke-dashoffset="314"
    transform="rotate(-90 60 60)"
    id="score-ring-fill"/>
  <text x="60" y="60" text-anchor="middle" dominant-baseline="middle"
    class="score-pct" id="score-pct-text">0%</text>
  <text x="60" y="76" text-anchor="middle"
    class="score-label">score</text>
</svg>
```

Animation:
```javascript
function animateScoreRing(pct) {
  const circumference = 314;
  const offset = circumference * (1 - pct/100);
  const fill = document.getElementById('score-ring-fill');
  fill.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)';
  fill.style.strokeDashoffset = offset;
  // Animate pct counter
  let cur = 0;
  const step = pct / 60; // 60 frames at ~16ms = ~1s
  const intv = setInterval(() => {
    cur = Math.min(cur + step, pct);
    document.getElementById('score-pct-text').textContent = Math.round(cur) + '%';
    if (cur >= pct) clearInterval(intv);
  }, 16);
}
```

Ring color: `var(--accent)` for ≥70%, `var(--orange)` for 50–69%, `var(--red)` for <50%.

**Type breakdown table:**
```html
<div class="type-breakdown">
  <div class="breakdown-title">By Question Type</div>
  <div class="type-row" id="type-rows">
    <!-- Injected dynamically per question type that appeared in session -->
    <div class="type-row-item">
      <span class="type-badge-sm" style="color: #6366f1">Diagnosis</span>
      <div class="type-bar-track">
        <div class="type-bar-fill" style="width: Npx; background: #6366f1"></div>
      </div>
      <span class="type-fraction">8/10</span>
    </div>
  </div>
</div>
```

Only show question types that appeared in the session (skip types with 0 total).

**Domain breakdown:**
Same pattern as clinical-exercise.html's domain breakdown. Show all domains that appeared
in the session. Each row: domain code + name, colored bar, fraction.

**Encounter replay list:**
```html
<div class="replay-section">
  <div class="replay-title">Case Review</div>
  <div id="replay-list">
    <div class="replay-row">
      <span class="replay-outcome correct">✓</span>
      <span class="replay-label">Adult Female, 34 — Mood Disorders</span>
      <span class="replay-domain">CPAT</span>
      <button onclick="replayEncounter(0)" class="btn-replay">Review</button>
    </div>
  </div>
</div>
```

`replayEncounter(idx)`:
- Set `state.encIdx = idx`
- Set all phases to completed (all chart items shown immediately, no animation)
- Show the encounter in read-only mode
- Add a "← Back to Results" button in phase-controls

**localStorage schema:**
```javascript
// Key: 'encounter_scores'
// Value: { CPAT: { correct: 12, total: 20 }, PTHE: { correct: 8, total: 15 }, ... }
// Key: 'encounter_type_scores'
// Value: { primary_diagnosis: { correct: 5, total: 8 }, ... }

function persistScores() {
  const all = JSON.parse(localStorage.getItem('encounter_scores') || '{}');
  Object.entries(state.domainScores).forEach(([d, s]) => {
    all[d] = all[d] || { correct:0, total:0 };
    all[d].correct += s.correct;
    all[d].total += s.total;
  });
  localStorage.setItem('encounter_scores', JSON.stringify(all));
  // Same pattern for type_scores
}
```

**Completion criteria:**
- Score ring animates from 0 to correct percentage on screen show
- Ring color changes correctly based on score band
- Type breakdown shows only types present in session
- Domain breakdown bars are proportional and labeled
- Encounter replay correctly shows each case
- localStorage correctly accumulates across sessions (not overwritten)
- "New Session" navigates to settings page
- "Try Again" reloads with same params

---

### Chunk 7 — Index Integration

**Goal:** Add the Patient Encounter card to `index.html` with correct styling and linking.

**Deliverables:**
1. Modified `index.html` with new module card added to the grid

**Implementation notes:**

Add a new `.module-card` to `.modules-grid` in `index.html`. The card follows the exact
same HTML structure as existing cards. Place it as the first card (replacing or before
the existing Clinical Vignette card — position to be decided based on visual grid flow).

New card HTML:
```html
<div class="module-card" onclick="location.href='clinical-presentation-settings.html'">
  <div class="card-icon">⚕</div>
  <div class="card-meta">
    <span class="card-label" style="color:#818cf8">IMMERSIVE</span>
  </div>
  <div class="card-title">Patient Encounter</div>
  <div class="card-desc">Animated cases. Real clinical judgment.</div>
  <div class="card-arrow" style="color:#6366f1">→</div>
</div>
```

Add to the existing `<style>` block in index.html:
```css
/* Patient Encounter card accent */
.module-card:nth-child(N):hover { /* N = the position of the new card */
  border-color: rgba(99,102,241,.3);
  box-shadow: 0 0 40px rgba(99,102,241,.08);
}
```

**Completion criteria:**
- New card appears in the module grid
- Clicking navigates to `clinical-presentation-settings.html`
- Indigo color accent is consistent with the module's identity
- Card layout matches the visual style of existing cards

---

### Chunk 8 — Full Data Generation (All 9 Domains)

**Goal:** Generate complete encounter datasets for all 9 EPPP domains.

**Deliverables:**
1. `data/PMET_presentations.json` — 30 encounters
2. `data/LDEV_presentations.json` — 30 encounters
3. `data/SOCU_presentations.json` — 30 encounters
4. `data/WDEV_presentations.json` — 30 encounters
5. `data/CASS_presentations.json` — 30 encounters
6. `data/PETH_presentations.json` — 30 encounters

**Special notes by domain:**

**PMET** (Psychological Measurement): Patients presenting for testing. The clinical
encounter is a psychoeducational or assessment intake. Phases include: referral context,
patient/family concerns about testing, behavioral observations during interview.
Questions test knowledge of test selection, reliability/validity concepts applied to
a case, interpreting scores.

**LDEV** (Lifespan Development): Patient age must match the developmental stage tested.
Generate cases across the lifespan: infants (parent-report encounters), children,
adolescents, adults, older adults. Phases include parent/guardian input for pediatric cases.

**SOCU** (Social/Cultural): Encounters must explicitly surface cultural identity,
socioeconomic context, systemic factors. Avatar initial state should reflect cultural
presentation differences (e.g., somatization as cultural idiom of distress).

**WDEV** (Workforce/Supervision): Encounter setting is often a supervision session or
organizational consultation, not a patient clinical encounter. The "patient" may be
a supervisee or colleague. This requires a note in the system prompt to adapt.

**CASS** (Clinical Assessment): Encounter is an assessment session. Phases include:
presenting concern, behavioral observations during testing, informant report.

**PETH** (Ethics): Encounter surfaces an ethical dilemma. The "patient" presents
a situation that requires the clinician to navigate informed consent, confidentiality,
dual relationship concerns, mandated reporting, etc.

**Completion criteria:**
- All 9 domain JSON files exist and parse
- Each has ≥ 25 valid encounters
- All major subdomains represented (min. 2 encounters each)
- Encounters for non-standard domains (WDEV, PETH, LDEV) are adapted correctly

---

### Chunk 9 — Polish, Responsive Layout, QA

**Goal:** Final quality pass across all files. No rough edges.

**Deliverables:**
1. All files finalized and tested
2. Responsive layout correct on mobile (< 640px)
3. All animation performance verified (no janky animations)
4. Edge case handling verified

**QA checklist:**

**Responsive layout:**
- [ ] On mobile, chart panel moves below the patient stage (stack vertically)
- [ ] Avatar scales to 75% on mobile without breaking
- [ ] Speech bubble wraps correctly on narrow screens
- [ ] Option grid is 1-column on mobile (not 2)
- [ ] Results score ring + breakdown stack vertically on mobile
- [ ] Settings page 3-col domain grid → 2-col → 1-col at breakpoints

**Animation performance:**
- [ ] All CSS animations use `transform` and `opacity` only (no layout-triggering props)
- [ ] Typewriter interval is properly cleared on screen transitions
- [ ] Auto-advance timer is properly cleared on manual advance
- [ ] No memory leaks: all intervals cleared in `showScreen()`

**Edge cases:**
- [ ] A domain JSON that fails to fetch: silently skipped, others load
- [ ] Pool has fewer encounters than CFG.count: use all available
- [ ] Encounter with 0 behavioral tags: tag overlay stays empty (no error)
- [ ] Encounter with 0 chart reveals in a phase: chart stays unchanged (no error)
- [ ] Encounter with 2 questions: both questions render + score correctly
- [ ] `weakest` order with no localStorage history: falls back to shuffled
- [ ] Speed=manual: Next button is always visible, auto-advance never fires
- [ ] Review encounter from results: no animation re-runs, chart shows all items
- [ ] All 9 domains selected with count=5: only 5 encounters shown

**Visual polish:**
- [ ] Nav breadcrumb shows current encounter number
- [ ] Phase label updates correctly at each phase transition
- [ ] Speech bubble resizes gracefully for short vs. long dialogue
- [ ] Chart panel scrolls correctly when many items are revealed
- [ ] Behavioral tags don't overflow their container
- [ ] Feedback panel never clips below viewport on short screens (scroll if needed)
- [ ] Score ring text is legible at all score values

---

## Execution Order & Dependencies

```
Chunk 0  (Data Generator + CPAT/PTHE/BPSY)
    ↓
Chunk 1  (Settings Page)     ← independent of Chunk 0, can run in parallel
    ↓
Chunk 2  (Exercise Skeleton)      ← requires Chunk 0 (needs real data to test loading)
    ↓
Chunk 3  (SVG Avatar)             ← requires Chunk 2 (placed inside exercise page)
    ↓
Chunk 4  (Encounter Engine)       ← requires Chunk 3 (uses avatar state functions)
    ↓
Chunk 5  (Question + Feedback)    ← requires Chunk 4 (follows encounter flow)
    ↓
Chunk 6  (Results + localStorage) ← requires Chunk 5 (needs session answer data)
    ↓
Chunk 7  (Index Integration)      ← requires Chunk 1 (settings page must exist)
    ↓
Chunk 8  (Full Data Generation)   ← requires Chunk 0 (extends the generator)
    ↓
Chunk 9  (Polish + QA)            ← requires all prior chunks complete
```

---

## Status

| Chunk | Description | Status |
|---|---|---|
| 0 | Data Architecture & Initial Generation | Pending |
| 1 | Settings Page | Pending |
| 2 | Exercise Skeleton + Loading | Pending |
| 3 | SVG Patient Avatar + Animations | Pending |
| 4 | Encounter Presentation Engine | Pending |
| 5 | Question, Answer Selection & Feedback | Pending |
| 6 | Results Screen & localStorage | Pending |
| 7 | Index Integration | Pending |
| 8 | Full Data Generation (All 9 Domains) | Pending |
| 9 | Polish, Responsive Layout, QA | Pending |

---

*This document is the authoritative implementation specification. Execute each chunk completely
before beginning the next. Do not defer polish to later chunks. Each chunk must be shippable.*
