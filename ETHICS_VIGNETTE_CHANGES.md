# Ethics Vignette Module — Change Plan (v2)

**Created:** 2026-03-05
**Supersedes:** previous ETHICS_VIGNETTE_CHANGES.md

**Files in scope:**
- `ethics-settings.html`
- `ethics-exercise.html`
- `data/PETH_vignettes.json`

---

## TASK LIST

| # | Task | File(s) | Priority | Status |
|---|---|---|---|---|
| 1 | Fix "Weakest First" — subdomain score tracking in recordAnswer | exercise | P0 | done |
| 2 | Fix "Weakest First" — sort pool by subdomain weakness | exercise | P0 | done |
| 3 | Fix sessionCorrect/sessionTotal accumulation bug | exercise | P0 | done |
| 4 | Add subdomain field to sessionAnswers entries | exercise | P0 | done |
| 5 | Pre-select L1 difficulty by default | settings | P1 | done |
| 6 | Keyboard shortcuts (A/B/C/D to answer, Enter/Space to advance) | exercise | P1 | done |
| 7 | Session Review Screen (post-results question walkthrough) | exercise | P1 | done |
| 8 | Fix domain_name mislabeling in PETH_vignettes.json | JSON | P2 | done |
| 9 | Audit and fix L1 hint words that name APA standard numbers | JSON | P2 | done |
| 10 | Flag source question 124 for content review | JSON | P2 | done |
| 11 | Per-subdomain results breakdown | exercise | P3 | done |
| 12 | Add subdomain filter section to settings | settings + exercise | P3 | done |
| 13 | Persist last-used settings to localStorage | settings | P3 | done |
| 14 | Fix loading progress bar (renders but never fills) | exercise | P4 | done |
| 15 | Timer pause on window blur (Page Visibility API) | exercise | P4 | done |
| 16 | L5 annotation indicator ("no hint words" note) | exercise | P4 | done |
| 17 | Update "Weakest First" sublabel copy | settings | P4 | done |

---

## IMPLEMENTATION ORDER

Dependencies determine order. Execute strictly in this sequence:

```
Phase 1 — Data (no code deps):
  Task 8  → fix domain_name in JSON
  Task 9  → fix L1 hint words in JSON
  Task 10 → flag question 124 in JSON

Phase 2 — Exercise page core bugs:
  Task 4  → add subdomain to sessionAnswers  (prereq for Tasks 1, 3, 7, 11)
  Task 3  → fix sessionCorrect accumulation  (prereq for Task 11)
  Task 1  → subdomain score tracking         (prereq for Task 2)
  Task 2  → fix Weakest First sort

Phase 3 — Settings page core:
  Task 5  → pre-select L1 default
  Task 17 → update Weakest First copy

Phase 4 — Study features:
  Task 11 → per-subdomain results breakdown  (depends on Tasks 3+4)
  Task 7  → Session Review Screen            (depends on Task 4)
  Task 6  → keyboard shortcuts

Phase 5 — Persistence + filter:
  Task 13 → persist settings
  Task 12 → subdomain filter                 (depends on Task 13)

Phase 6 — Polish:
  Task 14 → loading progress bar
  Task 15 → timer pause on blur
  Task 16 → L5 annotation indicator
```

---

## TASK 1 — Fix "Weakest First": subdomain score tracking

**File:** `ethics-exercise.html`
**Problem:** `recordAnswer()` only tracks PETH domain-level scores. "Weakest First" needs
subdomain-level accuracy data to know what to surface first.

**Current `recordAnswer` function (~line 367):**
```javascript
function recordAnswer(isCorrect){
  const code='PETH';
  if(!domainScores[code]) domainScores[code]={correct:0,total:0,sessionCorrect:0,sessionTotal:0};
  domainScores[code].total++; domainScores[code].sessionTotal=(domainScores[code].sessionTotal||0)+1;
  if(isCorrect){domainScores[code].correct++;domainScores[code].sessionCorrect=(domainScores[code].sessionCorrect||0)+1;}
  sessionAnswers.push({id:questions[current].id,correct:isCorrect,domain:code});
}
```

NOTE: Task 4 (add subdomain to sessionAnswers) and Task 3 (fix sessionCorrect) are folded into
this replacement. Apply all three changes at once in this single edit.

**Replace with (handles Tasks 1, 3, and 4 together):**
```javascript
function recordAnswer(isCorrect){
  const code = 'PETH';
  const sub  = questions[current].subdomain || 'Unknown';

  // cumulative all-time tracking (unchanged semantics)
  if(!domainScores[code]) domainScores[code]={correct:0,total:0};
  domainScores[code].total++;
  if(isCorrect) domainScores[code].correct++;

  // subdomain-level cumulative tracking (new — powers Weakest First)
  if(!domainScores._subdomains) domainScores._subdomains={};
  if(!domainScores._subdomains[sub]) domainScores._subdomains[sub]={correct:0,total:0};
  domainScores._subdomains[sub].total++;
  if(isCorrect) domainScores._subdomains[sub].correct++;

  // sessionAnswers: always fresh per page-load, now includes subdomain field
  sessionAnswers.push({id:questions[current].id, correct:isCorrect, domain:code, subdomain:sub});
}
```

**Key changes:**
- Removed `sessionCorrect`/`sessionTotal` from the stored object entirely — session stats are
  now computed live from the `sessionAnswers` array, which is always fresh (not loaded from storage).
- Added `_subdomains` tracking object under the module's score entry.
- Added `subdomain` field to each `sessionAnswers` entry.

**Also update the score-seeding block in `loadQuestions()` (~line 299):**

Current:
```javascript
domainScores['PETH'] = (getStoredScores()[MODULE]||{})['PETH'] || {correct:0,total:0,sessionCorrect:0,sessionTotal:0};
```

Replace with:
```javascript
const storedModule = getStoredScores()[MODULE] || {};
domainScores['PETH']      = storedModule['PETH']      || {correct:0, total:0};
domainScores._subdomains  = storedModule._subdomains  || {};
```

`saveScores()` requires no change — it already saves the entire `domainScores` object.

---

## TASK 2 — Fix "Weakest First": sort pool by subdomain weakness

**File:** `ethics-exercise.html`
**Depends on:** Task 1 (domainScores._subdomains must be seeded first)
**Problem:** The `weakest` branch in `loadQuestions()` calls `shuffle(pool)` — identical to the
default. Stored scores are loaded but never consulted.

**Current code (~line 300):**
```javascript
if(CFG.order==='weakest') shuffle(pool);
else if(CFG.order==='sequential') pool.sort((a,b)=>(a.subdomain||'').localeCompare(b.subdomain||''));
else shuffle(pool);
```

**Replace with:**
```javascript
if(CFG.order === 'weakest'){
  const subs = domainScores._subdomains || {};
  const subPct = (subName) => {
    const s = subs[subName];
    if(!s || s.total === 0) return -1; // unplayed subdomains come first (most valuable)
    return s.correct / s.total;
  };
  pool.sort((a, b) => {
    const diff = subPct(a.subdomain) - subPct(b.subdomain);
    if(diff !== 0) return diff; // lower accuracy first
    return Math.random() - 0.5; // shuffle within same subdomain bucket
  });
} else if(CFG.order === 'sequential'){
  pool.sort((a,b) => (a.subdomain||'').localeCompare(b.subdomain||''));
} else {
  shuffle(pool);
}
```

**How it works:**
- Subdomains with no history get pct = -1, so they sort to the front (you haven't tried them).
- Among scored subdomains, lower accuracy = lower pct = earlier in queue.
- Questions within the same subdomain are randomly ordered.

**Verification after implementation:**
1. Play a session, deliberately miss several questions from "APA Ethics Code Standards 9 & 10".
2. Start a new session with "Weakest First".
3. Confirm that Standards 9 & 10 questions appear prominently at the start.

---

## TASK 3 — Fix sessionCorrect/sessionTotal accumulation bug

**Covered by Task 1.** This task is explicitly called out here because it is a data integrity
bug independent of the Weakest First feature.

**The bug:** `recordAnswer()` loads the stored `domainScores['PETH']` object (which includes
`sessionCorrect` and `sessionTotal` from all previous sessions ever played) and then increments
them. The results screen reads these accumulated fields to render the domain bar score, so the
bar displays lifetime stats mislabeled as this session's performance.

**Example:** You've played 4 sessions historically (100 questions, 70 correct). You play today's
session of 10 questions and get 9 correct. The bar shows "79/110" instead of "9/10".

**The score ring above it is NOT affected** — it reads from `sessionAnswers.length` and
`sessionAnswers.filter(a=>a.correct).length`, which are always fresh.

**Fix:** Already applied in Task 1's replacement code — `sessionCorrect`/`sessionTotal` are
removed from the stored object. Session stats are always derived from the in-memory `sessionAnswers`
array in `showResults()`. See Task 11 for the results bar rendering that uses this correctly.

---

## TASK 4 — Add subdomain field to sessionAnswers entries

**Covered by Task 1.** Called out separately because it is a prerequisite for Tasks 7 and 11.

The `sessionAnswers.push(...)` call in `recordAnswer()` gains a `subdomain` field in Task 1's
replacement. No additional change needed here — just confirming the dependency.

---

## TASK 5 — Pre-select L1 difficulty by default

**File:** `ethics-settings.html`
**Problem:** Page loads with zero difficulty levels selected. Clicking "Begin Session" immediately
triggers validation error. At minimum, L1 should be on by default.

**Change 1 — HTML (~line 374):** Add `selected` class to L1 card:
```html
<!-- BEFORE -->
<div class="level-card" data-level="1" onclick="toggleLevel(this)">

<!-- AFTER -->
<div class="level-card selected" data-level="1" onclick="toggleLevel(this)">
```

**Change 2 — JS state (~line 570):**
```javascript
// BEFORE
const state = {
  levels: new Set(),
  ...
};

// AFTER
const state = {
  levels: new Set(['1']),
  ...
};
```

No other changes needed — `updateSummary()` at the bottom of the script renders the initial
state correctly.

Note: Task 13 (persistence) will load saved settings on top of these defaults. If the user had
previously saved preferences with no levels selected (shouldn't happen after validation is in
place), the defaults handle it gracefully.

---

## TASK 6 — Keyboard shortcuts

**File:** `ethics-exercise.html`
**Problem:** No keyboard navigation. On timed sessions especially, requiring mouse clicks to
select answers and advance is significant friction. EPPP candidates benefit from drill speed.

**Supported keys:**
- `A` / `B` / `C` / `D` — select the corresponding answer option
- `Enter`, `Space`, or `ArrowRight` — advance to next question (only after answering)
- `1` / `2` / `3` / `4` — alternative answer selection (in case options render in non-ABCD order)

**Implementation:** Add a keydown event listener in the script block, after the existing
functions. Place it just before the `loadQuestions()` call at the bottom.

```javascript
document.addEventListener('keydown', (e) => {
  // Don't intercept if user is typing in an input
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

  // Answer selection — only when quiz screen is active and not yet answered
  if(document.getElementById('screen-quiz').classList.contains('active') && !answered){
    const keyMap = { 'a':'A', 'b':'B', 'c':'C', 'd':'D', '1':'A', '2':'B', '3':'C', '4':'D' };
    const letter = keyMap[e.key.toLowerCase()];
    if(letter){
      // find the option button with this letter and click it if it exists
      const btn = document.querySelector(`.option-btn[data-letter="${letter}"]`);
      if(btn){ e.preventDefault(); btn.click(); }
    }
  }

  // Advance — only when next-btn is visible
  if(['Enter','ArrowRight',' '].includes(e.key)){
    const nextBtn = document.getElementById('next-btn');
    if(nextBtn && nextBtn.classList.contains('visible')){
      e.preventDefault();
      nextBtn.click();
    }
  }
});
```

**UX consideration:** The `Space` key is included for advancing but must be caught with
`e.preventDefault()` to avoid scrolling the page. This is safe because the Space bar has no
other meaningful role in this UI.

**On the results screen:** No keyboard shortcuts needed there — there are only two buttons and
no time pressure.

**Verification:**
1. Load a session. Press 'B'. Confirm option B is selected.
2. Press Enter. Confirm advance to next question.
3. On last question, press Enter after answering. Confirm results screen appears.
4. On a timed session (45s), confirm keypresses stop the timer correctly.

---

## TASK 7 — Session Review Screen

**File:** `ethics-exercise.html`
**Problem:** After results, there is no way to review which questions you got wrong, what the
correct answers were, or why. This is the biggest missing study-value feature. All necessary
data exists in `sessionAnswers` and `questions`.

**Design:** Add a fourth screen (`#screen-review`) that appears when the user clicks a
"Review Session" button on the results screen. It shows every question in session order with:
- The vignette (collapsed by default, expandable)
- Your answer vs. the correct answer
- The correct answer's explanation
- A pass/fail indicator

**Step 1 — Add screen HTML** (insert after `#screen-results` closing `</div>`, before `</body>`):

```html
<div id="screen-review" class="screen">
  <div class="review-inner" id="review-inner"></div>
</div>
```

**Step 2 — Add CSS** to the `<style>` block:

```css
#screen-review.active {
  display: block;
  padding: 32px 24px 80px;
}
.review-inner {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeInUp .4s ease-out both;
}
.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.review-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 1.6rem;
}
.review-title em { font-style: italic; color: var(--accent-light); }
.review-back {
  font-size: 13px; font-weight: 500; color: var(--text3);
  background: none; border: none; cursor: pointer;
  transition: color .2s;
}
.review-back:hover { color: var(--accent); }

.review-card {
  background: rgba(255,255,255,.025);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}
.review-card.card-correct { border-color: rgba(52,211,153,.3); }
.review-card.card-wrong   { border-color: rgba(248,113,113,.25); }

.review-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
}
.review-q-num {
  font-size: 11px; font-weight: 700; color: var(--text3);
  width: 28px; flex-shrink: 0;
}
.review-q-snippet {
  flex: 1;
  font-size: 13px; color: var(--text2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.review-result {
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.card-correct .review-result { color: var(--green); }
.card-wrong   .review-result { color: var(--red); }
.review-chevron {
  font-size: 12px; color: var(--text3); flex-shrink: 0;
  transition: transform .2s;
}
.review-card.expanded .review-chevron { transform: rotate(90deg); }

.review-card-body {
  display: none;
  padding: 0 18px 18px;
  border-top: 1px solid var(--border);
}
.review-card.expanded .review-card-body { display: block; }

.review-vignette {
  font-size: 13px; color: var(--text3); line-height: 1.7;
  padding: 14px 0 12px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}
.review-answers { display: flex; flex-direction: column; gap: 8px; }
.review-answer-row {
  display: flex; align-items: flex-start; gap: 10px;
  font-size: 13px; line-height: 1.5;
}
.review-answer-label {
  font-size: 10px; font-weight: 700; letter-spacing: .06em;
  padding: 2px 7px; border-radius: 4px; flex-shrink: 0; margin-top: 1px;
}
.label-your-correct { background: rgba(52,211,153,.15); color: var(--green); }
.label-your-wrong   { background: rgba(248,113,113,.15); color: var(--red); }
.label-correct      { background: rgba(52,211,153,.08); color: var(--green); border: 1px solid rgba(52,211,153,.2); }
.review-explanation {
  font-size: 12px; color: var(--text3); line-height: 1.55;
  margin-top: 4px; padding: 8px 10px;
  background: rgba(255,255,255,.02); border-radius: 7px;
  border-left: 2px solid rgba(52,211,153,.3);
}
```

**Step 3 — Add "Review Session" button to results screen actions:**

Find the `results-actions` div (around line 260 in HTML):
```html
<div class="results-actions">
  <button class="btn-primary" onclick="location.href='ethics-settings.html'">New Session</button>
  <button class="btn-secondary" onclick="location.href=location.href">Try Again</button>
</div>
```

Replace with:
```html
<div class="results-actions">
  <button class="btn-primary" onclick="location.href='ethics-settings.html'">New Session</button>
  <button class="btn-secondary" id="review-btn" onclick="showReview()">Review Session</button>
  <button class="btn-secondary" onclick="location.href=location.href">Try Again</button>
</div>
```

**Step 4 — Add `showReview()` function** in the script block:

```javascript
function showReview(){
  document.getElementById('screen-results').classList.remove('active');
  document.getElementById('screen-review').classList.add('active');

  const container = document.getElementById('review-inner');
  container.innerHTML = '';

  // Header
  const header = document.createElement('div');
  header.className = 'review-header';
  header.innerHTML = `
    <h2 class="review-title">Session <em>Review</em></h2>
    <button class="review-back" onclick="showResultsFromReview()">← Back to Results</button>
  `;
  container.appendChild(header);

  // One card per question
  sessionAnswers.forEach((ans, i) => {
    const q = questions[i];
    if(!q) return;

    const isCorrect = ans.correct;
    const card = document.createElement('div');
    card.className = `review-card ${isCorrect ? 'card-correct' : 'card-wrong'}`;

    // Collapsed header — shows question snippet
    const snippet = q.question.length > 80 ? q.question.slice(0, 80) + '…' : q.question;
    card.innerHTML = `
      <div class="review-card-header" onclick="toggleReviewCard(this.parentElement)">
        <span class="review-q-num">Q${i+1}</span>
        <span class="review-q-snippet">${escapeHtml(snippet)}</span>
        <span class="review-result">${isCorrect ? '✓ Correct' : '✗ Wrong'}</span>
        <span class="review-chevron">›</span>
      </div>
      <div class="review-card-body">
        <div class="review-vignette">${escapeHtml(q.vignette)}</div>
        <div class="review-answers">
          ${buildReviewAnswers(q, ans)}
        </div>
      </div>
    `;

    container.appendChild(card);
  });

  // Auto-expand all wrong answers for immediate review
  document.querySelectorAll('.review-card.card-wrong').forEach(c => c.classList.add('expanded'));
}

function buildReviewAnswers(q, ans){
  // Show: your answer (if wrong) + correct answer with explanation
  let html = '';
  const yourLetter = ans.yourLetter; // see note below
  const correctLetter = q.correct_answer;

  if(yourLetter && yourLetter !== correctLetter){
    html += `
      <div class="review-answer-row">
        <span class="review-answer-label label-your-wrong">Your answer (${yourLetter})</span>
        <span>${escapeHtml(q.options[yourLetter] || '')}</span>
      </div>`;
  }
  html += `
    <div class="review-answer-row">
      <span class="review-answer-label label-correct">Correct (${correctLetter})</span>
      <div>
        <div>${escapeHtml(q.options[correctLetter] || '')}</div>
        <div class="review-explanation">${escapeHtml((q.option_explanations||{})[correctLetter]||'')}</div>
      </div>
    </div>`;
  return html;
}

function toggleReviewCard(card){
  card.classList.toggle('expanded');
}

function showResultsFromReview(){
  document.getElementById('screen-review').classList.remove('active');
  document.getElementById('screen-results').classList.add('active');
}
```

**Step 5 — Store selected answer letter in sessionAnswers.**

The current `recordAnswer()` call does not store which letter the user selected — only whether
they were correct. Update `selectAnswer()` to pass the chosen letter:

In `selectAnswer()` (~line 356), change the `recordAnswer` call:
```javascript
// BEFORE
recordAnswer(isCorrect);

// AFTER
recordAnswer(isCorrect, letter);
```

In the updated `recordAnswer()` function from Task 1, add `yourLetter` parameter:
```javascript
function recordAnswer(isCorrect, yourLetter){
  ...
  sessionAnswers.push({
    id: questions[current].id,
    correct: isCorrect,
    domain: code,
    subdomain: sub,
    yourLetter: yourLetter || null,  // null on timeout (no letter chosen)
  });
}
```

In `timeoutQuestion()`, the call is `recordAnswer(false)` with no letter — this is correct,
`yourLetter` defaults to `null` and the review shows only the correct answer for timed-out
questions.

**Behavior:**
- Wrong answer cards auto-expand on review load (the most useful state — you want to see
  your misses immediately).
- Correct answer cards are collapsed by default (click to expand if curious).
- All vignettes are shown collapsed inside each card — click header to expand.

---

## TASK 8 — Fix mislabeled domain_name in PETH_vignettes.json

**File:** `data/PETH_vignettes.json`
**Problem:** Every question and the top-level metadata object has
`"domain_name": "Psychopharmacology & Ethics"`. PETH is the professional ethics domain.
Psychopharmacology is a separate EPPP content area. The `legacy_domain_name` field correctly
reads `"Ethics, Legal, and Professional Issues"`.

**Fix:** Run this Python script from the `mastery-page/` directory:

```python
with open('data/PETH_vignettes.json', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('"Psychopharmacology & Ethics"', '"Professional Ethics"')
with open('data/PETH_vignettes.json', 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Replaced {content.count("Professional Ethics")} occurrences.')
```

**Verify:** Spot-check lines 3 (top-level metadata), and 5 representative questions spread
across the file. All should read `"domain_name": "Professional Ethics"`.

---

## TASK 9 — Audit and fix L1 hint words naming APA standard numbers

**File:** `data/PETH_vignettes.json`
**Problem:** Some L1 `hint_words` arrays include strings like `"Standard 6.02"` or standalone
`"APA Ethics Code"`. These name the answer rather than building clinical language recognition —
the whole point of hint words.

**Audit:** Search for `"Standard ` (with trailing space) inside hint_words arrays. Also search
for `"APA Ethics Code"` as a standalone entry.

**Known instance — source question 124, L1 (~line 1421):**

Current:
```json
"hint_words": ["de-identification", "APA Ethics Code", "Standard 6.02"]
```

Replace with:
```json
"hint_words": ["de-identification", "confidential records", "fax"]
```

**Rule for all replacements:**
- Remove any hint word that is a standard number (e.g., "Standard 6.02")
- Remove `"APA Ethics Code"` as a standalone hint (applies to every question, signals nothing)
- Replace removed entries with clinical terminology, job-role language, or action verbs from
  the vignette scenario itself that signal the ethical issue without naming the standard

**After L1 audit, do an L2 pass** for the same pattern.

---

## TASK 10 — Flag source question 124 for content review

**File:** `data/PETH_vignettes.json`
**Problem:** Question 124 asserts that records faxed to a treating therapist must be
de-identified per Standard 6.02. In practice, de-identifying records before sending to a
treating clinician renders them useless — the therapist can't match anonymous data to their
patient. Standard 6.02 de-identification requirements govern research/teaching dissemination,
not provider-to-provider clinical exchange. This may be EPPP-specific framing, but it needs
verification against actual APA Ethics Code text.

**Fix:** Add a `"review_flag"` field to all 5 levels of source question 124
(IDs: JQ-ETH-124-vignette-L1 through L5). Insert after `"legacy_domain_name"` in each:

```json
"review_flag": "Content accuracy: verify Standard 6.02 requires de-identification before faxing records to a treating provider. May reflect EPPP-specific item framing rather than clinical standard."
```

The `review_flag` field is not read by the exercise page and has no runtime effect.

**Resolution options (pending human review):**
- If Standard 6.02 supports the answer: remove flag, optionally annotate `source_summary`
- If incorrect: revise vignette, options, correct_answer, and all 5 sets of explanations

---

## TASK 11 — Per-subdomain results breakdown

**File:** `ethics-exercise.html`
**Depends on:** Tasks 1+4 (subdomain field must exist in sessionAnswers)
**Problem:** Results screen shows one bar labeled "PETH" with accumulated lifetime stats
(itself a bug, fixed by removing sessionCorrect — see Task 3). Should show one bar per
subdomain that appeared in the session, computed from the fresh `sessionAnswers` array.

**Add short-label map near the top of the script block:**
```javascript
const SUBDOMAIN_SHORT = {
  'APA Ethics Code Overview and Standards 1 & 2': 'Stds 1–2',
  'APA Ethics Code Standards 3 & 4':              'Stds 3–4',
  'APA Ethics Code Standards 5 & 6':              'Stds 5–6',
  'APA Ethics Code Standards 7 & 8':              'Stds 7–8',
  'APA Ethics Code Standards 9 & 10':             'Stds 9–10',
  'Professional Issues':                          'Prof. Issues',
};
```

**Replace the domain-rows block in `showResults()` (~line 398):**

Current:
```javascript
const s=domainScores['PETH']||{sessionCorrect:0,sessionTotal:0};
const sc=s.sessionCorrect||0,st=s.sessionTotal||0,dp=st?Math.round(sc/st*100):0,cls=dp>=75?'high':dp>=50?'mid':'low';
document.getElementById('domain-rows').innerHTML=`<div class="db-row">...</div>`;
setTimeout(()=>{ document.querySelectorAll('.db-fill').forEach(el=>el.style.width=el.dataset.pct+'%'); },200);
```

Replace with:
```javascript
const subRows = document.getElementById('domain-rows');
subRows.innerHTML = '';

// Collect unique subdomains that appeared this session, in logical order
const SUBDOMAIN_ORDER = [
  'APA Ethics Code Overview and Standards 1 & 2',
  'APA Ethics Code Standards 3 & 4',
  'APA Ethics Code Standards 5 & 6',
  'APA Ethics Code Standards 7 & 8',
  'APA Ethics Code Standards 9 & 10',
  'Professional Issues',
];
const sessionSubs = SUBDOMAIN_ORDER.filter(s =>
  sessionAnswers.some(a => a.subdomain === s)
);

if(sessionSubs.length === 0){
  // Fallback: single aggregate bar (shouldn't happen with well-formed data)
  const total = sessionAnswers.length, correct = sessionAnswers.filter(a=>a.correct).length;
  const dp = total ? Math.round(correct/total*100) : 0;
  subRows.innerHTML = `<div class="db-row"><span class="db-domain">PETH</span><div class="db-track"><div class="db-fill ${dp>=75?'high':dp>=50?'mid':'low'}" style="width:0%" data-pct="${dp}"></div></div><span class="db-score">${correct}/${total}</span></div>`;
} else {
  sessionSubs.forEach(sub => {
    const subAnswers = sessionAnswers.filter(a => a.subdomain === sub);
    const st = subAnswers.length;
    const sc = subAnswers.filter(a => a.correct).length;
    const dp = st ? Math.round(sc/st*100) : 0;
    const cls = dp>=75?'high':dp>=50?'mid':'low';
    const label = SUBDOMAIN_SHORT[sub] || sub;
    subRows.innerHTML += `<div class="db-row"><span class="db-domain" style="width:76px;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${sub}">${label}</span><div class="db-track"><div class="db-fill ${cls}" style="width:0%" data-pct="${dp}"></div></div><span class="db-score">${sc}/${st}</span></div>`;
  });
}
setTimeout(()=>{ document.querySelectorAll('.db-fill').forEach(el=>el.style.width=el.dataset.pct+'%'); },200);
```

---

## TASK 12 — Add subdomain filter section to settings

**File:** `ethics-settings.html` (settings) + `ethics-exercise.html` (exercise reader)
**Depends on:** Task 13 (persistence) — implement Task 13 first, then extend it here
**Problem:** Users cannot target specific APA Standard areas for practice. All 6 subdomains
are always included. For EPPP prep, targeted subdomain drilling is high value.

**Subdomain list and short labels (add as constants at top of script block in settings):**
```javascript
const SUBDOMAINS = [
  'APA Ethics Code Overview and Standards 1 & 2',
  'APA Ethics Code Standards 3 & 4',
  'APA Ethics Code Standards 5 & 6',
  'APA Ethics Code Standards 7 & 8',
  'APA Ethics Code Standards 9 & 10',
  'Professional Issues',
];
const SUBDOMAIN_SHORT = {
  'APA Ethics Code Overview and Standards 1 & 2': 'Stds 1 & 2',
  'APA Ethics Code Standards 3 & 4':              'Stds 3 & 4',
  'APA Ethics Code Standards 5 & 6':              'Stds 5 & 6',
  'APA Ethics Code Standards 7 & 8':              'Stds 7 & 8',
  'APA Ethics Code Standards 9 & 10':             'Stds 9 & 10',
  'Professional Issues':                          'Prof. Issues',
};
```

**Add `subdomains` to state:**
```javascript
const state = {
  levels:     new Set(['1']),
  count:      10,
  order:      'shuffled',
  timer:      'off',
  annotations: false,
  subdomains: new Set(SUBDOMAINS), // all selected by default
};
```

**CSS — add to style block:**
```css
.subdomain-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.sub-chip {
  padding: 7px 14px;
  background: rgba(255,255,255,0.025); border: 1px solid var(--border);
  border-radius: 20px; font-size: 12px; font-weight: 500; color: var(--text3);
  cursor: pointer; user-select: none;
  transition: border-color 0.2s, background 0.2s, color 0.2s;
}
.sub-chip:hover { background: rgba(255,255,255,0.05); }
.sub-chip.selected {
  border-color: var(--gold);
  background: rgba(212,160,84,0.08);
  color: var(--gold-light);
}
.select-all-btn {
  font-size: 11px; font-weight: 500; color: var(--text3);
  background: none; border: none; cursor: pointer; padding: 0;
  transition: color 0.2s;
}
.select-all-btn:hover { color: var(--gold); }
```

**HTML — insert new section between Question Order (section 3) and Rapid Fire (section 4):**
```html
<!-- ── 3b. SUBDOMAIN FILTER ── -->
<div class="settings-section">
  <div class="section-header">
    <div class="section-label">Focus Area</div>
    <button class="select-all-btn" id="sub-select-all" onclick="toggleAllSubdomains()">Deselect All</button>
  </div>
  <div class="subdomain-chips" id="subdomain-chips"></div>
  <p class="warn" id="subdomain-warn">Select at least one focus area to continue.</p>
</div>
```

**JS functions:**
```javascript
function initSubdomainChips(){
  const container = document.getElementById('subdomain-chips');
  SUBDOMAINS.forEach(sub => {
    const chip = document.createElement('div');
    chip.className = 'sub-chip selected';
    chip.dataset.sub = sub;
    chip.textContent = SUBDOMAIN_SHORT[sub];
    chip.onclick = () => toggleSubdomain(chip, sub);
    container.appendChild(chip);
  });
}

function toggleSubdomain(chip, sub){
  if(state.subdomains.has(sub)){
    state.subdomains.delete(sub);
    chip.classList.remove('selected');
  } else {
    state.subdomains.add(sub);
    chip.classList.add('selected');
  }
  syncSelectAllBtn();
  updateSummary();
}

function toggleAllSubdomains(){
  const allSelected = state.subdomains.size === SUBDOMAINS.length;
  if(allSelected){
    state.subdomains.clear();
    document.querySelectorAll('.sub-chip').forEach(c => c.classList.remove('selected'));
  } else {
    SUBDOMAINS.forEach(s => state.subdomains.add(s));
    document.querySelectorAll('.sub-chip').forEach(c => c.classList.add('selected'));
  }
  syncSelectAllBtn();
  updateSummary();
}

function syncSelectAllBtn(){
  const allSelected = state.subdomains.size === SUBDOMAINS.length;
  document.getElementById('sub-select-all').textContent = allSelected ? 'Deselect All' : 'Select All';
}
```

**Validation — add to `startSession()`:**
```javascript
document.getElementById('subdomain-warn').style.display = 'none';
if(state.subdomains.size === 0){
  document.getElementById('subdomain-warn').style.display = 'block';
  valid = false;
}
```

**URL param — add to `startSession()` params:**
```javascript
const params = new URLSearchParams({
  levels:     [...state.levels].sort().join(','),
  count:      state.count,
  order:      state.order,
  timer:      state.timer,
  hints:      state.annotations ? '1' : '0',
  subdomains: [...state.subdomains].join('|'),
});
```

**Exercise page — read param and filter pool in `loadQuestions()`.**

Add to CFG parsing (~line 273):
```javascript
const subParam = sp.get('subdomains');
const CFG = {
  levels:     (sp.get('levels') || '1,2,3,4,5').split(',').map(Number),
  count:      parseInt(sp.get('count')) || 10,
  order:      sp.get('order') || 'shuffled',
  timer:      sp.get('timer') || 'off',
  hints:      sp.get('hints') === '1',
  subdomains: subParam ? subParam.split('|') : null, // null = all
};
```

In `loadQuestions()`, after the difficulty filter line:
```javascript
let pool = r.questions.filter(q => CFG.levels.includes(q.difficulty_level));
if(CFG.subdomains) pool = pool.filter(q => CFG.subdomains.includes(q.subdomain));
```

**Summary bar — add Focus item** (insert before the Hints sep/item pair):
```html
<div class="summary-sep"></div>
<div class="summary-item">
  <span class="s-label">Focus</span>
  <span class="s-val" id="sum-subs">All</span>
</div>
```

**`updateSummary()` addition:**
```javascript
const subCount = state.subdomains.size;
document.getElementById('sum-subs').textContent =
  subCount === SUBDOMAINS.length ? 'All' : `${subCount} area${subCount !== 1 ? 's' : ''}`;
```

**Bottom of script init call order:**
```javascript
initSubdomainChips(); // render chips first
loadSavedSettings();  // restore saved state (may toggle chip classes)
updateSummary();
```

---

## TASK 13 — Persist last-used settings to localStorage

**File:** `ethics-settings.html`
**Storage key:** `'ethics_session_prefs'`
**Problem:** Every visit requires re-selecting difficulty levels, count, order, and timer.

**Add `loadSavedSettings()` function:**
```javascript
function loadSavedSettings(){
  let saved;
  try { saved = JSON.parse(localStorage.getItem('ethics_session_prefs') || 'null'); }
  catch { return; }
  if(!saved) return;

  // Levels
  if(Array.isArray(saved.levels) && saved.levels.length){
    document.querySelectorAll('.level-card').forEach(c => c.classList.remove('selected'));
    state.levels = new Set();
    saved.levels.forEach(l => {
      state.levels.add(String(l));
      document.querySelector(`[data-level="${l}"]`)?.classList.add('selected');
    });
  }

  // Count
  if(saved.count){
    state.count = saved.count;
    const preset = document.querySelector(`[data-count="${saved.count}"]`);
    document.querySelectorAll('.count-btn').forEach(b => b.classList.remove('selected'));
    if(preset) preset.classList.add('selected');
    else document.getElementById('custom-count').value = saved.count;
  }

  // Order
  if(saved.order){
    state.order = saved.order;
    document.querySelectorAll('[data-order]').forEach(o =>
      o.classList.toggle('selected', o.dataset.order === saved.order)
    );
  }

  // Timer
  if(saved.timer !== undefined){
    state.timer = String(saved.timer);
    document.querySelectorAll('.rapid-card').forEach(c =>
      c.classList.toggle('selected', c.dataset.timer === String(saved.timer))
    );
  }

  // Subdomains (populated by Task 12)
  if(Array.isArray(saved.subdomains)){
    state.subdomains = new Set(saved.subdomains);
    document.querySelectorAll('.sub-chip').forEach(c =>
      c.classList.toggle('selected', state.subdomains.has(c.dataset.sub))
    );
    syncSelectAllBtn();
  }
}
```

**Save in `startSession()` before redirect:**
```javascript
localStorage.setItem('ethics_session_prefs', JSON.stringify({
  levels:     [...state.levels],
  count:      state.count,
  order:      state.order,
  timer:      state.timer,
  subdomains: [...state.subdomains],
}));
```

**Call order at bottom of script (after Task 12's `initSubdomainChips`):**
```javascript
initSubdomainChips(); // must run before loadSavedSettings to have chips in DOM
loadSavedSettings();
updateSummary();
```

---

## TASK 14 — Fix loading progress bar

**File:** `ethics-exercise.html`
**Problem:** The `loading-progress-fill` div exists with a CSS width-transition but width is
never updated in JS. It permanently shows an empty bar.

**Fix:** Animate the bar with a CSS keyframe instead of trying to synchronize it with actual
load progress (which is a single fetch, making real progress impractical).

**In the `<style>` block, add:**
```css
@keyframes loadingPulse {
  0%   { width: 0%; }
  60%  { width: 85%; }
  100% { width: 92%; }
}
.loading-progress-fill.animating {
  animation: loadingPulse 1.2s ease-out forwards;
}
```

**In `loadQuestions()`, start the animation immediately:**
```javascript
async function loadQuestions(){
  document.getElementById('loading-progress-fill').classList.add('animating');
  const r = await fetch(`${DATA_BASE}PETH_vignettes.json`).then(r=>r.json());
  // ... rest unchanged
  // On success, snap to 100% before hiding
  const fill = document.getElementById('loading-progress-fill');
  fill.style.animation = 'none';
  fill.style.width = '100%';
  // small delay so user sees 100%, then switch screens
  await new Promise(r => setTimeout(r, 150));
  document.getElementById('screen-loading').classList.remove('active');
  document.getElementById('screen-quiz').classList.add('active');
  renderQuestion();
}
```

Note: Remove the existing screen-switch calls from inside `loadQuestions()` since this
replacement handles them at the end.

---

## TASK 15 — Timer pause on window blur

**File:** `ethics-exercise.html`
**Problem:** `setInterval` continues regardless of tab visibility. On a 45s timer, switching
tabs for 30s leaves only 15s when returning — unfair and counterproductive for studying.

**Implementation:** Use the Page Visibility API to pause/resume the timer.

Add in the script block, after the existing timer functions:
```javascript
document.addEventListener('visibilitychange', () => {
  if(!timerSec || answered) return;
  if(document.hidden){
    clearInterval(timerInterval);
  } else {
    // Resume only if there's time left and not yet answered
    if(timerLeft > 0 && !answered){
      timerInterval = setInterval(()=>{
        timerLeft--;
        updateTimerUI();
        if(timerLeft <= 0){ clearInterval(timerInterval); if(!answered) timeoutQuestion(); }
      }, 1000);
    }
  }
});
```

This fires whenever the user switches tabs or minimizes the window. The timer stops when the
page is hidden and resumes from wherever it was when the user returns.

---

## TASK 16 — L5 annotation indicator

**File:** `ethics-exercise.html`
**Problem:** When annotations are ON and an L5 question appears (which has `hint_words: []`),
nothing is highlighted. There is no indicator that this is by design. Learners may think the
feature is broken.

**Fix:** In `renderQuestion()`, after setting `vignette-text` innerHTML, add a conditional note:

Current (~line 321):
```javascript
document.getElementById('vignette-text').innerHTML = CFG.hints
  ? highlightHints(q.vignette, q.hint_words)
  : escapeHtml(q.vignette);
```

Replace with:
```javascript
document.getElementById('vignette-text').innerHTML = CFG.hints
  ? highlightHints(q.vignette, q.hint_words)
  : escapeHtml(q.vignette);

// Show or hide the "no hints" note
let noHintNote = document.getElementById('no-hint-note');
if(!noHintNote){
  noHintNote = document.createElement('div');
  noHintNote.id = 'no-hint-note';
  noHintNote.style.cssText = 'font-size:11px;color:var(--text3);margin-top:8px;font-style:italic;';
  document.getElementById('vignette-text').parentElement.appendChild(noHintNote);
}
const showNote = CFG.hints && (!q.hint_words || q.hint_words.length === 0);
noHintNote.textContent = showNote ? 'No hint words — L5 questions use pure behavioral language.' : '';
noHintNote.style.display = showNote ? 'block' : 'none';
```

---

## TASK 17 — Update "Weakest First" sublabel copy

**File:** `ethics-settings.html`
**Location:** `data-order="weakest"` toggle option (~line 471).

```html
<!-- BEFORE -->
<div class="toggle-sublabel">Prioritize your lowest-scoring domains</div>

<!-- AFTER -->
<div class="toggle-sublabel">Prioritize your lowest-scoring subdomains</div>
```

---

## TESTING CHECKLIST

### Bugs fixed
- [ ] "Weakest First" with no history surfaces unplayed subdomains first
- [ ] "Weakest First" with history surfaces lowest-accuracy subdomains first
- [ ] Results domain bar shows this session only (e.g. 8/10), not lifetime accumulation
- [ ] `sessionAnswers` entries have `subdomain` and `yourLetter` fields

### Settings
- [ ] Page loads with L1 pre-selected, no error on immediate "Begin Session"
- [ ] Saved settings restore on return visit (levels, count, order, timer, subdomains)
- [ ] All 6 subdomain chips render selected by default
- [ ] Deselecting all chips blocks session start with warning
- [ ] "Select All / Deselect All" toggles correctly
- [ ] Summary bar shows "All" when all subdomains selected, "N areas" otherwise
- [ ] "Weakest First" sublabel reads "subdomains" not "domains"

### Exercise
- [ ] Subdomain URL param filters questions correctly (single-subdomain sessions work)
- [ ] Keyboard: press A/B/C/D selects correct option
- [ ] Keyboard: Enter/Space advances to next question after answering
- [ ] Keyboard shortcuts do nothing before answering (Enter doesn't advance)
- [ ] Timer pauses when tab is hidden; resumes when tab regains focus
- [ ] Loading bar animates to ~90%, snaps to 100%, then quiz appears
- [ ] L5 questions with annotations ON show "No hint words" note
- [ ] L1-L4 questions with annotations ON show no "No hint words" note

### Review Screen
- [ ] "Review Session" button appears on results screen
- [ ] Wrong-answer cards auto-expand on review load
- [ ] Correct-answer cards start collapsed
- [ ] Your chosen answer displayed for wrong answers
- [ ] Correct answer + explanation shown for every card
- [ ] Vignette text shows inside expanded card
- [ ] "Back to Results" returns to results screen
- [ ] Timed-out questions show null yourLetter (no "your answer" row shown)

### Data (JSON)
- [ ] domain_name reads "Professional Ethics" throughout (spot-check 10 questions)
- [ ] No hint_words contain a standard number or standalone "APA Ethics Code"
- [ ] review_flag present on all 5 levels of source question 124

### Per-subdomain results
- [ ] One bar per subdomain that appeared in the session
- [ ] Bars colored correctly (green ≥75%, yellow ≥50%, red <50%)
- [ ] Short labels fit in the domain column without overflow
- [ ] Bars animate from 0% to correct width on results load
