#!/usr/bin/env python3
"""
generate_subcortical_json.py

Generates anatomically accurate brainstem and cerebellum meshes from
brain atlases via marching cubes, then exports as JSON arrays that
Three.js can load directly as BufferGeometry (bypassing GLB/GLTF).

Brainstem  — Harvard-Oxford subcortical atlas (thr0, 1mm)
Cerebellum — AAL SPM5 atlas (2mm)

Also bakes procedural textures as PNG files (brainstem zones, folia bands).

Outputs:
  data/brain_meshes/brainstem_mesh.json   — {positions, indices, normals, uvs}
  data/brain_meshes/cerebellum_mesh.json  — {positions, indices, normals, uvs}
  data/brain_meshes/brainstem_texture.png — 512x512 medulla/pons/midbrain
  data/brain_meshes/cerebellum_texture.png — 1024x512 folia bands
"""

import sys, gc, json
import numpy as np
from pathlib import Path
from scipy import ndimage
import nibabel as nib
from skimage import measure
from PIL import Image

OUTPUT_DIR = Path("data/brain_meshes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Coordinate transform (must match cortex + region overlays) ────────────────
# FreeSurfer RAS: x=right, y=anterior, z=superior
# Three.js:       x=right, y=up(superior), z=toward-viewer(anterior)
# -> out = [-x_fs, z_fs, y_fs] * COORD_SCALE + COORD_OFFSET
COORD_SCALE  = 1.0 / 75.0
COORD_OFFSET = np.array([0.118, -0.204, 0.438], dtype=np.float64)

def to_threejs(coords):
    """MNI/FreeSurfer RAS mm -> Three.js world units."""
    c = np.asarray(coords, dtype=np.float64)
    x_out = -c[:, 0]
    y_out =  c[:, 2]
    z_out =  c[:, 1]
    return (np.column_stack([x_out, y_out, z_out]) * COORD_SCALE + COORD_OFFSET).astype(np.float32)


# ── Mesh generation ──────────────────────────────────────────────────────────

def voxels_to_mesh(mask_3d, affine, step_size, sigma):
    """Binary 3D mask -> smoothed marching-cubes surface in Three.js coords."""
    smoothed = ndimage.gaussian_filter(mask_3d.astype(np.float32), sigma=sigma)
    verts_v, faces, _, _ = measure.marching_cubes(smoothed, level=0.5,
                                                   step_size=step_size)
    ones     = np.ones((len(verts_v), 1), dtype=np.float32)
    verts_mm = (affine @ np.hstack([verts_v.astype(np.float32), ones]).T).T[:, :3]
    verts_3d = to_threejs(verts_mm)
    faces    = faces.astype(np.int32)

    # Fix face winding: ensure normals point outward
    centroid = verts_3d.mean(axis=0)
    v0 = verts_3d[faces[:, 0]]
    v1 = verts_3d[faces[:, 1]]
    v2 = verts_3d[faces[:, 2]]
    face_normals = np.cross(v1 - v0, v2 - v0)
    face_centers = (v0 + v1 + v2) / 3.0
    dots = np.sum(face_normals * (face_centers - centroid), axis=1)
    inward = dots < 0
    if inward.sum() > len(faces) // 2:
        faces = faces[:, ::-1]
    elif inward.sum() > 0:
        faces[inward] = faces[inward][:, ::-1]

    return verts_3d, faces


def compute_vertex_normals(verts, faces):
    """Compute smooth per-vertex normals from face normals."""
    normals = np.zeros_like(verts)
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    # Accumulate face normals onto each vertex
    for i in range(3):
        np.add.at(normals, faces[:, i], fn)
    # Normalize
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals / np.maximum(lengths, 1e-9)
    return normals.astype(np.float32)


# ── UV mapping ───────────────────────────────────────────────────────────────

def sphere_to_uv_brainstem(verts):
    """Spherical UV for brainstem. v=elevation (medulla->midbrain), u=azimuthal."""
    centroid = verts.mean(axis=0)
    v_c = verts - centroid
    r   = np.linalg.norm(v_c, axis=1, keepdims=True)
    n   = v_c / np.maximum(r, 1e-9)
    # In Three.js coords: x=right, y=up, z=anterior
    # u: azimuthal around vertical (y) axis, seam at posterior
    u = (np.arctan2(n[:, 0], -n[:, 2]) + np.pi) / (2.0 * np.pi)
    # v: elevation (y component), 0=bottom, 1=top
    v = (np.arcsin(np.clip(n[:, 1], -1.0, 1.0)) + np.pi / 2.0) / np.pi
    return np.stack([u, v], axis=1).astype(np.float32), centroid


def sphere_to_uv_cerebellum(verts):
    """Spherical UV for cerebellum. v=elevation for folia bands, u=circumferential."""
    centroid = verts.mean(axis=0)
    v_c = verts - centroid
    r   = np.linalg.norm(v_c, axis=1, keepdims=True)
    n   = v_c / np.maximum(r, 1e-9)
    # u: azimuthal, seam anterior (facing brainstem, hidden)
    u = (np.arctan2(n[:, 0], n[:, 2]) + np.pi) / (2.0 * np.pi)
    # v: elevation (y component)
    v = (np.arcsin(np.clip(n[:, 1], -1.0, 1.0)) + np.pi / 2.0) / np.pi
    return np.stack([u, v], axis=1).astype(np.float32), centroid


def remove_seam_faces(uv, faces, wrap_threshold=0.35):
    """Drop triangles that straddle the u=0/1 wrap seam."""
    u0 = uv[faces[:, 0], 0]
    u1 = uv[faces[:, 1], 0]
    u2 = uv[faces[:, 2], 0]
    span = (np.maximum(np.maximum(u0, u1), u2)
            - np.minimum(np.minimum(u0, u1), u2))
    return faces[span < wrap_threshold]


# ── Texture generation ───────────────────────────────────────────────────────

def generate_brainstem_texture():
    """Procedural brainstem texture: medulla / pons / midbrain zones."""
    W, H = 512, 512
    uu = np.linspace(0.0, 1.0, W, dtype=np.float32)
    vv = np.linspace(0.0, 1.0, H, dtype=np.float32)
    UU, VV = np.meshgrid(uu, vv)

    MEDULLA_COL  = np.array([168, 132, 120], dtype=np.float32)
    PONS_COL     = np.array([195, 158, 145], dtype=np.float32)
    MIDBRAIN_COL = np.array([172, 138, 126], dtype=np.float32)

    def logistic(x, x0, k=20.0):
        return 1.0 / (1.0 + np.exp(-k * (x - x0)))

    pons_mask     = logistic(VV, 0.36) * (1.0 - logistic(VV, 0.64))
    midbrain_mask = logistic(VV, 0.61)
    medulla_mask  = np.maximum(1.0 - pons_mask - midbrain_mask, 0.0)

    base = np.zeros((H, W, 3), dtype=np.float32)
    for i in range(3):
        base[:, :, i] = (medulla_mask  * MEDULLA_COL[i]
                       + pons_mask     * PONS_COL[i]
                       + midbrain_mask * MIDBRAIN_COL[i])

    pons_fibers = 0.55 * pons_mask * np.sin(VV * 18 * 2.0 * np.pi)
    long_tracts = 0.10 * np.sin(UU * 14 * 2.0 * np.pi)
    rng  = np.random.default_rng(7)
    noise = 0.06 * rng.standard_normal((H, W)).astype(np.float32)
    curv = pons_fibers + long_tracts + noise

    RIDGE_COL  = np.array([218, 185, 168], dtype=np.float32)
    GROOVE_COL = np.array([ 92,  62,  54], dtype=np.float32)

    t_pos = np.clip( curv / 1.8, 0.0, 1.0)
    t_neg = np.clip(-curv / 1.8, 0.0, 1.0)

    rgb = np.empty((H, W, 3), dtype=np.uint8)
    for i in range(3):
        ch = (base[:, :, i]
              + t_pos * (RIDGE_COL[i] - base[:, :, i])
              + t_neg * (GROOVE_COL[i] - base[:, :, i]))
        rgb[:, :, i] = np.clip(ch, 0, 255).astype(np.uint8)
    return rgb


def generate_cerebellum_texture():
    """Procedural cerebellar folia texture."""
    W, H = 1024, 512
    SULCI_COL = np.array([55,  18,   8], dtype=np.float32)
    GYRI_COL  = np.array([221, 184, 152], dtype=np.float32)

    uu = np.linspace(0.0, 1.0, W, dtype=np.float32)
    vv = np.linspace(0.0, 1.0, H, dtype=np.float32)
    UU, VV = np.meshgrid(uu, vv)

    N_PRI = 22
    N_SEC = 66

    curv = np.sin(VV * N_PRI * 2.0 * np.pi)
    curv += 0.45 * np.sin(VV * N_SEC * 2.0 * np.pi)
    curv += 0.18 * np.sin(UU * 5.0 * 2.0 * np.pi
                           + VV * N_PRI * 2.0 * np.pi * 0.12)
    rng  = np.random.default_rng(42)
    curv += 0.08 * rng.standard_normal((H, W)).astype(np.float32)

    t   = np.clip(curv / 2.0 + 0.5, 0.0, 1.0).astype(np.float32)
    rgb = np.empty((H, W, 3), dtype=np.uint8)
    for i in range(3):
        ch = SULCI_COL[i] * (1.0 - t) + GYRI_COL[i] * t
        rgb[:, :, i] = np.clip(ch, 0, 255).astype(np.uint8)
    return rgb


# ── JSON export ──────────────────────────────────────────────────────────────

def export_mesh_json(verts, faces, normals, uvs, out_path):
    """Export mesh as JSON with flat float/int arrays for Three.js BufferGeometry."""
    data = {
        'positions': verts.flatten().tolist(),
        'indices':   faces.flatten().tolist(),
        'normals':   normals.flatten().tolist(),
        'uvs':       uvs.flatten().tolist(),
        'vertexCount': len(verts),
        'faceCount':   len(faces),
    }
    with open(out_path, 'w') as f:
        json.dump(data, f)
    sz = out_path.stat().st_size
    print(f"    Saved: {out_path.name}  ({sz/1e3:.0f} KB, "
          f"{len(verts):,} verts, {len(faces):,} faces)")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':

    print("[1/4] Loading atlases...")
    from nilearn import datasets as _ds
    import ssl, requests as _req, warnings as _warn

    # SSL workaround for Windows
    _orig_ctx = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context
    _orig_send = _req.Session.send
    def _patched_send(self, *args, **kwargs):
        kwargs['verify'] = False
        return _orig_send(self, *args, **kwargs)
    _req.Session.send = _patched_send
    _warn.filterwarnings('ignore', message='.*Unverified HTTPS.*')

    # ── BRAINSTEM ──
    print("[2/4] Generating brainstem mesh (Harvard-Oxford atlas)...")
    ho = _ds.fetch_atlas_harvard_oxford("sub-maxprob-thr0-1mm")
    ho_img = nib.load(ho.maps) if isinstance(ho.maps, (str, bytes)) else ho.maps
    if not hasattr(ho_img, 'get_fdata'):
        ho_img = nib.load(str(ho.maps))
    ho_data = ho_img.get_fdata(dtype=np.float32)

    BRAINSTEM_VAL = 8
    bs_mask = (ho_data == BRAINSTEM_VAL)
    print(f"    Brainstem: {bs_mask.sum():,} voxels (atlas value {BRAINSTEM_VAL})")

    if bs_mask.sum() < 100:
        print("    ERROR: brainstem mask empty."); sys.exit(1)

    bs_verts, bs_faces = voxels_to_mesh(bs_mask, ho_img.affine,
                                         step_size=1, sigma=0.8)
    print(f"    Raw mesh: {len(bs_verts):,} verts, {len(bs_faces):,} faces")

    # UV map
    bs_uv, bs_centroid = sphere_to_uv_brainstem(bs_verts)
    print(f"    Centroid (Three.js): {bs_centroid.round(4)}")
    bs_faces = remove_seam_faces(bs_uv, bs_faces)
    print(f"    After seam removal: {len(bs_faces):,} faces")

    # Normals
    bs_normals = compute_vertex_normals(bs_verts, bs_faces)

    # Export mesh JSON
    export_mesh_json(bs_verts, bs_faces, bs_normals, bs_uv,
                     OUTPUT_DIR / "brainstem_mesh.json")

    # Texture
    print("    Baking brainstem texture...")
    bs_tex = generate_brainstem_texture()
    Image.fromarray(bs_tex, 'RGB').save(str(OUTPUT_DIR / "brainstem_texture.png"))
    print(f"    Saved: brainstem_texture.png ({(OUTPUT_DIR / 'brainstem_texture.png').stat().st_size/1e3:.0f} KB)")

    del ho_data, bs_mask, ho_img, bs_verts, bs_faces, bs_normals, bs_uv
    gc.collect()

    # ── CEREBELLUM ──
    print("[3/4] Generating cerebellum mesh (AAL atlas)...")
    try:
        aal = _ds.fetch_atlas_aal()
    except Exception:
        aal = _ds.fetch_atlas_aal(version='SPM5')

    aal_img = nib.load(aal.maps) if isinstance(aal.maps, (str, bytes)) else aal.maps
    if not hasattr(aal_img, 'get_fdata'):
        aal_img = nib.load(str(aal.maps))
    aal_data = aal_img.get_fdata(dtype=np.float32)

    cereb_vals = set()
    for label, idx in zip(aal.labels, aal.indices):
        if "cerebel" in label.lower() or "vermis" in label.lower():
            cereb_vals.add(int(idx))

    print(f"    Found {len(cereb_vals)} cerebellar label values "
          f"(range {min(cereb_vals)}..{max(cereb_vals)})")

    cb_mask = np.isin(aal_data.astype(np.int32), sorted(cereb_vals))
    print(f"    Cerebellum: {cb_mask.sum():,} voxels")

    if cb_mask.sum() < 100:
        print("    ERROR: cerebellum mask empty."); sys.exit(1)

    cb_verts, cb_faces = voxels_to_mesh(cb_mask, aal_img.affine,
                                         step_size=1, sigma=0.3)
    print(f"    Raw mesh: {len(cb_verts):,} verts, {len(cb_faces):,} faces")

    del aal_data, cb_mask, aal_img
    gc.collect()

    # UV map
    cb_uv, cb_centroid = sphere_to_uv_cerebellum(cb_verts)
    print(f"    Centroid (Three.js): {cb_centroid.round(4)}")
    cb_faces = remove_seam_faces(cb_uv, cb_faces)
    print(f"    After seam removal: {len(cb_faces):,} faces")

    # Normals
    cb_normals = compute_vertex_normals(cb_verts, cb_faces)

    # Export mesh JSON
    export_mesh_json(cb_verts, cb_faces, cb_normals, cb_uv,
                     OUTPUT_DIR / "cerebellum_mesh.json")

    # Texture
    print("    Baking cerebellum texture...")
    cb_tex = generate_cerebellum_texture()
    Image.fromarray(cb_tex, 'RGB').save(str(OUTPUT_DIR / "cerebellum_texture.png"))
    print(f"    Saved: cerebellum_texture.png ({(OUTPUT_DIR / 'cerebellum_texture.png').stat().st_size/1e3:.0f} KB)")

    # Restore SSL
    ssl._create_default_https_context = _orig_ctx
    _req.Session.send = _orig_send

    print("\n[4/4] Done!")
    print(f"  {OUTPUT_DIR / 'brainstem_mesh.json'}")
    print(f"  {OUTPUT_DIR / 'brainstem_texture.png'}")
    print(f"  {OUTPUT_DIR / 'cerebellum_mesh.json'}")
    print(f"  {OUTPUT_DIR / 'cerebellum_texture.png'}")
