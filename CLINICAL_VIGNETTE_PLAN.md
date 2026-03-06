# Clinical Vignette Module — Improvement Plan
_Generated: 2026-03-05_

This document details every identified issue with the clinical vignette module and provides exact implementation instructions. Work through sections in order — earlier sections have no dependencies and no regression risk.

---

## Section 1 — Data Corrections (no regression risk)

### 1.1 Fix BPSY Subdomain Capitalization

**File:** `data/BPSY_vignettes.json`
**Issue:** 5 questions carry the subdomain string `"Neurological and Endocrine disorders"` (lowercase 'd'). The canonical form used by 85 other questions is `"Neurological and Endocrine Disorders"`. The Sequential sort and meta-badges will treat these as two separate subdomains.
**Fix:** String replace in the JSON file.

- Find: `"Neurological and Endocrine disorders"`
- Replace with: `"Neurological and Endocrine Disorders"`
- Occurrences: 5 (all within `"subdomain"` fields)

### 1.2 Fix Hardcoded Counts in Settings Page

**File:** `clinical-settings.html`
**Issue:** All nine domain cards display hardcoded anchor and vignette counts that are wrong — sourced from projected generation targets, never updated after actual generation. Actual vs. claimed:

| Domain | Correct Text to Display |
|--------|------------------------|
| PMET   | `91 anchors · 620 vignettes` |
| LDEV   | `117 anchors · 585 vignettes` |
| CPAT   | `132 anchors · 660 vignettes` |
| PTHE   | `98 anchors · 550 vignettes` |
| SOCU   | `96 anchors · 505 vignettes` |
| WDEV   | `113 anchors · 565 vignettes` |
| BPSY   | `131 anchors · 695 vignettes` |
| CASS   | `61 anchors · 325 vignettes` |
| PETH   | `112 anchors · 560 vignettes` |

**Fix:** In `clinical-settings.html`, find each `<div class="domain-q-count">` block and replace its text content with the correct values from the table above.

---

## Section 2 — Domain Label Fixes

### 2.1 Rename PETH Display Name

**File:** `clinical-settings.html`
**Issue:** The PETH domain card reads "Psychopharmacology & Ethics" but all 560 PETH questions are exclusively ethics/legal/professional content (legacy code `ETH`). The psychopharmacology content (antipsychotics, antidepressants, other psychoactive drugs) is entirely in BPSY — 105 questions across two subdomains. A user selecting PETH to study pharmacology gets zero pharmacology.

**Fix:** Change the PETH domain full name to:
> `Ethics, Law & Professional Practice`

In `clinical-settings.html`, find:
```html
<div class="domain-full-name">Psychopharmacology &amp; Ethics</div>
```
Replace with:
```html
<div class="domain-full-name">Ethics, Law &amp; Professional Practice</div>
```

No change needed to domain code, JSON files, or exercise page (domain code `PETH` stays the same everywhere).

### 2.2 Rename PMET Display Name

**File:** `clinical-settings.html`
**Issue:** PMET is labeled "Psychometrics & Research Methods" but 125 of 620 questions (20%) cover operant conditioning, classical conditioning, and memory/forgetting — sourced from legacy code `LEA` (Learning). These are not standard psychometrics topics and will surprise users studying for that domain.

**Fix:** Change the PMET domain full name to:
> `Research Methods, Measurement & Learning`

In `clinical-settings.html`, find:
```html
<div class="domain-full-name">Psychometrics &amp; Research Methods</div>
```
Replace with:
```html
<div class="domain-full-name">Research Methods, Measurement &amp; Learning</div>
```

**Longer-term (deferred — requires data regeneration):** Move the 125 LEA questions out of PMET and into BPSY, since classical/operant conditioning and memory are biological bases of behavior on the EPPP. This requires rerunning generation with corrected domain routing. Do not attempt during this pass.

---

## Section 3 — Exercise Page Bug Fixes

### 3.1 Fix Results "Domains" Count (1-line fix)

**File:** `clinical-exercise.html`, line 654
**Issue:** The results summary card shows `CFG.domains.length` — the number of domains the user _selected_, not the number that actually appeared in their question set. If a user selects 9 domains but draws 10 questions (all happening to come from 2 domains), it displays "9".
**Fix:** `domainsUsed` is already computed on line 660. Use it.

Find (line 654):
```js
<div class="rs-item"><span class="rs-label">Domains</span><span class="rs-val">${CFG.domains.length}</span></div>
```
Replace with:
```js
<div class="rs-item"><span class="rs-label">Domains</span><span class="rs-val">${domainsUsed.length}</span></div>
```

**Dependency:** This line must execute after `domainsUsed` is defined (line 660). Since both are inside `showResults()` and this line is in a template literal assigned to `innerHTML`, the actual DOM write happens via `document.getElementById('results-summary').innerHTML = ...` which runs before `domainsUsed` is declared. **Resolution:** Move the `domainsUsed` declaration (line 660) to _before_ the results-summary innerHTML assignment (line 650). Then use `domainsUsed.length` in the template literal.

Restructured `showResults()` ordering:
1. Compute `total`, `correct`, `pct`
2. Compute `domainsUsed` ← move here (currently line 660)
3. Compute `levelsUsed`
4. Set ring animation
5. Set `results-summary` innerHTML (now can reference `domainsUsed.length`)
6. Build domain rows (already uses `domainsUsed`)

### 3.2 Fix CSS :not() Wildcard Selector

**File:** `clinical-exercise.html`, line 113
**Issue:** `.option-btn:hover:not(.answered-*)` — the `*` wildcard inside `:not()` is not valid CSS. Browsers silently drop the `:not()` entirely, meaning option buttons retain their hover effect (color change, translateX transform) even after the user has answered. This is confusing visual feedback.

**Fix:** After an answer is selected, add the class `answered` to every `.option-btn` in the grid. Update the CSS rule to use `:not(.answered)`.

**CSS change** — find:
```css
.option-btn:hover:not(.answered-*) { background:rgba(255,255,255,.045); border-color:rgba(212,160,84,.3); transform:translateX(2px); }
```
Replace with:
```css
.option-btn:hover:not(.answered) { background:rgba(255,255,255,.045); border-color:rgba(212,160,84,.3); transform:translateX(2px); }
```

**JS change** — in `selectAnswer()` and `timeoutQuestion()`, after the `document.querySelectorAll('.option-btn').forEach(...)` loop, add:
```js
document.querySelectorAll('.option-btn').forEach(btn => btn.classList.add('answered'));
```

### 3.3 Fix Hint Highlighting Edge-Case Bug

**File:** `clinical-exercise.html`, function `highlightHints` (~line 367)
**Issue:** The function calls `escapeHtml(text)` first, then applies regex to the escaped output. If a hint word contains `&`, `<`, or `>` (unlikely but possible), the HTML-escaped form (`&amp;`, `&lt;`, `&gt;`) won't match. More importantly, the regex `\b` word-boundary on the _escaped_ text may mismatch on `&amp;` boundaries.

**Fix:** Rewrite to split on hint words first, then escape each piece:

```js
function highlightHints(text, words) {
  if (!words || !words.length) return escapeHtml(text);

  // Build a regex that matches any hint word (longest first to avoid partial matches)
  const sorted = [...words].sort((a, b) => b.length - a.length);
  const pattern = sorted.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const re = new RegExp(`(${pattern})`, 'gi');

  // Split on matches, escape each segment, wrap matches in span
  return text.split(re).map((seg, i) =>
    i % 2 === 1
      ? `<span class="hint-word">${escapeHtml(seg)}</span>`
      : escapeHtml(seg)
  ).join('');
}
```

This approach splits the raw text on hint-word boundaries before escaping, so special characters in either the text or the hint words are handled correctly.

---

## Section 4 — Exercise Page UX Improvements

### 4.1 True Session Retry via sessionStorage

**File:** `clinical-exercise.html`
**Issue:** `retrySession()` calls `location.href = location.href`, which re-runs `loadQuestions()` with a fresh shuffle — producing different questions each time. Users expecting to reattempt the same failed questions get a new random draw.

**Plan:**
- When `loadQuestions()` finalizes the `questions` array (after slice), store the array of question IDs to `sessionStorage`:
  ```js
  sessionStorage.setItem('clinical_retry_ids', JSON.stringify(questions.map(q => q.id)));
  ```
- `retrySession()` sets a flag before reloading:
  ```js
  function retrySession() {
    sessionStorage.setItem('clinical_retry_mode', '1');
    location.href = location.href;
  }
  ```
- At the start of `loadQuestions()`, check for retry mode. If set, load all relevant domain files, filter to the saved IDs (preserving order), skip the normal count/order slice logic, clear the flag, and proceed:
  ```js
  const retryIds = sessionStorage.getItem('clinical_retry_mode') === '1'
    ? JSON.parse(sessionStorage.getItem('clinical_retry_ids') || '[]')
    : null;
  sessionStorage.removeItem('clinical_retry_mode');
  ```
  After building `pool`, if `retryIds` is set:
  ```js
  const idSet = new Set(retryIds);
  const idOrder = new Map(retryIds.map((id, i) => [id, i]));
  questions = pool.filter(q => idSet.has(q.id)).sort((a, b) => idOrder.get(a.id) - idOrder.get(b.id));
  ```

### 4.2 Wrong-Answer Review Screen

**File:** `clinical-exercise.html`
**Issue:** After completion, users see only aggregate stats. There is no way to revisit the specific questions they got wrong, review the explanations, or see which answer was correct.

**Plan:**

**Data collection:** Already collected in `sessionAnswers`. Extend `recordAnswer()` to also push the full question object when wrong:
```js
// Add to session state at top:
const wrongQuestions = [];

// In recordAnswer(), after pushing to sessionAnswers:
if (!isCorrect) wrongQuestions.push(questions[current]);
```

**New screen:** Add a fourth screen `#screen-review` after `#screen-results`. It renders wrong questions in read-only mode with the correct answer pre-highlighted and all per-option explanations visible.

**Results page button:** Add "Review Mistakes (N)" button to `results-actions`. Only render it if `wrongQuestions.length > 0`. Clicking it transitions to `#screen-review`.

**Review screen layout:**
- Header: "Review — N Missed Questions"
- For each wrong question: the vignette card, question text, all options (rendered with `.correct` or `.dimmed` classes pre-applied, per-option explanations visible), domain/subdomain/level badges.
- No timer, no interaction — pure read-only.
- "Back to Results" and "New Session" buttons at bottom.

**Screen structure to add** (after `#screen-results` div):
```html
<div id="screen-review" class="screen">
  <div class="results-inner">
    <div class="results-hero">
      <h1>Review <em>Mistakes</em></h1>
    </div>
    <div id="review-questions"></div>
    <div class="results-actions">
      <button class="btn-primary" onclick="newSession()">New Session</button>
      <button class="btn-secondary" onclick="backToResults()">← Back to Results</button>
    </div>
  </div>
</div>
```

**`renderReview()` function:**
```js
function renderReview() {
  document.getElementById('screen-results').classList.remove('active');
  document.getElementById('screen-review').classList.add('active');
  const container = document.getElementById('review-questions');
  container.innerHTML = '';
  wrongQuestions.forEach((q, idx) => {
    const div = document.createElement('div');
    div.style.cssText = 'margin-bottom:32px; border-top:1px solid var(--border); padding-top:24px;';
    div.innerHTML = `
      <div class="meta-row" style="margin-bottom:12px;">
        <span class="badge badge-domain">${q.domain_code}</span>
        <span class="badge badge-sub">${q.subdomain || ''}</span>
        <span class="badge ${LEVEL_BADGE_CLASS[q.difficulty_level]}">${LEVEL_LABELS[q.difficulty_level]}</span>
        <span style="margin-left:auto;font-size:11px;color:var(--text3);">${idx + 1} / ${wrongQuestions.length}</span>
      </div>
      <div class="vignette-card" style="margin-bottom:16px;">
        <div class="vignette-label">Vignette</div>
        <div class="vignette-text">${escapeHtml(q.vignette)}</div>
      </div>
      <div class="question-text" style="margin-bottom:16px;">${escapeHtml(q.question)}</div>
      <div class="options-grid">
        ${Object.entries(q.options).map(([letter, text]) => {
          const isCorrect = letter === q.correct_answer;
          const cls = isCorrect ? 'correct' : 'dimmed';
          const icon = isCorrect ? '✓' : '';
          const exp = (q.option_explanations || {})[letter] || '';
          return `
            <div class="option-btn ${cls}" style="cursor:default;">
              <div class="option-letter">${letter}</div>
              <div class="option-content">
                <div class="option-text">${escapeHtml(text)}</div>
                ${exp ? `<div class="option-explanation">${escapeHtml(exp)}</div>` : ''}
              </div>
              <span class="option-icon">${icon}</span>
            </div>`;
        }).join('')}
      </div>
    `;
    container.appendChild(div);
  });
}

function backToResults() {
  document.getElementById('screen-review').classList.remove('active');
  document.getElementById('screen-results').classList.add('active');
}
```

**Review button in results-actions:**
```html
<!-- Only show if wrong questions exist — inject via JS after showResults() -->
```
In `showResults()`, after building the existing buttons:
```js
if (wrongQuestions.length > 0) {
  const reviewBtn = document.createElement('button');
  reviewBtn.className = 'btn-secondary';
  reviewBtn.textContent = `Review Mistakes (${wrongQuestions.length})`;
  reviewBtn.onclick = renderReview;
  document.querySelector('.results-actions').appendChild(reviewBtn);
}
```

### 4.3 Disable "Weakest First" for New Users

**File:** `clinical-settings.html`
**Issue:** "Weakest First" is always selectable, but on first use (no `mastery_scores` in localStorage) all domains tie at 0.5, making the sort meaningless. The feature silently provides no benefit.

**Plan:** On page load in the settings script, check for stored scores. If none exist for the `clinical` module, add a visual indicator to the "Weakest First" toggle option and disable it from selection, replacing its sublabel with an explanatory note.

```js
// At the end of the settings script, after updateSummary():
(function checkWeakestFirst() {
  try {
    const stored = JSON.parse(localStorage.getItem('mastery_scores') || '{}');
    const hasHistory = stored.clinical && Object.values(stored.clinical).some(s => s.total > 0);
    if (!hasHistory) {
      const weakestOption = document.querySelector('[data-order="weakest"]');
      if (weakestOption) {
        weakestOption.style.opacity = '0.45';
        weakestOption.style.cursor = 'default';
        weakestOption.style.pointerEvents = 'none';
        weakestOption.querySelector('.toggle-sublabel').textContent = 'Complete a session first to unlock';
      }
    }
  } catch {}
})();
```

---

## Section 5 — Settings Page UX Improvements

### 5.1 Timer Warning for 25s + L4/L5

**File:** `clinical-settings.html`
**Issue:** L4/L5 vignettes are 150–300+ words with four lengthy answer choices requiring careful reasoning. The 25-second "Rapid Fire" timer does not allow enough time to read the vignette, let alone reason through complex distractors. Users may not realize this mismatch before starting.

**Plan:** Add a warning element below the timer section that appears when _both_ the 25s timer is selected _and_ any of L4 or L5 is selected.

Add HTML after the rapid-fire grid:
```html
<p class="warn" id="timer-level-warn" style="display:none;">
  ⚠ 25 seconds may be insufficient for L4/L5 vignettes, which require reading 150–300+ words and evaluating complex answer choices.
</p>
```

Add JS trigger in both `selectRapid()` and `toggleLevel()`:
```js
function updateTimerLevelWarn() {
  const hasHighLevel = state.levels.has('4') || state.levels.has('5');
  const isRapidFire  = state.timer === '25';
  document.getElementById('timer-level-warn').style.display =
    (hasHighLevel && isRapidFire) ? 'block' : 'none';
}
// Call updateTimerLevelWarn() at the end of toggleLevel() and selectRapid()
```

---

## Section 6 — Content Development (Deferred — Requires Generation)

These items cannot be addressed by code changes alone. They require running the vignette generation pipeline.

### 6.1 Expand CASS

CASS has only 325 questions (61 anchors, 7 subdomains) — the most underdeveloped domain. Target parity is ~550 questions (110 anchors).

**Missing subdomains to add:**
- Neuropsychological assessment (Halstead-Reitan, Luria-Nebraska, Trail Making)
- Projective techniques (Rorschach, TAT, sentence completion)
- Structured clinical interviews (SCID, MINI, diagnostic interviewing)
- Behavioral observation methods
- MMPI-2 expanded (currently only 30 questions — need ~60)
- Cross-cultural assessment considerations

**Action:** Identify source passages in `content/domain8/*.html` covering these areas, generate anchors and vignettes using `generate_spot_errors.py` equivalent for vignettes, append to `CASS_vignettes.json` without resetting existing IDs.

### 6.2 Resolve PETH Psychopharmacology Gap

PETH is named "Psychopharmacology & Ethics" but contains zero pharmacology content. Two options:

**Option A (Recommended — no regeneration):** Rename definitively (already done in Section 2.1). Psychopharmacology content remains in BPSY, which is the academically appropriate home for it. Update the settings page BPSY description to note it includes pharmacology subdomains.

**Option B (Deferred):** Generate pharmacology-focused vignettes (antipsychotics, antidepressants, mood stabilizers, anxiolytics, stimulants — mechanisms, side effects, clinical decision-making) and add them to `PETH_vignettes.json`. This would require sourcing from domain content files and running the generation pipeline. Do not attempt until CASS expansion is complete.

### 6.3 Resolve PMET Anchor ID Collisions

23 of 91 PMET source question IDs generated 15 vignettes each (3 distinct anchors × 5 levels) due to ID normalization errors ('01', '001', '1' treated as separate IDs during generation). This creates content redundancy clusters in PMET.

**Action (deferred):** During next PMET regeneration, deduplicate source question IDs by normalizing to zero-padded 3-digit strings before generation. No immediate code fix needed.

---

## Implementation Order

| # | Change | File | Status |
|---|--------|------|--------|
| 1 | BPSY subdomain capitalization fix | `data/BPSY_vignettes.json` | ✅ Done |
| 2 | Fix all 9 domain count labels | `clinical-settings.html` | ✅ Done (now dynamic) |
| 3 | Rename PETH display name | `clinical-settings.html` | ✅ Done |
| 4 | Rename PMET display name | `clinical-settings.html` | ✅ Done |
| 5 | Fix results Domains count | `clinical-exercise.html` | ✅ Done |
| 6 | Fix CSS :not() + add answered class | `clinical-exercise.html` | ✅ Done |
| 7 | Fix highlightHints() | `clinical-exercise.html` | ✅ Done |
| 8 | Disable Weakest First when no history | `clinical-settings.html` | ✅ Done |
| 9 | Timer/level warning | `clinical-settings.html` | ✅ Done |
| 10 | True retry via sessionStorage | `clinical-exercise.html` | ✅ Done |
| 11 | Wrong-answer review screen | `clinical-exercise.html` | ✅ Done |
| 11b | Keyboard navigation (A/B/C/D, Enter) | `clinical-exercise.html` | ✅ Done |
| 11c | No-questions dead-end fix (back link) | `clinical-exercise.html` | ✅ Done |
| 11d | Dynamic counts from vignette_stats.json | `clinical-settings.html` | ✅ Done |
| 12 | Expand CASS content | `data/CASS_vignettes.json` | ✅ Done (146 anchors · 750 vignettes) |
| 13 | Resolve PMET anchor ID collisions | `data/PMET_vignettes.json` | ✅ Done (124 anchors · 620 vignettes, 0 duplicate IDs) |

## Final vignette_stats.json (2026-03-05)
| Domain | Anchors | Vignettes |
|--------|---------|-----------|
| PMET   | 124     | 620       |
| LDEV   | 117     | 585       |
| CPAT   | 132     | 660       |
| PTHE   | 98      | 550       |
| SOCU   | 96      | 505       |
| WDEV   | 113     | 565       |
| BPSY   | 131     | 695       |
| CASS   | 146     | 750       |
| PETH   | 112     | 560       |
| **Total** | **1,069** | **5,490** |

## CASS Generation Notes (2026-03-05)
- Generator: `mastery-page/generate_vignettes.py`
- Source: `PassEPPP-website/content/questions/domain-8-{ae,ic,lf,ns,pa,ts,vi}.json`
- Each file has 10 usable (single_choice/multiple_choice) + 16 non-standard (skipped)
- 85 new anchors × 5 levels = 425 new vignettes → CASS total: 146 anchors, 750 vignettes
- Manifest `data/vignette_stats.json` auto-updates after each anchor

## PMET ID Fix Notes (2026-03-05)
- Script: `mastery-page/fix_pmet_ids.py`
- Problem: 91 apparent source IDs but 124 true anchors (collisions via '1'/'01'/'001' normalization)
- Fix: grouped by (source_question_id, source_summary) → assigned sequential zero-padded 3-digit IDs
- Result: 124 unique anchors, 620 vignettes preserved, 0 duplicate vignette IDs
