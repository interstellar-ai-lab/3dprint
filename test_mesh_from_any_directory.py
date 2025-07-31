#!/usr/bin/env python3
"""
Comprehensive test script to generate OBJ mesh from images in any directory
"""

import asyncio
import sys
import os
import pathlib
import glob
import argparse

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_3d_mesh_with_llm

async def test_mesh_from_directory(directory_path: str, max_images: int = 4):
    """Test generating OBJ mesh from images in a directory"""
    
    print(f"🧪 Testing Mesh Generation from Directory: {directory_path}")
    print("=" * 60)
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"❌ Directory not found: {directory_path}")
        return None
    
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
        return None
    
    # Limit the number of images to process
    if len(image_files) > max_images:
        print(f"📊 Limiting to first {max_images} images (out of {len(image_files)})")
        image_files = image_files[:max_images]
    
    # Create metadata based on the images
    metadata = f"Generated from {len(image_files)} local images in directory: {os.path.basename(directory_path)}. Images are different views of the same object for 3D reconstruction."
    
    print(f"\n📝 Metadata: {metadata}")
    print(f"🎯 Processing {len(image_files)} images...")
    
    try:
        # Convert local file paths to file:// URLs for the LLM
        image_urls = [f"file://{img_file}" for img_file in image_files]
        
        print(f"\n🎮 Generating 3D mesh from {len(image_urls)} images...")
        result = await generate_3d_mesh_with_llm(metadata, image_urls)
        
        if result and not result.startswith("Error"):
            print(f"✅ Successfully generated mesh: {result}")
            
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
                lines = content.split('\n')[:15]
                print("📄 First 15 lines:")
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                
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

async def list_available_directories():
    """List available image directories"""
    
    print("📁 Available Image Directories:")
    print("=" * 40)
    
    # Look for generated_images directory
    generated_images_dir = "webapp/generated_images"
    if os.path.exists(generated_images_dir):
        print(f"📂 {generated_images_dir}/")
        session_dirs = [d for d in os.listdir(generated_images_dir) if os.path.isdir(os.path.join(generated_images_dir, d))]
        
        for session_dir in session_dirs:
            session_path = os.path.join(generated_images_dir, session_dir)
            image_count = len([f for f in os.listdir(session_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))])
            print(f"   └── {session_dir}/ ({image_count} images)")
    
    # Look for other potential directories
    potential_dirs = [
        "generated_images",
        "images",
        "test_images",
        "sample_images"
    ]
    
    for dir_name in potential_dirs:
        if os.path.exists(dir_name):
            image_count = len([f for f in os.listdir(dir_name) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))])
            print(f"📂 {dir_name}/ ({image_count} images)")

async def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(description="Generate OBJ mesh from images in a directory")
    parser.add_argument("directory", nargs="?", help="Directory containing images")
    parser.add_argument("--max-images", type=int, default=4, help="Maximum number of images to process (default: 4)")
    parser.add_argument("--list", action="store_true", help="List available directories")
    
    args = parser.parse_args()
    
    if args.list:
        await list_available_directories()
        return
    
    if not args.directory:
        print("❌ Please provide a directory path or use --list to see available directories")
        print("\nUsage examples:")
        print("  python test_mesh_from_any_directory.py /path/to/images")
        print("  python test_mesh_from_any_directory.py --list")
        print("  python test_mesh_from_any_directory.py webapp/generated_images/session_XXXX --max-images 8")
        return
    
    result = await test_mesh_from_directory(args.directory, args.max_images)
    
    if result:
        print(f"\n🎯 Final result: {result}")
    else:
        print("\n❌ Failed to generate mesh")

if __name__ == "__main__":
    asyncio.run(main()) 