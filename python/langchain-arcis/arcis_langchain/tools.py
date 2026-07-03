"""
LangChain tools for the Arcis treasury (Base mainnet).

    from arcis_langchain import get_arcis_tools
    tools = get_arcis_tools(private_key=os.environ["ARCIS_AGENT_PK"])
    # add `tools` to any LangChain agent

Read-only if no key is provided (deposit/withdraw will report that a wallet
is required; all read tools still work).
"""
from __future__ import annotations

from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from .client import ArcisClient, to_usdc, TIER_LABELS


# ── input schemas ──
class AddressInput(BaseModel):
    agent_address: str = Field(description="The agent/wallet address to inspect (0x...).")


class DepositInput(BaseModel):
    amount_usdc: float = Field(description="Amount of USDC to deposit, e.g. 100 for 100 USDC.")


class WithdrawInput(BaseModel):
    shares: int = Field(
        description="Amount of raUSDC shares (raw, 6 decimals) to redeem. "
        "Use check_position to read the agent's share balance first."
    )


class LoanInput(BaseModel):
    loan_id: int = Field(description="The loan id to check.")


def get_arcis_tools(
    private_key: Optional[str] = None,
    rpc_url: str = "https://mainnet.base.org",
) -> List[StructuredTool]:
    """Return the Arcis LangChain tools, bound to one client."""
    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)

    def vault_status() -> str:
        """Get the live Arcis vault status: TVL, APY, and pause state."""
        tvl = client.vault.functions.totalAssets().call()
        paused = client.vault.functions.paused().call()
        apy = client.live_apy()
        return (
            f"Arcis USDC Vault (Base mainnet)\n"
            f"TVL: ${to_usdc(tvl)} USDC\n"
            f"APY: {apy}\n"
            f"Status: {'PAUSED' if paused else 'Active'}"
        )

    def check_position(agent_address: str) -> str:
        """Check an agent's Arcis position: raUSDC shares, USDC value, and remaining deposit capacity."""
        addr = client.w3.to_checksum_address(agent_address)
        shares = client.vault.functions.balanceOf(addr).call()
        value = client.vault.functions.balance(addr).call()
        max_dep = client.vault.functions.maxDeposit(addr).call()
        return (
            f"Agent: {addr}\n"
            f"raUSDC shares (raw): {shares}\n"
            f"Position value: ${to_usdc(value)} USDC\n"
            f"Remaining deposit capacity: ${to_usdc(max_dep)} USDC"
        )

    def credit_status() -> str:
        """Get Arcis credit-module status: lending pool size, total borrowed, and utilization."""
        pool = client.credit.functions.lendingPool().call()
        borrowed = client.credit.functions.totalBorrowed().call()
        total = pool + borrowed
        util = (borrowed / total * 100) if total > 0 else 0
        return (
            f"Lending pool: ${to_usdc(pool)} USDC\n"
            f"Total borrowed: ${to_usdc(borrowed)} USDC\n"
            f"Utilization: {util:.1f}%"
        )

    def collateral_ratio(agent_address: str) -> str:
        """Get an agent's collateral ratio (set by ERC-8004 reputation tier). Lower ratio = better terms."""
        addr = client.w3.to_checksum_address(agent_address)
        ratio_bps = client.credit.functions.getCollateralRatio(addr).call()
        return (
            f"Agent: {addr}\n"
            f"Collateral ratio: {ratio_bps / 100:.1f}% "
            f"(reputation tiers: {', '.join(f'{k}={v}' for k, v in TIER_LABELS.items())})"
        )

    def loan_health(loan_id: int) -> str:
        """Check whether a loan is healthy and the total amount owed."""
        healthy = client.credit.functions.isHealthy(loan_id).call()
        owed = client.credit.functions.totalOwed(loan_id).call()
        return (
            f"Loan #{loan_id}\n"
            f"Total owed: ${to_usdc(owed)} USDC\n"
            f"Status: {'HEALTHY' if healthy else 'AT RISK — repay to avoid liquidation'}"
        )

    def deposit_usdc(amount_usdc: float) -> str:
        """Deposit idle USDC into the Arcis vault to earn yield. Auto-approves USDC. Returns the tx hash."""
        try:
            tx = client.deposit(amount_usdc)
            return f"Deposited ${amount_usdc:,.2f} USDC into the Arcis vault. Tx: {tx}"
        except Exception as e:
            return f"Deposit failed: {e}"

    def withdraw_usdc(shares: int) -> str:
        """Withdraw from the Arcis vault by redeeming raUSDC shares. Returns the tx hash."""
        try:
            tx = client.withdraw_shares(shares)
            return f"Withdrew {shares} raUSDC shares from the Arcis vault. Tx: {tx}"
        except Exception as e:
            return f"Withdraw failed: {e}"

    return [
        StructuredTool.from_function(vault_status, name="arcis_vault_status"),
        StructuredTool.from_function(check_position, name="arcis_check_position", args_schema=AddressInput),
        StructuredTool.from_function(credit_status, name="arcis_credit_status"),
        StructuredTool.from_function(collateral_ratio, name="arcis_collateral_ratio", args_schema=AddressInput),
        StructuredTool.from_function(loan_health, name="arcis_loan_health", args_schema=LoanInput),
        StructuredTool.from_function(deposit_usdc, name="arcis_deposit_usdc", args_schema=DepositInput),
        StructuredTool.from_function(withdraw_usdc, name="arcis_withdraw_usdc", args_schema=WithdrawInput),
    ]
