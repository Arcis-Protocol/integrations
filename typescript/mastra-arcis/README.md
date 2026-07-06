# @arcisprotocol/mastra-arcis

[Mastra](https://mastra.ai) tools for the **Arcis** treasury — the money layer for AI agents on Base mainnet. Give any Mastra agent the ability to earn yield on idle USDC, read its position, and check credit, all through the Agent Treasury Interface.

```bash
npm i @arcisprotocol/mastra-arcis
```

```ts
import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { getArcisTools } from "@arcisprotocol/mastra-arcis";

const treasury = new Agent({
  name: "treasury",
  instructions: "You manage the agent's idle USDC through Arcis on Base.",
  model: openai("gpt-4o"),
  tools: getArcisTools({ privateKey: process.env.AGENT_PK as `0x${string}` }),
});

const res = await treasury.generate("What's the vault earning, and should I deposit my idle 100 USDC?");
console.log(res.text);
```

Reads (`arcis_vault_status`, `arcis_position`, `arcis_credit_status`) work with no key.
Writes (`arcis_deposit`, `arcis_withdraw`) require `privateKey`. Non-custodial — the key stays in your process.

MIT · [docs.arcis.money](https://docs.arcis.money)
