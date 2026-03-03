#!/usr/bin/env python3
"""
generate_parcellated_brain.py — Brain Pathology 3.0 Region Generator

Splits the fsaverage7 pial cortex into per-region meshes using the
Desikan-Killiany atlas (aparc.annot) and extracts subcortical structures
from FreeSurfer's aseg volumetric segmentation via marching cubes.

OUTPUTS (all in data/brain_meshes/):
  Cortical:
    frontal_lobe.glb        — merged DK parcels for frontal lobe
    prefrontal_cortex.glb   — superiorfrontal region (PFC proxy)
    brocas_area.glb         — parsopercularis + parstriangularis (LH only)
    motor_cortex.glb        — precentral gyrus
    somatosensory_cortex.glb — postcentral gyrus
    parietal_lobe.glb       — merged DK parcels for parietal lobe
    temporal_lobe.glb       — merged DK parcels for temporal lobe
    wernickes_area.glb      — superiortemporal posterior (LH only)
    occipital_lobe.glb      — merged DK parcels for occipital lobe
    cingulate_gyrus.glb     — rostral + caudal anterior + posterior cingulate
    medial_frontal.glb      — medialorbitofrontal + frontalpole
    full_hemisphere.glb     — entire right hemisphere (for glass mode)

  Subcortical (from aseg via marching cubes):
    thalamus.glb            — L+R thalamus
    hippocampus.glb         — L+R hippocampus
    amygdala.glb            — L+R amygdala
    caudate.glb             — L+R caudate nucleus
    putamen.glb             — L+R putamen
    globus_pallidus.glb     — L+R globus pallidus

  Already generated separately:
    brainstem.glb           — from generate_hires_subcortical.py
    cerebellum.glb          — from generate_hires_subcortical.py

  Manifest:
    brain_regions_manifest.json — file paths + metadata for brain-3d-v3.js

PREREQUISITES:
  pip install nibabel nilearn trimesh numpy scipy scikit-image pillow

USAGE:
  python generate_parcellated_brain.py
"""

import sys
import gc
import json
import time
import numpy as np
from pathlib import Path

print("=" * 60)
print("generate_parcellated_brain.py — Brain Pathology 3.0")
print("=" * 60)

print("\n[0/8] Importing libraries...")
import nibabel as nib
from nilearn import datasets
import trimesh
import trimesh.visual

# Optional: for subcortical marching cubes
try:
    from scipy import ndimage
    from skimage import measure
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("  WARNING: scipy/skimage not available — subcortical extraction skipped")

OUTPUT_DIR = Path("data/brain_meshes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — which DK parcels map to which EPPP-relevant regions
# ═══════════════════════════════════════════════════════════════════════════════

# Desikan-Killiany parcel names → our region IDs
# Each value is a list of DK parcel names (as they appear in aparc.annot)
DK_TO_REGION = {
    "frontal_lobe": [
        "superiorfrontal", "rostralmiddlefrontal", "caudalmiddlefrontal",
        "lateralorbitofrontal", "frontalpole",
        "parsopercularis", "parstriangularis", "parsorbitalis",
        "medialorbitofrontal", "paracentral",
    ],
    "prefrontal_cortex": [
        "superiorfrontal", "rostralmiddlefrontal", "frontalpole",
    ],
    "brocas_area": [
        "parsopercularis", "parstriangularis",
    ],
    "motor_cortex": [
        "precentral",
    ],
    "somatosensory_cortex": [
        "postcentral",
    ],
    "parietal_lobe": [
        "superiorparietal", "inferiorparietal",
        "supramarginal", "precuneus",
    ],
    "temporal_lobe": [
        "superiortemporal", "middletemporal", "inferiortemporal",
        "bankssts", "transversetemporal", "fusiform",
        "entorhinal", "temporalpole", "parahippocampal",
    ],
    "wernickes_area": [
        "superiortemporal",  # posterior portion — we'll use the full parcel
    ],
    "occipital_lobe": [
        "lateraloccipital", "cuneus", "pericalcarine", "lingual",
    ],
    "cingulate_gyrus": [
        "rostralanteriorcingulate", "caudalanteriorcingulate",
        "posteriorcingulate", "isthmuscingulate",
    ],
    "medial_frontal": [
        "medialorbitofrontal", "frontalpole",
    ],
    "insula": [
        "insula",
    ],
}

# Broca's and Wernicke's are left-hemisphere only
LH_ONLY_REGIONS = {"brocas_area", "wernickes_area"}

# FreeSurfer aseg label IDs for subcortical structures
ASEG_LABELS = {
    "thalamus":        [10, 49],     # Left=10, Right=49
    "hippocampus":     [17, 53],
    "amygdala":        [18, 54],
    "caudate":         [11, 50],
    "putamen":         [12, 51],
    "globus_pallidus": [13, 52],
    "nucleus_accumbens": [26, 58],
}

# Max faces per region mesh (decimate if exceeded)
MAX_FACES = 4000


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Load fsaverage7 surfaces + annotations
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1/8] Fetching fsaverage7 surfaces...")
surf = datasets.fetch_surf_fsaverage('fsaverage7')

print("[2/8] Loading pial surfaces + aparc annotations...")

# Left hemisphere
lh_pial   = nib.load(surf.pial_left)
lh_verts  = lh_pial.darrays[0].data.astype(np.float32)
lh_faces  = lh_pial.darrays[1].data.astype(np.int32)
print(f"  LH pial: {len(lh_verts):,} verts, {len(lh_faces):,} faces")

# Right hemisphere
rh_pial   = nib.load(surf.pial_right)
rh_verts  = rh_pial.darrays[0].data.astype(np.float32)
rh_faces  = rh_pial.darrays[1].data.astype(np.int32)
print(f"  RH pial: {len(rh_verts):,} verts, {len(rh_faces):,} faces")

# Load aparc annotation (Desikan-Killiany)
# Try to find the annotation files from FreeSurfer subjects directory
# They should be alongside the nilearn-downloaded data
import os

# nilearn stores fsaverage7 annotation files
fsavg_dir = Path(surf.pial_left).parent
lh_annot_path = fsavg_dir / "lh.aparc.annot"
rh_annot_path = fsavg_dir / "rh.aparc.annot"

# Alternative: check FreeSurfer subjects directory
FS_SUBJECTS = os.environ.get("SUBJECTS_DIR", "")
if not lh_annot_path.exists() and FS_SUBJECTS:
    lh_annot_path = Path(FS_SUBJECTS) / "fsaverage7" / "label" / "lh.aparc.annot"
    rh_annot_path = Path(FS_SUBJECTS) / "fsaverage7" / "label" / "rh.aparc.annot"

# Another fallback: nilearn data directory
if not lh_annot_path.exists():
    # Try nilearn's own downloaded copy
    nilearn_dir = Path(surf.pial_left).parent.parent
    for candidate in [
        nilearn_dir / "label" / "lh.aparc.annot",
        nilearn_dir / "lh.aparc.annot",
        Path.home() / "nilearn_data" / "freesurfer" / "fsaverage7" / "label" / "lh.aparc.annot",
    ]:
        if candidate.exists():
            lh_annot_path = candidate
            rh_annot_path = candidate.parent / "rh.aparc.annot"
            break

has_annot = lh_annot_path.exists() and rh_annot_path.exists()

if has_annot:
    print(f"  Loading annotations: {lh_annot_path}")
    lh_labels, lh_ctab, lh_names = nib.freesurfer.read_annot(str(lh_annot_path))
    rh_labels, rh_ctab, rh_names = nib.freesurfer.read_annot(str(rh_annot_path))
    # Decode label names
    lh_names = [n.decode('utf-8') if isinstance(n, bytes) else n for n in lh_names]
    rh_names = [n.decode('utf-8') if isinstance(n, bytes) else n for n in rh_names]
    print(f"  LH parcels: {len(lh_names)} ({', '.join(lh_names[:6])}...)")
    print(f"  RH parcels: {len(rh_names)} ({', '.join(rh_names[:6])}...)")
else:
    print("  WARNING: aparc.annot not found — will use bounding-box region extraction")
    print(f"  Looked in: {lh_annot_path}")
    lh_labels = lh_names = rh_labels = rh_names = None


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Compute coordinate transform (match hires brain GLB)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3/8] Computing coordinate transform...")

TRANSFORM_JSON = OUTPUT_DIR / "cortex_transform.json"

if TRANSFORM_JSON.exists():
    _t     = json.loads(TRANSFORM_JSON.read_text())
    centre = np.array(_t["centre"], dtype=np.float32)
    scale  = float(_t["scale"])
    print(f"  Loaded from {TRANSFORM_JSON.name}")
else:
    all_v  = np.vstack([lh_verts, rh_verts])
    centre = (all_v.max(axis=0) + all_v.min(axis=0)) * 0.5
    verts_c = all_v - centre
    scale  = float(2.0 / (verts_c.max(axis=0) - verts_c.min(axis=0)).max())
    del all_v, verts_c
    gc.collect()
    TRANSFORM_JSON.write_text(json.dumps(
        {"centre": [float(c) for c in centre], "scale": scale}, indent=2))
    print(f"  Computed and saved to {TRANSFORM_JSON.name}")

print(f"  centre={np.round(centre, 3)}, scale={scale:.8f}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Transform vertices to mesh coordinate space
# ═══════════════════════════════════════════════════════════════════════════════

# The existing brain-3d.js uses a different coordinate system:
# x = -x_FS (flip), y = z_FS (superior=up), z = y_FS (anterior=depth)
# Plus an offset. But the hires brain GLB uses FreeSurfer RAS directly,
# just centred and scaled. Let's match the hires brain's coordinate system.

lh_verts_mesh = ((lh_verts - centre) * scale).astype(np.float32)
rh_verts_mesh = ((rh_verts - centre) * scale).astype(np.float32)

# For the "full hemisphere" glass mesh, we combine both hemispheres
# but only keep the right hemisphere for the overlay
nv_lh = len(lh_verts_mesh)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Extract cortical regions
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[4/8] Extracting cortical regions from DK parcellation...")

manifest = {}


def extract_region_from_annot(region_id, dk_parcels, verts, faces, labels, names,
                              hemi_label="LH"):
    """
    Given a list of DK parcel names, find matching label indices,
    collect faces whose ALL 3 vertices are in those labels,
    and build a trimesh from the result.
    """
    # Find label indices for the requested parcels
    target_indices = set()
    for pname in dk_parcels:
        for i, n in enumerate(names):
            if n.lower() == pname.lower():
                target_indices.add(i)
                break

    if not target_indices:
        print(f"    {hemi_label} {region_id}: no matching parcels found for {dk_parcels}")
        return None, None

    # Find vertices belonging to these parcels
    vert_mask = np.zeros(len(verts), dtype=bool)
    for idx in target_indices:
        vert_mask |= (labels == idx)

    # Collect faces where ALL 3 vertices are in the target parcels
    face_mask = (vert_mask[faces[:, 0]] &
                 vert_mask[faces[:, 1]] &
                 vert_mask[faces[:, 2]])
    region_faces = faces[face_mask]

    if len(region_faces) == 0:
        print(f"    {hemi_label} {region_id}: 0 faces matched")
        return None, None

    # Re-index to use only needed vertices
    used_verts = np.unique(region_faces)
    new_index  = np.full(len(verts), -1, dtype=np.int32)
    new_index[used_verts] = np.arange(len(used_verts), dtype=np.int32)
    new_faces = new_index[region_faces]
    new_verts = verts[used_verts]

    return new_verts, new_faces


def decimate_if_needed(verts, faces, max_faces):
    """Decimate mesh if it exceeds max_faces."""
    if len(faces) <= max_faces:
        return verts, faces
    try:
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        decimated = mesh.simplify_quadric_decimation(max_faces)
        return decimated.vertices.astype(np.float32), decimated.faces.astype(np.int32)
    except Exception as e:
        print(f"    Decimation failed ({e}), keeping original {len(faces)} faces")
        return verts, faces


def export_region_glb(verts, faces, out_path, color=None):
    """Export a solid-color region mesh as GLB."""
    if color is None:
        color = [212, 170, 144, 255]  # default tissue color
    vertex_colors = np.tile(color, (len(verts), 1)).astype(np.uint8)
    vis = trimesh.visual.ColorVisuals(vertex_colors=vertex_colors)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, visual=vis, process=False)
    mesh.export(str(out_path))
    sz = out_path.stat().st_size
    return sz


# Process each cortical region
for region_id, dk_parcels in DK_TO_REGION.items():
    print(f"\n  Region: {region_id}")

    if not has_annot:
        print(f"    Skipped (no annotation data)")
        continue

    all_verts_list = []
    all_faces_list = []
    vert_offset = 0

    # Left hemisphere — always included for all regions
    v, f = extract_region_from_annot(
        region_id, dk_parcels,
        lh_verts_mesh, lh_faces, lh_labels, lh_names, "LH"
    )
    if v is not None:
        all_verts_list.append(v)
        all_faces_list.append(f + vert_offset)
        vert_offset += len(v)
        print(f"    LH: {len(v):,} verts, {len(f):,} faces")

    # Right hemisphere (skip for LH-only regions)
    if region_id not in LH_ONLY_REGIONS:
        v, f = extract_region_from_annot(
            region_id, dk_parcels,
            rh_verts_mesh, rh_faces, rh_labels, rh_names, "RH"
        )
        if v is not None:
            all_verts_list.append(v)
            all_faces_list.append(f + vert_offset)
            vert_offset += len(v)
            print(f"    RH: {len(v):,} verts, {len(f):,} faces")

    if not all_verts_list:
        print(f"    EMPTY — skipping")
        continue

    merged_verts = np.vstack(all_verts_list).astype(np.float32)
    merged_faces = np.vstack(all_faces_list).astype(np.int32)

    # Decimate if too large
    merged_verts, merged_faces = decimate_if_needed(merged_verts, merged_faces, MAX_FACES)

    out_path = OUTPUT_DIR / f"{region_id}.glb"
    sz = export_region_glb(merged_verts, merged_faces, out_path)

    manifest[region_id] = {
        "file": f"data/brain_meshes/{region_id}.glb",
        "type": "cortical",
        "vertexCount": len(merged_verts),
        "faceCount": len(merged_faces),
    }
    print(f"    Saved: {out_path.name} ({sz/1e3:.0f} KB, "
          f"{len(merged_verts):,} verts, {len(merged_faces):,} faces)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Full hemisphere for glass mode
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[5/8] Generating full hemisphere (glass overlay)...")

# Right hemisphere only — decimate aggressively for glass mode
rh_v, rh_f = decimate_if_needed(rh_verts_mesh, rh_faces, 18000)

out_path = OUTPUT_DIR / "full_hemisphere.glb"
sz = export_region_glb(rh_v, rh_f, out_path, color=[180, 160, 145, 80])
manifest["full_hemisphere"] = {
    "file": "data/brain_meshes/full_hemisphere.glb",
    "type": "glass",
    "vertexCount": len(rh_v),
    "faceCount": len(rh_f),
}
print(f"  Saved: {out_path.name} ({sz/1e3:.0f} KB, "
      f"{len(rh_v):,} verts, {len(rh_f):,} faces)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: Extract subcortical structures from aseg
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[6/8] Extracting subcortical structures from aseg...")

if HAS_SCIPY:
    # Try to find the aseg volume
    aseg_path = None

    # Check nilearn data directory for FreeSurfer aseg
    search_paths = [
        Path.home() / "nilearn_data" / "freesurfer" / "fsaverage7" / "mri" / "aseg.mgz",
        Path.home() / "nilearn_data" / "freesurfer" / "fsaverage" / "mri" / "aseg.mgz",
    ]
    if FS_SUBJECTS:
        search_paths.insert(0, Path(FS_SUBJECTS) / "fsaverage7" / "mri" / "aseg.mgz")
        search_paths.insert(1, Path(FS_SUBJECTS) / "fsaverage" / "mri" / "aseg.mgz")

    for p in search_paths:
        if p.exists():
            aseg_path = p
            break

    if aseg_path:
        print(f"  Loading: {aseg_path}")
        aseg_img = nib.load(str(aseg_path))
        aseg_data = aseg_img.get_fdata(dtype=np.float32)

        for region_id, label_vals in ASEG_LABELS.items():
            print(f"\n  Region: {region_id}")
            mask = np.zeros_like(aseg_data, dtype=bool)
            for lv in label_vals:
                mask |= (aseg_data == lv)
            nvox = mask.sum()
            print(f"    Voxels: {nvox:,} (labels {label_vals})")

            if nvox < 50:
                print(f"    Too few voxels — skipping")
                continue

            try:
                # Smooth slightly and march
                smoothed = ndimage.gaussian_filter(mask.astype(np.float32), sigma=0.5)
                verts_v, faces_mc, _, _ = measure.marching_cubes(
                    smoothed, level=0.5, step_size=1)
                ones = np.ones((len(verts_v), 1), dtype=np.float32)
                verts_mm = (aseg_img.affine @ np.hstack(
                    [verts_v.astype(np.float32), ones]).T).T[:, :3]
                verts_ms = ((verts_mm - centre) * scale).astype(np.float32)
                faces_mc = faces_mc.astype(np.int32)

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
                print(f"    Saved: {out_path.name} ({sz/1e3:.0f} KB, "
                      f"{len(verts_ms):,} verts, {len(faces_mc):,} faces)")

            except Exception as e:
                print(f"    Marching cubes failed: {e}")

        del aseg_data, aseg_img
        gc.collect()
    else:
        print("  WARNING: aseg.mgz not found — subcortical GLBs not regenerated")
        print("  Existing subcortical GLBs (if any) will be preserved in manifest")
        # Preserve existing subcortical entries
        for region_id in ASEG_LABELS:
            glb_path = OUTPUT_DIR / f"{region_id}.glb"
            if glb_path.exists():
                manifest[region_id] = {
                    "file": f"data/brain_meshes/{region_id}.glb",
                    "type": "subcortical",
                }
                print(f"  Preserved existing: {region_id}.glb")
else:
    print("  Skipped (scipy/skimage not available)")
    for region_id in ASEG_LABELS:
        glb_path = OUTPUT_DIR / f"{region_id}.glb"
        if glb_path.exists():
            manifest[region_id] = {
                "file": f"data/brain_meshes/{region_id}.glb",
                "type": "subcortical",
            }
            print(f"  Preserved existing: {region_id}.glb")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: Preserve brainstem + cerebellum (generated separately)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[7/8] Checking brainstem + cerebellum...")

for rid, fname in [("brainstem", "hires_brainstem.glb"), ("cerebellum", "hires_cerebellum.glb")]:
    p = OUTPUT_DIR / fname
    if p.exists():
        manifest[rid] = {
            "file": f"data/brain_meshes/{fname}",
            "type": "subcortical",
        }
        print(f"  Found: {fname} ({p.stat().st_size/1e3:.0f} KB)")
    else:
        # Fall back to non-hires version
        p2 = OUTPUT_DIR / f"{rid}.glb"
        if p2.exists():
            manifest[rid] = {
                "file": f"data/brain_meshes/{rid}.glb",
                "type": "subcortical",
            }
            print(f"  Found fallback: {rid}.glb ({p2.stat().st_size/1e3:.0f} KB)")
        else:
            print(f"  WARNING: {rid} not found — run generate_hires_subcortical.py first")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8: Write manifest
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[8/8] Writing manifest...")

manifest_path = OUTPUT_DIR.parent / "brain_regions_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"  Saved: {manifest_path}")
print(f"  Regions: {len(manifest)}")

print("\n" + "=" * 60)
print("Done! Generated region meshes:")
for rid, entry in sorted(manifest.items()):
    verts = entry.get("vertexCount", "?")
    faces = entry.get("faceCount", "?")
    print(f"  {rid:30s} {entry['type']:12s} {verts:>6} verts  {faces:>6} faces")
print("=" * 60)
