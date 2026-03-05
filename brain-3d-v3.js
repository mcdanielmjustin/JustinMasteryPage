/**
 * brain-3d-v3.js — Brain Pathology 3.0 Engine
 *
 * Built from scratch for BrainFacts.org-quality interactivity.
 *
 * Architecture:
 *   1. Full-brain hires cortex (pial surface GLB) as visual base
 *   2. Per-region overlay GLBs — hidden by default, zero GPU cost
 *   3. Permanent subcortical meshes (brainstem, cerebellum) — always rendered
 *   4. MeshPhysicalMaterial for the cortex (clearcoat, sheen, wet-tissue look)
 *   5. Full raycaster: hover glow, click select, glass isolation
 *
 * Toggles:
 *   - Glass Brain: cortex + permanents → 8% opacity; selected region → 100% opaque
 *   - Split Brain: clip plane at midline, DoubleSide fill, hide subcortical
 *   - Cerebellum: independent show/hide for the cerebellum mesh
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
import { DRACOLoader }   from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer }   from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }        from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass }          from 'three/addons/postprocessing/GTAOPass.js';
import { UnrealBloomPass }   from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass }        from 'three/addons/postprocessing/OutputPass.js';

console.log('[brain-3d-v3] Engine loaded, Three.js r' + THREE.REVISION);


// ═══════════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════════

var ASSET_VERSION = '20260304q';
var MIDLINE_X = 0.118;

var OVERLAY_COLORS = {
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
  insula:               0xB8A040,
  thalamus:             0xE09060,
  hippocampus:          0xE07050,
  amygdala:             0xD86060,
  caudate:              0xD08860,
  putamen:              0xC07850,
  globus_pallidus:      0xB87060,
  nucleus_accumbens:    0xC0A070,
  brainstem:            0x9090C0,
  cerebellum:           0x80C0A0,
  // New structures
  pons:                 0x8888B8,
  medulla:              0x7878A8,
  midbrain:             0x9898C8,
  hypothalamus:         0xD8A060,
  corpus_callosum:      0xE0D0B0,
  pituitary:            0xC8A880,
  olfactory_bulb:       0xA0D090,
  substantia_nigra:     0x808080,
  vta:                  0x90A0B0,
};

var TISSUE_COLOR = 0xD4AA90;

var PERMANENT_IDS = new Set(['brainstem', 'cerebellum']);

// Regions where the cerebellum partially occludes the selected structure in
// the default lateral camera view — auto-glass the cerebellum while selected.
// Brainstem segments viewed from anterior-lateral still benefit from a transparent
// cerebellum since it wraps the posterior brainstem.
var CEREBELLUM_GLASS_REGIONS = new Set([
  'temporal_lobe', 'occipital_lobe',
  'brainstem', 'midbrain', 'pons', 'medulla',
]);

// Regions that exist on both hemispheres and should show a mirrored right-side overlay.
// Language-dominant regions (Broca's, Wernicke's) and midline structures (cingulate, corpus
// callosum, medial_frontal) are intentionally excluded.
var BILATERAL_REGIONS = new Set([
  'frontal_lobe', 'prefrontal_cortex', 'motor_cortex',
  'parietal_lobe', 'somatosensory_cortex', 'temporal_lobe', 'occipital_lobe',
  'insula',
  'thalamus', 'hippocampus', 'amygdala', 'caudate', 'putamen', 'globus_pallidus',
  'nucleus_accumbens', 'hypothalamus', 'substantia_nigra',
  'vta', 'olfactory_bulb',
]);


// ═══════════════════════════════════════════════════════════════════════════════
// RENDERER
// ═══════════════════════════════════════════════════════════════════════════════

var renderer, canvas;

try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  canvas = renderer.domElement;
  canvas.style.cssText = 'display:block; border-radius:16px; cursor:grab;';
} catch (e) {
  console.error('[brain-3d-v3] WebGL unavailable:', e.message);
  window.dispatchEvent(new CustomEvent('brain3dNoWebGL'));
  window.__brain3d = {
    mount: function(){}, unmount: function(){}, setCameraView: function(){},
    highlightRegion: function(){}, enterQuizMode: function(){}, exitQuizCamera: function(){}, dimAllRegions: function(){}, resetRegions: function(){},
    toggleGlass: function(){}, toggleSplit: function(){}, toggleCerebellum: function(){}, toggleBrainstem: function(){},
    setSubcorticalVisible: function(){}, focusRegion: function(){},
    regionMeshes: [], corticalMeshes: [], subcorticalMeshes: [],
    ready: Promise.resolve(), CAMERA_VIEWS: {},
  };
  throw e;
}


// ═══════════════════════════════════════════════════════════════════════════════
// SCENE
// ═══════════════════════════════════════════════════════════════════════════════

var scene = new THREE.Scene();
scene.background = new THREE.Color(0x0A0D14);

var brainGroup = new THREE.Group();
scene.add(brainGroup);

// ── Procedural studio environment map for MeshPhysicalMaterial reflections ──
// 5-element setup: sky dome, key area, fill area, rim area, ground plane, accent sphere
var _envMap = null;
(function() {
  var pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileCubemapShader();
  var envScene = new THREE.Scene();

  // Sky dome — warm neutral upper hemisphere
  var skyGeo = new THREE.SphereGeometry(10, 32, 16);
  var skyMat = new THREE.MeshBasicMaterial({ color: 0x404550, side: THREE.BackSide });
  envScene.add(new THREE.Mesh(skyGeo, skyMat));

  // Key area — warm overhead (large, dominant)
  var keyArea = new THREE.Mesh(
    new THREE.PlaneGeometry(6, 6),
    new THREE.MeshBasicMaterial({ color: 0x806858 })
  );
  keyArea.position.set(0, 8, 0);
  keyArea.rotation.x = Math.PI / 2;
  envScene.add(keyArea);

  // Fill area — cool blue from left
  var fillArea = new THREE.Mesh(
    new THREE.PlaneGeometry(4, 4),
    new THREE.MeshBasicMaterial({ color: 0x506070 })
  );
  fillArea.position.set(-6, 2, 3);
  fillArea.lookAt(0, 0, 0);
  envScene.add(fillArea);

  // Rim area — warm backlight from below-behind
  var rimArea = new THREE.Mesh(
    new THREE.PlaneGeometry(5, 3),
    new THREE.MeshBasicMaterial({ color: 0x604838 })
  );
  rimArea.position.set(0, -4, -6);
  rimArea.lookAt(0, 0, 0);
  envScene.add(rimArea);

  // Ground plane — dark warm floor for grounded reflections
  var groundPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(20, 20),
    new THREE.MeshBasicMaterial({ color: 0x201510 })
  );
  groundPlane.position.set(0, -9, 0);
  groundPlane.rotation.x = -Math.PI / 2;
  envScene.add(groundPlane);

  // Accent sphere — small bright specular catch (simulates point highlight)
  var accentSphere = new THREE.Mesh(
    new THREE.SphereGeometry(0.5, 8, 8),
    new THREE.MeshBasicMaterial({ color: 0xFFEEDD })
  );
  accentSphere.position.set(5, 6, 4);
  envScene.add(accentSphere);

  _envMap = pmrem.fromScene(envScene, 0.04).texture;
  _envMap.colorSpace = THREE.SRGBColorSpace;
  scene.environment = _envMap;
  pmrem.dispose();
})();


// ═══════════════════════════════════════════════════════════════════════════════
// CAMERA
// ═══════════════════════════════════════════════════════════════════════════════

var camera = new THREE.PerspectiveCamera(40, 1.54, 0.1, 100);
camera.position.set(4.8, 0.5, 0.4);

var CAM_ORIGIN = new THREE.Vector3(0.55, 0.05, 0.10);

var controls = new OrbitControls(camera, canvas);
controls.enableDamping  = true;
controls.dampingFactor  = 0.07;
controls.minDistance     = 1.8;
controls.maxDistance     = 10.0;
controls.enablePan       = false;
controls.target.copy(CAM_ORIGIN);
controls.update();


// ═══════════════════════════════════════════════════════════════════════════════
// LIGHTING — 5-point professional setup
// ═══════════════════════════════════════════════════════════════════════════════

// Key light — warm directional from upper-right-front (with shadow map)
var keyLight = new THREE.DirectionalLight(0xFFF8F4, 2.0);
keyLight.position.set(5, 7, 4);
keyLight.castShadow = true;
keyLight.shadow.mapSize.width  = 1024;
keyLight.shadow.mapSize.height = 1024;
keyLight.shadow.bias = -0.0003;
keyLight.shadow.camera.near = 0.5;
keyLight.shadow.camera.far  = 25;
keyLight.shadow.camera.left   = -3;
keyLight.shadow.camera.right  =  3;
keyLight.shadow.camera.top    =  3;
keyLight.shadow.camera.bottom = -3;
scene.add(keyLight);

// Fill light — cool blue from left to soften shadows
var fillLight = new THREE.DirectionalLight(0xD0E0FF, 0.55);
fillLight.position.set(-4, 2, -2);
scene.add(fillLight);

// Rim light — warm backlight for edge separation
var rimLight = new THREE.DirectionalLight(0xFFEEDD, 0.5);
rimLight.position.set(0, -5, -4);
scene.add(rimLight);

// Hemisphere light — subtle sky/ground ambient
scene.add(new THREE.HemisphereLight(0xD0D8E8, 0x2A1008, 0.4));

// Ambient — very subtle base fill
scene.add(new THREE.AmbientLight(0xFFEFEF, 0.12));


// ═══════════════════════════════════════════════════════════════════════════════
// POST-PROCESSING PIPELINE
// ═══════════════════════════════════════════════════════════════════════════════

var composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

// Screen-space ambient occlusion — darkens sulci naturally
var gtaoPass = new GTAOPass(scene, camera, window.innerWidth, window.innerHeight);
gtaoPass.output = GTAOPass.OUTPUT.Default;
gtaoPass.updateGtaoMaterial({ radius: 0.3, distanceExponent: 2, thickness: 2, samples: 16 });
gtaoPass.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3 });
composer.addPass(gtaoPass);

// Subtle bloom — wet-highlight glow on specular catches
var bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  0.15,   // strength
  0.4,    // radius
  0.85    // threshold
);
composer.addPass(bloomPass);

// Output pass — applies tone mapping + color space conversion
composer.addPass(new OutputPass());


// ═══════════════════════════════════════════════════════════════════════════════
// MESH REGISTRIES
// ═══════════════════════════════════════════════════════════════════════════════

var hiresMeshes       = [];  // full_brain_hires.glb child meshes
var permanentMeshes   = [];  // brainstem + cerebellum — always visible
var cerebellumMeshes  = [];  // cerebellum specifically (for independent toggle)
var brainstemMeshes   = [];  // brainstem specifically

var regionMeshes      = [];  // all overlay region meshes (flat)
var corticalMeshes    = [];  // cortical overlays only
var subcorticalMeshes = [];  // subcortical overlays only

var regionCentroids   = {};  // regionId → Vector3 centroid
var regionCameraPos   = {};  // regionId → Vector3 camera position

var selectedRegionId  = null;
var hoveredRegionId   = null;
var glassOn           = false;
var _autoGlassActive  = false;  // true when glass was auto-enabled for a buried region
var splitOn           = false;
var _autoSplitActive  = false;  // true when split was auto-enabled for a medial region
var cerebellumVisible = true;
var brainstemVisible  = true;
var quizMode          = false;

var dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('./node_modules/three/examples/jsm/libs/draco/gltf/');
var loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);


// ═══════════════════════════════════════════════════════════════════════════════
// HIRES CORTEX LOADER — MeshPhysicalMaterial
// ═══════════════════════════════════════════════════════════════════════════════

function loadHiresBrain() {
  return new Promise(function(resolve) {
    // Draco-compressed hires cortex (655k faces, ~2.6MB) — best quality, smallest download
    var cortexPath = 'data/brain_meshes/full_brain_draco.glb?v=' + ASSET_VERSION;

    // Pre-load normal map + AO map textures in parallel with GLB
    var texLoader = new THREE.TextureLoader();
    var normalMapTex = null;
    var aoMapTex = null;

    texLoader.load('data/brain_meshes/cortex_normal_map.png', function(tex) {
      tex.colorSpace = THREE.LinearSRGBColorSpace;  // normal maps use linear
      normalMapTex = tex;
      console.log('[brain-3d-v3] Normal map loaded:', tex.image.width + 'x' + tex.image.height);
      // If GLB already loaded (race condition), apply normal map retroactively
      hiresMeshes.forEach(function(m) {
        if (m.material && m.material._isHiresMat && !m.material.normalMap) {
          m.material.normalMap = normalMapTex;
          m.material.normalScale = new THREE.Vector2(1.2, 1.2);
          m.material.needsUpdate = true;
          console.log('[brain-3d-v3] Normal map applied retroactively');
        }
      });
    }, undefined, function(err) {
      console.warn('[brain-3d-v3] Normal map failed to load:', err);
    });

    texLoader.load('data/brain_meshes/cortex_ao_map.png', function(tex) {
      tex.colorSpace = THREE.LinearSRGBColorSpace;  // AO is linear data
      tex.channel = 0;  // reuse UV0 (avoids needing UV2)
      aoMapTex = tex;
      console.log('[brain-3d-v3] AO map loaded:', tex.image.width + 'x' + tex.image.height);
      // If GLB already loaded, apply AO retroactively
      hiresMeshes.forEach(function(m) {
        if (m.material && m.material._isHiresMat && !m.material.aoMap) {
          m.material.aoMap = aoMapTex;
          m.material.aoMapIntensity = 0.7;
          m.material.needsUpdate = true;
          console.log('[brain-3d-v3] AO map applied retroactively');
        }
      });
    }, undefined, function(err) {
      console.warn('[brain-3d-v3] AO map failed to load:', err);
    });

    _progress(5, 'Loading cortex\u2026');

    loader.load(cortexPath,
      function(gltf) {
        _progress(68, 'Parsing cortex\u2026');
        gltf.scene.traverse(function(child) {
          if (!child.isMesh) return;
          child.geometry.computeVertexNormals();

          // Upgrade to MeshPhysicalMaterial with normal map + AO-baked texture
          var oldMap = child.material ? child.material.map : null;
          if (oldMap) {
            oldMap.colorSpace = THREE.SRGBColorSpace;
          }
          var physMat = new THREE.MeshPhysicalMaterial({
            color:              new THREE.Color(0xFFEEE4),  // original near-white
            map:                oldMap,
            emissive:           new THREE.Color(0x6B3A2A),  // original warm fill
            emissiveIntensity:  0.20,
            normalMap:          normalMapTex,
            normalScale:        new THREE.Vector2(1.2, 1.2),
            aoMap:              aoMapTex,
            aoMapIntensity:     0.7,
            envMap:             _envMap,
            envMapIntensity:    0.12,
            roughness:          0.75,
            metalness:          0.0,
            clearcoat:          0.08,
            clearcoatRoughness: 0.60,
            sheen:              0.05,
            sheenRoughness:     0.70,
            sheenColor:         new THREE.Color(0xDDBBAA),
            iridescence:        0.04,
            // Subsurface scattering (translucency)
            transmission:       0.08,
            thickness:          0.5,
            ior:                1.4,
            attenuationColor:   new THREE.Color(0xE09070),
            attenuationDistance: 0.5,
            side:               THREE.FrontSide,
          });
          physMat._isHiresMat = true;
          child.material = physMat;

          child.castShadow = true;
          child.receiveShadow = true;
          hiresMeshes.push(child);
        });
        brainGroup.add(gltf.scene);
        _progress(72, 'Applying textures\u2026');
        console.log('[brain-3d-v3] Draco hires cortex loaded (' + hiresMeshes.length + ' mesh, 655k faces)');
        resolve();
      },
      function(event) {
        // Real byte-level download progress (5–65%)
        if (event.total > 0) {
          var mb = (event.loaded / 1048576).toFixed(1);
          var tot = (event.total / 1048576).toFixed(1);
          var pct = 5 + Math.round((event.loaded / event.total) * 60);
          _progress(pct, 'Loading cortex\u2026 ' + mb + '\u202fMB\u202f/\u202f' + tot + '\u202fMB');
        }
      },
      function(err) {
        // Fall back to uncompressed optimized, then raw hires
        console.warn('[brain-3d-v3] Draco cortex not found, trying optimized fallback...');
        loader.load('data/brain_meshes/full_brain_optimized.glb?v=' + ASSET_VERSION,
          function(gltf) {
            gltf.scene.traverse(function(child) {
              if (!child.isMesh) return;
              child.geometry.computeVertexNormals();
              var oldMap = child.material ? child.material.map : null;
              var physMat = new THREE.MeshPhysicalMaterial({
                color: new THREE.Color(0xFFEEE4),
                map: oldMap, emissive: new THREE.Color(0x6B3A2A),
                emissiveIntensity: 0.20, envMap: _envMap, envMapIntensity: 0.12,
                roughness: 0.75, metalness: 0.0, clearcoat: 0.08,
                clearcoatRoughness: 0.60, sheen: 0.05, sheenRoughness: 0.70,
                sheenColor: new THREE.Color(0xDDBBAA), iridescence: 0.04,
                transmission: 0.08, thickness: 0.5, ior: 1.4,
                attenuationColor: new THREE.Color(0xE09070), attenuationDistance: 0.5,
                side: THREE.FrontSide,
              });
              physMat._isHiresMat = true;
              child.material = physMat;
              child.castShadow = true;
              child.receiveShadow = true;
              hiresMeshes.push(child);
            });
            brainGroup.add(gltf.scene);
            console.log('[brain-3d-v3] Hires cortex loaded (fallback)');
            resolve();
          },
          undefined,
          function(err2) {
            console.warn('[brain-3d-v3] Cortex load failed:', err2);
            resolve();
          }
        );
      }
    );
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// ANATOMICAL BRAINSTEM + CEREBELLUM  (JSON mesh + procedural texture PNG)
// ═══════════════════════════════════════════════════════════════════════════════

function _loadAtlasMesh(regionId, jsonUrl, textureUrl) {
  /**
   * Load an atlas-derived mesh from JSON (positions, indices, normals, uvs)
   * and apply a procedural texture PNG. Returns a Promise that resolves
   * when the mesh is added to the scene.
   */
  return new Promise(function(resolve) {
    fetch(jsonUrl)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var geo = new THREE.BufferGeometry();
        geo.setAttribute('position',
          new THREE.Float32BufferAttribute(new Float32Array(data.positions), 3));
        geo.setAttribute('normal',
          new THREE.Float32BufferAttribute(new Float32Array(data.normals), 3));
        geo.setAttribute('uv',
          new THREE.Float32BufferAttribute(new Float32Array(data.uvs), 2));
        geo.setIndex(new THREE.Uint32BufferAttribute(new Uint32Array(data.indices), 1));

        // Load the procedural texture
        var texLoader = new THREE.TextureLoader();
        texLoader.load(textureUrl, function(tex) {
          tex.colorSpace = THREE.SRGBColorSpace;
          tex.wrapS = THREE.ClampToEdgeWrapping;
          tex.wrapT = THREE.ClampToEdgeWrapping;
          tex.minFilter = THREE.LinearMipmapLinearFilter;
          tex.magFilter = THREE.LinearFilter;

          var baseColor = new THREE.Color(TISSUE_COLOR);
          var mat = new THREE.MeshPhysicalMaterial({
            map:                tex,
            color:              baseColor,
            emissive:           new THREE.Color(0x000000),
            emissiveIntensity:  0.04,
            envMap:             _envMap,
            envMapIntensity:    0.08,
            roughness:          0.68,
            metalness:          0.0,
            clearcoat:          0.10,
            clearcoatRoughness: 0.38,
            sheen:              0.09,
            sheenRoughness:     0.52,
            sheenColor:         new THREE.Color(0xFFBBAA),
            transparent:        false,
            opacity:            1.0,
            side:               THREE.DoubleSide,
            depthWrite:         true,
          });
          mat._origColor     = baseColor.clone();
          mat._origEmissive  = new THREE.Color(0x000000);
          mat._origRoughness = mat.roughness;

          var mesh = new THREE.Mesh(geo, mat);
          mesh.name = regionId;
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          mesh.visible = true;

          // Gold selection outline
          var selMat = new THREE.MeshBasicMaterial({
            color: 0xFFD060, side: THREE.BackSide,
            transparent: true, opacity: 0.0, depthWrite: false,
          });
          var selOutline = new THREE.Mesh(geo, selMat);
          selOutline.scale.setScalar(1.04);
          selOutline.renderOrder = 3;
          selOutline.visible = false;
          selOutline.userData = { isOutline: true };
          mesh.userData = {
            regionId: regionId, label: regionId, type: 'subcortical',
            permanent: true, overlayMat: mat, selOutline: selOutline,
          };
          mesh.add(selOutline);

          // Register in all arrays
          permanentMeshes.push(mesh);
          regionMeshes.push(mesh);
          subcorticalMeshes.push(mesh);
          if (regionId === 'cerebellum') cerebellumMeshes.push(mesh);
          if (regionId === 'brainstem')  brainstemMeshes.push(mesh);

          brainGroup.add(mesh);

          // Compute centroid for camera focus
          var box = new THREE.Box3().setFromObject(mesh);
          var center = new THREE.Vector3();
          box.getCenter(center);
          regionCentroids[regionId] = center;
          regionCameraPos[regionId] = computeRegionCameraPos(center, regionId, 'subcortical');

          console.log('[brain-3d-v3] Atlas ' + regionId + ': '
            + data.vertexCount + ' verts, ' + data.faceCount + ' faces at',
            center.x.toFixed(3), center.y.toFixed(3), center.z.toFixed(3));

          resolve(mesh);
        }, undefined, function(err) {
          // Texture load failed -- fall back to solid color
          console.warn('[brain-3d-v3] Texture load failed for ' + regionId + ', using solid color');
          var baseColor = new THREE.Color(TISSUE_COLOR);
          var mat = new THREE.MeshPhysicalMaterial({
            color: baseColor, envMap: _envMap, envMapIntensity: 0.08,
            roughness: 0.68, metalness: 0.0, emissive: baseColor,
            emissiveIntensity: 0.04, clearcoat: 0.10, clearcoatRoughness: 0.38,
            sheen: 0.09, sheenRoughness: 0.52, sheenColor: new THREE.Color(0xFFBBAA),
            transparent: false, opacity: 1.0, side: THREE.DoubleSide, depthWrite: true,
          });
          mat._origColor     = baseColor.clone();
          mat._origEmissive  = baseColor.clone();
          mat._origRoughness = mat.roughness;

          var mesh = new THREE.Mesh(geo, mat);
          mesh.name = regionId;
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          mesh.visible = true;

          var selMat = new THREE.MeshBasicMaterial({
            color: 0xFFD060, side: THREE.BackSide,
            transparent: true, opacity: 0.0, depthWrite: false,
          });
          var selOutline = new THREE.Mesh(geo, selMat);
          selOutline.scale.setScalar(1.04);
          selOutline.renderOrder = 3;
          selOutline.visible = false;
          selOutline.userData = { isOutline: true };
          mesh.userData = {
            regionId: regionId, label: regionId, type: 'subcortical',
            permanent: true, overlayMat: mat, selOutline: selOutline,
          };
          mesh.add(selOutline);

          permanentMeshes.push(mesh);
          regionMeshes.push(mesh);
          subcorticalMeshes.push(mesh);
          if (regionId === 'cerebellum') cerebellumMeshes.push(mesh);
          if (regionId === 'brainstem')  brainstemMeshes.push(mesh);
          brainGroup.add(mesh);

          var box = new THREE.Box3().setFromObject(mesh);
          var center = new THREE.Vector3();
          box.getCenter(center);
          regionCentroids[regionId] = center;
          regionCameraPos[regionId] = computeRegionCameraPos(center, regionId, 'subcortical');
          resolve(mesh);
        });
      })
      .catch(function(err) {
        console.error('[brain-3d-v3] Failed to load ' + regionId + ' mesh JSON:', err);
        resolve(null);
      });
  });
}

function loadAtlasBrainstem() {
  return _loadAtlasMesh('brainstem',
    'data/brain_meshes/brainstem_mesh.json?v=' + ASSET_VERSION,
    'data/brain_meshes/brainstem_texture.png?v=' + ASSET_VERSION);
}

function loadAtlasCerebellum() {
  // Load high-detail JSON geometry (10K verts) with solid material (no texture to avoid UV stripe artifacts)
  console.log('[brain-3d-v3] loadAtlasCerebellum() called');
  return new Promise(function(resolve) {
    fetch('data/brain_meshes/cerebellum_mesh.json?v=' + ASSET_VERSION)
      .then(function(r) {
        console.log('[brain-3d-v3] cerebellum JSON fetch status:', r.status);
        return r.json();
      })
      .then(function(data) {
        console.log('[brain-3d-v3] cerebellum JSON parsed, verts:', data.positions.length / 3);
        var positions = new Float32Array(data.positions);
        var normals   = new Float32Array(data.normals);
        var nVerts    = positions.length / 3;

        // Compute centroid
        var cx = 0, cy = 0, cz = 0;
        for (var vi = 0; vi < nVerts; vi++) {
          cx += positions[vi * 3];
          cy += positions[vi * 3 + 1];
          cz += positions[vi * 3 + 2];
        }
        cx /= nVerts; cy /= nVerts; cz /= nVerts;

        // Displace vertices along normals to create folia ridges
        var FOLIA_FREQ = 55.0;   // number of folia bands
        var FOLIA_AMP  = 0.008;  // ridge depth (subtle)
        for (var vi = 0; vi < nVerts; vi++) {
          var py = positions[vi * 3 + 1];  // Y = elevation in scene space
          var localY = py - cy;
          var ridge = Math.sin(localY * FOLIA_FREQ * 2.0 * Math.PI) * FOLIA_AMP;
          positions[vi * 3]     += normals[vi * 3]     * ridge;
          positions[vi * 3 + 1] += normals[vi * 3 + 1] * ridge;
          positions[vi * 3 + 2] += normals[vi * 3 + 2] * ridge;
        }

        var geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geo.setAttribute('normal',   new THREE.Float32BufferAttribute(normals, 3));
        geo.setIndex(new THREE.Uint32BufferAttribute(new Uint32Array(data.indices), 1));
        geo.computeVertexNormals();  // recompute after displacement — ridges catch light naturally

        var baseColor = new THREE.Color(0xD88878);  // saturated pink-flesh — survives ACES desaturation
        var mat = new THREE.MeshPhysicalMaterial({
          color:              baseColor,
          emissive:           new THREE.Color(0x5A2A2A),
          emissiveIntensity:  0.08,
          envMap:             _envMap,
          envMapIntensity:    0.06,
          clearcoat:          0.04,
          clearcoatRoughness: 0.7,
          sheen:              0.03,
          sheenRoughness:     0.75,
          sheenColor:         new THREE.Color(0xDDBBAA),
          roughness:          0.78,
          metalness:          0.0,
          side:               THREE.DoubleSide,
          depthWrite:         true,
        });
        mat._origColor     = baseColor.clone();
        mat._origEmissive  = new THREE.Color(0x5A2A2A);
        mat._origRoughness = mat.roughness;
        console.log('[brain-3d-v3] Cerebellum: color=#D88878, ridgeAmp=0.008, ridgeFreq=55, faces=~124K');

        var mesh = new THREE.Mesh(geo, mat);
        mesh.name = 'cerebellum';
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.visible = true;

        var selMat = new THREE.MeshBasicMaterial({
          color: 0xFFD060, side: THREE.BackSide,
          transparent: true, opacity: 0.0, depthWrite: false,
        });
        var selOutline = new THREE.Mesh(geo, selMat);
        selOutline.scale.setScalar(1.04);
        selOutline.renderOrder = 3;
        selOutline.visible = false;
        selOutline.userData = { isOutline: true };
        mesh.userData = {
          regionId: 'cerebellum', label: 'cerebellum', type: 'subcortical',
          permanent: true, overlayMat: mat, selOutline: selOutline,
        };
        mesh.add(selOutline);

        permanentMeshes.push(mesh);
        regionMeshes.push(mesh);
        subcorticalMeshes.push(mesh);
        cerebellumMeshes.push(mesh);
        brainGroup.add(mesh);

        var box = new THREE.Box3().setFromObject(mesh);
        var center = new THREE.Vector3();
        box.getCenter(center);
        regionCentroids['cerebellum'] = center;
        regionCameraPos['cerebellum'] = computeRegionCameraPos(center, 'cerebellum', 'subcortical');
        resolve(mesh);
      })
      .catch(function(err) {
        console.error('[brain-3d-v3] Failed to load cerebellum mesh:', err);
        resolve(null);
      });
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// CEREBELLUM GLASS HELPER
// ═══════════════════════════════════════════════════════════════════════════════

// Makes the cerebellum semi-transparent (glass) or restores it to its current
// natural state (opaque normally, glass if global glass mode is on).
// Called automatically when certain regions are highlighted/deselected.
function _setCerebellumGlass(on) {
  if (!cerebellumVisible) return;
  cerebellumMeshes.forEach(function(m) {
    var mat = m.userData.overlayMat;
    if (!mat) return;
    if (on) {
      mat.transparent = true;
      mat.opacity     = 0.08;
      mat.depthWrite  = false;
      mat.side        = THREE.DoubleSide;
    } else if (glassOn) {
      // Global glass mode already controls opacity — don't fight it
      mat.transparent = true;
      mat.opacity     = 0.08;
      mat.depthWrite  = false;
      mat.side        = THREE.DoubleSide;
    } else {
      mat.color.copy(mat._origColor);
      mat.emissive.copy(mat._origEmissive);
      mat.emissiveIntensity = 0.04;
      mat.transparent = false;
      mat.opacity     = 1.0;
      mat.depthWrite  = true;
      mat.side        = THREE.FrontSide;
    }
    mat.needsUpdate = true;
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// OUTLINE GEOMETRY UTILITY
// ═══════════════════════════════════════════════════════════════════════════════

// Displaces every vertex outward by `amount` scene units along its vertex normal.
// This gives a UNIFORM border thickness regardless of where the mesh sits in the
// scene — unlike scale.setScalar() which inflates away from the world origin and
// produces nearly-invisible borders for structures near the scene centre (e.g.
// cingulate gyrus, medial frontal).
var OUTLINE_INFLATE = 0.022;  // ~1.65 mm at scene scale (1 unit = 75 mm)

function _inflateGeomByNormal(geom) {
  var out = geom.clone();
  var pos = out.attributes.position;
  var nrm = out.attributes.normal;
  if (!nrm) return out;
  for (var i = 0; i < pos.count; i++) {
    pos.setX(i, pos.getX(i) + nrm.getX(i) * OUTLINE_INFLATE);
    pos.setY(i, pos.getY(i) + nrm.getY(i) * OUTLINE_INFLATE);
    pos.setZ(i, pos.getZ(i) + nrm.getZ(i) * OUTLINE_INFLATE);
  }
  pos.needsUpdate = true;
  return out;
}


// ═══════════════════════════════════════════════════════════════════════════════
// BILATERAL MIRROR UTILITY
// ═══════════════════════════════════════════════════════════════════════════════

// Creates a right-hemisphere mirror of a left-hemisphere overlay mesh by reflecting
// vertex positions across x = MIDLINE_X, flipping x-normals, and reversing winding.
// The mirror shares the same material so colour/opacity stay in sync automatically.
// In split view the hardware clip plane (x > MIDLINE_X) removes it entirely — no
// special-case code needed.
function _createMirrorMesh(sourceMesh) {
  var origGeom   = sourceMesh.geometry;
  var mirrorGeom = origGeom.clone();

  var pos = mirrorGeom.attributes.position;
  for (var i = 0; i < pos.count; i++) {
    pos.setX(i, 2.0 * MIDLINE_X - pos.getX(i));
  }
  pos.needsUpdate = true;

  if (mirrorGeom.attributes.normal) {
    var nrm = mirrorGeom.attributes.normal;
    for (var i = 0; i < nrm.count; i++) {
      nrm.setX(i, -nrm.getX(i));
    }
    nrm.needsUpdate = true;
  }

  if (mirrorGeom.index) {
    var idx = mirrorGeom.index.array;
    for (var i = 0; i < idx.length; i += 3) {
      var tmp    = idx[i + 1];
      idx[i + 1] = idx[i + 2];
      idx[i + 2] = tmp;
    }
    mirrorGeom.index.needsUpdate = true;
  }

  var mirror         = new THREE.Mesh(mirrorGeom, sourceMesh.material);
  mirror.castShadow    = false;
  mirror.receiveShadow = false;
  mirror.visible       = false;
  mirror.userData      = { isMirror: true, regionId: sourceMesh.userData.regionId };

  // Give the mirror its own gold selection outline using the same normal-inflation
  // approach as the source mesh so border width is consistent on both hemispheres.
  var mirrorSelMat = new THREE.MeshBasicMaterial({
    color:       0xFFD060,
    side:        THREE.BackSide,
    transparent: true,
    opacity:     0.0,
    depthWrite:  false,
  });
  var mirrorSelOutline = new THREE.Mesh(_inflateGeomByNormal(mirrorGeom), mirrorSelMat);
  mirrorSelOutline.renderOrder = 3;
  mirrorSelOutline.visible = false;
  mirrorSelOutline.userData = { isOutline: true };
  mirror.userData.selOutline = mirrorSelOutline;
  mirror.add(mirrorSelOutline);

  return mirror;
}


// ═══════════════════════════════════════════════════════════════════════════════
// REGION OVERLAY LOADER
// ═══════════════════════════════════════════════════════════════════════════════

function loadRegion(regionId, entry, permanent) {
  return new Promise(function(resolve) {
    loader.load(entry.file + '?v=' + ASSET_VERSION,
      function(gltf) {
        var baseColor = permanent
          ? new THREE.Color(TISSUE_COLOR)
          : new THREE.Color(OVERLAY_COLORS[regionId] || 0x8888AA);

        var mat = new THREE.MeshPhysicalMaterial({
          color:              baseColor,
          envMap:             _envMap,
          envMapIntensity:    permanent ? 0.08 : 0.09,
          roughness:          permanent ? 0.68 : 0.58,
          metalness:          0.0,
          emissive:           baseColor,
          emissiveIntensity:  permanent ? 0.04 : 0.18,
          clearcoat:          permanent ? 0.10 : 0.14,
          clearcoatRoughness: permanent ? 0.38 : 0.32,
          sheen:              permanent ? 0.09 : 0.15,
          sheenRoughness:     0.52,
          sheenColor:         new THREE.Color(0xFFBBAA),
          transparent:        !permanent,
          opacity:            1.0,
          side:               THREE.FrontSide,
          depthWrite:         true,
          // Pull non-permanent overlays slightly forward so they don't z-fight
          // with the cortex surface they sit flush against (important for medial
          // structures like cingulate gyrus viewed in split mode).
          polygonOffset:      !permanent,
          polygonOffsetFactor: -2,
          polygonOffsetUnits: -4,
        });
        mat._origColor     = baseColor.clone();
        mat._origEmissive  = baseColor.clone();
        mat._origRoughness = mat.roughness;

        // Collect meshes iteratively to avoid stack overflow on deeply nested GLBs
        var meshList = [];
        var stack = [gltf.scene];
        while (stack.length > 0) {
          var node = stack.pop();
          if (node.isMesh) meshList.push(node);
          if (node.children) {
            for (var si = 0; si < node.children.length; si++) {
              stack.push(node.children[si]);
            }
          }
        }

        meshList.forEach(function(child) {
          child.geometry.computeVertexNormals();
          child.material      = mat;
          child.name          = regionId;
          child.castShadow    = false;
          child.receiveShadow = false;
          child.visible       = permanent;

          child.userData = {
            regionId:   regionId,
            label:      regionId,
            type:       entry.type,
            permanent:  permanent,
            overlayMat: mat,
          };

          // Gold selection outline — vertices displaced outward along normals by a
          // fixed distance (OUTLINE_INFLATE) so the border width is uniform for
          // all regions including thin medial structures like cingulate gyrus.
          var selMat = new THREE.MeshBasicMaterial({
            color:       0xFFD060,
            side:        THREE.BackSide,
            transparent: true,
            opacity:     0.0,
            depthWrite:  false,
          });
          var selOutline = new THREE.Mesh(_inflateGeomByNormal(child.geometry), selMat);
          selOutline.renderOrder = 3;
          selOutline.visible = false;
          selOutline.userData = { isOutline: true };
          child.userData.selOutline = selOutline;
          child.add(selOutline);

          // Track in registries
          if (permanent) {
            permanentMeshes.push(child);
            if (regionId === 'cerebellum') cerebellumMeshes.push(child);
            if (regionId === 'brainstem')  brainstemMeshes.push(child);
          }
          regionMeshes.push(child);
          if (entry.type === 'subcortical') {
            subcorticalMeshes.push(child);
          } else {
            corticalMeshes.push(child);
          }
        });

        // Bilateral mirror: for symmetric regions, reflect each mesh across
        // x = MIDLINE_X so BOTH hemispheres light up when the region is selected.
        if (!permanent && BILATERAL_REGIONS.has(regionId)) {
          meshList.forEach(function(child) {
            var mirror = _createMirrorMesh(child);
            child.userData.mirrorMesh = mirror;
            brainGroup.add(mirror);
          });
        }

        brainGroup.add(gltf.scene);

        // Compute centroid for camera auto-focus
        var box = new THREE.Box3().setFromObject(gltf.scene);
        var center = new THREE.Vector3();
        box.getCenter(center);
        regionCentroids[regionId] = center.clone();

        // Compute ideal camera position — offset from centroid toward viewer
        var camPos = computeRegionCameraPos(center, regionId, entry.type);
        regionCameraPos[regionId] = camPos;

        resolve();
      },
      undefined,
      function(err) {
        console.warn('[brain-3d-v3] Region load failed (' + regionId + '):', err);
        resolve();
      }
    );
  });
}

function computeRegionCameraPos(center, regionId, type) {
  // Direction from brain center to region centroid
  var dir = center.clone().sub(CAM_ORIGIN);
  var dist = dir.length();
  if (dist < 0.01) dir.set(1, 0, 0);
  dir.normalize();

  // Camera distance: closer for small subcortical, further for large cortical
  var camDist = (type === 'subcortical') ? 3.0 : 4.2;

  // ── Frontal lobe regions ──────────────────────────────────────────────────
  // Lateral + pushed anterior so the frontal convexity is centred in frame
  if (regionId === 'frontal_lobe') {
    return new THREE.Vector3(4.2, 0.8, 2.2);
  }
  // Lateral-anterior, elevated — shows dorsal PFC and orbital surface
  if (regionId === 'prefrontal_cortex') {
    return new THREE.Vector3(3.8, 1.0, 2.8);
  }
  // Tighter lateral-anterior — zooms in on the small inferior frontal patch
  if (regionId === 'brocas_area') {
    return new THREE.Vector3(3.2, 0.1, 1.3);
  }
  // Lateral, slightly inferior — insula is auto-glassed so opercular cortex is
  // transparent; camera looks into the Sylvian fissure from the lateral side
  if (regionId === 'insula') {
    return new THREE.Vector3(4.5, -0.2, 0.4);
  }
  // Lateral, elevated — precentral strip runs superior-to-inferior
  if (regionId === 'motor_cortex') {
    return new THREE.Vector3(4.5, 2.2, 0.4);
  }

  // ── Parietal lobe regions ─────────────────────────────────────────────────
  // Lateral + elevated + slightly posterior (y_MNI ≈ −30 to −75, z_MNI ≈ 30–75)
  if (regionId === 'parietal_lobe') {
    return new THREE.Vector3(4.0, 2.5, -0.8);
  }
  // Lateral, elevated — postcentral strip (similar to motor, slightly posterior)
  if (regionId === 'somatosensory_cortex') {
    return new THREE.Vector3(4.5, 2.0, 0.0);
  }

  // ── Temporal lobe regions ─────────────────────────────────────────────────
  // Direct lateral, slightly inferior — STG/MTG/ITG at z_MNI ≈ 0–15
  if (regionId === 'temporal_lobe') {
    return new THREE.Vector3(4.8, -0.6, 0.5);
  }
  // Lateral, eye level, pulled posterior — posterior STG (y_MNI < −25)
  if (regionId === 'wernickes_area') {
    return new THREE.Vector3(5.0, 0.1, -1.0);
  }

  // ── Medial-wall cortical structures ──────────────────────────────────────
  if (regionId === 'cingulate_gyrus' || regionId === 'medial_frontal') {
    return new THREE.Vector3(center.x - 3.5, center.y + 0.3, center.z);
  }

  // ── Subcortical — glass mode auto-activates for these; camera angles are ──
  // ── chosen to centre the structure in frame through the glass cortex.   ──

  // Thalamus  cen≈(0.271,-0.111,0.185): deep central, slightly inferior
  // Camera elevated-lateral to separate thalamus from brainstem below it
  if (regionId === 'thalamus') {
    return new THREE.Vector3(3.5, 1.0, 0.2);
  }
  // Hippocampus  cen≈(0.411,-0.364,0.125): medial temporal, inferior
  // Lateral + well below eye level to frame the inferior temporal region
  if (regionId === 'hippocampus') {
    return new THREE.Vector3(3.5, -2.2, 0.0);
  }
  // Amygdala  cen≈(0.411,-0.464,0.345): anterior to hippocampus, same depth
  // Lateral-inferior, pushed anteriorly to separate from hippocampus
  if (regionId === 'amygdala') {
    return new THREE.Vector3(3.5, -2.2, 1.5);
  }
  // Caudate  cen≈(0.271,-0.077,0.451): C-shaped, head anterior, tail curves posterior-inferior
  // Elevated + anterior — shows the full C-curve from above-lateral
  if (regionId === 'caudate') {
    return new THREE.Vector3(3.0, 2.8, 1.5);
  }
  // Putamen  cen≈(0.418,-0.197,0.418): most lateral basal ganglia structure
  // Direct lateral, slightly elevated — putamen is at a good lateral depth
  if (regionId === 'putamen') {
    return new THREE.Vector3(3.5, 0.5, 0.8);
  }
  // Globus pallidus  cen≈(0.371,-0.211,0.358): medial to putamen, deep
  // Same lateral angle as putamen but slightly more anteriorly centred
  if (regionId === 'globus_pallidus') {
    return new THREE.Vector3(3.5, 0.5, 0.5);
  }
  // Nucleus accumbens: ventral striatum, anterior to caudate/putamen
  // MNI ≈ (-10, 12, -6) → scene ≈ (0.25, -0.28, 0.60)
  // Lateral, slightly inferior, strongly anterior
  if (regionId === 'nucleus_accumbens') {
    return new THREE.Vector3(3.5, 0.2, 2.2);
  }
  // Hypothalamus: midline, below thalamus, above brainstem
  // MNI center (-4,-5,-9) → scene ≈ (0.17, -0.32, 0.37)
  // Lateral, slightly below — distinctly inferior to thalamus view
  if (regionId === 'hypothalamus') {
    return new THREE.Vector3(3.5, -0.8, 0.4);
  }
  // Substantia nigra: paired midbrain crescent, dorsal to cerebral peduncles
  // MNI center (-12,-19,-14) → scene ≈ (0.28, -0.39, 0.18)
  // Lateral-inferior, matches the inferior midbrain position
  if (regionId === 'substantia_nigra') {
    return new THREE.Vector3(3.5, -1.0, 0.2);
  }

  // ── Brainstem / cerebellum ────────────────────────────────────────────────
  // Camera must come from the ANTERIOR-LATERAL side (positive z) because the
  // cerebellum sits POSTERIOR to the brainstem (z_scene ≈ -0.3 to -0.56) and
  // would block the view from behind.  Lateral + inferior + anterior = clear
  // unobstructed window onto the brainstem.
  if (regionId === 'brainstem') {
    // Full brainstem: midbrain through medulla. Elevated lateral-anterior.
    return new THREE.Vector3(2.5, -2.0, 1.5);
  }
  if (regionId === 'cerebellum') {
    // Cerebellum: posterior-inferior. Camera from below-behind.
    return new THREE.Vector3(center.x + 0.5, center.y - 3.5, center.z - 2.0);
  }

  // ── New subcortical / deep structures ────────────────────────────────────
  // VTA: ventral tegmental area, medial midbrain (dopaminergic reward center)
  // MNI (-4,-16,-12) → scene ≈ (0.17,-0.36,0.22); lateral-inferior like SN
  if (regionId === 'vta') {
    return new THREE.Vector3(3.5, -1.2, 0.0);
  }
  // Pituitary: sella turcica, below hypothalamus, very inferior midline
  // MNI (0,+5,-24) → scene ≈ (0.12,-0.52,0.51); from below-anterior
  if (regionId === 'pituitary') {
    return new THREE.Vector3(2.5, -3.0, 2.0);
  }
  // Olfactory bulb: anterior-inferior frontal, very anterior
  // MNI (-9,+24,-22) → scene ≈ (0.24,-0.49,0.76); from below-anterior
  if (regionId === 'olfactory_bulb') {
    return new THREE.Vector3(2.5, -3.0, 4.0);
  }
  // Corpus callosum: midline arch; auto-split shows medial cut face
  // Camera on medial/right side (x<0) looking toward the exposed medial surface
  if (regionId === 'corpus_callosum') {
    return new THREE.Vector3(-3.0, 0.8, 0.3);
  }
  // ── Hindbrain segments (all use auto-glass + cerebellum-glass) ───────────
  // Camera from anterior-lateral-inferior so the cerebellum (z_scene ≈ -0.35,
  // posterior) stays BEHIND the brainstem and does not block the view.
  //
  // Scene coords of brainstem segments (MNI → scene):
  //   Midbrain ctr  ≈ (0.12, -0.42, 0.22)   z_MNI -14 to -22
  //   Pons ctr      ≈ (0.12, -0.60, 0.12)   z_MNI -22 to -37
  //   Medulla ctr   ≈ (0.12, -0.80, 0.02)   z_MNI -37 to -57
  if (regionId === 'midbrain') {
    // Lateral + slightly above center + well anterior
    return new THREE.Vector3(2.5, -1.2, 1.8);
  }
  if (regionId === 'pons') {
    // Lateral + inferior + anterior — pons is the widest brainstem segment
    return new THREE.Vector3(2.5, -2.0, 1.2);
  }
  if (regionId === 'medulla') {
    // Lateral + most inferior + anterior
    return new THREE.Vector3(2.5, -3.0, 0.8);
  }

  // General: place camera along the direction from brain center through region
  return center.clone().add(dir.multiplyScalar(camDist));
}


// ═══════════════════════════════════════════════════════════════════════════════
// LOAD ORCHESTRATION
// ═══════════════════════════════════════════════════════════════════════════════

var _readyResolve = null;
var _readyPromise = new Promise(function(res) { _readyResolve = res; });

// ── Progress helper ───────────────────────────────────────────────────────────
// pct: 0-100  |  label: human-readable stage description
function _progress(pct, label) {
  window.dispatchEvent(new CustomEvent('brain3dProgress', {
    detail: { pct: pct, label: label }
  }));
}

async function loadBrain() {
  _progress(0, 'Initializing\u2026');

  // Load manifest + hires cortex in parallel
  var manifest = null;
  try {
    var results = await Promise.allSettled([
      fetch('data/brain_regions_manifest.json?v=' + ASSET_VERSION).then(function(r) { return r.json(); }),
      loadHiresBrain(),   // emits pct 5–72 internally via onProgress
    ]);
    if (results[0].status === 'fulfilled') manifest = results[0].value;
  } catch (e) {
    console.warn('[brain-3d-v3] Init error:', e);
  }

  // Cortex is ready — mount canvas and start fading the overlay.
  // Regions load silently in the background after this point.
  _progress(75, 'Building structures\u2026');
  window.dispatchEvent(new CustomEvent('brain3dReady', { detail: { regionCount: 0 } }));

  // Load anatomical brainstem + cerebellum from atlas-derived JSON meshes
  var atlasMeshPromises = [loadAtlasBrainstem(), loadAtlasCerebellum()];

  if (!manifest) {
    await Promise.allSettled(atlasMeshPromises);
    _progress(100, 'Ready');
    _readyResolve();
    return;
  }

  var regionIds = Object.keys(manifest).filter(function(id) {
    return manifest[id].type !== 'glass' && !PERMANENT_IDS.has(id);
  });
  var loadedCount = 0;
  var totalRegions = regionIds.length;

  await Promise.allSettled(atlasMeshPromises);
  _progress(80, 'Loading regions\u2026');

  var BATCH = 8;
  for (var bi = 0; bi < regionIds.length; bi += BATCH) {
    var batch = regionIds.slice(bi, bi + BATCH);
    await Promise.allSettled(batch.map(function(id) {
      return loadRegion(id, manifest[id], false).then(function() {
        loadedCount++;
        var pct = 80 + Math.round((loadedCount / totalRegions) * 14);  // 80–94%
        _progress(pct, 'Loading regions\u2026 ' + loadedCount + '\u202f/\u202f' + totalRegions);
      });
    }));
  }

  _progress(95, 'Finalizing scene\u2026');

  if (splitOn) toggleSplit(true);

  _progress(100, 'Ready');
  _readyResolve();
}

loadBrain();


// ═══════════════════════════════════════════════════════════════════════════════
// CAMERA PRESETS
// ═══════════════════════════════════════════════════════════════════════════════

var CAMERA_VIEWS = {
  lateral:    new THREE.Vector3( 4.8,   0.5,   0.4),
  medial:     new THREE.Vector3(-3.8,   0.5,   0.4),
  superior:   new THREE.Vector3( 0.6,   5.5,   0.8),
  inferior:   new THREE.Vector3( 0.6,  -5.5,   0.8),
  anterior:   new THREE.Vector3( 0.5,   0.5,   5.2),
  posterior:  new THREE.Vector3( 0.5,   0.5,  -5.6),
  brainstem:  new THREE.Vector3( 1.8,  -3.2,  -3.5),
  cerebellum: new THREE.Vector3( 0.6,  -4.2,  -3.0),
};

var camFrom     = null;
var camTo       = null;
var camT        = 0;
var targetFrom  = null;
var targetTo    = null;
var CAM_DUR     = 0.72;

function _startCamTransition(toPos, toTarget) {
  camFrom    = camera.position.clone();
  camTo      = toPos.clone();
  targetFrom = controls.target.clone();
  targetTo   = toTarget.clone();
  camT       = 0;
  controls.enabled = false;  // disable OrbitControls during transition
}

function setCameraView(name) {
  var tgt = CAMERA_VIEWS[name];
  if (!tgt) return;
  _startCamTransition(tgt, CAM_ORIGIN);
}

function focusRegion(regionId) {
  var camPos = regionCameraPos[regionId];
  var center = regionCentroids[regionId];
  if (!camPos || !center) return;
  // In quiz mode the quiz bar covers the bottom ~15-20% of the viewport.
  // Shifting the orbit target 0.15 world units downward makes the camera tilt
  // slightly upward, pushing brain content up in the frame and clearing the bar.
  var target = quizMode ? center.clone().setY(center.y - 0.15) : center;
  _startCamTransition(camPos, target);
}


// ═══════════════════════════════════════════════════════════════════════════════
// OVERLAY VISIBILITY HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

function _showOverlay(mesh, showOutline) {
  mesh.visible = true;
  _visibleCacheDirty = true;
  var sel = mesh.userData.selOutline;
  if (sel) {
    sel.visible = !!showOutline;
    if (showOutline) { sel.material.opacity = 0.65; }
  }
  // Show right-hemisphere mirror (and its own selOutline) in sync
  var mirror = mesh.userData.mirrorMesh;
  if (mirror) {
    mirror.visible = true;
    var mirrorSel = mirror.userData.selOutline;
    if (mirrorSel) {
      mirrorSel.visible = !!showOutline;
      if (showOutline) { mirrorSel.material.opacity = 0.65; }
    }
  }
}

function _hideOverlay(mesh) {
  if (mesh.userData.permanent) return;
  mesh.visible = false;
  _visibleCacheDirty = true;
  var sel = mesh.userData.selOutline;
  if (sel) { sel.visible = false; sel.material.opacity = 0.0; }
  var mirror = mesh.userData.mirrorMesh;
  if (mirror) {
    mirror.visible = false;
    var mirrorSel = mirror.userData.selOutline;
    if (mirrorSel) { mirrorSel.visible = false; mirrorSel.material.opacity = 0.0; }
  }
}

function _hideAllOverlays() {
  regionMeshes.forEach(_hideOverlay);
}

function _restorePermanent() {
  permanentMeshes.forEach(function(m) {
    var mat = m.userData.overlayMat;
    if (!mat) return;
    mat.color.copy(mat._origColor);
    mat.emissive.copy(mat._origEmissive);
    mat.emissiveIntensity = 0.04;
    mat.transparent = false;
    mat.opacity = 1.0;
    mat.depthWrite = true;
    mat.needsUpdate = true;
    m.visible = true;
    // Respect cerebellum and brainstem toggles
    if (m.userData.regionId === 'cerebellum' && !cerebellumVisible) {
      m.visible = false;
    }
    if (m.userData.regionId === 'brainstem' && !brainstemVisible) {
      m.visible = false;
    }
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// HIRES GLASS HELPERS
// ═══════════════════════════════════════════════════════════════════════════════

function _applyHiresGlass(on, excludeRegionId) {
  var allVisual = hiresMeshes.concat(permanentMeshes);
  allVisual.forEach(function(m) {
    if (!m.material) return;
    // Skip hidden cerebellum/brainstem
    if (m.userData && m.userData.regionId === 'cerebellum' && !cerebellumVisible) return;
    if (m.userData && m.userData.regionId === 'brainstem' && !brainstemVisible) return;
    // Skip the selected region's permanent mesh (it stays opaque in isolation)
    if (excludeRegionId && m.userData && m.userData.regionId === excludeRegionId) return;
    if (on) {
      m.material.transparent = true;
      m.material.opacity     = 0.08;
      m.material.depthWrite  = false;
      m.material.side        = THREE.DoubleSide;
      if (m.material._isHiresMat) {
        m.material.roughness          = 0.10;
        m.material.clearcoat          = 0.35;
        m.material.clearcoatRoughness = 0.15;
        m.material.transmission       = 0;  // disable SSS in glass mode
      }
    } else {
      m.material.transparent = false;
      m.material.opacity     = 1.0;
      m.material.depthWrite  = true;
      m.material.side        = THREE.FrontSide;
      if (m.material._isHiresMat) {
        m.material.roughness          = 0.75;
        m.material.clearcoat          = 0.08;
        m.material.clearcoatRoughness = 0.60;
        m.material.transmission       = 0.08;  // restore SSS
      } else if (m.userData && m.userData.overlayMat) {
        m.material.roughness = m.material._origRoughness || 0.68;
      }
    }
    m.material.needsUpdate = true;
  });
}

function _dimHires(on) {
  var allVisual = hiresMeshes.concat(permanentMeshes);
  allVisual.forEach(function(m) {
    if (!m.material) return;
    if (m.userData && m.userData.regionId === 'cerebellum' && !cerebellumVisible) return;
    if (on) {
      m.material.transparent = true;
      m.material.opacity     = 0.40;
      m.material.depthWrite  = false;
    } else if (!glassOn) {
      m.material.transparent = false;
      m.material.opacity     = 1.0;
      m.material.depthWrite  = true;
    }
    m.material.needsUpdate = true;
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// PUBLIC REGION API
// ═══════════════════════════════════════════════════════════════════════════════

function highlightRegion(regionId) {
  // Restore cerebellum from any previous region's auto-glass before applying
  // the new region's state (avoids permanently glassed cerebellum on switch).
  _setCerebellumGlass(false);

  // Auto-glass for deeply buried structures — hidden behind opaque cortex
  // without glass mode. Includes all deep subcortical + buried cortical (insula).
  var _AUTO_GLASS_REGIONS = new Set([
    'insula',
    'thalamus', 'hippocampus', 'amygdala',
    'caudate', 'putamen', 'globus_pallidus',
    'nucleus_accumbens', 'hypothalamus', 'substantia_nigra',
    'vta', 'pituitary', 'olfactory_bulb', 'corpus_callosum',
    // Brainstem segments: overlay meshes are hidden behind the permanent
    // brainstem mesh unless glass mode is active (makes brainstem 8% opacity).
    'midbrain', 'pons', 'medulla',
  ]);
  if (_AUTO_GLASS_REGIONS.has(regionId) && !glassOn) {
    glassOn = true;
    _applyHiresGlass(true);
    _autoGlassActive = true;
    window.dispatchEvent(new CustomEvent('brain3dGlassChanged', { detail: { glassOn: true } }));
  } else if (_autoGlassActive && !_AUTO_GLASS_REGIONS.has(regionId)) {
    // Leaving an auto-glass region — restore opaque brain.
    glassOn = false;
    _applyHiresGlass(false);
    _autoGlassActive = false;
    window.dispatchEvent(new CustomEvent('brain3dGlassChanged', { detail: { glassOn: false } }));
  }

  // For cortical regions (no glass), always restore brain to 100% opacity.
  // Undoes any dimming from dimAllRegions() or prior quiz question state.
  if (!glassOn) {
    _dimHires(false);
  }

  selectedRegionId = regionId;

  // Medial-wall structures — auto-enable split view so the medial surface is
  // visible. Auto-disable when leaving a medial region (mirrors _autoGlassActive).
  // The UI split button stays in sync via the brain3dSplitChanged event.
  var _MEDIAL_AUTO_SPLIT = { cingulate_gyrus: true, medial_frontal: true, corpus_callosum: true };
  if (_MEDIAL_AUTO_SPLIT[regionId] && !splitOn) {
    toggleSplit(true);
    _autoSplitActive = true;
  } else if (_autoSplitActive && !_MEDIAL_AUTO_SPLIT[regionId]) {
    toggleSplit(false);
    _autoSplitActive = false;
  }

  _hideAllOverlays();

  // _hideAllOverlays() skips permanent meshes, so prior highlight colors on the
  // brainstem persist. Explicitly restore brainstem when it's not the target region.
  // _hideAllOverlays() skips permanent meshes, so prior highlight colors and
  // selection outlines on brainstem/cerebellum persist. Restore each one when
  // it is not the target region.
  var _permanentRestoreIds = [];
  if (regionId !== 'brainstem')   _permanentRestoreIds.push('brainstem');
  if (regionId !== 'cerebellum')  _permanentRestoreIds.push('cerebellum');
  permanentMeshes.forEach(function(m) {
    if (_permanentRestoreIds.indexOf(m.userData.regionId) === -1) return;
    var mat = m.userData.overlayMat;
    if (mat) {
      mat.color.copy(mat._origColor);
      mat.emissive.copy(mat._origEmissive);
      mat.emissiveIntensity = 0.04;
      mat.needsUpdate = true;
    }
    var sel = m.userData.selOutline;
    if (sel) { sel.visible = false; sel.material.opacity = 0.0; }
  });

  // In glass mode, apply glass FIRST (before region material override)
  // and exclude the selected region from dimming
  if (glassOn) {
    _applyHiresGlass(true, regionId);
    // Brainstem sub-segments: show brainstem shell at 65% opacity (visible
    // anatomical context) rather than full 8% glass — it is the parent structure.
    if (regionId === 'midbrain' || regionId === 'pons' || regionId === 'medulla') {
      brainstemMeshes.forEach(function(m) {
        if (!m.material || !brainstemVisible) return;
        m.material.transparent = true;
        m.material.opacity = 0.65;
        m.material.depthWrite = false;
        m.material.needsUpdate = true;
      });
    }
  }

  regionMeshes.forEach(function(m) {
    if (m.userData.regionId !== regionId) return;
    var mat = m.userData.overlayMat;
    if (!mat) return;

    var col = new THREE.Color(OVERLAY_COLORS[regionId] || 0x8888AA);
    mat.color.copy(col);
    mat.emissive.copy(col);

    if (glassOn) {
      // ISOLATION MODE: selected region fully opaque, everything else glass
      mat.emissiveIntensity = 0.30;
      mat.transparent       = false;
      mat.opacity           = 1.0;
      mat.depthWrite        = true;
      mat.side              = THREE.FrontSide;
      mat.roughness         = 0.55;
      mat.clearcoat         = 0.18;
      mat.clearcoatRoughness = 0.30;
    } else {
      // Normal highlight: semi-transparent overlay on opaque cortex
      mat.emissiveIntensity = 0.32;
      mat.transparent       = true;
      mat.opacity           = 0.92;
      mat.depthWrite        = true;
      mat.side              = THREE.FrontSide;
    }
    mat.needsUpdate = true;
    _showOverlay(m, true);
  });

  // Auto-glass the cerebellum for regions it occludes in the lateral view
  if (CEREBELLUM_GLASS_REGIONS.has(regionId)) {
    _setCerebellumGlass(true);
  }
}

var _quizCamSavedPos = null;

function enterQuizMode() {
  // Set quiz mode flag (suppresses hover overlays) without dimming the brain.
  // Brain stays at 100% opacity; only the selected chip's region is highlighted.
  quizMode = true;
  selectedRegionId = null;
  _hideAllOverlays();

  // Zoom out slightly so the brain fits comfortably above the quiz bar.
  // _quizCamSavedPos is saved ONCE (at quiz start) and never overwritten mid-quiz,
  // so the base position never drifts across questions or chip-click focus events.
  // Always zoom relative to CAM_ORIGIN so the orbit target resets to brain center.
  if (!_quizCamSavedPos) {
    _quizCamSavedPos = camera.position.clone();
  }
  var dir    = _quizCamSavedPos.clone().sub(CAM_ORIGIN).normalize();
  var dist   = _quizCamSavedPos.distanceTo(CAM_ORIGIN);
  var newPos = CAM_ORIGIN.clone().add(dir.multiplyScalar(dist * 1.15));
  _startCamTransition(newPos, CAM_ORIGIN.clone());
}

// Restore camera to pre-quiz position. Call from stopQuiz() only — NOT between
// questions — so the saved base is never lost mid-quiz.
function exitQuizCamera() {
  if (_quizCamSavedPos) {
    _startCamTransition(_quizCamSavedPos, CAM_ORIGIN.clone());
    _quizCamSavedPos = null;
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
    if (!mat) return;
    var col = new THREE.Color(OVERLAY_COLORS[m.userData.regionId] || 0x8888AA);
    mat.color.copy(col);
    mat.emissive.copy(col);
    mat.emissiveIntensity = 0.18;
    mat.transparent       = true;
    mat.opacity           = 0.55;
    mat.depthWrite        = false;
    mat.needsUpdate       = true;
    _showOverlay(m, false);
  });
}

function resetRegions() {
  _setCerebellumGlass(false);  // restore before state is cleared
  // Clear auto-glass state if active
  if (_autoGlassActive) {
    _autoGlassActive = false;
    if (glassOn) {
      glassOn = false;
      _applyHiresGlass(false);
      window.dispatchEvent(new CustomEvent('brain3dGlassChanged', { detail: { glassOn: false } }));
    }
  }
  quizMode = false;
  selectedRegionId = null;
  hoveredRegionId = null;
  _hideAllOverlays();

  if (glassOn) {
    // Glass stays on — just remove the isolation (no selected region)
    _applyHiresGlass(true);
  } else {
    // Fully restore opaque state
    _restorePermanent();
    _dimHires(false);
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// GLASS BRAIN TOGGLE
// ═══════════════════════════════════════════════════════════════════════════════

function toggleGlass(forceState) {
  _autoGlassActive = false;  // manual toggle overrides auto-glass tracking
  if (typeof forceState === 'boolean') {
    glassOn = forceState;
  } else {
    glassOn = !glassOn;
  }
  _applyHiresGlass(glassOn);

  if (!glassOn) {
    // Exiting glass: restore everything to opaque
    _hideAllOverlays();
    _restorePermanent();
    selectedRegionId = null;
  } else if (selectedRegionId) {
    // Glass on + region already selected → re-apply isolation
    highlightRegion(selectedRegionId);
  }

  return glassOn;
}


// ═══════════════════════════════════════════════════════════════════════════════
// SPLIT BRAIN TOGGLE
// ═══════════════════════════════════════════════════════════════════════════════

var _splitPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), -MIDLINE_X);

function toggleSplit(forceState) {
  if (typeof forceState === 'boolean') {
    splitOn = forceState;
  } else {
    splitOn = !splitOn;
    _autoSplitActive = false;  // manual toggle clears auto-split tracking
  }

  if (splitOn) {
    // Use hardware clip plane (gl_ClipDistance) via renderer.clippingPlanes.
    // Unlike material.clippingPlanes (which discards in the fragment shader),
    // hardware clipping runs before rasterization — so the invisible hemisphere
    // never writes to the depth buffer, shadow map, or transmission pre-pass.
    // This lets GTAO, shadows, AO map, and transmission all stay on at full
    // quality without seeing the ghost hemisphere.
    renderer.clippingPlanes = [_splitPlane];
    renderer.localClippingEnabled = true;

    // Show cut face interior on cortex
    hiresMeshes.forEach(function(m) {
      if (!m.material) return;
      m.material.side = THREE.DoubleSide;
      m.material.needsUpdate = true;
    });

    // Clip cortical overlay meshes too so they don't poke through
    corticalMeshes.forEach(function(m) {
      var mat = m.userData.overlayMat;
      if (!mat) return;
      mat.side = THREE.DoubleSide;
      mat.needsUpdate = true;
    });

    // Hide subcortical overlays (they straddle midline) but keep brainstem + cerebellum
    permanentMeshes.forEach(function(m) {
      if (m.userData.regionId === 'cerebellum') {
        m.visible = cerebellumVisible;
      } else if (m.userData.regionId === 'brainstem') {
        m.visible = brainstemVisible;
      }
    });
    // Show subcortical structures in split view (they sit at the interior)
    subcorticalMeshes.forEach(function(m) {
      if (m.userData.permanent) return;
      m.visible = true;
      var mat = m.userData.overlayMat;
      if (mat) {
        mat.clippingPlanes = [];  // no clipping — fully visible
        mat.needsUpdate = true;
      }
    });
  } else {
    // Remove global hardware clip and restore cortex materials
    renderer.clippingPlanes = [];
    renderer.localClippingEnabled = false;
    hiresMeshes.forEach(function(m) {
      if (!m.material) return;
      m.material.side = glassOn ? THREE.DoubleSide : THREE.FrontSide;
      m.material.needsUpdate = true;
    });

    // Restore cortical overlay sides
    corticalMeshes.forEach(function(m) {
      var mat = m.userData.overlayMat;
      if (!mat) return;
      mat.side = THREE.FrontSide;
      mat.needsUpdate = true;
    });

    _restorePermanent();
  }

  // Notify the UI (e.g. the split button) so it can sync its visual state
  window.dispatchEvent(new CustomEvent('brain3dSplitChanged', { detail: { splitOn: splitOn } }));

  return splitOn;
}


// ═══════════════════════════════════════════════════════════════════════════════
// CEREBELLUM TOGGLE
// ═══════════════════════════════════════════════════════════════════════════════

function toggleCerebellum(forceState) {
  if (typeof forceState === 'boolean') {
    cerebellumVisible = forceState;
  } else {
    cerebellumVisible = !cerebellumVisible;
  }

  // Respect split mode: cerebellum stays hidden if split is on
  var effectiveVisible = cerebellumVisible && !splitOn;

  cerebellumMeshes.forEach(function(m) {
    m.visible = effectiveVisible;
    // Restore material state when re-showing
    if (effectiveVisible) {
      var mat = m.userData.overlayMat;
      if (!mat) return;
      if (glassOn) {
        mat.transparent        = true;
        mat.opacity            = 0.08;
        mat.depthWrite         = false;
        mat.side               = THREE.DoubleSide;
      } else {
        mat.color.copy(mat._origColor);
        mat.emissive.copy(mat._origEmissive);
        mat.emissiveIntensity  = 0.04;
        mat.transparent        = false;
        mat.opacity            = 1.0;
        mat.depthWrite         = true;
        mat.side               = THREE.FrontSide;
        mat.roughness          = mat._origRoughness || 0.68;
        mat.clearcoat          = 0.10;
        mat.clearcoatRoughness = 0.38;
      }
      mat.needsUpdate = true;
    }
  });

  // Also toggle the cerebellum overlay if it exists
  regionMeshes.forEach(function(m) {
    if (m.userData.regionId === 'cerebellum' && !m.userData.permanent) {
      if (!effectiveVisible) m.visible = false;
    }
  });

  return cerebellumVisible;
}


// ═══════════════════════════════════════════════════════════════════════════════
// BRAINSTEM TOGGLE
// ═══════════════════════════════════════════════════════════════════════════════

function toggleBrainstem(forceState) {
  if (typeof forceState === 'boolean') {
    brainstemVisible = forceState;
  } else {
    brainstemVisible = !brainstemVisible;
  }

  brainstemMeshes.forEach(function(m) {
    m.visible = brainstemVisible;
    if (brainstemVisible) {
      var mat = m.userData.overlayMat;
      if (!mat) return;
      if (glassOn) {
        mat.transparent        = true;
        mat.opacity            = 0.08;
        mat.depthWrite         = false;
        mat.side               = THREE.DoubleSide;
      } else {
        mat.color.copy(mat._origColor);
        mat.emissive.copy(mat._origEmissive);
        mat.emissiveIntensity  = 0.04;
        mat.transparent        = false;
        mat.opacity            = 1.0;
        mat.depthWrite         = true;
        mat.side               = THREE.FrontSide;
        mat.roughness          = mat._origRoughness || 0.68;
        mat.clearcoat          = 0.10;
        mat.clearcoatRoughness = 0.38;
      }
      mat.needsUpdate = true;
    }
  });

  // Also toggle the brainstem overlay if it exists
  regionMeshes.forEach(function(m) {
    if (m.userData.regionId === 'brainstem' && !m.userData.permanent) {
      if (!brainstemVisible) m.visible = false;
    }
  });

  return brainstemVisible;
}


// ═══════════════════════════════════════════════════════════════════════════════
// SUBCORTICAL VISIBILITY
// ═══════════════════════════════════════════════════════════════════════════════

function setSubcorticalVisible(show) {
  subcorticalMeshes.forEach(function(m) {
    if (m.userData.permanent) {
      // Respect cerebellum and brainstem toggles
      if (m.userData.regionId === 'cerebellum') {
        m.visible = show && cerebellumVisible;
      } else if (m.userData.regionId === 'brainstem') {
        m.visible = show && brainstemVisible;
      } else {
        m.visible = show;
      }
    } else {
      if (!show) _hideOverlay(m);
    }
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// RAYCASTER + POINTER INTERACTION
// ═══════════════════════════════════════════════════════════════════════════════

var raycaster = new THREE.Raycaster();
var mouse     = new THREE.Vector2(-10, -10);
var downPos   = null;

function _findNearestRegion(point) {
  // Given a world-space hit point on the cortex, find the closest region by centroid
  var bestId   = null;
  var bestDist = Infinity;
  for (var id in regionCentroids) {
    if (PERMANENT_IDS.has(id)) continue;  // skip brainstem/cerebellum — use direct hit
    var d = regionCentroids[id].distanceTo(point);
    if (d < bestDist) {
      bestDist = d;
      bestId   = id;
    }
  }
  // Only return if reasonably close (within ~1.5 units in mesh space)
  return (bestId && bestDist < 1.5) ? bestId : null;
}

var _visibleCache = [];
var _visibleCacheDirty = true;

function _rayHitRegion() {
  raycaster.setFromCamera(mouse, camera);

  // 1. Check visible overlay meshes first (they have priority)
  // Reuse cached array to avoid per-call allocation
  if (_visibleCacheDirty) {
    _visibleCache = regionMeshes.filter(function(m) { return m.visible; });
    _visibleCacheDirty = false;
  }
  var overlayHits = raycaster.intersectObjects(_visibleCache, false);
  for (var i = 0; i < overlayHits.length; i++) {
    if (!overlayHits[i].object.userData.isOutline) {
      return overlayHits[i].object;
    }
  }

  // 2. If no overlay hit, check hires cortex mesh and find nearest region
  if (hiresMeshes.length) {
    var cortexHits = raycaster.intersectObjects(hiresMeshes, false);
    if (cortexHits.length > 0) {
      var hitPoint = cortexHits[0].point;
      var nearestId = _findNearestRegion(hitPoint);
      if (nearestId) {
        // Return a synthetic "hit object" so callers can read .userData.regionId
        return { userData: { regionId: nearestId, _cortexHit: true } };
      }
    }
  }

  return null;
}

function _setHoverEmissive(regionId, intensity) {
  regionMeshes.forEach(function(m) {
    if (m.userData.regionId !== regionId) return;
    var mat = m.userData.overlayMat;
    if (!mat) return;
    mat.emissiveIntensity = intensity;
    mat.needsUpdate = true;
  });
}

var _lastHoverTime = 0;
var _HOVER_THROTTLE = 50;  // ms — max 20 raycasts/sec instead of unlimited

canvas.addEventListener('pointermove', function(e) {
  var r = canvas.getBoundingClientRect();
  mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
  mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;

  // Skip raycasting while dragging (panning/rotating) or if throttled
  if (downPos) { canvas.style.cursor = 'grabbing'; return; }
  var now = performance.now();
  if (now - _lastHoverTime < _HOVER_THROTTLE) return;
  _lastHoverTime = now;

  var hit = _rayHitRegion();
  var id  = hit ? hit.userData.regionId : null;

  if (id !== hoveredRegionId) {
    // Restore previous hover
    if (hoveredRegionId && hoveredRegionId !== selectedRegionId) {
      regionMeshes.forEach(function(m) {
        if (m.userData.regionId !== hoveredRegionId) return;
        if (m.userData.permanent) {
          _setHoverEmissive(hoveredRegionId, 0.04);
        } else if (!quizMode) {
          _hideOverlay(m);
        }
      });
    }

    hoveredRegionId = id;
    canvas.style.cursor = id ? 'pointer' : 'grab';

    // Notify UI
    if (window.__brainUI && window.__brainUI.hoverRegion) {
      window.__brainUI.hoverRegion(id);
    }

    // Apply new hover highlight
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
          mat.color.copy(col);
          mat.emissive.copy(col);
          mat.emissiveIntensity = 0.20;
          mat.transparent = true;
          mat.opacity = 0.35;
          mat.depthWrite = false;
          mat.needsUpdate = true;
          _showOverlay(m, false);
        }
      });
    }
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
    // This was a click, not a drag
    var r = canvas.getBoundingClientRect();
    mouse.x =  ((e.clientX - r.left) / r.width)  * 2 - 1;
    mouse.y = -((e.clientY - r.top)  / r.height) * 2 + 1;
    var hit = _rayHitRegion();
    if (hit) {
      var rid = hit.userData.regionId;
      if (window.__brainUI && window.__brainUI.openRegion) {
        window.__brainUI.openRegion(rid);
      }
      if (!quizMode) highlightRegion(rid);
    } else {
      // Clicked empty space — deselect
      if (selectedRegionId && !quizMode) {
        resetRegions();
        if (window.__brainUI && window.__brainUI.closeRegion) {
          window.__brainUI.closeRegion();
        }
      }
    }
  }
  downPos = null;
});

canvas.addEventListener('pointerleave', function() {
  mouse.set(-10, -10);
  downPos = null;  // clear stale click position
  if (hoveredRegionId && hoveredRegionId !== selectedRegionId) {
    regionMeshes.forEach(function(m) {
      if (m.userData.regionId !== hoveredRegionId) return;
      if (m.userData.permanent) {
        _setHoverEmissive(hoveredRegionId, 0.04);
      } else if (!quizMode) {
        _hideOverlay(m);
      }
    });
  }
  hoveredRegionId = null;
  if (window.__brainUI && window.__brainUI.hoverRegion) {
    window.__brainUI.hoverRegion(null);
  }
});


// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION LOOP
// ═══════════════════════════════════════════════════════════════════════════════

var animId = null;
var lastTs = 0;

function animate(ts) {
  animId = requestAnimationFrame(animate);
  var dt = Math.min((ts - lastTs) / 1000, 0.05);
  lastTs = ts;

  // Smooth camera transition
  if (camTo) {
    camT = Math.min(camT + dt / CAM_DUR, 1);
    var e = 1 - Math.pow(1 - camT, 3);  // ease-out cubic
    camera.position.lerpVectors(camFrom, camTo, e);
    if (targetTo) {
      controls.target.lerpVectors(targetFrom, targetTo, e);
    }
    if (camT >= 1) {
      camTo = null;
      targetTo = null;
      controls.enabled = true;  // re-enable OrbitControls
    }
    controls.update();
  } else {
    controls.update();
  }

  composer.render();
}


// ═══════════════════════════════════════════════════════════════════════════════
// RESIZE + MOUNT / UNMOUNT
// ═══════════════════════════════════════════════════════════════════════════════

var mountedContainer = null;

var resizeObserver = new ResizeObserver(function() {
  if (!mountedContainer) return;
  var w = mountedContainer.clientWidth;
  var h = mountedContainer.clientHeight || Math.round(w / 1.54);
  renderer.setSize(w, h);
  composer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
});

function mount(container) {
  if (typeof container === 'string') container = document.querySelector(container);
  if (!container) return;
  if (mountedContainer === container) {
    if (!animId) animate(0);
    return;
  }
  if (mountedContainer) resizeObserver.unobserve(mountedContainer);
  mountedContainer = container;
  container.appendChild(canvas);
  resizeObserver.observe(container);
  var w = container.clientWidth  || window.innerWidth - 256;
  var h = container.clientHeight || window.innerHeight - 52;
  renderer.setSize(w, h);
  composer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  if (!animId) animate(0);
  setCameraView('lateral');
}

function unmount() {
  if (animId) {
    cancelAnimationFrame(animId);
    animId = null;
  }
  if (mountedContainer) {
    resizeObserver.unobserve(mountedContainer);
    if (canvas.parentNode === mountedContainer) {
      mountedContainer.removeChild(canvas);
    }
    mountedContainer = null;
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════════════════════

window.__brain3d = {
  mount:               mount,
  unmount:             unmount,
  setCameraView:       setCameraView,
  focusRegion:         focusRegion,
  CAMERA_VIEWS:        CAMERA_VIEWS,
  highlightRegion:     highlightRegion,
  enterQuizMode:       enterQuizMode,
  exitQuizCamera:      exitQuizCamera,
  dimAllRegions:       dimAllRegions,
  resetRegions:        resetRegions,
  toggleGlass:         toggleGlass,
  toggleSplit:         toggleSplit,
  toggleCerebellum:    toggleCerebellum,
  toggleBrainstem:     toggleBrainstem,
  setSubcorticalVisible: setSubcorticalVisible,
  regionMeshes:        regionMeshes,
  corticalMeshes:      corticalMeshes,
  subcorticalMeshes:   subcorticalMeshes,
  regionCentroids:     regionCentroids,
  regionCameraPos:     regionCameraPos,
  ready:               _readyPromise,

  // State getters
  isGlassOn:           function() { return glassOn; },
  isSplitOn:           function() { return splitOn; },
  isCerebellumVisible: function() { return cerebellumVisible; },
  isBrainstemVisible:  function() { return brainstemVisible; },
  getSelectedRegion:   function() { return selectedRegionId; },
};

// Auto-mount if target element exists
var _autoMount = document.getElementById('brain-stage') || document.getElementById('brain-container-3d');
if (_autoMount) mount(_autoMount);
