/**
 * brain-3d.js — Hybrid Brain Engine (v4)
 *
 * Visual layer  : full_brain_hires.glb  (FreeSurfer fsaverage7, sulcal texture,
 *                 regenerated in region coordinate space by fix_hires_coords.py)
 * Interaction   : per-region GLBs loaded INVISIBLY as raycasting + highlight overlays
 *
 * Coordinate system (matches generate_subcortical.py / fix_hires_coords.py):
 *   x = −x_FreeSurfer  (left-hemi lateral surface at +x, medial at MIDLINE_X ≈ 0.118)
 *   y = z_FreeSurfer   (superior = up)
 *   z = y_FreeSurfer   (anterior = depth)
 *   scale = 1/75,  COORD_OFFSET = [0.118, −0.204, 0.438]
 *   CAM_TARGET = (0.55, 0.05, 0.10)
 *   Brain midline x (interhemispheric fissure) = COORD_OFFSET.x = 0.118
 *
 * Glass-brain isolation mode:
 *   When a region is selected while glass is ON, the hires brain goes to 10% opacity
 *   and the selected region overlay is fully opaque — "dissection" / isolation look.
 *
 * Exposed as window.__brain3d (same interface as previous versions).
 */

import * as THREE        from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }    from 'three/addons/loaders/GLTFLoader.js';

console.log('[brain-3d] v4 loaded, Three.js r' + THREE.REVISION);

// Interhemispheric midline in our coordinate space (= COORD_OFFSET.x from Python scripts)
const MIDLINE_X = 0.118;

// ══════════════════════════════════════════════════════════════════════════════
// REGION OVERLAY COLORS — vivid, distinct palette for highlighted overlays
// ══════════════════════════════════════════════════════════════════════════════

const REGION_COLORS = {
  frontal_lobe:         0xE8805A,
  prefrontal_cortex:    0xD4724E,
  brocas_area:          0xE86060,
  motor_cortex:         0xD08040,
  medial_frontal:       0xCC7050,
  parietal_lobe:        0x7EB8C8,
  somatosensory_cortex: 0x60A8C0,
  temporal_lobe:        0x80C870,
  wernickes_area:       0x60B850,
  occipital_lobe:       0xC080D0,
  cingulate_gyrus:      0xD0A030,
  thalamus:             0xE09060,
  hippocampus:          0xE07050,
  amygdala:             0xD86060,
  caudate:              0xD08860,
  putamen:              0xC07850,
  globus_pallidus:      0xB87060,
  brainstem:            0x9090C0,
  cerebellum:           0x80C0A0,
};

// ══════════════════════════════════════════════════════════════════════════════
// RENDERER
// ══════════════════════════════════════════════════════════════════════════════

var renderer, canvas;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping         = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  canvas = renderer.domElement;
  canvas.style.cssText = 'display:block; border-radius:16px; cursor:grab;';
} catch (e) {
  console.error('[brain-3d] WebGL unavailable:', e.message);
  window.dispatchEvent(new CustomEvent('brain3dNoWebGL'));
  window.__brain3d = {
    mount:function(){}, unmount:function(){}, setCameraView:function(){},
    highlightRegion:function(){}, dimAllRegions:function(){}, resetRegions:function(){},
    toggleGlass:function(){}, toggleSplit:function(){}, setSubcorticalVisible:function(){},
    regionMeshes:[], corticalMeshes:[], subcorticalMeshes:[],
    ready: Promise.resolve(), CAMERA_VIEWS:{},
    setCsMode:function(){}, setCsSlider:function(){}, setVascTerritory:function(){},
    toggleLesionMode:function(){}, resetLesions:function(){}, activatePathology:function(){},
    clearPathology:function(){}, showPathway:function(){}, hidePathway:function(){}, setPathway:function(){},
    PATHOLOGY_DEFS:{},
  };
  throw e;
}

// ══════════════════════════════════════════════════════════════════════════════
// SCENE + CAMERA + CONTROLS
// ══════════════════════════════════════════════════════════════════════════════

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0A0D14);

const camera = new THREE.PerspectiveCamera(40, 1.54, 0.1, 100);
camera.position.set(4.8, 0.5, 0.4);

const CAM_TARGET = new THREE.Vector3(0.55, 0.05, 0.10);
const controls   = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.minDistance   = 2.0;
controls.maxDistance   = 10.0;
controls.enablePan     = false;
controls.target.copy(CAM_TARGET);
controls.update();

// ══════════════════════════════════════════════════════════════════════════════
// LIGHTING
// ══════════════════════════════════════════════════════════════════════════════

const keyLight = new THREE.DirectionalLight(0xFFF5EE, 2.8);
keyLight.position.set(5, 7, 4);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xD0E0FF, 0.6);
fillLight.position.set(-4, 2, -2);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xFFE8C0, 1.0);
rimLight.position.set(0, -5, -4);
scene.add(rimLight);

scene.add(new THREE.HemisphereLight(0xC8D8F0, 0x401808, 0.45));
scene.add(new THREE.AmbientLight(0xFFEEE8, 0.12));

// ══════════════════════════════════════════════════════════════════════════════
// MESH REGISTRIES
// ══════════════════════════════════════════════════════════════════════════════

const brainGroup        = new THREE.Group();
scene.add(brainGroup);

const hiresMeshes       = [];   // all sub-meshes of full_brain_hires.glb
var   hiresGlassOn      = false;
var   splitOn           = false;

const regionMeshes      = [];   // overlay meshes (invisible until highlighted)
const corticalMeshes    = [];
const subcorticalMeshes = [];

var selectedRegionId    = null; // currently selected / isolated region
var hoveredRegionId     = null;
var quizMode            = false; // true while dimAllRegions is active

const loader = new GLTFLoader();

// ══════════════════════════════════════════════════════════════════════════════
// HIRES BRAIN LOADER — visual beauty layer
// ══════════════════════════════════════════════════════════════════════════════

function loadHiresBrain() {
  return new Promise(function(resolve) {
    loader.load(
      'data/brain_meshes/full_brain_hires.glb',
      function(gltf) {
        gltf.scene.traverse(function(child) {
          if (!child.isMesh) return;
          child.geometry.computeVertexNormals();
          if (child.material) {
            child.material.roughness   = 0.82;
            child.material.metalness   = 0.00;
            child.material.needsUpdate = true;
          }
          child.castShadow    = false;
          child.receiveShadow = false;
          hiresMeshes.push(child);
        });
        brainGroup.add(gltf.scene);
        console.log('[brain-3d] Hires brain loaded — ' + hiresMeshes.length + ' mesh(es)');
        resolve();
      },
      undefined,
      function(err) {
        console.warn('[brain-3d] Hires brain load failed (region overlays still work):', err);
        resolve(); // non-fatal
      }
    );
  });
}

// Apply / restore glass appearance on all hires sub-meshes
function _applyHiresState() {
  hiresMeshes.forEach(function(m) {
    if (!m.material) return;
    if (hiresGlassOn) {
      m.material.transparent = true;
      m.material.opacity     = 0.10;
      m.material.depthWrite  = false;
      m.material.roughness   = 0.08;
      m.material.color.setHex(0xC8D8E8);
    } else {
      m.material.transparent = false;
      m.material.opacity     = 1.0;
      m.material.depthWrite  = true;
      m.material.roughness   = 0.82;
      m.material.color.setHex(0xFFFFFF); // white = texture shows through fully
    }
    m.material.needsUpdate = true;
  });
}

// Dim hires brain for quiz mode (overlays become visible cues)
function _applyHiresDim(dim) {
  hiresMeshes.forEach(function(m) {
    if (!m.material) return;
    if (dim) {
      m.material.transparent = true;
      m.material.opacity     = 0.50;
      m.material.depthWrite  = false;
    } else if (!hiresGlassOn) {
      m.material.transparent = false;
      m.material.opacity     = 1.0;
      m.material.depthWrite  = true;
    }
    m.material.needsUpdate = true;
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// REGION OVERLAY LOADER — invisible meshes for raycasting + highlighting
// ══════════════════════════════════════════════════════════════════════════════

function makeOverlayMaterial(regionId) {
  var col = new THREE.Color(REGION_COLORS[regionId] || 0x8888AA);
  var mat = new THREE.MeshStandardMaterial({
    color:             col,
    roughness:         0.55,
    metalness:         0.00,
    emissive:          col,
    emissiveIntensity: 0.20,
    transparent:       true,
    opacity:           0.0,   // hidden by default
    depthWrite:        false,
    side:              THREE.DoubleSide,
  });
  mat._origColor = col.clone();
  return mat;
}

function loadRegionOverlay(regionId, entry) {
  return new Promise(function(resolve) {
    loader.load(
      entry.file,
      function(gltf) {
        var mat = makeOverlayMaterial(regionId);

        gltf.scene.traverse(function(child) {
          if (!child.isMesh) return;
          child.geometry.computeVertexNormals();
          child.material      = mat;
          child.name          = regionId;
          child.castShadow    = false;
          child.receiveShadow = false;
          child.userData = {
            regionId:   regionId,
            label:      regionId,
            type:       entry.type,
            overlayMat: mat,
          };

          // Gold selection outline (BackSide, hidden until selected)
          var selMat = new THREE.MeshBasicMaterial({
            color:       0xFFD060,
            side:        THREE.BackSide,
            transparent: true,
            opacity:     0.0,
            depthWrite:  false,
          });
          var selOutline = new THREE.Mesh(child.geometry, selMat);
          selOutline.scale.setScalar(1.045);
          selOutline.renderOrder = 3;
          selOutline.userData    = { isOutline: true };
          child.userData.selOutline = selOutline;
          child.add(selOutline);

          regionMeshes.push(child);
          if (entry.type === 'subcortical') {
            subcorticalMeshes.push(child);
          } else {
            corticalMeshes.push(child);
          }
        });

        brainGroup.add(gltf.scene);
        resolve();
      },
      undefined,
      function(err) {
        console.warn('[brain-3d] Region overlay failed (' + regionId + '):', err);
        resolve(); // non-fatal
      }
    );
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// LOAD ORCHESTRATION
// ══════════════════════════════════════════════════════════════════════════════

var _readyResolve = null;
var _readyPromise = new Promise(function(res) { _readyResolve = res; });

async function loadBrain() {
  console.log('[brain-3d] loadBrain() starting');

  // Load manifest + hires brain concurrently
  window.dispatchEvent(new CustomEvent('brain3dProgress', { detail: { loaded: 0, total: 20 } }));

  var manifestResult = null;
  try {
    var [res] = await Promise.allSettled([
      fetch('data/brain_regions_manifest.json').then(function(r) { return r.json(); }),
      loadHiresBrain(),
    ]);
    if (res.status === 'fulfilled') manifestResult = res.value;
  } catch (e) {
    console.warn('[brain-3d] Init load issue:', e);
  }

  // Fire brain3dReady so the loading overlay clears and the hires brain becomes visible.
  // Region overlays continue loading silently in the background.
  window.dispatchEvent(new CustomEvent('brain3dProgress', { detail: { loaded: 10, total: 20 } }));
  window.dispatchEvent(new CustomEvent('brain3dReady', { detail: { regionCount: 0 } }));

  if (!manifestResult) {
    _readyResolve();
    return;
  }

  // Load region overlays in background
  var regionIds = Object.keys(manifestResult).filter(function(id) {
    return manifestResult[id].type !== 'glass';
  });
  var loaded = 10;
  var total  = 10 + regionIds.length;

  await Promise.allSettled(
    regionIds.map(function(id) {
      return loadRegionOverlay(id, manifestResult[id]).then(function() {
        loaded++;
        window.dispatchEvent(new CustomEvent('brain3dProgress', {
          detail: { loaded: loaded, total: total }
        }));
      });
    })
  );

  console.log('[brain-3d] All region overlays loaded — count: ' + regionMeshes.length);
  _readyResolve();
}

loadBrain();

// ══════════════════════════════════════════════════════════════════════════════
// CAMERA PRESET VIEWS
// ══════════════════════════════════════════════════════════════════════════════

var CAMERA_VIEWS = {
  lateral:    new THREE.Vector3( 4.8,  0.5,  0.4),
  medial:     new THREE.Vector3(-3.8,  0.5,  0.4),
  superior:   new THREE.Vector3( 0.6,  5.5,  0.8),
  inferior:   new THREE.Vector3( 0.6, -5.5,  0.8),
  anterior:   new THREE.Vector3( 0.5,  0.5,  5.2),
  posterior:  new THREE.Vector3( 0.5,  0.5, -5.6),
  brainstem:  new THREE.Vector3( 1.8, -3.2, -3.5),
  cerebellum: new THREE.Vector3( 0.6, -4.2, -3.0),
};

var camFrom = null, camTo = null, camT = 0;
const CAM_DUR = 0.72;

function setCameraView(name) {
  var tgt = CAMERA_VIEWS[name];
  if (!tgt) return;
  camFrom = camera.position.clone();
  camTo   = tgt.clone();
  camT    = 0;
  controls.target.copy(CAM_TARGET);
}

// ══════════════════════════════════════════════════════════════════════════════
// OVERLAY HELPERS
// ══════════════════════════════════════════════════════════════════════════════

function _setOverlay(mesh, opacity, selOpacity) {
  var m = mesh.userData.overlayMat;
  if (!m) return;
  m.opacity     = opacity;
  m.depthWrite  = opacity > 0.5;
  m.needsUpdate = true;
  var sel = mesh.userData.selOutline;
  if (sel && sel.material) {
    sel.material.opacity    = selOpacity;
    sel.material.needsUpdate = true;
  }
}

function _clearAllOverlays() {
  regionMeshes.forEach(function(m) { _setOverlay(m, 0, 0); });
}

// ══════════════════════════════════════════════════════════════════════════════
// PUBLIC REGION API
// ══════════════════════════════════════════════════════════════════════════════

/**
 * highlightRegion
 *   Explore mode (glass ON)  : hires→glass, selected region→fully opaque (isolation)
 *   Explore mode (glass OFF) : selected region→coloured 75% overlay on hires brain
 *   Quiz mode               : same as explore but called after dimAllRegions
 */
function highlightRegion(regionId) {
  selectedRegionId = regionId;
  _clearAllOverlays();

  if (hiresGlassOn) {
    // Isolation view: everything glass except the target region
    _applyHiresState();  // confirms glass state
    regionMeshes.forEach(function(m) {
      if (m.userData.regionId === regionId) {
        _setOverlay(m, 0.95, 0.80);
      }
    });
  } else {
    // Normal: dimmed hires + coloured overlay only on target
    _applyHiresDim(false);
    regionMeshes.forEach(function(m) {
      if (m.userData.regionId === regionId) {
        _setOverlay(m, 0.78, 0.0);
      }
    });
  }
}

/**
 * dimAllRegions — quiz click mode
 * Dims hires brain + shows semi-transparent coloured halos on active regions only
 */
function dimAllRegions(exceptIds) {
  quizMode = true;
  exceptIds = exceptIds || [];
  selectedRegionId = null;
  _clearAllOverlays();
  _applyHiresDim(true);

  regionMeshes.forEach(function(m) {
    if (exceptIds.indexOf(m.userData.regionId) !== -1) {
      _setOverlay(m, 0.50, 0.0);
    }
  });
}

/**
 * resetRegions — called between questions and when info panel closes
 */
function resetRegions() {
  quizMode = false;
  selectedRegionId = null;
  _clearAllOverlays();
  _applyHiresState();   // restore to current glass state (opaque if glass off)
  if (!hiresGlassOn) {
    _applyHiresDim(false);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// GLASS BRAIN + SPLIT
// ══════════════════════════════════════════════════════════════════════════════

function toggleGlass() {
  hiresGlassOn = !hiresGlassOn;
  _applyHiresState();

  if (!hiresGlassOn) {
    // Glass turned OFF: clear any isolation overlay
    _clearAllOverlays();
    selectedRegionId = null;
  } else if (selectedRegionId) {
    // Glass turned ON while a region is selected: show isolation immediately
    highlightRegion(selectedRegionId);
  }
}

function setSubcorticalVisible(show) {
  subcorticalMeshes.forEach(function(m) {
    _setOverlay(m, show ? 0.75 : 0.0, 0.0);
  });
}

function toggleSplit() {
  splitOn = !splitOn;
  if (splitOn) {
    // Keep left hemisphere (x >= MIDLINE_X) by clipping away right hemisphere (x < MIDLINE_X)
    // THREE.Plane clips fragments where dot(n, p) + d < 0
    // dot((1,0,0), p) - MIDLINE_X < 0  →  x < MIDLINE_X  → clips right hemisphere
    renderer.clippingPlanes = [ new THREE.Plane(new THREE.Vector3(1, 0, 0), -MIDLINE_X) ];
  } else {
    renderer.clippingPlanes = [];
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// POINTER + RAYCASTING
// ══════════════════════════════════════════════════════════════════════════════

var raycaster   = new THREE.Raycaster();
var mouse       = new THREE.Vector2(-10, -10);
var downPos     = null;

function _showTooltip(regionId) {
  var tip  = document.getElementById('hover-tip');
  var name = document.getElementById('hover-tip-name');
  if (!tip || !name) return;
  if (regionId) {
    name.textContent = regionId.replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    tip.style.opacity = '1';
  } else {
    tip.style.opacity = '0';
  }
}

function _rayHit() {
  raycaster.setFromCamera(mouse, camera);
  var hits = raycaster.intersectObjects(regionMeshes, false);
  return hits.length ? hits[0].object : null;
}

canvas.addEventListener('pointermove', function(e) {
  var r   = canvas.getBoundingClientRect();
  mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
  mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;

  var hit = _rayHit();
  var id  = hit ? hit.userData.regionId : null;

  if (id !== hoveredRegionId) {
    // Restore previous hover overlay (unless it's the selected region)
    if (hoveredRegionId && hoveredRegionId !== selectedRegionId && !quizMode) {
      regionMeshes.forEach(function(m) {
        if (m.userData.regionId === hoveredRegionId) _setOverlay(m, 0, 0);
      });
    }
    hoveredRegionId = id;
    canvas.style.cursor = id ? 'pointer' : 'grab';
    _showTooltip(id);

    // Show hover overlay (unless already in quiz or isolation mode)
    if (id && id !== selectedRegionId && !quizMode) {
      regionMeshes.forEach(function(m) {
        if (m.userData.regionId === id) _setOverlay(m, 0.30, 0);
      });
    }

    // Drive brain-pathology.html's direct emissive access
    regionMeshes.forEach(function(m) {
      if (m.userData.overlayMat) {
        m.userData.overlayMat.emissiveIntensity = (m.userData.regionId === id) ? 0.40 : 0.20;
      }
    });
  }
});

canvas.addEventListener('pointerdown', function(e) {
  canvas.style.cursor = 'grabbing';
  downPos = { x: e.clientX, y: e.clientY };
});

canvas.addEventListener('pointerup', function(e) {
  canvas.style.cursor = hoveredRegionId ? 'pointer' : 'grab';
  if (!downPos) return;
  var dx = e.clientX - downPos.x;
  var dy = e.clientY - downPos.y;
  if (Math.sqrt(dx * dx + dy * dy) < 5) {
    var r = canvas.getBoundingClientRect();
    mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
    mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;
    var hit = _rayHit();
    if (hit) {
      var regionId = hit.userData.regionId;
      if (window.__brainUI && window.__brainUI.openRegion) {
        window.__brainUI.openRegion(regionId);
      }
      if (!quizMode) {
        highlightRegion(regionId);
      }
    }
  }
  downPos = null;
});

canvas.addEventListener('pointerleave', function() {
  mouse.set(-10, -10);
  if (hoveredRegionId && hoveredRegionId !== selectedRegionId && !quizMode) {
    regionMeshes.forEach(function(m) {
      if (m.userData.regionId === hoveredRegionId) _setOverlay(m, 0, 0);
    });
  }
  hoveredRegionId = null;
  _showTooltip(null);
});

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
    var e = 1 - Math.pow(1 - camT, 3);  // ease-out cubic
    camera.position.lerpVectors(camFrom, camTo, e);
    camera.lookAt(controls.target);
    if (camT >= 1) { camTo = null; controls.update(); }
  } else {
    controls.update();
  }

  renderer.render(scene, camera);
}

// ══════════════════════════════════════════════════════════════════════════════
// RESIZE + MOUNT / UNMOUNT
// ══════════════════════════════════════════════════════════════════════════════

var mountedContainer = null;

var resizeObserver = new ResizeObserver(function() {
  if (!mountedContainer) return;
  var w = mountedContainer.clientWidth;
  var h = mountedContainer.clientHeight || Math.round(w / 1.54);
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
});

function mount(container) {
  if (typeof container === 'string') container = document.querySelector(container);
  if (!container) return;
  if (mountedContainer === container) { if (!animId) animate(0); return; }
  if (mountedContainer) resizeObserver.unobserve(mountedContainer);
  mountedContainer = container;
  container.appendChild(canvas);
  resizeObserver.observe(container);
  var w = container.clientWidth  || window.innerWidth  - 256;
  var h = container.clientHeight || window.innerHeight - 52;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
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
}

// ══════════════════════════════════════════════════════════════════════════════
// PUBLIC API
// ══════════════════════════════════════════════════════════════════════════════

window.__brain3d = {
  mount, unmount,
  setCameraView, CAMERA_VIEWS,
  highlightRegion, dimAllRegions, resetRegions,
  regionMeshes, corticalMeshes, subcorticalMeshes,
  toggleGlass, toggleSplit, setSubcorticalVisible,
  ready: _readyPromise,
  // Compat stubs
  setCsMode:         function() {},
  setCsSlider:       function() {},
  setVascTerritory:  function() {},
  toggleLesionMode:  function() {},
  resetLesions:      function() {},
  activatePathology: function() {},
  clearPathology:    function() {},
  showPathway:       function() {},
  hidePathway:       function() {},
  setPathway:        function() {},
  PATHOLOGY_DEFS:    {},
};

// Auto-mount to well-known container IDs
var _c = document.getElementById('brain-stage') || document.getElementById('brain-container-3d');
if (_c) mount(_c);
