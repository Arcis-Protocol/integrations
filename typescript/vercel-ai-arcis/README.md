# @arcisprotocol/vercel-ai-arcis

Vercel AI SDK tools for the **Arcis treasury** on Base mainnet. Give any model
an agent treasury: earn yield on idle USDC, check positions, borrow against
reputation — all through the AI SDK's `tools` interface.

```bash
npm install @arcisprotocol/vercel-ai-arcis ai
```

```ts
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { getArcisTools } from "@arcisprotocol/vercel-ai-arcis";

const { text } = await generateText({
  model: openai("gpt-4o"),
  tools: getArcisTools({ privateKey: process.env.AGENT_PK as `0x${string}` }),
  maxSteps: 5,
  prompt: "What is the Arcis vault earning, and should I deposit 100 idle USDC?",
});
```

Omit `privateKey` for read-only use (status, position, vault list, credit terms
still work). Reads and writes go straight to Base mainnet via the audited
`@arcisprotocol/sdk`.

## Tools

| Tool | Wallet needed | Purpose |
|---|---|---|
| `arcis_vault_status` | no | TVL, APY, pause state |
| `arcis_check_position` | no | position value, shares, live APY |
| `arcis_list_vaults` | no | agent-token vaults (e.g. $CUSTOS) |
| `arcis_credit_terms` | no | ERC-8004 tiers + lending pool |
| `arcis_deposit_usdc` | yes | deposit idle USDC (auto-approves) |
| `arcis_withdraw_usdc` | yes | withdraw (amount or full position) |

## Why

x402 is how agents *earn* USDC. Arcis is where that idle USDC *works* — same
asset, same chain, no bridging.

MIT · [arcis.money](https://arcis.money)
