from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel,ImageGenerationTool
import asyncio
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import set_tracing_disabled
from agents import Runner

# Create agent
openai_client = AsyncOpenAI(api_key="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")
set_tracing_disabled(disabled=True)
model_1 = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)
### agent 1: generation_agent


INSTRUCTIONS = """Our task is to generate the materials needed for 3D CAD generation, given the query. 
    You may need to generate multi-view 2D images with aligned size, as well as metadata.
    output all the materials that we might need."""

agent = Agent(
    name="Assistant",
    instructions=INSTRUCTIONS,
    model=model_1
    )

# Create a session instance
session = SQLiteSession("conversation_123")
async def main():
    query = input("What would you like to generate? ")
    print(query)
# First turn
    result_1 = await Runner.run(
        agent,
        "Our task is to generate the materials needed for 3D CAD generation, given the query. You may need to generate multi-view 2D images with aligned size, as well as metadata.output all the materials that we might need.",
        session=session
    )
    print(result_1.final_output)  # "San Francisco"



if __name__ == "__main__":
    asyncio.run(main())