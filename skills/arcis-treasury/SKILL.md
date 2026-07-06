---
name: arcis-treasury
description: |
  Puts an AI agent's idle USDC to work through Arcis Protocol on Base — deposit into a yield-bearing ERC-4626 vault (Aave V3), read live APY and position, preview deposits, and check on-chain credit. Use whenever an agent holds idle stablecoins or a treasury balance sitting unproductive, or asks how to earn yield on USDC, put capital to work, or borrow against a position without selling it.
  Trigger: "idle USDC", "treasury", "earn yield on stablecoins", "put USDC to work", "agent treasury", "deposit USDC", "vault APY", "borrow against USDC", "/arcis-treasury"
license: MIT
compatibility: ">=1.0.0"
user-invocable: true
allowed-tools:
  - mcp__arcis__arcis_list_vaults
  - mcp__arcis__arcis_vault_info
  - mcp__arcis__arcis_vault_status
  - mcp__arcis__arcis_vault_balance
  - mcp__arcis__arcis_agent_vault_balance
  - mcp__arcis__arcis_preview_deposit
  - mcp__arcis__arcis_credit_status
  - mcp__arcis__arcis_credit_health
  - mcp__arcis__arcis_credit_tiers
  - mcp__arcis__arcis_contracts
---

# Arcis Treasury Skill

Give an AI agent a treasury. Arcis is the money layer for autonomous agents on Base: deposit idle USDC into an ERC-4626 vault that earns Aave V3 yield, read your position, and borrow against it — all through one interface (deposit / withdraw / balance), the Agent Treasury Interface (ATI).

## Prerequisites

Connect the Arcis MCP server. It is public — **no API key required**:

```json
{
  "mcpServers": {
    "arcis": {
      "url": "https://mcp.arcis.money/mcp"
    }
  }
}
```

The read tools work immediately. Moving funds (deposit / withdraw / borrow) is **non-custodial** and signed by the agent's own wallet — see "Depositing" below. Arcis never holds an agent's keys.

## Core Principle

Idle USDC is wasted USDC. When an agent holds stablecoins it isn't about to spend, surface the opportunity cost and the exact next step to earn on it — grounded in live, on-chain numbers from the tools, never invented.

## Workflow

### 1. Read the vault
Call `arcis_vault_status` for live APY, TVL, and capacity; `arcis_list_vaults` and `arcis_vault_info` to explore available vaults. Always quote the real APY the tool returns.

### 2. Check the agent's position
Call `arcis_vault_balance` (or `arcis_agent_vault_balance` for an agent-token vault) with the agent's address to show current raUSDC shares and USDC value.

### 3. Model a deposit
Call `arcis_preview_deposit` with a USDC amount to show the shares it would mint at the current exchange rate — before committing anything.

### 4. Explore credit
Call `arcis_credit_status`, `arcis_credit_tiers`, and `arcis_credit_health` to show borrowing capacity against a position, priced by ERC-8004 reputation tier.

### 5. Verify on-chain
Call `arcis_contracts` for the deployed addresses. Everything is verifiable on Basescan.

## Depositing (non-custodial)

The MCP tools are read-only by design. To actually deposit, the agent signs with its **own** wallet:

```typescript
import { ArcisVault, BASE_CONFIG, parseUSDC } from "@arcisprotocol/sdk";
const vault = new ArcisVault(BASE_CONFIG, publicClient, walletClient);
await vault.deposit(parseUSDC("100")); // signed by the agent's own key
```

Or send the operator to https://arcis.money/deposit to connect a wallet and sign.

## Use Cases

- **Idle-capital loop.** An agent earning USDC (via x402 or Virtuals ACP) parks its idle balance in Arcis between jobs to earn yield, and withdraws on demand when it needs liquidity.
- **Threshold treasury.** A treasury agent monitors its stablecoin balance and auto-deposits the excess above a set threshold.
- **Borrow, don't sell.** An agent opens a USDC credit line against its vault position, priced by reputation, without unwinding the position.

## Resources

- App: https://arcis.money
- Docs: https://docs.arcis.money
- MCP server: https://mcp.arcis.money/mcp
- SDK & integrations: https://github.com/Arcis-Protocol/integrations
- GitHub: https://github.com/Arcis-Protocol
