# Streak Challenge — Change Plan
**Generated:** 2026-03-05
**Scope:** `streak-settings.html`, `streak-exercise.html`, `data/streak_manifest.json` (new)

---

## Change Index

| ID    | Title                                   | Priority | Files                                     |
|-------|-----------------------------------------|----------|-------------------------------------------|
| SC-01 | Show explanation after each answer      | P1       | streak-exercise.html                      |
| SC-02 | Fix isNewBest tracking (use flag)       | P1       | streak-exercise.html                      |
| SC-03 | Fix streak-best-inline display logic    | P1       | streak-exercise.html                      |
| SC-04 | Difficulty level filter                 | P2       | streak-settings.html, streak-exercise.html|
| SC-05 | Angle focus filter                      | P2       | streak-settings.html, streak-exercise.html|
| SC-06 | Dynamic question counts via manifest    | P2       | streak-settings.html, data/ (new file)    |

---

## SC-01 — Show Explanation After Each Answer

**Problem:** The `explanation` field exists on every question but is never surfaced. After a correct or wrong answer, the user sees only "Correct! Streak: X" or "Incorrect — streak reset." They can't learn why an answer is right or wrong, which undermines the educational purpose of the module.

**Solution:** Add an explanation panel below the feedback bar that appears after every answer (correct or wrong) and disappears when the next question loads.

---

### streak-exercise.html — CSS

Add after the `.feedback-bar` rule block (around line 285):

```css
/* Explanation panel */
.explanation-box {
  display: none;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--text2);
  line-height: 1.65;
  animation: slideUp 0.25s ease-out both;
}
.explanation-box.visible { display: block; }
.explanation-label {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text3);
  margin-bottom: 8px;
}
```

---

### streak-exercise.html — HTML

Insert immediately after the `#feedback-bar` div and before `#next-btn` (around line 440):

```html
<div class="explanation-box" id="explanation-box">
  <div class="explanation-label">&#128218; Explanation</div>
  <div id="explanation-text"></div>
</div>
```

---

### streak-exercise.html — JS: nextQuestion()

At the bottom of `nextQuestion()` where feedback is reset (around line 660), add:

```js
// Reset explanation
const expBox = document.getElementById('explanation-box');
expBox.classList.remove('visible');
document.getElementById('explanation-text').textContent = '';
```

---

### streak-exercise.html — JS: selectOption()

At the end of `selectOption()`, after `showFeedback(...)` is called for both correct and wrong branches, add a unified block (after line 714):

```js
// Show explanation (always)
const expBox = document.getElementById('explanation-box');
if (current.explanation) {
  document.getElementById('explanation-text').textContent = current.explanation;
  expBox.classList.add('visible');
}
```

Place this BEFORE the `setTimeout(() => endGame(false), 1200)` branch — when the game is ending immediately (lives = 0), the explanation is briefly visible before the game-over screen transitions, which is intentional. The 1200ms delay is enough to read it.

---

## SC-02 — Fix isNewBest Tracking

**Problem:** `endGame()` uses `finalStreak >= bestStreak` to show the "New Personal Best!" badge (line 742). But `bestStreak` is updated during the run on every correct answer. So by the time endGame runs, `finalStreak === bestStreak` is the expected state even after setting a genuine new best — making `>=` fire on ties with the prior session best too.

**Root cause:** The flag for "did we set a new best this run?" is conflated with the end-state comparison.

**Solution:** Track a boolean `newBestSet` that becomes `true` the first time `bestStreak` is updated. Use this flag in `endGame` instead of the comparison.

---

### streak-exercise.html — JS: State variables (around line 511)

Add after `let lastWrong = null;`:

```js
let newBestSet = false;  // true if bestStreak was surpassed this run
```

---

### streak-exercise.html — JS: selectOption() — correct branch (around line 691)

Replace the existing bestStreak update block:

```js
// BEFORE:
if (streak > bestStreak) {
  bestStreak = streak;
  localStorage.setItem(STORAGE_KEY, bestStreak);
}

// AFTER:
if (streak > bestStreak) {
  bestStreak = streak;
  localStorage.setItem(STORAGE_KEY, bestStreak);
  newBestSet = true;
}
```

---

### streak-exercise.html — JS: endGame() (line 742)

Replace:

```js
// BEFORE:
const isNewBest = finalStreak > 0 && finalStreak >= bestStreak && !exhausted;

// AFTER:
const isNewBest = newBestSet && !exhausted;
```

---

### streak-exercise.html — JS: restartStreak()

Reset the flag on restart (around line 773):

```js
// Add:
newBestSet = false;
```

---

## SC-03 — Fix streak-best-inline Display Logic

**Problem:** `bumpStreakDisplay()` (line 613) shows a sub-label under the streak counter. The current logic:
```js
bestInline.textContent = peakStreak > streak ? `Session best: ${peakStreak}` : (bestStreak > streak ? `Personal best: ${bestStreak}` : '');
```
Goes **blank** in these valid, motivating states:
- Right after recovering your session peak (peakStreak === streak, bestStreak === streak)
- When you're at exactly your personal best mid-run (streak === bestStreak, no prior session loss)

**Solution:** Rewrite the condition with explicit cases.

---

### streak-exercise.html — JS: bumpStreakDisplay() (line 613)

Replace the `bestInline.textContent` line with:

```js
const bestInline = document.getElementById('streak-best-inline');
if (peakStreak > streak) {
  // Recovering from an earlier loss — show this session's peak
  bestInline.textContent = `Session best: ${peakStreak}`;
} else if (bestStreak > streak) {
  // Below all-time best — motivate
  bestInline.textContent = `Personal best: ${bestStreak}`;
} else {
  // At or beyond all-time best — the big number speaks for itself
  bestInline.textContent = '';
}
```

This avoids the blank state on recovery and simplifies the logic.

---

## SC-04 — Difficulty Level Filter

**Problem:** Every question has a `difficulty_level` field (1 = easy, 2 = medium, 3 = hard) populated across all 9 `_basic.json` files, but the streak module ignores it. Users cannot warm up with easy questions or intentionally challenge themselves with hard ones.

**Solution:** Add a "Difficulty" toggle section to the settings page (5 options: All / Easy / Medium / Hard / Medium+Hard). Pass as a URL param and filter the pool in the exercise before shuffle.

---

### streak-settings.html — state object (line 533)

Add `difficulty` field:

```js
const state = {
  domains:    new Set(),
  mixed:      false,
  lives:      1,
  lifeevery:  '0',
  shuffle:    'on',
  difficulty: 'all',   // NEW
};
```

---

### streak-settings.html — HTML: New section after "Question Order" section (after line 501)

```html
<!-- ── 5. DIFFICULTY ── -->
<div class="settings-section">
  <div class="section-header">
    <div class="section-label">Difficulty</div>
  </div>
  <div class="toggle-row">
    <div class="toggle-option selected" data-difficulty="all" onclick="selectToggle(this,'difficulty')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">All Levels</div>
        <div class="toggle-sublabel">Easy, medium &amp; hard mixed</div>
      </div>
    </div>
    <div class="toggle-option" data-difficulty="1" onclick="selectToggle(this,'difficulty')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Easy</div>
        <div class="toggle-sublabel">Foundational recall</div>
      </div>
    </div>
    <div class="toggle-option" data-difficulty="2" onclick="selectToggle(this,'difficulty')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Medium</div>
        <div class="toggle-sublabel">Application &amp; contrast</div>
      </div>
    </div>
    <div class="toggle-option" data-difficulty="3" onclick="selectToggle(this,'difficulty')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Hard</div>
        <div class="toggle-sublabel">Scenarios &amp; implications</div>
      </div>
    </div>
  </div>
</div>
```

---

### streak-settings.html — HTML: Summary bar (around line 504–523)

Add two new summary items after the Shuffle item:

```html
<div class="summary-sep"></div>
<div class="summary-item">
  <span class="s-label">Difficulty</span>
  <span class="s-val" id="sum-difficulty">All</span>
</div>
```

---

### streak-settings.html — JS: updateSummary()

Add inside `updateSummary()`:

```js
const diffLabels = { all: 'All', '1': 'Easy', '2': 'Medium', '3': 'Hard' };
document.getElementById('sum-difficulty').textContent = diffLabels[state.difficulty] || 'All';
```

---

### streak-settings.html — JS: startSession()

Add `difficulty` to the URL params:

```js
const params = new URLSearchParams({
  domains,
  lives:      state.lives,
  lifeevery:  state.lifeevery,
  shuffle:    state.shuffle,
  difficulty: state.difficulty,   // NEW
});
```

---

### streak-exercise.html — JS: Config section (around line 491)

Add after the `SHUFFLE` constant:

```js
const DIFFICULTY = params.get('difficulty') || 'all';
```

---

### streak-exercise.html — JS: loadQuestions() — pool filtering (after pool concatenation, before shuffle block, around line 537)

Insert after the `pool.length === 0` check but before the shuffle block:

```js
// Apply difficulty filter
if (DIFFICULTY !== 'all') {
  const level = parseInt(DIFFICULTY, 10);
  pool = pool.filter(q => q.difficulty_level === level);
  if (pool.length === 0) {
    document.getElementById('loading-text').textContent =
      'No questions found for that difficulty level. Try a different setting.';
    return;
  }
}
```

---

### streak-exercise.html — JS: STORAGE_KEY (line 498)

Update the storage key to include difficulty so bests are tracked per difficulty level:

```js
// BEFORE:
const STORAGE_KEY = 'streak_best_' + CFG_DOMAINS.slice().sort().join('_');

// AFTER:
const STORAGE_KEY = 'streak_best_' + CFG_DOMAINS.slice().sort().join('_') + '_d' + DIFFICULTY;
```

---

## SC-05 — Angle Focus Filter

**Problem:** All 5 question angles (direct_recall, clinical_scenario, contrast, example_recognition, implication) are always mixed in. A user who wants to focus on clinical application (scenarios) or pure recall can't isolate those.

**Solution:** Add a single-select "Angle" toggle after the Difficulty section. Options: All Angles | Recall | Scenarios | Contrast | Example | Implication. Passed as URL param, filtered in exercise.

Each angle is exactly 20% of any domain's pool, so per-domain counts for a single-angle single-domain run would be: BPSY=206, CASS=96, CPAT=210, etc. — adequate for a streak session.

---

### streak-settings.html — state object

Add `angle` field:

```js
angle: 'all',
```

---

### streak-settings.html — HTML: New section after Difficulty section

```html
<!-- ── 6. ANGLE FOCUS ── -->
<div class="settings-section">
  <div class="section-header">
    <div class="section-label">Angle Focus</div>
  </div>
  <div class="toggle-row" style="flex-wrap: wrap;">
    <div class="toggle-option selected" data-angle="all" onclick="selectToggle(this,'angle')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">All Angles</div>
        <div class="toggle-sublabel">Mixed question types</div>
      </div>
    </div>
    <div class="toggle-option" data-angle="direct_recall" onclick="selectToggle(this,'angle')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Recall</div>
        <div class="toggle-sublabel">Definition &amp; identification</div>
      </div>
    </div>
    <div class="toggle-option" data-angle="clinical_scenario" onclick="selectToggle(this,'angle')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Scenarios</div>
        <div class="toggle-sublabel">Vignette application</div>
      </div>
    </div>
    <div class="toggle-option" data-angle="contrast" onclick="selectToggle(this,'angle')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Contrast</div>
        <div class="toggle-sublabel">Distinguish similar concepts</div>
      </div>
    </div>
    <div class="toggle-option" data-angle="example_recognition" onclick="selectToggle(this,'angle')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Examples</div>
        <div class="toggle-sublabel">Recognize real-world instances</div>
      </div>
    </div>
    <div class="toggle-option" data-angle="implication" onclick="selectToggle(this,'angle')">
      <div class="toggle-radio"><div class="toggle-radio-dot"></div></div>
      <div>
        <div class="toggle-label">Implication</div>
        <div class="toggle-sublabel">Higher-order consequences</div>
      </div>
    </div>
  </div>
</div>
```

---

### streak-settings.html — HTML: Summary bar

Add after the Difficulty summary item:

```html
<div class="summary-sep"></div>
<div class="summary-item">
  <span class="s-label">Angle</span>
  <span class="s-val" id="sum-angle">All</span>
</div>
```

---

### streak-settings.html — JS: updateSummary()

```js
const angleLabels = {
  all: 'All', direct_recall: 'Recall', clinical_scenario: 'Scenarios',
  contrast: 'Contrast', example_recognition: 'Examples', implication: 'Impl.'
};
document.getElementById('sum-angle').textContent = angleLabels[state.angle] || 'All';
```

---

### streak-settings.html — JS: startSession()

Add `angle` to URL params:

```js
angle: state.angle,
```

---

### streak-exercise.html — JS: Config section

Add:

```js
const ANGLE = params.get('angle') || 'all';
```

---

### streak-exercise.html — JS: loadQuestions() — pool filtering

After the difficulty filter block, add:

```js
// Apply angle filter
if (ANGLE !== 'all') {
  pool = pool.filter(q => q.angle === ANGLE);
  if (pool.length === 0) {
    document.getElementById('loading-text').textContent =
      'No questions found for that angle. Try a different setting.';
    return;
  }
}
```

---

### streak-exercise.html — JS: STORAGE_KEY

Update again to include angle:

```js
const STORAGE_KEY = 'streak_best_'
  + CFG_DOMAINS.slice().sort().join('_')
  + '_d' + DIFFICULTY
  + '_a' + ANGLE;
```

---

## SC-06 — Dynamic Question Counts via Manifest

**Problem:** Domain card counts in `streak-settings.html` are hardcoded and will silently drift as questions are added to `_basic.json` files.

**Solution:** Create `data/streak_manifest.json` with current counts. The settings page fetches it on load and updates `.domain-q-count` elements. Falls back silently to the hardcoded HTML values if the fetch fails.

---

### Create: `data/streak_manifest.json`

```json
{
  "generated": "2026-03-05",
  "domains": {
    "BPSY": 1030,
    "CASS": 480,
    "CPAT": 1050,
    "LDEV": 610,
    "PETH": 980,
    "PMET": 965,
    "PTHE": 725,
    "SOCU": 730,
    "WDEV": 875
  }
}
```

**Maintenance note:** Regenerate this file whenever `_basic.json` files are updated. A one-liner to regenerate:
```bash
python3 -c "
import json, os
data_dir = 'data'
counts = {}
for f in os.listdir(data_dir):
    if f.endswith('_basic.json'):
        code = f.replace('_basic.json', '')
        qs = json.load(open(os.path.join(data_dir, f), encoding='utf-8')).get('questions', [])
        counts[code] = len(qs)
manifest = {'generated': '$(date +%Y-%m-%d)', 'domains': counts}
json.dump(manifest, open('data/streak_manifest.json', 'w'), indent=2)
print('Updated:', counts)
"
```

---

### streak-settings.html — JS: On page load

Add after `updateSummary();` at the bottom of the script:

```js
// Dynamically update question counts from manifest
fetch('data/streak_manifest.json')
  .then(r => r.json())
  .then(manifest => {
    document.querySelectorAll('.domain-card').forEach(card => {
      const code = card.dataset.domain;
      const count = manifest.domains && manifest.domains[code];
      if (count !== undefined) {
        const el = card.querySelector('.domain-q-count');
        if (el) el.textContent = count.toLocaleString() + ' questions';
      }
    });
  })
  .catch(() => { /* Fail silently; hardcoded HTML values remain */ });
```

---

## Implementation Order

Execute changes in this sequence to keep both files in a testable state after each step:

1. **SC-06**: Create manifest file (no code changes, low risk)
2. **SC-02**: Fix isNewBest flag (exercise only, isolated change)
3. **SC-03**: Fix streak-best-inline logic (exercise only, isolated change)
4. **SC-01**: Add explanation panel (exercise — CSS + HTML + JS)
5. **SC-04**: Difficulty filter (settings + exercise — linked change, do both at once)
6. **SC-05**: Angle filter (settings + exercise — linked change, do both at once)
7. **SC-06 (settings side)**: Add manifest fetch to settings page

---

## Validation Checklist

After all changes:
- [ ] Explanation appears after correct answer and shows explanation text
- [ ] Explanation appears after wrong answer and shows explanation text
- [ ] Explanation disappears when Next Question is clicked
- [ ] "New Personal Best!" badge appears only when a new best is set, not on ties
- [ ] streak-best-inline shows "Session best" after a reset, "Personal best" when below all-time, blank at/above all-time best
- [ ] Difficulty "Easy" filters to only difficulty_level === 1 questions
- [ ] Difficulty "Medium" filters to only difficulty_level === 2 questions
- [ ] Difficulty "Hard" filters to only difficulty_level === 3 questions
- [ ] Difficulty "All" applies no filter
- [ ] Angle "Recall" filters to only direct_recall questions
- [ ] Angle "Scenarios" filters to only clinical_scenario questions
- [ ] Other angles filter correctly
- [ ] Empty pool after filter shows informative error message, not silent hang
- [ ] Summary bar updates live for all new settings
- [ ] Settings URL params pass all 6 variables to exercise correctly
- [ ] localStorage keys include difficulty and angle to prevent cross-contamination of bests
- [ ] Manifest fetch updates hardcoded counts silently; page still works if fetch fails
- [ ] All existing functionality (lives, life extension, game over screen, restart) works unchanged
