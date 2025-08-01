from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import pathlib
import uuid
from typing import Optional, Dict, Any
import base64
from PIL import Image
import io
from openai import OpenAI
import tempfile
import os

# Import your existing multi-agent functionality
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from multiagent import generation_agent, writer_agent, Runner, SQLiteSession, extract_image_urls_from_text, parse_evaluation_text, download_image_to_base64, generate_3d_mesh_with_llm

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
app.mount("/static", StaticFiles(directory="api/static"), name="static")

# Store active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

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
    with open("api/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/generate", response_model=GenerationResponse)
async def start_generation(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start the 3D generation process"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Initialize session data
    active_sessions[session_id] = {
        "status": "starting",
        "query": request.query,
        "iteration": 0,
        "metadata": None,
        "image_urls": [],  # Store all image URLs
        "b64_images": [],  # Store all base64 images
        "mime_types": [],  # Store MIME types for each image
        "mesh_file_path": None,  # Store current mesh file path
        "mesh_filename": None,  # Store current mesh filename for download
        "iteration_meshes": {},  # Store mesh files for each iteration
        "iteration_data": {},  # Store complete data for each iteration
        "evaluations": [],
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
        "iteration": session_data["iteration"],
        "metadata": session_data["metadata"],
        "image_urls": session_data["image_urls"],
        "b64_images": session_data["b64_images"],
        "mime_types": session_data["mime_types"],
        "mesh_file_path": session_data["mesh_file_path"],
        "mesh_filename": session_data["mesh_filename"],
        "iteration_meshes": session_data["iteration_meshes"],
        "iteration_data": session_data["iteration_data"],
        "evaluations": session_data["evaluations"],
        "error": session_data["error"]
    }

@app.get("/api/image/{session_id}")
async def get_generated_image(session_id: str):
    """Get the first generated image for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    b64_images = session_data.get("b64_images", [])
    mime_types = session_data.get("mime_types", [])
    
    if not b64_images:
        raise HTTPException(status_code=404, detail="No images generated")
    
    # Return the first image
    return {
        "image_data": b64_images[0],
        "mime_type": mime_types[0] if mime_types else "image/jpeg"
    }

@app.get("/api/local-image/{session_id}/{image_index}")
async def get_local_image(session_id: str, image_index: int):
    """Get a local image file for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    local_image_paths = session_data.get("local_image_paths", [])
    
    if not local_image_paths or image_index >= len(local_image_paths):
        raise HTTPException(status_code=404, detail="Image not found")
    
    local_path = local_image_paths[image_index]
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    # Return the image file
    return FileResponse(
        path=local_path,
        media_type="image/png",
        filename=f"image_{image_index}.png"
    )

@app.get("/api/mesh/{session_id}")
async def get_generated_mesh(session_id: str):
    """Get the generated mesh file for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    if not session_data["mesh_file_path"]:
        raise HTTPException(status_code=404, detail="No mesh generated yet")
    
    mesh_path = pathlib.Path(session_data["mesh_file_path"])
    if not mesh_path.exists():
        raise HTTPException(status_code=404, detail="Mesh file not found")
    
    filename = session_data["mesh_filename"] or f"mesh_{session_id}.obj"
    return FileResponse(
        mesh_path,
        media_type="application/octet-stream",
        filename=filename
    )

@app.get("/api/mesh/{session_id}/{iteration}")
async def get_iteration_mesh(session_id: str, iteration: int):
    """Get the generated mesh file for a specific iteration"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    if iteration not in session_data["iteration_meshes"]:
        raise HTTPException(status_code=404, detail=f"No mesh found for iteration {iteration}")
    
    mesh_path = pathlib.Path(session_data["iteration_meshes"][iteration])
    if not mesh_path.exists():
        raise HTTPException(status_code=404, detail="Mesh file not found")
    
    filename = f"mesh_{session_id}_iteration_{iteration}.obj"
    return FileResponse(
        mesh_path,
        media_type="application/octet-stream",
        filename=filename
    )

@app.get("/api/mesh-visualization/{session_id}/{iteration}")
async def get_mesh_visualization(session_id: str, iteration: int):
    """Get PNG mesh visualization for a specific iteration"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    if iteration not in session_data["iteration_meshes"]:
        raise HTTPException(status_code=404, detail=f"No mesh found for iteration {iteration}")
    
    # Look for PNG file with same base name as the OBJ file
    mesh_path = pathlib.Path(session_data["iteration_meshes"][iteration])
    png_path = mesh_path.with_suffix('.png')
    
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="Mesh visualization not found")
    
    return FileResponse(
        png_path,
        media_type="image/png",
        filename=f"mesh_visualization_{session_id}_iteration_{iteration}.png"
    )

async def run_generation_loop(session_id: str, query: str):
    """Run the complete generation loop in the background"""
    try:
        session_data = active_sessions[session_id]
        session_data["status"] = "generating"
        
        # Create SQLite session for the agents
        db_session = SQLiteSession(f"web_session_{session_id}")
        
        iteration = 0
        suggestions = ""
        
        # Step 1: Generate metadata and image prompts
        result_1 = await Runner.run(generation_agent, f"Please generate the materials needed for 3D CAD generation for: {query}", session=db_session)
        
        # Parse the structured output
        try:
            import json
            parsed_output = json.loads(result_1.final_output)
            metadata = parsed_output.get("metadata", "")
            image_prompts = parsed_output.get("image_prompts", [])
            description = parsed_output.get("description", "")
        except (json.JSONDecodeError, KeyError):
            metadata = result_1.final_output
            image_prompts = []
            description = ""
        
        # Step 2: Generate images from prompts
        image_urls = []
        if image_prompts:
            print(f"\nGenerating {len(image_prompts)} images from prompts...")
            from multiagent import generate_images_from_prompts
            image_urls, _ = await generate_images_from_prompts(image_prompts)
        else:
            image_urls = extract_image_urls_from_text(metadata)
        
        # Step 3: Download images locally
        local_image_paths = []
        if image_urls:
            print(f"\nDownloading {len(image_urls)} images locally...")
            from multiagent import download_images_locally
            local_image_paths = await download_images_locally(image_urls, session_id)

        # Download and convert all images to base64
        b64_images = []
        mime_types = []
        if image_urls:
            for url in image_urls:
                b64_data, mime_type = await download_image_to_base64(url)
                if b64_data:
                    b64_images.append(b64_data)
                    mime_types.append(mime_type)

        session_data["metadata"] = metadata
        session_data["image_urls"] = image_urls
        session_data["local_image_paths"] = local_image_paths
        session_data["b64_images"] = b64_images
        session_data["mime_types"] = mime_types
        session_data["iteration"] = iteration
        
        # Store complete iteration data
        session_data["iteration_data"][iteration] = {
            "metadata": metadata,
            "image_urls": image_urls,
            "local_image_paths": local_image_paths,
            "b64_images": b64_images,
            "mime_types": mime_types
        }
        
        # Generate mesh for this iteration using LLM
        try:
            mesh_path = await generate_3d_mesh_with_llm(metadata, image_urls)
            if mesh_path and not mesh_path.startswith("Error"):
                session_data["iteration_meshes"][iteration] = mesh_path
                session_data["mesh_file_path"] = mesh_path  # Keep current mesh
                session_data["mesh_filename"] = pathlib.Path(mesh_path).name
                print(f"Generated LLM-based mesh for iteration {iteration}: {mesh_path}")
        except Exception as e:
            print(f"Error generating LLM-based mesh for iteration {iteration}: {e}")
        
        # Iterative improvement loop
        while suggestions != "well done" and iteration < 5:  # Limit to 5 iterations
            iteration += 1
            session_data["iteration"] = iteration
            session_data["status"] = f"evaluating_iteration_{iteration}"
            
            # Run evaluation agent
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
            
            # Only add image content if we have valid base64 images
            if b64_images and len(b64_images) > 0:
                for i, b64_image in enumerate(b64_images):
                    if b64_image and b64_image.strip():
                        contents.insert(0, {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_image",
                                    "detail": "auto",
                                    "image_url": f"data:{mime_types[i]};base64,{b64_image}",
                                }
                            ],
                        })
            
            result = await Runner.run(writer_agent, contents)
            evaluation_text = result.final_output
            
            # Parse the evaluation text manually
            parsed_evaluation = parse_evaluation_text(evaluation_text)
            suggestions = parsed_evaluation["suggestions_for_improvement"]
            
            # Store evaluation results
            evaluation = {
                "iteration": iteration,
                "markdown_report": parsed_evaluation["markdown_report"],
                "suggestions": parsed_evaluation["suggestions_for_improvement"],
                "short_summary": parsed_evaluation["short_summary"]
            }
            session_data["evaluations"].append(evaluation)
            
            if suggestions == "well done":
                break
                
            # Generate improved version
            session_data["status"] = f"improving_iteration_{iteration}"
            new_prompt = (
                f"The target for your generation is: {query}. Detailed task is introduced by the instructions from the system above.\n\n"
                f"Below are the metadata from your previous generation attempt:\n\n{metadata}\n\n"
                f"Please refine the generation results based on the system instructions. Pay special attention to the following suggestions for improvement: {suggestions}.\n\n"
                f"Additionally, consider the scores and reasoning provided in the evaluation report for the previous generation attempt:\n\n{parsed_evaluation['markdown_report']}."
            )
            
            result_1 = await Runner.run(generation_agent, new_prompt, session=db_session)
            
            # Parse the structured output again
            try:
                parsed_output = json.loads(result_1.final_output)
                metadata = parsed_output.get("metadata", "")
                image_prompts = parsed_output.get("image_prompts", [])
                description = parsed_output.get("description", "")
            except (json.JSONDecodeError, KeyError):
                metadata = result_1.final_output
                image_prompts = []
                description = ""
            
            # Generate new images from prompts
            if image_prompts:
                print(f"\nGenerating {len(image_prompts)} new images from prompts...")
                image_urls, _ = await generate_images_from_prompts(image_prompts)
            else:
                image_urls = extract_image_urls_from_text(metadata)
            
            # Download new images locally
            local_image_paths = []
            if image_urls:
                print(f"\nDownloading {len(image_urls)} new images locally...")
                local_image_paths = await download_images_locally(image_urls, session_id)

            # Download and convert all images to base64
            b64_images = []
            mime_types = []
            if image_urls:
                for url in image_urls:
                    b64_data, mime_type = await download_image_to_base64(url)
                    if b64_data:
                        b64_images.append(b64_data)
                        mime_types.append(mime_type)

            session_data["metadata"] = metadata
            session_data["image_urls"] = image_urls
            session_data["local_image_paths"] = local_image_paths
            session_data["b64_images"] = b64_images
            session_data["mime_types"] = mime_types
            
            # Store complete iteration data
            session_data["iteration_data"][iteration] = {
                "metadata": metadata,
                "image_urls": image_urls,
                "local_image_paths": local_image_paths,
                "b64_images": b64_images,
                "mime_types": mime_types
            }
            
            # Generate mesh for this iteration
            try:
                mesh_path = await generate_3d_mesh_with_llm(metadata, image_urls)
                if mesh_path and not mesh_path.startswith("Error"):
                    session_data["iteration_meshes"][iteration] = mesh_path
                    session_data["mesh_file_path"] = mesh_path  # Keep current mesh
                    session_data["mesh_filename"] = pathlib.Path(mesh_path).name
                    print(f"Generated mesh for iteration {iteration}: {mesh_path}")
            except Exception as e:
                print(f"Error generating mesh for iteration {iteration}: {e}")
        
        session_data["status"] = "completed"
        
    except Exception as e:
        session_data["status"] = "error"
        session_data["error"] = str(e)
        print(f"Error in generation loop: {e}")

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": [
            {
                "session_id": session_id,
                "status": data["status"],
                "query": data["query"],
                "iteration": data["iteration"]
            }
            for session_id, data in active_sessions.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 