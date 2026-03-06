# Spot the Error — Improvement Plan

Generated: 2026-03-05
Reference for all upcoming changes to the Spot the Error module.

---

## Priority 1 — High-Impact Bugs & UX Fixes (implement now)

### 1.1  Settings: Available count ignores mode + type filters
**File:** `spot-settings.html`
**Problem:** The summary bar "Available" count shows raw total questions for selected domains,
ignoring the chosen Exercise Mode and Passage Type filters. If a user picks WDEV + passage_click,
the bar says "203 available" but only 18 passage_click questions exist — they'd silently get 18
instead of the requested 20.

**Fix:**
1. Add a `DOMAIN_DATA = {}` object at the top of the script (parallel to `DOMAIN_COUNTS`).
2. In `checkAvailability()`, populate `DOMAIN_DATA[code]` with the full questions array from
   `window.__SPOT_DATA[code].questions` (in addition to already setting `DOMAIN_COUNTS[code] = n`).
3. In `updateSummary()`, replace the simple `.reduce(s + DOMAIN_COUNTS[c])` with a filtered
   reduce that applies `state.type` and `state.mode` to the raw arrays:
   ```js
   const totalQ = [...state.domains].reduce((s, c) => {
     let qs = DOMAIN_DATA[c] || [];
     if (state.type !== 'all') qs = qs.filter(q => q.passage_type === state.type);
     if (state.mode !== 'all') qs = qs.filter(q => (q.mode || 'mc') === state.mode);
     return s + qs.length;
   }, 0);
   ```
4. The domain button count display remains the raw total (so users can see how large each domain is
   regardless of filters). Only the summary bar "Available" field uses the filtered count.
5. If filtered totalQ is 0 but domains are selected, show a warning and disable the Start button
   (same as the no-domain-selected case). Warning text: "No questions match the selected filters."

---

### 1.2  Settings: "Select All" adds locked/unavailable domains to state
**File:** `spot-settings.html`
**Problem:** `selectAllAvailable()` iterates ALL `.domain-btn` elements (including locked ones with
0 questions) and adds them to `state.domains`. If a domain is locked, it adds nothing to the pool
but can cause confusing URL params.

**Fix:** Restrict the toggle to only codes present in `DOMAIN_COUNTS`:
```js
function selectAllAvailable() {
  const available = Object.keys(DOMAIN_COUNTS);
  const allSelected = available.every(c => state.domains.has(c));
  if (allSelected) {
    available.forEach(c => state.domains.delete(c));
  } else {
    available.forEach(c => state.domains.add(c));
  }
  document.querySelectorAll('.domain-btn').forEach(b =>
    b.classList.toggle('active', state.domains.has(b.dataset.code))
  );
  updateSummary();
}
```

---

### 1.3  Settings: Add "Paragraphs" as a selectable Passage Type
**File:** `spot-settings.html`
**Problem:** Passage Type only offers "All Types", "Definitions", "Clinical Notes." Paragraphs are
the most common passage type across all domains but are not filterable on their own.

**Fix:**
1. Add a fourth button to the passage-type `diff-row`:
   ```html
   <button class="diff-btn" data-type="paragraph" onclick="selectType('paragraph')">
     <div class="d-title">Paragraphs</div>
     <div class="d-desc">Standard study text passages</div>
   </button>
   ```
2. The `diff-row` already has `flex-wrap:wrap` (same as the Exercise Mode row), so a 4th option
   wraps cleanly. No CSS change needed.
3. Add `paragraph: 'Paragraphs'` to `TYPE_LABELS` in both `spot-settings.html` and
   `spot-exercise.html`.

---

### 1.4  Exercise: "Try Again" reuses the same pool instead of drawing fresh
**File:** `spot-exercise.html`
**Problem:** `restartSession()` reshuffles the existing `pool` variable in place. A user who scores
poorly and retries sees the exact same N questions in a different order. A genuine retry should draw
a new random sample from the full domain pool.

**Fix:** Extract the pool-building logic from `loadData()` into a standalone helper, then call it
from both `loadData()` (fresh session path) and `restartSession()`:

```js
// New helper — builds and shuffles a fresh pool from the full domain data
function buildFreshPool() {
  const spotData = window.__SPOT_DATA || {};
  const all = [];
  for (const code of DOMAIN_CODES) {
    const data = spotData[code];
    if (!data) continue;
    let qs = data.questions || [];
    if (TYPE_FILTER !== 'all') qs = qs.filter(q => q.passage_type === TYPE_FILTER);
    if (MODE_FILTER !== 'all') qs = qs.filter(q => (q.mode || 'mc') === MODE_FILTER);
    all.push(...qs);
  }
  for (let i = all.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [all[i], all[j]] = [all[j], all[i]];
  }
  return all.slice(0, COUNT);
}

function restartSession() {
  current = 0; correct = 0; answered = false; missed = [];
  clearSession();
  pool = buildFreshPool();
  document.getElementById('btn-review').style.display    = 'none';
  document.getElementById('screen-results').style.display = 'none';
  document.getElementById('progress-fill').style.width    = '0%';
  showQuestion();
}
```

In `loadData()`, replace the inline shuffle+slice with `pool = buildFreshPool()` (after the
session-restore check fails).

---

### 1.5  Exercise: Keyboard shortcuts for passage_click and vocab modes
**File:** `spot-exercise.html`
**Problem:** Keys 1–4 only work for MC mode. passage_click (sentences) and vocab (cards) have
natural discrete-item selection that maps to number keys. sentence_click is inline text and
doesn't support numbered selection cleanly — leave it mouse-only.

**Fix:**

**A. Update the keydown handler:**
```js
document.addEventListener('keydown', e => {
  if (answered) {
    if (e.key === 'Enter' || e.key === 'ArrowRight') {
      const nb = document.getElementById('next-btn');
      if (nb && nb.style.display !== 'none') nb.click();
    }
    return;
  }

  const q    = pool[current];
  const mode = q ? qMode(q) : 'mc';

  if (['1','2','3','4','5','6','7','8'].includes(e.key)) {
    const idx = parseInt(e.key) - 1;
    if (mode === 'mc') {
      const btns = document.querySelectorAll('.option-btn:not(:disabled)');
      if (btns[idx]) btns[idx].click();
    } else if (mode === 'passage_click') {
      const sents = document.querySelectorAll('.clickable-sentence');
      if (sents[idx]) sents[idx].click();
    } else if (mode === 'vocab') {
      const cards = document.querySelectorAll('.vocab-card');
      if (cards[idx]) cards[idx].click();
    }
    return;
  }
});
```

Note: passage_click can have up to ~8 sentences so support keys 1–8. vocab is always 4 cards.

**B. Add visible number labels to selectable items:**

In `renderPassageClick()`, prepend a faint position badge to each sentence div:
```js
div.innerHTML = `<span class="item-num">${idx + 1}</span>` +
  document.createTextNode(sentence).textContent;
// or construct as: div.dataset.num = idx + 1;
```
Simpler: set a CSS counter on `.passage-sentences` and use `::before` pseudo-elements — this
avoids innerHTML manipulation and works with the existing textContent assignment:
```css
.passage-sentences { counter-reset: sentence-num; }
.clickable-sentence {
  counter-increment: sentence-num;
  padding-left: 42px;
  position: relative;
}
.clickable-sentence::before {
  content: counter(sentence-num);
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  font-weight: 700;
  color: var(--text3);
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 5px;
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
  line-height: 1;
}
```

In `renderVocab()`, add a position badge to each card. Since cards are shuffled, the badge should
reflect the DOM (display) order. Add the badge in the card construction loop, using a display index:
```js
displayOrder.forEach((origIdx, displayIdx) => {
  // ...
  const badge = document.createElement('div');
  badge.className = 'vocab-num';
  badge.textContent = displayIdx + 1;
  card.insertBefore(badge, card.firstChild);
  // ...
});
```
CSS:
```css
.vocab-card { position: relative; }
.vocab-num {
  position: absolute; top: 10px; right: 10px;
  font-size: 10px; font-weight: 700; color: var(--text3);
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 5px; width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
}
```

**C. Update kbd-hint text in each renderer:**
- `renderPassageClick`: `<kbd>1</kbd>–<kbd>N</kbd> to select sentence &middot; <kbd>Enter</kbd> to continue`
- `renderVocab`: `<kbd>1</kbd>–<kbd>4</kbd> to select card &middot; <kbd>Enter</kbd> to continue`
- `renderSentenceClick`: `Click a phrase &middot; <kbd>Enter</kbd> to continue` (unchanged — no keyboard select)

---

## Priority 2 — Data Generation Gaps

### 2.1  CASS is severely undercovered (28%)
**Problem:** CASS has 832 source passages but only 237 spot questions. Every other domain is 40%+.
The gap represents ~400 untapped passages.

**Action:** Run the generator targeting CASS for all 4 modes with --resume:
```
cd mastery-page
python generate_spot_errors.py --domain CASS --mode mc --resume
python generate_spot_errors.py --domain CASS --mode vocab --resume
python generate_spot_errors.py --domain CASS --mode passage_click --resume
python generate_spot_errors.py --domain CASS --mode sentence_click --resume
```
Expected result: ~250–300 additional CASS questions (approaching 60% coverage).

### 2.2  WDEV passage_click is dangerously thin (18 questions)
**Problem:** A user selecting WDEV + passage_click + 20 questions gets only 18 silently.
**Action:** `python generate_spot_errors.py --domain WDEV --mode passage_click --resume`
Target: at least 40 passage_click questions for WDEV.

### 2.3  Other domains with low passage_click counts
PMET (32), PTHE (28), PETH (20) are all low relative to their total counts.
Run `--mode passage_click --resume` for each after CASS/WDEV.

---

## Priority 3 — Generator Improvements

### 3.1  Stamp "mode": "mc" on mc questions
**File:** `generate_spot_errors.py`
**Problem:** mc questions have no `mode` field; the JS default `q.mode || 'mc'` works but is
implicit. The data should be self-documenting.

**Fix:** In `generate_question()`, add `"mode": "mc"` to the returned dict:
```python
return {
    "id":           passage['id'],
    "mode":         "mc",          # ← add this
    "domain_code":  ...
```

Note: This changes the format of newly generated mc questions. Existing mc questions in the JSONs
have no mode field and the JS `|| 'mc'` fallback still covers them. No migration needed.

### 3.2  Add --mode all shortcut
**File:** `generate_spot_errors.py`
**Problem:** Generating all 4 modes requires 4 separate script invocations per domain.

**Fix:** Add `'all'` as a valid `--mode` choice. In `main()`, when mode is 'all', iterate
`['mc', 'passage_click', 'sentence_click', 'vocab']` sequentially, calling `process_domain()`
for each:
```python
if args.mode == 'all':
    for m in ['mc', 'passage_click', 'sentence_click', 'vocab']:
        for code in domains:
            process_domain(client, code, args.count, args.resume, m)
else:
    for code in domains:
        process_domain(client, code, args.count, args.resume, args.mode)
```
Update the `choices` list: `choices=['mc', 'passage_click', 'sentence_click', 'vocab', 'all']`

---

## Priority 4 — Lower Priority / Deferred

### 4.1  Cumulative performance history in localStorage
Store per-domain accuracy stats across sessions in a separate localStorage key
(`spot_stats_{domain_code}`). Display in the settings page domain buttons as a secondary line
below the question count: "Last session: 72%". This requires architecture in the exercise page
(write stats on session complete) and settings page (read stats in `checkAvailability`).
**Defer** — significant scope, not blocking.

### 4.2  "Focus on weak domains" mode
After enough session history exists, offer a "Smart Mode" in settings that weights the random pool
toward domains/chapters where the user has scored lowest. **Defer** — depends on 4.1.

### 4.3  Short-passage pre-filter for vocab and sentence_click generators
Some single-sentence bullets reach the vocab/sentence_click generators and produce questions with
minimal context (e.g., LDEV-0514). Add a minimum word count filter (e.g., >= 30 words) to `todo`
in `process_domain()` for vocab and sentence_click modes.
```python
if mode in ('vocab', 'sentence_click'):
    todo = [p for p in todo if len(p['passage'].split()) >= 30]
```
**Defer** — affects only new generation runs; existing question quality is acceptable.

---

## Implementation Order

1. [ ] Write planning doc (this file) — DONE
2. [ ] Implement 1.1 – 1.5 in settings and exercise pages
3. [ ] Run CASS generation (2.1)
4. [ ] Run WDEV passage_click generation (2.2)
5. [ ] Implement generator improvements (3.1, 3.2)
6. [ ] Run remaining thin passage_click domains (2.3)
7. [ ] Defer 4.x items

---

## File Manifest

| File | Changes |
|------|---------|
| `mastery-page/spot-settings.html` | 1.1, 1.2, 1.3 |
| `mastery-page/spot-exercise.html` | 1.4, 1.5 |
| `mastery-page/generate_spot_errors.py` | 3.1, 3.2 |
| `mastery-page/data/*_spot.json` | rebuilt by data generation (2.x) |
| `mastery-page/data/spot_data.js` | rebuilt by build_spot_bundle.py after 2.x |
