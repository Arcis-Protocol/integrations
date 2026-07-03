# @arcisprotocol/game-plugin-arcis

A [GAME](https://docs.game.virtuals.io/) (Virtuals Protocol) plugin that gives any GAME agent a **treasury** on Base mainnet.

Your agent can earn yield on idle USDC, check its position, discover agent-token vaults, and read its credit terms — through the Arcis Agent Treasury Interface, no human in the loop.

> Where it fits: agent-payment rails like **x402** let your agent *earn* USDC. Arcis is where that idle USDC *works* — same asset, same chain, instantly withdrawable when the agent needs to spend again.

## Install

```bash
npm install @arcisprotocol/game-plugin-arcis @virtuals-protocol/game
```

## Usage

```ts
import { GameAgent } from "@virtuals-protocol/game";
import { ArcisPlugin } from "@arcisprotocol/game-plugin-arcis";

const arcis = new ArcisPlugin({
  privateKey: process.env.AGENT_PK as `0x${string}`, // omit for read-only
});

const agent = new GameAgent(process.env.GAME_API_KEY!, {
  name: "Treasury Agent",
  goal: "Keep idle USDC earning yield; withdraw when funds are needed",
  description: "An agent that manages its own capital via Arcis on Base",
  workers: [arcis.getWorker()],
});

await agent.init();
await agent.run();
```

That's it — the agent now has one worker (`Arcis Treasury Worker`) exposing five functions.

## Functions

| Function | What it does | Writes? |
|---|---|---|
| `deposit_idle_usdc` | Deposit idle USDC into the Arcis vault to earn yield (auto-approves). Omit amount to deposit the full idle balance. | ✅ |
| `withdraw_from_treasury` | Withdraw USDC back to the wallet. Omit amount / say "all" for the full position. Instant. | ✅ |
| `check_treasury_position` | Read position value, shares, and live vault APY. | — |
| `list_agent_vaults` | List all agent-token vaults in the factory registry (e.g. `$CUSTOS`). | — |
| `get_credit_terms` | Read ERC-8004 reputation tiers and lending-pool size. | — |

The worker's `getEnvironment()` also surfaces the live vault APY, the agent's treasury value, and its idle USDC balance into the agent's state each planning cycle — so the agent *sees* when it has idle capital to put to work.

## Options

```ts
new ArcisPlugin({
  privateKey,        // 0x-prefixed agent wallet key. Omit → read-only (reads still work).
  rpcUrl,            // defaults to https://mainnet.base.org
  id, name, description, // override the worker identity if you want
});
```

## Read-only mode

Omit `privateKey` and the read functions (`check_treasury_position`, `list_agent_vaults`, `get_credit_terms`) still work — useful for monitoring or research agents. Deposit/withdraw will return a clear "no wallet configured" result.

## Network

Base mainnet (chain `8453`). USDC vault: `0x00325d9da832b38179ed2f0dabd4062d93e325a7`. Full contract list and protocol docs: [arcis.money](https://arcis.money) · [github.com/Arcis-Protocol](https://github.com/Arcis-Protocol)

## License

MIT
