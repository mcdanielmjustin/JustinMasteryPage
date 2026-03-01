/**
 * brain-3d.js — 3D Brain Explorer (v2)
 *
 * Clean rebuild: each anatomical region is its own ellipsoid mesh.
 * No vertex zone classification, no carved hemisphere.
 *
 * Exposes window.__brain3d = {
 *   mount(container), unmount(),
 *   setCameraView(name), CAMERA_VIEWS,
 *   highlightRegion(id), dimAllRegions(exceptIds[]), resetRegions()
 * }
 */

import * as THREE         from 'three';
import { OrbitControls }  from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }     from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass }    from 'three/addons/postprocessing/OutlinePass.js';
import { OutputPass }     from 'three/addons/postprocessing/OutputPass.js';

// ══════════════════════════════════════════════════════════════════════════════
// RENDERER
// ══════════════════════════════════════════════════════════════════════════════

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled   = true;
renderer.shadowMap.type      = THREE.PCFSoftShadowMap;
renderer.toneMapping         = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.5;

const canvas = renderer.domElement;
canvas.style.cssText = 'display:block; border-radius:16px; cursor:grab;';

// ── Post-processing ────────────────────────────────────────────────────────────
const composer = new EffectComposer(renderer);

// ══════════════════════════════════════════════════════════════════════════════
// SCENE
// ══════════════════════════════════════════════════════════════════════════════

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0A0D14);

// ── Camera ─────────────────────────────────────────────────────────────────────
const camera = new THREE.PerspectiveCamera(40, 1.54, 0.1, 100);
camera.position.set(4.8, 0.5, 0.4);

// ── Controls ───────────────────────────────────────────────────────────────────
// Brain center of mass sits around (0.55, 0.05, 0.1); orbit around that point.
const CAM_TARGET = new THREE.Vector3(0.55, 0.05, 0.10);
const controls   = new OrbitControls(camera, canvas);
controls.enableDamping  = true;
controls.dampingFactor  = 0.07;
controls.minDistance    = 2.8;
controls.maxDistance    = 10.0;
controls.enablePan      = false;
controls.target.copy(CAM_TARGET);
controls.update();

// ══════════════════════════════════════════════════════════════════════════════
// LIGHTING  (clinical: cool-white key + blue fill/rim + hemisphere ambient)
// ══════════════════════════════════════════════════════════════════════════════

// Near-white overhead key — produces sharp gyral specular highlights
const keyLight = new THREE.DirectionalLight(0xFFF8F4, 3.6);
keyLight.position.set(-2, 6, 3.5);
keyLight.castShadow              = true;
keyLight.shadow.mapSize.setScalar(2048);
scene.add(keyLight);

// Cool-blue lateral fill — shadow areas are blue, not black
const fillLight = new THREE.DirectionalLight(0xC4D8FF, 0.65);
fillLight.position.set(5, 0.5, -1.5);
scene.add(fillLight);

// Cyan rim from behind-below — separates brain from dark background
const rimLight = new THREE.DirectionalLight(0x90BCFF, 2.0);
rimLight.position.set(1.5, -3, -5);
scene.add(rimLight);

// Hemisphere: cool sky above / warm ground below
scene.add(new THREE.HemisphereLight(0xB0C8E0, 0x583020, 0.70));

// Very subtle neutral base
scene.add(new THREE.AmbientLight(0x808898, 0.15));

// ══════════════════════════════════════════════════════════════════════════════
// GYRAL NORMAL MAP  (canvas-generated, tiled over each lobe)
// ══════════════════════════════════════════════════════════════════════════════

function makeGyralNormal(size) {
  size = size || 512;
  var c   = document.createElement('canvas');
  c.width = c.height = size;
  var ctx = c.getContext('2d');
  var img = ctx.createImageData(size, size);

  // Height field: sum of cosine waves at multiple frequencies.
  // Gradient computed by central finite difference → normal vector.
  function h(x, y) {
    return (
      0.55 * Math.sin(x * 0.042 + 0.40) * Math.sin(y * 0.038 + 0.80) +
      0.35 * Math.sin(x * 0.030 + 1.20) * Math.cos(y * 0.044 + 0.30) +
      0.28 * Math.sin(x * 0.092 + 2.10) * Math.sin(y * 0.085 + 1.50) +
      0.15 * Math.sin(x * 0.180 + 0.70) * Math.sin(y * 0.155 + 2.00) +
      0.08 * Math.cos(x * 0.260 + 1.80) * Math.cos(y * 0.220 + 0.60)
    );
  }

  var strength = 1.2;
  var eps      = 1.0;

  for (var y = 0; y < size; y++) {
    for (var x = 0; x < size; x++) {
      var dhdx = (h(x + eps, y) - h(x - eps, y)) / (2 * eps);
      var dhdy = (h(x, y + eps) - h(x, y - eps)) / (2 * eps);
      var nx   = -dhdx * strength;
      var ny   = -dhdy * strength;
      var nz   = 1.0;
      var len  = Math.sqrt(nx * nx + ny * ny + nz * nz);
      var i    = (y * size + x) * 4;
      img.data[i]     = Math.round((nx / len * 0.5 + 0.5) * 255);
      img.data[i + 1] = Math.round((ny / len * 0.5 + 0.5) * 255);
      img.data[i + 2] = Math.round((nz / len * 0.5 + 0.5) * 255);
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);

  var tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(2.5, 2.5);
  return tex;
}

const GYRAL_NORMAL = makeGyralNormal(512);

// ══════════════════════════════════════════════════════════════════════════════
// LOBE DEFINITIONS
//
// Each lobe is a SphereGeometry(1, 72, 54) scaled to an ellipsoid via
// mesh.scale = (rx, ry, rz) and mesh.position = (cx, cy, cz).
//
// Coordinate system (left hemisphere):
//   x  0=medial   → 1.5=lateral
//   y −1=inferior  → 1.4=superior
//   z −1.8=posterior → 1.8=anterior
//
// Major lobes render before sub-regions. Sub-regions (sub:true) get polygon
// offset so they sit visually on top without z-fighting.
// ══════════════════════════════════════════════════════════════════════════════

const LOBE_DEFS = [
  // ── Major lobes ─────────────────────────────────────────────────────────────
  { id:'frontal_lobe',         label:'Frontal Lobe',
    cx:0.58, cy: 0.28, cz: 0.88,  rx:0.76, ry:0.72, rz:0.82,
    color:0xCC7260 },
  { id:'parietal_lobe',        label:'Parietal Lobe',
    cx:0.60, cy: 0.72, cz:-0.22,  rx:0.62, ry:0.50, rz:0.54,
    color:0x5A9E94 },
  { id:'temporal_lobe',        label:'Temporal Lobe',
    cx:1.00, cy:-0.32, cz: 0.15,  rx:0.42, ry:0.42, rz:0.92,
    color:0x7A72A8 },
  { id:'occipital_lobe',       label:'Occipital Lobe',
    cx:0.52, cy: 0.10, cz:-1.28,  rx:0.54, ry:0.52, rz:0.52,
    color:0xB89830 },
  // ── Separate structures ──────────────────────────────────────────────────────
  { id:'cerebellum',           label:'Cerebellum',
    cx:0.50, cy:-0.64, cz:-1.22,  rx:0.76, ry:0.37, rz:0.58,
    color:0x5888A0 },
  { id:'brainstem',            label:'Brainstem',
    cx:0.18, cy:-0.90, cz:-0.52,  rx:0.18, ry:0.48, rz:0.18,
    color:0x786858 },
  // ── Sub-regions (rendered on top of parent lobes) ─────────────────────────
  { id:'prefrontal_cortex',    label:'Prefrontal Cortex',
    cx:0.52, cy: 0.34, cz: 1.54,  rx:0.42, ry:0.54, rz:0.30,
    color:0xBA6054, sub:true },
  { id:'motor_cortex',         label:'Motor Cortex',
    cx:0.63, cy: 0.80, cz: 0.46,  rx:0.17, ry:0.50, rz:0.21,
    color:0xD06858, sub:true },
  { id:'somatosensory_cortex', label:'Somatosensory Cortex',
    cx:0.63, cy: 0.76, cz: 0.14,  rx:0.17, ry:0.46, rz:0.21,
    color:0x4E9088, sub:true },
  { id:'brocas_area',          label:"Broca's Area",
    cx:0.88, cy:-0.08, cz: 0.62,  rx:0.25, ry:0.23, rz:0.29,
    color:0xAE5A50, sub:true },
  { id:'wernickes_area',       label:"Wernicke's Area",
    cx:0.88, cy: 0.12, cz:-0.18,  rx:0.26, ry:0.24, rz:0.29,
    color:0x6A62A0, sub:true },
];

// ══════════════════════════════════════════════════════════════════════════════
// BUILD BRAIN MESHES
// ══════════════════════════════════════════════════════════════════════════════

const brainGroup   = new THREE.Group();
scene.add(brainGroup);
const regionMeshes = [];

const BASE_GEO = new THREE.SphereGeometry(1, 72, 54);

LOBE_DEFS.forEach(function(def) {
  var mat = new THREE.MeshPhysicalMaterial({
    color:              new THREE.Color(def.color),
    roughness:          0.50,
    metalness:          0.00,
    clearcoat:          0.58,
    clearcoatRoughness: 0.12,
    normalMap:          GYRAL_NORMAL,
    normalScale:        new THREE.Vector2(0.45, 0.45),
    emissive:           new THREE.Color(0x000000),
    emissiveIntensity:  0,
  });

  if (def.sub) {
    mat.polygonOffset       = true;
    mat.polygonOffsetFactor = -2;
    mat.polygonOffsetUnits  = -2;
  }

  var mesh         = new THREE.Mesh(BASE_GEO, mat);
  mesh.scale.set(def.rx, def.ry, def.rz);
  mesh.position.set(def.cx, def.cy, def.cz);
  mesh.renderOrder   = def.sub ? 1 : 0;
  mesh.castShadow    = true;
  mesh.receiveShadow = true;
  mesh.name          = def.id;
  mesh.userData      = { regionId: def.id, label: def.label, def: def };

  brainGroup.add(mesh);
  regionMeshes.push(mesh);
});

// Ground shadow plane
var groundMesh = new THREE.Mesh(
  new THREE.PlaneGeometry(10, 10),
  new THREE.ShadowMaterial({ opacity: 0.18 })
);
groundMesh.receiveShadow = true;
groundMesh.rotation.x    = -Math.PI / 2;
groundMesh.position.y    = -1.5;
scene.add(groundMesh);

// ══════════════════════════════════════════════════════════════════════════════
// POST-PROCESSING  (OutlinePass for gold region selection)
// ══════════════════════════════════════════════════════════════════════════════

var renderPass  = new RenderPass(scene, camera);
var outlinePass = new OutlinePass(new THREE.Vector2(700, 455), scene, camera);
outlinePass.edgeStrength            = 4.2;
outlinePass.edgeGlow                = 0.5;
outlinePass.edgeThickness           = 2.0;
outlinePass.pulsePeriod             = 0;
outlinePass.visibleEdgeColor.set('#d4a054');
outlinePass.hiddenEdgeColor.set('#7a5820');
outlinePass.selectedObjects         = [];
var outputPass = new OutputPass();

composer.addPass(renderPass);
composer.addPass(outlinePass);
composer.addPass(outputPass);

// ══════════════════════════════════════════════════════════════════════════════
// INTERACTION — hover emissive + click gold outline
// ══════════════════════════════════════════════════════════════════════════════

var raycaster    = new THREE.Raycaster();
var mouse        = new THREE.Vector2(-10, -10);
var hoveredMesh  = null;
var selectedMesh = null;

function setHover(mesh) {
  if (hoveredMesh === mesh) return;
  if (hoveredMesh && hoveredMesh !== selectedMesh) {
    hoveredMesh.material.emissiveIntensity = 0;
  }
  hoveredMesh = mesh;
  if (hoveredMesh && hoveredMesh !== selectedMesh) {
    hoveredMesh.material.emissive.set(0xffffff);
    hoveredMesh.material.emissiveIntensity = 0.20;
  }
}

function selectRegion(mesh) {
  if (selectedMesh === mesh) return;
  if (selectedMesh) {
    selectedMesh.material.emissive.set(0x000000);
    selectedMesh.material.emissiveIntensity = 0;
    outlinePass.selectedObjects = [];
  }
  selectedMesh = mesh;
  if (!mesh) return;
  outlinePass.selectedObjects = [mesh];
  mesh.material.emissive.set(0xd4a054);
  mesh.material.emissiveIntensity = 0.14;
  if (window.__brainUI) window.__brainUI.openRegion(mesh.userData.regionId);
}

// ══════════════════════════════════════════════════════════════════════════════
// CAMERA PRESET VIEWS
// ══════════════════════════════════════════════════════════════════════════════

var CAMERA_VIEWS = {
  lateral:   new THREE.Vector3( 4.8,  0.5,  0.4),
  medial:    new THREE.Vector3(-3.8,  0.5,  0.4),
  superior:  new THREE.Vector3( 0.6,  5.5,  0.8),
  inferior:  new THREE.Vector3( 0.6, -5.5,  0.8),
  anterior:  new THREE.Vector3( 0.5,  0.5,  5.2),
  posterior: new THREE.Vector3( 0.5,  0.5, -5.6),
};

var camFrom = null, camTo = null, camT = 0;
var CAM_DUR = 0.72;

function setCameraView(name) {
  var tgt = CAMERA_VIEWS[name];
  if (!tgt) return;
  camFrom = camera.position.clone();
  camTo   = tgt.clone();
  camT    = 0;
  controls.target.copy(CAM_TARGET);
  document.querySelectorAll('.view-preset-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.view === name);
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// QUIZ-MODE REGION API
// ══════════════════════════════════════════════════════════════════════════════

function highlightRegion(regionId) {
  regionMeshes.forEach(function(m) {
    var match = m.userData.regionId === regionId;
    m.material.emissive.set(match ? 0xd4a054 : 0x000000);
    m.material.emissiveIntensity = match ? 0.28 : 0;
    m.material.opacity           = 1;
    m.material.transparent       = false;
  });
  var mesh = regionMeshes.find(function(m) { return m.userData.regionId === regionId; });
  outlinePass.selectedObjects = mesh ? [mesh] : [];
}

function dimAllRegions(exceptIds) {
  exceptIds = exceptIds || [];
  regionMeshes.forEach(function(m) {
    var keep = exceptIds.indexOf(m.userData.regionId) !== -1;
    m.material.opacity     = keep ? 1.0 : 0.18;
    m.material.transparent = !keep;
    m.material.depthWrite  = keep;
  });
}

function resetRegions() {
  regionMeshes.forEach(function(m) {
    m.material.opacity       = 1;
    m.material.transparent   = false;
    m.material.depthWrite    = true;
    m.material.emissiveIntensity = 0;
  });
  outlinePass.selectedObjects = [];
  selectedMesh = null;
  hoveredMesh  = null;
}

// ══════════════════════════════════════════════════════════════════════════════
// ANIMATION LOOP
// ══════════════════════════════════════════════════════════════════════════════

var animId = null;
var lastTs = 0;

function animate(ts) {
  animId = requestAnimationFrame(animate);
  var dt = Math.min((ts - lastTs) / 1000, 0.05);
  lastTs = ts;

  if (camTo) {
    camT = Math.min(camT + dt / CAM_DUR, 1);
    var e = 1 - Math.pow(1 - camT, 3);    // ease-out cubic
    camera.position.lerpVectors(camFrom, camTo, e);
    camera.lookAt(controls.target);
    if (camT >= 1) { camTo = null; controls.update(); }
  } else {
    controls.update();
  }

  raycaster.setFromCamera(mouse, camera);
  var hits     = raycaster.intersectObjects(regionMeshes, false);
  var newHover = hits.length ? hits[0].object : null;
  if (newHover !== hoveredMesh) {
    setHover(newHover);
    canvas.style.cursor = newHover ? 'pointer' : 'grab';
  }

  composer.render();
}

// ══════════════════════════════════════════════════════════════════════════════
// POINTER EVENTS
// ══════════════════════════════════════════════════════════════════════════════

var downPos = null;

canvas.addEventListener('pointermove', function(e) {
  var r = canvas.getBoundingClientRect();
  mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
  mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;
});

canvas.addEventListener('pointerdown', function(e) {
  canvas.style.cursor = 'grabbing';
  downPos = { x: e.clientX, y: e.clientY };
});

canvas.addEventListener('pointerup', function(e) {
  canvas.style.cursor = hoveredMesh ? 'pointer' : 'grab';
  if (!downPos) return;
  var dx = e.clientX - downPos.x;
  var dy = e.clientY - downPos.y;
  if (Math.sqrt(dx * dx + dy * dy) < 5) {
    var r = canvas.getBoundingClientRect();
    mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
    mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);
    var hits = raycaster.intersectObjects(regionMeshes, false);
    selectRegion(hits.length ? hits[0].object : null);
  }
  downPos = null;
});

canvas.addEventListener('pointerleave', function() {
  mouse.set(-10, -10);
  setHover(null);
});

// ══════════════════════════════════════════════════════════════════════════════
// RESIZE
// ══════════════════════════════════════════════════════════════════════════════

var mountedContainer = null;

var resizeObserver = new ResizeObserver(function() {
  if (!mountedContainer) return;
  var w = mountedContainer.clientWidth;
  var h = mountedContainer.clientHeight || Math.round(w / 1.54);
  renderer.setSize(w, h);
  composer.setSize(w, h);
  outlinePass.resolution.set(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
});

// ══════════════════════════════════════════════════════════════════════════════
// MOUNT / UNMOUNT
// ══════════════════════════════════════════════════════════════════════════════

function mount(container) {
  if (typeof container === 'string') container = document.querySelector(container);
  if (!container) return;
  if (mountedContainer === container) { if (!animId) animate(0); return; }
  if (mountedContainer) resizeObserver.unobserve(mountedContainer);
  mountedContainer = container;
  container.appendChild(canvas);
  resizeObserver.observe(container);
  if (!animId) animate(0);
  setCameraView('lateral');
}

function unmount() {
  if (animId) { cancelAnimationFrame(animId); animId = null; }
  if (mountedContainer) {
    resizeObserver.unobserve(mountedContainer);
    if (canvas.parentNode === mountedContainer) mountedContainer.removeChild(canvas);
    mountedContainer = null;
  }
  hoveredMesh  = null;
  selectedMesh = null;
  outlinePass.selectedObjects = [];
}

// ══════════════════════════════════════════════════════════════════════════════
// PUBLIC API
// ══════════════════════════════════════════════════════════════════════════════

window.__brain3d = {
  mount, unmount,
  setCameraView, CAMERA_VIEWS,
  highlightRegion, dimAllRegions, resetRegions,
  regionMeshes,
  // Compat aliases
  corticalMeshes:    regionMeshes,
  subcorticalMeshes: [],
  // Feature stubs (rebuilt incrementally as needed)
  toggleGlass:       function() {},
  setCsMode:         function() {},
  setCsSlider:       function() {},
  setVascTerritory:  function() {},
  toggleLesionMode:  function() {},
  resetLesions:      function() {},
  activatePathology: function() {},
  clearPathology:    function() {},
  PATHOLOGY_DEFS:    {},
  showPathway:       function() {},
  hidePathway:       function() {},
  setPathway:        function() {},
};

// Auto-mount on load if ?view=3d
var _v = new URLSearchParams(location.search).get('view');
if (_v === '3d') {
  var _c = document.getElementById('brain-container-3d');
  if (_c) mount(_c);
}
