"""
arcis-agent-kit — the Arcis treasury for every agent framework.

One shared client + tool spec, adapters for OpenAI, Claude, Gemini, Grok (xAI),
CrewAI, AutoGen, Coinbase AgentKit, Pydantic AI, and Google ADK. Base mainnet.
"""
from .client import ArcisClient
from .spec import TOOL_SPECS, TOOL_NAMES, dispatch, get_spec
from .adapters import (
    openai_tools,
    grok_tools,
    anthropic_tools,
    gemini_tools,
    handle_tool_call,
    get_crewai_tools,
    get_autogen_tools,
)

# Optional framework adapters — these import their heavy framework deps lazily
# inside the functions, so importing the package never requires them installed.
from .agentkit import arcis_action_provider
from .pydantic_ai import (
    get_pydantic_ai_toolset,
    get_pydantic_ai_functions,
    get_adk_tools,
)

__all__ = [
    "ArcisClient",
    "TOOL_SPECS", "TOOL_NAMES", "dispatch", "get_spec",
    "openai_tools", "grok_tools", "anthropic_tools", "gemini_tools",
    "handle_tool_call", "get_crewai_tools", "get_autogen_tools",
    "arcis_action_provider",
    "get_pydantic_ai_toolset", "get_pydantic_ai_functions", "get_adk_tools",
]
__version__ = "1.1.0"
