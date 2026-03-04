#!/usr/bin/env python3
"""
generate_brain_meshes.py — One-time mesh generation for JustinMasteryPage 3D brain.

Produces anatomically-accurate GLTF meshes from freely available neuroimaging atlases.

Sources:
  Cortical surface  : nilearn fsaverage5 pial + Destrieux 2009 parcellation
  Subcortical       : Harvard-Oxford subcortical atlas (marching cubes)
  Cerebellum        : AAL atlas (marching cubes, all cerebellar parcels merged)
  Glass brain shell : Full left hemisphere pial (simplified)

Outputs:
  data/brain_meshes/{region_id}.glb    — binary GLTF per region
  data/brain_regions_manifest.json     — index of all generated meshes

Usage:
  pip install nilearn nibabel trimesh pygltflib numpy scipy scikit-image
  python generate_brain_meshes.py

Coordinate transform (FreeSurfer/MNI -> Three.js):
  FreeSurfer RAS: x=right, y=anterior, z=superior
  Three.js:       x=right, y=up(superior), z=toward-viewer(anterior)
  Left hemisphere: negate x so lateral surface is at +x (matches camera convention)
  -> out = [-x_fs, z_fs, y_fs] * COORD_SCALE + COORD_OFFSET

COORD_SCALE  = 1/75  (places brain in ~2-unit bounding box, matching existing ellipsoid brain)
COORD_OFFSET = computed from surface centroid to align with current CAM_TARGET (0.55, 0.05, 0.10)
"""

import json
import sys
import traceback
import numpy as np
from pathlib import Path

# ─── Output paths ──────────────────────────────────────────────────────────────

OUT_DIR       = Path("data/brain_meshes")
MANIFEST_PATH = Path("data/brain_regions_manifest.json")

# ─── Coordinate transform ──────────────────────────────────────────────────────

COORD_SCALE   = 1.0 / 75.0
# CAM_TARGET in brain-3d.js is (0.55, 0.05, 0.10).
# COORD_OFFSET is computed at runtime from the surface centroid so the brain
# is centred at CAM_TARGET.  Set to zero here; overwritten in main().
COORD_OFFSET  = np.array([0.0, 0.0, 0.0], dtype=np.float64)

# Max faces per mesh type — set high to preserve all available detail
MAX_FACES_CORTICAL    = 999_999
MAX_FACES_SUBCORTICAL = 999_999
MAX_FACES_GLASS       = 999_999
MAX_FACES_CEREBELLUM  = 999_999

# ─── Region mappings ────────────────────────────────────────────────────────────

# Destrieux 2009 atlas labels -> brain region IDs.
# Reference: Destrieux et al. (2010) NeuroImage 53(1):1-15
# Label names match those stored in the nilearn-fetched GIFTI / .annot files.
# Overlapping label sets are intentional: Broca's area overlaps frontal_lobe, etc.
DESTRIEUX_REGIONS = {

    "frontal_lobe": [
        # Precentral gyrus (primary motor cortex, BA4) IS part of the frontal
        # lobe — it is the posterior-most frontal gyrus, bounded by the central
        # sulcus posteriorly. Added G_precentral + related paracentral/precentral
        # sulcal labels for correct anatomical extent.
        "G_precentral", "G_and_S_paracentral",
        "S_precentral-inf-part", "S_precentral-sup-part",
        "G_front_sup", "G_front_middle",
        "G_front_inf-Opercular", "G_front_inf-Orbital", "G_front_inf-Triangul",
        "G_and_S_transv_frontopol", "G_and_S_frontomargin",
        "G_orbital", "G_rectus", "G_subcallosal",
        "S_front_sup", "S_front_middle", "S_front_inf",
        "S_suborbital", "S_orbital-H_Shaped", "S_orbital_lateral",
        "S_orbital_med-olfact",
        "Lat_Fis-ant-Horizont", "Lat_Fis-ant-Vertical",
    ],

    "prefrontal_cortex": [
        # Full anatomical PFC — everything anterior to premotor cortex (BA6).
        # DLPFC (BA 9/46): dorsolateral prefrontal cortex
        "G_front_sup", "G_front_middle",
        "S_front_sup", "S_front_middle",
        # VLPFC (BA 45/47): ventrolateral prefrontal cortex
        "G_front_inf-Triangul", "G_front_inf-Orbital",
        # OFC (BA 11/13): orbitofrontal cortex
        "G_orbital", "G_rectus", "G_subcallosal",
        "S_suborbital", "S_orbital-H_Shaped", "S_orbital_lateral",
        "S_orbital_med-olfact",
        # Frontopolar (BA 10): anterior-most PFC
        "G_and_S_transv_frontopol", "G_and_S_frontomargin",
    ],

    "brocas_area": [
        # Strictly BA 44 (pars opercularis) + BA 45 (pars triangularis).
        # G_front_inf-Orbital (BA 47, pars orbitalis) removed — it is
        # adjacent but not part of classic Broca's language area.
        # Fissure labels removed — they are sulcal boundaries, not cortex.
        "G_front_inf-Opercular",
        "G_front_inf-Triangul",
    ],

    "motor_cortex": [
        "G_precentral", "G_and_S_paracentral",
        "S_central", "S_precentral-inf-part", "S_precentral-sup-part",
    ],

    "parietal_lobe": [
        "G_parietal_sup", "G_pariet_inf-Angular", "G_pariet_inf-Supramar",
        "G_precuneus",
        "S_intrapariet_and_P_trans", "S_parieto_occipital",
        "S_subparietal", "S_postcentral",
    ],

    "somatosensory_cortex": [
        "G_postcentral",
        "S_postcentral", "S_central",
    ],

    "temporal_lobe": [
        "G_temp_sup-Lateral", "G_temp_sup-Plan_polar",
        "G_temp_sup-Plan_tempo", "G_temp_sup-G_T_transv",
        "G_temporal_middle", "G_temporal_inf",
        "G_oc-temp_med-Parahip", "G_oc-temp_lat-fusifor",
        "Pole_temporal",
        "S_temporal_sup", "S_temporal_inf", "S_temporal_transverse",
        "Lat_Fis-post",
        "S_oc-temp_lat", "S_oc-temp_med_and_Lingual",
        "S_collat_transv_ant", "S_collat_transv_post",
    ],

    "wernickes_area": [
        # Planum temporale (BA 22 posterior) is the anatomical core of
        # Wernicke's area. G_temp_sup-Lateral was removed — it spans the
        # ENTIRE lateral STG (anterior pole to posterior), causing the mesh
        # to extend far too anteriorly (z-error > 0.40 in scene units).
        "G_temp_sup-Plan_tempo",
        "Lat_Fis-post",
    ],

    "occipital_lobe": [
        "G_cuneus", "G_occipital_sup", "G_occipital_middle",
        "G_oc-temp_lat-fusifor", "G_oc-temp_med-Lingual",
        "G_and_S_occipital_inf", "Pole_occipital",
        "S_calcarine", "S_oc_middle_and_Lunatus",
        "S_oc_sup_and_transversal", "S_oc-temp_med_and_Lingual",
        "S_occipital_ant", "S_parieto_occipital",
    ],

    "cingulate_gyrus": [
        "G_and_S_cingul-Ant", "G_and_S_cingul-Mid-Ant",
        "G_and_S_cingul-Mid-Post",
        "G_cingul-Post-dorsal", "G_cingul-Post-ventral",
        "S_cingul-Marginalis", "S_pericallosal",
    ],

    "medial_frontal": [
        "G_and_S_frontomargin", "G_and_S_transv_frontopol",
        "G_rectus", "G_subcallosal",
        "S_suborbital", "S_orbital_med-olfact",
    ],
}

# Harvard-Oxford subcortical atlas label alternatives.
# Each list is tried in order; both exact and case-insensitive partial matching
# are attempted, to handle label wording differences between atlas versions.
HO_SUBCORTICAL = {
    "thalamus":         ["Left Thalamus", "Left Thalamus Proper", "Thalamus"],
    "hippocampus":      ["Left Hippocampus", "Hippocampus"],
    "amygdala":         ["Left Amygdala", "Amygdala"],
    "caudate":          ["Left Caudate", "Caudate"],
    "putamen":          ["Left Putamen", "Putamen"],
    "globus_pallidus":  ["Left Pallidum", "Pallidum", "Left Globus Pallidus"],
    "brainstem":        ["Brain-Stem", "Brain Stem", "Brainstem"],
}

# ─── Coordinate helpers ─────────────────────────────────────────────────────────

def to_threejs(coords_fs):
    """
    Transform FreeSurfer RAS (or MNI) mm coordinates to Three.js world units.

    FreeSurfer RAS convention:  x=right, y=anterior, z=superior
    Three.js convention:        x=right, y=up(superior), z=toward-viewer(anterior)

    For the left hemisphere pial surface, x values are negative (leftward).
    We negate x so that the lateral surface (most negative x) maps to
    positive x in Three.js — this matches the camera position in brain-3d.js
    which views the lateral surface from positive x.

    Scale factor (COORD_SCALE = 1/75) converts mm to Three.js units so the
    whole brain is ~2 units wide, matching the existing ellipsoid brain.
    COORD_OFFSET centres the brain at the camera target.
    """
    c = np.asarray(coords_fs, dtype=np.float64)
    x_out =  -c[:, 0]   # negate: lateral(-x_fs) -> +x_3js
    y_out =   c[:, 2]   # superior (z_fs) -> up (y_3js)
    z_out =   c[:, 1]   # anterior (y_fs) -> depth (z_3js)
    return (np.column_stack([x_out, y_out, z_out]) * COORD_SCALE + COORD_OFFSET).astype(np.float32)

# ─── Parcellation loader ────────────────────────────────────────────────────────

def load_parcellation(filepath):
    """
    Load a surface parcellation from a file path.
    Handles FreeSurfer .annot and GIFTI formats.

    Returns:
        label_data  : (N_verts,) int32 array — one label key per vertex
        key_to_name : dict mapping int key -> str region name
    """
    import nibabel as nib
    fp = str(filepath)

    if fp.endswith(".annot"):
        # nibabel freesurfer reader: returns (labels, ctab, names)
        # With orig_ids=False (default), labels are 0..N-1 indices into names.
        # Value -1 indicates medial wall / unlabelled vertices.
        labels, _ctab, names = nib.freesurfer.io.read_annot(fp)
        key_to_name = {-1: "unknown"}
        for i, nm in enumerate(names):
            key_to_name[i] = nm.decode() if isinstance(nm, bytes) else str(nm)
        return labels.astype(np.int32), key_to_name

    # GIFTI annotation format (.label.gii, .annot.gii, .gii)
    img = nib.load(fp)
    label_data = img.darrays[0].data.astype(np.int32)
    key_to_name = {}
    try:
        table = img.labeltable.labels
        if table:
            for lbl in table:
                nm = lbl.label
                key_to_name[lbl.key] = nm.decode() if isinstance(nm, bytes) else str(nm)
    except Exception:
        pass

    if not key_to_name:
        # Fallback: assume consecutive 0-indexed keys
        for k in range(int(label_data.max()) + 1):
            key_to_name[k] = f"region_{k}"

    return label_data, key_to_name


def load_destrieux_parcellation(destrieux):
    """
    Load Destrieux atlas parcellation, handling nilearn API differences.

    nilearn < 0.10 : destrieux.map_left is a file path (str)
    nilearn >= 0.10 : destrieux.map_left is already a numpy array

    In the numpy-array case the integer values are direct indices into
    destrieux.labels (i.e., map_left[v] == i means labels[i] is the region).

    Returns:
        label_data  : (N_verts,) int32 array
        key_to_name : dict mapping int key -> str region name
    """
    map_left = destrieux.map_left

    # Detect numpy array (nilearn >= 0.10 returns the data directly)
    if isinstance(map_left, np.ndarray) or (
        hasattr(map_left, "__array__") and not isinstance(map_left, (str, bytes, Path))
    ):
        label_data = np.asarray(map_left, dtype=np.int32)
        key_to_name = {}
        for i, nm in enumerate(destrieux.labels):
            key_to_name[i] = nm.decode() if isinstance(nm, bytes) else str(nm)
        return label_data, key_to_name

    # File path case (older nilearn)
    return load_parcellation(str(map_left))

# ─── Mesh helpers ───────────────────────────────────────────────────────────────

def make_submesh(verts, faces, vertex_mask):
    """
    Extract sub-mesh from a full surface using a boolean vertex mask.
    Only includes faces whose three vertices are ALL inside the mask (no partial faces).
    Returns a trimesh.Trimesh or None if the result is empty.
    """
    import trimesh
    if not np.any(vertex_mask):
        return None

    # Keep only faces where every vertex passes the mask
    face_mask  = np.all(vertex_mask[faces], axis=1)
    sub_faces  = faces[face_mask]
    if len(sub_faces) == 0:
        return None

    # Compact: drop unreferenced vertices, remap face indices
    used        = np.unique(sub_faces)
    remap       = np.zeros(len(verts), dtype=np.int64)
    remap[used] = np.arange(len(used))

    # process=False: avoid trimesh 4.x fill_holes() which hangs on open meshes.
    # The atlas surface is already clean; no extra processing needed.
    mesh = trimesh.Trimesh(
        vertices = verts[used],
        faces    = remap[sub_faces],
        process  = False,
    )
    return mesh if len(mesh.faces) > 0 else None


def simplify(mesh, target_faces):
    """
    Simplify mesh to ≤ target_faces triangles using quadratic decimation.
    Falls back silently if simplification is unavailable or fails.
    """
    if len(mesh.faces) <= target_faces:
        return mesh
    # trimesh 4.x simplify_quadric_decimation takes target_reduction (0-1 fraction to REMOVE)
    target_reduction = max(0.0, 1.0 - (target_faces / len(mesh.faces)))
    m = getattr(mesh, 'simplify_quadric_decimation', None)
    if m is not None:
        try:
            s = m(target_reduction)
            if s is not None and len(s.faces) > 0:
                return s
        except Exception as e:
            print(f"      [warn] simplify_quadric_decimation failed: {e}")
    return mesh


def save_glb(mesh, path):
    """Export trimesh to GLB (binary GLTF single-file format). Returns True on success."""
    try:
        data = mesh.export(file_type="glb")
        Path(path).write_bytes(data)
        return True
    except Exception as e:
        print(f"      [error] export failed -> {path}: {e}")
        return False


def mesh_bounds(mesh):
    b = mesh.bounds
    return {"min": b[0].tolist(), "max": b[1].tolist()}


def load_nifti(obj):
    """
    Load a NIfTI image from either a file path or an already-loaded image object.

    nilearn >= 0.13 returns atlas .maps as a Nifti1Image directly.
    Older nilearn returns a file path string.
    This helper handles both cases transparently.
    """
    import nibabel as nib
    if isinstance(obj, (str, bytes)) or hasattr(obj, '__fspath__'):
        return nib.load(obj)
    # Already a nibabel image object
    return obj


# ─── Harvard-Oxford label search ────────────────────────────────────────────────

def find_ho_idx(ho_labels_list, options):
    """
    Find the NIfTI integer value for a subcortical region in the Harvard-Oxford atlas.

    ho_labels_list : list where index i corresponds to NIfTI value i.
                     (In nilearn 0.13.1+, simply list(ho.labels) — Background is ho.labels[0])
    options        : list of candidate label strings to try, in priority order.

    Tries exact case-insensitive match first, then substring match.
    Returns the integer NIfTI value, or None if not found.
    """
    lowered = [(i, nm.strip().lower()) for i, nm in enumerate(ho_labels_list)]
    for opt in options:
        opt_l = opt.strip().lower()
        # Exact match
        for i, nm in lowered:
            if nm == opt_l:
                return i
        # Substring match (opt is contained in atlas label or vice-versa)
        for i, nm in lowered:
            if opt_l in nm or nm in opt_l:
                return i
    return None


# ─── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    global COORD_OFFSET

    import nibabel as nib
    from nilearn import datasets
    from nilearn.surface import load_surf_mesh
    import trimesh
    from skimage.measure import marching_cubes

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 1 — Cortical surfaces  (fsaverage5 pial + Destrieux atlas)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STAGE 1/4  Cortical surfaces (fsaverage5 + Destrieux)")
    print("=" * 60)

    print("  Fetching fsaverage5 surface ...")
    fsavg = datasets.fetch_surf_fsaverage(mesh="fsaverage5")
    print("  Loading left pial surface ...")
    coords_fs, faces = load_surf_mesh(fsavg.pial_left)
    coords_fs = np.asarray(coords_fs, dtype=np.float64)
    faces     = np.asarray(faces,     dtype=np.int64)
    print(f"  Pial surface: {len(coords_fs):,} verts, {len(faces):,} faces")

    print("  Fetching Destrieux atlas ...")
    destrieux = datasets.fetch_atlas_surf_destrieux()
    print("  Loading parcellation ...")
    label_data, key_to_name = load_destrieux_parcellation(destrieux)
    uniq_vals = np.unique(label_data)
    print(f"  Parcellation: {len(key_to_name)} labels, "
          f"vertex value range [{uniq_vals.min()}..{uniq_vals.max()}]")
    print(f"  Sample labels: {list(key_to_name.items())[:5]}")
    sys.stdout.flush()

    # Build reverse lookup: name -> list of integer keys
    name_to_keys = {}
    for k, nm in key_to_name.items():
        name_to_keys.setdefault(nm, []).append(k)

    # Diagnostic: report any target labels absent from this atlas version
    all_target = {lbl for v in DESTRIEUX_REGIONS.values() for lbl in v}
    missing    = all_target - set(name_to_keys)
    if missing:
        print(f"  [info] {len(missing)} target label(s) not in this atlas version "
              f"(they will be silently skipped):")
        for m in sorted(missing)[:10]:
            print(f"         '{m}'")
        if len(missing) > 10:
            print(f"         ... and {len(missing)-10} more")

    # ── Compute coordinate offset so the brain centroid aligns with CAM_TARGET ──
    # Use the full surface (medial wall excluded via Destrieux labels) to find
    # the actual centroid, then shift to match brain-3d.js CAM_TARGET.
    MEDIAL_NAMES = {
        "Medial_wall", "Unknown", "unknown", "???", "corpuscallosum",
        "Background+FreeSurfer_Defined_Medial_Wall", "Medial Wall",
    }
    medial_keys   = {k for nm, ks in name_to_keys.items()
                     if nm in MEDIAL_NAMES for k in ks}
    lateral_mask  = ~np.isin(label_data, list(medial_keys))

    # Use the same hardcoded offset as fix_hires_coords.py so region
    # overlays align exactly with the hires cortex GLB.
    COORD_OFFSET = np.array([0.118, -0.204, 0.438], dtype=np.float64)
    print(f"  Coordinate offset (hardcoded, matches cortex GLB): {COORD_OFFSET}")

    # Now re-compute with final offset
    coords_3d = to_threejs(coords_fs)

    # ── Export cortical region meshes ─────────────────────────────────────────
    for region_id, target_labels in DESTRIEUX_REGIONS.items():
        print(f"  Processing {region_id} ..."); sys.stdout.flush()
        vertex_mask = np.zeros(len(coords_fs), dtype=bool)
        for lbl in target_labels:
            for k in name_to_keys.get(lbl, []):
                vertex_mask |= (label_data == k)
        if not vertex_mask.any():
            print(f"  [skip] {region_id}: no matching vertices"); sys.stdout.flush()
            continue

        mesh = make_submesh(coords_3d, faces, vertex_mask)
        if mesh is None:
            print(f"  [skip] {region_id}: empty mesh after extraction"); sys.stdout.flush()
            continue

        print(f"    mesh: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces"); sys.stdout.flush()
        mesh = simplify(mesh, MAX_FACES_CORTICAL)
        print(f"    simplified: {len(mesh.faces):,} faces"); sys.stdout.flush()
        out  = OUT_DIR / f"{region_id}.glb"
        if save_glb(mesh, out):
            manifest[region_id] = {
                "file":        f"data/brain_meshes/{region_id}.glb",
                "type":        "cortical",
                "vertexCount": len(mesh.vertices),
                "faceCount":   len(mesh.faces),
                "bounds":      mesh_bounds(mesh),
            }
            print(f"  OK {region_id}: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")
            sys.stdout.flush()

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 2 — Glass brain (full hemisphere shell)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STAGE 2/4  Glass brain (full hemisphere shell)")
    print("=" * 60)

    glass_mask = ~np.isin(label_data, list(medial_keys))
    glass_mesh = make_submesh(coords_3d, faces, glass_mask)
    if glass_mesh is not None:
        glass_mesh = simplify(glass_mesh, MAX_FACES_GLASS)
        out = OUT_DIR / "full_hemisphere.glb"
        if save_glb(glass_mesh, out):
            manifest["full_hemisphere"] = {
                "file":        "data/brain_meshes/full_hemisphere.glb",
                "type":        "glass",
                "vertexCount": len(glass_mesh.vertices),
                "faceCount":   len(glass_mesh.faces),
                "bounds":      mesh_bounds(glass_mesh),
            }
            print(f"  OK full_hemisphere: {len(glass_mesh.vertices):,} verts, "
                  f"{len(glass_mesh.faces):,} faces")
    else:
        print("  [warn] Glass brain mesh is empty")

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 3 — Subcortical structures (Harvard-Oxford atlas)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STAGE 3/4  Subcortical (Harvard-Oxford sub-maxprob-thr25-1mm)")
    print("=" * 60)

    try:
        print("  Fetching atlas ...")
        ho = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-1mm")
        ho_img    = load_nifti(ho.maps)
        ho_data   = ho_img.get_fdata()
        ho_affine = ho_img.affine
        # nilearn 0.13.1+ includes 'Background' as ho.labels[0], so NIfTI value i
        # maps directly to ho.labels[i] — no manual prepend needed.
        # Older code prepended "background" which caused a 1-position shift,
        # making every structure fetch the NEXT label's voxels (GP→brainstem, etc.).
        ho_labels_with_bg = list(ho.labels)
        print(f"  Atlas loaded: {len(ho.labels)} regions")

        for region_id, label_opts in HO_SUBCORTICAL.items():
            idx = find_ho_idx(ho_labels_with_bg, label_opts)
            if idx is None:
                print(f"  [skip] {region_id}: label not found in atlas")
                print(f"         Tried: {label_opts}")
                # Print first 15 labels to help debugging
                print(f"         Available (first 15): {ho_labels_with_bg[1:16]}")
                continue

            matched_name = ho_labels_with_bg[idx]
            vol = (ho_data == idx).astype(np.float32)

            # For all structures except the brainstem (which is midline),
            # mask out right-hemisphere voxels before marching cubes.
            # Some HO atlas versions use bilateral labels (e.g. "Pallidum")
            # that contaminate the left-hemisphere mesh with right-side voxels.
            if region_id != "brainstem":
                xi, yi, zi = np.meshgrid(
                    np.arange(vol.shape[0]), np.arange(vol.shape[1]),
                    np.arange(vol.shape[2]), indexing="ij")
                vox_coords = np.column_stack([xi.ravel(), yi.ravel(),
                                              zi.ravel(), np.ones(xi.size)])
                mni_x = (ho_affine @ vox_coords.T)[0].reshape(vol.shape)
                # MNI x > 5 mm is right hemisphere; zero those voxels out
                vol[mni_x > 5] = 0
                print(f"    left-hemi filter: {int(vol.sum())} voxels remaining")

            if vol.sum() < 20:
                print(f"  [skip] {region_id}: <20 voxels (atlas value {idx}, "
                      f"'{matched_name}')")
                continue

            # Marching cubes in voxel space, then transform to Three.js
            verts_v, mc_faces, _, _ = marching_cubes(vol, level=0.5)
            # Apply full affine: voxel index -> MNI mm
            ones      = np.ones((len(verts_v), 1))
            verts_mni = (ho_affine @ np.hstack([verts_v, ones]).T).T[:, :3]
            verts_3d  = to_threejs(verts_mni)

            mesh = trimesh.Trimesh(vertices=verts_3d, faces=mc_faces, process=False)
            mesh = simplify(mesh, MAX_FACES_SUBCORTICAL)

            out = OUT_DIR / f"{region_id}.glb"
            if save_glb(mesh, out):
                manifest[region_id] = {
                    "file":        f"data/brain_meshes/{region_id}.glb",
                    "type":        "subcortical",
                    "vertexCount": len(mesh.vertices),
                    "faceCount":   len(mesh.faces),
                    "bounds":      mesh_bounds(mesh),
                }
                print(f"  OK {region_id} ('{matched_name}'): "
                      f"{len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")

    except Exception as e:
        print(f"  [ERROR] Subcortical pipeline failed: {e}")
        traceback.print_exc()
        print("  -> Subcortical structures will be absent from manifest.")

    # ═══════════════════════════════════════════════════════════════════════════
    # STAGE 4 — Cerebellum (AAL atlas, all cerebellar parcels merged)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STAGE 4/4  Cerebellum (AAL atlas)")
    print("=" * 60)

    try:
        # Windows Python 3.12+ may fail SSL certificate verification for some
        # atlas download hosts.  Disable verification for this one-time script.
        import ssl
        _orig_ctx = ssl._create_default_https_context
        ssl._create_default_https_context = ssl._create_unverified_context

        print("  Fetching AAL atlas ...")
        try:
            aal = datasets.fetch_atlas_aal()
        except Exception as e_aal:
            print(f"  [warn] Default AAL fetch failed ({e_aal}), trying version='SPM5' ...")
            aal = datasets.fetch_atlas_aal(version='SPM5')

        # Restore SSL context
        ssl._create_default_https_context = _orig_ctx

        aal_img    = load_nifti(aal.maps)
        aal_data   = aal_img.get_fdata()
        aal_affine = aal_img.affine

        # aal.indices[i] is the integer value in the NIfTI that corresponds to
        # aal.labels[i].  Use int() because some nilearn versions store strings.
        cereb_vol   = np.zeros(aal_data.shape, dtype=np.float32)
        cereb_count = 0
        for label, idx in zip(aal.labels, aal.indices):
            if "cerebel" in label.lower() or "vermis" in label.lower():
                cereb_vol[aal_data == int(idx)] = 1.0
                cereb_count += 1

        print(f"  Combined {cereb_count} cerebellar parcels")
        if cereb_vol.sum() < 20:
            print("  [warn] No cerebellar voxels found — check AAL labels")
        else:
            verts_v, mc_faces, _, _ = marching_cubes(cereb_vol, level=0.5)
            ones      = np.ones((len(verts_v), 1))
            verts_mni = (aal_affine @ np.hstack([verts_v, ones]).T).T[:, :3]
            verts_3d  = to_threejs(verts_mni)

            mesh = trimesh.Trimesh(vertices=verts_3d, faces=mc_faces, process=False)
            mesh = simplify(mesh, MAX_FACES_CEREBELLUM)

            out = OUT_DIR / "cerebellum.glb"
            if save_glb(mesh, out):
                manifest["cerebellum"] = {
                    "file":        "data/brain_meshes/cerebellum.glb",
                    "type":        "cortical",
                    "vertexCount": len(mesh.vertices),
                    "faceCount":   len(mesh.faces),
                    "bounds":      mesh_bounds(mesh),
                }
                print(f"  OK cerebellum: {len(mesh.vertices):,} verts, "
                      f"{len(mesh.faces):,} faces")

    except Exception as e:
        print(f"  [ERROR] Cerebellum pipeline failed: {e}")
        traceback.print_exc()

    # ═══════════════════════════════════════════════════════════════════════════
    # Write manifest
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("Writing manifest")
    print("=" * 60)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  {MANIFEST_PATH}  ({len(manifest)} regions)")

    # Summary by type
    by_type = {}
    for r, info in manifest.items():
        by_type.setdefault(info["type"], []).append(r)
    for t in sorted(by_type):
        print(f"  {t:12s}: {', '.join(sorted(by_type[t]))}")

    # Warn if expected regions are missing
    expected = set(DESTRIEUX_REGIONS) | set(HO_SUBCORTICAL) | {"cerebellum", "full_hemisphere"}
    missing_from_manifest = expected - set(manifest)
    if missing_from_manifest:
        print(f"\n  [warn] {len(missing_from_manifest)} expected region(s) not in manifest:")
        for m in sorted(missing_from_manifest):
            print(f"         {m}")

    print("\nDone.")


if __name__ == "__main__":
    # Guard: must be run from the mastery-page directory
    if not Path("data").exists():
        print("ERROR: Run this script from the mastery-page/ directory.")
        print("       cd mastery-page && python generate_brain_meshes.py")
        sys.exit(1)
    main()
