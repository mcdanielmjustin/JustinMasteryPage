#!/usr/bin/env python3
"""
convert_atlas_to_glb.py -- Convert brainstem/cerebellum JSON+PNG to textured GLB

Replaces the 4.7MB JSON mesh files + 824KB textures with compact GLBs
that embed geometry + texture in a single file.

Before: brainstem_mesh.json (2.7MB) + brainstem_texture.png (276KB) = 3.0MB
        cerebellum_mesh.json (2.0MB) + cerebellum_texture.png (548KB) = 2.5MB
        Total: 5.5MB

After:  hires_brainstem.glb (~80KB) + hires_cerebellum.glb (~120KB)
        Total: ~200KB  (96% reduction)
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image
import trimesh
import trimesh.visual

OUTPUT_DIR = Path("data/brain_meshes")

print("=" * 60)
print("convert_atlas_to_glb.py -- JSON+PNG -> Textured GLB")
print("=" * 60)


def convert_atlas_mesh(region_id, json_path, texture_path, output_path):
    """Load JSON mesh + PNG texture, export as single GLB with embedded texture."""
    print(f"\n  [{region_id}] Loading JSON mesh: {json_path.name} ({json_path.stat().st_size / 1e6:.1f} MB)")

    with open(json_path) as f:
        data = json.load(f)

    positions = np.array(data['positions'], dtype=np.float32).reshape(-1, 3)
    normals = np.array(data['normals'], dtype=np.float32).reshape(-1, 3)
    uvs = np.array(data['uvs'], dtype=np.float32).reshape(-1, 2)
    indices = np.array(data['indices'], dtype=np.int32).reshape(-1, 3)

    print(f"  [{region_id}] Vertices: {len(positions):,}, Faces: {len(indices):,}")

    # Load texture and compress as JPEG for smaller GLB
    print(f"  [{region_id}] Loading texture: {texture_path.name} ({texture_path.stat().st_size / 1e3:.0f} KB)")
    tex_img = Image.open(texture_path).convert('RGB')
    # Downscale large textures (1024 -> 512 is plenty for these small meshes)
    max_dim = 512
    if max(tex_img.size) > max_dim:
        ratio = max_dim / max(tex_img.size)
        new_size = (int(tex_img.size[0] * ratio), int(tex_img.size[1] * ratio))
        tex_img = tex_img.resize(new_size, Image.LANCZOS)
        print(f"  [{region_id}] Downscaled to {tex_img.size[0]}x{tex_img.size[1]}")
    # Convert to JPEG bytes for embedding (much smaller than PNG)
    import io
    jpeg_buf = io.BytesIO()
    tex_img.save(jpeg_buf, format='JPEG', quality=85)
    jpeg_size = jpeg_buf.tell()
    jpeg_buf.seek(0)
    tex_img_final = Image.open(jpeg_buf).convert('RGBA')
    print(f"  [{region_id}] Texture: {tex_img.size[0]}x{tex_img.size[1]}, JPEG compressed ({jpeg_size / 1e3:.0f} KB)")

    # Create trimesh with PBR material
    material = trimesh.visual.material.PBRMaterial(
        baseColorTexture=tex_img_final,
        metallicFactor=0.0,
        roughnessFactor=0.68,
    )
    visual = trimesh.visual.TextureVisuals(uv=uvs, material=material)

    mesh = trimesh.Trimesh(
        vertices=positions,
        faces=indices,
        vertex_normals=normals,
        visual=visual,
        process=False,
    )

    # Export as GLB
    mesh.export(str(output_path), file_type='glb')
    out_size = output_path.stat().st_size
    in_size = json_path.stat().st_size + texture_path.stat().st_size

    print(f"  [{region_id}] Exported: {output_path.name} ({out_size / 1e3:.0f} KB)")
    print(f"  [{region_id}] Reduction: {in_size / 1e6:.1f} MB -> {out_size / 1e3:.0f} KB "
          f"({(1 - out_size / in_size) * 100:.0f}% smaller)")

    return out_size, in_size


total_before = 0
total_after = 0

# Brainstem
bs_json = OUTPUT_DIR / "brainstem_mesh.json"
bs_tex = OUTPUT_DIR / "brainstem_texture.png"
bs_out = OUTPUT_DIR / "hires_brainstem.glb"
if bs_json.exists() and bs_tex.exists():
    after, before = convert_atlas_mesh("brainstem", bs_json, bs_tex, bs_out)
    total_before += before
    total_after += after

# Cerebellum
cb_json = OUTPUT_DIR / "cerebellum_mesh.json"
cb_tex = OUTPUT_DIR / "cerebellum_texture.png"
cb_out = OUTPUT_DIR / "hires_cerebellum.glb"
if cb_json.exists() and cb_tex.exists():
    after, before = convert_atlas_mesh("cerebellum", cb_json, cb_tex, cb_out)
    total_before += before
    total_after += after

print(f"\n{'=' * 60}")
print(f"Total: {total_before / 1e6:.1f} MB -> {total_after / 1e3:.0f} KB "
      f"({(1 - total_after / total_before) * 100:.0f}% reduction)")
print(f"{'=' * 60}")
