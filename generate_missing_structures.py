#!/usr/bin/env python3
"""
generate_missing_structures.py — Generate 8 missing brain structures

Splits the existing brainstem mesh into pons/medulla/midbrain by Y-coordinate,
and creates parametric meshes for hypothalamus, pituitary, olfactory bulb,
substantia nigra, VTA, and corpus callosum.

Outputs to data/brain_meshes/:
  medulla.glb, pons.glb, midbrain.glb,
  hypothalamus.glb, pituitary.glb, olfactory_bulb.glb,
  substantia_nigra.glb, vta.glb, corpus_callosum.glb
"""

import sys
import numpy as np
from pathlib import Path
import trimesh

OUTPUT_DIR = Path("data/brain_meshes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Coordinate transform (same as generate_hires_subcortical.py) ──
COORD_SCALE  = 1.0 / 75.0
COORD_OFFSET = np.array([0.118, -0.204, 0.438], dtype=np.float64)

def to_threejs(coords):
    """MNI/FreeSurfer RAS mm -> Three.js world units."""
    c = np.asarray(coords, dtype=np.float64)
    x_out = -c[:, 0]
    y_out =  c[:, 2]
    z_out =  c[:, 1]
    return (np.column_stack([x_out, y_out, z_out]) * COORD_SCALE + COORD_OFFSET).astype(np.float32)


def make_ellipsoid(center_mni, radii_mm, subdivisions=3):
    """Create an ellipsoid mesh at MNI coordinates with given radii.
    Returns a trimesh in Three.js coordinate space."""
    sphere = trimesh.creation.icosphere(subdivisions=subdivisions)
    verts = sphere.vertices.copy()
    # Scale by radii
    verts[:, 0] *= radii_mm[0]
    verts[:, 1] *= radii_mm[1]
    verts[:, 2] *= radii_mm[2]
    # Translate to MNI center
    verts[:, 0] += center_mni[0]
    verts[:, 1] += center_mni[1]
    verts[:, 2] += center_mni[2]
    # Transform to Three.js space
    verts_3js = to_threejs(verts)
    mesh = trimesh.Trimesh(vertices=verts_3js, faces=sphere.faces, process=True)
    mesh.fix_normals()
    return mesh


def make_bilateral_ellipsoid(centers_mni, radii_mm, subdivisions=3):
    """Create bilateral (left + right) ellipsoids and merge them."""
    left = make_ellipsoid(centers_mni[0], radii_mm, subdivisions)
    right = make_ellipsoid(centers_mni[1], radii_mm, subdivisions)
    merged = trimesh.util.concatenate([left, right])
    merged.merge_vertices()
    merged.fix_normals()
    return merged


print("=" * 60)
print("generate_missing_structures.py")
print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. BRAINSTEM SPLIT — pons, medulla, midbrain
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1/4] Splitting brainstem into medulla / pons / midbrain...")

brainstem_path = OUTPUT_DIR / "hires_brainstem.glb"
if brainstem_path.exists():
    bs_scene = trimesh.load(str(brainstem_path))
    if isinstance(bs_scene, trimesh.Scene):
        bs_meshes = [g for g in bs_scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
        bs_mesh = trimesh.util.concatenate(bs_meshes) if len(bs_meshes) > 1 else bs_meshes[0]
    else:
        bs_mesh = bs_scene

    # Compute face centroids in Y (Three.js up axis)
    face_centroids = bs_mesh.triangles_center
    y_vals = face_centroids[:, 1]
    y_min, y_max = y_vals.min(), y_vals.max()
    y_range = y_max - y_min

    # Split by Y-position: medulla (bottom 33%), pons (middle 33%), midbrain (top 33%)
    boundary_low  = y_min + y_range * 0.33
    boundary_high = y_min + y_range * 0.66

    medulla_faces  = np.where(y_vals <= boundary_low)[0]
    pons_faces     = np.where((y_vals > boundary_low) & (y_vals <= boundary_high))[0]
    midbrain_faces = np.where(y_vals > boundary_high)[0]

    def extract_submesh(mesh, face_indices, name):
        selected = mesh.faces[face_indices]
        unique_verts, inverse = np.unique(selected.ravel(), return_inverse=True)
        new_faces = inverse.reshape(-1, 3)
        new_verts = mesh.vertices[unique_verts]
        sub = trimesh.Trimesh(vertices=new_verts, faces=new_faces, process=True)
        sub.fix_normals()
        out_path = OUTPUT_DIR / f"{name}.glb"
        sub.export(str(out_path))
        print(f"  {name}: {len(sub.faces):,} faces -> {out_path.name} "
              f"({out_path.stat().st_size / 1e3:.0f} KB)")
        return sub

    extract_submesh(bs_mesh, medulla_faces, "medulla")
    extract_submesh(bs_mesh, pons_faces, "pons")
    extract_submesh(bs_mesh, midbrain_faces, "midbrain")
else:
    print(f"  WARNING: {brainstem_path} not found — skipping brainstem split")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PARAMETRIC STRUCTURES (5 new)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[2/4] Creating parametric structures...")

# Hypothalamus — center MNI (0, -4, -8), radii 5x4x3mm
hypo = make_ellipsoid([0, -4, -8], [5, 4, 3])
hypo_path = OUTPUT_DIR / "hypothalamus.glb"
hypo.export(str(hypo_path))
print(f"  hypothalamus: {len(hypo.faces):,} faces -> {hypo_path.name} "
      f"({hypo_path.stat().st_size / 1e3:.0f} KB)")

# Pituitary — center MNI (0, -2, -22), radii 5x4x3mm
pit = make_ellipsoid([0, -2, -22], [5, 4, 3])
pit_path = OUTPUT_DIR / "pituitary.glb"
pit.export(str(pit_path))
print(f"  pituitary: {len(pit.faces):,} faces -> {pit_path.name} "
      f"({pit_path.stat().st_size / 1e3:.0f} KB)")

# Olfactory bulb — bilateral MNI (±8, 32, -18), elongated 2x6x2mm
olb = make_bilateral_ellipsoid(
    [[-8, 32, -18], [8, 32, -18]], [2, 6, 2])
olb_path = OUTPUT_DIR / "olfactory_bulb.glb"
olb.export(str(olb_path))
print(f"  olfactory_bulb: {len(olb.faces):,} faces -> {olb_path.name} "
      f"({olb_path.stat().st_size / 1e3:.0f} KB)")

# Substantia nigra — bilateral MNI (±10, -18, -10), 4x8x2mm
sn = make_bilateral_ellipsoid(
    [[-10, -18, -10], [10, -18, -10]], [4, 8, 2])
sn_path = OUTPUT_DIR / "substantia_nigra.glb"
sn.export(str(sn_path))
print(f"  substantia_nigra: {len(sn.faces):,} faces -> {sn_path.name} "
      f"({sn_path.stat().st_size / 1e3:.0f} KB)")

# VTA (Ventral Tegmental Area) — bilateral MNI (±4, -16, -12), 2x5x2mm
vta = make_bilateral_ellipsoid(
    [[-4, -16, -12], [4, -16, -12]], [2, 5, 2])
vta_path = OUTPUT_DIR / "vta.glb"
vta.export(str(vta_path))
print(f"  vta: {len(vta.faces):,} faces -> {vta_path.name} "
      f"({vta_path.stat().st_size / 1e3:.0f} KB)")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CORPUS CALLOSUM — parametric C-shaped tube
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[3/4] Creating corpus callosum...")

# Define control points along the CC in MNI space (sagittal midline)
# Rostrum → genu → body → splenium
cc_control_points_mni = np.array([
    [0,  20, -5],   # rostrum (anterior-inferior)
    [0,  30,   5],  # genu (anterior curve)
    [0,  25,  20],  # anterior body
    [0,  10,  25],  # mid-body (superior)
    [0,  -5,  25],  # posterior body
    [0, -20,  20],  # isthmus
    [0, -30,  10],  # splenium
    [0, -25,   0],  # splenium tip (posterior-inferior)
], dtype=np.float64)

# Create a tube along these control points using spline interpolation
from scipy.interpolate import CubicSpline
t = np.linspace(0, 1, len(cc_control_points_mni))
t_fine = np.linspace(0, 1, 80)  # 80 points along the curve

cs_x = CubicSpline(t, cc_control_points_mni[:, 0])
cs_y = CubicSpline(t, cc_control_points_mni[:, 1])
cs_z = CubicSpline(t, cc_control_points_mni[:, 2])

spine_mni = np.column_stack([cs_x(t_fine), cs_y(t_fine), cs_z(t_fine)])

# Varying radius along the CC: thicker at genu and splenium, thinner at body
# Normalized position along the curve
radii = np.ones(len(t_fine)) * 3.0  # base radius 3mm
# Genu (10-25%): thicker
radii[int(len(t_fine)*0.10):int(len(t_fine)*0.25)] = 4.5
# Body (25-65%): thinner
radii[int(len(t_fine)*0.25):int(len(t_fine)*0.65)] = 2.5
# Splenium (75-95%): thicker
radii[int(len(t_fine)*0.75):int(len(t_fine)*0.95)] = 5.0
# Taper at ends
radii[:3] = np.linspace(1.5, radii[3], 3)
radii[-3:] = np.linspace(radii[-4], 1.5, 3)

# Build tube mesh: circles perpendicular to the spine at each point
n_radial = 12  # vertices per cross-section
all_verts = []
all_faces = []

for i in range(len(spine_mni)):
    # Compute local frame (tangent, normal, binormal)
    if i == 0:
        tangent = spine_mni[1] - spine_mni[0]
    elif i == len(spine_mni) - 1:
        tangent = spine_mni[-1] - spine_mni[-2]
    else:
        tangent = spine_mni[i+1] - spine_mni[i-1]
    tangent = tangent / (np.linalg.norm(tangent) + 1e-9)

    # Choose up vector
    up = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(tangent, up)) > 0.9:
        up = np.array([0.0, 1.0, 0.0])

    normal = np.cross(tangent, up)
    normal = normal / (np.linalg.norm(normal) + 1e-9)
    binormal = np.cross(tangent, normal)

    r = radii[i]
    for j in range(n_radial):
        angle = 2 * np.pi * j / n_radial
        pt = spine_mni[i] + r * (np.cos(angle) * normal + np.sin(angle) * binormal)
        all_verts.append(pt)

# Build faces (quads split into triangles)
for i in range(len(spine_mni) - 1):
    for j in range(n_radial):
        j_next = (j + 1) % n_radial
        v00 = i * n_radial + j
        v01 = i * n_radial + j_next
        v10 = (i + 1) * n_radial + j
        v11 = (i + 1) * n_radial + j_next
        all_faces.append([v00, v10, v01])
        all_faces.append([v01, v10, v11])

# Cap the ends
for end_ring, flip in [(0, True), (len(spine_mni) - 1, False)]:
    center_idx = len(all_verts)
    all_verts.append(spine_mni[end_ring])
    base = end_ring * n_radial
    for j in range(n_radial):
        j_next = (j + 1) % n_radial
        if flip:
            all_faces.append([center_idx, base + j_next, base + j])
        else:
            all_faces.append([center_idx, base + j, base + j_next])

cc_verts_mni = np.array(all_verts, dtype=np.float64)
cc_faces = np.array(all_faces, dtype=np.int32)

# Transform to Three.js space
cc_verts_3js = to_threejs(cc_verts_mni)

cc_mesh = trimesh.Trimesh(vertices=cc_verts_3js, faces=cc_faces, process=True)
cc_mesh.fix_normals()

cc_path = OUTPUT_DIR / "corpus_callosum.glb"
cc_mesh.export(str(cc_path))
print(f"  corpus_callosum: {len(cc_mesh.faces):,} faces -> {cc_path.name} "
      f"({cc_path.stat().st_size / 1e3:.0f} KB)")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[4/4] Summary")
new_structures = [
    "medulla", "pons", "midbrain",
    "hypothalamus", "pituitary", "olfactory_bulb",
    "substantia_nigra", "vta", "corpus_callosum"
]
for name in new_structures:
    p = OUTPUT_DIR / f"{name}.glb"
    if p.exists():
        print(f"  {p.name:30s} {p.stat().st_size / 1e3:6.0f} KB")
    else:
        print(f"  {name:30s} MISSING")

print("\n" + "=" * 60)
print("Done! Generated 9 new structure meshes.")
print("=" * 60)
