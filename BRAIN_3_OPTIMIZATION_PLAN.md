# Brain Explorer 3.0 — Architecture Optimization Plan

> **Purpose:** Comprehensive optimization roadmap for `brain-3d-v3.js` and the Brain Explorer 3.0
> module. Written to be self-contained — can be picked up in a new chat session with full context.
> Reference this document before making any changes to the 3D brain engine.
>
> **Last updated:** 2026-03-03
> **Current engine:** `brain-3d-v3.js`
> **Exercise page:** `brain-exercise-30.html`
> **Settings page:** `brain-settings-30.html`

---

## Instructions for Claude — Read This First

This document is a living plan, not a rigid script. Before starting any work, read the
entire document to understand where the project stands. Then do the following:

### 1. Assess current state before touching anything
Run through this checklist at the start of every session:
- Pull latest from `origin/master` and check `git log --oneline -10` to see what has
  already been done since this document was written.
- Open `brain-3d-v3.js` and read the top comment block — it reflects the actual
  current architecture. If it contradicts this document, trust the code.
- Check if the priority table in Section 4 still reflects reality. If earlier phases
  have already been completed, cross them off mentally and start from the next uncompleted item.
- Note the `Last updated` date above. If significant time has passed, re-read the key
  source files before assuming the plan is still accurate.

### 2. Adapt and pivot freely
This plan was written at a specific moment in time. The codebase will evolve. You are
expected to deviate from this plan whenever the situation calls for it:
- If a planned approach turns out to be incompatible with how the code has evolved,
  **abandon it and find a better path**. Do not force a plan that no longer fits.
- If you discover a performance issue not listed here that is clearly more impactful
  than the next planned phase, **address it first** and note it in this document.
- If a phase turns out to be unnecessary because a different fix already solved the
  underlying problem, **skip it** and move on.
- If the Three.js version has been upgraded or a new library introduced, re-evaluate
  whether the implementation sketches in this plan still apply.

### 3. Validate as you go, not just at the end
After each sub-phase:
- Open `http://localhost:8080/brain-exercise-30.html` and confirm the brain still
  renders correctly with all features intact (split, glass, hover, quiz).
- Check the browser console for errors or new warnings.
- Verify draw call count using the Chrome DevTools Performance tab or Three.js stats.
- If something broke that you cannot quickly fix, **revert that change** and document
  what happened in this file before moving to the next item.

### 4. Update this document as work progresses
After completing any phase or sub-phase:
- Mark it complete by adding `✅ Done — [date]` next to the phase heading.
- If you pivoted from the plan, add a brief `> Note:` block under the phase explaining
  what was actually done and why it differed.
- Update the `Last updated` date at the top of this file.
- Commit this document alongside the code changes so the plan stays in sync with reality.

### 5. Non-negotiables — never compromise these
No matter how the plan evolves, these constraints are fixed:
- The cortex must retain `MeshPhysicalMaterial` with normal map + sulcal AO texture.
  This is the core quality differentiator. Do not downgrade the cortex material.
- The atlas-derived brainstem and cerebellum geometry must remain anatomically accurate.
  Format changes (JSON → GLB) are fine. Mesh simplification beyond what already exists is not.
- The quiz engine in `brain-exercise-30.html` must remain fully functional after every change.
- All toggles (split, glass, cerebellum, brainstem) must continue to work correctly.
- Visual quality must be equal to or better than the current state after every commit.
  Performance improvements that degrade appearance are not acceptable.

### 6. When in doubt, ask
If you encounter an ambiguous situation — a design decision with real tradeoffs, a change
that might affect quiz behavior, or a phase that seems to conflict with a non-negotiable —
stop and ask the user before proceeding. It is better to pause and align than to make a
consequential architectural decision unilaterally.

---

### 7. Do not take the lazy route — scrutinize this document

This plan contains several lazy compromises that were written under time pressure. Before
implementing any phase, identify whether it is the *right* solution or just the *easy* one.
The goal is a production-quality 3D brain engine, not a patched-together demo. The following
sections of this document have been identified as lazy and must be treated with skepticism:

#### ⚠️ Lazy: Phase 3B — "Throttle raycasting to 30Hz"
This is an explicit cop-out. It says so in the document: "As an interim fix before 3A."
A 30Hz raycast throttle is a band-aid that halves responsiveness while leaving the
fundamental problem (raycasting a 100k-face mesh) completely unsolved. Do not implement 3B.
Go directly to 3A, and use `three-mesh-bvh` (a proven library) instead of a proxy mesh:

```js
import { computeBoundsTree, disposeBoundsTree, acceleratedRaycast } from 'three-mesh-bvh';
THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
THREE.BufferGeometry.prototype.disposeBoundsTree = disposeBoundsTree;
THREE.Mesh.prototype.raycast = acceleratedRaycast;
// After loading cortex:
cortexMesh.geometry.computeBoundsTree();
```

`three-mesh-bvh` makes raycasting the 100k-face cortex as fast as raycasting a 1k-face mesh
with no proxy needed, no extra assets, and no loss of intersection precision. It is the
industry standard for this problem.

---

#### ⚠️ Lazy: Phase 2B — Material pooling (80 pre-compiled instances)
The plan labels material pooling as "Approach A (simpler)" and calls the right solution
"Approach B" without actually specifying it. Creating 80 pre-compiled material instances
(4 variants × 20 regions) is wasteful in both memory and load time. It also still requires
material swaps which, while not recompiling shaders, still cause draw state changes.

The correct solution is a single **custom `ShaderMaterial`** for all region overlays with
uniform arrays driving per-region state. One shader, one set of uniforms, zero recompilation
ever, and state changes that are a single `uniform1fv` call:

```glsl
// Fragment shader concept:
uniform vec3  uRegionColors[20];
uniform float uRegionEmissive[20];   // 0.0 = dim, 0.18 = default, 0.55 = hover, 0.70 = selected
uniform float uRegionOpacity[20];
attribute float aRegionIndex;         // per-vertex region ID baked at merge time

void main() {
  int idx = int(aRegionIndex);
  vec3  col = uRegionColors[idx];
  float em  = uRegionEmissive[idx];
  float op  = uRegionOpacity[idx];
  // ... PBR lighting with col and em
  gl_FragColor = vec4(col * (1.0 + em), op);
}
```

On hover, update one float in the uniform array — no material swap, no shader recompile,
no draw call change. This is how professional real-time 3D applications handle per-instance
state. It requires Phase 1B (merged geometry) to be done first, which is correct ordering.

---

#### ⚠️ Lazy: Phase 1B — InstancedMesh dismissed without full exploration
The plan says "InstancedMesh — impossible since shapes differ — skip." This dismissal is
premature. While true that InstancedMesh requires identical geometry per instance, the
plan skips over the far more powerful solution that Phase 1B should actually implement:

**The correct approach is merged geometry + vertex attribute region index + custom shader.**
Not `mergeGeometries()` with a shared generic material (as the plan sketches), but a
purpose-built architecture where:
1. All 20 region geometries are merged at load time into one `BufferGeometry`
2. A custom `aRegionIndex` vertex attribute (float) is written during merge, encoding
   which region each vertex belongs to (0–19)
3. A single `ShaderMaterial` reads `aRegionIndex` to look up that region's current
   color/state from uniform arrays (see Phase 2B above)
4. Result: 1 draw call for all 20 regions, zero per-region materials, zero per-region
   draw state, state changes are `gl.uniform1fv()` calls (microseconds)

This is the *same pattern* that Unity, Unreal, and production WebGL engines use for
rendering many objects with per-instance state. It is the ambitious solution.

---

#### ⚠️ Lazy: Priority table front-loads easy work
The priority table puts demand rendering (Easy) and 30Hz throttle (Easy, and now
eliminated) first because they are quick wins. The ambitious priority order is different:
the architectural changes (merged geometry + custom shader) should be done first because
they unlock all downstream optimizations. Easy cosmetic fixes done before the architecture
is right will require rework. Correct priority:

1. `three-mesh-bvh` for raycasting (unlocks accurate 60Hz hover with no cost)
2. Merged geometry + vertex attribute region index (architectural foundation)
3. Custom ShaderMaterial with uniform arrays (eliminates all recompilation)
4. Demand rendering with proper OrbitControls damping support (idle GPU = 0%)
5. JSON → GLB for brainstem/cerebellum + Draco/meshopt compression for all GLBs
6. KTX2/Basis Universal for all textures
7. Stencil buffer or EffectComposer OutlinePass for selection outlines

---

#### ⚠️ Lazy: Phase 4B uses Draco when meshopt is superior for Three.js
Draco requires a WASM decoder that must fully load before any mesh decompresses.
`meshoptimizer` (meshopt) is natively supported in Three.js via `MeshoptDecoder`,
compresses geometry similarly to Draco, and often achieves better compression for
non-indexed geometry. Use meshopt unless Draco is demonstrably better for a specific file.

```js
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
loader.setMeshoptDecoder(MeshoptDecoder);
```

Compress with:
```bash
npx gltf-transform optimize input.glb output.glb --compress meshopt
```

---

#### ⚠️ Lazy: Phase 5B — Texture disposal is solving the wrong problem
Region overlays use solid-color materials — they do not have unique texture maps.
Disposing textures on region hide addresses a problem that barely exists for overlays.
The real memory issue is the shared envMap and the cortex normal map being held in GPU
VRAM permanently. The right solution is not disposal but proper GPU memory budgeting:
measure actual VRAM usage with `renderer.info.memory` before and after load, and only
optimize if measurements show a real problem. Do not prematurely fix things that are not
measured bottlenecks.

---

#### The standard to hold yourself to
Before writing any implementation, ask: "Is this how a professional 3D graphics engineer
would build this, or is this how someone gets it working and moves on?" The goal is the
former. When the plan offers a simpler alternative alongside the correct one, always
implement the correct one. When the plan acknowledges a limitation or compromise, treat
that as a signal to find a better approach rather than accepting the limitation.

---

## 1. Current Architecture Overview

### What the engine does
- Loads a full-brain cortex mesh (`full_brain_optimized.glb`, 100k faces, 4MB) as the visual base
- Loads 20 per-region overlay GLBs (~72–75KB each) hidden by default, shown on hover/select
- Loads atlas-derived brainstem + cerebellum from JSON meshes + PNG textures
- Uses `MeshPhysicalMaterial` on every mesh (clearcoat, sheen, normal map, envMap)
- Raycasts on `pointermove` at 60Hz to detect hover over cortex and overlay meshes
- Split-brain via `THREE.Plane` clipping applied per-material
- Selection outlines via duplicate geometry scaled 1.04× per region

### Asset inventory
| File | Size | Faces | Notes |
|------|------|-------|-------|
| `full_brain_optimized.glb` | 4.0MB | ~100k | Decimated from 655k hires |
| `full_brain_hires.glb` | 17MB | ~655k | Fallback only |
| `cortex_normal_map.png` | 1.6MB | — | 2048×1024, baked from hires |
| `cortex_sulcal_ao.png` | 1.7MB | — | AO baked into sulcal texture |
| `cortex_ao_map.png` | 436KB | — | Separate AO pass |
| `brainstem_mesh.json` | 2.7MB | 27,531 | Harvard-Oxford atlas, marching cubes |
| `cerebellum_mesh.json` | 2.0MB | 20,313 | AAL atlas, marching cubes |
| `brainstem_texture.png` | 273KB | — | Zoned procedural texture |
| `cerebellum_texture.png` | 546KB | — | Folia band texture |
| Per-region GLBs (×20) | ~72–75KB each | ~4k each | Harvard-Oxford parcellated regions |

### Key source files
```
mastery-page/
  brain-3d-v3.js              # Main 3D engine (1,470 lines)
  brain-exercise-30.html      # Exercise/quiz UI + event wiring
  brain-settings-30.html      # Settings page with renderer/category config
  data/
    brain_data.js             # Quiz question bank
    brain_regions_manifest.json  # Region → file mapping
    brain_meshes/             # All GLB, JSON, PNG assets
  generate_parcellated_brain.py   # Generates region GLBs from Harvard-Oxford atlas
  generate_subcortical_json.py    # Generates brainstem/cerebellum JSON meshes
  optimize_cortex.py              # Decimates cortex 655k→100k faces
```

---

## 2. Performance Problems — Root Cause Analysis

### Problem 1 (CRITICAL): Draw call explosion from per-region geometry
**Current behavior:**
Each of the 20 regions is a separate `THREE.Mesh`. Each also has a duplicate outline mesh
(scaled 1.04×) attached as a child. When regions are visible, the GPU receives:
- 1 cortex draw call
- 1 brainstem draw call
- 1 cerebellum draw call
- Up to 20 region draw calls
- Up to 20 outline draw calls
= **43 draw calls per frame** at peak

**Why it matters:**
Draw calls are expensive because each one requires a CPU→GPU state switch. The GPU is
fast at rendering triangles; it's the *number of separate commands* that kills performance.

**Where in code:**
`brain-3d-v3.js` lines 496–600 (`loadRegion()`), lines 565–571 (outline mesh creation),
`brain-3d-v3.js` lines 690–701 (batch load loop).

---

### Problem 2 (CRITICAL): `MeshPhysicalMaterial` on every mesh
**Current behavior:**
Every mesh — cortex, brainstem, cerebellum, all 20 regions, all 20 outlines — uses
`MeshPhysicalMaterial` with `clearcoat`, `sheen`, `sheenColor`, `sheenRoughness`, `envMap`,
`normalMap`. This is Three.js's most expensive shader.

**Why it matters:**
The fragment shader must evaluate clearcoat BRDF + sheen BRDF + standard PBR + normal
mapping for **every pixel of every mesh every frame**. On the cortex alone (100k faces,
~500k pixels at typical viewport), this is enormous GPU work per frame.

**Where in code:**
Lines 261–275 (cortex), 297–300 (fallback cortex), 357–368 (atlas meshes),
504–521 (region overlays).

---

### Problem 3 (CRITICAL): Shader recompilation on every material state change
**Current behavior:**
On every hover, selection, toggle (glass, split, cerebellum, brainstem), the code sets
`material.needsUpdate = true`. This signals Three.js to recompile the GLSL shader for
that material. Shader compilation stalls the GPU pipeline for 20–300ms.

**Why it matters:**
The stutter you feel when hovering over a region or toggling split-brain is shader
recompilation. It blocks the main thread.

**Where in code:**
Lines 802 (`_restorePermanent`), 851, 869 (glass toggle), 915 (dimAllRegions),
1241–1242 (pointermove hover), 1004/1013/1032/1041 (clipping planes toggle).

**Root cause:**
Using material properties that require shader recompile (clipping, transparency changes)
instead of GPU uniforms that can be updated without recompile.

---

### Problem 4 (HIGH): 60Hz raycasting on 100k-face cortex
**Current behavior:**
`pointermove` fires `_rayHitRegion()` every frame. This calls:
1. `raycaster.intersectObjects(visibleOverlays, false)` — tests all visible region meshes
2. `raycaster.intersectObjects(hiresMeshes, false)` — tests the 100k-face cortex

**Why it matters:**
Raycasting against 100k faces every pointer move (60×/sec) is significant CPU work even
with Three.js's BVH acceleration. On lower-end hardware this causes frame hitching.

**Where in code:**
Lines 1251–1260 (`pointermove` handler), lines 1192–1215 (`_rayHitRegion`).

---

### Problem 5 (HIGH): JSON mesh format for brainstem/cerebellum (slow parse)
**Current behavior:**
Brainstem (2.7MB) and cerebellum (2.0MB) are loaded as raw JSON arrays of vertex
positions, normals, UVs, and face indices. JSON parsing in JS is single-threaded and slow.

**Why it matters:**
A 2.7MB JSON file takes significantly longer to parse than an equivalent binary GLB,
which is read as a typed ArrayBuffer. This extends load time noticeably.

**Where in code:**
Lines 329–489 (`_loadAtlasMesh()`), `data/brain_meshes/brainstem_mesh.json`,
`data/brain_meshes/cerebellum_mesh.json`.

---

### Problem 6 (MEDIUM): Color allocation on every pointer move
**Current behavior:**
Every `pointermove` event that hits a region executes:
```js
new THREE.Color(OVERLAY_COLORS[id] || 0x8888AA)  // line 1285
```
This allocates a new `Color` object 60×/second, creating GC pressure.

**Where in code:**
Lines 1285, 893 (`highlightRegion`), 931 (`dimAllRegions`).

---

### Problem 7 (MEDIUM): Split-brain clipping forces shader recompile per toggle
**Current behavior:**
Toggling split-brain sets `material.clippingPlanes = [_splitPlane]` (or `[]`) on every
material in the scene. Each change triggers shader recompilation for every affected material.

**Where in code:**
Lines 999–1056 (`toggleSplit()`).

---

### Problem 8 (MEDIUM): Brainstem/cerebellum JSON → should be GLB
The atlas-derived brainstem and cerebellum meshes are stored as plain JSON (vertex arrays).
They should be exported as GLB (binary GLTF) for 10× faster load times and smaller files.

---

## 3. Optimization Roadmap

Optimizations are listed in priority order. Each phase can be implemented independently.

---

### Phase 1 — Draw Call Reduction (Highest ROI)

**Goal:** Reduce from 43 draw calls/frame to ≤5.

#### 1A: Replace duplicate outline meshes with stencil buffer outlines

**Current:** Each region has a duplicate geometry child mesh scaled 1.04× as an outline.
This doubles draw calls for visible regions.

**Fix:** Use Three.js stencil buffer approach:
1. Render selected region normally into stencil buffer (stencil write)
2. Render scaled outline mesh only to pixels NOT in stencil (stencil test)
3. Only 1 outline pass for the entire scene, regardless of region count

**Implementation sketch:**
```js
// On the selected region mesh:
mesh.material.stencilWrite = true;
mesh.material.stencilRef = 1;
mesh.material.stencilFunc = THREE.AlwaysStencilFunc;

// Outline pass (single FullScreenQuad or scaled outline):
outlineMat.stencilWrite = false;
outlineMat.stencilRef = 1;
outlineMat.stencilFunc = THREE.NotEqualStencilFunc;
```

**Files to change:** `brain-3d-v3.js` lines 565–571 (remove outline mesh creation),
lines 385–398 (remove outline for permanent meshes), update selection/highlight functions.

**Expected gain:** Eliminates 20 draw calls when regions are highlighted.

---

#### 1B: Merge region overlays into a single instanced or batched mesh

**Current:** 20 separate GLB meshes, each its own draw call.

**Option A — InstancedMesh (best performance):**
All 20 regions share one geometry (impossible since shapes differ — skip).

**Option B — Merged geometry with vertex colors (recommended):**
At load time, merge all 20 region geometries into a single `BufferGeometry` using
`THREE.BufferGeometryUtils.mergeGeometries()`. Store region ID per vertex in a custom
attribute. Use a single material with a color lookup uniform (array of 20 vec3 colors).

```js
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// After all regions load:
var merged = mergeGeometries(regionGeometries, true); // true = add groups
var singleMesh = new THREE.Mesh(merged, sharedMaterial);
scene.add(singleMesh);
```

Use `mesh.geometry.groups` to map each group to a region ID for raycasting.

**Files to change:** `brain-3d-v3.js` — rewrite `loadRegion()` to collect geometries,
add a merge step after all regions load (after line 700 in current code).

**Expected gain:** 20 draw calls → 1 draw call for all regions. Massive.

---

### Phase 2 — Material Downgrade + Shader Uniform Strategy

**Goal:** Eliminate shader recompilation. Keep visual quality via texture.

#### 2A: Downgrade region overlays to MeshStandardMaterial

Region overlays are colored solid meshes — they don't need clearcoat or sheen.
`MeshStandardMaterial` renders identically for colored geometry and compiles 3–5×
faster than `MeshPhysicalMaterial`.

**Change in `loadRegion()` (line 504):**
```js
// BEFORE
var mat = new THREE.MeshPhysicalMaterial({
  clearcoat: 0.14, sheen: 0.15, sheenRoughness: 0.52, ...
});

// AFTER
var mat = new THREE.MeshStandardMaterial({
  color: baseColor, roughness: 0.58, metalness: 0.0,
  emissive: baseColor, emissiveIntensity: 0.18,
  envMap: _envMap, envMapIntensity: 0.09,
  transparent: false,
});
```

Keep `MeshPhysicalMaterial` ONLY on the cortex (where the normal map + sulcal texture
actually benefit from it). The visual difference on region overlays is imperceptible.

**Files to change:** `brain-3d-v3.js` lines 504–521.

---

#### 2B: Replace `material.needsUpdate` with GPU uniforms for hover/selection state

**Current problem:** Setting `material.color`, `material.emissive`, `material.opacity`
marks the shader for recompilation.

**Fix:** Pre-compile all material variants at load time, then swap between pre-compiled
instances (no recompile needed) or use a custom `ShaderMaterial` with uniforms.

**Approach A (simpler) — Material pooling:**
Create 3 pre-compiled material variants per region at load time:
- `mat_default` — resting state
- `mat_hover` — hover emissive glow
- `mat_selected` — gold highlight

On state change, swap `mesh.material = mat_hover` instead of modifying the material.
Material swaps are cheap; material property modifications are expensive.

```js
region.matDefault  = buildMat(baseColor, 0.18);
region.matHover    = buildMat(baseColor, 0.55);  // higher emissive
region.matSelected = buildMat(0xFFD060,  0.70);  // gold

// On hover:
mesh.material = region.matHover;  // no needsUpdate, no recompile
```

**Files to change:** `brain-3d-v3.js` — add material pre-compilation to `loadRegion()`,
rewrite `_showOverlay`, `_hideOverlay`, `highlightRegion`, `dimAllRegions`.

---

#### 2C: Pre-compile clipping plane shader variant

**Current:** Toggling split-brain sets `clippingPlanes` on all materials, causing recompile.

**Fix:** Pre-compile TWO material variants per region at load time — one with clipping,
one without. Store as `mat_default_clipped` / `mat_default_unclipped`. On split toggle,
swap mesh.material rather than modifying clippingPlanes.

This means 4 variants per region × 20 regions = 80 pre-compiled materials. Sounds like
a lot, but pre-compilation happens once at load (not during interaction), and material
swaps are free.

---

### Phase 3 — Raycasting Optimization

**Goal:** Eliminate 60Hz cortex raycasting.

#### 3A: Separate low-poly raycasting proxy mesh

**Current:** Raycasting runs against the 100k-face cortex every pointer move.

**Fix:** At asset generation time, create a second ultra-low-poly version of the cortex
(~2k–5k faces) used ONLY for raycasting. Never rendered. Hidden (`mesh.visible = false`
does not exclude from raycasting — use a separate raycast scene or `layers`).

Use Three.js `Layers` to separate the raycast proxy:
```js
RAYCAST_LAYER = 1;
proxyMesh.layers.set(RAYCAST_LAYER);
proxyMesh.visible = false;
raycaster.layers.set(RAYCAST_LAYER);  // only hits proxy
```

**Generate proxy in `optimize_cortex.py`:**
```python
# After 100k decimation, decimate again to 3k faces for raycasting proxy
proxy = mesh.decimate(target_count=3000)
proxy.export('data/brain_meshes/cortex_raycast_proxy.glb')
```

**Expected gain:** Raycasting a 3k-face mesh instead of 100k = ~33× less work per frame.

---

#### 3B: Throttle pointermove raycasting to 30Hz

As an interim fix before 3A:
```js
var _lastRaycast = 0;
canvas.addEventListener('pointermove', function(e) {
  var now = performance.now();
  if (now - _lastRaycast < 33) return;  // 30Hz cap
  _lastRaycast = now;
  // ... raycast logic
});
```

**Files to change:** `brain-3d-v3.js` lines 1251–1260.

---

### Phase 4 — Asset Format Optimization

#### 4A: Convert brainstem/cerebellum JSON → GLB

**Current:** 2.7MB + 2.0MB JSON files (slow JS parse).

**Fix:** Export brainstem and cerebellum as binary GLB from `generate_subcortical_json.py`.

```python
# In generate_subcortical_json.py, replace json.dump() with:
import trimesh
mesh = trimesh.Trimesh(vertices=verts, faces=faces)
mesh.export('data/brain_meshes/brainstem.glb')
```

Then update `_loadAtlasMesh()` in `brain-3d-v3.js` to use `GLTFLoader` instead of
`fetch().then(r.json())`. Embed the texture in the GLB using trimesh or Blender.

**Expected gain:** 2.7MB JSON → ~400KB GLB (7× smaller), parse time ~10× faster.

---

#### 4B: Compress GLBs with Draco or meshopt

All GLBs (cortex + 20 region files) can be compressed with Draco geometry compression,
reducing file size by 60–80%.

```bash
# Using gltf-pipeline (npm package)
npx gltf-pipeline -i full_brain_optimized.glb -o full_brain_optimized_draco.glb --draco.compressionLevel 7
```

Then add `DRACOLoader` to `brain-3d-v3.js`:
```js
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
var dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('./node_modules/three/examples/jsm/libs/draco/');
loader.setDRACOLoader(dracoLoader);
```

**Expected gain:** 4MB cortex → ~800KB. 20 region files (1.5MB total) → ~300KB.
Total asset load: ~14MB → ~3MB.

---

#### 4C: Convert PNG textures to KTX2/Basis Universal

Normal map (1.6MB PNG) and sulcal texture (1.7MB PNG) can be compressed to GPU-native
format using Basis Universal, which:
1. Compresses the file size by ~5×
2. Uploads directly to GPU texture memory without decompression on CPU

```bash
# Using basisu CLI
basisu cortex_normal_map.png -output_file cortex_normal_map.ktx2
```

```js
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
var ktx2Loader = new KTX2Loader();
ktx2Loader.setTranscoderPath('./node_modules/three/examples/jsm/libs/basis/');
ktx2Loader.detectSupport(renderer);
```

**Expected gain:** Texture upload time ~5× faster. VRAM usage ~3–5× smaller.

---

### Phase 5 — Memory / GC Fixes

#### 5A: Pre-allocate scratch Color/Vector3 objects

Replace per-frame `new THREE.Color()` allocations with reused scratch objects:

```js
// At module top level:
var _scratchColor = new THREE.Color();
var _scratchVec   = new THREE.Vector3();

// In highlightRegion() and pointermove handler:
_scratchColor.setHex(OVERLAY_COLORS[regionId] || 0x8888AA);
mat.emissive.copy(_scratchColor);
// No allocation, no GC pressure
```

**Files to change:** `brain-3d-v3.js` lines 893, 931, 1285.

---

#### 5B: Dispose textures on region hide

When a region is hidden (`_hideOverlay()`), dispose its material textures from GPU:
```js
function _disposeRegionTextures(mat) {
  if (mat.map)     { mat.map.dispose(); }
  if (mat.envMap)  { /* shared — don't dispose */ }
}
```

Note: Only dispose textures that are unique per-region, NOT the shared envMap.

---

### Phase 6 — Render Loop Efficiency

#### 6A: Demand rendering — only render when something changed

**Current:** `requestAnimationFrame` fires `renderer.render()` unconditionally 60×/second
even when nothing in the scene has changed (user not interacting, no camera movement,
no animation).

**Fix:** Dirty flag pattern.
```js
var _dirty = true;

function markDirty() { _dirty = true; }

function animate(ts) {
  animId = requestAnimationFrame(animate);
  controls.update();
  if (!_dirty && !camTo) return;  // skip render if nothing changed
  _dirty = false;
  renderer.render(scene, camera);
}

// Call markDirty() on:
// - pointermove (hover changes)
// - region selection
// - camera movement (hook OrbitControls 'change' event)
// - any toggle
controls.addEventListener('change', markDirty);
```

**Expected gain:** When idle, 0% GPU usage instead of continuous 60Hz renders.
This alone may be the single most impactful change for battery/thermals.

---

## 4. Implementation Priority

| Priority | Phase | Expected FPS gain | Difficulty |
|----------|-------|-------------------|------------|
| 1 | **6A** — Demand rendering | Eliminates idle GPU usage | Easy |
| 2 | **3B** — Throttle raycasting to 30Hz | Halves raycast cost | Easy |
| 3 | **2A** — MeshStandard on overlays | Faster shader compile | Easy |
| 4 | **2B** — Material pooling (pre-compiled variants) | Eliminates interaction stutter | Medium |
| 5 | **1A** — Stencil outlines | Eliminates 20 draw calls | Medium |
| 6 | **1B** — Merge region geometries | 20 → 1 draw call | Hard |
| 7 | **4A** — JSON → GLB for brainstem/cerebellum | 7× faster load | Medium |
| 8 | **3A** — Raycast proxy mesh | 33× faster raycasting | Hard |
| 9 | **4B** — Draco compression | 5× smaller assets | Medium |
| 10 | **4C** — KTX2 textures | 5× faster texture upload | Medium |
| 11 | **5A** — Scratch Color allocation | Reduces GC | Easy |
| 12 | **2C** — Pre-compiled clipping variants | Eliminates split stutter | Hard |

---

## 5. What to Preserve (Do Not Change)

- **Cortex material:** Keep `MeshPhysicalMaterial` with normal map + AO sulcal texture
  on the cortex itself. This is the primary quality differentiator vs. BrainFacts.
- **Atlas-derived brainstem/cerebellum:** Real anatomy from Harvard-Oxford + AAL atlases.
  Only change the file format (JSON → GLB), not the mesh data.
- **All region colors** (`OVERLAY_COLORS` map, lines 38–60)
- **Coordinate system** (lines 18–22 of engine header)
- **Camera presets** — all 6 views (lateral, medial, superior, anterior, posterior, inferior)
- **Split-brain, glass brain, cerebellum/brainstem toggles**
- **Quiz engine** in `brain-exercise-30.html`

---

## 6. Quality Comparison: Ours vs. BrainFacts

| Feature | BrainFacts | Brain Explorer 3.0 (Ours) |
|---------|------------|--------------------------|
| Cortex mesh | Low-poly, stylized | 100k face mesh (decimated from real 655k-face pial surface) |
| Brainstem | Simple shape | 27,531 faces, Harvard-Oxford atlas (marching cubes on real MRI) |
| Cerebellum | Simple shape | 20,313 faces, AAL atlas, folia band texture |
| Sulcal depth | Not represented | AO baked into texture — deep sulci visibly darker |
| Normal mapping | None | 2048×1024 normal map baked from 655k-face hires mesh |
| Material | Flat/standard | PBR: clearcoat, sheen, envMap reflections on cortex |
| Region count | ~29 basic | 22 Harvard-Oxford parcellated regions |
| Anatomy source | Illustrated | Real atlas data (Harvard-Oxford cortical + AAL subcortical) |

**Verdict:** Our visual quality significantly exceeds BrainFacts. The performance gap is
purely architectural (draw calls, shader complexity, render loop), not hardware requirement.
The goal is to close the performance gap without sacrificing quality.

---

## 7. Success Metrics

After completing Phases 1–3:
- Draw calls: ≤5 per frame (currently up to 43)
- Interaction stutter: Zero shader recompilation on hover/selection
- Raycasting: ≤33ms per pointermove event (currently can be 60–100ms)
- Idle GPU usage: ~0% (currently 60Hz continuous)

After completing Phases 4–6:
- Initial load time: ≤3 seconds on broadband (currently 8–15s)
- Total asset download: ≤3MB (currently ~14MB)
- Frame time: ≤16ms at 1080p on mid-range GPU (currently 20–40ms)

---

## 8. File Change Map

```
brain-3d-v3.js
  Phase 1A: lines 565-571, 385-398 — remove outline mesh, add stencil
  Phase 1B: lines 690-701 — add mergeGeometries after load
  Phase 2A: lines 504-521 — MeshStandard for overlays
  Phase 2B: loadRegion() — add pre-compiled material variants
  Phase 2C: toggleSplit() lines 999-1056 — swap materials instead of clippingPlanes
  Phase 3A: add RAYCAST_LAYER, load proxy mesh
  Phase 3B: lines 1251-1260 — add 30Hz throttle
  Phase 5A: lines 893, 931, 1285 — scratch Color/Vector3
  Phase 6A: animate() lines 1362-1386 — dirty flag

generate_subcortical_json.py
  Phase 4A: replace json.dump() with trimesh GLB export

optimize_cortex.py
  Phase 3A: add second decimation pass to 3k faces for raycast proxy

brain-exercise-30.html
  Phase 2B: no changes needed (all wired through window.__brain3d API)
  Phase 3B: no changes needed
```
