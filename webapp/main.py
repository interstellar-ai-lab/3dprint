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
from multiagent import generation_agent, writer_agent, Runner, SQLiteSession

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
        "status": "starting",
        "query": request.query,
        "iteration": 0,
        "metadata": None,
        "b64_image": None,
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
        "b64_image": session_data["b64_image"],
        "evaluations": session_data["evaluations"],
        "error": session_data["error"]
    }

@app.get("/api/image/{session_id}")
async def get_generated_image(session_id: str):
    """Get the generated image for a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    if not session_data["b64_image"]:
        raise HTTPException(status_code=404, detail="No image generated yet")
    
    # Convert base64 to image response
    image_data = base64.b64decode(session_data["b64_image"])
    return FileResponse(
        io.BytesIO(image_data),
        media_type="image/jpeg",
        filename=f"generated_{session_id}.jpg"
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
        
        # Initial generation
        metadata, b64_image = generation_agent(iteration, query)
        session_data["metadata"] = metadata
        session_data["b64_image"] = b64_image
        session_data["iteration"] = iteration
        
        # Iterative improvement loop
        while suggestions != "well done" and iteration < 5:  # Limit to 5 iterations
            iteration += 1
            session_data["iteration"] = iteration
            session_data["status"] = f"evaluating_iteration_{iteration}"
            
            # Run evaluation agent
            contents = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "detail": "auto",
                            "image_url": f"data:image/jpeg;base64,{b64_image}",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": f"The generated metadata is: {metadata}.",
                },
                {
                    "role": "user",
                    "content": "Please evaluate the generated 2D images and metadata, and think about the follow-up questions according to the guidelines.",
                }
            ]
            
            result = await Runner.run(writer_agent, contents)
            suggestions = result.final_output.suggestions_for_improvement
            
            # Store evaluation results
            evaluation = {
                "iteration": iteration,
                "markdown_report": result.final_output.markdown_report,
                "suggestions": result.final_output.suggestions_for_improvement,
                "short_summary": result.final_output.short_summary
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
                f"Additionally, consider the scores and reasoning provided in the evaluation report for the previous generation attempt:\n\n{result.final_output.markdown_report}."
            )
            
            metadata, b64_image = generation_agent(iteration, new_prompt)
            session_data["metadata"] = metadata
            session_data["b64_image"] = b64_image
        
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