#!/usr/bin/env python3
"""
Simple test script for GCP upload functionality
"""

import sys
import os
sys.path.append('webapp')

from app import initialize_gcp_storage, upload_to_gcs
from PIL import Image, ImageDraw
import tempfile
from datetime import datetime

def test_simple_upload():
    """Test simple file upload to GCS"""
    print("🔧 Testing Simple GCP Upload")
    print("=" * 40)
    
    # Initialize GCP
    if not initialize_gcp_storage():
        print("❌ Failed to initialize GCP")
        return False
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), color='lightblue')
    draw = ImageDraw.Draw(img)
    draw.text((50, 90), "Test Image", fill='black')
    draw.text((30, 120), f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill='black')
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        img.save(temp_file.name, 'PNG')
        temp_path = temp_file.name
    
    print(f"✅ Test image created: {temp_path}")
    
    # Upload to GCS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gcs_path = f"test_uploads/simple_test_{timestamp}.png"
    
    gcs_url = upload_to_gcs(f"file://{temp_path}", gcs_path)
    
    if gcs_url:
        print(f"✅ Upload successful!")
        print(f"   GCS URL: {gcs_url}")
        print(f"   GCS Path: {gcs_path}")
        
        # Cleanup
        os.unlink(temp_path)
        print("✅ Test file cleaned up")
        
        return True
    else:
        print("❌ Upload failed")
        return False

if __name__ == "__main__":
    success = test_simple_upload()
    if success:
        print("\n🎉 GCP upload test completed successfully!")
    else:
        print("\n❌ GCP upload test failed!")
        sys.exit(1)
