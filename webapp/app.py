#!/usr/bin/env python3
"""
Multi agent to generate 3D images - Flask Web App for EC2 Deployment
"""

from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import json
import os
import sys
import uuid
import pathlib
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import base64
from PIL import Image
import io
from openai import OpenAI, AsyncOpenAI
import aiohttp
import threading
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webapp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import studio module
# Add the project root directory to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
project_root = os.path.abspath(project_root)
sys.path.insert(0, project_root)

try:
    from studio_module import create_supabase_studio_manager
    SUPABASE_STUDIO_AVAILABLE = True
    logger.info("✅ Studio module imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Studio module not available: {e}")
    SUPABASE_STUDIO_AVAILABLE = False

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://3dviewer.net", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8001", "http://127.0.0.1:8001", "https://vicino.ai", "https://www.vicino.ai", "https://vicino.ai:8001", "https://vicino.ai:443", "http://vicino.ai", "http://www.vicino.ai", "http://vicino.ai:8001"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With", "Cache-Control", "Pragma"],
        "supports_credentials": True
    }
})

# Store active sessions (in production, use a proper database)
active_sessions = {}

# OpenAI clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET_NAME = "generated-images-bucket"

# Initialize Supabase client if available
try:
    from supabase import create_client, Client
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        # Use service key for server-side operations (bypasses RLS)
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        SUPABASE_AVAILABLE = True
        logger.info("✅ Supabase client initialized successfully with service key")
    elif SUPABASE_URL and SUPABASE_ANON_KEY:
        # Fallback to anon key if service key not available
        supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        SUPABASE_AVAILABLE = True
        logger.info("✅ Supabase client initialized with anon key (RLS restrictions may apply)")
    else:
        supabase_client = None
        SUPABASE_AVAILABLE = False
        logger.warning("⚠️ Supabase URL or keys not found in environment variables")
except ImportError:
    supabase_client = None
    SUPABASE_AVAILABLE = False
    logger.warning("⚠️ Supabase library not installed. Install with: pip install supabase")

async def download_image_to_pil(image_url: str) -> Optional[Image.Image]:
    """Download image from URL and convert to PIL Image"""
    try:
        # Handle HTTP URL
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return Image.open(io.BytesIO(image_data))
                else:
                    logger.error(f"Failed to download image from {image_url}: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error loading image from {image_url}: {e}")
        return None

def upload_image_to_supabase(image_data: bytes, filename: str, content_type: str = "image/png", bucket_name: str = None) -> Optional[str]:
    """Upload file to Supabase storage bucket using service key"""
    if not SUPABASE_AVAILABLE or not supabase_client:
        logger.warning("⚠️ Supabase not available, skipping upload")
        return None
    
    # Use provided bucket name or default to images bucket
    target_bucket = bucket_name or SUPABASE_BUCKET_NAME
    
    try:
        # Upload to Supabase storage using service key
        response = supabase_client.storage.from_(target_bucket).upload(
            path=filename,
            file=image_data,
            file_options={"content-type": content_type}
        )
        
        if response:
            # Generate public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{target_bucket}/{filename}"
            logger.info(f"✅ Uploaded file to Supabase bucket '{target_bucket}': {public_url}")
            return public_url
        else:
            logger.error("❌ Failed to upload file to Supabase")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error uploading file to Supabase: {e}")
        return None

def insert_image_record(target_object: str, image_url: str, iteration: int = None, model_3d_url: str = None) -> Optional[int]:
    """Insert image record into generated_images table"""
    if not SUPABASE_AVAILABLE or not supabase_client:
        logger.warning("⚠️ Supabase not available, skipping database insert")
        return None
    
    try:
        # Prepare data for insertion
        data = {
            "target_object": target_object,
            "image_url": image_url,
            "iteration": iteration
        }
        
        # Add 3D model URL if provided
        if model_3d_url:
            data["3d_url"] = model_3d_url
        
        # Insert the record
        response = supabase_client.table('generated_images').insert(data).execute()
        
        if response.data and len(response.data) > 0:
            inserted_id = response.data[0].get('id')
            logger.info(f"✅ Inserted image record with ID: {inserted_id}")
            return inserted_id
        else:
            logger.error("❌ No data returned from insert operation")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error inserting image record: {e}")
        return None

def download_image_to_pil_sync(image_url: str) -> Optional[Image.Image]:
    """Download image from URL or load from file and convert to PIL Image (synchronous version)"""
    try:
        if image_url.startswith("file://"):
            # Handle local file
            file_path = image_url.replace("file://", "")
            return Image.open(file_path)
        else:
            # Handle HTTP URL
            import requests
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                logger.error(f"Failed to download image from {image_url}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error loading image from {image_url}: {e}")
        return None

def generate_multiview_with_gpt_image1(target_object: str, iteration: int = 1, previous_feedback: List[str] = None, previous_image_url: str = None) -> str:
    """Generate 2x2 multiview image using GPT-Image-1 with image-to-image capability"""
    
    # Create the generation instructions
    instructions = f"""Your task is to generate a 2x2 grid with 4 specific views of the same object for 3D reconstruction: {target_object}. 

GRID LAYOUT (2x2):
- Top Left: FRONT view
- Top Right: RIGHT view  
- Bottom Left: LEFT view
- Bottom Right: BACK view

CRITICAL OBJECT CONSISTENCY REQUIREMENTS (MOST IMPORTANT):
- EXACT same object type across ALL 4 views (e.g., if it's a Golden Retriever, ALL 4 views must show Golden Retrievers)
- EXACT same color, texture, and material across ALL 4 views
- EXACT same size and proportions across ALL 4 views
- EXACT same pose/position of the object across ALL 4 views
- NO variations in object appearance, shape, or characteristics
- NO different objects in different grid positions
- NO mixed object types (e.g., some Golden Retrievers, some other dog breeds)

VIEW REQUIREMENTS:
- FRONT view: Object facing directly toward the camera
- RIGHT view: Object rotated 90 degrees to show right side
- LEFT view: Object rotated 90 degrees to show left side  
- BACK view: Object rotated 180 degrees to show back/rear

OBJECT CONSISTENCY IS THE MOST CRITICAL FACTOR FOR 3D RECONSTRUCTION. FAILURE TO MAINTAIN CONSISTENCY WILL RESULT IN POOR RECONSTRUCTION QUALITY."""

    # Add feedback from previous iterations
    feedback_text = " ".join(previous_feedback) if previous_feedback else "No specific feedback available"
    if previous_feedback:
        if iteration > 1:
            instructions += f" IMPORTANT: Based on the previous image, address these specific issues: {feedback_text}. Maintain the good aspects while fixing the problems identified."
        else:
            instructions += f" IMPORTANT: Address these specific issues from previous iteration: {feedback_text}"
    
    try:
        # Debug logging
        logger.info(f"🔍 Debug: iteration={iteration}, previous_image_url={'None' if previous_image_url is None else 'exists'}")
        
        # For first iteration - text to image
        if iteration == 1 or not previous_image_url:
            logger.info(f"🎨 Generating initial image for '{target_object}' (iteration {iteration})...")
            response = openai_sync_client.images.generate(
                model="gpt-image-1",
                prompt=instructions,
                size="1024x1024",
            )
        else:
            # For subsequent iterations - image edit with feedback
            logger.info(f"🎨 Editing previous image with feedback for '{target_object}' (iteration {iteration})...")
            
            # Download previous image
            previous_image = download_image_to_pil_sync(previous_image_url)
            if not previous_image:
                logger.warning(f"⚠️  Could not load previous image for iteration {iteration}, using text-to-image generation instead")
                response = openai_sync_client.images.generate(
                    model="gpt-image-1",
                    prompt=instructions,
                    size="1024x1024",
                )
            else:
                # Create edit instructions based on feedback
                edit_instructions = f"""Improve this 2x2 multiview image of {target_object} by addressing these specific issues: {feedback_text}. Maintain the overall structure and good aspects while fixing the identified problems.

GRID LAYOUT (2x2):
- Top Left: FRONT view
- Top Right: RIGHT view  
- Bottom Left: LEFT view
- Bottom Right: BACK view

CRITICAL: Ensure EXACT object consistency across ALL 4 views:
- Same object type, color, texture, size, and proportions
- NO variations in object appearance or characteristics
- NO mixed object types or different objects

VIEW REQUIREMENTS:
- FRONT view: Object facing directly toward the camera
- RIGHT view: Object rotated 90 degrees to show right side
- LEFT view: Object rotated 90 degrees to show left side  
- BACK view: Object rotated 180 degrees to show back/rear

OBJECT CONSISTENCY IS THE MOST CRITICAL FACTOR FOR 3D RECONSTRUCTION."""
                
                # Save PIL image to temporary file
                import tempfile
                temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                previous_image.save(temp_image_file, format='PNG')
                temp_image_file.close()
                
                # Create a proper mask with alpha channel for editing
                # Create a white mask with transparency to allow full editing
                mask_image = Image.new('RGBA', previous_image.size, (255, 255, 255, 255))
                temp_mask_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                mask_image.save(temp_mask_file, format='PNG')
                temp_mask_file.close()
                
                # Open files in binary mode for the API
                with open(temp_image_file.name, "rb") as image_file, open(temp_mask_file.name, "rb") as mask_file:
                    response = openai_sync_client.images.edit(
                        model="gpt-image-1",
                        image=image_file,
                        mask=mask_file,
                        prompt=edit_instructions,
                        n=1,
                        size="1024x1024"
                    )
        
        if hasattr(response, 'data') and response.data:
            # Check if it's a URL or base64 data
            first_item = response.data[0]
            if hasattr(first_item, 'url') and first_item.url:
                image_url = first_item.url
                
                image_url = first_item.url
                return image_url
                    
            elif hasattr(first_item, 'b64_json') and first_item.b64_json:
                # Handle base64 data - save to PNG file and upload to Supabase
                try:
                    # Decode base64 data
                    image_data = base64.b64decode(first_item.b64_json)
                    
                    # Generate filename for Supabase
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{target_object.replace(' ', '_')}_{iteration}_{timestamp}.png"
                    
                    # Create temporary file
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    return f"file://{temp_file.name}"
                        
                except Exception as e:
                    logger.error(f"❌ Error handling base64 data: {e}")
                    return None
            else:
                logger.error(f"❌ Unexpected response format")
                return None
        else:
            logger.error(f"❌ No image data in response")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error generating with GPT-4 Vision: {e}")
        return None

def evaluate_image_with_gpt4v(image_url: str, target_object: str, iteration: int) -> Dict:
    """Evaluate generated image using GPT-4 Vision"""
    
    evaluation_prompt = f"""Analyze this 2x2 multiview grid image of a {target_object} for 3D reconstruction suitability.

    EVALUATION CRITERIA:
    1. Image Quality (1-10): Clarity, resolution, lighting, focus
    2. Grid Structure (1-10): How well the 2x2 grid layout works
    3. Angle Diversity (1-10): How well the 4 cardinal views (front, back, left, right) are represented
    4. Object Consistency (1-10): Same object appearance across all views
    5. Background Cleanliness (1-10): Pure white background
    6. 3D Reconstruction Suitability (1-10): Overall suitability for 3D reconstruction

    GRID LAYOUT CHECK:
    - Top Left: Should be FRONT view
    - Top Right: Should be RIGHT view  
    - Bottom Left: Should be LEFT view
    - Bottom Right: Should be BACK view

    OBJECT CONSISTENCY CHECK:
    - Are all 4 objects the same type? (e.g., all Golden Retrievers)
    - Are all objects in the same pose? (all standing OR all sitting OR all lying down)
    - Are all objects the same size and color?
    - If you see mixed poses (some standing, some sitting), this is a major issue

    SCORING:
    - Score 10: Perfect quality, meets all requirements
    - Score 8-9: Excellent quality with minor issues
    - Score 6-7: Good quality with noticeable issues
    - Score 4-5: Poor quality with major issues
    - Score 1-3: Very poor quality or major failures

    Provide your evaluation in this exact format:

    Image Quality: [score]/10
    Grid Structure: [score]/10
    Angle Diversity: [score]/10
    Object Consistency: [score]/10
    Background Cleanliness: [score]/10
    3D Reconstruction Suitability: [score]/10

    Overall Score: [average]/10

    Specific Issues Found:
    - [List any issues you see]

    Suggestions for Improvement:
    - [List suggestions for improvement]"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Handle both URLs and data URLs
            if image_url.startswith("data:image/"):
                # Handle data URL directly
                # Extract base64 data from data URL
                header, encoded = image_url.split(",", 1)
                base64_image = encoded
            else:
                # Download and encode the image
                image = download_image_to_pil_sync(image_url)
                if not image:
                    raise Exception("Failed to download image")
                
                # Convert to base64
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Call GPT-4 Vision API
            response = openai_sync_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": evaluation_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            evaluation_text = response.choices[0].message.content
            logger.info(f"🔍 Evaluation completed for iteration {iteration} (text length: {len(evaluation_text)} chars)")
            
            # Check if the response indicates failure
            if "I'm sorry" in evaluation_text or "I can't assist" in evaluation_text:
                raise Exception("Evaluation agent refused to process the request")
            
            # Parse the evaluation
            parsed_results = parse_evaluation_text(evaluation_text)
            
            # Apply penalties if needed
            parsed_results = apply_object_consistency_penalties(parsed_results, evaluation_text)
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"❌ Evaluation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"🔄 Retrying evaluation... (attempt {attempt + 2}/{max_retries})")
                import time
                time.sleep(2)  # Wait before retry
            else:
                logger.error(f"❌ All evaluation attempts failed, using fallback scores")
                # Return fallback evaluation results
                return {
                    "scores": {
                        "Image Quality": 5.0,
                        "Grid Structure": 5.0,
                        "Angle Diversity": 5.0,
                        "Object Consistency": 5.0,
                        "Background Cleanliness": 5.0,
                        "3D Reconstruction Suitability": 5.0,
                        "overall": 5.0
                    },
                    "issues": ["Evaluation failed - using fallback scores"],
                    "suggestions": ["Retry evaluation or check image quality"]
                }

def parse_evaluation_text(text: str) -> Dict:
    """Parse evaluation text into structured data"""
    lines = text.split('\n')
    
    scores = {}
    issues = []
    suggestions = []
    
    in_issues = False
    in_suggestions = False
    
    for line in lines:
        line = line.strip()
        
        # Parse scores
        if ':' in line and '/10' in line:
            parts = line.split(':')
            if len(parts) == 2:
                metric = parts[0].strip()
                score_part = parts[1].strip()
                if '/10' in score_part:
                    try:
                        score = float(score_part.split('/')[0])
                        scores[metric] = score
                    except ValueError:
                        logger.warning(f"   ❌ Could not parse score from: {line}")
        
        # Parse issues and suggestions
        if "Specific Issues Found:" in line:
            in_issues = True
            in_suggestions = False
            continue
        elif "Suggestions for Improvement:" in line:
            in_issues = False
            in_suggestions = True
            continue
        elif line.startswith("Image Quality:") or line.startswith("Grid Structure:") or line.startswith("Overall Score:"):
            in_issues = False
            in_suggestions = False
        
        # Extract issues
        if in_issues and line:
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                issue = line[1:].strip()
                if issue:  # Only add non-empty issues
                    issues.append(issue)
            elif line and not line.startswith('Specific Issues Found:'):
                issues.append(line)
        
        # Extract suggestions
        if in_suggestions and line:
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                suggestion = line[1:].strip()
                if suggestion:  # Only add non-empty suggestions
                    suggestions.append(suggestion)
            elif line and not line.startswith('Suggestions for Improvement:'):
                suggestions.append(line)
    
    # Calculate overall score if not present
    if 'Overall Score' not in scores and scores:
        overall_score = sum(scores.values()) / len(scores)
        scores['overall'] = overall_score
    
    return {
        "scores": scores,
        "issues": issues,
        "suggestions": suggestions
    }

def apply_object_consistency_penalties(parsed_results: Dict, evaluation_text: str) -> Dict:
    """Apply penalties to object consistency scores based on detected issues"""
    
    # Check for specific object consistency issues in the evaluation text
    text_lower = evaluation_text.lower()
    
    # Define penalties for different issues
    penalties = {
        "mixed_poses": 0,
        "different_sizes": 0,
        "different_colors": 0,
        "pose_inconsistency": 0
    }
    
    # AGGRESSIVE PENALTY DETECTION - Check for any mention of pose-related issues
    pose_keywords = ["standing", "sitting", "lying", "pose", "position", "posture", "stance"]
    if any(keyword in text_lower for keyword in pose_keywords):
        if "inconsistent" in text_lower or "different" in text_lower or "mixed" in text_lower:
            penalties["pose_inconsistency"] = 4
            penalties["mixed_poses"] = 4
    
    # Check for size issues
    if "size" in text_lower and ("different" in text_lower or "inconsistent" in text_lower):
        penalties["different_sizes"] = 3
    
    # Check for color/texture issues
    if "color" in text_lower and ("different" in text_lower or "inconsistent" in text_lower):
        penalties["different_colors"] = 4
    
    # MANUAL OVERRIDE: If Object Consistency score is suspiciously high (9+) but no penalties detected,
    # apply a conservative penalty to encourage more iterations
    scores = parsed_results.get("scores", {})
    if "Object Consistency" in scores:
        original_score = scores["Object Consistency"]
        total_penalty = sum(penalties.values())
        
        # If score is very high (9+) but no penalties detected, apply conservative penalty
        if original_score >= 9.0 and total_penalty == 0:
            # Check if the evaluation mentions any issues at all
            if "issue" in text_lower or "problem" in text_lower or "variation" in text_lower:
                penalties["conservative_penalty"] = 2
                total_penalty = 2
                logger.info(f"🔍 Applied conservative penalty: High score but issues mentioned")
        
        # Apply penalty (minimum score of 1)
        new_score = max(1, original_score - total_penalty)
        scores["Object Consistency"] = new_score
        
        # Recalculate overall score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
            scores["overall"] = overall_score
        
        logger.info(f"🔍 Applied object consistency penalties:")
        logger.info(f"   Original Object Consistency score: {original_score}")
        logger.info(f"   Total penalty: {total_penalty}")
        logger.info(f"   New Object Consistency score: {new_score}")
        logger.info(f"   New overall score: {overall_score}")
    
    return parsed_results

def meets_quality_threshold(scores: Dict) -> bool:
    """Check if quality threshold is met (REASONABLE STANDARDS - allows iterations for improvement)"""
    overall = scores.get("overall", 0)
    grid_structure = scores.get("Grid Structure", 0)
    angle_diversity = scores.get("Angle Diversity", 0)
    object_consistency = scores.get("Object Consistency", 0)
    
    # REASONABLE thresholds - allows iterations for improvement while maintaining good standards
    all_scores = [v for k, v in scores.items() if isinstance(v, (int, float)) and k != "overall"]
    
    # Check if we have good overall score and reasonable individual scores
    return (
        overall >= 8.5 and  # Good overall score
        grid_structure >= 8.0 and  # Good grid structure
        angle_diversity >= 8.0 and  # Good angle diversity
        object_consistency >= 8.5 and  # Good object consistency (pose consistency)
        all(score >= 7.0 for score in all_scores)  # Reasonable bar across all metrics
    )

def save_metadata(session_id: str, iteration: int, target_object: str, image_url: str, evaluation_results: Dict, mode: str = "quick") -> str:
    """Save metadata for this iteration"""
    session_dir = pathlib.Path(f"generated_images/session_{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_file = session_dir / f"metadata_iteration_{iteration:02d}.json"
    metadata_data = {
        "session_id": session_id,
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "target_object": target_object,
        "image_url": image_url,
        "evaluation_results": evaluation_results,
        "generation_model": "gpt-image-1",
        "evaluation_model": "gpt-4o",
        "mode": mode
    }
    

    
    with open(metadata_file, 'w') as f:
        json.dump(metadata_data, f, indent=2)
    
    return str(metadata_file)

def run_hybrid_multiview_generation(session_id: str, target_object: str, mode: str = "quick") -> Dict:
    """Run iterative hybrid multiview generation with different modes"""
    
    session_id = session_id
    previous_feedback = []
    previous_image_url = None
    all_results = []
    iteration = 0
    
    # Set iteration limits based on mode
    if mode.lower() == "deep":
        max_iterations = 10
        mode_display = "Deep Think Mode"
    else:  # quick mode (default)
        max_iterations = 3
        mode_display = "Quick Mode"
    
    logger.info(f"🚀 Starting {mode_display} for '{target_object}' (max {max_iterations} iterations)")
    
    # Initialize session
    active_sessions[session_id] = {
        "status": "running",
        "target_object": target_object,
        "mode": mode,
        "max_iterations": max_iterations,
        "current_iteration": 0,
        "iterations": [],
        "final_score": 0,
        "evaluation_status": None
    }
    
    while True:
        iteration += 1
        
        # Check iteration limit based on mode
        if iteration > max_iterations:
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["final_score"] = scores.get("overall", 0) if 'scores' in locals() else 0
            active_sessions[session_id]["message"] = f"Reached maximum iterations ({max_iterations}) for {mode_display} - best result achieved"
            break
        
        # Update session status
        active_sessions[session_id]["current_iteration"] = iteration
        
        # Generate image with GPT-Image-1 (image-to-image for iterations > 1)
        image_url = generate_multiview_with_gpt_image1(target_object, iteration, previous_feedback, previous_image_url)
        
        if not image_url:
            active_sessions[session_id]["status"] = "failed"
            active_sessions[session_id]["error"] = "Failed to generate image"
            break
        
        # IMMEDIATELY add the image to session (before evaluation)
        iteration_result = {
            "iteration": iteration,
            "image_url": image_url,
            "evaluation": None,  # Will be updated after evaluation
            "metadata_file": None,  # Will be updated after evaluation
            "evaluation_status": "evaluating"  # Show evaluation progress
        }
        all_results.append(iteration_result)
        
        # Update session with iteration data IMMEDIATELY
        active_sessions[session_id]["iterations"].append(iteration_result)
        
        # Update session status to show evaluation progress
        active_sessions[session_id]["evaluation_status"] = f"Evaluating..."
        
        # Evaluate image with GPT-4 Vision
        evaluation_results = evaluate_image_with_gpt4v(image_url, target_object, iteration)
        
        # Save metadata
        metadata_file = save_metadata(session_id, iteration, target_object, image_url, evaluation_results, mode)
        
        # Update the existing iteration_result with evaluation data
        active_sessions[session_id]["iterations"][-1]["evaluation"] = evaluation_results
        active_sessions[session_id]["iterations"][-1]["metadata_file"] = metadata_file
        active_sessions[session_id]["iterations"][-1]["evaluation_status"] = "completed"
        
        # Clear evaluation status
        active_sessions[session_id]["evaluation_status"] = None
        
        # Check if quality threshold is met
        scores = evaluation_results.get("scores", {})
        if meets_quality_threshold(scores):
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["final_score"] = scores.get("overall", 0)
            active_sessions[session_id]["message"] = f"Quality threshold met in {mode_display} - generation completed"
            break
        
        # Store current image URL for next iteration
        previous_image_url = image_url
        
        # Print image URL info without cluttering the console
        if image_url.startswith('data:image/'):
            logger.info(f"📸 Stored base64 image for iteration {iteration}")
        elif image_url.startswith('http'):
            logger.info(f"📸 Stored remote image URL for iteration {iteration}: {image_url[:50]}...")
        else:
            logger.info(f"📸 Stored image for iteration {iteration}")
        
        # Prepare feedback for next iteration
        previous_feedback = evaluation_results.get("suggestions", [])
        scores = evaluation_results.get("scores", {})
        issues = evaluation_results.get("issues", [])
        
        logger.info(f"📊 Iteration {iteration} Evaluation Results ({mode_display}):")
        logger.info(f"   Scores: {scores}")
        logger.info(f"   Issues Found: {issues}")
        logger.info(f"   Suggestions for Improvement: {previous_feedback}")
        logger.info(f"   Overall Score: {scores.get('overall', 'N/A')}/10")
        logger.info(f"   Remaining iterations: {max_iterations - iteration}")
        
        # Add a minimal delay between iterations to prevent overwhelming the API
        import time
        time.sleep(0.5)
    
    return {
        "session_id": session_id,
        "target_object": target_object,
        "mode": mode,
        "max_iterations": max_iterations,
        "iterations": all_results,
        "final_score": active_sessions[session_id]["final_score"]
    }

@app.route('/')
def home():
    """Main page with input form"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """Start iterative generation process"""
    try:
        data = request.get_json()
        target_object = data.get('target_object', '').strip()
        mode = data.get('mode', 'quick') # Default to 'quick' if not provided
        
        if not target_object:
            return jsonify({"error": "Target object is required"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Start generation in background
        def run_generation():
            try:
                run_hybrid_multiview_generation(session_id, target_object, mode)
            except Exception as e:
                logger.error(f"Error in generation thread for session {session_id}: {e}")
                if session_id in active_sessions:
                    active_sessions[session_id]["status"] = "failed"
                    active_sessions[session_id]["error"] = str(e)
        
        # Run in background thread
        thread = threading.Thread(target=run_generation)
        thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
        thread.start()
        
        logger.info(f"Started generation session {session_id} for '{target_object}' in {mode} mode")
        
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "message": f"Started iterative generation for: {target_object} in {mode} mode"
        })
        
    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """Get current status and results for a session"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        
        return jsonify({
            "session_id": session_id,
            "status": session["status"],
            "target_object": session["target_object"],
            "mode": session["mode"],
            "max_iterations": session["max_iterations"],
            "current_iteration": session["current_iteration"],
            "iterations": session["iterations"],
            "final_score": session["final_score"],
            "error": session.get("error", None),
            "evaluation_status": session.get("evaluation_status", None)
        })
        
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/image/<session_id>/<int:iteration>')
def get_iteration_image(session_id, iteration):
    """Get image for a specific iteration"""
    try:
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        session = active_sessions[session_id]
        if iteration > len(session["iterations"]):
            return jsonify({"error": "Iteration not found"}), 404
        
        iteration_data = session["iterations"][iteration - 1]
        image_url = iteration_data["image_url"]
        
        # Handle file URLs
        if image_url.startswith('file://'):
            file_path = image_url.replace('file://', '')
            return send_file(file_path, mimetype='image/png')
        
        # Handle base64 data URLs
        elif image_url.startswith('data:image/'):
            # Extract the base64 data
            header, encoded = image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            
            # Determine content type from the data URL
            content_type = header.split(":")[1].split(";")[0]
            
            # Return the image data directly
            return Response(image_data, mimetype=content_type)
        
        # Handle OpenAI URLs - download and serve the image
        elif image_url.startswith('http'):
            # Use requests to download the image
            try:
                import requests
                response = requests.get(image_url, timeout=30)
                if response.status_code == 200:
                    # Determine content type from response headers or URL
                    content_type = response.headers.get('content-type', 'image/png')
                    return Response(response.content, mimetype=content_type)
                else:
                    return jsonify({"error": "Failed to fetch image from URL"}), 500
            except Exception as e:
                logger.error(f"Failed to download image: {e}")
                return jsonify({"error": f"Failed to download image: {str(e)}"}), 500
        
        else:
            return jsonify({"error": "Invalid image URL format"}), 400
            
    except Exception as e:
        logger.error(f"Error serving image for session {session_id}, iteration {iteration}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    try:
        sessions = []
        for session_id, session_data in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "status": session_data["status"],
                "target_object": session_data["target_object"],
                "mode": session_data["mode"],
                "max_iterations": session_data["max_iterations"],
                "current_iteration": session_data["current_iteration"],
                "final_score": session_data["final_score"]
            })
        
        return jsonify({"sessions": sessions})
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-3d', methods=['POST'])
def generate_3d():
    """Generate 3D model from image using Tripo API"""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        iteration = data.get('iteration')
        target_object = data.get('targetObject')
        image_url = data.get('imageUrl')
        
        if not all([session_id, iteration, target_object, image_url]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Check if session exists
        if session_id not in active_sessions:
            return jsonify({"error": "Session not found"}), 404
        
        # Get image data (handle both local files and URLs)
        try:
            if image_url.startswith("file://"):
                # Handle local file
                file_path = image_url.replace("file://", "")
                with open(file_path, 'rb') as f:
                    image_data = f.read()
            else:
                # Handle HTTP URL
                import requests
                response = requests.get(image_url, timeout=30)
                if response.status_code != 200:
                    return jsonify({"error": "Failed to download image"}), 400
                image_data = response.content
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return jsonify({"error": "Failed to read image"}), 400
        
        # Upload to Supabase
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{target_object.replace(' ', '_')}_{iteration}_{timestamp}.png"
        
        supabase_url = upload_image_to_supabase(image_data, filename)
        if not supabase_url:
            return jsonify({"error": "Failed to upload image to Supabase"}), 500
        
        # Insert record into database
        record_id = insert_image_record(target_object, supabase_url, iteration)
        if not record_id:
            return jsonify({"error": "Failed to insert database record"}), 500
        
        # Generate 3D model using Tripo API
        try:
            # Import the Tripo functions
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            
            from test_tripo_multiview_to_3d import create_multiview_task, get_task, download, crop_multiview_image
            
            # Load the image and crop it into 4 views
            from PIL import Image
            import io
            
            # Load the image
            image = Image.open(io.BytesIO(image_data))
            
            # Crop the image into 4 views (front, right, left, back)
            views = crop_multiview_image(image)
            
            # Submit to Tripo API
            task_id = create_multiview_task(views)
            
            # Poll for completion
            max_attempts = 60  # 10 minutes with 10-second intervals
            for attempt in range(max_attempts):
                info = get_task(task_id)
                if info.get("code") != 0:
                    return jsonify({"error": f"Tripo API error: {info}"}), 500
                
                status = info["data"]["status"]
                if status in ("success", "succeeded", "SUCCESS"):
                    out = info["data"]["output"]
                    model_url = out.get("pbr_model") or out.get("model")
                    if model_url:
                        # Download the model
                        model_filename = f"tripo_model_{session_id}_{iteration}.glb"
                        model_path = download(model_url, model_filename)
                        
                        # Upload GLB file to Supabase 3D files bucket
                        glb_supabase_url = None
                        if SUPABASE_AVAILABLE and supabase_client:
                            try:
                                # Read the downloaded GLB file
                                with open(model_path, 'rb') as f:
                                    glb_data = f.read()
                                
                                # Upload to Supabase 3D files bucket
                                glb_filename = f"{target_object.replace(' ', '_')}_{iteration}_{timestamp}.glb"
                                glb_supabase_url = upload_image_to_supabase(
                                    glb_data, 
                                    glb_filename, 
                                    content_type="model/gltf-binary",
                                    bucket_name="generated-3d-files"
                                )
                                
                                if glb_supabase_url:
                                    # Update the database record with Supabase 3D model URL
                                    supabase_client.table('generated_images').update({
                                        "3d_url": glb_supabase_url
                                    }).eq('id', record_id).execute()
                                    logger.info(f"✅ Uploaded GLB to Supabase: {glb_supabase_url}")
                                else:
                                    logger.error("❌ Failed to upload GLB to Supabase")
                                    
                            except Exception as e:
                                logger.error(f"Error uploading GLB to Supabase: {e}")
                        
                        # Clean up local file
                        try:
                            os.remove(model_path)
                        except:
                            pass
                        
                        return jsonify({
                            "success": True,
                            "model_url": glb_supabase_url or model_path,
                            "supabase_record_id": record_id
                        })
                    else:
                        return jsonify({"error": "No model URL in Tripo response"}), 500
                elif status in ("failed", "error"):
                    return jsonify({"error": f"Tripo task failed: {info}"}), 500
                
                import time
                time.sleep(10)  # Wait 10 seconds before next poll
            
            return jsonify({"error": "Timeout waiting for 3D generation"}), 408
            
        except Exception as e:
            logger.error(f"Error generating 3D model: {e}")
            return jsonify({"error": f"3D generation failed: {str(e)}"}), 500
        
    except Exception as e:
        logger.error(f"Error in generate-3d endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    })

# Studio API Routes (Supabase only)

@app.route('/api/studio/supabase/images')
def list_supabase_studio_images():
    """List images from Supabase storage using the generated_images table"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        # Get query parameters
        max_results = int(request.args.get('max_results', 100))
        search_query = request.args.get('search', '')
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Search or list images
        if search_query:
            result = supabase_manager.search_images(search_query, max_results)
        else:
            result = supabase_manager.list_public_images(max_results=max_results)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "images": result["images"],
                "total_count": result["total_count"],
                "search_query": search_query if search_query else None
            })
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error listing Supabase studio images: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/studio/supabase/images/<int:image_id>')
def get_supabase_studio_image_metadata(image_id):
    """Get metadata for a specific Supabase studio image by ID"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Get image metadata
        result = supabase_manager.get_image_metadata(image_id=image_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "metadata": result["metadata"]
            })
        else:
            return jsonify({"error": result["error"]}), 404
            
    except Exception as e:
        logger.error(f"Error getting Supabase studio image metadata: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/studio/supabase/images/insert', methods=['POST'])
def insert_supabase_studio_image():
    """Insert a new image record into the generated_images table"""
    try:
        if not SUPABASE_STUDIO_AVAILABLE:
            return jsonify({"error": "Supabase Studio functionality not available"}), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        target_object = data.get('target_object')
        image_url = data.get('image_url')
        model_3d_url = data.get('model_3d_url')
        iteration = data.get('iteration')
        
        if not target_object or not image_url:
            return jsonify({"error": "target_object and image_url are required"}), 400
        
        # Create Supabase studio manager
        supabase_manager = create_supabase_studio_manager()
        
        # Initialize the manager
        init_result = supabase_manager.initialize()
        if not init_result["success"]:
            return jsonify({"error": f"Supabase initialization failed: {init_result['error']}"}), 503
        
        # Insert image
        result = supabase_manager.insert_image(
            target_object=target_object,
            image_url=image_url,
            model_3d_url=model_3d_url,
            iteration=iteration
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "inserted_id": result["inserted_id"],
                "record": result["record"]
            })
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        logger.error(f"Error inserting Supabase studio image: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/studio/proxy-file')
def proxy_file():
    """Proxy any file download to bypass CORS restrictions"""
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({"error": "URL parameter is required"}), 400
        
        logger.info(f"🔗 Proxying file from: {url}")
        
        # Import requests for making HTTP requests
        import requests
        
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Determine content type based on file extension
        content_type = 'application/octet-stream'  # Default
        if url.lower().endswith('.glb'):
            content_type = 'model/gltf-binary'
        elif url.lower().endswith('.gltf'):
            content_type = 'model/gltf+json'
        elif url.lower().endswith('.zip'):
            content_type = 'application/zip'
        elif url.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif url.lower().endswith('.png'):
            content_type = 'image/png'
        
        # Return the file content with appropriate headers
        return Response(
            response.content,
            mimetype=content_type,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'Content-Length': str(len(response.content))
            }
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file from {url}: {e}")
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error proxying file: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # For production deployment on EC2
    app.run(debug=False, host='0.0.0.0', port=8001) 