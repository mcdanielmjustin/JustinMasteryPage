#!/usr/bin/env python3
"""
generate_hires_subcortical.py  (v3)

Brainstem  — Harvard-Oxford subcortical atlas (thr0, 1mm), step_size=1
             + spherical UV map with procedural medulla/pons/midbrain texture
Cerebellum — AAL SPM5 atlas (2mm), step_size=1, sigma=0.3
             + spherical UV map with procedural folia texture baked in

Outputs:
  data/brain_meshes/hires_brainstem.glb
  data/brain_meshes/hires_cerebellum.glb
"""

import sys, gc
import numpy as np
from pathlib import Path
from scipy import ndimage
import nibabel as nib
import trimesh
import trimesh.visual
from trimesh.visual.material import PBRMaterial
from skimage import measure
from PIL import Image

OUTPUT_DIR = Path("data/brain_meshes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Atlas data fetched via nilearn (auto-downloads and caches)
HO_NII  = None  # set in main block after nilearn fetch
AAL_NII = None
AAL_TXT = None

# ── Folia texture constants (same ramp as cortex) ─────────────────────────────
SULCI_COL = np.array([55,  18,   8], dtype=np.float32)   # #371208 dark sulci
GYRI_COL  = np.array([221, 184, 152], dtype=np.float32)  # #DDB898 light gyri
TEX_W, TEX_H = 1024, 512                                  # texture resolution


# ── Coordinate transform (must match fix_hires_coords.py / generate_brain_meshes.py) ──
# FreeSurfer RAS: x=right, y=anterior, z=superior
# Three.js:       x=right, y=up(superior), z=toward-viewer(anterior)
# -> out = [-x_fs, z_fs, y_fs] * COORD_SCALE + COORD_OFFSET
COORD_SCALE  = 1.0 / 75.0
COORD_OFFSET = np.array([0.118, -0.204, 0.438], dtype=np.float64)

def to_threejs(coords):
    """MNI/FreeSurfer RAS mm → Three.js world units (same as cortex + region overlays)."""
    c = np.asarray(coords, dtype=np.float64)
    x_out = -c[:, 0]   # negate: lateral(-x) → +x_3js
    y_out =  c[:, 2]   # superior (z) → up (y_3js)
    z_out =  c[:, 1]   # anterior (y) → depth (z_3js)
    return (np.column_stack([x_out, y_out, z_out]) * COORD_SCALE + COORD_OFFSET).astype(np.float32)

print("[1/3] Coordinate transform: [-x, z, y] * 1/75 + COORD_OFFSET")
print(f"    COORD_OFFSET = {COORD_OFFSET}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def voxels_to_mesh(mask_3d, affine, step_size, sigma):
    """Binary 3D mask → smoothed marching-cubes surface in Three.js coordinate space."""
    smoothed = ndimage.gaussian_filter(mask_3d.astype(np.float32), sigma=sigma)
    verts_v, faces, _, _ = measure.marching_cubes(smoothed, level=0.5,
                                                   step_size=step_size)
    ones     = np.ones((len(verts_v), 1), dtype=np.float32)
    verts_mm = (affine @ np.hstack([verts_v.astype(np.float32), ones]).T).T[:, :3]
    verts_3d = to_threejs(verts_mm)
    faces    = faces.astype(np.int32)

    # Fix face winding: ensure normals point outward (required for FrontSide rendering).
    # The axis-swap in to_threejs can invert winding from marching cubes output.
    centroid = verts_3d.mean(axis=0)
    v0 = verts_3d[faces[:, 0]]
    v1 = verts_3d[faces[:, 1]]
    v2 = verts_3d[faces[:, 2]]
    face_normals = np.cross(v1 - v0, v2 - v0)
    face_centers = (v0 + v1 + v2) / 3.0
    dots = np.sum(face_normals * (face_centers - centroid), axis=1)
    inward = dots < 0
    if inward.sum() > len(faces) // 2:
        # Majority inward — flip all faces
        faces = faces[:, ::-1]
    elif inward.sum() > 0:
        # Flip only inward-facing faces
        faces[inward] = faces[inward][:, ::-1]

    return verts_3d, faces


def sphere_to_uv_brainstem(verts):
    """
    Spherical UV projection centred on the brainstem centroid.

    u = azimuthal angle — seam placed posteriorly (hidden against spine)
    v = elevation  0 = inferior (medulla), 1 = superior (midbrain)

    v is used to drive the three-zone anatomical texture.
    """
    centroid = verts.mean(axis=0)
    v_c = verts - centroid
    r   = np.linalg.norm(v_c, axis=1, keepdims=True)
    n   = v_c / np.maximum(r, 1e-9)
    # seam at y < 0 (posterior midline, hidden against spine)
    u = (np.arctan2(n[:, 0], -n[:, 1]) + np.pi) / (2.0 * np.pi)
    v = (np.arcsin(np.clip(n[:, 2], -1.0, 1.0)) + np.pi / 2.0) / np.pi
    return np.stack([u, v], axis=1).astype(np.float32), centroid


def generate_brainstem_texture():
    """
    Procedural brainstem texture — three anatomical segments.

    Medulla  (v 0.00–0.42): grayish-pink, fine longitudinal tract lines
    Pons     (v 0.38–0.62): lighter rosier-pink, horizontal transverse fiber striations
    Midbrain (v 0.58–1.00): slightly darker olive-gray, longitudinal fiber pattern
    """
    BS_W, BS_H = 512, 512
    uu = np.linspace(0.0, 1.0, BS_W, dtype=np.float32)
    vv = np.linspace(0.0, 1.0, BS_H, dtype=np.float32)
    UU, VV = np.meshgrid(uu, vv)

    # Anatomical base colours (RGB float32)
    MEDULLA_COL  = np.array([168, 132, 120], dtype=np.float32)  # grayish-pink
    PONS_COL     = np.array([195, 158, 145], dtype=np.float32)  # lighter / rosier
    MIDBRAIN_COL = np.array([172, 138, 126], dtype=np.float32)  # olive-gray

    def logistic(x, x0, k=20.0):
        return 1.0 / (1.0 + np.exp(-k * (x - x0)))

    pons_mask     = logistic(VV, 0.36) * (1.0 - logistic(VV, 0.64))
    midbrain_mask = logistic(VV, 0.61)
    medulla_mask  = np.maximum(1.0 - pons_mask - midbrain_mask, 0.0)

    # Blend base colours
    base = np.zeros((BS_H, BS_W, 3), dtype=np.float32)
    for i in range(3):
        base[:, :, i] = (medulla_mask  * MEDULLA_COL[i]
                       + pons_mask     * PONS_COL[i]
                       + midbrain_mask * MIDBRAIN_COL[i])

    # Pontine transverse fiber striations (horizontal, only in pons band)
    pons_fibers = 0.55 * pons_mask * np.sin(VV * 18 * 2.0 * np.pi)

    # Fine longitudinal tract lines throughout (very subtle vertical)
    long_tracts = 0.10 * np.sin(UU * 14 * 2.0 * np.pi)

    # Biological noise
    rng  = np.random.default_rng(7)
    noise = 0.06 * rng.standard_normal((BS_H, BS_W)).astype(np.float32)

    curv = pons_fibers + long_tracts + noise

    RIDGE_COL = np.array([218, 185, 168], dtype=np.float32)  # surface ridge / gyral peak
    GROOVE_COL = np.array([ 92,  62,  54], dtype=np.float32)  # deep groove / sulcus

    t_pos = np.clip( curv / 1.8, 0.0, 1.0)
    t_neg = np.clip(-curv / 1.8, 0.0, 1.0)

    rgb = np.empty((BS_H, BS_W, 3), dtype=np.uint8)
    for i in range(3):
        ch = (base[:, :, i]
              + t_pos * (RIDGE_COL[i] - base[:, :, i])
              + t_neg * (GROOVE_COL[i] - base[:, :, i]))
        rgb[:, :, i] = np.clip(ch, 0, 255).astype(np.uint8)
    return rgb


def sphere_to_uv_cerebellum(verts):
    """
    Spherical UV projection centred on the cerebellum's own centroid.

    u = azimuthal angle in the x–y plane (circumferential, seam at y≈0, x<0)
    v = elevation from bottom (z component) → folia run as horizontal bands

    The seam is placed anteriorly so it faces the brainstem and is rarely seen.
    """
    centroid = verts.mean(axis=0)
    v_c = verts - centroid
    r   = np.linalg.norm(v_c, axis=1, keepdims=True)
    n   = v_c / np.maximum(r, 1e-9)
    # u: atan2(x, y) — seam where y < 0, x ≈ 0 (anterior midline)
    u = (np.arctan2(n[:, 0], n[:, 1]) + np.pi) / (2.0 * np.pi)
    # v: elevation — z component, z-up = top of cerebellum
    v = (np.arcsin(np.clip(n[:, 2], -1.0, 1.0)) + np.pi / 2.0) / np.pi
    return np.stack([u, v], axis=1).astype(np.float32), centroid


def remove_seam_faces(uv, faces, wrap_threshold=0.35):
    """Drop triangles that straddle the u=0/1 wrap seam."""
    u0 = uv[faces[:, 0], 0]
    u1 = uv[faces[:, 1], 0]
    u2 = uv[faces[:, 2], 0]
    span = (np.maximum(np.maximum(u0, u1), u2)
            - np.minimum(np.minimum(u0, u1), u2))
    return faces[span < wrap_threshold]


def generate_folia_texture():
    """
    Procedural cerebellar folia texture.

    Primary bands  — 22 main folia, constant in u (horizontal on the surface)
    Secondary bands — 3 secondary fissures per primary folium for depth
    Lateral drift   — slight sinusoidal deviation so folia aren't perfectly flat
    Noise           — random grain for biological realism
    """
    uu = np.linspace(0.0, 1.0, TEX_W, dtype=np.float32)
    vv = np.linspace(0.0, 1.0, TEX_H, dtype=np.float32)
    UU, VV = np.meshgrid(uu, vv)

    N_PRI = 22   # main folia count
    N_SEC = 66   # secondary fissures (3× primary)

    # Primary horizontal folia
    curv = np.sin(VV * N_PRI * 2.0 * np.pi)
    # Deeper secondary fissures at every third primary
    curv += 0.45 * np.sin(VV * N_SEC * 2.0 * np.pi)
    # Slight lateral drift (folia bow gently)
    curv += 0.18 * np.sin(UU * 5.0 * 2.0 * np.pi
                           + VV * N_PRI * 2.0 * np.pi * 0.12)
    # Biological noise
    rng  = np.random.default_rng(42)
    curv += 0.08 * rng.standard_normal((TEX_H, TEX_W)).astype(np.float32)

    # Map curvature → colour (same ramp as cortex)
    t   = np.clip(curv / 2.0 + 0.5, 0.0, 1.0).astype(np.float32)
    rgb = np.empty((TEX_H, TEX_W, 3), dtype=np.uint8)
    for i in range(3):
        ch = SULCI_COL[i] * (1.0 - t) + GYRI_COL[i] * t
        rgb[:, :, i] = np.clip(ch, 0, 255).astype(np.uint8)
    return rgb


def make_textured_glb(verts, faces, uv, tex_rgb, out_path):
    """Export a UV-mapped mesh with an embedded texture (cerebellum)."""
    pil_tex  = Image.fromarray(tex_rgb, 'RGB').convert('RGBA')
    material = trimesh.visual.texture.SimpleMaterial(image=pil_tex)
    vis      = trimesh.visual.TextureVisuals(uv=uv, material=material)
    mesh     = trimesh.Trimesh(vertices=verts, faces=faces,
                               visual=vis, process=False)
    mesh.export(str(out_path))
    sz = out_path.stat().st_size
    print(f"    Saved: {out_path.name}  ({sz/1e3:.0f} KB, "
          f"{len(verts):,} verts, {len(faces):,} faces)")


# ── Step 2: Brainstem ─────────────────────────────────────────────────────────

print("[2/3] Generating brainstem (HO thr0, step_size=1, sigma=0.8, UV+texture)...")

from nilearn import datasets as _ds

# Fetch Harvard-Oxford atlas via nilearn (auto-downloads)
print("    Fetching Harvard-Oxford subcortical atlas...")
ho = _ds.fetch_atlas_harvard_oxford("sub-maxprob-thr0-1mm")
ho_img  = nib.load(ho.maps) if isinstance(ho.maps, (str, bytes)) else ho.maps
if hasattr(ho_img, 'get_fdata'):
    ho_data = ho_img.get_fdata(dtype=np.float32)
else:
    ho_img = nib.load(str(ho.maps))
    ho_data = ho_img.get_fdata(dtype=np.float32)

# Brain-Stem = XML index 7 → atlas value 8 (1-indexed)
BRAINSTEM_VAL = 8
bs_mask = (ho_data == BRAINSTEM_VAL)
print(f"    Brainstem: {bs_mask.sum():,} voxels  (atlas value {BRAINSTEM_VAL})")

if bs_mask.sum() < 100:
    print("    ERROR: brainstem mask empty.");  sys.exit(1)

bs_verts, bs_faces = voxels_to_mesh(bs_mask, ho_img.affine,
                                     step_size=1, sigma=0.8)

# UV map + procedural texture (medulla / pons / midbrain zones)
print("    Computing spherical UV map for brainstem...")
bs_uv, bs_centroid = sphere_to_uv_brainstem(bs_verts)
print(f"    Centroid: {bs_centroid.round(3)}")
bs_faces_tex = remove_seam_faces(bs_uv, bs_faces)
print(f"    After seam removal: {len(bs_faces_tex):,} faces "
      f"({len(bs_faces) - len(bs_faces_tex):,} seam faces dropped)")

print("    Baking 512×512 brainstem texture (medulla/pons/midbrain)...")
bs_rgb = generate_brainstem_texture()
print(f"    Brainstem texture: {bs_rgb.shape}, range [{bs_rgb.min()},{bs_rgb.max()}]")

make_textured_glb(bs_verts, bs_faces_tex, bs_uv,
                  bs_rgb,
                  out_path=OUTPUT_DIR / "hires_brainstem.glb")

del ho_data, bs_mask, ho_img, bs_verts, bs_faces, bs_faces_tex, bs_uv, bs_rgb
gc.collect()


# ── Step 3: Cerebellum ────────────────────────────────────────────────────────

print("[3/3] Generating cerebellum (AAL SPM5, step_size=1, sigma=0.3 + folia texture)...")

# Fetch AAL atlas via nilearn (auto-downloads)
print("    Fetching AAL atlas...")
import ssl, requests as _req, warnings as _warn
_orig_ctx = ssl._create_default_https_context
ssl._create_default_https_context = ssl._create_unverified_context
# Monkeypatch requests to bypass SSL cert issues on Windows Python 3.14
_orig_send = _req.Session.send
def _patched_send(self, *args, **kwargs):
    kwargs['verify'] = False
    return _orig_send(self, *args, **kwargs)
_req.Session.send = _patched_send
_warn.filterwarnings('ignore', message='.*Unverified HTTPS.*')
try:
    aal = _ds.fetch_atlas_aal()
except Exception:
    aal = _ds.fetch_atlas_aal(version='SPM5')
ssl._create_default_https_context = _orig_ctx
_req.Session.send = _orig_send

aal_img  = nib.load(aal.maps) if isinstance(aal.maps, (str, bytes)) else aal.maps
if not hasattr(aal_img, 'get_fdata'):
    aal_img = nib.load(str(aal.maps))
aal_data = aal_img.get_fdata(dtype=np.float32)

# Collect cerebellum label values from the atlas metadata
cereb_vals = set()
for label, idx in zip(aal.labels, aal.indices):
    if "cerebel" in label.lower() or "vermis" in label.lower():
        cereb_vals.add(int(idx))

print(f"    Found {len(cereb_vals)} cerebellar label values "
      f"(range {min(cereb_vals)}..{max(cereb_vals)})")

cb_mask = np.isin(aal_data.astype(np.int32), sorted(cereb_vals))
print(f"    Cerebellum: {cb_mask.sum():,} voxels")

if cb_mask.sum() < 100:
    print("    ERROR: cerebellum mask empty.");  sys.exit(1)

# Low smoothing to preserve surface texture detail
cb_verts, cb_faces = voxels_to_mesh(cb_mask, aal_img.affine,
                                     step_size=1, sigma=0.3)
del aal_data, cb_mask, aal_img
gc.collect()

print(f"    Raw mesh: {len(cb_verts):,} verts, {len(cb_faces):,} faces")

# UV mapping
print("    Computing spherical UV map...")
cb_uv, cb_centroid = sphere_to_uv_cerebellum(cb_verts)
print(f"    Centroid: {cb_centroid.round(3)}")

# Remove seam faces
cb_faces_tex = remove_seam_faces(cb_uv, cb_faces)
print(f"    After seam removal: {len(cb_faces_tex):,} faces "
      f"({len(cb_faces) - len(cb_faces_tex):,} seam faces dropped)")

# Procedural folia texture
print(f"    Baking {TEX_W}×{TEX_H} folia texture...")
folia_rgb = generate_folia_texture()
print(f"    Folia texture: {folia_rgb.shape}, "
      f"range [{folia_rgb.min()},{folia_rgb.max()}]")

make_textured_glb(cb_verts, cb_faces_tex, cb_uv,
                  folia_rgb,
                  out_path=OUTPUT_DIR / "hires_cerebellum.glb")

print("\nDone!")
print(f"  data/brain_meshes/hires_brainstem.glb")
print(f"  data/brain_meshes/hires_cerebellum.glb")
