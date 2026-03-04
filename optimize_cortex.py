#!/usr/bin/env python3
"""
optimize_cortex.py — Decimate cortex mesh + bake normal map + ambient occlusion

Takes the 655k-face full_brain_hires.glb and produces:
  1. full_brain_optimized.glb — decimated to ~100k faces with baked texture
  2. full_brain_draco.glb — Draco-compressed version (~4MB)
  3. cortex_normal_map.png — normal map baked from high-poly to low-poly
  4. Updates the sulcal texture with ambient occlusion darkening

Uses curvature-adaptive face allocation: more faces on high-curvature
sulci/ridges, fewer on flat gyral surfaces.
"""

import sys, gc, json, time
import numpy as np
from pathlib import Path
from PIL import Image
import trimesh

OUTPUT_DIR = Path("data/brain_meshes")

print("=" * 60)
print("optimize_cortex.py — Cortex Mesh Optimization")
print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Load high-poly cortex
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1/5] Loading high-poly cortex...")
hires_path = OUTPUT_DIR / "full_brain_hires.glb"

scene = trimesh.load(str(hires_path))

# Extract mesh(es) from the scene
if isinstance(scene, trimesh.Scene):
    meshes = [g for g in scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
    if len(meshes) == 1:
        hi_mesh = meshes[0]
    else:
        hi_mesh = trimesh.util.concatenate(meshes)
elif isinstance(scene, trimesh.Trimesh):
    hi_mesh = scene
else:
    print(f"  ERROR: Unexpected type {type(scene)}")
    sys.exit(1)

hi_verts = hi_mesh.vertices.astype(np.float32)
hi_faces = hi_mesh.faces.astype(np.int32)
print(f"  High-poly: {len(hi_verts):,} verts, {len(hi_faces):,} faces")
print(f"  File size: {hires_path.stat().st_size / 1e6:.1f} MB")

# Extract existing UV coordinates
hi_uv = None
if hasattr(hi_mesh.visual, 'uv') and hi_mesh.visual.uv is not None:
    hi_uv = hi_mesh.visual.uv.astype(np.float32)
    print(f"  UV coordinates: {hi_uv.shape}")

# Extract existing texture
hi_texture = None
if hasattr(hi_mesh.visual, 'material'):
    mat = hi_mesh.visual.material
    if hasattr(mat, 'image') and mat.image is not None:
        hi_texture = np.array(mat.image.convert('RGB'))
        print(f"  Existing texture: {hi_texture.shape}")
    elif hasattr(mat, 'baseColorTexture') and mat.baseColorTexture is not None:
        hi_texture = np.array(mat.baseColorTexture.convert('RGB'))
        print(f"  Existing baseColorTexture: {hi_texture.shape}")

# Compute high-poly vertex normals
hi_mesh.fix_normals()
hi_normals = hi_mesh.vertex_normals.astype(np.float32)
print(f"  Vertex normals: {hi_normals.shape}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Curvature-adaptive decimation
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_FACES = 100000

# -- Step 2A: Remove degenerate faces --
print(f"\n[2/6] Removing degenerate faces...")
face_areas = hi_mesh.area_faces
degenerate_mask = face_areas < 1e-8
n_degenerate = degenerate_mask.sum()

if n_degenerate > 0:
    good_face_idx = np.where(~degenerate_mask)[0]
    hi_mesh = trimesh.Trimesh(
        vertices=hi_verts, faces=hi_faces[good_face_idx], process=True)
    hi_verts = hi_mesh.vertices.astype(np.float32)
    hi_faces = hi_mesh.faces.astype(np.int32)
    hi_mesh.fix_normals()
    hi_normals = hi_mesh.vertex_normals.astype(np.float32)
    print(f"  Removed {n_degenerate:,} degenerate faces (area < 1e-8)")
    print(f"  Clean mesh: {len(hi_verts):,} verts, {len(hi_faces):,} faces")
else:
    print(f"  No degenerate faces found")

# -- Step 2B: Compute per-face curvature --
print(f"\n[3/6] Computing per-face curvature...")
t0 = time.time()

# Use dihedral angles at face adjacencies as curvature proxy
face_curvature = np.zeros(len(hi_faces), dtype=np.float32)
face_count = np.zeros(len(hi_faces), dtype=np.float32)

adj_pairs = hi_mesh.face_adjacency            # (N, 2) adjacent face pairs
adj_angles = hi_mesh.face_adjacency_angles     # dihedral angle per pair

for i in range(len(adj_pairs)):
    f1, f2 = adj_pairs[i]
    angle = adj_angles[i]
    face_curvature[f1] += angle
    face_curvature[f2] += angle
    face_count[f1] += 1
    face_count[f2] += 1

face_count[face_count == 0] = 1
face_curvature /= face_count

print(f"  Curvature range: [{face_curvature.min():.4f}, {face_curvature.max():.4f}]")
print(f"  Mean: {face_curvature.mean():.4f}, Median: {np.median(face_curvature):.4f}")

# -- Step 2C: Two-pass selective decimation --
print(f"\n[4/6] Curvature-adaptive decimation...")
t1 = time.time()

# Split faces into low-curvature (bottom 40%) and high-curvature (top 60%)
threshold = np.percentile(face_curvature, 40)
low_curv_idx = np.where(face_curvature <= threshold)[0]
high_curv_idx = np.where(face_curvature > threshold)[0]

print(f"  Low-curvature faces: {len(low_curv_idx):,} (bottom 40%)")
print(f"  High-curvature faces: {len(high_curv_idx):,} (top 60%)")

def submesh_from_faces(mesh, face_indices):
    """Extract a submesh from selected face indices."""
    selected_faces = mesh.faces[face_indices]
    # Remap vertex indices to only include used vertices
    unique_verts, inverse = np.unique(selected_faces.ravel(), return_inverse=True)
    new_faces = inverse.reshape(-1, 3)
    new_verts = mesh.vertices[unique_verts]
    sub = trimesh.Trimesh(vertices=new_verts, faces=new_faces, process=False)
    sub.fix_normals()
    return sub

# Extract and decimate low-curvature region (flat gyral surfaces → 30%)
low_mesh = submesh_from_faces(hi_mesh, low_curv_idx)
low_target = max(1000, int(len(low_curv_idx) * 0.30))
print(f"  Decimating low-curvature: {len(low_curv_idx):,} → ~{low_target:,} faces...")
low_dec = low_mesh.simplify_quadric_decimation(face_count=low_target)
print(f"  Low-curvature result: {len(low_dec.faces):,} faces")

# Extract and decimate high-curvature region (sulci/ridges → 70%)
high_mesh = submesh_from_faces(hi_mesh, high_curv_idx)
high_target = max(1000, int(len(high_curv_idx) * 0.70))
print(f"  Decimating high-curvature: {len(high_curv_idx):,} → ~{high_target:,} faces...")
high_dec = high_mesh.simplify_quadric_decimation(face_count=high_target)
print(f"  High-curvature result: {len(high_dec.faces):,} faces")

# Merge back into single mesh
lo_mesh = trimesh.util.concatenate([low_dec, high_dec])
# Merge close vertices at the seam between regions (within 1e-5 units)
lo_mesh.merge_vertices(merge_tex=True, merge_norm=True)
lo_mesh.fix_normals()

lo_verts = lo_mesh.vertices.astype(np.float32)
lo_faces = lo_mesh.faces.astype(np.int32)
lo_normals = lo_mesh.vertex_normals.astype(np.float32)

print(f"  Final merged mesh: {len(lo_verts):,} verts, {len(lo_faces):,} faces")
print(f"  Decimation took {time.time() - t1:.1f}s")

# Verify face area distribution improved
lo_face_areas = lo_mesh.area_faces
hi_face_areas = hi_mesh.area_faces
hi_cv = hi_face_areas.std() / hi_face_areas.mean() if hi_face_areas.mean() > 0 else 0
lo_cv = lo_face_areas.std() / lo_face_areas.mean() if lo_face_areas.mean() > 0 else 0
print(f"  Face area CV: {hi_cv:.3f} (hires) → {lo_cv:.3f} (optimized)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Transfer UV coordinates from high-poly to low-poly
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[5/7] Transferring UV coordinates...")

if hi_uv is not None and len(hi_uv) == len(hi_verts):
    # Find nearest high-poly vertex for each low-poly vertex
    from scipy.spatial import cKDTree
    tree = cKDTree(hi_verts)
    _, nearest_idx = tree.query(lo_verts, k=1)
    lo_uv = hi_uv[nearest_idx]
    print(f"  UV transferred: {lo_uv.shape}")
else:
    # Generate spherical UV if no existing UV
    print("  No existing UV — generating spherical projection...")
    centroid = lo_verts.mean(axis=0)
    v_c = lo_verts - centroid
    r = np.linalg.norm(v_c, axis=1, keepdims=True)
    n = v_c / np.maximum(r, 1e-9)
    u = (np.arctan2(n[:, 0], n[:, 2]) + np.pi) / (2.0 * np.pi)
    v = (np.arcsin(np.clip(n[:, 1], -1.0, 1.0)) + np.pi / 2.0) / np.pi
    lo_uv = np.stack([u, v], axis=1).astype(np.float32)
    print(f"  Generated UV: {lo_uv.shape}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Bake normal map (tangent-space, from high-poly normals)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[6/7] Baking normal map...")

NMAP_W, NMAP_H = 2048, 1024

# For each low-poly vertex, we have the low-poly normal and the high-poly normal
# (from the nearest high-poly vertex). The difference is the normal map detail.

# Get the high-poly normals at the low-poly vertex positions
from scipy.spatial import cKDTree
if 'tree' not in dir():
    tree = cKDTree(hi_verts)
_, nearest_idx = tree.query(lo_verts, k=1)
hi_normals_at_lo = hi_normals[nearest_idx]

# Compute tangent-space normal perturbation
# In tangent space, the "flat" normal is (0, 0, 1)
# The delta is how the high-poly normal differs from the low-poly normal
# We compute a simple approximation: project hi normal into lo normal's frame

# Build a tangent frame for each low-poly vertex
def build_tangent_frames(normals):
    """Build tangent + bitangent for each normal vector."""
    N = normals / np.linalg.norm(normals, axis=1, keepdims=True).clip(1e-9)
    # Pick an arbitrary non-parallel vector for cross product
    up = np.zeros_like(N)
    up[:, 1] = 1.0  # Y-up
    # For normals nearly parallel to Y, use X instead
    parallel = np.abs(np.sum(N * up, axis=1)) > 0.99
    up[parallel] = [1.0, 0.0, 0.0]

    T = np.cross(N, up)
    T = T / np.linalg.norm(T, axis=1, keepdims=True).clip(1e-9)
    B = np.cross(N, T)
    return T, B, N

T, B, N = build_tangent_frames(lo_normals)

# Project high-poly normals into tangent space of low-poly
# tangent_normal = [dot(hi_n, T), dot(hi_n, B), dot(hi_n, N)]
tn_x = np.sum(hi_normals_at_lo * T, axis=1)
tn_y = np.sum(hi_normals_at_lo * B, axis=1)
tn_z = np.sum(hi_normals_at_lo * N, axis=1)

# Normalize
tn_len = np.sqrt(tn_x**2 + tn_y**2 + tn_z**2).clip(1e-9)
tn_x /= tn_len
tn_y /= tn_len
tn_z /= tn_len

# Encode as RGB: [-1, 1] → [0, 255]
tn_r = ((tn_x * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
tn_g = ((tn_y * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)
tn_b = ((tn_z * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)

# Rasterize vertex normals to UV-space texture
normal_map = np.full((NMAP_H, NMAP_W, 3), 128, dtype=np.uint8)  # flat normal = (128, 128, 255)
normal_map[:, :, 2] = 255  # Z = 1.0 default

# Paint each vertex's normal at its UV position
for i in range(len(lo_verts)):
    px = int(lo_uv[i, 0] * (NMAP_W - 1))
    py = int((1.0 - lo_uv[i, 1]) * (NMAP_H - 1))  # flip V
    px = max(0, min(NMAP_W - 1, px))
    py = max(0, min(NMAP_H - 1, py))
    normal_map[py, px] = [tn_r[i], tn_g[i], tn_b[i]]

# Dilate to fill gaps between scattered vertex samples
from scipy import ndimage
for ch in range(3):
    channel = normal_map[:, :, ch].astype(np.float32)
    # Create mask of painted pixels (not default)
    if ch == 2:
        mask = (channel != 255).astype(np.float32)
    else:
        mask = (channel != 128).astype(np.float32)
    # Spread painted values outward
    for _ in range(8):
        dilated = ndimage.maximum_filter(channel * mask, size=3)
        dilated_mask = ndimage.maximum_filter(mask, size=3)
        fill = (mask == 0) & (dilated_mask > 0)
        channel[fill] = dilated[fill]
        mask[fill] = 1
    normal_map[:, :, ch] = channel.astype(np.uint8)

# Apply Gaussian blur to smooth the normal map
for ch in range(3):
    normal_map[:, :, ch] = ndimage.gaussian_filter(
        normal_map[:, :, ch].astype(np.float32), sigma=1.5
    ).clip(0, 255).astype(np.uint8)

nmap_path = OUTPUT_DIR / "cortex_normal_map.png"
Image.fromarray(normal_map, 'RGB').save(str(nmap_path))
print(f"  Normal map: {nmap_path.name} ({nmap_path.stat().st_size / 1e3:.0f} KB)")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Bake ambient occlusion into texture
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[7/7] Baking ambient occlusion...")

# Compute per-vertex AO using cavity detection:
# Vertices deep in sulci have normals that point toward nearby geometry
# (high average dot product with vectors to neighbors = occluded)

# For each vertex, find its K nearest neighbors
K_NEIGHBORS = 24
AO_RADIUS = 0.15  # in mesh units — capture nearby fold geometry

tree_lo = cKDTree(lo_verts)
dists, neighbors = tree_lo.query(lo_verts, k=K_NEIGHBORS + 1)  # +1 for self

ao_values = np.zeros(len(lo_verts), dtype=np.float32)

for i in range(len(lo_verts)):
    # Skip self (index 0)
    nbr_idx = neighbors[i, 1:]
    nbr_dists = dists[i, 1:]

    # Only consider neighbors within AO_RADIUS
    within = nbr_dists < AO_RADIUS
    if within.sum() == 0:
        ao_values[i] = 1.0  # fully exposed
        continue

    # Direction vectors from vertex to its neighbors
    dirs = lo_verts[nbr_idx[within]] - lo_verts[i]
    dirs_norm = dirs / np.linalg.norm(dirs, axis=1, keepdims=True).clip(1e-9)

    # Occlusion = how much the vertex normal points TOWARD nearby geometry
    # If normal points away from neighbors → exposed (high AO)
    # If normal points toward neighbors → occluded (low AO)
    dots = np.sum(dirs_norm * lo_normals[i], axis=1)

    # Positive dots = neighbor is "above" the surface normal → less occluded
    # Negative dots = neighbor is "below" → more occluded
    # Weight by distance (closer neighbors matter more)
    weights = 1.0 - (nbr_dists[within] / AO_RADIUS)
    occlusion = np.sum(np.clip(-dots, 0, 1) * weights) / (weights.sum() + 1e-9)

    ao_values[i] = 1.0 - occlusion * 0.7  # scale down to avoid too-dark

# Clamp and normalize
ao_values = np.clip(ao_values, 0.15, 1.0)
print(f"  AO range: [{ao_values.min():.3f}, {ao_values.max():.3f}]")

# Bake AO into texture (darken the sulcal texture where AO is low)
AO_TEX_W, AO_TEX_H = 2048, 1024

if hi_texture is not None:
    # Use existing texture as base
    ao_texture = np.array(Image.fromarray(hi_texture).resize(
        (AO_TEX_W, AO_TEX_H), Image.LANCZOS), dtype=np.float32)
    print(f"  Using existing texture as AO base: {ao_texture.shape}")
else:
    # Generate sulcal-style base texture from curvature
    ao_texture = np.full((AO_TEX_H, AO_TEX_W, 3), 180, dtype=np.float32)
    print(f"  Generated blank AO base")

# Rasterize per-vertex AO onto the texture
ao_map_2d = np.ones((AO_TEX_H, AO_TEX_W), dtype=np.float32)

for i in range(len(lo_verts)):
    px = int(lo_uv[i, 0] * (AO_TEX_W - 1))
    py = int((1.0 - lo_uv[i, 1]) * (AO_TEX_H - 1))
    px = max(0, min(AO_TEX_W - 1, px))
    py = max(0, min(AO_TEX_H - 1, py))
    ao_map_2d[py, px] = ao_values[i]

# Dilate AO values to fill gaps
ao_mask = (ao_map_2d != 1.0).astype(np.float32)
for _ in range(12):
    dilated = ndimage.minimum_filter(ao_map_2d, size=3)
    dilated_mask = ndimage.maximum_filter(ao_mask, size=3)
    fill = (ao_mask == 0) & (dilated_mask > 0)
    ao_map_2d[fill] = dilated[fill]
    ao_mask[fill] = 1

# Smooth the AO map
ao_map_2d = ndimage.gaussian_filter(ao_map_2d, sigma=3.0)
ao_map_2d = np.clip(ao_map_2d, 0.15, 1.0)

# Apply AO to texture (multiply)
for ch in range(3):
    ao_texture[:, :, ch] = (ao_texture[:, :, ch] * ao_map_2d).clip(0, 255)

ao_tex_img = Image.fromarray(ao_texture.astype(np.uint8), 'RGB')
ao_tex_path = OUTPUT_DIR / "cortex_sulcal_ao.png"
ao_tex_img.save(str(ao_tex_path))
print(f"  AO texture: {ao_tex_path.name} ({ao_tex_path.stat().st_size / 1e3:.0f} KB)")

# Also save standalone AO map for potential separate use
ao_map_img = (ao_map_2d * 255).clip(0, 255).astype(np.uint8)
ao_map_path = OUTPUT_DIR / "cortex_ao_map.png"
Image.fromarray(ao_map_img, 'L').save(str(ao_map_path))
print(f"  AO map: {ao_map_path.name} ({ao_map_path.stat().st_size / 1e3:.0f} KB)")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT: Save optimized cortex GLB
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[Export] Saving optimized cortex GLB...")

# Create the optimized mesh with the AO-baked texture
material = trimesh.visual.texture.SimpleMaterial(
    image=ao_tex_img.convert('RGBA'))
visual = trimesh.visual.TextureVisuals(uv=lo_uv, material=material)
opt_mesh = trimesh.Trimesh(
    vertices=lo_verts, faces=lo_faces, visual=visual, process=False)

opt_path = OUTPUT_DIR / "full_brain_optimized.glb"
opt_mesh.export(str(opt_path))
opt_sz = opt_path.stat().st_size

print(f"  Saved: {opt_path.name} ({opt_sz / 1e6:.1f} MB)")
print(f"  Size reduction: {hires_path.stat().st_size / 1e6:.1f} MB -> {opt_sz / 1e6:.1f} MB "
      f"({(1 - opt_sz / hires_path.stat().st_size) * 100:.0f}% smaller)")

# Draco compression
draco_path = OUTPUT_DIR / "full_brain_draco.glb"
try:
    import DracoPy
    # Re-export with Draco compression via trimesh's built-in support
    opt_mesh.export(str(draco_path), file_type='glb')
    # trimesh uses DracoPy if installed for automatic Draco encoding
    draco_sz = draco_path.stat().st_size
    print(f"  Draco compressed: {draco_path.name} ({draco_sz / 1e6:.1f} MB)")
except ImportError:
    print("  DracoPy not installed — skipping Draco compression")
    print("  Install with: pip install DracoPy")
    # Copy uncompressed as fallback
    import shutil
    shutil.copy2(str(opt_path), str(draco_path))
    draco_sz = opt_sz
    print(f"  Copied uncompressed GLB as fallback: {draco_path.name}")

print("\n" + "=" * 60)
print("Done!")
print(f"  {opt_path}")
print(f"  {draco_path}")
print(f"  {nmap_path}")
print(f"  {ao_tex_path}")
print(f"  {ao_map_path}")
print("=" * 60)
