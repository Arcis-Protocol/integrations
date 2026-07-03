# arcis-agent-kit

The Arcis treasury for **every agent framework**. One install, adapters for OpenAI, Claude, Gemini, Grok (xAI), CrewAI, AutoGen, Coinbase AgentKit, Pydantic AI, and Google ADK — plus skill packages for OpenClaw and Hermes. Earn yield on idle USDC, check positions, and manage capital on **Base mainnet**.

> Where it fits: payment rails like **x402** let your agent *earn* USDC. Arcis is where that idle USDC *works* — same asset, same chain, instantly withdrawable when the agent needs to spend.

## Install

```bash
pip install arcis-agent-kit
# framework extras as needed:
pip install "arcis-agent-kit[crewai]"     # CrewAI
pip install "arcis-agent-kit[autogen]"    # AutoGen
pip install "arcis-agent-kit[agentkit]"   # Coinbase AgentKit
pip install "arcis-agent-kit[pydantic-ai]" # Pydantic AI
pip install "arcis-agent-kit[google-adk]" # Google ADK
```

## One spec, every framework

All adapters are built from a single shared tool spec + dispatcher, so behavior is identical everywhere. Seven tools: `arcis_vault_status`, `arcis_check_position`, `arcis_credit_status`, `arcis_collateral_ratio`, `arcis_loan_health`, `arcis_deposit_usdc`, `arcis_withdraw_usdc`.

### Provider LLMs (function calling)

```python
from arcis_agent_kit import ArcisClient, openai_tools, handle_tool_call
import json

arcis = ArcisClient(private_key="0x...")           # omit for read-only
tools = openai_tools()                              # or anthropic_tools(), gemini_tools(), grok_tools()

# In your tool-call loop, execute what the model asks for:
out = handle_tool_call(arcis, call.function.name, json.loads(call.function.arguments))
```

| Provider | Schema function | Notes |
|---|---|---|
| OpenAI | `openai_tools()` | Chat Completions / Assistants |
| Claude (Anthropic) | `anthropic_tools()` | Messages API `input_schema` |
| Gemini | `gemini_tools()` | wrap in `{"function_declarations": ...}` |
| Grok (xAI) | `grok_tools()` | OpenAI-compatible; point `base_url` at `api.x.ai` |

`handle_tool_call(client, name, args)` runs the tool and returns a string for any provider.

### Coinbase AgentKit, Pydantic AI, Google ADK

```python
from arcis_agent_kit import arcis_action_provider   # Coinbase AgentKit action provider
from arcis_agent_kit import get_pydantic_ai_toolset  # Pydantic AI FunctionToolset
from arcis_agent_kit import get_adk_tools            # Google ADK FunctionTool list
```

AgentKit is Base/USDC-native, and its framework extensions mean the Arcis action
provider is also reachable from LangChain, the Vercel AI SDK, and MCP.

### Agent libraries

```python
from arcis_agent_kit import get_crewai_tools, get_autogen_tools

crew_tools = get_crewai_tools(private_key="0x...")   # list[crewai BaseTool]
# agent = Agent(role="Treasurer", tools=crew_tools, ...)

for fn, name, desc in get_autogen_tools(private_key="0x..."):
    autogen.register_function(fn, caller=assistant, executor=user, name=name, description=desc)
```

Runnable examples for all six are in [`examples/`](./examples/).

## Self-hosted agents (OpenClaw, Hermes)

These runtimes consume **MCP + a skill file**, not a Python import. Connect the Arcis MCP server once and drop in the skill:

- **OpenClaw** — see [`../openclaw-arcis/`](../openclaw-arcis/): `arcis.skill.md` + `mcp-config.json`. Add `https://mcp.arcis.money/mcp` to your `TOOLS.md`.
- **Hermes Agent** — see [`../hermes-arcis/`](../hermes-arcis/): copy `arcis-treasury.md` to `~/.hermes/skills/`, then `hermes mcp add arcis --url https://mcp.arcis.money/mcp`.

## Read-only mode

Omit the private key and the read tools still work (status, position, credit, vaults) — good for monitoring agents. Write tools report that a wallet is required.

## Live data

`arcis_vault_status` reads the current APY from the Arcis MCP endpoint (same source as the dashboard). All reads hit Base mainnet directly.

## Network

Base mainnet (chain `8453`). USDC vault `0x00325d9da832b38179ed2f0dabd4062d93e325a7`. Docs: [arcis.money](https://arcis.money) · [github.com/Arcis-Protocol](https://github.com/Arcis-Protocol)

## License

MIT
