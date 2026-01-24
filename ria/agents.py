from langchain.agents import create_agent
from deepagents import create_deep_agent
from langchain_core.tools import tool

from .llm_provider import LLMRegistry
from .prompts import *
from .tools import get_tools

# ===================================== #
#               MODEL
# ===================================== #

# The model is the reasoning engine of your agent.
llm = LLMRegistry.get("gpt-41")

# ===================================== #
#               TOOLS
# ===================================== #

# Tools give agents the ability to take actions.
tools = get_tools()

# ===================================== #
#     SUBAGENTS AS SUPERVISOR TOOLS
# ===================================== #

def _create_agent_as_supervisor_tool(subagent: str = None):
    """Create tools from agents"""

    # Function to export an agent as a tool
    def export_agent_as_tool(agent, tool_name: str, tool_description: str):
        """Create a tool from an agent"""
        @tool(name_or_callable=tool_name, description=tool_description)
        async def agent_as_tool(request: str) -> str:
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": request}]
            })
            return result["messages"][-1].text
        return agent_as_tool

    # create_agent builds a graph-based agent runtime using LangGraph. 
    # A graph consists of nodes (steps) and edges (connections) that define how your agent processes information. 
    # The agent moves through this graph, executing nodes like the model node (which calls the model), the tools node (which executes tools), or middleware.
    # Agents combine language models with tools to create systems that can reason about tasks, decide which tools to use and iteratively work towards solutions.
    # An LLM Agent runs tools in a loop to achieve a goal.
    agent = create_agent(
        model=llm,
        tools=tools[f"mcp-{subagent}"] if f"mcp-{subagent}" in tools.keys() else [],
        system_prompt=globals()[f"{subagent}_agent_prompt"]
    )
    agent_as_tool =  export_agent_as_tool(
        agent=agent,
        tool_name=f"{subagent}_agent_tool",
        tool_description=globals()[f"{subagent}_agent_description"]
    )

    return agent_as_tool

# ===================================== #
#              SUPERVISOR
# ===================================== #

def create_supervisor():
    """Create the supervisor that manages the agents"""
    supervisor = create_agent(
        model=llm,
        tools=[_create_agent_as_supervisor_tool(subagent) for subagent in SUBAGENTS],
        system_prompt=SUPERVISOR_PROMPT
    )
    return supervisor

# ============================= #
#           SUBAGENTS
# ============================= #

# Define the subagent configurations
def _create_subagent(subagent: str = None):
    """Create subagents"""
    subagent_config = {
        "name": f"{subagent}_subagent",
        "description": globals()[f"{subagent}_agent_description"],
        "system_prompt": globals()[f"{subagent}_agent_prompt"],
        "tools": tools[f"mcp-{subagent}"] if f"mcp-{subagent}" in tools.keys() else [],
    }

    return subagent_config

# ===================================== #
#            DEEPAGENT
# ===================================== #

def create_deepagent():
    """Create the deepagent that manages the agents"""
    deepagent = create_deep_agent(
        model=llm,
        tools=[],
        system_prompt=DEEPAGENT_PROMPT,
        subagents=[_create_subagent(subagent) for subagent in SUBAGENTS],
    )
    return deepagent
