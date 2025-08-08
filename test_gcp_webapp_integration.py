#!/usr/bin/env python3
"""
Test script to verify GCP storage integration with the webapp
"""

import os
import json
import tempfile
from datetime import datetime
from pathlib import Path

# Add the webapp directory to the path so we can import from it
import sys
sys.path.append('webapp')

# Import the GCP functions from the webapp
from app import initialize_gcp_storage, upload_to_gcs

def test_gcp_integration():
    """Test GCP storage integration"""
    print("🔧 Testing GCP Storage Integration with Webapp")
    print("=" * 50)
    
    # Test 1: Initialize GCP Storage
    print("\n1️⃣ Testing GCP Storage Initialization...")
    gcp_initialized = initialize_gcp_storage()
    
    if gcp_initialized:
        print("✅ GCP Storage initialized successfully")
    else:
        print("❌ GCP Storage initialization failed")
        return False
    
    # Test 2: Create a test file
    print("\n2️⃣ Creating test file...")
    test_content = f"Test file created at {datetime.now().isoformat()}"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name
    
    print(f"✅ Test file created: {temp_file_path}")
    
    # Test 3: Upload to GCS
    print("\n3️⃣ Testing file upload to GCS...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gcs_path = f"test_uploads/webapp_integration_test_{timestamp}.txt"
    
    gcs_url = upload_to_gcs(f"file://{temp_file_path}", gcs_path)
    
    if gcs_url:
        print(f"✅ File uploaded successfully to: {gcs_url}")
    else:
        print("❌ File upload failed")
        return False
    
    # Test 4: Test with a PNG file (simulating image upload)
    print("\n4️⃣ Testing PNG file upload (simulating image generation)...")
    
    # Create a simple PNG file using PIL
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "Test", fill='black')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_png:
            img.save(temp_png.name, 'PNG')
            temp_png_path = temp_png.name
        
        print(f"✅ Test PNG created: {temp_png_path}")
        
        # Upload PNG to GCS
        png_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gcs_png_path = f"generated_images/test_session/png_test_{png_timestamp}.png"
        
        gcs_png_url = upload_to_gcs(f"file://{temp_png_path}", gcs_png_path)
        
        if gcs_png_url:
            print(f"✅ PNG uploaded successfully to: {gcs_png_url}")
        else:
            print("❌ PNG upload failed")
            return False
            
    except ImportError:
        print("⚠️  PIL not available, skipping PNG test")
    except Exception as e:
        print(f"❌ PNG test failed: {e}")
        return False
    
    # Cleanup
    print("\n5️⃣ Cleaning up test files...")
    try:
        os.unlink(temp_file_path)
        if 'temp_png_path' in locals():
            os.unlink(temp_png_path)
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 All GCP integration tests passed!")
    print("The webapp should now be able to upload generated images to GCS.")
    
    return True

if __name__ == "__main__":
    success = test_gcp_integration()
    if not success:
        print("\n❌ Some tests failed. Check the logs above for details.")
        sys.exit(1)
    else:
        print("\n✅ All tests completed successfully!")
