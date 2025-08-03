from pydantic import BaseModel
from agents import Agent, ImageGenerationTool, Runner, trace, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from agents import set_tracing_disabled
import os

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

# Use environment variable for API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Please set it in your .env file for local development "
        "or in your Vercel environment variables for deployment."
    )

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
set_tracing_disabled(disabled=True)
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)

INSTRUCTIONS = (
    "Our task is to generate the materials needed for 3D CAD generation, given the query. You may need to generate multi-view 2D images with aligned size, as well as metadata."
    "output all the materials that we might need."
)
generation_agent = Agent(
    name="aaa",
    instructions=INSTRUCTIONS,
    model=model,
    # tools=[ImageGenerationTool(
    #             tool_config={"type": "image_generation", "quality": "low"},
    #         )],
    # output_type=ReportData,
)

class ReportData(BaseModel):
    meta_data: str
    """The metadata for the generated materials."""

    image: str
    """The multi-view 2D image in base64 format."""

    follow_up_questions: list[str]
    """Suggested [potential materials to generate"""



