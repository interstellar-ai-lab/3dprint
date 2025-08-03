#!/usr/bin/env python3
"""
Test script for evaluation agent with multi-view images only
Tests the evaluation agent's ability to score multi-view images and iterate until quality threshold is met
Uses image metadata for evaluation and ensures each iteration builds upon previous metadata
"""

import asyncio
import json
import os
import base64
import aiohttp
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

# Import the necessary components
from src.agents import Agent, Runner
from src.agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import OpenAI, AsyncOpenAI

# Initialize OpenAI clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Please set it in your .env file for local development "
        "or in your Vercel environment variables for deployment."
    )
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)

# Model for agents
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)

# Model with vision capabilities for image analysis
vision_model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)

# Evaluation agent prompt that uses metadata
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
- Specific angle descriptions for each of the 16 views
- Lighting specifications
- Material properties
- Geometric constraints
- Any other relevant parameters for 3D reconstruction

If all scores are higher than 6.5, your suggestions_for_improvement should be "well done", and your metadata_suggestions should be "current metadata is sufficient".

The report should be in markdown format, and it should be detailed and comprehensive.
"""

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

def save_metadata(session_id: str, iteration: int, metadata: Dict, image_url: str, evaluation_results: Dict) -> str:
    """Save metadata for the current iteration"""
    # Create session directory
    session_dir = Path(f"generated_images/session_{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Create metadata file
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

# Generation agent prompt for multi-view images with metadata integration
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

# Create agents
evaluation_agent = Agent(
    name="EvaluationAgent",
    instructions=EVALUATION_PROMPT,
    model=model
)

generation_agent = Agent(
    name="GenerationAgent", 
    instructions=GENERATION_PROMPT,
    model=model
)

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
        "coordinate system", "axis labels", "license plates", "overlays",
        "different colors", "color variations", "orange", "grey", "blue",
        "coordinate", "axis", "labels", "text overlays", "technical overlays"
    ]
    
    failure_count = 0
    for indicator in failure_indicators:
        if indicator.lower() in text.lower():
            failure_count += 1
            print(f"🔍 Found failure indicator: {indicator}")
    
    # If we found multiple failure indicators, force low scores
    if failure_count >= 2:
        print(f"🔍 Found {failure_count} failure indicators, forcing low scores")
        result["scores"] = {"image_quality": 1, "metadata_accuracy": 1, "completeness": 1}
        result["suggestions_for_improvement"] = f"Major failures detected: {failure_count} critical issues found"
    
    # If we found "well done" but no scores, assume high scores
    elif result["suggestions_for_improvement"] == "well done" and all(score == 0 for score in result["scores"].values()):
        print("🔍 Found 'well done' but no scores parsed, assuming high scores")
        result["scores"] = {"image_quality": 8, "metadata_accuracy": 8, "completeness": 8}
    
    # If no scores were found at all, this is likely a failure
    elif all(score == 0 for score in result["scores"].values()):
        print("🔍 No scores found in evaluation, likely indicating major failures")
        result["scores"] = {"image_quality": 1, "metadata_accuracy": 1, "completeness": 1}
        result["suggestions_for_improvement"] = "Major failures detected: wrong grid size, multiple objects, or wrong background/style"
    
    # Extract short summary (first few sentences)
    sentences = text.split('.')
    if len(sentences) > 0:
        result["short_summary"] = sentences[0].strip() + "."
    
    # Extract suggestions if not "well done"
    if result["suggestions_for_improvement"] != "well done":
        # Look for suggestions in multiple ways
        suggestions_found = False
        
        # Method 1: Look for explicit suggestion/improvement sections
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ["suggestion", "improvement", "fix", "issue", "problem"]):
                suggestions = []
                for j in range(i, min(i + 10, len(lines))):  # Look further ahead
                    if lines[j].strip():
                        suggestions.append(lines[j].strip())
                result["suggestions_for_improvement"] = " ".join(suggestions)
                suggestions_found = True
                break
        
        # Method 2: If no explicit suggestions, look for negative feedback in the text
        if not suggestions_found:
            negative_indicators = []
            for line in lines:
                line_lower = line.lower()
                if any(indicator in line_lower for indicator in [
                    "wrong", "incorrect", "missing", "failed", "problem", "issue", 
                    "not", "lacks", "poor", "bad", "inconsistent", "different"
                ]):
                    negative_indicators.append(line.strip())
            
            if negative_indicators:
                result["suggestions_for_improvement"] = " ".join(negative_indicators[:3])  # Take first 3 issues
                suggestions_found = True
        
        # Method 3: If still no suggestions, provide generic feedback based on scores
        if not suggestions_found:
            low_score_areas = []
            if result["scores"]["image_quality"] < 6:
                low_score_areas.append("improve image quality and visual clarity")
            if result["scores"]["metadata_accuracy"] < 6:
                low_score_areas.append("improve metadata accuracy and descriptions")
            if result["scores"]["completeness"] < 6:
                low_score_areas.append("ensure complete coverage of all required angles")
            
            if low_score_areas:
                result["suggestions_for_improvement"] = "Focus on: " + ", ".join(low_score_areas)
            else:
                result["suggestions_for_improvement"] = "Continue improving the generation"
    
    # Extract metadata suggestions
    if result["metadata_suggestions"] != "current metadata is sufficient":
        # Look for metadata suggestions in the text
        metadata_section_found = False
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ["metadata", "angle", "lighting", "material", "geometric"]):
                metadata_suggestions = []
                for j in range(i, min(i + 15, len(lines))):  # Look further ahead
                    if lines[j].strip():
                        metadata_suggestions.append(lines[j].strip())
                result["metadata_suggestions"] = " ".join(metadata_suggestions)
                metadata_section_found = True
                break
        
        # If no explicit metadata suggestions, provide generic ones based on scores
        if not metadata_section_found:
            if result["scores"]["metadata_accuracy"] < 6:
                result["metadata_suggestions"] = "Improve metadata accuracy with specific angle descriptions, lighting specifications, and material properties"
            elif result["scores"]["completeness"] < 6:
                result["metadata_suggestions"] = "Enhance metadata to include complete coverage specifications for 360° horizontal rotation and full vertical elevation"
            else:
                result["metadata_suggestions"] = "Refine metadata with more detailed specifications for optimal 3D reconstruction"
    
    return result

def meets_quality_threshold(scores: Dict) -> bool:
    """Check if all scores meet the quality threshold (6.5)"""
    # If any score is 0, it means parsing failed, so we need to check the suggestions
    if any(score == 0 for score in scores.values()):
        return False
    return all(score >= 6.5 for score in scores.values())

async def test_evaluation_with_multi_view(object_name: str) -> Dict:
    """Test evaluation agent with multi-view images and iterate until quality threshold is met"""
    print(f"🧪 Testing evaluation agent with multi-view images for: {object_name}")
    print("=" * 80)
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    print(f"📋 Session ID: {session_id}")
    
    iteration = 1
    current_metadata = {}
    current_image_url = ""
    parsed_evaluation = None
    
    while True:  # Continue until quality threshold is met
        print(f"\n🔄 Iteration {iteration}")
        print("-" * 50)
        
        # Load previous iteration metadata
        previous_metadata = load_previous_metadata(session_id, iteration)
        
        # Step 1: Generate image prompt and metadata
        if iteration == 1:
            # First iteration - generate from scratch
            previous_metadata_context = ""
            previous_metadata_json = "null"
        else:
            # Subsequent iterations - use feedback from evaluation and previous metadata
            previous_metadata_context = f"""
            Previous iteration feedback:
            - Image Quality: {parsed_evaluation["scores"]["image_quality"]}/10
            - Metadata Accuracy: {parsed_evaluation["scores"]["metadata_accuracy"]}/10  
            - Completeness: {parsed_evaluation["scores"]["completeness"]}/10
            
            Issues to fix: {parsed_evaluation["suggestions_for_improvement"]}
            
            Metadata suggestions: {parsed_evaluation["metadata_suggestions"]}
            
            Previous metadata: {previous_metadata.get("generation_metadata", "") if previous_metadata else "None"}
            
            Based on the evaluation feedback and previous metadata above, create an IMPROVED prompt for DALL-E 3 that addresses the specific issues mentioned.
            
            CRITICAL: You must modify the base prompt to specifically address the feedback. For example:
            - If the feedback mentions "wrong grid size" or "not 4x4", emphasize "exactly 16 squares in a 4x4 grid"
            - If the feedback mentions "multiple objects", emphasize "exactly ONE object per square"
            - If the feedback mentions "grid lines" or "background issues", emphasize "pure white background with NO lines, text, or overlays"
            - If the feedback mentions "inconsistent lighting", emphasize "identical lighting conditions across all views"
            - If the feedback mentions "wrong style", emphasize "photorealistic rendering, NOT wireframe or low-poly"
            - If the feedback mentions "inconsistent colors", emphasize "identical color and material across all 16 views"
            - If the feedback mentions "object too small/large", emphasize "object occupies 60-80% of each square"
            - If the feedback mentions "metadata mismatch", improve the metadata descriptions to match what should be generated
            - If the feedback mentions "incomplete coverage", ensure metadata includes all required angles for 3D reconstruction
            """
            previous_metadata_json = json.dumps(previous_metadata) if previous_metadata else "null"
        
        prompt = GENERATION_PROMPT.format(
            query=object_name,
            previous_metadata_context=previous_metadata_context,
            previous_metadata_json=previous_metadata_json
        )
        
        print(f"📝 Generating image prompt and metadata...")
        result = await Runner.run(generation_agent, prompt)
        
        # Parse the response
        print(f"📄 Raw response: {result.final_output[:200]}...")
        try:
            # Handle markdown code blocks
            response_text = result.final_output.strip()
            if response_text.startswith("```json"):
                # Remove markdown code block formatting
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                # Remove generic markdown code block formatting
                response_text = response_text.replace("```", "").strip()
            
            parsed_output = json.loads(response_text)
            current_metadata = {
                "target_object": parsed_output.get("target_object", object_name),
                "generation_metadata": parsed_output.get("generation_metadata", ""),
                "image_prompt": parsed_output.get("image_prompt", ""),
                "description": parsed_output.get("description", ""),
                "previous_iteration_metadata": parsed_output.get("previous_iteration_metadata", None)
            }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to parse generation response: {e}")
            current_metadata = {
                "target_object": object_name,
                "generation_metadata": result.final_output,
                "image_prompt": "",
                "description": "",
                "previous_iteration_metadata": None
            }
        
        print(f"✅ Generated metadata: {len(current_metadata['generation_metadata'])} characters")
        print(f"✅ Generated image prompt: {len(current_metadata['image_prompt'])} characters")
        
        # Step 2: Generate image with DALL-E 3
        if current_metadata['image_prompt']:
            print(f"🎨 Generating image with DALL-E 3...")
            current_image_url = await generate_image_with_dalle3(current_metadata['image_prompt'])
            if current_image_url:
                print(f"✅ Generated image: {current_image_url}")
            else:
                print(f"❌ Failed to generate image")
                break
        else:
            print(f"❌ No image prompt found")
            break
        
        # Step 3: Download image and convert to base64 for visual evaluation
        print(f"📊 Downloading image for visual evaluation...")
        b64_image, b64_mime_type = await download_image_to_base64(current_image_url)
        
        if not b64_image:
            print(f"❌ Failed to download image for evaluation")
            break
        
        print(f"✅ Successfully converted image to base64 for visual evaluation")
        
        # Step 4: Evaluate the generated image and metadata with visual input
        print(f"📊 Evaluating generated content with visual input...")
        
        # Create multimodal content with the actual image and metadata
        evaluation_contents = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "detail": "auto",
                        "image_url": f"data:{b64_mime_type};base64,{b64_image}",
                    }
                ],
            },
            {
                "role": "user",
                "content": f"""
                TARGET OBJECT: {current_metadata['target_object']}
                
                GENERATED METADATA: {current_metadata['generation_metadata']}
                
                DESCRIPTION: {current_metadata['description']}
                
                PREVIOUS ITERATION METADATA: {current_metadata['previous_iteration_metadata'] if current_metadata['previous_iteration_metadata'] else 'None (First iteration)'}
                
                CRITICAL EVALUATION REQUIREMENTS (BE VERY STRICT):
                1. **Grid Layout**: Count the exact number of squares - it MUST be exactly 16 squares in a 4x4 grid (4 rows × 4 columns)
                2. **Object Count**: Each square MUST contain exactly ONE object - if any square has multiple objects, this is a MAJOR FAILURE
                3. **Object Type Consistency**: ALL 16 squares must show the SAME object type
                4. **Background**: MUST be pure white or transparent - NO grid lines, NO text, NO numbers, NO watermarks, NO gray backgrounds
                5. **Style**: MUST be photorealistic/realistic - NOT wireframe, NOT low-poly, NOT 3D model style
                6. **Pose Consistency**: The object MUST be in the SAME pose across all 16 views
                7. **Size Consistency**: The object MUST appear the same size in all 16 squares
                8. **Angle Diversity**: Each square MUST show a DIFFERENT angle/view of the object
                9. **Lighting Consistency**: All views must have IDENTICAL lighting conditions
                10. **Surface Detail Preservation**: All surface details and textures must be clearly visible
                11. **Edge Definition**: Sharp, well-defined edges and contours
                12. **Depth Information**: Sufficient depth cues through shadows and perspective
                13. **No Occlusion**: No parts of the object should be hidden
                14. **Scale Reference**: Object should occupy 60-80% of each square
                15. **Color Consistency**: Same color/material appearance across all views
                16. **Geometric Accuracy**: No distortion, stretching, or warping
                17. **Metadata Accuracy**: The metadata must accurately describe what was generated
                18. **Completeness**: The 16 views must provide sufficient coverage for 3D reconstruction
                
                FAILURE CRITERIA (Score 1-3):
- Wrong grid size (not 4x4)
- Multiple objects in any square
- Mix of different object types
- ANY grid lines, text, numbers, coordinate systems, axis labels, or overlays on background
- Wireframe/low-poly style
- Watermarks or logos
- Inconsistent poses
- Inconsistent object sizes
- Inconsistent lighting across views
- Poor edge definition or blurry contours
- Missing surface details or textures
- Object occlusion or hidden parts
- DIFFERENT colors or materials across views
- Geometric distortion or warping
- Insufficient depth information
- Object too small or too large in squares
- Metadata mismatch with generated content
- Incomplete angle coverage for 3D reconstruction
                
                VISUAL INSPECTION CHECKLIST:
- Count the exact number of grid cells (should be 16)
- Check each cell for object count (should be exactly 1 per cell)
- Verify all objects are the same type
- Look for ANY grid lines, text, numbers, coordinate systems, axis labels, or overlays on background
- Check for wireframe or low-poly rendering effects
- Verify pose consistency across all views
- Check size consistency across all cells
- Check lighting consistency across all views
- Verify surface details and textures are preserved
- Assess edge definition and contour sharpness
- Check for depth information and shadows
- Verify no object parts are occluded
- Confirm object scale (60-80% of square size)
- Check for IDENTICAL color and material across ALL views (NO variations)
- Verify geometric accuracy (no distortion)
- Compare metadata description with actual generated content
- Assess completeness of angle coverage for 3D reconstruction
                
                IMPORTANT: You can now see the actual image! Please evaluate it visually and be extremely strict.
                Count the squares, check each square for object count, examine the background, style, and consistency.
                Compare the metadata with what was actually generated.
                
                Please evaluate this multi-view image generation for 3D reconstruction with EXTREME STRICTNESS.
                """
            }
        ]
        
        evaluation_result = await Runner.run(evaluation_agent, evaluation_contents)
        evaluation_text = evaluation_result.final_output
        
        # Debug: Show evaluation text
        print(f"📄 Evaluation text: {evaluation_text[:500]}...")
        
        # Parse evaluation
        parsed_evaluation = parse_evaluation_text(evaluation_text)
        
        # Save metadata for this iteration
        metadata_file = save_metadata(session_id, iteration, current_metadata, current_image_url, parsed_evaluation)
        
        # Display evaluation results
        print(f"\n📊 Evaluation Results (Iteration {iteration}):")
        print(f"  Image Quality: {parsed_evaluation['scores']['image_quality']}/10")
        print(f"  Metadata Accuracy: {parsed_evaluation['scores']['metadata_accuracy']}/10")
        print(f"  Completeness: {parsed_evaluation['scores']['completeness']}/10")
        print(f"  Suggestions: {parsed_evaluation['suggestions_for_improvement']}")
        print(f"  Metadata Suggestions: {parsed_evaluation['metadata_suggestions']}")
        
        # Check if quality threshold is met
        if meets_quality_threshold(parsed_evaluation["scores"]):
            print(f"\n🎉 Quality threshold met! All scores >= 6.5")
            print(f"✅ Final scores:")
            for criterion, score in parsed_evaluation["scores"].items():
                print(f"  {criterion.replace('_', ' ').title()}: {score}/10")
            break
        
        print(f"\n⚠️  Quality threshold not met. Continuing to iteration {iteration + 1}...")
        iteration += 1
    
    print(f"\n📋 Final Results:")
    print(f"  Session ID: {session_id}")
    print(f"  Total iterations: {iteration}")
    print(f"  Final image URL: {current_image_url}")
    print(f"  Final metadata length: {len(current_metadata.get('generation_metadata', ''))} characters")
    
    return {
        "session_id": session_id,
        "iterations": iteration,
        "final_image_url": current_image_url,
        "final_metadata": current_metadata,
        "final_scores": parsed_evaluation["scores"] if parsed_evaluation else {"image_quality": 0, "metadata_accuracy": 0, "completeness": 0},
        "quality_threshold_met": meets_quality_threshold(parsed_evaluation["scores"]) if parsed_evaluation else False
    }

async def main():
    """Main test function"""
    print("🚀 Starting Evaluation Agent Test with Multi-View Images and Metadata Integration")
    print("=" * 80)
    
    # Get user input for object
    object_name = input("What object would you like to generate multi-view images for? (e.g., car, dog, chair): ").strip()
    if not object_name:
        object_name = "car"  # Default
    
    print(f"\n🎯 Testing with object: {object_name}")
    
    # Run the evaluation test
    results = await test_evaluation_with_multi_view(object_name)
    
    print(f"\n" + "=" * 80)
    print("📊 Test Summary:")
    print(f"  Object: {object_name}")
    print(f"  Session ID: {results['session_id']}")
    print(f"  Iterations completed: {results['iterations']}")
    print(f"  Quality threshold met: {results['quality_threshold_met']}")
    print(f"  Final scores: {results['final_scores']}")
    
    if results['final_image_url']:
        print(f"  Final image URL: {results['final_image_url']}")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 