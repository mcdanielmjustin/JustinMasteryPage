# Patient Encounter Module — Elevation Plan & Corrective Procedures

> **Purpose**: This document is the single source of truth for all identified deficiencies, prescribed fixes, and architectural guidance for elevating the Patient Encounter module (`clinical-presentation-exercise.html` + `clinical-presentation-settings.html`) to world-class quality. It is designed to survive context compaction and serve as a reference across multiple Claude sessions.
>
> **Last updated**: 2026-03-03
> **Current commit**: `4921421` (master)
> **Files in scope**: `clinical-presentation-exercise.html`, `clinical-presentation-settings.html`, `generate_presentations.py`, `data/*_presentations.json`

---

## How to Use This Document

1. **Starting a new session**: Tell Claude: *"Read CLINICAL_PRESENTATION_ELEVATION.md and continue from where we left off."*
2. **Tracking progress**: Each item has a status — `DONE`, `IN PROGRESS`, or `TODO`. Update the status in this file after each session.
3. **Priority**: Items are grouped into waves. Complete Wave 1 before Wave 2, etc. Within each wave, items are ordered by impact.
4. **Corrective approach**: Every item includes (a) what's wrong, (b) where in the code, (c) the exact fix, and (d) verification steps. Claude should follow these precisely but adapt if the code has changed since this document was written.

---

## Status Dashboard

| Wave | Items | Done | Remaining |
|------|-------|------|-----------|
| 0 — Already Shipped | 8 items | 8/8 | 0 |
| 1 — Critical Bugs & UX | 6 items | 0/6 | 6 |
| 2 — Question Screen Polish | 7 items | 0/7 | 7 |
| 3 — Results & Coaching | 5 items | 0/5 | 5 |
| 4 — Settings & Session Intelligence | 5 items | 0/5 | 5 |
| 5 — World-Class Enhancements | 4 items | 0/4 | 4 |

---

## Wave 0 — Already Shipped (commit `4921421`) — `DONE`

These items were implemented in the initial elevation pass. Documented here for reference so future sessions don't re-implement them.

### 0.1 Jaw animation during dialogue — `DONE`
- **What was wrong**: The jaw (`#avatar-jaw`) never moved during typewriter sequences. `avatar_emotion` controlled the root state class, but `state-speaking` was never applied during dialogue because the emotion was always clinical (e.g., `distressed`, `tearful`).
- **Fix applied**: In `runTypewriter()`, jaw animation is now applied directly via inline `style.animation` on the `#avatar-jaw` element, independent of the root emotion state. `startJaw()` fires when typewriter begins, `stopJaw()` fires on completion or skip.
- **Location**: `runTypewriter()` function (~line 1689).

### 0.2 flat_affect and hopeful visual states — `DONE`
- **What was wrong**: `flat_affect` was just slower breathing (indistinguishable from idle). `hopeful` was barely different breathing rate.
- **Fix applied**:
  - `flat_affect`: Added `blinkSlow` keyframe animation (5s cycle), `filter: saturate(0.55) brightness(0.92)` on `#avatar-face`, flat mouth path `M91 128 Q100 128 109 128`.
  - `hopeful`: Added `postureUpright` keyframe (0.6s forward, then breathe), `filter: saturate(1.15) brightness(1.04)` on face, smile mouth path `M91 127 Q100 123 109 127`.
  - Added `MOUTH_PATHS` constant object mapping all emotion states to SVG `d` attributes. `setAvatarState()` now morphs `#avatar-mouth` on every state change.
- **Location**: CSS state classes (~line 114), `MOUTH_PATHS` object (~line 1882), `setAvatarState()` (~line 1897).

### 0.3 Tag positioning overlap — `DONE`
- **What was wrong**: 8 fixed positions with modulo wrap caused tags to stack directly on top of each other after the 8th tag.
- **Fix applied**: Replaced with two-column stacking system (`_tagCols`). Tags alternate left/right columns, each capped at `TAG_MAX_ROWS = 7`. When a column fills, the oldest tag fades out. `resetTagColumns()` clears state per encounter.
- **Location**: Tag system (~line 1769).

### 0.4 appearance_tags rendered — `DONE`
- **What was wrong**: `enc.encounter.patient.appearance_tags` was never displayed.
- **Fix applied**: Pre-seeded in the tag overlay before phase 1 via `revealBehavioralTags(appearanceTags, true)`. Grey italic style (`tag-appearance` CSS class) distinguishes them from phase-triggered tags.
- **Location**: `startEncounter()` (~line 1503), CSS `.tag-appearance` (~line 432).

### 0.5 referral_context rendered — `DONE`
- **What was wrong**: `enc.encounter.referral_context` was never shown.
- **Fix applied**: Added a pre-populated "Intake" section at the top of the chart panel in `buildChartSections()`. Shows setting and referral context immediately (no animation). Styled with indigo label border.
- **Location**: `buildChartSections()` (~line 1581), CSS `.chart-row-intake` (~line 304).

### 0.6 Keyboard shortcuts on encounter screen — `DONE`
- **What was wrong**: `keydown` handler only activated on `#screen-question`. Space/Enter/Escape did nothing on the encounter screen.
- **Fix applied**: Extended handler: Space/Enter advances phase (when typewriter not running), Escape/Backspace skips typewriter (clicks bubble). Question screen also now accepts Space for advance.
- **Location**: Keyboard handler (~line 2357).

### 0.7 Correct answer rationale in feedback — `DONE`
- **What was wrong**: `distractor_rationale[correct_answer]` was filtered out — the feedback only showed "Why not A/C/D?" but never "Why B is correct."
- **Fix applied**: Correct answer rationale rendered first in a green-highlighted row (`.distractor-correct` CSS class) before the wrong-answer rows.
- **Location**: `showFeedback()` (~line 2115), CSS `.distractor-correct` (~line 575).

### 0.8 Mid-session persistence — `DONE`
- **What was wrong**: `persistScores()` only called at session end. Browser close mid-session lost all progress.
- **Fix applied**: `persistScores()` now called after every question answer in `selectAnswer()`.
- **Location**: `selectAnswer()` (~line 2112).

---

## Wave 1 — Critical Encounter Screen Fixes — `TODO`

These directly affect whether the encounter *feels* like a patient sitting across from you.

### 1.1 Avatar too small and passive — `TODO`

**Priority**: Very High
**What's wrong**: The avatar is 200×320px — about the size of a business card — centered in a ~780px column. Most of the patient stage is empty dark space. The patient dominates neither visually nor emotionally. In a real encounter the patient fills your field of vision.

**Where in code**:
- CSS: `.avatar-wrap` sets the avatar container dimensions.
- CSS: `.patient-stage` layout controls the vertical composition.

**Corrective procedure**:
1. Increase avatar dimensions to 260×416px on desktop (>768px). Keep 200×320 on mobile.
2. Remove `justify-content: center` from `.patient-stage` and replace with a flex layout that places avatar+bubble from the top third of the stage.
3. Remove `max-width: 420px` on the patient info bar — it should match the bubble width and be visually aligned.
4. Verify the SVG `viewBox` still renders correctly at the larger size (it should — SVG is vector).

**Verification**: Open an encounter on a 1920×1080 monitor. The avatar should feel like it fills the left third of the viewport. The patient should feel present, not floating in void.

**Adaptive notes for Claude**: If the SVG paths render with visible aliasing at the larger size, add `shape-rendering: geometricPrecision` to the SVG root. If the layout breaks on tablets (768-1024px), add an intermediate breakpoint.

---

### 1.2 Speech bubble too transparent — `TODO`

**Priority**: High
**What's wrong**: `background: rgba(255,255,255,.05)` — nearly invisible. The bubble looks like a ghost rectangle, not a spoken thought.

**Where in code**: CSS `.speech-bubble` rule.

**Corrective procedure**:
1. Change fill to `rgba(255,255,255,.09)`.
2. Add `box-shadow: 0 4px 20px rgba(0,0,0,.3)` to lift it off the background.
3. Increase border opacity to `rgba(255,255,255,.12)`.

**Verification**: The bubble should register as a distinct floating card when squinting at the screen. It should feel like a dialogue box, not a transparent overlay.

---

### 1.3 Bubble text too small and wrong color — `TODO`

**Priority**: High
**What's wrong**: `font-size: 13px; color: var(--text2)` (#a8a8b3). This is the most important text during an encounter — the patient's words — rendered in secondary text color at 13px.

**Where in code**: CSS `#bubble-text` or `.bubble-text` styles.

**Corrective procedure**:
1. Change to `font-size: 14px`.
2. Change to `color: var(--text)` (full white / primary text color).
3. Set `line-height: 1.7` for comfortable reading.

**Verification**: The patient's dialogue should be the most visually prominent text on the encounter screen. It should feel like the primary reading target, not ambient content.

---

### 1.4 Clinician probe inside patient bubble — `TODO`

**Priority**: High
**What's wrong**: The clinician-probe element sits inside the speech bubble. With the new indigo-border styling, it looks like both speakers share the same bubble — as if the patient is quoting the clinician. These are two different speakers.

**Where in code**:
- HTML: `#clinician-probe` is a child of `#speech-bubble`.
- CSS: `.clinician-probe` styling.
- JS: `startPhase()` sets probe text and visibility.

**Corrective procedure** (two valid approaches — pick one):

**Option A — Move probe above the bubble** (recommended):
1. In the HTML, move `#clinician-probe` out of `#speech-bubble` and place it directly above it in the `.patient-stage` layout flow.
2. Style it as a small standalone label: `font-size: 11px; font-style: italic; color: var(--text2);` with prefix "You ask:" or "Clinician:".
3. Remove the indigo border-left styling (it's no longer needed once it's spatially separated).
4. The patient's response appears in the bubble below it — visually distinct.

**Option B — Keep inside but add separator**:
1. Keep the probe inside the bubble.
2. Add a "Clinician:" prefix label on its own line in bold.
3. Add a thin horizontal rule (`<hr>` styled as `border-top: 1px solid rgba(255,255,255,.08); margin: 8px 0;`) between the probe and patient text.
4. Keep the indigo left-border to mark the clinician's portion.

**Verification**: During a phase with a clinician prompt followed by patient dialogue, it should be immediately obvious that two different people are speaking. The visual separation should be clear enough that a first-time user never confuses who is speaking.

**Adaptive notes for Claude**: If Option A causes layout shifts (the probe appearing before the bubble pushes the bubble down), consider using absolute positioning for the probe above the bubble with a fixed height allocation.

---

### 1.5 Behavioral tags need spatial logic — `TODO`

**Priority**: Medium
**What's wrong**: Tags float in absolute position without spatial anchoring. They alternate left/right columns even when behaviorally related (e.g., "anhedonia" and "flat affect" from the same phase end up in opposite columns). No legend/header orients the test-taker.

**Where in code**: `revealBehavioralTags()` function, tag alternation logic.

**Corrective procedure**:
1. Add a faint label above the tag area: "OBSERVED" in `var(--text3)`, `font-size: 9px`, `letter-spacing: .1em`, positioned at top of the tag overlay.
2. Change the alternation logic so tags from the **same phase** go to the **same column**. Track a `_currentPhaseColumn` variable that alternates per phase (not per tag). All tags from phase 1 go left, phase 2 right, phase 3 left, etc.
3. Appearance tags (pre-encounter) always go to the left column.

**Verification**: Run an encounter with 4+ phases. Tags from the same phase should cluster in the same column. The "OBSERVED" label should be visible but non-intrusive.

---

### 1.6 "Click to skip" affordance on speech bubble — `TODO`

**Priority**: Medium
**What's wrong**: The bubble is clickable to skip the typewriter, but there's no visual hint. First-time users sit through the entire typewriter animation unaware they can skip it. The cursor is `pointer` and `user-select: none` (correct) but no tooltip or text hint exists.

**Where in code**: `#speech-bubble` styling and `runTypewriter()` click handler.

**Corrective procedure**:
1. Add a small hint element inside the bubble: `<span id="skip-hint" class="skip-hint">click to skip</span>`.
2. Style: `font-size: 9px; color: var(--text3); opacity: 0.5; position: absolute; bottom: 4px; right: 10px; pointer-events: none;`.
3. Show the hint during the first typewriter sequence of the session only. After the first skip (or after the first encounter completes), set a flag and hide it permanently via `display: none`.
4. Also show the keyboard shortcut: "click or press Esc to skip".

**Verification**: New user opens their first encounter. A faint "click or press Esc to skip" appears in the bottom-right of the bubble during typewriter. After they skip once (or after the first encounter), it never appears again.

---

## Wave 2 — Question Screen Polish — `TODO`

### 2.1 Review Case shows only last phase — `TODO`

**Priority**: High
**What's wrong**: When a student clicks "Review Case" during a question, the encounter screen reappears showing only the last phase's dialogue. The student reviewed the case to answer the *current question* — they need to see *all* the dialogue, not just the final phase.

**Where in code**: `reviewEncounter()` function — it calls `startPhase()` with only the last phase.

**Corrective procedure**:
1. In `reviewEncounter()`, build a scrollable transcript of ALL completed phases' dialogues.
2. Create a new container element (or repurpose the bubble area) that renders each phase as a labeled block:
   ```
   CHIEF COMPLAINT
   "I can't sleep anymore. It's been months..."
   
   SYMPTOM EXPLORATION
   Clinician: "Tell me more about your sleep patterns."
   "I lie awake until 3 or 4 AM. My mind won't stop..."
   ```
3. Style each phase block with the phase label as a header, clinician prompts in italic, patient dialogue in normal text.
4. Make the transcript scrollable (`overflow-y: auto; max-height: 70vh`).
5. The "Return to Question" button should still work as it does now.

**Verification**: During a question after phase 3, click "Review Case." You should see all 3 phases' dialogue in a readable transcript, not just the last phase's speech bubble.

**Adaptive notes for Claude**: If the encounter screen layout doesn't support a transcript view cleanly, consider rendering the transcript as a modal overlay on the question screen instead — this avoids the full screen switch and keeps the question visible.

---

### 2.2 Feedback panel animation snaps — `TODO`

**Priority**: Medium
**What's wrong**: `max-height: 2000px; transition: max-height .5s ease` — since actual content is ~200-300px, the transition hits full height in 10% of its duration and "coasts" for 450ms. The panel appears to snap open.

**Where in code**: CSS `.feedback-panel` / `.feedback-panel.visible` rules.

**Corrective procedure**:
Replace the max-height hack with CSS grid animation:
```css
.feedback-panel {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows .35s ease;
}
.feedback-panel > .feedback-inner {
  overflow: hidden;
}
.feedback-panel.visible {
  grid-template-rows: 1fr;
}
```
This requires wrapping the feedback content in a `.feedback-inner` div if not already wrapped.

**Verification**: Answer a question. The feedback panel should smoothly unfold to its exact content height — no snap, no coast.

**Adaptive notes for Claude**: If the grid animation approach causes issues in Safari/iOS, fall back to `max-height` but calculate the actual content height with JS: `el.style.maxHeight = el.scrollHeight + 'px'`.

---

### 2.3 Explanation renders as plain text — `TODO`

**Priority**: High
**What's wrong**: `document.getElementById('feedback-explanation').textContent = q.explanation` — renders as raw unformatted text. EPPP explanations often include DSM criteria references, clinical terms that should be italicized, and comparisons.

**Where in code**: `showFeedback()` function, explanation rendering line.

**Corrective procedure**:
1. Change `textContent` to `innerHTML`.
2. The data is already sanitized (generated by `generate_presentations.py`), but add a lightweight sanitizer as a safety net:
   ```javascript
   function sanitizeExplanation(html) {
     const allowed = /<\/?(b|i|em|strong|br|sub|sup)>/gi;
     // Strip everything except allowed tags
     return html.replace(/<\/?[^>]+(>|$)/g, (match) => allowed.test(match) ? match : '');
   }
   ```
3. Apply: `explanationEl.innerHTML = sanitizeExplanation(q.explanation || '')`.
4. Also apply to `distractor_rationale` text values for consistency.

**Verification**: If an explanation contains `<em>Major Depressive Disorder</em>`, it should render in italics. If it contains a `<script>` tag (it shouldn't, but safety), the tag should be stripped.

---

### 2.4 "Review Case" / "Next" button hierarchy — `TODO`

**Priority**: High
**What's wrong**: Both `.feedback-actions` buttons have `flex: 1` — equal width. "Review Case" (secondary action) is as prominent as "Next →" (primary action), causing decision hesitation at every question.

**Where in code**: CSS `.feedback-actions` layout, `.btn-secondary` and `.btn-primary` styles.

**Corrective procedure**:
1. Change "Review Case" to `flex: 0 0 auto; padding: 13px 16px;` — it should be compact.
2. Keep "Next →" at `flex: 1` — it fills remaining space and dominates visually.
3. Ensure "Next →" is on the right (it should be, as the second DOM child in a flex row).

**Verification**: After answering a question, the "Next →" button should be ~3x wider than "Review Case" and clearly the default action.

---

### 2.5 Option letter badges too faint — `TODO`

**Priority**: Medium
**What's wrong**: The A/B/C/D letter badges in option buttons use `color: var(--text3)` — barely visible against the dark background. They provide no pre-attentive scanning signal.

**Where in code**: CSS `.option-letter` or equivalent rule.

**Corrective procedure**:
1. Change option letter color to `var(--text2)` (brighter secondary text).
2. Add a subtle background: `background: rgba(255,255,255,.06); border-radius: 4px;`.
3. Consider slightly larger font: `font-size: 13px; font-weight: 700;`.

**Verification**: Glance at the four options. The A/B/C/D letters should pop as distinct landmarks before you read the option text.

---

### 2.6 Phase context on question screen — `TODO`

**Priority**: Medium
**What's wrong**: Once the encounter screen fades out and the question screen appears, there's no signal about encounter progress. The test-taker loses spatial context.

**Where in code**: Question screen rendering in `showQuestion()` or equivalent.

**Corrective procedure**:
1. Below the case strip (patient label + setting), add a small text indicator: `"After phase 3 of 4"` or `"Encounter in progress — 3/4 phases observed"`.
2. Style: `font-size: 10px; color: var(--text3); text-align: center; margin-top: 2px;`.
3. Pull the phase count from `state.phaseIdx` and `enc.encounter.phases.length`.

**Verification**: During a question mid-encounter, you should see a small indicator telling you how many phases you've observed.

---

### 2.7 Feedback tone varies by question type — `TODO`

**Priority**: Medium
**What's wrong**: Correct/wrong feedback is always the same binary text ("Correct!" / "Incorrect — the correct answer is B") regardless of question type. A risk_assessment miss has clinical stakes that a dsm_criteria miss does not.

**Where in code**: `showFeedback()` — the correct/wrong text rendering.

**Corrective procedure**:
1. Create a `FEEDBACK_TONE` constant mapping question types to custom incorrect messages:
   ```javascript
   const FEEDBACK_TONE = {
     risk_assessment: "In clinical practice, this choice could delay crisis intervention.",
     immediate_intervention: "This patient required a different immediate response.",
     differential_diagnosis: "The differential here hinges on a key distinguishing feature.",
     dsm_criteria: "Review the specific diagnostic criteria for this disorder.",
     treatment_approach: "Consider the evidence base for this presentation.",
     default: "The correct answer is"
   };
   ```
2. When rendering an incorrect answer, prepend the type-specific tone before the correct answer reveal.
3. Keep the correct answer feedback unchanged ("Correct!").

**Verification**: Answer a risk_assessment question wrong. The feedback should mention clinical stakes, not just "Incorrect — the correct answer is B."

---

## Wave 3 — Results & Coaching — `TODO`

### 3.1 "Weakest area" callout — `TODO`

**Priority**: High
**What's wrong**: The type breakdown shows every question type but never surfaces the most actionable insight: which type was weakest this session.

**Where in code**: `buildResults()` function, after the type breakdown bars are built.

**Corrective procedure**:
1. After computing all type accuracies, find the type with the lowest percentage (minimum 2 questions in that type to be meaningful).
2. Add a callout card below the type breakdown:
   ```html
   <div class="weakest-callout">
     <span class="weakest-icon">⚡</span>
     <span class="weakest-text">Focus area: <strong>Risk Assessment</strong> — 2/5 (40%)</span>
   </div>
   ```
3. Style with a subtle amber/orange left border and background tint.
4. Only show if there's a meaningful gap (weakest type is ≥15% below average).

**Verification**: Complete a session where you deliberately miss all risk_assessment questions. The results should highlight "Risk Assessment" as a focus area.

---

### 3.2 Score ring benchmark tick — `TODO`

**Priority**: Medium
**What's wrong**: The score ring percentage has no context. Ring turns green ≥70%, orange ≥50%, red below. But there's no stated threshold, no EPPP passing benchmark visual.

**Where in code**: `buildResults()` — SVG ring rendering.

**Corrective procedure**:
1. Draw a small tick mark on the ring at 70% (the EPPP passing threshold) using a second thin SVG arc or a small line.
2. Add a secondary label below the score: `"EPPP target: 70%"` in `var(--text3)`, `font-size: 10px`.
3. Keep the current color thresholds.

**Verification**: Score 65%. The ring should be orange, and a small tick mark at 70% should be visible, showing how close you are to the target.

---

### 3.3 Replay list partial outcome — `TODO`

**Priority**: Low
**What's wrong**: Replay list shows outcome as `✓` or `✗`. The `~` partial symbol (some correct, not all) is never used even though the CSS `.partial` class exists.

**Where in code**: `buildResults()` — replay list rendering.

**Corrective procedure**:
1. When computing the outcome character, check if the encounter had multiple questions with mixed results.
2. If some correct and some wrong: use `~` with class `partial` (styled in yellow/amber).
3. Show fraction next to the outcome: `✓ 2/2` or `~ 1/2` or `✗ 0/2`.

**Verification**: Complete an encounter with 2 questions, get one right and one wrong. The replay list should show `~ 1/2` in yellow.

---

### 3.4 Results headings for doctoral level — `TODO`

**Priority**: Low
**What's wrong**: "Great Work!" at ≥80% feels patronizing for a doctoral-level EPPP candidate.

**Where in code**: `buildResults()` — heading text logic.

**Corrective procedure**:
Change to:
- ≥80%: `"Strong <em>Session</em>"`
- ≥60%: `"Session <em>Complete</em>"` (keep)
- <60%: `"Review <em>Flagged Cases</em>"`

---

### 3.5 Bar animation timing — `TODO`

**Priority**: Low
**What's wrong**: Type breakdown bars animate via `setTimeout(200)` — they start animating while the results card is still fading in (`fadeInUp .5s`), so animations fight for attention.

**Where in code**: `buildResults()` — `setTimeout` that triggers bar fill.

**Corrective procedure**:
Increase the `setTimeout` delay from `200` to `700` — this lets the card fade in (500ms) and the ring begin filling (starts immediately but takes 1.2s) before bars animate as a second visual wave.

---

## Wave 4 — Settings & Session Intelligence — `TODO`

### 4.1 Historical performance on settings page — `TODO`

**Priority**: High
**What's wrong**: Test-taker configures a session with no signal of past performance. The data is in localStorage but never displayed.

**Where in code**: `clinical-presentation-settings.html` — the domain card rendering area.

**Corrective procedure**:
1. On settings page load, read `encounter_scores` (or whatever the localStorage key is) for each domain.
2. Below the page header, add a small performance banner:
   ```
   Your performance: CPAT 74% · PTHE 61% · 3 sessions completed
   ```
3. Style: `font-size: 12px; color: var(--text3); text-align: center; padding: 8px; background: rgba(255,255,255,.03); border-radius: 8px; margin-bottom: 16px;`.
4. Show "No sessions yet" if localStorage is empty.

**Verification**: Complete a session, return to settings. You should see your accuracy per domain.

---

### 4.2 Speed labels describe the experience — `TODO`

**Priority**: Medium
**What's wrong**: "Normal — 30ms/char" is meaningless to a test-taker. The sublabel exists but says "Default — Recommended" instead of describing the feel.

**Where in code**: `clinical-presentation-settings.html` — speed option rendering.

**Corrective procedure**:
Change sublabels to:
- **Slow**: "Patient speaks slowly, ~3 s pause between scenes"
- **Normal**: "Natural pacing, ~1.5 s pause between scenes"
- **Fast**: "Rapid presentation, ~0.5 s pause"
- **Manual**: "You control every phase advance with a button click"

---

### 4.3 Domain cards show encounter counts — `TODO`

**Priority**: Medium
**What's wrong**: Domain cards show a category label ("Diagnostic clinical encounters") but no count. Test-takers should know how many encounters exist in each domain.

**Where in code**: `clinical-presentation-settings.html` — domain card rendering.

**Corrective procedure**:
1. Either hardcode approximate counts per domain (from the data files) or dynamically fetch and count on page load.
2. Show next to domain name: `"CPAT — ~30 encounters"`.
3. If dynamic: fetch each `{DOMAIN}_presentations.json`, count `encounters.length`, cache in a variable.

**Adaptive notes for Claude**: If fetching all 9 JSON files on settings page load is too slow, hardcode counts and update them when new data is generated. Add a comment noting the counts should be updated when `generate_presentations.py` runs.

---

### 4.4 "Resume last session" — `TODO`

**Priority**: High
**What's wrong**: No way to continue from where you left off. If localStorage has stored progress, the settings page should offer to resume.

**Where in code**: `clinical-presentation-settings.html` — add new section above domain selection.

**Corrective procedure**:
1. On page load, check localStorage for any in-progress session data (partial scores, last configuration).
2. If found, show a banner:
   ```html
   <div class="resume-banner">
     Last session: CPAT · 8/10 correct · <a href="clinical-presentation-exercise.html?resume=1">Resume</a>
   </div>
   ```
3. The exercise page should check for `?resume=1` and reload the saved session state instead of starting fresh.
4. Style the banner prominently — it should be the first thing the returning user sees.

**Adaptive notes for Claude**: This requires saving session state (pool, current encounter index, answers) to localStorage during the session, not just scores. The mid-session persistence (Wave 0 item 0.8) already saves scores — extend it to save full session state.

---

### 4.5 "Mixed Domains" prominence — `TODO`

**Priority**: Medium
**What's wrong**: The mixed-domain option is a dashed-border tab below the domain grid. It's visually de-emphasized when it's arguably the most clinically valid practice mode (real EPPP cases don't announce their domain).

**Where in code**: `clinical-presentation-settings.html` — mixed domains UI element.

**Corrective procedure**:
1. Move "Mixed Domains" to above the domain grid as a prominent option.
2. Style it as a solid-border card (not dashed) with an indigo accent.
3. Add subtitle: "Practice without domain hints — like the real EPPP."
4. Keep individual domain cards below as a "Target specific domains" section.

---

## Wave 5 — World-Class Enhancements — `TODO`

### 5.1 Patient-specific avatar appearance — `TODO`

**Priority**: Very High (highest single-item impact)
**What's wrong**: "Adult Female, 34" and "Young Adult Male, 22" produce the same avatar — same hair, skin, clothing. The SVG infrastructure supports variation (separate hair, face, body groups) but it's never used.

**Where in code**:
- SVG: `#avatar-hair`, `#avatar-face`, `#avatar-body` groups in the inline SVG.
- JS: Would need a new `configureAvatar(patient)` function called in `startEncounter()`.

**Corrective procedure**:
1. Define appearance presets:
   ```javascript
   const AVATAR_PRESETS = {
     skin: {
       light:  { face: '#f5d0a9', body: '#e8c49a' },
       medium: { face: '#c68e5b', body: '#b37d4a' },
       dark:   { face: '#8b5e3c', body: '#7a4d2b' }
     },
     hair: {
       short:  'M75 58 Q100 45 125 58 L123 72 Q100 65 77 72 Z',
       medium: 'M70 58 Q100 40 130 58 L130 90 Q100 75 70 90 Z',
       long:   'M68 58 Q100 38 132 58 L135 115 Q100 95 65 115 Z'
     },
     hairColor: {
       dark:   '#2c1810',
       brown:  '#5c3a1e',
       light:  '#a0784c',
       grey:   '#8a8a8a'
     }
   };
   ```
2. Parse `patient.label` for age/gender tokens:
   - "Adult Female, 34" → female, age 34 → medium hair, random skin
   - "Elderly Male, 72" → male, age 72 → short hair, grey hair color, slight forward lean
   - "Young Adult Male, 22" → male, age 22 → short hair, random skin
3. Create `configureAvatar(patient)` that:
   - Selects skin tone (random from 3, consistent per encounter via hash of patient label)
   - Selects hair style based on parsed gender (short for male, medium/long for female)
   - Selects hair color based on age (grey for 60+)
   - Applies by setting fill colors and path `d` attributes on SVG elements
4. Call `configureAvatar(enc.encounter.patient)` at the start of `startEncounter()`, before phase 1.

**Verification**: Run 3 different encounters. Each avatar should look visibly different — different skin tone, different hair. An elderly patient should have grey hair.

**Adaptive notes for Claude**: The SVG element IDs (`#avatar-hair`, `#avatar-face`, etc.) may differ from these names — inspect the actual SVG in the file to get correct IDs. Hair morphing via path `d` attribute swap is the simplest approach. If the SVG doesn't have a separate hair element, you may need to add one.

---

### 5.2 Clinician probe as distinct voice — `TODO`

**Priority**: Medium
**What's wrong**: The clinician's prompt renders as text with an indigo border, but it doesn't *feel* like a voice. There's no temporal separation — the 400ms pause happens, dots appear, then patient speaks. The clinician's words arrive simultaneously with the bubble.

**Where in code**: `startPhase()` — probe rendering and typewriter initiation.

**Corrective procedure**:
1. Show the clinician probe text first (with its own brief typewriter effect at 2x speed, ~15ms/char).
2. After probe typewriter completes, pause 600ms.
3. Then show the patient thinking dots and begin patient typewriter.
4. This creates a turn-taking rhythm: clinician speaks → pause → patient responds.

**Verification**: During a phase with a clinician prompt, you should perceive two distinct speaking turns — clinician first, then patient — not simultaneous text.

---

### 5.3 Phase transcript accordion on question screen — `TODO`

**Priority**: High
**What's wrong**: When answering a question, the student must remember everything the patient said. There's no way to review the encounter dialogue without switching screens. In clinical reality, case notes are in front of you.

**Where in code**: Question screen HTML and `showQuestion()` function.

**Corrective procedure**:
1. Below the case strip on the question screen, add a collapsible accordion: "Review encounter notes ▾".
2. When expanded, show a text-only transcript of all completed phases (same format as Wave 2 item 2.1).
3. Collapsed by default to avoid cluttering the question.
4. Style: max-height: 200px, overflow-y: auto, background: rgba(255,255,255,.03).

**Verification**: During a question, click "Review encounter notes." A compact transcript of all phase dialogues should appear without leaving the question screen.

---

### 5.4 Subdomain-level weakest-first ordering — `TODO`

**Priority**: Medium
**What's wrong**: The `weakest` ordering operates at domain level only. A student weak in CPAT/Psychotic Disorders but strong in CPAT/Mood Disorders gets a random mix from CPAT.

**Where in code**: Session ordering logic — likely in the exercise page's encounter pool sorting.

**Corrective procedure**:
1. In `persistScores()`, store accuracy per subdomain (not just per domain):
   ```javascript
   // Key: "CPAT/Mood Disorders" → { correct: 5, total: 8 }
   ```
2. In the encounter pool sorting (when order is `weakest`), sort by subdomain accuracy instead of domain accuracy.
3. Fall back to domain accuracy for subdomains with no history.

**Verification**: Complete 10 encounters in CPAT, getting all Mood Disorders right and all Psychotic Disorders wrong. On next session with `weakest` order, Psychotic Disorders encounters should appear first.

---

## Architectural Notes for Future Claude Sessions

### File structure
- **Exercise page**: `clinical-presentation-exercise.html` — single-file app, ~2500 lines, CSS + SVG + JS all inline.
- **Settings page**: `clinical-presentation-settings.html` — separate file, ~270 lines.
- **Data files**: `data/{DOMAIN}_presentations.json` — 9 domain files.
- **Generator**: `generate_presentations.py` — creates the JSON data files.
- **Existing roadmap**: `CLINICAL_PRESENTATION_ROADMAP.md` — original build specification (architecture, data schema, chunk plan). Still valid as reference for data schema and module identity.

### CSS custom properties (design tokens)
```
--bg:           #0a0a0f    (page background)
--bg2:          #12121a    (card/panel background)
--bg3:          #1a1a24    (elevated surface)
--surface:      #16161e    (content surface)
--border:       rgba(255,255,255,.06)
--text:         #e8e8ed    (primary text — white)
--text2:        #a8a8b3    (secondary text)
--text3:        #6b6b78    (muted text)
--accent:       #6366f1    (indigo — module accent)
--accent-light: #818cf8
--accent-dark:  #4f46e5
--green:        #34d399
--red:          #f87171
--orange:       #fb923c
--blue:         #60a5fa
--purple:       #a78bfa
```

### State machine
The exercise page is a state machine with three screens:
1. `#screen-encounter` — phases play sequentially, each with typewriter + chart reveal + tags
2. `#screen-question` — questions appear between or after phases
3. `#screen-results` — final score + replay

State object (`state`) tracks: `pool`, `encIdx`, `steps`, `stepIdx`, `phaseIdx`, `avatarState`, `typewriterInt`, `phaseRunning`, `answered`, `sessionAnswers`, `reviewMode`.

### Key functions
- `startEncounter(enc)` — initializes encounter, builds chart, seeds appearance tags, starts first phase
- `startPhase(phase)` — sets avatar state, runs clinician probe, runs typewriter, reveals chart rows + tags
- `advancePhase()` / `advanceStep()` — state machine progression
- `showQuestion(q)` — renders question card
- `selectAnswer(letter)` — records answer, calls persistScores and showFeedback
- `showFeedback(q, isCorrect)` — renders explanation + distractor rationale
- `buildResults()` — renders score ring, type breakdown, replay list
- `setAvatarState(emotion)` — applies CSS class + mouth morph
- `runTypewriter(text, charMs, onComplete)` — character-by-character typing with jaw animation
- `revealBehavioralTags(tags, isAppearance)` — staggered tag reveal in two columns
- `buildChartSections(enc)` — builds chart panel with intake + category sections
- `persistScores()` — saves to localStorage

### Data schema quick reference
```
encounter.patient.label         → "Adult Female, 34"
encounter.patient.appearance_tags → ["disheveled", "poor eye contact"]
encounter.setting               → "Outpatient mental health clinic"
encounter.referral_context      → "Self-referred after urging from spouse"
encounter.phases[].phase_label  → "CHIEF COMPLAINT"
encounter.phases[].clinician_prompt → "What brings you in today?"
encounter.phases[].dialogue     → "I can't sleep anymore..."
encounter.phases[].avatar_emotion → "distressed"
encounter.phases[].behavioral_tags → ["psychomotor slowing"]
encounter.phases[].chart_data[].category → "Mood & Affect"
encounter.phases[].chart_data[].key → "Affect"
encounter.phases[].chart_data[].value → "Constricted, tearful"
encounter.questions[].type      → "dsm_criteria" | "differential_diagnosis" | etc.
encounter.questions[].correct_answer → "B"
encounter.questions[].explanation → "..."
encounter.questions[].distractor_rationale → { A: "...", B: "...", C: "...", D: "..." }
```

### Testing procedure
After any modification:
1. Start a local server: `python -m http.server 8080` in the repo root.
2. Open: `http://localhost:8080/clinical-presentation-exercise.html?domains=CPAT&levels=1,2,3,4&count=3&order=shuffled&speed=normal&tags=1&chart=1`
3. Verify: encounter loads, avatar animates, tags appear, chart fills, questions render, feedback shows, results display.
4. Test keyboard: Space advances phase, Escape skips typewriter, A/B/C/D selects answer.
5. Test edge cases: browser refresh mid-session (scores should persist), Review Case button, replay from results.

### Non-negotiable constraints
- **Single-file architecture**: The exercise page is a single HTML file with inline CSS and JS. Do not split into separate files.
- **No build tools**: No webpack, no npm, no bundler. Raw HTML/CSS/JS served statically.
- **No external dependencies**: No React, no jQuery, no CSS frameworks. Everything is vanilla.
- **Dark theme only**: The module uses a dark theme matching the rest of MasteryPage. Do not add light mode.
- **Mobile-responsive**: All changes must work on mobile (375px width minimum).
- **Performance**: The file loads in <1s on a local server. Keep it fast — no heavy libraries.

---

## Appendix: Rejected or Deferred Ideas

These were considered but are not currently planned:

- **Ambient sound effects** (breathing, pen scratching) — too gimmicky for a study tool, distracting in library/café settings.
- **Timer pressure on questions** — EPPP is not timed per-question; adding artificial time pressure misrepresents the exam.
- **AI-generated follow-up questions** — requires API calls, adds latency, breaks the offline-capable design.
- **3D avatar** — massively increases complexity for marginal benefit over well-animated 2D SVG.

---

*This document should be updated after each implementation session. When all items in a wave are DONE, update the Status Dashboard and move to the next wave.*
