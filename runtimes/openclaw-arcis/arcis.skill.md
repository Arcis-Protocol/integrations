# Arcis Treasury Skill

Give your OpenClaw agent a treasury on Base mainnet. Earn yield on idle USDC,
check positions, and manage capital through the Arcis MCP server.

## Capability

The agent can:
- Check the live Arcis vault status (TVL, APY)
- Deposit idle USDC to earn yield (~variable APY via Aave V3)
- Check its treasury position
- List agent-token vaults
- Read agent-credit terms

## Connection

Arcis exposes a Model Context Protocol (MCP) server. Add it to your OpenClaw
`TOOLS.md` (or MCP config):

```
[mcp.arcis]
url = "https://mcp.arcis.money/mcp"
transport = "http"
description = "Arcis treasury — earn yield on idle USDC on Base mainnet"
```

Once connected, the agent has these tools:
- `arcis_vault_status` — live TVL, APY, allocation
- `arcis_vault_balance` — an agent's position
- `arcis_list_vaults` — agent-token vault registry
- `arcis_vault_info` — vault details + deposit instructions
- `arcis_agent_vault_balance` — position in an agent-token vault
- `arcis_credit_status`, `arcis_credit_tiers` — borrowing terms
- `arcis_preview_deposit` — preview shares for a deposit

## Heartbeat routine (optional)

Add to the agent's scheduled routine so idle USDC never sits dead:

> Every 6 hours: check my USDC balance. If it is above my spending buffer,
> use the Arcis tools to deposit the excess into the vault so it earns yield.
> Before any planned spend, withdraw what I need first.

## Why

Agent payment rails (x402) let your agent earn USDC. Arcis is where that idle
USDC works between jobs — same asset, same chain, instantly withdrawable.

Docs: https://arcis.money · https://arcis.money/skills
