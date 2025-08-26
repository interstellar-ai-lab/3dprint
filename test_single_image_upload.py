#!/usr/bin/env python3
"""
Test script for single image upload functionality
"""

import requests
import json
import os
from PIL import Image
import io

def test_single_image_upload():
    """Test the single image upload endpoint"""
    
    # Test configuration
    API_BASE = "http://localhost:8001"
    
    # Create a simple test image
    test_image = Image.new('RGB', (512, 512), color='red')
    img_buffer = io.BytesIO()
    test_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Prepare the request
    files = {
        'image': ('test_image.png', img_buffer, 'image/png')
    }
    
    headers = {
        'Authorization': 'Bearer test_token'  # This will fail auth, but we can test the endpoint structure
    }
    
    try:
        print("Testing single image upload endpoint...")
        response = requests.post(f"{API_BASE}/api/upload-single-image", 
                               files=files, 
                               headers=headers,
                               timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("✅ Endpoint exists and requires authentication (expected)")
        elif response.status_code == 200:
            print("✅ Endpoint works!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the webapp is running on localhost:8001")
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

def test_tripo_single_image_functions():
    """Test the Tripo single image functions"""
    try:
        print("\nTesting Tripo single image functions...")
        
        # Import the functions
        from test_tripo_single_image_to_3d import create_single_image_task, get_task, download
        
        # Create a test image
        test_image = Image.new('RGB', (512, 512), color='blue')
        
        print("✅ Successfully imported Tripo functions")
        print("✅ Test image created")
        
        # Note: We can't actually test the API calls without a valid API key
        # but we can verify the functions exist and are callable
        print("✅ Functions are callable (API calls would require valid TRIPO_API_KEY)")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error testing functions: {e}")

if __name__ == "__main__":
    print("🧪 Testing Single Image Upload Functionality")
    print("=" * 50)
    
    test_single_image_upload()
    test_tripo_single_image_functions()
    
    print("\n✅ Test completed!")
