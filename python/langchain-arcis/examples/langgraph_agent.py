"""
Example: a LangGraph agent that manages its Arcis treasury on Base mainnet.

    pip install arcis-langchain langgraph langchain-openai
    export OPENAI_API_KEY=...
    export ARCIS_AGENT_PK=0x...     # optional; omit for read-only monitoring
    python examples/langgraph_agent.py

LangGraph consumes LangChain tools directly, so the same arcis-langchain tools
work unchanged inside a LangGraph ReAct agent.
"""
import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from arcis_langchain import get_arcis_tools

# Pass a key to enable deposit/withdraw; omit for read-only.
tools = get_arcis_tools(private_key=os.environ.get("ARCIS_AGENT_PK"))
llm = ChatOpenAI(model="gpt-4o", temperature=0)

agent = create_react_agent(llm, tools)

if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [("user", "What is the Arcis vault earning, and how much idle USDC should I deposit?")]}
    )
    for message in result["messages"]:
        message.pretty_print()
