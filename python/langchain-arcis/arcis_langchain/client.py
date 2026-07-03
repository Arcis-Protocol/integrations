"""
Arcis client for LangChain tools — Base mainnet.

Thin web3 wrapper exposing the reads and writes the LangChain tools need.
Live APY is read from the Arcis MCP REST endpoint (same source the
dashboard uses); everything else is read straight from chain.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import requests
from web3 import Web3

# ── Base mainnet (chain 8453) ──
DEFAULT_RPC = "https://mainnet.base.org"
APY_ENDPOINT = "https://mcp.arcis.money/api/vault"

VAULT = Web3.to_checksum_address("0x00325d9da832b38179ed2f0dabd4062d93e325a7")
FACTORY = Web3.to_checksum_address("0x9f5697eEB94ee1C7CEDfEb2080A9398D42170FBC")
CREDIT = Web3.to_checksum_address("0xdf31800e620f728297340d66acf5a306f07ce7a1")
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")

USDC_DECIMALS = 6

# ── Minimal ABIs (only what the tools call; verified against on-chain contracts) ──
VAULT_ABI = [
    {"name": "totalAssets", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "exchangeRate", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "balance", "type": "function", "inputs": [{"name": "agent", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "balanceOf", "type": "function", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "paused", "type": "function", "inputs": [], "outputs": [{"type": "bool"}], "stateMutability": "view"},
    {"name": "maxDeposit", "type": "function", "inputs": [{"name": "agent", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "previewWithdraw", "type": "function", "inputs": [{"name": "shares", "type": "uint256"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "deposit", "type": "function", "inputs": [{"name": "amount", "type": "uint256"}], "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable"},
    {"name": "withdraw", "type": "function", "inputs": [{"name": "shares", "type": "uint256"}], "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable"},
]

CREDIT_ABI = [
    {"name": "lendingPool", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "totalBorrowed", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "getCollateralRatio", "type": "function", "inputs": [{"name": "agent", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "totalOwed", "type": "function", "inputs": [{"name": "loanId", "type": "uint256"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "isHealthy", "type": "function", "inputs": [{"name": "loanId", "type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "view"},
]

ERC20_ABI = [
    {"name": "approve", "type": "function", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "allowance", "type": "function", "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "balanceOf", "type": "function", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
]

TIER_LABELS = {0: "Unranked", 1: "Bronze", 2: "Silver", 3: "Gold", 4: "Platinum"}


def to_usdc(raw: int) -> str:
    return f"{raw / 10**USDC_DECIMALS:,.2f}"


def from_usdc(amount: float) -> int:
    return int(round(amount * 10**USDC_DECIMALS))


@dataclass
class ArcisClient:
    """
    Base mainnet Arcis client.

    Read-only by default. Pass a private_key (or set ARCIS_AGENT_PK) to enable
    deposit/withdraw. Everything is on Base mainnet, chain 8453.
    """

    rpc_url: str = DEFAULT_RPC
    private_key: Optional[str] = None

    def __post_init__(self):
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.vault = self.w3.eth.contract(address=VAULT, abi=VAULT_ABI)
        self.credit = self.w3.eth.contract(address=CREDIT, abi=CREDIT_ABI)
        self.usdc = self.w3.eth.contract(address=USDC, abi=ERC20_ABI)

        key = self.private_key or os.environ.get("ARCIS_AGENT_PK")
        if key:
            self.account = self.w3.eth.account.from_key(key)
        else:
            self.account = None

    # ── reads ──
    def live_apy(self) -> str:
        """Live vault APY from the Arcis MCP endpoint; falls back gracefully."""
        try:
            r = requests.get(APY_ENDPOINT, timeout=8)
            r.raise_for_status()
            data = r.json()
            if data.get("apy"):
                return str(data["apy"])
        except Exception:
            pass
        return "variable (live APY endpoint unavailable)"

    # ── writes ──
    def _require_wallet(self):
        if not self.account:
            raise RuntimeError(
                "No wallet configured. Pass private_key to ArcisClient or set "
                "ARCIS_AGENT_PK to enable deposits/withdrawals."
            )

    def _send(self, tx) -> str:
        signed = self.account.sign_transaction(tx)
        h = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(h, timeout=120)
        return receipt["transactionHash"].hex()

    def _base_tx(self) -> dict:
        return {
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "chainId": 8453,
        }

    def deposit(self, amount_usdc: float) -> str:
        """Approve if needed, then deposit USDC into the vault. Returns tx hash."""
        self._require_wallet()
        raw = from_usdc(amount_usdc)

        allowance = self.usdc.functions.allowance(self.account.address, VAULT).call()
        if allowance < raw:
            approve_tx = self.usdc.functions.approve(VAULT, raw).build_transaction(
                {**self._base_tx(), "gas": 80_000}
            )
            self._send(approve_tx)
            # refresh nonce for the next tx
        dep_tx = self.vault.functions.deposit(raw).build_transaction(
            {**self._base_tx(), "gas": 300_000}
        )
        return self._send(dep_tx)

    def withdraw_shares(self, shares: int) -> str:
        """Withdraw by redeeming raUSDC shares. Returns tx hash."""
        self._require_wallet()
        tx = self.vault.functions.withdraw(shares).build_transaction(
            {**self._base_tx(), "gas": 300_000}
        )
        return self._send(tx)

    @property
    def address(self) -> Optional[str]:
        return self.account.address if self.account else None
