"""
Example: a LangChain agent that manages its Arcis treasury on Base mainnet.

    pip install arcis-langchain langchain langchain-openai
    export OPENAI_API_KEY=...
    export ARCIS_AGENT_PK=0x...     # optional; omit for read-only monitoring
    python examples/treasury_agent.py
"""
import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from arcis_langchain import get_arcis_tools

# Pass a key to enable deposit/withdraw; omit for read-only.
tools = get_arcis_tools(private_key=os.environ.get("ARCIS_AGENT_PK"))

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a treasury agent for Arcis Protocol on Base mainnet. "
     "You help keep idle USDC earning yield and monitor credit health. "
     "When the user has idle USDC, suggest depositing it. When they need to "
     "spend, help them withdraw. Always check the live vault status first. "
     "Be concise and precise with numbers."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    # Read-only example (works without a wallet key):
    result = executor.invoke({
        "input": "What's the current state of the Arcis vault, and what would an "
                 "agent gain by depositing 100 idle USDC here?"
    })
    print("\n" + result["output"])

    # With ARCIS_AGENT_PK set, the agent can actually act:
    # executor.invoke({"input": "Deposit 50 USDC into the vault."})
    # executor.invoke({"input": "Check my position at 0x... and withdraw everything."})
