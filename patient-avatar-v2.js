/**
 * patient-avatar-v2.js — Patient Encounter 2.0 Avatar Engine
 *
 * Procedural humanoid built entirely from Three.js geometry.
 * Ready Player Me was discontinued Jan 31 2026 — no GLB files required.
 *
 * Rendering pipeline matches brain-3d-v3.js quality:
 *   - WebGLRenderer, ACESFilmicToneMapping, SRGBColorSpace
 *   - PMREM procedural studio environment map (skin-tone adapted)
 *   - 5-point lighting: key, fill, rim, under-bounce, hemisphere + ambient
 *   - MeshPhysicalMaterial (clearcoat, sheen, SSS) on all skin surfaces
 *   - EffectComposer: GTAOPass + UnrealBloomPass + OutputPass
 *
 * Avatar system:
 *   - Full seated humanoid from sphere/cylinder/capsule geometry
 *   - 8 demographic configs (skin tone, hair color, clothing color, eye color)
 *   - 13 clinical emotion states via head/body transform lerp
 *   - Speaking jaw animation via _jawGroup rotation
 *   - Idle breathing animation + random eye blink
 *
 * Public API: window.__PatientAvatar
 *   .mount(container, options)       — inject canvas, start render loop
 *   .unmount()                       — cleanup GPU resources
 *   .loadDemographic(type)           — switch avatar appearance, returns Promise
 *   .setEmotion(emotion)             — set posture/expression state
 *   .setSpeaking(bool)               — start/stop jaw animation
 *   .resize(w, h)                    — update renderer size
 *   .ready                           — Promise<void> resolves after mount
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

// Appearance config per demographic type: skin, hair, clothing, iris color
var DEMOGRAPHIC_CONFIGS = {
  adult_male:        { skin: 0xC8886A, hair: 0x2A1808, cloth: 0x252E3A, eye: 0x3A5068 },
  adult_female:      { skin: 0xD89A7C, hair: 0x1A0E08, cloth: 0x302838, eye: 0x4A6858 },
  young_male:        { skin: 0xC8886A, hair: 0x4A3018, cloth: 0x2A3838, eye: 0x385058 },
  young_female:      { skin: 0xD89A7C, hair: 0x7A4A22, cloth: 0x3A2845, eye: 0x486055 },
  adolescent_male:   { skin: 0xC07A60, hair: 0x4A3020, cloth: 0x2A3028, eye: 0x485868 },
  adolescent_female: { skin: 0xD09078, hair: 0x5A3818, cloth: 0x283040, eye: 0x405860 },
  elder_male:        { skin: 0xB88868, hair: 0x909090, cloth: 0x282828, eye: 0x405060 },
  elder_female:      { skin: 0xC8907A, hair: 0xC0B8B0, cloth: 0x30283A, eye: 0x4A5860 },
};

// Emotion → ARKit morph target influences (0–1) for Rocketbox GLB avatars
var EMOTION_MORPHS = {
  idle:        {},
  speaking:    {},  // jaw driven separately by _animateJaw
  concerned:   { AK_01_BrowDownLeft:0.35, AK_02_BrowDownRight:0.35, AK_03_BrowInnerUp:0.55 },
  anxious:     { AK_21_EyeWideLeft:0.50,  AK_22_EyeWideRight:0.50,  AK_04_BrowOuterUpLeft:0.30, AK_05_BrowOuterUpRight:0.30 },
  distressed:  { AK_01_BrowDownLeft:0.65, AK_02_BrowDownRight:0.65, AK_30_MouthFrownLeft:0.45,  AK_31_MouthFrownRight:0.45, AK_03_BrowInnerUp:0.50 },
  confused:    { AK_38_MouthPucker:0.25,  AK_01_BrowDownLeft:0.20,  AK_02_BrowDownRight:0.20 },
  hopeful:     { AK_44_MouthSmileLeft:0.45,AK_45_MouthSmileRight:0.45, AK_04_BrowOuterUpLeft:0.20, AK_05_BrowOuterUpRight:0.20 },
  relieved:    { AK_44_MouthSmileLeft:0.35,AK_45_MouthSmileRight:0.35 },
  proud:       { AK_44_MouthSmileLeft:0.25,AK_45_MouthSmileRight:0.25, AK_03_BrowInnerUp:0.20 },
  embarrassed: { AK_19_EyeSquintLeft:0.40, AK_20_EyeSquintRight:0.40, AK_44_MouthSmileLeft:0.15, AK_45_MouthSmileRight:0.15 },
  tearful:     { AK_30_MouthFrownLeft:0.65,AK_31_MouthFrownRight:0.65, AK_19_EyeSquintLeft:0.50, AK_20_EyeSquintRight:0.50, AK_03_BrowInnerUp:0.75 },
  engaged:     { AK_04_BrowOuterUpLeft:0.20,AK_05_BrowOuterUpRight:0.20 },
  flat:        { AK_19_EyeSquintLeft:0.20, AK_20_EyeSquintRight:0.20 },
  flat_affect: { AK_19_EyeSquintLeft:0.20, AK_20_EyeSquintRight:0.20 },
  guarded:     { AK_19_EyeSquintLeft:0.30, AK_20_EyeSquintRight:0.30, AK_01_BrowDownLeft:0.20, AK_02_BrowDownRight:0.20 },
  agitated:    { AK_01_BrowDownLeft:0.50, AK_02_BrowDownRight:0.50, AK_50_NoseSneerLeft:0.30, AK_51_NoseSneerRight:0.30, AK_30_MouthFrownLeft:0.25, AK_31_MouthFrownRight:0.25 },
  neutral:     {},
  angry:       { AK_01_BrowDownLeft:0.80, AK_02_BrowDownRight:0.80, AK_50_NoseSneerLeft:0.50, AK_51_NoseSneerRight:0.50, AK_30_MouthFrownLeft:0.40, AK_31_MouthFrownRight:0.40 },
};

// All ARKit morph keys we ever drive (for lerp state tracking)
var MORPH_KEYS = [
  'AK_01_BrowDownLeft','AK_02_BrowDownRight','AK_03_BrowInnerUp',
  'AK_04_BrowOuterUpLeft','AK_05_BrowOuterUpRight',
  'AK_19_EyeSquintLeft','AK_20_EyeSquintRight',
  'AK_21_EyeWideLeft','AK_22_EyeWideRight',
  'AK_30_MouthFrownLeft','AK_31_MouthFrownRight',
  'AK_38_MouthPucker',
  'AK_44_MouthSmileLeft','AK_45_MouthSmileRight',
  'AK_50_NoseSneerLeft','AK_51_NoseSneerRight',
];

// Emotion → posture transform targets
// headX : forward(+) / back(-) tilt in radians
// headZ : side tilt, patient's right(+) / left(-)
// bodyX : forward lean of torso
// shoulderY : shoulder raise(+) / drop(-)  in world units
var EMOTION_TRANSFORMS = {
  idle:        { headX:  0.00, headZ:  0.00, bodyX:  0.00, shoulderY:  0.000 },
  speaking:    { headX:  0.02, headZ:  0.00, bodyX:  0.00, shoulderY:  0.000 },
  concerned:   { headX:  0.14, headZ:  0.00, bodyX:  0.06, shoulderY: -0.015 },
  anxious:     { headX: -0.06, headZ:  0.05, bodyX: -0.03, shoulderY:  0.010 },
  distressed:  { headX:  0.24, headZ:  0.00, bodyX:  0.12, shoulderY: -0.030 },
  confused:    { headX:  0.05, headZ:  0.18, bodyX:  0.00, shoulderY:  0.000 },
  hopeful:     { headX: -0.12, headZ:  0.00, bodyX: -0.04, shoulderY:  0.008 },
  relieved:    { headX: -0.08, headZ:  0.00, bodyX: -0.02, shoulderY: -0.005 },
  proud:       { headX: -0.16, headZ:  0.00, bodyX: -0.06, shoulderY:  0.015 },
  embarrassed: { headX:  0.12, headZ:  0.20, bodyX:  0.04, shoulderY: -0.020 },
  tearful:     { headX:  0.20, headZ:  0.00, bodyX:  0.10, shoulderY: -0.040 },
  engaged:     { headX: -0.04, headZ:  0.00, bodyX: -0.02, shoulderY:  0.005 },
  flat:        { headX:  0.04, headZ:  0.00, bodyX:  0.01, shoulderY: -0.010 },
  flat_affect: { headX:  0.04, headZ:  0.00, bodyX:  0.01, shoulderY: -0.010 },
  guarded:     { headX: -0.05, headZ:  0.00, bodyX: -0.04, shoulderY:  0.008 },
  agitated:    { headX:  0.06, headZ:  0.03, bodyX:  0.04, shoulderY:  0.012 },
  neutral:     { headX:  0.00, headZ:  0.00, bodyX:  0.00, shoulderY:  0.000 },
  angry:       { headX:  0.08, headZ:  0.00, bodyX:  0.06, shoulderY:  0.015 },
};


// ═══════════════════════════════════════════════════════════════════════════════
// MODULE STATE
// ═══════════════════════════════════════════════════════════════════════════════

var _renderer = null;
var _scene    = null;
var _camera   = null;
var _controls = null;
var _composer = null;
var _envMap   = null;
var _clock    = null;
var _animFrameId    = null;
var _resizeObserver = null;
var _container      = null;
var _canvasW = 320;
var _canvasH = 400;

// Avatar groups
var _avatarGroup   = null;   // root — breathing applied here
var _bodyGroup     = null;   // torso + arms (body lean)
var _headGroup     = null;   // head (head rotation)
var _jawGroup      = null;   // lower jaw (speaking)
var _shoulderGroup = null;   // clavicle crossbar (shoulder raise/drop)
var _eyeLidL       = null;   // left eyelid mesh (scaled for blink)
var _eyeLidR       = null;   // right eyelid mesh

var _chairGroup = null;

var _currentDemographic = null;
var _currentEmotion     = 'idle';
var _isSpeaking         = false;

// Rocketbox GLB bone + morph refs (null when using procedural avatar)
var _isGLB         = false;
var _faceM         = null;   // SkinnedMesh with 175 ARKit + viseme morph targets
var _headBone      = null;   // Bip01 Head
var _jawBone       = null;   // Bip01 MJaw
var _spineBone     = null;   // Bip01 Spine2 (upper body lean)
var _clavBoneL     = null;   // Bip01 L Clavicle
var _clavBoneR     = null;   // Bip01 R Clavicle
var _uArmBoneL     = null;   // Bip01 L UpperArm
var _uArmBoneR     = null;   // Bip01 R UpperArm
var _fArmBoneL     = null;   // Bip01 L Forearm
var _fArmBoneR     = null;   // Bip01 R Forearm

// Transform lerp state
var _currentT = { headX: 0, headZ: 0, bodyX: 0, shoulderY: 0 };
var _targetT  = { headX: 0, headZ: 0, bodyX: 0, shoulderY: 0 };

// Arm pose lerp state (GLB only)
var _currentArm = { uZ: 0.14, uX: 0.10, fX: 0.45, fZ: 0.04 };
var _targetArm  = { uZ: 0.14, uX: 0.10, fX: 0.45, fZ: 0.04 };

// Morph target lerp state (GLB only) — keys from MORPH_KEYS
var _currentMorphs = {};
var _targetMorphs  = {};
MORPH_KEYS.forEach(function(k) { _currentMorphs[k] = 0; _targetMorphs[k] = 0; });

var _breathPhase = 0;
var _jawPhase    = 0;
var _blinkTimer  = 0;
var _nextBlink   = 3.5 + Math.random() * 2.0;

var _readyResolve = null;
var _readyReject  = null;


// ═══════════════════════════════════════════════════════════════════════════════
// ENVIRONMENT MAP — warm studio for skin tones
// ═══════════════════════════════════════════════════════════════════════════════

function _buildEnvMap() {
  var pmrem = new THREE.PMREMGenerator(_renderer);
  pmrem.compileCubemapShader();
  var envScene = new THREE.Scene();

  // Sky dome — warm neutral ceiling
  envScene.add(new THREE.Mesh(
    new THREE.SphereGeometry(10, 32, 16),
    new THREE.MeshBasicMaterial({ color: 0x3A3530, side: THREE.BackSide })
  ));

  // Key area — warm 3200K tungsten overhead
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

  // Rim area — warm backlight
  var rimArea = new THREE.Mesh(
    new THREE.PlaneGeometry(4, 3),
    new THREE.MeshBasicMaterial({ color: 0x704838 })
  );
  rimArea.position.set(0, 5, -5);
  rimArea.lookAt(0, 0, 0);
  envScene.add(rimArea);

  // Ground bounce — dark warm floor
  var ground = new THREE.Mesh(
    new THREE.PlaneGeometry(20, 20),
    new THREE.MeshBasicMaterial({ color: 0x201510 })
  );
  ground.position.set(0, -9, 0);
  ground.rotation.x = -Math.PI / 2;
  envScene.add(ground);

  // Catchlight — round softbox highlight
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
// LIGHTING — 5-point face-optimized
// ═══════════════════════════════════════════════════════════════════════════════

function _buildLights() {
  // ── KEY — warm portrait light, tight frustum on face ──────────────────────
  var keyLight = new THREE.DirectionalLight(0xFFF4EC, 3.2);
  keyLight.position.set(2.0, 6.5, 4.5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width  = 2048;
  keyLight.shadow.mapSize.height = 2048;
  keyLight.shadow.bias           = -0.0002;
  keyLight.shadow.normalBias     = 0.02;
  // Tight frustum — focussed on face / upper body for crisp facial shadows
  keyLight.shadow.camera.near   = 1;
  keyLight.shadow.camera.far    = 16;
  keyLight.shadow.camera.left   = -1.2;
  keyLight.shadow.camera.right  =  1.2;
  keyLight.shadow.camera.top    =  1.8;
  keyLight.shadow.camera.bottom = -0.4;
  _scene.add(keyLight);

  // ── FILL — soft cool daylight from screen-left ─────────────────────────────
  var fillLight = new THREE.DirectionalLight(0xC8DCFF, 0.80);
  fillLight.position.set(-4, 3, 3);
  _scene.add(fillLight);

  // ── RIM — warm gold from behind, separates hair/shoulders from wall ────────
  var rimLight = new THREE.DirectionalLight(0xFFCC80, 1.10);
  rimLight.position.set(0, 5, -5);
  _scene.add(rimLight);

  // ── CATCH LIGHT — tiny point near lens, fires specular glints in eyes ──────
  var catchLight = new THREE.PointLight(0xFFFAF0, 0.55, 3.5, 2);
  catchLight.position.set(0.3, 2.2, 1.8);
  _scene.add(catchLight);

  // ── BOUNCE — warm low light from lap/sofa surface ─────────────────────────
  var bounceLight = new THREE.DirectionalLight(0xFFE8B0, 0.22);
  bounceLight.position.set(0, -1.5, 1.5);
  _scene.add(bounceLight);

  // ── HEMISPHERE + AMBIENT base ─────────────────────────────────────────────
  _scene.add(new THREE.HemisphereLight(0xD0D8E8, 0x4A3018, 0.40));
  _scene.add(new THREE.AmbientLight(0xFFF4EC, 0.08));
}


// ═══════════════════════════════════════════════════════════════════════════════
// POST-PROCESSING — GTAOPass + UnrealBloomPass + OutputPass
// ═══════════════════════════════════════════════════════════════════════════════

function _buildComposer() {
  _composer = new EffectComposer(_renderer);
  _composer.addPass(new RenderPass(_scene, _camera));

  var gtaoPass = new GTAOPass(_scene, _camera, _canvasW, _canvasH);
  gtaoPass.output = GTAOPass.OUTPUT.Default;
  gtaoPass.updateGtaoMaterial({
    radius: 0.22,           // tighter — catches fine facial creases
    distanceExponent: 2.5,
    thickness: 1.2,
    samples: 16,            // more samples = smoother AO on face
  });
  gtaoPass.updatePdMaterial({ lumaPhi: 12, depthPhi: 2.5, normalPhi: 4, radius: 4 });
  _composer.addPass(gtaoPass);

  // Subtle bloom — eye glints and window glow only
  _composer.addPass(new UnrealBloomPass(
    new THREE.Vector2(_canvasW, _canvasH),
    0.12, 0.30, 0.92
  ));

  _composer.addPass(new OutputPass());
}


// ═══════════════════════════════════════════════════════════════════════════════
// SCENE — therapy room environment
// ═══════════════════════════════════════════════════════════════════════════════

function _makeCushionTex(hexBase, hexDark) {
  // Tufted cushion texture: fabric base + circular button-stitch marks in a grid
  var sz = 512;
  var cv = document.createElement('canvas');
  cv.width = cv.height = sz;
  var ctx = cv.getContext('2d');
  var base = '#' + hexBase.toString(16).padStart(6, '0');
  var dark = '#' + hexDark.toString(16).padStart(6, '0');

  // Solid base
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, sz, sz);

  // Subtle linen weave
  for (var y = 0; y < sz; y += 4) {
    ctx.globalAlpha = 0.18;
    ctx.fillStyle = dark;
    ctx.fillRect(0, y, sz, 1.5);
  }
  for (var x = 0; x < sz; x += 6) {
    ctx.globalAlpha = 0.10;
    ctx.fillStyle = dark;
    ctx.fillRect(x, 0, 2, sz);
  }
  ctx.globalAlpha = 1;

  // Button-stitch circles in a grid (2x2 per tile so it repeats naturally)
  var cols = 2, rows = 2;
  var cellW = sz / cols, cellH = sz / rows;
  for (var row = 0; row < rows; row++) {
    for (var col = 0; col < cols; col++) {
      var cx = cellW * (col + 0.5);
      var cy = cellH * (row + 0.5);

      // Outer gathering shadow (radial gradient simulating fabric pulled inward)
      var grad = ctx.createRadialGradient(cx, cy, 4, cx, cy, cellW * 0.38);
      grad.addColorStop(0,   dark + 'AA');
      grad.addColorStop(0.3, dark + '44');
      grad.addColorStop(1,   dark + '00');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, cellW * 0.38, 0, Math.PI * 2);
      ctx.fill();

      // Button circle — dark ring
      ctx.strokeStyle = dark;
      ctx.lineWidth = 5;
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      ctx.arc(cx, cy, 10, 0, Math.PI * 2);
      ctx.stroke();

      // Button fill
      ctx.fillStyle = dark;
      ctx.globalAlpha = 0.70;
      ctx.beginPath();
      ctx.arc(cx, cy, 7, 0, Math.PI * 2);
      ctx.fill();

      // Stitch lines radiating outward (8 stitches)
      ctx.strokeStyle = dark;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.45;
      for (var s = 0; s < 8; s++) {
        var angle = (s / 8) * Math.PI * 2;
        var r0 = 13, r1 = 22;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle) * r0, cy + Math.sin(angle) * r0);
        ctx.lineTo(cx + Math.cos(angle) * r1, cy + Math.sin(angle) * r1);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
  }

  var tex = new THREE.CanvasTexture(cv);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(3, 3);
  return tex;
}

function _buildScene() {

  // ── MATERIALS ──────────────────────────────────────────────────────────────
  var wallMat = new THREE.MeshPhysicalMaterial({
    color: 0xE4DDD0, roughness: 0.96, metalness: 0,   // warm off-white
  });
  var floorMat = new THREE.MeshPhysicalMaterial({
    color: 0x7A5A3A, roughness: 0.58, metalness: 0,   // warm medium oak
    envMap: _envMap, envMapIntensity: 0.05,
  });
  var baseboardMat = new THREE.MeshPhysicalMaterial({
    color: 0xF0ECE4, roughness: 0.70, metalness: 0,
  });
  var winFrameMat = new THREE.MeshPhysicalMaterial({
    color: 0x6B4422, roughness: 0.45, metalness: 0.05,  // warm walnut brown
    envMap: _envMap, envMapIntensity: 0.12,
  });
  var winRevealMat = new THREE.MeshPhysicalMaterial({
    color: 0xE8E2D6, roughness: 0.80, metalness: 0,  // plaster reveal
  });
  var winGlassMat = new THREE.MeshPhysicalMaterial({
    color: 0xC0D8F0, roughness: 0.04, metalness: 0,
    transparent: true, opacity: 0.28,
    envMap: _envMap, envMapIntensity: 0.55,
  });
  var winSkyMat = new THREE.MeshStandardMaterial({
    color: 0x90C8E8,
    emissive: new THREE.Color(0x5AAAD8), emissiveIntensity: 0.90,
  });
  var frameMat = new THREE.MeshPhysicalMaterial({
    color: 0x5C3D1E, roughness: 0.42, metalness: 0.15,
  });
  var canvasMat  = new THREE.MeshStandardMaterial({ color: 0xD8C9A8, roughness: 0.95 });
  var paintSkyMat = new THREE.MeshStandardMaterial({ color: 0x87B8D4, roughness: 0.95 });
  var paintMidMat = new THREE.MeshStandardMaterial({ color: 0x9EB07A, roughness: 0.95 });
  var paintSunMat = new THREE.MeshStandardMaterial({ color: 0xE8A44A, roughness: 0.90 });
  var potMat   = new THREE.MeshPhysicalMaterial({ color: 0x8C4E28, roughness: 0.80, metalness: 0 });
  var soilMat  = new THREE.MeshStandardMaterial({ color: 0x2A1A0A, roughness: 0.95 });
  var leafMat  = new THREE.MeshPhysicalMaterial({ color: 0x3A7C28, roughness: 0.75, metalness: 0 });
  var leafDkMat = new THREE.MeshPhysicalMaterial({ color: 0x225018, roughness: 0.80, metalness: 0 });

  // ── FLOOR ──────────────────────────────────────────────────────────────────
  var floor = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  _scene.add(floor);

  // ── BACK WALL ──────────────────────────────────────────────────────────────
  var wall = new THREE.Mesh(new THREE.PlaneGeometry(10, 7), wallMat);
  wall.position.set(0, 3.5, -2.4);
  wall.receiveShadow = true;
  _scene.add(wall);

  var baseboard = new THREE.Mesh(new THREE.BoxGeometry(10, 0.10, 0.03), baseboardMat);
  baseboard.position.set(0, 0.05, -2.38);
  _scene.add(baseboard);

  // ── WINDOW — centered on back wall, upper portion ─────────────────────────
  var winW = 1.10, winH = 1.30;
  var winX = 0.35, winY = 2.15, winZ = -2.38;
  var revealDepth = 0.18;  // wall thickness / reveal depth

  var winGroup = new THREE.Group();
  winGroup.position.set(winX, winY, winZ);

  // Sky glow behind glass
  var sky = new THREE.Mesh(new THREE.PlaneGeometry(winW + 0.02, winH + 0.02), winSkyMat);
  sky.position.z = -0.03;
  winGroup.add(sky);

  // Glass pane
  var glass = new THREE.Mesh(new THREE.PlaneGeometry(winW - 0.08, winH - 0.08), winGlassMat);
  glass.position.z = 0.00;
  winGroup.add(glass);

  // ── Outer casing — thick shadow-casting frame pieces ──────────────────────
  var fw = 0.09, fh = 0.09;  // frame width
  [
    // x,    y,              w,            h,      depth
    [0,       winH/2 + fw/2, winW + fw*2,  fw,     0.10],  // top
    [0,      -winH/2 - fw/2, winW + fw*2,  fw,     0.10],  // bottom
    [-winW/2 - fw/2, 0,      fw,  winH + fw*2,     0.10],  // left
    [ winW/2 + fw/2, 0,      fw,  winH + fw*2,     0.10],  // right
  ].forEach(function(r) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(r[2], r[3], r[4]), winFrameMat);
    m.position.set(r[0], r[1], r[4] / 2);
    m.castShadow = true; m.receiveShadow = true;
    winGroup.add(m);
  });

  // ── Inner muntin bars (cross) ──────────────────────────────────────────────
  var mw = 0.04;
  [[0, 0, winW - 0.02, mw, 0.06], [0, 0, mw, winH - 0.02, 0.06]].forEach(function(r) {
    var m = new THREE.Mesh(new THREE.BoxGeometry(r[2], r[3], r[4]), winFrameMat);
    m.position.set(r[0], r[1], r[4] / 2 + 0.01);
    winGroup.add(m);
  });

  // ── Window reveal — wall depth around opening (plaster sides, wood sill) ───
  [
    { geo: new THREE.BoxGeometry(winW + fw*2, revealDepth, fw),           pos: [0, winH/2 + fw/2, -revealDepth/2],            mat: winRevealMat },
    { geo: new THREE.BoxGeometry(revealDepth, winH + fw*2, fw),           pos: [-winW/2 - fw/2, 0, -revealDepth/2],           mat: winRevealMat },
    { geo: new THREE.BoxGeometry(revealDepth, winH + fw*2, fw),           pos: [ winW/2 + fw/2, 0, -revealDepth/2],           mat: winRevealMat },
    // Bottom sill — brown wood, protrudes forward
    { geo: new THREE.BoxGeometry(winW + fw*2 + 0.12, 0.07, fw + 0.18),   pos: [0, -winH/2 - fw/2, -revealDepth * 0.1 + 0.09], mat: winFrameMat },
  ].forEach(function(r) {
    var m = new THREE.Mesh(r.geo, r.mat);
    m.position.set(r.pos[0], r.pos[1], r.pos[2]);
    m.castShadow = true; m.receiveShadow = true;
    winGroup.add(m);
  });

  _scene.add(winGroup);

  // Exterior daylight — cool blue-white, shadow-casting, streaming through window
  var winSpot = new THREE.SpotLight(0xC8E0FF, 2.8, 10, Math.PI / 9, 0.25);
  winSpot.position.set(winX, 4.5, -1.8);
  winSpot.target.position.set(0, 0.6, 0);
  winSpot.castShadow = true;
  winSpot.shadow.mapSize.width  = 1024;
  winSpot.shadow.mapSize.height = 1024;
  winSpot.shadow.bias = -0.001;
  _scene.add(winSpot);
  _scene.add(winSpot.target);

  // ── PAINTING — upper-left wall, within frame ───────────────────────────────
  var paintGroup = new THREE.Group();
  paintGroup.position.set(-0.92, 2.08, -2.37);

  var outerFrame = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.54, 0.05), frameMat);
  paintGroup.add(outerFrame);

  var canvas = new THREE.Mesh(new THREE.BoxGeometry(0.60, 0.42, 0.03), canvasMat);
  canvas.position.z = 0.02;
  paintGroup.add(canvas);

  // Sky band
  var pSky = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.20, 0.01), paintSkyMat);
  pSky.position.set(0, 0.09, 0.035);
  paintGroup.add(pSky);

  // Ground/meadow band
  var pGround = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.18, 0.01), paintMidMat);
  pGround.position.set(0, -0.08, 0.035);
  paintGroup.add(pGround);

  // Sun circle
  var pSun = new THREE.Mesh(new THREE.CircleGeometry(0.052, 16), paintSunMat);
  pSun.position.set(0.16, 0.06, 0.038);
  paintGroup.add(pSun);

  _scene.add(paintGroup);

  // ── PLANT — right side, floor level, partially visible ────────────────────
  var plantGroup = new THREE.Group();
  plantGroup.position.set(1.08, 0, -2.10);

  var pot = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.09, 0.26, 14), potMat);
  pot.position.y = 0.13;
  pot.castShadow = true; pot.receiveShadow = true;
  plantGroup.add(pot);

  var soil = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.02, 14), soilMat);
  soil.position.y = 0.26;
  plantGroup.add(soil);

  var stemCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.025, 0.36, 8), soilMat);
  stemCyl.position.y = 0.44;
  plantGroup.add(stemCyl);

  [
    { x:  0.00, y: 0.70, z:  0.00, r: 0.17 },
    { x:  0.13, y: 0.57, z:  0.04, r: 0.13 },
    { x: -0.11, y: 0.60, z: -0.03, r: 0.14 },
    { x:  0.05, y: 0.48, z:  0.11, r: 0.12 },
    { x: -0.07, y: 0.50, z: -0.09, r: 0.11 },
  ].forEach(function(s, i) {
    var leaf = new THREE.Mesh(new THREE.SphereGeometry(s.r, 10, 8), i % 2 === 0 ? leafMat : leafDkMat);
    leaf.scale.set(1, 0.55, 1);
    leaf.position.set(s.x, s.y, s.z);
    leaf.castShadow = true;
    plantGroup.add(leaf);
  });
  _scene.add(plantGroup);

  // ── BACKGROUND SOFA — full-width, against back wall, fills bottom of frame ──
  var cushionTex = _makeCushionTex(0x7A8B6A, 0x3A5040);
  var sofaMat = new THREE.MeshPhysicalMaterial({
    color: 0x7A8B6A, map: cushionTex, roughness: 0.92, metalness: 0,
    envMap: _envMap, envMapIntensity: 0.02,
    sheen: 0.15, sheenRoughness: 0.8,
    sheenColor: new THREE.Color(0x9AAE88),
  });
  var sofaDarkMat = new THREE.MeshPhysicalMaterial({
    color: 0x506050, roughness: 0.94, metalness: 0,
  });
  var sofaLegMat = new THREE.MeshPhysicalMaterial({
    color: 0x2E1A08, roughness: 0.35, metalness: 0.25,
    envMap: _envMap, envMapIntensity: 0.12,
  });

  var sofa = new THREE.Group();
  var sofaW = 3.2;

  var sofaBase = new THREE.Mesh(new THREE.BoxGeometry(sofaW, 0.14, 0.82), sofaDarkMat);
  sofaBase.position.set(0, 0.37, 0);
  sofa.add(sofaBase);

  var cush0 = new THREE.Mesh(new THREE.BoxGeometry(sofaW / 3 - 0.04, 0.22, 0.76), sofaMat);
  cush0.position.set(-sofaW / 3, 0.52, 0.02); sofa.add(cush0);
  var cush1 = new THREE.Mesh(new THREE.BoxGeometry(sofaW / 3 - 0.04, 0.22, 0.76), sofaMat);
  cush1.position.set(0, 0.52, 0.02); sofa.add(cush1);
  var cush2 = new THREE.Mesh(new THREE.BoxGeometry(sofaW / 3 - 0.04, 0.22, 0.76), sofaMat);
  cush2.position.set(sofaW / 3, 0.52, 0.02); sofa.add(cush2);

  var sofaBackPanel = new THREE.Mesh(new THREE.BoxGeometry(sofaW, 0.72, 0.12), sofaDarkMat);
  sofaBackPanel.position.set(0, 1.00, -0.38);
  sofa.add(sofaBackPanel);

  var bc0 = new THREE.Mesh(new THREE.BoxGeometry(sofaW / 3 - 0.06, 0.62, 0.18), sofaMat);
  bc0.position.set(-sofaW / 3, 0.99, -0.30); sofa.add(bc0);
  var bc1 = new THREE.Mesh(new THREE.BoxGeometry(sofaW / 3 - 0.06, 0.62, 0.18), sofaMat);
  bc1.position.set(0, 0.99, -0.30); sofa.add(bc1);
  var bc2 = new THREE.Mesh(new THREE.BoxGeometry(sofaW / 3 - 0.06, 0.62, 0.18), sofaMat);
  bc2.position.set(sofaW / 3, 0.99, -0.30); sofa.add(bc2);

  var armL = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.34, 0.82), sofaMat);
  armL.position.set(-(sofaW / 2 + 0.09), 0.58, 0); sofa.add(armL);
  var armLTop = new THREE.Mesh(new THREE.BoxGeometry(0.20, 0.07, 0.84), sofaMat);
  armLTop.position.set(-(sofaW / 2 + 0.09), 0.78, 0); sofa.add(armLTop);
  var armR = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.34, 0.82), sofaMat);
  armR.position.set(sofaW / 2 + 0.09, 0.58, 0); sofa.add(armR);
  var armRTop = new THREE.Mesh(new THREE.BoxGeometry(0.20, 0.07, 0.84), sofaMat);
  armRTop.position.set(sofaW / 2 + 0.09, 0.78, 0); sofa.add(armRTop);

  var legPositions = [-1.40, -0.70, 0, 0.70, 1.40];
  for (var li = 0; li < legPositions.length; li++) {
    var legF = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.03, 0.28, 8), sofaLegMat);
    legF.position.set(legPositions[li], 0.14, 0.34);
    sofa.add(legF);
    var legB = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.03, 0.28, 8), sofaLegMat);
    legB.position.set(legPositions[li], 0.14, -0.34);
    sofa.add(legB);
  }

  // Bring sofa forward so the avatar sits in it; lower slightly to match seat height
  sofa.position.set(0, -0.10, -0.42);
  _scene.add(sofa);

  // ── PROCEDURAL CHAIR (fallback for non-GLB avatar) ─────────────────────────
  _chairGroup = new THREE.Group();
  var chairSeatMat = new THREE.MeshPhysicalMaterial({
    color: 0x3A2E44, roughness: 0.85, metalness: 0,
    envMap: _envMap, envMapIntensity: 0.02,
  });
  var chairLegMat = new THREE.MeshPhysicalMaterial({
    color: 0x1A1418, roughness: 0.7, metalness: 0.25,
  });
  var chairSeat = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.08, 0.50), chairSeatMat);
  chairSeat.position.set(0, 0.48, 0.05);
  chairSeat.receiveShadow = true;
  _chairGroup.add(chairSeat);
  var chairBack = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.65, 0.07), chairSeatMat);
  chairBack.position.set(0, 0.90, -0.20);
  chairBack.receiveShadow = true;
  _chairGroup.add(chairBack);
  [[-0.22, -0.25], [0.22, -0.25], [-0.22, 0.25], [0.22, 0.25]].forEach(function(p) {
    var leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.5, 8), chairLegMat);
    leg.position.set(p[0], 0.25, p[1]);
    _chairGroup.add(leg);
  });
  _chairGroup.visible = false;  // sofa replaces this; shown only for procedural avatar fallback
  _scene.add(_chairGroup);
}


// ═══════════════════════════════════════════════════════════════════════════════
// PROCEDURAL HUMANOID
// ═══════════════════════════════════════════════════════════════════════════════

function _m(geo, mat) {
  var mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow    = true;
  mesh.receiveShadow = true;
  return mesh;
}

function _buildHumanoid(config) {
  // Remove previous avatar
  if (_avatarGroup) {
    _scene.remove(_avatarGroup);
    _avatarGroup = null;
  }
  _headGroup = null; _jawGroup = null;
  _bodyGroup = null; _shoulderGroup = null;
  _eyeLidL   = null; _eyeLidR = null;

  var skinColor  = config.skin  || 0xC8886A;
  var hairColor  = config.hair  || 0x2A1808;
  var clothColor = config.cloth || 0x252E3A;
  var eyeColor   = config.eye   || 0x3A5068;

  var s = new THREE.MeshPhysicalMaterial({
    color: skinColor, roughness: 0.65, metalness: 0,
    clearcoat: 0.15, clearcoatRoughness: 0.45,
    sheen: 0.25, sheenRoughness: 0.60,
    sheenColor: new THREE.Color(0xFFCCAA),
    envMap: _envMap, envMapIntensity: 0.08,
  });
  var h = new THREE.MeshPhysicalMaterial({
    color: hairColor, roughness: 0.72, metalness: 0,
    sheen: 0.35, sheenRoughness: 0.55,
    sheenColor: new THREE.Color(hairColor),
    envMap: _envMap, envMapIntensity: 0.04,
  });
  var c = new THREE.MeshPhysicalMaterial({
    color: clothColor, roughness: 0.85, metalness: 0,
    sheen: 0.10, sheenRoughness: 0.8,
    sheenColor: new THREE.Color(0x888888),
    envMap: _envMap, envMapIntensity: 0.02,
  });
  var irisMat = new THREE.MeshPhysicalMaterial({
    color: eyeColor, roughness: 0.05, metalness: 0,
    clearcoat: 1.0, clearcoatRoughness: 0.0,
    envMap: _envMap, envMapIntensity: 0.35,
  });
  var whiteMat = new THREE.MeshPhysicalMaterial({
    color: 0xEEEAE4, roughness: 0.45, metalness: 0,
    envMap: _envMap, envMapIntensity: 0.08,
  });
  var pupilMat = new THREE.MeshPhysicalMaterial({
    color: 0x080808, roughness: 0.05, metalness: 0,
    clearcoat: 1.0, envMap: _envMap, envMapIntensity: 0.5,
  });

  _avatarGroup   = new THREE.Group();
  _headGroup     = new THREE.Group();
  _jawGroup      = new THREE.Group();
  _bodyGroup     = new THREE.Group();
  _shoulderGroup = new THREE.Group();

  // ── HEAD ──────────────────────────────────────────────────────────────────

  // Skull
  var skull = _m(new THREE.SphereGeometry(0.135, 32, 24), s);
  skull.scale.y = 1.14;
  _headGroup.add(skull);

  // Hair cap — top 52% of sphere
  var hairCap = _m(
    new THREE.SphereGeometry(0.140, 26, 18, 0, Math.PI * 2, 0, Math.PI * 0.52), h
  );
  hairCap.scale.y = 1.14;
  _headGroup.add(hairCap);

  // Ears
  [-1, 1].forEach(function(side) {
    var ear = _m(new THREE.SphereGeometry(0.038, 10, 8), s);
    ear.scale.z = 0.52;
    ear.position.set(side * 0.133, 0, 0);
    _headGroup.add(ear);
  });

  // Eyes: whites → iris → pupil → eyelid
  [-1, 1].forEach(function(side) {
    var white = _m(new THREE.SphereGeometry(0.033, 14, 10), whiteMat);
    white.scale.z = 0.68;
    white.position.set(side * 0.052, 0.024, 0.110);
    _headGroup.add(white);

    var iris = _m(new THREE.SphereGeometry(0.021, 12, 8), irisMat);
    iris.scale.z = 0.55;
    iris.position.set(side * 0.052, 0.024, 0.119);
    _headGroup.add(iris);

    var pupil = _m(new THREE.SphereGeometry(0.012, 10, 8), pupilMat);
    pupil.scale.z = 0.55;
    pupil.position.set(side * 0.052, 0.024, 0.122);
    _headGroup.add(pupil);

    // Eyelid — thin half-sphere scaled to 0 (open), 1 (blink)
    var lid = _m(
      new THREE.SphereGeometry(0.036, 14, 8, 0, Math.PI * 2, 0, Math.PI * 0.5),
      s.clone()
    );
    lid.scale.set(1.0, 0, 0.28);
    lid.position.set(side * 0.052, 0.024, 0.112);
    _headGroup.add(lid);
    if (side === -1) _eyeLidL = lid;
    else             _eyeLidR = lid;
  });

  // Nose — subtle protrusion
  var nose = _m(new THREE.SphereGeometry(0.026, 10, 8), s);
  nose.scale.set(0.65, 0.50, 0.62);
  nose.position.set(0, -0.020, 0.122);
  _headGroup.add(nose);

  // Lower jaw — partial sphere that rotates open for speaking
  var jawGeo = new THREE.SphereGeometry(0.120, 24, 14, 0, Math.PI * 2, Math.PI * 0.44, Math.PI * 0.52);
  var jawMesh = _m(jawGeo, s);
  jawMesh.scale.y = 0.88;
  _jawGroup.add(jawMesh);
  _jawGroup.position.set(0, -0.044, 0.025);
  _headGroup.add(_jawGroup);

  _headGroup.position.set(0, 1.66, 0);

  // ── NECK ──────────────────────────────────────────────────────────────────
  var neck = _m(new THREE.CylinderGeometry(0.054, 0.064, 0.18, 14), s);
  neck.position.set(0, 1.46, 0);
  _bodyGroup.add(neck);

  // ── SHOULDERS ─────────────────────────────────────────────────────────────
  var clavicle = _m(new THREE.CapsuleGeometry(0.058, 0.40, 6, 12), c);
  clavicle.rotation.z = Math.PI / 2;
  _shoulderGroup.add(clavicle);
  _shoulderGroup.position.set(0, 1.34, -0.02);
  _bodyGroup.add(_shoulderGroup);

  // ── TORSO ─────────────────────────────────────────────────────────────────
  var chest = _m(new THREE.CylinderGeometry(0.155, 0.165, 0.36, 14), c);
  chest.position.set(0, 1.08, -0.02);
  _bodyGroup.add(chest);

  var abdomen = _m(new THREE.CylinderGeometry(0.145, 0.135, 0.22, 14), c);
  abdomen.position.set(0, 0.80, -0.01);
  _bodyGroup.add(abdomen);

  // ── ARMS ──────────────────────────────────────────────────────────────────
  [-1, 1].forEach(function(side) {
    // Upper arm — slightly angled down and out
    var uArm = _m(new THREE.CapsuleGeometry(0.048, 0.24, 4, 10), c);
    uArm.rotation.z = side * 0.40;
    uArm.position.set(side * 0.23, 1.18, 0.00);
    _bodyGroup.add(uArm);

    // Forearm — angled forward to rest on lap
    var fArm = _m(new THREE.CapsuleGeometry(0.040, 0.22, 4, 10), s);
    fArm.rotation.z = side * 0.18;
    fArm.rotation.x = 0.55;
    fArm.position.set(side * 0.25, 0.95, 0.08);
    _bodyGroup.add(fArm);

    // Hand
    var hand = _m(new THREE.SphereGeometry(0.045, 12, 10), s);
    hand.scale.set(0.82, 0.62, 1.0);
    hand.position.set(side * 0.26, 0.70, 0.22);
    _bodyGroup.add(hand);
  });

  // ── SEATED LEGS ───────────────────────────────────────────────────────────
  [-1, 1].forEach(function(side) {
    // Thigh — horizontal, extending forward
    var thigh = _m(new THREE.CapsuleGeometry(0.072, 0.34, 4, 10), c);
    thigh.rotation.x = Math.PI / 2;
    thigh.position.set(side * 0.11, 0.52, 0.20);
    _bodyGroup.add(thigh);

    // Lower leg — going down from knee
    var lLeg = _m(new THREE.CapsuleGeometry(0.052, 0.28, 4, 10), c);
    lLeg.position.set(side * 0.11, 0.22, 0.44);
    _bodyGroup.add(lLeg);
  });

  _avatarGroup.add(_bodyGroup);
  _avatarGroup.add(_headGroup);
  _scene.add(_avatarGroup);

  console.log('[patient-avatar-v2] Humanoid built:', _currentDemographic);
}


// ═══════════════════════════════════════════════════════════════════════════════
// GLB LOADING — Avaturn avatar format
// ═══════════════════════════════════════════════════════════════════════════════

var _loader = null;

function _applyAvaturnMaterials(gltf) {
  // Base color is always 0xFFFFFF so Avaturn's baked textures show through
  // unmodified — we only layer PBR properties on top for rendering quality.
  var skinMat = new THREE.MeshPhysicalMaterial({
    color: 0xFFFFFF, roughness: 0.65, metalness: 0,
    clearcoat: 0.15, clearcoatRoughness: 0.45,
    sheen: 0.25, sheenRoughness: 0.60,
    sheenColor: new THREE.Color(0xFFCCAA),
    envMap: _envMap, envMapIntensity: 0.08,
  });
  var hairMat = new THREE.MeshPhysicalMaterial({
    color: 0xFFFFFF, roughness: 0.72, metalness: 0,
    sheen: 0.35, sheenRoughness: 0.55,
    sheenColor: new THREE.Color(0xD4AA70),
    envMap: _envMap, envMapIntensity: 0.04,
  });
  var clothMat = new THREE.MeshPhysicalMaterial({
    color: 0xFFFFFF, roughness: 0.85, metalness: 0,
    sheen: 0.10, sheenRoughness: 0.8,
    sheenColor: new THREE.Color(0x888888),
    envMap: _envMap, envMapIntensity: 0.02,
  });
  var shoeMat = new THREE.MeshPhysicalMaterial({
    color: 0xFFFFFF, roughness: 0.75, metalness: 0,
    envMap: _envMap, envMapIntensity: 0.03,
  });

  gltf.scene.traverse(function(child) {
    if (!child.isMesh) return;
    child.castShadow    = true;
    child.receiveShadow = true;

    var n = child.name.toLowerCase();
    var origMap = child.material && child.material.map ? child.material.map : null;
    if (origMap) origMap.colorSpace = THREE.SRGBColorSpace;

    var mat;
    if (n.includes('hair')) {
      mat = hairMat.clone();
    } else if (n.includes('shoe') || n.includes('boot')) {
      mat = shoeMat.clone();
    } else if (n.includes('look') || n.includes('cloth') || n.includes('outfit') || n.includes('shirt')) {
      mat = clothMat.clone();
    } else {
      mat = skinMat.clone();
    }
    if (origMap) mat.map = origMap;
    child.material = mat;
  });
}

// Rocketbox bone names → rotation.z for A-pose → relaxed repose
// Kept subtle — arms barely visible in portrait crop, aggressive repose causes hair/collar clipping
// Named arm poses — uZ: upper arm abduction, uX: upper arm forward, fX: forearm down, fZ: forearm roll
var ARM_POSES = {
  relaxed:   { uZ: 0.14, uX: 0.10, fX: 0.45, fZ:  0.04 }, // natural resting in lap
  withdrawn: { uZ: 0.06, uX: 0.22, fX: 0.62, fZ:  0.02 }, // collapsed, hands tight in lap
  guarded:   { uZ: 0.05, uX: 0.32, fX: 0.52, fZ: -0.12 }, // arms pulled in, hands toward center
  tense:     { uZ: 0.22, uX: 0.06, fX: 0.22, fZ:  0.06 }, // arms slightly raised, stiff
  open:      { uZ: 0.20, uX: 0.04, fX: 0.38, fZ:  0.06 }, // open, relaxed
};

var EMOTION_ARM_POSES = {
  idle:        'relaxed',
  speaking:    'relaxed',
  neutral:     'relaxed',
  engaged:     'relaxed',
  concerned:   'relaxed',
  relieved:    'open',
  proud:       'open',
  hopeful:     'open',
  confused:    'open',
  anxious:     'guarded',
  guarded:     'guarded',
  embarrassed: 'withdrawn',
  distressed:  'withdrawn',
  tearful:     'withdrawn',
  flat_affect: 'withdrawn',
  flat:        'withdrawn',
  agitated:    'tense',
  angry:       'tense',
};

function _enhanceRocketboxMaterials(gltf) {
  // Preserve Rocketbox's baked textures — just layer envMap for PBR quality
  gltf.scene.traverse(function(child) {
    if (!child.isMesh) return;
    child.castShadow    = true;
    child.receiveShadow = true;
    var mats = Array.isArray(child.material) ? child.material : [child.material];
    mats.forEach(function(mat) {
      if (!mat) return;
      mat.envMap          = _envMap;
      mat.envMapIntensity = 0.06;
      if (mat.map) mat.map.colorSpace = THREE.SRGBColorSpace;
      mat.needsUpdate = true;
    });
  });
}

function _setupRocketboxRefs(gltf) {
  // Find face mesh — the one with the most morph targets (hipoly mesh)
  var bestCount = 0;
  _faceM = null;
  _headBone = null; _jawBone = null; _spineBone = null;
  _clavBoneL = null; _clavBoneR = null;

  gltf.scene.traverse(function(node) {
    if (node.isMesh && node.morphTargetDictionary) {
      var count = Object.keys(node.morphTargetDictionary).length;
      if (count > bestCount) { bestCount = count; _faceM = node; }
    }
    var n = node.name;
    if (n === 'Bip01 Head')       _headBone  = node;
    if (n === 'Bip01 MJaw')       _jawBone   = node;
    if (n === 'Bip01 Spine2')     _spineBone = node;
    if (n === 'Bip01 L Clavicle') _clavBoneL = node;
    if (n === 'Bip01 R Clavicle') _clavBoneR = node;
    if (n === 'Bip01 L UpperArm') _uArmBoneL = node;
    if (n === 'Bip01 R UpperArm') _uArmBoneR = node;
    if (n === 'Bip01 L Forearm')  _fArmBoneL = node;
    if (n === 'Bip01 R Forearm')  _fArmBoneR = node;
  });

  _isGLB = true;
  // Reset morph lerp state
  MORPH_KEYS.forEach(function(k) { _currentMorphs[k] = 0; _targetMorphs[k] = 0; });
  // Reset arm lerp state to relaxed pose
  var initPose = ARM_POSES.relaxed;
  _currentArm.uZ = initPose.uZ; _currentArm.uX = initPose.uX;
  _currentArm.fX = initPose.fX; _currentArm.fZ = initPose.fZ;
  _targetArm.uZ  = initPose.uZ; _targetArm.uX  = initPose.uX;
  _targetArm.fX  = initPose.fX; _targetArm.fZ  = initPose.fZ;

  console.log('[patient-avatar-v2] Rocketbox refs — faceM:', !!_faceM,
    'morphs:', bestCount, 'headBone:', !!_headBone, 'jawBone:', !!_jawBone,
    'uArmL:', !!_uArmBoneL, 'uArmR:', !!_uArmBoneR, 'fArmL:', !!_fArmBoneL, 'fArmR:', !!_fArmBoneR);
}

function _loadGLB(type, config) {
  return new Promise(function(resolve) {
    var path = 'data/avatars/' + type + '.glb';
    console.log('[patient-avatar-v2] _loadGLB start, path=', path);
    if (!_loader) {
      console.error('[patient-avatar-v2] _loader is null — falling back');
      _buildHumanoid(config || DEMOGRAPHIC_CONFIGS.adult_male);
      resolve(); return;
    }
    _loader.load(
      path,
      function(gltf) {
        try {
          if (_avatarGroup) { _scene.remove(_avatarGroup); _avatarGroup = null; }
          _headGroup = null; _jawGroup = null;
          _bodyGroup = null; _shoulderGroup = null;
          _eyeLidL   = null; _eyeLidR = null;
          _isGLB     = false;

          _enhanceRocketboxMaterials(gltf);
          _avatarGroup = gltf.scene;
          _avatarGroup.position.set(0, 0, 0);
          _scene.add(_avatarGroup);

          _setupRocketboxRefs(gltf);

          if (_chairGroup) _chairGroup.visible = false;

          // Auto-frame camera on the avatar's head based on actual bounding box
          var box = new THREE.Box3().setFromObject(_avatarGroup);
          var avatarHeight = box.max.y - box.min.y;
          var headY = box.min.y + avatarHeight * 0.88; // ~88% up = face level
          console.log('[patient-avatar-v2] avatar bbox:', JSON.stringify({
            minY: box.min.y.toFixed(2), maxY: box.max.y.toFixed(2),
            height: avatarHeight.toFixed(2), headY: headY.toFixed(2)
          }));
          if (_controls) {
            _controls.target.set(0, headY, 0);
            _controls.update();
          }
          if (_camera) {
            _camera.position.set(0, headY, 1.4);
            _camera.lookAt(0, headY, 0);
          }

          console.log('[patient-avatar-v2] Rocketbox GLB loaded:', type);
          resolve();
        } catch(e) {
          console.error('[patient-avatar-v2] Error in GLB onLoad:', e);
          _buildHumanoid(config || DEMOGRAPHIC_CONFIGS.adult_male);
          resolve();
        }
      },
      null,
      function(err) {
        console.warn('[patient-avatar-v2] GLB not found for ' + type + ', trying adult_male fallback');
        if (type !== 'adult_male') {
          _loader.load('data/avatars/adult_male.glb',
            function(gltf) {
              if (_avatarGroup) { _scene.remove(_avatarGroup); _avatarGroup = null; }
              _isGLB = false;
              _enhanceRocketboxMaterials(gltf);
              _avatarGroup = gltf.scene;
              _avatarGroup.position.set(0, 0, 0);
              _scene.add(_avatarGroup);
              _setupRocketboxRefs(gltf);
              if (_chairGroup) _chairGroup.visible = false;
              var box2 = new THREE.Box3().setFromObject(_avatarGroup);
              var headY2 = box2.min.y + (box2.max.y - box2.min.y) * 0.88;
              if (_controls) { _controls.target.set(0, headY2, 0); _controls.update(); }
              if (_camera) { _camera.position.set(0, headY2, 1.4); _camera.lookAt(0, headY2, 0); }
              console.log('[patient-avatar-v2] adult_male fallback loaded');
              resolve();
            },
            null,
            function() {
              console.warn('[patient-avatar-v2] adult_male fallback also missing — using procedural');
              _buildHumanoid(DEMOGRAPHIC_CONFIGS.adult_male);
              resolve();
            }
          );
        } else {
          _buildHumanoid(DEMOGRAPHIC_CONFIGS.adult_male);
          resolve();
        }
      }
    );
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// EMOTION / TRANSFORM SYSTEM
// ═══════════════════════════════════════════════════════════════════════════════

function _setTargetTransforms(emotion) {
  var t = EMOTION_TRANSFORMS[emotion] || EMOTION_TRANSFORMS.idle;
  _targetT.headX     = t.headX;
  _targetT.headZ     = t.headZ;
  _targetT.bodyX     = t.bodyX;
  _targetT.shoulderY = t.shoulderY;
  // Set morph target goals for GLB
  var morphDef = EMOTION_MORPHS[emotion] || {};
  MORPH_KEYS.forEach(function(k) { _targetMorphs[k] = morphDef[k] || 0; });
  // Set arm pose goals for GLB
  var poseName = EMOTION_ARM_POSES[emotion] || 'relaxed';
  var pose = ARM_POSES[poseName] || ARM_POSES.relaxed;
  _targetArm.uZ = pose.uZ; _targetArm.uX = pose.uX;
  _targetArm.fX = pose.fX; _targetArm.fZ = pose.fZ;
}

function _lerpTransforms(dt) {
  var rate = 1 - Math.pow(0.04, dt);
  _currentT.headX     = THREE.MathUtils.lerp(_currentT.headX,     _targetT.headX,     rate);
  _currentT.headZ     = THREE.MathUtils.lerp(_currentT.headZ,     _targetT.headZ,     rate);
  _currentT.bodyX     = THREE.MathUtils.lerp(_currentT.bodyX,     _targetT.bodyX,     rate);
  _currentT.shoulderY = THREE.MathUtils.lerp(_currentT.shoulderY, _targetT.shoulderY, rate);

  if (_isGLB) {
    if (_headBone) {
      _headBone.rotation.x = _currentT.headX;
      _headBone.rotation.z = _currentT.headZ;
    }
    if (_spineBone) {
      _spineBone.rotation.x = _currentT.bodyX * 0.5;
    }
  } else {
    if (_headGroup) {
      _headGroup.rotation.x = _currentT.headX;
      _headGroup.rotation.z = _currentT.headZ;
    }
    if (_bodyGroup)    { _bodyGroup.rotation.x    = _currentT.bodyX; }
    if (_shoulderGroup){ _shoulderGroup.position.y = _currentT.shoulderY; }
  }
}

function _lerpMorphs(dt) {
  if (!_isGLB || !_faceM || !_faceM.morphTargetDictionary) return;
  var rate = 1 - Math.pow(0.04, dt);
  var dict = _faceM.morphTargetDictionary;
  var infl = _faceM.morphTargetInfluences;
  MORPH_KEYS.forEach(function(k) {
    var idx = dict[k];
    if (idx === undefined) return;
    _currentMorphs[k] = THREE.MathUtils.lerp(_currentMorphs[k], _targetMorphs[k], rate);
    infl[idx] = _currentMorphs[k];
  });
}


function _lerpArms(dt) {
  if (!_isGLB || !_uArmBoneL) return;
  var rate = 1 - Math.pow(0.03, dt);  // slightly slower than head/morph for natural feel
  _currentArm.uZ = THREE.MathUtils.lerp(_currentArm.uZ, _targetArm.uZ, rate);
  _currentArm.uX = THREE.MathUtils.lerp(_currentArm.uX, _targetArm.uX, rate);
  _currentArm.fX = THREE.MathUtils.lerp(_currentArm.fX, _targetArm.fX, rate);
  _currentArm.fZ = THREE.MathUtils.lerp(_currentArm.fZ, _targetArm.fZ, rate);
  if (_uArmBoneL) { _uArmBoneL.rotation.z =  _currentArm.uZ; _uArmBoneL.rotation.x = _currentArm.uX; }
  if (_uArmBoneR) { _uArmBoneR.rotation.z = -_currentArm.uZ; _uArmBoneR.rotation.x = _currentArm.uX; }
  if (_fArmBoneL) { _fArmBoneL.rotation.x = _currentArm.fX; _fArmBoneL.rotation.z =  _currentArm.fZ; }
  if (_fArmBoneR) { _fArmBoneR.rotation.x = _currentArm.fX; _fArmBoneR.rotation.z = -_currentArm.fZ; }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION — breathing, jaw, blink
// ═══════════════════════════════════════════════════════════════════════════════

function _animateBreathing(dt) {
  _breathPhase += dt * 0.72;   // ~1 breath per 8.7 seconds
  if (_avatarGroup) {
    _avatarGroup.position.y = Math.sin(_breathPhase) * 0.004;
    _avatarGroup.rotation.z = Math.sin(_breathPhase * 0.5) * 0.0025;
  }
}

function _animateJaw(dt) {
  if (!_isSpeaking) return;
  _jawPhase += dt * 7.0;
  var jawVal = Math.max(0, 0.06 + Math.sin(_jawPhase) * 0.08 + Math.sin(_jawPhase * 1.65) * 0.035);

  if (_isGLB && _faceM && _faceM.morphTargetDictionary) {
    var idx = _faceM.morphTargetDictionary['AK_25_JawOpen'];
    if (idx !== undefined) _faceM.morphTargetInfluences[idx] = Math.min(1, jawVal * 3.5);
  } else if (_jawGroup) {
    _jawGroup.rotation.x = jawVal;
  }
}

function _animateBlink(dt) {
  _blinkTimer += dt;
  if (_blinkTimer < _nextBlink) return;
  _blinkTimer = 0;
  _nextBlink  = 3.0 + Math.random() * 4.5;

  if (_isGLB && _faceM && _faceM.morphTargetDictionary) {
    var dict = _faceM.morphTargetDictionary;
    var infl = _faceM.morphTargetInfluences;
    var idxL = dict['AK_09_EyeBlinkLeft'];
    var idxR = dict['AK_10_EyeBlinkRight'];
    if (idxL !== undefined) infl[idxL] = 1;
    if (idxR !== undefined) infl[idxR] = 1;
    setTimeout(function() {
      if (!_faceM) return;
      if (idxL !== undefined) _faceM.morphTargetInfluences[idxL] = 0;
      if (idxR !== undefined) _faceM.morphTargetInfluences[idxR] = 0;
    }, 120);
  } else if (_eyeLidL && _eyeLidR) {
    _eyeLidL.scale.y = 1;
    _eyeLidR.scale.y = 1;
    setTimeout(function() {
      if (_eyeLidL) _eyeLidL.scale.y = 0;
      if (_eyeLidR) _eyeLidR.scale.y = 0;
    }, 120);
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION LOOP
// ═══════════════════════════════════════════════════════════════════════════════

function _animate() {
  _animFrameId = requestAnimationFrame(_animate);
  var dt = _clock.getDelta();
  if (_controls) _controls.update();
  _animateBreathing(dt);
  _lerpTransforms(dt);
  _lerpMorphs(dt);
  _lerpArms(dt);
  _animateBlink(dt);
  if (_isSpeaking) _animateJaw(dt);
  _composer.render();
}


// ═══════════════════════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * mount(container, options)
 * Initializes WebGL renderer inside container. Call before loadDemographic.
 * options: { width, height, controls }
 */
function mount(container, options) {
  options = options || {};
  _container = container;
  _canvasW = options.width  || container.offsetWidth  || 320;
  _canvasH = options.height || container.offsetHeight || 400;

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
  _renderer.domElement.style.cssText = 'display:block; border-radius:16px;';
  container.appendChild(_renderer.domElement);

  _scene = new THREE.Scene();
  _scene.background = new THREE.Color(0x0A0B10);
  _scene.fog = new THREE.Fog(0x0A0B10, 8, 16);

  // Tight portrait crop — face + upper chest, arms out of frame
  _camera = new THREE.PerspectiveCamera(34, _canvasW / _canvasH, 0.1, 30);
  _camera.position.set(0, 1.58, 1.6);
  _camera.lookAt(0, 1.62, 0);

  if (options.controls !== false) {
    _controls = new OrbitControls(_camera, _renderer.domElement);
    _controls.enableDamping = true;
    _controls.dampingFactor = 0.07;
    _controls.minDistance   = 1.5;
    _controls.maxDistance   = 5.0;
    _controls.minPolarAngle = 0.8;
    _controls.maxPolarAngle = 1.6;
    _controls.enablePan     = false;
    _controls.target.set(0, 1.5, 0);
    _controls.update();
  }

  _clock = new THREE.Clock();
  _buildEnvMap();
  _buildLights();
  _buildComposer();
  _buildScene();

  // GLTF + Draco loader
  var dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath('./vendor/three/examples/jsm/libs/draco/gltf/');
  _loader = new GLTFLoader();
  _loader.setDRACOLoader(dracoLoader);

  if (typeof ResizeObserver !== 'undefined') {
    _resizeObserver = new ResizeObserver(function(entries) {
      if (!entries[0]) return;
      var w = Math.round(entries[0].contentRect.width);
      var h = Math.round(w * (_canvasH / _canvasW));
      if (w > 0 && h > 0) resize(w, h);
    });
    _resizeObserver.observe(container);
  }

  _animate();
  console.log('[patient-avatar-v2] Mounted, canvas', _canvasW + 'x' + _canvasH);
  if (_readyResolve) _readyResolve();
}

/**
 * unmount()
 * Stop render loop, remove canvas, free GPU resources.
 */
function unmount() {
  if (_animFrameId !== null) { cancelAnimationFrame(_animFrameId); _animFrameId = null; }
  if (_resizeObserver) { _resizeObserver.disconnect(); _resizeObserver = null; }
  if (_controls) { _controls.dispose(); _controls = null; }
  if (_composer) { _composer.dispose(); _composer = null; }
  if (_renderer) {
    if (_container && _renderer.domElement.parentNode === _container)
      _container.removeChild(_renderer.domElement);
    _renderer.dispose();
    _renderer = null;
  }
  _scene = null; _camera = null; _envMap = null;
  _avatarGroup = null; _headGroup = null; _jawGroup = null;
  _bodyGroup   = null; _shoulderGroup = null;
  _eyeLidL     = null; _eyeLidR = null;
  console.log('[patient-avatar-v2] Unmounted');
}

/**
 * loadDemographic(type)
 * Rebuild avatar geometry with colors for the given demographic.
 * Returns Promise<void> (resolves synchronously — no network request).
 */
function loadDemographic(type) {
  if (!_scene) {
    console.warn('[patient-avatar-v2] loadDemographic called before mount() — queuing');
    _currentDemographic = type;
    return Promise.resolve();
  }
  _currentDemographic = type || 'adult_male';
  var config = DEMOGRAPHIC_CONFIGS[_currentDemographic] || DEMOGRAPHIC_CONFIGS.adult_male;
  return _loadGLB(_currentDemographic, config).then(function() {
    _setTargetTransforms(_currentEmotion);
  });
}

/**
 * setEmotion(emotion)
 * Smoothly transitions avatar posture to the target emotion state.
 */
function setEmotion(emotion) {
  if (!EMOTION_TRANSFORMS[emotion]) {
    emotion = 'idle';
  }
  _currentEmotion = emotion;
  _setTargetTransforms(emotion);
}

/**
 * setSpeaking(bool)
 * Enable/disable jaw speaking animation.
 */
function setSpeaking(isSpeaking) {
  _isSpeaking = !!isSpeaking;
  if (!isSpeaking) {
    if (_isGLB && _faceM && _faceM.morphTargetDictionary) {
      var idx = _faceM.morphTargetDictionary['AK_25_JawOpen'];
      if (idx !== undefined) _faceM.morphTargetInfluences[idx] = 0;
    } else if (_jawGroup) {
      _jawGroup.rotation.x = 0;
    }
  }
}

/**
 * resize(w, h)
 * Update renderer and composer to new pixel dimensions.
 */
function resize(w, h) {
  if (!_renderer) return;
  _canvasW = w; _canvasH = h;
  _renderer.setSize(w, h);
  if (_camera) { _camera.aspect = w / h; _camera.updateProjectionMatrix(); }
  if (_composer) _composer.setSize(w, h);
}


// ═══════════════════════════════════════════════════════════════════════════════
// READY PROMISE + EXPORT
// ═══════════════════════════════════════════════════════════════════════════════

var _readyPromise = new Promise(function(resolve, reject) {
  _readyResolve = resolve;
  _readyReject  = reject;
});

window.__PatientAvatar = {
  mount:           mount,
  unmount:         unmount,
  loadDemographic: loadDemographic,
  setEmotion:      setEmotion,
  setSpeaking:     setSpeaking,
  resize:          resize,
  ready:           _readyPromise,
  _getScene:       function() { return _scene; },
  _getRenderer:    function() { return _renderer; },
};

console.log('[patient-avatar-v2] window.__PatientAvatar registered');
