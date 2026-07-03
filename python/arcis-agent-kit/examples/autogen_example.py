"""AutoGen with Arcis tools. `pip install pyautogen arcis-agent-kit`"""
import os
import autogen
from arcis_agent_kit import get_autogen_tools

config_list = [{"model": "gpt-4o", "api_key": os.environ["OPENAI_API_KEY"]}]

assistant = autogen.AssistantAgent(
    "treasury_assistant",
    llm_config={"config_list": config_list},
    system_message="You manage an agent's Arcis treasury on Base. Use the Arcis tools to check state and act.",
)
user = autogen.UserProxyAgent("user", human_input_mode="NEVER", code_execution_config=False)

# Register each Arcis tool with the assistant (caller) and user proxy (executor).
for fn, name, desc in get_autogen_tools(private_key=os.environ.get("ARCIS_AGENT_PK")):
    autogen.register_function(fn, caller=assistant, executor=user, name=name, description=desc)

user.initiate_chat(assistant, message="What is the Arcis vault earning, and what would depositing 100 USDC do?")
