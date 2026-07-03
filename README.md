# Arcis Integrations

Framework and runtime integrations for [Arcis Protocol](https://arcis.money) — the treasury layer for AI agents on Base mainnet. Every integration reaches the same **Agent Treasury Interface**: `deposit`, `withdraw`, `balance`. Earn a variable APY on idle USDC, auto-manage a treasury, borrow against reputation, discover vaults.

> x402 is how agents earn USDC. Arcis is where it works — same asset, same chain, no bridging.

## Python — `python/`

| Package | Install | Covers |
|---|---|---|
| [`arcis-agent-kit`](python/arcis-agent-kit) | `pip install arcis-agent-kit` | OpenAI · Claude · Gemini · Grok (xAI) · CrewAI · AutoGen · Coinbase AgentKit · Pydantic AI · Google ADK |
| [`arcis-langchain`](python/langchain-arcis) | `pip install arcis-langchain` | LangChain — 7 StructuredTools with live APY |

## TypeScript / JavaScript — `typescript/`

| Package | Install | Framework |
|---|---|---|
| [`@arcisprotocol/vercel-ai-arcis`](typescript/vercel-ai-arcis) | `npm i @arcisprotocol/vercel-ai-arcis` | Vercel AI SDK |
| [`@arcisprotocol/game-plugin-arcis`](typescript/game-plugin-arcis) | `npm i @arcisprotocol/game-plugin-arcis` | GAME (Virtuals Protocol) |
| [`@arcisprotocol/eliza-plugin-arcis`](typescript/eliza-plugin-arcis) | `npm i @arcisprotocol/eliza-plugin-arcis` | ElizaOS |

## Model-agnostic runtimes — `runtimes/`

| Integration | What it is |
|---|---|
| [`openclaw-arcis`](runtimes/openclaw-arcis) | Skill file + MCP config for the OpenClaw runtime |
| [`hermes-arcis`](runtimes/hermes-arcis) | Treasury skill for `~/.hermes/skills/` |

Any MCP client can also connect directly to the hosted server at `https://mcp.arcis.money/mcp`.

## Related repos

- [`sdk`](https://github.com/Arcis-Protocol/sdk) — the `@arcisprotocol/sdk` these build on
- [`mcp`](https://github.com/Arcis-Protocol/mcp) — hosted MCP server
- [`docs`](https://github.com/Arcis-Protocol/docs) — protocol documentation & runnable examples
- [`core`](https://github.com/Arcis-Protocol/core) — on-chain contracts

## License

MIT
