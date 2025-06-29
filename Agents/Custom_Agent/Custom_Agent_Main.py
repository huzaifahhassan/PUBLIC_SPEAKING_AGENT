from  Custom_Agent.sub_agents.extract_guiding_info.agent import extract_guiding_info
from  Custom_Agent.sub_agents.script_creator_agent.agent import script_creator_agent
from  Custom_Agent.sub_agents.judge1.agent import judge1
from  Custom_Agent.sub_agents.judge2.agent import judge2
from  Custom_Agent.sub_agents.judge3.agent import judge3
from  Custom_Agent.sub_agents.Correct_Incorp.agent import Correct_Incorp
from  Custom_Agent.sub_agents.fact_checker.agent import fact_checker
from  Custom_Agent.sub_agents.note_adder.agent import note_adder
from  Browser_Search.simple_crawl4ai import url_runner

# Full runnable code for the StoryFlowAgent example
import logging
from typing import AsyncGenerator
from typing_extensions import override
import ast
import time


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

from dotenv import load_dotenv
load_dotenv()

# --- Constants ---
APP_NAME = "script_app"
USER_ID = "12345"
SESSION_ID = "123344"
GEMINI_2_FLASH = "gemini-2.0-flash"

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#=====================================================================================================
# CREATING THE CUSTOM AGENT SUB CLASS
#=====================================================================================================
class script_creator(BaseAgent):
    """
    Custom agent for a script generation and refinement workflow.

    This agent orchestrates a sequence of LLM agents to generate a story,
    critique it, revise it, check grammar and tone.
    """

    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    script_creator_agent: LlmAgent
    extract_guiding_info: LlmAgent
    judge1: LlmAgent
    judge2: LlmAgent
    judge3: LlmAgent
    improver_agent : LlmAgent
    note_adder : LlmAgent
    fact_checker : LlmAgent

    loop_agent: LoopAgent
    #sequential_agent: SequentialAgent
    parallel_agent: ParallelAgent

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
        note_adder : LlmAgent,
        fact_checker : LlmAgent,
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
            note_adder : Adds helper notes to the final script
            fact_checker : checks facts and corrects if needed
        """
        # Create internal agents *before* calling super().__init__

        parallel_agent = ParallelAgent(
            name="parallel_agent",
            sub_agents=[judge1, judge2]
        )

        loop_agent = LoopAgent(
            name="loop_agent", sub_agents=[parallel_agent, improver_agent ], max_iterations=1
        )



        # Define the sub_agents list for the framework
        sub_agents_list = [
            extract_guiding_info,
            script_creator_agent,
            loop_agent,
            note_adder,
            fact_checker
        ]

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            name=name,
            script_creator_agent = script_creator_agent,
            extract_guiding_info=extract_guiding_info,
            judge1=judge1,
            judge2=judge2,
            judge3=judge3,
            improver_agent=improver_agent,
            fact_checker = fact_checker,
            note_adder=note_adder,
            parallel_agent=parallel_agent,
            loop_agent=loop_agent,
            sub_agents=sub_agents_list, # Pass the sub_agents list directly
        )

#=====================================================================================================
# CREATING THE EXECUTION LOGIC FOR THE CUSTOM AGENT
#=====================================================================================================

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom orchestration logic for the story workflow.
        Uses the instance attributes assigned by Pydantic (e.g., self.script generator).
        """
        logger.info(f"[{self.name}] Starting script creation workflow.")

        # 1. Initial Guideline Extractor
        logger.info(f"[{self.name}] Running Extractor...")
        async for event in self.extract_guiding_info.run_async(ctx):
            #logger.info(f"[{self.name}] Event from Extractor: {event.model_dump_json(indent=2 , exclude_none=True)}")
            yield event


        # Check if guiding info was generated before proceeding
        if "guiding_info" not in ctx.session.state or not ctx.session.state["guiding_info"]:
            logger.error(f"[{self.name}] Failed to extract guiding information. Aborting workflow.")
            return # Stop processing if initial story failed

        # Extracting Guiding Info From Guiding Info Dictionary
        # Getting the saved string
        raw_guiding_info_str = ctx.session.state.get("guiding_info")
        # Removing unneeded json ``` form start and end
        cleaned_str = raw_guiding_info_str.strip().replace("```json", "").replace("```", "").strip()

        # saving each value against a single global key in the state dictionary
        if ctx.session.state["guiding_info"]:
            ctx.session.state["TOPIC"] = ast.literal_eval(cleaned_str)["TOPIC"]
            ctx.session.state["AUDIENCE_PROFESSION"] = ast.literal_eval(cleaned_str)["AUDIENCE_PROFESSION"]
            ctx.session.state["AUDIENCE_AGE"] = ast.literal_eval(cleaned_str)["AUDIENCE_AGE"]
            ctx.session.state["SPEAKER_GOAL"] = ast.literal_eval(cleaned_str)["SPEAKER_GOAL"]
            ctx.session.state["TONE"] = ast.literal_eval(cleaned_str)["TONE"]
            ctx.session.state["LENGTH"] = ast.literal_eval(cleaned_str)["LENGTH"]
            ctx.session.state["SPECIAL_INSTRUCTIONS"] = ast.literal_eval(cleaned_str)["SPECIAL_INSTRUCTIONS"]


        # 2. Script Creator
        logger.info(f"[{self.name}] Running Script Creator Agent...")
        # Running the script creator
        async for event in self.script_creator_agent.run_async(ctx):
            #logger.info(f"[{self.name}] Event from Script Creator Agent: {event.model_dump_json(indent=2, exclude_none=True)}")
            yield event

        # How to add a time Delay
        # print("Sleeping for 10 seconds")
        # time.sleep(10)
        # print("Waking up after 10 seconds")

        # Custom Looping Agent with While Loop
        while True:

            # Coubt of the No. of Iterations
            COUNTER = 1

            # 3. RUNNING PARALLEL JUDGE AGENT
            logger.info(f"[{self.name}] Running Parallel Judge Agent...")
            async for event in self.parallel_agent.run_async(ctx):
                #logger.info(f"[{self.name}] Event from Parallel: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event

            # GETTING ALL CRITIQUES AS STRING (Not Used Yet)
            critique1 = raw_guiding_info_str = ctx.session.state.get("critique_j1")
            critique2 = raw_guiding_info_str = ctx.session.state.get("critique_j2")

            # 4. RUNNING Improver JUDGE AGENT
            logger.info(f"[{self.name}] Running Improver Agent...")
            async for event in self.improver_agent.run_async(ctx):
                #logger.info(f"[{self.name}] Event from Improver Agent: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event

           # 5. RUNNING FACT EXTRACTOR JUDGE AGENT
            logger.info(f"[{self.name}] Running FACT CHECKING Judge Agent...")
            async for event in self.judge3.run_async(ctx):
                #logger.info(f"[{self.name}] Event from Judge3: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event

            # EXTRACTING FACTS AND STORING IN LIST
            critique3 = raw_guiding_info_str = ctx.session.state.get("critique_j3")
            critique3 = ast.literal_eval(critique3.strip().replace("```json", "").replace("```", "").strip())
            unverified_facts = critique3["global_facts"]

            # LIST OF FACTS
            facts = []
            for i in range(len(unverified_facts)):
                # global_fact_1 (key format)
                key = "global_fact_" + str(i+1)
                facts.append(unverified_facts[key])

            # LIST OF WEB RESULTS (A LIST OF LIST) EACH SUB LIST CONTAINS FIVE RESULTS FOR EACH QUERY
            web_content = []
            for i in range(len(facts)):
                content = url_runner(facts[i])
                content = await content
                web_content.append(content)

            print("Extracted Web Content: " , web_content)

            # Making a Dictionary ( key (fact to be checked) : value (web results))
            facts_and_web_research = {}
            for i in range(len(web_content)):
                key = "global_fact_" + str(i+1)
                fact = unverified_facts[key]
                value = web_content[i]
                combined_value = ' '.join(value)
                facts_and_web_research[fact] = combined_value

            ctx.session.state["facts_and_web_research"] = facts_and_web_research

            # 5. RUNNING FACT CHECKING AND CORRECTOR AGENT
            logger.info(f"[{self.name}] Running FACT CHECKING Judge Agent...")
            async for event in self.fact_checker.run_async(ctx):
                #logger.info(f"[{self.name}] Event from fact_checker: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event


            # 6. HUMAN IN LOOP
            # Response = "more" (Decent but can be improved, Go another turn)
            # Response = "good" (Decent enough. Give the script to the User)
            print("######################################################################")
            print("Here is the IMPROVED Script:")
            improved_script = ctx.session.state.get("script")
            print("START OF SCRIPT")
            print({improved_script})
            print("END OF SCRIPT")
            print("")
            print("######################################################################")
            print("Here is the FACT CHECKED Script:")
            fact_checked = ctx.session.state.get("improved_script")
            print("START OF SCRIPT")
            print({fact_checked})
            print("END OF SCRIPT")
            print("")
            print("######################################################################")  
            print("Give Your Feedback\n Response = 'more' (Decent but can be improved, Go another turn\n Response = 'good' (Decent enough. Give the script to the User) ")
            feedback = input("Your Feedback:")

            if feedback == "more":
                continue

            elif feedback == "good":
                # RUNNING Note Adder AGENT
                logger.info(f"[{self.name}] Running Note Adder Agent...")
                async for event in self.note_adder.run_async(ctx):
                    #logger.info(f"[{self.name}] Event from Improver Agent: {event.model_dump_json(indent=2, exclude_none=True)}")
                    yield event

                script_with_notes = ctx.session.state.get("script_with_notes")

                # Saving Script to File
                text_file = open("Script_With_Notes.txt", "w")
                text_file.write(script_with_notes)
                text_file.close()
                break

            else:
                print("Error")
                break        

#=====================================================================================================
# CREATING SESSION, RUNNER AND CUSTOM AGENT INSTANCE
#=====================================================================================================

# Creator custom agent instance
script_creator_agent_instance = script_creator(
    name="ScriptCreatorAgent",
    script_creator_agent=script_creator_agent,
    extract_guiding_info=extract_guiding_info,
    judge1=judge1,
    judge2=judge2,
    judge3=judge3,
    improver_agent=Correct_Incorp,
    fact_checker= fact_checker,
    note_adder=note_adder,
)

# --- Setup Runner and Session ---
session_service = InMemorySessionService()
initial_state = {}
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
    state=initial_state # Pass initial state here
)
logger.info(f"Initial session state: {session.state}")

runner = Runner(
    agent=script_creator_agent_instance, # Pass the custom orchestrator agent
    app_name=APP_NAME,
    session_service=session_service
)

def call_agent(prompt:str):

    #getting current session

    current_session = session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    if not current_session:
        logger.error("No session found. Please create a session first.")
        return None
    
    content = types.Content(role='user', parts=[types.Part(text=f"{prompt}")])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    final_response = "No final response captured."
    for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            #logger.info(f"Potential final response from [{event.author}]: {event.content.parts[0].text}")
            final_response = event.content.parts[0].text

    #print("\n--- Agent Interaction Result ---")
    #print("Agent Final Response: ", final_response)

    final_session = session_service.get_session(app_name=APP_NAME, 
                                                user_id=USER_ID, 
                                                session_id=SESSION_ID)
    #print("Final Session State:")
    import json
    #print(json.dumps(final_session.state, indent=2))
    #print("-------------------------------\n")

# --- Run the Agent ---
call_agent("I am giving a talk on boosting productivity for modern office work. The audience will be of the age 20-50 and all professional. It should be just 2 mins long and professional and informative. ")