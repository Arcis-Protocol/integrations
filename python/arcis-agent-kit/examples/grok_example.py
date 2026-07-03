"""Grok (xAI) with Arcis tools — OpenAI-compatible. `pip install openai arcis-agent-kit`"""
import json, os
from openai import OpenAI
from arcis_agent_kit import ArcisClient, grok_tools, handle_tool_call

# xAI's API is OpenAI-compatible — just point the base_url at x.ai.
xai = OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1")
arcis = ArcisClient(private_key=os.environ.get("ARCIS_AGENT_PK"))
messages = [{"role": "user", "content": "Check the Arcis vault and tell me the current APY."}]

resp = xai.chat.completions.create(model="grok-4", messages=messages, tools=grok_tools())
msg = resp.choices[0].message
while msg.tool_calls:
    messages.append(msg)
    for call in msg.tool_calls:
        out = handle_tool_call(arcis, call.function.name, json.loads(call.function.arguments))
        messages.append({"role": "tool", "tool_call_id": call.id, "content": out})
    resp = xai.chat.completions.create(model="grok-4", messages=messages, tools=grok_tools())
    msg = resp.choices[0].message
print(msg.content)
