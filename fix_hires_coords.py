#!/usr/bin/env python3
"""
fix_hires_coords.py

Regenerates full_brain_hires.glb using the SAME coordinate transform
as the per-region GLBs (generate_brain_meshes.py / generate_subcortical.py):
    output = [-x_fs, z_fs, y_fs] * (1/75) + COORD_OFFSET

COORD_OFFSET = [0.118, -0.204, 0.438]  (left-hemisphere centroid -> CAM_TARGET)

This aligns the hires visual brain with the region-overlay meshes so the
hybrid brain-3d.js can stack them correctly.

Reuses the existing full_brain_sulcal.png — no texture baking, runs in ~30s.
"""

import sys
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path("data/brain_meshes")

# ── Coordinate transform (must match generate_subcortical.py exactly) ──────────
COORD_SCALE  = 1.0 / 75.0
COORD_OFFSET = np.array([0.118, -0.204, 0.438], dtype=np.float64)


def to_threejs(coords_fs):
    """
    FreeSurfer RAS (x=right, y=anterior, z=superior) in mm
    → Three.js (x=-right, y=superior, z=anterior) scaled + offset
    """
    c = np.asarray(coords_fs, dtype=np.float64)
    x_out = -c[:, 0]   # negate: left-hemi lateral (−x_fs) → +x_3js
    y_out =  c[:, 2]   # superior (z_fs) → up (y_3js)
    z_out =  c[:, 1]   # anterior (y_fs) → depth (z_3js)
    return (np.column_stack([x_out, y_out, z_out]) * COORD_SCALE + COORD_OFFSET).astype(np.float32)


def sphere_to_uv(sph):
    """Equirectangular projection matching generate_hires_brain.py."""
    r = np.linalg.norm(sph, axis=1, keepdims=True)
    n = sph / np.maximum(r, 1e-9)
    u = (np.arctan2(n[:, 1], n[:, 0]) + np.pi) / (2.0 * np.pi)
    v = np.arccos(np.clip(n[:, 2], -1.0, 1.0)) / np.pi
    return np.stack([u, v], axis=1).astype(np.float32)


def remove_seam_faces(uv, faces):
    """Drop triangles straddling the u=0/1 wrap seam."""
    u0 = uv[faces[:, 0], 0]
    u1 = uv[faces[:, 1], 0]
    u2 = uv[faces[:, 2], 0]
    span = np.maximum(np.maximum(u0, u1), u2) - np.minimum(np.minimum(u0, u1), u2)
    return faces[span < 0.25]


print("=" * 60)
print("fix_hires_coords.py")
print("Regenerating full_brain_hires.glb in region-GLB coordinate space")
print("=" * 60)

# ── [1] Imports ─────────────────────────────────────────────────────────────────
print("\n[1/5] Importing libraries...")
import nibabel as nib
from nilearn import datasets
from PIL import Image
import trimesh
import trimesh.visual

# ── [2] Load surfaces ─────────────────────────────────────────────────────────
print("[2/5] Loading fsaverage7 pial + sphere surfaces...")
surf = datasets.fetch_surf_fsaverage('fsaverage7')

lh_pial  = nib.load(surf.pial_left)
lh_verts_fs = lh_pial.darrays[0].data.astype(np.float32)
lh_faces    = lh_pial.darrays[1].data.astype(np.int32)

rh_pial  = nib.load(surf.pial_right)
rh_verts_fs = rh_pial.darrays[0].data.astype(np.float32)
rh_faces    = rh_pial.darrays[1].data.astype(np.int32)

print(f"  LH: {len(lh_verts_fs):,} verts  {len(lh_faces):,} faces")
print(f"  RH: {len(rh_verts_fs):,} verts  {len(rh_faces):,} faces")

lh_sph = nib.load(surf.sphere_left ).darrays[0].data.astype(np.float32)
rh_sph = nib.load(surf.sphere_right).darrays[0].data.astype(np.float32)

# ── [3] UV coordinates ─────────────────────────────────────────────────────────
print("[3/5] Computing UV (sphere projection)...")

lh_uv_full = sphere_to_uv(lh_sph)
rh_uv_full = sphere_to_uv(rh_sph)

# Pack hemispheres side by side: LH→[0,0.5], RH→[0.5,1.0]
lh_uv = lh_uv_full.copy();  lh_uv[:, 0] *= 0.5
rh_uv = rh_uv_full.copy();  rh_uv[:, 0] = 0.5 + rh_uv_full[:, 0] * 0.5

lh_faces = remove_seam_faces(lh_uv, lh_faces)
rh_faces = remove_seam_faces(rh_uv, rh_faces)
print(f"  After seam removal: LH {len(lh_faces):,}  RH {len(rh_faces):,}")

# ── [4] Apply coordinate transform ─────────────────────────────────────────────
print("[4/5] Applying [-x, z, y] * 1/75 + COORD_OFFSET transform...")
print(f"  COORD_OFFSET = {COORD_OFFSET}")

lh_verts_3d = to_threejs(lh_verts_fs)
rh_verts_3d = to_threejs(rh_verts_fs)

nv_lh = len(lh_verts_3d)
rh_faces_off = rh_faces + nv_lh

all_verts = np.vstack([lh_verts_3d, rh_verts_3d])
all_faces = np.vstack([lh_faces, rh_faces_off]).astype(np.int32)
all_uv    = np.vstack([lh_uv, rh_uv]).astype(np.float32)

bbox_min = all_verts.min(axis=0)
bbox_max = all_verts.max(axis=0)
print(f"  Vertices : {len(all_verts):,}")
print(f"  Faces    : {len(all_faces):,}")
print(f"  Bounds   : {bbox_min.round(3)}  ->  {bbox_max.round(3)}")
print(f"  Center   : {((bbox_min + bbox_max) / 2).round(3)}")

# ── [5] Build + export GLB ────────────────────────────────────────────────────
print("[5/5] Building GLB with existing sulcal texture...")

tex_path = OUTPUT_DIR / 'full_brain_sulcal.png'
if not tex_path.exists():
    print(f"  ERROR: {tex_path} not found. Run generate_hires_brain.py first.")
    sys.exit(1)

pil_tex  = Image.open(str(tex_path)).convert('RGBA')
material = trimesh.visual.texture.SimpleMaterial(image=pil_tex)
vis      = trimesh.visual.TextureVisuals(uv=all_uv, material=material)
mesh     = trimesh.Trimesh(vertices=all_verts, faces=all_faces, visual=vis, process=False)

glb_path = OUTPUT_DIR / 'full_brain_hires.glb'
mesh.export(str(glb_path))
sz = glb_path.stat().st_size / 1e6
print(f"  GLB saved: {glb_path}  ({sz:.1f} MB)")

print("\n✓  Done!")
print("  full_brain_hires.glb now uses the same coordinate system as region GLBs.")
print("  Left hemisphere lateral surface is at +x, y=superior, z=anterior.")
print("  CAM_TARGET (0.55, 0.05, 0.10) is in the left-hemisphere centroid.")
