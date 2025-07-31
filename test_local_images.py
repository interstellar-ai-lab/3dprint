#!/usr/bin/env python3
"""
Test script for local image saving functionality
"""

import asyncio
import sys
import os
import pathlib

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_images_from_prompts

async def test_local_image_saving():
    """Test that images are saved locally"""
    
    print("🧪 Testing Local Image Saving")
    print("=" * 50)
    
    # Test prompts
    test_prompts = [
        "A red coffee mug on white background, front view",
        "A blue coffee mug on white background, side view",
        "A green coffee mug on white background, top view"
    ]
    
    print(f"📝 Testing with {len(test_prompts)} prompts...")
    
    try:
        # Generate images
        image_urls, local_paths = await generate_images_from_prompts(test_prompts)
        
        print(f"✅ Generated {len(image_urls)} image URLs")
        print(f"✅ Saved {len([p for p in local_paths if p])} images locally")
        
        # Check local files
        for i, local_path in enumerate(local_paths):
            if local_path:
                if os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    print(f"✅ Image {i+1}: {local_path} ({file_size} bytes)")
                else:
                    print(f"❌ Image {i+1}: File not found at {local_path}")
            else:
                print(f"⚠️  Image {i+1}: No local path")
        
        # Check if metadata file was created
        images_dir = pathlib.Path("generated_images")
        if images_dir.exists():
            session_dirs = [d for d in images_dir.iterdir() if d.is_dir() and d.name.startswith("session_")]
            if session_dirs:
                latest_session = max(session_dirs, key=lambda x: x.stat().st_mtime)
                metadata_file = latest_session / "metadata.txt"
                if metadata_file.exists():
                    print(f"✅ Metadata file created: {metadata_file}")
                    with open(metadata_file, 'r') as f:
                        content = f.read()
                    print(f"📄 Metadata content preview: {content[:200]}...")
                else:
                    print("❌ Metadata file not found")
            else:
                print("❌ No session directories found")
        else:
            print("❌ Generated images directory not found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_local_image_saving()) 