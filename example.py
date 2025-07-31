from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel
import asyncio
from openai import AsyncOpenAI
from agents import set_tracing_disabled
# Create agent

openai_client = AsyncOpenAI(api_key="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")
set_tracing_disabled(disabled=True)
model = OpenAIChatCompletionsModel(
    model="gpt-4o",
    openai_client=openai_client
)
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
    model=model
)
# Create a session instance
session = SQLiteSession("conversation_123")
async def main():
# First turn
    result = await Runner.run(
        agent,
        "What city is the Golden Gate Bridge in?",
        session=session
    )
    print(result.final_output)  # "San Francisco"

    # Second turn - agent automatically remembers previous context
    result = await Runner.run(
        agent,       
        "What state is it in?",
        session=session
    )
    print(result.final_output)  # "California"

# Also works with synchronous runner
    # result = Runner.run_sync(
    #     agent,
    #     input ="What's the population?",
    #     session=session
    # )
    # print(result.final_output)  # "Approximately 39 million"
asyncio.run(main())