#!/usr/bin/env python3
"""
GPT-4 Vision + DALL-E 3 Hybrid Multiview Image Generation Test
Uses DALL-E 3 for generation and GPT-4 Vision for evaluation and feedback
"""

import asyncio
import json
import os
import pathlib
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import base64
from PIL import Image
import io

from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
            file_path = image_url[7:]  # Remove "file://" prefix
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

async def generate_multiview_with_gpt_image1(target_object: str, iteration: int = 1, previous_feedback: List[str] = None) -> str:
    """Generate 4x4 multiview image using GPT-4 Vision (gpt-image-1)"""
    
    print(f"🎨 Generating 4x4 multiview for '{target_object}' (iteration {iteration})...")
    
    # Create the generation instructions
    instructions = f"""Your task is to generate 16 views of the same object that can be used for 3D CAD reconstruction for the target object: {target_object}. Each view should be aligned in size. Make sure the 16 views are diverse and cover different angles and perspectives of the object."""

    # Add feedback from previous iterations
    if previous_feedback:
        feedback_text = " ".join(previous_feedback)
        instructions += f" IMPORTANT: Address these specific issues from previous iteration: {feedback_text}"
    
    try:
        response = await asyncio.to_thread(
            openai_sync_client.images.generate,
            model="gpt-image-1",
            prompt=instructions,
            size="1024x1024",
        )

        # print('response url', response.data[0].url)
        
        print(f"🔍 Response type: {type(response)}")
        print(f"🔍 Response data length: {len(response.data) if response.data else 0}")
        
        if hasattr(response, 'data') and response.data:
            # Check if it's a URL or base64 data
            first_item = response.data[0]
            if hasattr(first_item, 'url') and first_item.url:
                image_url = first_item.url
                print(f"✅ Generated image URL: {image_url}")
                return image_url
            elif hasattr(first_item, 'b64_json') and first_item.b64_json:
                # Handle base64 data
                print(f"✅ Generated base64 image data (length: {len(first_item.b64_json)})")
                
                # Decode base64 and save to temporary file
                import tempfile
                import base64
                
                try:
                    # Decode base64 data
                    image_data = base64.b64decode(first_item.b64_json)
                    
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    print(f"✅ Saved base64 image to temporary file: {temp_file.name}")
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
    
    print(f"🔍 Evaluating image (iteration {iteration})...")
    
    evaluation_prompt = f"""You are an expert evaluator for 3D reconstruction image sets. Analyze this 4x4 multiview image of a {target_object}.

EVALUATION CRITERIA (Be Extremely Strict):
1. Image Quality (1-10): Clarity, resolution, lighting, focus, overall visual quality
2. Grid Structure (1-10): Perfect 4x4 grid with exactly 16 separate images
3. Angle Diversity (1-10): 16 distinctly different 3D viewing angles
4. Object Consistency (1-10): Same object appearance across all 16 views
5. Background Cleanliness (1-10): Pure white background with no extra elements
6. 3D Reconstruction Suitability (1-10): Overall suitability for 3D reconstruction

CRITICAL CHECKS:
- Verify it's a perfect 4x4 grid (16 images, not 9 or other formats)
- Check that each of the 16 positions shows a different angle
- Ensure the object is identical across all views
- Confirm pure white background with no extra elements
- Verify no text, numbers, or technical annotations

Provide your evaluation in this exact format:

Image Quality: [score]/10
Grid Structure: [score]/10
Angle Diversity: [score]/10
Object Consistency: [score]/10
Background Cleanliness: [score]/10
3D Reconstruction Suitability: [score]/10

Overall Score: [average]/10

Specific Issues Found:
[List specific problems found]

Suggestions for Improvement:
[Specific, actionable suggestions for the next iteration]"""

    try:
        # Download image for evaluation
        image = await download_image_to_pil(image_url)
        if not image:
            return {
                "scores": {"overall": 3},
                "issues": ["Failed to download image for evaluation"],
                "suggestions": ["Check image URL and try again"]
            }
        
        # Convert image to base64 for GPT-4 Vision
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": evaluation_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        evaluation_text = response.choices[0].message.content
        print(f"📝 Evaluation response: {evaluation_text}")
        
        # Parse evaluation results
        return parse_evaluation_text(evaluation_text)
        
    except Exception as e:
        print(f"❌ Error in evaluation: {e}")
        return {
            "scores": {"overall": 3},
            "issues": [f"Evaluation error: {e}"],
            "suggestions": ["Check evaluation system and try again"]
        }

def parse_evaluation_text(text: str) -> Dict:
    """Parse evaluation text and extract scores and feedback"""
    
    scores = {}
    issues = []
    suggestions = []
    
    try:
        # Extract scores
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line and '/10' in line:
                parts = line.split(':')
                if len(parts) == 2:
                    metric = parts[0].strip()
                    score_part = parts[1].strip()
                    if '/10' in score_part:
                        score_str = score_part.split('/')[0].strip()
                        try:
                            score = float(score_str)
                            scores[metric] = score
                        except ValueError:
                            pass
        
        # Extract issues and suggestions
        in_issues = False
        in_suggestions = False
        
        for line in lines:
            line = line.strip()
            if "Specific Issues Found:" in line:
                in_issues = True
                in_suggestions = False
                continue
            elif "Suggestions for Improvement:" in line:
                in_issues = False
                in_suggestions = True
                continue
            elif line.startswith("Image Quality:") or line.startswith("Grid Structure:"):
                in_issues = False
                in_suggestions = False
                continue
            
            if in_issues and line and not line.startswith('-'):
                issues.append(line)
            elif in_suggestions and line and not line.startswith('-'):
                suggestions.append(line)
        
        # Calculate overall score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
            scores["overall"] = overall_score
        
    except Exception as e:
        print(f"❌ Error parsing evaluation text: {e}")
        scores = {"overall": 3}
        issues = ["Failed to parse evaluation"]
        suggestions = ["Check evaluation format"]
    
    return {
        "scores": scores,
        "issues": issues,
        "suggestions": suggestions
    }

def meets_quality_threshold(scores: Dict) -> bool:
    """Check if quality threshold is met (very strict)"""
    overall = scores.get("overall", 0)
    grid_structure = scores.get("Grid Structure", 0)
    angle_diversity = scores.get("Angle Diversity", 0)
    # Require all individual scores to be at least 8.5
    all_scores = [v for k, v in scores.items() if isinstance(v, (int, float))]
    return (
        overall >= 9.5 and
        grid_structure >= 9.5 and
        angle_diversity >= 9.5 and
        all(score >= 8.5 for score in all_scores)
    )

async def save_metadata(session_id: str, iteration: int, target_object: str, image_url: str, evaluation_results: Dict) -> str:
    """Save metadata for this iteration"""
    session_dir = pathlib.Path(f"generated_images/gpt4v_gpt_image1_hybrid_{session_id}")
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
    
    print(f"💾 Metadata saved to {metadata_file}")
    return str(metadata_file)

async def run_hybrid_multiview_generation(target_object: str) -> Dict:
    """Run iterative hybrid multiview generation (GPT-4 Vision + GPT-4 Vision evaluation)"""
    
    print(f"🚀 Starting Hybrid Multiview Generation for: {target_object}")
    print("🎨 Using GPT-4 Vision for generation + GPT-4 Vision for evaluation")
    print("=" * 70)
    
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    previous_feedback = []
    all_results = []
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n🔄 Iteration {iteration}")
        print("-" * 50)
        
        # Generate image with GPT-4 Vision
        image_url = await generate_multiview_with_gpt_image1(target_object, iteration, previous_feedback)
        
        if not image_url:
            print("❌ Failed to generate image")
            break
        
        # Display the generated image
        print(f"🖼️ Generated Image (Iteration {iteration}):")
        print(f"   🔗 Image URL: {image_url}")
        
        # Handle different URL types
        if image_url.startswith('file://'):
            local_path = image_url.replace('file://', '')
            print(f"   📁 Local File: {local_path}")
            
            # Try to display image if it's a local file
            if os.path.exists(local_path):
                try:
                    from PIL import Image
                    img = Image.open(local_path)
                    print(f"   📐 Size: {img.size}")
                    print(f"   🎨 Mode: {img.mode}")
                    print(f"   💾 File Size: {os.path.getsize(local_path)} bytes")
                    # You could add image display here if running in a GUI environment
                except Exception as e:
                    print(f"   ⚠️ Could not load image: {e}")
            else:
                print(f"   ⚠️ Local file not found: {local_path}")
        elif image_url.startswith('http'):
            print(f"   🌐 Remote URL: {image_url}")
        else:
            print(f"   📁 File Path: {image_url}")
        
        # Evaluate image with GPT-4 Vision
        print(f"🔍 Evaluating image (iteration {iteration})...")
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
        
        # Display detailed evaluation results
        scores = evaluation_results.get("scores", {})
        overall_score = scores.get("overall", 0)
        
        print(f"\n📊 EVALUATION RESULTS (Iteration {iteration}):")
        print(f"   🎯 Overall Score: {overall_score:.1f}/10")
        print(f"   🔗 Image URL: {image_url}")
        
        # Display individual scores
        for score_name, score_value in scores.items():
            if score_name != "overall":
                print(f"   📈 {score_name.replace('_', ' ').title()}: {score_value:.1f}/10")
        
        # Display issues
        if evaluation_results.get("issues"):
            print(f"\n❌ ISSUES FOUND:")
            for i, issue in enumerate(evaluation_results["issues"], 1):
                print(f"   {i}. {issue}")
        
        # Display suggestions
        if evaluation_results.get("suggestions"):
            print(f"\n💡 SUGGESTIONS FOR IMPROVEMENT:")
            for i, suggestion in enumerate(evaluation_results["suggestions"], 1):
                print(f"   {i}. {suggestion}")
        
        # Check if quality threshold is met
        if meets_quality_threshold(scores):
            print(f"\n✅ QUALITY THRESHOLD MET! (Score: {overall_score:.1f}/10)")
            print("🎉 Stopping iterations.")
            break
        
        # Ask user if they want to continue
        print(f"\n🤔 Continue to next iteration? (y/n): ", end="")
        try:
            # For automated testing, we'll continue automatically
            # In a real scenario, you'd get user input here
            continue_choice = "y"  # Default to continue
            print("y (auto-continue)")
        except KeyboardInterrupt:
            print("\n⏹️ User interrupted. Stopping iterations.")
            break
        
        if continue_choice.lower() != 'y':
            print("⏹️ User chose to stop. Ending iterations.")
            break
        
        # Prepare feedback for next iteration
        previous_feedback = evaluation_results.get("suggestions", [])
        
        print(f"⏳ Waiting 2 seconds before next iteration...")
        await asyncio.sleep(2)
    
    # Final results
    print("\n" + "=" * 70)
    print("🏁 GPT-4 VISION MULTIVIEW GENERATION COMPLETE")
    print(f"📁 Session ID: {session_id}")
    print(f"📊 Total iterations: {len(all_results)}")
    
    if all_results:
        final_score = all_results[-1]["evaluation"]["scores"].get("overall", 0)
        print(f"🎯 Final score: {final_score:.1f}/10")
        print(f"🖼️ Final image: {all_results[-1]['image_url']}")
    
    return {
        "session_id": session_id,
        "target_object": target_object,
        "iterations": all_results,
        "final_score": final_score if all_results else 0
    }

async def main():
    """Main function"""
    print("🚀 GPT-4 Vision Multiview Image Generation Test")
    print("=" * 70)
    
    # Test with a dog
    target_object = "Golden Retriever dog"
    
    results = await run_hybrid_multiview_generation(target_object)
    
    print("\n📋 Summary:")
    print(f"✅ Session completed: {results['session_id']}")
    print(f"🎯 Target object: {results['target_object']}")
    print(f"📊 Final score: {results['final_score']:.1f}/10")
    print(f"🔄 Total iterations: {len(results['iterations'])}")

if __name__ == "__main__":
    asyncio.run(main()) 