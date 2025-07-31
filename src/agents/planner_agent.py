from pydantic import BaseModel
from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel
import asyncio
from openai import AsyncOpenAI
from agents import set_tracing_disabled
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)
openai_client = AsyncOpenAI(api_key="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")
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
