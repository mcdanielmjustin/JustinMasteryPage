/**
 * brain-3d.js — Hybrid Brain Engine (v5)
 *
 * Visual layer:
 *   • full_brain_hires.glb   — cerebral cortex (pial surface, 655k faces, sulcal texture)
 *   • brainstem.glb          — always visible, tissue-coloured permanent mesh
 *   • cerebellum.glb         — always visible, tissue-coloured permanent mesh
 *
 * Interaction overlays (cortical + subcortical region GLBs):
 *   • Loaded with mesh.visible = false by default — ZERO draw-call overhead
 *   • Made visible only when highlighted / selected / dimmed
 *
 * Glass-brain isolation:
 *   Glass ON + region selected → hires brain + subcortical permanents → glass (10% opacity),
 *   selected region overlay → fully opaque coloured mesh (isolation / dissection view)
 *
 * Performance:
 *   • visible=false (not just opacity=0) eliminates phantom draw calls from 19 overlays
 *   • No post-processing passes, no shadow maps, no edge geometry
 *
 * Coordinate system (matches generate_brain_meshes.py / fix_hires_coords.py):
 *   x = −x_FS  (left-hemi lateral at +x)
 *   y = z_FS   (superior = up)
 *   z = y_FS   (anterior = depth)
 *   scale 1/75, COORD_OFFSET [0.118, −0.204, 0.438], midline x = 0.118
 */

import * as THREE        from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }    from 'three/addons/loaders/GLTFLoader.js';

console.log('[brain-3d] v5 loaded, Three.js r' + THREE.REVISION);

const MIDLINE_X = 0.118;

// ══════════════════════════════════════════════════════════════════════════════
// OVERLAY COLORS — vivid, used only when a region is highlighted
// ══════════════════════════════════════════════════════════════════════════════

const OVERLAY_COLORS = {
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

// Tissue colour for permanent subcortical meshes — similar to hires brain flesh tone
const TISSUE_COLOR = 0xD4AA90;

// Regions that are always displayed as permanent meshes (not in pial surface)
const PERMANENT_SUBCORTICAL = new Set(['brainstem', 'cerebellum']);

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
    ready:Promise.resolve(), CAMERA_VIEWS:{},
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

const hiresMeshes       = [];   // full_brain_hires.glb sub-meshes
const permanentMeshes   = [];   // brainstem, cerebellum — always visible
var   hiresGlassOn      = false;
var   splitOn           = false;

// Overlay meshes: visible = false by default (zero GPU cost when not shown)
const regionMeshes      = [];   // all overlay meshes (flat list)
const corticalMeshes    = [];
const subcorticalMeshes = [];

var   selectedRegionId  = null;
var   hoveredRegionId   = null;
var   quizMode          = false;

const loader = new GLTFLoader();

// ══════════════════════════════════════════════════════════════════════════════
// HIRES BRAIN LOADER
// ══════════════════════════════════════════════════════════════════════════════

function loadHiresBrain() {
  return new Promise(function(resolve) {
    loader.load('data/brain_meshes/full_brain_hires.glb',
      function(gltf) {
        gltf.scene.traverse(function(child) {
          if (!child.isMesh) return;
          child.geometry.computeVertexNormals();
          if (child.material) {
            child.material.roughness   = 0.82;
            child.material.metalness   = 0.00;
            child.material.needsUpdate = true;
          }
          child.castShadow = child.receiveShadow = false;
          hiresMeshes.push(child);
        });
        brainGroup.add(gltf.scene);
        console.log('[brain-3d] Hires brain loaded (' + hiresMeshes.length + ' mesh)');
        resolve();
      },
      undefined,
      function(err) { console.warn('[brain-3d] Hires load failed:', err); resolve(); }
    );
  });
}

function _applyHiresGlass(on) {
  var allVisual = hiresMeshes.concat(permanentMeshes);
  allVisual.forEach(function(m) {
    if (!m.material) return;
    if (on) {
      m.material.transparent = true;
      m.material.opacity     = 0.10;
      m.material.depthWrite  = false;
      m.material.roughness   = 0.08;
    } else {
      m.material.transparent = false;
      m.material.opacity     = 1.0;
      m.material.depthWrite  = true;
      m.material.roughness   = (hiresMeshes.indexOf(m) >= 0) ? 0.82 : 0.75;
    }
    m.material.needsUpdate = true;
  });
}

function _dimHires(on) {
  var allVisual = hiresMeshes.concat(permanentMeshes);
  allVisual.forEach(function(m) {
    if (!m.material) return;
    if (on) {
      m.material.transparent = true;
      m.material.opacity     = 0.45;
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
// REGION OVERLAY LOADER
// permanent=true → always visible flesh-tone mesh (brainstem, cerebellum)
// permanent=false → invisible overlay, shown only when highlighted
// ══════════════════════════════════════════════════════════════════════════════

function loadRegion(regionId, entry, permanent) {
  return new Promise(function(resolve) {
    loader.load(entry.file,
      function(gltf) {
        var col   = permanent
              ? new THREE.Color(TISSUE_COLOR)
              : new THREE.Color(OVERLAY_COLORS[regionId] || 0x8888AA);
        var mat   = new THREE.MeshStandardMaterial({
          color:             col,
          roughness:         permanent ? 0.78 : 0.55,
          metalness:         0.00,
          emissive:          col,
          emissiveIntensity: permanent ? 0.04 : 0.20,
          transparent:       !permanent,
          opacity:           permanent ? 1.0 : 1.0,  // visibility controlled by .visible
          side:              THREE.FrontSide,
        });
        mat._origColor = col.clone();

        gltf.scene.traverse(function(child) {
          if (!child.isMesh) return;
          child.geometry.computeVertexNormals();
          child.material      = mat;
          child.name          = regionId;
          child.castShadow    = child.receiveShadow = false;
          child.visible       = permanent;   // ← key: false until needed
          child.userData      = {
            regionId:   regionId,
            label:      regionId,
            type:       entry.type,
            permanent:  permanent,
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
          selOutline.visible     = false;
          selOutline.userData    = { isOutline: true };
          child.userData.selOutline = selOutline;
          child.add(selOutline);

          if (permanent) {
            permanentMeshes.push(child);
          }
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
      function(err) { console.warn('[brain-3d] Region load failed (' + regionId + '):', err); resolve(); }
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

  window.dispatchEvent(new CustomEvent('brain3dProgress', { detail: { loaded: 0, total: 20 } }));

  var manifest = null;
  try {
    var [mRes] = await Promise.allSettled([
      fetch('data/brain_regions_manifest.json').then(function(r) { return r.json(); }),
      loadHiresBrain(),
    ]);
    if (mRes.status === 'fulfilled') manifest = mRes.value;
  } catch (e) { console.warn('[brain-3d] Init error:', e); }

  // Fire brain3dReady so loading overlay clears — overlays continue in background
  window.dispatchEvent(new CustomEvent('brain3dProgress', { detail: { loaded: 10, total: 20 } }));
  window.dispatchEvent(new CustomEvent('brain3dReady',    { detail: { regionCount: 0 } }));

  if (!manifest) { _readyResolve(); return; }

  var regionIds = Object.keys(manifest).filter(function(id) {
    return manifest[id].type !== 'glass';
  });
  var loaded = 10, total = 10 + regionIds.length;

  await Promise.allSettled(
    regionIds.map(function(id) {
      var permanent = PERMANENT_SUBCORTICAL.has(id);
      return loadRegion(id, manifest[id], permanent).then(function() {
        loaded++;
        window.dispatchEvent(new CustomEvent('brain3dProgress',
          { detail: { loaded: loaded, total: total } }));
      });
    })
  );

  console.log('[brain-3d] All loaded — ' + regionMeshes.length + ' regions, '
              + permanentMeshes.length + ' permanent');
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
// OVERLAY VISIBILITY HELPERS
// ══════════════════════════════════════════════════════════════════════════════

function _showOverlay(mesh, showSel) {
  mesh.visible = true;
  var sel = mesh.userData.selOutline;
  if (sel) sel.visible = !!showSel;
}

// Hide overlay — but leave permanent meshes (brainstem, cerebellum) visible
function _hideOverlay(mesh) {
  if (mesh.userData.permanent) return;
  mesh.visible = false;
  var sel = mesh.userData.selOutline;
  if (sel) sel.visible = false;
}

function _hideAllOverlays() {
  regionMeshes.forEach(_hideOverlay);
}

// Restore permanent meshes to their normal tissue-coloured state
function _restorePermanent() {
  permanentMeshes.forEach(function(m) {
    var mat = m.userData.overlayMat;
    if (!mat) return;
    mat.color.copy(mat._origColor);
    mat.emissive.copy(mat._origColor);
    mat.emissiveIntensity = 0.04;
    mat.transparent       = false;
    mat.opacity           = 1.0;
    mat.needsUpdate       = true;
    m.visible = true;
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// PUBLIC REGION API
// ══════════════════════════════════════════════════════════════════════════════

function highlightRegion(regionId) {
  selectedRegionId = regionId;
  _hideAllOverlays();

  regionMeshes.forEach(function(m) {
    if (m.userData.regionId !== regionId) return;
    // Make the overlay visible with vivid colour
    var mat = m.userData.overlayMat;
    if (mat) {
      var col = new THREE.Color(OVERLAY_COLORS[regionId] || 0x8888AA);
      mat.color.copy(col);
      mat.emissive.copy(col);
      mat.emissiveIntensity = hiresGlassOn ? 0.35 : 0.22;
      mat.transparent       = hiresGlassOn ? false : true;
      mat.opacity           = hiresGlassOn ? 1.0 : 0.82;
      mat.needsUpdate       = true;
    }
    _showOverlay(m, false);
  });

  if (hiresGlassOn) {
    _applyHiresGlass(true);
  }
}

function dimAllRegions(exceptIds) {
  quizMode = true;
  exceptIds = exceptIds || [];
  selectedRegionId = null;
  _hideAllOverlays();
  _dimHires(true);

  regionMeshes.forEach(function(m) {
    if (exceptIds.indexOf(m.userData.regionId) === -1) return;
    var mat = m.userData.overlayMat;
    if (mat) {
      var col = new THREE.Color(OVERLAY_COLORS[m.userData.regionId] || 0x8888AA);
      mat.color.copy(col);
      mat.emissive.copy(col);
      mat.emissiveIntensity = 0.18;
      mat.transparent       = true;
      mat.opacity           = 0.55;
      mat.needsUpdate       = true;
    }
    _showOverlay(m, false);
  });
}

function resetRegions() {
  quizMode = false;
  selectedRegionId = null;
  _hideAllOverlays();
  _restorePermanent();
  _applyHiresGlass(hiresGlassOn);
  if (!hiresGlassOn) _dimHires(false);
}

// ══════════════════════════════════════════════════════════════════════════════
// GLASS + SPLIT
// ══════════════════════════════════════════════════════════════════════════════

function toggleGlass() {
  hiresGlassOn = !hiresGlassOn;
  _applyHiresGlass(hiresGlassOn);
  if (!hiresGlassOn) {
    _hideAllOverlays();
    _restorePermanent();
    selectedRegionId = null;
  } else if (selectedRegionId) {
    highlightRegion(selectedRegionId);
  }
}

function setSubcorticalVisible(show) {
  subcorticalMeshes.forEach(function(m) {
    if (m.userData.permanent) {
      m.visible = show;
    } else {
      if (!show) _hideOverlay(m);
    }
  });
}

function toggleSplit() {
  splitOn = !splitOn;
  renderer.clippingPlanes = splitOn
    ? [ new THREE.Plane(new THREE.Vector3(1, 0, 0), -MIDLINE_X) ]
    : [];
}

// ══════════════════════════════════════════════════════════════════════════════
// RAYCASTING + POINTER
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

// Raycast against all region meshes (permanent visible ones are always hittable;
// invisible overlays require a small trick: temporarily make them raycaster-only).
function _rayHit() {
  raycaster.setFromCamera(mouse, camera);
  // For invisible overlays, temporarily allow raycast by checking all meshes
  // (Three.js raycaster skips visible=false meshes by default, so we must
  // include all and filter out permanent+invisible combos manually).
  var candidates = regionMeshes.filter(function(m) {
    return m.visible || true;  // include all — invisible ones won't intersect hires brain
  });
  var hits = raycaster.intersectObjects(regionMeshes, false);
  return hits.length ? hits[0].object : null;
}

// Actually Three.js DOES skip visible=false in intersectObjects. For hover on
// invisible overlays we need another approach. We'll raycast against the hires
// brain bounding boxes per region instead — but for simplicity, we just use
// the always-visible permanent meshes for direct hover, and disable cortical hover
// unless glass mode shows overlays.
function _rayHitSafe() {
  raycaster.setFromCamera(mouse, camera);
  // Only hit meshes that are actually rendered (visible=true)
  var visible = regionMeshes.filter(function(m) { return m.visible; });
  var hits    = raycaster.intersectObjects(visible, false);
  return hits.length ? hits[0].object : null;
}

canvas.addEventListener('pointermove', function(e) {
  var r   = canvas.getBoundingClientRect();
  mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
  mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;

  var hit = _rayHitSafe();
  var id  = hit ? hit.userData.regionId : null;

  if (id !== hoveredRegionId) {
    // Restore previous hover (unless it's the selected region or permanent)
    if (hoveredRegionId && hoveredRegionId !== selectedRegionId) {
      regionMeshes.forEach(function(m) {
        if (m.userData.regionId !== hoveredRegionId) return;
        if (m.userData.permanent) {
          // Restore permanent to tissue color
          var mat = m.userData.overlayMat;
          if (mat) { mat.emissiveIntensity = 0.04; mat.needsUpdate = true; }
        } else if (!quizMode) {
          _hideOverlay(m);
        }
      });
    }

    hoveredRegionId = id;
    canvas.style.cursor = id ? 'pointer' : 'grab';
    _showTooltip(id);

    // Show hover highlight
    if (id && id !== selectedRegionId) {
      regionMeshes.forEach(function(m) {
        if (m.userData.regionId !== id) return;
        var mat = m.userData.overlayMat;
        if (!mat) return;
        if (m.userData.permanent) {
          mat.emissiveIntensity = 0.30;
          mat.needsUpdate = true;
        } else if (!quizMode) {
          var col = new THREE.Color(OVERLAY_COLORS[id] || 0x8888AA);
          mat.color.copy(col); mat.emissive.copy(col);
          mat.emissiveIntensity = 0.22;
          mat.transparent = true; mat.opacity = 0.35;
          mat.needsUpdate = true;
          _showOverlay(m, false);
        }
      });
    }

    // Let brain-pathology.html's direct emissive access also work
    regionMeshes.forEach(function(m) {
      if (m.userData.overlayMat) {
        m.userData.overlayMat.emissiveIntensity =
          (m.userData.regionId === id) ? 0.35 : (m.userData.permanent ? 0.04 : 0.20);
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
  var dx = e.clientX - downPos.x, dy = e.clientY - downPos.y;
  if (Math.sqrt(dx * dx + dy * dy) < 5) {
    var r = canvas.getBoundingClientRect();
    mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
    mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;
    var hit = _rayHitSafe();
    if (hit) {
      var rid = hit.userData.regionId;
      if (window.__brainUI && window.__brainUI.openRegion) window.__brainUI.openRegion(rid);
      if (!quizMode) highlightRegion(rid);
    }
  }
  downPos = null;
});

canvas.addEventListener('pointerleave', function() {
  mouse.set(-10, -10);
  if (hoveredRegionId && hoveredRegionId !== selectedRegionId) {
    regionMeshes.forEach(function(m) {
      if (m.userData.regionId !== hoveredRegionId) return;
      if (m.userData.permanent) {
        if (m.userData.overlayMat) { m.userData.overlayMat.emissiveIntensity = 0.04; m.userData.overlayMat.needsUpdate = true; }
      } else if (!quizMode) {
        _hideOverlay(m);
      }
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
    var e = 1 - Math.pow(1 - camT, 3);
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
  setCsMode:function(){}, setCsSlider:function(){}, setVascTerritory:function(){},
  toggleLesionMode:function(){}, resetLesions:function(){}, activatePathology:function(){},
  clearPathology:function(){}, showPathway:function(){}, hidePathway:function(){}, setPathway:function(){},
  PATHOLOGY_DEFS:{},
};

var _c = document.getElementById('brain-stage') || document.getElementById('brain-container-3d');
if (_c) mount(_c);
