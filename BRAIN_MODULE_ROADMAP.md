# Brain Pathology Module — Vision & Build Roadmap

## The Problem This Solves

Current EPPP prep tools teach surface localization: "click the right lobe." That is the
lowest level of neuroanatomy. Real EPPP mastery requires understanding 3D spatial
relationships, white matter circuits, subcortical structures, and why damage at a specific
point produces that exact deficit. No existing product does this well. This module fills
that gap.

---

## Current State (Completed)

- `brain-settings.html` — Category/count selector (7 categories, 4 counts)
- `brain-exercise.html` — SVG lateral-view brain, 11 clickable regions, 3 question types,
  4-screen flow (loading → quiz → results → review), study/explore mode, localStorage
  session save, realistic tissue rendering (feTurbulence texture, dense sulci/gyri, 55+
  path elements)
- `data/brain_data.js` — 25 hand-authored questions + 11 region info objects
- `index.html` — Module card added

---

## Vision: What the Finished Module Looks Like

### Study Mode (Explore)
A **Three.js 3D brain** the student can freely rotate with mouse or touch. Every structure
is a separate mesh object — click it and an info panel slides up with anatomy, function,
clinical syndromes, and vascular territory. Toggles include:

- **Glass Brain** — cortex becomes transparent, subcortical structures visible beneath
- **Vascular Territories** — MCA (pink) / ACA (blue) / PCA (purple) color overlay
- **Pathway Animations** — glowing particles travel along named circuits in real-time
- **Cross-Section Slider** — drag a plane axially/coronally/sagittally through the brain
- **Lesion Simulator** — click to "damage" any structure; deficits and interrupted
  pathways are shown immediately
- **Comparative Pathology** — toggle overlays for Alzheimer's, Parkinson's, Huntington's,
  split-brain, MCA stroke

### Quiz Mode (Exercise)
The existing SVG quiz engine extended to two views:

- **Lateral view** — current 11 regions, 25 questions (already built)
- **Medial/sagittal view** — 12+ new structures, 25+ new questions

Three question types remain: deficit→location, location→deficit, case vignette→location.

---

## Highest-Yield Structures to Add (EPPP-Specific)

### Subcortical (invisible in current lateral SVG)
| Structure | Key EPPP Content |
|---|---|
| Hippocampus (bilateral) | H.M., anterograde amnesia, declarative memory |
| Amygdala | Klüver-Bucy, fear conditioning, emotional memory |
| Caudate nucleus | Huntington's disease, OCD circuits |
| Putamen + Globus Pallidus | Basal ganglia motor loops, Parkinson's |
| Substantia nigra | Dopamine, Parkinson's (nigrostriatal pathway) |
| Thalamus | Relay station, thalamic aphasia, Korsakoff |
| Hypothalamus | Autonomic/endocrine control, Klüver-Bucy |
| Mamillary bodies | Korsakoff syndrome (thiamine deficiency) |
| Fornix | Papez circuit, connects hippocampus to mamillary bodies |
| Cingulate gyrus | Abulia, attention, pain, emotion regulation |
| Corpus callosum (genu/body/splenium) | Split-brain, disconnection syndromes, alexia |
| Arcuate fasciculus | Conduction aphasia (Broca ↔ Wernicke tract) |
| Internal capsule | Pure motor stroke, UMN lesion pattern |

### Circuits to Animate
| Circuit | Structures | Clinical Relevance |
|---|---|---|
| Papez circuit | Hippocampus → Fornix → Mamillary bodies → Anterior thalamus → Cingulate → Entorhinal → Hippocampus | Memory consolidation, Korsakoff |
| Motor pathway | Motor cortex → Internal capsule → Cerebral peduncle → Decussation → Spinal cord | UMN vs LMN lesions |
| Visual pathway | Retina → Optic chiasm → LGN → Optic radiations → V1 | Hemianopia, quadrantanopia patterns |
| Language circuit | Wernicke → Arcuate fasciculus → Broca → Motor cortex | Conduction aphasia |
| Nigrostriatal | Substantia nigra → Striatum (caudate + putamen) | Parkinson's dopamine depletion |

---

## Architecture

```
brain-settings.html
    → brain-exercise.html
          ├── ?mode=study    Three.js 3D explorer
          │     ├── glass-brain toggle
          │     ├── pathway animation overlay
          │     ├── cross-section slider
          │     ├── lesion simulator
          │     └── vascular territory toggle
          │
          └── ?mode=quiz    SVG quiz engine (existing)
                ├── view=lateral   (current, 11 regions)
                └── view=medial    (new, 12+ regions)

data/brain_data.js       — shared: regions, info, questions for all views/modes
```

---

## Chunking Plan

Each chunk is scoped to stay within a single context window. Chunks that touch large files
are split so Claude never reads + rewrites more than ~800 lines in one session.

---

### PHASE 1 — Medial View (pure SVG, same engine)
**Goal:** Double the quiz content, add all high-yield medial/subcortical structures.
No new dependencies. Ships fast.

#### Chunk 1A — Medial brain SVG drawing
**File:** `brain-exercise.html` (SVG section only)
**Task:** Draw a second inline SVG for the medial/sagittal view. 12 structures as `<g>`
elements with `data-region` attributes, same realistic tissue gradients and sulci approach.

Structures to draw (medial SVG, left hemisphere cut surface):
- Corpus callosum (genu, body, splenium — drawn as C-shape)
- Cingulate gyrus (arching above corpus callosum)
- Thalamus (oval, center)
- Hypothalamus (below thalamus)
- Mamillary bodies (small bumps on hypothalamus)
- Hippocampus (curved, medial temporal)
- Amygdala (almond, anterior to hippocampus)
- Fornix (arching white matter tract)
- Brainstem (midbrain / pons / medulla, full length)
- Cerebellum (posterior fossa, foliated)
- Medial frontal cortex (superior frontal gyrus medial surface)
- Occipital pole (cuneus / precuneus)

**Complexity:** Medium. New SVG paths only — no JS changes.

#### Chunk 1B — Medial region info objects in brain_data.js
**File:** `data/brain_data.js` (regions section only)
**Task:** Add 12 new region info objects (ba, functions, syndromes, vascular) to
`window.__BRAIN_DATA.regions` for all medial structures.
**Complexity:** Low. Data authoring only.

#### Chunk 1C — Medial questions in brain_data.js
**File:** `data/brain_data.js` (questions array only)
**Task:** Author ~25 new questions covering medial structures. All 3 types.
Priority questions:
- Papez circuit stations (hippocampus, fornix, mamillary bodies, anterior thalamus)
- Corpus callosum disconnection syndromes
- Klüver-Bucy (amygdala + temporal)
- Korsakoff mamillary body lesions
- Thalamic aphasia, thalamic syndrome
- Cingulate abulia
- Split-brain experiments
- Hippocampal bilateral damage (H.M.)
**Complexity:** Medium. Data authoring only.

#### Chunk 1D — View switcher (Lateral | Medial tabs)
**File:** `brain-exercise.html` (JS + CSS sections, NOT the SVG)
**Task:** Add view-toggle tabs above the SVG. JS switches between
`#brain-svg-lateral` and `#brain-svg-medial` with a CSS crossfade. URL param
`view=medial` sets default. Settings page gets medial-specific question filter.
**Complexity:** Low-medium. JS/CSS only.

---

### PHASE 2 — Three.js 3D Explorer
**Goal:** Replace the SVG in study/explore mode with a real 3D brain. This is the "wow."
Each chunk isolates one concern so no single session is overwhelming.

#### Chunk 2A — Three.js scene scaffold
**File:** New `brain-3d.js` + additions to `brain-exercise.html`
**Task:** Set up Three.js scene: renderer, camera (perspective), orbit controls, ambient +
directional lights (warm upper-left key light matching the SVG palette). Load or construct
a basic brain hemisphere mesh (can start with a subdivided ellipsoid displaced to
approximate brain shape — no GLTF needed initially). Render loop. Responsive resize.
Apply a custom ShaderMaterial that matches the warm tissue color palette.
**Complexity:** Medium. Three.js is well-documented.

#### Chunk 2B — Cortical region meshes + click detection
**File:** `brain-3d.js`
**Task:** Replace single mesh with 11 separate meshes matching the lateral SVG regions
(frontal, parietal, temporal, occipital, motor, sensory, PFC, Broca, Wernicke, cerebellum,
brainstem). Raycasting on click/tap. Hover highlight (emissive color). Selected region gold
outline (OutlinePass from Three.js postprocessing). Info panel integration (reuses existing
`.info-panel` CSS).
**Complexity:** Medium-high.

#### Chunk 2C — Subcortical structure meshes
**File:** `brain-3d.js`
**Task:** Add 13 subcortical structures as separate mesh objects, hidden by default,
revealed by glass-brain toggle. Use Three.js primitives (SphereGeometry, TorusGeometry,
TubeGeometry for tracts) scaled and positioned anatomically. Each structure clickable with
full info panel.
**Complexity:** Medium-high. Coordinate system setup is the main challenge.

#### Chunk 2D — Glass brain toggle
**File:** `brain-3d.js`
**Task:** Button triggers opacity animation on all cortical meshes (MeshPhysicalMaterial
with transparency). Subcortical structures fade in. Toggle back fades cortex opaque.
Smooth 600ms tween.
**Complexity:** Low-medium.

#### Chunk 2E — Cross-section slider
**File:** `brain-3d.js`
**Task:** A vertical slider (axial plane, top=superior→bottom=inferior). A
Three.js `Plane` object moves through the scene. All meshes use `clippingPlanes` array
to be cut at that plane. A 2D cross-section disc renders at the cut level showing the
internal structure colors. Three mode buttons: Axial | Coronal | Sagittal.
**Complexity:** High. Three.js clipping planes are well-supported but require careful setup.

---

### PHASE 3 — Pathways & Lesion Simulator
**Goal:** Make circuits spatial and interactive.

#### Chunk 3A — Vascular territory overlay
**File:** `brain-3d.js` (3D) + `brain-exercise.html` (SVG lateral overlay)
**Task:** Three colored semi-transparent mesh overlays for MCA/ACA/PCA territories.
In SVG mode, three translucent filled paths. Toggle button. Tooltips on hover.
**Complexity:** Low-medium.

#### Chunk 3B — Pathway animation engine
**File:** `brain-3d.js`
**Task:** Generic `animatePathway(nodes, color, speed)` function. Uses Three.js
`TubeGeometry` along a CatmullRomCurve3 path through anatomical waypoints.
Animated particles (Points geometry) travel along the tube using a shader or
per-frame position update. Speed, color, and particle density configurable per pathway.
**Complexity:** High. The animation engine itself is the hard part; adding new pathways
after is trivial.

#### Chunk 3C — Papez circuit + motor pathway animations
**File:** `brain-3d.js` (uses engine from 3B)
**Task:** Papez: 6-node circuit, looping particles, labels at each node.
Motor: cortex → decussation → spinal cord, show left-hemisphere → right-body crossing.
UI: pathway selector panel.
**Complexity:** Medium (depends on 3B).

#### Chunk 3D — Visual, language, dopamine pathway animations
**File:** `brain-3d.js`
**Task:** Visual: bilateral pathways, show partial decussation at chiasm — makes
hemianopia patterns immediately intuitive. Language: Broca ↔ Wernicke via arcuate
fasciculus. Dopamine: SN → striatum.
**Complexity:** Medium (depends on 3B).

#### Chunk 3E — Lesion simulator
**File:** `brain-3d.js`
**Task:** "Damage mode" toggle. Click any structure → it turns dark red, a deficit list
slides in, pathways passing through that structure grey out. Multiple structures can be
damaged simultaneously (compound syndromes). "Reset" clears all damage.
Shares deficit data from `brain_data.js` region info objects.
**Complexity:** Medium-high.

---

### PHASE 4 — Comparative Pathology
**Goal:** Visual pattern recognition for neurodegenerative diseases.

#### Chunk 4A — Pathology overlay system
**File:** `brain-3d.js`
**Task:** Generic overlay system: given a list of {region, opacity, colorShift}, tween
meshes to show atrophy or lesion patterns. Implement:
- **Alzheimer's**: hippocampal + entorhinal atrophy (regions shrink + darken)
- **Parkinson's**: substantia nigra depigments (loses color)
- **MCA stroke**: MCA territory infarct (grey, swollen)
**Complexity:** Medium.

#### Chunk 4B — Additional pathology overlays
**File:** `brain-3d.js`
**Task:**
- **Huntington's**: caudate atrophy, enlarged lateral ventricles
- **Split-brain**: corpus callosum absent/severed — pathway animations show disconnection
- **Korsakoff**: mamillary body lesion + thalamic lesion
- **TBI frontal**: PFC + orbitofrontal damage pattern
**Complexity:** Low (depends on 4A engine).

---

## Data Additions Required

### New questions (Phase 1)
~25 medial/subcortical questions covering all structures above.

### New region info objects (Phase 1)
12 medial structures × full info (ba, functions, syndromes, vascular).

### Pathway definitions (Phase 3)
5 pathways × {name, nodes (3D coordinates), color, description, clinical relevance}.

### Pathology definitions (Phase 4)
7 pathologies × {name, affected_regions[], description, clinical_features[]}.

---

## Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| 3D library | Three.js r165+ | Best documentation, no build step required via CDN |
| Brain mesh | Procedural (Three.js geometry) | No external assets needed, fully controllable |
| GLTF models | Optional enhancement in later phase | Avoids asset pipeline complexity |
| Quiz engine | Keep SVG | Reliable cross-device click detection, already built |
| Pathways | TubeGeometry + Points animation | Smooth, performant, no shader expertise required |
| Clipping | Three.js clippingPlanes | Native support, no postprocessing needed |
| Touch | OrbitControls (built-in touch support) | Works out of the box |

---

## Files At Completion

```
mastery-page/
├── index.html                    (modified — module card)
├── brain-settings.html           (modified — medial view option)
├── brain-exercise.html           (modified — lateral SVG + medial SVG + 3D scene mount)
├── brain-3d.js                   (new — Three.js explorer, ~800 lines)
├── data/
│   └── brain_data.js             (expanded — 50+ questions, 23+ regions, pathways, pathologies)
└── BRAIN_MODULE_ROADMAP.md       (this file)
```

---

## Session Guidance for Claude

Each chunk above is designed to be completed in a single Claude session without exceeding
context limits. Before starting any chunk:

1. Read only the files listed in that chunk's **File** field
2. Complete only the task described — do not add unrequested features
3. Commit after each chunk with a descriptive message
4. Update this file's "Current State" section when a phase is complete

The largest single files will be `brain-exercise.html` (~1500 lines at completion) and
`brain-3d.js` (~800 lines). Both stay under the Read tool's 2000-line limit per session.
