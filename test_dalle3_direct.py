import asyncio
import os
from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel
from openai import AsyncOpenAI, OpenAI
from agents import set_tracing_disabled
import base64
import aiohttp

# Disable tracing for cleaner output
set_tracing_disabled(disabled=True)

# API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI clients
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

# Model configuration for text generation
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)

# Agent for text processing
text_agent = Agent(
    name="TextAgent",
    instructions="You are an agent that processes text and creates prompts for image generation. You do not generate images yourself.",
    model=model
)

# Create a session
session = SQLiteSession("test_dalle_session")

async def generate_image_with_dalle3(prompt: str) -> str:
    """Generate image using DALL-E 3 directly"""
    try:
        print(f"🎨 Generating image with DALL-E 3: {prompt[:50]}...")
        
        response = await asyncio.to_thread(
            openai_sync_client.images.generate,
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard"
        )
        
        image_url = response.data[0].url
        print(f"✅ DALL-E 3 image generated: {image_url[:50]}...")
        return image_url
        
    except Exception as e:
        print(f"❌ Error generating image with DALL-E 3: {e}")
        return ""

async def download_image_to_base64(image_url: str) -> tuple[str, str]:
    """Download image from URL and convert to base64"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    mime_type = "image/png"  # DALL-E 3 returns PNG
                    return base64_data, mime_type
                else:
                    print(f"Failed to download image: {response.status}")
                    return "", ""
    except Exception as e:
        print(f"Error downloading image: {e}")
        return "", ""

async def test_dalle3_approach(object_name: str):
    """Test the DALL-E 3 approach"""
    print(f"🧪 Testing DALL-E 3 approach for: {object_name}")
    
    # Step 1: Use GPT-4o to create a detailed prompt
    prompt_creation = f"""Create a detailed prompt for generating an image of a {object_name} that can be used for 3D CAD reconstruction. 
    The image should have a white background, high detail, and be suitable for 3D modeling."""
    
    try:
        print(f"📝 Creating image prompt with GPT-4o...")
        result = await asyncio.wait_for(
            Runner.run(text_agent, prompt_creation, session=session),
            timeout=60  # 1 minute timeout
        )
        
        dalle_prompt = result.final_output
        print(f"✅ Prompt created: {dalle_prompt[:100]}...")
        
        # Step 2: Generate image with DALL-E 3
        image_url = await generate_image_with_dalle3(dalle_prompt)
        
        if image_url:
            # Step 3: Convert to base64 for display
            b64_data, mime_type = await download_image_to_base64(image_url)
            
            if b64_data:
                print(f"✅ Successfully converted image to base64")
                print(f"📊 Base64 length: {len(b64_data)} characters")
                print(f"🔗 Original URL: {image_url}")
                
                # Step 4: Create JSON response
                json_response = {
                    "metadata": f"Generated image of a {object_name} using DALL-E 3. Prompt: {dalle_prompt}",
                    "image_url": image_url,
                    "description": f"High-quality image of a {object_name} suitable for 3D CAD reconstruction"
                }
                
                print(f"✅ Final JSON response created")
                return True, json_response
            else:
                print(f"❌ Failed to convert image to base64")
                return False, None
        else:
            print(f"❌ Failed to generate image with DALL-E 3")
            return False, None
            
    except asyncio.TimeoutError:
        print(f"❌ Prompt creation timed out")
        return False, None
    except Exception as e:
        print(f"❌ Error in DALL-E 3 approach: {e}")
        return False, None

async def test_multi_view_generation(object_name: str):
    """Test generating multiple views for 3D reconstruction"""
    print(f"\n🧪 Testing multi-view generation for: {object_name}")
    
    # Create a prompt for multiple views
    multi_view_prompt = f"""Create a detailed prompt for generating a single image that shows 16 different views of a {object_name} arranged in a 4x4 grid layout. 
    Each view should show the {object_name} from a different angle (front, back, left, right, top, bottom, and 10 intermediate angles). 
    All views should have consistent lighting, white background, high detail, and the {object_name} should appear the same size in each view. 
    This image will be used for 3D CAD reconstruction."""
    
    try:
        print(f"📝 Creating multi-view prompt with GPT-4o...")
        result = await asyncio.wait_for(
            Runner.run(text_agent, multi_view_prompt, session=session),
            timeout=60
        )
        
        dalle_prompt = result.final_output
        print(f"✅ Multi-view prompt created: {dalle_prompt[:100]}...")
        
        # Generate the multi-view image
        image_url = await generate_image_with_dalle3(dalle_prompt)
        
        if image_url:
            b64_data, mime_type = await download_image_to_base64(image_url)
            
            if b64_data:
                json_response = {
                    "metadata": f"Generated multi-view image of a {object_name} using DALL-E 3. Prompt: {dalle_prompt}",
                    "image_url": image_url,
                    "description": f"Single image containing 16 different views of a {object_name} arranged in a 4x4 grid for 3D CAD reconstruction"
                }
                
                print(f"✅ Multi-view image generated successfully")
                print(f"✅ Successfully converted multi-view image to base64")
                print(f"📊 Base64 length: {len(b64_data)} characters")
                print(f"🔗 Multi-view Image URL: {image_url}")
                return True, json_response
            else:
                print(f"❌ Failed to convert multi-view image to base64")
                return False, None
        else:
            print(f"❌ Failed to generate multi-view image")
            return False, None
            
    except asyncio.TimeoutError:
        print(f"❌ Multi-view prompt creation timed out")
        return False, None
    except Exception as e:
        print(f"❌ Error in multi-view generation: {e}")
        return False, None

async def main():
    print("🚀 Starting DALL-E 3 Direct Image Generation Tests")
    print("=" * 60)
    
    # Get user input for the object to generate
    object_name = input("What object would you like to generate an image of? (e.g., dog, car, chair, apple): ").strip()
    if not object_name:
        object_name = "dog"  # Default fallback
    print(f"🎯 Generating images for: {object_name}")
    print()
    
    # Test 1: Simple DALL-E 3 approach
    success1, result1 = await test_dalle3_approach(object_name)
    
    # Test 2: Multi-view generation
    success2, result2 = await test_multi_view_generation(object_name)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ Simple DALL-E 3 approach: {'PASS' if success1 else 'FAIL'}")
    print(f"✅ Multi-view generation: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All DALL-E 3 tests passed!")
        print("\n📋 Sample JSON responses:")
        if result1:
            print("Simple approach result:")
            print(f"  Image URL: {result1['image_url'][:50]}...")
        if result2:
            print("Multi-view approach result:")
            print(f"  Image URL: {result2['image_url'][:50]}...")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 