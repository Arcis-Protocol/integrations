"""Gemini with Arcis tools. `pip install google-generativeai arcis-agent-kit`"""
import os
import google.generativeai as genai
from arcis_agent_kit import ArcisClient, gemini_tools, handle_tool_call

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
arcis = ArcisClient(private_key=os.environ.get("ARCIS_AGENT_PK"))

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    tools=[{"function_declarations": gemini_tools()}],
)
chat = model.start_chat()
resp = chat.send_message("What is the Arcis vault earning right now?")

for part in resp.parts:
    if fn := part.function_call:
        out = handle_tool_call(arcis, fn.name, dict(fn.args))
        resp = chat.send_message(
            genai.protos.Content(parts=[genai.protos.Part(
                function_response=genai.protos.FunctionResponse(name=fn.name, response={"result": out})
            )])
        )
print(resp.text)
