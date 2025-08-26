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

def create_single_image_task(image: Image.Image, model_version="v3.0-20250812", texture=True, pbr=True):
    """Create single-image-to-model task"""
    # Upload image to get image token
    filename = "single_image.png"
    image_token = upload_image(image, filename)
    
    # Create payload for single image to model
    payload = {
        "type": "image_to_model",
        "model_version": model_version,
        "texture": texture,
        "pbr": pbr,
        "file": {
            "type": "png",
            "file_token": image_token
        }
    }
    
    print("Submitting single-image-to-model task...")
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

if __name__ == "__main__":
    # Test with a sample image URL
    image_url = "https://example.com/sample_image.jpg"
    
    try:
        # Download and process the image
        image = download_image(image_url)
        print(f"Image size: {image.size}")
        
        # Submit single-image-to-model task with texture and PBR options
        task_id = create_single_image_task(image, texture=True, pbr=True)
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
                output_path = "tripo_single_image_model.glb"
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
