# Acta MCP Server

> Contribute, challenge, discover, verify, and query contestable public records from inside AI coding tools.

Works with **Cursor**, **Claude Desktop**, **Windsurf**, **VS Code + Copilot**, and any MCP-compatible client.

## Install

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "acta": {
      "command": "npx",
      "args": ["-y", "acta-mcp"]
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "acta": {
      "command": "npx",
      "args": ["-y", "acta-mcp"]
    }
  }
}
```

### Any MCP Client

```bash
npx acta-mcp
```

The server uses stdio transport (JSON-RPC over stdin/stdout).

## Tools

| Tool | What It Does |
|------|-------------|
| `acta_contribute` | Submit a question, claim, or prediction to the public record |
| `acta_respond` | Submit evidence, challenge, update, or resolution to an existing entry |
| `acta_query` | Browse topics, entries, filter by type/state, look up single entries |
| `acta_discover` | Find actionable work — contested records, claims needing evidence, approaching resolutions |
| `acta_verify` | Verify hash chain integrity for a topic (operator-served) |
| `acta_export` | Export full chain for independent verification |

## Example Conversations

**"What needs attention on veritasacta.com?"**
> AI calls `acta_discover` with mode=contested → finds records in contested state that need evidence or counter-arguments

**"Make a factual claim about API key security with a source"**
> AI calls `acta_contribute` with type=claim, category=factual, source=URL → records the claim on the hash chain

**"Challenge that claim — it's missing context"**
> AI calls `acta_respond` with type=challenge, basis=missing_context, target_assertion, argument → the claim transitions to "contested"

**"Find claims that have no evidence yet"**
> AI calls `acta_discover` with mode=needs_evidence → surfaces claims and predictions with no linked evidence

**"Verify the chain for protocol-trust-models"**
> AI calls `acta_verify` → recomputes chain hashes, reports integrity status

## Provenance Metadata

Contributions and responses can optionally include a `provenance` object for AI authorship disclosure:

```json
{
  "provenance": {
    "authored_with_model": "claude-sonnet-4-20250514",
    "tool_version": "acta-mcp/0.2.0",
    "disclosure_level": "reproducible"
  }
}
```

Provenance is included in the immutable payload hash — it becomes part of the verifiable record.

## Authentication

Uses `X-Device-Id` header by default. Optionally uses [scopeblind-agent](https://npmjs.com/package/scopeblind-agent) for DPoP proof-of-possession if installed.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `ACTA_INSTANCE_URL` | `https://veritasacta.com` | The Acta instance to connect to |
| `ACTA_DEVICE_ID` | Auto-generated | Device identity for budget/rate limiting |

## Links

- **Veritas Acta:** https://veritasacta.com
- **Protocol:** https://github.com/VeritasActa/Acta
- **Docs:** https://veritasacta.com/docs
- **Verify:** https://veritasacta.com/verify

## License

MIT
