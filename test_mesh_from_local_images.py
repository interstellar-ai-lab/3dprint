#!/usr/bin/env python3
"""
Test script to generate OBJ mesh from local images
"""

import asyncio
import sys
import os
import pathlib
import glob

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_3d_mesh_with_llm

async def test_mesh_from_local_images():
    """Test generating OBJ mesh from local images"""
    
    print("🧪 Testing Mesh Generation from Local Images")
    print("=" * 50)
    
    # Target directory
    target_dir = "/Users/Interstellar/Documents/3dprint/openai-agents-python/webapp/generated_images/session_840c1b06-e317-45cd-9b83-d24875c2eedf"
    
    print(f"📁 Target directory: {target_dir}")
    
    # Check if directory exists
    if not os.path.exists(target_dir):
        print(f"❌ Directory not found: {target_dir}")
        return
    
    # Find all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(target_dir, ext)
        image_files.extend(glob.glob(pattern))
    
    # Sort files to ensure consistent order
    image_files.sort()
    
    print(f"🖼️  Found {len(image_files)} image files:")
    for i, img_file in enumerate(image_files):
        file_size = os.path.getsize(img_file)
        print(f"   {i+1}: {os.path.basename(img_file)} ({file_size} bytes)")
    
    if not image_files:
        print("❌ No image files found in directory")
        return
    
    # Create metadata based on the images
    metadata = f"Generated from {len(image_files)} local images in session directory. Images appear to be different views of the same object for 3D reconstruction."
    
    print(f"\n📝 Metadata: {metadata}")
    
    try:
        # Test LLM mesh generation with local image paths
        print(f"\n🎮 Generating 3D mesh from {len(image_files)} local images...")
        
        # Convert local file paths to file:// URLs for the LLM
        image_urls = [f"file://{img_file}" for img_file in image_files]
        
        result = await generate_3d_mesh_with_llm(metadata, image_urls)
        
        if result and not result.startswith("Error"):
            print(f"✅ Successfully generated mesh: {result}")
            
            # Check if the file exists and contains OBJ content
            if os.path.exists(result):
                with open(result, 'r') as f:
                    content = f.read()
                
                print(f"✅ Mesh file created: {result}")
                print(f"✅ File size: {len(content)} characters")
                
                # Check for OBJ content
                vertices = content.count('v ')
                faces = content.count('f ')
                normals = content.count('vn ')
                
                print(f"✅ Contains {vertices} vertices, {faces} faces, {normals} normals")
                
                # Show first few lines
                lines = content.split('\n')[:10]
                print("📄 First 10 lines:")
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                
                if vertices > 0 and faces > 0:
                    print("🎉 SUCCESS: Valid OBJ content generated from local images!")
                else:
                    print("⚠️  WARNING: File created but no valid OBJ content found")
            else:
                print(f"❌ Mesh file not found at: {result}")
        else:
            print(f"❌ Failed to generate mesh: {result}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_mesh_from_directory(directory_path: str):
    """Test generating OBJ mesh from any directory"""
    
    print(f"🧪 Testing Mesh Generation from Directory: {directory_path}")
    print("=" * 50)
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Find all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(directory_path, ext)
        image_files.extend(glob.glob(pattern))
    
    # Sort files to ensure consistent order
    image_files.sort()
    
    print(f"🖼️  Found {len(image_files)} image files:")
    for i, img_file in enumerate(image_files):
        file_size = os.path.getsize(img_file)
        print(f"   {i+1}: {os.path.basename(img_file)} ({file_size} bytes)")
    
    if not image_files:
        print("❌ No image files found in directory")
        return
    
    # Create metadata
    metadata = f"Generated from {len(image_files)} local images in directory: {os.path.basename(directory_path)}"
    
    try:
        # Convert local file paths to file:// URLs for the LLM
        image_urls = [f"file://{img_file}" for img_file in image_files]
        
        result = await generate_3d_mesh_with_llm(metadata, image_urls)
        
        if result and not result.startswith("Error"):
            print(f"✅ Successfully generated mesh: {result}")
            
            if os.path.exists(result):
                with open(result, 'r') as f:
                    content = f.read()
                
                vertices = content.count('v ')
                faces = content.count('f ')
                
                print(f"✅ Mesh contains {vertices} vertices, {faces} faces")
                
                if vertices > 0 and faces > 0:
                    print("🎉 SUCCESS: Valid OBJ content generated!")
                    return result
                else:
                    print("⚠️  WARNING: No valid OBJ content found")
            else:
                print(f"❌ Mesh file not found at: {result}")
        else:
            print(f"❌ Failed to generate mesh: {result}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return None

if __name__ == "__main__":
    # Test with the specific directory
    asyncio.run(test_mesh_from_local_images())
    
    # You can also test with any other directory by uncommenting:
    # asyncio.run(test_mesh_from_directory("/path/to/your/image/directory")) 