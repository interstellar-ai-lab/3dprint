#!/usr/bin/env python3
"""
Test script to check if GPT-4o and DALL-E 3 are working correctly
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multiagent import client, generate_image

async def test_dalle3():
    """Test if DALL-E 3 is working"""
    print("🎨 Testing DALL-E 3...")
    
    try:
        # Test DALL-E 3 image generation
        prompt = "A simple red coffee mug on a white background, centered, high quality"
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard"
        )
        
        image_url = response.data[0].url
        print(f"✅ DALL-E 3 working! Generated image URL: {image_url[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ DALL-E 3 error: {str(e)}")
        return False

async def test_gpt4o_vision():
    """Test if GPT-4o Vision is working"""
    print("🧠 Testing GPT-4o Vision...")
    
    try:
        # Test GPT-4o with a simple text prompt first
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Hello! Can you see this message?"}
            ],
            max_tokens=50
        )
        
        print(f"✅ GPT-4o text working! Response: {response.choices[0].message.content}")
        
        # Test GPT-4o Vision with a simple image (we'll use a simple PNG)
        # Create a simple 1x1 red pixel PNG
        import base64
        simple_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
        
        vision_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What do you see in this image?"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64.b64encode(simple_png).decode()}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        
        print(f"✅ GPT-4o Vision working! Response: {vision_response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ GPT-4o Vision error: {str(e)}")
        return False

async def test_generate_image_function():
    """Test the generate_image function from multiagent"""
    print("🖼️  Testing generate_image function...")
    
    try:
        # Import the function from multiagent
        from multiagent import generate_image
        
        result = generate_image("A blue coffee mug on white background", "low")
        
        if result and not result.startswith("Error"):
            print(f"✅ generate_image function working! Result: {result[:50]}...")
            return True
        else:
            print(f"❌ generate_image function error: {result}")
            return False
            
    except Exception as e:
        print(f"❌ generate_image function error: {str(e)}")
        return False

async def main():
    """Run all model tests"""
    print("🧪 Testing Model Availability")
    print("=" * 50)
    
    # Test DALL-E 3
    dalle3_working = await test_dalle3()
    print()
    
    # Test GPT-4o Vision
    gpt4o_working = await test_gpt4o_vision()
    print()
    
    # Test generate_image function
    generate_image_working = await test_generate_image_function()
    print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("=" * 50)
    print(f"DALL-E 3: {'✅ Working' if dalle3_working else '❌ Not Working'}")
    print(f"GPT-4o Vision: {'✅ Working' if gpt4o_working else '❌ Not Working'}")
    print(f"generate_image function: {'✅ Working' if generate_image_working else '❌ Not Working'}")
    
    if dalle3_working and gpt4o_working:
        print("\n🎉 All models are working! Your 3D generation pipeline should work correctly.")
    else:
        print("\n⚠️  Some models are not working. Check your API keys and model availability.")

if __name__ == "__main__":
    asyncio.run(main()) 