#!/usr/bin/env python3
"""
Test script for the updated clean_glb_asset_properties function in webapp/app.py
"""

import sys
import os
sys.path.append('webapp')

# Import the function from the webapp
from app import clean_glb_asset_properties

def test_glb_cleanup():
    """Test the GLB cleanup function with the tripo file"""
    
    # Test file path
    test_file = "/Users/Interstellar/Downloads/tripo_multiview_model.glb"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print("🧪 Testing updated clean_glb_asset_properties function...")
    print("=" * 60)
    
    # Read the original file
    with open(test_file, 'rb') as f:
        original_data = f.read()
    
    print(f"📁 Original file size: {len(original_data) / (1024 * 1024):.2f} MB")
    
    # Test the cleanup function
    try:
        cleaned_data = clean_glb_asset_properties(original_data)
        
        print(f"✅ Cleanup successful!")
        print(f"📁 Cleaned file size: {len(cleaned_data) / (1024 * 1024):.2f} MB")
        
        # Save the cleaned file for inspection
        output_file = "/Users/Interstellar/Downloads/tripo_multiview_model_webapp_cleaned.glb"
        with open(output_file, 'wb') as f:
            f.write(cleaned_data)
        
        print(f"💾 Saved cleaned file to: {output_file}")
        
        # Verify the cleaned file can be loaded
        from pygltflib import GLTF2
        gltf = GLTF2().load_from_bytes(cleaned_data)
        
        print(f"\n📊 Cleaned GLB Structure:")
        print(f"  - Nodes: {len(gltf.nodes) if gltf.nodes else 0}")
        print(f"  - Meshes: {len(gltf.meshes) if gltf.meshes else 0}")
        print(f"  - Materials: {len(gltf.materials) if gltf.materials else 0}")
        print(f"  - Textures: {len(gltf.textures) if gltf.textures else 0}")
        print(f"  - Images: {len(gltf.images) if gltf.images else 0}")
        print(f"  - Scenes: {len(gltf.scenes) if gltf.scenes else 0}")
        
        # Show some cleaned names
        if gltf.nodes:
            for i, node in enumerate(gltf.nodes):
                name = getattr(node, 'name', None)
                print(f"  Node {i}: '{name}'")
        
        if gltf.meshes:
            for i, mesh in enumerate(gltf.meshes):
                name = getattr(mesh, 'name', None)
                print(f"  Mesh {i}: '{name}'")
        
        if gltf.materials:
            for i, material in enumerate(gltf.materials):
                name = getattr(material, 'name', None)
                print(f"  Material {i}: '{name}'")
        
        if gltf.images:
            for i, image in enumerate(gltf.images):
                name = getattr(image, 'name', None)
                print(f"  Image {i}: '{name}'")
        
        # Check asset info
        if hasattr(gltf, 'asset') and gltf.asset:
            generator = getattr(gltf.asset, 'generator', None)
            copyright_info = getattr(gltf.asset, 'copyright', None)
            print(f"  Generator: '{generator}'")
            print(f"  Copyright: '{copyright_info}'")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_glb_cleanup()
