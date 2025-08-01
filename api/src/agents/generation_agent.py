from pydantic import BaseModel
from agents import Agent, ImageGenerationTool, Runner, trace, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from agents import set_tracing_disabled

openai_client = AsyncOpenAI(api_key="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")
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



