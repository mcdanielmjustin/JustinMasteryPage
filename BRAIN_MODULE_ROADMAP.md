# Brain Pathology Module — Complete Vision & Technical Roadmap

## Mandate

This module is the centerpiece of MasteryPage's neuropsychology preparation. It must be
the best interactive brain anatomy tool available for EPPP students — better than any
textbook, better than any existing app. Every chunk should be executed at the highest
possible quality. Do not hedge on difficulty. Do not simplify to make the task easier.
Build the thing that genuinely helps students master neuropsychology.

---

## Current State (as of Chunk 0 — complete)

### Files built
- `brain-settings.html` — Category/count selector, 7 categories, 4 count options,
  summary bar, "Explore Brain Map" button linking to study mode
- `brain-exercise.html` — Full quiz engine + SVG lateral brain. 4-screen flow
  (loading → quiz → results → review). 3 question types. localStorage session
  save/restore. Study/explore mode with slide-up info panel. Realistic SVG tissue
  rendering: 5 SVG filters (f-sulcal deep-groove penumbra, f-gyrus warm crown glow,
  f-cortex feTurbulence fractal-noise texture, brain-shadow, region-glow), 116 path
  elements, 55+ sulci, 4-stop radial gradients per region, subsurface scatter layer,
  pial vasculature, cerebellum folia, per-region CSS drop-shadows, exploded-diagram
  region separation
- `data/brain_data.js` — `window.__BRAIN_DATA` with 25 questions across 7 categories,
  11 region info objects (label, ba, functions, syndromes, vascular)

### SVG lateral brain — 11 regions (in drawing order, with transforms)
All coordinates are in base space (viewBox 0 0 520 360). Region `<g>` elements have
`transform="translate(x,y)"` for exploded-diagram separation.

| Region ID | Transform | Role |
|---|---|---|
| occipital_lobe | translate(11,1) | Drawn first (deepest) |
| parietal_lobe | translate(7,-5) | |
| temporal_lobe | translate(-4,8) | |
| frontal_lobe | translate(-10,-3) | |
| cerebellum | translate(6,9) | |
| brainstem | translate(0,9) | |
| motor_cortex | translate(-5,-6) | Sub-region, drawn on top |
| somatosensory_cortex | translate(-3,-7) | Sub-region |
| prefrontal_cortex | translate(-12,-2) | Sub-region |
| brocas_area | translate(-11,1) | Sub-region |
| wernickes_area | translate(6,5) | Sub-region |

### Gradient/filter IDs in use
Gradients: g-frontal, g-pfc, g-broca, g-motor, g-parietal, g-sensory, g-temporal,
g-wernicke, g-occipital, g-cerebellum, g-brainstem, g-specular, g-hotspot, g-scatter,
g-ambient, g-rim
Filters: brain-shadow, region-glow, f-sulcal, f-gyrus, f-cortex
ClipPaths: clip-cb (cerebellum folia mask)

### CSS class system for brain regions
`.brain-region` — base (drop-shadow, transition)
`.region-active` — cursor pointer (quiz mode)
`.region-dimmed` — opacity 0.16 (inactive in quiz)
`.region-selected` — gold dashed stroke (user clicked, awaiting submit)
`.region-highlighted` — pulsing gold (location_to_deficit type: "this region is damaged")
`.region-correct` — green fill (correct answer)
`.region-wrong` — red fill + shake (wrong answer)
`.svg-study-mode .brain-region` — all clickable (study mode)
`.study-selected` — gold drop-shadow (study mode selected)

### JS global state (quiz mode)
`pool[]`, `current`, `correct`, `answered`, `missed[]`, `selectedRegion`,
`selectedChipIdx`, `submitted`, `IS_STUDY`, `CATEGORIES`, `COUNT`

### Key JS functions
`renderQuestion(q)` — dispatches to type-specific renderers
`renderDeficitToLocation(q)` — activates correct + distractor regions, dims rest
`renderLocationToDeficit(q)` — highlights target region, shows 4 chips
`handleSubmit()` — scores, reveals explanation, locks interaction
`nextQuestion()` — advances pool, calls renderQuestion
`initStudy()` — sets up study mode, all regions clickable
`handleStudyRegionClick(g)` — populates and opens info panel
`populateInfoPanel(label, info)` — fills the slide-up panel

---

## Architecture (Full Vision)

```
brain-settings.html
    │
    ├── Start Session → brain-exercise.html?categories=...&count=...&view=lateral
    │                   brain-exercise.html?categories=...&count=...&view=medial
    │
    └── Explore Brain → brain-exercise.html?mode=study&view=lateral  (default)
                        brain-exercise.html?mode=study&view=medial
                        brain-exercise.html?mode=study&view=3d

brain-exercise.html
    ├── mode=quiz, view=lateral   → existing SVG lateral quiz (DONE)
    ├── mode=quiz, view=medial    → new SVG medial quiz (Phase 1)
    ├── mode=study, view=lateral  → existing SVG study mode (DONE)
    ├── mode=study, view=medial   → new SVG study mode (Phase 1)
    └── mode=study, view=3d       → Three.js explorer (Phase 2)

data/brain_data.js
    ├── regions{}        — info objects for all structures (lateral + medial)
    ├── questions[]      — all quiz questions (lateral + medial)
    ├── pathways[]       — circuit definitions for Phase 3
    └── pathologies[]    — comparative pathology overlays for Phase 4
```

---

## The Full Structure Set (EPPP High-Yield)

### Already built (lateral SVG, 11 regions)
Frontal lobe, Prefrontal cortex, Broca's area, Motor cortex, Parietal lobe,
Somatosensory cortex, Temporal lobe, Wernicke's area, Occipital lobe,
Cerebellum, Brainstem

### Phase 1 additions (medial SVG, 12 new regions)
Corpus callosum, Cingulate gyrus, Thalamus, Hypothalamus, Mamillary bodies,
Hippocampus, Amygdala, Fornix, Medial frontal cortex, Cuneus/Precuneus (occipital
medial), Cerebellum vermis, Full brainstem (midbrain / pons / medulla labeled)

### Phase 2 additions (3D subcortical, visible via glass-brain)
Caudate nucleus, Putamen, Globus pallidus, Substantia nigra, Subthalamic nucleus,
Locus coeruleus, Raphe nuclei, Internal capsule, Arcuate fasciculus, Corona radiata

---

## PHASE 1 — Medial View (SVG, same quiz engine)

### Why Phase 1 first
Pure SVG — zero new dependencies. Same question engine. Same CSS. Same JS routing.
Ships fast. Adds ~12 high-yield structures and ~25 questions that cover the most-tested
EPPP neuropsychology content not reachable from the lateral view. Students who can ace
the lateral view still fail questions about Korsakoff, Klüver-Bucy, split-brain,
conduction aphasia, and Papez circuit pathology — all of which require medial anatomy.

---

### CHUNK 1A — Medial Brain SVG Drawing

**Files to read before starting:**
- `brain-exercise.html` lines 519–1020 (the entire SVG block) — understand the exact
  HTML structure, defs, drawing order, gradient IDs, filter IDs, texture layer approach
- `brain-exercise.html` lines 133–200 (CSS for `.brain-region`, all state classes) —
  the medial SVG must use identical CSS classes

**Files to write:**
- `brain-exercise.html` — add the medial SVG immediately after the lateral SVG's
  closing `</div>` (`.brain-container`), wrapped in its own `.brain-container` div
  with `id="brain-container-medial"` and `style="display:none"` initially

**What to build:**
A complete second inline SVG (`id="brain-svg-medial"`, `viewBox="0 0 520 380"`) showing
the left hemisphere cut along the midsagittal plane. This is the view you get when you
slice the brain exactly down the middle and look at the cut surface from the right.

**Anatomical orientation:**
- Left = anterior (frontal pole / orbitofrontal)
- Right = posterior (occipital pole)
- Top = superior (vertex)
- Bottom = inferior (brainstem exits downward)
- The corpus callosum forms a large C-shape in the center-upper area
- The cingulate gyrus arches above the corpus callosum
- The thalamus and hypothalamus sit below the corpus callosum, center
- The brainstem extends downward-right from the diencephalon
- The hippocampus and amygdala are in the medial temporal region (lower-left area)
- The cerebellum fills the lower-right posterior fossa

**12 regions to draw (approximate SVG coordinates, base space before transforms):**

```
1. MEDIAL FRONTAL CORTEX (id: medial_frontal)
   The frontal lobe medial surface — superior frontal gyrus medial face, paracentral lobule
   Location: upper-left quadrant, x:35-210, y:20-180
   Path: large curved region filling upper-left. Anterior border curves from top-left
   downward. Superior border follows brain vertex. Posterior boundary = paracentral sulcus
   (just anterior to where motor/sensory strips hit the medial surface).
   Approximate: M 210,30 C 170,18 120,16 80,26 C 50,36 32,68 30,110
                C 30,148 36,175 50,195 C 70,210 100,215 130,210
                C 155,206 175,195 192,180 C 205,165 210,140 210,30 Z
   Gradient: new g-med-frontal (same warm tissue palette, cx=30% cy=28%)
   Label: "Med. Frontal" at x=105, y=100

2. CINGULATE GYRUS (id: cingulate_gyrus)
   The gyrus that arches above and follows the corpus callosum like a belt
   Location: arching band, x:50-370, y:100-190 (curves above corpus callosum)
   Path: a banana-shaped arc following the corpus callosum curve
   Approximate: M 55,192 C 68,178 90,168 120,162 C 160,156 210,154 260,154
                C 300,154 335,158 360,168 C 375,176 382,188 375,200
                C 362,210 335,212 298,208 C 255,204 210,202 165,204
                C 125,206 90,210 68,212 C 58,212 50,206 55,192 Z
   Gradient: new g-cingulate
   Label: "Cingulate" at x=215, y=184

3. CORPUS CALLOSUM (id: corpus_callosum)
   The massive white matter commissure — the most prominent feature on medial view
   Location: center, x:80-380, y:190-240 (thick C-shaped band)
   Draw as 3 sections: genu (anterior knob), body (main horizontal span), splenium (posterior bulb)
   Main path (unified): M 90,238 C 82,228 80,216 84,206 C 88,196 98,188 112,186
                         C 135,183 175,182 220,182 C 265,182 320,184 355,190
                         C 374,194 382,204 380,216 C 378,228 368,236 350,238
                         C 320,240 270,240 220,240 C 170,240 125,240 90,238 Z
   This is the full corpus callosum body. Genu = left bulge, Splenium = right bulge.
   Make genu visually distinct by adding a rounded protrusion at left end:
   Genu overlay: M 84,206 C 80,196 76,185 78,175 C 82,162 94,156 106,158
                  C 118,160 126,170 124,182 C 120,188 112,192 106,192 C 100,192 92,198 84,206 Z
   Gradient: g-cc (white/cream — white matter, distinctly paler than cortex)
   g-cc stops: #F0E8DE (lit) → #D4C4B0 (mid) → #A89080 (shadow) → #6A5040 (deep)
   Label: "Corpus Callosum" at x=225, y=214

4. THALAMUS (id: thalamus)
   Egg-shaped relay station, below corpus callosum body, center of brain
   Location: center, approximately x:200-310, y:248-300
   Path: M 210,252 C 224,244 248,240 272,240 C 296,240 316,248 322,262
         C 328,276 320,294 304,302 C 286,308 260,308 240,302
         C 220,296 206,282 210,252 Z
   Gradient: g-thalamus (slightly grayer/cooler than cortex — diencephalon tissue)
   Label: "Thalamus" at x=265, y=276

5. HYPOTHALAMUS (id: hypothalamus)
   Below thalamus, small but critical — autonomic and endocrine hub
   Location: x:220-285, y:302-330
   Path: M 228,304 C 238,298 256,296 274,298 C 286,300 294,308 290,320
         C 286,330 270,336 254,334 C 236,330 224,320 228,304 Z
   Gradient: g-hypothalamus (slightly warmer/darker than thalamus)
   Label: "Hypothalamus" at x=258, y=318

6. MAMILLARY BODIES (id: mamillary_bodies)
   Two small bumps on the inferior surface of the hypothalamus — Korsakoff landmark
   Location: x:240-275, y:332-348
   Path: Two small ellipses side by side
   Left: M 243,340 C 243,334 249,330 255,330 C 261,330 267,334 267,340
         C 267,346 261,350 255,350 C 249,350 243,346 243,340 Z
   Right: (omit — we see only medial surface, so just one visible)
   Use an ellipse element: <ellipse cx="256" cy="340" rx="14" ry="10">
   Gradient: g-mamillary (small, so use solid #B87860 with subtle radial)
   Label: "Mamillary B." at x=256, y=358 (small font, 8px)

7. FORNIX (id: fornix)
   White matter arch connecting hippocampus to mamillary bodies — Papez circuit backbone
   Location: arching tract, x:155-285, y:220-310
   Draw as a curved stroke-based path (filled thin arc, not a region — but still make it
   clickable by giving it a wider invisible hitarea)
   Visible path: M 160,265 C 162,252 168,240 180,232 C 194,222 216,220 240,222
                  C 258,224 272,232 278,248 C 282,260 280,276 272,290
                  C 266,302 258,310 250,314
   Render as a white-matter tract: fill the area between a double-stroked path
   (inner and outer boundary) to create a tract shape ~12px wide
   Gradient: g-fornix (cream/white, white matter)
   Label: "Fornix" at x=205, y=228 (small, 8px)

8. HIPPOCAMPUS (id: hippocampus)
   Seahorse-shaped structure in medial temporal lobe — declarative memory
   Location: lower-left, x:60-180, y:250-320
   In medial view it appears as a curved banana/J-shaped structure
   Path: M 70,268 C 68,254 76,242 90,238 C 108,234 130,238 148,248
         C 165,258 174,272 172,288 C 170,304 158,316 142,320
         C 122,322 100,316 84,305 C 72,295 68,282 70,268 Z
   Gradient: g-hippocampus (olive-warm, slightly darker than cortex — allocortex)
   g-hippocampus: #D09A72 → #A06848 → #744030 → #3E1C10
   Label: "Hippocampus" at x=120, y=282

9. AMYGDALA (id: amygdala)
   Almond-shaped nucleus, anterior to hippocampus, medial temporal
   Location: x:56-108, y:226-268
   Path: M 62,244 C 62,230 70,220 84,218 C 98,216 110,224 112,240
         C 114,256 106,268 90,270 C 74,270 62,260 62,244 Z
   Gradient: g-amygdala (slightly redder/deeper than hippocampus — primitive cortex)
   g-amygdala: #C88C6A → #9A5C40 → #6C3428 → #381410
   Label: "Amygdala" at x=86, y=246

10. CUNEUS / PRECUNEUS (id: occipital_medial)
    Medial occipital cortex — V1 on medial surface, visual processing
    Location: upper-right, x:340-490, y:22-185
    Path: M 380,28 C 408,22 445,24 468,42 C 486,58 490,90 486,128
          C 482,166 468,196 446,210 C 424,222 398,222 376,210
          C 358,198 348,178 345,155 C 342,128 346,98 356,72
          C 363,50 370,32 380,28 Z
    Gradient: g-occipital (reuse from lateral, same region)
    Label: "Occipital\n(Medial)" at x=428, y=118 — split into two tspan lines

11. CEREBELLUM VERMIS + HEMISPHERE (id: cerebellum_medial)
    In medial view: the vermis (central) + posterior hemisphere visible
    Location: lower-right, x:310-490, y:240-378
    Path: M 316,248 C 335,236 368,228 400,230 C 432,232 462,246 480,268
          C 494,288 496,316 488,342 C 478,364 456,376 428,378
          C 396,380 360,372 334,354 C 312,338 302,312 306,284
          C 308,268 312,254 316,248 Z
    Apply folia (horizontal lines clipped to this shape, same technique as lateral)
    Gradient: g-cerebellum (reuse from lateral — same tissue)
    Label: "Cerebellum" at x=402, y=310

12. BRAINSTEM MEDIAL (id: brainstem_medial)
    Full brainstem visible on medial view: midbrain → pons → medulla
    More elongated than lateral view brainstem
    Location: x:255-340, y:288-378
    Path: M 262,292 C 278,284 306,280 326,286 C 340,292 346,308 344,328
          C 342,350 334,368 320,376 C 304,382 284,378 272,368
          C 258,356 252,336 254,314 C 255,302 258,294 262,292 Z
    Add segmentation lines (midbrain/pons, pons/medulla) as in lateral
    Gradient: g-brainstem (reuse from lateral)
    Label: "Brainstem" at x=300, y=332

```

**Drawing order (painter's algorithm — deepest first):**
1. occipital_medial (background, posterior)
2. cerebellum_medial (background, posterior-inferior)
3. brainstem_medial (overlaps cerebellum)
4. medial_frontal (large region, fills left)
5. corpus_callosum (prominent central structure)
6. cingulate_gyrus (above corpus callosum)
7. thalamus (below corpus callosum)
8. hypothalamus (below thalamus)
9. mamillary_bodies (below hypothalamus)
10. fornix (thin tract, draws over thalamus)
11. hippocampus (medial temporal, lower-left)
12. amygdala (anterior to hippocampus, top)

**New gradient IDs to create (add to existing `<defs>`):**
- `g-med-frontal` — same 4-stop warm tissue as g-frontal
- `g-cingulate` — slightly cooler pink (cingulate is often depicted as slightly purplish)
  stops: #D8AABA → #A07080 → #784860 → #401830
- `g-cc` — cream/white (white matter): #EEE4DA → #CCBCAA → #A09080 → #6A5040
- `g-thalamus` — gray-rose: #CCB0A8 → #9C7870 → #6C4848 → #381C20
- `g-hypothalamus` — slightly warmer than thalamus: #C8A090 → #986860 → #684040 → #341818
- `g-mamillary` — small, use radial: #C4907A → #946050 → #643830
- `g-fornix` — white matter cream: #EAE0D2 → #C8B8A0 → #9A8878 → #604840
- `g-hippocampus` — olive-warm (allocortex): #D09A72 → #A06848 → #744030 → #3E1C10
- `g-amygdala` — deep warm: #C88C6A → #9A5C40 → #6C3428 → #381410

**Texture layer for medial SVG:**
Add the same three-tier texture approach as lateral:
- f-sulcal group: major sulci of medial surface
  - Callosal sulcus (between corpus callosum and cingulate)
  - Cingulate sulcus (above cingulate gyrus)
  - Parieto-occipital sulcus (boundary on medial surface)
  - Calcarine sulcus (horizontal fissure in occipital medial, landmark for V1)
  - Subparietal sulcus, collateral sulcus, rhinal sulcus
- f-gyrus group: medial gyral highlights
- f-cortex overlay: same fractal noise approach as lateral

**Transforms (exploded-diagram separation — small gaps between structures):**
- medial_frontal: translate(-8, -4)
- cingulate_gyrus: translate(0, -6)
- corpus_callosum: translate(0, 0) — anchor piece, no transform
- thalamus: translate(4, 2)
- hypothalamus: translate(4, 4)
- mamillary_bodies: translate(4, 6)
- fornix: translate(0, -2)
- hippocampus: translate(-6, 4)
- amygdala: translate(-8, 2)
- occipital_medial: translate(10, -4)
- cerebellum_medial: translate(8, 8)
- brainstem_medial: translate(2, 8)

**Quality bar for Chunk 1A:**
- The medial SVG should look as realistic as the lateral SVG — same tissue colors, same
  depth, same sulci treatment. Do not draw simple colored blobs. Apply gradients, sulci
  strokes with f-sulcal filter, gyri highlights with f-gyrus filter, and the f-cortex
  fractal noise overlay on the full medial silhouette.
- The corpus callosum must visually read as white matter (cream/ivory) distinctly
  different from gray matter cortex.
- The fornix should be a recognizable arch — thin, white-matter colored, anatomically
  positioned curving from hippocampus up and forward to mamillary bodies.
- Mamillary bodies must be small but clearly labeled and clickable — they are one of the
  highest-yield structures for the EPPP (Korsakoff syndrome).
- All 12 regions must be `<g>` elements with `data-region`, `data-label`, `id`, and
  `class="brain-region"` — identical structure to lateral regions.
- The backdrop ellipse and warm ambient should be added for the medial SVG too.

**Do NOT:**
- Do not create a new CSS file. All styles go in the existing `<style>` block.
- Do not add a new `<script>` block. The medial SVG is pure markup — the existing JS
  will handle it once the view-switcher is added in Chunk 1D.
- Do not simplify the structures. Draw all 12. If a structure seems too small to matter
  (mamillary bodies, fornix), draw it anyway — it is high-yield EPPP content.

---

### CHUNK 1B — Medial Region Info Objects (brain_data.js)

**Files to read before starting:**
- `data/brain_data.js` lines 1–80 (the `regions` object) — understand exact schema
  of existing info objects to match format exactly

**Files to write:**
- `data/brain_data.js` — add 12 new entries to `window.__BRAIN_DATA.regions`

**Schema (match exactly):**
```javascript
"region_id": {
  "label": "Display Name",
  "info": {
    "ba": "Brodmann areas or 'N/A (subcortical)'",
    "functions": ["function 1", "function 2", ...],   // 4-6 items
    "syndromes": ["Syndrome: description", ...],       // 3-5 items
    "vascular": "Artery name(s)"
  }
}
```

**12 objects to write — full content:**

```
corpus_callosum:
  label: "Corpus Callosum"
  ba: "N/A (white matter commissure)"
  functions:
    - "Interhemispheric transfer of sensory, motor, and cognitive information"
    - "Coordinates bilateral motor movements"
    - "Enables language areas (left) to process visual input from right hemisphere"
    - "Genu connects prefrontal regions; body connects motor/sensory; splenium connects visual areas"
  syndromes:
    - "Split-brain syndrome: surgical callosotomy severs hemispheric communication; left hand does not know what right hand is doing; left hemisphere cannot name objects held in left hand (right hemisphere)"
    - "Alien hand syndrome: callosal damage (often genu) causes one hand to act autonomously, opposing the other hand's intentional movements"
    - "Pure alexia without agraphia: splenial + left occipital damage; written words seen by right occipital cannot reach left language areas; patient can write but cannot read what they wrote"
    - "Callosal disconnection: anterior lesion causes ideomotor apraxia in left hand (cannot follow verbal commands with left hand); posterior lesion causes tactile anomia (cannot name object in left hand)"
  vascular: "Anterior cerebral artery (genu + body) · Posterior cerebral artery (splenium)"

cingulate_gyrus:
  label: "Cingulate Gyrus"
  ba: "BA 24 (anterior), BA 23 (posterior), BA 31, BA 32"
  functions:
    - "Anterior cingulate: conflict monitoring, error detection, pain affect, emotional processing"
    - "Posterior cingulate: spatial orientation, memory retrieval, self-referential processing"
    - "Part of the Papez circuit — processes emotional valence"
    - "Voluntary movement initiation (supplementary motor area adjacency)"
    - "Regulates autonomic nervous system responses to emotional stimuli"
  syndromes:
    - "Abulia / akinetic mutism: bilateral anterior cingulate damage produces profound reduction in spontaneous movement, speech, and emotional expression; patient appears awake but does not initiate behavior"
    - "Anterior cingulate syndrome: impaired response inhibition, poor performance on Stroop task, perseveration; often confused with frontal lobe syndrome"
    - "Pain asymbolia: damage disconnects pain sensation from its affective/motivational component; patient feels pain but is not distressed by it"
    - "Cingulotomy (surgical): historically used for intractable depression and OCD; reduces emotional suffering without eliminating sensation"
  vascular: "Anterior cerebral artery (anterior) · Posterior cerebral artery (posterior)"

thalamus:
  label: "Thalamus"
  ba: "N/A (subcortical diencephalon)"
  functions:
    - "Relay station for almost all sensory information en route to cortex (except olfaction)"
    - "VPL nucleus: relays somatosensory (touch, proprioception, pain) to somatosensory cortex"
    - "LGN (lateral geniculate nucleus): relays visual information to V1"
    - "MGN (medial geniculate nucleus): relays auditory information to auditory cortex"
    - "Anterior nucleus: part of Papez circuit, relays from mamillary bodies to cingulate"
    - "Mediodorsal nucleus: connects prefrontal cortex; involved in executive function and emotion"
    - "Pulvinar: attentional gating of visual and multimodal information"
  syndromes:
    - "Thalamic syndrome (Dejerine-Roussy): thalamic infarct causes contralateral hemibody pain and dysesthesia (central post-stroke pain); initially sensory loss, then chronic burning pain as thalamus recovers partially"
    - "Thalamic aphasia: dominant (left) thalamic lesion causes fluent aphasia with jargon, intact repetition, and hypophonia; differs from cortical aphasia by preserved repetition and fluctuating severity"
    - "Korsakoff amnesia: mediodorsal thalamic nucleus destruction (thiamine deficiency) causes anterograde and retrograde amnesia, confabulation; paired with mamillary body damage"
    - "Fatal familial insomnia: prion disease specifically targeting thalamic nuclei; progressive inability to sleep, autonomic dysfunction, dementia"
    - "Thalamic neglect: right thalamic lesion can cause contralateral neglect mimicking parietal neglect"
  vascular: "Posterior cerebral artery (thalamoperforating branches) · Posterior communicating artery"

hypothalamus:
  label: "Hypothalamus"
  ba: "N/A (subcortical diencephalon)"
  functions:
    - "Autonomic nervous system regulation (sympathetic and parasympathetic control)"
    - "Endocrine system master regulator (releases/inhibits pituitary hormones)"
    - "Hunger and satiety (lateral hypothalamus = hunger; ventromedial = satiety)"
    - "Circadian rhythm regulation (suprachiasmatic nucleus responds to light)"
    - "Temperature regulation (thermostat of the body)"
    - "Fluid balance and thirst (osmoreceptors trigger ADH release)"
    - "Emotional expression (rage, fear responses via connections to amygdala)"
  syndromes:
    - "Klüver-Bucy syndrome (partial): hypothalamic + bilateral temporal damage contributes to hyperphagia, hypersexuality, emotional blunting; full syndrome also requires amygdala bilateral damage"
    - "Lateral hypothalamic lesion: loss of hunger drive (aphagia) → starvation if untreated; 'lesion here = lose the desire to eat'"
    - "Ventromedial hypothalamic lesion: loss of satiety signal → hyperphagia, obesity; 'lesion here = can't stop eating'"
    - "Diabetes insipidus: damage to supraoptic or paraventricular nuclei disrupts ADH production → excessive thirst and urination (not to be confused with diabetes mellitus)"
    - "Wernicke's encephalopathy: thiamine deficiency damages hypothalamus, mamillary bodies, and periaqueductal gray; triad of confusion, ataxia, ophthalmoplegia"
  vascular: "Posterior communicating artery · Anterior cerebral artery (preoptic area)"

mamillary_bodies:
  label: "Mamillary Bodies"
  ba: "N/A (subcortical — posterior hypothalamus)"
  functions:
    - "Critical relay in Papez circuit: receive input from hippocampus via fornix"
    - "Project to anterior thalamus via mamillothalamic tract"
    - "Involved in spatial memory and navigation (with hippocampus)"
    - "Recollective (explicit) memory encoding"
  syndromes:
    - "Korsakoff syndrome: bilateral mamillary body destruction from thiamine (vitamin B1) deficiency (chronic alcoholism). Severe anterograde amnesia, retrograde amnesia, confabulation (patient invents plausible but false memories to fill gaps). Unlike hippocampal amnesia, patients do not show distress at memory loss — they confabulate instead."
    - "Wernicke-Korsakoff: Wernicke's encephalopathy (acute: confusion + ataxia + ophthalmoplegia) that progresses to Korsakoff's psychosis (chronic: amnesia + confabulation) if thiamine not given immediately"
    - "Mamillary body atrophy on MRI: pathognomonic finding in chronic alcohol-related brain damage; visible on standard T1 imaging as bilateral volume loss"
  vascular: "Posterior cerebral artery · Posterior communicating artery (mamillary branches)"

hippocampus:
  label: "Hippocampus"
  ba: "N/A (archicortex — 3-layer allocortex)"
  functions:
    - "Encoding new declarative (explicit) memories — both episodic and semantic"
    - "Memory consolidation: transfers information from short-term to long-term storage"
    - "Spatial navigation and cognitive mapping (place cells)"
    - "Pattern separation: distinguishes similar memories from each other"
    - "Part of Papez circuit: projects to mamillary bodies via fornix"
    - "Context-dependent memory recall"
  syndromes:
    - "Bilateral hippocampal amnesia (H.M. syndrome): complete anterograde amnesia for declarative memory; cannot form any new long-term explicit memories; intelligence, language, and procedural memory (cerebellum/striatum) preserved; remote long-term memories largely intact; unable to recognize people met after surgery"
    - "Unilateral hippocampal lesion: left = verbal memory impairment; right = nonverbal/spatial memory impairment; neither causes severe amnesia alone"
    - "Transient global amnesia: sudden-onset dense anterograde amnesia lasting hours, then resolving completely; likely vascular etiology; patient repeatedly asks the same questions"
    - "Hippocampal sclerosis: most common cause of temporal lobe epilepsy; mesial temporal sclerosis on MRI; surgical resection effective but risks amnesia if contralateral hippocampus is abnormal"
    - "Alzheimer's disease: hippocampal atrophy is the earliest and most prominent structural change; amyloid plaques and tau tangles first appear in entorhinal cortex then hippocampus; anterograde memory failure is cardinal early symptom"
  vascular: "Posterior cerebral artery (hippocampal branches) · Anterior choroidal artery"

amygdala:
  label: "Amygdala"
  ba: "N/A (subcortical — telencephalic limbic structure)"
  functions:
    - "Fear conditioning and threat detection (basolateral complex)"
    - "Emotional memory consolidation — enhances hippocampal encoding of emotionally arousing events (epinephrine/norepinephrine gate)"
    - "Social cognition: reading emotional facial expressions, especially fear"
    - "Attaches emotional significance to stimuli (stimulus-affect associations)"
    - "Mediates conditioned fear responses (CS→fear via LeDoux's 'low road')"
    - "Modulates autonomic responses to threats (heart rate, cortisol)"
  syndromes:
    - "Klüver-Bucy syndrome: bilateral amygdala + anterior temporal damage; psychic blindness (visual agnosia), hyperorality (mouths objects), hypersexuality, placidity (loss of fear and aggression), hypermetamorphosis (compelled to attend to all stimuli). Seen after bilateral temporal lobectomy, herpes simplex encephalitis (predilection for temporal lobes), severe Alzheimer's"
    - "Urbach-Wiethe disease: rare bilateral amygdala calcification from lipoid proteinosis; patient cannot experience fear, cannot recognize fearful faces; provides natural human model of amygdala function"
    - "PTSD pathophysiology: hyperactive amygdala with diminished prefrontal inhibition; exaggerated fear responses to trauma cues; reduced hippocampal volume also seen"
    - "Anxiety disorders: amygdala hyperreactivity implicated in generalized anxiety, social phobia, specific phobias; anxiolytics (benzodiazepines) suppress amygdala activity"
  vascular: "Anterior choroidal artery · Middle cerebral artery (anterior temporal branches)"

fornix:
  label: "Fornix"
  ba: "N/A (white matter tract)"
  functions:
    - "Primary output pathway of the hippocampus"
    - "Carries hippocampal projections to mamillary bodies (postcommissural fornix)"
    - "Carries hippocampal projections to septal nuclei and hypothalamus (precommissural)"
    - "Essential link in Papez circuit: hippocampus → fornix → mamillary bodies"
    - "Bidirectional: also carries input from septal nuclei back to hippocampus"
  syndromes:
    - "Fornix transection: bilateral surgical or traumatic fornix damage produces amnesia resembling hippocampal amnesia — severe anterograde amnesia with retrograde gradient; often seen with colloid cysts of third ventricle compressing fornix"
    - "Colloid cyst: benign third-ventricle cyst that compresses fornix; causes episodic memory loss, sudden-onset headaches, and (rarely) sudden death from acute hydrocephalus"
    - "Wernicke-Korsakoff: fornix degeneration contributes to amnestic syndrome alongside mamillary body and thalamic damage"
  vascular: "Anterior cerebral artery · Posterior communicating artery"

cingulate_gyrus: (see above — already specified)

medial_frontal:
  label: "Medial Frontal Cortex"
  ba: "BA 6 (supplementary motor area), BA 8 (frontal eye fields medial), BA 32/24 (anterior cingulate overlap), BA 10 (frontopolar)"
  functions:
    - "Supplementary motor area (SMA): planning and initiating voluntary movements, especially bimanual coordination"
    - "Mediates internally-generated (self-initiated) movements vs. externally-triggered"
    - "Bladder and bowel voluntary control center"
    - "Attention and task switching (anterior cingulate adjacency)"
    - "Represents the leg and foot in the motor/sensory homunculus (medial surface)"
  syndromes:
    - "Anterior cerebral artery stroke: leg > arm weakness and sensory loss (because leg representation is on medial surface, ACA territory); arm/face relatively spared (MCA territory); urinary incontinence common"
    - "Abulia: medial frontal + anterior cingulate damage produces profound apathy, poverty of speech and movement, loss of initiation; patient appears depressed but does not report subjective distress; distinct from depression"
    - "Alien hand syndrome (frontal type): SMA + corpus callosum damage causes one hand to act against the patient's will; typically non-dominant hand"
    - "SMA syndrome: temporary mutism and contralateral hemiparesis after SMA resection (e.g., tumor removal); typically resolves within weeks as ipsilateral SMA compensates"
  vascular: "Anterior cerebral artery (ACA)"

occipital_medial:
  label: "Medial Occipital (Cuneus / Precuneus)"
  ba: "BA 17 (primary visual cortex V1, calcarine sulcus), BA 18, BA 7 (precuneus)"
  functions:
    - "Primary visual cortex (V1) receives input from LGN along calcarine sulcus"
    - "Upper visual field represented in cuneus (above calcarine)"
    - "Lower visual field represented in lingual gyrus (below calcarine)"
    - "Precuneus: visuospatial imagery, episodic memory retrieval, self-referential processing"
    - "Highly activated during visual imagination and mental imagery"
  syndromes:
    - "Cortical blindness: bilateral V1 destruction → complete loss of conscious vision despite intact eyes and optic nerves; pupillary light reflex preserved (pretectal pathway intact); Anton's syndrome = patient denies blindness and confabulates visual experiences"
    - "Homonymous hemianopia: unilateral V1 lesion → loss of contralateral visual field in both eyes; macular sparing common (dual blood supply from MCA and PCA at occipital pole)"
    - "Superior quadrantanopia (pie-in-the-sky): lesion of lower bank of calcarine sulcus (cuneus / upper field representation); caused by temporal lobe lesions affecting inferior optic radiations (Meyer's loop)"
    - "Precuneus atrophy: prominent in Alzheimer's disease and posterior cortical atrophy; causes visuospatial deficits and dressing apraxia"
  vascular: "Posterior cerebral artery (calcarine artery)"

cerebellum_medial:
  label: "Cerebellum (Medial View)"
  ba: "N/A (cerebellar cortex)"
  functions:
    - "Vermis (midline): axial/truncal coordination, gait, postural stability"
    - "Flocculonodular lobe: vestibular coordination, eye movements, balance"
    - "Lateral hemispheres (not visible in medial view): limb coordination, fine motor"
    - "Timing and sequencing of movements (internal clock)"
    - "Motor learning and adaptation (long-term potentiation in Purkinje cells)"
  syndromes:
    - "Midline (vermis) lesion: truncal and gait ataxia; wide-based drunken gait; truncal titubation (rhythmic swaying); nystagmus; most common with medulloblastoma in children (midline cerebellum)"
    - "Flocculonodular lesion: vestibular ataxia, severe imbalance without limb ataxia; cannot stand or walk (truncal) but finger-to-nose intact when seated"
    - "All cerebellar deficits are IPSILATERAL: cerebellar pathways decussate twice (double cross) so lesion side = deficit side — opposite of cortical lesions"
  vascular: "Posterior inferior cerebellar artery (PICA) — vermis and inferior hemisphere"

brainstem_medial:
  label: "Brainstem"
  ba: "N/A (contains CN nuclei III–XII, reticular formation, ascending/descending tracts)"
  functions: (same as lateral view brainstem — reuse existing info object or cross-reference)
```

**Quality bar:**
- Every syndrome entry must be clinically specific and EPPP-relevant.
- Vascular fields must be accurate — students will rely on these for vascular questions.
- Functions should be mechanistic, not just definitional.

---

### CHUNK 1C — Medial Questions (brain_data.js)

**Files to read before starting:**
- `data/brain_data.js` full file — understand existing 25 questions for format, quality
  bar, and to avoid content duplication

**Files to write:**
- `data/brain_data.js` — append ~25 new questions to the `questions[]` array

**Question format (exact schema):**
```javascript
// Type 1: deficit_to_location
{
  "id": "BRAIN-XXX",
  "type": "deficit_to_location",
  "category": "memory|motor|aphasia|visual|sensory|executive|vascular",
  "question": "Clinical scenario or symptom description. Which region is most likely damaged?",
  "target_region": "region_id",
  "distractor_regions": ["id1", "id2", "id3"],  // 3 distractors
  "explanation": "Mechanistic explanation citing anatomy, physiology, and clinical relevance."
}

// Type 2: location_to_deficit
{
  "id": "BRAIN-XXX",
  "type": "location_to_deficit",
  "category": "...",
  "question": "Damage to the highlighted region would most likely produce:",
  "highlighted_region": "region_id",
  "options": ["correct answer", "distractor 1", "distractor 2", "distractor 3"],
  "correct_option_index": 0,
  "explanation": "..."
}

// Type 3: case_to_location
{
  "id": "BRAIN-XXX",
  "type": "case_to_location",
  "category": "...",
  "question": "Multi-sentence clinical vignette. Which region is primarily implicated?",
  "target_region": "region_id",
  "distractor_regions": ["id1", "id2", "id3"],
  "explanation": "..."
}
```

**25 questions to author (mandatory topics — all high EPPP yield):**

1. Corpus callosum — split-brain: left hand can't name object held in right hand
2. Corpus callosum — pure alexia without agraphia (splenial + left occipital)
3. Corpus callosum — alien hand syndrome
4. Cingulate — abulia case vignette (profound apathy, no spontaneous movement/speech)
5. Cingulate — anterior cingulate location_to_deficit (options include perseveration, aphasia, amnesia, motor weakness)
6. Thalamus — Dejerine-Roussy (central post-stroke pain, burning dysesthesia)
7. Thalamus — thalamic aphasia (fluent, intact repetition, hypophonia)
8. Thalamus — Korsakoff: mediodorsal nucleus damage role
9. Hypothalamus — lateral lesion: aphagia/starvation
10. Hypothalamus — ventromedial lesion: hyperphagia/obesity
11. Hypothalamus — location_to_deficit: ANS regulation, circadian rhythm, thermoregulation
12. Mamillary bodies — Korsakoff classic case (alcoholic, confabulates, thiamine deficiency)
13. Mamillary bodies — Wernicke-Korsakoff progression case vignette
14. Hippocampus — H.M. case (bilateral resection, anterograde amnesia, IQ preserved)
15. Hippocampus — location_to_deficit: declarative memory encoding
16. Hippocampus — Alzheimer's earliest structural change
17. Amygdala — Klüver-Bucy case (herpes encephalitis, hyperorality, placidity)
18. Amygdala — fear conditioning: patient cannot be conditioned to fear CS (Urbach-Wiethe type)
19. Amygdala — location_to_deficit options: fear/emotional learning vs aphasia vs motor vs visual
20. Fornix — colloid cyst compression: episodic memory loss
21. Fornix — Papez circuit: which structure does fornix connect hippocampus to?
22. Medial frontal — ACA stroke (leg > arm weakness, incontinence)
23. Medial frontal — SMA: internally-generated vs externally-triggered movements
24. Occipital medial — cortical blindness with Anton's syndrome (denies blindness)
25. Occipital medial / cuneus — superior quadrantanopia ("pie in the sky") — which bank of calcarine

**Distractor selection rules:**
- Distractors must be plausible — always include at least 1 anatomically adjacent region
- For memory questions: always include frontal_lobe as a distractor (executive memory confound)
- For vascular questions: always include appropriate vascular territory neighbors
- Never make distractors obviously wrong

**Quality bar:**
- Explanations must be 3–5 sentences minimum, mechanistic, EPPP-specific
- Case vignettes must be clinically realistic (age, presentation, context)
- Questions must not duplicate any existing question in spirit or content
- All medial-view regions (corpus_callosum, cingulate_gyrus, thalamus, hypothalamus,
  mamillary_bodies, hippocampus, amygdala, fornix, medial_frontal, occipital_medial)
  must appear as target_region at least once

---

### CHUNK 1D — View Switcher (Lateral | Medial tabs)

**Files to read before starting:**
- `brain-exercise.html` lines 1–130 (CSS section) — understand existing CSS variables
- `brain-exercise.html` lines 474–540 (nav + screen structure) — understand layout
- `brain-exercise.html` lines 1050–1300 (JavaScript section) — understand routing logic,
  renderQuestion(), initStudy(), URL param parsing

**Files to write:**
- `brain-exercise.html` — CSS + HTML + JS modifications only (NOT the SVG sections)
- `brain-settings.html` — add medial category support and view param to start URL

**What to build:**

**HTML additions:**
- Tab bar (`<div class="view-tabs" id="view-tabs">`) with two buttons:
  `[🧠 Lateral View]` and `[✦ Medial View]`
  Positioned above `.brain-container` inside `#screen-quiz`
  Hidden in results/review screens
- Both `.brain-container` divs (`#brain-container-lateral`, `#brain-container-medial`)
  are present in DOM; `display:none` toggled by JS

**CSS additions:**
```css
.view-tabs { display:flex; gap:8px; width:100%; max-width:700px; margin-bottom:12px; }
.view-tab {
  flex:1; background:rgba(255,255,255,0.04); border:1px solid var(--border);
  border-radius:10px; padding:9px; font-size:12px; font-weight:600;
  color:var(--text3); cursor:pointer; transition:all 0.2s;
}
.view-tab.active {
  background:rgba(244,63,94,0.1); border-color:var(--border-rose);
  color:var(--rose-light);
}
.view-tab:hover:not(.active) { border-color:rgba(244,63,94,0.2); color:var(--text2); }
```

**JS additions:**
- `let CURRENT_VIEW = params.get('view') || 'lateral'` — persists across questions
- `function switchView(view)` — toggles container visibility, updates tab active state,
  re-renders current question on new SVG
- Tab buttons call `switchView('lateral')` and `switchView('medial')`
- `renderQuestion(q)` must check `CURRENT_VIEW` and target the correct SVG's `<g>` elements
- `initStudy()` must wire up click handlers on both SVGs
- URL param `?view=medial` initializes medial view, starts medial questions only

**Settings page additions:**
- The category filter chips do not change (same 7 categories)
- The "Start Session" URL gains `&view=lateral` or `&view=medial` parameter
- Add a View selector in settings: two buttons `[Lateral]` `[Medial]` (same style as
  count buttons) — default Lateral
- The "Explore Brain Map" button links to `brain-exercise.html?mode=study&view=lateral`
  and a new "Explore Medial" button links to `?mode=study&view=medial`

**Medial category filter:**
- The medial question pool adds questions tagged to existing categories (memory, vascular,
  motor, etc.) so no new category chips are needed
- Filter logic already works by matching `q.category` — no change needed

---

## PHASE 2 — Three.js 3D Explorer

### CHUNK 2A — Three.js Scene Scaffold

**Files to read before starting:**
- `brain-exercise.html` lines 1–50 (head, CSS variables) — match color palette exactly
- `brain-exercise.html` lines 195–220 (brain-container CSS) — understand layout context
- `brain-exercise.html` lines 1050–1100 (URL param parsing, IS_STUDY logic) — understand
  how study mode is detected and how to add 3D mode routing

**Files to write:**
- New file: `brain-3d.js` — all Three.js code lives here, imported as `<script>` module
- `brain-exercise.html` — add `<script type="module" src="brain-3d.js">` in head,
  add `#brain-container-3d` div (hidden unless `view=3d`), add Three.js CDN import map

**Three.js setup:**
```html
<!-- Add to <head> in brain-exercise.html -->
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/"
  }
}
</script>
```

**Scene configuration:**
```javascript
// brain-3d.js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

// Camera — perspective, positioned to see full brain
const camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100);
camera.position.set(0, 0.5, 4.5);

// Orbit controls — damped, constrained
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 2.5;
controls.maxDistance = 8;
controls.enablePan = false;  // no panning — keep brain centered
```

**Lighting (must match SVG warm-tissue aesthetic):**
```javascript
// Warm key light from upper-left (matches SVG light source direction)
const keyLight = new THREE.DirectionalLight(0xFFE8D0, 2.8);
keyLight.position.set(-3, 4, 3);

// Cool fill from right (prevents total black in shadow)
const fillLight = new THREE.DirectionalLight(0xD0E0FF, 0.6);
fillLight.position.set(4, 1, -2);

// Rim light from behind-right (adds depth separation)
const rimLight = new THREE.DirectionalLight(0xFFD0C0, 0.9);
rimLight.position.set(2, -1, -4);

// Ambient (base illumination, warm)
const ambient = new THREE.AmbientLight(0xC8906A, 0.4);
```

**Brain mesh approach (procedural — no GLTF needed):**
Build the hemisphere from a modified SphereGeometry using vertex displacement:
```javascript
const geo = new THREE.SphereGeometry(1.4, 128, 96);
// Displace vertices to approximate brain shape:
// - Flatten bottom slightly (inferior surface)
// - Elongate anterior-posterior axis (brain is egg-shaped)
// - Add gyrus-like displacement using sine-wave combinations
// - Cut hemisphere: vertices with z < -0.1 (medial face) set to flat
const pos = geo.attributes.position;
for (let i = 0; i < pos.count; i++) {
  let x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
  // Elongate AP axis
  z *= 1.3;
  // Flatten inferior
  if (y < 0) y *= 0.7;
  // Gyrus displacement — multiple frequency sine waves
  const r = Math.sqrt(x*x + y*y + z*z);
  const disp = 0.04 * Math.sin(x*8) * Math.sin(y*7) * Math.sin(z*6)
             + 0.025 * Math.sin(x*14) * Math.sin(y*13);
  // Apply displacement along normal direction
  ...
}
```

**Material (MeshPhysicalMaterial for realism):**
```javascript
const brainMaterial = new THREE.MeshPhysicalMaterial({
  color: new THREE.Color(0xC87858),      // warm pinkish-tan base
  roughness: 0.72,                        // brain surface is matte-satin
  metalness: 0.0,
  transmission: 0.0,
  thickness: 0.8,
  clearcoat: 0.12,                        // pial membrane wet sheen
  clearcoatRoughness: 0.4,
  subsurfaceLightingIntensity: 0.3,       // approximate subsurface scatter
});
```

**Deliverable for 2A:** A single brain hemisphere mesh visible in the browser that
rotates smoothly with mouse drag, correctly lit with warm tissue colors, integrated into
the existing `brain-exercise.html` when `?mode=study&view=3d`.

---

### CHUNK 2B — Cortical Region Meshes + Click Detection

**Goal:** Replace single-mesh brain with 11 separate meshes (matching lateral SVG regions).
Raycasting on click highlights region; info panel uses existing `brain_data.js` data.

Build each region as a sub-mesh created from the master hemisphere geometry using
zone-based vertex selection:
- Divide hemisphere into anatomical zones by angular position
- Frontal: anterior 40% of AP axis, above Sylvian plane
- Parietal: middle 30%, superior
- Temporal: middle 50%, inferior to Sylvian plane
- Occipital: posterior 30%
- Etc.

Use `THREE.Raycaster` for click detection. Hover: emissive color pulse.
Selected: `OutlinePass` from Three.js postprocessing (gold outline, 2px).

---

### CHUNK 2C — Subcortical Structure Meshes (Glass Brain)

13 subcortical structures built from Three.js primitives:
- Hippocampus: `TorusGeometry` bent into J-shape
- Amygdala: `SphereGeometry` (small, 0.18 radius)
- Thalamus: `SphereGeometry` flattened (0.30 × 0.24 × 0.20)
- Caudate: `TorusGeometry` (long C-shape)
- Putamen: `SphereGeometry` (0.22 radius, lateral to caudate)
- Globus pallidus: `SphereGeometry` (0.14 radius, medial to putamen)
- Substantia nigra: `CylinderGeometry` (thin, dark pigmented)
- Corpus callosum: `TorusGeometry` arching (large, white material)
- Fornix: `TubeGeometry` along CatmullRomCurve3 waypoints
- Mamillary bodies: 2× small `SphereGeometry`
- Internal capsule: `BoxGeometry` tapered
- Hypothalamus: `SphereGeometry` (small, 0.14)
- Amygdala (bilateral): mirror of above

All hidden (`visible: false`) by default. Glass brain toggle reveals them.

---

### CHUNK 2D — Glass Brain Toggle

CSS-driven opacity animation on cortical meshes (`MeshPhysicalMaterial.opacity`).
Tween from opacity 1.0 → 0.18 over 600ms. Subcortical meshes fade in simultaneously.
Toggle button in 3D explorer UI.

---

### CHUNK 2E — Cross-Section Slider

Three.js `clippingPlanes` on all meshes. A `THREE.Plane` object moves along the
selected axis (axial/coronal/sagittal). A colored disc (`CircleGeometry`) renders at
the cut face showing internal structure colors. Three mode buttons select axis.
Slider input (range 0–100) maps to plane position.

---

## PHASE 3 — Pathways & Lesion Simulator

### CHUNK 3A — Vascular Territory Overlay
SVG version: 3 semi-transparent filled path overlays (MCA/ACA/PCA) on lateral SVG.
3D version: 3 `MeshBasicMaterial` transparent meshes covering correct regions.
Toggle button cycles: off → MCA → ACA → PCA → all → off.

### CHUNK 3B — Pathway Animation Engine (Three.js)
Generic `Pathway` class:
```javascript
class Pathway {
  constructor(name, waypoints, color, speed, particleCount)
  // waypoints: Array of THREE.Vector3 through anatomical positions
  // Uses TubeGeometry along CatmullRomCurve3
  // Particles: Points geometry, positions updated each frame along curve parameter t
  // t advances at `speed` per second, wraps at 1.0
  animate(delta) // called each frame
  show() / hide()
}
```

### CHUNK 3C — Papez Circuit + Motor Pathway
Papez: hippocampus → fornix → mamillary bodies → anterior thalamus → cingulate → entorhinal → hippocampus
Motor: motor cortex → internal capsule → cerebral peduncle → pyramidal decussation → spinal cord (shown exiting bottom of brainstem)
UI: pathway selector panel on left side of 3D view

### CHUNK 3D — Visual, Language, Dopamine Pathways
Visual: bilateral — retina (represented as small spheres at camera near-plane) → optic chiasm → LGN → Meyer's loop (temporal) / dorsal stream (parietal) → V1. Show partial decussation at chiasm (nasal fibers cross, temporal don't) — this makes hemianopia patterns immediately intuitive.
Language: Wernicke → arcuate fasciculus → Broca → motor cortex (unidirectional animation)
Dopamine nigrostriatal: substantia nigra → striatum (caudate + putamen)

### CHUNK 3E — Lesion Simulator
"Damage Mode" toggle. Click structure → turn dark red, show deficit list, grey out
pathways passing through it. Multi-structure compound syndromes supported.
Deficit data pulled directly from `brain_data.js` region info objects.
Reset button clears all damage.

---

## PHASE 4 — Comparative Pathology

### CHUNK 4A — Pathology Overlay System
Generic overlay engine: given `{region_id, scale_factor, opacity_factor, color_shift}`,
tween mesh properties to show atrophy, lesion, or depigmentation.

Initial pathologies:
- **Alzheimer's**: hippocampus + entorhinal → shrink to 60%, darken
- **Parkinson's**: substantia nigra → desaturate (gray), shrink 40%
- **MCA stroke**: MCA territory meshes → gray, slightly swollen (+10% scale)

### CHUNK 4B — Additional Pathologies
- Huntington's: caudate atrophy → 50% scale, lateral ventricles expand (add ventricle mesh)
- Split-brain: corpus callosum → sever (visible gap), pathway animations show disconnection
- Korsakoff: mamillary bodies + mediodorsal thalamus → shrink, darken
- TBI frontal: PFC + orbitofrontal → show contusion pattern

---

## Data File Expansion Plan

```
data/brain_data.js at completion:
  regions: 23+ objects (11 lateral + 12 medial)
  questions: 50+ (25 lateral + 25 medial)
  pathways: 5 (Papez, Motor, Visual, Language, Dopamine)
  pathologies: 7 (Alzheimer's, Parkinson's, Huntington's, Korsakoff, Split-brain, MCA, TBI)
```

Pathway schema (Phase 3):
```javascript
window.__BRAIN_DATA.pathways = [
  {
    id: "papez",
    name: "Papez Circuit",
    color: "#D4A054",
    description: "Memory consolidation circuit; damage at any node → amnesia",
    nodes: [
      { region: "hippocampus", label: "Hippocampus", position: [x,y,z] },
      { region: "fornix", label: "Fornix", position: [x,y,z] },
      { region: "mamillary_bodies", label: "Mamillary Bodies", position: [x,y,z] },
      { region: "thalamus", label: "Anterior Thalamus", position: [x,y,z] },
      { region: "cingulate_gyrus", label: "Cingulate Gyrus", position: [x,y,z] },
    ],
    loop: true
  },
  ...
]
```

---

## File Size Reference (for context window planning)

| File | Current lines | Expected at completion |
|---|---|---|
| brain-exercise.html | ~1300 | ~1800 (Phase 1) |
| brain-3d.js | 0 | ~900 (Phase 2-4) |
| data/brain_data.js | ~350 | ~750 |
| brain-settings.html | ~415 | ~480 |

No file will exceed 2000 lines. Each can be read in full in a single session.

---

## Session Protocol for Each Chunk

Before starting any chunk:
1. Read ONLY the files listed under "Files to read before starting"
2. Read this roadmap section for that chunk in full
3. Do not simplify the specification to make the task easier — build what is described
4. Aim for the same visual quality as the lateral SVG (the reference bar for this project)
5. Commit after completing the chunk with a clear message referencing the chunk ID
6. Do not start the next chunk in the same session

Quality standard: every feature built must be the best possible version of that feature,
not a placeholder or simplified version. Students are preparing for a high-stakes licensure
exam. The quality of this tool directly affects their preparation. Build accordingly.
