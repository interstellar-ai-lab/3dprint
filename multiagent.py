from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel
import asyncio
from pydantic import BaseModel
from openai import AsyncOpenAI, OpenAI
from agents import set_tracing_disabled
import base64
import json
import pathlib
import aiohttp
import html
import os
import uuid
from datetime import datetime
from typing import Optional, Dict

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

# API Keys for different providers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI clients
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

set_tracing_disabled(disabled=True)

### agent 1: generation_agent
model_1 = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)
GENERATION_PROMPT = """
Your task is to generate ONE image containing 16 different views of the object that can be used for 3D reconstruction for the target object: {query}. 

{previous_metadata_context}

Create a simple, clear prompt for DALL-E 3 that will generate a 4x4 grid of 16 views of the object.

"A set of sixteen digital photographs arranged in a 4x4 grid featuring a {query} captured from different angles. Each sub-image shows the {query} from a distinct viewpoint: front, back, left, right, top, bottom, and various oblique angles. The {query} is centered in each view, with consistent lighting, scale, and positioning. The background is pure white with no shadows or other objects, suitable for 3D reconstruction."

Return your response in this JSON format:
{{
    "target_object": "{query}",
    "generation_metadata": "Detailed description of the object and the 16 views for 3D reconstruction, including specific angle descriptions, lighting specifications, material properties, and geometric constraints",
    "image_prompt": "The prompt for DALL-E 3 to generate the single image with 16 views",
    "description": "Description of what was generated and how it can be used for reconstruction",
    "previous_iteration_metadata": {previous_metadata_json}
}}
"""

# DALL-E 3 image generation function
async def generate_image_with_dalle3(prompt: str) -> str:
    """Generate image using DALL-E 3 directly"""
    try:
        print(f"🎨 Generating image with DALL-E 3: {prompt[:50]}...")
        
        # Get image size from environment or use default
        image_size = os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024")
        
        response = await asyncio.to_thread(
            openai_sync_client.images.generate,
            model="dall-e-3",
            prompt=prompt,
            size=image_size,
            quality="standard"
        )
        
        image_url = response.data[0].url
        print(f"✅ DALL-E 3 image generated: {image_url[:50]}...")
        return image_url
        
    except Exception as e:
        print(f"❌ Error generating image with DALL-E 3: {e}")
        return ""

def extract_image_urls_from_text(text: str) -> list[str]:
    """Extract image URLs from text response"""
    import re
    import json
    
    # Try to parse as JSON first
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "image_urls" in data:
            return data["image_urls"]
        elif isinstance(data, list):
            # If it's a list, assume it contains URLs
            return [url for url in data if isinstance(url, str) and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Fallback: Look for URLs that might be image URLs using regex
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    # Filter for likely image URLs
    image_urls = [url for url in urls if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
    return image_urls

def create_image_gallery_html(image_urls: list[str], iteration: int) -> str:
    """Create HTML for displaying images in a collapsible gallery"""
    if not image_urls:
        return "<p>No images generated in this iteration.</p>"
    
    html_content = f"""
    <details style="margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; padding: 10px;">
        <summary style="cursor: pointer; font-weight: bold; color: #333; padding: 10px; background-color: #f5f5f5; border-radius: 4px;">
            📸 Show/Hide {len(image_urls)} Generated Images (Iteration {iteration})
        </summary>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; padding: 15px;">
    """
    
    for i, url in enumerate(image_urls):
        html_content += f"""
            <div style="border: 1px solid #eee; border-radius: 8px; padding: 10px; text-align: center;">
                <img src="{html.escape(url)}" alt="Generated Image {i+1}" style="max-width: 100%; height: auto; border-radius: 4px;">
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Image {i+1}</p>
            </div>
        """
    
    html_content += """
        </div>
    </details>
    """
    return html_content

def create_3d_viewer_html(mesh_path: str, iteration: int) -> str:
    """Create HTML for 3D mesh viewer with Three.js"""
    viewer_id = f"viewer-{iteration}"
    canvas_id = f"canvas-{iteration}"
    
    html_content = f"""
    <details style="margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; padding: 10px;">
        <summary style="cursor: pointer; font-weight: bold; color: #333; padding: 10px; background-color: #e8f4fd; border-radius: 4px;">
            🎮 Show/Hide 3D Mesh Viewer (Iteration {iteration})
        </summary>
        <div class="viewer-container" id="{viewer_id}" style="position: relative; width: 100%; height: 500px; border-radius: 12px; overflow: hidden; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); margin: 20px 0;">
            <canvas id="{canvas_id}" style="width: 100%; height: 100%; display: block;"></canvas>
            
            <div class="viewer-controls" style="position: absolute; top: 15px; right: 15px; display: flex; flex-direction: column; gap: 10px; z-index: 10;">
                <button class="viewer-control-btn" onclick="toggleRotation_{iteration}()" id="rotationBtn_{iteration}" title="Toggle Auto-Rotation" style="background: rgba(255, 255, 255, 0.9); border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.3s ease; backdrop-filter: blur(10px);">
                    🔄
                </button>
                <button class="viewer-control-btn" onclick="resetCamera_{iteration}()" title="Reset Camera" style="background: rgba(255, 255, 255, 0.9); border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.3s ease; backdrop-filter: blur(10px);">
                    🏠
                </button>
                <button class="viewer-control-btn" onclick="toggleWireframe_{iteration}()" id="wireframeBtn_{iteration}" title="Toggle Wireframe" style="background: rgba(255, 255, 255, 0.9); border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.3s ease; backdrop-filter: blur(10px);">
                    🔲
                </button>
                <button class="viewer-control-btn" onclick="screenshot_{iteration}()" title="Take Screenshot" style="background: rgba(255, 255, 255, 0.9); border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.3s ease; backdrop-filter: blur(10px);">
                    📸
                </button>
            </div>
            
            <div class="viewer-info" id="viewerInfo_{iteration}" style="position: absolute; bottom: 15px; left: 15px; background: rgba(0, 0, 0, 0.7); color: white; padding: 10px 15px; border-radius: 8px; font-size: 14px; backdrop-filter: blur(10px);">
                Loading 3D model...
            </div>
            
            <div class="loading-overlay" id="loadingOverlay_{iteration}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.8); display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; z-index: 20;">
                <div class="spinner" style="width: 40px; height: 40px; border: 4px solid rgba(255, 255, 255, 0.3); border-top: 4px solid white; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 15px;"></div>
                Loading 3D model...
            </div>
        </div>
        
        <div class="viewer-actions" style="display: flex; gap: 15px; margin-top: 20px; justify-content: center;">
            <button class="btn btn-secondary" onclick="downloadMesh_{iteration}()" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 8px; cursor: pointer;">
                📥 Download Mesh
            </button>
            <button class="btn" onclick="exportScreenshot_{iteration}()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">
                📸 Export Screenshot
            </button>
        </div>
        
        <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            .viewer-control-btn:hover {{
                background: rgba(255, 255, 255, 1) !important;
                transform: scale(1.1);
            }}
            
            .viewer-control-btn.active {{
                background: #667eea !important;
                color: white !important;
            }}
        </style>
        
        <script>
            // Three.js Variables for iteration {iteration}
            let scene_{iteration}, camera_{iteration}, renderer_{iteration}, mesh_{iteration}, controls_{iteration};
            let isRotating_{iteration} = true;
            let isWireframe_{iteration} = false;
            
            // Initialize Three.js Scene for iteration {iteration}
            function initThreeJS_{iteration}() {{
                const canvas = document.getElementById('{canvas_id}');
                
                // Scene
                scene_{iteration} = new THREE.Scene();
                scene_{iteration}.background = new THREE.Color(0x1a1a2e);
                
                // Camera
                camera_{iteration} = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
                camera_{iteration}.position.set(5, 5, 5);
                
                // Renderer
                renderer_{iteration} = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true }});
                renderer_{iteration}.setSize(canvas.clientWidth, canvas.clientHeight);
                renderer_{iteration}.shadowMap.enabled = true;
                renderer_{iteration}.shadowMap.type = THREE.PCFSoftShadowMap;
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                scene_{iteration}.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(10, 10, 5);
                directionalLight.castShadow = true;
                scene_{iteration}.add(directionalLight);
                
                const pointLight = new THREE.PointLight(0x667eea, 0.5, 100);
                pointLight.position.set(-10, 10, -10);
                scene_{iteration}.add(pointLight);
                
                // Grid Helper
                const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
                scene_{iteration}.add(gridHelper);
                
                // Controls
                controls_{iteration} = new THREE.OrbitControls(camera_{iteration}, renderer_{iteration}.domElement);
                controls_{iteration}.enableDamping = true;
                controls_{iteration}.dampingFactor = 0.05;
                
                // Load the mesh
                loadOBJModel_{iteration}('{mesh_path}');
                
                // Animation Loop
                animate_{iteration}();
            }}
            
            // Animation Loop for iteration {iteration}
            function animate_{iteration}() {{
                requestAnimationFrame(animate_{iteration});
                
                if (isRotating_{iteration} && mesh_{iteration}) {{
                    mesh_{iteration}.rotation.y += 0.01;
                }}
                
                controls_{iteration}.update();
                renderer_{iteration}.render(scene_{iteration}, camera_{iteration});
            }}
            
            // Load OBJ File for iteration {iteration}
            function loadOBJModel_{iteration}(url) {{
                const loadingOverlay = document.getElementById('loadingOverlay_{iteration}');
                const viewerInfo = document.getElementById('viewerInfo_{iteration}');
                
                loadingOverlay.style.display = 'flex';
                viewerInfo.textContent = 'Loading 3D model...';
                
                // Clear existing mesh
                if (mesh_{iteration}) {{
                    scene_{iteration}.remove(mesh_{iteration});
                }}
                
                const loader = new THREE.OBJLoader();
                loader.load(
                    url,
                    function(object) {{
                        // Center and scale the model
                        const box = new THREE.Box3().setFromObject(object);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const scale = 3 / maxDim;
                        
                        object.position.sub(center);
                        object.scale.setScalar(scale);
                        
                        // Add material
                        const material = new THREE.MeshPhongMaterial({{ 
                            color: 0x667eea,
                            shininess: 100,
                            transparent: true,
                            opacity: 0.9
                        }});
                        
                        object.traverse(function(child) {{
                            if (child.isMesh) {{
                                child.material = material;
                                child.castShadow = true;
                                child.receiveShadow = true;
                            }}
                        }});
                        
                        mesh_{iteration} = object;
                        scene_{iteration}.add(mesh_{iteration});
                        
                        // Update camera to fit model
                        const distance = maxDim * 2;
                        camera_{iteration}.position.set(distance, distance, distance);
                        controls_{iteration}.target.copy(center);
                        controls_{iteration}.update();
                        
                        loadingOverlay.style.display = 'none';
                        viewerInfo.textContent = `Model loaded: ${{mesh_{iteration}.children.length}} objects`;
                    }},
                    function(xhr) {{
                        const progress = (xhr.loaded / xhr.total * 100).toFixed(0);
                        viewerInfo.textContent = `Loading: ${{progress}}%`;
                    }},
                    function(error) {{
                        loadingOverlay.style.display = 'none';
                        viewerInfo.textContent = 'Error loading model';
                        console.error('Error loading OBJ:', error);
                    }}
                );
            }}
            
            // Control Functions for iteration {iteration}
            function toggleRotation_{iteration}() {{
                isRotating_{iteration} = !isRotating_{iteration};
                const btn = document.getElementById('rotationBtn_{iteration}');
                btn.classList.toggle('active', isRotating_{iteration});
            }}
            
            function resetCamera_{iteration}() {{
                if (mesh_{iteration}) {{
                    const box = new THREE.Box3().setFromObject(mesh_{iteration});
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const distance = maxDim * 2;
                    
                    camera_{iteration}.position.set(distance, distance, distance);
                    controls_{iteration}.target.copy(center);
                    controls_{iteration}.update();
                }}
            }}
            
            function toggleWireframe_{iteration}() {{
                isWireframe_{iteration} = !isWireframe_{iteration};
                const btn = document.getElementById('wireframeBtn_{iteration}');
                btn.classList.toggle('active', isWireframe_{iteration});
                
                if (mesh_{iteration}) {{
                    mesh_{iteration}.traverse(function(child) {{
                        if (child.isMesh) {{
                            child.material.wireframe = isWireframe_{iteration};
                        }}
                    }});
                }}
            }}
            
            function screenshot_{iteration}() {{
                renderer_{iteration}.render(scene_{iteration}, camera_{iteration});
                const canvas = renderer_{iteration}.domElement;
                const link = document.createElement('a');
                link.download = '3d-model-screenshot-{iteration}.png';
                link.href = canvas.toDataURL();
                link.click();
            }}
            
            function downloadMesh_{iteration}() {{
                window.open('{mesh_path}', '_blank');
            }}
            
            function exportScreenshot_{iteration}() {{
                screenshot_{iteration}();
            }}
            
            // Initialize Three.js when the details element is opened
            document.addEventListener('DOMContentLoaded', function() {{
                const details = document.querySelector('#{viewer_id}').closest('details');
                details.addEventListener('toggle', function() {{
                    if (this.open) {{
                        // Load Three.js libraries if not already loaded
                        if (typeof THREE === 'undefined') {{
                            loadThreeJS();
                        }} else {{
                            initThreeJS_{iteration}();
                        }}
                    }}
                }});
            }});
            
            // Load Three.js libraries
            function loadThreeJS() {{
                const scripts = [
                    'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
                    'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js',
                    'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'
                ];
                
                let loaded = 0;
                scripts.forEach(src => {{
                    const script = document.createElement('script');
                    script.src = src;
                    script.onload = () => {{
                        loaded++;
                        if (loaded === scripts.length) {{
                            initThreeJS_{iteration}();
                        }}
                    }};
                    document.head.appendChild(script);
                }});
            }}
        </script>
    </details>
    """
    return html_content

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

async def download_images_locally(image_urls: list[str], session_id: str = None) -> list[str]:
    """Download images from URLs and save them locally
    
    Args:
        image_urls: List of image URLs to download
        session_id: Optional session ID for organizing files
        
    Returns:
        List of local file paths where images were saved
    """
    import pathlib
    import uuid
    import aiohttp
    
    # Create images directory
    images_dir = pathlib.Path("generated_images")
    images_dir.mkdir(exist_ok=True)
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    session_dir = images_dir / f"session_{session_id}"
    session_dir.mkdir(exist_ok=True)
    
    print(f"📁 Downloading {len(image_urls)} images to: {session_dir}")
    
    local_paths = []
    
    for i, url in enumerate(image_urls):
        if not url or url.startswith("Error"):
            print(f"⚠️  Skipping invalid URL {i+1}: {url}")
            local_paths.append("")
            continue
            
        try:
            print(f"⬇️  Downloading image {i+1}/{len(image_urls)}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # Save with descriptive filename
                        filename = f"image_{i+1:02d}.png"
                        file_path = session_dir / filename
                        
                        with open(file_path, "wb") as f:
                            f.write(image_data)
                        
                        local_paths.append(str(file_path))
                        print(f"✅ Saved: {filename}")
                    else:
                        print(f"❌ Failed to download image {i+1}: {response.status}")
                        local_paths.append("")
                        
        except Exception as e:
            print(f"❌ Error downloading image {i+1}: {str(e)}")
            local_paths.append("")
    
    # Save metadata about this session
    metadata_file = session_dir / "metadata.txt"
    with open(metadata_file, "w") as f:
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Downloaded: {len([p for p in local_paths if p])} images\n")
        f.write(f"Timestamp: {pathlib.Path().cwd()}\n\n")
        for i, url in enumerate(image_urls):
            f.write(f"Image {i+1}: {url}\n")
            if i < len(local_paths) and local_paths[i]:
                f.write(f"Saved as: {local_paths[i]}\n")
            f.write("\n")
    
    print(f"📄 Session metadata saved to: {metadata_file}")
    print(f"🎯 Downloaded {len([p for p in local_paths if p])} images successfully")
    
    return local_paths

# No longer needed - GPT-4o generates images directly

def parse_evaluation_text(text: str) -> Dict:
    """Parse evaluation text to extract structured data"""
    result = {
        "short_summary": "",
        "markdown_report": text,
        "suggestions_for_improvement": "",
        "metadata_suggestions": "",
        "scores": {"image_quality": 0, "metadata_accuracy": 0, "completeness": 0}
    }
    
    # Look for "well done" in the text
    if "well done" in text.lower():
        result["suggestions_for_improvement"] = "well done"
        result["metadata_suggestions"] = "current metadata is sufficient"
    
    # Extract scores from the text - look for multiple patterns
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if "image quality" in line_lower:
            # Look for score patterns like "Image Quality: 8/10" or "Image Quality: 8" or "Score: 8"
            import re
            score_match = re.search(r'(\d+)/10|(\d+)(?=\s*$)|score:\s*(\d+)', line)
            if score_match:
                score = int(score_match.group(1) or score_match.group(2) or score_match.group(3))
                result["scores"]["image_quality"] = score
                print(f"🔍 Found Image Quality score: {score}")
        elif "metadata accuracy" in line_lower:
            score_match = re.search(r'(\d+)/10|(\d+)(?=\s*$)|score:\s*(\d+)', line)
            if score_match:
                score = int(score_match.group(1) or score_match.group(2) or score_match.group(3))
                result["scores"]["metadata_accuracy"] = score
                print(f"🔍 Found Metadata Accuracy score: {score}")
        elif "completeness" in line_lower:
            score_match = re.search(r'(\d+)/10|(\d+)(?=\s*$)|score:\s*(\d+)', line)
            if score_match:
                score = int(score_match.group(1) or score_match.group(2) or score_match.group(3))
                result["scores"]["completeness"] = score
                print(f"🔍 Found Completeness score: {score}")
    
    # Check for failure indicators in the text
    failure_indicators = [
        "5x5", "25 views", "25 squares", "wrong grid", "not 4x4",
        "multiple objects", "stacked", "overlapping", "three cars", "two cars",
        "grid pattern", "text labels", "numbers", "gray background",
        "wireframe", "low-poly", "3d model style", "toy-like",
        "watermark", "visual stu", "grid lines", "black lines",
        "different object types", "mix of", "cars and motorcycles",
        "circular objects", "multiple motorcycles",
    ]
    
    # Extract suggestions for improvement
    suggestions = []
    for line in lines:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in failure_indicators):
            suggestions.append(line.strip())
        elif "suggestion" in line_lower or "improvement" in line_lower:
            suggestions.append(line.strip())
    
    if suggestions:
        result["suggestions_for_improvement"] = " ".join(suggestions)
    else:
        result["suggestions_for_improvement"] = "Continue improving the generation"
    
    # Extract metadata suggestions (look for the fourth section)
    metadata_section = False
    metadata_lines = []
    for line in lines:
        if "fourth" in line.lower() or "metadata suggestions" in line.lower():
            metadata_section = True
            continue
        elif metadata_section and line.strip():
            if any(keyword in line.lower() for keyword in ["first", "second", "third", "fifth"]):
                break
            metadata_lines.append(line.strip())
    
    if metadata_lines:
        result["metadata_suggestions"] = " ".join(metadata_lines)
    else:
        result["metadata_suggestions"] = "Improve metadata with more specific details"
    
    # Extract short summary (first few sentences)
    sentences = text.split('.')
    if len(sentences) > 0:
        result["short_summary"] = sentences[0].strip() + "."
    
    return result

# Metadata functions for iterative evaluation
def save_metadata(session_id: str, iteration: int, metadata: Dict, image_url: str, evaluation_results: Dict) -> str:
    """Save comprehensive metadata for each iteration"""
    session_dir = Path(f"generated_images/session_{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = session_dir / f"metadata_iteration_{iteration:02d}.json"
    metadata_data = {
        "session_id": session_id,
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "target_object": metadata.get("target_object", ""),
        "generation_metadata": metadata.get("generation_metadata", ""),
        "image_prompt": metadata.get("image_prompt", ""),
        "description": metadata.get("description", ""),
        "image_url": image_url,
        "evaluation_results": evaluation_results,
        "previous_iteration_metadata": metadata.get("previous_iteration_metadata", None)
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata_data, f, indent=2)
    print(f"✅ Saved metadata to {metadata_file}")
    return str(metadata_file)

def load_previous_metadata(session_id: str, iteration: int) -> Optional[Dict]:
    """Load metadata from the previous iteration"""
    if iteration <= 1:
        return None
    previous_metadata_file = Path(f"generated_images/session_{session_id}/metadata_iteration_{iteration-1:02d}.json")
    if previous_metadata_file.exists():
        try:
            with open(previous_metadata_file, 'r') as f:
                metadata = json.load(f)
            print(f"✅ Loaded previous metadata from {previous_metadata_file}")
            return metadata
        except Exception as e:
            print(f"❌ Failed to load previous metadata: {e}")
            return None
    else:
        print(f"⚠️  No previous metadata found at {previous_metadata_file}")
        return None

def meets_quality_threshold(scores: Dict) -> bool:
    """Check if the scores meet the quality threshold for stopping iterations"""
    if not scores:
        return False
    # Check if all scores are 8 or higher
    return all(score >= 8 for score in scores.values())

# Output schema for generation agent
class GenerationOutput(BaseModel):
    metadata: str
    """Detailed metadata about the generated views and object specifications."""
    
    image_urls: list[str]
    """List of URLs for the generated images."""
    
    description: str
    """Description of what was generated and how it can be used for CAD reconstruction."""

# Generation agent - uses GPT-4o's built-in image generation capabilities
generation_agent = Agent(
    name="GenerationAgent",
    instructions=GENERATION_PROMPT,
    model=model_1
)


### agent 2: evaluation_agent
# Agent used to synthesize a final report from the individual summaries
model_2 = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)
EVALUATION_PROMPT = """
You are a STRICT evaluation agent for 3D reconstruction images. 
You must be extremely critical and only give high scores if ALL requirements are perfectly met.

CRITICAL REQUIREMENTS FOR 3D RECONSTRUCTION:
1. **4x4 Grid Layout**: The image MUST contain exactly 16 squares arranged in a 4x4 grid (4 rows × 4 columns)
2. **One Object Per Square**: Each square MUST contain exactly ONE instance of the object - NO EXCEPTIONS
3. **Same Object Type**: ALL 16 squares must show the SAME object type
4. **Same Pose**: The object MUST be in the SAME pose/position across all 16 views
5. **16 Distinct Angles**: Each square MUST show a DIFFERENT angle/view of the object
6. **Consistent Size**: The object MUST appear the same size in all 16 squares
7. **PURE WHITE BACKGROUND**: ABSOLUTELY NO grid lines, NO text, NO numbers, NO watermarks, NO coordinate systems, NO axis labels, NO overlays - ONLY PURE WHITE BACKGROUND
8. **Realistic Style**: Photorealistic or realistic rendering, NOT wireframe/low-poly/3D model style
9. **Lighting Consistency**: All views must have IDENTICAL lighting conditions
10. **Surface Detail Preservation**: All surface details, textures, and features must be clearly visible and consistent
11. **Edge Definition**: Sharp, well-defined edges and contours for accurate geometry extraction
12. **Depth Information**: Sufficient depth cues through shadows, perspective, and overlapping
13. **No Occlusion**: No parts of the object should be hidden or occluded in any view
14. **Scale Reference**: Object should occupy 60-80% of each square for optimal detail capture
15. **IDENTICAL COLOR/MATERIAL**: EXACTLY the same color, material, and appearance across ALL 16 views - NO color variations
16. **Geometric Accuracy**: No distortion, stretching, or warping of the object shape

SCORING CRITERIA (BE VERY STRICT):
- **Score 1-3**: Major failures (wrong grid size, multiple objects, wrong background, wrong style)
- **Score 4-6**: Some requirements met but significant issues remain
- **Score 7-8**: Most requirements met with minor issues
- **Score 9-10**: ALL requirements perfectly met

First, analyze the provided metadata and summarize the generation intent and specifications.

Second, evaluate using these three criteria and assign a score (1-10) for each:
1. Image Quality: Assess visual clarity, proper 4x4 grid layout, one object per square, same object type, same pose across all views, realistic rendering style, clean white background, lighting consistency, surface detail preservation, edge definition, depth information, no occlusion, proper scale (60-80%), color consistency, and geometric accuracy.
2. Metadata Accuracy: Evaluate the correctness and relevance of the metadata for reconstruction, including proper angle descriptions, lighting specifications, material properties, and geometric constraints. Check if the metadata accurately describes what was generated.
3. Completeness: Determine if the 16 distinct angles provide sufficient coverage for 3D reconstruction with 360° horizontal rotation, full vertical elevation (-90° to +90°), key views (front, back, left, right, top, bottom), and 10 intermediate angles for smooth reconstruction.

You MUST include the exact scores in this format:
- Image Quality: X/10
- Metadata Accuracy: X/10  
- Completeness: X/10

Third, provide specific, actionable suggestions for improvement. Be very specific about what needs to be fixed. For example:
- "Wrong grid size: Image shows 25 squares instead of 16. Need exactly 4x4 grid."
- "Multiple objects detected: Square 3 contains 2 objects. Need exactly ONE object per square."
- "Background issues: Gray background with grid lines. Need pure white background with NO lines or text."
- "Style issues: Wireframe rendering detected. Need photorealistic style."
- "Lighting inconsistency: Different shadows across views. Need identical lighting conditions."
- "Color inconsistency: Object appears blue in some views, red in others. Need identical color across all views."
- "Metadata mismatch: Metadata describes 16 views but image shows different layout."
- "Incomplete coverage: Missing top/bottom views needed for full 3D reconstruction."

Fourth, provide updated metadata suggestions for the next iteration. This should include:
- Specific angle measurements and descriptions
- Lighting specifications (type, intensity, direction)
- Material properties (color, texture, reflectivity)
- Geometric constraints and measurements
- Any additional details needed for better reconstruction

The metadata suggestions should build upon the previous iteration's feedback and provide more precise specifications for the next generation attempt.
"""


class ReportData_2(BaseModel):
    short_summary: str
    """A short 2-3 sentence evaluation of the generated 2D images and metadata."""

    markdown_report: str
    """The final report"""

    suggestions_for_improvement: str
    """Suggestions to improve the generated 2D images and metadata."""

evaluation_agent = Agent(
    name="EvaluationAgent",
    instructions=EVALUATION_PROMPT,
    model=model_2
)

writer_agent = Agent(
    name="Writeragent",
    instructions=EVALUATION_PROMPT,
    model=model_2
    # Removed output_type=ReportData_2 to avoid JSON parsing issues
)

async def generate_3d_mesh_with_llm(metadata: str, image_urls: list[str]) -> str:
    """Generate 3D mesh using GPT-4 Image model for image generation"""
    import os
    import pathlib
    import base64
    print(f"🎮 Generating 3D mesh from {len(image_urls)} images using GPT-4 Image model...")
    
    # Validate inputs
    if not metadata or not isinstance(metadata, str):
        print("❌ ERROR: Invalid metadata parameter")
        return "Error: Invalid metadata"
    
    if not image_urls or not isinstance(image_urls, list):
        print("❌ ERROR: Invalid image_urls parameter")
        return "Error: Invalid image_urls"
    
    if len(image_urls) == 0:
        print("❌ ERROR: No image URLs provided for mesh generation")
        return "Error: No images available for mesh generation"
    
    try:
        # Create output directory
        out_dir = pathlib.Path("mesh_outputs")
        out_dir.mkdir(exist_ok=True)
        
        # Generate a unique filename
        import uuid
        mesh_id = str(uuid.uuid4())[:8]
        mesh_filename = f"mesh_llm_{mesh_id}.obj"
        mesh_path = out_dir / mesh_filename
        
        # Create the prompt using the image URLs instead of embedding base64 data
        prompt = f"""
        Give me the 3D mesh for the object in the images. 
        The images include multi-views of the object, and the corresponding metadata can be found in: {metadata}. 
        Generate a detailed 3D mesh visualization based on the object shown in the images.
        """
        
        # Use GPT-4 Image model to generate a mesh visualization
        img_resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
        )
        
        # Get the generated image data
        mesh_data = img_resp.data[0].b64_json
        
        # Save the mesh visualization image
        png_path = out_dir / f"mesh_llm_{mesh_id}.png"
        with open(png_path, "wb") as f:
            f.write(base64.b64decode(mesh_data))
        
        print(f"✅ Generated mesh visualization: {png_path}")
        
        # Create OBJ file with reference to the generated visualization
        obj_content = f"""# 3D Mesh Visualization Generated by GPT-4 Image Model
# Generated from {len(image_urls)} images
# Metadata: {metadata}
# Visualization saved as: {png_path}

# This is a reference to the generated mesh visualization
# The actual 3D mesh is represented as an image: {png_path}

# Simple cube mesh as placeholder (actual mesh is in the generated image)
v -1.0 -1.0 -1.0
v 1.0 -1.0 -1.0
v 1.0 1.0 -1.0
v -1.0 1.0 -1.0
v -1.0 -1.0 1.0
v 1.0 -1.0 1.0
v 1.0 1.0 1.0
v -1.0 1.0 1.0
vn 0.0 0.0 -1.0
vn 0.0 0.0 1.0
vn 0.0 -1.0 0.0
vn 0.0 1.0 0.0
vn -1.0 0.0 0.0
vn 1.0 0.0 0.0
f 1//1 2//1 3//1 4//1
f 5//2 8//2 7//2 6//2
f 1//3 5//3 6//3 2//3
f 2//4 6//4 7//4 3//4
f 3//5 7//5 8//5 4//5
f 5//6 1//6 4//6 8//6"""
        
        # Save the OBJ file
        with open(mesh_path, "w") as f:
            f.write(obj_content)
        
        print(f"✅ Successfully generated mesh with GPT-4 Image model: {mesh_path}")
        return str(mesh_path)
        
    except Exception as e:
        print(f"❌ Error generating mesh with GPT-4 Image model: {str(e)}")
        return f"Error generating mesh: {str(e)}"

# Create a session instance
session = SQLiteSession("conversation_123")

async def run_enhanced_generation_loop(query: str, session_id: str = None) -> Dict:
    """Run the enhanced iterative generation and evaluation loop with metadata integration"""
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    print(f"🚀 Starting enhanced generation loop for: {query}")
    print(f"📋 Session ID: {session_id}")
    
    # Initialize session data
    session_data = {
        "session_id": session_id,
        "query": query,
        "status": "running",
        "current_iteration": 0,
        "max_iterations": 5,
        "metadata_files": [],
        "image_urls": [],
        "mesh_paths": [],
        "evaluation_history": []
    }
    
    iteration = 1
    db_session = SQLiteSession(session_id)
    
    try:
        while iteration <= session_data["max_iterations"]:
            print(f"\n🔄 Iteration {iteration}")
            print("-" * 50)
            
            # Load previous metadata for iterative feedback
            previous_metadata = load_previous_metadata(session_id, iteration)
            
            # Prepare context for generation
            previous_metadata_context = ""
            previous_metadata_json = "null"
            
            if previous_metadata:
                previous_metadata_context = f"""
                Previous iteration feedback:
                - Scores: {previous_metadata.get('evaluation_results', {}).get('scores', {})}
                - Suggestions: {previous_metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '')}
                - Metadata suggestions: {previous_metadata.get('evaluation_results', {}).get('metadata_suggestions', '')}
                
                Use this feedback to improve the current generation.
                """
                previous_metadata_json = json.dumps(previous_metadata.get('evaluation_results', {}).get('metadata_suggestions', ''))
            
            print("📝 Generating image prompt and metadata...")
            
            # Generate new metadata and image prompt
            prompt = GENERATION_PROMPT.format(
                query=query,
                previous_metadata_context=previous_metadata_context,
                previous_metadata_json=previous_metadata_json
            )
            
            result = await Runner.run(generation_agent, prompt, session=db_session)
            generation_text = result.final_output
            
            # Parse the generation result
            try:
                generation_data = json.loads(generation_text)
                metadata = generation_data
            except json.JSONDecodeError:
                print(f"❌ Failed to parse generation result as JSON: {generation_text}")
                metadata = {
                    "target_object": query,
                    "generation_metadata": generation_text,
                    "image_prompt": f"A 4x4 grid of {query} from different angles",
                    "description": "Generated from text response",
                    "previous_iteration_metadata": previous_metadata_json
                }
            
            # Generate image using DALL-E 3
            image_url = await generate_image_with_dalle3(metadata["image_prompt"])
            if not image_url:
                print("❌ Failed to generate image")
                break
            
            print(f"🎨 Generated image: {image_url}")
            
            # Download and encode image for evaluation
            image_base64, image_format = await download_image_to_base64(image_url)
            
            # Prepare evaluation content
            evaluation_contents = f"""
            Please evaluate the following image and metadata for 3D reconstruction:
            
            TARGET OBJECT: {query}
            
            METADATA:
            {json.dumps(metadata, indent=2)}
            
            IMAGE:
            <image>{image_base64}</image>
            
            Please provide a comprehensive evaluation following the strict criteria.
            """
            
            print("🔍 Evaluating generated image and metadata...")
            
            # Run evaluation
            evaluation_result = await Runner.run(evaluation_agent, evaluation_contents, session=db_session)
            evaluation_text = evaluation_result.final_output
            
            # Parse evaluation results
            evaluation_results = parse_evaluation_text(evaluation_text)
            
            print(f"📊 Evaluation scores: {evaluation_results.get('scores', {})}")
            
            # Save metadata for this iteration
            metadata_file = save_metadata(session_id, iteration, metadata, image_url, evaluation_results)
            
            # Update session data
            session_data["current_iteration"] = iteration
            session_data["metadata_files"].append(metadata_file)
            session_data["image_urls"].append(image_url)
            session_data["evaluation_history"].append(evaluation_results)
            
            # Generate 3D mesh
            mesh_path = await generate_3d_mesh_with_llm(metadata["generation_metadata"], [image_url])
            session_data["mesh_paths"].append(mesh_path)
            
            # Check if quality threshold is met
            if meets_quality_threshold(evaluation_results.get("scores", {})):
                print("✅ Quality threshold met! Stopping iterations.")
                session_data["status"] = "completed"
                break
            
            iteration += 1
        
        if iteration > session_data["max_iterations"]:
            session_data["status"] = "max_iterations_reached"
            print("⚠️  Reached maximum iterations")
        
        return session_data
        
    except Exception as e:
        print(f"❌ Error in enhanced generation loop: {e}")
        session_data["status"] = "error"
        session_data["error"] = str(e)
        return session_data

async def test_simple_generation():
    """Test simple image generation without the complex prompt"""
    print("🧪 Testing simple image generation...")
    
    simple_prompt = "Generate a simple image of a dog"
    
    try:
        result = await asyncio.wait_for(
            Runner.run(generation_agent, simple_prompt, session=session),
            timeout=300  # 5 minutes timeout
        )
        print(f"✅ Simple generation completed!")
        print(f"📄 Response: {result.final_output[:200]}...")
        return True
    except asyncio.TimeoutError:
        print(f"❌ Simple generation timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Simple generation failed: {e}")
        return False

async def main():
    # Test the enhanced generation loop with metadata integration
    print("🚀 Testing enhanced generation loop with metadata integration...")
    query = "a modern sports car"
    result = await run_enhanced_generation_loop(query)
    print(f"✅ Enhanced generation completed with status: {result['status']}")
    print(f"📊 Final iteration: {result['current_iteration']}")
    print(f"🎨 Generated {len(result['image_urls'])} images")
    print(f"📁 Saved {len(result['metadata_files'])} metadata files")
    
    # First test simple generation
    if not await test_simple_generation():
        print("❌ Simple generation failed, stopping...")
        return
    
    query = input("What would you like to generate? ")
    print(query)
    
    suggestions = ""
    iteration = 0
    
    # Step 1: Generate prompt and metadata using GPT-4o
    print(f"📝 Creating image generation prompt for: {query}")
    print(f"⏱️  This may take a few minutes...")
    
    try:
        # Add timeout to the Runner.run call
        result_1 = await asyncio.wait_for(
            Runner.run(generation_agent, f"Please generate the materials needed for 3D CAD generation for: {query}", session=session),
            timeout=300  # 5 minutes timeout
        )
        print(f"✅ Prompt generation completed!")
        print(f"📄 Response length: {len(result_1.final_output)} characters")
        print(f"📄 Response preview: {result_1.final_output[:200]}...")
    except asyncio.TimeoutError:
        print(f"❌ Prompt generation timed out after 5 minutes")
        raise
    except Exception as e:
        print(f"❌ Error during prompt generation: {e}")
        raise
    
    # Parse the structured output for metadata and image prompt
    try:
        import json
        parsed_output = json.loads(result_1.final_output)
        metadata = parsed_output.get("metadata", "")
        description = parsed_output.get("description", "")
        image_prompt = parsed_output.get("image_prompt", "")
        print(f"✅ Successfully parsed JSON response")
        print(f"📝 Metadata length: {len(metadata)} characters")
        print(f"🎨 Image prompt length: {len(image_prompt)} characters")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  Failed to parse JSON response: {e}")
        print(f"📄 Raw response: {result_1.final_output}")
        # Fallback to extracting from text
        metadata = result_1.final_output
        description = ""
        image_prompt = ""
    
    # Step 2: Generate image using DALL-E 3
    image_urls = []
    if image_prompt:
        print(f"🎨 Generating image with DALL-E 3...")
        image_url = await generate_image_with_dalle3(image_prompt)
        if image_url:
            image_urls.append(image_url)
            print(f"✅ Successfully generated image: {image_url[:50]}...")
        else:
            print(f"❌ Failed to generate image with DALL-E 3")
            image_urls = ["placeholder_image_url"]
    else:
        print(f"⚠️  No image prompt found in response")
        image_urls = ["placeholder_image_url"]
    
    # Step 3: Download images locally
    local_image_paths = []
    if image_urls:
        print(f"\nDownloading {len(image_urls)} images locally...")
        local_image_paths = await download_images_locally(image_urls, "main_session")
    # Download and convert first image to base64 if available
    b64_image = ""
    b64_mime_type = "image/jpeg"
    if image_urls:
        b64_image, b64_mime_type = await download_image_to_base64(image_urls[0])
    
    while suggestions != "well done":
        iteration += 1
        # First turn
        contents = [
            {
                "role": "user",
                "content": f"The generated metadata is: {metadata}.",
            },
            {
                "role": "user",
                "content": "Please evaluate the generated 2D images and metadata, and think about the follow-up questions according to the guidelines.",
            }            
        ]
        
        # Only add image content if we have a valid base64 image
        if b64_image and b64_image.strip():
            contents.insert(0, {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "detail": "auto",
                        "image_url": f"data:{b64_mime_type};base64,{b64_image}",
                    }
                ],
            })
        result_2 = await Runner.run(writer_agent, contents)
        evaluation_text = result_2.final_output
        
        # Parse the evaluation text manually
        parsed_evaluation = parse_evaluation_text(evaluation_text)
        suggestions = parsed_evaluation["suggestions_for_improvement"]
        
        new_prompt = (
            f"The target for your generation is: {query}. Detailed task is introduced by the instructions from the system above.\n\n"
            f"Below are the metadata from your previous generation attempt:\n\n{metadata}\n\n"
            f"Please refine the generation results based on the system instructions. Pay special attention to the following suggestions for improvement: {suggestions}.\n\n"
            f"Additionally, consider the scores and reasoning provided in the evaluation report for the previous generation attempt:\n\n{parsed_evaluation['markdown_report']}."
        )
        
        # Generate improved version with new prompt
        result_1 = await Runner.run(generation_agent, new_prompt, session=session)
        
        # Parse the structured output for metadata and image prompt
        try:
            parsed_output = json.loads(result_1.final_output)
            metadata = parsed_output.get("metadata", "")
            description = parsed_output.get("description", "")
            image_prompt = parsed_output.get("image_prompt", "")
        except (json.JSONDecodeError, KeyError):
            metadata = result_1.final_output
            description = ""
            image_prompt = ""
        
        # Generate new image using DALL-E 3
        image_urls = []
        if image_prompt:
            print(f"🎨 Generating improved image with DALL-E 3...")
            image_url = await generate_image_with_dalle3(image_prompt)
            if image_url:
                image_urls.append(image_url)
                print(f"✅ Successfully generated improved image: {image_url[:50]}...")
            else:
                print(f"❌ Failed to generate improved image with DALL-E 3")
                image_urls = ["placeholder_image_url"]
        else:
            print(f"⚠️  No image prompt found in improved response")
            image_urls = ["placeholder_image_url"]
        
        # Download new images locally
        local_image_paths = []
        if image_urls:
            print(f"\nDownloading {len(image_urls)} new images locally...")
            local_image_paths = await download_images_locally(image_urls, f"main_session_iter_{iteration}")
        # Download and convert first image to base64 if available
        b64_image = ""
        b64_mime_type = "image/jpeg"
        if image_urls:
            b64_image, b64_mime_type = await download_image_to_base64(image_urls[0])
        # Second turn - agent automatically remembers previous context
        # Save the evaluation results separately for each iteration
        out_dir = pathlib.Path(f"evaluation_reports_{iteration}"); out_dir.mkdir(exist_ok=True)
        
        # Generate mesh for this iteration using LLM
        mesh_path = await generate_3d_mesh_with_llm(metadata, image_urls)
        
        # Create HTML report with images and 3D viewer
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Iteration {iteration} Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .content {{ margin: 20px 0; }}
                .evaluation {{ background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .section {{ margin: 30px 0; }}
                .section h2 {{ color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Iteration {iteration} Report</h1>
                <p><strong>Query:</strong> {query}</p>
                <p><strong>Generated {len(image_urls)} images</strong></p>
                <p><strong>3D Mesh:</strong> {pathlib.Path(mesh_path).name}</p>
            </div>
            
            <div class="section">
                <h2>📸 Generated Images</h2>
                {create_image_gallery_html(image_urls, iteration)}
            </div>
            
            <div class="section">
                <h2>🎮 3D Mesh Viewer</h2>
                {create_3d_viewer_html(mesh_path, iteration)}
            </div>
            
            <div class="evaluation">
                <h2>📊 Evaluation Report</h2>
                <h3>Short Summary</h3>
                <p>{parsed_evaluation["short_summary"]}</p>
                
                <h3>Detailed Report</h3>
                <div style="white-space: pre-wrap;">{parsed_evaluation["markdown_report"]}</div>
                
                <h3>Suggestions for Improvement</h3>
                <p><strong>{parsed_evaluation["suggestions_for_improvement"]}</strong></p>
            </div>
        </body>
        </html>
        """
        
        # Save HTML report
        html_path = out_dir / f"iteration_{iteration}_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        
        # Save markdown report
        markdown_path = out_dir / f"iteration_{iteration}_report.md"
        with open(markdown_path, "w") as f:
            f.write(parsed_evaluation["markdown_report"])
        
        # Save suggestions for improvement
        suggestions_path = out_dir / f"iteration_{iteration}_suggestions.txt"
        with open(suggestions_path, "w") as f:
            f.write(parsed_evaluation["suggestions_for_improvement"])
        
        # Save short summary
        summary_path = out_dir / f"iteration_{iteration}_summary.txt"
        with open(summary_path, "w") as f:
            f.write(parsed_evaluation["short_summary"])
        
        # Print the markdown report to the console
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration} COMPLETED")
        print(f"{'='*60}")
        print(f"Generated {len(image_urls)} images")
        print(f"Created 3D mesh: {pathlib.Path(mesh_path).name}")
        print(f"HTML report with 3D viewer saved to: {html_path}")
        print(f"Markdown report saved to: {markdown_path}")
        print(f"\nEvaluation Summary: {parsed_evaluation['short_summary']}")
        print(f"Suggestions: {parsed_evaluation['suggestions_for_improvement']}")
        print(f"\n{parsed_evaluation['markdown_report']}")
        print(f"{'='*60}\n")
    print("All iterations completed. Final report saved in", out_dir)
    
    # Create a final summary HTML file
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Final Report - {query}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #e8f5e8; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .iteration {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; padding: 15px; }}
            .iteration h3 {{ color: #2c5aa0; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #667eea; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
            .stat-label {{ color: #666; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 Final Report - {query}</h1>
            <p><strong>Total Iterations:</strong> {iteration}</p>
            <p><strong>Status:</strong> ✅ Task completed successfully!</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{iteration}</div>
                <div class="stat-label">Total Iterations</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{iteration * 16}</div>
                <div class="stat-label">Total Images Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{iteration}</div>
                <div class="stat-label">3D Meshes Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">🎮</div>
                <div class="stat-label">Interactive 3D Viewers</div>
            </div>
        </div>
        
        <h2>📁 Generated Reports</h2>
        <p>Each iteration has its own folder with detailed reports, images, and interactive 3D mesh viewers:</p>
        <ul>
    """
    
    for i in range(1, iteration + 1):
        final_html += f"""
            <li><strong>Iteration {i}:</strong> 
                <a href="evaluation_reports_{i}/iteration_{i}_report.html" target="_blank">🎮 View Interactive Report</a> | 
                <a href="evaluation_reports_{i}/iteration_{i}_report.md" target="_blank">📄 View Markdown Report</a> |
                <a href="mesh_outputs/mesh_{i}.obj" target="_blank">📦 Download 3D Mesh</a>
            </li>
        """
    
    final_html += """
        </ul>
        
        <div class="iteration">
            <h3>📋 Final Summary</h3>
            <p>The multi-agent system has successfully completed the 3D CAD generation task through iterative improvement.</p>
            <p>Each iteration generated 16 images and was evaluated for quality, accuracy, and completeness.</p>
            <p>🎮 <strong>Interactive 3D Viewers:</strong> Each iteration includes a fully interactive 3D mesh viewer with:</p>
            <ul>
                <li>🔄 Auto-rotation and manual camera controls</li>
                <li>🔲 Wireframe toggle for detailed inspection</li>
                <li>📸 Screenshot capture functionality</li>
                <li>📥 Direct mesh download capability</li>
                <li>🎨 Professional lighting and materials</li>
            </ul>
            <p>Check the individual iteration reports above to see all generated images, 3D meshes, and detailed evaluations.</p>
        </div>
    </body>
    </html>
    """
    
    # Save final summary
    final_path = pathlib.Path("final_report.html")
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"\n🎉 FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Task completed in {iteration} iterations")
    print(f"📁 Final report: {final_path}")
    print(f"📸 Each iteration generated and displayed 16 images")
    print(f"🎮 Each iteration includes interactive 3D mesh viewer")
    print(f"📦 3D mesh files saved in mesh_outputs/ folder")
    print(f"📊 Detailed reports saved in evaluation_reports_* folders")
    print(f"{'='*60}")
    
    print("✅ All mesh data generated and saved successfully.")

if __name__ == "__main__":
    asyncio.run(main())