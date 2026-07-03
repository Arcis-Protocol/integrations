"""CrewAI with Arcis tools. `pip install crewai arcis-agent-kit`"""
import os
from crewai import Agent, Task, Crew
from arcis_agent_kit import get_crewai_tools

tools = get_crewai_tools(private_key=os.environ.get("ARCIS_AGENT_PK"))

treasurer = Agent(
    role="Treasury Manager",
    goal="Keep the agent's idle USDC earning yield in Arcis and monitor its position",
    backstory="An autonomous treasurer that manages capital on Base mainnet via Arcis.",
    tools=tools,
    verbose=True,
)

task = Task(
    description="Check the Arcis vault status and report what an agent would earn by depositing idle USDC.",
    expected_output="A concise report of the vault's TVL, APY, and a deposit recommendation.",
    agent=treasurer,
)

crew = Crew(agents=[treasurer], tasks=[task], verbose=True)
print(crew.kickoff())
