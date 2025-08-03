from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import json
import os
import sys
import uuid
import pathlib
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
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

# Simplified implementations of functions that were imported from multiagent
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

async def generate_with_openai(prompt: str) -> str:
    """Generate text using OpenAI GPT-4"""
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates image prompts and metadata for 3D reconstruction."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating with OpenAI: {e}")
        return ""

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

def apply_scoring_penalties(evaluation_results: Dict, iteration: int, evaluation_text: str) -> Dict:
    """Apply scoring penalties for common issues, especially in early iterations"""
    scores = evaluation_results.get('scores', {})
    if not scores:
        return evaluation_results
    
    # Make a copy to avoid modifying the original
    new_scores = scores.copy()
    penalties_applied = []
    
    # First iteration penalties (more strict)
    if iteration == 1:
        # Penalty for first iteration - typically not perfect
        for key in new_scores:
            if new_scores[key] > 6:
                penalty = 2
                new_scores[key] = max(1, new_scores[key] - penalty)
                penalties_applied.append(f"First iteration penalty: -{penalty} points")
        
        # Additional penalties for common first iteration issues
        text_lower = evaluation_text.lower()
        
        # Penalty for grid issues
        if any(issue in text_lower for issue in ["grid", "layout", "arrangement", "4x4"]):
            for key in new_scores:
                penalty = 1
                new_scores[key] = max(1, new_scores[key] - penalty)
            penalties_applied.append("Grid layout issues: -1 point each")
        
        # Penalty for lighting issues
        if any(issue in text_lower for issue in ["lighting", "brightness", "shadow", "dark", "light"]):
            new_scores["image_quality"] = max(1, new_scores["image_quality"] - 1)
            penalties_applied.append("Lighting issues: -1 point image quality")
        
        # Penalty for angle issues
        if any(issue in text_lower for issue in ["angle", "view", "perspective", "position"]):
            new_scores["completeness"] = max(1, new_scores["completeness"] - 1)
            penalties_applied.append("Angle/view issues: -1 point completeness")
        
        # Penalty for background issues
        if any(issue in text_lower for issue in ["background", "clean", "white", "neutral"]):
            new_scores["image_quality"] = max(1, new_scores["image_quality"] - 1)
            penalties_applied.append("Background issues: -1 point image quality")
    
    # General penalties for all iterations
    text_lower = evaluation_text.lower()
    
    # Penalty for any mention of "improve" or "better" - indicates issues
    if any(word in text_lower for word in ["improve", "better", "enhance", "fix", "adjust"]):
        for key in new_scores:
            if new_scores[key] > 7:
                penalty = 1
                new_scores[key] = max(1, new_scores[key] - penalty)
        penalties_applied.append("Improvement suggestions found: -1 point each for scores >7")
    
    # Penalty for quality issues
    if any(issue in text_lower for issue in ["blur", "artifact", "noise", "compression", "quality"]):
        new_scores["image_quality"] = max(1, new_scores["image_quality"] - 2)
        penalties_applied.append("Quality issues: -2 points image quality")
    
    # Update the evaluation results
    evaluation_results["scores"] = new_scores
    
    # Add penalty information to suggestions
    if penalties_applied:
        penalty_text = f"Scoring penalties applied: {'; '.join(penalties_applied)}"
        current_suggestions = evaluation_results.get("suggestions_for_improvement", "")
        evaluation_results["suggestions_for_improvement"] = f"{penalty_text}. {current_suggestions}"
    
    return evaluation_results

def meets_quality_threshold(scores: Dict) -> bool:
    """Check if the scores meet the quality threshold for stopping iterations"""
    if not scores:
        return False
    # Check if average score is 9.0 or higher and no score is below 8.0
    avg_score = sum(scores.values()) / len(scores)
    min_score = min(scores.values())
    return avg_score >= 9.0 and min_score >= 8.0

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
    suggestions_section = False
    suggestions_lines = []
    metadata_section = False
    metadata_lines = []
    
    for line in lines:
        line_lower = line.lower()
        
        # Check for section headers
        if "suggestions for improvement:" in line_lower:
            suggestions_section = True
            metadata_section = False
            continue
        elif "metadata suggestions:" in line_lower:
            metadata_section = True
            suggestions_section = False
            continue
        elif any(keyword in line_lower for keyword in ["image quality:", "metadata accuracy:", "completeness:"]):
            suggestions_section = False
            metadata_section = False
            continue
        
        # Collect content for each section
        if suggestions_section and line.strip() and not line.strip().startswith('[') and not line.strip().endswith(']'):
            suggestions_lines.append(line.strip())
        elif metadata_section and line.strip() and not line.strip().startswith('[') and not line.strip().endswith(']'):
            metadata_lines.append(line.strip())
    
    # Set the suggestions
    if suggestions_lines:
        result["suggestions_for_improvement"] = " ".join(suggestions_lines)
    else:
        # Fallback: look for any lines with improvement-related keywords
        improvement_lines = []
        for line in lines:
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in failure_indicators):
                improvement_lines.append(line.strip())
            elif any(keyword in line_lower for keyword in ["improve", "better", "enhance", "fix", "adjust", "change"]):
                improvement_lines.append(line.strip())
        
        if improvement_lines:
            result["suggestions_for_improvement"] = " ".join(improvement_lines)
        else:
            result["suggestions_for_improvement"] = "Continue improving the generation"
    
    # Set the metadata suggestions
    if metadata_lines:
        result["metadata_suggestions"] = " ".join(metadata_lines)
    else:
        # Fallback: look for metadata-related suggestions
        metadata_improvement_lines = []
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["prompt", "metadata", "description", "specification"]):
                metadata_improvement_lines.append(line.strip())
        
        if metadata_improvement_lines:
            result["metadata_suggestions"] = " ".join(metadata_improvement_lines)
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

@app.route('/')
def home():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """Handle generation requests"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session data
        active_sessions[session_id] = {
            "session_id": session_id,
            "query": query,
            "status": "starting",
            "current_iteration": 0,
            "metadata_files": [],
            "image_urls": [],
            "evaluation_history": [],
            "error": None
        }
        
        # Start the generation process in the background
        import threading
        
        def run_generation():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_generation_loop(session_id, query))
            finally:
                loop.close()
        
        # Start the generation in a background thread
        thread = threading.Thread(target=run_generation)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'session_id': session_id,
            'status': 'starting',
            'message': 'Generation started successfully',
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """Get status of a generation session"""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = active_sessions[session_id]
    
    return jsonify({
        'session_id': session_id,
        'status': session_data['status'],
        'query': session_data['query'],
        'current_iteration': session_data['current_iteration'],
        'metadata_files': session_data['metadata_files'],
        'image_urls': session_data['image_urls'],
        'evaluation_history': session_data['evaluation_history'],
        'error': session_data.get('error')
    })

@app.route('/api/metadata/<session_id>/<int:iteration>')
def get_iteration_metadata(session_id, iteration):
    """Get detailed metadata for a specific iteration"""
    metadata_file = pathlib.Path(f"generated_images/session_{session_id}/metadata_iteration_{iteration:02d}.json")
    if not metadata_file.exists():
        return jsonify({'error': 'Metadata not found'}), 404
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    return jsonify(metadata)

@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    return jsonify({
        'sessions': [
            {
                'session_id': session_id,
                'status': data['status'],
                'query': data['query'],
                'current_iteration': data['current_iteration']
            }
            for session_id, data in active_sessions.items()
        ]
    })

async def run_generation_loop(session_id: str, query: str):
    """Run the enhanced iterative generation and evaluation loop with metadata integration"""
    print(f"🚀 Starting enhanced generation loop for: {query}")
    
    iteration = 1
    
    try:
        while True:
            print(f"\n🔄 Iteration {iteration}")
            print("-" * 50)
            
            # Load previous metadata for iterative feedback
            previous_metadata = load_previous_metadata(session_id, iteration)
            
            # Prepare context for generation
            previous_metadata_context = ""
            previous_metadata_json = "null"
            
            if previous_metadata:
                previous_scores = previous_metadata.get('evaluation_results', {}).get('scores', {})
                previous_suggestions = previous_metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '')
                previous_metadata_suggestions = previous_metadata.get('evaluation_results', {}).get('metadata_suggestions', '')
                
                previous_metadata_context = f"""
                CRITICAL: Previous iteration had these scores: {previous_scores}
                
                Previous improvement suggestions: {previous_suggestions}
                Previous metadata suggestions: {previous_metadata_suggestions}
                
                You MUST address these specific issues in your new generation. The previous iteration was not good enough and needs significant improvement.
                """
                previous_metadata_json = json.dumps({
                    "previous_scores": previous_scores,
                    "previous_suggestions": previous_suggestions,
                    "previous_metadata_suggestions": previous_metadata_suggestions
                })
            
            print("📝 Generating image prompt and metadata...")
            
            # Generate new metadata and image prompt using the enhanced generation prompt
            generation_prompt = f"""
Your task is to generate ONE image containing 16 different views of the object that can be used for 3D reconstruction for the target object: {query}. 

{previous_metadata_context}

CRITICAL REQUIREMENTS:
1. You MUST address every specific issue mentioned in the previous feedback
2. The previous iteration was not good enough - you need to make significant improvements
3. Be extremely specific in your image prompt to avoid the problems from the previous iteration
4. Focus on the exact issues mentioned in the previous suggestions

Create a detailed, specific prompt for DALL-E 3 that will generate a 4x4 grid of 16 views of the object. The prompt should be comprehensive and specifically address the issues from previous iterations.

Base prompt structure (ENHANCE THIS BASED ON PREVIOUS FEEDBACK):
"A set of sixteen digital photographs arranged in a 4x4 grid featuring a {query} captured from different angles. Each sub-image shows the {query} from a distinct viewpoint: front, back, left, right, top, bottom, and various oblique angles. The {query} is centered in each view, with consistent lighting, scale, and positioning. The background is pure white with no shadows or other objects, suitable for 3D reconstruction."

Return your response in this JSON format:
{{
    "target_object": "{query}",
    "generation_metadata": "Detailed description of the object and the 16 views for 3D reconstruction, including specific angle descriptions, lighting specifications, material properties, and geometric constraints. MUST address the specific issues from previous feedback: {previous_metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '') if previous_metadata else 'No previous feedback'}",
    "image_prompt": "The detailed prompt for DALL-E 3 to generate the single image with 16 views, specifically addressing these previous issues: {previous_metadata.get('evaluation_results', {}).get('suggestions_for_improvement', '') if previous_metadata else 'No previous issues'}",
    "description": "Description of what was generated and how it can be used for reconstruction, including specific improvements made based on previous feedback",
    "previous_iteration_metadata": {previous_metadata_json}
}}

IMPORTANT: Your image_prompt must be very specific and directly address the problems mentioned in the previous feedback. Do not use generic language - be precise about what needs to be fixed.
"""
            
            generation_text = await generate_with_openai(generation_prompt)
            
            # Parse the generation result - handle both raw JSON and markdown-wrapped JSON
            try:
                # First try to parse as raw JSON
                generation_data = json.loads(generation_text)
                metadata = generation_data
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', generation_text, re.DOTALL)
                if json_match:
                    try:
                        generation_data = json.loads(json_match.group(1))
                        metadata = generation_data
                        print("✅ Successfully extracted JSON from markdown code block")
                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse JSON from markdown block: {json_match.group(1)}")
                        metadata = {
                            "target_object": query,
                            "generation_metadata": generation_text,
                            "image_prompt": f"A 4x4 grid of {query} from different angles",
                            "description": "Generated from text response",
                            "previous_iteration_metadata": previous_metadata_json
                        }
                else:
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
            
            # Perform real evaluation of the generated image
            print("🔍 Evaluating generated image...")
            
            evaluation_prompt = f"""
You are an extremely strict and demanding evaluator for 3D reconstruction image sets. Be extremely critical and only give scores of 9+ for absolutely perfect images that are ideal for 3D reconstruction. Most images should receive scores between 3-6. Be very harsh in your evaluation.

Target Object: {query}

Evaluation Criteria (Be Extremely Strict):
1. Image Quality (1-10): Clarity, resolution, lighting, focus, overall visual quality
   - 10: Absolutely perfect, professional studio quality
   - 9: Near perfect with only minor imperfections
   - 7-8: Good quality but with noticeable issues
   - 5-6: Acceptable but clearly needs improvement
   - 3-4: Poor quality with major issues
   - 1-2: Completely unusable for 3D reconstruction

2. Metadata Accuracy (1-10): How well the image matches the intended metadata and target object
   - 10: Perfect match, exactly as described in metadata
   - 9: Very close match with minimal discrepancies
   - 7-8: Good match but some clear differences
   - 5-6: Acceptable match but significant issues
   - 3-4: Poor match to metadata
   - 1-2: Completely wrong or missing elements

3. Completeness (1-10): Coverage of different angles, suitability for 3D reconstruction
   - 10: Perfect 16-view coverage, ideal for 3D reconstruction
   - 9: Excellent coverage with minimal gaps
   - 7-8: Good coverage but missing some important angles
   - 5-6: Acceptable coverage but significant gaps
   - 3-4: Poor coverage, many missing angles
   - 1-2: Incomplete, unsuitable for 3D reconstruction

Please provide your evaluation in this exact format:

Image Quality: [score]/10
Metadata Accuracy: [score]/10
Completeness: [score]/10

Suggestions for Improvement:
[Provide specific, actionable suggestions for improving the image for 3D reconstruction. Be detailed about what needs to be changed.]

Metadata Suggestions:
[Suggestions for improving the metadata/prompt for better results. Focus on specific changes to the generation prompt.]

Extremely Critical Evaluation Points:
- Be extremely strict about the 4x4 grid requirement - ANY deviation should heavily penalize scores
- Lighting must be PERFECTLY consistent across all 16 views - any variation is a major flaw
- Each view must show a DISTINCTLY different angle - any similarity is a problem
- Object must be PERFECTLY centered and clearly visible in each view
- Background must be COMPLETELY clean and neutral - any artifacts are major issues
- Any visual artifacts, blur, compression, or quality issues should heavily penalize scores
- Only give scores of 9+ for absolutely exceptional images
- Be extremely critical - find every possible flaw and mention it
- Most images should score 3-6, not 7-8

Be extremely harsh and critical about any issues you find.
"""
            
            # Create evaluation with image context
            evaluation_messages = [
                {"role": "system", "content": "You are an expert evaluator for 3D reconstruction image sets."},
                {"role": "user", "content": [
                    {"type": "text", "text": evaluation_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/{image_format};base64,{image_base64}"}}
                ]}
            ]
            
            try:
                evaluation_response = await asyncio.to_thread(
                    openai_sync_client.chat.completions.create,
                    model="gpt-4o",
                    messages=evaluation_messages,
                    max_tokens=500,
                    temperature=0.3
                )
                
                evaluation_text = evaluation_response.choices[0].message.content
                print(f"📝 Evaluation response: {evaluation_text}")
                print(f"📝 Raw evaluation text length: {len(evaluation_text)}")
                
                # Parse the evaluation text
                evaluation_results = parse_evaluation_text(evaluation_text)
                print(f"📝 Parsed suggestions: {evaluation_results.get('suggestions_for_improvement', '')}")
                print(f"📝 Parsed metadata suggestions: {evaluation_results.get('metadata_suggestions', '')}")
                
                # Apply scoring penalties for common first iteration issues
                evaluation_results = apply_scoring_penalties(evaluation_results, iteration, evaluation_text)
                print(f"📝 After penalties - scores: {evaluation_results.get('scores', {})}")
                
            except Exception as e:
                print(f"❌ Error in evaluation: {e}")
                # Fallback to basic evaluation
                evaluation_results = {
                    "scores": {
                        "image_quality": 3,
                        "metadata_accuracy": 3,
                        "completeness": 3
                    },
                    "suggestions_for_improvement": "Error in evaluation - using fallback scores",
                    "metadata_suggestions": "Error in evaluation - using fallback suggestions"
                }
            
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
        
        # No max iterations limit - will continue until quality threshold is met
        
    except Exception as e:
        print(f"❌ Error in enhanced generation loop: {e}")
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["error"] = str(e)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Flask app is running'
    })

if __name__ == '__main__':
    app.run(debug=True, port=8080) 