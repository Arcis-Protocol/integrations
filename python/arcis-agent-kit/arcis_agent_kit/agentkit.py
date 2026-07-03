"""
Coinbase AgentKit action provider for Arcis.

Gives any AgentKit agent an Arcis treasury on Base mainnet. Because AgentKit
has framework extensions for LangChain, Vercel AI SDK, and MCP, this single
provider makes Arcis usable from all of those too.

    from coinbase_agentkit import AgentKit, AgentKitConfig
    from arcis_agent_kit.agentkit import arcis_action_provider

    agent_kit = AgentKit(AgentKitConfig(
        wallet_provider=wallet_provider,          # Base mainnet
        action_providers=[arcis_action_provider(private_key=...)],
    ))

Built against the documented AgentKit interface: an ActionProvider subclass
whose methods are decorated with @create_action (name, description, schema).
Actions return strings. Executes through the shared Arcis dispatcher, so
behavior matches every other Arcis framework adapter.
"""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field

from .client import ArcisClient
from .spec import dispatch


# ── Action schemas (pydantic, per AgentKit convention) ──
class VaultStatusSchema(BaseModel):
    pass


class CheckPositionSchema(BaseModel):
    agent_address: str = Field(..., description="Wallet address to inspect (0x...).")


class CreditStatusSchema(BaseModel):
    pass


class DepositSchema(BaseModel):
    amount_usdc: float = Field(..., description="USDC to deposit, e.g. 100.")


class WithdrawSchema(BaseModel):
    shares: int = Field(..., description="raUSDC shares (raw, 6 decimals) to redeem.")


def arcis_action_provider(
    private_key: str | None = None,
    rpc_url: str = "https://mainnet.base.org",
):
    """
    Build the Arcis AgentKit action provider.

    Imports AgentKit lazily so this module can be imported even when AgentKit
    isn't installed (the rest of arcis-agent-kit has no AgentKit dependency).
    """
    try:
        from coinbase_agentkit import ActionProvider, create_action  # type: ignore
        from coinbase_agentkit.network import Network  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise ImportError(
            "Coinbase AgentKit is not installed. `pip install coinbase-agentkit` "
            "to use arcis_action_provider()."
        ) from e

    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)

    class ArcisActionProvider(ActionProvider):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__("arcis", [])

        # Base mainnet only.
        def supports_network(self, network: "Network") -> bool:  # type: ignore[name-defined]
            chain_id = getattr(network, "chain_id", None)
            return chain_id in (None, "8453", 8453)

        @create_action(
            name="arcis_vault_status",
            description="Get the live Arcis vault status on Base: TVL, APY, pause state.",
            schema=VaultStatusSchema,
        )
        def vault_status(self, args: Dict[str, Any]) -> str:
            return dispatch(client, "arcis_vault_status", {})

        @create_action(
            name="arcis_check_position",
            description="Check an agent's Arcis position: raUSDC shares, USDC value, remaining capacity.",
            schema=CheckPositionSchema,
        )
        def check_position(self, args: Dict[str, Any]) -> str:
            return dispatch(client, "arcis_check_position", {"agent_address": args["agent_address"]})

        @create_action(
            name="arcis_credit_status",
            description="Get Arcis credit-module status: lending pool, borrowed, utilization.",
            schema=CreditStatusSchema,
        )
        def credit_status(self, args: Dict[str, Any]) -> str:
            return dispatch(client, "arcis_credit_status", {})

        @create_action(
            name="arcis_deposit_usdc",
            description="Deposit idle USDC into the Arcis vault to earn yield. Auto-approves. Needs a wallet.",
            schema=DepositSchema,
        )
        def deposit_usdc(self, args: Dict[str, Any]) -> str:
            return dispatch(client, "arcis_deposit_usdc", {"amount_usdc": args["amount_usdc"]})

        @create_action(
            name="arcis_withdraw_usdc",
            description="Withdraw from the Arcis vault by redeeming raUSDC shares. Needs a wallet.",
            schema=WithdrawSchema,
        )
        def withdraw_usdc(self, args: Dict[str, Any]) -> str:
            return dispatch(client, "arcis_withdraw_usdc", {"shares": args["shares"]})

    return ArcisActionProvider()
