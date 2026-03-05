# Complete the Table — Change Plan
_Created: 2026-03-05_

## Overview

Seven concrete, scoped changes across three files.  No new features.
All changes are backwards-compatible with existing `table_data.js`.

---

## Files Modified

| File | Changes |
|------|---------|
| `table-settings.html` | 3 fixes |
| `table-exercise.html` | 4 fixes |
| `generate_tables.py`  | 1 fix   |

---

## Phase 1 — Settings Page (`table-settings.html`)

### Fix S-1: Add missing `.diff-btn` / `.d-title` / `.d-desc` CSS

**Problem:** The Challenge Mode section uses `.diff-btn`, `.d-title`, and `.d-desc` class names
that have zero CSS definitions in the file.  The three mode buttons render as completely
unstyled browser-default buttons.

**Location:** Insert after the `.count-btn.hover` rule (around line 202), inside `<style>`.

**CSS to add:**
```css
/* Challenge mode buttons */
.diff-row { display: flex; flex-direction: column; gap: 10px; }
.diff-btn {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.2s, background 0.2s;
  color: #fff;
  width: 100%;
}
.diff-btn.active {
  background: rgba(45,212,191,0.1);
  border-color: rgba(45,212,191,0.5);
}
.diff-btn:hover:not(.active) { border-color: rgba(45,212,191,0.25); }
.d-title { font-size: 13px; font-weight: 600; margin-bottom: 3px; color: var(--text); }
.diff-btn.active .d-title { color: var(--teal-light); }
.d-desc  { font-size: 11px; color: var(--text3); line-height: 1.4; }
```

---

### Fix S-2: "Select All" must exclude locked domains

**Problem:** `selectAllAvailable()` iterates ALL 9 `.domain-btn` elements, including ones
with the `.locked` class (no data available).  Clicking "Select All" adds locked domains to
`state.domains`, making them appear selected and passing their codes to the exercise URL.

Also `updateSummary()` uses the same all-buttons selector for the "Deselect All" toggle check,
so the button never flips to "Deselect All" as long as any locked domain exists.

**Location:** `selectAllAvailable()` function and `updateSummary()` function in `<script>`.

**Change in `selectAllAvailable()`:**
```js
// BEFORE:
const allBtns  = document.querySelectorAll('.domain-btn');

// AFTER:
const allBtns  = document.querySelectorAll('.domain-btn:not(.locked)');
```

**Change in `updateSummary()`:**
```js
// BEFORE:
const allBtnCodes = [...document.querySelectorAll('.domain-btn')].map(b => b.dataset.code);

// AFTER:
const allBtnCodes = [...document.querySelectorAll('.domain-btn:not(.locked)')].map(b => b.dataset.code);
```

---

### Fix S-3: Warn when requested count exceeds available pool

**Problem:** The count selector allows choosing 40 questions from a domain that has only
15–17 usable questions (WDEV: 15, PMET: 17, PTHE: 18).  The exercise page silently gives
fewer questions than requested with no indication to the user.

**Location:** `updateSummary()` in `<script>` + a new `<div>` element in the Count section card.

**HTML to add** (inside the count section-card, after `.count-row` div):
```html
<div id="count-warn" class="warn" style="color:#fbbf24; display:none;"></div>
```

**JS change** — add inside `updateSummary()`, after the `totalQ` line:
```js
const countWarn = document.getElementById('count-warn');
if (totalQ > 0 && totalQ < state.count) {
  countWarn.textContent =
    `Only ${totalQ} question${totalQ === 1 ? '' : 's'} available \u2014 session will use all of them.`;
  countWarn.style.display = 'block';
} else {
  countWarn.style.display = 'none';
}
```

---

## Phase 2 — Exercise Page (`table-exercise.html`)

### Fix E-1: Chip disambiguation by unique ID (same-value chip bug)

**Problem:** Chips are identified by `dataset.text` (the option string).  When two blanks in
the same question share identical text (e.g., two cells both reading "Impaired"), drag-and-drop
always picks the first matching chip element, not the one actually dragged.  This can cause the
wrong chip to be removed from the panel and the wrong blank to be considered filled.

**Fix:** Assign each chip a session-unique integer `data-chip-id`.  Pass the chipId via
`dataTransfer` so `ondrop` can find the exact chip element.  `returnChip` issues a new chipId
(that's fine — uniqueness during a single drag operation is all that matters).

**Changes to `<script>`:**

Add a counter above `makeChip`:
```js
let _chipIdSeq = 0;
```

Inside `makeChip`, add one line after `chip.draggable = true`:
```js
chip.dataset.chipId = String(_chipIdSeq++);
```

Inside `makeChip`'s `ondragstart`, add one line:
```js
e.dataTransfer.setData('chipId', chip.dataset.chipId);
```

Inside `wirePlaceTarget`'s `ondrop`, change the chipEl lookup from:
```js
// BEFORE:
const chipEl = chipEls.find(c => c.dataset.text === text && c.isConnected);

// AFTER:
const chipId = e.dataTransfer.getData('chipId');
const chipEl = chipId
  ? chipEls.find(c => c.dataset.chipId === chipId && c.isConnected)
  : chipEls.find(c => c.dataset.text === text && c.isConnected);
```

---

### Fix E-2: Hide Submit until all blanks are placed (Few / Full modes)

**Problem:** The Submit button is shown immediately when a question loads, even before the user
has placed any chips.  In multi-blank modes this invites accidental submission with empty blanks,
which silently marks all unfilled cells wrong.

**Fix:** In Few / Full modes, keep `submit-btn` hidden until every blank has `placedText !== null`.
Call a `checkSubmitReady()` helper from `placeChip()` and from the "return chip by tapping" path
inside `wirePlaceTarget`'s `onclick`.

**Add function** (insert near other helper functions):
```js
function checkSubmitReady() {
  if (MODE === 'one') return; // always visible in one-blank mode
  const allFilled = blanks.every(b => b.placedText !== null);
  document.getElementById('submit-btn').style.display = allFilled ? 'block' : 'none';
}
```

**Change in `showQuestion()`** — for multi-blank modes, start with submit hidden:
```js
// BEFORE:
document.getElementById('submit-btn').style.display = 'block';

// AFTER:
document.getElementById('submit-btn').style.display = MODE === 'one' ? 'block' : 'none';
```

**Change in `placeChip()`** — call checkSubmitReady at the end:
```js
// At the end of placeChip(), before the closing brace:
checkSubmitReady();
```

**Change in `wirePlaceTarget`'s `onclick`** — call checkSubmitReady after returning a chip:
```js
// In the `else if (blank.placedText !== null)` branch (return chip to panel):
// After: td.innerHTML = '<span class="drop-hint">Drop here</span>';
// Add:
checkSubmitReady();
```

---

### Fix E-3: Feedback panel shows all blank answers in Few / Full modes

**Problem:** After submitting in Three Blanks or Full Table mode, the `feedback-value` div reads:
> "Key answer: [q.correct_value]"
This is the primary blank value only.  Users who missed other blanks see no textual summary of
those correct values; they must read the colored table cells.

**Fix:** In Few / Full modes, build a mini-list of all blank → correct value pairs.

**Change in `submitAnswer()`**, replace the `feedback-value` innerHTML assignment:
```js
// BEFORE:
document.getElementById('feedback-value').innerHTML =
  MODE === 'one'
    ? `<strong>Answer:</strong> &ldquo;${escHtml(q.correct_value)}&rdquo;`
    : `<strong>Key answer:</strong> &ldquo;${escHtml(q.correct_value)}&rdquo;`;

// AFTER:
if (MODE === 'one') {
  document.getElementById('feedback-value').innerHTML =
    `<strong>Answer:</strong> &ldquo;${escHtml(q.correct_value)}&rdquo;`;
} else {
  const lines = blanks.map(b => {
    const colLabel = escHtml(q.headers[b.col] || ('Col ' + (b.col + 1)));
    return `<span style="color:var(--text2)">${colLabel} \u2192</span> &ldquo;${escHtml(b.value)}&rdquo;`;
  });
  document.getElementById('feedback-value').innerHTML =
    `<strong>Correct values:</strong><br>${lines.join('<br>')}`;
}
```

---

### Fix E-4: Review screen "Correct answer" label for multi-blank questions

**Problem:** `renderReview()` always appends:
> `✓ Correct answer: "[q.correct_value]"`
In Few / Full modes, this singles out only the original primary blank even though the student
missed other cells too.  The label is also grammatically singular.

**Fix:** Make the label context-aware.

**Change in `renderReview()`**, replace the `ansLabel.textContent` line:
```js
// BEFORE:
ansLabel.textContent = `\u2713 Correct answer: \u201c${q.correct_value}\u201d`;

// AFTER:
ansLabel.textContent = MODE === 'one'
  ? `\u2713 Correct answer: \u201c${q.correct_value}\u201d`
  : '\u2713 All correct values shown in table above';
```

---

## Phase 3 — Generator (`generate_tables.py`)

### Fix G-1: Add 140-character option limit to system prompt

**Problem:** `generate_tables.py` passes no length constraint to Claude.  31 of 266 generated
questions (12%) have at least one option > 140 characters and are silently filtered out by the
exercise page.  PETH loses 25% of its questions this way.

**Fix:** Add an explicit hard constraint to `SYSTEM_PROMPT`.

**Location:** End of the `Instructions:` numbered list and end of the `Rules:` section.

**Change:** In `SYSTEM_PROMPT`, add item 4 to the numbered instructions:
```
4. LENGTH CONSTRAINT (hard limit): Every string in "options" — including the correct answer —
   MUST be ≤ 140 characters.
   - If the natural cell text is longer than 140 characters, abbreviate it while preserving
     its key distinguishing details.
   - If you cannot represent all 4 distinct options within 140 characters each, pick a
     DIFFERENT cell to blank (one whose options will fit).
```

And add to `Rules:`:
```
- Every element of "options" must be ≤ 140 characters. This is a hard constraint with no exceptions.
```

---

## Verification Checklist

All 16 automated checks passed (2026-03-05).

- [x] **S-1**: `.diff-btn`, `.d-title`, `.d-desc` CSS added — Challenge Mode buttons now styled
- [x] **S-2**: `selectAllAvailable()` and `updateSummary()` use `:not(.locked)` selector
- [x] **S-3**: `#count-warn` div + JS logic added to `updateSummary()`
- [x] **E-1**: `_chipIdSeq` counter; `data-chip-id` on each chip; `chipId` in drag dataTransfer and ondrop lookup
- [x] **E-2**: `checkSubmitReady()` added; submit hidden initially in few/all mode; called from `placeChip()` and return-chip path
- [x] **E-3**: `feedback-value` now lists all blank→value pairs in few/all mode
- [x] **E-4**: Review "Correct answer" label is mode-aware

---

## Regeneration Step (requires API key)

The 31 over-length questions were **stripped from all JSON files** and the bundle was rebuilt
(2026-03-05).  Run this to regenerate them (and expand all domains toward 50 questions):

```bash
cd C:\Users\mcdan\mastery-page
python generate_tables.py --all --resume
```

`--resume` targets `count=50` per domain.  Current usable counts vs what will be attempted:

| Domain | Now | Target | New Qs |
|--------|-----|--------|--------|
| BPSY   |  39 |     50 |    ~11 |
| CASS   |  41 |     50 |     ~9 |
| CPAT   |  19 |     50 |    ~31 |
| LDEV   |  31 |     50 |    ~19 |
| PETH   |  33 |     50 |    ~17 |
| PMET   |  17 |     50 |    ~33 |
| PTHE   |  18 |     50 |    ~32 |
| SOCU   |  22 |     50 |    ~28 |
| WDEV   |  15 |     50 |    ~35 |
| **Total** | **235** | **450** | **~185** |

The generator auto-rebuilds `table_data.js` at the end.  If some domains can't reach 50
(too few tables in the HTML source), it will generate as many as exist.

## Out of Scope (deferred)

- Chapter/topic filtering within a domain (large feature)
- Session history / spaced repetition (large feature)
- Skip/Pass option during exercise
