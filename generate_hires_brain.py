#!/usr/bin/env python3
"""
generate_hires_brain.py

Downloads FreeSurfer fsaverage7 (163k verts / 328k faces per hemisphere)
via nilearn, UV-maps both hemispheres, bakes a sulcal-depth texture, and
exports a single GLB with embedded texture.

Outputs:
  data/brain_meshes/full_brain_hires.glb      (~20 MB, embedded texture)
  data/brain_meshes/full_brain_sulcal.png     (4096×2048 sulcal depth map)
"""

import sys, time
import numpy as np
from pathlib import Path

print("[1/7] Importing libraries...")
import nibabel as nib
from nilearn import datasets
import matplotlib
matplotlib.use('Agg')
import matplotlib.tri as mtri
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
import trimesh
import trimesh.visual

OUTPUT_DIR = Path("data/brain_meshes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEX_W, TEX_H = 4096, 2048

# ── 1. Download fsaverage7 ────────────────────────────────────────────────────
print("[2/7] Fetching fsaverage7 via nilearn (downloads ~80 MB on first run)...")
surf = datasets.fetch_surf_fsaverage('fsaverage7')

# ── 2. Load pial surfaces ─────────────────────────────────────────────────────
print("[3/7] Loading pial surfaces...")
lh_pial = nib.load(surf.pial_left)
lh_verts = lh_pial.darrays[0].data.astype(np.float32)
lh_faces = lh_pial.darrays[1].data.astype(np.int32)
print(f"    LH pial : {len(lh_verts):>7,} verts  {len(lh_faces):>7,} faces")

rh_pial = nib.load(surf.pial_right)
rh_verts = rh_pial.darrays[0].data.astype(np.float32)
rh_faces = rh_pial.darrays[1].data.astype(np.int32)
print(f"    RH pial : {len(rh_verts):>7,} verts  {len(rh_faces):>7,} faces")

# ── 3. Load curvature (sulcal proxy) ──────────────────────────────────────────
print("[4/7] Loading curvature maps (sulcal depth proxy)...")
lh_curv = nib.load(surf.curv_left).darrays[0].data.astype(np.float32)
rh_curv = nib.load(surf.curv_right).darrays[0].data.astype(np.float32)

# ── 4. Load sphere, compute UV ────────────────────────────────────────────────
print("[5/7] Computing UV coordinates from sphere surfaces...")
lh_sph = nib.load(surf.sphere_left).darrays[0].data.astype(np.float32)
rh_sph = nib.load(surf.sphere_right).darrays[0].data.astype(np.float32)

def sphere_to_uv(sph):
    """Equirectangular projection: sphere -> [0,1]²"""
    r = np.linalg.norm(sph, axis=1, keepdims=True)
    n = sph / np.maximum(r, 1e-9)
    u = (np.arctan2(n[:, 1], n[:, 0]) + np.pi) / (2.0 * np.pi)
    v = np.arccos(np.clip(n[:, 2], -1.0, 1.0)) / np.pi
    return np.stack([u, v], axis=1).astype(np.float32)

lh_uv_full = sphere_to_uv(lh_sph)   # u in [0,1]
rh_uv_full = sphere_to_uv(rh_sph)   # u in [0,1]

# Pack hemispheres side by side: LH -> [0.0, 0.5],  RH -> [0.5, 1.0]
lh_uv = lh_uv_full.copy();  lh_uv[:, 0] *= 0.5
rh_uv = rh_uv_full.copy();  rh_uv[:, 0] = 0.5 + rh_uv_full[:, 0] * 0.5

def remove_seam_faces(uv, faces):
    """Drop triangles that straddle the u=0/1 wrap seam (back of head)."""
    u0 = uv[faces[:, 0], 0]
    u1 = uv[faces[:, 1], 0]
    u2 = uv[faces[:, 2], 0]
    span = np.maximum(np.maximum(u0, u1), u2) - np.minimum(np.minimum(u0, u1), u2)
    return faces[span < 0.25]   # 0.25 = half of 0.5 (each hemi occupies 0.5 of total width)

lh_faces_tex = remove_seam_faces(lh_uv, lh_faces)
rh_faces_tex = remove_seam_faces(rh_uv, rh_faces)
print(f"    After seam removal: LH {len(lh_faces_tex):,}  RH {len(rh_faces_tex):,} tex-faces")

# ── 5. Bake sulcal texture ────────────────────────────────────────────────────
print(f"[6/7] Baking {TEX_W}×{TEX_H} sulcal texture (may take 2–5 min)...")

# Colour ramp: sulci (curv<0) = dark reddish-brown  ->  gyri (curv>0) = flesh peach
SULCI_COL = np.array([55, 18, 8],    dtype=np.float32)   # #371208
GYRI_COL  = np.array([221, 184, 152], dtype=np.float32)  # #DDB898

def curv_to_rgb(curv_grid_masked):
    """Map curvature masked-array to uint8 RGB (H×W×3). Stays in float32."""
    filled = np.ma.filled(curv_grid_masked, fill_value=np.float32(0.0)).astype(np.float32)
    t = np.clip(filled, np.float32(-0.5), np.float32(0.5)) + np.float32(0.5)  # [0,1]
    # Build channels independently to minimise peak allocation
    rgb = np.empty((*t.shape, 3), dtype=np.uint8)
    one = np.float32(1.0)
    for i in range(3):
        ch = SULCI_COL[i] * (one - t) + GYRI_COL[i] * t
        np.clip(ch, 0, 255, out=ch)
        rgb[:, :, i] = ch.astype(np.uint8)
    # Outside-brain pixels -> flesh background
    if hasattr(curv_grid_masked, 'mask'):
        mask = np.ma.getmaskarray(curv_grid_masked)
        if mask.any():
            rgb[mask] = GYRI_COL.astype(np.uint8)
    return rgb

# Sample grid: left half covers u∈[0, 0.5],  right half covers u∈[0.5, 1.0]
gx_l = np.linspace(0.0, 0.5, TEX_W // 2, dtype=np.float32)
gx_r = np.linspace(0.5, 1.0, TEX_W // 2, dtype=np.float32)
gy   = np.linspace(0.0, 1.0, TEX_H,      dtype=np.float32)

GX_l, GY = np.meshgrid(gx_l, gy)
GX_r, _  = np.meshgrid(gx_r, gy)

import gc

STRIP_H = 64   # small strips to minimise peak allocation per batch

def bake_to_rgb(uv, faces, curv, gx, gy):
    """
    Interpolate curvature onto a grid and immediately convert to uint8 RGB,
    processing row-strips so only one strip is live at a time.
    Returns (TEX_H, len(gx), 3) uint8 array.
    """
    tri    = mtri.Triangulation(uv[:, 0], uv[:, 1], faces)
    interp = mtri.LinearTriInterpolator(tri, curv)
    rows   = np.empty((len(gy), len(gx), 3), dtype=np.uint8)
    one    = np.float32(1.0)

    for y0 in range(0, len(gy), STRIP_H):
        y1        = min(y0 + STRIP_H, len(gy))
        GXs, GYs  = np.meshgrid(gx, gy[y0:y1])
        strip_ma  = interp(GXs, GYs)                         # masked float64
        filled    = np.ma.filled(strip_ma, np.float32(0.0)).astype(np.float32)
        t         = np.clip(filled, np.float32(-0.5), np.float32(0.5)) + np.float32(0.5)
        for i in range(3):
            ch = SULCI_COL[i] * (one - t) + GYRI_COL[i] * t
            rows[y0:y1, :, i] = np.clip(ch, 0, 255).astype(np.uint8)
        # Restore outside-brain pixels to flesh
        mask = np.ma.getmaskarray(strip_ma)
        if mask.any():
            rows[y0:y1][mask] = GYRI_COL.astype(np.uint8)
        del GXs, GYs, strip_ma, filled, t
    return rows

t0 = time.time()
print("    Baking left hemisphere...")
rgb_l = bake_to_rgb(lh_uv, lh_faces_tex, lh_curv, gx_l, gy)
print(f"    LH done in {time.time()-t0:.1f}s — freeing LH bake data...")
del lh_faces_tex, lh_curv, lh_sph, lh_pial   # keep lh_uv, lh_verts, lh_faces for GLB
gc.collect()

t0 = time.time()
print("    Baking right hemisphere...")
rgb_r = bake_to_rgb(rh_uv, rh_faces_tex, rh_curv, gx_r, gy)
print(f"    RH done in {time.time()-t0:.1f}s")
del rh_faces_tex, rh_curv, rh_sph, rh_pial   # keep rh_uv, rh_verts, rh_faces for GLB
gc.collect()

rgb = np.hstack([rgb_l, rgb_r])   # (TEX_H, TEX_W, 3)
del rgb_l, rgb_r
gc.collect()

tex_path = OUTPUT_DIR / 'full_brain_sulcal.png'
Image.fromarray(rgb).save(str(tex_path))
print(f"    Texture saved: {tex_path}  ({tex_path.stat().st_size/1e6:.1f} MB)")

# ── 6. Merge hemispheres ──────────────────────────────────────────────────────
print("[7/7] Merging hemispheres, centering, exporting GLB...")

nv_lh        = len(lh_verts)
rh_faces_off = rh_faces + nv_lh

all_verts = np.vstack([lh_verts, rh_verts])
all_faces = np.vstack([lh_faces, rh_faces_off]).astype(np.int32)
all_uv    = np.vstack([lh_uv, rh_uv]).astype(np.float32)

# Centre and scale to fit roughly in a ±1 cube (matching existing mesh convention)
centre = (all_verts.max(axis=0) + all_verts.min(axis=0)) * 0.5
verts  = (all_verts - centre).astype(np.float32)
scale  = 2.0 / (verts.max(axis=0) - verts.min(axis=0)).max()
verts *= scale

print(f"    Vertices : {len(verts):,}")
print(f"    Faces    : {len(all_faces):,}")
print(f"    Bounds   : {verts.min(axis=0).round(3)}  ->  {verts.max(axis=0).round(3)}")

# Build textured trimesh
pil_tex  = Image.open(tex_path).convert('RGBA')
material = trimesh.visual.texture.SimpleMaterial(image=pil_tex)
vis      = trimesh.visual.TextureVisuals(uv=all_uv, material=material)
mesh     = trimesh.Trimesh(vertices=verts, faces=all_faces, visual=vis, process=False)

glb_path = OUTPUT_DIR / 'full_brain_hires.glb'
mesh.export(str(glb_path))
sz = glb_path.stat().st_size / 1e6
print(f"    GLB saved : {glb_path}  ({sz:.1f} MB)")

print("\n✓  All done!")
print(f"   Texture : {tex_path}")
print(f"   GLB     : {glb_path}")
