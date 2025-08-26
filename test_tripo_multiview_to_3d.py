import os
import time
import requests
import sys
from PIL import Image
import io
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("TRIPO_API_KEY")
if not API_KEY:
    raise ValueError("TRIPO_API_KEY not found in environment variables. Please set it in your .env file.")

BASE = "https://api.tripo3d.ai/v2/openapi"
HDRS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def download_image(url: str) -> Image.Image:
    """Download image from URL and return PIL Image object"""
    print(f"Downloading image from: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))

def  crop_multiview_image(image: Image.Image) -> dict:
    """Crop multiview image into 4 separate views"""
    width, height = image.size
    half_width = width // 2
    half_height = height // 2
    
    # Crop into 4 quadrants
    # Top left: front view
    front_view = image.crop((0, 0, half_width, half_height))
    
    left_view = image.crop((half_width, 0, width, half_height))
    
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

def upload_image(image: Image.Image, filename: str) -> str:
    """Upload image to Tripo and return image token"""
    url = "https://api.tripo3d.ai/v2/openapi/upload/sts"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Save image to bytes
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    files = {'file': (filename, img_buffer, 'image/png')}
    
    print(f"Uploading {filename}...")
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    
    data = response.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Upload error: {data}")
    
    image_token = data["data"]["image_token"]
    print(f"Uploaded {filename}, got token: {image_token}")
    return image_token

def create_multiview_task(views: dict, model_version="v3.0-20250812", texture=True, pbr=True):
    """Create multiview-to-model task"""
    # Upload each view to get image tokens
    image_tokens = {}
    for view_name, image in views.items():
        filename = f"{view_name}_view.png"
        image_tokens[view_name] = upload_image(image, filename)
    
    # Create payload with image tokens in correct order: [front, left, back, right]
    payload = {
        "type": "multiview_to_model",
        "model_version": model_version,
        "texture": texture,
        "pbr": pbr,
        "files": [
            {
                "type": "png",
                "file_token": image_tokens["front"]
            },
            {
                "type": "png",
                "file_token": image_tokens["left"]
            },
            {
                "type": "png", 
                "file_token": image_tokens["back"]
            },
            {
                "type": "png",
                "file_token": image_tokens["right"]
            }
        ]
    }
    
    print("Submitting multiview-to-model task...")
    print(f"Payload keys: {list(payload.keys())}")
    
    try:
        r = requests.post(f"{BASE}/task", json=payload, headers=HDRS, timeout=60)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Create task error: {data}")
        return data["data"]["task_id"]
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise

def get_task(task_id: str):
    """Get task status and results"""
    r = requests.get(f"{BASE}/task/{task_id}", headers=HDRS, timeout=60)
    r.raise_for_status()
    return r.json()

def download(url: str, out_path: str):
    """Download file from URL"""
    print(f"Downloading: {url}")
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return out_path

def save_cropped_views(views: dict, output_dir: str = "cropped_views"):
    """Save cropped views for inspection"""
    os.makedirs(output_dir, exist_ok=True)
    for view_name, image in views.items():
        filename = f"{output_dir}/{view_name}_view.png"
        image.save(filename)
        print(f"Saved {view_name} view: {filename}")

if __name__ == "__main__":
    # Download the multiview image
    multiview_url = "https://nzkkbpekateqhygeghmw.supabase.co/storage/v1/object/public/generated-images-bucket/Libra_vibe_coffee_mug_with_pink_handle_2_20250822_063738.png"
    
    try:
        # Download and process the image
        image = download_image(multiview_url)
        print(f"Original image size: {image.size}")
        
        # Crop into 4 views
        views = crop_multiview_image(image)
        print("Cropped image into 4 views")
        
        # Save cropped views for inspection
        save_cropped_views(views)
        
        # Submit multiview-to-model task with texture and PBR options
        # texture=True: Enable texturing (default: True)
        # pbr=True: Enable PBR materials (default: True)
        # If pbr=True, texture is ignored and used as True
        task_id = create_multiview_task(views, texture=True, pbr=True)
        print("Task ID:", task_id)
        
        # Poll for completion
        print("Polling for completion... (this can take several minutes)")
        while True:
            info = get_task(task_id)
            if info.get("code") != 0:
                print("Error:", info)
                sys.exit(1)
            
            status = info["data"]["status"]
            print(f"Status: {status}")
            
            if status in ("success", "succeeded", "SUCCESS"):
                out = info["data"]["output"]
                # Get model URL (prefer PBR model if available)
                model_url = out.get("pbr_model") or out.get("model")
                if not model_url:
                    print("No model URL found in output:", out)
                    sys.exit(1)
                
                # Download the 3D model
                output_path = "tripo_multiview_model.glb"
                path = download(model_url, output_path)
                print(f"Success! Downloaded 3D model: {path}")
                break
            elif status in ("failed", "error"):
                print("Task failed:", info)
                sys.exit(1)
            
            time.sleep(10)  # Poll every 10 seconds
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
