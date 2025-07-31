#!/usr/bin/env python3
"""
Complete test pipeline for image generation and LLM-based 3D mesh creation
"""

import asyncio
import sys
import os
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import (
    generate_images_from_prompts, 
    download_images_locally,
    generate_3d_mesh_with_llm,
    generation_agent,
    Runner,
    SQLiteSession
)

async def test_complete_pipeline():
    """Test the complete pipeline: image generation -> LLM mesh creation"""
    
    query = "a modern coffee mug with handle"
    
    print("🚀 Testing Complete Pipeline")
    print(f"Query: {query}")
    print("=" * 50)
    
    # Step 1: Generate image prompts using the agent
    print("\n📝 Step 1: Generating image prompts...")
    try:
        session = SQLiteSession("test_pipeline")
        result = await Runner.run(
            generation_agent, 
            f"Please generate the materials needed for 3D CAD generation for: {query}", 
            session=session
        )
        
        # Parse the response
        try:
            parsed_output = json.loads(result.final_output)
            metadata = parsed_output.get("metadata", "")
            image_prompts = parsed_output.get("image_prompts", [])
            description = parsed_output.get("description", "")
            print(f"✅ Generated {len(image_prompts)} image prompts")
            print(f"✅ Metadata: {metadata[:100]}...")
        except (json.JSONDecodeError, KeyError):
            print("⚠️  Could not parse JSON response, using fallback")
            metadata = result.final_output
            image_prompts = []
            description = ""
            
    except Exception as e:
        print(f"❌ Error in step 1: {str(e)}")
        return
    
    # Step 2: Generate images from prompts
    print("\n🖼️  Step 2: Generating images from prompts...")
    try:
        if image_prompts:
            image_urls, _ = await generate_images_from_prompts(image_prompts)
            print(f"✅ Generated {len(image_urls)} images")
            
            # Show first few URLs
            for i, url in enumerate(image_urls[:3]):
                print(f"   Image {i+1}: {url[:50]}...")
        else:
            print("⚠️  No image prompts found, skipping image generation")
            image_urls = []
    
    # Step 3: Download images locally
    print("\n⬇️  Step 3: Downloading images locally...")
    try:
        if image_urls:
            local_image_paths = await download_images_locally(image_urls, "test_pipeline")
            print(f"✅ Downloaded {len([p for p in local_image_paths if p])} images locally")
            
            # Show first few local paths
            for i, local_path in enumerate(local_image_paths[:3]):
                if local_path:
                    print(f"   Local {i+1}: {local_path}")
        else:
            print("⚠️  No images to download")
            local_image_paths = []
            
    except Exception as e:
        print(f"❌ Error in step 2: {str(e)}")
        image_urls = []
    
    # Step 3: Generate 3D mesh using LLM
    print("\n🎮 Step 3: Generating 3D mesh using LLM...")
    try:
        if image_urls:
            mesh_path = await generate_3d_mesh_with_llm(metadata, image_urls)
            
            if mesh_path and not mesh_path.startswith("Error"):
                print(f"✅ Successfully generated LLM-based mesh: {mesh_path}")
                
                # Check the mesh file
                if os.path.exists(mesh_path):
                    with open(mesh_path, 'r') as f:
                        content = f.read()
                    print(f"✅ Mesh file size: {len(content)} characters")
                    
                    # Count vertices and faces
                    vertices = content.count('v ')
                    faces = content.count('f ')
                    print(f"✅ Mesh contains {vertices} vertices and {faces} faces")
                else:
                    print("❌ Mesh file not found")
            else:
                print(f"❌ Failed to generate mesh: {mesh_path}")
        else:
            print("⚠️  No images available for mesh generation")
            
    except Exception as e:
        print(f"❌ Error in step 3: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Pipeline test completed!")

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline()) 