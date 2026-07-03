# arcis-langchain

LangChain tools for the [Arcis](https://arcis.money) treasury — let any Python agent earn yield on idle USDC, check its position, and read credit terms, on **Base mainnet**.

> Where it fits: agent-payment rails like **x402** let your agent *earn* USDC. Arcis is where that idle USDC *works* — same asset, same chain, instantly withdrawable when the agent needs to spend.

## Install

```bash
pip install arcis-langchain
```

## Usage

```python
import os
from arcis_langchain import get_arcis_tools

# Pass a key to enable deposit/withdraw; omit for read-only monitoring.
tools = get_arcis_tools(private_key=os.environ.get("ARCIS_AGENT_PK"))

# Add `tools` to any LangChain agent:
from langchain.agents import create_tool_calling_agent, AgentExecutor
# ... agent = create_tool_calling_agent(llm, tools, prompt) ...
```

That's it — your agent now has 7 Arcis tools.

## Tools

| Tool | What it does | Needs key? |
|---|---|---|
| `arcis_vault_status` | Live vault TVL, APY, pause state | — |
| `arcis_check_position` | An agent's raUSDC shares, USDC value, remaining capacity | — |
| `arcis_credit_status` | Lending pool size, total borrowed, utilization | — |
| `arcis_collateral_ratio` | An agent's collateral ratio by ERC-8004 reputation tier | — |
| `arcis_loan_health` | Whether a loan is healthy and total owed | — |
| `arcis_deposit_usdc` | Deposit idle USDC to earn yield (auto-approves) | ✅ |
| `arcis_withdraw_usdc` | Withdraw by redeeming raUSDC shares | ✅ |

The five read tools work with no wallet — good for monitoring and research agents. The two write tools need a key (constructor arg or `ARCIS_AGENT_PK`).

## Direct client (no LangChain)

```python
from arcis_langchain import ArcisClient

c = ArcisClient(private_key="0x...")   # or ARCIS_AGENT_PK
print(c.live_apy())
tx = c.deposit(100)         # 100 USDC, auto-approves
```

## Live APY

`arcis_vault_status` and `ArcisClient.live_apy()` read the current APY from the Arcis MCP endpoint (`https://mcp.arcis.money/api/vault`) — the same source the dashboard uses — and fall back gracefully if it's unreachable.

## Network

Base mainnet (chain `8453`). USDC vault `0x00325d9da832b38179ed2f0dabd4062d93e325a7`. Full docs: [arcis.money](https://arcis.money) · [github.com/Arcis-Protocol](https://github.com/Arcis-Protocol)

## License

MIT
