/**
 * brain-3d.js — Three.js 3D Brain Explorer
 * Phase 2, Chunk 2A: Scene scaffold + hemisphere mesh
 *
 * Exposes window.__brain3d = { mount(container), unmount() }
 * Called by brain-exercise.html when the user switches to the 3D view.
 */

import * as THREE            from 'three';
import { OrbitControls }     from 'three/addons/controls/OrbitControls.js';

// ══════════════════════════════════════════════════════════════════════════════
// RENDERER
// ══════════════════════════════════════════════════════════════════════════════

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled    = true;
renderer.shadowMap.type       = THREE.PCFSoftShadowMap;
renderer.toneMapping          = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure  = 1.2;

const canvas = renderer.domElement;
canvas.style.borderRadius = '16px';
canvas.style.display      = 'block';
canvas.style.cursor       = 'grab';

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
// BRAIN HEMISPHERE GEOMETRY
// ══════════════════════════════════════════════════════════════════════════════

/**
 * Builds a single left hemisphere mesh from a displaced SphereGeometry.
 * Shape modifications:
 *   - Elongate AP axis (brain is ovoid, not spherical)
 *   - Flatten inferior surface (sits on skull base)
 *   - Widen slightly at equator
 *   - Flatten medial face toward x = 0 cut plane
 *   - Multi-frequency sine-wave gyral displacement along surface normals
 */
function buildHemisphere() {
  const geo = new THREE.SphereGeometry(1.4, 128, 96);
  const pos = geo.attributes.position;

  // First pass: shape the overall form
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

    // Low-frequency: major gyri / sulci
    const lf =
      0.052 * Math.sin(x * 6.8 + 0.40) * Math.sin(y * 6.2 + 0.80) * Math.sin(z * 5.0 + 0.20) +
      0.040 * Math.sin(x * 5.0 + 1.20) * Math.cos(y * 7.5 + 0.60) * Math.sin(z * 6.5 + 1.40);

    // Medium-frequency: secondary folding
    const mf =
      0.027 * Math.sin(x * 11.5 + 2.10) * Math.sin(y * 10.0 + 1.30) * Math.sin(z * 9.5 + 0.90) +
      0.019 * Math.cos(x * 14.0 + 0.70) * Math.sin(y * 13.5 + 2.50) * Math.cos(z * 11.0 + 1.80);

    // High-frequency: fine surface texture
    const hf =
      0.009 * Math.sin(x * 22.0 + 1.50) * Math.sin(y * 20.0 + 0.80) * Math.sin(z * 18.0 + 2.20) +
      0.006 * Math.cos(x * 28.0 + 0.40) * Math.cos(y * 26.0 + 1.90);

    const disp = lf + mf + hf;

    // Suppress displacement near the medial cut-face (keep it clean)
    const medialSuppress   = Math.min(1, Math.max(0, x + 0.3) / 0.4);
    // Suppress at the inferior pole (brainstem attachment area)
    const inferiorSuppress = Math.min(1, (y + 1.4) / 0.45);

    const dispFinal = disp * medialSuppress * inferiorSuppress;

    // Displace radially along surface normal approximation
    x += (x / r) * dispFinal;
    y += (y / r) * dispFinal;
    z += (z / r) * dispFinal;

    pos.setXYZ(i, x, y, z);
  }

  pos.needsUpdate = true;
  geo.computeVertexNormals();

  const mat = new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(0xC87858),   // warm pinkish-tan tissue
    roughness:          0.72,                         // matte-satin (not glossy)
    metalness:          0.00,
    clearcoat:          0.12,                         // subtle pial membrane sheen
    clearcoatRoughness: 0.40,
    side:               THREE.FrontSide,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow    = true;
  mesh.receiveShadow = false;
  mesh.name = 'hemisphere';
  return mesh;
}

/**
 * Flat disc closing the medial cut face (x ≈ 0 plane).
 * Uses a slightly darker pinkish-brown to visually read as a cut surface.
 */
function buildMedialFace() {
  // Oval profile: brain is ~1.28 units tall at midline, ~1.1 wide
  const shape = new THREE.Shape();
  const rx = 1.06, ry = 1.22;
  for (let a = 0; a <= Math.PI * 2; a += 0.05) {
    const px = Math.cos(a) * rx;
    const py = Math.sin(a) * ry * (py_raw => py_raw < 0 ? 0.68 : 1)(Math.sin(a));
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
  mesh.rotation.y = Math.PI / 2;  // face the +x normal (medial face toward viewer)
  mesh.position.x = 0.032;
  mesh.name = 'medial-face';
  return mesh;
}

/**
 * Shadow-receiving ground plane (invisible except for soft shadow).
 */
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

// ── Assemble scene ────────────────────────────────────────────────────────────
// Group hemisphere + medial face so they rotate as a unit
const brainGroup = new THREE.Group();
brainGroup.add(buildHemisphere());
brainGroup.add(buildMedialFace());
brainGroup.rotation.y = -0.28;   // Initial pose: slight rotation showing temporal lobe

scene.add(brainGroup);
scene.add(buildGroundPlane());

// ══════════════════════════════════════════════════════════════════════════════
// 3D UI OVERLAY  (label strip at bottom of canvas)
// ══════════════════════════════════════════════════════════════════════════════
// Note: HTML overlay labels are added by brain-exercise.html when mounting.
// brain-3d.js only handles the WebGL scene.

// ══════════════════════════════════════════════════════════════════════════════
// ANIMATION LOOP
// ══════════════════════════════════════════════════════════════════════════════

let animFrameId   = null;
let autoRotate    = true;
let lastTs        = 0;
let idleTimer     = null;

function animate(ts) {
  animFrameId = requestAnimationFrame(animate);
  const delta = Math.min((ts - lastTs) / 1000, 0.05);
  lastTs = ts;

  controls.update();

  if (autoRotate) {
    brainGroup.rotation.y += delta * 0.18;   // ~10°/s idle rotation
  }

  renderer.render(scene, camera);
}

// Stop auto-rotate on interaction; resume after 6 s of no interaction
canvas.addEventListener('pointerdown', () => {
  autoRotate = false;
  canvas.style.cursor = 'grabbing';
  clearTimeout(idleTimer);
});
canvas.addEventListener('pointerup', () => {
  canvas.style.cursor = 'grab';
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => { autoRotate = true; }, 6000);
});

// ══════════════════════════════════════════════════════════════════════════════
// MOUNT / UNMOUNT / RESIZE
// ══════════════════════════════════════════════════════════════════════════════

let mountedContainer = null;

function handleResize(container) {
  const w = container.clientWidth  || 700;
  const h = Math.max(260, Math.round(w * 0.65));
  renderer.setSize(w, h);
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

/** Stop the render loop and detach from the DOM. */
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
}

// ── Expose API ────────────────────────────────────────────────────────────────
window.__brain3d = { mount, unmount };

// Auto-mount if the page already has view=3d on load
// (module executes after DOM is ready — container element exists)
(function autoMountOnLoad() {
  const view = new URLSearchParams(location.search).get('view');
  if (view === '3d') {
    const c = document.getElementById('brain-container-3d');
    if (c) mount(c);
  }
})();
