# arcis-treasury — CoinMarketCap-Marketplace-format skill

Drop-in skill (SKILL.md format) that lets any AI agent discover and use **Arcis Protocol** — the treasury/yield layer for agents on Base — through the Arcis MCP server. Compatible with Claude Code, VS Code, and any MCP client, same as the CoinMarketCap Agent Hub skills.

## Install

1. Copy the skill folder into your agent's skills directory:

```bash
cp -r skills/arcis-treasury /path/to/your/skills/directory/
```

2. Add the Arcis MCP server to your MCP config (public, no API key):

```json
{
  "mcpServers": {
    "arcis": { "url": "https://mcp.arcis.money/mcp" }
  }
}
```

3. Ask your agent: *"What's the Arcis vault earning, and should I put my idle USDC to work?"*

Non-custodial: read tools need no key; deposits are signed by the agent's own wallet.
