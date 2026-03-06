/**
 * brain-3d.js — Hybrid Brain Engine (v6)
 *
 * Visual layer  : full_brain_hires.glb  (FreeSurfer fsaverage7 pial, sulcal texture)
 *   Auto-detects whether the GLB is in FreeSurfer RAS (old, center≈origin) or
 *   region-GLB space (new, center≈0.11,0,0.20) and applies the correct matrix.
 *
 * Permanent meshes : brainstem.glb + cerebellum.glb — always visible, tissue colour
 *   (pial surface does not include these structures)
 *
 * Interaction overlays : 17 cortical + subcortical region GLBs
 *   loaded SEQUENTIALLY with visible=false → zero ongoing GPU cost
 *
 * Glass isolation: glass ON + region selected → hires+permanents at 10% opacity,
 *   selected region overlay fully opaque (dissection view)
 *
 * Coordinate system (region GLB space, matches generate_brain_meshes.py):
 *   x = −x_FS  (left-hemi lateral at +x), y = z_FS (superior=up), z = y_FS (anterior)
 *   scale 1/75, COORD_OFFSET [0.118,−0.204,0.438], midline x = 0.118
 *
 * If full_brain_hires.glb is the OLD version (FreeSurfer RAS, centred at origin),
 * a runtime matrix brings it into region-GLB space automatically.
 */

import * as THREE        from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }    from 'three/addons/loaders/GLTFLoader.js';

console.log('[brain-3d] v6 loaded, Three.js r' + THREE.REVISION);

const MIDLINE_X = 0.118;

// ── Overlay colours ────────────────────────────────────────────────────────────
const OVERLAY_COLORS = {
  frontal_lobe:0xE8805A, prefrontal_cortex:0xD4724E, brocas_area:0xE86060,
  motor_cortex:0xD08040, medial_frontal:0xCC7050,
  parietal_lobe:0x7EB8C8, somatosensory_cortex:0x60A8C0,
  temporal_lobe:0x80C870, wernickes_area:0x60B850,
  occipital_lobe:0xC080D0, cingulate_gyrus:0xD0A030,
  thalamus:0xE09060, hippocampus:0xE07050, amygdala:0xD86060,
  caudate:0xD08860, putamen:0xC07850, globus_pallidus:0xB87060,
  brainstem:0x9090C0, cerebellum:0x80C0A0,
};
const TISSUE_COLOR = 0xD4A888;
const PERMANENT_SUBCORTICAL = new Set(['brainstem', 'cerebellum']);

// ── Renderer ───────────────────────────────────────────────────────────────────
var renderer, canvas;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true });
  // Cap at 1.5× — on retina screens 2× doubles pixel count for little visual gain
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
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

// ── Scene / Camera / Controls ──────────────────────────────────────────────────
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

// ── Lighting ───────────────────────────────────────────────────────────────────
scene.add(Object.assign(new THREE.DirectionalLight(0xFFF5EE, 2.8), {position: {set(x,y,z){this.x=x;this.y=y;this.z=z;return this;}}}).position.set(5,7,4) && new THREE.DirectionalLight(0xFFF5EE,2.8));
// (cleaner version below)
(function() {
  var k = new THREE.DirectionalLight(0xFFF5EE, 2.8); k.position.set(5, 7, 4); scene.add(k);
  var f = new THREE.DirectionalLight(0xD0E0FF, 0.6); f.position.set(-4,2,-2); scene.add(f);
  var r = new THREE.DirectionalLight(0xFFE8C0, 1.0); r.position.set(0,-5,-4); scene.add(r);
  scene.add(new THREE.HemisphereLight(0xC8D8F0, 0x401808, 0.45));
  scene.add(new THREE.AmbientLight(0xFFEEE8, 0.12));
})();

// ── Mesh registries ────────────────────────────────────────────────────────────
const brainGroup      = new THREE.Group();
scene.add(brainGroup);

const hiresMeshes     = [];
const permanentMeshes = [];
var   hiresGlassOn    = false;
var   splitOn         = false;

const regionMeshes      = [];
const corticalMeshes    = [];
const subcorticalMeshes = [];
var   selectedRegionId  = null;
var   hoveredRegionId   = null;
var   quizMode          = false;

const loader = new GLTFLoader();

// ── Transform: FreeSurfer RAS (normalised, centred at origin) → region GLB space
// Applied at runtime when the loaded hires GLB is detected to be in old FS RAS coords.
// Derivation: v_region = [-v_h, z_h, y_h] * S + offset
//   where S = 1/(75 * scale_hires), scale_hires = 2/max_span_mm ≈ 2/165 ≈ 0.01212, S ≈ 1.10
const S_FS = 1.10;
const FS_TO_REGION = (function() {
  var m = new THREE.Matrix4();
  m.set(-S_FS, 0, 0, MIDLINE_X,
         0, 0, S_FS, -0.204,
         0, S_FS, 0,  0.438,
         0, 0,   0,   1);
  return m;
}());

// ── Hires brain loader ─────────────────────────────────────────────────────────
function loadHiresBrain() {
  return new Promise(function(resolve) {
    // ?v=6 busts any browser cache of a previous version
    loader.load('data/brain_meshes/full_brain_hires.glb?v=6',
      function(gltf) {
        var sc = gltf.scene;

        // Detect coordinate space from bounding-box centre:
        //   Old GLB (FreeSurfer RAS, centred at origin) → center.length() < 0.15
        //   New GLB (region coords)                    → center.length() ≈ 0.23
        var box    = new THREE.Box3().setFromObject(sc);
        var center = box.getCenter(new THREE.Vector3());
        var isOldCoords = center.length() < 0.15;
        console.log('[brain-3d] Hires bounds:', box.min.toArray().map(function(v){return v.toFixed(2);}),
                    '→', box.max.toArray().map(function(v){return v.toFixed(2);}),
                    'centre len:', center.length().toFixed(3),
                    isOldCoords ? '(OLD FS-RAS → applying transform)' : '(region coords OK)');

        sc.traverse(function(child) {
          if (!child.isMesh) return;
          if (isOldCoords) child.geometry.applyMatrix4(FS_TO_REGION);
          child.geometry.computeVertexNormals();
          if (child.material) {
            child.material.roughness   = 0.82;
            child.material.metalness   = 0.00;
            child.material.needsUpdate = true;
          }
          child.castShadow = child.receiveShadow = false;
          hiresMeshes.push(child);
        });

        brainGroup.add(sc);
        console.log('[brain-3d] Hires brain ready — ' + hiresMeshes.length + ' mesh(es)');
        resolve();
      },
      function(xhr) {
        if (xhr.total > 0)
          console.log('[brain-3d] Hires: ' + Math.round(xhr.loaded/xhr.total*100) + '%');
      },
      function(err) {
        console.error('[brain-3d] Hires load FAILED:', err);
        resolve(); // non-fatal
      }
    );
  });
}

// Apply / restore glass state on all visual meshes (hires + permanents)
function _applyHiresState() {
  var all = hiresMeshes.concat(permanentMeshes);
  all.forEach(function(m) {
    if (!m.material) return;
    if (hiresGlassOn) {
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
  var all = hiresMeshes.concat(permanentMeshes);
  all.forEach(function(m) {
    if (!m.material) return;
    if (on && !hiresGlassOn) {
      m.material.transparent = true;
      m.material.opacity     = 0.45;
      m.material.depthWrite  = false;
    } else if (!on && !hiresGlassOn) {
      m.material.transparent = false;
      m.material.opacity     = 1.0;
      m.material.depthWrite  = true;
    }
    m.material.needsUpdate = true;
  });
}

// ── Region overlay / permanent mesh loader ─────────────────────────────────────
function loadRegion(regionId, entry, permanent) {
  return new Promise(function(resolve) {
    loader.load(entry.file,
      function(gltf) {
        var col = new THREE.Color(permanent ? TISSUE_COLOR : (OVERLAY_COLORS[regionId] || 0x8888AA));
        var mat = new THREE.MeshStandardMaterial({
          color:             col,
          roughness:         permanent ? 0.78 : 0.55,
          metalness:         0,
          emissive:          col,
          emissiveIntensity: permanent ? 0.06 : 0.20,
          transparent:       !permanent,
          opacity:           1.0,
          side:              THREE.FrontSide,
        });
        mat._origColor = col.clone();

        gltf.scene.traverse(function(child) {
          if (!child.isMesh) return;
          child.geometry.computeVertexNormals();
          child.material = mat;
          child.name = regionId;
          child.castShadow = child.receiveShadow = false;
          child.visible = !!permanent;
          child.userData = { regionId:regionId, label:regionId, type:entry.type,
                             permanent:!!permanent, overlayMat:mat };

          // Gold selection outline (hidden until selected)
          var selMat = new THREE.MeshBasicMaterial({
            color:0xFFD060, side:THREE.BackSide, transparent:true, opacity:0, depthWrite:false
          });
          var selOutline = new THREE.Mesh(child.geometry, selMat);
          selOutline.scale.setScalar(1.045);
          selOutline.renderOrder = 3;
          selOutline.visible = false;
          selOutline.userData = {isOutline:true};
          child.userData.selOutline = selOutline;
          child.add(selOutline);

          regionMeshes.push(child);
          if (entry.type === 'subcortical') subcorticalMeshes.push(child);
          else                              corticalMeshes.push(child);
          if (permanent) permanentMeshes.push(child);
        });
        brainGroup.add(gltf.scene);
        resolve();
      },
      undefined,
      function(err) { console.warn('[brain-3d] Region failed ('+regionId+'):', err); resolve(); }
    );
  });
}

// ── Load orchestration ─────────────────────────────────────────────────────────
var _readyResolve = null;
var _readyPromise = new Promise(function(res) { _readyResolve = res; });

async function loadBrain() {
  console.log('[brain-3d] loadBrain() start');
  window.dispatchEvent(new CustomEvent('brain3dProgress', {detail:{loaded:0,total:20}}));

  // 1. Manifest + hires brain in parallel (hires is the heavy one)
  var manifest = null;
  try {
    var results = await Promise.allSettled([
      fetch('data/brain_regions_manifest.json').then(function(r){return r.json();}),
      loadHiresBrain()
    ]);
    if (results[0].status === 'fulfilled') manifest = results[0].value;
  } catch(e) { console.warn('[brain-3d] init error:', e); }

  // Signal "hires brain ready" so loading overlay clears
  window.dispatchEvent(new CustomEvent('brain3dProgress', {detail:{loaded:10,total:20}}));
  window.dispatchEvent(new CustomEvent('brain3dReady',    {detail:{regionCount:0}}));

  if (!manifest) { _readyResolve(); return; }

  // 2. Load region overlays SEQUENTIALLY to avoid main-thread spikes
  //    (each GLB is tiny < 100 KB; total time is still < 2 s on localhost)
  var regionIds = Object.keys(manifest).filter(function(id){
    return manifest[id].type !== 'glass';
  });
  var loaded = 10, total = 10 + regionIds.length;

  for (var i = 0; i < regionIds.length; i++) {
    var id = regionIds[i];
    await loadRegion(id, manifest[id], PERMANENT_SUBCORTICAL.has(id));
    loaded++;
    window.dispatchEvent(new CustomEvent('brain3dProgress',
      {detail:{loaded:loaded, total:total}}));
  }

  console.log('[brain-3d] All done — ' + regionMeshes.length + ' regions, '
              + permanentMeshes.length + ' permanent');
  _readyResolve();
}

loadBrain();

// ── Camera presets ─────────────────────────────────────────────────────────────
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
  var tgt = CAMERA_VIEWS[name]; if (!tgt) return;
  camFrom = camera.position.clone(); camTo = tgt.clone(); camT = 0;
  controls.target.copy(CAM_TARGET);
}

// ── Overlay helpers ────────────────────────────────────────────────────────────
function _showOverlay(m, selOpacity) {
  m.visible = true;
  var sel = m.userData.selOutline;
  if (sel) { sel.visible = selOpacity > 0; if (sel.material) { sel.material.opacity = selOpacity; sel.material.needsUpdate = true; } }
}
function _hideOverlay(m) {
  if (m.userData.permanent) return; // never hide permanent meshes
  m.visible = false;
  var sel = m.userData.selOutline; if (sel) sel.visible = false;
}
function _hideAllOverlays() { regionMeshes.forEach(_hideOverlay); }

function _restorePermanent() {
  permanentMeshes.forEach(function(m) {
    var mat = m.userData.overlayMat; if (!mat) return;
    mat.color.copy(mat._origColor);
    mat.emissive.copy(mat._origColor);
    mat.emissiveIntensity = 0.06;
    mat.transparent = false; mat.opacity = 1.0;
    mat.needsUpdate = true; m.visible = true;
  });
}

// ── Public region API ──────────────────────────────────────────────────────────
function highlightRegion(regionId) {
  selectedRegionId = regionId;
  _hideAllOverlays();
  regionMeshes.forEach(function(m) {
    if (m.userData.regionId !== regionId) return;
    var mat = m.userData.overlayMat;
    if (mat) {
      var col = new THREE.Color(OVERLAY_COLORS[regionId] || 0x8888AA);
      mat.color.copy(col); mat.emissive.copy(col);
      mat.emissiveIntensity = hiresGlassOn ? 0.38 : 0.24;
      mat.transparent = !hiresGlassOn; mat.opacity = hiresGlassOn ? 1.0 : 0.85;
      mat.needsUpdate = true;
    }
    _showOverlay(m, 0);
  });
  if (hiresGlassOn) _applyHiresState();
}

function dimAllRegions(exceptIds) {
  quizMode = true; exceptIds = exceptIds || [];
  selectedRegionId = null;
  _hideAllOverlays();
  _dimHires(true);
  regionMeshes.forEach(function(m) {
    if (exceptIds.indexOf(m.userData.regionId) === -1) return;
    var mat = m.userData.overlayMat;
    if (mat) {
      var col = new THREE.Color(OVERLAY_COLORS[m.userData.regionId] || 0x8888AA);
      mat.color.copy(col); mat.emissive.copy(col);
      mat.emissiveIntensity = 0.18; mat.transparent = true; mat.opacity = 0.55;
      mat.needsUpdate = true;
    }
    _showOverlay(m, 0);
  });
}

function resetRegions() {
  quizMode = false; selectedRegionId = null;
  _hideAllOverlays();
  _restorePermanent();
  _applyHiresState();
  if (!hiresGlassOn) _dimHires(false);
}

// ── Glass + Split ──────────────────────────────────────────────────────────────
function toggleGlass() {
  hiresGlassOn = !hiresGlassOn;
  _applyHiresState();
  if (!hiresGlassOn) { _hideAllOverlays(); _restorePermanent(); selectedRegionId = null; }
  else if (selectedRegionId) highlightRegion(selectedRegionId);
}
function setSubcorticalVisible(show) {
  subcorticalMeshes.forEach(function(m) {
    if (m.userData.permanent) m.visible = !!show;
    else if (!show) _hideOverlay(m);
  });
}
function toggleSplit() {
  splitOn = !splitOn;
  renderer.clippingPlanes = splitOn
    ? [new THREE.Plane(new THREE.Vector3(1,0,0), -MIDLINE_X)]
    : [];
}

// ── Raycasting ─────────────────────────────────────────────────────────────────
var raycaster = new THREE.Raycaster();
var mouse     = new THREE.Vector2(-10,-10);
var downPos   = null;

function _showTooltip(id) {
  var tip=document.getElementById('hover-tip'), nm=document.getElementById('hover-tip-name');
  if (!tip||!nm) return;
  if (id) { nm.textContent=id.replace(/_/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase();}); tip.style.opacity='1'; }
  else    { tip.style.opacity='0'; }
}
function _rayHit() {
  raycaster.setFromCamera(mouse, camera);
  var vis = regionMeshes.filter(function(m){return m.visible;});
  var hits = raycaster.intersectObjects(vis, false);
  return hits.length ? hits[0].object : null;
}

canvas.addEventListener('pointermove', function(e) {
  var r=canvas.getBoundingClientRect();
  mouse.x= ((e.clientX-r.left)/r.width) *2-1;
  mouse.y=-((e.clientY-r.top) /r.height)*2+1;
  var hit=_rayHit(), id=hit?hit.userData.regionId:null;
  if (id !== hoveredRegionId) {
    if (hoveredRegionId && hoveredRegionId!==selectedRegionId && !quizMode) {
      regionMeshes.forEach(function(m){
        if (m.userData.regionId!==hoveredRegionId) return;
        if (m.userData.permanent) { if(m.userData.overlayMat){m.userData.overlayMat.emissiveIntensity=0.06;m.userData.overlayMat.needsUpdate=true;} }
        else _hideOverlay(m);
      });
    }
    hoveredRegionId=id; canvas.style.cursor=id?'pointer':'grab'; _showTooltip(id);
    if (id && id!==selectedRegionId) {
      regionMeshes.forEach(function(m){
        if (m.userData.regionId!==id) return;
        if (m.userData.permanent) { if(m.userData.overlayMat){m.userData.overlayMat.emissiveIntensity=0.32;m.userData.overlayMat.needsUpdate=true;} }
        else if (!quizMode) {
          var col=new THREE.Color(OVERLAY_COLORS[id]||0x8888AA);
          var mat=m.userData.overlayMat;
          if(mat){mat.color.copy(col);mat.emissive.copy(col);mat.emissiveIntensity=0.22;mat.transparent=true;mat.opacity=0.32;mat.needsUpdate=true;}
          _showOverlay(m,0);
        }
      });
    }
    regionMeshes.forEach(function(m){
      if(m.userData.overlayMat)
        m.userData.overlayMat.emissiveIntensity=(m.userData.regionId===id)?0.35:(m.userData.permanent?0.06:0.20);
    });
  }
});

canvas.addEventListener('pointerdown', function(e) {
  canvas.style.cursor='grabbing'; downPos={x:e.clientX,y:e.clientY};
});
canvas.addEventListener('pointerup', function(e) {
  canvas.style.cursor=hoveredRegionId?'pointer':'grab';
  if (!downPos) return;
  var dx=e.clientX-downPos.x, dy=e.clientY-downPos.y;
  if (Math.sqrt(dx*dx+dy*dy)<5) {
    var r=canvas.getBoundingClientRect();
    mouse.x= ((e.clientX-r.left)/r.width) *2-1;
    mouse.y=-((e.clientY-r.top) /r.height)*2+1;
    var hit=_rayHit();
    if (hit) {
      var rid=hit.userData.regionId;
      if (window.__brainUI&&window.__brainUI.openRegion) window.__brainUI.openRegion(rid);
      if (!quizMode) highlightRegion(rid);
    }
  }
  downPos=null;
});
canvas.addEventListener('pointerleave', function() {
  mouse.set(-10,-10);
  if (hoveredRegionId&&hoveredRegionId!==selectedRegionId&&!quizMode) {
    regionMeshes.forEach(function(m){
      if(m.userData.regionId!==hoveredRegionId) return;
      if(m.userData.permanent){if(m.userData.overlayMat){m.userData.overlayMat.emissiveIntensity=0.06;m.userData.overlayMat.needsUpdate=true;}}
      else _hideOverlay(m);
    });
  }
  hoveredRegionId=null; _showTooltip(null);
});

// ── Animation loop ─────────────────────────────────────────────────────────────
var animId=null, lastTs=0;
function animate(ts) {
  animId=requestAnimationFrame(animate);
  var dt=Math.min((ts-lastTs)/1000,0.05); lastTs=ts;
  if (camTo) {
    camT=Math.min(camT+dt/CAM_DUR,1);
    var e=1-Math.pow(1-camT,3);
    camera.position.lerpVectors(camFrom,camTo,e);
    camera.lookAt(controls.target);
    if(camT>=1){camTo=null;controls.update();}
  } else controls.update();
  renderer.render(scene,camera);
}

// ── Resize / Mount / Unmount ───────────────────────────────────────────────────
var mountedContainer=null;
var resizeObserver=new ResizeObserver(function(){
  if(!mountedContainer) return;
  var w=mountedContainer.clientWidth, h=mountedContainer.clientHeight||Math.round(w/1.54);
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix();
});
function mount(container) {
  if(typeof container==='string') container=document.querySelector(container);
  if(!container) return;
  if(mountedContainer===container){if(!animId)animate(0);return;}
  if(mountedContainer) resizeObserver.unobserve(mountedContainer);
  mountedContainer=container; container.appendChild(canvas); resizeObserver.observe(container);
  var w=container.clientWidth||window.innerWidth-256, h=container.clientHeight||window.innerHeight-52;
  renderer.setSize(w,h); camera.aspect=w/h; camera.updateProjectionMatrix();
  if(!animId) animate(0);
  setCameraView('lateral');
}
function unmount() {
  if(animId){cancelAnimationFrame(animId);animId=null;}
  if(mountedContainer){
    resizeObserver.unobserve(mountedContainer);
    if(canvas.parentNode===mountedContainer) mountedContainer.removeChild(canvas);
    mountedContainer=null;
  }
}

// ── Public API ─────────────────────────────────────────────────────────────────
window.__brain3d = {
  mount, unmount, setCameraView, CAMERA_VIEWS,
  highlightRegion, dimAllRegions, resetRegions,
  regionMeshes, corticalMeshes, subcorticalMeshes,
  toggleGlass, toggleSplit, setSubcorticalVisible,
  ready:_readyPromise,
  setCsMode:function(){}, setCsSlider:function(){}, setVascTerritory:function(){},
  toggleLesionMode:function(){}, resetLesions:function(){}, activatePathology:function(){},
  clearPathology:function(){}, showPathway:function(){}, hidePathway:function(){}, setPathway:function(){},
  PATHOLOGY_DEFS:{},
};

var _c=document.getElementById('brain-stage')||document.getElementById('brain-container-3d');
if(_c) mount(_c);
