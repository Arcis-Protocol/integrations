import { tool } from "ai";
import { z } from "zod";
import {
  ArcisVault,
  VaultFactory,
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
 * getArcisTools — Vercel AI SDK tools for the Arcis treasury on Base mainnet.
 *
 *   import { generateText } from "ai";
 *   import { openai } from "@ai-sdk/openai";
 *   import { getArcisTools } from "@arcisprotocol/vercel-ai-arcis";
 *
 *   const { text } = await generateText({
 *     model: openai("gpt-4o"),
 *     tools: getArcisTools({ privateKey: process.env.AGENT_PK as `0x${string}` }),
 *     maxSteps: 5,
 *     prompt: "What is the Arcis vault earning, and should I deposit 100 idle USDC?",
 *   });
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
  const factory = new VaultFactory(BASE_CONFIG, publicClient);
  const credit = new AgentCredit(BASE_CONFIG, publicClient, walletClient);

  const needWallet = "No wallet configured. Pass privateKey to getArcisTools to enable this.";

  return {
    arcis_vault_status: tool({
      description:
        "Get the live Arcis vault status on Base mainnet: TVL, APY, pause state. Use before deciding to deposit.",
      parameters: z.object({}),
      execute: async () => {
        const [state, apy] = await Promise.all([vault.state(), vault.apy()]);
        return {
          tvlUsdc: formatUSDC(state.totalAssets),
          apy,
          paused: state.paused,
          network: "Base mainnet",
        };
      },
    }),

    arcis_check_position: tool({
      description:
        "Check an agent's Arcis position: value including earned yield, raUSDC shares, and the live APY.",
      parameters: z.object({
        agentAddress: z.string().describe("Wallet address to inspect (0x...)."),
      }),
      execute: async ({ agentAddress }) => {
        const who = agentAddress as Address;
        const [pos, apy] = await Promise.all([vault.position(who), vault.apy()]);
        return {
          address: who,
          positionValueUsdc: formatUSDC(pos.value),
          shares: pos.shares.toString(),
          vaultApy: apy,
        };
      },
    }),

    arcis_list_vaults: tool({
      description:
        "List all agent-token vaults in the Arcis factory registry (e.g. the $CUSTOS vault).",
      parameters: z.object({}),
      execute: async () => {
        const vaults = await factory.listVaults();
        return vaults.map((v) => ({
          vault: v.vault,
          asset: v.asset,
          name: v.name,
          symbol: v.symbol,
          totalAssets: v.totalAssets.toString(),
          paused: v.paused,
        }));
      },
    }),

    arcis_credit_terms: tool({
      description:
        "Get Arcis agent-credit reputation tiers (ERC-8004) and the lending pool size, to gauge borrow terms.",
      parameters: z.object({}),
      execute: async () => {
        const pool = await credit.lendingPool();
        return {
          reputationTiers: TIER_LABELS,
          lendingPoolUsdc: formatUSDC(pool),
          note: "Rate and collateral ratio improve with reputation tier.",
        };
      },
    }),

    arcis_deposit_usdc: tool({
      description:
        "Deposit idle USDC into the Arcis vault to earn yield (~variable APY via Aave V3). Auto-approves USDC. " +
        "Use for idle USDC — including x402 revenue — that should be productive.",
      parameters: z.object({
        amountUsdc: z.number().describe("Amount of USDC to deposit, e.g. 100."),
      }),
      execute: async ({ amountUsdc }) => {
        if (!walletClient || !account) return { error: needWallet };
        try {
          const res = await vault.deposit(parseUSDC(String(amountUsdc)));
          return {
            deposited: formatUSDC(res.amount),
            sharesReceived: formatUSDC(res.shares),
            txHash: res.txHash,
          };
        } catch (e) {
          return { error: e instanceof Error ? e.message : "deposit failed" };
        }
      },
    }),

    arcis_withdraw_usdc: tool({
      description:
        "Withdraw from the Arcis vault. Provide a USDC amount, or omit to withdraw the full position. Instant.",
      parameters: z.object({
        amountUsdc: z
          .number()
          .optional()
          .describe("USDC to withdraw. Omit to withdraw everything."),
      }),
      execute: async ({ amountUsdc }) => {
        if (!walletClient || !account) return { error: needWallet };
        try {
          let shares: bigint;
          if (amountUsdc === undefined) {
            const pos = await vault.position(account.address);
            shares = pos.shares;
          } else {
            shares = await vault.sharesForAssets(parseUSDC(String(amountUsdc)));
          }
          if (shares <= 0n) return { error: "No position to withdraw." };
          const res = await vault.withdraw(shares);
          return { withdrewUsdc: formatUSDC(res.amount), txHash: res.txHash };
        } catch (e) {
          return { error: e instanceof Error ? e.message : "withdraw failed" };
        }
      },
    }),
  };
}

export default getArcisTools;
