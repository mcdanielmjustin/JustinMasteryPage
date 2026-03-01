# JustinMasteryPage — Brain Pathology Module

> **EPPP mastery practice site** — clinical vignettes, ethics, This or That, Spot the Error, and an interactive 3D Brain module.
> Hosted at: [GitHub repo](https://github.com/mcdanielmjustin/JustinMasteryPage)

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Current State — 2D SVG Brain (Archived)](#2-current-state--2d-svg-brain-archived)
3. [Next Phase — Full 3D Brain Model](#3-next-phase--full-3d-brain-model)
4. [Architecture Overview](#4-architecture-overview)
5. [Phase 1 — Python Mesh Generation Pipeline](#5-phase-1--python-mesh-generation-pipeline)
6. [Phase 2 — brain-3d.js Rewrite](#6-phase-2--brain-3djs-rewrite)
7. [Phase 3 — brain-exercise.html Changes](#7-phase-3--brain-exercisehtml-changes)
8. [Phase 4 — brain_data.js Expansion](#8-phase-4--brain_datajs-expansion)
9. [Implementation Sequencing](#9-implementation-sequencing)
10. [Verification Steps](#10-verification-steps)
11. [Other Modules](#11-other-modules)

---

## 1. Project Structure

```
mastery-page/
├── index.html                        ← module grid landing page
├── brain-settings.html               ← brain quiz category/count selector
├── brain-exercise.html               ← brain quiz engine + 3D viewer (ACTIVE)
├── brain-exercise-svg-archive.html   ← 2D SVG brain (archived, do not delete)
├── brain-3d.js                       ← Three.js 3D viewer (ACTIVE — to be rewritten)
├── brain-3d-v1.js                    ← first Three.js build (ellipsoid only, keep for ref)
├── brain-settings.html               ← quiz settings page
├── generate_brain_meshes.py          ← [TO CREATE] one-time GLTF mesh generator
├── data/
│   ├── brain_data.js                 ← window.__BRAIN_DATA (regions + questions)
│   ├── brain_meshes/                 ← [TO GENERATE] one GLTF file per brain region
│   └── brain_regions_manifest.json  ← [TO GENERATE] index of GLTF paths and bounds
├── spot-exercise.html
├── spot-settings.html
├── clinical-exercise.html
├── clinical-settings.html
├── ethics-exercise.html
├── ethics-settings.html
├── thisorthat-exercise.html
├── thisorthat-settings.html
├── table-exercise.html
├── table-settings.html
├── streak-exercise.html
├── streak-settings.html
└── content/
    └── domain1-9/                    ← HTML lecture content per domain
```

### Domain codes

| Code | Domain |
|------|--------|
| PMET | domain1 — Psychological Measurement |
| LDEV | domain2 — Lifespan Development |
| CPAT | domain3 — Clinical Psychopathology |
| PTHE | domain4 — Psychological Theories |
| SOCU | domain5 — Social/Cultural Bases |
| WDEV | domain6 — Work/Organizational |
| BPSY | domain7 — Biological Bases (neuropsychology lives here) |
| CASS | domain8 — Clinical Assessment |
| PETH | domain9 — Professional Ethics |

---

## 2. Current State — 2D SVG Brain (Archived)

### Status: COMPLETE — archived as `brain-exercise-svg-archive.html`

The original brain module used a hand-crafted SVG lateral brain with 11 interactive
regions. It is complete and polished. The SVG is being replaced by the 3D model below,
but the archive is preserved for reference.

### Files (archived state)

| File | Role |
|------|------|
| `brain-exercise-svg-archive.html` | Full quiz engine + 2D SVG lateral brain |
| `brain-3d-v1.js` | First Three.js attempt (ellipsoid meshes, saved for reference) |

### SVG brain — 11 regions

| Region ID | Label |
|-----------|-------|
| `frontal_lobe` | Frontal Lobe |
| `prefrontal_cortex` | Prefrontal Cortex |
| `brocas_area` | Broca's Area |
| `motor_cortex` | Motor Cortex |
| `parietal_lobe` | Parietal Lobe |
| `somatosensory_cortex` | Somatosensory Cortex |
| `temporal_lobe` | Temporal Lobe |
| `wernickes_area` | Wernicke's Area |
| `occipital_lobe` | Occipital Lobe |
| `cerebellum` | Cerebellum |
| `brainstem` | Brainstem |

### SVG technical details (preserved for reference)

- `viewBox 0 0 520 360` — coordinate space for all paths
- 116 path elements, 55+ sulci drawn as separate paths
- 5 SVG filters: `f-sulcal` (deep groove penumbra), `f-gyrus` (warm crown glow),
  `f-cortex` (feTurbulence fractal-noise texture), `brain-shadow`, `region-glow`
- 4-stop radial gradients per region
- Subsurface scatter layer (separate `<use>` elements at reduced opacity)
- Pial vasculature drawn as fine red-orange lines
- Cerebellum folia as layered arcs
- Per-region CSS drop-shadows
- Exploded-diagram region separation via `transform="translate(x,y)"`

### Current brain_data.js (25 questions, 7 categories, 11 regions)

Questions are stored as a flat array in `window.__BRAIN_DATA.questions`.
Each question has:
```js
{
  id: "unique_id",
  category: "structure|function|deficit|pathology|vascular|syndrome|development",
  type: 1|2|3,       // 1=deficit→location, 2=location→deficit, 3=text+chips
  question: "...",
  target: "region_id",    // the brain region this question is about
  distractors: ["id",...], // for type 1/2 only
  options: ["...",],       // for type 3 chip questions
  answer: "...",           // correct answer text
  explanation: "..."
}
```

Each region object:
```js
{
  label: "Frontal Lobe",
  info: {
    ba: "BA 4, 6, ...",
    functions: ["...", "..."],
    syndromes: ["...", "..."],
    vascular: "MCA · ACA"
  }
}
```

---

## 3. Next Phase — Full 3D Brain Model

### Goal

Replace the ellipsoid-placeholder `brain-3d.js` (current active version) with a real
anatomically-accurate 3D brain built from FreeSurfer and Harvard-Oxford atlas data.
The result should be comparable to BrainFacts.org — real cortical surface geometry,
clickable anatomical regions, glass-brain transparency revealing subcortical structures.

### Why not keep the current ellipsoid brain-3d.js?

The current `brain-3d.js` (commit `77d1996`) uses sphere geometries scaled to ellipsoids.
It looks presentable but is not anatomically accurate — Broca's area is a blob, not the
pars opercularis / triangularis. For a serious EPPP tool, students need to see real sulcal
boundaries and real topography. The GLTF pipeline solves this permanently.

---

## 4. Architecture Overview

```
generate_brain_meshes.py          ← one-time Python run (setup step)
    ↓ produces
data/brain_meshes/*.gltf          ← one GLTF file per brain region
data/brain_regions_manifest.json  ← index of region → file, bounds, vertex/face counts

brain-3d.js                       ← Three.js viewer (loads GLTFs, handles interaction)
    ↑ called by
brain-exercise.html               ← quiz engine + UI (3D view, camera controls, glass toggle)
    ↑ reads
data/brain_data.js                ← region info + questions (expanded for new regions)
```

### Files to create / modify

| File | Action | Key Changes |
|------|---------|-------------|
| `generate_brain_meshes.py` | **Create** | Downloads FreeSurfer fsaverage + Harvard-Oxford atlas, exports GLTF per region |
| `data/brain_regions_manifest.json` | **Generated** | Output of script; lists available GLTF paths and bounds |
| `brain-3d.js` | **Rewrite** | GLTFLoader-based; loads real anatomy; same public API |
| `brain-exercise.html` | **Major edit** | Remove SVG block, add 3D container, camera controls, glass-brain toggle |
| `data/brain_data.js` | **Expand** | Add 15+ new region info objects, ~25 new questions |
| `brain-exercise-svg-archive.html` | **Create first** | Copy of current brain-exercise.html before changes (SVG preservation) |

---

## 5. Phase 1 — Python Mesh Generation Pipeline

**File:** `mastery-page/generate_brain_meshes.py`

### Prerequisites

```bash
pip install nilearn nibabel trimesh pygltflib numpy scipy scikit-image
```

### What the script does

1. **Cortical surfaces** — Downloads `nilearn.datasets.fetch_surf_fsaverage()` (left
   hemisphere pial surface + Desikan-Killiany `aparc` annotation). For each region group,
   extracts vertices/faces, simplifies to ≤4,000 faces, exports GLTF.

2. **Subcortical structures** — Downloads
   `nilearn.datasets.fetch_atlas_harvard_oxford('sub-maxprob-thr25-1mm')` (volumetric
   NIfTI in MNI space). Runs `skimage.measure.marching_cubes` on each labeled region.
   Registers to fsaverage RAS space via affine. Exports GLTF.

3. **Glass brain shell** — Full left hemisphere pial surface, simplified to ≤8,000
   faces, exported as `full_hemisphere.gltf`.

4. **Manifest** — Writes `data/brain_regions_manifest.json`:
   ```json
   {
     "frontal_lobe": {
       "file": "data/brain_meshes/frontal_lobe.gltf",
       "vertexCount": 1234,
       "faceCount": 2468,
       "bounds": { "min": [-10, -5, 10], "max": [60, 80, 70] }
     }
   }
   ```

### Coordinate transform

FreeSurfer RAS → Three.js:
```
[x_fs, y_fs, z_fs] → [x_fs, z_fs, -y_fs]
```
Three.js is y-up; FreeSurfer is z-up, y-anterior.

### Cortical region mapping (Desikan-Killiany parcels → region IDs)

| Region ID | Desikan-Killiany Parcels |
|-----------|--------------------------|
| `frontal_lobe` | superiorfrontal, rostralmiddlefrontal, caudalmiddlefrontal, lateralorbitofrontal, medialorbitofrontal, frontalpole |
| `prefrontal_cortex` | frontalpole, rostralmiddlefrontal, medialorbitofrontal, lateralorbitofrontal |
| `brocas_area` | parsopercularis, parstriangularis, parsorbitalis |
| `motor_cortex` | precentral |
| `parietal_lobe` | superiorparietal, inferiorparietal, supramarginal, precuneus |
| `somatosensory_cortex` | postcentral |
| `temporal_lobe` | superiortemporal, middletemporal, inferiortemporal, transversetemporal, fusiform, entorhinal, parahippocampal |
| `wernickes_area` | superiortemporal (posterior approximation — full parcel used) |
| `occipital_lobe` | lateraloccipital, cuneus, lingual, pericalcarine |
| `cingulate_gyrus` | rostralanteriorcingulate, caudalanteriorcingulate, posteriorcingulate, isthmuscingulate |
| `medial_frontal` | medialorbitofrontal, frontalpole (medial aspect approximation) |

### Subcortical region mapping (Harvard-Oxford atlas label → region ID)

| Region ID | Harvard-Oxford Label |
|-----------|----------------------|
| `thalamus` | Thalamus |
| `hippocampus` | Hippocampus |
| `amygdala` | Amygdala |
| `caudate` | Caudate |
| `putamen` | Putamen |
| `globus_pallidus` | Pallidum |
| `brainstem` | Brain-Stem |

### Cerebellum

Use `nilearn.datasets.fetch_atlas_aal()` which includes cerebellum parcels.
Combine all cerebellum labels into one mesh → `cerebellum.gltf`.

### Corpus callosum + fornix

Not in cortical surface parcellation. Options:
1. Use `nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-1mm')` or
   Jülich atlas for white matter structures.
2. **Fallback (preferred for now):** Build as procedural ellipsoid meshes in Three.js
   with anatomically-placed parameters (same as existing ellipsoid approach), so the
   region is interactive even if not MRI-derived.

---

## 6. Phase 2 — brain-3d.js Rewrite

### Public API (preserved — same contract as current brain-3d.js)

```js
window.__brain3d = {
  mount(container),          // attach canvas to DOM element
  unmount(),                 // detach and stop animation
  setCameraView(name),       // jump to preset camera position
  CAMERA_VIEWS,              // { lateral, medial, superior, inferior, anterior, posterior }
  highlightRegion(id),       // quiz mode: gold glow on one region, dim others
  dimAllRegions(exceptIds),  // quiz mode: fade all except listed
  resetRegions(),            // clear all highlight/dim state
  regionMeshes,              // array of all THREE.Mesh objects
  corticalMeshes,            // subset: cortical regions
  subcorticalMeshes,         // subset: subcortical regions
  toggleGlass(bool),         // NEW: cortex → transparent; subcortical visible
  setSubcorticalVisible(bool), // NEW: show/hide subcortical structures
}
```

**Events dispatched on `window`:**
- `brain3dReady` — all meshes loaded and ready
- `brain3dProgress` — `{ detail: { loaded, total } }` — for loading progress bar

### Loading sequence

1. Fetch `data/brain_regions_manifest.json`
2. Load `full_hemisphere.gltf` first (glass brain shell) → renders immediately
   semi-transparent while rest loads
3. Load all cortical region GLTFs in parallel (`Promise.all`)
4. Load subcortical GLTFs in parallel
5. Dispatch `brain3dReady`
6. Show progress bar during load (fire `brain3dProgress` events per file)

### Material system

| State | Material Properties |
|-------|---------------------|
| Default (cortical) | `MeshPhysicalMaterial`, region color from brain_data.js palette, `roughness:0.50`, `clearcoat:0.58`, gyral normal map |
| Glass brain shell | Same material, `transparent:true, opacity:0.08, depthWrite:false` |
| Subcortical default | Warm neutral colors, initially hidden |
| Hover | `emissive: 0xffffff, emissiveIntensity: 0.20` |
| Selected (study mode) | Gold outline (OutlinePass), `emissiveIntensity: 0.14` |
| Highlighted (quiz) | `emissive: 0xd4a054, emissiveIntensity: 0.28` + OutlinePass |
| Dimmed (quiz) | `opacity: 0.08, transparent: true, depthWrite: false` |

### Camera views (6 presets)

```js
CAMERA_VIEWS = {
  lateral:   new THREE.Vector3( 4.8,  0.5,  0.4),
  medial:    new THREE.Vector3(-3.8,  0.5,  0.4),
  superior:  new THREE.Vector3( 0.6,  5.5,  0.8),
  inferior:  new THREE.Vector3( 0.6, -5.5,  0.8),
  anterior:  new THREE.Vector3( 0.5,  0.5,  5.2),
  posterior: new THREE.Vector3( 0.5,  0.5, -5.6),
}
```
Camera target (orbit center): `(0.55, 0.05, 0.10)`
Animation: ease-out cubic, 0.72s duration.

### Preserved from current brain-3d.js

- `makeGyralNormal(512)` — canvas-generated gyral normal map (keep as-is)
- 4-light setup: key light (0xFFF8F4), fill (0xC4D8FF), rim (0x90BCFF), hemisphere
- OrbitControls settings: `minDistance:2.8, maxDistance:10, enablePan:false, dampingFactor:0.07`
- ResizeObserver for responsive canvas
- Pointer event handling: move = hover, click (if delta < 5px) = select

### Imports via importmap (add to existing)

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
```

---

## 7. Phase 3 — brain-exercise.html Changes

### Step 0: Archive first

```bash
cp brain-exercise.html brain-exercise-svg-archive.html
```

### Remove from brain-exercise.html

- Entire `<div class="brain-container" id="brain-container-lateral">` block (contains
  all 116 SVG path elements)
- All SVG-specific JS functions:
  - `renderDeficitToLocation(q)` — rewrite for 3D API
  - `renderLocationToDeficit(q)` — rewrite for 3D API
  - `handleRegionClick(regionId)` — rewrite for 3D API
  - `handleStudyRegionClick(regionId)` — rewrite for 3D API
- SVG-only CSS classes: `.brain-region`, `.svg-study-mode`, `.region-dimmed`,
  `.region-highlighted`, `.region-correct`, `.region-wrong`, `.region-selected`,
  `.study-selected`

### Add to brain-exercise.html

```html
<!-- Replace SVG container with: -->
<div id="brain-container-3d" class="brain-container-3d"></div>

<!-- Camera view presets bar -->
<div class="view-controls">
  <button class="view-preset-btn" data-view="lateral">Lateral</button>
  <button class="view-preset-btn" data-view="medial">Medial</button>
  <button class="view-preset-btn" data-view="superior">Superior</button>
  <button class="view-preset-btn" data-view="inferior">Inferior</button>
  <button class="view-preset-btn" data-view="anterior">Anterior</button>
  <button class="view-preset-btn" data-view="posterior">Posterior</button>
</div>

<!-- Glass brain toggle -->
<button id="glass-toggle">Show Inside</button>

<!-- Loading overlay (shown until brain3dReady) -->
<div id="brain-loading-overlay">
  <div class="brain-load-bar-bg">
    <div class="brain-load-bar-fill" id="brain-load-bar"></div>
  </div>
  <p>Loading brain model…</p>
</div>

<!-- Script -->
<script type="module" src="brain-3d.js"></script>
```

### Update JS routing

| Old SVG function | New 3D equivalent |
|-----------------|-------------------|
| `renderDeficitToLocation(q)` | `__brain3d.dimAllRegions([q.target, ...q.distractors])`  then `__brain3d.highlightRegion(q.target)` |
| `renderLocationToDeficit(q)` | `__brain3d.highlightRegion(q.target)` + show chip options |
| `handleSubmit()` | `__brain3d.highlightRegion(correct)` / `__brain3d.dimAllRegions([wrong])` for feedback |
| `initStudy()` | `__brain3d.resetRegions()` + enable canvas click passthrough |
| `handleStudyRegionClick(id)` | `populateInfoPanel(__BRAIN_DATA.regions[id])` |

### Wire study click events

`brain-3d.js` fires `window.__brainUI.openRegion(regionId)` when a region is clicked
in study mode. Set this up in `brain-exercise.html`:

```js
window.__brainUI = {
  openRegion(regionId) {
    populateInfoPanel(regionId);
    infoPanel.classList.add('open');
  }
};
```

### importmap additions

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170/examples/jsm/",
    ...existing entries...
  }
}
</script>
```
Add `three/addons/loaders/GLTFLoader.js` and `three/addons/loaders/DRACOLoader.js`.

---

## 8. Phase 4 — brain_data.js Expansion

### New regions to add (15 structures)

Each follows the existing schema: `{ label, info: { ba, functions[], syndromes[], vascular } }`

| Region ID | Label | Key Clinical Content |
|-----------|-------|---------------------|
| `medial_frontal` | Medial Frontal Cortex | SMA, akinetic mutism, abulia, ACA territory |
| `cingulate_gyrus` | Cingulate Gyrus | Papez circuit, pain matrix, ACC/PCC roles, Papez circuit lesions |
| `corpus_callosum` | Corpus Callosum | Interhemispheric transfer, split-brain syndromes, alien hand |
| `fornix` | Fornix | Hippocampus → mammillary body relay; Korsakoff amnesia |
| `thalamus` | Thalamus | Relay nuclei (VL, VPL, LGN, MGN, pulvinar), thalamic aphasia, thalamic pain |
| `hypothalamus` | Hypothalamus | Autonomic control, homeostasis, Klüver-Bucy (amygdala link), Wernicke's encephalopathy |
| `mammillary_bodies` | Mammillary Bodies | Papez circuit node, Korsakoff syndrome landmark |
| `hippocampus` | Hippocampus | Memory consolidation, H.M. case, bilateral damage → anterograde amnesia |
| `amygdala` | Amygdala | Fear conditioning, Klüver-Bucy, social-emotional processing |
| `caudate` | Caudate | Striatum, OCD (hyper-caudate), Huntington's (caudate atrophy) |
| `putamen` | Putamen | Direct/indirect basal ganglia pathway, Parkinson's dopamine target |
| `globus_pallidus` | Globus Pallidus | Output nucleus of basal ganglia; GPi/GPe distinction; Wilson's disease |
| `brainstem_midbrain` | Midbrain | CN III/IV, substantia nigra (Parkinson's), red nucleus, Weber's syndrome |
| `brainstem_pons` | Pons | CN V-VIII, PPRF, locked-in syndrome, central pontine myelinolysis |
| `brainstem_medulla` | Medulla | CN IX-XII, Wallenberg syndrome (lateral medullary), pyramidal decussation |

### New quiz questions to add (~25 questions)

Topics to cover:

**Thalamus**
- Q: Relay nucleus for somatosensory information → VPL (ventral posterolateral)
- Q: Thalamic stroke → contralateral hemisensory loss + possible thalamic pain
- Q: Which nucleus relays visual info → LGN (lateral geniculate nucleus)

**Hippocampus / Amnesia**
- Q: Patient HM — bilateral hippocampal removal → anterograde amnesia preserved procedural
- Q: Korsakoff syndrome — which structure most damaged → mammillary bodies (fornix lesion)
- Q: Hippocampal damage in early Alzheimer's → retrograde > anterograde temporal gradient

**Amygdala / Klüver-Bucy**
- Q: Bilateral temporal lobectomy → Klüver-Bucy (hypersexuality, placidity, hyperorality, visual agnosia)
- Q: Which structure essential for fear conditioning → amygdala (basolateral complex)
- Q: Urbach-Wiethe disease (calcified amygdala) → failure to recognize fear expressions

**Basal Ganglia**
- Q: Huntington's disease → atrophy of caudate nucleus (enlarged ventricles on MRI)
- Q: Direct pathway effect → increased movement; indirect pathway → decreased movement
- Q: OCD neuroimaging → hyperactivity in caudate (orbitofronto-striato-thalamic loop)
- Q: MPTP toxin → destroys substantia nigra pars compacta → Parkinson's symptoms

**Corpus Callosum**
- Q: Split-brain — left visual field stimulus → cannot name (right hemisphere, no verbal access)
- Q: Alien hand syndrome → corpus callosum lesion (or supplementary motor area)
- Q: Pure alexia without agraphia → left V1 + splenium of corpus callosum disconnection

**Cingulate / Papez Circuit**
- Q: Papez circuit loop → hippocampus → fornix → mammillary bodies → anterior thalamus → cingulate → hippocampus
- Q: Anterior cingulate lesion → akinetic mutism, lack of motivation, flat affect
- Q: Which structure bridges memory and emotion in Papez circuit → cingulate gyrus

**Brainstem**
- Q: Locked-in syndrome → bilateral pontine lesion (PPRF + corticospinal); eye movement preserved
- Q: Wallenberg (lateral medullary) syndrome → PICA occlusion: ipsilateral face pain/temp + contralateral body pain/temp + dysphagia + Horner's
- Q: Weber's syndrome → midbrain: CN III palsy (ipsilateral) + contralateral hemiplegia

### Question type distribution to maintain

| Type | Description | Approx % |
|------|-------------|----------|
| 1 | Deficit → location (click/select brain region) | 40% |
| 2 | Location → deficit (brain region shown, name the deficit) | 30% |
| 3 | Text stem + chip answers | 30% |

---

## 9. Implementation Sequencing

```
Step 1  Archive current brain-exercise.html
        → cp brain-exercise.html brain-exercise-svg-archive.html
        → commit: "Archive 2D SVG brain before 3D replacement"

Step 2  Write generate_brain_meshes.py
        → Create file; implement cortical surface + subcortical + glass brain pipeline
        → Output: data/brain_meshes/*.gltf + data/brain_regions_manifest.json

Step 3  Run the script, verify GLTF output
        → pip install nilearn nibabel trimesh pygltflib numpy scipy scikit-image
        → python generate_brain_meshes.py
        → Verify: ≥11 GLTF files in data/brain_meshes/, valid manifest JSON

Step 4  Rewrite brain-3d.js with GLTFLoader
        → Replace ellipsoid mesh builder with GLTF loading pipeline
        → Preserve exact same public API (window.__brain3d)
        → Add toggleGlass(), setSubcorticalVisible()
        → Add brain3dReady and brain3dProgress events

Step 5  Update brain-exercise.html
        → Remove SVG container and SVG-only JS/CSS
        → Add 3D container div, camera view buttons, glass toggle
        → Add loading overlay with progress bar
        → Update JS routing functions to use __brain3d API
        → Wire __brainUI.openRegion for study mode

Step 6  Expand brain_data.js
        → Add 15 new region info objects
        → Add ~25 new quiz questions
        → Ensure each new region in manifest has a matching entry in brain_data.js

Step 7  End-to-end browser test (see Verification Steps below)
```

---

## 10. Verification Steps

### After Step 3 (mesh generation)
- `data/brain_meshes/` contains ≥11 GLTF files including `full_hemisphere.gltf`
- `data/brain_regions_manifest.json` is valid JSON with ≥11 region entries
- Each GLTF file is <5MB uncompressed (target: <2MB per region)

### After Step 4 (brain-3d.js rewrite)
- Open browser console; `window.__brain3d` is defined
- `brain3dReady` event fires within 10 seconds on a local server
- No THREE.js errors in console

### After Step 5 (brain-exercise.html update)
- `brain-exercise.html?mode=study` — brain loads, glass brain renders semi-transparent,
  regions are clickable, info panel populates with region data
- `brain-exercise.html?categories=structure&count=10` — questions render, region
  highlighting works on 3D model, correct/wrong feedback visible
- All 6 camera view buttons animate camera to correct position
- Glass toggle: cortex goes transparent → subcortical structures visible
- Mobile (375px): canvas resizes, touch/pinch controls work (OrbitControls handles this)

### Regression — SVG archive still works
- `brain-exercise-svg-archive.html` loads correctly with 2D SVG brain
- All 11 SVG regions are clickable in study mode
- Quiz mode still functions on the archived page

---

## 11. Other Modules

These modules are complete and not affected by the 3D brain work:

| Module | Settings | Exercise | Data |
|--------|----------|----------|------|
| Spot the Error | `spot-settings.html` | `spot-exercise.html` | `data/{DOMAIN}_spot.json` |
| Clinical Vignettes | `clinical-settings.html` | `clinical-exercise.html` | `data/{DOMAIN}_vignettes.json` |
| Patient Encounter | `clinical-presentation-settings.html` | `clinical-presentation-exercise.html` | `data/{DOMAIN}_presentations.json` |
| Ethics | `ethics-settings.html` | `ethics-exercise.html` | `data/{DOMAIN}_vignettes.json` |
| This or That | `thisorthat-settings.html` | `thisorthat-exercise.html` | `data/{DOMAIN}_contrast.json` |
| Table Drill | `table-settings.html` | `table-exercise.html` | `data/{DOMAIN}_tables.json` |
| Streak | `streak-settings.html` | `streak-exercise.html` | `data/{DOMAIN}_basic.json` |

### Passage data (used by Spot the Error generator)
Extracted from `content/domain1-9/*.html` by `extract_passages.py` and
`supplement_passages.py`. Counts as of 2026-02-26:

| Domain | Passages |
|--------|----------|
| BPSY | 501 |
| CASS | 832 |
| CPAT | 378 |
| LDEV | 452 |
| PETH | 515 |
| PMET | 494 |
| PTHE | 271 |
| SOCU | 545 |
| WDEV | 273 |
| **Total** | **4,261** |

### Admin
- Admin panel: `C:\Users\mcdan\PassEPPP-website\pages\justin.html`
- PassEPPP website: `C:\Users\mcdan\PassEPPP-website\`
- JustinPipeline (PowerPoint generator): `C:\Users\mcdan\JustinPipeline\`

---

*Last updated: 2026-03-01 — 3D brain plan finalized, implementation pending Step 1.*
