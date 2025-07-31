#!/usr/bin/env python3
"""
Test script for LLM-based 3D mesh generation
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import generate_3d_mesh_with_llm, download_image_to_base64

async def test_llm_mesh_generation():
    """Test the LLM-based mesh generation with sample data"""
    
    # Sample metadata
    metadata = """
    Object: Coffee Mug
    Material: Ceramic
    Color: White with blue rim
    Dimensions: 10cm height, 8cm diameter
    Features: Handle, cylindrical body, flat bottom
    Views: 16 different angles including front, back, sides, top, bottom, and various 3/4 views
    """
    
    # Sample image URLs (you can replace these with actual URLs)
    sample_image_urls = [
        "https://example.com/mug_front.jpg",
        "https://example.com/mug_back.jpg", 
        "https://example.com/mug_side.jpg",
        "https://example.com/mug_top.jpg"
    ]
    
    print("Testing LLM-based 3D mesh generation...")
    print(f"Metadata: {metadata[:100]}...")
    print(f"Number of images: {len(sample_image_urls)}")
    
    try:
        # Test the mesh generation
        mesh_path = await generate_3d_mesh_with_llm(metadata, sample_image_urls)
        
        if mesh_path and not mesh_path.startswith("Error"):
            print(f"✅ Successfully generated mesh: {mesh_path}")
            
            # Check if the file exists and has content
            if os.path.exists(mesh_path):
                with open(mesh_path, 'r') as f:
                    content = f.read()
                print(f"✅ Mesh file created with {len(content)} characters")
                print(f"✅ First 200 characters: {content[:200]}...")
            else:
                print("❌ Mesh file not found")
        else:
            print(f"❌ Failed to generate mesh: {mesh_path}")
            
    except Exception as e:
        print(f"❌ Error during mesh generation: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_llm_mesh_generation()) 