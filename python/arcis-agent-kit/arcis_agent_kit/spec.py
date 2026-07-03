"""
Framework-agnostic Arcis tool specifications + dispatcher.

One definition of the Arcis treasury capabilities, expressed as plain data,
plus a dispatcher that executes a tool by name. Every framework adapter
(OpenAI, Claude, Gemini, Grok, CrewAI, AutoGen) is built from THIS — so the
behavior is identical everywhere and there is a single source of truth.

    from arcis_agent_kit import ArcisClient, TOOL_SPECS, dispatch

    client = ArcisClient(private_key=...)
    result = dispatch(client, "arcis_vault_status", {})
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .client import ArcisClient, to_usdc, TIER_LABELS


# ── Tool specifications (framework-neutral) ──
# Each: name, description, and JSON-schema-style parameters.
TOOL_SPECS: List[Dict[str, Any]] = [
    {
        "name": "arcis_vault_status",
        "description": "Get the live Arcis vault status on Base mainnet: TVL, APY, and pause state. "
        "Use to see what the vault is currently earning before deciding to deposit.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "arcis_check_position",
        "description": "Check an agent's Arcis position: raUSDC shares, USDC value, and remaining deposit capacity.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_address": {"type": "string", "description": "Wallet address to inspect (0x...)."}
            },
            "required": ["agent_address"],
        },
    },
    {
        "name": "arcis_credit_status",
        "description": "Get Arcis credit-module status: lending pool size, total borrowed, and utilization percent.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "arcis_collateral_ratio",
        "description": "Get an agent's collateral ratio, set by its ERC-8004 reputation tier. Lower ratio = better terms.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_address": {"type": "string", "description": "Wallet address to inspect (0x...)."}
            },
            "required": ["agent_address"],
        },
    },
    {
        "name": "arcis_loan_health",
        "description": "Check whether an Arcis loan is healthy and the total amount owed.",
        "parameters": {
            "type": "object",
            "properties": {"loan_id": {"type": "integer", "description": "The loan id to check."}},
            "required": ["loan_id"],
        },
    },
    {
        "name": "arcis_deposit_usdc",
        "description": "Deposit idle USDC into the Arcis vault to earn yield (~variable APY via Aave V3). "
        "Auto-approves USDC. Use when the agent holds idle USDC — including x402 revenue — that should be productive. "
        "Requires a configured wallet.",
        "parameters": {
            "type": "object",
            "properties": {"amount_usdc": {"type": "number", "description": "USDC to deposit, e.g. 100."}},
            "required": ["amount_usdc"],
        },
    },
    {
        "name": "arcis_withdraw_usdc",
        "description": "Withdraw from the Arcis vault by redeeming raUSDC shares. Instant. Requires a configured wallet.",
        "parameters": {
            "type": "object",
            "properties": {
                "shares": {"type": "integer", "description": "raUSDC shares (raw, 6 decimals) to redeem. Read via arcis_check_position."}
            },
            "required": ["shares"],
        },
    },
]

TOOL_NAMES = [t["name"] for t in TOOL_SPECS]


# ── Executors (the actual behavior, one per tool) ──
def _valid_address(client: ArcisClient, agent_address: str) -> Optional[str]:
    """Return a checksummed address, or None if the input isn't a valid address."""
    try:
        return client.w3.to_checksum_address(agent_address)
    except Exception:  # noqa: BLE001
        return None


def _vault_status(client: ArcisClient, **_: Any) -> str:
    tvl = client.vault.functions.totalAssets().call()
    paused = client.vault.functions.paused().call()
    apy = client.live_apy()
    return (
        f"Arcis USDC Vault (Base mainnet)\n"
        f"TVL: ${to_usdc(tvl)} USDC\n"
        f"APY: {apy}\n"
        f"Status: {'PAUSED' if paused else 'Active'}"
    )


def _check_position(client: ArcisClient, agent_address: str, **_: Any) -> str:
    addr = _valid_address(client, agent_address)
    if addr is None:
        return f"Invalid address: {agent_address!r}. Provide a 0x-prefixed 40-hex-character address."
    shares = client.vault.functions.balanceOf(addr).call()
    value = client.vault.functions.balance(addr).call()
    max_dep = client.vault.functions.maxDeposit(addr).call()
    return (
        f"Agent: {addr}\n"
        f"raUSDC shares (raw): {shares}\n"
        f"Position value: ${to_usdc(value)} USDC\n"
        f"Remaining deposit capacity: ${to_usdc(max_dep)} USDC"
    )


def _credit_status(client: ArcisClient, **_: Any) -> str:
    pool = client.credit.functions.lendingPool().call()
    borrowed = client.credit.functions.totalBorrowed().call()
    total = pool + borrowed
    util = (borrowed / total * 100) if total > 0 else 0
    return (
        f"Lending pool: ${to_usdc(pool)} USDC\n"
        f"Total borrowed: ${to_usdc(borrowed)} USDC\n"
        f"Utilization: {util:.1f}%"
    )


def _collateral_ratio(client: ArcisClient, agent_address: str, **_: Any) -> str:
    addr = _valid_address(client, agent_address)
    if addr is None:
        return f"Invalid address: {agent_address!r}. Provide a 0x-prefixed 40-hex-character address."
    ratio_bps = client.credit.functions.getCollateralRatio(addr).call()
    tiers = ", ".join(f"{k}={v}" for k, v in TIER_LABELS.items())
    return f"Agent: {addr}\nCollateral ratio: {ratio_bps / 100:.1f}%\nReputation tiers: {tiers}"


def _loan_health(client: ArcisClient, loan_id: int, **_: Any) -> str:
    healthy = client.credit.functions.isHealthy(int(loan_id)).call()
    owed = client.credit.functions.totalOwed(int(loan_id)).call()
    return (
        f"Loan #{loan_id}\n"
        f"Total owed: ${to_usdc(owed)} USDC\n"
        f"Status: {'HEALTHY' if healthy else 'AT RISK — repay to avoid liquidation'}"
    )


def _deposit(client: ArcisClient, amount_usdc: float, **_: Any) -> str:
    try:
        tx = client.deposit(float(amount_usdc))
        return f"Deposited ${float(amount_usdc):,.2f} USDC into the Arcis vault. Tx: {tx}"
    except Exception as e:  # noqa: BLE001
        return f"Deposit failed: {e}"


def _withdraw(client: ArcisClient, shares: int, **_: Any) -> str:
    try:
        tx = client.withdraw_shares(int(shares))
        return f"Withdrew {int(shares)} raUSDC shares from the Arcis vault. Tx: {tx}"
    except Exception as e:  # noqa: BLE001
        return f"Withdraw failed: {e}"


_EXECUTORS: Dict[str, Callable[..., str]] = {
    "arcis_vault_status": _vault_status,
    "arcis_check_position": _check_position,
    "arcis_credit_status": _credit_status,
    "arcis_collateral_ratio": _collateral_ratio,
    "arcis_loan_health": _loan_health,
    "arcis_deposit_usdc": _deposit,
    "arcis_withdraw_usdc": _withdraw,
}


def dispatch(client: ArcisClient, name: str, arguments: Dict[str, Any] | None = None) -> str:
    """Execute an Arcis tool by name with a dict of arguments. Returns a string result."""
    fn = _EXECUTORS.get(name)
    if not fn:
        return f"Unknown Arcis tool: {name}"
    try:
        return fn(client, **(arguments or {}))
    except TypeError as e:
        return f"Bad arguments for {name}: {e}"


def get_spec(name: str) -> Dict[str, Any]:
    for s in TOOL_SPECS:
        if s["name"] == name:
            return s
    raise KeyError(name)
