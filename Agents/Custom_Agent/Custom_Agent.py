from typing import List
from pydantic import BaseModel, Field
from google.adk.agents import Agent, SequentialAgent, ParallelAgent,LoopAgent, BaseAgent, LlmAgent

class script_creator(BaseAgent):
    """
    Custom agent for a story generation and refinement workflow.

    This agent orchestrates a sequence of LLM agents to generate a story,
    critique it, revise it, check grammar and tone, and potentially
    regenerate the story if the tone is negative.
    """

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
            name="paralled_judge",
            sub_agents=[judge1, judge2, judge3]
        )

        loop_agent = LoopAgent(
            name="loop_agent", sub_agents=[parallel_judges, improver_agent ], max_iterations=2
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