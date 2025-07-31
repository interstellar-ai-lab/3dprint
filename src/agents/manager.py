from __future__ import annotations

import asyncio
import time

from rich.console import Console
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.agents import Runner, custom_span, gen_trace_id, trace
from generation_agent import generation_agent
from planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from search_agent import search_agent
from writer_agent import ReportData, writer_agent
from printer import Printer
import tempfile
import base64

class CadManager:
    def __init__(self):
        self.console = Console()
        self.printer = Printer(self.console)

    async def run(self, query: str) -> None:
        trace_id = gen_trace_id()
        with trace("Generation trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                is_done=True,
                hide_checkmark=True,
            )

            self.printer.update_item(
                "starting",
                "Starting generating...",
                is_done=True,
                hide_checkmark=True,
            )
            gen_results = await self._initial_gen(query)
            print(gen_results)
            # while True:
            #     eval = await self._write_report(gen_results)
            #     gen_results = await self._initial_gen(eval)

        #     final_report = f"Report summary\n\n{gen_results.short_summary}"
        #     self.printer.update_item("final_report", final_report, is_done=True)

        #     self.printer.end()

        # print("\n\n=====REPORT=====\n\n")
        # print(f"Report: {report.markdown_report}")
        # print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
        # follow_up_questions = "\n".join(report.follow_up_questions)
        # print(f"Follow up questions: {follow_up_questions}")

    async def _initial_gen(self, query: str) -> WebSearchPlan:
        self.printer.update_item("planning", "Planning generation...")
        result = await Runner.run(
                generation_agent, f"Query: {query}"
            )
        print(result.final_output)
        for item in result.new_items:
            if (
                item.type == "tool_call_item"
                and item.raw_item.type == "image_generation_call"
                and (img_result := item.raw_item.result)
            ):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(base64.b64decode(img_result))
                    temp_path = tmp.name

        return result.final_output_as(WebSearchPlan)

    # async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
    #     self.printer.update_item("writing", "Thinking about report...")
    #     input = f"Original query: {query}\nSummarized search results: {search_results}"
    #     result = await Runner.run(
    #         writer_agent,
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
    #     update_messages = [
    #         "Thinking about report...",
    #         "Planning report structure...",
    #         "Writing outline...",
    #         "Creating sections...",
    #         "Cleaning up formatting...",
    #         "Finalizing report...",
    #         "Finishing report...",
    #     ]

    #     last_update = time.time()
    #     next_message = 0
    #     async for _ in result.stream_events():
    #         if time.time() - last_update > 5 and next_message < len(update_messages):
    #             self.printer.update_item("writing", update_messages[next_message])
    #             next_message += 1
    #             last_update = time.time()

    #     self.printer.mark_item_done("writing")
    #     return result.final_output_as(ReportData)
