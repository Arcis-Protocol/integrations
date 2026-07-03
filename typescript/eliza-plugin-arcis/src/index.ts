/**
 * @arcisprotocol/eliza-plugin-arcis
 *
 * Gives any ElizaOS agent a treasury: idle USDC auto-earns a variable APY in the
 * Arcis vault on Base, and is auto-withdrawn when the agent needs to spend.
 *
 * Three actions the agent can call in conversation or autonomously:
 *   DEPOSIT_IDLE   — move idle USDC into the vault
 *   WITHDRAW_FUNDS — pull USDC back out for a payment
 *   CHECK_TREASURY — report position, yield, and vault APY
 *
 * Plus an always-on service that manages idle capital on an interval so the
 * agent earns yield with zero prompting.
 *
 * Targets @elizaos/core 1.x.
 *
 * @see https://arcis.money
 */
import {
  Service,
  type Plugin,
  type IAgentRuntime,
  type Memory,
  type State,
  type Action,
  type ActionResult,
  type HandlerCallback,
} from "@elizaos/core";
import {
  createPublicClient, createWalletClient, http, formatUnits, parseUnits,
  type PublicClient, type WalletClient,
} from "viem";
import { base } from "viem/chains";
import { privateKeyToAccount } from "viem/accounts";
import { IdleCapitalManager, BASE_CONFIG, ArcisVault } from "@arcisprotocol/sdk";

// ── Runtime settings the agent operator provides ──
// getSetting() returns string | boolean | number | null; coerce to string.
function setting(runtime: IAgentRuntime, key: string, fallback = ""): string {
  const v = runtime.getSetting(key);
  return v === null || v === undefined ? fallback : String(v);
}

function getConfig(runtime: IAgentRuntime) {
  const pk = setting(runtime, "ARCIS_AGENT_PRIVATE_KEY") as `0x${string}`;
  const rpc = setting(runtime, "BASE_RPC_URL", "https://mainnet.base.org");
  if (!pk) throw new Error("ARCIS_AGENT_PRIVATE_KEY not set");
  const account = privateKeyToAccount(pk);
  const publicClient = createPublicClient({ chain: base, transport: http(rpc) }) as PublicClient;
  const walletClient = createWalletClient({ chain: base, transport: http(rpc), account }) as WalletClient;
  return { account, publicClient, walletClient };
}

// ═══════════════════════════════════════════════════════════
//  SERVICE — always-on idle capital management
// ═══════════════════════════════════════════════════════════

export class ArcisTreasuryService extends Service {
  static serviceType = "arcis_treasury";
  capabilityDescription =
    "Manages the agent's idle USDC on Base: auto-deposits into the Arcis vault to earn yield and withdraws when funds are needed.";

  private manager?: IdleCapitalManager;

  /** ElizaOS 1.x service factory — constructs, starts, and returns the service. */
  static async start(runtime: IAgentRuntime): Promise<ArcisTreasuryService> {
    const service = new ArcisTreasuryService(runtime);
    const { publicClient, walletClient } = getConfig(runtime);

    service.manager = new IdleCapitalManager(BASE_CONFIG, publicClient, walletClient, {
      depositThreshold: parseUnits(setting(runtime, "ARCIS_DEPOSIT_THRESHOLD", "100"), 6),
      reserveMinimum: parseUnits(setting(runtime, "ARCIS_RESERVE_MIN", "20"), 6),
      withdrawTrigger: parseUnits(setting(runtime, "ARCIS_WITHDRAW_TRIGGER", "5"), 6),
      withdrawAmount: parseUnits(setting(runtime, "ARCIS_WITHDRAW_AMOUNT", "25"), 6),
      intervalMs: 120_000,
      onDeposit: (amt, _shares, tx) =>
        console.log(`[Arcis] Deposited $${formatUnits(amt, 6)} idle USDC -> earning yield. ${tx}`),
      onWithdraw: (_shares, amt, tx) =>
        console.log(`[Arcis] Withdrew $${formatUnits(amt, 6)} for spending. ${tx}`),
    });
    service.manager.start();
    console.log("[Arcis] Treasury service active — idle USDC now auto-compounds.");
    return service;
  }

  async stop(): Promise<void> {
    this.manager?.stop();
  }

  getManager(): IdleCapitalManager | undefined {
    return this.manager;
  }
}

// ═══════════════════════════════════════════════════════════
//  ACTIONS
// ═══════════════════════════════════════════════════════════

const depositAction: Action = {
  name: "DEPOSIT_IDLE",
  similes: ["DEPOSIT_USDC", "EARN_YIELD", "PUT_TO_WORK", "STAKE_IDLE"],
  description: "Deposit the agent's idle USDC into the Arcis vault to earn yield.",
  validate: async (runtime: IAgentRuntime) => !!runtime.getSetting("ARCIS_AGENT_PRIVATE_KEY"),
  handler: async (
    runtime: IAgentRuntime,
    message: Memory,
    _state?: State,
    _opts?: unknown,
    callback?: HandlerCallback,
  ): Promise<ActionResult> => {
    const { publicClient, walletClient } = getConfig(runtime);
    const vault = new ArcisVault(BASE_CONFIG, publicClient, walletClient);

    // Parse an amount from the message, else deposit all idle above reserve.
    const m = message.content.text?.match(/\$?([0-9][0-9,]*\.?[0-9]*)/);
    const walletUsdc = await vault.usdcBalance(walletClient.account!.address);
    let amount: bigint;
    if (m) {
      amount = parseUnits(m[1].replace(/,/g, ""), 6);
    } else {
      const reserve = parseUnits("20", 6);
      amount = walletUsdc > reserve ? walletUsdc - reserve : 0n;
    }
    if (amount <= 0n) {
      const text = "No idle USDC to deposit — wallet is at or below the reserve floor.";
      await callback?.({ text });
      return { success: false, text };
    }
    const { txHash } = await vault.deposit(amount);
    const text = `Deposited $${formatUnits(amount, 6)} into the Arcis vault. Now earning ~${await vault.apy()}% APY via Aave V3.\nTx: https://basescan.org/tx/${txHash}`;
    await callback?.({ text });
    return { success: true, text, data: { txHash } };
  },
  examples: [[
    { name: "{{user1}}", content: { text: "Put my idle USDC to work" } },
    { name: "{{agent}}", content: { text: "Depositing idle USDC into the Arcis vault to earn yield.", actions: ["DEPOSIT_IDLE"] } },
  ]],
};

const withdrawAction: Action = {
  name: "WITHDRAW_FUNDS",
  similes: ["WITHDRAW_USDC", "PULL_FUNDS", "GET_USDC", "UNSTAKE"],
  description: "Withdraw USDC from the Arcis vault back to the agent wallet for spending.",
  validate: async (runtime: IAgentRuntime) => !!runtime.getSetting("ARCIS_AGENT_PRIVATE_KEY"),
  handler: async (
    runtime: IAgentRuntime,
    message: Memory,
    _state?: State,
    _opts?: unknown,
    callback?: HandlerCallback,
  ): Promise<ActionResult> => {
    const { publicClient, walletClient } = getConfig(runtime);
    const vault = new ArcisVault(BASE_CONFIG, publicClient, walletClient);
    const pos = await vault.position(walletClient.account!.address);

    const m = message.content.text?.match(/\$?([0-9][0-9,]*\.?[0-9]*)/);
    let shares: bigint;
    if (m) {
      const usdc = parseUnits(m[1].replace(/,/g, ""), 6);
      shares = await vault.sharesForAssets(usdc);
    } else {
      shares = pos.shares;
    }
    if (shares <= 0n) {
      const text = "No vault position to withdraw.";
      await callback?.({ text });
      return { success: false, text };
    }
    const { txHash } = await vault.withdraw(shares);
    const text = `Withdrew from the Arcis vault to your wallet.\nTx: https://basescan.org/tx/${txHash}`;
    await callback?.({ text });
    return { success: true, text, data: { txHash } };
  },
  examples: [[
    { name: "{{user1}}", content: { text: "I need $50 for a payment" } },
    { name: "{{agent}}", content: { text: "Pulling $50 from the Arcis vault.", actions: ["WITHDRAW_FUNDS"] } },
  ]],
};

const checkAction: Action = {
  name: "CHECK_TREASURY",
  similes: ["TREASURY_STATUS", "VAULT_BALANCE", "MY_YIELD", "CHECK_POSITION"],
  description: "Report the agent's Arcis vault position, value, and current APY.",
  validate: async () => true,
  handler: async (
    runtime: IAgentRuntime,
    _message: Memory,
    _state?: State,
    _opts?: unknown,
    callback?: HandlerCallback,
  ): Promise<ActionResult> => {
    const { publicClient, walletClient } = getConfig(runtime);
    const vault = new ArcisVault(BASE_CONFIG, publicClient, walletClient);
    const [pos, walletUsdc, apy] = await Promise.all([
      vault.position(walletClient.account!.address),
      vault.usdcBalance(walletClient.account!.address),
      vault.apy(),
    ]);
    const text = [
      `Treasury status:`,
      `  Vault position: $${formatUnits(pos.value, 6)} (${pos.shares} raUSDC)`,
      `  Liquid in wallet: $${formatUnits(walletUsdc, 6)}`,
      `  Current APY: ~${apy}% via Aave V3`,
    ].join("\n");
    await callback?.({ text });
    return { success: true, text, data: { position: pos.value.toString(), apy } };
  },
  examples: [[
    { name: "{{user1}}", content: { text: "How much yield am I earning?" } },
    { name: "{{agent}}", content: { text: "Checking your Arcis treasury.", actions: ["CHECK_TREASURY"] } },
  ]],
};

// ═══════════════════════════════════════════════════════════
//  PLUGIN
// ═══════════════════════════════════════════════════════════

export const arcisPlugin: Plugin = {
  name: "arcis",
  description: "Agent treasury on Base — idle USDC earns yield in the Arcis vault, auto-managed.",
  actions: [depositAction, withdrawAction, checkAction],
  services: [ArcisTreasuryService],
  providers: [],
};

export default arcisPlugin;
