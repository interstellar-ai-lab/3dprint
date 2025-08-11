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
    
    # Test uploading a PNG to the bucket
    print(f"\n📤 Testing PNG upload to Supabase bucket...")
    upload_result = test_upload_png(manager)
    
    if upload_result["success"]:
        print("✅ PNG upload test completed successfully!")
        print(f"  Uploaded file: {upload_result['filename']}")
        print(f"  Public URL: {upload_result['public_url']}")
    else:
        print(f"❌ PNG upload test failed: {upload_result['error']}")
        if "solution" in upload_result:
            print(f"  💡 {upload_result['solution']}")
    
    # Test uploading a PNG using service key
    print(f"\n📤 Testing PNG upload using service key...")
    service_upload_result = test_upload_png_service_key()
    
    if service_upload_result["success"]:
        print("✅ Service key upload test completed successfully!")
        print(f"  Uploaded file: {service_upload_result['filename']}")
        print(f"  Public URL: {service_upload_result['public_url']}")
    else:
        print(f"❌ Service key upload test failed: {service_upload_result['error']}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

def test_upload_png(manager):
    """Test uploading a PNG file to Supabase storage"""
    try:
        from PIL import Image
        import io
        import tempfile
        from datetime import datetime
        
        # Create a simple test image
        print("  Creating test PNG image...")
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            test_image.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
        
        # Read the file data
        with open(temp_file_path, 'rb') as f:
            image_data = f.read()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_upload_{timestamp}.png"
        
        print(f"  Uploading {filename} to Supabase...")
        
        # Try to upload to Supabase using the manager's client
        try:
            response = manager.client.storage.from_(manager.bucket_name).upload(
                path=filename,
                file=image_data,
                file_options={"content-type": "image/png"}
            )
            
            if response:
                # Generate public URL
                public_url = f"{manager.supabase_url}/storage/v1/object/public/{manager.bucket_name}/{filename}"
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                return {
                    "success": True,
                    "filename": filename,
                    "public_url": public_url,
                    "size": len(image_data)
                }
            else:
                # Clean up temporary file
                os.unlink(temp_file_path)
                return {
                    "success": False,
                    "error": "Upload response was empty"
                }
                
        except Exception as upload_error:
            error_msg = str(upload_error)
            if "row-level security policy" in error_msg or "Unauthorized" in error_msg:
                print(f"  ⚠️ RLS Error: {error_msg}")
                print(f"  💡 Solution: Use SUPABASE_SERVICE_ROLE_KEY instead of SUPABASE_ANON_KEY")
                print(f"  📝 To fix this, set the environment variable:")
                print(f"     export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                return {
                    "success": False,
                    "error": f"RLS Policy Error: {error_msg}. Use service role key for uploads.",
                    "solution": "Set SUPABASE_SERVICE_ROLE_KEY environment variable"
                }
            else:
                raise upload_error
            
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return {
            "success": False,
            "error": str(e)
        }

def test_upload_png_service_key():
    """Test uploading a PNG file using service key"""
    try:
        from PIL import Image
        import tempfile
        from datetime import datetime
        from supabase import create_client
        
        # Get service key from environment
        service_key = os.getenv('SUPABASE_SERVICE_KEY')
        supabase_url = os.getenv('SUPABASE_URL')
        
        if not service_key or not supabase_url:
            return {
                "success": False,
                "error": "Service key or URL not available"
            }
        
        # Create service key client
        service_client = create_client(supabase_url, service_key)
        
        # Create a simple test image
        print("  Creating test PNG image for service key upload...")
        test_image = Image.new('RGB', (100, 100), color='blue')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            test_image.save(temp_file, format='PNG')
            temp_file_path = temp_file.name
        
        # Read the file data
        with open(temp_file_path, 'rb') as f:
            image_data = f.read()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"service_key_test_{timestamp}.png"
        
        print(f"  Uploading {filename} with service key...")
        
        # Upload to Supabase using service key client
        response = service_client.storage.from_("generated-images-bucket").upload(
            path=filename,
            file=image_data,
            file_options={"content-type": "image/png"}
        )
        
        if response:
            # Generate public URL
            public_url = f"{supabase_url}/storage/v1/object/public/generated-images-bucket/{filename}"
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return {
                "success": True,
                "filename": filename,
                "public_url": public_url,
                "size": len(image_data)
            }
        else:
            # Clean up temporary file
            os.unlink(temp_file_path)
            return {
                "success": False,
                "error": "Upload response was empty"
            }
            
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    test_supabase_studio()
