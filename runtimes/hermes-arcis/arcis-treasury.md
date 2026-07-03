# Skill: Arcis Treasury

Manage an on-chain treasury on Base mainnet via Arcis — earn yield on idle
USDC, check positions, and borrow against reputation.

## When to use

Use this skill whenever I am holding idle USDC (including USDC earned via x402
or other payment rails) that isn't needed right now, or when I need to know my
treasury state, or when I need liquidity and should withdraw.

## How it works

Arcis exposes an MCP server. Connect it once:

```bash
hermes mcp add arcis --url https://mcp.arcis.money/mcp --transport http
```

That gives me these tools:
- `arcis_vault_status` — live vault TVL, APY, allocation
- `arcis_vault_balance` — my position value
- `arcis_preview_deposit` — preview shares before depositing
- `arcis_list_vaults` — agent-token vault registry
- `arcis_vault_info` — vault details + deposit instructions
- `arcis_credit_status`, `arcis_credit_tiers` — borrowing terms

## Routine

1. Check my USDC balance.
2. If it exceeds my spending buffer, deposit the excess into the Arcis vault
   (`arcis_vault_status` to confirm it's active first).
3. Before a planned spend, withdraw what I need — funds return instantly.
4. Periodically check `arcis_vault_balance` to track earned yield.

## Notes

- Network: Base mainnet (chain 8453). Asset: USDC.
- Yield source: Aave V3. ~30% of vault stays liquid for instant withdrawals.
- This is real capital on mainnet — confirm amounts before depositing.

Learn more: https://arcis.money · https://arcis.money/skills
