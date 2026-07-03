/**
 * Standalone demo of the Arcis treasury loop — no ElizaOS required.
 * Shows exactly what the plugin does under the hood.
 *
 *   BASE_RPC_URL=... AGENT_KEY=0x... npx tsx demo.ts
 */
import { createPublicClient, createWalletClient, http, formatUnits, parseUnits } from "viem";
import { base } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import { ArcisVault, IdleCapitalManager, BASE_CONFIG } from "@arcisprotocol/sdk";

const pk = process.env.AGENT_KEY as `0x${string}`;
const rpc = process.env.BASE_RPC_URL || "https://mainnet.base.org";
if (!pk) { console.error("Set AGENT_KEY=0x..."); process.exit(1); }

const account = privateKeyToAccount(pk);
const publicClient = createPublicClient({ chain: base, transport: http(rpc) });
const walletClient = createWalletClient({ chain: base, transport: http(rpc), account });

async function main() {
  const vault = new ArcisVault(BASE_CONFIG, publicClient, walletClient);

  // 1. Show current treasury state
  const [pos, walletUsdc, apy] = await Promise.all([
    vault.position(account.address),
    vault.usdcBalance(account.address),
    vault.apy(),
  ]);
  console.log(`Agent: ${account.address}`);
  console.log(`Wallet USDC:    $${formatUnits(walletUsdc, 6)}`);
  console.log(`Vault position: $${formatUnits(pos.value, 6)} (${pos.shares} raUSDC)`);
  console.log(`Vault APY:      ~${apy}%`);

  // 2. Start the always-on idle capital manager
  const manager = new IdleCapitalManager(BASE_CONFIG, publicClient, walletClient, {
    depositThreshold: parseUnits("100", 6),
    reserveMinimum: parseUnits("20", 6),
    withdrawTrigger: parseUnits("5", 6),
    withdrawAmount: parseUnits("25", 6),
    intervalMs: 120_000,
    onDeposit: (amt, _s, tx) => console.log(`↑ deposited $${formatUnits(amt, 6)} — ${tx}`),
    onWithdraw: (_s, amt, tx) => console.log(`↓ withdrew $${formatUnits(amt, 6)} — ${tx}`),
  });
  manager.start();
  console.log("\nIdle-capital manager running. Idle USDC now auto-compounds. Ctrl-C to stop.");
}

main().catch(console.error);
