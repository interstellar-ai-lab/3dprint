from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import pathlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import base64
from PIL import Image
import io
from openai import OpenAI, AsyncOpenAI
import tempfile
import os
import aiohttp

# Import your existing multi-agent functionality
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from multiagent import generation_agent, evaluation_agent, Runner, SQLiteSession, download_image_to_base64, generate_3d_mesh_with_llm

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="3D Generation Multi-Agent Web App", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

# OpenAI clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

# Metadata functions for iterative evaluation
def save_metadata(session_id: str, iteration: int, metadata: Dict, image_url: str, evaluation_results: Dict) -> str:
    """Save comprehensive metadata for each iteration"""
    session_dir = pathlib.Path(f"generated_images/session_{session_id}")
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
    previous_metadata_file = pathlib.Path(f"generated_images/session_{session_id}/metadata_iteration_{iteration-1:02d}.json")
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

class GenerationRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class GenerationResponse(BaseModel):
    session_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/generate", response_model=GenerationResponse)
async def start_generation(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start the 3D generation process"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Initialize session data
    active_sessions[session_id] = {
        "session_id": session_id,
        "query": request.query,
        "status": "starting",
        "current_iteration": 0,
        "max_iterations": 5,
        "metadata_files": [],
        "image_urls": [],
        "mesh_paths": [],
        "evaluation_history": [],
        "error": None
    }
    
    # Start background task
    background_tasks.add_task(run_generation_loop, session_id, request.query)
    
    return GenerationResponse(
        session_id=session_id,
        status="starting",
        message="Generation started successfully"
    )

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Get the current status of a generation session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": session_data["status"],
        "query": session_data["query"],
        "current_iteration": session_data["current_iteration"],
        "max_iterations": session_data["max_iterations"],
        "metadata_files": session_data["metadata_files"],
        "image_urls": session_data["image_urls"],
        "mesh_paths": session_data["mesh_paths"],
        "evaluation_history": session_data["evaluation_history"],
        "error": session_data.get("error")
    }

@app.get("/api/metadata/{session_id}/{iteration}")
async def get_iteration_metadata(session_id: str, iteration: int):
    """Get detailed metadata for a specific iteration"""
    metadata_file = pathlib.Path(f"generated_images/session_{session_id}/metadata_iteration_{iteration:02d}.json")
    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    return metadata

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": [
            {
                "session_id": session_id,
                "status": data["status"],
                "query": data["query"],
                "current_iteration": data["current_iteration"]
            }
            for session_id, data in active_sessions.items()
        ]
    }

async def run_generation_loop(session_id: str, query: str):
    """Run the enhanced iterative generation and evaluation loop with metadata integration"""
    print(f"🚀 Starting enhanced generation loop for: {query}")
    print(f"📋 Session ID: {session_id}")
    
    iteration = 1
    db_session = SQLiteSession(session_id)
    
    try:
        while iteration <= active_sessions[session_id]["max_iterations"]:
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
            
            # Generate new metadata and image prompt using the enhanced generation prompt
            generation_prompt = f"""
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
            
            result = await Runner.run(generation_agent, generation_prompt, session=db_session)
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
            
            # Prepare evaluation content using a more concise evaluation prompt
            evaluation_contents = f"""
You are a STRICT evaluation agent for 3D reconstruction images. Evaluate the image and metadata for 3D reconstruction.

CRITICAL REQUIREMENTS:
1. **4x4 Grid Layout**: Exactly 16 squares in 4x4 grid
2. **One Object Per Square**: Exactly ONE object per square
3. **Same Object Type**: ALL 16 squares show SAME object
4. **Same Pose**: Object in SAME pose across all views
5. **16 Distinct Angles**: Different angle/view in each square
6. **Consistent Size**: Object same size in all squares
7. **PURE WHITE BACKGROUND**: NO grid lines, text, numbers, watermarks
8. **Realistic Style**: Photorealistic, NOT wireframe/low-poly
9. **Lighting Consistency**: IDENTICAL lighting conditions
10. **Color Consistency**: EXACTLY same color/material across ALL views

TARGET OBJECT: {query}

METADATA:
{json.dumps(metadata, indent=2)}

IMAGE:
<image>{image_base64}</image>

Evaluate using these criteria and assign scores (1-10):
1. Image Quality: Visual clarity, proper 4x4 grid, one object per square, same object type, same pose, realistic style, white background, lighting consistency, color consistency.
2. Metadata Accuracy: Correctness and relevance of metadata for reconstruction, proper angle descriptions, lighting specifications, material properties.
3. Completeness: 16 distinct angles provide sufficient coverage for 3D reconstruction with 360° rotation, key views (front, back, left, right, top, bottom), and intermediate angles.

Include exact scores: "Image Quality: X/10", "Metadata Accuracy: X/10", "Completeness: X/10"

Provide specific improvement suggestions and metadata suggestions for next iteration.
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
            active_sessions[session_id]["current_iteration"] = iteration
            active_sessions[session_id]["metadata_files"].append(metadata_file)
            active_sessions[session_id]["image_urls"].append(image_url)
            active_sessions[session_id]["evaluation_history"].append(evaluation_results)
            
            # Check if quality threshold is met
            if meets_quality_threshold(evaluation_results.get("scores", {})):
                print("✅ Quality threshold met! Stopping iterations.")
                active_sessions[session_id]["status"] = "completed"
                break
            
            iteration += 1
        
        if iteration > active_sessions[session_id]["max_iterations"]:
            active_sessions[session_id]["status"] = "max_iterations_reached"
            print("⚠️  Reached maximum iterations")
        
    except Exception as e:
        print(f"❌ Error in enhanced generation loop: {e}")
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 