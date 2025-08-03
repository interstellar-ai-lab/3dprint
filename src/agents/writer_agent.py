# Agent used to synthesize a final report from the individual summaries.
from pydantic import BaseModel
import base64
from agents import Agent, OpenAIChatCompletionsModel
import os
FILEPATH = os.path.join(os.path.dirname(__file__), "media/image_bison.jpg")
from openai import AsyncOpenAI
from agents import set_tracing_disabled

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
# def image_to_base64(image_path):
#     with open(image_path, "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
#     return encoded_string


# async def main():
#     # Print base64-encoded image
#     b64_image = image_to_base64(FILEPATH)

#     agent = Agent(
#         name="Assistant",
#         instructions="You are a helpful assistant.",
#     )

#     result = await Runner.run(
#         agent,
#         [
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "input_image",
#                         "detail": "auto",
#                         "image_url": f"data:image/jpeg;base64,{b64_image}",
#                     }
#                 ],
#             },
#             {
#                 "role": "user",
#                 "content": "What do you see in this image?",
#             },
#         ],
#     )
#     print(result.final_output)

PROMPT = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research "
    "assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)


class ReportData(BaseModel):
    short_summary: str
    """A short 2-3 sentence summary of the findings."""

    markdown_report: str
    """The final report"""

    follow_up_questions: list[str]
    """Suggested topics to research further"""


writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model=model,
    output_type=ReportData,
)
