# Patient Encounter 2.0 — Three.js Avatar System
## Master Planning Document

**Status:** In Progress
**Quality target:** Brain Pathology 3.0 (`brain-3d-v3.js`)
**Started:** 2026-03-05
**Repository:** `mcdanielmjustin/JustinMasteryPage`

---

## 1. Executive Summary

Patient Encounter 1.0 uses flat SVG avatars with CSS animations. Patient Encounter 2.0 replaces the SVG with a real-time 3D avatar rendered via Three.js — the same engine, same post-processing pipeline, and same material quality used in Brain Pathology 3.0. The 3D avatar loads a GLTF/GLB humanoid mesh (from Ready Player Me), applies PBR skin materials, and drives 52 ARKit blend shapes for facial emotion states. The result looks like a real-time game-engine cutscene instead of a flat illustration.

**Key files created by this plan:**
| File | Purpose |
|---|---|
| `patient-avatar-v2.js` | Three.js module source (bundle this → `patient-avatar-v2.bundle.js`) |
| `patient-avatar-v2.bundle.js` | Bundled output loaded by exercise-v2.html |
| `clinical-presentation-exercise-v2.html` | Exercise page using 3D avatar |
| `clinical-presentation-settings-v2.html` | Settings page linking to exercise-v2.html |
| `data/avatars/*.glb` | 8 demographic GLTF avatars from Ready Player Me |

**Files NOT modified:** `clinical-presentation-exercise.html` (v1 remains unchanged)

---

## 2. Quality Reference — Brain Pathology 3.0

`brain-3d-v3.js` establishes the quality bar. Replicate its entire pipeline:

| Feature | Brain 3.0 Setting | Avatar 2.0 Setting |
|---|---|---|
| Renderer | WebGLRenderer, antialias:true, PCFSoftShadowMap | Same |
| Tone mapping | ACESFilmicToneMapping, exposure 1.0 | Same |
| Color space | SRGBColorSpace | Same |
| Pixel ratio | min(devicePixelRatio, 2) | Same |
| Material | MeshPhysicalMaterial, clearcoat, sheen, SSS | Same, tuned for skin |
| Env map | PMREM procedural 5-element studio | Same, warmer for skin |
| Lighting | 5-point: key, fill, rim, hemisphere, ambient | Same, adjusted angles for face |
| Shadows | PCFSoftShadowMap, 1024×1024 map | Same |
| Post: SSAO | GTAOPass radius:0.3, 16 samples | radius:0.4, 8 samples (portrait crop) |
| Post: Bloom | UnrealBloomPass strength:0.15, threshold:0.85 | strength:0.08, threshold:0.90 |
| Post: Output | OutputPass (tone map + color space) | Same |

---

## 3. File Structure

```
mastery-page/
├── patient-avatar-v2.js                  ← Three.js source module (AUTHOR THIS)
├── patient-avatar-v2.bundle.js           ← esbuild output (BUILD THIS)
├── clinical-presentation-exercise-v2.html
├── clinical-presentation-settings-v2.html
├── PLAN_patient_encounter_v2.md          ← this file
└── data/
    └── avatars/
        ├── adult_male.glb
        ├── adult_female.glb
        ├── young_male.glb
        ├── young_female.glb
        ├── adolescent_male.glb
        ├── adolescent_female.glb
        ├── elder_male.glb
        └── elder_female.glb
```

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| 3D engine | Three.js r170+ (same version as brain-3d-v3) |
| Avatar source | Ready Player Me (readyplayer.me) — free web tool, exports `.glb` |
| 3D mesh compression | Draco (already in `vendor/three/examples/jsm/libs/draco/gltf/`) |
| Bundler | esbuild (same as brain-3d-v3.bundle.js) |
| Emotion system | 52 ARKit blend shapes via `morphTargetInfluences` |
| Integration | `window.__PatientAvatar` global API, same pattern as `window.__brain3d` |

---

## 5. patient-avatar-v2.js — Complete Architecture

### 5.1 Module Pattern

Matches brain-3d-v3.js exactly: top-level ES module with `import * as THREE` and named addon imports. Exposes `window.__PatientAvatar` global object at the end of the file.

```javascript
import * as THREE          from 'three';
import { OrbitControls }   from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }      from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader }     from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer }  from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }      from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass }        from 'three/addons/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass }      from 'three/addons/postprocessing/OutputPass.js';
```

### 5.2 WebGLRenderer Setup

```javascript
var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;          // slightly brighter for skin
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
// Canvas style — portrait crop, rounded corners
renderer.domElement.style.cssText = 'display:block; border-radius:16px;';
```

### 5.3 Scene

```javascript
var scene = new THREE.Scene();
scene.background = new THREE.Color(0x0A0B10);    // near-black, matches exercise bg
scene.fog = new THREE.Fog(0x0A0B10, 6, 14);      // subtle depth fog
```

### 5.4 PMREM Procedural Environment Map (skin-tone adapted)

Same 5-element structure as brain-3d-v3 but warmer for skin reflections:

```javascript
// Sky dome — warm neutral studio ceiling
new THREE.MeshBasicMaterial({ color: 0x3A3530, side: THREE.BackSide })

// Key area overhead — warm 3200K tungsten
color: 0x9A7055 (warmer than brain's 0x806858)

// Fill area left — cool daylight bounce
color: 0x405868

// Rim area rear — warm hair-light backlight
color: 0x704838

// Ground plane — dark warm floor
color: 0x201510

// Accent sphere — catchlight (simulates round softbox)
color: 0xFFEECC
```

### 5.5 Camera

```javascript
// Portrait framing: shows head + upper torso (therapy session POV)
var camera = new THREE.PerspectiveCamera(35, 0.75, 0.1, 30);
// Avatar head is at y≈1.55 (seated), camera at eye level
camera.position.set(0, 1.5, 3.2);
// Look slightly up at the patient's face (submissive framing = patient looks larger)
camera.lookAt(0, 1.55, 0);
```

OrbitControls setup (damping matches brain-3d-v3):
```javascript
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.minDistance = 1.5;
controls.maxDistance = 5.0;
controls.minPolarAngle = 0.8;  // prevent going below floor
controls.maxPolarAngle = 1.6;
controls.enablePan = false;
controls.target.set(0, 1.4, 0);
```

### 5.6 5-Point Lighting (face-optimized)

```javascript
// Key light — warm 3200K from upper right front (creates facial depth)
var keyLight = new THREE.DirectionalLight(0xFFF0E8, 2.4);
keyLight.position.set(3, 5, 3);
keyLight.castShadow = true;
keyLight.shadow.mapSize.width  = 1024;
keyLight.shadow.mapSize.height = 1024;
keyLight.shadow.bias = -0.0003;

// Fill light — cool daylight from upper left (open shadows)
var fillLight = new THREE.DirectionalLight(0xD0E8FF, 0.60);
fillLight.position.set(-3, 2, 2);

// Rim / hair light — warm backlight from upper rear (separates hair from bg)
var rimLight = new THREE.DirectionalLight(0xFFDDB0, 0.80);
rimLight.position.set(0, 6, -4);
rimLight.castShadow = false;

// Under light — subtle warm bounce from below (simulates floor/desk bounce)
var underLight = new THREE.DirectionalLight(0xFFE8C0, 0.15);
underLight.position.set(0, -2, 2);

// Hemisphere + ambient — sky/ground and base fill
scene.add(new THREE.HemisphereLight(0xD8DDE8, 0x3A2010, 0.35));
scene.add(new THREE.AmbientLight(0xFFF0E8, 0.10));
```

### 5.7 Post-Processing Pipeline

```javascript
var composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

// SSAO — adds contact shadows under chin, in eye sockets, around ears
var gtaoPass = new GTAOPass(scene, camera, W, H);
gtaoPass.output = GTAOPass.OUTPUT.Default;
gtaoPass.updateGtaoMaterial({
  radius: 0.4,          // slightly larger than brain for human scale
  distanceExponent: 2,
  thickness: 1.5,
  samples: 8,           // 8 vs 16 — portrait crop doesn't need full resolution
});
gtaoPass.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3 });

// Bloom — subtle wet-eye highlight and skin sheen
var bloomPass = new UnrealBloomPass(
  new THREE.Vector2(W, H),
  0.08,   // strength  — much subtler than brain
  0.4,    // radius
  0.90    // threshold — only brightest specular catches bloom
);

composer.addPass(new OutputPass());
```

### 5.8 GLTFLoader + DRACOLoader

```javascript
var dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('./vendor/three/examples/jsm/libs/draco/gltf/');
var loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);
```

GLB path pattern: `data/avatars/{type}.glb`
Types: `adult_male`, `adult_female`, `young_male`, `young_female`,
        `adolescent_male`, `adolescent_female`, `elder_male`, `elder_female`

### 5.9 Material Assignment System

When a GLB loads, traverse all child meshes and identify material type by mesh name (Ready Player Me uses standard mesh naming conventions):

```
Mesh name contains "Wolf3D_Skin"     → skinMat     (MeshPhysicalMaterial, SSS)
Mesh name contains "Wolf3D_Eye"      → eyeMat      (clearcoat glass)
Mesh name contains "Wolf3D_Hair"     → hairMat     (anisotropic sheen)
Mesh name contains "Wolf3D_Teeth"    → teethMat    (slightly emissive white)
Mesh name contains "Wolf3D_Outfit"   → clothMat    (diffuse, high roughness)
Mesh name contains "Wolf3D_Body"     → skinMat     (same as face skin)
Otherwise                            → defaultMat  (standard diffuse)
```

**Skin Material** (most important — drives the 3D quality):
```javascript
var skinMat = new THREE.MeshPhysicalMaterial({
  map:                  skinTexture,       // baked albedo from RPM
  roughness:            0.65,
  metalness:            0.0,
  clearcoat:            0.15,             // very subtle skin sheen
  clearcoatRoughness:   0.45,
  sheen:                0.30,             // subsurface color bleeding
  sheenRoughness:       0.60,
  sheenColor:           new THREE.Color(0xFFCCAA),  // warm SSS tint
  // Subsurface scattering approximation (translucency on ear/nostril edges)
  transmission:         0.04,
  thickness:            0.8,
  ior:                  1.38,
  attenuationColor:     new THREE.Color(0xFF8866),
  attenuationDistance:  0.4,
  envMap:               _envMap,
  envMapIntensity:      0.08,
  normalMap:            normalMapTex,     // if available from RPM export
  normalScale:          new THREE.Vector2(0.8, 0.8),
  side:                 THREE.FrontSide,
});
skinMat.castShadow = true;
skinMat.receiveShadow = true;
```

**Eye Material** (glass-like clarity):
```javascript
var eyeMat = new THREE.MeshPhysicalMaterial({
  map:                  eyeTexture,
  roughness:            0.02,
  metalness:            0.0,
  clearcoat:            1.0,
  clearcoatRoughness:   0.0,
  transmission:         0.12,
  ior:                  1.50,
  envMap:               _envMap,
  envMapIntensity:      0.30,
});
```

**Hair Material** (anisotropic sheen):
```javascript
var hairMat = new THREE.MeshPhysicalMaterial({
  map:                  hairTexture,
  roughness:            0.55,
  metalness:            0.0,
  sheen:                0.6,
  sheenRoughness:       0.4,
  sheenColor:           new THREE.Color(0x8B6040),   // adjust per demographic
  envMap:               _envMap,
  envMapIntensity:      0.05,
});
```

**Clothing Material**:
```javascript
var clothMat = new THREE.MeshPhysicalMaterial({
  map:                  clothTexture,
  roughness:            0.85,
  metalness:            0.0,
  sheen:                0.2,
  sheenRoughness:       0.8,
  sheenColor:           new THREE.Color(0xAAAAAA),
  envMap:               _envMap,
  envMapIntensity:      0.02,
});
```

### 5.10 Blend Shape Emotion System

Ready Player Me avatars export with **52 ARKit blend shape morph targets** on the mesh named `Wolf3D_Head`. Access them via:

```javascript
var headMesh = null;
gltf.scene.traverse(function(node) {
  if (node.isMesh && node.name === 'Wolf3D_Head') headMesh = node;
});
// headMesh.morphTargetDictionary  → { 'jawOpen': 0, 'mouthSmileLeft': 1, ... }
// headMesh.morphTargetInfluences  → Float32Array of values [0..1]
```

**Complete emotion → blend shape mapping table:**

| Emotion | Blend Shapes (name: target value) |
|---|---|
| `idle` | all: 0 (breathing animation only) |
| `speaking` | jawOpen: 0.0→0.35 (animated), mouthSmileLeft: 0.08, mouthSmileRight: 0.08 |
| `concerned` | browDownLeft: 0.45, browDownRight: 0.45, browInnerUp: 0.35, mouthFrownLeft: 0.20, mouthFrownRight: 0.20, mouthPressLeft: 0.10, mouthPressRight: 0.10 |
| `anxious` | browInnerUp: 0.55, browOuterUpLeft: 0.20, browOuterUpRight: 0.20, eyeWideLeft: 0.30, eyeWideRight: 0.30, mouthStretchLeft: 0.15, mouthStretchRight: 0.15, cheekPuff: 0.08 |
| `distressed` | browDownLeft: 0.70, browDownRight: 0.70, browInnerUp: 0.45, mouthFrownLeft: 0.55, mouthFrownRight: 0.55, eyeSquintLeft: 0.30, eyeSquintRight: 0.30, noseSneerLeft: 0.20, noseSneerRight: 0.20, jawForward: 0.10 |
| `confused` | browDownLeft: 0.50, browOuterUpRight: 0.55, eyeSquintLeft: 0.20, mouthLeft: 0.15, mouthPressLeft: 0.15, mouthPressRight: 0.15, cheekSquintRight: 0.10 |
| `hopeful` | browOuterUpLeft: 0.30, browOuterUpRight: 0.30, mouthSmileLeft: 0.28, mouthSmileRight: 0.28, cheekSquintLeft: 0.18, cheekSquintRight: 0.18, eyeSquintLeft: 0.12, eyeSquintRight: 0.12 |
| `relieved` | mouthSmileLeft: 0.42, mouthSmileRight: 0.42, cheekSquintLeft: 0.32, cheekSquintRight: 0.32, eyeSquintLeft: 0.18, eyeSquintRight: 0.18, browOuterUpLeft: 0.12, browOuterUpRight: 0.12 |
| `proud` | mouthSmileLeft: 0.30, mouthSmileRight: 0.30, cheekSquintLeft: 0.22, cheekSquintRight: 0.22, browOuterUpLeft: 0.18, browOuterUpRight: 0.18, mouthShrugUpper: 0.10 |
| `embarrassed` | mouthFrownLeft: 0.22, mouthFrownRight: 0.22, eyeLookDownLeft: 0.40, eyeLookDownRight: 0.40, browInnerUp: 0.28, cheekSquintLeft: 0.18, cheekSquintRight: 0.18, mouthPucker: 0.10 |
| `tearful` | browInnerUp: 0.72, browDownLeft: 0.25, browDownRight: 0.25, mouthFrownLeft: 0.45, mouthFrownRight: 0.45, mouthPucker: 0.22, mouthStretchLeft: 0.12, mouthStretchRight: 0.12, eyeBlinkLeft: 0.20, eyeBlinkRight: 0.20 |
| `engaged` | browOuterUpLeft: 0.22, browOuterUpRight: 0.22, eyeWideLeft: 0.18, eyeWideRight: 0.18, mouthSmileLeft: 0.12, mouthSmileRight: 0.12, eyeLookUpLeft: 0.10, eyeLookUpRight: 0.10 |
| `flat` | eyeSquintLeft: 0.10, eyeSquintRight: 0.10 (everything else 0) |

**Transition system** — smooth lerp between emotion states:
```javascript
// Target blend shape values stored in _targetInfluences{}
// Each animation frame: lerp current → target at rate 0.08 per frame (60fps ≈ 130ms transition)
function _lerpEmotions(dt) {
  if (!headMesh) return;
  var dict = headMesh.morphTargetDictionary;
  var infl = headMesh.morphTargetInfluences;
  for (var name in _targetInfluences) {
    var idx = dict[name];
    if (idx === undefined) continue;
    infl[idx] = THREE.MathUtils.lerp(infl[idx], _targetInfluences[name], 0.08);
  }
}
```

**Speaking jaw animation** — driven in the render loop:
```javascript
var _jawPhase = 0;
function _animateJaw(dt) {
  if (!_isSpeaking || !headMesh) return;
  _jawPhase += dt * 8.0;   // ~8 cycles/sec jaw frequency
  var jawIdx = headMesh.morphTargetDictionary['jawOpen'];
  if (jawIdx !== undefined) {
    headMesh.morphTargetInfluences[jawIdx] =
      0.12 + Math.sin(_jawPhase) * 0.14 + Math.sin(_jawPhase * 1.7) * 0.06;
  }
}
```

**Idle breathing** — subtle body sway (on the avatar group):
```javascript
var _breathPhase = 0;
function _animateBreathing(dt) {
  _breathPhase += dt * 0.7;   // 0.7 rad/sec ≈ 1 breath per 9 seconds
  avatarGroup.position.y = Math.sin(_breathPhase) * 0.004;
  avatarGroup.rotation.z = Math.sin(_breathPhase * 0.5) * 0.003;
}
```

### 5.11 Animation Loop

```javascript
var _clock = new THREE.Clock();
var _isSpeaking = false;
var _targetInfluences = {};   // emotion blend shape targets
var _animFrameId = null;

function _animate() {
  _animFrameId = requestAnimationFrame(_animate);
  var dt = _clock.getDelta();
  controls.update();
  _animateBreathing(dt);
  _lerpEmotions(dt);
  if (_isSpeaking) _animateJaw(dt);
  composer.render();
}
```

### 5.12 Public API

```javascript
window.__PatientAvatar = {
  // Mount renderer canvas into a container element
  // options: { width, height, onLoad, onProgress, onError }
  mount: function(container, options) { ... },

  // Unmount — remove canvas, cancel animation, free GPU resources
  unmount: function() { ... },

  // Load a demographic GLB. type = 'adult_male' | 'adult_female' | etc.
  // Returns Promise<void>
  loadDemographic: function(type) { ... },

  // Set emotion state (same 13 states as v1 SVG system)
  // Smooth-lerps all blend shapes to target values
  setEmotion: function(emotion) { ... },

  // Start/stop jaw speaking animation
  setSpeaking: function(isSpeaking) { ... },

  // Resize renderer to new dimensions
  resize: function(w, h) { ... },

  // Ready promise — resolves after mount() completes WebGL init
  ready: null,  // set to Promise in mount()
};
```

---

## 6. Ready Player Me GLB Generation

### 6.1 Step-by-Step Workflow

1. Go to **readyplayer.me** → click "Try it free" → create avatar
2. Choose **Half Body** or **Full Body** (Full Body is better — shows seated posture)
3. Configure demographics (guide below)
4. Click **Download** → choose **GLB** format
5. Export settings:
   - **Texture quality:** High (1K or 2K textures)
   - **Mesh LOD:** Medium (good balance)
   - **Include morph targets:** YES (required for expressions)
   - **Draco compression:** YES if available (reduces size 3-5x)
6. Save as `data/avatars/{type}.glb`

### 6.2 Demographic Appearance Guide

| Avatar Type | Hair | Skin | Clothing |
|---|---|---|---|
| `young_male` | Short brown, messy | Medium light | T-shirt, jeans |
| `young_female` | Ponytail, dark brown | Medium light | Hoodie, casual |
| `adolescent_male` | Medium, slightly long | Varied (diverse options) | Hoodie or polo |
| `adolescent_female` | Shoulder-length, varied | Varied | Casual top |
| `adult_male` | Short, professional | Medium (use diverse RPM options) | Dress shirt, no tie |
| `adult_female` | Shoulder-length | Medium | Blouse or professional top |
| `elder_male` | White/grey, sparse | Lighter, more wrinkled (RPM has aging sliders) | Cardigan or button shirt |
| `elder_female` | White/grey, curled | Lighter | Blouse, cardigan |

### 6.3 Ready Player Me Embed API (Alternative)

Instead of downloading .glb files manually, use the RPM iframe embed:
```javascript
// Load RPM avatar builder in an iframe, receive GLB URL via postMessage
var frame = document.createElement('iframe');
frame.src = 'https://mcdanielmjustin.readyplayer.me/avatar?frameApi';
// Listen for 'v1.avatar.exported' event → contains .glb URL
// Then fetch and cache the GLB locally
```

This allows custom avatar creation in the future (student-chosen avatar).

### 6.4 Placeholder Strategy (for development before .glb files exist)

When `data/avatars/{type}.glb` is missing, show a clean loading state:
- Display a simple colored sphere at head position
- Apply the same lighting/materials (so it still looks 3D and polished)
- Log `[patient-avatar-v2] GLB not found: {type}` to console
- Retry with `data/avatars/adult_male.glb` as universal fallback

---

## 7. Integration — clinical-presentation-exercise-v2.html

### 7.1 Changes from v1

The v2 exercise HTML is a copy of `clinical-presentation-exercise.html` with these changes:

#### Change A — Title
```html
<!-- v1: -->
<title>Patient Encounter — Mastery Page</title>
<!-- v2: -->
<title>Patient Encounter 2.0 — Mastery Page</title>
```

#### Change B — Remove SVG avatar CSS (lines ~111-543 in v1)
All CSS blocks referencing:
- `#avatar-root`, `#avatar-body`, `#avatar-head`, `#avatar-face`
- `#avatar-jaw`, `#avatar-mouth`, `#avatar-eyes`, `#avatar-hand`
- `.state-idle`, `.state-speaking`, `.state-concerned`, etc.
- `@keyframes breathe`, `@keyframes jawSpeak`, `@keyframes blink`

Replace with:
```css
/* Avatar 3D container */
.avatar-wrap {
  position: relative;
  width: 100%;
  /* height determined by Three.js renderer canvas */
}
#avatar-3d-canvas {
  width: 100% !important;
  height: auto !important;
  border-radius: 16px;
}
.avatar-loading-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(10,11,16,0.6); border-radius: 16px;
  color: var(--text2); font-size: 13px; font-weight: 500;
  transition: opacity 0.3s;
}
.avatar-loading-overlay.hidden { opacity: 0; pointer-events: none; }
```

#### Change C — Replace avatar-wrap HTML (line ~957 in v1)
```html
<!-- v1: -->
<div class="avatar-wrap" id="avatar-wrap">
  <!-- avatar SVG injected here -->
</div>

<!-- v2: -->
<div class="avatar-wrap" id="avatar-wrap">
  <div class="avatar-loading-overlay" id="avatar-loading-overlay">
    Loading avatar...
  </div>
  <!-- Three.js canvas injected here by PatientAvatar.mount() -->
</div>
```

#### Change D — Module loader (in `<head>`, before `</head>`)
```html
<script type="module">
  import('./patient-avatar-v2.bundle.js').catch(function(e) {
    console.warn('[encounter-v2] 3D avatar bundle not found, disabling 3D:', e.message);
    window.__PatientAvatar = null;
  });
</script>
```

#### Change E — Replace `loadAvatar()` and `setAvatarState()` functions

**Remove:**
- `loadAvatar(avatarType)` function entirely
- `setAvatarState(emotion)` function entirely
- The SVG MOUTH_PATHS object

**Replace with:**
```javascript
function loadAvatar(avatarType) {
  const pa = window.__PatientAvatar;
  if (!pa) return;
  const overlay = document.getElementById('avatar-loading-overlay');
  if (overlay) overlay.classList.remove('hidden');
  pa.loadDemographic(avatarType).then(function() {
    if (overlay) overlay.classList.add('hidden');
  }).catch(function(e) {
    console.warn('[encounter-v2] Avatar load failed:', e);
    if (overlay) overlay.classList.add('hidden');
  });
}

function setAvatarState(emotion) {
  const pa = window.__PatientAvatar;
  if (!pa) return;
  pa.setEmotion(emotion);
  state.avatarState = emotion;
}
```

#### Change F — Replace jaw animation in `runTypewriter()`
```javascript
// v1:
const startJaw = () => {
  if (jaw) jaw.style.animation = 'jawSpeak .32s ease-in-out infinite';
};
const stopJaw = () => {
  if (jaw) jaw.style.animation = '';
};

// v2:
const startJaw = () => {
  const pa = window.__PatientAvatar;
  if (pa) pa.setSpeaking(true);
};
const stopJaw = () => {
  const pa = window.__PatientAvatar;
  if (pa) pa.setSpeaking(false);
};
```

#### Change G — Mount call in initialization

After `DOMContentLoaded` or at session start, add:
```javascript
// Initialize 3D avatar system when page loads
(function initAvatarSystem() {
  function _tryMount() {
    const pa = window.__PatientAvatar;
    if (!pa) return;   // bundle not yet loaded
    const wrap = document.getElementById('avatar-wrap');
    if (!wrap) return;
    pa.mount(wrap, {
      width: wrap.offsetWidth || 320,
      height: Math.round((wrap.offsetWidth || 320) * 1.25),  // 4:5 portrait ratio
    });
  }
  // Poll until PatientAvatar bundle loads (async module import)
  var _mountPoll = setInterval(function() {
    if (window.__PatientAvatar) {
      clearInterval(_mountPoll);
      _tryMount();
    }
  }, 100);
  // Timeout after 5 seconds — bundle not available
  setTimeout(function() { clearInterval(_mountPoll); }, 5000);
})();
```

#### Change H — Remove `<script src="avatar-svgs.js">` at bottom

Replace with nothing (v2 uses Three.js bundle, not SVG data).

#### Change I — Header badge

In the nav title area, add a "2.0" badge:
```html
<span class="nav-title">Patient Encounter</span>
<span style="
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; font-size: 10px; font-weight: 700;
  padding: 2px 7px; border-radius: 999px;
  letter-spacing: 0.05em; vertical-align: middle;
">2.0</span>
```

### 7.2 `detectAvatarType()` — Kept Identical

The demographic detection function is **unchanged** in v2. Same logic, same 8 types, same regex patterns. It feeds directly into `loadDemographic(type)`.

---

## 8. Build Process — Bundling

### 8.1 esbuild Command

```bash
# From mastery-page/ directory
npx esbuild patient-avatar-v2.js \
  --bundle \
  --format=esm \
  --outfile=patient-avatar-v2.bundle.js \
  --platform=browser \
  --external:./vendor/three/examples/jsm/libs/draco/gltf/* \
  --minify
```

OR, if using the same build script pattern as brain-3d-v3:
```bash
# Check existing brain bundle build script
cat build_brain_bundle.py   # likely uses esbuild or rollup
```

### 8.2 NPM Three.js Resolution

Confirm `three` package is installed:
```bash
cd mastery-page
npm list three   # should show three@0.170.x
# If missing:
npm install three@latest
```

### 8.3 CDN Fallback (no build tooling)

If building locally isn't possible, use an importmap in the HTML head:
```html
<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.170.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.170.0/examples/jsm/"
  }
}
</script>
<script type="module" src="patient-avatar-v2.js"></script>
```

---

## 9. Scene Composition — The Therapy Room

Beyond just the avatar, the scene should suggest a therapy office:

### 9.1 Environment Objects (simple geometry, no extra assets needed)

```javascript
// Floor — polished dark wood
var floorMat = new THREE.MeshPhysicalMaterial({
  color: 0x2A1E14, roughness: 0.5, metalness: 0.0,
  envMapIntensity: 0.03,
});
var floor = new THREE.Mesh(new THREE.PlaneGeometry(6, 6), floorMat);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

// Wall behind patient — muted grey-green
var wallMat = new THREE.MeshPhysicalMaterial({
  color: 0x3A4035, roughness: 0.95, metalness: 0.0,
});
var wall = new THREE.Mesh(new THREE.PlaneGeometry(6, 5), wallMat);
wall.position.set(0, 2.5, -2.0);
wall.receiveShadow = true;
scene.add(wall);

// Chair — simple box geometry (avatar sits on this)
// Use Draco-compressed chair.glb if available, otherwise procedural boxes
```

### 9.2 Camera Position Validation

With the avatar seated at origin (head at y≈1.55), camera at (0, 1.5, 3.2), FOV 35:
- **Framing**: head + neck + upper chest visible (standard therapy POV)
- **Depth of field**: NOT applied (keeps simple, matches brain-3d-v3 approach)
- **No orbit controls in production**: lock controls or remove for final version

---

## 10. GLB Asset Technical Requirements

| Spec | Requirement |
|---|---|
| File format | GLTF 2.0 / GLB (binary) |
| Draco compression | Preferred (3-5x size reduction) |
| File size target | < 5 MB per avatar, ideally < 3 MB |
| Polygon count | ~15,000–30,000 triangles (RPM medium quality) |
| Textures | 1K or 2K albedo, normal, roughness-metalness maps |
| Morph targets | 52 ARKit blend shapes on `Wolf3D_Head` mesh |
| Skeleton | Full humanoid rig (RPM standard) |
| Seated pose | Avatar should export in A-pose; seated posing via skeletal animation or manual bone transforms |

### 10.1 Seated Posing

Ready Player Me exports in A-pose (standing arms out). To make avatar look seated:
Option A — **Bone transforms**: After loading, find the Hip/Spine/UpperLeg bones and rotate to simulate sitting.
Option B — **Export with custom pose**: Use an intermediate tool (Blender) to pose the avatar seated, then re-export.
Option C — **Camera crop**: Frame camera so only head/shoulders visible; standing vs seated irrelevant.

**Recommended for Phase 1:** Option C (camera crop). Phase 2: Option A (bone transforms).

---

## 11. Implementation Checklist

### Phase 1 — Infrastructure (Can be done without GLB files)
- [ ] Write `patient-avatar-v2.js` source module
- [ ] Bundle to `patient-avatar-v2.bundle.js`
- [ ] Create `clinical-presentation-settings-v2.html`
- [ ] Create `clinical-presentation-exercise-v2.html`
- [ ] Test: page loads without JS errors, Three.js canvas appears
- [ ] Test: placeholder sphere shows when no GLB file found
- [ ] Add "Patient Encounter 2.0" link to `index.html` / mastery-page landing

### Phase 2 — GLB Assets
- [ ] Create all 8 avatars on readyplayer.me
- [ ] Download as Draco-compressed GLB
- [ ] Place in `data/avatars/`
- [ ] Test: avatar loads correctly for each demographic type
- [ ] Test: all 13 emotion states visually correct
- [ ] Test: speaking jaw animation looks natural

### Phase 3 — Polish
- [ ] Bone transforms for seated posture (or Blender-posed GLBs)
- [ ] Refine skin material per demographic (elder avatar → slightly desaturate, more roughness)
- [ ] Fine-tune emotion blend shapes (may need adjustments per avatar)
- [ ] Add idle idle eye-look saccades (subtle eye movement during idle)
- [ ] Add random blink animation (blink every 3-6 seconds randomly)
- [ ] Consider adding subtle head bob during speaking

### Phase 4 — Production
- [ ] Version-stamp GLB files for cache busting (e.g., `adult_male.glb?v=20260310`)
- [ ] Performance audit: maintain 60fps on mid-range hardware
- [ ] Mobile check: reduce GTAOPass samples if needed for mobile
- [ ] Rotate GitHub token (old token was shared in conversation)
- [ ] Push to GitHub, deploy to Vercel

---

## 12. Known Risks and Mitigations

| Risk | Mitigation |
|---|---|
| GLB files too large | Use Draco compression; target < 3 MB each |
| Ready Player Me blend shape names differ from ARKit | Map against actual RPM documentation; RPM uses exact ARKit names for Half-Body Full-Body avatars |
| Three.js GTAOPass causes performance issues on low-end machines | Add `if (performance.now() < 16) composer.render(); else renderer.render()` toggle |
| Seated pose looks unnatural | Use camera crop (Option C above) for Phase 1 |
| WebGL not supported | Catch renderer creation error; fall back to v1 SVG system via iframe or redirect |
| ImportMap compatibility (older browsers) | Use bundle approach (avoids importmap entirely) |
| Blend shape names changed in newer RPM versions | Log all morph target names on load and map dynamically |

---

## 13. File: patient-avatar-v2.js — Key Code Structure Outline

```
patient-avatar-v2.js
├── Imports (Three.js + addons)
├── CONSTANTS (DEMO_TYPES, EMOTION_BLEND_SHAPES, GLB_PATH)
├── Module-level variables (renderer, scene, camera, composer, etc.)
├── _buildEnvMap() — PMREM studio environment
├── _buildLights() — 5-point lighting setup
├── _buildComposer() — GTAOPass + BloomPass + OutputPass
├── _buildScene() — floor, wall, ambient geometry
├── _buildLoader() — GLTFLoader + DRACOLoader
├── _applyMaterials(gltf) — skin/eye/hair/cloth material assignment
├── _loadGLB(type) — loads data/avatars/{type}.glb, returns Promise
├── _setTargetInfluences(emotion) — populates _targetInfluences map
├── _lerpEmotions(dt) — per-frame blend shape lerp
├── _animateJaw(dt) — per-frame jaw speaking animation
├── _animateBreathing(dt) — idle body sway
├── _animate() — main RAF loop
├── mount(container, options) — public API
├── unmount() — public API cleanup
├── loadDemographic(type) — public API
├── setEmotion(emotion) — public API
├── setSpeaking(bool) — public API
└── window.__PatientAvatar = { mount, unmount, loadDemographic, setEmotion, setSpeaking, resize, ready }
```

---

## 14. Links and References

- **Three.js r170 addons source:** `vendor/three/examples/jsm/`
- **DRACOLoader decoder:** `vendor/three/examples/jsm/libs/draco/gltf/`
- **Reference implementation:** `brain-3d-v3.js` (full production example)
- **Brain exercise loader pattern:** `brain-exercise-30.html` line 494 (`<script type="module">`)
- **Patient data structure:** `data/CASS_presentations.json` → `encounter.patient.label`, `initial_avatar_state`, `phases[].avatar_emotion`
- **Original exercise:** `clinical-presentation-exercise.html` — do NOT modify
- **Original settings:** `clinical-presentation-settings.html` — do NOT modify
- **Ready Player Me docs:** readyplayer.me/developers

---

*Document version: 1.0 — 2026-03-05*
*Next step: implement `patient-avatar-v2.js` source file*
