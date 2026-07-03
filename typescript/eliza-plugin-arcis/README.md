# @arcisprotocol/eliza-plugin-arcis

Give any ElizaOS agent a treasury. Idle USDC auto-earns a variable APY in the [Arcis](https://arcis.money) vault on Base, and is auto-withdrawn when the agent needs to spend.

Your agent earns yield between jobs without you writing a line of DeFi code.

## What it does

- **Always-on idle capital management** — a background service watches the agent's USDC balance, deposits the excess above a reserve floor, and pulls funds back when the balance runs low. Zero prompting required.
- **Three conversational actions** the agent can also trigger on demand:
  - `DEPOSIT_IDLE` — "put my idle USDC to work"
  - `WITHDRAW_FUNDS` — "I need $50 for a payment"
  - `CHECK_TREASURY` — "how much yield am I earning?"

Under the hood it uses [`@arcisprotocol/sdk`](https://www.npmjs.com/package/@arcisprotocol/sdk). Every deposit and withdrawal is an on-chain transaction verifiable on Basescan.

## Install

```bash
npm install @arcisprotocol/eliza-plugin-arcis @arcisprotocol/sdk
```

## Configure

Add the plugin to your character and set these agent settings:

```json
{
  "name": "MyAgent",
  "plugins": ["@arcisprotocol/eliza-plugin-arcis"],
  "settings": {
    "ARCIS_AGENT_PRIVATE_KEY": "0x...",
    "BASE_RPC_URL": "https://base-mainnet.g.alchemy.com/v2/YOUR_KEY",
    "ARCIS_DEPOSIT_THRESHOLD": "100",
    "ARCIS_RESERVE_MIN": "20",
    "ARCIS_WITHDRAW_TRIGGER": "5",
    "ARCIS_WITHDRAW_AMOUNT": "25"
  }
}
```

| Setting | Meaning | Default |
|---|---|---|
| `ARCIS_AGENT_PRIVATE_KEY` | Agent wallet key (funded with USDC + a little ETH for gas) | required |
| `BASE_RPC_URL` | Base RPC endpoint | public RPC |
| `ARCIS_DEPOSIT_THRESHOLD` | Deposit idle USDC above this ($) | 100 |
| `ARCIS_RESERVE_MIN` | Keep this much liquid for spending ($) | 20 |
| `ARCIS_WITHDRAW_TRIGGER` | Withdraw when wallet drops below this ($) | 5 |
| `ARCIS_WITHDRAW_AMOUNT` | Amount to pull per withdrawal ($) | 25 |

## Use it in code

```ts
import { arcisPlugin } from "@arcisprotocol/eliza-plugin-arcis";

const runtime = new AgentRuntime({
  character,
  plugins: [arcisPlugin],
  // ...
});
```

Once running, the treasury service starts automatically. The agent's idle USDC begins compounding, and the three actions are available in conversation.

## Try it without ElizaOS

A standalone demo shows the exact loop the plugin runs:

```bash
AGENT_KEY=0xYourKey BASE_RPC_URL=https://... npx tsx demo.ts
```

It prints your wallet + vault position and starts the idle-capital manager.

## How the treasury works

```
Agent earns USDC (jobs, x402 payments, tips)
   ↓  balance climbs past ARCIS_DEPOSIT_THRESHOLD
Plugin deposits the excess → receives raUSDC shares → earns a variable APY (Aave V3)
   ↓  agent needs to spend, balance drops below ARCIS_WITHDRAW_TRIGGER
Plugin withdraws ARCIS_WITHDRAW_AMOUNT → USDC back in wallet, ready to pay
```

The vault keeps 30% liquid reserve for instant withdrawals and deploys 70% to Aave V3. A 0.1% fee applies only to withdrawals within 24h of deposit (flash-loan guard).

## Contracts (Base mainnet)

- Vault: `0x00325d9da832b38179ed2f0dabd4062d93e325a7`
- USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`

## Links

- Website: https://arcis.money
- Dashboard: https://arcis.money/dashboard
- SDK: https://www.npmjs.com/package/@arcisprotocol/sdk
- Docs: https://github.com/Arcis-Protocol/docs

---

*MIT · Built on the Agent Treasury Interface — deposit(), withdraw(), balance().*
