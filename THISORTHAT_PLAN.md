# This or That — Change Plan
**Date:** 2026-03-05
**Scope:** Bug fixes, UI corrections, keyboard nav, data accuracy, content expansion

---

## PRIORITY ORDER

1. BUG-01 — makeFlashcard() fallback produces same answer for both choices (BREAKING)
2. BUG-02 — revealBlindNames() called N times inside forEach (minor, non-breaking)
3. UI-01 — Settings page shows fabricated anchor/vignette counts (misleading)
4. UI-02 — Dead CSS in settings (level-card styles, never used)
5. UI-03 — No pool-exhaustion warning in exercise
6. FEAT-01 — Keyboard navigation in exercise
7. FEAT-02 — Lifetime stats row on results screen
8. DATA-01 — Domain misclassification: PMET file contains Learning content, not psychometrics
9. DATA-02 — Thin domains need content expansion (WDEV 12, CASS 15, PTHE 16, PETH 16)

---

## BUG-01: makeFlashcard() fallback — both choices can be the same item

**File:** `thisorthat-exercise.html`
**Location:** lines ~370-378
**Severity:** Breaking — renders a question unanswerable (both buttons same concept)

**Root cause:**
The fallback path (triggered when key_distinction doesn't parse into two named items)
independently calls Math.random() for both `correct` and `wrong`, so both can resolve
to item_x or both to item_y.

```
// BROKEN (current):
return {
    clue: q.key_distinction || q.question,
    correct: Math.random() < 0.5 ? q.item_x : q.item_y,
    wrong:   Math.random() < 0.5 ? q.item_x : q.item_y, // "will be fixed below" — LIE
};
```

**Fix:**
Assign one side first, derive the other as the complement.

```
// FIXED:
const correctItem = Math.random() < 0.5 ? q.item_x : q.item_y;
return {
    clue:    q.key_distinction || q.question,
    correct: correctItem,
    wrong:   correctItem === q.item_x ? q.item_y : q.item_x,
};
```

Also remove the misleading "will be fixed below" comment.

---

## BUG-02: revealBlindNames() called inside forEach loop

**File:** `thisorthat-exercise.html`
**Location:** lines ~517-524 (timeoutQuestion function)
**Severity:** Minor — no visible bug, but double DOM re-write on pair header

**Root cause:**
`revealBlindNames()` rewrites `pair-vs-row` innerHTML. Calling it once per button
(2x) causes the second call to re-do DOM work the first already completed.

**Fix:**
Move `revealBlindNames()` call to AFTER the forEach closes.

```
// BROKEN:
document.querySelectorAll('.choice-btn').forEach(btn => {
    btn.classList.add(btn.dataset.correct === '1' ? 'correct' : 'dimmed');
    revealBlindNames();
});

// FIXED:
document.querySelectorAll('.choice-btn').forEach(btn => {
    btn.classList.add(btn.dataset.correct === '1' ? 'correct' : 'dimmed');
});
revealBlindNames();
```

---

## UI-01: Settings page — replace fabricated counts with actual data

**File:** `thisorthat-settings.html`
**Location:** `.domain-q-count` divs inside each `.domain-card`
**Problem:** Shows "193 anchors · 965 vignettes" style counts copied from vignette system.
These are completely wrong — this module uses contrast pairs.

**Fix:** Replace each `.domain-q-count` with the actual count of contrast pairs from JSON.
Also change the terminology from "anchors · vignettes" to "contrast pairs".

Actual counts (verified from JSON files):
- PMET: 30 contrast pairs
- LDEV: 22 contrast pairs
- CPAT: 30 contrast pairs
- PTHE: 16 contrast pairs
- SOCU: 24 contrast pairs
- WDEV: 12 contrast pairs
- BPSY: 29 contrast pairs
- CASS: 15 contrast pairs
- PETH: 16 contrast pairs

**Each domain-q-count div should read:** `"X contrast pairs"`

---

## UI-02: Settings page — remove dead CSS (level cards)

**File:** `thisorthat-settings.html`
**Location:** CSS lines ~138-179
**Problem:** Full styling for `.level-card`, `.levels-grid`, `.badge-l1` through `.badge-l5`,
`.level-info`, `.level-name`, `.level-desc`, `.level-pill`, `.pill-l1` through `.pill-l5`
exists but NO corresponding HTML exists. These styles are never applied.

**Fix:** Delete the entire "LEVEL CARDS" CSS block (~lines 138-179).
The block is clearly marked with `/* ── LEVEL CARDS ── */` comment for easy identification.

---

## UI-03: Exercise — pool exhaustion warning

**File:** `thisorthat-exercise.html`
**Location:** `loadQuestions()` function, after `questions = pool.slice(0, CFG.count)`
**Problem:** If user requests 50 questions from WDEV (12 available), they silently get 12.
No indication that the session was truncated.

**Fix:** After the slice, if `questions.length < CFG.count`, inject a one-time toast/banner
at the top of the quiz screen on the first render. Suggested message:

> "Only [N] questions available for your selection — showing all [N]."

Implementation: Add a `<div id="pool-warn" class="pool-warn"></div>` element to quiz screen.
In `loadQuestions()`, after the slice:
```javascript
if (questions.length < CFG.count) {
    const warn = document.getElementById('pool-warn');
    warn.textContent = `Only ${questions.length} questions available — showing all ${questions.length}.`;
    warn.style.display = 'block';
}
```
Style `.pool-warn` as a subtle amber notice bar (matching gold theme) that auto-dismisses
after the first question is answered, or stays until next question.

---

## FEAT-01: Keyboard navigation

**File:** `thisorthat-exercise.html`
**Location:** Add a `keydown` event listener in the `<script>` block, near the bottom (boot section)
**Problem:** No keyboard shortcuts. For exam-speed drilling, mouse-only is a significant friction point.

**Key bindings:**
- `1` or `a` or `ArrowLeft` → click the left choice button (first in DOM)
- `2` or `l` or `ArrowRight` or `d` → click the right choice button (second in DOM)
- `Enter` or `Space` → trigger next-btn click (when next-btn is visible)

**Implementation:**
```javascript
document.addEventListener('keydown', e => {
    // Don't intercept when typing in an input
    if (e.target.tagName === 'INPUT') return;

    const btns = document.querySelectorAll('.choice-btn:not(.correct):not(.wrong):not(.dimmed)');
    const nextBtn = document.getElementById('next-btn');

    if ((e.key === 'Enter' || e.key === ' ') && nextBtn.classList.contains('visible')) {
        e.preventDefault();
        nextBtn.click();
        return;
    }

    const allBtns = [...document.querySelectorAll('.choice-btn')];
    if (!answered && allBtns.length === 2) {
        if (e.key === '1' || e.key === 'a' || e.key === 'ArrowLeft') {
            e.preventDefault();
            allBtns[0].click();
        } else if (e.key === '2' || e.key === 'l' || e.key === 'd' || e.key === 'ArrowRight') {
            e.preventDefault();
            allBtns[1].click();
        }
    }
});
```

Also: add a small keyboard hint below the choices-row, shown only on non-touch devices:
```html
<div class="kb-hint" id="kb-hint">
    Press <kbd>1</kbd> / <kbd>2</kbd> to choose &nbsp;·&nbsp; <kbd>Enter</kbd> to continue
</div>
```
Style `.kb-hint` as `font-size: 11px; color: var(--text3); text-align: center;`
Hide it on mobile via `@media (pointer: coarse) { .kb-hint { display: none; } }`

---

## FEAT-02: Lifetime accuracy on results screen

**File:** `thisorthat-exercise.html`
**Location:** `showResults()` function, results-summary div
**Problem:** Results only show session score. Lifetime cumulative accuracy (stored in localStorage)
is silently accumulated but never surfaced to the user.

**Fix:** Add a "Lifetime" stat item to the results-summary grid alongside Score/Correct/Domains.

```javascript
// In showResults(), after calculating pct:
const allStored = getStoredScores()[MODULE] || {};
let ltCorrect = 0, ltTotal = 0;
for (const [d, s] of Object.entries(allStored)) {
    ltCorrect += s.correct || 0;
    ltTotal   += s.total   || 0;
}
const ltPct = ltTotal ? Math.round(ltCorrect / ltTotal * 100) : null;
const ltDisplay = ltPct !== null ? `${ltPct}%` : '—';
```

Then include in the results-summary innerHTML:
```html
<div class="rs-item">
    <span class="rs-label">Lifetime</span>
    <span class="rs-val">${ltDisplay}</span>
</div>
```

---

## DATA-01: PMET domain misclassification

**Files:** `data/PMET_contrast.json`, `thisorthat-settings.html`
**Problem:** All 30 questions in PMET_contrast.json are Learning theory content
(classical conditioning, operant conditioning, reinforcement schedules, social learning).
Legacy IDs confirm this: `LEA_CONT_001` through `LEA_CONT_030`.
PMET should contain psychometrics and research methods content (reliability, validity,
research design, statistics). Instead, that content is partially scattered in CASS.

**Options evaluated:**
- Option A: Rename PMET to include "Learning" in its label (cheap, misleading)
- Option B: Move these 30 questions to CPAT or BPSY (domain debate — learning could go either place)
- Option C: Create a standalone Learning domain file (LDEV already taken; could use LERN)
- Option D: Reclassify questions within PMET as subdomain "Learning & Conditioning" and accept the mismatch as a historical artifact, while adding TRUE psychometrics content

**Recommended: Option D short-term + proper content generation long-term**

Short-term fix (immediately implementable):
- Update `domain_name` in PMET_contrast.json from "Psychometrics & Research Methods"
  to "Learning, Memory & Research Methods" to more honestly reflect current content
- Update the matching label in `thisorthat-settings.html` domain card

Long-term (content generation task):
- Generate 30 true PMET questions: reliability, validity types, research designs,
  statistics (z-test, t-test, ANOVA, chi-square, effect size, power), sampling methods
- Move current 30 Learning questions to BPSY (where conditioning has physiological roots)
  or create new LERN domain

---

## DATA-02: Content expansion — thin domains

**Target minimums:** 30 contrast pairs per domain
**Method:** Generate via Claude API (similar to generate_spot_errors.py pattern)

### Expansion targets:

| Domain | Current | Need | Priority |
|--------|---------|------|----------|
| WDEV | 12 | +18 | CRITICAL |
| CASS | 15 | +15 | HIGH |
| PTHE | 16 | +14 | HIGH |
| PETH | 16 | +14 | HIGH |
| LDEV | 22 | +8 | MEDIUM |
| SOCU | 24 | +6 | MEDIUM |

### WDEV expansion topics (18 needed):
- Job characteristics model (Hackman & Oldham) vs. motivator-hygiene (Herzberg)
- Role conflict vs. role ambiguity
- Succession planning vs. workforce planning
- 360-degree feedback vs. upward feedback
- Coaching vs. mentoring
- Gainsharing vs. profit sharing
- Realistic job preview vs. standard recruitment
- Organizational socialization vs. onboarding
- Stretch goals vs. proximal goals (Locke & Latham)
- Job enlargement vs. job enrichment
- Structured interview vs. unstructured interview (already have behavioral/situational)
- Assessment center vs. work sample test
- Person-organization fit vs. person-job fit
- Formal vs. informal organizational structure
- Centralized vs. decentralized decision-making
- Organizational commitment (affective vs. continuance vs. normative)
- Burnout vs. engagement
- Turnover intention vs. absenteeism

### CASS expansion topics (15 needed):
- Reliability vs. validity (general distinction)
- Test-retest reliability vs. alternate-form reliability
- Sensitivity vs. specificity (clinical screening)
- Positive predictive value vs. negative predictive value
- Base rate vs. hit rate
- Structured vs. semi-structured clinical interview
- Projective vs. objective personality tests
- Behavioral assessment vs. self-report assessment
- Neuropsychological screening vs. comprehensive neuropsychological evaluation
- Rating scale vs. checklist (behavioral observation)
- DSM-5 categorical vs. dimensional diagnosis
- GAF vs. WHODAS (functional assessment)
- Intellectual disability vs. specific learning disorder
- ADHD inattentive vs. ADHD hyperactive-impulsive presentation
- Malingering vs. factitious disorder

### PTHE expansion topics (14 needed):
- Primary prevention vs. secondary prevention vs. tertiary prevention
- Behavioral activation vs. cognitive restructuring
- Schema therapy vs. standard CBT
- Motivational interviewing vs. brief advice
- Systematic desensitization vs. flooding
- DBT validation vs. DBT change strategies
- Acceptance vs. commitment (ACT)
- Psychodynamic interpretation vs. clarification
- Supportive therapy vs. insight-oriented therapy
- Cognitive processing therapy vs. prolonged exposure (PTSD)
- Mindfulness-based stress reduction vs. mindfulness-based cognitive therapy
- Couples therapy (Gottman) vs. emotionally focused therapy
- Functional family therapy vs. multisystemic therapy
- Harm reduction vs. abstinence-based treatment

### PETH expansion topics (14 needed):
- SSRI vs. SNRI mechanism and use
- Typical vs. atypical antipsychotics
- Mood stabilizers: lithium vs. valproate
- Benzodiazepine vs. non-benzodiazepine anxiolytics
- MAOIs vs. TCAs
- Stimulant vs. non-stimulant ADHD treatment
- Tardive dyskinesia vs. Parkinsonism (medication side effects)
- Informed consent vs. assent (minors)
- Confidentiality vs. privilege
- Mandatory reporting vs. duty to warn (Tarasoff)
- Multiple relationships vs. boundary crossings
- Competency to stand trial vs. criminal responsibility (insanity)
- Child abuse reporting: reasonable suspicion vs. confirmed abuse
- Ethics complaint vs. malpractice suit

### Generation script approach:
Create `generate_contrast.py` modeled on `generate_spot_errors.py`:
- Input: domain code, list of concept pairs to generate
- Output: properly formatted JSON appended to existing domain file
- Uses Claude API with system prompt emphasizing EPPP focus and key_distinction format
- Deduplicates against existing question items before writing
- Validates that each question has: id, domain_code, subdomain, item_x, item_y,
  question, answer, key_distinction, commonly_confused_because

---

## IMPLEMENTATION SEQUENCE

### Phase 1 — Immediate code fixes (this session)
1. BUG-01: Fix makeFlashcard() fallback
2. BUG-02: Move revealBlindNames() outside forEach
3. UI-01: Replace fabricated counts in settings
4. UI-02: Remove dead CSS from settings
5. FEAT-01: Add keyboard navigation

### Phase 2 — Exercise enhancements (this session, after Phase 1)
6. UI-03: Pool exhaustion warning
7. FEAT-02: Lifetime stats on results screen

### Phase 3 — Data corrections (next session or separate task)
8. DATA-01: Rename PMET label to reflect actual Learning content
9. DATA-02: Write generate_contrast.py and generate expansions for WDEV/CASS/PTHE/PETH

---

## FILES TO MODIFY

| File | Changes |
|------|---------|
| `thisorthat-exercise.html` | BUG-01, BUG-02, UI-03, FEAT-01, FEAT-02 |
| `thisorthat-settings.html` | UI-01, UI-02 |
| `data/PMET_contrast.json` | DATA-01 (domain_name field) |
| `generate_contrast.py` | DATA-02 (new file) |

---
*Reference this document for all This or That changes.*
