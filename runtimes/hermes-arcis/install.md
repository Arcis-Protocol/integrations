# Installing the Arcis skill in Hermes Agent

Hermes stores skills as documents in `~/.hermes/skills/`. To add the Arcis
treasury skill:

1. Copy the skill document:
   ```bash
   cp arcis-treasury.md ~/.hermes/skills/arcis-treasury.md
   ```

2. Connect the Arcis MCP server:
   ```bash
   hermes mcp add arcis --url https://mcp.arcis.money/mcp --transport http
   ```

3. Reference it in a task:
   > "I have idle USDC. Use the Arcis treasury skill to put it to work."

Hermes will load the skill document on demand (its skill system loads only the
relevant skill when needed) and call the Arcis MCP tools.
