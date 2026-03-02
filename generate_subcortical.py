#!/usr/bin/env python3
"""
generate_subcortical.py -- Stages 3+4: subcortical + cerebellum meshes.
Loads cached atlas files directly (bypasses nilearn network fetch which hangs
on some Windows configurations even when files are already cached).
Run from mastery-page/ directory.
"""

import json, sys, traceback, xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path

OUT_DIR       = Path("data/brain_meshes")
MANIFEST_PATH = Path("data/brain_regions_manifest.json")

# Coordinate transform parameters (computed by generate_brain_meshes.py Stage 1)
COORD_SCALE  = 1.0 / 75.0
COORD_OFFSET = np.array([0.118, -0.204, 0.438], dtype=np.float64)

MAX_FACES = 4_000

# Harvard-Oxford label candidates (we look up index from the XML)
HO_SUBCORTICAL = {
    "thalamus":        ["Left Thalamus", "Thalamus"],
    "hippocampus":     ["Left Hippocampus", "Hippocampus"],
    "amygdala":        ["Left Amygdala", "Amygdala"],
    "caudate":         ["Left Caudate", "Caudate"],
    "putamen":         ["Left Putamen", "Putamen"],
    "globus_pallidus": ["Left Pallidum", "Pallidum"],
    "brainstem":       ["Brain-Stem", "Brain Stem"],
}

# Possible nilearn cache locations for the HO atlas
_HO_SEARCH_PATHS = [
    Path.home() / "nilearn_data" / "fsl" / "data" / "atlases" / "HarvardOxford",
    Path("C:/Users/mcdan/nilearn_data/fsl/data/atlases/HarvardOxford"),
]
_HO_XML_PATHS = [
    Path.home() / "nilearn_data" / "fsl" / "data" / "atlases" / "HarvardOxford-Subcortical.xml",
    Path("C:/Users/mcdan/nilearn_data/fsl/data/atlases/HarvardOxford-Subcortical.xml"),
]
_AAL_SEARCH_PATHS = [
    Path.home() / "nilearn_data" / "aal_3v2",
]


def to_threejs(coords):
    c = np.asarray(coords, dtype=np.float64)
    x_out = -c[:, 0]
    y_out =  c[:, 2]
    z_out =  c[:, 1]
    return (np.column_stack([x_out, y_out, z_out]) * COORD_SCALE + COORD_OFFSET).astype(np.float32)


def save_glb(mesh, path):
    try:
        data = mesh.export(file_type="glb")
        Path(path).write_bytes(data)
        return True
    except Exception as e:
        print(f"  [error] export failed: {e}")
        return False


def mesh_bounds(mesh):
    b = mesh.bounds
    return {"min": b[0].tolist(), "max": b[1].tolist()}


def simplify_mesh(mesh, max_faces):
    if len(mesh.faces) <= max_faces:
        return mesh
    # trimesh 4.x simplify_quadric_decimation takes target_reduction (0-1 fraction to REMOVE)
    target_reduction = max(0.0, 1.0 - (max_faces / len(mesh.faces)))
    for method_name in ('simplify_quadric_decimation',):
        m = getattr(mesh, method_name, None)
        if m is not None:
            try:
                s = m(target_reduction)
                if s is not None and len(s.faces) > 0:
                    return s
            except Exception as e:
                print(f"  [warn] {method_name} failed: {e}")
            break
    return mesh


def find_ho_nifti():
    """Find the HO subcortical NIfTI file in the nilearn cache."""
    for search_dir in _HO_SEARCH_PATHS:
        if search_dir.exists():
            nii = search_dir / "HarvardOxford-sub-maxprob-thr25-1mm.nii.gz"
            if nii.exists():
                return nii
    return None


def parse_ho_labels():
    """Parse label names and 1-based NIfTI indices from the HO Subcortical XML."""
    for xml_path in _HO_XML_PATHS:
        if not xml_path.exists():
            continue
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
        # index attr is 0-based; NIfTI value = index + 1
        labels = {}  # nifti_value -> label_name
        for elem in root.iter('label'):
            idx = int(elem.get('index', -1))
            name = (elem.text or '').strip()
            if idx >= 0 and name:
                labels[idx + 1] = name  # NIfTI value
        return labels
    return {}


def find_aal_nifti():
    """Find the AAL NIfTI file in the nilearn cache."""
    for search_dir in _AAL_SEARCH_PATHS:
        if not search_dir.exists():
            continue
        for nii in search_dir.rglob("*.nii.gz"):
            if "aal" in nii.name.lower() or "roi" in nii.name.lower():
                return nii
    return None


def main():
    import nibabel as nib
    import trimesh
    from skimage.measure import marching_cubes

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing manifest
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
        print(f"Loaded manifest with {len(manifest)} regions.")
    else:
        manifest = {}

    # ── STAGE 3: Subcortical (Harvard-Oxford, direct cache load) ─────────────
    print("\n" + "=" * 60)
    print("STAGE 3/4  Subcortical (Harvard-Oxford, direct cache load)")
    print("=" * 60)
    sys.stdout.flush()

    try:
        ho_nii = find_ho_nifti()
        if ho_nii is None:
            print("  [skip] HO NIfTI not found in cache; skipping subcortical.")
        else:
            print(f"  Loading: {ho_nii}")
            ho_img    = nib.load(str(ho_nii))
            ho_data   = ho_img.get_fdata()
            ho_affine = ho_img.affine
            ho_labels = parse_ho_labels()
            print(f"  Loaded: shape {ho_data.shape}, {len(ho_labels)} label entries")
            sys.stdout.flush()

            # Build reverse lookup: name (lower) -> nifti value
            name_to_val = {nm.strip().lower(): v for v, nm in ho_labels.items()}

            for region_id, label_opts in HO_SUBCORTICAL.items():
                if region_id in manifest:
                    print(f"  [skip] {region_id}: already in manifest")
                    sys.stdout.flush()
                    continue

                # Find NIfTI integer value
                nv = None
                matched_name = None
                for opt in label_opts:
                    opt_l = opt.strip().lower()
                    if opt_l in name_to_val:
                        nv = name_to_val[opt_l]
                        matched_name = opt
                        break
                    # substring
                    for nm_l, v in name_to_val.items():
                        if opt_l in nm_l or nm_l in opt_l:
                            nv = v
                            matched_name = nm_l
                            break
                    if nv is not None:
                        break

                if nv is None:
                    print(f"  [skip] {region_id}: not in atlas labels. Tried: {label_opts}")
                    print(f"         Atlas values (first 15): {list(ho_labels.items())[:15]}")
                    sys.stdout.flush()
                    continue

                vol = (ho_data == nv).astype(np.float32)
                n_vox = int(vol.sum())
                print(f"  {region_id}: '{matched_name}' (val {nv}), {n_vox} voxels")
                sys.stdout.flush()

                if n_vox < 20:
                    print(f"  [skip] too few voxels")
                    continue

                verts_v, mc_faces, _, _ = marching_cubes(vol, level=0.5)
                ones      = np.ones((len(verts_v), 1))
                verts_mni = (ho_affine @ np.hstack([verts_v, ones]).T).T[:, :3]
                verts_3d  = to_threejs(verts_mni)

                mesh = trimesh.Trimesh(vertices=verts_3d, faces=mc_faces, process=False)
                before = len(mesh.faces)
                mesh = simplify_mesh(mesh, MAX_FACES)
                print(f"    {before:,} -> {len(mesh.faces):,} faces")
                sys.stdout.flush()

                out = OUT_DIR / f"{region_id}.glb"
                if save_glb(mesh, out):
                    manifest[region_id] = {
                        "file":        f"data/brain_meshes/{region_id}.glb",
                        "type":        "subcortical",
                        "vertexCount": len(mesh.vertices),
                        "faceCount":   len(mesh.faces),
                        "bounds":      mesh_bounds(mesh),
                    }
                    print(f"  OK {region_id}: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")
                    sys.stdout.flush()

    except Exception as e:
        print(f"  [ERROR] Subcortical: {e}")
        traceback.print_exc()
    sys.stdout.flush()

    # ── STAGE 4: Cerebellum (AAL, direct cache) ───────────────────────────────
    print("\n" + "=" * 60)
    print("STAGE 4/4  Cerebellum (AAL direct cache)")
    print("=" * 60)
    sys.stdout.flush()

    if "cerebellum" in manifest:
        print("  [skip] already in manifest")
    else:
        try:
            aal_nii = find_aal_nifti()
            if aal_nii is None:
                print("  [skip] AAL NIfTI not found in cache. Download the AAL atlas manually.")
                print("  To download: python -c \"import ssl; ssl._create_default_https_context=ssl._create_unverified_context; from nilearn import datasets; datasets.fetch_atlas_aal()\"")
            else:
                print(f"  Loading: {aal_nii}")
                aal_img    = nib.load(str(aal_nii))
                aal_data   = aal_img.get_fdata()
                aal_affine = aal_img.affine
                print(f"  Shape: {aal_data.shape}, values: {int(aal_data.min())}..{int(aal_data.max())}")
                sys.stdout.flush()

                # Try to find an accompanying labels file
                aal_dir  = aal_nii.parent
                txt_file = None
                for f in aal_dir.rglob("*.txt"):
                    txt_file = f; break
                for f in aal_dir.rglob("*.xml"):
                    txt_file = f; break

                # Build cerebellum mask from known AAL cerebellum value ranges
                # AAL cerebellum: typically indices 91-116 (Cerebellum_1_L to Vermis_10)
                cereb_vol   = np.zeros(aal_data.shape, dtype=np.float32)
                cereb_count = 0

                if txt_file:
                    print(f"  Labels file: {txt_file}")
                    # Try to parse labels
                    for line in txt_file.read_text(encoding='utf-8', errors='replace').splitlines():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            try:
                                idx = int(parts[0])
                                name = ' '.join(parts[1:])
                                if 'cerebel' in name.lower() or 'vermis' in name.lower():
                                    cereb_vol[aal_data == idx] = 1.0
                                    cereb_count += 1
                            except ValueError:
                                pass
                else:
                    # Fallback: use known value range for AAL cerebellum (2001-2110 for AAL3v2)
                    print("  No labels file found; using known AAL3v2 cerebellum range 2001-2110")
                    for v in range(2001, 2111):
                        if (aal_data == v).any():
                            cereb_vol[aal_data == v] = 1.0
                            cereb_count += 1
                    if cereb_count == 0:
                        # Try AAL1 range 91-116
                        print("  Trying AAL1 range 91-116...")
                        for v in range(91, 117):
                            if (aal_data == v).any():
                                cereb_vol[aal_data == v] = 1.0
                                cereb_count += 1

                print(f"  Combined {cereb_count} cerebellar parcels, {int(cereb_vol.sum())} voxels")
                sys.stdout.flush()

                if cereb_vol.sum() < 20:
                    print("  [warn] No cerebellar voxels found")
                else:
                    verts_v, mc_faces, _, _ = marching_cubes(cereb_vol, level=0.5)
                    ones      = np.ones((len(verts_v), 1))
                    verts_mni = (aal_affine @ np.hstack([verts_v, ones]).T).T[:, :3]
                    verts_3d  = to_threejs(verts_mni)

                    mesh = trimesh.Trimesh(vertices=verts_3d, faces=mc_faces, process=False)
                    before = len(mesh.faces)
                    mesh = simplify_mesh(mesh, MAX_FACES)
                    print(f"  {before:,} -> {len(mesh.faces):,} faces")

                    out = OUT_DIR / "cerebellum.glb"
                    if save_glb(mesh, out):
                        manifest["cerebellum"] = {
                            "file":        "data/brain_meshes/cerebellum.glb",
                            "type":        "cortical",
                            "vertexCount": len(mesh.vertices),
                            "faceCount":   len(mesh.faces),
                            "bounds":      mesh_bounds(mesh),
                        }
                        print(f"  OK cerebellum: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")

        except Exception as e:
            print(f"  [ERROR] Cerebellum: {e}")
            traceback.print_exc()
    sys.stdout.flush()

    # ── Write updated manifest ────────────────────────────────────────────────
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest updated: {len(manifest)} regions")
    by_type = {}
    for r, info in manifest.items():
        by_type.setdefault(info["type"], []).append(r)
    for t in sorted(by_type):
        print(f"  {t:12s}: {', '.join(sorted(by_type[t]))}")
    print("\nDone.")


if __name__ == "__main__":
    if not Path("data").exists():
        print("ERROR: Run from mastery-page/ directory.")
        sys.exit(1)
    main()
