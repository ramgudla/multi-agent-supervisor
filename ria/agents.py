import importlib
from langchain.agents import create_agent
from deepagents import create_deep_agent
from langchain_core.tools import tool

from .models import get_model
from .tools import get_tools
from .prompts import SUPERVISOR_PROMPT, DEEPAGENT_PROMPT, WORKERS

# ===================================== #
#               MODEL
# ===================================== #

# The model is the reasoning engine of your agent.
llm = get_model()

# ===================================== #
#               PROMPTS
# ===================================== #

def _get_prompts():
    """Get the prompts for each agent"""

    prompts_module_str = "ria.prompts"
    prompts_module = importlib.import_module(prompts_module_str)

    for worker in WORKERS:
        globals()[f"{worker}_agent_prompt"] = str(getattr(prompts_module, f"{worker}_agent_prompt"))
        globals()[f"{worker}_agent_description"] = str(getattr(prompts_module, f"{worker}_agent_description"))

# You can shape how your agent approaches tasks by providing a prompt.
_get_prompts()

# ===================================== #
#               TOOLS
# ===================================== #

# Tools give agents the ability to take actions.
tools = get_tools()

# ===================================== #
#               AGENTS
# ===================================== #

agents = []

# create_agent builds a graph-based agent runtime using LangGraph. 
# A graph consists of nodes (steps) and edges (connections) that define how your agent processes information. 
# The agent moves through this graph, executing nodes like the model node (which calls the model), the tools node (which executes tools), or middleware.
def _create_agents():
    """Create the agents"""
    for worker in WORKERS:
        # `lambda worker_name=worker` defines a single parameter 'worker_name' for the lambda function and assigns it a default value, worker.
        globals()[f"{worker}_agent"] = lambda worker_name=worker : create_agent(
            model=llm,
            tools=tools[f"mcp_{worker_name}_tools"],
            system_prompt=globals()[f"{worker_name}_agent_prompt"]
        )
        agents.append(globals()[f"{worker}_agent"]())

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
    
    for worker in WORKERS:
        # `lambda worker_name=worker` defines a single parameter 'worker_name' for the lambda function and assigns it a default value, worker.
        globals()[f"{worker}_agent_as_tool"] = lambda worker_name=worker : create_agent_as_tool(
            agent_func=globals()[f"{worker_name}_agent"],
            tool_name=f"{worker_name}_agent_tool",
            description=globals()[f"{worker_name}_agent_description"]
        ) 
        supervisor_tools.append(globals()[f"{worker}_agent_as_tool"]())

_create_supervisor_tools()

# ============================================= #
#  SUBAGENTS AS SUPERVISOR TOOLS (ALTERNATIVE)
# ============================================= #

# @tool
# async def devops_agent_as_tool(request: str) -> str:
#     """read metrics, read logs, download logs from mc-dope (devops) servers.

#     Use this when the user wants to read logs, read metrics, download logs, loook for canaries etc from mc_devops server.

#     Input: Natural language devops request (e.g., 'Are there any canary failures in mpaasoicnative tenancy of us-phoenix-1 region for the phonebook oracle integration cloud?')
#     """
#     result = await devops_agent().ainvoke({
#         "messages": [{"role": "user", "content": request}]
#     })
#     return result["messages"][-1].text

# @tool
# async def atlassian_agent_as_tool(request: str) -> str:
#     """read, update comments, re-assign jira issues.

#     Input: Natural language request related to jira issue (e.g., 'Get the details of jira id EHRM-3552 the EHRM project queue')
#     """
#     result = await atlassian_agent().ainvoke({
#         "messages": [{"role": "user", "content": request}]
#     })
#     return result["messages"][-1].text

# ===================================== #
#           SUPERVISOR
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
#    SUBAGENTS OF DEEPAGENT
# ============================= #
sub_agents = []

def _create_subagents():
    """Create subagents"""
    for worker in WORKERS:
        globals()[f"{worker}_subagent"] = {
            "name": f"{worker}_subagent",
            "description": globals()[f"{worker}_agent_description"],
            "system_prompt": globals()[f"{worker}_agent_prompt"],
            "tools": tools[f"mcp_{worker}_tools"] if f"mcp_{worker}_tools" in tools.keys() else [],
        }
        sub_agents.append(globals()[f"{worker}_subagent"])

_create_subagents()

# ====================================== #
#  SUBAGENTS OF DEEPAGENT (ALTERNATIVE)
# ====================================== #

# from .prompts import devops_agent_prompt, atlassian_agent_prompt, math_agent_prompt
# devops_subagent = {
#     "name": "devops_subagent",
#     "description": "Used to research specific AI policy and regulation questions in depth.",
#     "system_prompt": devops_agent_prompt,
#     "tools": tools["mcp_devops_tools"] if "mcp_devops_tools" in tools.keys() else [],
# }

# atlassian_subagent = {
#     "name": "atlassian_subagent",
#     "description": "Critiques AI policy research reports for completeness, clarity, and accuracy.",
#     "system_prompt": atlassian_agent_prompt,
#     "tools": tools["mcp_atlassian_tools"] if "mcp_atlassian_tools" in tools.keys() else [],
# }

# math_subagent = {
#     "name": "math_subagent",
#     "description": "Critiques AI policy research reports for completeness, clarity, and accuracy.",
#     "system_prompt": math_agent_prompt,
#     "tools": tools["mcp_math_tools"] if "mcp_math_tools" in tools.keys() else [],
# }

# sub_agents = [devops_subagent, atlassian_subagent, math_subagent]

# ===================================== #
#            DEEPAGENT
# ===================================== #

def create_deepagent():
    """Create the deepagent that manages the agents"""
    deep_agent = create_deep_agent(
        model=llm,
        tools=[],
        system_prompt=DEEPAGENT_PROMPT,
        subagents=sub_agents,
    )
    return deep_agent
