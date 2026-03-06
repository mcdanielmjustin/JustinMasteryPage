# Patient Avatar Overhaul — 8-Avatar SVG System
## Complete Implementation Guide (Resume-Safe Across Sessions)

**Date authored:** 2026-03-05
**Module:** `mastery-page/clinical-presentation-exercise.html`
**Status:** Planning — not yet implemented

---

## 1. Project Scope

Replace the single hard-coded inline SVG patient avatar with a dynamic system that
selects one of **8 demographically distinct SVG avatars** based on the patient's age
and gender as parsed from `enc.encounter.patient.label`.

**The 8 avatar types:**
| Key | Description | Age Range |
|-----|-------------|-----------|
| `young_male` | Elementary-age boy | ~8–11 |
| `young_female` | Elementary-age girl | ~8–11 |
| `adolescent_male` | Teen boy | ~12–17 |
| `adolescent_female` | Teen girl | ~12–17 |
| `adult_male` | Adult man | ~18–64 |
| `adult_female` | Adult woman | ~18–64 |
| `elder_male` | Elderly man | ~65+ |
| `elder_female` | Elderly woman | ~65+ |

All 13 emotional animation states (idle, speaking, distressed, tearful, anxious,
agitated, guarded, flat_affect, hopeful, confused) work on **all 8 avatars** with
**zero CSS changes** — because all avatars share the same element IDs and coordinate
anchors.

---

## 2. Files to Create / Modify

### CREATE (new file):
```
mastery-page/avatar-svgs.js
```
Defines `window.__AVATAR_SVGS` — an object with 8 keys, each containing a full
SVG string for one avatar type.

### MODIFY (existing file):
```
mastery-page/clinical-presentation-exercise.html
```
Three targeted changes only:
1. **Line ~957–1200:** Replace the inline `<svg id="avatar-root">` block with a
   placeholder comment. The SVG is now injected dynamically via `loadAvatar()`.
2. **Near line ~956 `<div class="avatar-wrap">` block:** Add an empty `<div id="avatar-wrap">`.
3. **Near line ~2255 (MOUTH_PATHS area):** Add `detectAvatarType()` and `loadAvatar()` functions.
4. **Line 1710:** In `startEncounter(enc)`, add `loadAvatar(detectAvatarType(...))` call.
5. **In `<head>` or before `</body>`:** Add `<script src="avatar-svgs.js"></script>`.

---

## 3. What NOT to Touch

**Do NOT modify any of the following:**
- `setAvatarState()` function (line ~2269) — works unchanged on all 8 avatars
- `MOUTH_PATHS` object (line ~2255) — shared coordinates, valid for all 8 avatars
- Any phase logic, question engine, scoring, or results screen
- `startEncounter()` logic except adding 2 lines before line 1710
- Chart panel, speech bubble, behavioral tags, inline question panel
- CSS keyframe animations (all use same IDs — no changes needed)
- Any other module (spot, vignette, table, brain, etc.)

---

## 4. Current Avatar System — Exact Code Locations

```
File: mastery-page/clinical-presentation-exercise.html

Line 86–132:  CSS keyframe animations + avatar state classes (.state-idle, etc.)
Line 539–546: .avatar-wrap CSS (width:260px height:416px, position:absolute left:24px bottom:0)
Line 957–1201: <div class="avatar-wrap"> containing the inline <svg id="avatar-root">
              — THIS IS THE BLOCK BEING REPLACED
Line 1685:    function startEncounter(enc) { ... }
Line 1710:    setAvatarState(enc.encounter.patient.initial_avatar_state || 'idle');
              — INSERT loadAvatar() call HERE (2 lines before this)
Line 2255–2267: MOUTH_PATHS object (10 emotion → SVG path d values)
Line 2269–2293: function setAvatarState(emotion) { ... }
```

**CSS animation targets (unchanged — all 8 avatars must use these IDs):**
```
#avatar-root   — gets .state-* class
#avatar-body   — breathing animations (transform-origin: 100px 185px)
#avatar-head   — tilt animations (transform-origin: 100px 130px)
#avatar-face   — filter animations (flat_affect desaturate, hopeful brighten)
#avatar-jaw    — jawSpeak animation (transform-origin: 100px 126px)
#avatar-eyes   — gazeAvert, blinkSlow animations
#avatar-hand   — fidgetHand animation (transform-origin: 100px 214px)
#avatar-hair   — (no animation currently, but ID must exist)
#avatar-brow   — (no animation currently, but ID must exist)
#avatar-tear   — tearFall animation (opacity controlled)
#avatar-mouth  — .setAttribute('d', ...) in setAvatarState()
#avatar-nose   — (no animation, but conventional to include)
```

---

## 5. Architecture

### Coordinate System — CRITICAL

All 8 avatars use **identical SVG coordinate anchors** for animation-critical elements.
This is what makes the shared CSS work without any changes.

```
viewBox:                "0 0 200 320"   — same for all 8
Head ellipse center:    cx="100" cy="107"  — same for all 8
Jaw transform-origin:   100px 126px     — baked in CSS, same for all 8
Head transform-origin:  100px 130px     — baked in CSS, same for all 8
Body transform-origin:  100px 185px     — baked in CSS, same for all 8
Hand transform-origin:  100px 214px     — baked in CSS, same for all 8
Mouth baseline Y:       ~126            — MOUTH_PATHS coordinates fixed, same for all 8
```

What **varies** per avatar:
- Head ellipse rx/ry (size)
- Hair element paths and colors
- Body proportions (torso height, leg length, shoulder width)
- Skin tone gradient colors
- Clothing colors and style paths
- Eye dimensions and iris color
- Optional: wrinkle strokes (elder), thicker brows (adolescent male)
- Skin tone gradients (unique per avatar)
- Clothing color fills

### Loading Flow

```
page load
  → <script src="avatar-svgs.js"> defines window.__AVATAR_SVGS
  → avatar-wrap div is empty (no inline SVG)

loadEncounters() runs
  → for each encounter, startEncounter(enc) called
     → detectAvatarType(enc.encounter.patient.label)  ← NEW
     → loadAvatar(avatarType)                         ← NEW
       → injects SVG string from __AVATAR_SVGS[type] into #avatar-wrap
     → setAvatarState(enc.encounter.patient.initial_avatar_state || 'idle')
       → works exactly as before on the newly injected SVG elements
```

---

## 6. Demographic Detection Logic — `detectAvatarType(label)`

**Patient label examples from actual data:**
- `"Parent (Mother), Adult Female, 38"`
- `"Adolescent Male, 15"`
- `"Child, Male, 8"`
- `"Adult Male, 42"`
- `"Elderly Female, 74"`
- `"Older Adult Male, 68"`
- `"Parent (Father), Adult Male, 45"`

**Detection algorithm:**

```javascript
function detectAvatarType(patientLabel) {
  if (!patientLabel) return 'adult_male';
  const label = patientLabel.toLowerCase();

  // --- Gender detection ---
  // Explicit female keywords
  const isFemale = /\b(female|woman|women|girl|mother|daughter|she|her|mrs|ms|miss)\b/.test(label);
  const gender = isFemale ? 'female' : 'male';

  // --- Age extraction ---
  // Match a 1–3 digit number that looks like an age (not a year like 2023)
  const ageMatch = label.match(/\b([5-9]|[1-9]\d|1[01]\d)\b/);
  const age = ageMatch ? parseInt(ageMatch[1]) : null;

  // --- Age group from number ---
  let ageGroup;
  if (age !== null) {
    if      (age <= 11) ageGroup = 'young';
    else if (age <= 17) ageGroup = 'adolescent';
    else if (age <= 64) ageGroup = 'adult';
    else                ageGroup = 'elder';
  } else {
    // Fallback: keyword detection
    if      (/\b(child|kid|boy|girl|elementary|youth|young child)\b/.test(label)) ageGroup = 'young';
    else if (/\b(teen|adolescent|juvenile|high.?school|minor)\b/.test(label))     ageGroup = 'adolescent';
    else if (/\b(elder|elderly|old|senior|geriatric|older adult)\b/.test(label))  ageGroup = 'elder';
    else                                                                            ageGroup = 'adult';
  }

  return ageGroup + '_' + gender;
}
```

**Mapping table (examples):**
| Patient Label | Detected Type |
|---|---|
| "Parent (Mother), Adult Female, 38" | adult_female |
| "Adolescent Male, 15" | adolescent_male |
| "Child, Female, 9" | young_female |
| "Elderly Male, 74" | elder_male |
| "Adult Male, 42" | adult_male |
| "Older Adult Female, 68" | elder_female |
| "Teen Girl, 16" | adolescent_female |
| "Boy, 10" | young_male |

---

## 7. `loadAvatar()` Function — Exact Code

```javascript
function loadAvatar(avatarType) {
  const wrap = document.getElementById('avatar-wrap');
  if (!wrap || !window.__AVATAR_SVGS) return;
  const svgStr = window.__AVATAR_SVGS[avatarType] || window.__AVATAR_SVGS['adult_male'];
  wrap.innerHTML = svgStr;
  // Ensure new avatar-root starts in idle (setAvatarState will override momentarily)
  const root = wrap.querySelector('#avatar-root');
  if (root) root.setAttribute('class', 'state-idle');
}
```

**Where to add this function:** Place it immediately **before** the `function setAvatarState(emotion)` block at ~line 2269.

---

## 8. HTML Modifications — Exact Changes

### Change A: Remove inline SVG, leave empty div
**Find (lines 956–1201):**
```html
<!-- Avatar container — inline SVG patient -->
<div class="avatar-wrap" id="avatar-wrap">
  <svg id="avatar-root" class="state-idle"
       viewBox="0 0 200 320" xmlns="http://www.w3.org/2000/svg"
       style="width:100%;height:100%;overflow:visible">
    ... (entire SVG, ~240 lines) ...
  </svg>
</div>
```

**Replace with:**
```html
<!-- Avatar container — SVG injected dynamically by loadAvatar() -->
<div class="avatar-wrap" id="avatar-wrap">
  <!-- avatar SVG injected here by loadAvatar() -->
</div>
```

### Change B: Add script tag
**Find (near end of file, before `</body>`):**
```html
</body>
```
**Replace with:**
```html
<script src="avatar-svgs.js"></script>
</body>
```

### Change C: Call loadAvatar in startEncounter
**Find (line ~1709–1710):**
```javascript
    // Set initial avatar state
    setAvatarState(enc.encounter.patient.initial_avatar_state || 'idle');
```
**Replace with:**
```javascript
    // Set initial avatar state — load correct avatar for patient demographics first
    const _avatarType = detectAvatarType(enc.encounter.patient.label);
    loadAvatar(_avatarType);
    setAvatarState(enc.encounter.patient.initial_avatar_state || 'idle');
```

### Change D: Add detectAvatarType + loadAvatar functions
**Find (line ~2269):**
```javascript
  function setAvatarState(emotion) {
```
**Insert BEFORE that line:**
```javascript
  /* ────────────────────────────────────────────────────────────────
     AVATAR SELECTION — detect demographic type from patient label
     and inject the matching SVG into #avatar-wrap
  ──────────────────────────────────────────────────────────────── */
  function detectAvatarType(patientLabel) {
    if (!patientLabel) return 'adult_male';
    const label = patientLabel.toLowerCase();
    const isFemale = /\b(female|woman|women|girl|mother|daughter|she|her|mrs|ms|miss)\b/.test(label);
    const gender = isFemale ? 'female' : 'male';
    const ageMatch = label.match(/\b([5-9]|[1-9]\d|1[01]\d)\b/);
    const age = ageMatch ? parseInt(ageMatch[1]) : null;
    let ageGroup;
    if (age !== null) {
      if      (age <= 11) ageGroup = 'young';
      else if (age <= 17) ageGroup = 'adolescent';
      else if (age <= 64) ageGroup = 'adult';
      else                ageGroup = 'elder';
    } else {
      if      (/\b(child|kid|boy|girl|elementary|youth)\b/.test(label))         ageGroup = 'young';
      else if (/\b(teen|adolescent|juvenile|high.?school|minor)\b/.test(label)) ageGroup = 'adolescent';
      else if (/\b(elder|elderly|old|senior|geriatric|older adult)\b/.test(label)) ageGroup = 'elder';
      else                                                                        ageGroup = 'adult';
    }
    return ageGroup + '_' + gender;
  }

  function loadAvatar(avatarType) {
    const wrap = document.getElementById('avatar-wrap');
    if (!wrap || !window.__AVATAR_SVGS) return;
    const svgStr = window.__AVATAR_SVGS[avatarType] || window.__AVATAR_SVGS['adult_male'];
    wrap.innerHTML = svgStr;
    const root = wrap.querySelector('#avatar-root');
    if (root) root.setAttribute('class', 'state-idle');
  }

```

---

## 9. MOUTH_PATHS — Shared Across All 8 Avatars

The existing MOUTH_PATHS object requires **NO changes**. All 8 avatars place the
mouth at the same absolute SVG coordinates (y~126), so the paths work universally.

```javascript
// EXISTING — DO NOT MODIFY
const MOUTH_PATHS = {
  idle:        'M91 126 Q100 131 109 126',  // gentle resting curve
  speaking:    'M91 126 Q100 131 109 126',  // same as idle (jaw animation does the work)
  distressed:  'M92 130 Q100 135 108 130',  // jaw-drop frown
  tearful:     'M92 129 Q100 134 108 129',  // trembling-frown shape
  anxious:     'M91 127 Q100 131 109 127',  // near-neutral, tight
  agitated:    'M91 127 Q100 130 109 127',
  guarded:     'M92 127 Q100 131 108 127',
  flat_affect: 'M91 128 Q100 128 109 128',  // dead flat line
  hopeful:     'M91 127 Q100 123 109 127',  // gentle smile
  confused:    'M92 127 Q100 131 108 128',  // slight asymmetric frown
};
```

---

## 10. CSS — Zero Changes Required

All existing CSS animation rules use ID selectors that work on whichever SVG is
currently in the DOM. Example:
```css
.state-speaking #avatar-jaw { animation: jawSpeak .32s ease-in-out infinite; }
```
This targets `#avatar-jaw` **inside** the element with `.state-speaking`. Since
`#avatar-root` gets the class and `#avatar-jaw` is always inside it, this works
for all 8 avatars without modification.

The `transform-origin` values in the CSS are absolute pixel coordinates within the
SVG coordinate space — and since all 8 avatars use the same viewBox and same element
positions (for animation-critical parts), they are valid for all 8.

---

## 11. Avatar SVG Specifications

### Shared Element Rules (apply to ALL 8 avatars):

**Required IDs (all must exist in every avatar SVG):**
```
#avatar-root, #avatar-body, #avatar-head, #avatar-face, #avatar-jaw,
#avatar-eyes, #avatar-hand, #avatar-hair, #avatar-brow, #avatar-tear,
#avatar-mouth, #avatar-nose, #avatar-head-shape
```

**Required attributes on avatar-root:**
```html
<svg id="avatar-root"
     viewBox="0 0 200 320"
     xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:100%;overflow:visible">
```

**Required attributes on avatar-body:**
```html
<g id="avatar-body" style="transform-origin:100px 185px" filter="url(#f-avatar-shadow)">
```

**Required attributes on avatar-head:**
```html
<g id="avatar-head" style="transform-origin:100px 130px">
```

**Required attributes on avatar-jaw:**
```html
<g id="avatar-jaw" style="transform-origin:100px 126px">
```

**Required attributes on avatar-hand:**
```html
<g id="avatar-hand" style="transform-origin:100px 214px">
```

**Shared chair block (IDENTICAL in all 8 — copy verbatim):**
```html
<g id="chair">
  <rect x="60" y="170" width="80" height="110" rx="6"
        fill="url(#g-chair)" stroke="#222" stroke-width="1.2"/>
  <rect x="52" y="255" width="96" height="18" rx="5"
        fill="#3a3a4a" stroke="#222" stroke-width="1"/>
  <rect x="46" y="230" width="16" height="44" rx="4"
        fill="#3a3a4a" stroke="#222" stroke-width="1"/>
  <rect x="138" y="230" width="16" height="44" rx="4"
        fill="#3a3a4a" stroke="#222" stroke-width="1"/>
  <rect x="56" y="273" width="8" height="36" rx="3" fill="#2a2a38"/>
  <rect x="136" y="273" width="8" height="36" rx="3" fill="#2a2a38"/>
  <rect x="66" y="278" width="6" height="30" rx="2" fill="#252530"/>
  <rect x="128" y="278" width="6" height="30" rx="2" fill="#252530"/>
  <rect x="56" y="292" width="88" height="5" rx="2" fill="#2a2a38"/>
  <ellipse cx="100" cy="312" rx="44" ry="5" fill="rgba(0,0,0,0.25)"/>
</g>
```

**Shared filters/gradients (chair + shadow — same in all 8 `<defs>`):**
```html
<linearGradient id="g-chair" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%"   stop-color="#4a4a5a"/>
  <stop offset="100%" stop-color="#2e2e3a"/>
</linearGradient>
<filter id="f-avatar-shadow" x="-20%" y="-10%" width="140%" height="130%">
  <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="rgba(0,0,0,0.35)"/>
</filter>
```

---

### 11.1 `adult_male` — The Baseline Avatar

This is the closest to the existing SVG. Use it as the template; all others are
derived from it.

**Skin:** Warm medium-light — stop-0 `#f0b878`, stop-100 `#e8a858`
**Face skin (lighter):** stop-0 `#f5c08e`, stop-100 `#edaa68`
**Hair:** Dark brown `#3a2010`, short
**Eyes:** Blue-grey `#5a7ab5`
**Clothing:** Navy blue — shirt `#5b6fa6` / `#3b4f7e`, pants same

```html
<!-- DEFS unique to adult_male -->
<linearGradient id="g-skin" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%"   stop-color="#f0b878"/>
  <stop offset="100%" stop-color="#e8a858"/>
</linearGradient>
<linearGradient id="g-skin-face" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%"   stop-color="#f5c08e"/>
  <stop offset="100%" stop-color="#edaa68"/>
</linearGradient>
<linearGradient id="g-cloth" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%"   stop-color="#5b6fa6"/>
  <stop offset="100%" stop-color="#3b4f7e"/>
</linearGradient>
```

**Head:** `cx="100" cy="107" rx="29" ry="34"`
**Neck:** `x="91" y="134" width="18" height="22"`
**Torso:** `M72 185 Q68 205 70 230 L130 230 Q132 205 128 185 Q114 175 100 175 Q86 175 72 185Z`
**Left thigh:** `x="74" y="220" width="22" height="50"`
**Right thigh:** `x="104" y="220" width="22" height="50"`
**Left lower leg:** `x="76" y="262" width="18" height="32"`
**Right lower leg:** `x="106" y="262" width="18" height="32"`
**Left shoe:** `cx="85" cy="295" rx="13" ry="7"` fill="#282828"
**Right shoe:** `cx="115" cy="295" rx="13" ry="7"` fill="#282828"

**Hair (short, back mass):**
```html
<ellipse cx="100" cy="100" rx="34" ry="38" fill="#3a2010"/>
<path d="M68 100 Q62 115 66 128" fill="none" stroke="#3a2010" stroke-width="8" stroke-linecap="round"/>
<path d="M132 100 Q138 115 134 128" fill="none" stroke="#3a2010" stroke-width="8" stroke-linecap="round"/>
```

**Eyes:** `rx="7" ry="5.5"` (whites), iris circles `r="3.8"` fill="#5a7ab5", pupil `r="2"` fill="#1a1a28"

**Brows:** Normal weight paths
```
Left:  d="M82 93 Q88 90 94 92"  stroke="#5a3010" stroke-width="2.2"
Right: d="M106 92 Q112 90 118 93" stroke="#5a3010" stroke-width="2.2"
```

**Mouth (initial idle):** `d="M91 126 Q100 131 109 126"` stroke="#b07050"

**Special:** Faint stubble shadow — 3 tiny ellipses on chin:
```html
<ellipse cx="96" cy="133" rx="3" ry="1.2" fill="rgba(80,40,10,0.12)"/>
<ellipse cx="104" cy="133" rx="3" ry="1.2" fill="rgba(80,40,10,0.12)"/>
<ellipse cx="100" cy="135" rx="4" ry="1.2" fill="rgba(80,40,10,0.10)"/>
```

---

### 11.2 `adult_female`

**Skin:** Warm light — stop-0 `#f6c8a0`, stop-100 `#eaaa78`
**Face skin:** stop-0 `#fad4b0`, stop-100 `#f0b888`
**Hair:** Dark brown `#3a1a08`, shoulder-length (extends to y~155 below head)
**Eyes:** Green-grey `#7a9060`
**Clothing:** Teal blouse — `#5a8a7a` / `#3a6a5a`, dark pants `#3a3a50`

**Head:** `cx="100" cy="107" rx="27" ry="33"` (slightly narrower than male)
**Neck:** `x="92" y="134" width="16" height="20"`
**Torso:** `M74 187 Q70 206 72 228 L128 228 Q130 206 126 187 Q113 178 100 178 Q87 178 74 187Z`
(narrower shoulders than adult_male)

**Hair (shoulder-length, parted center):**
```html
<!-- Back mass -->
<ellipse cx="100" cy="100" rx="32" ry="40" fill="#3a1a08"/>
<!-- Left side falls to shoulder -->
<path d="M69 100 Q62 120 65 145 Q68 155 72 158" fill="none"
      stroke="#3a1a08" stroke-width="12" stroke-linecap="round"/>
<!-- Right side falls to shoulder -->
<path d="M131 100 Q138 120 135 145 Q132 155 128 158" fill="none"
      stroke="#3a1a08" stroke-width="12" stroke-linecap="round"/>
<!-- Top part with center part line -->
<path d="M80 78 Q100 72 120 78" fill="none"
      stroke="#3a1a08" stroke-width="6" stroke-linecap="round"/>
```

**Eyes:** Iris `r="3.6"` fill="#7a9060"
**Brows:** Slightly thinner, more arched:
```
Left:  d="M83 92 Q88 89 94 91"  stroke="#5a2808" stroke-width="1.8"
Right: d="M106 91 Q112 89 117 92" stroke="#5a2808" stroke-width="1.8"
```

**Legs:** Same height as adult_male but narrower:
- Left thigh: `x="76" y="220" width="20" height="48"`
- Right thigh: `x="104" y="220" width="20" height="48"`
- Lower legs: dark pants color `#2e2e48`
- Shoes: rounded flats `cx="85" cy="290" rx="11" ry="6"` fill="#282838"

**Mouth:** Same path coords as adult_male (shared MOUTH_PATHS works)
**No stubble.** No wrinkles.

---

### 11.3 `young_male`

**Key proportions:** Larger head-to-body ratio, shorter trunk, shorter legs, feet
don't reach the floor (hang or barely touch chair footrest area).

**Skin:** Medium olive — stop-0 `#f7c98a`, stop-100 `#e8a860`
**Face skin:** stop-0 `#fad6a0`, stop-100 `#f0b870`
**Hair:** Very dark brown (near black) `#2a1a08`, short messy — multiple small bumps
**Eyes:** Hazel-green `#5a8a70`, slightly larger
**Clothing:** Medium blue T-shirt `#4a7ab8` / `#2a5a98`, blue jeans `#3a5a8a` / `#2a4070`

**Head:** `cx="100" cy="107" rx="32" ry="37"` (bigger — classic child proportions)
**Ears:** cx="68" (left), cx="132" (right) — slightly further out due to bigger head
**Neck:** `x="92" y="138" width="16" height="18"` (shorter neck)
**Eye size:** whites `rx="8" ry="6.5"`, iris `r="4.2"` — larger proportionally

**Torso (shorter, narrower):**
```
M76 192 Q72 208 74 222 L126 222 Q128 208 124 192 Q112 183 100 183 Q88 183 76 192Z
```

**Legs (shorter — feet hang):**
- Left thigh: `x="76" y="222" width="20" height="42"`
- Right thigh: `x="104" y="222" width="20" height="42"`
- Left lower leg: `x="78" y="257" width="16" height="26"`
- Right lower leg: `x="106" y="257" width="16" height="26"`
- Left shoe: `cx="86" cy="285" rx="11" ry="6"` fill="#282828"
- Right shoe: `cx="114" cy="285" rx="11" ry="6"` fill="#282828"

**Hair (messy short — bumpy top):**
```html
<ellipse cx="100" cy="98" rx="35" ry="36" fill="#2a1a08"/>
<!-- Messy top bumps -->
<ellipse cx="90"  cy="77" rx="8"  ry="6"  fill="#2a1a08"/>
<ellipse cx="100" cy="74" rx="9"  ry="7"  fill="#2a1a08"/>
<ellipse cx="111" cy="77" rx="8"  ry="6"  fill="#2a1a08"/>
<!-- Side wisps shorter than adult -->
<path d="M66 100 Q60 112 63 122" fill="none" stroke="#2a1a08" stroke-width="7" stroke-linecap="round"/>
<path d="M134 100 Q140 112 137 122" fill="none" stroke="#2a1a08" stroke-width="7" stroke-linecap="round"/>
```

**Brows:** Lighter, thinner (child brows):
```
Left:  d="M82 92 Q88 90 94 92"  stroke="#5a3818" stroke-width="1.6"
Right: d="M106 92 Q112 90 118 92" stroke="#5a3818" stroke-width="1.6"
```

**Arms (shorter):**
- Left upper arm: `M75 195 Q62 204 64 220 Q70 226 76 220 Q74 206 82 198Z`
- Right upper arm: `M125 195 Q138 204 136 220 Q130 226 124 220 Q126 206 118 198Z`
- Left forearm: `M64 220 Q60 232 64 244 Q70 248 74 242 Q70 230 76 220Z`
- Right forearm: `M136 220 Q140 232 136 244 Q130 248 126 242 Q130 230 124 220Z`

**Hands:** Similar to adult but at y~244 (adjusted up):
```html
<g id="avatar-hand" style="transform-origin:100px 210px">
  <path d="M76 244 Q72 251 76 258 Q83 262 90 258 Q94 252 92 245 Q85 241 76 244Z" fill="url(#g-skin)"/>
  <path d="M124 244 Q128 251 124 258 Q117 262 110 258 Q106 252 108 245 Q115 241 124 244Z" fill="url(#g-skin)"/>
  <ellipse cx="100" cy="252" rx="9" ry="5" fill="url(#g-skin)" stroke="#dba070" stroke-width="0.5"/>
</g>
```

**No stubble. No wrinkles. Rounder, more open mouth in idle.**

**T-shirt neckline (crew neck, not V-neck):**
```html
<path d="M90 188 Q100 192 110 188" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-linecap="round"/>
```

---

### 11.4 `young_female`

**Skin:** Light peach — stop-0 `#f9d4a0`, stop-100 `#f0b878`
**Hair:** Auburn/medium brown `#7a3818`, pigtails
**Eyes:** Green `#5a9a60`
**Clothing:** Rose T-shirt `#c06888` / `#a04868`, purple leggings `#5a4090` / `#3a2870`

**Head:** `cx="100" cy="107" rx="31" ry="36"` (slightly smaller than young_male)
**Neck:** `x="93" y="137" width="14" height="18"`

**Hair (pigtails):**
```html
<!-- Back mass -->
<ellipse cx="100" cy="100" rx="33" ry="38" fill="#7a3818"/>
<!-- Center part -->
<path d="M100 74 L100 90" stroke="#5a2010" stroke-width="2" stroke-linecap="round"/>
<!-- Left pigtail — goes to side and curves down -->
<ellipse cx="62"  cy="108" rx="10" ry="14" fill="#7a3818"/>
<path d="M65 120 Q60 140 64 155" fill="none" stroke="#7a3818" stroke-width="9" stroke-linecap="round"/>
<!-- Right pigtail -->
<ellipse cx="138" cy="108" rx="10" ry="14" fill="#7a3818"/>
<path d="M135 120 Q140 140 136 155" fill="none" stroke="#7a3818" stroke-width="9" stroke-linecap="round"/>
<!-- Hair ties (small circles) -->
<circle cx="64"  cy="124" r="4" fill="#e04060"/>
<circle cx="136" cy="124" r="4" fill="#e04060"/>
```

**Eyes:** iris `r="4.2"` fill="#5a9a60"
**Brows:** Light, thin arched:
```
Left:  d="M83 91 Q88 88 94 90"  stroke="#7a3818" stroke-width="1.5"
Right: d="M106 90 Q112 88 117 91" stroke="#7a3818" stroke-width="1.5"
```

**Torso (slightly narrower than young_male):**
```
M78 193 Q74 208 76 222 L124 222 Q126 208 122 193 Q111 184 100 184 Q89 184 78 193Z
```

**Legs/leggings:**
- Thighs: `x="78" y="222" width="19" height="40"` fill purple, `x="103" y="222" width="19" height="40"`
- Lower legs: same purple, shorter
- Shoes: Mary-Jane style (rounded with strap):
  ```html
  <ellipse cx="87" cy="283" rx="11" ry="5.5" fill="#1a1428"/>
  <ellipse cx="113" cy="283" rx="11" ry="5.5" fill="#1a1428"/>
  <!-- Straps -->
  <rect x="82" y="278" width="10" height="2.5" rx="1" fill="#1a1428"/>
  <rect x="108" y="278" width="10" height="2.5" rx="1" fill="#1a1428"/>
  ```

**No stubble. No wrinkles.**

---

### 11.5 `adolescent_male`

**Skin:** Medium tan — stop-0 `#f2b870`, stop-100 `#d89848`
**Hair:** Very dark/near-black `#181008`, longer on top (modern undercut style)
**Eyes:** Grey-blue `#6a7a90`
**Clothing:** Hoodie `#5a6a9a` / `#3a4a7a` (darker navy), dark jeans `#2a3858` / `#1a2840`

**Head:** `cx="100" cy="107" rx="30" ry="35"` (transitioning to adult proportions)
**Neck:** `x="91" y="135" width="18" height="21"`

**Hair (longer top, shorter sides — undercut style):**
```html
<!-- Side mass (darker, close-cropped sides) -->
<ellipse cx="100" cy="104" rx="33" ry="36" fill="#181008"/>
<!-- Longer top swept slightly right -->
<ellipse cx="102" cy="86" rx="26" ry="18" fill="#181008"/>
<!-- Top flop / swept fringe -->
<path d="M76 86 Q90 76 115 82 Q120 84 118 88" fill="#181008" stroke="none"/>
<!-- Left side short -->
<path d="M68 102 Q63 114 65 125" fill="none" stroke="#181008" stroke-width="7" stroke-linecap="round"/>
<!-- Right side short -->
<path d="M132 102 Q137 114 135 125" fill="none" stroke="#181008" stroke-width="7" stroke-linecap="round"/>
```

**Eyes:** iris `r="3.9"` fill="#6a7a90"
**Brows (thicker — teen brows):**
```
Left:  d="M82 93 Q88 90 94 92"  stroke="#281808" stroke-width="2.4"
Right: d="M106 92 Q112 90 118 93" stroke="#281808" stroke-width="2.4"
```

**Torso (approaching adult height but still narrower):**
```
M74 188 Q70 207 72 228 L128 228 Q130 207 126 188 Q114 178 100 178 Q86 178 74 188Z
```
Hoodie front pocket line:
```html
<path d="M82 210 Q100 215 118 210" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1.2" stroke-linecap="round"/>
```

**Legs (longer than child, same as adult):**
- Thighs: `x="74" y="222" width="22" height="48"`, `x="104" y="222" width="22" height="48"`
- Lower: `x="76" y="263" width="18" height="30"` dark jeans color
- Shoes: Chunky sneakers:
  ```html
  <rect x="72" y="290" width="28" height="10" rx="4" fill="#303040"/>
  <rect x="100" y="290" width="28" height="10" rx="4" fill="#303040"/>
  <!-- Sole -->
  <rect x="71" y="296" width="30" height="5" rx="3" fill="#1a1a28"/>
  <rect x="99" y="296" width="30" height="5" rx="3" fill="#1a1a28"/>
  ```

**Slight jaw angularity:** The lower jaw path is slightly more angular than child:
```html
<path d="M75 120 Q79 137 100 143 Q121 137 125 120" fill="url(#g-skin-face)" stroke="none"/>
```

**No stubble yet. No wrinkles.**

---

### 11.6 `adolescent_female`

**Skin:** Warm light — stop-0 `#f8c890`, stop-100 `#eaaa68`
**Hair:** Medium brown `#5a2808`, shoulder-length straight
**Eyes:** Violet `#8a6098`
**Clothing:** Purple casual top `#9a60b0` / `#7a4090`, dark leggings `#2e2040` / `#1e1030`

**Head:** `cx="100" cy="107" rx="28" ry="34"` (narrower than adolescent_male)
**Neck:** `x="92" y="135" width="16" height="20"`

**Hair (shoulder-length, straight, center part):**
```html
<ellipse cx="100" cy="99" rx="30" ry="38" fill="#5a2808"/>
<!-- Center part line -->
<path d="M100 72 L100 88" stroke="#3a1808" stroke-width="1.5" stroke-linecap="round"/>
<!-- Left side falls to shoulder -->
<path d="M70 98 Q63 120 66 148 Q69 158 74 162" fill="none"
      stroke="#5a2808" stroke-width="11" stroke-linecap="round"/>
<!-- Right side falls to shoulder -->
<path d="M130 98 Q137 120 134 148 Q131 158 126 162" fill="none"
      stroke="#5a2808" stroke-width="11" stroke-linecap="round"/>
<!-- Slight curl at ends -->
<path d="M73 160 Q70 166 76 168" fill="none" stroke="#5a2808" stroke-width="8" stroke-linecap="round"/>
<path d="M127 160 Q130 166 124 168" fill="none" stroke="#5a2808" stroke-width="8" stroke-linecap="round"/>
```

**Eyes:** iris `r="3.7"` fill="#8a6098"
**Brows:** Neat, slightly arched:
```
Left:  d="M83 92 Q88 89 94 91"  stroke="#5a2808" stroke-width="1.8"
Right: d="M106 91 Q112 89 117 92" stroke="#5a2808" stroke-width="1.8"
```

**Torso (narrower shoulders, teen proportions):**
```
M76 190 Q72 208 74 226 L126 226 Q128 208 124 190 Q112 181 100 181 Q88 181 76 190Z
```

**Legs/leggings:**
- Thighs: `x="77" y="220" width="21" height="46"` dark leggings color
- Lower: same color, `x="79" y="259" width="17" height="28"`
- Shoes: simple rounded flats:
  ```html
  <ellipse cx="88" cy="289" rx="12" ry="6" fill="#1a1428"/>
  <ellipse cx="112" cy="289" rx="12" ry="6" fill="#1a1428"/>
  ```

---

### 11.7 `elder_male`

**Skin:** Slightly muted/drier — stop-0 `#e8b882`, stop-100 `#d09a60`
**Face skin:** stop-0 `#ecca94`, stop-100 `#d8a870`
**Hair:** Grey-white `#b8b8c0`, sparse/thinning on top
**Eyes:** Muted blue-grey `#7a8898`
**Clothing:** Brown cardigan `#7a6050` / `#5a4030`, dark trousers `#3a3028` / `#2a2018`

**Head:** `cx="100" cy="107" rx="29" ry="33"` (slightly less tall than adult — face droops)
**Neck:** `x="91" y="134" width="18" height="21"`

**Hair (sparse white/grey):**
```html
<!-- Sparse grey hair on top — thin wisps -->
<path d="M76 86 Q85 80 100 79 Q115 80 124 86" fill="none"
      stroke="#b8b8c0" stroke-width="5" stroke-linecap="round"/>
<!-- Side fringe (thinner) -->
<path d="M68 96 Q62 110 64 124" fill="none"
      stroke="#b8b8c0" stroke-width="5" stroke-linecap="round"/>
<path d="M132 96 Q138 110 136 124" fill="none"
      stroke="#b8b8c0" stroke-width="5" stroke-linecap="round"/>
<!-- Back of head — very thin coverage -->
<ellipse cx="100" cy="104" rx="33" ry="30" fill="none"
         stroke="#b8b8c0" stroke-width="3" opacity="0.4"/>
```

**Eyes:** iris `r="3.5"` fill="#7a8898" — slightly smaller/deeper
**Eye socket shadows (more prominent):**
```html
<ellipse cx="88"  cy="108" rx="9" ry="8" fill="rgba(0,0,0,0.09)"/>
<ellipse cx="112" cy="108" rx="9" ry="8" fill="rgba(0,0,0,0.09)"/>
```

**Brows (lighter, bushier — elder brows):**
```
Left:  d="M82 92 Q88 89 94 92"  stroke="#a09080" stroke-width="2.6"
Right: d="M106 92 Q112 89 118 93" stroke="#a09080" stroke-width="2.6"
```

**Wrinkle lines (thin, low-opacity strokes):**
```html
<!-- Forehead lines -->
<path d="M82 90 Q100 88 118 90" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="1" stroke-linecap="round"/>
<path d="M84 85 Q100 83 116 85" fill="none" stroke="rgba(160,120,80,0.14)" stroke-width="0.8" stroke-linecap="round"/>
<!-- Crow's feet left -->
<path d="M80 110 Q77 113 79 116" fill="none" stroke="rgba(160,120,80,0.20)" stroke-width="0.8" stroke-linecap="round"/>
<path d="M80 111 Q76 115 78 118" fill="none" stroke="rgba(160,120,80,0.15)" stroke-width="0.8" stroke-linecap="round"/>
<!-- Crow's feet right -->
<path d="M120 110 Q123 113 121 116" fill="none" stroke="rgba(160,120,80,0.20)" stroke-width="0.8" stroke-linecap="round"/>
<path d="M120 111 Q124 115 122 118" fill="none" stroke="rgba(160,120,80,0.15)" stroke-width="0.8" stroke-linecap="round"/>
<!-- Nasolabial folds -->
<path d="M90 118 Q88 124 90 128" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.8" stroke-linecap="round"/>
<path d="M110 118 Q112 124 110 128" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.8" stroke-linecap="round"/>
```

**Torso (cardigan — slightly rounded shoulders, slight forward lean via Q control points):**
```
M73 187 Q68 207 70 228 L130 228 Q132 207 127 187 Q114 177 100 177 Q86 177 73 187Z
```
Cardigan button line:
```html
<line x1="100" y1="190" x2="100" y2="225" stroke="rgba(0,0,0,0.2)" stroke-width="1.2" stroke-dasharray="3,4"/>
<!-- 3 buttons -->
<circle cx="100" cy="196" r="2" fill="rgba(0,0,0,0.25)"/>
<circle cx="100" cy="207" r="2" fill="rgba(0,0,0,0.25)"/>
<circle cx="100" cy="218" r="2" fill="rgba(0,0,0,0.25)"/>
```

**Slight stoop:** achieved by adjusting postureBow animation baseline (already in CSS for distressed) — for idle, body transform includes `transform: translateY(2px) rotate(-1.5deg)` via inline style on `#avatar-body`:
```html
<g id="avatar-body" style="transform-origin:100px 185px; transform: translateY(2px) rotate(-1.5deg);"
   filter="url(#f-avatar-shadow)">
```
Note: This static stoop offset is applied on the SVG element itself. The CSS animations apply additional transforms on top of this — CSS animations use `animation` not `transform` directly, so they don't override this inline transform. However, the `breathe` animation uses `scaleY` which WILL interact with the inline rotate. Test to confirm visual acceptability. If it causes jitter, remove the inline transform and instead adjust the torso path Q control points to lean forward slightly.

**Legs (same height as adult — elderly people's legs don't shorten):**
- Thighs: `x="74" y="222" width="22" height="46"` dark trouser color
- Shoes: wider, lower — `cx="85" cy="292" rx="14" ry="7"` — heavier shoes

---

### 11.8 `elder_female`

**Skin:** Soft muted light — stop-0 `#f0c8a0`, stop-100 `#e0aa80`
**Face skin:** stop-0 `#f6d4b0`, stop-100 `#e8b888`
**Hair:** White-grey `#d0d0d8`, short styled curls
**Eyes:** Muted grey `#808898`
**Clothing:** Mauve blouse `#8a6070` / `#6a4050`, dark trousers `#38303a` / `#28202a`

**Head:** `cx="100" cy="107" rx="26" ry="32"` (narrower/smaller — elderly female)
**Neck:** `x="92" y="134" width="16" height="20"`

**Hair (short white curled — classic elder woman style):**
```html
<!-- Base mass (shorter, sits close to head) -->
<ellipse cx="100" cy="97" rx="30" ry="28" fill="#d0d0d8"/>
<!-- Curl texture bumps on top -->
<ellipse cx="88"  cy="84" rx="8" ry="6"  fill="#d0d0d8"/>
<ellipse cx="100" cy="82" rx="9" ry="7"  fill="#d0d0d8"/>
<ellipse cx="112" cy="84" rx="8" ry="6"  fill="#d0d0d8"/>
<!-- Side puffs (shorter than men's side hair) -->
<ellipse cx="70"  cy="104" rx="8" ry="10" fill="#d0d0d8"/>
<ellipse cx="130" cy="104" rx="8" ry="10" fill="#d0d0d8"/>
<!-- Subtle curl highlights -->
<path d="M84 84 Q88 80 92 84" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5" stroke-linecap="round"/>
<path d="M98 82 Q102 78 106 82" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5" stroke-linecap="round"/>
```

**Eyes:** iris `r="3.4"` fill="#808898"
**Brows:** Very light, thin:
```
Left:  d="M83 93 Q88 91 94 93"  stroke="#b0a090" stroke-width="1.4"
Right: d="M106 93 Q112 91 117 93" stroke="#b0a090" stroke-width="1.4"
```

**Wrinkle lines:** Same pattern as elder_male but slightly fewer (lighter touch):
```html
<!-- Forehead -->
<path d="M84 90 Q100 88 116 90" fill="none" stroke="rgba(160,120,80,0.15)" stroke-width="0.9" stroke-linecap="round"/>
<!-- Crow's feet -->
<path d="M81 110 Q78 113 80 116" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.7" stroke-linecap="round"/>
<path d="M119 110 Q122 113 120 116" fill="none" stroke="rgba(160,120,80,0.18)" stroke-width="0.7" stroke-linecap="round"/>
<!-- Nasolabial folds -->
<path d="M91 118 Q89 124 91 128" fill="none" stroke="rgba(160,120,80,0.16)" stroke-width="0.7" stroke-linecap="round"/>
<path d="M109 118 Q111 124 109 128" fill="none" stroke="rgba(160,120,80,0.16)" stroke-width="0.7" stroke-linecap="round"/>
```

**Torso (blouse — narrower, with collar detail):**
```
M75 188 Q71 207 73 227 L127 227 Q129 207 125 188 Q113 179 100 179 Q87 179 75 188Z
```
Collar:
```html
<path d="M94 185 L100 194 L106 185" fill="none" stroke="rgba(255,255,255,0.22)"
      stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
```

Pearl necklace detail:
```html
<g opacity="0.65">
  <circle cx="90"  cy="167" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
  <circle cx="95"  cy="164" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
  <circle cx="100" cy="163" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
  <circle cx="105" cy="164" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
  <circle cx="110" cy="167" r="2.2" fill="#f0e8e0" stroke="#d0c8c0" stroke-width="0.5"/>
</g>
```

**Legs (narrower):**
- Thighs: `x="78" y="221" width="19" height="46"` dark trouser color
- Shoes: low-heeled dress shoes `cx="87" cy="289" rx="12" ry="6"` fill="#2a2030"

---

## 12. `avatar-svgs.js` — File Structure

```javascript
/**
 * avatar-svgs.js
 * Defines window.__AVATAR_SVGS — 8 complete SVG strings for patient avatars.
 * Loaded before clinical-presentation-exercise.html's main script.
 *
 * Usage: window.__AVATAR_SVGS['adult_female'] → SVG string
 *
 * Keys: young_male, young_female, adolescent_male, adolescent_female,
 *       adult_male, adult_female, elder_male, elder_female
 *
 * ALL avatars:
 * - viewBox="0 0 200 320"
 * - Face anchor: head center cy=107, mouth y=126 (matches shared MOUTH_PATHS)
 * - Same required element IDs (see PLAN_avatar_overhaul.md §4)
 */

(function() {
  'use strict';

  // Shared defs that appear in every avatar (chair gradient + drop shadow)
  // Each avatar's SVG string MUST include these in its <defs>
  // (they are duplicated across the 8 SVG strings for self-containment)

  window.__AVATAR_SVGS = {

    adult_male: `<svg id="avatar-root" viewBox="0 0 200 320"
       xmlns="http://www.w3.org/2000/svg"
       style="width:100%;height:100%;overflow:visible">
      <defs>
        <!-- [adult_male defs: g-skin, g-skin-face, g-cloth, g-chair, f-avatar-shadow] -->
      </defs>
      <!-- [chair block — identical across all] -->
      <!-- [avatar-body group with adult_male specs] -->
    </svg>`,

    adult_female: `...`,
    young_male:   `...`,
    young_female: `...`,
    adolescent_male:   `...`,
    adolescent_female: `...`,
    elder_male:   `...`,
    elder_female: `...`,
  };

})();
```

Each SVG string is a complete, self-contained SVG element (including `<svg>` open/close
tags and all `<defs>`). The gradient IDs (`g-skin`, `g-skin-face`, `g-cloth`, etc.) are
defined inside the `<defs>` of each avatar's SVG — they do NOT conflict because each
SVG is a separate DOM subtree within the same document.

**WARNING:** Since all 8 SVGs are injected into the same HTML document at runtime
(replacing each other, not simultaneously), gradient ID collisions are NOT an issue.
However, if they were shown simultaneously, IDs would clash. Because only one SVG is
ever in the DOM at a time (swap happens on each encounter), this is safe.

---

## 13. Animation State Compatibility Table

Verify that all 8 avatars support all 13 states correctly after implementation:

| State | CSS Target | Required Element | All 8 have it? |
|-------|-----------|-----------------|----------------|
| idle | #avatar-body breathe | avatar-body | YES (required) |
| speaking | #avatar-jaw jawSpeak | avatar-jaw | YES (required) |
| distressed | #avatar-body postureBow | avatar-body | YES (required) |
| tearful | #avatar-tear tearFall | avatar-tear | YES (required) |
| anxious | #avatar-body breatheFast, #avatar-hand fidgetHand | both | YES |
| agitated | #avatar-head microShake, #avatar-body breatheFast | both | YES |
| guarded | #avatar-eyes gazeAvert | avatar-eyes | YES |
| flat_affect | #avatar-body slow breathe, #avatar-eyes blinkSlow, #avatar-face desaturate | all | YES |
| hopeful | #avatar-body postureUpright, #avatar-face brighten | both | YES |
| confused | #avatar-head headTilt | avatar-head | YES |

---

## 14. Dev Panel Extension (Optional but Recommended)

The file has a dev panel for testing avatar states (lines ~2910–2930). After
implementing the 8 avatars, add an avatar-type selector to the dev panel:

```javascript
// In the dev panel HTML block, add:
// <select id="dev-avatar-select">
//   <option value="adult_male">adult_male</option>
//   <option value="adult_female">adult_female</option>
//   ... all 8 ...
// </select>
// <button onclick="loadAvatar(document.getElementById('dev-avatar-select').value)">
//   Load Avatar
// </button>
```

This lets you visually test all 8 avatars × all 13 states = 104 combinations.

---

## 15. Implementation Sequence

Execute in this exact order. Each step is independently verifiable.

### Step 1 — Create `avatar-svgs.js` with `adult_male` only
- Create `mastery-page/avatar-svgs.js`
- Implement `window.__AVATAR_SVGS` with only `adult_male` populated
- Other 7 keys: copy adult_male as placeholder
- Goal: verify the load mechanism works before building all 8

### Step 2 — Modify `clinical-presentation-exercise.html`
Make changes A, B, C, D from §8:
- Remove inline SVG from avatar-wrap (lines 957–1200)
- Add `<script src="avatar-svgs.js">` before `</body>`
- Add `detectAvatarType()` + `loadAvatar()` functions
- Add 2 lines to `startEncounter()`

### Step 3 — Verify adult_male works
- Open in browser, run a CASS or PMET encounter
- Confirm avatar appears, all animation states work
- Test dev panel state cycling
- Check console for errors

### Step 4 — Implement all 8 SVG variants in `avatar-svgs.js`
Build in this order (baseline → most complex):
1. `adult_female` (minimal changes from adult_male)
2. `adolescent_male`
3. `adolescent_female`
4. `young_male`
5. `young_female`
6. `elder_male`
7. `elder_female`

### Step 5 — Test demographic detection
- Check `detectAvatarType()` against actual patient labels in CASS/LDEV/CPAT JSONs
- `python3 -c "import json; d=json.load(open('data/CASS_presentations.json')); [print(e['encounter']['patient']['label']) for e in d['encounters']]"`
- Verify each label maps to the intended avatar type

### Step 6 — Full visual regression
- Run through all 9 domain presentation files
- Verify correct avatar appears for each encounter's demographic
- Test all 13 animation states on each of the 8 avatars using dev panel
- Confirm `tearFall` works (requires `avatar-tear` opacity restart in `setAvatarState()`)
- Confirm `flat_affect` desaturate filter works on new avatars

### Step 7 — Commit and push

```bash
cd /c/Users/mcdan/mastery-page
git add avatar-svgs.js clinical-presentation-exercise.html
git commit -m "Add 8-avatar demographic system for patient encounter module"
git push
```

---

## 16. Verification Checklist

- [ ] `window.__AVATAR_SVGS` defined with all 8 keys
- [ ] Each SVG has `id="avatar-root"` on root element
- [ ] Each SVG has all 13 required element IDs (see §4)
- [ ] Face anchor: mouth path at Y≈126 in all 8 avatars
- [ ] `#avatar-jaw` has `style="transform-origin:100px 126px"` in all 8
- [ ] `#avatar-body` has `style="transform-origin:100px 185px"` in all 8
- [ ] `#avatar-head` has `style="transform-origin:100px 130px"` in all 8
- [ ] `#avatar-hand` has `style="transform-origin:100px 214px"` in all 8
- [ ] `loadAvatar()` injected before `setAvatarState()` in function order
- [ ] `startEncounter()` calls `detectAvatarType()` then `loadAvatar()` before `setAvatarState()`
- [ ] `<script src="avatar-svgs.js">` added to HTML
- [ ] Old inline SVG removed (avatar-wrap is empty placeholder in HTML)
- [ ] No SVG gradient ID collisions cause visual artifacts
- [ ] All 8 avatars × 13 states = 104 combinations tested with dev panel
- [ ] `tearful` state: tear animation restarts on avatar swap (handled by existing `setAvatarState` code)
- [ ] `flat_affect` state: `filter: saturate(0.55)` on `#avatar-face` visible on all 8
- [ ] Patient label detection tested against real data from all 9 domain JSON files
- [ ] No JavaScript errors in console after swap
- [ ] Mobile layout: avatar-wrap responsive (CSS already handles this, no changes needed)

---

## 17. Sample Patient Labels → Avatar Type (from Real Data)

Run this to audit all patient labels in the dataset:

```bash
python3 -c "
import json, glob
for f in glob.glob('data/*_presentations.json'):
    d = json.load(open(f))
    for e in d.get('encounters', []):
        label = e.get('encounter',{}).get('patient',{}).get('label','')
        if label: print(label)
" | sort -u
```

Compare each line against `detectAvatarType()` logic to verify correct mapping.

---

## 18. Key Files Reference

| File | Role |
|------|------|
| `mastery-page/clinical-presentation-exercise.html` | Main exercise page — modify §8 changes only |
| `mastery-page/avatar-svgs.js` | CREATE — contains all 8 SVG strings |
| `mastery-page/PLAN_avatar_overhaul.md` | This document |
| `mastery-page/data/*_presentations.json` | Patient encounter data (read-only reference) |
| `mastery-page/clinical-presentation-settings.html` | Settings page — DO NOT TOUCH |

---

*Document complete. All information needed to implement this feature from scratch
is contained in this file. Begin at §15 Step 1.*
