#!/usr/bin/env python3
"""
Test script to verify GPT-4o Vision is working correctly
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_3d_mesh_with_llm

async def test_gpt4o_vision():
    """Test if GPT-4 Image model can analyze images and generate mesh"""
    
    print("🧪 Testing GPT-4 Image model for 3D mesh generation...")
    
    # Test parameters
    metadata = "Test object: Coffee mug with handle, ceramic material, white color, 10cm height"
    image_urls = [
        "https://example.com/mug1.jpg",  # These won't work, but we'll test the model call
        "https://example.com/mug2.jpg"
    ]
    
    print(f"📝 Test metadata: {metadata}")
    print(f"🖼️  Test image URLs: {image_urls}")
    
    try:
        # Call the function
        result = await generate_3d_mesh_with_llm(metadata, image_urls)
        
        print(f"✅ Function call completed!")
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
    asyncio.run(test_gpt4o_vision()) 