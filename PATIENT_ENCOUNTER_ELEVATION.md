# Patient Encounter Module — Elevation Reference

**Document type:** Living reference for ongoing improvements
**Module:** Patient Encounter (`clinical-presentation-exercise.html` + `clinical-presentation-settings.html`)
**Repo:** `mcdanielmjustin/JustinMasteryPage`
**Last full scrutiny:** 2026-03-03
**Scrutinized by:** Claude Sonnet 4.6

---

## How to Use This Document

This document is a multi-session reference. It survives context compaction. When starting
a new chat to continue improvements, paste this document (or its URL) and say:
**"Continue Patient Encounter elevation from PATIENT_ENCOUNTER_ELEVATION.md."**

Each issue has:
- A clear description of the problem
- Root cause (what in the code causes it)
- Corrective procedure (specific steps to fix it)
- Implementation notes for Claude (traps to avoid, patterns to follow)
- Status: `DONE`, `PENDING`, or `PARTIAL`

Items marked `DONE` were implemented on 2026-03-03. Do not re-implement them.
Items marked `PENDING` are the active work queue.
Items marked `PARTIAL` were started but need follow-up.

When implementing, always:
1. Read the target section of the file before editing — never edit blind
2. Run a Node sanity check after editing: `node -e "require('fs').readFileSync('clinical-presentation-exercise.html','utf8')" 2>&1`
3. Commit after each logical group of fixes, not after every individual edit
4. Push to `origin/master` when the user confirms

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ DONE | Implemented and committed |
| 🔲 PENDING | Not yet implemented |
| 🔶 PARTIAL | Partially implemented, needs follow-up |
| ⚠️ RISK | High-risk change — confirm with user before implementing |

---

## Architecture Quick Reference

```
clinical-presentation-settings.html   — session configuration page
clinical-presentation-exercise.html   — full exercise engine (2492 lines as of 2026-03-03)
data/{DOMAIN}_presentations.json      — encounter data (9 domains × 30 encounters)
generate_presentations.py             — Claude API data generator
```

**Key JS globals in exercise page:**
- `CFG` — session config parsed from URL params
- `state` — runtime session state (pool, indices, scores, answers)
- `MOUTH_PATHS` — SVG path strings per avatar emotion
- `_tagCols` — tag column state `{ left: {count, els[]}, right: {count, els[]} }`
- `SPEED_CONFIG` — `{ slow, normal, fast, manual }` typewriter timing
- `TYPE_BADGE` — question type → label + color mapping

**Key functions:**
- `startEncounter(enc)` — initializes encounter: chart, tags, avatar, phases
- `startPhase(phase)` — runs typewriter, chart reveals, tag reveals, auto-advance
- `runTypewriter(text, charMs, onComplete)` — types text char-by-char, animates jaw
- `setAvatarState(emotion)` — applies CSS state class + morphs mouth path
- `revealBehavioralTags(tags, isAppearance)` — stacking-column tag renderer
- `buildChartSections(enc)` — builds chart DOM with intake section pre-populated
- `renderQuestion(q)` — populates question screen
- `selectAnswer(letter)` — scores answer, persists, calls showFeedback
- `showFeedback(q, isCorrect)` — reveals explanation + distractor rationale
- `reviewEncounter()` — static read-only replay of encounter
- `buildResults()` — populates results screen
- `advanceStep()` — advances state machine (phase → question → next encounter)

**Avatar SVG IDs:** `#avatar-root`, `#avatar-body`, `#avatar-head`, `#avatar-face`,
`#avatar-eyes`, `#avatar-brow`, `#avatar-jaw`, `#avatar-mouth`, `#avatar-tear`,
`#avatar-hand`, `#avatar-hair`, `#avatar-legs`

---

---

# PART I — TECHNICAL & FUNCTIONAL FIXES

---

## T1 — Jaw never moves during dialogue
**Status:** ✅ DONE (committed 2026-03-03)

**Problem:** `setAvatarState()` sets emotion class (e.g., `state-distressed`) but `jawSpeak`
animation lives on `.state-speaking`. The data never uses `speaking` as `avatar_emotion`
because it would override the clinical affect. Result: jaw was completely static.

**Fix applied:** `runTypewriter()` now directly animates `#avatar-jaw` via inline style
`animation: jawSpeak .32s ease-in-out infinite` at typewriter start, clears it in `onComplete`
and in the skip handler.

---

## T2 — `flat_affect` and `hopeful` states visually indistinguishable from `idle`
**Status:** ✅ DONE (committed 2026-03-03)

**Problem:**
- `flat_affect` was just `breathe 8s` — barely slower than idle
- `hopeful` was just `breathe 3.5s` — barely faster than idle
Both states are pedagogically critical (flat affect = negative symptom; hopeful = therapeutic progress).

**Fix applied:**
- `flat_affect`: `breathe 9s` + `blinkSlow 5s` on `#avatar-eyes` + `filter: saturate(0.55) brightness(0.92)` on `#avatar-face`
- `hopeful`: `postureUpright .6s ease forwards` + `breathe 3.5s` + `filter: saturate(1.15) brightness(1.04)`
- `MOUTH_PATHS` object added with distinct SVG path strings per emotion:
  - `flat_affect`: `'M91 128 Q100 128 109 128'` (geometrically flat line)
  - `hopeful`: `'M91 127 Q100 123 109 127'` (gentle smile — control point raised)
  - `distressed`: `'M91 128 Q100 134 109 128'` (pronounced frown)
  - `tearful`: `'M92 129 Q100 134 108 129'`

**`setAvatarState` now morphs `#avatar-mouth` `d` attribute on every state change.**

---

## T3 — Behavioral tags overlap after 8 tags
**Status:** ✅ DONE (committed 2026-03-03)

**Problem:** Old system had 8 preset `{ top, left/right }` positions. `_tagSlotIdx % 8`
wrapped around, placing new tags directly on top of old ones.

**Fix applied:** Replaced with two stacking columns (`left` / `right`). State object:
```js
_tagCols = { left: { count: 0, els: [] }, right: { count: 0, els: [] } };
```
- Alternates left/right by total tag count
- Each column stacks top-down with `TAG_ROW_PX = 30` spacing
- When column hits `TAG_MAX_ROWS = 7`, oldest element fades out (opacity 0, then removed)
- `resetTagColumns()` must be called in `startEncounter()` — already done

**Pending refinement (see UX6):** Same-phase tags should go to same column, not alternate.

---

## T4 — Speech bubble tail was left-aligned instead of centered
**Status:** ✅ DONE (committed 2026-03-03)

**Fix applied:** `.bubble-tail { left: 50%; transform: translateX(-50%); }` replacing `left: 18px`.

---

## T5 — Clinician probe needed visual distinction
**Status:** ✅ DONE (committed 2026-03-03)

**Fix applied:** Added indigo left-border treatment:
```css
border-left: 2px solid rgba(99,102,241,.45);
background: rgba(99,102,241,.06);
border-radius: 0 6px 6px 0;
color: var(--accent-light);
```

**Pending refinement (see UX4):** The probe is still inside the patient's speech bubble.
It should be a separate element above the bubble.

---

## T6 — `appearance_tags` silently dropped
**Status:** ✅ DONE (committed 2026-03-03)

**Problem:** `enc.encounter.patient.appearance_tags` (e.g., `["disheveled", "poor eye contact"]`)
was never rendered anywhere.

**Fix applied:** In `startEncounter()`, appearance tags are pre-seeded into the tag overlay
before phase 1 begins using `revealBehavioralTags(appearanceTags, true)` (the second
parameter `isAppearance = true` applies `.tag-appearance` class — grey italic style —
instead of the clinical color coding).

---

## T7 — `referral_context` silently dropped
**Status:** ✅ DONE (committed 2026-03-03)

**Problem:** `enc.encounter.referral_context` (rich intake note like "Self-referred after
urging from spouse") was never rendered.

**Fix applied:** `buildChartSections()` now injects a pre-populated "Intake" chart section
at the top of the chart panel with Setting and Referral rows immediately visible
(`.chart-row-intake` class — no animation, `opacity: 1`).

---

## T8 — No keyboard shortcuts on encounter screen
**Status:** ✅ DONE (committed 2026-03-03)

**Fix applied:**
- `Space` / `Enter` on encounter screen → `advancePhase()` (only when typewriter is idle and phase is not running)
- `Escape` / `Backspace` on encounter screen → clicks speech bubble (triggers skip handler)
- Question screen now also accepts `Space` for advance (was Enter-only)

---

## T9 — Score persistence only at session end
**Status:** ✅ DONE (committed 2026-03-03)

**Fix applied:** `persistScores()` is now called inside `selectAnswer()` after every question,
not only in `nextEncounterOrResults()`. Partial sessions now survive browser close.

---

## T10 — `replayEncounter` state corruption risk
**Status:** 🔲 PENDING

**Problem:** When `replayEncounter(idx)` is called from the results screen, it mutates
`state.encIdx` but does NOT reset `state.steps`, `state.stepIdx`, or `state.phaseIdx`.
These still point to wherever the previous session ended. The `reviewEncounter()` path
works because it doesn't use `state.steps`, but the `advBtn.onclick = advancePhase`
restoration in the return callback calls `advanceStep()` with stale step index.

**Corrective procedure:**
In `replayEncounter()`, after setting `state.encIdx = idx`, also set:
```js
state.phaseIdx = 0;
state.qIdx     = 0;
state.stepIdx  = 0;
state.steps    = buildSteps(state.pool[idx]);
```
This is safe because `reviewEncounter()` overrides `advBtn.onclick` anyway.

---

## T11 — `weakest` sort is domain-level only, not subdomain-level
**Status:** 🔲 PENDING

**Problem:** `sortPool()` with `order === 'weakest'` sorts by domain accuracy from
localStorage. A student weak in CPAT/Psychotic Disorders but strong in CPAT/Mood Disorders
gets random CPAT encounters rather than targeted Psychotic Disorders cases.

**Corrective procedure:**
1. In `persistScores()`, also write subdomain scores:
   ```js
   const allSub = getStoredSubdomainScores();
   state.sessionAnswers.forEach(a => {
     const key = a.domain + '::' + a.subdomain;
     allSub[key] = allSub[key] || { correct: 0, total: 0 };
     allSub[key].total++;
     if (a.correct) allSub[key].correct++;
   });
   localStorage.setItem('encounter_subdomain_scores', JSON.stringify(allSub));
   ```
2. In `sortPool()` weakest branch, sort encounters by their subdomain accuracy:
   ```js
   const subScores = getStoredSubdomainScores();
   return pool.slice().sort((a, b) => {
     const aKey = a.domain_code + '::' + a.subdomain;
     const bKey = b.domain_code + '::' + b.subdomain;
     const aA = subScores[aKey] ? subScores[aKey].correct / subScores[aKey].total : 0.5;
     const bA = subScores[bKey] ? subScores[bKey].correct / subScores[bKey].total : 0.5;
     return aA - bA;
   });
   ```

---

## T12 — `reviewEncounter()` shows only last phase dialogue
**Status:** 🔲 PENDING  (see also UX29)

**Problem:** `reviewEncounter()` renders `lastPhase.dialogue` in the speech bubble.
When a student clicks "Review Case" during a question to check their reasoning, they
need to see ALL phase dialogues as a transcript, not just the final one.

**Corrective procedure:**
Replace the static single-dialogue display in `reviewEncounter()` with a scrollable
transcript inside the bubble area:
```js
// Instead of:
document.getElementById('bubble-text').textContent = lastPhase.dialogue || '';

// Build a full transcript:
const transcript = enc.encounter.phases.map((ph, i) => {
  const probeHtml = ph.clinician_prompt
    ? `<div class="transcript-probe">Clinician: "${escapeHtml(ph.clinician_prompt)}"</div>`
    : '';
  return `<div class="transcript-phase">
    <div class="transcript-phase-label">${escapeHtml(ph.phase_label)}</div>
    ${probeHtml}
    <div class="transcript-dialogue">${escapeHtml(ph.dialogue)}</div>
  </div>`;
}).join('');
document.getElementById('bubble-text').innerHTML = transcript;
```
Add CSS for `.transcript-phase`, `.transcript-phase-label`, `.transcript-probe`,
`.transcript-dialogue` — each phase separated by a subtle border.
The speech bubble's `min-height: 60px` will need to become `max-height: 60vh; overflow-y: auto`.

---

## T13 — "Review Case" button and "Next →" are equal width — wrong hierarchy
**Status:** 🔲 PENDING  (see also UX15)

**Problem:** In `.feedback-actions`, both `btn-secondary` (Review Case) and `btn-primary`
(Next →) have `flex: 1`. The secondary action is as visually prominent as the primary.

**Corrective procedure:**
In the CSS:
```css
/* Old: */
.btn-secondary { padding: 13px 18px; ... }

/* New: */
.btn-secondary { flex: 0 0 auto; padding: 13px 16px; ... }
/* btn-primary keeps flex: 1 */
```
This makes "Review Case" a compact secondary action on the left, "Next →" a full-width
primary button on the right.

---

---

# PART II — STYLE & TEST-TAKER EXPERIENCE

---

## UX1 — Avatar too small; patient stage is mostly empty space
**Status:** 🔲 PENDING

**Problem:** Avatar is `200×320px` in a stage that's roughly `780px × (100vh - 120px)`.
Most of the stage is empty dark space. The patient is not visually commanding.

**Corrective procedure:**
In CSS:
```css
/* Increase avatar size on desktop */
.avatar-wrap { width: 260px; height: 416px; }

/* On mobile keep current scale */
@media (max-width: 760px) {
  .avatar-wrap { width: 150px; height: 240px; }
}
```
Also change patient stage layout from `justify-content: center` (vertically centered) to:
```css
.patient-stage {
  justify-content: flex-start;
  padding-top: 40px;
}
```
This anchors the patient to the upper portion of the stage (like they're sitting across from
you at eye level) rather than floating in the middle of the screen.

**Implementation note:** The SVG is `viewBox="0 0 200 320"` and scales via `width:100%;height:100%`
on the SVG element — so changing `.avatar-wrap` dimensions is all that's needed.

---

## UX2 — Speech bubble too transparent; doesn't read as speech
**Status:** 🔲 PENDING

**Problem:** `background: rgba(255,255,255,.05)` — essentially invisible. The bubble shape
doesn't register as a distinct object.

**Corrective procedure:**
```css
.speech-bubble {
  background: rgba(255,255,255,.09);         /* was .05 */
  border: 1px solid rgba(255,255,255,.13);   /* was var(--border) = .07 */
  box-shadow: 0 4px 24px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.06);
}
```

---

## UX3 — Bubble text too small and secondary color; it's the most important content
**Status:** 🔲 PENDING

**Problem:** `font-size: 13px; color: var(--text2)` — `#a8a8b3`. The patient's words
are rendered at secondary text weight when they're the primary content of the encounter.

**Corrective procedure:**
```css
.bubble-text {
  font-size: 14px;           /* was 13px */
  color: var(--text);        /* was var(--text2) */
  line-height: 1.7;          /* was 1.6 */
}
```

---

## UX4 — Clinician probe inside patient bubble — two speakers sharing one bubble
**Status:** 🔶 PARTIAL (styled, but still inside bubble)

**Problem:** The clinician prompt (`"Clinician: 'What brings you in today?'"`) renders
inside the same bubble as the patient's response. Two speakers, one container. The styling
with indigo border helps but doesn't fix the fundamental structural issue.

**Corrective procedure:**
Move the clinician probe outside the `.speech-bubble` element entirely.
In HTML, restructure the patient-stage area:
```html
<!-- Clinician prompt — above the bubble, separate element -->
<div class="clinician-prompt-wrap" id="clinician-prompt-wrap" style="display:none">
  <div class="clinician-prompt-label">You ask:</div>
  <div class="clinician-prompt-text" id="clinician-probe"></div>
</div>

<!-- Patient speech bubble — below the prompt -->
<div class="speech-bubble hidden" id="speech-bubble">
  <div class="bubble-tail"></div>
  <div class="bubble-dots" id="bubble-dots">...</div>
  <div class="bubble-text" id="bubble-text"></div>
</div>
```
CSS:
```css
.clinician-prompt-wrap {
  width: 100%; max-width: 380px;
  margin-bottom: 8px;
  display: flex; flex-direction: column; gap: 2px;
}
.clinician-prompt-label {
  font-size: 10px; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--accent);
  opacity: .7;
}
.clinician-prompt-text {
  font-size: 12px; font-style: italic; color: var(--text3);
  padding: 6px 10px;
  border-left: 2px solid rgba(99,102,241,.35);
  background: rgba(99,102,241,.04);
  border-radius: 0 6px 6px 0;
}
```
In `startPhase()`, show/hide the `.clinician-prompt-wrap` instead of
`probe.classList.toggle('visible')`:
```js
// Show clinician prompt wrapper
document.getElementById('clinician-prompt-wrap').style.display = 'flex';
```

**Implementation note:** The `clinician-probe` element ID is used in `startEncounter()` to
hide it — update that reference too. Search for all `getElementById('clinician-probe')` calls.

---

## UX5 — Patient info bar priorities reversed; widths misaligned
**Status:** 🔲 PENDING

**Problem:** "Adult Female, 34" (patient label) appears first with `font-weight: 600`,
then the setting in small muted text. Setting provides the clinical frame and should
lead. Also: info bar has `max-width: 420px`, bubble has `max-width: 380px` — they're
not aligned width-wise.

**Corrective procedure:**
Swap order in HTML:
```html
<div class="patient-info-bar" id="patient-info-bar">
  <span class="patient-setting" id="patient-setting">—</span>
  <div class="patient-info-sep"></div>
  <span class="patient-label" id="patient-label">—</span>
</div>
```
And align widths:
```css
.patient-info-bar { max-width: 380px; }   /* match bubble */
.patient-setting  { font-size: 12px; color: var(--text2); font-weight: 500; }
.patient-label    { font-size: 11px; color: var(--text3); flex-shrink: 0; }
```

---

## UX6 — Same-phase tags split to opposite columns; no legend header
**Status:** 🔲 PENDING

**Problem:** `revealBehavioralTags()` alternates left/right by total count, so two tags
from the same phase end up in opposite columns. Visually coherent clusters of related
observations are split apart.

**Corrective procedure:**
Change the column-selection logic so all tags in a single `revealBehavioralTags()` call
go to the same column. Alternate columns per *call*, not per tag:

```js
function revealBehavioralTags(tags, isAppearance) {
  if (!CFG.showTags || !tags.length) return;
  const overlay = document.getElementById('tag-overlay');

  // Choose column for this entire batch based on which column has fewer tags
  const side = _tagCols.left.count <= _tagCols.right.count ? 'left' : 'right';
  const col  = _tagCols[side];

  tags.forEach((tag, idx) => {
    const tid = setTimeout(() => {
      if (col.count >= TAG_MAX_ROWS && col.els.length > 0) {
        const oldest = col.els.shift();
        oldest.style.transition = 'opacity .4s ease';
        oldest.style.opacity    = '0';
        setTimeout(() => oldest.remove(), 420);
        col.count--;
      }
      const el = document.createElement('span');
      el.className = 'behavior-tag ' + (isAppearance ? 'tag-appearance' : getTagColor(tag));
      el.textContent = tag;
      const topPct = TAG_START_Y + col.count * (TAG_ROW_PX / window.innerHeight * 100 * 3.2);
      el.style[side === 'left' ? 'left' : 'right'] = TAG_COL_X[side];
      el.style.top = topPct + '%';
      overlay.appendChild(el);
      col.els.push(el);
      col.count++;
    }, idx * 160);
    _tagTimeouts.push(tid);
  });
}
```

Also add a column legend. In HTML inside `.tag-overlay`:
```html
<div class="tag-overlay" id="tag-overlay">
  <div class="tag-col-label tag-col-label-left" id="tag-col-label-left"></div>
  <div class="tag-col-label tag-col-label-right" id="tag-col-label-right"></div>
</div>
```
CSS:
```css
.tag-col-label {
  position: absolute; top: 2%; font-size: 8px; font-weight: 700;
  letter-spacing: .12em; text-transform: uppercase; color: var(--text3);
  opacity: 0; transition: opacity .4s;
}
.tag-col-label-left  { left:  3%; }
.tag-col-label-right { right: 3%; }
.tag-col-label.visible { opacity: 1; }
```
Show labels as "OBSERVED" when first tag appears in each column.

---

## UX7 — Auto-advance bar too thin and low contrast
**Status:** 🔲 PENDING

**Problem:** 3px height on the phase controls footer. Barely visible as a temporal affordance.

**Corrective procedure:**
```css
.auto-bar {
  height: 4px;           /* was 3px */
}
.auto-bar-fill {
  background: var(--accent-light);  /* was var(--accent) — lighter = more contrast on dark surface */
}
```
Also move the bar to the very top of the phase controls footer (above the controls content)
rather than at the bottom. Change `position: absolute; bottom: 0` to `top: 0`. This puts
the timer at the visual boundary between the encounter content and the footer, making it
a natural divider that also functions as a clock.

---

## UX8 — Phase controls footer blends into chart surface
**Status:** 🔲 PENDING

**Problem:** `background: var(--surface)` + `border-top: 1px solid var(--border)` is
visually identical to the chart panel behind it. No sense of "this is a control strip."

**Corrective procedure:**
```css
.phase-controls {
  background: var(--bg3);  /* slightly darker than --surface */
  border-top: 1px solid var(--border);
  box-shadow: 0 -1px 0 rgba(99,102,241,.12);  /* subtle indigo top glow */
}
```

---

## UX9 — Phase label needs navigational pill treatment
**Status:** 🔲 PENDING

**Problem:** `font-size: 12px; font-weight: 700; color: var(--accent-light)` — the phase
name (e.g., "CHIEF COMPLAINT") is readable but has no visual landmark quality.

**Corrective procedure:**
Wrap phase label in a pill:
```css
.phase-num {
  font-size: 11px; font-weight: 700;
  letter-spacing: .06em; text-transform: uppercase;
  color: var(--accent-light);
  background: rgba(99,102,241,.1);
  border: 1px solid rgba(99,102,241,.2);
  border-radius: 20px;
  padding: 3px 10px;
}
```

---

## UX10 — Question screen simultaneous scale animation; options arrive too early
**Status:** 🔲 PENDING

**Problem:** `questionSlide` animation scales the entire `.question-wrap` including options.
All four options appear simultaneously with the question text, removing reading order.

**Corrective procedure:**
Stagger the entrance: animate `.q-prompt` and `.options-grid` separately.
In CSS:
```css
/* Remove animation from the whole wrap */
.question-wrap { animation: none; }

/* Animate sub-elements in sequence */
.case-strip    { animation: fadeInUp .28s ease both; }
.q-header      { animation: fadeInUp .28s ease .05s both; }
.q-prompt      { animation: fadeInUp .3s ease .08s both; }
.options-label { animation: fadeInUp .28s ease .14s both; }
.options-grid  { animation: fadeInUp .3s ease .18s both; }
```

In `renderQuestion()`, reset the animations by removing and re-adding the elements'
parent class. The cleanest approach: re-trigger animations by cloning the node:
```js
// At end of renderQuestion(), re-trigger stagger animations
const wrap = document.getElementById('question-wrap');
wrap.style.animation = 'none';
void wrap.offsetHeight;
// Re-add animation on children by forcing a reflow on each
['.case-strip','.q-header','.q-prompt','.options-label','.options-grid'].forEach(sel => {
  const el = wrap.querySelector(sel);
  if (!el) return;
  el.style.animation = 'none';
  void el.offsetHeight;
  el.style.animation = '';
});
```

---

## UX11 — Option letter badges too faint before selection
**Status:** 🔲 PENDING

**Problem:** `.option-letter { color: var(--text3) }` — `#6b6b76` on a dark background.
The A/B/C/D labels are barely readable before interaction.

**Corrective procedure:**
```css
.option-letter {
  color: var(--text2);                    /* was var(--text3) — brighter */
  background: rgba(255,255,255,.08);      /* was .06 — more visible */
  border: 1px solid rgba(255,255,255,.1); /* was var(--border) = .07 */
}
```

---

## UX12 — "Select the best answer:" label patronizing at doctoral level
**Status:** 🔲 PENDING

**Problem:** Wastes a line of visual space with something the test-taker already knows.

**Corrective procedure:**
In HTML, change `.options-label`:
```html
<!-- Remove this: -->
<div class="options-label">Select the best answer:</div>
```
If you want to keep something in that space, replace with a keyboard hint that adds value:
```html
<div class="options-label">Press <kbd>A</kbd> <kbd>B</kbd> <kbd>C</kbd> <kbd>D</kbd> to select · <kbd>Enter</kbd> to advance</div>
```
CSS for `kbd`:
```css
.options-label kbd {
  font-family: inherit; font-size: 9px; font-weight: 700;
  padding: 1px 5px; border-radius: 4px;
  background: rgba(255,255,255,.07); border: 1px solid var(--border);
  color: var(--text3);
}
```

---

## UX13 — Feedback panel `max-height` animation snaps instead of unfolds
**Status:** 🔲 PENDING

**Problem:** `max-height: 2000px; transition: max-height .5s ease` — the actual content
is ~200-300px so the transition hits full height in the first ~8% of its duration, then
"coasts" invisibly for 460ms. The panel appears to snap open.

**Corrective procedure:**
Replace with CSS Grid row animation — the only reliable way to animate unknown heights:
```css
/* Replace current: */
.feedback-panel { max-height: 0; overflow: hidden; transition: max-height .4s ease; border-radius: 12px; }
.feedback-panel.visible { max-height: 2000px; transition: max-height .5s ease; }
.feedback-inner { ... }

/* With: */
.feedback-panel { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .38s ease; border-radius: 12px; }
.feedback-panel.visible { grid-template-rows: 1fr; }
.feedback-inner { overflow: hidden; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; }
```

---

## UX14 — Explanation renders as plain `textContent`; cannot format clinical content
**Status:** 🔲 PENDING

**Problem:** `document.getElementById('feedback-explanation').textContent = q.explanation || ''`
— DSM criteria references, clinical terms, and comparisons in explanations arrive as
undifferentiated prose. `≥5 of 9 symptoms`, italic terms, bold diagnoses — all lost.

**Corrective procedure:**
The data is generated by Claude API and already sanitized (no HTML injection). Upgrade to innerHTML:
```js
// In showFeedback():
document.getElementById('feedback-explanation').innerHTML =
  (q.explanation || '').replace(/\n/g, '<br>');
```
**Also** update `generate_presentations.py` system prompt to allow the generator to use
`<strong>` and `<em>` within explanation text for critical terms:
```
In explanation and distractor_rationale fields, you may use <strong> for diagnosis names
and DSM criteria counts, and <em> for clinical terms. No other HTML tags.
```
**Risk note:** This requires trusting the generator output. Since data is generated offline
(not user-submitted), this is safe. Still — add a sanitization step:
```js
function safeHtml(s) {
  return (s || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/&lt;(\/?(strong|em))&gt;/g, '<$1>');
}
```
Use `safeHtml(q.explanation)` instead of raw `q.explanation`.

---

## UX15 — "Review Case" and "Next →" are equal width; hierarchy wrong
**Status:** 🔲 PENDING  (see also T13)

**Problem:** Both buttons have `flex: 1`. The secondary action is as prominent as the primary.

**Corrective procedure:** (same as T13)
```css
.btn-secondary { flex: 0 0 auto; }
/* btn-primary keeps flex: 1 */
```

---

## UX16 — No momentum signal on question screen showing you're mid-encounter
**Status:** 🔲 PENDING

**Problem:** When the question screen appears, the test-taker has lost the encounter
context. The case strip at top shows patient label and setting but nothing indicates
"you are mid-encounter, more phases follow."

**Corrective procedure:**
Add an encounter progress indicator to the `case-strip`:
```html
<div class="case-strip" id="case-strip">
  <span class="case-domain-badge" id="case-domain-badge"></span>
  <span class="case-patient-label" id="case-patient-label"></span>
  <span class="case-strip-sep"></span>
  <span class="case-setting-label" id="case-setting-label"></span>
  <!-- Add this: -->
  <span class="case-strip-sep case-phase-sep" id="case-phase-sep"></span>
  <span class="case-phase-progress" id="case-phase-progress"></span>
</div>
```
CSS:
```css
.case-phase-progress {
  font-size: 11px; color: var(--text3); font-style: italic;
}
```
In `transitionToQuestion()`, populate it:
```js
const totalPhases = enc.encounter.phases.length;
const phasesShown = state.phaseIdx + 1;
const remaining   = totalPhases - phasesShown;
document.getElementById('case-phase-sep').style.display = remaining > 0 ? '' : 'none';
document.getElementById('case-phase-progress').textContent =
  remaining > 0 ? `${remaining} phase${remaining > 1 ? 's' : ''} remaining` : 'Final question';
```

---

## UX17 — Feedback tone same regardless of question type; clinical severity ignored
**Status:** 🔲 PENDING

**Problem:** `"✓ Correct!"` and `"✗ Incorrect — correct answer is B"` for every type.
A missed `risk_assessment` question has different clinical stakes than a missed `dsm_criteria`.

**Corrective procedure:**
Add type-specific feedback prefixes to `showFeedback()`:
```js
const WRONG_PREFIX = {
  risk_assessment:       '✗ In practice, this choice could delay crisis response.',
  immediate_intervention:'✗ A different intervention is prioritized in this scenario.',
  treatment_planning:    '✗ The evidence-based approach differs here.',
  primary_diagnosis:     '✗ The diagnosis does not fit this presentation.',
  differential_diagnosis:'✗ The differential does not account for all features.',
  dsm_criteria:          '✗ The DSM-5-TR criteria are not satisfied here.',
  cultural_consideration:'✗ A culturally-informed approach is needed.',
  assessment_tool:       '✗ A different assessment instrument is indicated.',
};

header.innerHTML = isCorrect
  ? '<span>✓</span> Correct!'
  : `<span>✗</span> ${escapeHtml(WRONG_PREFIX[q.type] || '✗ Incorrect.')} The correct answer is <strong>${q.correct_answer}</strong>`;
```

---

## UX18 — Results headings feel like a gold-star system, not clinical feedback
**Status:** 🔲 PENDING

**Problem:** "Great Work!" / "Session Complete" / "Keep Practicing" — these are elementary
school reward framings for a doctoral-level licensure candidate.

**Corrective procedure:**
```js
if (pct >= 80)      heading.innerHTML = 'Strong <em>Performance</em>';
else if (pct >= 60) heading.innerHTML = 'Session <em>Complete</em>';
else                heading.innerHTML = 'Review <em>Flagged Cases</em>';
```

---

## UX19 — Replay list `✗` used for both partial and full miss; partial case never shown
**Status:** 🔲 PENDING

**Problem:** The `outcomeChar` is always `✓` or `✗`. The `partial` CSS class exists but
`outcomeChar` is never set to indicate partial credit.

**Corrective procedure:**
```js
const outcomeClass = allCorrect ? 'correct' : noneCorrect ? 'wrong' : 'partial';
const outcomeChar  = allCorrect ? '✓' : noneCorrect ? '✗' : '~';
```

---

## UX20 — Score ring has no 70% benchmark marker
**Status:** 🔲 PENDING

**Problem:** The ring shows your score but no reference point. EPPP passing context is absent.

**Corrective procedure:**
Add a tick mark to the SVG ring at the 70% position and a label below the ring:
```html
<!-- In the ring SVG, add a tick mark at 70%: -->
<circle class="ring-tick" cx="65" cy="65" r="52"
  stroke-dasharray="2 324.7" stroke-dashoffset="-98.0"
  transform="rotate(-90 65 65)"/>
```
CSS:
```css
.ring-tick { fill: none; stroke: rgba(255,255,255,.3); stroke-width: 12; stroke-linecap: round; }
```
*(The dashoffset of -98 positions the 2px tick at the 70% mark: 326.7 * 0.30 = 98.0)*

Also add below `ring-label`:
```html
<span class="ring-benchmark">EPPP target: 70%</span>
```
CSS:
```css
.ring-benchmark { font-size: 9px; color: var(--text3); letter-spacing: .06em; margin-top: 1px; }
```

---

## UX21 — Results bar animations fight card entry animation
**Status:** 🔲 PENDING

**Problem:** `buildResults()` sets a 200ms timeout for bar fills. But the results inner
container enters with `fadeInUp .5s`. At 200ms the card is still mid-fade while bars are
already filling — two competing motions.

**Corrective procedure:**
Increase both setTimeout delays to stagger after card entry:
```js
// Type bars — after card is visible
setTimeout(() => {
  typeRows.querySelectorAll('.type-bar-fill').forEach(el => el.style.width = el.dataset.pct + '%');
}, 620);

// Domain bars — after type bars start
setTimeout(() => {
  domRows.querySelectorAll('.db-fill').forEach(el => el.style.width = el.dataset.pct + '%');
}, 750);
```

---

## UX22 — No "weakest area" callout on results screen
**Status:** 🔲 PENDING

**Problem:** The type breakdown is passive. No coaching signal. A test-taker has to scan
all rows to identify their weakness.

**Corrective procedure:**
After building type rows, identify and highlight the lowest-scoring type:
```js
// Find weakest type
const typeEntries = Object.entries(state.typeScores).filter(([,s]) => s.total >= 2);
if (typeEntries.length > 1) {
  const weakest = typeEntries.reduce((a, b) =>
    (a[1].correct / a[1].total) < (b[1].correct / b[1].total) ? a : b
  );
  const conf = TYPE_BADGE[weakest[0]] || { label: weakest[0], color: '#f87171' };
  const pct  = Math.round(weakest[1].correct / weakest[1].total * 100);
  const callout = document.createElement('div');
  callout.className = 'weakest-callout';
  callout.innerHTML = `
    <span class="weakest-label">Focus area:</span>
    <span class="weakest-type" style="color:${conf.color}">${conf.label}</span>
    <span class="weakest-pct">${pct}% this session</span>`;
  document.querySelector('.type-breakdown').prepend(callout);
}
```
CSS:
```css
.weakest-callout {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: rgba(248,113,113,.07); border: 1px solid rgba(248,113,113,.2);
  border-radius: 10px; padding: 10px 16px; margin-bottom: 10px;
}
.weakest-label { font-size: 10px; font-weight: 700; color: var(--text3);
  text-transform: uppercase; letter-spacing: .08em; }
.weakest-type  { font-size: 13px; font-weight: 700; }
.weakest-pct   { font-size: 12px; color: var(--text3); margin-left: auto; }
```

---

## UX23 — Settings page has no historical performance context
**Status:** 🔲 PENDING

**Problem:** Test-taker configures a session with no signal of where they've been.
localStorage has accumulated domain scores from previous sessions but they're invisible.

**Corrective procedure:**
Add a performance banner at the top of `clinical-presentation-settings.html`, below the
page subtitle. Reads from `localStorage.getItem('encounter_scores')`:
```js
// In settings page, after DOMContentLoaded:
function renderHistoryBanner() {
  const scores = JSON.parse(localStorage.getItem('encounter_scores') || '{}');
  const entries = Object.entries(scores).filter(([, s]) => s && s.total > 0);
  if (!entries.length) return;

  const banner = document.getElementById('history-banner');
  banner.style.display = 'flex';
  banner.innerHTML = entries
    .sort((a,b) => (a[1].correct/a[1].total) - (b[1].correct/b[1].total))
    .map(([d, s]) => {
      const pct = Math.round(s.correct / s.total * 100);
      const color = pct >= 75 ? '#34d399' : pct >= 55 ? '#fb923c' : '#f87171';
      return `<span class="hist-item"><span class="hist-code">${d}</span>
              <span class="hist-pct" style="color:${color}">${pct}%</span></span>`;
    }).join('');
}
```
HTML to add in settings page after `.page-sub`:
```html
<div id="history-banner" class="history-banner" style="display:none"></div>
```
CSS:
```css
.history-banner {
  display: flex; gap: 16px; flex-wrap: wrap;
  background: rgba(255,255,255,.025); border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 18px; margin-bottom: 32px;
  align-items: center;
}
.hist-item  { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.hist-code  { font-size: 9px; font-weight: 700; letter-spacing: .1em; color: var(--text3); }
.hist-pct   { font-family: 'Instrument Serif', serif; font-size: 1.1rem; }
```

---

## UX24 — Speed card sublabels don't describe the actual experience
**Status:** 🔲 PENDING

**Problem:** Speed sublabels say things like "Default — Recommended" which tell the user
nothing about what the experience feels like at each speed.

**Corrective procedure:**
In settings HTML, update each `.speed-sublabel` value:
- Slow: `"50ms/char · 3s hold · slow speech"`
- Normal: `"30ms/char · 1.5s hold · natural pacing"` + `"(Recommended)"`
- Fast: `"12ms/char · 0.5s hold · rapid"`
- Manual: `"Click ›Next‹ to advance each phase"`

---

## UX25 — Domain cards show category labels, not encounter counts
**Status:** 🔲 PENDING

**Problem:** `.domain-q-count` shows "Diagnostic clinical encounters" — a description,
not a number. Test-takers can't calibrate session depth.

**Corrective procedure:**
Update settings HTML to show accurate hardcoded counts (30 per domain as of generation):
```html
<div class="domain-q-count">30 encounters available</div>
```
Or calculate dynamically in settings page JS by fetching the JSON count on load:
```js
// Lightweight: just read the total_encounters field
async function loadDomainCount(domain) {
  try {
    const r = await fetch(`data/${domain}_presentations.json`);
    if (!r.ok) return '—';
    const d = await r.json();
    return d.total_encounters || d.encounters?.length || '—';
  } catch { return '—'; }
}
```
Simpler: hardcode `30 encounters` now and update if regenerated.

---

## UX26 — No "Resume last session" affordance on settings page
**Status:** 🔲 PENDING

**Problem:** No way to quickly re-run the same configuration from the last session.

**Corrective procedure:**
Store last-used session params in `localStorage.setItem('encounter_last_params', location.search)`
at the start of `loadEncounters()` in the exercise page.

In the settings page, read this on load and show a resume banner if present:
```js
const lastParams = localStorage.getItem('encounter_last_params');
if (lastParams) {
  const sp = new URLSearchParams(lastParams);
  const resumeEl = document.getElementById('resume-banner');
  resumeEl.style.display = 'flex';
  resumeEl.querySelector('.resume-desc').textContent =
    `${sp.get('domains') || 'Mixed'} · ${sp.get('count') || 10} encounters · ${sp.get('speed') || 'normal'} speed`;
  resumeEl.querySelector('.resume-btn').href =
    'clinical-presentation-exercise.html' + lastParams;
}
```
HTML above `settings-section`:
```html
<div id="resume-banner" class="resume-banner" style="display:none">
  <div class="resume-icon">↩</div>
  <div class="resume-text">
    <div class="resume-title">Resume last session</div>
    <div class="resume-desc"></div>
  </div>
  <a class="resume-btn btn-resume" href="#">Resume →</a>
</div>
```

---

## UX27 — "Mixed Domains" option visually de-emphasized
**Status:** 🔲 PENDING

**Problem:** Mixed is shown as a dashed-border secondary tab below the grid. Clinically it's
the most valid practice mode for EPPP simulation.

**Corrective procedure:**
Move the Mixed tab *above* the domain grid. Change its visual treatment to match a primary
selected state by default — or add a section header that reads:
`"Or choose specific domains ↓"` below the Mixed tab, reframing individual selection as
the secondary path.

---

## UX28 — Empty state missing on replay list
**Status:** 🔲 PENDING

**Problem:** If no encounters were answered (edge case), `#replay-list` renders blank.

**Corrective procedure:**
After the `Object.entries(encMap).forEach(...)` loop in `buildResults()`:
```js
if (Object.keys(encMap).length === 0) {
  replayList.innerHTML = '<div class="replay-empty">No encounters recorded this session.</div>';
}
```

---

## UX29 — "Review Case" shows only last phase; full transcript needed
**Status:** 🔲 PENDING  (see also T12)

Already documented in T12 with corrective procedure.

---

## UX30 — No "click to skip" affordance on speech bubble
**Status:** 🔲 PENDING

**Problem:** New users don't know the bubble is clickable to skip typewriter.

**Corrective procedure:**
Add a faint skip hint inside the bubble that disappears after first use:

In HTML inside `.speech-bubble`:
```html
<div class="bubble-skip-hint" id="bubble-skip-hint">click to skip</div>
```
CSS:
```css
.bubble-skip-hint {
  position: absolute; bottom: 6px; right: 10px;
  font-size: 9px; color: var(--text3); opacity: .5;
  pointer-events: none; letter-spacing: .06em;
}
.bubble-skip-hint.hidden { display: none; }
```
In JS, after first skip, persist to localStorage and hide permanently:
```js
// In skipHandler:
const skipHint = document.getElementById('bubble-skip-hint');
if (skipHint) skipHint.classList.add('hidden');
localStorage.setItem('encounter_skip_hint_shown', '1');

// On page load:
if (localStorage.getItem('encounter_skip_hint_shown')) {
  const h = document.getElementById('bubble-skip-hint');
  if (h) h.classList.add('hidden');
}
```

---

---

# PART III — INSTRUCTIONS FOR CLAUDE

---

## How to approach this module

**This is a clinical simulation, not a quiz.** Every design decision should be evaluated
against the question: "Does this make the test-taker feel more like they're sitting across
from a real patient?" If a change adds polish without adding clinical immersion, deprioritize it.
If a change increases the realism or the emotional signal of the encounter, prioritize it.

**The avatar is the heart of the module.** The SVG patient — its breathing, its jaw moving
during speech, its flat affect, its tears — is the primary differentiator from every other
EPPP prep tool. Any time spent improving avatar fidelity pays more dividends than equivalent
time spent on color tweaks or layout adjustments. Treat the avatar like a character.

**The feedback panel is the learning moment.** The encounter is setup; the question is test;
the feedback is where actual learning happens. The distractor rationale, the explanation, the
correct-answer "Why B?" callout — these are the most educationally valuable elements in the
entire module. Prioritize their readability and clinical tone above all other content.

---

## Approach rules when implementing from this document

1. **Read before editing.** Always `Read` the specific section before writing an `Edit`.
   Never edit a section you haven't seen in this chat session.

2. **One logical group per commit.** Group edits by screen or concern, not by line proximity.
   Good: "All encounter screen style fixes." Bad: "Fixed three random things."

3. **Check for side effects.** Before editing any function, search for all callers:
   `grep -n "functionName" clinical-presentation-exercise.html`

4. **Verify with a Node sanity check after edits:**
   ```bash
   node -e "require('fs').readFileSync('clinical-presentation-exercise.html','utf8'); console.log('OK')"
   ```

5. **When implementing UX4 (clinician probe restructure)**, this touches both HTML and JS.
   Search all occurrences of `clinician-probe` before editing:
   `getElementById('clinician-probe')` appears in `startPhase()`, `startEncounter()`, and HTML.
   All three must be updated together or the probe disappears entirely.

6. **When implementing UX13 (feedback panel grid animation)**, the `.feedback-inner`
   element must get `overflow: hidden` — without this the grid animation doesn't clip.
   Test by answering a question and watching the panel expand.

7. **When implementing UX14 (innerHTML for explanation)**, always use the `safeHtml()`
   sanitizer described in the corrective procedure. Never use raw `innerHTML = q.explanation`.

8. **When implementing UX23 (history banner on settings page)**, that is a change to
   `clinical-presentation-settings.html` — a separate file. Don't accidentally edit the
   exercise page.

9. **Avatar changes** (UX1 — size increase) only require changing `.avatar-wrap` dimensions.
   The SVG scales automatically via `viewBox`. Do not touch the SVG path coordinates.

10. **The `state-flat_affect` CSS selector has an underscore.** Many CSS processors handle
    underscored class names differently. The current code uses `state-flat_affect` as a
    literal string. Don't rename it. The JS uses string concatenation `'state-' + emotion`
    where emotion is `'flat_affect'` — this is correct and intentional.

11. **When implementing T12 (review transcript)**, the `.speech-bubble` currently has
    `min-height: 60px` and is not scrollable. Before adding the transcript, change it to:
    ```css
    .speech-bubble { min-height: 60px; max-height: 55vh; overflow-y: auto; }
    ```
    Do not remove `min-height` — the dots animation needs the height while thinking.

12. **The `persistScores()` function accumulates additively** — it reads existing localStorage,
    adds session scores on top, and writes back. Calling it after every question (T9) is safe.
    Calling it at session end in addition (which still happens in `nextEncounterOrResults()`)
    means scores are double-counted. **Remove the `persistScores()` call from
    `nextEncounterOrResults()`** after confirming T9 is working.

13. **When implementing multiple PENDING items in one session**, implement in this order:
    - High-impact readability fixes first (UX3, UX14, UX15)
    - Structure/layout changes second (UX4, UX1)
    - Animation/timing last (UX10, UX13, UX21)
    This ensures the module is always in a usable state if work is interrupted.

14. **Test with `?dev=1` appended to the URL** to access the avatar state cycler panel.
    Use it to visually verify `flat_affect`, `hopeful`, `tearful`, and `distressed` states
    after any avatar changes.

15. **After implementing UX6 (tag column logic change)**, visually verify by running a
    session with all 9 domains and watching the first 3 phases of a multi-tag encounter.
    Same-phase tags should cluster to one column.

---

## Priority queue for next session

Implement these in order. Each is self-contained and non-breaking:

**Session A — Reading quality (30-60 min, exercise page only):**
1. UX3 — bubble text color and size
2. UX2 — bubble background opacity + box-shadow
3. UX11 — option letter badge brightness
4. UX15 / T13 — Review Case button not full-width
5. UX12 — remove patronizing "Select the best answer" label

**Session B — Feedback depth (30 min, exercise page only):**
1. UX14 — innerHTML for explanation with safeHtml sanitizer
2. UX17 — type-specific wrong-answer feedback text
3. UX22 — weakest area callout on results

**Session C — Layout and encounter immersion (45-60 min, exercise page):**
1. UX1 — avatar size increase
2. UX4 — clinician probe outside bubble
3. UX5 — patient info bar order swap
4. UX9 — phase label pill treatment
5. UX8 — phase controls footer background

**Session D — Animation quality (30 min, exercise page):**
1. UX13 — feedback panel grid animation
2. UX10 — staggered question screen entrance
3. UX21 — results bar animation timing fix

**Session E — Results screen (30 min, exercise page):**
1. UX20 — score ring 70% benchmark tick
2. UX19 — partial outcome `~` in replay list
3. UX18 — results heading tone
4. UX28 — empty state on replay list

**Session F — Settings page (45 min, settings page):**
1. UX23 — history banner with past domain scores
2. UX26 — resume last session affordance
3. UX24 — speed card sublabels
4. UX25 — domain card encounter counts
5. UX27 — Mixed Domains repositioning

**Session G — Technical bugs (30-45 min, exercise page):**
1. T10 — replayEncounter state corruption
2. T12 / UX29 — reviewEncounter full transcript
3. T11 — weakest sort at subdomain level
4. UX6 — same-phase tags to same column
5. UX30 — click-to-skip hint on bubble

---

## Note on `generate_presentations.py`

When implementing UX14 (innerHTML explanations), the generator should be updated to
optionally produce light HTML markup (`<strong>`, `<em>`) in explanation and
distractor_rationale fields. This requires:
1. Updating the system prompt in `generate_presentations.py`
2. Running `python generate_presentations.py --all --resume` to regenerate with markup
3. Validating that existing encounters still parse after regeneration

This is a data-layer change and should be done in a dedicated session after the HTML
renderer is updated to handle it safely.

---

*End of document. Update status fields as items are implemented.*
*This document should be committed to the repo so it persists across sessions.*
