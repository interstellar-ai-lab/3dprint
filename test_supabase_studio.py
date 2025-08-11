#!/usr/bin/env python3
"""
Test script for Supabase Studio Storage Manager
Demonstrates how to use the new StudioSupabaseManager to list images from Supabase storage
"""

import os
import json
from dotenv import load_dotenv
from studio_module import create_supabase_studio_manager

# Load environment variables
load_dotenv()

def test_supabase_studio():
    """Test the Supabase Studio Storage Manager"""
    print("🧪 Testing Supabase Studio Storage Manager")
    print("=" * 50)
    
    # Check if required environment variables are set
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("\n❌ Missing Environment Variables!")
        print("Please set the following environment variables:")
        print("- SUPABASE_URL=your_supabase_project_url")
        print("- SUPABASE_ANON_KEY=your_supabase_anon_key")
        return
    
    # Create Supabase Studio Manager
    print(f"\n🔌 Creating Supabase Studio Manager...")
    print(f"URL: {supabase_url}")
    
    manager = create_supabase_studio_manager(supabase_url, supabase_key)
    
    # Initialize the manager
    print("\n🚀 Initializing manager...")
    init_result = manager.initialize()
    
    if not init_result["success"]:
        print(f"❌ Initialization failed: {init_result['error']}")
        return
    
    print("✅ Manager initialized successfully!")
    
    # Test listing images
    print("\n📋 Listing images from Supabase storage...")
    list_result = manager.list_public_images(max_results=10)
    
    if list_result["success"]:
        print(f"✅ Found {list_result['total_count']} images:")
        
        for i, image in enumerate(list_result["images"], 1):
            print(f"\n  {i}. {image['filename']}")
            print(f"     Size: {image['size']:,} bytes")
            print(f"     Type: {image['content_type']}")
            print(f"     URL: {image['public_url']}")
            print(f"     Has 3D Model: {image['has_3d_model']}")
    else:
        print(f"❌ Failed to list images: {list_result['error']}")
    
    # Test getting metadata for a specific image
    if list_result["success"] and list_result["images"]:
        print(f"\n📊 Getting metadata for first image...")
        first_image = list_result["images"][0]
        metadata_result = manager.get_image_metadata(image_id=first_image["id"])
        
        if metadata_result["success"]:
            print("✅ Image metadata:")
            for key, value in metadata_result["metadata"].items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Failed to get metadata: {metadata_result['error']}")
    
    # Test generating signed URL
    if list_result["success"] and list_result["images"]:
        print(f"\n🔗 Generating signed URL for first image...")
        first_image = list_result["images"][0]
        signed_url_result = manager.generate_signed_url(first_image["name"])
        
        if signed_url_result["success"]:
            print("✅ Signed URL generated:")
            print(f"  URL: {signed_url_result['signed_url']}")
            print(f"  Expires: {signed_url_result['expires_at']}")
        else:
            print(f"❌ Failed to generate signed URL: {signed_url_result['error']}")
    
    # Test searching images
    print(f"\n🔍 Testing image search...")
    search_result = manager.search_images("car", max_results=5)
    
    if search_result["success"]:
        print(f"✅ Found {search_result['total_count']} images matching 'car':")
        for image in search_result["images"]:
            print(f"  📸 {image['target_object']} (ID: {image['id']})")
    else:
        print(f"❌ Search failed: {search_result['error']}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_supabase_studio()
