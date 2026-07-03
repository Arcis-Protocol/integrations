/**
 * Example: a GAME agent that manages its own treasury via Arcis.
 *
 * Run:
 *   export GAME_API_KEY=...        # from https://console.game.virtuals.io/
 *   export AGENT_PK=0x...          # the agent's wallet private key (Base mainnet)
 *   npx tsx examples/treasury-agent.ts
 */
import { GameAgent } from "@virtuals-protocol/game";
import { ArcisPlugin } from "../src/index.js";

const arcis = new ArcisPlugin({
  privateKey: process.env.AGENT_PK as `0x${string}` | undefined,
});

const agent = new GameAgent(process.env.GAME_API_KEY!, {
  name: "Treasury Agent",
  goal:
    "Keep the agent's idle USDC earning yield in Arcis, and withdraw when funds are needed to spend. " +
    "Maintain a small spending buffer; deposit the rest.",
  description:
    "An autonomous agent on Base mainnet that treats Arcis as its treasury. It earns yield on idle USDC " +
    "(including revenue earned via x402), checks its position, and withdraws when it needs liquidity.",
  workers: [arcis.getWorker()],
});

async function main() {
  agent.setLogger((agent, msg) => {
    console.log(`\n[${agent.name}] ${msg}`);
  });

  await agent.init();

  // Run a few autonomous steps. In production you'd loop with agent.step()
  // on a schedule, or call agent.run() for continuous operation.
  for (let i = 0; i < 3; i++) {
    await agent.step();
  }
}

main().catch(console.error);
