#!/usr/bin/env python3
"""
Multi agent to generate 3D reconstruction models
"""

from flask import Flask, request, jsonify, render_template, send_file
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
import tempfile
import aiohttp

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

# Store active sessions (in production, use a proper database)
active_sessions = {}

# OpenAI clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

async def download_image_to_pil(image_url: str) -> Optional[Image.Image]:
    """Download image from URL or load from file and convert to PIL Image"""
    try:
        if image_url.startswith("file://"):
            # Handle local file
            file_path = image_url.replace("file://", "")
            return Image.open(file_path)
        else:
            # Handle HTTP URL
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        return Image.open(io.BytesIO(image_data))
                    else:
                        print(f"Failed to download image from {image_url}: {response.status}")
                        return None
    except Exception as e:
        print(f"Error loading image from {image_url}: {e}")
        return None

async def generate_multiview_with_gpt_image1(target_object: str, iteration: int = 1, previous_feedback: List[str] = None, previous_image_url: str = None) -> str:
    """Generate 4x4 multiview image using GPT-Image-1 with image-to-image capability"""
    
    # Create the generation instructions
    instructions = f"""Your task is to generate 16 views of the same object that can be used for 3D reconstruction for the target object: {target_object}. Each view should be aligned in size. Make sure the 16 views are diverse and cover different angles and perspectives of the object.

CRITICAL OBJECT CONSISTENCY REQUIREMENTS (MOST IMPORTANT):
- EXACT same object type across ALL 16 views (e.g., if it's a Golden Retriever, ALL 16 views must show Golden Retrievers)
- EXACT same color, texture, and material across ALL 16 views
- EXACT same size and proportions across ALL 16 views
- EXACT same pose/position of the object across ALL 16 views
- NO variations in object appearance, shape, or characteristics
- NO different objects in different grid positions
- NO mixed object types (e.g., some Golden Retrievers, some other dog breeds)

OBJECT CONSISTENCY IS THE MOST CRITICAL FACTOR FOR 3D RECONSTRUCTION. FAILURE TO MAINTAIN CONSISTENCY WILL RESULT IN POOR RECONSTRUCTION QUALITY."""

    # Add feedback from previous iterations
    feedback_text = " ".join(previous_feedback) if previous_feedback else "No specific feedback available"
    if previous_feedback:
        if iteration > 1:
            instructions += f" IMPORTANT: Based on the previous image, address these specific issues: {feedback_text}. Maintain the good aspects while fixing the problems identified."
        else:
            instructions += f" IMPORTANT: Address these specific issues from previous iteration: {feedback_text}"
    
    try:
        # For first iteration - text to image
        if iteration == 1 or not previous_image_url:
            print(f"🎨 Generating initial image for '{target_object}' (iteration {iteration})...")
            response = await asyncio.to_thread(
                openai_sync_client.images.generate,
                model="gpt-image-1",
                prompt=instructions,
                size="1024x1024",
            )
        else:
            # For subsequent iterations - image edit with feedback
            print(f"🎨 Editing previous image with feedback for '{target_object}' (iteration {iteration})...")
            
            # Download previous image
            previous_image = await download_image_to_pil(previous_image_url)
            if not previous_image:
                print(f"❌ Failed to load previous image, falling back to text generation")
                response = await asyncio.to_thread(
                    openai_sync_client.images.generate,
                    model="gpt-image-1",
                    prompt=instructions,
                    size="1024x1024",
                )
            else:
                # Create edit instructions based on feedback
                edit_instructions = f"""Improve this 4x4 multiview image of {target_object} by addressing these specific issues: {feedback_text}. Maintain the overall structure and good aspects while fixing the identified problems.

CRITICAL: Ensure EXACT object consistency across ALL 16 views:
- Same object type, color, texture, size, and proportions
- NO variations in object appearance or characteristics
- NO mixed object types or different objects

OBJECT CONSISTENCY IS THE MOST CRITICAL FACTOR FOR 3D RECONSTRUCTION."""
                
                # Save PIL image to temporary file
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
                    response = await asyncio.to_thread(
                        openai_sync_client.images.edit,
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
                return image_url
            elif hasattr(first_item, 'b64_json') and first_item.b64_json:
                # Handle base64 data
                # Decode base64 and save to temporary file
                try:
                    # Decode base64 data
                    image_data = base64.b64decode(first_item.b64_json)
                    
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    return f"file://{temp_file.name}"
                except Exception as e:
                    print(f"❌ Error handling base64 data: {e}")
                    return None
            else:
                print(f"❌ Unexpected response format: {first_item}")
                return None
        else:
            print(f"❌ No image data in response: {response}")
            return None
        
    except Exception as e:
        print(f"❌ Error generating with GPT-4 Vision: {e}")
        return None

async def evaluate_image_with_gpt4v(image_url: str, target_object: str, iteration: int) -> Dict:
    """Evaluate generated image using GPT-4 Vision"""
    
    evaluation_prompt = f"""Analyze this 4x4 multiview grid image of a {target_object} for 3D reconstruction suitability.

    EVALUATION CRITERIA:
    1. Image Quality (1-10): Clarity, resolution, lighting, focus
    2. Grid Structure (1-10): How well the 4x4 grid layout works
    3. Angle Diversity (1-10): How many different viewing angles are shown
    4. Object Consistency (1-10): Same object appearance across all views
    5. Background Cleanliness (1-10): Pure white background
    6. 3D Reconstruction Suitability (1-10): Overall suitability for 3D reconstruction

    OBJECT CONSISTENCY CHECK:
    - Are all 16 objects the same type? (e.g., all Golden Retrievers)
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
            # Download and encode the image
            image = await download_image_to_pil(image_url)
            if not image:
                raise Exception("Failed to download image")
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Call GPT-4 Vision API
            response = await openai_client.chat.completions.create(
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
            print(f"🔍 Raw evaluation text for iteration {iteration}:")
            print(f"   {evaluation_text}")
            
            # Check if the response indicates failure
            if "I'm sorry" in evaluation_text or "I can't assist" in evaluation_text:
                raise Exception("Evaluation agent refused to process the request")
            
            # Parse the evaluation
            parsed_results = parse_evaluation_text(evaluation_text)
            
            # Apply penalties if needed
            parsed_results = apply_object_consistency_penalties(parsed_results, evaluation_text)
            
            return parsed_results
            
        except Exception as e:
            print(f"❌ Evaluation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying evaluation... (attempt {attempt + 2}/{max_retries})")
                await asyncio.sleep(2)  # Wait before retry
            else:
                print(f"❌ All evaluation attempts failed, using fallback scores")
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
    print(f"🔍 Starting to parse evaluation text...")
    print(f"   Text length: {len(text)} characters")
    
    lines = text.split('\n')
    print(f"   Number of lines: {len(lines)}")
    
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
                        print(f"   ✅ Extracted score: {metric} = {score}")
                    except ValueError:
                        print(f"   ❌ Could not parse score from: {line}")
        
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
                    print(f"   ✅ Extracted issue: {issue}")
            elif line and not line.startswith('Specific Issues Found:'):
                issues.append(line)
                print(f"   ✅ Extracted issue: {line}")
        
        # Extract suggestions
        if in_suggestions and line:
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                suggestion = line[1:].strip()
                if suggestion:  # Only add non-empty suggestions
                    suggestions.append(suggestion)
                    print(f"   ✅ Extracted suggestion: {suggestion}")
            elif line and not line.startswith('Suggestions for Improvement:'):
                suggestions.append(line)
                print(f"   ✅ Extracted suggestion: {line}")
    
    # Calculate overall score if not present
    if 'Overall Score' not in scores and scores:
        overall_score = sum(scores.values()) / len(scores)
        scores['overall'] = overall_score
        print(f"   📊 Calculated overall score: {overall_score}")
    
    print(f"📋 Parsed evaluation results:")
    print(f"   Parsed scores: {scores}")
    print(f"   Parsed issues: {issues}")
    print(f"   Parsed suggestions: {suggestions}")
    
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
                print(f"🔍 Applied conservative penalty: High score but issues mentioned")
        
        # Apply penalty (minimum score of 1)
        new_score = max(1, original_score - total_penalty)
        scores["Object Consistency"] = new_score
        
        # Recalculate overall score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
            scores["overall"] = overall_score
        
        print(f"🔍 Applied object consistency penalties:")
        print(f"   Original Object Consistency score: {original_score}")
        print(f"   Total penalty: {total_penalty}")
        print(f"   New Object Consistency score: {new_score}")
        print(f"   New overall score: {overall_score}")
    
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

async def save_metadata(session_id: str, iteration: int, target_object: str, image_url: str, evaluation_results: Dict) -> str:
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
        "evaluation_model": "gpt-4o"
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata_data, f, indent=2)
    
    return str(metadata_file)

async def run_hybrid_multiview_generation(session_id: str, target_object: str) -> Dict:
    """Run iterative hybrid multiview generation"""
    
    session_id = session_id
    previous_feedback = []
    previous_image_url = None
    all_results = []
    iteration = 0
    
    # Initialize session
    active_sessions[session_id] = {
        "status": "running",
        "target_object": target_object,
        "current_iteration": 0,
        "iterations": [],
        "final_score": 0
    }
    
    while True:
        iteration += 1
        
        # Add maximum iteration limit to prevent infinite loops
        if iteration > 15:  # Allow up to 15 iterations for improvement
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["final_score"] = scores.get("overall", 0) if 'scores' in locals() else 0
            active_sessions[session_id]["message"] = "Reached maximum iterations (15) - best result achieved"
            break
        
        # Update session status
        active_sessions[session_id]["current_iteration"] = iteration
        
        # Generate image with GPT-Image-1 (image-to-image for iterations > 1)
        image_url = await generate_multiview_with_gpt_image1(target_object, iteration, previous_feedback, previous_image_url)
        
        if not image_url:
            active_sessions[session_id]["status"] = "failed"
            active_sessions[session_id]["error"] = "Failed to generate image"
            break
        
        # Evaluate image with GPT-4 Vision
        evaluation_results = await evaluate_image_with_gpt4v(image_url, target_object, iteration)
        
        # Save metadata
        metadata_file = await save_metadata(session_id, iteration, target_object, image_url, evaluation_results)
        
        # Store results
        iteration_result = {
            "iteration": iteration,
            "image_url": image_url,
            "evaluation": evaluation_results,
            "metadata_file": metadata_file
        }
        all_results.append(iteration_result)
        
        # Update session with iteration data
        active_sessions[session_id]["iterations"].append(iteration_result)
        
        # Check if quality threshold is met
        scores = evaluation_results.get("scores", {})
        if meets_quality_threshold(scores):
            active_sessions[session_id]["status"] = "completed"
            active_sessions[session_id]["final_score"] = scores.get("overall", 0)
            break
        
        # Store current image URL for next iteration
        previous_image_url = image_url
        print(f"📸 Stored image URL for iteration {iteration}: {image_url[:50]}...")
        
        # Prepare feedback for next iteration
        previous_feedback = evaluation_results.get("suggestions", [])
        scores = evaluation_results.get("scores", {})
        issues = evaluation_results.get("issues", [])
        
        print(f"📊 Iteration {iteration} Evaluation Results:")
        print(f"   Scores: {scores}")
        print(f"   Issues Found: {issues}")
        print(f"   Suggestions for Improvement: {previous_feedback}")
        print(f"   Overall Score: {scores.get('overall', 'N/A')}/10")
        
        # Add a small delay between iterations
        await asyncio.sleep(1)
    
    return {
        "session_id": session_id,
        "target_object": target_object,
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
        
        if not target_object:
            return jsonify({"error": "Target object is required"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Start generation in background
        def run_generation():
            asyncio.run(run_hybrid_multiview_generation(session_id, target_object))
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=run_generation)
        thread.start()
        
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "message": f"Started iterative generation for: {target_object}"
        })
        
    except Exception as e:
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
            "current_iteration": session["current_iteration"],
            "iterations": session["iterations"],
            "final_score": session["final_score"],
            "error": session.get("error", None)
        })
        
    except Exception as e:
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
        
        if image_url.startswith("file://"):
            file_path = image_url.replace("file://", "")
            return send_file(file_path, mimetype='image/png')
        else:
            return jsonify({"error": "Image not accessible"}), 404
            
    except Exception as e:
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
                "current_iteration": session_data["current_iteration"],
                "final_score": session_data["final_score"]
            })
        
        return jsonify({"sessions": sessions})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080) 