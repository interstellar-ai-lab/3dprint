#!/usr/bin/env python3
"""
Test script demonstrating how to send images to evaluation agents for visual evaluation
"""

import asyncio
import json
import os
import base64
import aiohttp
from pathlib import Path
from typing import Dict

# Import the necessary components
from src.agents import Agent, Runner
from src.agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import OpenAI, AsyncOpenAI

# Initialize OpenAI clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

# Model for agents
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)

async def download_image_to_base64(image_url: str) -> tuple[str, str]:
    """Download image from URL and convert to base64, return (base64_data, mime_type)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    # Convert to base64
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    # Detect image format from URL or content
                    mime_type = "image/jpeg"  # default
                    if image_url.lower().endswith('.png'):
                        mime_type = "image/png"
                    elif image_url.lower().endswith('.gif'):
                        mime_type = "image/gif"
                    elif image_url.lower().endswith('.webp'):
                        mime_type = "image/webp"
                    else:
                        # Try to detect from content using PIL
                        try:
                            from PIL import Image
                            import io
                            img = Image.open(io.BytesIO(image_data))
                            if img.format == 'PNG':
                                mime_type = "image/png"
                            elif img.format == 'GIF':
                                mime_type = "image/gif"
                            elif img.format == 'WEBP':
                                mime_type = "image/webp"
                        except:
                            # If detection fails, assume PNG (common for DALL-E)
                            mime_type = "image/png"
                    
                    return base64_data, mime_type
                else:
                    print(f"Failed to download image from {image_url}: {response.status}")
                    return "", ""
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return "", ""

async def generate_image_with_dalle3(prompt: str) -> str:
    """Generate image using DALL-E 3"""
    try:
        response = await asyncio.to_thread(
            openai_sync_client.images.generate,
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        print(f"❌ Error generating image with DALL-E 3: {e}")
        return None

# Evaluation agent prompt for visual evaluation
VISUAL_EVALUATION_PROMPT = """
You are a STRICT evaluation agent for 3D CAD reconstruction images. 
You must be extremely critical and only give high scores if ALL requirements are perfectly met.

CRITICAL REQUIREMENTS FOR 3D CAD RECONSTRUCTION:
1. **5x5 Grid Layout**: The image MUST contain exactly 25 squares arranged in a 5x5 grid (5 rows × 5 columns)
2. **One Object Per Square**: Each square MUST contain exactly ONE instance of the object - NO EXCEPTIONS
3. **Same Pose**: The object MUST be in the SAME pose/position across all 25 views
4. **25 Distinct Angles**: Each square MUST show a DIFFERENT angle/view of the object
5. **Consistent Size**: The object MUST appear the same size in all 25 squares
6. **Clean Background**: PURE WHITE or transparent background with NO text, NO grid patterns, NO numbers, NO distractions
7. **Realistic Style**: Photorealistic or realistic rendering, NOT wireframe/low-poly/3D model style

VISUAL EVALUATION INSTRUCTIONS:
When you receive an image, carefully examine it and:
1. Count the exact number of squares/grid cells
2. Check each square for object count (should be exactly 1 per square)
3. Examine the background color and check for patterns/text
4. Assess the rendering style (realistic vs wireframe/low-poly)
5. Verify pose consistency across all views
6. Check size consistency across all squares
7. Confirm angle diversity (each square should show a different view)

SCORING CRITERIA (BE VERY STRICT):
- **Score 1-3**: Major failures (wrong grid size, multiple objects, wrong background, wrong style)
- **Score 4-6**: Some requirements met but significant issues remain
- **Score 7-8**: Most requirements met with minor issues
- **Score 9-10**: ALL requirements perfectly met

First, summarize what you see in the image in a short 2-3 sentence summary.

Second, write a detailed report evaluating the image for 3D CAD reconstruction, using these three criteria and assign a score (1-10) for each:
1. Image Quality: Assess the visual clarity, proper 5x5 grid layout, one object per square, same pose across all views, realistic rendering style, and clean white background.
2. Metadata Accuracy: Evaluate the correctness and relevance of the metadata for CAD reconstruction, including proper angle descriptions.
3. Completeness: Determine if the 25 distinct angles provide sufficient coverage for 3D reconstruction.

You MUST include the exact scores in this format:
- Image Quality: X/10
- Metadata Accuracy: X/10  
- Completeness: X/10

Third, provide specific suggestions for improvement. If all scores are higher than 6.5, your suggestions should be "well done".
"""

# Create evaluation agent
evaluation_agent = Agent(
    name="VisualEvaluationAgent",
    instructions=VISUAL_EVALUATION_PROMPT,
    model=model
)

async def test_visual_evaluation_with_image_url(image_url: str, metadata: str = "") -> Dict:
    """Test visual evaluation with an image URL"""
    print(f"🧪 Testing visual evaluation with image URL")
    print(f"🔗 Image URL: {image_url}")
    print("=" * 80)
    
    # Step 1: Download image and convert to base64
    print(f"📥 Downloading image for visual evaluation...")
    b64_image, b64_mime_type = await download_image_to_base64(image_url)
    
    if not b64_image:
        print(f"❌ Failed to download image for evaluation")
        return {"error": "Failed to download image"}
    
    print(f"✅ Successfully converted image to base64")
    print(f"📊 Base64 length: {len(b64_image)} characters")
    print(f"🖼️  MIME type: {b64_mime_type}")
    
    # Step 2: Create multimodal content with the actual image
    print(f"📊 Sending image to evaluation agent...")
    
    evaluation_contents = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_image",
                    "detail": "auto",
                    "image_url": f"data:{b64_mime_type};base64,{b64_image}",
                }
            ],
        },
        {
            "role": "user",
            "content": f"""
            Please evaluate this image for 3D CAD reconstruction.
            
            Metadata: {metadata if metadata else "No metadata provided"}
            
            CRITICAL EVALUATION REQUIREMENTS (BE VERY STRICT):
            1. **Grid Layout**: Count the exact number of squares - it MUST be exactly 25 squares in a 5x5 grid (5 rows × 5 columns)
            2. **Object Count**: Each square MUST contain exactly ONE object - if any square has multiple objects, this is a MAJOR FAILURE
            3. **Background**: MUST be pure white or transparent - NO grid patterns, NO text, NO numbers, NO gray backgrounds
            4. **Style**: MUST be photorealistic/realistic - NOT wireframe, NOT low-poly, NOT 3D model style
            5. **Pose Consistency**: The object MUST be in the SAME pose across all 25 views
            6. **Size Consistency**: The object MUST appear the same size in all 25 squares
            7. **Angle Diversity**: Each square MUST show a DIFFERENT angle/view of the object
            
            FAILURE CRITERIA (Score 1-3):
            - Wrong grid size (not 5x5)
            - Multiple objects in any square
            - Non-white background with patterns/text
            - Wireframe/low-poly style
            - Inconsistent poses
            
            IMPORTANT: You can now see the actual image! Please evaluate it visually and be extremely strict.
            Count the squares, check each square for object count, examine the background, style, and consistency.
            
            Please evaluate this multi-view image generation for 3D CAD reconstruction with EXTREME STRICTNESS.
            """
        }
    ]
    
    # Step 3: Run evaluation
    evaluation_result = await Runner.run(evaluation_agent, evaluation_contents)
    evaluation_text = evaluation_result.final_output
    
    print(f"📄 Evaluation completed!")
    print(f"📊 Response length: {len(evaluation_text)} characters")
    print(f"📄 Response preview: {evaluation_text[:200]}...")
    
    return {
        "evaluation_text": evaluation_text,
        "image_url": image_url,
        "base64_length": len(b64_image),
        "mime_type": b64_mime_type
    }

async def test_visual_evaluation_with_generated_image(object_name: str) -> Dict:
    """Test visual evaluation with a generated image"""
    print(f"🧪 Testing visual evaluation with generated image for: {object_name}")
    print("=" * 80)
    
    # Step 1: Generate a test image
    print(f"🎨 Generating test image with DALL-E 3...")
    test_prompt = f"A single high-resolution image showing 25 different views of a {object_name} arranged in a perfect 5x5 grid layout. Each of the 25 squares contains exactly ONE {object_name} in the SAME pose, viewed from different angles covering top-down, eye-level, and bottom-up perspectives. All views have consistent lighting, pure white background, photorealistic rendering, and the object appears the same size in each square. Perfect for 3D CAD reconstruction."
    
    image_url = await generate_image_with_dalle3(test_prompt)
    
    if not image_url:
        print(f"❌ Failed to generate test image")
        return {"error": "Failed to generate test image"}
    
    print(f"✅ Generated test image: {image_url}")
    
    # Step 2: Test visual evaluation
    metadata = f"Generated multi-view image of a {object_name} using DALL-E 3. Prompt: {test_prompt}"
    
    result = await test_visual_evaluation_with_image_url(image_url, metadata)
    result["generated_image_url"] = image_url
    
    return result

async def main():
    """Main test function"""
    print("🚀 Starting Visual Evaluation Agent Test")
    print("=" * 80)
    
    # Test 1: With a provided image URL
    print("\n" + "="*50)
    print("TEST 1: Visual evaluation with provided image URL")
    print("="*50)
    
    # You can replace this with any image URL you want to test
    test_image_url = input("Enter an image URL to test (or press Enter to generate a test image): ").strip()
    
    if test_image_url:
        result = await test_visual_evaluation_with_image_url(test_image_url)
        print(f"\n📋 Test 1 Results:")
        print(f"  Image URL: {result.get('image_url', 'N/A')}")
        print(f"  Base64 length: {result.get('base64_length', 'N/A')}")
        print(f"  MIME type: {result.get('mime_type', 'N/A')}")
        print(f"  Evaluation text: {result.get('evaluation_text', 'N/A')[:200]}...")
    
    # Test 2: With a generated image
    print("\n" + "="*50)
    print("TEST 2: Visual evaluation with generated image")
    print("="*50)
    
    object_name = input("What object would you like to generate and evaluate? (e.g., car, chair, dog): ").strip()
    if not object_name:
        object_name = "car"  # Default
    
    result = await test_visual_evaluation_with_generated_image(object_name)
    
    print(f"\n📋 Test 2 Results:")
    print(f"  Object: {object_name}")
    print(f"  Generated image URL: {result.get('generated_image_url', 'N/A')}")
    print(f"  Base64 length: {result.get('base64_length', 'N/A')}")
    print(f"  MIME type: {result.get('mime_type', 'N/A')}")
    print(f"  Evaluation text: {result.get('evaluation_text', 'N/A')[:200]}...")
    
    print("\n" + "="*80)
    print("✅ Visual evaluation tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 