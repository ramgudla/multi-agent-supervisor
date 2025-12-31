import importlib
from langchain.agents import create_agent
from deepagents import create_deep_agent
from langchain_core.tools import tool

from .llm_provider import LLMRegistry
from .prompts import SUPERVISOR_PROMPT, DEEPAGENT_PROMPT, SUBAGENTS
from .tools import get_tools

# ===================================== #
#               MODEL
# ===================================== #

# The model is the reasoning engine of your agent.
llm = LLMRegistry.get("qwen2.5-14b")

# ===================================== #
#               PROMPTS
# ===================================== #

# prompts are detailed, multi-layered instructions to agents that guide their behavior and decision-making processes.
# You can shape how your agent approaches tasks by providing a prompt.
def _get_prompts():
    """Get the prompts for each agent"""
    prompts_module_str = "ria.prompts"
    prompts_module = importlib.import_module(prompts_module_str)

    for subagent_name in SUBAGENTS:
        globals()[f"{subagent_name}_agent_prompt"] = str(getattr(prompts_module, f"{subagent_name}_agent_prompt"))
        globals()[f"{subagent_name}_agent_description"] = str(getattr(prompts_module, f"{subagent_name}_agent_description"))

_get_prompts()

# ===================================== #
#               TOOLS
# ===================================== #

# Tools give agents the ability to take actions.
tools = get_tools()

# ===================================== #
#               SUBAGENTS
# ===================================== #

# create_agent builds a graph-based agent runtime using LangGraph. 
# A graph consists of nodes (steps) and edges (connections) that define how your agent processes information. 
# The agent moves through this graph, executing nodes like the model node (which calls the model), the tools node (which executes tools), or middleware.
def _create_agents():
    """Create the agents"""
    for subagent_name in SUBAGENTS:
        # `lambda x=subagent_name` defines a single parameter 'x' for the lambda function and assigns it a default value, subagent_name.
        globals()[f"{subagent_name}_agent"] = lambda x=subagent_name : create_agent(
            model=llm,
            tools=tools[f"mcp-{x}"],
            system_prompt=globals()[f"{x}_agent_prompt"]
        )

# Agents combine language models with tools to create systems that can reason about tasks, decide which tools to use,
# and iteratively work towards solutions. An LLM Agent runs tools in a loop to achieve a goal.
_create_agents()

# ===================================== #
#     SUBAGENTS AS SUPERVISOR TOOLS
# ===================================== #

supervisor_tools = []

def _create_supervisor_tools():
    """Create tools from agents"""
    def create_agent_as_tool(agent_func, tool_name: str, description: str):
        """Create a tool from an agent function"""
        @tool(name_or_callable=tool_name, description=description)
        async def agent_as_tool(request: str) -> str:
            result = await agent_func().ainvoke({
                "messages": [{"role": "user", "content": request}]
            })
            return result["messages"][-1].text
        return agent_as_tool
    
    for subagent_name in SUBAGENTS:
        # `lambda x=subagent_name` defines a single parameter 'x' for the lambda function and assigns it a default value, subagent_name.
        globals()[f"{subagent_name}_agent_as_tool"] = lambda x=subagent_name : create_agent_as_tool(
            agent_func=globals()[f"{x}_agent"],
            tool_name=f"{x}_agent_tool",
            description=globals()[f"{x}_agent_description"]
        ) 
        supervisor_tools.append(globals()[f"{subagent_name}_agent_as_tool"]())

_create_supervisor_tools()

# ===================================== #
#              SUPERVISOR
# ===================================== #

def create_supervisor():
    """Create the supervisor that manages the agents"""
    supervisor = create_agent(
        model=llm,
        tools=supervisor_tools,
        system_prompt=SUPERVISOR_PROMPT
    )
    return supervisor

# ============================= #
#           SUBAGENTS
# ============================= #

subagents_ = []

# Define the subagent configurations
def _create_subagents():
    """Create subagents"""
    for subagent_name in SUBAGENTS:
        globals()[f"{subagent_name}_subagent"] = {
            "name": f"{subagent_name}_subagent",
            "description": globals()[f"{subagent_name}_agent_description"],
            "system_prompt": globals()[f"{subagent_name}_agent_prompt"],
            "tools": tools[f"mcp-{subagent_name}"] if f"mcp-{subagent_name}" in tools.keys() else [],
        }
        subagents_.append(globals()[f"{subagent_name}_subagent"])

_create_subagents()

# ===================================== #
#            DEEPAGENT
# ===================================== #

def create_deepagent():
    """Create the deepagent that manages the agents"""
    deepagent = create_deep_agent(
        model=llm,
        tools=[],
        system_prompt=DEEPAGENT_PROMPT,
        subagents=subagents_
    )
    return deepagent
