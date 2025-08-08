#!/usr/bin/env python3
"""
Test script to verify studio integration
"""

import requests
import json

def test_studio_integration():
    """Test studio API endpoints"""
    print("🔧 Testing Studio Integration")
    print("=" * 40)
    
    base_url = "http://localhost:8001"
    
    # Test 1: Health check
    print("\n1️⃣ Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Studio sessions endpoint
    print("\n2️⃣ Testing sessions endpoint...")
    try:
        response = requests.get(f"{base_url}/api/sessions")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sessions endpoint working - found {len(data.get('sessions', []))} sessions")
        else:
            print(f"❌ Sessions endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sessions endpoint error: {e}")
        return False
    
    # Test 3: Studio health endpoint
    print("\n3️⃣ Testing studio health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/studio/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Studio health endpoint working - {data.get('service')}")
        else:
            print(f"❌ Studio health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Studio health endpoint error: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All studio integration tests passed!")
    print("The studio module is working correctly with the main app.")
    
    return True

if __name__ == "__main__":
    success = test_studio_integration()
    if not success:
        print("\n❌ Some tests failed. Check the logs above for details.")
        exit(1)
    else:
        print("\n✅ All tests completed successfully!")
