"""
Arcis + Google ADK — treasury tools for a Gemini agent.

    pip install arcis-agent-kit google-adk
"""
import os
from google.adk.agents import LlmAgent
from arcis_agent_kit import get_adk_tools

agent = LlmAgent(
    model="gemini-2.0-flash",
    name="arcis_treasury_agent",
    instruction=(
        "You manage an AI agent's treasury on Arcis (Base mainnet). Put idle USDC "
        "to work and monitor the position. Check the vault before depositing."
    ),
    tools=get_adk_tools(private_key=os.environ.get("AGENT_PRIVATE_KEY")),
)

# Run via the ADK Runner / `adk web`. See https://google.github.io/adk-docs/
print(f"ADK agent '{agent.name}' ready with {len(get_adk_tools())} Arcis tools.")
