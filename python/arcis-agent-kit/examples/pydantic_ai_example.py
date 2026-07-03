"""
Arcis + Pydantic AI — a treasury-aware agent.

    pip install arcis-agent-kit pydantic-ai
"""
import os
import asyncio
from pydantic_ai import Agent
from arcis_agent_kit import get_pydantic_ai_toolset

agent = Agent(
    "openai:gpt-4o",
    toolsets=[get_pydantic_ai_toolset(private_key=os.environ.get("AGENT_PRIVATE_KEY"))],
    instructions=(
        "You manage an AI agent's treasury on Arcis (Base mainnet). Idle USDC — "
        "including x402 revenue — should earn yield. Check the vault before acting."
    ),
)

async def main():
    result = await agent.run(
        "What is the Arcis vault earning right now, and should I deposit 100 idle USDC?"
    )
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
