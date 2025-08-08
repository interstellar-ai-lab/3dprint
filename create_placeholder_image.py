#!/usr/bin/env python3
"""
Create a placeholder image for the studio
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image():
    """Create a placeholder image for when images fail to load"""
    
    # Create a 400x300 image with a light gray background
    width, height = 400, 300
    img = Image.new('RGB', (width, height), color='#f5f5f5')
    draw = ImageDraw.Draw(img)
    
    # Add a border
    draw.rectangle([0, 0, width-1, height-1], outline='#ddd', width=2)
    
    # Add text
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "Image Not Available"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text with a shadow effect
    draw.text((x+2, y+2), text, fill='#999', font=font)
    draw.text((x, y), text, fill='#666', font=font)
    
    # Add a smaller subtitle
    subtitle = "Generated image could not be loaded"
    try:
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        small_font = ImageFont.load_default()
    
    subtitle_bbox = draw.textbbox((0, 0), subtitle, small_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = y + text_height + 10
    
    draw.text((subtitle_x, subtitle_y), subtitle, fill='#999', font=small_font)
    
    # Save the image
    static_dir = "webapp/static"
    os.makedirs(static_dir, exist_ok=True)
    
    placeholder_path = os.path.join(static_dir, "placeholder-image.png")
    img.save(placeholder_path, "PNG")
    
    print(f"✅ Placeholder image created: {placeholder_path}")
    return placeholder_path

if __name__ == "__main__":
    create_placeholder_image()
