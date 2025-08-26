import os
import time
import requests
import sys
from PIL import Image
import io
import base64
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
MESHY_API_KEY = os.getenv("MESHY_API_KEY")
if not MESHY_API_KEY:
    raise ValueError("MESHY_API_KEY not found in environment variables. Please set it in your .env file.")

# Meshy API configuration
MESHY_BASE_URL = "https://api.meshy.ai/openapi/v1"
HEADERS = {
    "Authorization": f"Bearer {MESHY_API_KEY}",
    "Content-Type": "application/json"
}

def download_image(url: str) -> Image.Image:
    """Download image from URL and return PIL Image object"""
    print(f"Downloading image from: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))

def crop_multiview_image(image: Image.Image) -> dict:
    """Crop multiview image into 4 separate views"""
    width, height = image.size
    half_width = width // 2
    half_height = height // 2
    
    # Crop into 4 quadrants
    # Top left: front view
    front_view = image.crop((0, 0, half_width, half_height))
    
    # Top right: left view
    left_view = image.crop((half_width, 0, width, half_height))
    
    # Bottom left: right view
    right_view = image.crop((0, half_height, half_width, height))
    
    # Bottom right: back view
    back_view = image.crop((half_width, half_height, width, height))
    
    return {
        "front": front_view,
        "right": right_view, 
        "left": left_view,
        "back": back_view
    }

def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def image_to_data_uri(image: Image.Image) -> str:
    """Convert PIL Image to data URI format for Meshy API"""
    base64_str = image_to_base64(image)
    return f"data:image/png;base64,{base64_str}"

def create_meshy_multiview_task(views: dict, 
                               should_remesh=True,
                               should_texture=True,
                               enable_pbr=True):
    """
    Create Multi-Image to 3D task using Meshy API
    
    Args:
        views: Dictionary with 'front', 'left', 'back', 'right' PIL Image objects
        should_remesh: Whether to remesh the model
        should_texture: Whether to generate textures
        enable_pbr: Whether to generate PBR maps
    
    Returns:
        task_id: The Meshy task ID
    """
    
    # Convert images to data URIs
    image_urls = []
    view_names = ["front", "left", "back", "right"]  # Meshy expects this order
    
    for view_name in view_names:
        if view_name in views:
            image = views[view_name]
            data_uri = image_to_data_uri(image)
            image_urls.append(data_uri)
            print(f"Converted {view_name} view to data URI")
        else:
            raise ValueError(f"Missing {view_name} view in views dictionary")
    
    # Create payload according to Meshy API documentation
    payload = {
        "image_urls": image_urls,
        "should_remesh": should_remesh,
        "should_texture": should_texture,
        "enable_pbr": enable_pbr
    }
    
    print("Creating Meshy Multi-Image to 3D task...")
    print(f"Payload keys: {list(payload.keys())}")
    print(f"Number of images: {len(image_urls)}")
    print(f"Should Remesh: {should_remesh}")
    print(f"Should Texture: {should_texture}")
    print(f"Enable PBR: {enable_pbr}")
    
    try:
        response = requests.post(
            f"{MESHY_BASE_URL}/multi-image-to-3d",
            headers=HEADERS,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        task_id = data["result"]
        print(f"Meshy task created successfully. Task ID: {task_id}")
        return task_id
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise
    except Exception as e:
        print(f"Error creating Meshy task: {e}")
        raise

def get_meshy_task_status(task_id: str):
    """Get Meshy task status and results"""
    try:
        response = requests.get(
            f"{MESHY_BASE_URL}/multi-image-to-3d/{task_id}",
            headers=HEADERS,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting task status: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise

def download_meshy_model(url: str, output_path: str):
    """Download 3D model from Meshy URL"""
    print(f"Downloading model from: {url}")
    
    try:
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Model downloaded successfully: {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading model: {e}")
        raise

def save_cropped_views(views: dict, output_dir: str = "meshy_cropped_views"):
    """Save cropped views for inspection"""
    os.makedirs(output_dir, exist_ok=True)
    for view_name, image in views.items():
        filename = f"{output_dir}/{view_name}_view.png"
        image.save(filename)
        print(f"Saved {view_name} view: {filename}")

def check_meshy_balance():
    """Check Meshy API balance"""
    try:
        response = requests.get(
            f"{MESHY_BASE_URL}/balance",
            headers=HEADERS,
            timeout=60
        )
        response.raise_for_status()
        
        balance_data = response.json()
        print("Meshy API Balance:")
        print(json.dumps(balance_data, indent=2))
        return balance_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error checking balance: {e}")
        return None

def demo_meshy_multiview_to_3d():
    """Demo the complete Meshy Multi-Image to 3D workflow"""
    print("=" * 70)
    print("MESHY MULTI-IMAGE TO 3D API DEMO")
    print("=" * 70)
    
    # Configuration
    multiview_url = "https://nzkkbpekateqhygeghmw.supabase.co/storage/v1/object/public/generated-images-bucket/Libra_vibe_coffee_mug_with_pink_handle_2_20250822_063738.png"
    
    # Meshy API parameters
    should_remesh = True  # Enable remeshing
    should_texture = True  # Generate textures
    enable_pbr = True  # Enable PBR for better quality
    
    try:
        # Check API balance first
        print("\n💰 Checking Meshy API balance...")
        check_meshy_balance()
        
        # Download and process the multiview image
        print(f"\n🖼️ Downloading multiview image from: {multiview_url}")
        image = download_image(multiview_url)
        print(f"Original image size: {image.size}")
        
        # Crop into 4 views
        print("\n✂️ Cropping image into 4 views...")
        views = crop_multiview_image(image)
        print("Successfully cropped image into 4 views")
        
        # Save cropped views for inspection
        save_cropped_views(views)
        
        # Create Meshy Multi-Image to 3D task
        print(f"\n🚀 Creating Meshy Multi-Image to 3D task...")
        task_id = create_meshy_multiview_task(
            views=views,
            should_remesh=should_remesh,
            should_texture=should_texture,
            enable_pbr=enable_pbr
        )
        
        print(f"Task ID: {task_id}")
        
        # Poll for completion
        print("\n⏳ Polling for completion... (this can take several minutes)")
        while True:
            task_info = get_meshy_task_status(task_id)
            
            status = task_info["status"]
            progress = task_info.get("progress", 0)
            
            print(f"Status: {status} | Progress: {progress}%")
            
            if status == "SUCCEEDED":
                print("✅ Task completed successfully!")
                break
            elif status in ["FAILED", "CANCELED"]:
                error_msg = task_info.get("task_error", {}).get("message", "Unknown error")
                print(f"❌ Task failed: {error_msg}")
                sys.exit(1)
            
            time.sleep(10)  # Poll every 10 seconds
        
        # Download the 3D model
        print("\n📦 Downloading 3D model...")
        model_urls = task_info["model_urls"]
        
        # Download GLB format (most common)
        if "glb" in model_urls:
            glb_url = model_urls["glb"]
            glb_path = "meshy_multiview_model.glb"
            download_meshy_model(glb_url, glb_path)
            print(f"✅ GLB model downloaded: {glb_path}")
        
        # Download other formats if available
        for format_name, url in model_urls.items():
            if format_name != "glb":  # Already downloaded GLB
                format_path = f"meshy_multiview_model.{format_name}"
                download_meshy_model(url, format_path)
                print(f"✅ {format_name.upper()} model downloaded: {format_path}")
        
        # Download thumbnail if available
        if "thumbnail_url" in task_info:
            thumbnail_url = task_info["thumbnail_url"]
            thumbnail_path = "meshy_multiview_thumbnail.png"
            download_meshy_model(thumbnail_url, thumbnail_path)
            print(f"✅ Thumbnail downloaded: {thumbnail_path}")
        
        # Download textures if available
        if "texture_urls" in task_info and task_info["texture_urls"]:
            texture_dir = "meshy_textures"
            os.makedirs(texture_dir, exist_ok=True)
            
            for i, texture_set in enumerate(task_info["texture_urls"]):
                for texture_type, url in texture_set.items():
                    texture_path = f"{texture_dir}/texture_{i}_{texture_type}.png"
                    download_meshy_model(url, texture_path)
                    print(f"✅ {texture_type} texture downloaded: {texture_path}")
        
        print("\n🎉 MESHY MULTI-IMAGE TO 3D DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("Generated files:")
        print(f"  🖼️ Cropped views: meshy_cropped_views/")
        if "glb" in model_urls:
            print(f"  📦 3D Model (GLB): meshy_multiview_model.glb")
        if "thumbnail_url" in task_info:
            print(f"  🖼️ Thumbnail: meshy_multiview_thumbnail.png")
        if "texture_urls" in task_info and task_info["texture_urls"]:
            print(f"  🎨 Textures: meshy_textures/")
        
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 MESHY MULTI-IMAGE TO 3D API DEMO")
    print("This script demonstrates Meshy's Multi-Image to 3D API")
    print("Make sure you have set MESHY_API_KEY in your .env file")
    print()
    
    try:
        demo_meshy_multiview_to_3d()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        sys.exit(1)
