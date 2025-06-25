from google.adk.agents import Agent, SequentialAgent, ParallelAgent,LoopAgent
from google.adk.tools import google_search
from .sub_agents.script_creator_agent import script_creator_agent
from .sub_agents.extract_guiding_info import extract_guiding_info
from .sub_agents.judge1 import judge_1
from .sub_agents.judge2 import judge_2
from .sub_agents.judge3 import judge_3
from .sub_agents.Correct_Incorp import Correct_Incorp

def functionality():
    """ Describes the Functionality of the Root Agent """
    text = """This is what I can do:
    1. Create a Script
    2. Improve a Script for a Specific Category"""
    return {
        "Agent Functionality": text,
    }

judge_agents = ParallelAgent( 
    name="Judge_Agents",
    description="Judge Agent",
    sub_agents=[judge_1, judge_2, judge_3],
    )

root_agent = SequentialAgent( 
    name="Root_Agent",
    description="Root Agent",
    sub_agents=[extract_guiding_info, script_creator_agent, judge_agents, Correct_Incorp],
    )

Text = "I am going to do stand up comedy at a local bar. I need a script that is funny and engaging. The audience will be young adults, mostly in their 20s and 30s. The goal is to make them laugh and have a good time. The tone should be light-hearted and humorous. The script should be around 10 minutes long."