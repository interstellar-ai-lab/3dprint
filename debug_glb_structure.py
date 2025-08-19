#!/usr/bin/env python3
"""
Debug script to examine GLB file structure and names
"""

from pygltflib import GLTF2
from pathlib import Path

def examine_glb_detailed(glb_path: str):
    """Examine GLB file in detail to see all names and structure."""
    print(f"🔍 Examining GLB file: {glb_path}")
    print("=" * 60)
    
    gltf = GLTF2().load(glb_path)
    
    print(f"📊 File size: {Path(glb_path).stat().st_size / (1024 * 1024):.2f} MB")
    print(f"🏗️  Structure counts:")
    print(f"  - Nodes: {len(gltf.nodes) if gltf.nodes else 0}")
    print(f"  - Meshes: {len(gltf.meshes) if gltf.meshes else 0}")
    print(f"  - Materials: {len(gltf.materials) if gltf.materials else 0}")
    print(f"  - Textures: {len(gltf.textures) if gltf.textures else 0}")
    print(f"  - Images: {len(gltf.images) if gltf.images else 0}")
    print(f"  - Scenes: {len(gltf.scenes) if gltf.scenes else 0}")
    
    print(f"\n🏷️  NODE DETAILS:")
    if gltf.nodes:
        for i, node in enumerate(gltf.nodes):
            name = getattr(node, 'name', None)
            mesh = getattr(node, 'mesh', None)
            children = getattr(node, 'children', [])
            print(f"  Node {i}:")
            print(f"    Name: '{name}'")
            print(f"    Mesh index: {mesh}")
            print(f"    Children: {children}")
            if name and 'tripo' in name.lower():
                print(f"    ⚠️  CONTAINS TRIPO!")
    else:
        print("  No nodes found")
    
    print(f"\n🔲 MESH DETAILS:")
    if gltf.meshes:
        for i, mesh in enumerate(gltf.meshes):
            name = getattr(mesh, 'name', None)
            primitives = len(mesh.primitives) if mesh.primitives else 0
            print(f"  Mesh {i}:")
            print(f"    Name: '{name}'")
            print(f"    Primitives: {primitives}")
            if name and 'tripo' in name.lower():
                print(f"    ⚠️  CONTAINS TRIPO!")
    else:
        print("  No meshes found")
    
    print(f"\n🎨 MATERIAL DETAILS:")
    if gltf.materials:
        for i, material in enumerate(gltf.materials):
            name = getattr(material, 'name', None)
            print(f"  Material {i}:")
            print(f"    Name: '{name}'")
            if name and 'tripo' in name.lower():
                print(f"    ⚠️  CONTAINS TRIPO!")
    else:
        print("  No materials found")
    
    print(f"\n🖼️  TEXTURE DETAILS:")
    if gltf.textures:
        for i, texture in enumerate(gltf.textures):
            name = getattr(texture, 'name', None)
            source = getattr(texture, 'source', None)
            print(f"  Texture {i}:")
            print(f"    Name: '{name}'")
            print(f"    Source: {source}")
            if name and 'tripo' in name.lower():
                print(f"    ⚠️  CONTAINS TRIPO!")
    else:
        print("  No textures found")
    
    print(f"\n📸 IMAGE DETAILS:")
    if gltf.images:
        for i, image in enumerate(gltf.images):
            name = getattr(image, 'name', None)
            uri = getattr(image, 'uri', None)
            print(f"  Image {i}:")
            print(f"    Name: '{name}'")
            print(f"    URI: '{uri}'")
            if name and 'tripo' in name.lower():
                print(f"    ⚠️  CONTAINS TRIPO!")
    else:
        print("  No images found")
    
    print(f"\n🎬 SCENE DETAILS:")
    if gltf.scenes:
        for i, scene in enumerate(gltf.scenes):
            name = getattr(scene, 'name', None)
            nodes = getattr(scene, 'nodes', [])
            print(f"  Scene {i}:")
            print(f"    Name: '{name}'")
            print(f"    Nodes: {nodes}")
            if name and 'tripo' in name.lower():
                print(f"    ⚠️  CONTAINS TRIPO!")
    else:
        print("  No scenes found")
    
    print(f"\n📋 ASSET INFO:")
    if hasattr(gltf, 'asset') and gltf.asset:
        generator = getattr(gltf.asset, 'generator', None)
        version = getattr(gltf.asset, 'version', None)
        copyright = getattr(gltf.asset, 'copyright', None)
        print(f"  Generator: '{generator}'")
        print(f"  Version: '{version}'")
        print(f"  Copyright: '{copyright}'")
        if generator and 'tripo' in generator.lower():
            print(f"  ⚠️  GENERATOR CONTAINS TRIPO!")
        if copyright and 'tripo' in copyright.lower():
            print(f"  ⚠️  COPYRIGHT CONTAINS TRIPO!")
    else:
        print("  No asset info found")
    
    print("=" * 60)

def main():
    original_path = "/Users/Interstellar/Downloads/tripo_multiview_model.glb"
    cleaned_path = "/Users/Interstellar/Downloads/tripo_multiview_model_cleaned.glb"
    
    print("🔍 ORIGINAL FILE:")
    examine_glb_detailed(original_path)
    
    print("\n\n🔍 CLEANED FILE:")
    if Path(cleaned_path).exists():
        examine_glb_detailed(cleaned_path)
    else:
        print("❌ Cleaned file not found")

if __name__ == "__main__":
    main()
