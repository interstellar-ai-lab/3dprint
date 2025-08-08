#!/usr/bin/env python3
"""
Multi agent to generate 3D images - Flask Web App for EC2 Deployment
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import json
import os
import sys
import uuid
import pathlib
from datetime import datetime
from typing import Optional, Dict, Any, List
import base64
from PIL import Image
import io
from openai import OpenAI, AsyncOpenAI
import threading
import logging

# GCP Storage imports
try:
    from google.cloud import storage
    from google.oauth2 import credentials as user_credentials
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    logger.warning("Google Cloud Storage library not installed. Install with: pip install google-cloud-storage")
    GCP_AVAILABLE = False

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import studio module
from studio_module import studio_bp, init_studio_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webapp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Register studio blueprint
app.register_blueprint(studio_bp)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8001", "http://127.0.0.1:8001", "https://vicino.ai", "https://www.vicino.ai", "https://vicino.ai:8001", "https://vicino.ai:443", "http://vicino.ai", "http://www.vicino.ai", "http://vicino.ai:8001"],
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

# GCP Storage configuration
GCP_BUCKET_NAME = "vicino.ai"
GCP_PROJECT_ID = "fabled-pivot-468319-q2"  # Your GCP project ID
GCP_CREDENTIALS_PATH = "/Users/Interstellar/.config/gcloud/application_default_credentials.json"
gcp_storage_client = None

def initialize_gcp_storage():
    """Initialize GCP Storage client"""
    global gcp_storage_client
    
    if not GCP_AVAILABLE:
        logger.warning("GCP Storage not available - skipping GCS uploads")
        return False
    
    try:
        if os.path.exists(GCP_CREDENTIALS_PATH):
            # Load credentials from the default credentials file
            with open(GCP_CREDENTIALS_PATH, 'r') as f:
                cred_data = json.load(f)
            
            if 'type' in cred_data and cred_data['type'] == 'service_account':
                # Service account JSON file
                credentials = service_account.Credentials.from_service_account_file(GCP_CREDENTIALS_PATH)
            else:
                # Default credentials file (user credentials)
                credentials = user_credentials.Credentials.from_authorized_user_file(GCP_CREDENTIALS_PATH)
            
            # Initialize client with project ID
            gcp_storage_client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
            logger.info(f"✅ GCP Storage client initialized successfully for project: {GCP_PROJECT_ID}")
            return True
        else:
            logger.warning(f"GCP credentials file not found: {GCP_CREDENTIALS_PATH}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to initialize GCP Storage client: {e}")
        return False

def upload_to_gcs(local_file_path: str, gcs_path: str) -> Optional[str]:
    """Upload a file to Google Cloud Storage"""
    if not gcp_storage_client:
        logger.warning("GCP Storage client not initialized - skipping upload")
        return None
    
    try:
        # Remove file:// prefix if present
        clean_local_path = local_file_path.replace("file://", "")
        
        if not os.path.exists(clean_local_path):
            logger.error(f"Local file does not exist: {clean_local_path}")
            return None
        
        bucket = gcp_storage_client.bucket(GCP_BUCKET_NAME)
        blob = bucket.blob(gcs_path)
        
        # Upload the file
        blob.upload_from_filename(clean_local_path)
        
        # Note: Don't call make_public() for uniform bucket-level access
        # The bucket should be configured to allow public read access
        
        # Return the public HTTPS URL (assuming bucket is configured for public access)
        gcs_url = f"https://storage.googleapis.com/{GCP_BUCKET_NAME}/{gcs_path}"
        logger.info(f"✅ File uploaded to GCS: {gcs_url}")
        return gcs_url
        
    except Exception as e:
        logger.error(f"❌ Failed to upload file to GCS: {e}")
        return None

def load_png_image(image_path: str) -> Optional[Image.Image]:
    """Load PNG image from local file path"""
    try:
        # All paths start with file://, so just remove the prefix
        file_path = image_path.replace("file://", "")
        return Image.open(file_path)
    except Exception as e:
        logger.error(f"Error loading PNG image from {image_path}: {e}")
        return None

def generate_multiview_with_gpt_image1(target_object: str, iteration: int = 1, previous_feedback: List[str] = None, previous_image_path: str = None) -> str:
    """Generate 2x2 multiview image using GPT-Image-1 with image-to-image capability. Returns local file path."""
    
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
        logger.info(f"🔍 Debug: iteration={iteration}, previous_image_path={'None' if previous_image_path is None else 'exists'}")
        
        # For first iteration - text to image
        if iteration == 1 or not previous_image_path:
            logger.info(f"🎨 Generating initial image for '{target_object}' (iteration {iteration})...")
            response = openai_sync_client.images.generate(
                model="gpt-image-1",
                prompt=instructions,
                size="1024x1024",
            )
        else:
            # For subsequent iterations - image edit with feedback
            logger.info(f"🎨 Editing previous image with feedback for '{target_object}' (iteration {iteration})...")
            
            # Load previous PNG image
            previous_image = load_png_image(previous_image_path)
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
            # Handle base64 data from gpt-image-1
            first_item = response.data[0]
            if hasattr(first_item, 'b64_json') and first_item.b64_json:
                # Handle base64 data - save to PNG file
                try:
                    # Decode base64 data
                    image_data = base64.b64decode(first_item.b64_json)
                    
                    # Create temporary file
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    local_image_path = f"file://{temp_file.name}"
                    return local_image_path
                except Exception as e:
                    logger.error(f"❌ Error handling base64 data: {e}")
                    return None
            else:
                logger.error(f"❌ No base64 data in response")
                return None
        else:
            logger.error(f"❌ No image data in response")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error generating with GPT-4 Vision: {e}")
        return None

def evaluate_image_with_gpt4v(local_image_path: str, target_object: str, iteration: int) -> Dict:
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
            # Load PNG image and convert to base64
            image = load_png_image(local_image_path)
            if not image:
                raise Exception("Failed to load PNG image")
            
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

def save_metadata(session_id: str, iteration: int, target_object: str, local_image_path: str, evaluation_results: Dict, mode: str = "quick") -> str:
    """Save metadata for this iteration and upload image to GCS"""
    session_dir = pathlib.Path(f"generated_images/session_{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate GCS path for the image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gcs_image_path = f"generated_images/session_{session_id}/iteration_{iteration:02d}_{timestamp}.png"
    
    # Upload image to GCS
    gcs_url = upload_to_gcs(local_image_path, gcs_image_path)
    # Construct gsutil URI (requested naming)
    gsutil_uri = f"gs://{GCP_BUCKET_NAME}/{gcs_image_path}"
    
    metadata_file = session_dir / f"metadata_iteration_{iteration:02d}.json"
    metadata_data = {
        "session_id": session_id,
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "target_object": target_object,
        "local_image_path": local_image_path,
        # Canonical object path (kept for internal use and backwards compatibility)
        "gcs_image_path": gcs_image_path,
        # Legacy public URL field (kept for backwards compatibility)
        "gcs_url": gcs_url,
        # New names requested
        "public_url": gcs_url,
        "gsutil_uri": gsutil_uri,
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
    previous_image_path = None
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
        local_image_path = generate_multiview_with_gpt_image1(target_object, iteration, previous_feedback, previous_image_path)
        
        if not local_image_path:
            active_sessions[session_id]["status"] = "failed"
            active_sessions[session_id]["error"] = "Failed to generate image"
            break
        
        # IMMEDIATELY add the image to session (before evaluation)
        iteration_result = {
            "iteration": iteration,
            "local_image_path": local_image_path,
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
        evaluation_results = evaluate_image_with_gpt4v(local_image_path, target_object, iteration)
        
        # Save metadata
        metadata_file = save_metadata(session_id, iteration, target_object, local_image_path, evaluation_results, mode)
        
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
        
        # Store current image path for next iteration
        previous_image_path = local_image_path
        
        # Print image path info without cluttering the console
        if local_image_path.startswith('data:image/'):
            logger.info(f"📸 Stored base64 image for iteration {iteration}")
        elif local_image_path.startswith('http'):
            logger.info(f"📸 Stored remote image URL for iteration {iteration}: {local_image_path[:50]}...")
        else:
            logger.info(f"📸 Stored local image for iteration {iteration}")
        
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



@app.route('/models/<path:filename>')
def serve_model(filename):
    """Serve 3D model files"""
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'downloads', '3d_model_test')
    file_path = os.path.join(model_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    # Set appropriate MIME types
    mime_types = {
        '.obj': 'text/plain',
        '.mtl': 'text/plain',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg'
    }
    
    file_ext = os.path.splitext(filename)[1].lower()
    mime_type = mime_types.get(file_ext, 'application/octet-stream')
    
    return send_file(file_path, mimetype=mime_type)

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
        
        # Add GCS URLs to iterations if available
        iterations_with_gcs = []
        for iteration_data in session["iterations"]:
            iteration_with_gcs = iteration_data.copy()
            
            # Try to get GCS URL from metadata
            if "metadata_file" in iteration_data and iteration_data["metadata_file"]:
                try:
                    with open(iteration_data["metadata_file"], 'r') as f:
                        metadata = json.load(f)
                        iteration_with_gcs["gcs_url"] = metadata.get("gcs_url")
                        iteration_with_gcs["gcs_image_path"] = metadata.get("gcs_image_path")
                except Exception as e:
                    logger.warning(f"Could not read metadata file for iteration: {e}")
            
            iterations_with_gcs.append(iteration_with_gcs)
        
        return jsonify({
            "session_id": session_id,
            "status": session["status"],
            "target_object": session["target_object"],
            "mode": session["mode"],
            "max_iterations": session["max_iterations"],
            "current_iteration": session["current_iteration"],
            "iterations": iterations_with_gcs,
            "final_score": session["final_score"],
            "error": session.get("error", None),
            "evaluation_status": session.get("evaluation_status", None)
        })
        
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500





@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    })

if __name__ == '__main__':
    # Initialize GCP Storage
    logger.info("🔧 Initializing GCP Storage...")
    gcp_initialized = initialize_gcp_storage()
    if gcp_initialized:
        logger.info("✅ GCP Storage initialized successfully")
    else:
        logger.warning("⚠️  GCP Storage initialization failed - uploads will be skipped")
    
    # Initialize studio module with GCP client
    init_studio_module(gcp_storage_client, GCP_BUCKET_NAME)
    logger.info("✅ Studio module initialized")
    
    # For production deployment on EC2
    app.run(debug=False, host='0.0.0.0', port=8001) 