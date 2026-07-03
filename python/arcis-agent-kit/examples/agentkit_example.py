"""
Arcis + Coinbase AgentKit — give an AgentKit agent a treasury on Base.

    pip install arcis-agent-kit coinbase-agentkit coinbase-agentkit-langchain

Because AgentKit has framework extensions for LangChain, Vercel AI SDK, and MCP,
adding this one action provider makes Arcis reachable from all of those too.
"""
import os
from coinbase_agentkit import AgentKit, AgentKitConfig, CdpWalletProvider, CdpWalletProviderConfig
from arcis_agent_kit import arcis_action_provider

wallet_provider = CdpWalletProvider(CdpWalletProviderConfig(
    api_key_id=os.environ["CDP_API_KEY_ID"],
    api_key_secret=os.environ["CDP_API_KEY_SECRET"],
    network_id="base-mainnet",
))

agent_kit = AgentKit(AgentKitConfig(
    wallet_provider=wallet_provider,
    action_providers=[
        arcis_action_provider(private_key=os.environ.get("AGENT_PRIVATE_KEY")),
    ],
))

# Hand agent_kit to your framework extension of choice, e.g.:
#   from coinbase_agentkit_langchain import get_langchain_tools
#   tools = get_langchain_tools(agent_kit)
print("Arcis action provider registered with AgentKit on Base mainnet.")
for action in arcis_action_provider().get_actions():
    print(" -", action.name)
