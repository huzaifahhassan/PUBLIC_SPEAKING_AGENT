# Full runnable code for the StoryFlowAgent example
import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import LlmAgent, BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event
from pydantic import BaseModel, Field

from typing import List
from pydantic import BaseModel, Field
from google.adk.agents import Agent, SequentialAgent, ParallelAgent,LoopAgent, BaseAgent, LlmAgent

#=====================================================================================================
class script_creator(BaseAgent):

    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    script_creator_agent: LlmAgent
    extract_guiding_info: LlmAgent
    judge1: LlmAgent
    judge2: LlmAgent
    judge3: LlmAgent
    improver_agent : LlmAgent

    loop_agent: LoopAgent
    sequential_agent: SequentialAgent

    # model_config allows setting Pydantic configurations if needed, e.g., arbitrary_types_allowed
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name : str,
        script_creator_agent: LlmAgent,
        extract_guiding_info: LlmAgent,
        judge1: LlmAgent,
        judge2: LlmAgent,
        judge3: LlmAgent,
        improver_agent : LlmAgent,
    ):
        """
        Initializes the ps_coach.

        Args:
            name: Name of the root agent.
            script_creator_agent: script writer agent
            extract_guiding_info: guiding information extraction agent
            judge1: audience resonance and goal alignment judge agent
            judge2: logic and clarity and structure judge agent
            judge3: factuality and accuracy judge agent
            Correct_Incorp : critical incorporation agent
        """
        # Create internal agents *before* calling super().__init__

        parallel_judges = ParallelAgent(
            name="ParallelJudges",
            sub_agents=[judge1, judge2, judge3]
        )

        loop_agent = LoopAgent(
            name="CriticReviserLoop", sub_agents=[parallel_judges, improver_agent ], max_iterations=2
        )



        # Define the sub_agents list for the framework
        sub_agents_list = [
            extract_guiding_info,
            script_creator_agent,
            loop_agent,
        ]

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            script_creator_agent=script_creator_agent,
            extract_guiding_info=extract_guiding_info,
            judge1=judge1,
            judge2=judge2,
            judge3=judge3,
            improver_agent=improver_agent,
            parallel_judges=parallel_judges,
            loop_agent=loop_agent,
            sub_agents=sub_agents_list, # Pass the sub_agents list directly
        )

#=====================================================================================================

@override
async def _run_async_impl(
    self, ctx: InvocationContext
) -> AsyncGenerator[Event, None]:
    """
    Implements the custom orchestration logic for the story workflow.
    Uses the instance attributes assigned by Pydantic (e.g., self.story_generator).
    """
    logger.info(f"[{self.name}] Starting script creation workflow.")

    # 1. Initial Guideline Extractor
    logger.info(f"[{self.name}] Running Extractor...")
    async for event in self.extract_guiding_info.run_async(ctx):
        logger.info(f"[{self.name}] Event from Extractor: {event.model_dump_json(indent=2, exclude_none=True)}")
        yield event

    # Check if story was generated before proceeding
    if "guiding_info" not in ctx.session.state or not ctx.session.state["guiding_info"]:
         logger.error(f"[{self.name}] Failed to extract guiding information. Aborting workflow.")
         return # Stop processing if initial story failed


    # 2. Script Creator
    logger.info(f"[{self.name}] Running Script Creator Agent...")
    # Running the script creator
    async for event in self.script_creator_agent.run_async(ctx):
        logger.info(f"[{self.name}] Event from Script Creator Agent: {event.model_dump_json(indent=2, exclude_none=True)}")
        yield event


    # 3. Loop Agent for Critic and Improver
    logger.info(f"[{self.name}] Running Loop Agent...")
    # Use the loop_agent instance attribute assigned during init
    async for event in self.loop_agent.run_async(ctx):
        logger.info(f"[{self.name}] Event from PostProcessing: {event.model_dump_json(indent=2, exclude_none=True)}")
        yield event

    # We will add logic later

    # # 4. Tone-Based Conditional Logic
    # tone_check_result = ctx.session.state.get("tone_check_result")
    # logger.info(f"[{self.name}] Tone check result: {tone_check_result}")

    # if tone_check_result == "negative":
    #     logger.info(f"[{self.name}] Tone is negative. Regenerating story...")
    #     async for event in self.story_generator.run_async(ctx):
    #         logger.info(f"[{self.name}] Event from StoryGenerator (Regen): {event.model_dump_json(indent=2, exclude_none=True)}")
    #         yield event
    # else:
    #     logger.info(f"[{self.name}] Tone is not negative. Keeping current story.")
    #     pass

    # logger.info(f"[{self.name}] Workflow finished.")