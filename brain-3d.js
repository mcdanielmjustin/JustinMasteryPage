/**
 * brain-3d.js — Three.js 3D Brain Explorer
 * Phase 2, Chunk 2B: 11 cortical region meshes + raycasting click detection
 *
 * Replaces the single-mesh hemisphere with 9 cortical sub-meshes carved from
 * the displaced hemisphere geometry via zone-based vertex classification, plus
 * separate cerebellum and brainstem meshes.
 *
 * Hover: per-mesh white emissive pulse.
 * Click: OutlinePass gold outline + info panel via window.__brainUI bridge.
 *
 * Exposes window.__brain3d = { mount(container), unmount() }
 * Called by brain-exercise.html when the user switches to the 3D view.
 */

import * as THREE           from 'three';
import { OrbitControls }    from 'three/addons/controls/OrbitControls.js';
import { EffectComposer }   from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }       from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass }      from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass }       from 'three/addons/postprocessing/OutputPass.js';

// ══════════════════════════════════════════════════════════════════════════════
// RENDERER
// ══════════════════════════════════════════════════════════════════════════════

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled    = true;
renderer.shadowMap.type       = THREE.PCFSoftShadowMap;
renderer.toneMapping          = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure  = 1.2;
renderer.localClippingEnabled = true;   // required for per-material clippingPlanes (cross-section)

const canvas = renderer.domElement;
canvas.style.borderRadius = '16px';
canvas.style.display      = 'block';
canvas.style.cursor       = 'grab';

// ── EffectComposer (post-processing — OutlinePass for region selection) ────────
const composer = new EffectComposer(renderer);

// ══════════════════════════════════════════════════════════════════════════════
// SCENE
// ══════════════════════════════════════════════════════════════════════════════

const scene = new THREE.Scene();

// ── Camera ────────────────────────────────────────────────────────────────────
const camera = new THREE.PerspectiveCamera(45, 1.54, 0.1, 100);
camera.position.set(0, 0.55, 4.5);

// ── Orbit Controls ────────────────────────────────────────────────────────────
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance   = 2.5;
controls.maxDistance   = 8.0;
controls.enablePan     = false;
controls.target.set(0, 0.1, 0);
controls.update();

// ── Lighting ──────────────────────────────────────────────────────────────────
// Warm key light from upper-left (matches SVG lateral light source direction)
const keyLight = new THREE.DirectionalLight(0xFFE8D0, 2.8);
keyLight.position.set(-3, 4, 3);
keyLight.castShadow = true;
keyLight.shadow.mapSize.width  = 1024;
keyLight.shadow.mapSize.height = 1024;
keyLight.shadow.camera.near    = 0.5;
keyLight.shadow.camera.far     = 20;
scene.add(keyLight);

// Cool fill from right (prevents total black in shadow areas)
const fillLight = new THREE.DirectionalLight(0xD0E0FF, 0.6);
fillLight.position.set(4, 1, -2);
scene.add(fillLight);

// Rim light from behind-lower-right (depth separation from background)
const rimLight = new THREE.DirectionalLight(0xFFD0C0, 0.9);
rimLight.position.set(2, -1, -4);
scene.add(rimLight);

// Warm ambient — base illumination matching SVG tissue warmth
const ambient = new THREE.AmbientLight(0xC8906A, 0.4);
scene.add(ambient);

// ══════════════════════════════════════════════════════════════════════════════
// REGION COLOR PALETTE
// Each region uses the 20%-stop midpoint of its SVG radial gradient as the 3D
// base color, giving subtle tonal differentiation under the same tissue lighting.
// ══════════════════════════════════════════════════════════════════════════════

const REGION_COLORS = {
  frontal_lobe:         0xC8845E,
  prefrontal_cortex:    0xCE8C68,
  brocas_area:          0xBA7450,
  motor_cortex:         0xCC7E56,
  parietal_lobe:        0xBE7860,
  somatosensory_cortex: 0xD08870,
  temporal_lobe:        0xB87050,
  wernickes_area:       0xB06848,
  occipital_lobe:       0xA86C58,
  cerebellum:           0xA87C6A,
  brainstem:            0x967060,
};

// ══════════════════════════════════════════════════════════════════════════════
// VERTEX ZONE CLASSIFIER
// Priority-chain: each vertex (by centroid) is assigned to the first matching
// zone. Sub-regions (prefrontal, motor, somatosensory, broca, wernicke) are
// checked before their parent lobes to ensure proper carving.
//
// Coordinate system after displacement:
//   x  — medial (≈ 0) → lateral (≈ 1.5)
//   y  — inferior (≈ −0.95) → superior (≈ 1.4)
//   z  — posterior (≈ −1.82) → anterior (≈ 1.82)   [AP elongated 1.3×]
//
// Sylvian fissure approximation:
//   y_syl(z) ≈ 0.08 − 0.18·z
//   (tilts superiorly as it runs posteriorly — anterior: ≈ −0.16; posterior: ≈ +0.19)
// ══════════════════════════════════════════════════════════════════════════════

function classifyVertex(x, y, z) {
  // Medial cut-face — modeled as flat disc, not part of any lobe
  if (x < 0.13) return null;
  // Inferior pole below brainstem attachment area — excluded from cortical lobes
  if (y < -0.68) return null;

  const syl = 0.08 - 0.18 * z;   // Sylvian fissure y-level at this AP position

  // ── 1. Occipital — posterior third ───────────────────────────────────────
  if (z < -0.62) return 'occipital_lobe';

  // ── 2. Prefrontal — anterior-most, clearly above Sylvian ─────────────────
  if (z > 1.05 && y > syl) return 'prefrontal_cortex';

  // ── 3. Motor cortex — precentral strip (central-anterior, firmly superior) ──
  // y threshold syl+0.25 keeps motor away from inferior frontal / Broca zone
  if (z >= 0.30 && z <= 0.70 && y > syl + 0.25) return 'motor_cortex';

  // ── 4. Somatosensory — postcentral strip ─────────────────────────────────
  if (z >= 0.00 && z <= 0.32 && y > syl + 0.14) return 'somatosensory_cortex';

  // ── 5. Broca's area — inferior frontal gyrus (near Sylvian, anterior) ────
  if (z >= 0.35 && z <= 0.86 && y >= syl - 0.14 && y <= syl + 0.36)
    return 'brocas_area';

  // ── 6. Wernicke's area — posterior superior temporal / inferior parietal ──
  if (z >= -0.32 && z <= 0.06 && y >= syl && y <= syl + 0.52)
    return 'wernickes_area';

  // ── 7. Parietal lobe — superior middle (above Sylvian, posterior to central) ─
  if (z >= -0.64 && z <= 0.06 && y > syl + 0.12) return 'parietal_lobe';

  // ── 8. Temporal lobe — inferior to Sylvian ───────────────────────────────
  if (y <= syl + 0.15 && z >= -0.64) return 'temporal_lobe';

  // ── 9. Remaining frontal — catch-all for anterior hemisphere ─────────────
  if (z > 0.12) return 'frontal_lobe';

  return null;  // unclaimed (region boundaries / deep folds)
}

// ══════════════════════════════════════════════════════════════════════════════
// HEMISPHERE GEOMETRY
// Builds the displaced sphere geometry (same shaping as Chunk 2A) and returns
// it as a plain BufferGeometry — no mesh, shared for cortical region carving.
// ══════════════════════════════════════════════════════════════════════════════

function buildHemisphereGeo() {
  const geo = new THREE.SphereGeometry(1.4, 128, 96);
  const pos = geo.attributes.position;

  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);

    // 1. Elongate anterior–posterior axis (~17 cm vs ~14 cm width)
    z *= 1.30;

    // 2. Flatten inferior surface (skull base contact)
    if (y < 0) y *= 0.68;

    // 3. Slightly widen at the equatorial band
    const tiltNorm = Math.abs(y / 1.4);
    x *= 1.0 + 0.06 * (1 - tiltNorm * tiltNorm);

    // 4. Flatten medial face — pull vertices near x ≤ 0 toward x = 0
    if (x < 0.04) {
      const depth = Math.max(0, -x);
      x += depth * 0.94;
    }

    // 5. Multi-frequency gyral displacement along radial direction
    const r = Math.sqrt(x * x + y * y + z * z) || 1;

    const lf =
      0.052 * Math.sin(x * 6.8 + 0.40) * Math.sin(y * 6.2 + 0.80) * Math.sin(z * 5.0 + 0.20) +
      0.040 * Math.sin(x * 5.0 + 1.20) * Math.cos(y * 7.5 + 0.60) * Math.sin(z * 6.5 + 1.40);

    const mf =
      0.027 * Math.sin(x * 11.5 + 2.10) * Math.sin(y * 10.0 + 1.30) * Math.sin(z * 9.5 + 0.90) +
      0.019 * Math.cos(x * 14.0 + 0.70) * Math.sin(y * 13.5 + 2.50) * Math.cos(z * 11.0 + 1.80);

    const hf =
      0.009 * Math.sin(x * 22.0 + 1.50) * Math.sin(y * 20.0 + 0.80) * Math.sin(z * 18.0 + 2.20) +
      0.006 * Math.cos(x * 28.0 + 0.40) * Math.cos(y * 26.0 + 1.90);

    const disp = lf + mf + hf;

    const medialSuppress   = Math.min(1, Math.max(0, x + 0.3) / 0.4);
    const inferiorSuppress = Math.min(1, (y + 1.4) / 0.45);
    const dispFinal        = disp * medialSuppress * inferiorSuppress;

    x += (x / r) * dispFinal;
    y += (y / r) * dispFinal;
    z += (z / r) * dispFinal;

    pos.setXYZ(i, x, y, z);
  }

  pos.needsUpdate = true;
  geo.computeVertexNormals();
  return geo;
}

// ══════════════════════════════════════════════════════════════════════════════
// CORTICAL REGION CARVING
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Iterates every triangle in hemiGeo and collects those whose centroid falls
 * in the given region zone. Builds a compact BufferGeometry from those triangles
 * and wraps it in a Mesh with per-region MeshPhysicalMaterial.
 *
 * Returns null if no triangles matched (should not happen for valid zone IDs).
 */
function buildRegionMesh(hemiGeo, regionId) {
  const idxArr  = hemiGeo.index.array;
  const posArr  = hemiGeo.attributes.position.array;
  const normArr = hemiGeo.attributes.normal.array;

  // Collect original vertex-index triples whose centroid classifies as regionId
  const triVerts = [];
  for (let i = 0; i < idxArr.length; i += 3) {
    const a = idxArr[i], b = idxArr[i + 1], c = idxArr[i + 2];
    const cx = (posArr[a*3]   + posArr[b*3]   + posArr[c*3])   / 3;
    const cy = (posArr[a*3+1] + posArr[b*3+1] + posArr[c*3+1]) / 3;
    const cz = (posArr[a*3+2] + posArr[b*3+2] + posArr[c*3+2]) / 3;
    if (classifyVertex(cx, cy, cz) === regionId) {
      triVerts.push(a, b, c);
    }
  }

  if (triVerts.length === 0) return null;

  // Remap to a compact vertex buffer (only vertices used by this region)
  const vertMap      = new Map();
  const newPositions = [];
  const newNormals   = [];
  const newIndices   = [];

  for (const origIdx of triVerts) {
    if (!vertMap.has(origIdx)) {
      const ni = newPositions.length / 3;
      vertMap.set(origIdx, ni);
      newPositions.push(
        posArr[origIdx*3], posArr[origIdx*3+1], posArr[origIdx*3+2]
      );
      newNormals.push(
        normArr[origIdx*3], normArr[origIdx*3+1], normArr[origIdx*3+2]
      );
    }
    newIndices.push(vertMap.get(origIdx));
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(newPositions, 3));
  geo.setAttribute('normal',   new THREE.Float32BufferAttribute(newNormals,   3));
  geo.setIndex(newIndices);

  const mat = new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(REGION_COLORS[regionId] || 0xC87858),
    roughness:          0.72,
    metalness:          0.00,
    clearcoat:          0.12,
    clearcoatRoughness: 0.40,
    emissive:           new THREE.Color(0x000000),
    emissiveIntensity:  0,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.userData.regionId = regionId;
  mesh.castShadow        = true;
  mesh.receiveShadow     = false;
  mesh.name              = regionId;
  return mesh;
}

// ══════════════════════════════════════════════════════════════════════════════
// MEDIAL CUT FACE (decorative disc — not interactive)
// ══════════════════════════════════════════════════════════════════════════════

function buildMedialFace() {
  const shape = new THREE.Shape();
  const rx = 1.06, ry = 1.22;
  for (let a = 0; a <= Math.PI * 2; a += 0.05) {
    const px = Math.cos(a) * rx;
    const py = Math.sin(a) * ry * (Math.sin(a) < 0 ? 0.68 : 1);
    if (a === 0) shape.moveTo(px, py); else shape.lineTo(px, py);
  }
  shape.closePath();

  const geo = new THREE.ShapeGeometry(shape, 64);
  const mat = new THREE.MeshPhysicalMaterial({
    color:     new THREE.Color(0xA85C40),
    roughness: 0.85,
    metalness: 0.00,
    side:      THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.rotation.y = Math.PI / 2;
  mesh.position.x = 0.032;
  mesh.name = 'medial-face';
  return mesh;
}

// ══════════════════════════════════════════════════════════════════════════════
// CEREBELLUM
// Separate geometry: a foliated, laterally widened sphere with high-frequency
// folia displacement — distinct from the coarser cerebral gyri.
// ══════════════════════════════════════════════════════════════════════════════

function buildCerebellum() {
  const geo = new THREE.SphereGeometry(0.52, 80, 60);
  const pos = geo.attributes.position;

  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);

    // Flatten superior surface (sits below tentorium cerebelli)
    if (y > 0) y *= 0.65;
    // Flatten anterior face (nestles against the brainstem)
    if (z > 0) z *= 0.55;
    // Widen medial-lateral (cerebellum is wider than it is tall)
    x *= 1.38;

    // Fine folial displacement — higher frequency, smaller amplitude than cerebrum
    const r = Math.sqrt(x*x + y*y + z*z) || 1;
    const disp =
      0.024 * Math.sin(x * 20 + 0.40) * Math.sin(y * 16 + 1.20) * Math.sin(z * 18 + 0.80) +
      0.014 * Math.cos(x * 30 + 1.10) * Math.sin(y * 26 + 0.50) * Math.cos(z * 24 + 1.60) +
      0.007 * Math.sin(x * 44 + 0.70) * Math.cos(y * 38 + 1.90);

    x += (x / r) * disp;
    y += (y / r) * disp;
    z += (z / r) * disp;

    pos.setXYZ(i, x, y, z);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();

  const mat = new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(REGION_COLORS.cerebellum),
    roughness:          0.78,
    metalness:          0.00,
    clearcoat:          0.08,
    clearcoatRoughness: 0.50,
    emissive:           new THREE.Color(0x000000),
    emissiveIntensity:  0,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.userData.regionId = 'cerebellum';
  mesh.castShadow = true;
  mesh.name = 'cerebellum';
  // Posterior-inferior, slightly lateral (tucked under occipital lobe)
  mesh.position.set(0.52, -0.60, -1.18);
  mesh.rotation.set(0.18, 0.10, 0.04);
  return mesh;
}

// ══════════════════════════════════════════════════════════════════════════════
// BRAINSTEM
// Tapered cylinder (wider pons superiorly, narrower medulla inferiorly) with
// a slight anterior bow matching real anatomy.
// ══════════════════════════════════════════════════════════════════════════════

function buildBrainstem() {
  // radiusTop = pons (0.22), radiusBottom = medulla (0.16), height = 0.70
  const geo = new THREE.CylinderGeometry(0.22, 0.16, 0.70, 20, 4);

  // Slightly bow the cylinder anteriorly (brainstem curves forward)
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y  = pos.getY(i);
    const ty = (y + 0.35) / 0.70;   // normalised 0 (bottom) → 1 (top)
    pos.setZ(i, pos.getZ(i) + 0.08 * ty);
  }
  pos.needsUpdate = true;
  geo.computeVertexNormals();

  const mat = new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(REGION_COLORS.brainstem),
    roughness:          0.80,
    metalness:          0.00,
    clearcoat:          0.06,
    emissive:           new THREE.Color(0x000000),
    emissiveIntensity:  0,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.userData.regionId = 'brainstem';
  mesh.castShadow = true;
  mesh.name = 'brainstem';
  mesh.position.set(0.20, -0.90, -0.58);
  mesh.rotation.set(-0.22, 0.00, 0.04);
  return mesh;
}

// ══════════════════════════════════════════════════════════════════════════════
// GROUND PLANE (shadow-receiving, invisible)
// ══════════════════════════════════════════════════════════════════════════════

function buildGroundPlane() {
  const geo  = new THREE.PlaneGeometry(8, 8);
  const mat  = new THREE.ShadowMaterial({ opacity: 0.20 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.receiveShadow = true;
  mesh.rotation.x    = -Math.PI / 2;
  mesh.position.y    = -1.06;
  mesh.name = 'ground';
  return mesh;
}

// ══════════════════════════════════════════════════════════════════════════════
// SUBCORTICAL STRUCTURE MESHES
// All 13 structures are built here and stored in a dedicated THREE.Group.
// They start invisible (visible: false); Chunk 2D's glass-brain toggle
// reveals them while fading the cortex to near-transparency.
//
// Structures: hippocampus, amygdala (bilateral), thalamus, hypothalamus,
// mamillary bodies (bilateral), caudate nucleus, putamen, globus pallidus,
// substantia nigra, corpus callosum, fornix, internal capsule.
//
// Coordinate system (brainGroup local space):
//   x  — medial (≈ 0) → lateral (≈ 1.5)
//   y  — inferior (≈ −0.95) → superior (≈ 1.4)
//   z  — posterior (≈ −1.82) → anterior (≈ 1.82)
// ══════════════════════════════════════════════════════════════════════════════

/** Shared material factory for subcortical structures. */
function scMat(color) {
  return new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(color),
    roughness:          0.62,
    metalness:          0.00,
    clearcoat:          0.10,
    clearcoatRoughness: 0.50,
    emissive:           new THREE.Color(0x000000),
    emissiveIntensity:  0,
  });
}

/**
 * Builds all 13 subcortical mesh objects.
 * Returns { group: THREE.Group, meshes: Mesh[] }
 * group is added to brainGroup; meshes are pushed into regionMeshes.
 */
function buildSubcortical() {
  const group  = new THREE.Group();
  group.name   = 'subcortical';
  const meshes = [];

  function reg(mesh, regionId) {
    mesh.userData.regionId = regionId;
    mesh.castShadow        = true;
    mesh.name              = regionId;
    mesh.visible           = false;   // revealed by Chunk 2D glass-brain toggle
    group.add(mesh);
    meshes.push(mesh);
    return mesh;
  }

  // ── 1. Hippocampus (left) — J-shaped TubeGeometry ────────────────────────
  // Runs anterior–posterior in medial temporal lobe; head curves anteriorly.
  {
    const pts = [
      new THREE.Vector3(0.26, -0.14, -0.82),   // tail (posterior)
      new THREE.Vector3(0.28, -0.18, -0.58),   // body
      new THREE.Vector3(0.30, -0.20, -0.32),   // body
      new THREE.Vector3(0.32, -0.22, -0.08),   // body
      new THREE.Vector3(0.34, -0.22,  0.12),   // head approaching
      new THREE.Vector3(0.34, -0.18,  0.30),   // head
      new THREE.Vector3(0.32, -0.14,  0.38),   // head tip
    ];
    const curve = new THREE.CatmullRomCurve3(pts);
    const geo   = new THREE.TubeGeometry(curve, 60, 0.075, 8, false);
    reg(new THREE.Mesh(geo, scMat(0x8B4080)), 'hippocampus');
  }

  // ── 2. Amygdala — bilateral small spheres ────────────────────────────────
  // Left: anterior to hippocampal head, medial temporal. Right: mirrored.
  {
    const geoA  = new THREE.SphereGeometry(0.18, 18, 14);
    const left  = new THREE.Mesh(geoA, scMat(0x7A3040));
    left.position.set(0.34, -0.06, 0.40);
    reg(left, 'amygdala');

    const geoB  = new THREE.SphereGeometry(0.18, 18, 14);
    const right = new THREE.Mesh(geoB, scMat(0x7A3040));
    right.position.set(-0.34, -0.06, 0.40);   // contralateral (behind medial face)
    reg(right, 'amygdala');
  }

  // ── 3. Thalamus (left) — flattened sphere ────────────────────────────────
  // Central relay station; egg-shaped, 0.30 × 0.24 × 0.20 half-axes.
  {
    const geo  = new THREE.SphereGeometry(1, 32, 24);
    const mesh = new THREE.Mesh(geo, scMat(0x4A7098));
    mesh.scale.set(0.30, 0.24, 0.20);
    mesh.position.set(0.24, 0.26, -0.22);
    reg(mesh, 'thalamus');
  }

  // ── 4. Hypothalamus — small sphere ───────────────────────────────────────
  // Inferior to thalamus, above brainstem; autonomic + endocrine master.
  {
    const geo  = new THREE.SphereGeometry(0.14, 18, 14);
    const mesh = new THREE.Mesh(geo, scMat(0x7A5080));
    mesh.position.set(0.16, -0.10, -0.16);
    reg(mesh, 'hypothalamus');
  }

  // ── 5. Mamillary bodies — bilateral pairs ────────────────────────────────
  // Two small spheres at the posterior floor of the hypothalamus.
  {
    const geoM = new THREE.SphereGeometry(0.09, 14, 10);
    const mLeft  = new THREE.Mesh(geoM, scMat(0xB89080));
    const mRight = new THREE.Mesh(geoM.clone(), scMat(0xB89080));
    mLeft.position.set( 0.12, -0.22, -0.36);
    mRight.position.set(-0.12, -0.22, -0.36);
    reg(mLeft,  'mamillary_bodies');
    reg(mRight, 'mamillary_bodies');
  }

  // ── 6. Caudate nucleus (left) — C-shaped TubeGeometry ────────────────────
  // Head (frontal) → body (follows lateral ventricle) → tail (temporal).
  {
    const pts = [
      new THREE.Vector3(0.44,  0.26,  0.62),   // head (anterior-frontal)
      new THREE.Vector3(0.42,  0.36,  0.38),   // head–body junction
      new THREE.Vector3(0.40,  0.40,  0.12),   // body
      new THREE.Vector3(0.38,  0.40, -0.12),   // body
      new THREE.Vector3(0.36,  0.30, -0.36),   // body–tail
      new THREE.Vector3(0.35,  0.12, -0.52),   // tail
      new THREE.Vector3(0.35, -0.06, -0.54),   // tail
      new THREE.Vector3(0.35, -0.18, -0.40),   // tail tip (temporal)
    ];
    const curve = new THREE.CatmullRomCurve3(pts);
    const geo   = new THREE.TubeGeometry(curve, 80, 0.09, 8, false);
    reg(new THREE.Mesh(geo, scMat(0xB06820)), 'caudate');
  }

  // ── 7. Putamen (left) — flattened sphere ─────────────────────────────────
  // Lateral to globus pallidus; sensorimotor striatum.
  {
    const geo  = new THREE.SphereGeometry(1, 28, 22);
    const mesh = new THREE.Mesh(geo, scMat(0x9A5A18));
    mesh.scale.set(0.22, 0.28, 0.18);
    mesh.position.set(0.56, 0.18, 0.08);
    reg(mesh, 'putamen');
  }

  // ── 8. Globus pallidus (left) — small sphere ─────────────────────────────
  // Medial to putamen; basal ganglia output.
  {
    const geo  = new THREE.SphereGeometry(0.14, 18, 14);
    const mesh = new THREE.Mesh(geo, scMat(0x887024));
    mesh.position.set(0.40, 0.18, 0.06);
    reg(mesh, 'globus_pallidus');
  }

  // ── 9. Substantia nigra (left) — thin pigmented cylinder ─────────────────
  // In midbrain tegmentum; pars compacta (dopaminergic) is the affected region
  // in Parkinson's disease; modeled as a thin, very dark cylinder.
  {
    const geo  = new THREE.CylinderGeometry(0.05, 0.06, 0.26, 12);
    const mesh = new THREE.Mesh(geo, scMat(0x241810));
    mesh.position.set(0.20, -0.72, -0.44);
    mesh.rotation.set(-0.22, 0.00, 0.04);   // slight anterior tilt matching brainstem
    reg(mesh, 'substantia_nigra');
  }

  // ── 10. Corpus callosum — arching TorusGeometry in sagittal plane ─────────
  // Large myelinated commissure connecting hemispheres. Ring radius 0.70,
  // tube radius 0.07. Rotated so the ring lies in the YZ (sagittal) plane.
  {
    const geo  = new THREE.TorusGeometry(0.70, 0.07, 6, 60);
    const mesh = new THREE.Mesh(geo, scMat(0xD8C8A4));
    mesh.rotation.y = Math.PI / 2;   // ring in YZ sagittal plane
    mesh.position.set(0.04, 0.52, -0.06);
    reg(mesh, 'corpus_callosum');
  }

  // ── 11. Fornix — arching TubeGeometry from hippocampus to mamillary bodies ─
  // Crus → body (arches over thalamus) → columns → mamillary bodies.
  {
    const pts = [
      new THREE.Vector3(0.24, -0.08, -0.64),   // hippocampal fimbria
      new THREE.Vector3(0.18,  0.18, -0.48),   // crus fornicis ascending
      new THREE.Vector3(0.10,  0.65, -0.22),   // arch (superior to thalamus)
      new THREE.Vector3(0.08,  0.70,  0.00),   // body (peak)
      new THREE.Vector3(0.08,  0.68,  0.18),   // body anterior
      new THREE.Vector3(0.10,  0.40,  0.08),   // column descending
      new THREE.Vector3(0.12,  0.18, -0.06),   // column
      new THREE.Vector3(0.12, -0.02, -0.20),   // column inferior
      new THREE.Vector3(0.12, -0.20, -0.36),   // mamillary body target
    ];
    const curve = new THREE.CatmullRomCurve3(pts);
    const geo   = new THREE.TubeGeometry(curve, 80, 0.04, 6, false);
    reg(new THREE.Mesh(geo, scMat(0xC4B490)), 'fornix');
  }

  // ── 12. Internal capsule (left) — flattened box ───────────────────────────
  // V-shaped white matter band between thalamus and lenticular nucleus.
  // Spec calls for BoxGeometry "tapered"; modeled as a rotated flat box.
  {
    const geo  = new THREE.BoxGeometry(0.10, 0.44, 0.10);
    const mesh = new THREE.Mesh(geo, scMat(0xCCBCA0));
    mesh.position.set(0.32, 0.22, -0.08);
    mesh.rotation.set(0.06, 0.00, -0.12);
    reg(mesh, 'internal_capsule');
  }

  return { group, meshes };
}

// ══════════════════════════════════════════════════════════════════════════════
// ASSEMBLE SCENE
// ══════════════════════════════════════════════════════════════════════════════

// Build the master hemisphere geometry once (shared for all cortical carving)
const hemiGeo = buildHemisphereGeo();

// 9 cortical regions carved from the hemisphere
const CORTICAL_IDS = [
  'frontal_lobe', 'prefrontal_cortex', 'brocas_area', 'motor_cortex',
  'parietal_lobe', 'somatosensory_cortex', 'temporal_lobe', 'wernickes_area',
  'occipital_lobe',
];

const brainGroup   = new THREE.Group();
const regionMeshes = [];   // all interactive meshes for raycasting (cortical + subcortical)

for (const rid of CORTICAL_IDS) {
  const m = buildRegionMesh(hemiGeo, rid);
  if (m) { brainGroup.add(m); regionMeshes.push(m); }
}

// Separate cerebellum + brainstem meshes
const cerebellumMesh = buildCerebellum();
const brainstemMesh  = buildBrainstem();
brainGroup.add(cerebellumMesh); regionMeshes.push(cerebellumMesh);
brainGroup.add(brainstemMesh);  regionMeshes.push(brainstemMesh);

// Capture the 11 cortical meshes for Chunk 2D glass-brain toggle
const corticalMeshes = regionMeshes.slice();

// Build and attach 13 subcortical structures (all hidden by default)
const { group: subcorticalGroup, meshes: subcorticalMeshes } = buildSubcortical();
brainGroup.add(subcorticalGroup);
// Add to regionMeshes so raycasting includes them once visible
regionMeshes.push(...subcorticalMeshes);

// ── Pathology auxiliary mesh: lateral ventricle (Chunk 4B — Huntington's) ────
// Follows the caudate arc, positioned just superior and medial to it. Normally
// near-invisible (scale 0.01); expands during Huntington's pathology to show
// hydrocephalus ex vacuo — the vacated CSF space as the caudate shrinks.
// NOT added to regionMeshes (non-interactive; raycasting would be confusing here).
let lateralVentricleMesh = null;
{
  const pts = [
    new THREE.Vector3( 0.40,  0.42,  0.68),  // frontal horn
    new THREE.Vector3( 0.42,  0.52,  0.44),  // body (arches over caudate head)
    new THREE.Vector3( 0.40,  0.56,  0.18),  // body
    new THREE.Vector3( 0.38,  0.56, -0.08),  // posterior body
    new THREE.Vector3( 0.36,  0.50, -0.34),  // atrium (junction of horns)
    new THREE.Vector3( 0.35,  0.30, -0.54),  // temporal horn entry
    new THREE.Vector3( 0.35,  0.10, -0.58),  // temporal horn
    new THREE.Vector3( 0.35, -0.08, -0.44),  // temporal horn tip (near hippocampus)
  ];
  const curve = new THREE.CatmullRomCurve3(pts);
  const geo   = new THREE.TubeGeometry(curve, 80, 0.07, 8, false);
  const mat   = new THREE.MeshPhysicalMaterial({
    color:       new THREE.Color(0x60C0E8),   // CSF light blue
    roughness:   0.08,
    metalness:   0.12,
    transparent: true,
    opacity:     0.62,
    side:        THREE.DoubleSide,
  });
  lateralVentricleMesh = new THREE.Mesh(geo, mat);
  lateralVentricleMesh.scale.setScalar(0.01);  // near-invisible until pathology fires
  lateralVentricleMesh.visible = false;
  brainGroup.add(lateralVentricleMesh);
}

// Medial cut-face disc (non-interactive decoration)
brainGroup.add(buildMedialFace());

brainGroup.rotation.y = -0.28;   // Initial pose: slight rotation showing temporal lobe
scene.add(brainGroup);
scene.add(buildGroundPlane());

// ══════════════════════════════════════════════════════════════════════════════
// POST-PROCESSING — OutlinePass for gold region selection glow
// ══════════════════════════════════════════════════════════════════════════════

const renderPass  = new RenderPass(scene, camera);

const outlinePass = new OutlinePass(
  new THREE.Vector2(700, 455),   // initial size; updated in handleResize
  scene, camera
);
outlinePass.edgeStrength            = 3.8;
outlinePass.edgeGlow                = 0.4;
outlinePass.edgeThickness           = 1.8;
outlinePass.pulsePeriod             = 0;    // no pulsing — steady gold outline
outlinePass.visibleEdgeColor.set('#d4a054');   // gold
outlinePass.hiddenEdgeColor.set('#7a5820');    // darker gold (occluded edge)
outlinePass.selectedObjects         = [];

const outputPass = new OutputPass();   // final sRGB conversion

composer.addPass(renderPass);
composer.addPass(outlinePass);
composer.addPass(outputPass);

// ══════════════════════════════════════════════════════════════════════════════
// INTERACTION STATE — hover + click via raycasting
// ══════════════════════════════════════════════════════════════════════════════

const raycaster = new THREE.Raycaster();
const mouseNDC  = new THREE.Vector2(-10, -10);   // off-screen until first move

let hoveredMesh  = null;
let selectedMesh = null;

/** Set hover emissive on new mesh, clear previous (skip if already selected). */
function setHover(mesh) {
  if (hoveredMesh === mesh) return;
  if (hoveredMesh && hoveredMesh !== selectedMesh) {
    hoveredMesh.material.emissiveIntensity = 0;
  }
  hoveredMesh = mesh;
  if (hoveredMesh && hoveredMesh !== selectedMesh) {
    hoveredMesh.material.emissive.set(0xffffff);
    hoveredMesh.material.emissiveIntensity = 0.18;
  }
}

/**
 * Select a region mesh: apply gold OutlinePass + emissive tint, open info panel.
 * Passing null clears selection.
 */
function selectRegion(mesh) {
  // Lesion mode: clicks toggle damage instead of opening the info panel
  if (lesionActive) {
    if (mesh) toggleDamageRegion(mesh);
    return;
  }

  if (selectedMesh === mesh) return;

  // Clear previous selection's emissive + outline
  if (selectedMesh) {
    selectedMesh.material.emissive.set(0x000000);
    selectedMesh.material.emissiveIntensity = 0;
    outlinePass.selectedObjects = [];
  }

  selectedMesh = mesh;
  if (!mesh) return;

  outlinePass.selectedObjects = [mesh];
  mesh.material.emissive.set(0xd4a054);    // warm gold tint on selected region
  mesh.material.emissiveIntensity = 0.12;

  // Populate info panel via bridge exposed by brain-exercise.html
  if (window.__brainUI) {
    window.__brainUI.openRegion(mesh.userData.regionId);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// ANIMATION LOOP
// ══════════════════════════════════════════════════════════════════════════════

let animFrameId = null;
let autoRotate  = true;
let lastTs      = 0;
let idleTimer   = null;

// ── Lesion Simulator state ────────────────────────────────────────────────────
let lesionActive   = false;        // true = clicking a region applies damage
let damagedRegions = new Set();    // Set<regionId> of currently-damaged regions
let lesionPulseT   = 0;            // phase (radians) for pulsing red emissive

// ── Pathology Overlay state (Chunk 4A) ────────────────────────────────────────
let activePathology = null;    // string key of active pathology, or null
let pathologyT      = 0.0;     // lerp progress: 0 = normal state, 1 = fully affected
let pathologyDir    = 0;       // +1 = animating toward affected, -1 = returning to normal

// ── Glass-brain toggle state ──────────────────────────────────────────────────
let glassActive     = false;  // true = subcortical revealed
let glassProgress   = 0;      // 0 = full cortex, 1 = glass
let glassTweenStart = -1;     // rAF timestamp at tween start; -1 = idle
const GLASS_DURATION = 600;   // ms for full cortex ↔ glass transition

/** Apply glass progress t (0→1) to material opacity on all region meshes. */
function applyGlassProgress(t) {
  const corticalOpacity    = 1.0 - 0.82 * t;   // 1.0 → 0.18
  const subcorticalOpacity = t;                  // 0   → 1.0
  corticalMeshes.forEach(m => {
    m.material.opacity     = corticalOpacity;
    m.material.transparent = t > 0;
    m.material.depthWrite  = t < 0.5;            // avoid z-fighting once semi-transparent
  });
  subcorticalMeshes.forEach(m => {
    m.visible              = t > 0;
    m.material.opacity     = subcorticalOpacity;
  });
}

/** Toggle between opaque-cortex and glass-brain states; drives the tween. */
function toggleGlass() {
  glassActive     = !glassActive;
  glassTweenStart = performance.now();
  const btn = document.getElementById('btn-glass-brain');
  if (btn) btn.classList.toggle('active', glassActive);
}

// ══════════════════════════════════════════════════════════════════════════════
// CROSS-SECTION SLIDER (Chunk 2E)
// ══════════════════════════════════════════════════════════════════════════════
//
// THREE.Plane(normal, constant): kept geometry satisfies  normal·p + constant ≥ 0
//   i.e., normal·p ≥ −constant.
//
// Axis conventions (brainGroup local space):
//   axial    normal=(0,−1,0): keeps y ≤ d  (everything below the horizontal cut)
//   coronal  normal=(0,0,−1): keeps z ≤ d  (posterior to the coronal cut)
//   sagittal normal=(−1,0,0): keeps x ≤ d  (medial portion, sweeping from lateral)
//
// The clip plane is stored in world space and recomputed every frame so it
// follows the brainGroup as it auto-rotates or the user manually orbits.
// ─────────────────────────────────────────────────────────────────────────────

let csMode   = null;   // 'axial' | 'coronal' | 'sagittal' | null
let csSlider = 50;     // 0–100

const CS_AXES = {
  //              localNormal                              far    near
  axial:    { localNormal: new THREE.Vector3( 0, -1,  0), far:  1.6, near: -1.1 },
  coronal:  { localNormal: new THREE.Vector3( 0,  0, -1), far:  2.0, near: -2.0 },
  sagittal: { localNormal: new THREE.Vector3(-1,  0,  0), far:  1.7, near: -0.1 },
};

// Single shared world-space plane — updated every frame inside animate().
const csClipPlane = new THREE.Plane();

// Semi-transparent disc rendered at the cut face (world space, not in brainGroup).
let discMesh = null;

/** Build and add the cut-face indicator disc to the world scene. */
function buildCrossDisc() {
  const geo = new THREE.CircleGeometry(2.2, 64);
  const mat = new THREE.MeshBasicMaterial({
    color:       0xE8D8C4,   // warm white-matter / sulcal-interior tone
    transparent: true,
    opacity:     0.28,
    side:        THREE.DoubleSide,
    depthWrite:  false,
    // clippingPlanes intentionally absent — disc is never clipped
  });
  const mesh  = new THREE.Mesh(geo, mat);
  mesh.visible      = false;
  mesh.renderOrder  = 1;   // render after opaque brain surfaces
  scene.add(mesh);         // world-space; positioned each frame by updateCrossSection()
  return mesh;
}

/** Assign csClipPlane to every region mesh material. */
function activateClipping() {
  regionMeshes.forEach(m => {
    m.material.clippingPlanes = [csClipPlane];
    m.material.needsUpdate    = true;
  });
  if (discMesh) discMesh.visible = true;
}

/** Remove csClipPlane from every region mesh material. */
function deactivateClipping() {
  regionMeshes.forEach(m => {
    m.material.clippingPlanes = [];
    m.material.needsUpdate    = true;
  });
  if (discMesh) discMesh.visible = false;
}

/**
 * Recompute the world-space clip plane and disc transform from the current
 * csSlider value and brainGroup's live world matrix.  Called every frame.
 */
function updateCrossSection() {
  if (!csMode) return;

  const ax  = CS_AXES[csMode];
  const t   = csSlider / 100;

  // Lerp from far edge (t=0 → whole brain visible) to near edge (t=1 → most clipped)
  const d   = ax.far + (ax.near - ax.far) * t;

  // A point on the local-space plane (localNormal·p₀ + d = 0 → p₀ = localNormal·(−d))
  const localPt = ax.localNormal.clone().multiplyScalar(-d);
  const worldPt = localPt.clone().applyMatrix4(brainGroup.matrixWorld);

  // Rotate local normal to world space
  const worldN = ax.localNormal.clone()
    .transformDirection(brainGroup.matrixWorld)
    .normalize();

  // World-space plane: worldN·x + c = 0,  c = −worldN·worldPt
  csClipPlane.normal.copy(worldN);
  csClipPlane.constant = -worldN.dot(worldPt);

  // Position and orient the cut-face disc
  if (discMesh && discMesh.visible) {
    discMesh.position.copy(worldPt);
    discMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), worldN);
  }
}

/**
 * Activate a cross-section axis.  Clicking the currently-active axis toggles off.
 * Exposed via window.__brain3d and called from the HTML axis buttons.
 */
function setCsMode(mode) {
  if (csMode === mode) mode = null;   // toggle off

  // Sync axis button active states + slider visibility
  document.querySelectorAll('.cs-axis-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.axis === mode);
  });
  const sliderEl = document.getElementById('cs-slider');
  if (sliderEl) sliderEl.style.display = mode ? '' : 'none';

  const wasActive = !!csMode;
  csMode = mode;

  if (mode) {
    if (!wasActive) activateClipping();   // first activation — assign planes to materials
    updateCrossSection();                 // apply current slider value immediately
  } else {
    deactivateClipping();
  }
}

/** Update the cut plane to the new slider value (0–100). */
function setCsSlider(value) {
  csSlider = +value;
  if (csMode) updateCrossSection();
}

// ══════════════════════════════════════════════════════════════════════════════
// VASCULAR TERRITORY OVERLAY (Chunk 3A)
// ══════════════════════════════════════════════════════════════════════════════
//
// Territory assignments follow standard clinical neuroanatomy (EPPP-level):
//   MCA — lateral frontal, motor/sensory strip (arm/face), Broca, parietal, temporal, Wernicke
//   ACA — medial frontal / orbitofrontal (prefrontal_cortex in our model)
//   PCA — occipital (primary visual cortex and association areas)
//
// Overlays are clones of each cortical mesh's geometry rendered with a transparent
// MeshBasicMaterial using polygonOffset to avoid z-fighting with the underlying mesh.
// Overlay groups are lazily built on first call to setVascTerritory().
// ─────────────────────────────────────────────────────────────────────────────

const VASC_MAP = {
  frontal_lobe:         'mca',
  motor_cortex:         'mca',
  somatosensory_cortex: 'mca',
  brocas_area:          'mca',
  parietal_lobe:        'mca',
  temporal_lobe:        'mca',
  wernickes_area:       'mca',
  prefrontal_cortex:    'aca',
  occipital_lobe:       'pca',
  // cerebellum + brainstem = vertebrobasilar (not shown in MCA/ACA/PCA toggle)
};

const VASC_3D_COLORS = {
  mca: new THREE.Color(0xEF4444),   // rose-red
  aca: new THREE.Color(0x4ADE80),   // green
  pca: new THREE.Color(0xA78BFA),   // violet
};

let vasc3dGroups = null;   // { mca: Group, aca: Group, pca: Group } — built lazily

/** Build one transparent overlay mesh per cortical region and group by territory. */
function buildVasc3dGroups() {
  const groups = {};
  for (const id of Object.keys(VASC_3D_COLORS)) {
    const grp    = new THREE.Group();
    grp.name     = 'vasc_' + id;
    grp.visible  = false;
    brainGroup.add(grp);
    groups[id]   = grp;
  }

  corticalMeshes.forEach(m => {
    const terr = VASC_MAP[m.userData.regionId];
    if (!terr) return;   // cerebellum / brainstem — skip

    const mat = new THREE.MeshBasicMaterial({
      color:               VASC_3D_COLORS[terr],
      transparent:         true,
      opacity:             0.36,
      depthWrite:          false,
      side:                THREE.FrontSide,
      polygonOffset:       true,       // prevent z-fighting with underlying region mesh
      polygonOffsetFactor: -2,
      polygonOffsetUnits:  -2,
    });

    // Share the source geometry (no copy) — transforms duplicated from original mesh.
    const clone = new THREE.Mesh(m.geometry, mat);
    clone.position.copy(m.position);
    clone.rotation.copy(m.rotation);
    clone.scale.copy(m.scale);
    clone.renderOrder = 2;   // after region meshes (0) and cross-section disc (1)
    groups[terr].add(clone);
  });

  return groups;
}

/**
 * Show/hide vascular territory overlay groups.
 * mode: 'off' | 'mca' | 'aca' | 'pca' | 'all'
 * Called via window.__brain3d.setVascTerritory() from applyVascOverlay() in brain-exercise.html.
 */
function setVascTerritory(mode) {
  if (!vasc3dGroups) vasc3dGroups = buildVasc3dGroups();   // lazy first build
  const { mca, aca, pca } = vasc3dGroups;
  if (mode === 'off') {
    mca.visible = aca.visible = pca.visible = false;
  } else if (mode === 'all') {
    mca.visible = aca.visible = pca.visible = true;
  } else {
    mca.visible = mode === 'mca';
    aca.visible = mode === 'aca';
    pca.visible = mode === 'pca';
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// PATHWAY ANIMATION ENGINE — Chunk 3B
// Generic class for animated neural pathway tracts with flowing signal particles.
// Chunk 3C / 3D instantiate concrete pathways; this file only defines the engine.
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Renders a neural pathway as:
 *   1. A semi-transparent TubeGeometry (static tract anatomy)
 *   2. Glowing signal particles flowing along the tract each frame
 *
 * Particles are evenly pre-spaced on the curve so they never bunch up.
 * The tube is exempt from clipping planes (renderOrder 3) so it reads clearly
 * even when the cross-section slider is active.
 *
 * Usage (Chunk 3C/3D):
 *   const p = new Pathway({ name: 'corticospinal', waypoints: [...], color: 0xf59e0b });
 *   pathways.push(p);
 *   scene.add(p.group);   // attach to world scene, NOT brainGroup
 *   p.show();
 */
class Pathway {
  /**
   * @param {object}            opts
   * @param {string}            opts.name          Identifier (e.g. 'corticospinal')
   * @param {THREE.Vector3[]}   opts.waypoints     ≥2 world-space control points
   * @param {number}            opts.color         Hex color (e.g. 0xf59e0b)
   * @param {number}            [opts.speed=0.18]  Fraction of curve travelled per second
   * @param {number}            [opts.particleCount=20]  Simultaneous flowing particles
   * @param {number}            [opts.radius=0.022]      Tube radius (world units)
   * @param {boolean}           [opts.loop=false]  Closed curve (use two instances for
   *                                               bidirectional tracts instead)
   */
  constructor({ name, waypoints, color, speed = 0.18, particleCount = 20, radius = 0.022, loop = false }) {
    this.name  = name;
    this.speed = speed;
    this.n     = particleCount;
    this.loop  = loop;
    this._t    = 0;   // master phase, advances each frame, wraps at 1.0

    // ─── Curve ─────────────────────────────────────────────────────────────
    this.curve = new THREE.CatmullRomCurve3(waypoints, loop, 'catmullrom', 0.5);

    // Evenly pre-spaced offsets so particles are uniformly distributed at t=0
    this._offsets = new Float32Array(particleCount);
    for (let i = 0; i < particleCount; i++) this._offsets[i] = i / particleCount;

    const tColor = new THREE.Color(color);
    this.group   = new THREE.Group();
    this.group.visible = false;

    // ─── Tube (static anatomy visualization) ───────────────────────────────
    const tubeGeo = new THREE.TubeGeometry(this.curve, 80, radius, 6, loop);
    const tubeMat = new THREE.MeshPhysicalMaterial({
      color:             tColor,
      emissive:          tColor,
      emissiveIntensity: 0.28,
      transparent:       true,
      opacity:           0.38,
      depthWrite:        false,
      metalness:         0,
      roughness:         0.55,
    });
    this._tube             = new THREE.Mesh(tubeGeo, tubeMat);
    this._tube.renderOrder = 3;
    this.group.add(this._tube);

    // ─── Particles (flowing signal) ─────────────────────────────────────────
    const posArr     = new Float32Array(particleCount * 3);
    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));

    const particleMat = new THREE.PointsMaterial({
      color:           tColor,
      size:            0.068,
      map:             Pathway._particleTex(),
      transparent:     true,
      opacity:         0.92,
      blending:        THREE.AdditiveBlending,
      depthWrite:      false,
      sizeAttenuation: true,
    });

    this._points             = new THREE.Points(particleGeo, particleMat);
    this._points.renderOrder = 4;
    this._posAttr            = particleGeo.getAttribute('position');
    this.group.add(this._points);
  }

  /** Advance particle positions by `delta` seconds. Call once per animate() frame. */
  animate(delta) {
    if (!this.group.visible) return;
    this._t = (this._t + delta * this.speed) % 1.0;
    const pt = new THREE.Vector3();
    for (let i = 0; i < this.n; i++) {
      this.curve.getPoint((this._t + this._offsets[i]) % 1.0, pt);
      this._posAttr.setXYZ(i, pt.x, pt.y, pt.z);
    }
    this._posAttr.needsUpdate = true;
  }

  show()    { this.group.visible = true;  }
  hide()    { this.group.visible = false; }

  dispose() {
    this._tube.geometry.dispose();
    this._tube.material.dispose();
    this._points.geometry.dispose();
    this._points.material.dispose();
    // Shared particle texture is NOT disposed here — use Pathway._tex = null to free globally
  }

  // ─── Shared particle texture (canvas radial gradient, created once) ─────────
  static _tex = null;
  static _particleTex() {
    if (Pathway._tex) return Pathway._tex;
    const size   = 64;
    const cvs    = document.createElement('canvas');
    cvs.width    = cvs.height = size;
    const ctx    = cvs.getContext('2d');
    const half   = size / 2;
    const grad   = ctx.createRadialGradient(half, half, 0, half, half, half);
    grad.addColorStop(0.0, 'rgba(255,255,255,1.0)');
    grad.addColorStop(0.3, 'rgba(255,255,255,0.7)');
    grad.addColorStop(1.0, 'rgba(255,255,255,0.0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, size, size);
    Pathway._tex = new THREE.CanvasTexture(cvs);
    return Pathway._tex;
  }
}

/** All registered pathway instances.  Populated in Chunk 3C / 3D. */
const pathways = [];

function showPathway(name) { pathways.find(p => p.name === name)?.show(); }
function hidePathway(name) { pathways.find(p => p.name === name)?.hide(); }
function hideAllPathways() { pathways.forEach(p => p.hide()); }

// ── Chunk 3C: Papez Circuit ──────────────────────────────────────────────────
// Limbic memory circuit: hippocampus → fimbria → fornix arch → mamillary
// bodies → mamillothalamic tract → anterior thalamus → thalamocingulate
// radiation → cingulate gyrus → cingulum bundle → entorhinal cortex →
// hippocampus.  Loop, amber-gold, slow (learning / consolidation tempo).
//
// All waypoints are in brainGroup LOCAL space so the circuit rotates with the
// brain.  (pathway.group is added to brainGroup, not to scene.)
{
  const p = new Pathway({
    name:          'papez',
    color:         0xD4A054,
    speed:         0.14,       // 14 % of curve per second — unhurried
    particleCount: 28,
    radius:        0.020,
    loop:          true,
    waypoints: [
      new THREE.Vector3( 0.30, -0.16,  0.12),   // hippocampus body (mid-shaft)
      new THREE.Vector3( 0.26, -0.08, -0.60),   // fimbria of fornix (posterior)
      new THREE.Vector3( 0.18,  0.22, -0.46),   // crus fornicis ascending
      new THREE.Vector3( 0.10,  0.68, -0.08),   // fornix body — arch peak
      new THREE.Vector3( 0.10,  0.44,  0.06),   // column of fornix descending
      new THREE.Vector3( 0.12,  0.06, -0.12),   // column inferior
      new THREE.Vector3( 0.12, -0.22, -0.36),   // mamillary bodies
      new THREE.Vector3( 0.20,  0.10, -0.20),   // mamillothalamic tract
      new THREE.Vector3( 0.22,  0.28, -0.04),   // anterior thalamic nucleus
      new THREE.Vector3( 0.08,  0.90,  0.08),   // cingulate gyrus (medial cortex)
      new THREE.Vector3( 0.22,  0.48,  0.52),   // cingulum bundle → posterior
      new THREE.Vector3( 0.30, -0.08,  0.56),   // entorhinal / parahippocampal gyrus
      new THREE.Vector3( 0.32, -0.16,  0.32),   // hippocampus head (closes loop)
    ],
  });
  pathways.push(p);
  brainGroup.add(p.group);   // add to brainGroup — rotates with brain
}

// ── Chunk 3C: Corticospinal (Pyramidal) Tract ────────────────────────────────
// Primary motor pathway: motor cortex → corona radiata → internal capsule
// (posterior limb) → cerebral peduncle (midbrain) → pontine corticospinal
// fibers → medullary pyramid → pyramidal decussation → spinal cord.
// One-way, steel blue, faster tempo (rapid motor signal).
{
  const p = new Pathway({
    name:          'corticospinal',
    color:         0x5B9BD5,
    speed:         0.22,       // 22 % of curve per second — fast motor signal
    particleCount: 18,
    radius:        0.018,
    loop:          false,
    waypoints: [
      new THREE.Vector3( 0.62,  0.90,  0.22),   // motor cortex (precentral gyrus)
      new THREE.Vector3( 0.52,  0.64,  0.14),   // corona radiata (superior)
      new THREE.Vector3( 0.40,  0.40,  0.02),   // corona radiata (inferior)
      new THREE.Vector3( 0.32,  0.22, -0.08),   // internal capsule — posterior limb
      new THREE.Vector3( 0.26,  0.00, -0.18),   // cerebral peduncle (midbrain)
      new THREE.Vector3( 0.22, -0.72, -0.44),   // pontine corticospinal fibers
      new THREE.Vector3( 0.20, -0.92, -0.54),   // medullary pyramid
      new THREE.Vector3( 0.18, -1.12, -0.62),   // pyramidal decussation / spinal cord
    ],
  });
  pathways.push(p);
  brainGroup.add(p.group);   // add to brainGroup — rotates with brain
}

// ── Chunk 3D: Visual Pathway — Temporal (Uncrossed) Fibers ──────────────────
// Left temporal retinal fibers run IPSILATERALLY: left retina → optic nerve →
// lateral optic chiasm (no crossing) → left LGN → optic radiations →
// Meyer's loop (anterior temporal sweep, explains "pie in the sky" deficit) →
// left V1.  Warm pink #F4A0C0.
//
// KEY EDUCATIONAL POINT: visual_temporal + visual_nasal converge on the SAME
// left LGN → V1, so damage to left V1 causes RIGHT homonymous hemianopia from
// BOTH eyes — that's the anatomy of homonymous field defects.
{
  const p = new Pathway({
    name:          'visual_temporal',
    color:         0xF4A0C0,
    speed:         0.28,       // fast — visual processing is rapid (< 100 ms)
    particleCount: 22,
    radius:        0.016,
    loop:          false,
    waypoints: [
      new THREE.Vector3( 0.72,  0.00,  2.04),   // left retina / eye
      new THREE.Vector3( 0.56, -0.08,  1.52),   // left optic nerve
      new THREE.Vector3( 0.38, -0.16,  0.90),   // optic nerve approaching chiasm
      new THREE.Vector3( 0.20, -0.30,  0.14),   // optic chiasm — temporal fibers (lateral, no cross)
      new THREE.Vector3( 0.46,  0.08, -0.36),   // left LGN (posterolateral thalamus)
      new THREE.Vector3( 0.72, -0.10, -0.20),   // entering optic radiations — temporal lobe
      new THREE.Vector3( 0.80, -0.28,  0.08),   // Meyer's loop — anterior temporal sweep
      new THREE.Vector3( 0.78, -0.20, -0.34),   // Meyer's loop — curving posterior
      new THREE.Vector3( 0.80,  0.08, -0.82),   // optic radiations ascending toward V1
      new THREE.Vector3( 0.78,  0.30, -1.12),   // optic radiations posterior
      new THREE.Vector3( 0.75,  0.50, -1.40),   // V1 (primary visual cortex, calcarine sulcus)
    ],
  });
  pathways.push(p);
  brainGroup.add(p.group);
  // Left retina sphere — attached to pathway group so it shows/hides with the pathway
  const lRet = new THREE.Mesh(
    new THREE.SphereGeometry(0.055, 12, 8),
    new THREE.MeshBasicMaterial({ color: 0xF4A0C0, transparent: true, opacity: 0.90 })
  );
  lRet.position.set(0.72, 0.00, 2.04);
  p.group.add(lRet);
}

// ── Chunk 3D: Visual Pathway — Nasal (Crossed) Fibers ────────────────────────
// Right nasal retinal fibers CROSS the optic chiasm at the midline, then join
// the left LGN → Meyer's loop → left V1 — the same destination as the temporal
// pathway.  Teal #60C8C0.
// Crossing segment: x goes -0.38 → 0.00 → +0.46 (right → midline → left LGN).
{
  const p = new Pathway({
    name:          'visual_nasal',
    color:         0x60C8C0,
    speed:         0.28,
    particleCount: 22,
    radius:        0.016,
    loop:          false,
    waypoints: [
      new THREE.Vector3(-0.72,  0.00,  2.04),   // right retina (contralateral)
      new THREE.Vector3(-0.56, -0.08,  1.52),   // right optic nerve
      new THREE.Vector3(-0.38, -0.16,  0.90),   // approaching chiasm from right
      new THREE.Vector3( 0.00, -0.30,  0.14),   // optic chiasm — nasal fibers CROSS midline
      new THREE.Vector3( 0.46,  0.08, -0.36),   // left LGN (converges with temporal stream)
      new THREE.Vector3( 0.72, -0.10, -0.20),   // optic radiations — temporal lobe
      new THREE.Vector3( 0.80, -0.28,  0.08),   // Meyer's loop — anterior sweep
      new THREE.Vector3( 0.78, -0.20, -0.34),   // Meyer's loop — curving posterior
      new THREE.Vector3( 0.80,  0.08, -0.82),   // optic radiations ascending
      new THREE.Vector3( 0.78,  0.30, -1.12),   // optic radiations posterior
      new THREE.Vector3( 0.75,  0.50, -1.40),   // V1 (same destination as temporal)
    ],
  });
  pathways.push(p);
  brainGroup.add(p.group);
  // Right retina sphere
  const rRet = new THREE.Mesh(
    new THREE.SphereGeometry(0.055, 12, 8),
    new THREE.MeshBasicMaterial({ color: 0x60C8C0, transparent: true, opacity: 0.90 })
  );
  rRet.position.set(-0.72, 0.00, 2.04);
  p.group.add(rRet);
}

// ── Chunk 3D: Language Pathway — Arcuate Fasciculus ──────────────────────────
// Left-hemisphere language circuit: Wernicke's area (BA22, posterior STG) →
// arcuate fasciculus (C-shaped white matter arc through parietal operculum) →
// Broca's area (BA44/45, inferior frontal gyrus) → primary motor cortex
// (larynx/lip representation, lateral precentral).
// Damage to the arc alone = conduction aphasia (impaired repetition, fluent
// speech, intact comprehension).  Violet #9060D0.
{
  const p = new Pathway({
    name:          'language_arcuate',
    color:         0x9060D0,
    speed:         0.20,
    particleCount: 20,
    radius:        0.018,
    loop:          false,
    waypoints: [
      new THREE.Vector3( 0.75,  0.18, -0.28),   // Wernicke's area (posterior STG, BA22)
      new THREE.Vector3( 0.84,  0.36, -0.08),   // ascending into arcuate fasciculus
      new THREE.Vector3( 0.88,  0.64,  0.14),   // arcuate fasciculus — superior arc
      new THREE.Vector3( 0.86,  0.76,  0.44),   // arc turning anteriorly
      new THREE.Vector3( 0.82,  0.62,  0.72),   // anterior segment of arcuate
      new THREE.Vector3( 0.78,  0.32,  0.80),   // Broca's area (IFG, BA44/45)
      new THREE.Vector3( 0.72,  0.60,  0.36),   // ascending to precentral gyrus
      new THREE.Vector3( 0.64,  0.88,  0.24),   // motor cortex — larynx/lip representation
    ],
  });
  pathways.push(p);
  brainGroup.add(p.group);
}

// ── Chunk 3D: Dopamine Nigrostriatal Pathway ──────────────────────────────────
// Substantia nigra pars compacta → ascending nigrostriatal fibers (medial
// forebrain bundle / lateral hypothalamus) → striatum (putamen → caudate head).
// Dopamine depletion along this tract is the defining pathology of Parkinson's
// disease.  Progressive SN neuron loss → striatal DA deficit → bradykinesia,
// rigidity, resting tremor.  Orange-amber #E86010.
{
  const p = new Pathway({
    name:          'dopamine_nigrostriatal',
    color:         0xE86010,
    speed:         0.18,
    particleCount: 22,
    radius:        0.018,
    loop:          false,
    waypoints: [
      new THREE.Vector3( 0.20, -0.72, -0.44),   // substantia nigra pars compacta
      new THREE.Vector3( 0.22, -0.52, -0.28),   // nigrostriatal fibers ascending
      new THREE.Vector3( 0.26, -0.24, -0.10),   // medial forebrain bundle
      new THREE.Vector3( 0.34,  0.04,  0.04),   // striatal territory entry
      new THREE.Vector3( 0.46,  0.18,  0.06),   // GP / putamen border
      new THREE.Vector3( 0.56,  0.18,  0.08),   // putamen
      new THREE.Vector3( 0.50,  0.26,  0.40),   // toward caudate body
      new THREE.Vector3( 0.44,  0.26,  0.62),   // caudate head
    ],
  });
  pathways.push(p);
  brainGroup.add(p.group);
}

/**
 * Set a named pathway visible or hidden.
 * Called via window.__brain3d.setPathway(name, visible) from brain-exercise.html.
 * Pathway state is persistent across mount/unmount cycles — not reset in unmount().
 */
function setPathway(name, visible) {
  const p = pathways.find(pw => pw.name === name);
  if (p) { if (visible) p.show(); else p.hide(); }
}

// ══════════════════════════════════════════════════════════════════════════════
// LESION SIMULATOR — Chunk 3E
// Damage Mode: click any brain region → turns dark red with pulsing emissive.
// Pathways that pass through the damaged region are dimmed to grey.
// Multi-region compound syndromes: all damaged regionIds are sent to
// window.updateLesionPanel() defined in brain-exercise.html, which reads
// window.__BRAIN_DATA.regions[id].info.syndromes and renders the deficit list.
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Maps each region ID to the names of pathways that anatomically pass through
 * it.  Used to dim the correct pathway(s) when a region is damaged.
 */
const REGION_PATHWAY_MAP = {
  // ── Cortical ───────────────────────────────────────────────────────────────
  motor_cortex:        ['corticospinal', 'language_arcuate'],
  frontal_lobe:        ['corticospinal'],
  prefrontal_cortex:   [],
  brocas_area:         ['language_arcuate'],
  parietal_lobe:       ['language_arcuate'],
  somatosensory_cortex:[],
  temporal_lobe:       ['visual_temporal', 'visual_nasal', 'language_arcuate'],
  wernickes_area:      ['language_arcuate'],
  occipital_lobe:      ['visual_temporal', 'visual_nasal'],
  cerebellum:          [],
  brainstem:           ['corticospinal', 'dopamine_nigrostriatal'],
  // ── Subcortical ───────────────────────────────────────────────────────────
  hippocampus:         ['papez'],
  amygdala:            [],
  thalamus:            ['papez', 'visual_temporal', 'visual_nasal'],
  hypothalamus:        [],
  mamillary_bodies:    ['papez'],
  caudate:             ['dopamine_nigrostriatal'],
  putamen:             ['dopamine_nigrostriatal'],
  globus_pallidus:     ['dopamine_nigrostriatal'],
  substantia_nigra:    ['dopamine_nigrostriatal'],
  corpus_callosum:     [],
  fornix:              ['papez'],
  internal_capsule:    ['corticospinal'],
};

/** Apply deep-red damage appearance to a single mesh (idempotent). */
function _applyDamageMat(mesh) {
  if (mesh.userData._damageApplied) return;
  mesh.userData._damageApplied  = true;
  mesh.userData._origColor      = mesh.material.color.clone();
  mesh.userData._origEmissive   = mesh.material.emissive.clone();
  mesh.userData._origEmissiveInt= mesh.material.emissiveIntensity;
  mesh.material.color.set(0x9B1010);
  mesh.material.emissive.set(0x9B1010);
  mesh.material.emissiveIntensity = 0.18;
}

/** Remove damage appearance from a single mesh (idempotent). */
function _removeDamageMat(mesh) {
  if (!mesh.userData._damageApplied) return;
  mesh.material.color.copy(mesh.userData._origColor);
  mesh.material.emissive.copy(mesh.userData._origEmissive);
  mesh.material.emissiveIntensity = mesh.userData._origEmissiveInt;
  delete mesh.userData._damageApplied;
  delete mesh.userData._origColor;
  delete mesh.userData._origEmissive;
  delete mesh.userData._origEmissiveInt;
}

/**
 * Toggle damage on a region.  If not yet damaged → damage it and dim affected
 * pathways.  If already damaged → undamage it and restore pathways.
 * Called by selectRegion() when lesionActive is true.
 */
function toggleDamageRegion(mesh) {
  const rid = mesh.userData.regionId;
  if (!rid) return;

  if (damagedRegions.has(rid)) {
    damagedRegions.delete(rid);
    regionMeshes.forEach(m => { if (m.userData.regionId === rid) _removeDamageMat(m); });
  } else {
    damagedRegions.add(rid);
    regionMeshes.forEach(m => { if (m.userData.regionId === rid) _applyDamageMat(m); });
  }

  updatePathwayDimming();

  const resetBtn = document.getElementById('btn-reset-lesions');
  if (resetBtn) resetBtn.style.display = damagedRegions.size > 0 ? '' : 'none';

  // Broadcast to brain-exercise.html deficit panel
  window.updateLesionPanel && window.updateLesionPanel(Array.from(damagedRegions));
}

/**
 * Recalculate which pathways should be dimmed based on current damagedRegions.
 * A pathway is dimmed whenever any region in its anatomical course is damaged.
 */
function updatePathwayDimming() {
  const dimSet = new Set();
  for (const rid of damagedRegions) {
    (REGION_PATHWAY_MAP[rid] || []).forEach(n => dimSet.add(n));
  }

  pathways.forEach(p => {
    const tube = p._tube.material;
    const pts  = p._points.material;
    const shouldDim = p.group.visible && dimSet.has(p.name);

    if (shouldDim && !tube.userData._lesionDimmed) {
      // Store originals, apply grey
      tube.userData._lesionDimmed = pts.userData._lesionDimmed = true;
      tube.userData._lesionOrigC  = tube.color.clone();
      tube.userData._lesionOrigOp = tube.opacity;
      pts.userData._lesionOrigC   = pts.color.clone();
      pts.userData._lesionOrigOp  = pts.opacity;
      tube.color.setHex(0x555566);  tube.opacity = 0.12;
      pts.color.setHex(0x555566);   pts.opacity  = 0.08;

    } else if (!shouldDim && tube.userData._lesionDimmed) {
      // Restore originals
      tube.userData._lesionDimmed = pts.userData._lesionDimmed = false;
      tube.color.copy(tube.userData._lesionOrigC);
      tube.opacity = tube.userData._lesionOrigOp;
      pts.color.copy(pts.userData._lesionOrigC);
      pts.opacity = pts.userData._lesionOrigOp;
    }
  });
}

/**
 * Clear all lesion damage: restore mesh materials, undim pathways, hide panel.
 * Called by the Reset button and when toggling lesion mode off.
 */
function resetLesions() {
  regionMeshes.forEach(m => { if (m.userData._damageApplied) _removeDamageMat(m); });
  damagedRegions.clear();

  pathways.forEach(p => {
    const tube = p._tube.material;
    const pts  = p._points.material;
    if (tube.userData._lesionDimmed) {
      tube.userData._lesionDimmed = pts.userData._lesionDimmed = false;
      tube.color.copy(tube.userData._lesionOrigC);
      tube.opacity = tube.userData._lesionOrigOp;
      pts.color.copy(pts.userData._lesionOrigC);
      pts.opacity  = pts.userData._lesionOrigOp;
    }
  });

  window.updateLesionPanel && window.updateLesionPanel([]);
  const resetBtn = document.getElementById('btn-reset-lesions');
  if (resetBtn) resetBtn.style.display = 'none';
}

/**
 * Toggle Damage Mode on/off.
 * Called via window.__brain3d.toggleLesionMode() from the UI button.
 */
function toggleLesionMode() {
  lesionActive = !lesionActive;
  const modeBtn = document.getElementById('btn-damage-mode');
  if (modeBtn) modeBtn.classList.toggle('active', lesionActive);
  const panel = document.getElementById('lesion-panel');
  if (panel) panel.style.display = lesionActive ? '' : 'none';
  if (!lesionActive) {
    resetLesions();
    selectRegion(null);   // clear gold outline if a region was selected
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PATHOLOGY OVERLAY SYSTEM — Chunk 4A
// Generic tween engine: for each affected region, lerps scale and color toward
// a pathology target state, then back on deactivation.
//
// Schema per affected entry: { regionId, scaleFactor, targetColor (hex int) }
//   scaleFactor < 1 → atrophy (Alzheimer's, Parkinson's)
//   scaleFactor > 1 → edema / swelling (MCA stroke)
//   targetColor     → shift mesh color toward this (darken, desaturate, or gray)
// ═══════════════════════════════════════════════════════════════════════════════

const PATHOLOGY_DEFS = {
  alzheimers: {
    label:       "Alzheimer's",
    badgeColor:  '#9B6BA0',
    description: "Hippocampal + entorhinal atrophy — earliest structural change in AD",
    affected: [
      // Core: hippocampus shrinks to 60% — bilateral in AD, modeled here as left
      { regionId: 'hippocampus',   scaleFactor: 0.60, targetColor: 0x4A2818 },
      // Amygdala atrophy (Braak stages III–IV)
      { regionId: 'amygdala',      scaleFactor: 0.72, targetColor: 0x502A1C },
      // Medial temporal lobe thinning (entorhinal/parahippocampal — modeled on temporal)
      { regionId: 'temporal_lobe', scaleFactor: 0.91, targetColor: 0x6A3C28 },
      // Thalamic atrophy (mediodorsal nucleus — late stage)
      { regionId: 'thalamus',      scaleFactor: 0.85, targetColor: 0x5A3428 },
    ],
  },

  parkinsons: {
    label:       "Parkinson's",
    badgeColor:  '#7878A0',
    description: "Substantia nigra dopaminergic loss — depigmentation and nigrostriatal deafferentation",
    affected: [
      // Substantia nigra: heavily depigmented (gray), severe atrophy
      { regionId: 'substantia_nigra', scaleFactor: 0.55, targetColor: 0x3C3838 },
      // Striatum: downstream deafferentation — mild atrophy, color shift
      { regionId: 'putamen',          scaleFactor: 0.86, targetColor: 0x504848 },
      { regionId: 'caudate',          scaleFactor: 0.86, targetColor: 0x504848 },
      { regionId: 'globus_pallidus',  scaleFactor: 0.86, targetColor: 0x4E4646 },
    ],
  },

  mca_stroke: {
    label:       'MCA Stroke',
    badgeColor:  '#A05858',
    description: "MCA territory infarct — cytotoxic edema with gyriform cortical necrosis",
    affected: [
      // MCA territory: lateral frontal, parietal, temporal — swollen + gray (pallor)
      { regionId: 'frontal_lobe',          scaleFactor: 1.09, targetColor: 0x5E5454 },
      { regionId: 'parietal_lobe',         scaleFactor: 1.09, targetColor: 0x5E5454 },
      { regionId: 'temporal_lobe',         scaleFactor: 1.09, targetColor: 0x5E5454 },
      { regionId: 'prefrontal_cortex',     scaleFactor: 1.08, targetColor: 0x5C5252 },
      { regionId: 'motor_cortex',          scaleFactor: 1.10, targetColor: 0x5A5050 },
      { regionId: 'somatosensory_cortex',  scaleFactor: 1.10, targetColor: 0x5A5050 },
      { regionId: 'brocas_area',           scaleFactor: 1.10, targetColor: 0x585050 },
      { regionId: 'wernickes_area',        scaleFactor: 1.10, targetColor: 0x585050 },
      // Putamen + internal capsule in MCA deep territory
      { regionId: 'putamen',           scaleFactor: 1.08, targetColor: 0x5A5050 },
      { regionId: 'internal_capsule',  scaleFactor: 1.06, targetColor: 0x6A6060 },
    ],
  },

  // ── Chunk 4B additions ──────────────────────────────────────────────────────

  huntingtons: {
    label:       "Huntington's",
    badgeColor:  '#70B080',
    description: "Striatal neurodegeneration — caudate + putamen atrophy with hydrocephalus ex vacuo",
    affected: [
      // Caudate: severe atrophy — hallmark "butterfly sign" on axial MRI
      { regionId: 'caudate',         scaleFactor: 0.50, targetColor: 0x3A1A08 },
      // Putamen: strong dorsolateral gradient of cell loss
      { regionId: 'putamen',         scaleFactor: 0.68, targetColor: 0x3E2010 },
      // Globus pallidus: secondary degeneration from striatal input loss
      { regionId: 'globus_pallidus', scaleFactor: 0.76, targetColor: 0x403028 },
    ],
    // Special mesh: lateral ventricle expands (hydrocephalus ex vacuo) as caudate shrinks
    onTick(t) {
      if (!lateralVentricleMesh) return;
      lateralVentricleMesh.visible = t > 0.01;
      lateralVentricleMesh.scale.setScalar(Math.max(0.01, t));
    },
    onClear() {
      if (!lateralVentricleMesh) return;
      lateralVentricleMesh.visible = false;
      lateralVentricleMesh.scale.setScalar(0.01);
    },
  },

  split_brain: {
    label:       'Split-Brain',
    badgeColor:  '#E0A040',
    description: "Corpus callosotomy — midsagittal section; left hand / right hand disconnection",
    affected: [
      // Fornix: secondary disconnection — hippocampal-mamillary pathway loses callosal context
      { regionId: 'fornix', scaleFactor: 0.92, targetColor: 0x2C2010 },
    ],
    // CC: squish along the superior-inferior (Y) axis to create a visible sever plane + darken
    onTick(t) {
      regionMeshes.forEach(m => {
        if (m.userData.regionId !== 'corpus_callosum') return;
        if (!m.userData._sbOrig) {
          m.userData._sbOrig = { scale: m.scale.clone(), color: m.material.color.clone() };
        }
        const orig   = m.userData._sbOrig;
        const squish = 1 - 0.92 * t;   // Y axis compresses to 8% → visible sever gap
        m.scale.set(orig.scale.x, orig.scale.y * squish, orig.scale.z);
        m.material.color.lerpColors(orig.color, new THREE.Color(0x0E0808), t);
      });
    },
    onClear() {
      regionMeshes.forEach(m => {
        if (m.userData.regionId !== 'corpus_callosum' || !m.userData._sbOrig) return;
        m.scale.copy(m.userData._sbOrig.scale);
        m.material.color.copy(m.userData._sbOrig.color);
        delete m.userData._sbOrig;
      });
    },
  },

  korsakoff: {
    label:       'Korsakoff',
    badgeColor:  '#D08040',
    description: "Thiamine (B1) deficiency — mamillary body necrosis + mediodorsal thalamic damage",
    affected: [
      // Primary: bilateral mamillary body necrosis (pathognomonic)
      { regionId: 'mamillary_bodies', scaleFactor: 0.42, targetColor: 0x2C1008 },
      // Mediodorsal thalamic nucleus — critical for declarative memory consolidation
      { regionId: 'thalamus',         scaleFactor: 0.80, targetColor: 0x442C20 },
      // Secondary: hippocampal degeneration accelerated by metabolic damage
      { regionId: 'hippocampus',      scaleFactor: 0.88, targetColor: 0x503028 },
      // Fornix: dysfunctional tract (upstream input to mamillary bodies disrupted)
      { regionId: 'fornix',           scaleFactor: 0.85, targetColor: 0x4A3820 },
    ],
  },

  tbi_frontal: {
    label:       'TBI Frontal',
    badgeColor:  '#C06060',
    description: "Orbitofrontal contusion — coup impact + contrecoup posterior damage",
    affected: [
      // Coup: orbitofrontal strikes the bony orbital plate of the frontal skull base
      { regionId: 'prefrontal_cortex', scaleFactor: 0.87, targetColor: 0x481E14 },
      { regionId: 'frontal_lobe',      scaleFactor: 0.91, targetColor: 0x502818 },
      // Contrecoup: anterior temporal poles strike the tentorial edge
      { regionId: 'temporal_lobe',     scaleFactor: 0.94, targetColor: 0x4A2618 },
      // Contrecoup: occipital poles rebound against the posterior occipital bone
      { regionId: 'occipital_lobe',    scaleFactor: 0.95, targetColor: 0x482416 },
    ],
  },
};

/**
 * Activate a named pathology.  If `key` is already active, deactivates (toggles).
 * If switching to a different pathology, snaps the previous one off and immediately
 * starts the new one so transitions stay crisp.
 */
function activatePathology(key) {
  if (activePathology === key) {
    // Same pathology clicked — animate back to normal
    pathologyDir = -1;
    return;
  }

  // If another pathology is partially or fully applied, snap it back first
  if (activePathology !== null) {
    _snapClearPathology();
  }

  // Set up targets on each affected mesh
  const def = PATHOLOGY_DEFS[key];
  if (!def) return;

  for (const spec of def.affected) {
    const tColor = new THREE.Color(spec.targetColor);
    regionMeshes
      .filter(m => m.userData.regionId === spec.regionId && m.visible !== undefined)
      .forEach(m => {
        // Save original only once (guard against re-activation edge cases)
        if (!m.userData._pathorig) {
          m.userData._pathorig = {
            scale: m.scale.clone(),
            color: m.material.color.clone(),
          };
        }
        m.userData._pathtarg = {
          scaleFactor: spec.scaleFactor,
          color:       tColor,
        };
      });
  }

  activePathology = key;
  pathologyT      = 0.0;
  pathologyDir    = 1;

  window.onPathologyChange && window.onPathologyChange(key, def.label, def.description);
}

/**
 * Request an animated return to normal state.
 */
function clearPathology() {
  if (!activePathology) return;
  pathologyDir = -1;
}

/**
 * Instantly restore all pathology-affected meshes to their original state.
 * Used when switching pathologies without the user having to see a double-tween.
 */
function _snapClearPathology() {
  const wasKey = activePathology;   // capture before nulling
  regionMeshes.forEach(m => {
    const orig = m.userData._pathorig;
    if (orig) {
      m.scale.copy(orig.scale);
      m.material.color.copy(orig.color);
      delete m.userData._pathorig;
      delete m.userData._pathtarg;
    }
  });
  pathologyT      = 0;
  pathologyDir    = 0;
  activePathology = null;
  PATHOLOGY_DEFS[wasKey]?.onClear?.();   // restore special meshes (ventricle, CC squish)
  window.onPathologyChange && window.onPathologyChange(null);
}

/**
 * Called once per frame from animate().
 * Smoothly lerps affected mesh scales and colors toward or away from the pathology target.
 */
function tickPathologyTween(delta) {
  if (pathologyDir === 0) return;

  const SPEED = 2.0;   // full transition in ~0.5 seconds
  pathologyT += pathologyDir * SPEED * delta;
  pathologyT  = Math.max(0, Math.min(1, pathologyT));

  // Smoothstep ease-in/out: feels organic, not mechanical
  const t = pathologyT * pathologyT * (3 - 2 * pathologyT);

  regionMeshes.forEach(m => {
    const orig = m.userData._pathorig;
    const targ = m.userData._pathtarg;
    if (!orig || !targ) return;

    // Scale: lerp uniformly about the region center
    const ts = 1 + (targ.scaleFactor - 1) * t;
    m.scale.set(orig.scale.x * ts, orig.scale.y * ts, orig.scale.z * ts);

    // Color: lerp from original tissue color to pathology target
    m.material.color.lerpColors(orig.color, targ.color, t);
  });

  // onTick hook — for pathologies with special mesh effects (ventricle, CC squish)
  PATHOLOGY_DEFS[activePathology]?.onTick?.(t);

  // Animation complete
  if (pathologyT >= 1.0 && pathologyDir === 1) {
    pathologyDir = 0;   // fully affected — stop
  } else if (pathologyT <= 0.0 && pathologyDir === -1) {
    // Fully restored — clean up userData and clear active state
    const wasKey = activePathology;   // capture before nulling
    regionMeshes.forEach(m => {
      if (m.userData._pathorig) {
        m.scale.copy(m.userData._pathorig.scale);
        m.material.color.copy(m.userData._pathorig.color);
        delete m.userData._pathorig;
        delete m.userData._pathtarg;
      }
    });
    pathologyDir    = 0;
    activePathology = null;
    PATHOLOGY_DEFS[wasKey]?.onClear?.();   // restore special meshes on tween completion
    window.onPathologyChange && window.onPathologyChange(null);
  }
}

// Build the disc now — ASSEMBLE SCENE has already run so `scene` is populated.
discMesh = buildCrossDisc();

function animate(ts) {
  animFrameId = requestAnimationFrame(animate);
  const delta = Math.min((ts - lastTs) / 1000, 0.05);
  lastTs = ts;

  controls.update();

  if (autoRotate) {
    brainGroup.rotation.y += delta * 0.18;   // ~10°/s idle rotation
  }

  // Glass-brain opacity tween (ease-in-out cubic)
  if (glassTweenStart >= 0) {
    const raw    = (ts - glassTweenStart) / GLASS_DURATION;
    const target = glassActive ? 1 : 0;
    if (raw >= 1) {
      glassProgress   = target;
      glassTweenStart = -1;
      applyGlassProgress(glassProgress);
    } else {
      const e = raw < 0.5
        ? 4 * raw * raw * raw
        : 1 - Math.pow(-2 * raw + 2, 3) / 2;
      glassProgress = glassActive ? e : 1 - e;
      applyGlassProgress(glassProgress);
    }
  }

  // Recompute world-space clip plane to follow brainGroup rotation (auto or manual)
  if (csMode) updateCrossSection();

  // Advance pathway particle animations
  if (pathways.length) pathways.forEach(p => p.animate(delta));

  // Pathology overlay tween — lerp scale + color toward/away from pathology state
  tickPathologyTween(delta);

  // Lesion pulse — red emissive oscillation on all currently-damaged meshes
  if (lesionActive && damagedRegions.size > 0) {
    lesionPulseT = (lesionPulseT + delta * 2.2) % (Math.PI * 2);
    const pulse = 0.14 + 0.10 * Math.sin(lesionPulseT);
    regionMeshes.forEach(m => {
      if (m.userData._damageApplied && m.visible) m.material.emissiveIntensity = pulse;
    });
  }

  // Per-frame hover raycasting — filter by visibility so hidden subcortical
  // structures aren't hit before the glass-brain toggle reveals them.
  raycaster.setFromCamera(mouseNDC, camera);
  const hits     = raycaster.intersectObjects(regionMeshes, false)
                            .filter(h => h.object.visible !== false);
  const newHover = hits.length ? hits[0].object : null;
  if (newHover !== hoveredMesh) {
    setHover(newHover);
    canvas.style.cursor = newHover ? 'pointer' : (autoRotate ? 'grab' : 'grabbing');
  }

  composer.render();
}

// ── Pointer events ─────────────────────────────────────────────────────────────

let pointerDownPos = null;

canvas.addEventListener('pointermove', e => {
  const rect = canvas.getBoundingClientRect();
  mouseNDC.x =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
  mouseNDC.y = -((e.clientY - rect.top)  / rect.height) * 2 + 1;
});

canvas.addEventListener('pointerdown', e => {
  autoRotate = false;
  canvas.style.cursor = 'grabbing';
  clearTimeout(idleTimer);
  pointerDownPos = { x: e.clientX, y: e.clientY };
});

canvas.addEventListener('pointerup', e => {
  canvas.style.cursor = hoveredMesh ? 'pointer' : 'grab';
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { autoRotate = true; }, 6000);

  // Distinguish click (< 5px travel) from drag (orbit)
  if (pointerDownPos) {
    const dx = e.clientX - pointerDownPos.x;
    const dy = e.clientY - pointerDownPos.y;
    if (Math.sqrt(dx*dx + dy*dy) < 5) {
      // Recompute ray at release position for accuracy
      const rect = canvas.getBoundingClientRect();
      mouseNDC.x =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
      mouseNDC.y = -((e.clientY - rect.top)  / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouseNDC, camera);
      const clickHits = raycaster.intersectObjects(regionMeshes, false)
                                .filter(h => h.object.visible !== false);
      selectRegion(clickHits.length ? clickHits[0].object : null);
    }
  }
  pointerDownPos = null;
});

canvas.addEventListener('pointerleave', () => {
  mouseNDC.set(-10, -10);
  setHover(null);
});

// ══════════════════════════════════════════════════════════════════════════════
// MOUNT / UNMOUNT / RESIZE
// ══════════════════════════════════════════════════════════════════════════════

let mountedContainer = null;

function handleResize(container) {
  const w = container.clientWidth  || 700;
  const h = Math.max(260, Math.round(w * 0.65));
  renderer.setSize(w, h);
  composer.setSize(w, h);
  outlinePass.resolution.set(w, h);
  // Override inline style set by renderer so CSS width:100% works
  canvas.style.width  = '100%';
  canvas.style.height = h + 'px';
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

const resizeObserver = new ResizeObserver(() => {
  if (mountedContainer) handleResize(mountedContainer);
});

/**
 * Mount the 3D renderer canvas into the given container element (or CSS selector).
 * Safe to call multiple times — idempotent if already mounted in the same container.
 */
function mount(containerOrSelector) {
  const container = typeof containerOrSelector === 'string'
    ? document.querySelector(containerOrSelector)
    : containerOrSelector;

  if (!container) { console.warn('brain-3d: mount() target not found'); return; }

  // Already mounted in the correct container — just ensure loop is running
  if (mountedContainer === container) {
    if (animFrameId === null) animate(0);
    return;
  }

  // Move canvas if mounted elsewhere
  if (mountedContainer && canvas.parentNode === mountedContainer) {
    resizeObserver.unobserve(mountedContainer);
  }

  mountedContainer = container;
  container.appendChild(canvas);
  handleResize(container);
  resizeObserver.observe(container);

  if (animFrameId === null) animate(0);
}

/** Stop the render loop and detach from the DOM. Clears hover/selection state. */
function unmount() {
  if (animFrameId !== null) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }
  if (mountedContainer) {
    resizeObserver.unobserve(mountedContainer);
    if (canvas.parentNode === mountedContainer) {
      mountedContainer.removeChild(canvas);
    }
    mountedContainer = null;
  }
  // Reset interaction state so next mount starts clean
  hoveredMesh  = null;
  selectedMesh = null;
  outlinePass.selectedObjects = [];
  // NOTE: Pathway visibility is intentionally NOT reset here — pathway state
  // persists across mount/unmount so the 3D view restores correctly when the
  // user switches back from SVG view.  UI button state in brain-exercise.html
  // therefore always matches the actual group.visible state.

  // Reset vascular territory overlay
  if (vasc3dGroups) {
    vasc3dGroups.mca.visible = vasc3dGroups.aca.visible = vasc3dGroups.pca.visible = false;
  }

  // Reset cross-section state — remove clip planes and hide disc
  if (csMode) {
    csMode = null;
    deactivateClipping();
  }
  document.querySelectorAll('.cs-axis-btn').forEach(b => b.classList.remove('active'));
  const csSliderEl = document.getElementById('cs-slider');
  if (csSliderEl) csSliderEl.style.display = 'none';

  // Reset glass state — next mount always starts fully opaque
  if (glassProgress !== 0 || glassActive) {
    glassActive     = false;
    glassProgress   = 0;
    glassTweenStart = -1;
    applyGlassProgress(0);
  }
  const btn = document.getElementById('btn-glass-brain');
  if (btn) btn.classList.remove('active');
}

// ── Expose API ────────────────────────────────────────────────────────────────
// corticalMeshes + subcorticalMeshes exposed for reference; toggleGlass for the UI button.
window.__brain3d = {
  mount, unmount,
  corticalMeshes, subcorticalMeshes,
  toggleGlass,
  setCsMode, setCsSlider,
  setVascTerritory,
  // Chunk 3B — Pathway Animation Engine
  Pathway, pathways, showPathway, hidePathway,
  // Chunk 3C — Named pathway toggle
  setPathway,
  // Chunk 3E — Lesion Simulator
  toggleLesionMode, resetLesions,
  // Chunk 4A — Pathology Overlay System
  activatePathology, clearPathology, PATHOLOGY_DEFS,
};

// Auto-mount if the page already has view=3d on load
(function autoMountOnLoad() {
  const view = new URLSearchParams(location.search).get('view');
  if (view === '3d') {
    const c = document.getElementById('brain-container-3d');
    if (c) mount(c);
  }
})();
