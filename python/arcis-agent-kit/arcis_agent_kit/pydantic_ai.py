"""
Pydantic AI and Google ADK adapters for Arcis.

Both frameworks build tool schemas from a plain Python function's signature +
docstring. So both adapters expose the same set of well-documented callables,
bound to one Arcis client, executing through the shared dispatcher.

Pydantic AI:
    from arcis_agent_kit.pydantic_ai import get_pydantic_ai_toolset
    agent = Agent("openai:gpt-4o", toolsets=[get_pydantic_ai_toolset(private_key=...)])

Google ADK:
    from arcis_agent_kit.pydantic_ai import get_adk_tools
    agent = LlmAgent(model="gemini-2.0-flash", tools=get_adk_tools(private_key=...))
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from .client import ArcisClient
from .spec import dispatch


def _build_callables(client: ArcisClient) -> List[Callable[..., str]]:
    """
    Plain, fully-annotated, well-documented functions. Both Pydantic AI and
    Google ADK introspect these to build tool schemas.
    """

    def arcis_vault_status() -> str:
        """Get the live Arcis vault status on Base mainnet: TVL, APY, and pause state."""
        return dispatch(client, "arcis_vault_status", {})

    def arcis_check_position(agent_address: str) -> str:
        """Check an agent's Arcis position.

        Args:
            agent_address: The wallet address to inspect (0x...).
        """
        return dispatch(client, "arcis_check_position", {"agent_address": agent_address})

    def arcis_credit_status() -> str:
        """Get Arcis credit-module status: lending pool size, total borrowed, and utilization."""
        return dispatch(client, "arcis_credit_status", {})

    def arcis_collateral_ratio(agent_address: str) -> str:
        """Get an agent's collateral ratio, set by its ERC-8004 reputation tier.

        Args:
            agent_address: The wallet address to inspect (0x...).
        """
        return dispatch(client, "arcis_collateral_ratio", {"agent_address": agent_address})

    def arcis_loan_health(loan_id: int) -> str:
        """Check whether an Arcis loan is healthy and the total amount owed.

        Args:
            loan_id: The loan id to check.
        """
        return dispatch(client, "arcis_loan_health", {"loan_id": loan_id})

    def arcis_deposit_usdc(amount_usdc: float) -> str:
        """Deposit idle USDC into the Arcis vault to earn yield. Auto-approves. Requires a wallet.

        Args:
            amount_usdc: Amount of USDC to deposit, e.g. 100.
        """
        return dispatch(client, "arcis_deposit_usdc", {"amount_usdc": amount_usdc})

    def arcis_withdraw_usdc(shares: int) -> str:
        """Withdraw from the Arcis vault by redeeming raUSDC shares. Requires a wallet.

        Args:
            shares: raUSDC shares (raw, 6 decimals) to redeem. Read via arcis_check_position.
        """
        return dispatch(client, "arcis_withdraw_usdc", {"shares": shares})

    return [
        arcis_vault_status,
        arcis_check_position,
        arcis_credit_status,
        arcis_collateral_ratio,
        arcis_loan_health,
        arcis_deposit_usdc,
        arcis_withdraw_usdc,
    ]


def get_pydantic_ai_toolset(
    private_key: Optional[str] = None, rpc_url: str = "https://mainnet.base.org"
) -> Any:
    """
    Return a Pydantic AI FunctionToolset with all Arcis tools.

        from pydantic_ai import Agent
        from arcis_agent_kit.pydantic_ai import get_pydantic_ai_toolset
        agent = Agent("openai:gpt-4o", toolsets=[get_pydantic_ai_toolset(private_key=...)])
    """
    try:
        from pydantic_ai import FunctionToolset  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise ImportError(
            "Pydantic AI is not installed. `pip install pydantic-ai` to use get_pydantic_ai_toolset()."
        ) from e

    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)
    return FunctionToolset(tools=_build_callables(client))


def get_pydantic_ai_functions(
    private_key: Optional[str] = None, rpc_url: str = "https://mainnet.base.org"
) -> List[Callable[..., str]]:
    """
    Return the raw callables, for `Agent(tools=[...])` or manual registration.
    Useful if you prefer passing functions directly rather than a toolset.
    """
    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)
    return _build_callables(client)


def get_adk_tools(
    private_key: Optional[str] = None, rpc_url: str = "https://mainnet.base.org"
) -> List[Any]:
    """
    Return a list of Google ADK FunctionTool instances.

        from google.adk.agents import LlmAgent
        from arcis_agent_kit.pydantic_ai import get_adk_tools
        agent = LlmAgent(model="gemini-2.0-flash", tools=get_adk_tools(private_key=...))
    """
    try:
        from google.adk.tools import FunctionTool  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise ImportError(
            "Google ADK is not installed. `pip install google-adk` to use get_adk_tools()."
        ) from e

    client = ArcisClient(rpc_url=rpc_url, private_key=private_key)
    return [FunctionTool(fn) for fn in _build_callables(client)]
