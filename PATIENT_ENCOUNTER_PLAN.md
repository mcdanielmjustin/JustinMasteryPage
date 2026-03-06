# Patient Encounter Module — Implementation Plan

**Document type:** Active working plan — use this as session reference
**Module:** Patient Encounter (`clinical-presentation-exercise.html` + `clinical-presentation-settings.html`)
**Repo:** `mcdanielmjustin/JustinMasteryPage`
**Compiled:** 2026-03-05 — fresh full scrutiny of both files + all 9 data files
**Relationship to prior doc:** `PATIENT_ENCOUNTER_ELEVATION.md` remains the reference for
items T1–T9 (all DONE) and contains detailed corrective procedures for most items below.
This document consolidates, re-prioritizes, and adds newly discovered issues.

---

## How to Use This Document

This is the **active queue**. The ELEVATION.md document has the step-by-step corrective
procedures for each item. When implementing:

1. Find the item ID here
2. Go to the matching section in `PATIENT_ENCOUNTER_ELEVATION.md` for the exact code
3. Read the target file section before editing — never edit blind
4. Sanity-check after: `node -e "require('fs').readFileSync('clinical-presentation-exercise.html','utf8'); console.log('OK')"`
5. Commit after each session group, not each individual edit

Items with ★ have corrective procedures written here (not in ELEVATION.md) because they
are newly discovered in this scrutiny. All others defer to ELEVATION.md for procedure.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ DONE | Implemented and committed |
| 🔲 PENDING | Not yet implemented |
| 🔶 PARTIAL | Started, needs follow-up |
| ⚠️ RISK | High-risk — confirm before implementing |
| ★ NEW | Not in ELEVATION.md — procedure below |

---

## Architecture Quick Reference

```
clinical-presentation-settings.html    — session config page
clinical-presentation-exercise.html    — engine (~2500 lines)
data/{DOMAIN}_presentations.json       — encounter data (9 domains)
generate_presentations.py              — Claude API generator
PATIENT_ENCOUNTER_ELEVATION.md         — detailed corrective procedures (T1–T9 done, rest pending)
```

**Actual encounter counts (verified 2026-03-05):**

| Domain | Encounters | L1 | L2 | L3 | L4 |
|--------|-----------|----|----|----|----|
| BPSY   | 32        | 5  | 13 | 9  | 5  |
| CASS   | 30        | 5  | 11 | 5  | 9  |
| CPAT   | 32        | 5  | 12 | 7  | 8  |
| LDEV   | 32        | 5  | 12 | 7  | 8  |
| PETH   | 38        | 5  | 13 | 11 | 9  |
| PMET   | 30        | 5  | 11 | 5  | 9  |
| PTHE   | 32        | 5  | 13 | 6  | 8  |
| SOCU   | 30        | 5  | 11 | 6  | 8  |
| WDEV   | 30        | 5  | 11 | 7  | 7  |
| **Total** | **286** | **45** | **107** | **63** | **71** |

**Key structural fact:** Each encounter has exactly 3 phases and 2 questions.
286 encounters → 572 total questions across all domains.

---

---

# PART A — CRITICAL BUGS (fix before anything else)

---

## BUG-1 ★ — `persistScores()` double-counts every session
**Status:** 🔲 PENDING
**File:** `clinical-presentation-exercise.html`
**Severity:** High — inflates all domain accuracy scores; corrupts Weakest First ordering

**Problem:** `T9` (implemented) calls `persistScores()` after every answered question.
But `nextEncounterOrResults()` still also calls `persistScores()` at session end (the
original behavior). Every answer in a session is counted twice in localStorage.

**Fix:**
Find `nextEncounterOrResults` in the exercise JS. Remove the `persistScores()` call inside
it. The per-question call (from T9) is sufficient.

```js
// In nextEncounterOrResults(), find and remove this line:
persistScores();
```

Verify by answering 3 questions and checking localStorage:
```js
JSON.parse(localStorage.getItem('encounter_scores'))
// domain.total should equal number of questions answered, not 2×
```

---

## BUG-2 — `replayEncounter` state corruption
**Status:** 🔲 PENDING
**File:** `clinical-presentation-exercise.html`
**Severity:** High — crashes or produces wrong content when replaying from results screen
**Procedure:** See ELEVATION.md → T10

---

## BUG-3 ★ — Pool exhaustion silently delivers fewer encounters than requested
**Status:** 🔲 PENDING
**File:** `clinical-presentation-exercise.html`
**Severity:** Medium — user confusion

**Problem:** If a user selects L1 + CASS (only 5 L1 encounters), requests 10, the session
quietly delivers 5 with no message. The nav badge still shows "Encounter 5 of 10" only
because it derives from `pool.length` — actually it will show "Encounter 5 of 5" but the
user configured 10 and doesn't understand the discrepancy.

**Fix:**
In `loadEncounters()`, after `pool = pool.slice(0, CFG.count)`, add:
```js
if (pool.length < CFG.count) {
  const status = document.getElementById('loader-status');
  if (status) {
    status.textContent =
      `${pool.length} encounters available for your selection (${CFG.count} requested)`;
    status.style.color = 'var(--orange)';
  }
  // Brief pause so user sees the message before encounter starts
  await new Promise(r => setTimeout(r, 1800));
}
```

---

## BUG-4 ★ — `persistScores()` double-count on session end (corollary of BUG-1)
**Status:** 🔲 PENDING (same fix as BUG-1, listed separately for clarity)

This is the same issue. Fixing BUG-1 fixes BUG-4. Only one commit needed.

---

---

# PART B — SETTINGS PAGE (clinical-presentation-settings.html)

---

## SET-1 — Domain cards show descriptions, not encounter counts
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX25
**Note:** ELEVATION.md suggests hardcoding "30 encounters" but actual counts vary (30–38).
**Updated approach:** Load counts dynamically from JSON. Actual counts:
- BPSY: 32, CASS: 30, CPAT: 32, LDEV: 32, PETH: 38, PMET: 30, PTHE: 32, SOCU: 30, WDEV: 30

Either hardcode the accurate per-domain number or use the dynamic fetch from UX25.
The dynamic approach is preferred so it stays accurate after regeneration.

---

## SET-2 ★ — No "Select All Levels" shortcut
**Status:** 🔲 PENDING
**File:** `clinical-presentation-settings.html`

**Problem:** Domain section has a "Select all" / "Deselect all" toggle button.
Level section has no equivalent. A user wanting all 4 levels must click 4 cards.
Inconsistent UX with the domain section.

**Fix:**
In the settings HTML, add a select-all button to the level section header:
```html
<div class="section-header">
  <div class="section-label">Difficulty Level</div>
  <button class="select-all-btn" id="level-all-btn" onclick="toggleAllLevels()">Select all</button>
</div>
```

JS:
```js
function toggleAllLevels() {
  const cards = document.querySelectorAll('.level-card');
  const allSelected = [...cards].every(c => c.classList.contains('selected'));
  cards.forEach(card => {
    const lvl = card.dataset.level;
    if (allSelected) { card.classList.remove('selected'); state.levels.delete(lvl); }
    else             { card.classList.add('selected');    state.levels.add(lvl); }
  });
  document.getElementById('level-all-btn').textContent = allSelected ? 'Select all' : 'Deselect all';
  updateSummary();
}
```

---

## SET-3 — Historical performance banner on settings page
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX23

---

## SET-4 — Resume last session
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX26

---

## SET-5 — Mixed Domains visually de-emphasized
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX27

---

## SET-6 — Speed card sublabels don't describe the experience
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX24

---

## SET-7 ★ — No validation feedback when count exceeds pool size
**Status:** 🔲 PENDING
**File:** `clinical-presentation-settings.html`

**Problem:** The settings page has no way to know whether the user's selected
level+domain combination contains enough encounters to fill the requested count.
This is related to BUG-3 but is the settings-side prevention.

**Fix:** This is handled by BUG-3 in the exercise page (shows message after loading).
On the settings page, optionally show a soft warning if count=20 and only 1 domain + L1
are selected (which yields 5 encounters). This requires the same dynamic fetch as SET-1.
Implement as part of the dynamic count load — once counts are loaded, add a
`updateCountWarning()` call that fires when domain or level selection changes.

**Dependency:** Implement after SET-1 (dynamic count loading).

---

---

# PART C — READING QUALITY (highest immediate impact, exercise page)

These five items cost ~30–60 minutes and make the primary content readable.
All procedures are in ELEVATION.md.

---

## READ-1 — Bubble text too small and secondary color
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX3
**Impact:** The patient's words are the primary content. This is a tier-1 fix.

---

## READ-2 — Speech bubble too transparent
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX2

---

## READ-3 — Option letter badges too faint
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX11

---

## READ-4 — "Select the best answer" label
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX12
**Note:** Replace with A/B/C/D keyboard hint as described in UX12.

---

## READ-5 — "Review Case" and "Next →" equal width
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → T13 / UX15

---

---

# PART D — FEEDBACK DEPTH

These make the learning moment (post-question feedback) more clinically rigorous.

---

## FEED-1 — Explanation renders as plain text, cannot format clinical content
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX14
**Note:** Implement `safeHtml()` sanitizer as described. Do NOT use raw innerHTML.

---

## FEED-2 — Feedback tone same regardless of question type
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX17

---

## FEED-3 — Weakest area callout missing from results screen
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX22

---

---

# PART E — LAYOUT AND ENCOUNTER IMMERSION

---

## LAYOUT-1 — Clinician probe inside patient bubble
**Status:** 🔶 PARTIAL (styled, not structurally fixed)
**Procedure:** See ELEVATION.md → UX4
**Note:** This is the most structurally complex layout change. It touches HTML + JS
in three places (`startPhase()`, `startEncounter()`, and HTML structure). Read the
implementation note in ELEVATION.md carefully before starting. Search all occurrences
of `getElementById('clinician-probe')` first.

---

## LAYOUT-2 — Avatar too small; patient stage mostly empty
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX1
**Note:** Only requires changing `.avatar-wrap` dimensions. SVG scales automatically.

---

## LAYOUT-3 — Patient info bar priorities reversed
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX5

---

## LAYOUT-4 — Phase label needs pill treatment
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX9

---

## LAYOUT-5 — Phase controls footer blends into chart
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX8

---

## LAYOUT-6 ★ — Mobile layout breaks: 2-column grid collapses on narrow screens
**Status:** 🔲 PENDING
**File:** `clinical-presentation-exercise.html`

**Problem:** `.encounter-layout` uses `grid-template-columns: 1fr 320px`. On screens
narrower than ~600px, the patient-stage + chart-panel side-by-side layout is unusable.
The only mobile adaptation currently is reducing `.avatar-wrap` dimensions. The chart
panel, phase controls, and speech bubble are never hidden or reflowed for mobile.

**Fix:**
Add a mobile breakpoint that stacks the layout vertically and hides the chart panel behind
a toggle. At ≤760px:
```css
@media (max-width: 760px) {
  .encounter-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    height: auto;
    min-height: calc(100vh - 58px);
  }
  .chart-panel {
    display: none;  /* chart off by default on mobile */
  }
  .chart-panel.mobile-visible {
    display: flex;
    position: fixed;
    inset: 58px 0 0 0;
    z-index: 50;
    background: var(--surface);
  }
  .patient-stage {
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}
```

Add a chart toggle button in the nav on mobile:
```js
// On mobile, inject a chart toggle button into .nav-right
if (window.innerWidth <= 760) {
  const chartToggle = document.createElement('button');
  chartToggle.id = 'chart-toggle-btn';
  chartToggle.className = 'chart-toggle-btn';
  chartToggle.textContent = 'Chart';
  chartToggle.onclick = () => {
    document.querySelector('.chart-panel').classList.toggle('mobile-visible');
  };
  document.querySelector('.nav-right').prepend(chartToggle);
}
```

This keeps the encounter playable on mobile without requiring full responsive redesign.
Implement after LAYOUT-2 (avatar size) so both mobile changes are batched.

---

## LAYOUT-7 — No momentum signal on question screen showing you're mid-encounter
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX16

---

---

# PART F — ANIMATION AND TIMING

---

## ANIM-1 — Feedback panel snaps open instead of unfolding
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX13
**Note:** Must add `overflow: hidden` to `.feedback-inner` or the grid animation won't clip.

---

## ANIM-2 — Question screen options all arrive simultaneously
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX10

---

## ANIM-3 — Results bar animations fight card entry animation
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX21

---

## ANIM-4 — Auto-advance bar too thin and too low on footer
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX7
**Note:** Move bar from `position: absolute; bottom: 0` to `top: 0` as described.

---

## ANIM-5 — Same-phase behavioral tags split to opposite columns
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX6
**Note:** After implementing, visually verify by running a multi-tag encounter.

---

---

# PART G — RESULTS SCREEN

---

## RES-1 — Score ring has no 70% benchmark marker
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX20

---

## RES-2 — Partial encounter outcome never indicated in replay list
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX19

---

## RES-3 — Results headings use elementary-school framing
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX18

---

## RES-4 — Empty state missing on replay list
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX28

---

---

# PART H — TECHNICAL DEBT

---

## TECH-1 — "Weakest First" sort at domain level only, not subdomain
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → T11

---

## TECH-2 — "Review Case" shows only last phase; needs full transcript
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → T12 / UX29
**Note:** Speech bubble must get `max-height: 55vh; overflow-y: auto` before adding transcript.

---

## TECH-3 — No click-to-skip affordance on speech bubble
**Status:** 🔲 PENDING
**Procedure:** See ELEVATION.md → UX30

---

---

# PART I — CONTENT (DATA LAYER)

---

## CONTENT-1 ★ — L1 sparsity: only 5 encounters per domain at Foundational level
**Status:** 🔲 PENDING — requires regeneration

**Problem:** Every domain has exactly 5 L1 (Foundational) encounters. A user selecting
L1-only across multiple domains gets 45 encounters total. Selecting L1 + one domain
gets only 5 — exhausted in a single 5-encounter session. The learning value of L1 is
high: new learners need clean, textbook-presentation cases to build pattern recognition.

**Target:** 10–15 L1 encounters per domain (currently 5).

**Action:** When running `generate_presentations.py`, increase L1 target from 5 to 12.
Update the generation prompt to specify "at least 12 Level 1 encounters per domain."
Run with `--all --resume` to append to existing files without overwriting L2–L4.

**Priority:** Medium — content generation, not code. Run in a dedicated generation session.

---

## CONTENT-2 ★ — PETH outlier: 38 encounters vs. 30 for other domains
**Status:** informational / no action needed

PETH has 38 encounters while all others have 30–32. This is acceptable and actually
beneficial given PETH covers two major topics (pharmacology + ethics). No action needed.
Note: SET-1 (dynamic count loading) will handle the UI display correctly.

---

## CONTENT-3 ★ — Question type distribution unknown; potential type gaps
**Status:** 🔲 PENDING — audit needed

**Problem:** Each encounter has 2 questions. The types seen include:
`differential_diagnosis`, `immediate_intervention`, `primary_diagnosis`, `dsm_criteria`,
`cultural_consideration`, `assessment_tool`, `treatment_planning`, `risk_assessment`.
But the distribution across domains and levels is unknown. Some types (e.g., `risk_assessment`)
may be underrepresented in non-clinical domains (PMET, WDEV, SOCU) leading to artificial
type-based weakness signals.

**Action:**
```bash
python -c "
import json, os
from collections import Counter
types = Counter()
for f in os.listdir('data'):
    if not f.endswith('_presentations.json'): continue
    d = json.load(open(f'data/{f}', encoding='utf-8'))
    for enc in d['encounters']:
        for q in enc.get('questions', []):
            types[q.get('type', '?')] += 1
print(types.most_common())
"
```
Run this audit, then assess whether any type is missing from any domain.
If `risk_assessment` never appears in PMET, the type-based weakness results UI (FEED-3)
will unfairly flag PMET users who have simply never seen that type.

---

## CONTENT-4 ★ — Phase count fixed at 3; no variety in encounter depth
**Status:** informational / low priority

All 286 encounters have exactly 3 phases. This creates a uniform rhythm that can feel
mechanical after many sessions. Adding a small number of 2-phase encounters (simple,
clear presentations) and 4-phase encounters (complex, multi-symptom unfolding) would
increase variety. This is a generator-level change for a future generation cycle.

---

---

# IMPLEMENTATION SESSIONS

Implement in this order. Each session is self-contained.

---

## Session 1 — Critical Bugs (30–45 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** BUG-1 (double persistScores), BUG-2 (replayEncounter corruption), BUG-3 (pool exhaustion warning)

**Implementation order:**
1. Find `nextEncounterOrResults` → remove the `persistScores()` call inside it (BUG-1)
2. Find `replayEncounter()` → add the state reset lines (BUG-2, procedure in ELEVATION T10)
3. Find `loadEncounters()` pool slice → add count warning (BUG-3)
4. Verify: open DevTools, run a 3-question session, check `localStorage.encounter_scores` total counts

**Commit message:** `fix: remove persistScores double-count; fix replayEncounter state; add pool warning`

---

## Session 2 — Reading Quality (30–60 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** READ-1, READ-2, READ-3, READ-4, READ-5

**Implementation order:**
1. Bubble background + border + box-shadow (UX2/READ-2) — CSS only
2. Bubble text color + size + line-height (UX3/READ-1) — CSS only
3. Option letter badge brightness (UX11/READ-3) — CSS only
4. Remove "Select the best answer" label (UX12/READ-4) — HTML + optional kbd hint
5. Review Case button not flex:1 (T13/READ-5) — CSS only

All five are CSS-only or minimal HTML. Do them in one pass on the style block.

**Commit message:** `style: improve reading quality — bubble, option letters, feedback hierarchy`

---

## Session 3 — Settings Page (45 min)
**Files:** `clinical-presentation-settings.html`
**Items:** SET-1 (dynamic counts), SET-2 (level select-all), SET-3 (history banner), SET-6 (speed sublabels)

**Implementation order:**
1. Add `toggleAllLevels()` JS + "Select all" button to level section (SET-2) — self-contained
2. Update speed sublabels to show actual timing values (SET-6) — HTML only
3. Update domain card counts — use dynamic fetch approach (SET-1)
4. Add history banner `div` + `renderHistoryBanner()` JS (SET-3, procedure in ELEVATION UX23)

**Commit message:** `feat(settings): level select-all, dynamic domain counts, history banner, speed labels`

---

## Session 4 — Feedback Depth (30 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** FEED-1 (innerHTML explanation), FEED-2 (type-specific wrong answers), FEED-3 (weakest callout)

**Implementation order:**
1. Add `safeHtml()` function near top of JS (ELEVATION UX14 procedure)
2. Replace `textContent` with `safeHtml()` for explanation field (ELEVATION UX14)
3. Add `WRONG_PREFIX` object + type-specific feedback (ELEVATION UX17/FEED-2)
4. Add weakest-area callout after type breakdown in `buildResults()` (ELEVATION UX22/FEED-3)

**Commit message:** `feat: typed feedback text, safeHtml explanation renderer, weakest-area callout`

---

## Session 5 — Layout and Immersion (60 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** LAYOUT-2 (avatar size), LAYOUT-3 (patient info bar), LAYOUT-4 (phase pill), LAYOUT-5 (footer bg), LAYOUT-7 (momentum signal)

**Implementation order:**
1. Avatar wrap dimensions increase (ELEVATION UX1/LAYOUT-2) — CSS only
2. Patient info bar order swap + width alignment (ELEVATION UX5/LAYOUT-3) — CSS + HTML
3. Phase label pill CSS (ELEVATION UX9/LAYOUT-4) — CSS only
4. Phase controls footer background (ELEVATION UX8/LAYOUT-5) — CSS only
5. Case-phase-progress indicator on question screen (ELEVATION UX16/LAYOUT-7) — HTML + JS

**Commit message:** `style(layout): larger avatar, info bar order, phase pill, footer contrast, momentum indicator`

---

## Session 6 — Clinician Probe Restructure (45 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** LAYOUT-1

**This session is dedicated entirely to UX4** because it is the most structurally invasive
change and requires coordinated edits across HTML, CSS, and JS.

**Steps:**
1. Read ELEVATION.md → UX4 completely before touching any code
2. Search for ALL occurrences: `getElementById('clinician-probe')` — there are 3+
3. Add `.clinician-prompt-wrap` HTML element above `.speech-bubble`
4. Move probe content out of bubble into the new wrapper
5. Update JS in `startPhase()` to show/hide the new wrapper
6. Update JS in `startEncounter()` to clear the new wrapper
7. Verify on both auto-advance and manual modes
8. Verify on review mode

**Commit message:** `feat(layout): move clinician probe above patient bubble`

---

## Session 7 — Animation Quality (30 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** ANIM-1 (feedback panel grid), ANIM-2 (staggered question entrance), ANIM-3 (results timing), ANIM-4 (auto-advance bar)

**Implementation order:**
1. Auto-advance bar: height 4px, color accent-light, move to top of footer (ELEVATION UX7/ANIM-4) — CSS
2. Feedback panel grid animation (ELEVATION UX13/ANIM-1) — CSS (remember `overflow:hidden` on inner)
3. Staggered question screen entrance (ELEVATION UX10/ANIM-2) — CSS + JS reflow reset
4. Results bar animation timing (ELEVATION UX21/ANIM-3) — JS setTimeout values

**Commit message:** `style(animation): grid feedback panel, staggered options, bar timing, advance bar`

---

## Session 8 — Results Screen (30 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** RES-1 (70% ring tick), RES-2 (partial outcome), RES-3 (heading tone), RES-4 (empty state)

**Commit message:** `style(results): 70% benchmark ring, partial outcome indicator, heading tone, empty state`

---

## Session 9 — Technical Debt (45–60 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** TECH-1 (subdomain-level weakest sort), TECH-2 (full transcript review), TECH-3 (skip hint)

**Implementation order:**
1. Skip hint (ELEVATION UX30/TECH-3) — simplest, HTML + minimal JS
2. Full transcript in reviewEncounter (ELEVATION T12/TECH-2) — must set bubble max-height first
3. Subdomain-level weakest sort (ELEVATION T11/TECH-1) — requires localStorage schema extension

**Commit message:** `feat(tech): skip hint, full review transcript, subdomain weakest sort`

---

## Session 10 — Mobile Layout (45 min)
**Files:** `clinical-presentation-exercise.html`
**Items:** LAYOUT-6

**Commit message:** `feat(mobile): stacked layout, chart toggle button, narrow screen support`

---

## Session 11 — Settings Page: Resume + Mixed Reposition (30 min)
**Files:** `clinical-presentation-settings.html`
**Items:** SET-4 (resume last session), SET-5 (mixed domain repositioning)

**Commit message:** `feat(settings): resume last session, mixed domains repositioned above grid`

---

## Session 12 — Content Audit (standalone Python)
**Items:** CONTENT-3 (question type distribution audit), CONTENT-1 if warranted

Run the Python audit described in CONTENT-3. Report findings. If type gaps exist, update
`generate_presentations.py` and run targeted regeneration.

---

---

# QUALITY ASSESSMENT (reference only, no code changes)

## Question Quality — Summary

**Data structure:** Each encounter has `setting`, `referral_context`, `patient`, `phases[]`.
Each phase has `phase_label`, `dialogue`, `clinician_prompt`, `behavioral_tags[]`, `avatar_emotion`.
Each encounter has 2 questions with `type`, `prompt`, `options{A-D}`, `correct_answer`,
`explanation`, `distractor_rationale{}`.

**L1 (Foundational):** Clean, textbook presentations. Hint: behavioral_tags are explicit
clinical signals. Questions are direct (e.g., "What is the primary diagnosis?"). Appropriate
for first-pass learning.

**L2 (Intermediate):** Mild complicating factors. One or two plausible differentials.
Options are all clinically defensible; the wrong ones are wrong for specific, testable reasons.

**L3 (Advanced):** Atypical presentation. The sampled CPAT L3 (acute psychosis, 22yo male)
is clinically excellent: phases build logically, avatar emotions escalate correctly
(agitated → guarded → confused), behavioral tags per phase are precise and non-redundant,
and both questions (differential requiring ruling out Bipolar I w/psychotic features vs.
Substance-Induced; immediate intervention requiring motivational engagement over confrontation)
test exactly the clinical reasoning an EPPP candidate must demonstrate. This is high-quality.

**L4 (Expert):** Complex comorbidity. Vignette initially favors the wrong diagnosis.
Distractor rationale is detailed. Consistent with EPPP difficulty ceiling.

**Question type variety:** 8 types identified (`differential_diagnosis`, `immediate_intervention`,
`primary_diagnosis`, `dsm_criteria`, `cultural_consideration`, `assessment_tool`,
`treatment_planning`, `risk_assessment`). Distribution across domains not yet audited (see CONTENT-3).

**Overall quality verdict:** High. The encounter data is clinically appropriate, pedagogically
structured, and well-differentiated by difficulty. The primary gap is quantity (286 total
encounters, only 5 per domain at L1), not quality.

---

## Settings Page — Summary

The configuration surface is appropriate for the module's complexity. Six configuration
dimensions (levels, domains, count, speed, display options, order) are the right set.
No configuration is missing; the issues are:
1. Stale/descriptive domain counts instead of actual numbers
2. No level select-all shortcut
3. No historical context visible to returning users
4. Speed sublabels don't communicate the timing experience

All four are fixable in Session 3.

---

*End of plan. Update status fields as items are completed.*
*Commit this document to the repo after Session 1 so it persists across sessions.*
