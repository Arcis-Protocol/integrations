import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import {
  ArcisVault,
  AgentCredit,
  BASE_CONFIG,
  formatUSDC,
  parseUSDC,
  TIER_LABELS,
} from "@arcisprotocol/sdk";
import {
  createPublicClient,
  createWalletClient,
  http,
  type Address,
  type PublicClient,
  type WalletClient,
} from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { base } from "viem/chains";

export interface ArcisToolsOptions {
  /** Agent wallet private key. Omit for read-only (reads still work). */
  privateKey?: `0x${string}`;
  /** Base mainnet RPC URL. Defaults to https://mainnet.base.org */
  rpcUrl?: string;
}

/**
 * getArcisTools — Mastra tools for the Arcis treasury on Base mainnet.
 *
 *   import { Agent } from "@mastra/core/agent";
 *   import { openai } from "@ai-sdk/openai";
 *   import { getArcisTools } from "@arcisprotocol/mastra-arcis";
 *
 *   const agent = new Agent({
 *     name: "treasury",
 *     instructions: "You manage the agent's idle USDC through Arcis.",
 *     model: openai("gpt-4o"),
 *     tools: getArcisTools({ privateKey: process.env.AGENT_PK as `0x${string}` }),
 *   });
 *
 * Reads work with no key; deposit/withdraw require `privateKey`.
 */
export function getArcisTools(options: ArcisToolsOptions = {}) {
  const rpcUrl = options.rpcUrl ?? "https://mainnet.base.org";

  const publicClient = createPublicClient({
    chain: base,
    transport: http(rpcUrl),
  }) as PublicClient;

  let walletClient: WalletClient | undefined;
  let account: ReturnType<typeof privateKeyToAccount> | undefined;
  if (options.privateKey) {
    account = privateKeyToAccount(options.privateKey);
    walletClient = createWalletClient({ account, chain: base, transport: http(rpcUrl) });
  }

  const vault = new ArcisVault(BASE_CONFIG, publicClient, walletClient);
  const credit = new AgentCredit(BASE_CONFIG, publicClient, walletClient);

  const requireWallet = () => {
    if (!walletClient || !account) {
      throw new Error("This action moves funds and needs a wallet — pass `privateKey` to getArcisTools().");
    }
    return account.address as Address;
  };

  const arcis_vault_status = createTool({
    id: "arcis_vault_status",
    description: "Get the Arcis raUSDC vault status: live APY and TVL on Base mainnet. Read-only.",
    inputSchema: z.object({}),
    execute: async () => {
      const [state, apy] = await Promise.all([vault.state(), vault.apy()]);
      return { tvlUsdc: formatUSDC(state.totalAssets), apy, paused: state.paused, network: "Base mainnet" };
    },
  });

  const arcis_position = createTool({
    id: "arcis_position",
    description: "Read an agent's Arcis vault position (raUSDC shares + USDC value) and the live APY. Read-only.",
    inputSchema: z.object({
      agentAddress: z.string().describe("Agent wallet address (defaults to your own wallet)"),
    }).partial(),
    execute: async ({ context }) => {
      const who = ((context?.agentAddress as Address) ?? account?.address) as Address;
      if (!who) throw new Error("No address — pass `agentAddress` or set a privateKey.");
      const [pos, apy] = await Promise.all([vault.position(who), vault.apy()]);
      return { address: who, positionValueUsdc: formatUSDC(pos.value), shares: pos.shares.toString(), vaultApy: apy };
    },
  });

  const arcis_deposit = createTool({
    id: "arcis_deposit",
    description: "Deposit idle USDC into the Arcis vault to earn yield. Requires a wallet. Minimum 1 USDC.",
    inputSchema: z.object({ amountUsdc: z.string().describe("USDC amount to deposit, e.g. '100'") }),
    execute: async ({ context }) => {
      requireWallet();
      try {
        const res = await vault.deposit(parseUSDC(String(context.amountUsdc)));
        return { deposited: formatUSDC(res.amount), sharesReceived: formatUSDC(res.shares), txHash: res.txHash, explorer: `https://basescan.org/tx/${res.txHash}` };
      } catch (e) {
        return { error: e instanceof Error ? e.message : "deposit failed" };
      }
    },
  });

  const arcis_withdraw = createTool({
    id: "arcis_withdraw",
    description: "Withdraw from the Arcis vault — redeem raUSDC shares back to USDC. Requires a wallet.",
    inputSchema: z.object({ shares: z.string().describe("raUSDC shares to redeem, or 'max' for the whole position") }),
    execute: async ({ context }) => {
      const me = requireWallet();
      try {
        let shares: bigint;
        if (context.shares === "max") {
          const pos = await vault.position(me);
          shares = pos.shares as bigint;
        } else {
          shares = BigInt(context.shares);
        }
        const res = await vault.withdraw(shares);
        return { withdrewUsdc: formatUSDC(res.amount), txHash: res.txHash, explorer: `https://basescan.org/tx/${res.txHash}` };
      } catch (e) {
        return { error: e instanceof Error ? e.message : "withdraw failed" };
      }
    },
  });

  const arcis_credit_status = createTool({
    id: "arcis_credit_status",
    description: "Get Arcis AgentCredit status: lending-pool liquidity and the reputation-tier table. Read-only.",
    inputSchema: z.object({}),
    execute: async () => {
      const pool = await credit.lendingPool();
      return { lendingPoolUsdc: formatUSDC(pool), reputationTiers: TIER_LABELS, note: "Rate and collateral ratio improve with reputation tier." };
    },
  });

  return { arcis_vault_status, arcis_position, arcis_deposit, arcis_withdraw, arcis_credit_status };
}

export default getArcisTools;
