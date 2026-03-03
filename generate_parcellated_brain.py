#!/usr/bin/env python3
"""
generate_parcellated_brain.py — Brain Pathology 3.0 Region Generator (v2)

Uses the Harvard-Oxford CORTICAL atlas (volumetric, MNI space) to project
parcellation labels onto fsaverage7 pial surface vertices. This avoids
the need for FreeSurfer annotation files (aparc.annot).

For subcortical structures, uses the Harvard-Oxford SUBCORTICAL atlas
(same approach as generate_hires_subcortical.py) via marching cubes.

OUTPUTS (all in data/brain_meshes/):
  Cortical (surface projection from HO cortical atlas):
    frontal_lobe.glb, prefrontal_cortex.glb, brocas_area.glb,
    motor_cortex.glb, somatosensory_cortex.glb, parietal_lobe.glb,
    temporal_lobe.glb, wernickes_area.glb, occipital_lobe.glb,
    cingulate_gyrus.glb, medial_frontal.glb, insula.glb,
    full_hemisphere.glb (glass mode)

  Subcortical (marching cubes from HO subcortical atlas):
    thalamus.glb, hippocampus.glb, amygdala.glb,
    caudate.glb, putamen.glb, globus_pallidus.glb,
    nucleus_accumbens.glb

  brainstem + cerebellum: generated separately (JSON meshes)

  brain_regions_manifest.json — metadata for brain-3d-v3.js

USAGE:
  pip install nibabel nilearn trimesh numpy scipy scikit-image fast_simplification
  python generate_parcellated_brain.py
"""

import sys, gc, json, os, ssl, time
import warnings
import numpy as np
from pathlib import Path

print("=" * 60)
print("generate_parcellated_brain.py — Brain Pathology 3.0 (v2)")
print("=" * 60)

print("\n[0] Importing libraries...")
import nibabel as nib
from scipy import ndimage
from skimage import measure
import trimesh

# SSL workaround for Windows
ssl._create_default_https_context = ssl._create_unverified_context
import requests as _req
_orig_send = _req.Session.send
def _patched_send(self, *a, **kw):
    kw['verify'] = False
    return _orig_send(self, *a, **kw)
_req.Session.send = _patched_send
warnings.filterwarnings('ignore', message='.*Unverified.*')

from nilearn import datasets

OUTPUT_DIR = Path("data/brain_meshes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COORDINATE TRANSFORM
# ═══════════════════════════════════════════════════════════════════════════════

# The existing full_brain_hires.glb uses Transform B: (verts - centre) * scale
# This is loaded by brain-3d-v3.js via GLTFLoader.
# Region overlays must use the SAME transform so they align with the cortex.

TRANSFORM_JSON = OUTPUT_DIR / "cortex_transform.json"


# ═══════════════════════════════════════════════════════════════════════════════
# HO CORTICAL ATLAS → EPPP REGION MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

# Harvard-Oxford cortical label indices → our EPPP region IDs
# Each key is our region ID; each value is a list of HO cortical label indices
HO_TO_REGION = {
    "frontal_lobe": [
        1,   # Frontal Pole
        3,   # Superior Frontal Gyrus
        4,   # Middle Frontal Gyrus
        5,   # IFG pars triangularis
        6,   # IFG pars opercularis
        7,   # Precentral Gyrus
        25,  # Frontal Medial Cortex
        26,  # Juxtapositional Lobule (SMA)
        33,  # Frontal Orbital Cortex
        41,  # Frontal Opercular Cortex
    ],
    "prefrontal_cortex": [
        1,   # Frontal Pole
        3,   # Superior Frontal Gyrus
        4,   # Middle Frontal Gyrus
        33,  # Frontal Orbital Cortex
    ],
    "brocas_area": [
        5,   # IFG pars triangularis
        6,   # IFG pars opercularis
    ],
    "motor_cortex": [
        7,   # Precentral Gyrus
        26,  # Juxtapositional Lobule (SMA)
    ],
    "somatosensory_cortex": [
        17,  # Postcentral Gyrus
    ],
    "parietal_lobe": [
        17,  # Postcentral Gyrus
        18,  # Superior Parietal Lobule
        19,  # Supramarginal Gyrus ant
        20,  # Supramarginal Gyrus post
        21,  # Angular Gyrus
        31,  # Precuneous Cortex
    ],
    "temporal_lobe": [
        8,   # Temporal Pole
        9,   # STG anterior
        10,  # STG posterior
        11,  # MTG anterior
        12,  # MTG posterior
        13,  # MTG temporooccipital
        14,  # ITG anterior
        15,  # ITG posterior
        16,  # ITG temporooccipital
        34,  # Parahippocampal ant
        35,  # Parahippocampal post
        37,  # Temporal Fusiform ant
        38,  # Temporal Fusiform post
        44,  # Planum Polare
        45,  # Heschl's Gyrus
        46,  # Planum Temporale
    ],
    "wernickes_area": [
        10,  # STG posterior
        46,  # Planum Temporale
    ],
    "occipital_lobe": [
        22,  # Lateral Occipital sup
        23,  # Lateral Occipital inf
        24,  # Intracalcarine Cortex
        32,  # Cuneal Cortex
        36,  # Lingual Gyrus
        39,  # Temporal Occipital Fusiform
        40,  # Occipital Fusiform
        47,  # Supracalcarine Cortex
        48,  # Occipital Pole
    ],
    "cingulate_gyrus": [
        28,  # Paracingulate Gyrus
        29,  # Cingulate ant
        30,  # Cingulate post
        27,  # Subcallosal Cortex
    ],
    "medial_frontal": [
        25,  # Frontal Medial Cortex
        1,   # Frontal Pole
    ],
    "insula": [
        2,   # Insular Cortex
        42,  # Central Opercular Cortex
    ],
}

# Broca's and Wernicke's: left-hemisphere only
LH_ONLY_REGIONS = {"brocas_area", "wernickes_area"}

# Harvard-Oxford subcortical atlas label values for marching cubes
HO_SUBCORTICAL = {
    "thalamus":          [4, 15],   # L Thal=4, R Thal=15
    "hippocampus":       [6, 17],   # L Hipp=6, R Hipp=17
    "amygdala":          [5, 16],   # L Amyg=5, R Amyg=16
    "caudate":           [3, 14],   # L Caud=3, R Caud=14
    "putamen":           [7, 18],   # L Put=7, R Put=18
    "globus_pallidus":   [8, 19],   # L GP=8, R GP=19
    "nucleus_accumbens": [9, 20],   # L NAcc=9, R NAcc=20
}

# Max faces per region mesh
MAX_FACES = 4000


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def decimate_if_needed(verts, faces, max_faces):
    """Decimate mesh if it exceeds max_faces."""
    if len(faces) <= max_faces:
        return verts, faces
    try:
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        decimated = mesh.simplify_quadric_decimation(face_count=max_faces)
        return decimated.vertices.astype(np.float32), decimated.faces.astype(np.int32)
    except Exception as e:
        print(f"    Decimation failed ({e}), keeping original {len(faces)} faces")
        return verts, faces


def export_region_glb(verts, faces, out_path, color=None):
    """Export a region mesh as GLB (geometry only, no vertex colors).
    JS replaces materials anyway, so ColorVisuals is unnecessary and
    causes deeply nested GLTF scene graphs that overflow the stack."""
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    mesh.export(str(out_path))
    return out_path.stat().st_size


def voxel_label_for_vertices(verts_mni, atlas_data, atlas_affine):
    """
    For each surface vertex (in MNI mm), find the atlas voxel label.
    Uses nearest-neighbor lookup in the volumetric atlas.
    """
    # MNI mm → voxel indices via inverse affine
    inv_affine = np.linalg.inv(atlas_affine)
    ones = np.ones((len(verts_mni), 1), dtype=np.float64)
    coords_h = np.hstack([verts_mni.astype(np.float64), ones])
    vox_coords = (inv_affine @ coords_h.T).T[:, :3]

    # Round to nearest voxel
    vox_ijk = np.round(vox_coords).astype(np.int32)

    # Clamp to volume bounds
    for dim in range(3):
        vox_ijk[:, dim] = np.clip(vox_ijk[:, dim], 0, atlas_data.shape[dim] - 1)

    # Look up labels
    labels = atlas_data[vox_ijk[:, 0], vox_ijk[:, 1], vox_ijk[:, 2]]
    return labels.astype(np.int32)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Load fsaverage7 surfaces
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1/7] Fetching fsaverage7 pial surfaces...")
surf = datasets.fetch_surf_fsaverage('fsaverage7')

lh_pial = nib.load(surf.pial_left)
lh_verts_mni = lh_pial.darrays[0].data.astype(np.float32)
lh_faces = lh_pial.darrays[1].data.astype(np.int32)
print(f"  LH pial: {len(lh_verts_mni):,} verts, {len(lh_faces):,} faces")

rh_pial = nib.load(surf.pial_right)
rh_verts_mni = rh_pial.darrays[0].data.astype(np.float32)
rh_faces = rh_pial.darrays[1].data.astype(np.int32)
print(f"  RH pial: {len(rh_verts_mni):,} verts, {len(rh_faces):,} faces")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Load/compute coordinate transform
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[2/7] Loading coordinate transform...")
if TRANSFORM_JSON.exists():
    _t = json.loads(TRANSFORM_JSON.read_text())
    centre = np.array(_t["centre"], dtype=np.float32)
    scale = float(_t["scale"])
    print(f"  Loaded: centre={np.round(centre,3)}, scale={scale:.8f}")
else:
    all_v = np.vstack([lh_verts_mni, rh_verts_mni])
    centre = (all_v.max(axis=0) + all_v.min(axis=0)) * 0.5
    verts_c = all_v - centre
    scale = float(2.0 / (verts_c.max(axis=0) - verts_c.min(axis=0)).max())
    TRANSFORM_JSON.write_text(json.dumps(
        {"centre": [float(c) for c in centre], "scale": scale}, indent=2))
    print(f"  Computed: centre={np.round(centre,3)}, scale={scale:.8f}")

# Transform to mesh space (same as full_brain_hires.glb)
lh_verts_mesh = ((lh_verts_mni - centre) * scale).astype(np.float32)
rh_verts_mesh = ((rh_verts_mni - centre) * scale).astype(np.float32)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Label surface vertices from HO cortical atlas
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3/7] Loading Harvard-Oxford cortical atlas and labeling vertices...")
ho_cort = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-1mm")
ho_cort_img = nib.load(ho_cort.maps) if isinstance(ho_cort.maps, (str, bytes)) else ho_cort.maps
if not hasattr(ho_cort_img, 'get_fdata'):
    ho_cort_img = nib.load(str(ho_cort.maps))
ho_cort_data = ho_cort_img.get_fdata(dtype=np.float32)

print(f"  Atlas shape: {ho_cort_data.shape}, {len(ho_cort.labels)} labels")
print(f"  Projecting labels onto {len(lh_verts_mni) + len(rh_verts_mni):,} surface vertices...")

lh_labels = voxel_label_for_vertices(lh_verts_mni, ho_cort_data, ho_cort_img.affine)
rh_labels = voxel_label_for_vertices(rh_verts_mni, ho_cort_data, ho_cort_img.affine)

# Count labeled vertices
lh_labeled = np.sum(lh_labels > 0)
rh_labeled = np.sum(rh_labels > 0)
print(f"  LH: {lh_labeled:,}/{len(lh_labels):,} vertices labeled ({100*lh_labeled/len(lh_labels):.1f}%)")
print(f"  RH: {rh_labeled:,}/{len(rh_labels):,} vertices labeled ({100*rh_labeled/len(rh_labels):.1f}%)")

del ho_cort_data, ho_cort_img
gc.collect()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Extract cortical regions
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[4/7] Extracting cortical regions...")

manifest = {}


def extract_region(region_id, ho_indices, verts, faces, labels, hemi):
    """Extract faces where all 3 vertices have labels in ho_indices."""
    vert_mask = np.zeros(len(verts), dtype=bool)
    for idx in ho_indices:
        vert_mask |= (labels == idx)

    face_mask = (vert_mask[faces[:, 0]] &
                 vert_mask[faces[:, 1]] &
                 vert_mask[faces[:, 2]])
    region_faces = faces[face_mask]

    if len(region_faces) == 0:
        return None, None

    # Re-index vertices
    used = np.unique(region_faces)
    new_idx = np.full(len(verts), -1, dtype=np.int32)
    new_idx[used] = np.arange(len(used), dtype=np.int32)
    return verts[used], new_idx[region_faces]


for region_id, ho_indices in HO_TO_REGION.items():
    all_verts = []
    all_faces = []
    offset = 0

    # Left hemisphere
    v, f = extract_region(region_id, ho_indices, lh_verts_mesh, lh_faces, lh_labels, "LH")
    if v is not None:
        all_verts.append(v)
        all_faces.append(f + offset)
        offset += len(v)

    # Right hemisphere (skip for LH-only regions)
    if region_id not in LH_ONLY_REGIONS:
        v, f = extract_region(region_id, ho_indices, rh_verts_mesh, rh_faces, rh_labels, "RH")
        if v is not None:
            all_verts.append(v)
            all_faces.append(f + offset)
            offset += len(v)

    if not all_verts:
        print(f"  {region_id}: EMPTY — skipping")
        continue

    merged_v = np.vstack(all_verts).astype(np.float32)
    merged_f = np.vstack(all_faces).astype(np.int32)

    # Decimate if needed
    merged_v, merged_f = decimate_if_needed(merged_v, merged_f, MAX_FACES)

    out_path = OUTPUT_DIR / f"{region_id}.glb"
    sz = export_region_glb(merged_v, merged_f, out_path)

    # Compute bounds
    bmin = merged_v.min(axis=0).tolist()
    bmax = merged_v.max(axis=0).tolist()

    manifest[region_id] = {
        "file": f"data/brain_meshes/{region_id}.glb",
        "type": "cortical",
        "vertexCount": len(merged_v),
        "faceCount": len(merged_f),
        "bounds": {"min": bmin, "max": bmax},
    }
    print(f"  {region_id}: {len(merged_v):,} verts, {len(merged_f):,} faces ({sz/1e3:.0f} KB)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Full hemisphere for glass mode
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[5/7] Generating full hemisphere (glass overlay)...")

# Use right hemisphere, decimate for performance
rh_v, rh_f = decimate_if_needed(rh_verts_mesh, rh_faces, 18000)
out_path = OUTPUT_DIR / "full_hemisphere.glb"
sz = export_region_glb(rh_v, rh_f, out_path, color=[180, 160, 145, 80])

bmin = rh_v.min(axis=0).tolist()
bmax = rh_v.max(axis=0).tolist()
manifest["full_hemisphere"] = {
    "file": "data/brain_meshes/full_hemisphere.glb",
    "type": "glass",
    "vertexCount": len(rh_v),
    "faceCount": len(rh_f),
    "bounds": {"min": bmin, "max": bmax},
}
print(f"  full_hemisphere: {len(rh_v):,} verts, {len(rh_f):,} faces ({sz/1e3:.0f} KB)")

del rh_v, rh_f
gc.collect()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: Subcortical structures via marching cubes
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[6/7] Extracting subcortical structures (HO subcortical atlas)...")

ho_sub = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr0-1mm")
ho_sub_img = nib.load(ho_sub.maps) if isinstance(ho_sub.maps, (str, bytes)) else ho_sub.maps
if not hasattr(ho_sub_img, 'get_fdata'):
    ho_sub_img = nib.load(str(ho_sub.maps))
ho_sub_data = ho_sub_img.get_fdata(dtype=np.float32)

print(f"  Subcortical atlas: {ho_sub_data.shape}")
print(f"  Labels: {ho_sub.labels[:10]}...")

for region_id, label_vals in HO_SUBCORTICAL.items():
    mask = np.zeros_like(ho_sub_data, dtype=bool)
    for lv in label_vals:
        mask |= (ho_sub_data == lv)
    nvox = mask.sum()

    if nvox < 50:
        print(f"  {region_id}: {nvox} voxels — too few, skipping")
        continue

    try:
        smoothed = ndimage.gaussian_filter(mask.astype(np.float32), sigma=0.5)
        verts_v, faces_mc, _, _ = measure.marching_cubes(smoothed, level=0.5, step_size=1)
        ones = np.ones((len(verts_v), 1), dtype=np.float32)
        verts_mm = (ho_sub_img.affine @ np.hstack([verts_v.astype(np.float32), ones]).T).T[:, :3]
        # Transform B: same as cortex
        verts_ms = ((verts_mm - centre) * scale).astype(np.float32)
        faces_mc = faces_mc.astype(np.int32)

        # Fix face winding
        centroid = verts_ms.mean(axis=0)
        v0, v1, v2 = verts_ms[faces_mc[:, 0]], verts_ms[faces_mc[:, 1]], verts_ms[faces_mc[:, 2]]
        fn = np.cross(v1 - v0, v2 - v0)
        fc = (v0 + v1 + v2) / 3.0
        dots = np.sum(fn * (fc - centroid), axis=1)
        inward = dots < 0
        if inward.sum() > len(faces_mc) // 2:
            faces_mc = faces_mc[:, ::-1]
        elif inward.sum() > 0:
            faces_mc[inward] = faces_mc[inward][:, ::-1]

        # Decimate
        verts_ms, faces_mc = decimate_if_needed(verts_ms, faces_mc, MAX_FACES)

        out_path = OUTPUT_DIR / f"{region_id}.glb"
        sz = export_region_glb(verts_ms, faces_mc, out_path)

        manifest[region_id] = {
            "file": f"data/brain_meshes/{region_id}.glb",
            "type": "subcortical",
            "vertexCount": len(verts_ms),
            "faceCount": len(faces_mc),
        }
        print(f"  {region_id}: {len(verts_ms):,} verts, {len(faces_mc):,} faces "
              f"({nvox:,} vox, {sz/1e3:.0f} KB)")

    except Exception as e:
        print(f"  {region_id}: marching cubes failed — {e}")
        # Preserve existing GLB if available
        glb_path = OUTPUT_DIR / f"{region_id}.glb"
        if glb_path.exists():
            manifest[region_id] = {
                "file": f"data/brain_meshes/{region_id}.glb",
                "type": "subcortical",
            }
            print(f"    Preserved existing: {region_id}.glb")

del ho_sub_data, ho_sub_img
gc.collect()


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: Brainstem + cerebellum + manifest
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[7/7] Finalizing manifest...")

# Brainstem + cerebellum are generated by generate_subcortical_json.py (JSON meshes)
# They are loaded separately in brain-3d-v3.js, not via the manifest.
# But include them in manifest for reference.
for rid, fname in [("brainstem", "hires_brainstem.glb"), ("cerebellum", "hires_cerebellum.glb")]:
    p = OUTPUT_DIR / fname
    if p.exists():
        manifest[rid] = {"file": f"data/brain_meshes/{fname}", "type": "subcortical"}
        print(f"  {rid}: {p.stat().st_size/1e3:.0f} KB")

manifest_path = OUTPUT_DIR.parent / "brain_regions_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"\n  Manifest: {manifest_path} ({len(manifest)} regions)")

# Restore SSL
ssl._create_default_https_context = ssl._create_default_https_context
_req.Session.send = _orig_send

print("\n" + "=" * 60)
print("Done! Generated region meshes:")
for rid, entry in sorted(manifest.items()):
    v = entry.get("vertexCount", "?")
    f = entry.get("faceCount", "?")
    print(f"  {rid:30s} {entry['type']:12s} {str(v):>6} verts  {str(f):>6} faces")
print("=" * 60)
