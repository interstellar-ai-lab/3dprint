#!/usr/bin/env python3
"""
Test script for multi-view upload endpoint
"""

import requests
import os
from PIL import Image
import io

def create_test_image(size=(512, 512), color=(128, 128, 128)):
    """Create a simple test image"""
    img = Image.new('RGB', size, color)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def test_multiview_upload():
    """Test the multi-view upload endpoint"""
    
    # Create test images for each view
    views = {
        'front': create_test_image(color=(255, 0, 0)),    # Red
        'left': create_test_image(color=(0, 255, 0)),     # Green
        'back': create_test_image(color=(0, 0, 255)),     # Blue
        'right': create_test_image(color=(255, 255, 0))   # Yellow
    }
    
    # Prepare files for upload
    files = {}
    for view_name, buffer in views.items():
        files[view_name] = (f'{view_name}_test.png', buffer, 'image/png')
    
    print("🧪 Testing multi-view upload endpoint...")
    
    try:
        # Send request to the endpoint
        response = requests.post(
            'http://localhost:8001/api/upload-multiview',
            files=files,
            timeout=30
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Upload successful!")
            print(f"📋 Response data: {data}")
            
            if 'record_id' in data:
                print(f"🆔 Record ID: {data['record_id']}")
                print(f"🔗 Status URL: {data.get('status_url', 'N/A')}")
            
            return data
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the Flask server is running on port 8001")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_status_endpoint(record_id):
    """Test the status endpoint"""
    print(f"\n🔍 Testing status endpoint for record {record_id}...")
    
    try:
        response = requests.get(f'http://localhost:8001/api/generation-status/{record_id}')
        print(f"📡 Status response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Status data: {data}")
            return data
        else:
            print(f"❌ Status check failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting multi-view upload test...")
    
    # Test upload
    result = test_multiview_upload()
    
    if result and 'record_id' in result:
        # Test status endpoint
        test_status_endpoint(result['record_id'])
    
    print("\n✨ Test completed!")
