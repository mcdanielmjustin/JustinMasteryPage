/**
 * patient-avatar-v2.js — Patient Encounter 2.0 Avatar Engine
 *
 * Three.js-powered 3D avatar system for the Patient Encounter 2.0 module.
 * Matches the full pipeline quality of brain-3d-v3.js:
 *   - WebGLRenderer with ACESFilmicToneMapping + SRGBColorSpace
 *   - PMREM procedural studio environment map (skin-tone adapted)
 *   - 5-point lighting: key, fill, rim, under-bounce, hemisphere + ambient
 *   - MeshPhysicalMaterial for skin (clearcoat, sheen, SSS approximation)
 *   - EffectComposer: GTAOPass (SSAO) + UnrealBloomPass + OutputPass
 *   - GLTFLoader + DRACOLoader for Ready Player Me .glb avatars
 *   - 52 ARKit blend shapes driving 13 clinical emotion states
 *   - Smooth lerp transitions between emotion states
 *   - Idle breathing animation + speaking jaw animation
 *
 * Public API: window.__PatientAvatar
 *   .mount(container, options)         — inject canvas, start render loop
 *   .unmount()                         — cleanup GPU resources
 *   .loadDemographic(type)             — load GLB, returns Promise
 *   .setEmotion(emotion)               — set blend shape target state
 *   .setSpeaking(bool)                 — start/stop jaw animation
 *   .resize(w, h)                      — update renderer size
 *   .ready                             — Promise<void> resolves after mount
 *
 * GLB asset path: data/avatars/{type}.glb
 * Types: adult_male, adult_female, young_male, young_female,
 *        adolescent_male, adolescent_female, elder_male, elder_female
 *
 * See PLAN_patient_encounter_v2.md for full implementation notes.
 */

import * as THREE          from 'three';
import { OrbitControls }   from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }      from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader }     from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer }  from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass }      from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass }        from 'three/addons/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass }      from 'three/addons/postprocessing/OutputPass.js';

console.log('[patient-avatar-v2] Engine loaded, Three.js r' + THREE.REVISION);


// ═══════════════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════════

var ASSET_VERSION = '20260305a';

var GLB_BASE = 'data/avatars/';

var DEMO_TYPES = [
  'adult_male', 'adult_female',
  'young_male', 'young_female',
  'adolescent_male', 'adolescent_female',
  'elder_male', 'elder_female',
];

// 52 ARKit blend shape targets per emotion state.
// All unlisted shapes default to 0 (reset by setEmotion).
var EMOTION_BLEND_SHAPES = {
  idle: {},

  speaking: {
    // jawOpen is driven by _animateJaw during speaking — kept low here
    mouthSmileLeft:  0.08,
    mouthSmileRight: 0.08,
  },

  concerned: {
    browDownLeft:    0.45,
    browDownRight:   0.45,
    browInnerUp:     0.35,
    mouthFrownLeft:  0.20,
    mouthFrownRight: 0.20,
    mouthPressLeft:  0.10,
    mouthPressRight: 0.10,
  },

  anxious: {
    browInnerUp:       0.55,
    browOuterUpLeft:   0.20,
    browOuterUpRight:  0.20,
    eyeWideLeft:       0.30,
    eyeWideRight:      0.30,
    mouthStretchLeft:  0.15,
    mouthStretchRight: 0.15,
    cheekPuff:         0.08,
  },

  distressed: {
    browDownLeft:    0.70,
    browDownRight:   0.70,
    browInnerUp:     0.45,
    mouthFrownLeft:  0.55,
    mouthFrownRight: 0.55,
    eyeSquintLeft:   0.30,
    eyeSquintRight:  0.30,
    noseSneerLeft:   0.20,
    noseSneerRight:  0.20,
    jawForward:      0.10,
  },

  confused: {
    browDownLeft:    0.50,
    browOuterUpRight: 0.55,
    eyeSquintLeft:   0.20,
    mouthLeft:       0.15,
    mouthPressLeft:  0.15,
    mouthPressRight: 0.15,
    cheekSquintRight: 0.10,
  },

  hopeful: {
    browOuterUpLeft:  0.30,
    browOuterUpRight: 0.30,
    mouthSmileLeft:   0.28,
    mouthSmileRight:  0.28,
    cheekSquintLeft:  0.18,
    cheekSquintRight: 0.18,
    eyeSquintLeft:    0.12,
    eyeSquintRight:   0.12,
  },

  relieved: {
    mouthSmileLeft:   0.42,
    mouthSmileRight:  0.42,
    cheekSquintLeft:  0.32,
    cheekSquintRight: 0.32,
    eyeSquintLeft:    0.18,
    eyeSquintRight:   0.18,
    browOuterUpLeft:  0.12,
    browOuterUpRight: 0.12,
  },

  proud: {
    mouthSmileLeft:   0.30,
    mouthSmileRight:  0.30,
    cheekSquintLeft:  0.22,
    cheekSquintRight: 0.22,
    browOuterUpLeft:  0.18,
    browOuterUpRight: 0.18,
    mouthShrugUpper:  0.10,
  },

  embarrassed: {
    mouthFrownLeft:   0.22,
    mouthFrownRight:  0.22,
    eyeLookDownLeft:  0.40,
    eyeLookDownRight: 0.40,
    browInnerUp:      0.28,
    cheekSquintLeft:  0.18,
    cheekSquintRight: 0.18,
    mouthPucker:      0.10,
  },

  tearful: {
    browInnerUp:       0.72,
    browDownLeft:      0.25,
    browDownRight:     0.25,
    mouthFrownLeft:    0.45,
    mouthFrownRight:   0.45,
    mouthPucker:       0.22,
    mouthStretchLeft:  0.12,
    mouthStretchRight: 0.12,
    eyeBlinkLeft:      0.20,
    eyeBlinkRight:     0.20,
  },

  engaged: {
    browOuterUpLeft:  0.22,
    browOuterUpRight: 0.22,
    eyeWideLeft:      0.18,
    eyeWideRight:     0.18,
    mouthSmileLeft:   0.12,
    mouthSmileRight:  0.12,
    eyeLookUpLeft:    0.10,
    eyeLookUpRight:   0.10,
  },

  flat: {
    eyeSquintLeft:  0.10,
    eyeSquintRight: 0.10,
  },
};

// All known ARKit shape names — used to zero out unset shapes on emotion change
var ALL_ARKIT_SHAPES = [
  'browDownLeft','browDownRight','browInnerUp','browOuterUpLeft','browOuterUpRight',
  'cheekPuff','cheekSquintLeft','cheekSquintRight',
  'eyeBlinkLeft','eyeBlinkRight',
  'eyeLookDownLeft','eyeLookDownRight','eyeLookInLeft','eyeLookInRight',
  'eyeLookOutLeft','eyeLookOutRight','eyeLookUpLeft','eyeLookUpRight',
  'eyeSquintLeft','eyeSquintRight','eyeWideLeft','eyeWideRight',
  'jawForward','jawLeft','jawOpen','jawRight',
  'mouthClose','mouthDimpleLeft','mouthDimpleRight',
  'mouthFrownLeft','mouthFrownRight','mouthFunnel',
  'mouthLeft','mouthLowerDownLeft','mouthLowerDownRight',
  'mouthPressLeft','mouthPressRight','mouthPucker','mouthRight',
  'mouthRollLower','mouthRollUpper','mouthShrugLower','mouthShrugUpper',
  'mouthSmileLeft','mouthSmileRight','mouthStretchLeft','mouthStretchRight',
  'mouthUpperUpLeft','mouthUpperUpRight',
  'noseSneerLeft','noseSneerRight',
  'tongueOut',
];


// ═══════════════════════════════════════════════════════════════════════════════
// MODULE STATE
// ═══════════════════════════════════════════════════════════════════════════════

var _renderer = null;
var _scene = null;
var _camera = null;
var _controls = null;
var _composer = null;
var _envMap = null;
var _clock = null;
var _animFrameId = null;
var _resizeObserver = null;
var _container = null;
var _canvasW = 320;
var _canvasH = 400;

var _loader = null;
var _avatarGroup = null;   // holds current loaded avatar GLB
var _headMesh = null;      // Wolf3D_Head mesh (has blend shapes)
var _placeholderMesh = null;  // fallback sphere shown while no GLB

var _currentDemographic = null;
var _currentEmotion = 'idle';
var _isSpeaking = false;
var _targetInfluences = {};   // emotion blend shape targets (pre-multiplied to 0 for missing shapes)
var _breathPhase = 0;
var _jawPhase = 0;
var _blinkTimer = 0;
var _nextBlink = 3.5;  // seconds until next blink

var _readyResolve = null;
var _readyReject = null;


// ═══════════════════════════════════════════════════════════════════════════════
// ENVIRONMENT MAP — warm studio for skin tones
// ═══════════════════════════════════════════════════════════════════════════════

function _buildEnvMap() {
  var pmrem = new THREE.PMREMGenerator(_renderer);
  pmrem.compileCubemapShader();
  var envScene = new THREE.Scene();

  // Sky dome — warm neutral studio ceiling
  envScene.add(new THREE.Mesh(
    new THREE.SphereGeometry(10, 32, 16),
    new THREE.MeshBasicMaterial({ color: 0x3A3530, side: THREE.BackSide })
  ));

  // Key area — warm 3200K tungsten overhead (dominant)
  var keyArea = new THREE.Mesh(
    new THREE.PlaneGeometry(6, 6),
    new THREE.MeshBasicMaterial({ color: 0x9A7055 })
  );
  keyArea.position.set(2, 8, 3);
  keyArea.rotation.x = Math.PI / 2;
  envScene.add(keyArea);

  // Fill area — cool daylight from upper left
  var fillArea = new THREE.Mesh(
    new THREE.PlaneGeometry(4, 4),
    new THREE.MeshBasicMaterial({ color: 0x405868 })
  );
  fillArea.position.set(-6, 3, 2);
  fillArea.lookAt(0, 0, 0);
  envScene.add(fillArea);

  // Rim area — warm hair light from rear
  var rimArea = new THREE.Mesh(
    new THREE.PlaneGeometry(4, 3),
    new THREE.MeshBasicMaterial({ color: 0x704838 })
  );
  rimArea.position.set(0, 5, -5);
  rimArea.lookAt(0, 0, 0);
  envScene.add(rimArea);

  // Ground plane — dark warm floor (desk/floor bounce)
  var groundPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(20, 20),
    new THREE.MeshBasicMaterial({ color: 0x201510 })
  );
  groundPlane.position.set(0, -9, 0);
  groundPlane.rotation.x = -Math.PI / 2;
  envScene.add(groundPlane);

  // Accent sphere — catchlight (round softbox highlight)
  var accent = new THREE.Mesh(
    new THREE.SphereGeometry(0.4, 8, 8),
    new THREE.MeshBasicMaterial({ color: 0xFFEECC })
  );
  accent.position.set(4, 7, 4);
  envScene.add(accent);

  _envMap = pmrem.fromScene(envScene, 0.04).texture;
  _envMap.colorSpace = THREE.SRGBColorSpace;
  _scene.environment = _envMap;
  pmrem.dispose();
}


// ═══════════════════════════════════════════════════════════════════════════════
// LIGHTING — 5-point face-optimized setup
// ═══════════════════════════════════════════════════════════════════════════════

function _buildLights() {
  // Key light — warm 3200K from upper right front (creates facial depth)
  var keyLight = new THREE.DirectionalLight(0xFFF0E8, 2.4);
  keyLight.position.set(3, 5, 3);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width  = 1024;
  keyLight.shadow.mapSize.height = 1024;
  keyLight.shadow.bias = -0.0003;
  keyLight.shadow.camera.near = 0.5;
  keyLight.shadow.camera.far  = 20;
  keyLight.shadow.camera.left   = -2;
  keyLight.shadow.camera.right  =  2;
  keyLight.shadow.camera.top    =  2;
  keyLight.shadow.camera.bottom = -2;
  _scene.add(keyLight);

  // Fill light — cool daylight from upper left (opens shadows)
  var fillLight = new THREE.DirectionalLight(0xD0E8FF, 0.60);
  fillLight.position.set(-3, 2, 2);
  _scene.add(fillLight);

  // Rim / hair light — warm backlight from upper rear (separates hair from bg)
  var rimLight = new THREE.DirectionalLight(0xFFDDB0, 0.80);
  rimLight.position.set(0, 6, -4);
  _scene.add(rimLight);

  // Under light — subtle warm bounce from below (desk/lap reflection)
  var underLight = new THREE.DirectionalLight(0xFFE8C0, 0.15);
  underLight.position.set(0, -2, 2);
  _scene.add(underLight);

  // Hemisphere + ambient base fill
  _scene.add(new THREE.HemisphereLight(0xD8DDE8, 0x3A2010, 0.35));
  _scene.add(new THREE.AmbientLight(0xFFF0E8, 0.10));
}


// ═══════════════════════════════════════════════════════════════════════════════
// POST-PROCESSING — GTAOPass + UnrealBloomPass + OutputPass
// ═══════════════════════════════════════════════════════════════════════════════

function _buildComposer() {
  _composer = new EffectComposer(_renderer);
  _composer.addPass(new RenderPass(_scene, _camera));

  // SSAO — adds contact shadows under chin, in eye sockets, around ears
  var gtaoPass = new GTAOPass(_scene, _camera, _canvasW, _canvasH);
  gtaoPass.output = GTAOPass.OUTPUT.Default;
  gtaoPass.updateGtaoMaterial({
    radius: 0.4,
    distanceExponent: 2,
    thickness: 1.5,
    samples: 8,
  });
  gtaoPass.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3 });
  _composer.addPass(gtaoPass);

  // Bloom — subtle wet-eye highlight and skin specular
  var bloomPass = new UnrealBloomPass(
    new THREE.Vector2(_canvasW, _canvasH),
    0.08,   // strength — very subtle
    0.4,    // radius
    0.90    // threshold — only sharpest specular catches bloom
  );
  _composer.addPass(bloomPass);

  // Output — tone mapping + color space conversion
  _composer.addPass(new OutputPass());
}


// ═══════════════════════════════════════════════════════════════════════════════
// SCENE GEOMETRY — therapy room environment
// ═══════════════════════════════════════════════════════════════════════════════

function _buildScene() {
  // Floor — polished dark wood
  var floor = new THREE.Mesh(
    new THREE.PlaneGeometry(8, 8),
    new THREE.MeshPhysicalMaterial({
      color: 0x2A1E14, roughness: 0.55, metalness: 0.0,
      envMap: _envMap, envMapIntensity: 0.04,
    })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  _scene.add(floor);

  // Back wall — muted grey-green (therapy office color)
  var wall = new THREE.Mesh(
    new THREE.PlaneGeometry(8, 6),
    new THREE.MeshPhysicalMaterial({
      color: 0x3A4035, roughness: 0.95, metalness: 0.0,
    })
  );
  wall.position.set(0, 3, -2.2);
  wall.receiveShadow = true;
  _scene.add(wall);

  // Simple chair — box geometry placeholder until chair.glb is available
  var seatMat = new THREE.MeshPhysicalMaterial({
    color: 0x2A2030, roughness: 0.85, metalness: 0.0,
    envMap: _envMap, envMapIntensity: 0.02,
  });
  // Seat cushion
  var seat = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.08, 0.50), seatMat);
  seat.position.set(0, 0.48, 0.05);
  seat.receiveShadow = true;
  _scene.add(seat);
  // Back rest
  var back = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.65, 0.07), seatMat);
  back.position.set(0, 0.9, -0.20);
  back.receiveShadow = true;
  _scene.add(back);
  // Chair legs
  var legMat = new THREE.MeshPhysicalMaterial({
    color: 0x1A1418, roughness: 0.7, metalness: 0.25,
  });
  [[-0.22, -0.25], [0.22, -0.25], [-0.22, 0.25], [0.22, 0.25]].forEach(function(pos) {
    var leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.5, 8), legMat);
    leg.position.set(pos[0], 0.25, pos[1]);
    _scene.add(leg);
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// PLACEHOLDER — shown when no GLB is available
// ═══════════════════════════════════════════════════════════════════════════════

function _buildPlaceholder() {
  if (_placeholderMesh) {
    _scene.remove(_placeholderMesh);
    _placeholderMesh.geometry.dispose();
    _placeholderMesh.material.dispose();
  }
  var geo = new THREE.SphereGeometry(0.18, 32, 32);
  var mat = new THREE.MeshPhysicalMaterial({
    color: 0xD4AA90, roughness: 0.65, metalness: 0.0,
    clearcoat: 0.15, clearcoatRoughness: 0.45,
    sheen: 0.3, sheenColor: new THREE.Color(0xFFCCAA),
    envMap: _envMap, envMapIntensity: 0.08,
  });
  _placeholderMesh = new THREE.Mesh(geo, mat);
  _placeholderMesh.position.set(0, 1.55, 0);
  _placeholderMesh.castShadow = true;
  _scene.add(_placeholderMesh);
  console.log('[patient-avatar-v2] Showing placeholder sphere (no GLB loaded)');
}


// ═══════════════════════════════════════════════════════════════════════════════
// MATERIAL ASSIGNMENT — applied to all GLB child meshes after load
// ═══════════════════════════════════════════════════════════════════════════════

function _applyMaterials(gltf) {
  var skinMat = new THREE.MeshPhysicalMaterial({
    roughness:            0.65,
    metalness:            0.0,
    clearcoat:            0.15,
    clearcoatRoughness:   0.45,
    sheen:                0.30,
    sheenRoughness:       0.60,
    sheenColor:           new THREE.Color(0xFFCCAA),
    transmission:         0.04,
    thickness:            0.8,
    ior:                  1.38,
    attenuationColor:     new THREE.Color(0xFF8866),
    attenuationDistance:  0.4,
    envMap:               _envMap,
    envMapIntensity:      0.08,
    side:                 THREE.FrontSide,
  });

  var eyeMat = new THREE.MeshPhysicalMaterial({
    roughness:          0.02,
    metalness:          0.0,
    clearcoat:          1.0,
    clearcoatRoughness: 0.0,
    transmission:       0.12,
    ior:                1.50,
    envMap:             _envMap,
    envMapIntensity:    0.30,
  });

  var hairMat = new THREE.MeshPhysicalMaterial({
    roughness:      0.55,
    metalness:      0.0,
    sheen:          0.6,
    sheenRoughness: 0.4,
    sheenColor:     new THREE.Color(0x8B6040),
    envMap:         _envMap,
    envMapIntensity: 0.05,
  });

  var teethMat = new THREE.MeshPhysicalMaterial({
    roughness:         0.35,
    metalness:         0.0,
    emissive:          new THREE.Color(0xF8F4F0),
    emissiveIntensity: 0.04,
    envMap:            _envMap,
    envMapIntensity:   0.06,
  });

  var clothMat = new THREE.MeshPhysicalMaterial({
    roughness:      0.85,
    metalness:      0.0,
    sheen:          0.2,
    sheenRoughness: 0.8,
    sheenColor:     new THREE.Color(0xAAAAAA),
    envMap:         _envMap,
    envMapIntensity: 0.02,
  });

  gltf.scene.traverse(function(child) {
    if (!child.isMesh) return;

    child.castShadow    = true;
    child.receiveShadow = true;

    var origMap = child.material ? child.material.map : null;
    if (origMap) origMap.colorSpace = THREE.SRGBColorSpace;

    var n = child.name.toLowerCase();
    var mat;

    if (n.includes('skin') || n.includes('body') || n.includes('head')) {
      mat = skinMat.clone();
      if (origMap) mat.map = origMap;
    } else if (n.includes('eye') || n.includes('cornea')) {
      mat = eyeMat.clone();
      if (origMap) mat.map = origMap;
    } else if (n.includes('hair') || n.includes('brow')) {
      mat = hairMat.clone();
      if (origMap) {
        mat.map = origMap;
        // Rough guess at hair color from texture — override sheen accordingly
      }
    } else if (n.includes('teeth') || n.includes('mouth')) {
      mat = teethMat.clone();
      if (origMap) mat.map = origMap;
    } else if (n.includes('outfit') || n.includes('shirt') || n.includes('cloth')) {
      mat = clothMat.clone();
      if (origMap) mat.map = origMap;
    } else {
      // Default — use skin-like diffuse with original texture
      mat = new THREE.MeshPhysicalMaterial({
        map: origMap, roughness: 0.7, metalness: 0.0,
        envMap: _envMap, envMapIntensity: 0.04,
      });
    }

    child.material = mat;
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// GLB LOADING
// ═══════════════════════════════════════════════════════════════════════════════

function _loadGLB(type) {
  return new Promise(function(resolve, reject) {
    if (DEMO_TYPES.indexOf(type) === -1) {
      console.warn('[patient-avatar-v2] Unknown demographic type:', type, '— using adult_male');
      type = 'adult_male';
    }

    var path = GLB_BASE + type + '.glb?v=' + ASSET_VERSION;
    console.log('[patient-avatar-v2] Loading:', path);

    _loader.load(
      path,
      function(gltf) {
        // Remove previous avatar
        if (_avatarGroup) {
          _scene.remove(_avatarGroup);
          _avatarGroup = null;
          _headMesh = null;
        }
        if (_placeholderMesh) {
          _scene.remove(_placeholderMesh);
        }

        _applyMaterials(gltf);

        // Find the head mesh with blend shapes
        gltf.scene.traverse(function(node) {
          if (node.isMesh && node.morphTargetDictionary &&
              Object.keys(node.morphTargetDictionary).length > 0) {
            _headMesh = node;
            console.log('[patient-avatar-v2] Head mesh found:', node.name,
              '—', Object.keys(node.morphTargetDictionary).length, 'blend shapes');
            // Log all blend shape names for debugging
            console.log('[patient-avatar-v2] Blend shapes:', Object.keys(node.morphTargetDictionary).join(', '));
          }
        });

        _avatarGroup = gltf.scene;
        // Center avatar at origin, standing height so seated posture looks right
        // (camera crop shows head/chest only — see PLAN_patient_encounter_v2.md)
        _scene.add(_avatarGroup);

        _currentDemographic = type;
        // Re-apply current emotion to new avatar
        _setTargetInfluences(_currentEmotion);

        console.log('[patient-avatar-v2] Loaded demographic:', type);
        resolve();
      },
      function(xhr) {
        if (xhr.total > 0) {
          var pct = Math.round((xhr.loaded / xhr.total) * 100);
          console.log('[patient-avatar-v2] Loading ' + type + '... ' + pct + '%');
        }
      },
      function(err) {
        console.warn('[patient-avatar-v2] GLB not found for ' + type + ':', err.message || err);
        // Try fallback to adult_male if not already trying it
        if (type !== 'adult_male') {
          console.log('[patient-avatar-v2] Falling back to adult_male.glb');
          _loadGLB('adult_male').then(resolve).catch(function() {
            _buildPlaceholder();
            resolve();  // resolve (not reject) so encounter can continue
          });
        } else {
          _buildPlaceholder();
          resolve();  // graceful degradation
        }
      }
    );
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// EMOTION SYSTEM — blend shape lerp
// ═══════════════════════════════════════════════════════════════════════════════

function _setTargetInfluences(emotion) {
  var map = EMOTION_BLEND_SHAPES[emotion] || EMOTION_BLEND_SHAPES.idle;

  // Zero all shapes first, then apply targets
  _targetInfluences = {};
  ALL_ARKIT_SHAPES.forEach(function(name) {
    _targetInfluences[name] = map[name] !== undefined ? map[name] : 0;
  });

  // During speaking state, jawOpen is handled by _animateJaw — zero it here
  if (emotion === 'speaking') {
    _targetInfluences['jawOpen'] = 0;
  }
}

function _lerpEmotions(dt) {
  if (!_headMesh || !_headMesh.morphTargetDictionary) return;
  var dict = _headMesh.morphTargetDictionary;
  var infl = _headMesh.morphTargetInfluences;
  var lerpRate = 0.08;

  for (var name in _targetInfluences) {
    var idx = dict[name];
    if (idx === undefined) continue;
    infl[idx] = THREE.MathUtils.lerp(infl[idx], _targetInfluences[name], lerpRate);
  }
}

function _animateJaw(dt) {
  if (!_isSpeaking || !_headMesh || !_headMesh.morphTargetDictionary) return;
  _jawPhase += dt * 8.0;   // ~8 open/close cycles per second
  var jawIdx = _headMesh.morphTargetDictionary['jawOpen'];
  if (jawIdx === undefined) return;
  // Natural jaw: base 0.08 + sinusoidal variation
  _headMesh.morphTargetInfluences[jawIdx] =
    0.08 + Math.sin(_jawPhase) * 0.12 + Math.sin(_jawPhase * 1.7) * 0.05;
}

function _animateBreathing(dt) {
  _breathPhase += dt * 0.72;   // ≈ 1 breath per 8.7 seconds
  if (_avatarGroup) {
    _avatarGroup.position.y = Math.sin(_breathPhase) * 0.004;
    _avatarGroup.rotation.z = Math.sin(_breathPhase * 0.5) * 0.003;
  }
  if (_placeholderMesh) {
    _placeholderMesh.position.y = 1.55 + Math.sin(_breathPhase) * 0.004;
  }
}

function _animateBlink(dt) {
  if (!_headMesh || !_headMesh.morphTargetDictionary) return;
  _blinkTimer += dt;
  if (_blinkTimer < _nextBlink) return;

  // Trigger blink — quick 120ms close then reopen
  _blinkTimer = 0;
  _nextBlink = 3.0 + Math.random() * 4.0;  // 3-7 seconds between blinks

  var lIdx = _headMesh.morphTargetDictionary['eyeBlinkLeft'];
  var rIdx = _headMesh.morphTargetDictionary['eyeBlinkRight'];
  if (lIdx === undefined || rIdx === undefined) return;

  // Override target for a blink duration — animation handles it
  var origL = _targetInfluences['eyeBlinkLeft']  || 0;
  var origR = _targetInfluences['eyeBlinkRight'] || 0;

  _targetInfluences['eyeBlinkLeft']  = 0.95;
  _targetInfluences['eyeBlinkRight'] = 0.95;
  setTimeout(function() {
    _targetInfluences['eyeBlinkLeft']  = origL;
    _targetInfluences['eyeBlinkRight'] = origR;
  }, 120);
}


// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION LOOP
// ═══════════════════════════════════════════════════════════════════════════════

function _animate() {
  _animFrameId = requestAnimationFrame(_animate);
  var dt = _clock.getDelta();
  if (_controls) _controls.update();
  _animateBreathing(dt);
  _lerpEmotions(dt);
  _animateBlink(dt);
  if (_isSpeaking) _animateJaw(dt);
  _composer.render();
}


// ═══════════════════════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * mount(container, options)
 * Initializes the Three.js renderer inside the given DOM container.
 * options: { width, height, controls }
 *   - width/height: initial canvas size (default 320×400)
 *   - controls: true|false — enable orbit controls (default false for production)
 */
function mount(container, options) {
  options = options || {};
  _container = container;
  _canvasW = options.width  || container.offsetWidth  || 320;
  _canvasH = options.height || container.offsetHeight || 400;

  // ── Renderer ──
  try {
    _renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  } catch (e) {
    console.error('[patient-avatar-v2] WebGL unavailable:', e.message);
    if (_readyReject) _readyReject(e);
    return;
  }
  _renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  _renderer.setSize(_canvasW, _canvasH);
  _renderer.toneMapping = THREE.ACESFilmicToneMapping;
  _renderer.toneMappingExposure = 1.15;
  _renderer.outputColorSpace = THREE.SRGBColorSpace;
  _renderer.shadowMap.enabled = true;
  _renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  _renderer.domElement.style.cssText = 'display:block; border-radius:16px; width:100%; height:auto;';
  container.appendChild(_renderer.domElement);

  // ── Scene ──
  _scene = new THREE.Scene();
  _scene.background = new THREE.Color(0x0A0B10);
  _scene.fog = new THREE.Fog(0x0A0B10, 8, 16);

  // ── Camera ──
  _camera = new THREE.PerspectiveCamera(35, _canvasW / _canvasH, 0.1, 30);
  // Portrait framing: head + upper chest, eye-level for seated patient
  _camera.position.set(0, 1.5, 3.2);
  _camera.lookAt(0, 1.55, 0);

  // ── Optional orbit controls ──
  if (options.controls !== false) {
    _controls = new OrbitControls(_camera, _renderer.domElement);
    _controls.enableDamping  = true;
    _controls.dampingFactor  = 0.07;
    _controls.minDistance    = 1.5;
    _controls.maxDistance    = 5.0;
    _controls.minPolarAngle  = 0.8;
    _controls.maxPolarAngle  = 1.6;
    _controls.enablePan      = false;
    _controls.target.set(0, 1.4, 0);
    _controls.update();
  }

  // ── Clock ──
  _clock = new THREE.Clock();

  // ── Build pipeline ──
  _buildEnvMap();
  _buildLights();
  _buildComposer();
  _buildScene();

  // ── GLTF Loader ──
  var dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath('./vendor/three/examples/jsm/libs/draco/gltf/');
  _loader = new GLTFLoader();
  _loader.setDRACOLoader(dracoLoader);

  // ── Show placeholder until GLB loads ──
  _buildPlaceholder();

  // ── Resize observer ──
  if (typeof ResizeObserver !== 'undefined') {
    _resizeObserver = new ResizeObserver(function(entries) {
      if (!entries[0]) return;
      var w = Math.round(entries[0].contentRect.width);
      var h = Math.round(w * (_canvasH / _canvasW));
      if (w > 0 && h > 0) resize(w, h);
    });
    _resizeObserver.observe(container);
  }

  // ── Start loop ──
  _animate();

  console.log('[patient-avatar-v2] Mounted, canvas', _canvasW + 'x' + _canvasH);
  if (_readyResolve) _readyResolve();
}

/**
 * unmount()
 * Stop the render loop, remove canvas, free GPU resources.
 */
function unmount() {
  if (_animFrameId !== null) {
    cancelAnimationFrame(_animFrameId);
    _animFrameId = null;
  }
  if (_resizeObserver) {
    _resizeObserver.disconnect();
    _resizeObserver = null;
  }
  if (_controls) {
    _controls.dispose();
    _controls = null;
  }
  if (_composer) {
    _composer.dispose();
    _composer = null;
  }
  if (_renderer) {
    if (_container && _renderer.domElement.parentNode === _container) {
      _container.removeChild(_renderer.domElement);
    }
    _renderer.dispose();
    _renderer = null;
  }
  _scene = null;
  _camera = null;
  _avatarGroup = null;
  _headMesh = null;
  _placeholderMesh = null;
  _envMap = null;
  console.log('[patient-avatar-v2] Unmounted');
}

/**
 * loadDemographic(type)
 * Load a Ready Player Me GLB avatar for the given demographic type.
 * Returns Promise<void>.
 */
function loadDemographic(type) {
  if (!_loader) {
    console.warn('[patient-avatar-v2] loadDemographic called before mount()');
    return Promise.resolve();
  }
  return _loadGLB(type || 'adult_male');
}

/**
 * setEmotion(emotion)
 * Set the avatar's facial expression. Transitions smoothly via blend shape lerp.
 * Valid emotions: idle, speaking, concerned, anxious, distressed, confused,
 *                 hopeful, relieved, proud, embarrassed, tearful, engaged, flat
 */
function setEmotion(emotion) {
  if (!EMOTION_BLEND_SHAPES[emotion]) {
    console.warn('[patient-avatar-v2] Unknown emotion:', emotion, '— defaulting to idle');
    emotion = 'idle';
  }
  _currentEmotion = emotion;
  _setTargetInfluences(emotion);
}

/**
 * setSpeaking(bool)
 * Enable/disable the jaw speaking animation.
 * Call setSpeaking(true) when typewriter starts, setSpeaking(false) when it ends.
 */
function setSpeaking(isSpeaking) {
  _isSpeaking = !!isSpeaking;
  if (!isSpeaking && _headMesh && _headMesh.morphTargetDictionary) {
    // Return jaw to rest on stop
    var jawIdx = _headMesh.morphTargetDictionary['jawOpen'];
    if (jawIdx !== undefined) {
      _targetInfluences['jawOpen'] = 0;
    }
  }
}

/**
 * resize(w, h)
 * Update renderer and composer to new dimensions.
 */
function resize(w, h) {
  if (!_renderer) return;
  _canvasW = w;
  _canvasH = h;
  _renderer.setSize(w, h);
  if (_camera) {
    _camera.aspect = w / h;
    _camera.updateProjectionMatrix();
  }
  if (_composer) _composer.setSize(w, h);
}


// ═══════════════════════════════════════════════════════════════════════════════
// READY PROMISE
// ═══════════════════════════════════════════════════════════════════════════════

var _readyPromise = new Promise(function(resolve, reject) {
  _readyResolve = resolve;
  _readyReject  = reject;
});


// ═══════════════════════════════════════════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════════════════════════════════════════

window.__PatientAvatar = {
  mount:           mount,
  unmount:         unmount,
  loadDemographic: loadDemographic,
  setEmotion:      setEmotion,
  setSpeaking:     setSpeaking,
  resize:          resize,
  ready:           _readyPromise,
  // Expose for debugging
  _getScene:       function() { return _scene; },
  _getRenderer:    function() { return _renderer; },
};

console.log('[patient-avatar-v2] window.__PatientAvatar registered');
