import {
  GameWorker,
  GameFunction,
  ExecutableGameFunctionResponse,
  ExecutableGameFunctionStatus,
} from "@virtuals-protocol/game";
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

export interface ArcisPluginOptions {
  /** Agent wallet private key (0x-prefixed). Required for deposit/withdraw. Omit for read-only. */
  privateKey?: `0x${string}`;
  /** Base mainnet RPC URL. Defaults to https://mainnet.base.org */
  rpcUrl?: string;
  /** Override the worker id. */
  id?: string;
  /** Override the worker name. */
  name?: string;
  /** Override the worker description. */
  description?: string;
}

/**
 * ArcisPlugin — gives any GAME (Virtuals) agent a treasury on Base mainnet.
 *
 * The agent can earn yield on idle USDC, check its position, discover
 * agent-token vaults, and read its credit terms — all through the Arcis
 * Agent Treasury Interface.
 *
 *   import { GameAgent } from "@virtuals-protocol/game";
 *   import { ArcisPlugin } from "@arcisprotocol/game-plugin-arcis";
 *
 *   const arcis = new ArcisPlugin({ privateKey: process.env.AGENT_PK as `0x${string}` });
 *   const agent = new GameAgent(process.env.GAME_API_KEY!, {
 *     name: "Treasury Agent",
 *     goal: "Keep idle USDC earning yield; withdraw when funds are needed",
 *     description: "An agent that manages its own capital via Arcis",
 *     workers: [arcis.getWorker()],
 *   });
 *   await agent.init();
 *   await agent.run();
 */
export class ArcisPlugin {
  private publicClient: PublicClient;
  private walletClient?: WalletClient;
  private account?: ReturnType<typeof privateKeyToAccount>;
  private vault: ArcisVault;
  private factory: VaultFactory;
  private credit: AgentCredit;

  public readonly id: string;
  public readonly name: string;
  public readonly description: string;

  constructor(options: ArcisPluginOptions = {}) {
    const rpcUrl = options.rpcUrl ?? "https://mainnet.base.org";

    this.publicClient = createPublicClient({
      chain: base,
      transport: http(rpcUrl),
    }) as PublicClient;

    if (options.privateKey) {
      this.account = privateKeyToAccount(options.privateKey);
      this.walletClient = createWalletClient({
        account: this.account,
        chain: base,
        transport: http(rpcUrl),
      });
    }

    this.vault = new ArcisVault(BASE_CONFIG, this.publicClient, this.walletClient);
    this.factory = new VaultFactory(BASE_CONFIG, this.publicClient);
    this.credit = new AgentCredit(BASE_CONFIG, this.publicClient, this.walletClient);

    this.id = options.id ?? "arcis_treasury_worker";
    this.name = options.name ?? "Arcis Treasury Worker";
    this.description =
      options.description ??
      "Manages the agent's on-chain treasury via Arcis on Base mainnet. " +
        "Can earn yield on idle USDC, check the agent's position and the live vault APY, " +
        "list agent-token vaults, and read the agent's credit terms. " +
        "Use whenever the agent has idle USDC that should be productive, or needs to know its treasury state.";
  }

  /** The agent's own address, if a wallet was provided. */
  public get address(): Address | undefined {
    return this.account?.address;
  }

  /** Returns the GameWorker to attach to a GameAgent's `workers` array. */
  public getWorker(): GameWorker {
    return new GameWorker({
      id: this.id,
      name: this.name,
      description: this.description,
      functions: [
        this.depositIdleUsdcFunction,
        this.withdrawFunction,
        this.checkPositionFunction,
        this.listVaultsFunction,
        this.creditTermsFunction,
      ],
      getEnvironment: async () => {
        try {
          const apy = await this.vault.apy();
          const env: Record<string, unknown> = {
            network: "Base mainnet",
            vaultApy: apy,
            hasWallet: Boolean(this.account),
          };
          if (this.account) {
            const pos = await this.vault.position(this.account.address);
            env.treasuryValueUsdc = formatUSDC(pos.value);
            env.idleUsdc = formatUSDC(
              await this.vault.usdcBalance(this.account.address)
            );
          }
          return env;
        } catch {
          return { network: "Base mainnet", hasWallet: Boolean(this.account) };
        }
      },
    });
  }

  // -- Functions -----------------------------------------------------------

  get depositIdleUsdcFunction() {
    return new GameFunction({
      name: "deposit_idle_usdc",
      description:
        "Deposit idle USDC from the agent's wallet into the Arcis vault to earn yield (variable APY via Aave V3). " +
        "Use when the agent holds USDC that isn't needed right now - including USDC earned via x402 or other " +
        "agent-payment rails. USDC approval is handled automatically. Funds stay withdrawable at any time.",
      args: [
        {
          name: "amount",
          description:
            "Amount of USDC to deposit, as a human number (e.g. '100' for 100 USDC). Omit to deposit the full idle wallet balance.",
        },
      ] as const,
      executable: async (args, logger) => {
        try {
          if (!this.walletClient || !this.account) {
            return new ExecutableGameFunctionResponse(
              ExecutableGameFunctionStatus.Failed,
              "No wallet configured. Provide a privateKey to ArcisPlugin to enable deposits."
            );
          }

          let amount: bigint;
          if (args.amount && String(args.amount).toLowerCase() !== "all") {
            amount = parseUSDC(String(args.amount));
          } else {
            amount = await this.vault.usdcBalance(this.account.address);
          }

          if (amount <= 0n) {
            return new ExecutableGameFunctionResponse(
              ExecutableGameFunctionStatus.Failed,
              "No idle USDC available to deposit."
            );
          }

          logger(`Depositing ${formatUSDC(amount)} USDC into the Arcis vault...`);
          const res = await this.vault.deposit(amount);

          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Done,
            `Deposited ${formatUSDC(res.amount)} USDC into the Arcis vault (received ${formatUSDC(
              res.shares
            )} raUSDC shares). Now earning yield; withdrawable anytime. Tx: ${res.txHash}`
          );
        } catch (e) {
          const msg = e instanceof Error ? e.message : "Unknown error";
          logger(`Deposit failed: ${msg}`);
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Failed,
            `Failed to deposit: ${msg}`
          );
        }
      },
    });
  }

  get withdrawFunction() {
    return new GameFunction({
      name: "withdraw_from_treasury",
      description:
        "Withdraw USDC from the Arcis vault back to the agent's wallet. Use when the agent needs liquidity to spend " +
        "(e.g. to pay for an x402 API call or a service). Withdrawals are instant.",
      args: [
        {
          name: "amount",
          description:
            "Amount of USDC to withdraw, as a human number (e.g. '50'). Omit or say 'all' to withdraw the entire position.",
        },
      ] as const,
      executable: async (args, logger) => {
        try {
          if (!this.walletClient || !this.account) {
            return new ExecutableGameFunctionResponse(
              ExecutableGameFunctionStatus.Failed,
              "No wallet configured. Provide a privateKey to ArcisPlugin to enable withdrawals."
            );
          }

          const wantsAll =
            !args.amount || String(args.amount).toLowerCase() === "all";

          let shares: bigint;
          if (wantsAll) {
            const pos = await this.vault.position(this.account.address);
            shares = pos.shares;
          } else {
            shares = await this.vault.sharesForAssets(
              parseUSDC(String(args.amount))
            );
          }

          if (shares <= 0n) {
            return new ExecutableGameFunctionResponse(
              ExecutableGameFunctionStatus.Failed,
              "Nothing to withdraw - the agent has no position in the vault."
            );
          }

          logger(
            wantsAll
              ? "Withdrawing the full Arcis position..."
              : `Withdrawing ${args.amount} USDC from the Arcis vault...`
          );
          const res = await this.vault.withdraw(shares);

          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Done,
            `Withdrew ${formatUSDC(res.amount)} USDC from the Arcis vault. Funds are back in the agent's wallet. Tx: ${res.txHash}`
          );
        } catch (e) {
          const msg = e instanceof Error ? e.message : "Unknown error";
          logger(`Withdraw failed: ${msg}`);
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Failed,
            `Failed to withdraw: ${msg}`
          );
        }
      },
    });
  }

  get checkPositionFunction() {
    return new GameFunction({
      name: "check_treasury_position",
      description:
        "Read the agent's current Arcis position: deposited value including earned yield, share balance, and the " +
        "live vault APY. Read-only - no transaction. Use to decide whether to deposit more or withdraw.",
      args: [
        {
          name: "address",
          description:
            "Optional wallet address to check. Defaults to the agent's own wallet.",
        },
      ] as const,
      executable: async (args, logger) => {
        try {
          const who = (args.address as Address) ?? this.account?.address;
          if (!who) {
            return new ExecutableGameFunctionResponse(
              ExecutableGameFunctionStatus.Failed,
              "No address to check. Provide an address or configure a wallet."
            );
          }
          logger(`Reading Arcis position for ${who}...`);
          const [pos, apy] = await Promise.all([
            this.vault.position(who),
            this.vault.apy(),
          ]);
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Done,
            JSON.stringify({
              address: who,
              positionValueUsdc: formatUSDC(pos.value),
              shares: pos.shares.toString(),
              vaultApy: apy,
              network: "Base mainnet",
            })
          );
        } catch (e) {
          const msg = e instanceof Error ? e.message : "Unknown error";
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Failed,
            `Failed to read position: ${msg}`
          );
        }
      },
    });
  }

  get listVaultsFunction() {
    return new GameFunction({
      name: "list_agent_vaults",
      description:
        "List all agent-token vaults in the Arcis factory registry (e.g. the $CUSTOS vault). " +
        "Use to discover which tokens have a vault the agent can deposit into for custody or credit collateral. Read-only.",
      args: [] as const,
      executable: async (_args, logger) => {
        try {
          logger("Listing Arcis agent-token vaults...");
          const vaults = await this.factory.listVaults();
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Done,
            JSON.stringify(
              vaults.map((v) => ({
                vault: v.vault,
                asset: v.asset,
                name: v.name,
                symbol: v.symbol,
                totalAssets: v.totalAssets.toString(),
                paused: v.paused,
              }))
            )
          );
        } catch (e) {
          const msg = e instanceof Error ? e.message : "Unknown error";
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Failed,
            `Failed to list vaults: ${msg}`
          );
        }
      },
    });
  }

  get creditTermsFunction() {
    return new GameFunction({
      name: "get_credit_terms",
      description:
        "Get the Arcis agent-credit reputation tiers (ERC-8004) and the lending pool size. Use to understand what " +
        "borrow terms the agent may qualify for before borrowing against its position. Read-only.",
      args: [] as const,
      executable: async (_args, logger) => {
        try {
          logger("Reading Arcis credit terms...");
          const pool = await this.credit.lendingPool();
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Done,
            JSON.stringify({
              reputationTiers: TIER_LABELS,
              lendingPoolUsdc: formatUSDC(pool),
              note: "Borrow rate and collateral ratio improve with ERC-8004 reputation tier.",
            })
          );
        } catch (e) {
          const msg = e instanceof Error ? e.message : "Unknown error";
          return new ExecutableGameFunctionResponse(
            ExecutableGameFunctionStatus.Failed,
            `Failed to read credit terms: ${msg}`
          );
        }
      },
    });
  }
}

export default ArcisPlugin;
