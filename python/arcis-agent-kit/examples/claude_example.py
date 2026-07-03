"""Claude (Anthropic) with Arcis tools. `pip install anthropic arcis-agent-kit`"""
import os
from anthropic import Anthropic
from arcis_agent_kit import ArcisClient, anthropic_tools, handle_tool_call

client = Anthropic()
arcis = ArcisClient(private_key=os.environ.get("ARCIS_AGENT_PK"))
messages = [{"role": "user", "content": "Check the Arcis vault status and my position at 0xYourAddress."}]

while True:
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1024, messages=messages, tools=anthropic_tools()
    )
    if resp.stop_reason != "tool_use":
        print("".join(b.text for b in resp.content if b.type == "text"))
        break
    messages.append({"role": "assistant", "content": resp.content})
    results = []
    for block in resp.content:
        if block.type == "tool_use":
            out = handle_tool_call(arcis, block.name, block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
    messages.append({"role": "user", "content": results})
