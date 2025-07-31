from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel,ImageGenerationTool, OpenAIResponsesModel
import asyncio
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import set_tracing_disabled
from agents import Runner
import tempfile
import base64
from openai import OpenAI
import json
import pathlib
from PIL import Image
import io

# API Keys for different providers
OPENAI_API_KEY = "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"
CLAUDE_API_KEY = "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"
# Add your DeepSeek and Qwen API keys here when you have them
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
QWEN_API_KEY = "your_qwen_api_key_here"

# OpenAI client for image generation (still needed for DALL-E)
client = OpenAI(api_key=OPENAI_API_KEY)

# Different API clients for text generation
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

claude_client = AsyncOpenAI(
    api_key=CLAUDE_API_KEY,
    base_url="https://api.anthropic.com/v1"
)

# DeepSeek client (uncomment when you have the API key)
# deepseek_client = AsyncOpenAI(
#     api_key=DEEPSEEK_API_KEY,
#     base_url="https://api.deepseek.com/v1"
# )

# Qwen client (uncomment when you have the API key)
# qwen_client = AsyncOpenAI(
#     api_key=QWEN_API_KEY,
#     base_url="https://dashscope.aliyuncs.com/api/v1"
# )

set_tracing_disabled(disabled=True)

# Configuration for different models - easy to switch for testing
MODEL_CONFIGS = {
    "openai": {
        "client": openai_client,
        "model": "gpt-4o",
        "name": "OpenAI GPT-4o"
    },
    "claude": {
        "client": claude_client,
        "model": "claude-3-sonnet-20240229",
        "name": "Claude 3 Sonnet"
    },
    # "deepseek": {
    #     "client": deepseek_client,
    #     "model": "deepseek-chat",
    #     "name": "DeepSeek Chat"
    # },
    # "qwen": {
    #     "client": qwen_client,
    #     "model": "qwen-turbo",
    #     "name": "Qwen Turbo"
    # }
}

# Current model to use for testing - change this to test different APIs
CURRENT_MODEL = "claude"  # Options: "openai", "claude", "deepseek", "qwen"

### agent 1: generation_agent
# 1) Get prompts + metadata
def generation_agent(iteration,query):
    INSTRUCTIONS = f"""Your task is to generate 16 views of the same object that can be used for 3D CAD reconstruction for the target object: {query}. Each view should be aligned in size. Make sure the 20 views are diverse and cover different angles and perspectives of the object.
    """
    img_resp = client.images.generate(
            model="gpt-image-1",
            prompt=INSTRUCTIONS,
            size="1024x1024",
        )
    # Compress the image data by resizing and re-encoding

    # Decode the base64 image data
    original_image_data = base64.b64decode(img_resp.data[0].b64_json)
    original_image = Image.open(io.BytesIO(original_image_data))

    # Resize the image to reduce size (e.g., 512x512)
    resized_image = original_image.resize((128, 128))

    # Re-encode the resized image to base64
    buffer = io.BytesIO()
    resized_image.save(buffer, format="JPEG")
    compressed_image_data = buffer.getvalue()
    b64 = base64.b64encode(compressed_image_data).decode("utf-8")
    prompt = "Based on the multi-view image, generate the metadata for the 3D CAD generation task. Please ensure precise metadata for conversion into a 3D model format. Add accompanying MTL and basic UV coordinates."
    chat = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Here is the base64 image data: {b64}. Please analyze it and generate the required metadata."}
        ]
    )

    metadata =chat.choices[0].message.content


    # 2) Render each view
    out_dir = pathlib.Path("renders"); out_dir.mkdir(exist_ok=True)
    png_path = out_dir / f"{iteration}.png"
    with open(png_path, "wb") as f:
        f.write(base64.b64decode(b64))

    # 3) Package everything
    package = {
        "metadata": metadata,
    }
    with open(out_dir / "package.json", "a") as f:
        json.dump(package, f, indent=2)

    print("Done. Files in", out_dir)
    return metadata, b64

# ### agent 1: generation_agent
# model_1 = OpenAIResponsesModel(
#     model="gpt-4o",
#     openai_client=openai_client
# )
# PROMPT = """
#     Your task is to generate 20 views of the same object that can be used for 3D CAD reconstruction for the target object: {query}. Each view should be aligned in size. Make sure the 20 views are diverse and cover different angles and perspectives of the object.
#     """

# generation_agent = Agent(
#     name="Writeragent",
#     instructions=PROMPT,
#     model=model_1,
#     tools=[ImageGenerationTool(
#                 tool_config={"type": "image_generation", "quality": "low"},
#             )]
# )


### agent 2: evaluation_agent
# Agent used to synthesize a final report from the individual summaries.dog
current_config = MODEL_CONFIGS[CURRENT_MODEL]
print(f"Using {current_config['name']} for evaluation agent")

model_2 = OpenAIChatCompletionsModel(
    model=current_config["model"],
    openai_client=current_config["client"]
)
PROMPT = """
    You are an evaluation agent. 
    You need to evaluate the generated 2D images and metadata, and write a report about the evaluation.
    Answer the follow-up questions to provide hints for the next round of generation. 
    First, summarize the generated 2D images and metadata in a short 2-3 sentence summary.

    Second, you need to write a report evaluating whether these 2D images and metadata are correct/sufficient for the CAD generation task, using the following three criteria and assign a score (1-10) for each:
    1. Image Quality: Assess the visual clarity and alignment of the generated 2D images.
    2. Metadata Accuracy: Evaluate the correctness and relevance of the metadata for CAD reconstruction.
    3. Completeness: Determine if the number of views and metadata provided are sufficient for the task.  
    Include these scores in your report and provide detailed reasoning (be as specific as possible) for each score.    
     
    Third, provide suggestions for improvement. If all scores are higher than 6.5, your suggestions_for_improvement should be "well done", nothing more.
    The report should be in markdown format, and it should be detailed and comprehensive.

    """


class ReportData_2(BaseModel):
    short_summary: str
    """A short 2-3 sentence evaluation of the generated 2D images and metadata."""

    markdown_report: str
    """The final report"""

    suggestions_for_improvement: str
    """Suggestions to improve the generated 2D images and metadata."""

writer_agent = Agent(
    name="Writeragent",
    instructions=PROMPT,
    model=model_2,
    output_type=ReportData_2
)

#agent 3 generate mesh image
def generate_mesh_image(metadata, b64_image):
    prompt = f"""
    Give me the 3D mesh for the object in the image {b64_image}. 
    The image include multi-views of the object, and the corresponding metadata can be found in: {metadata}. 
    """
    
    img_resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
        )
    # Compress the image data by resizing and re-encoding

    # Decode the base64 image data
    mesh_data = img_resp.data[0].b64_json

    # Save the mesh data to a file
    out_dir = pathlib.Path("mesh_outputs"); out_dir.mkdir(exist_ok=True)
    png_path = out_dir / "mesh_image.png"
    with open(png_path, "wb") as f:
        f.write(base64.b64decode(mesh_data))
    

# Create a session instance
session = SQLiteSession("conversation_123")

# Function to switch models for testing
def switch_model(model_name):
    """Switch to a different model for testing"""
    global CURRENT_MODEL, model_2, writer_agent
    if model_name in MODEL_CONFIGS:
        CURRENT_MODEL = model_name
        current_config = MODEL_CONFIGS[model_name]
        print(f"Switching to {current_config['name']}")
        
        model_2 = OpenAIChatCompletionsModel(
            model=current_config["model"],
            openai_client=current_config["client"]
        )
        
        writer_agent = Agent(
            name="Writeragent",
            instructions=PROMPT,
            model=model_2,
            output_type=ReportData_2
        )
        return True
    else:
        print(f"Model {model_name} not found. Available models: {list(MODEL_CONFIGS.keys())}")
        return False

async def main():
    query = input("What would you like to generate? ")
    print(query)
    
    # Ask which model to use for testing
    print(f"\nAvailable models for testing:")
    for key, config in MODEL_CONFIGS.items():
        print(f"  {key}: {config['name']}")
    
    model_choice = input(f"\nWhich model to use? (default: {CURRENT_MODEL}): ").strip().lower()
    if model_choice and model_choice in MODEL_CONFIGS:
        switch_model(model_choice)
    
    suggestions = ""
    iteration = 0
    #result_1 = await Runner.run(generation_agent, "Please generate the materials needed for 3D CAD generation.", session=session)
    metadata, b64_image = generation_agent(iteration, query)
    while suggestions != "well done":
        iteration += 1
    # First turn
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
        result_2 = await Runner.run(writer_agent, contents)
        suggestions = result_2.final_output.suggestions_for_improvement
        new_prompt = (
            f"The target for your generation is: {query}. Detailed task is introduced by the instructions from the system above.\n\n"
            f"Below are the metadata from your previous generation attempt:\n\n{metadata}\n\n"
            f"Please refine the generation results based on the system instructions. Pay special attention to the following suggestions for improvement: {suggestions}.\n\n"
            f"Additionally, consider the scores and reasoning provided in the evaluation report for the previous generation attempt:\n\n{result_2.final_output.markdown_report}."
        )
        metadata, b64_image = generation_agent(iteration, new_prompt)
        # Second turn - agent automatically remembers previous context
        # Save the evaluation results separately for each iteration
        out_dir = pathlib.Path(f"evaluation_reports_{iteration}"); out_dir.mkdir(exist_ok=True)
        
        # Save markdown report
        markdown_path = out_dir / f"iteration_{iteration}_report.md"
        with open(markdown_path, "w") as f:
            f.write(result_2.final_output.markdown_report)
        
        # Save suggestions for improvement
        suggestions_path = out_dir / f"iteration_{iteration}_suggestions.txt"
        with open(suggestions_path, "w") as f:
            f.write(result_2.final_output.suggestions_for_improvement)
        
        # Save short summary
        summary_path = out_dir / f"iteration_{iteration}_summary.txt"
        with open(summary_path, "w") as f:
            f.write(result_2.final_output.short_summary)
        
        # Print the markdown report to the console
        print(result_2.final_output.markdown_report)
    print("All iterations completed. Final report saved in", out_dir)
    # Generate mesh image using GPT-4o

    # Call the function to generate the mesh image
    # generate_mesh_image(metadata, b64_image)
    print("Mesh data generated and saved.")

if __name__ == "__main__":
    asyncio.run(main())