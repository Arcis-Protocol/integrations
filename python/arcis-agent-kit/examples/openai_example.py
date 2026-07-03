"""OpenAI (GPT) with Arcis tools. `pip install openai arcis-agent-kit`"""
import json, os
from openai import OpenAI
from arcis_agent_kit import ArcisClient, openai_tools, handle_tool_call

oai = OpenAI()
arcis = ArcisClient(private_key=os.environ.get("ARCIS_AGENT_PK"))
messages = [{"role": "user", "content": "What is the Arcis vault earning right now, and should my agent deposit 100 idle USDC?"}]

resp = oai.chat.completions.create(model="gpt-4o", messages=messages, tools=openai_tools())
msg = resp.choices[0].message

while msg.tool_calls:
    messages.append(msg)
    for call in msg.tool_calls:
        out = handle_tool_call(arcis, call.function.name, json.loads(call.function.arguments))
        messages.append({"role": "tool", "tool_call_id": call.id, "content": out})
    resp = oai.chat.completions.create(model="gpt-4o", messages=messages, tools=openai_tools())
    msg = resp.choices[0].message

print(msg.content)
