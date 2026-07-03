"""
Framework adapters — turn the shared Arcis tool spec into each framework's
native tool format. All adapters execute through the same dispatcher, so
behavior is identical across every framework.

Provider LLMs (function/tool calling):
    openai_tools()      -> OpenAI Chat Completions / Assistants tools schema
    grok_tools()        -> xAI Grok (OpenAI-compatible) — same schema
    anthropic_tools()   -> Claude tool-use schema
    gemini_tools()      -> Gemini function declarations

Agent libraries:
    get_crewai_tools()  -> list[crewai.tools.BaseTool]
    get_autogen_tools() -> list[(callable, name, description)] for AutoGen register

Every function takes the tool schema; execution is via `handle_tool_call`
(providers) or the returned callables (libraries).
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from .client import ArcisClient
from .spec import TOOL_SPECS, dispatch


# ══════════════════════════════════════════════════════════════════
#  Provider LLM schemas (no framework imports needed — plain dicts)
# ══════════════════════════════════════════════════════════════════

def openai_tools() -> List[Dict[str, Any]]:
    """OpenAI (and any OpenAI-compatible API) `tools` array for chat.completions."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in TOOL_SPECS
    ]


# xAI Grok uses the OpenAI-compatible tools schema verbatim.
grok_tools = openai_tools


def anthropic_tools() -> List[Dict[str, Any]]:
    """Claude (Anthropic Messages API) tool-use schema."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in TOOL_SPECS
    ]


def gemini_tools() -> List[Dict[str, Any]]:
    """Gemini function declarations (wrap in {"function_declarations": gemini_tools()})."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"],
        }
        for t in TOOL_SPECS
    ]


def handle_tool_call(client: ArcisClient, name: str, arguments: Dict[str, Any] | None = None) -> str:
    """
    Execute a tool the model asked for. Use this in your provider loop:

      # OpenAI / Grok:
      for call in msg.tool_calls:
          out = handle_tool_call(client, call.function.name, json.loads(call.function.arguments))

      # Claude:
      out = handle_tool_call(client, block.name, block.input)

      # Gemini:
      out = handle_tool_call(client, part.function_call.name, dict(part.function_call.args))
    """
    return dispatch(client, name, arguments or {})


# ══════════════════════════════════════════════════════════════════
#  CrewAI
# ══════════════════════════════════════════════════════════════════

def get_crewai_tools(private_key: str | None = None, rpc_url: str = "https://mainnet.base.org") -> List[Any]:
    """
    Return a list of CrewAI BaseTool instances.

        from arcis_agent_kit import get_crewai_tools
        agent = Agent(role="Treasurer", tools=get_crewai_tools(private_key=...), ...)
    """
    try:
        from crewai.tools import BaseTool  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise ImportError(
            "CrewAI is not installed. `pip install crewai` to use get_crewai_tools()."
        ) from e

    from pydantic import BaseModel, Field, create_model, PrivateAttr

    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)
    tools: List[Any] = []

    # A single generic tool class; each instance carries its own spec.
    class _ArcisTool(BaseTool):
        name: str
        description: str
        args_schema: type[BaseModel]
        _tool_name: str = PrivateAttr()
        _client: Any = PrivateAttr()

        def __init__(self, *, tool_name: str, client_ref: Any, **data: Any):
            super().__init__(**data)
            self._tool_name = tool_name
            self._client = client_ref

        def _run(self, **kwargs: Any) -> str:
            return dispatch(self._client, self._tool_name, kwargs)

    for spec in TOOL_SPECS:
        name = spec["name"]
        props = spec["parameters"].get("properties", {})
        required = set(spec["parameters"].get("required", []))

        fields: Dict[str, Tuple[type, Any]] = {}
        for pname, pinfo in props.items():
            py_type = {"string": str, "number": float, "integer": int, "boolean": bool}.get(
                pinfo.get("type"), str
            )
            default = ... if pname in required else None
            fields[pname] = (py_type, Field(default, description=pinfo.get("description", "")))
        args_model = (
            create_model(f"{name}_Args", **fields) if fields else create_model(f"{name}_Args")
        )

        tools.append(
            _ArcisTool(
                tool_name=name,
                client_ref=client,
                name=name,
                description=spec["description"],
                args_schema=args_model,
            )
        )

    return tools


# ══════════════════════════════════════════════════════════════════
#  AutoGen
# ══════════════════════════════════════════════════════════════════

def get_autogen_tools(
    private_key: str | None = None, rpc_url: str = "https://mainnet.base.org"
) -> List[Tuple[Callable[..., str], str, str]]:
    """
    Return (callable, name, description) tuples for AutoGen.

        from arcis_agent_kit import get_autogen_tools
        for fn, name, desc in get_autogen_tools(private_key=...):
            autogen.register_function(fn, caller=assistant, executor=user_proxy,
                                      name=name, description=desc)

    Each callable has an explicit signature matching the tool's parameters so
    AutoGen can generate the schema.
    """
    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)
    out: List[Tuple[Callable[..., str], str, str]] = []

    for spec in TOOL_SPECS:
        name = spec["name"]
        desc = spec["description"]

        def _make(tool_name: str) -> Callable[..., str]:
            def _fn(**kwargs: Any) -> str:
                return dispatch(client, tool_name, kwargs)
            _fn.__name__ = tool_name
            _fn.__doc__ = desc
            return _fn

        out.append((_make(name), name, desc))

    return out
