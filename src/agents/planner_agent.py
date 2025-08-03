from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel
import asyncio
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

agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
set_tracing_disabled(disabled=True)
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)

PROMPT = (
    "Our task is to generate the materials needed for 3D CAD generation, given the query. You may need to generate multi-view 2D images with aligned size, as well as metadata."
    "output all the materials that we might need."
)


class WebSearchItem(BaseModel):
    reason: str
    "Your reasoning for why this search is important to the query."

    query: str
    "The search term to use for the web search."


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]
    """A list of web searches to perform to best answer the query."""


planner_agent = Agent(
    name="PlannerAgent",
    instructions=PROMPT,
    model=model,
    output_type=WebSearchPlan,
)
