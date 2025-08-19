#!/usr/bin/env python3
"""
Test script to verify GLB cleanup results
"""

import json
from pathlib import Path
from pygltflib import GLTF2

def examine_glb(glb_path: str) -> dict:
    """Examine GLB file structure and return key information."""
    gltf = GLTF2().load(glb_path)
    
    info = {
        "file_path": glb_path,
        "file_size_mb": Path(glb_path).stat().st_size / (1024 * 1024),
        "nodes": [],
        "meshes": [],
        "materials": [],
        "textures": [],
        "images": [],
        "scenes": [],
        "asset_info": {}
    }
    
    # Examine nodes
    if gltf.nodes:
        for i, node in enumerate(gltf.nodes):
            node_info = {
                "index": i,
                "name": getattr(node, 'name', None),
                "mesh": getattr(node, 'mesh', None),
                "children": getattr(node, 'children', [])
            }
            info["nodes"].append(node_info)
    
    # Examine meshes
    if gltf.meshes:
        for i, mesh in enumerate(gltf.meshes):
            mesh_info = {
                "index": i,
                "name": getattr(mesh, 'name', None),
                "primitives_count": len(mesh.primitives) if mesh.primitives else 0
            }
            info["meshes"].append(mesh_info)
    
    # Examine materials
    if gltf.materials:
        for i, material in enumerate(gltf.materials):
            material_info = {
                "index": i,
                "name": getattr(material, 'name', None)
            }
            info["materials"].append(material_info)
    
    # Examine textures
    if gltf.textures:
        for i, texture in enumerate(gltf.textures):
            texture_info = {
                "index": i,
                "name": getattr(texture, 'name', None),
                "source": getattr(texture, 'source', None)
            }
            info["textures"].append(texture_info)
    
    # Examine images
    if gltf.images:
        for i, image in enumerate(gltf.images):
            image_info = {
                "index": i,
                "name": getattr(image, 'name', None),
                "uri": getattr(image, 'uri', None)
            }
            info["images"].append(image_info)
    
    # Examine scenes
    if gltf.scenes:
        for i, scene in enumerate(gltf.scenes):
            scene_info = {
                "index": i,
                "name": getattr(scene, 'name', None),
                "nodes": getattr(scene, 'nodes', [])
            }
            info["scenes"].append(scene_info)
    
    # Examine asset info
    if hasattr(gltf, 'asset') and gltf.asset:
        info["asset_info"] = {
            "generator": getattr(gltf.asset, 'generator', None),
            "version": getattr(gltf.asset, 'version', None),
            "copyright": getattr(gltf.asset, 'copyright', None)
        }
    
    return info

def print_comparison(original_info: dict, cleaned_info: dict):
    """Print a comparison between original and cleaned GLB files."""
    print("=" * 80)
    print("GLB CLEANUP COMPARISON")
    print("=" * 80)
    
    print(f"\n📁 FILE INFO:")
    print(f"Original: {original_info['file_path']} ({original_info['file_size_mb']:.2f} MB)")
    print(f"Cleaned:  {cleaned_info['file_path']} ({cleaned_info['file_size_mb']:.2f} MB)")
    
    print(f"\n🏗️  STRUCTURE:")
    print(f"Nodes:     {len(original_info['nodes'])} -> {len(cleaned_info['nodes'])}")
    print(f"Meshes:    {len(original_info['meshes'])} -> {len(cleaned_info['meshes'])}")
    print(f"Materials: {len(original_info['materials'])} -> {len(cleaned_info['materials'])}")
    print(f"Textures:  {len(original_info['textures'])} -> {len(cleaned_info['textures'])}")
    print(f"Images:    {len(original_info['images'])} -> {len(cleaned_info['images'])}")
    print(f"Scenes:    {len(original_info['scenes'])} -> {len(cleaned_info['scenes'])}")
    
    print(f"\n🏷️  NODE NAMES:")
    for i, (orig_node, clean_node) in enumerate(zip(original_info['nodes'], cleaned_info['nodes'])):
        orig_name = orig_node['name'] or f"unnamed_{i}"
        clean_name = clean_node['name'] or f"unnamed_{i}"
        if orig_name != clean_name:
            print(f"  Node {i}: '{orig_name}' -> '{clean_name}'")
        else:
            print(f"  Node {i}: '{orig_name}' (unchanged)")
    
    print(f"\n🔲 MESH NAMES:")
    for i, (orig_mesh, clean_mesh) in enumerate(zip(original_info['meshes'], cleaned_info['meshes'])):
        orig_name = orig_mesh['name'] or f"unnamed_{i}"
        clean_name = clean_mesh['name'] or f"unnamed_{i}"
        if orig_name != clean_name:
            print(f"  Mesh {i}: '{orig_name}' -> '{clean_name}'")
        else:
            print(f"  Mesh {i}: '{orig_name}' (unchanged)")
    
    print(f"\n🎨 MATERIAL NAMES:")
    for i, (orig_mat, clean_mat) in enumerate(zip(original_info['materials'], cleaned_info['materials'])):
        orig_name = orig_mat['name'] or f"unnamed_{i}"
        clean_name = clean_mat['name'] or f"unnamed_{i}"
        if orig_name != clean_name:
            print(f"  Material {i}: '{orig_name}' -> '{clean_name}'")
        else:
            print(f"  Material {i}: '{orig_name}' (unchanged)")
    
    print(f"\n🖼️  TEXTURE NAMES:")
    for i, (orig_tex, clean_tex) in enumerate(zip(original_info['textures'], cleaned_info['textures'])):
        orig_name = orig_tex['name'] or f"unnamed_{i}"
        clean_name = clean_tex['name'] or f"unnamed_{i}"
        if orig_name != clean_name:
            print(f"  Texture {i}: '{orig_name}' -> '{clean_name}'")
        else:
            print(f"  Texture {i}: '{orig_name}' (unchanged)")
    
    print(f"\n📸 IMAGE NAMES:")
    for i, (orig_img, clean_img) in enumerate(zip(original_info['images'], cleaned_info['images'])):
        orig_name = orig_img['name'] or f"unnamed_{i}"
        clean_name = clean_img['name'] or f"unnamed_{i}"
        if orig_name != clean_name:
            print(f"  Image {i}: '{orig_name}' -> '{clean_name}'")
        else:
            print(f"  Image {i}: '{orig_name}' (unchanged)")
    
    print(f"\n🎬 SCENE NAMES:")
    for i, (orig_scene, clean_scene) in enumerate(zip(original_info['scenes'], cleaned_info['scenes'])):
        orig_name = orig_scene['name'] or f"unnamed_{i}"
        clean_name = clean_scene['name'] or f"unnamed_{i}"
        if orig_name != clean_name:
            print(f"  Scene {i}: '{orig_name}' -> '{clean_name}'")
        else:
            print(f"  Scene {i}: '{orig_name}' (unchanged)")
    
    print(f"\n📋 ASSET INFO:")
    orig_gen = original_info['asset_info'].get('generator', 'None')
    clean_gen = cleaned_info['asset_info'].get('generator', 'None')
    if orig_gen != clean_gen:
        print(f"  Generator: '{orig_gen}' -> '{clean_gen}'")
    else:
        print(f"  Generator: '{orig_gen}' (unchanged)")
    
    orig_copyright = original_info['asset_info'].get('copyright', 'None')
    clean_copyright = cleaned_info['asset_info'].get('copyright', 'None')
    if orig_copyright != clean_copyright:
        print(f"  Copyright: '{orig_copyright}' -> '{clean_copyright}'")
    else:
        print(f"  Copyright: '{orig_copyright}' (unchanged)")
    
    print("=" * 80)

def main():
    original_path = "/Users/Interstellar/Downloads/shoes.glb"
    cleaned_path = "/Users/Interstellar/Downloads/shoes_cleaned.glb"
    
    if not Path(original_path).exists():
        print(f"❌ Original file not found: {original_path}")
        return
    
    if not Path(cleaned_path).exists():
        print(f"❌ Cleaned file not found: {cleaned_path}")
        print("Please run the cleanup script first: python glb_cleanup.py '/Users/Interstellar/Downloads/shoes.glb'")
        return
    
    print("🔍 Examining original GLB file...")
    original_info = examine_glb(original_path)
    
    print("🔍 Examining cleaned GLB file...")
    cleaned_info = examine_glb(cleaned_path)
    
    print_comparison(original_info, cleaned_info)

if __name__ == "__main__":
    main()
