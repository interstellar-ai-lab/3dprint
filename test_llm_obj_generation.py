#!/usr/bin/env python3
"""
Test script for LLM OBJ generation
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_3d_mesh_with_llm

async def test_llm_obj_generation():
    """Test that the LLM generates OBJ content"""
    
    print("🧪 Testing LLM OBJ Generation")
    print("=" * 50)
    
    # Test data
    test_metadata = "A modern coffee mug with handle, cylindrical shape, white ceramic material"
    test_image_urls = [
        "https://example.com/mug_front.png",
        "https://example.com/mug_side.png",
        "https://example.com/mug_top.png"
    ]
    
    print(f"📝 Testing with metadata: {test_metadata}")
    print(f"🖼️  Testing with {len(test_image_urls)} image URLs")
    
    try:
        # Test LLM mesh generation
        result = await generate_3d_mesh_with_llm(test_metadata, test_image_urls)
        
        if result and not result.startswith("Error"):
            print(f"✅ Successfully generated mesh: {result}")
            
            # Check if the file exists and contains OBJ content
            if os.path.exists(result):
                with open(result, 'r') as f:
                    content = f.read()
                
                print(f"✅ Mesh file created: {result}")
                print(f"✅ File size: {len(content)} characters")
                
                # Check for OBJ content
                vertices = content.count('v ')
                faces = content.count('f ')
                normals = content.count('vn ')
                
                print(f"✅ Contains {vertices} vertices, {faces} faces, {normals} normals")
                
                # Show first few lines
                lines = content.split('\n')[:10]
                print("📄 First 10 lines:")
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                
                if vertices > 0 and faces > 0:
                    print("🎉 SUCCESS: Valid OBJ content generated!")
                else:
                    print("⚠️  WARNING: File created but no valid OBJ content found")
            else:
                print(f"❌ Mesh file not found at: {result}")
        else:
            print(f"❌ Failed to generate mesh: {result}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_obj_generation()) 