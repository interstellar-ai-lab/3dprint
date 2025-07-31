#!/usr/bin/env python3
"""
Test script for downloading images locally
"""

import asyncio
import sys
import os
import pathlib

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import download_images_locally

async def test_download_images():
    """Test downloading images from URLs locally"""
    
    print("🧪 Testing Image Download Function")
    print("=" * 50)
    
    # Test URLs (these are example URLs - they might not work)
    test_urls = [
        "https://oaidalleapiprodscus.blob.core.windows.net/private/org-1234567890/user-1234567890/img-1234567890.png",
        "https://example.com/test1.png",
        "https://example.com/test2.png"
    ]
    
    print(f"📝 Testing with {len(test_urls)} URLs...")
    
    try:
        # Download images
        local_paths = await download_images_locally(test_urls, "test_download")
        
        print(f"✅ Attempted to download {len(test_urls)} images")
        print(f"✅ Successfully downloaded {len([p for p in local_paths if p])} images")
        
        # Check local files
        for i, local_path in enumerate(local_paths):
            if local_path:
                if os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    print(f"✅ Image {i+1}: {local_path} ({file_size} bytes)")
                else:
                    print(f"❌ Image {i+1}: File not found at {local_path}")
            else:
                print(f"⚠️  Image {i+1}: Download failed")
        
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
    asyncio.run(test_download_images()) 