#!/usr/bin/env python3
"""
Simple test to verify generate_3d_mesh_with_llm function call
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_3d_mesh_with_llm

async def test_function_call():
    """Test if the function can be called with proper parameters"""
    
    print("🧪 Testing generate_3d_mesh_with_llm function call...")
    
    # Test parameters
    metadata = "Test object: Coffee mug with handle, ceramic material, white color"
    image_urls = [
        "https://example.com/mug1.jpg",
        "https://example.com/mug2.jpg",
        "https://example.com/mug3.jpg"
    ]
    
    print(f"📝 Test metadata: {metadata}")
    print(f"🖼️  Test image URLs: {image_urls}")
    
    try:
        # Call the function
        result = await generate_3d_mesh_with_llm(metadata, image_urls)
        
        print(f"✅ Function call successful!")
        print(f"📁 Result: {result}")
        
        if result and not result.startswith("Error"):
            print("✅ Function returned valid result")
        else:
            print("❌ Function returned error")
            
    except Exception as e:
        print(f"❌ Function call failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_function_call()) 