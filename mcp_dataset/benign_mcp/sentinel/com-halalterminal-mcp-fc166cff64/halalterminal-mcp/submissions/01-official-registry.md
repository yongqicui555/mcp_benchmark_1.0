# 01 — Official MCP Registry (registry.modelcontextprotocol.io)

**Why this is #1:** Cascades automatically to **mcpservers.org**, **LobeHub**, **Mastra**, and **modelcontextprotocol.info**. One submission, four listings.

## Prerequisites

1. `@halalterminal/mcp` published to npm (see [02-npm.md](./02-npm.md)) — the published `package.json` MUST contain `"mcpName": "com.halalterminal/mcp"` (already in our `package.json`).
2. Decide on **namespace verification**. We're using DNS for `com.halalterminal/`. Alternative: drop to `io.github.goww7/halalterminal-mcp` (uses GitHub OAuth, no DNS needed — but weaker brand SEO).

## Install `mcp-publisher`

It's a Go binary, NOT an npm package.

```bash
# macOS / Linux
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" \
  | tar xz mcp-publisher && sudo mv mcp-publisher /usr/local/bin/

# Or
brew install mcp-publisher
```

## Verify the namespace (DNS path — recommended)

```bash
mcp-publisher login dns --domain halalterminal.com
```

It will print a `TXT` record. Add it on the DNS provider for `halalterminal.com`:

```
_mcp-registry.halalterminal.com  TXT  "mcp-registry-verify=<token>"
```

Wait ~30s for propagation, then re-run the login command — it will succeed and persist credentials in `~/.mcp-publisher/`.

**Fallback (no DNS access):** edit `server.json` to set `"name": "io.github.goww7/halalterminal-mcp"`, also update `mcpName` in `package.json` (and re-bump npm version since you can't republish), then `mcp-publisher login github`.

## Publish

From the repo root (`/root/halalterminal-mcp`):

```bash
mcp-publisher publish
```

It reads `./server.json`, validates the npm package's `mcpName` matches, and posts to the registry. You'll see a confirmation URL like `https://registry.modelcontextprotocol.io/v0/servers/com.halalterminal/mcp`.

## After publish — verify the cascade

Check these aggregators within 24–48h:
- https://mcpservers.org/?q=halal
- https://lobehub.com/mcp/search?q=halal
- https://mastra.ai/mcp-registry?search=halal

If a listing is missing after 72h, file an issue on the aggregator's repo with the registry URL.

## Keeping it fresh

Every npm version bump → re-bump `version` in `server.json` → `mcp-publisher publish` again. Same flow.
