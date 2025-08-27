#!/usr/bin/env python3
"""
Demo script for Google Gemini image editing functionality.
This script demonstrates how to use the Gemini 2.5 Flash Image Preview model
to edit images based on text instructions.
"""

import os
import sys
from pathlib import Path
from PIL import Image
from io import BytesIO

# Try to import required modules
try:
    import google.generativeai as genai
    from PIL import Image
    from io import BytesIO
except ImportError as e:
    print(f"Error: Required module not found: {e}")
    print("Please install required packages:")
    print("pip install google-generativeai Pillow")
    sys.exit(1)


from dotenv import load_dotenv
load_dotenv()

def setup_environment():
    """Set up the environment and check for required variables."""
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not found.")
        print("Please set your Gemini API key:")
        print("export GEMINI_API_KEY='your_api_key_here'")
        print("Or create a .env file with: GEMINI_API_KEY=your_api_key_here")
        return False
    
    # Configure the API
    try:
        genai.configure(api_key=api_key)
        print("✓ Gemini API configured successfully")
        return True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return False

def create_test_image(output_path="demo_test_image.jpg"):
    """Create a simple test image for demonstration."""
    try:
        # Create a colorful test image
        img = Image.new('RGB', (300, 200), color='lightblue')
        
        # Add some simple shapes for demonstration
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        # Draw a simple house
        draw.rectangle([50, 100, 150, 180], fill='brown')
        draw.polygon([(50, 100), (100, 50), (150, 100)], fill='red')
        draw.rectangle([70, 120, 90, 140], fill='black')  # door
        draw.rectangle([110, 110, 130, 130], fill='yellow')  # window
        
        # Save the image
        img.save(output_path, 'JPEG', quality=95)
        print(f"✓ Created test image: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error creating test image: {e}")
        return None

def edit_image_with_gemini(image_path, edit_instruction):
    """
    Edit an image using Gemini AI based on the provided instruction.
    
    Args:
        image_path (str): Path to the input image
        edit_instruction (str): Text instruction for editing the image
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the original image data
        if not os.path.exists(image_path):
            print(f"Error: Image file not found: {image_path}")
            return False
        
        with open(image_path, "rb") as f:
            original_image_bytes = f.read()
        
        print(f"✓ Loaded image: {image_path} ({len(original_image_bytes)} bytes)")
        
        # Create image part using current SDK approach
        image_part = {
            "inline_data": {
                "data": original_image_bytes,
                "mime_type": "image/jpeg"
            }
        }
        
        # Create the content with the original image and the editing instruction
        contents = [
            image_part,
            edit_instruction
        ]
        
        print(f"✓ Created content with instruction: {edit_instruction}")
        print("Sending image and edit instruction to Gemini...")
        
        # Create the model and generate the response
        model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
        response = model.generate_content(contents)
        
        print("✓ Received response from Gemini")
        
        # Check for and save the generated (edited) image
        edited_image_found = False
        for i, part in enumerate(response.candidates[0].content.parts):
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                edited_image = Image.open(BytesIO(image_data))
                
                base_name = Path(image_path).stem
                output_filename = f"{base_name}_edited_by_gemini.png"
                edited_image.save(output_filename)
                
                print(f"✓ Edited image saved as: {output_filename}")
                print(f"  Image size: {edited_image.size}")
                print(f"  Image mode: {edited_image.mode}")
                edited_image_found = True
                
            elif hasattr(part, 'text') and part.text:
                print(f"Model text response: {part.text}")
        
        if not edited_image_found:
            print("⚠ No edited image was generated. The model might have only provided text.")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error during image editing: {e}")
        return False

def main():
    """Main function to run the demo."""
    print("🎨 Gemini Image Editing Demo")
    print("=" * 40)
    
    # Setup environment
    if not setup_environment():
        print("\nDemo cannot continue without proper API configuration.")
        return
    
    # Create a test image
    test_image_path = create_test_image()
    if not test_image_path:
        print("Demo cannot continue without a test image.")
        return
    
    print(f"\n📸 Using test image: {test_image_path}")
    
    # Define the edit instruction
    edit_instruction = (
        "Make this image look like a painting by Vincent van Gogh, "
        "with swirling brushstrokes and vibrant colors. "
        "Add a small, friendly dragon flying in the sky."
    )
    
    print(f"\n🎯 Edit instruction: {edit_instruction}")
    
    # Perform the image editing
    print("\n🚀 Starting image editing process...")
    success = edit_image_with_gemini(test_image_path, edit_instruction)
    
    if success:
        print("\n✅ Demo completed successfully!")
        print("Check the current directory for the edited image.")
    else:
        print("\n❌ Demo encountered an error.")
    
    # Cleanup
    try:
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"✓ Cleaned up test image: {test_image_path}")
    except Exception as e:
        print(f"Warning: Could not clean up test image: {e}")

if __name__ == "__main__":
    main()
