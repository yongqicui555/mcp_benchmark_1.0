# DepScope MCP Server

[![npm version](https://img.shields.io/npm/v/depscope-mcp.svg)](https://www.npmjs.com/package/depscope-mcp)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.txt)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-success)](https://modelcontextprotocol.io/)

**Package intelligence MCP server for AI agents.** Stops AI coding agents (Claude, ChatGPT, Cursor, Windsurf, Copilot) from installing **hallucinated**, **deprecated**, or **malicious** packages across **19 ecosystems**.

→ Backed by [depscope.dev](https://depscope.dev) — 1.2M+ packages indexed, 19,000+ vulnerabilities tracked, real-time.

## What's new in v0.9.0

The MCP server now sends a **system-prompt directive** to your AI client at handshake (`server.instructions`). Claude Code, Cursor, Windsurf and other MCP clients receive a proactive-invocation brief automatically — manual rule files (`CLAUDE.md`, `.cursorrules`, `.windsurfrules`) are now **optional**. Existing rules still work; they're just redundant.

What the model sees at every session start:

- The 19-ecosystem coverage list
- An "INVOKE PROACTIVELY" directive with explicit triggers (install, version bump, lockfile change, "module not found" errors, library comparison)
- Three pillars: token-saving, energy-saving, security
- Standard invocation flow: `check_malicious` → `check_typosquat` → `check_package` → `install_command`

For Claude Code there is also a **companion plugin** that bundles the MCP server with a skill carrying rich frontmatter triggers:

```bash
git clone https://github.com/cuttalo/depscope-claude-plugin ~/.claude/plugins/depscope
```

All npm versions `<0.9.0` are now deprecated. Run `npm update -g depscope-mcp` if you installed globally.

---

## Why this exists

LLMs frequently invent package names that look real but don't exist (`fastapi-turbo`, `lodahs`, `tokio-stream-extras`). When an agent tries to install one, it might hit an attacker's typosquat. **DepScope verifies every package before install.**

## Quick start

### Claude Desktop / Cursor / Windsurf (remote MCP)

Add to your MCP config:

```json
{
  "mcpServers": {
    "depscope": {
      "url": "https://mcp.depscope.dev/mcp"
    }
  }
}
```

### Local (stdio via npx)

```json
{
  "mcpServers": {
    "depscope": {
      "command": "npx",
      "args": ["-y", "depscope-mcp"]
    }
  }
}
```

## Tools (22)

| Tool | Purpose |
|---|---|
| `check_package` | Full package check: deprecated/CVE/health/recommendation |
| `get_health_score` | 0-100 score with breakdown (maintenance/popularity/security/maturity/community) |
| `get_vulnerabilities` | Open CVEs from OSV + KEV/EPSS |
| `package_exists` | Hallucination detector (404 = LLM invented it) |
| `find_alternatives` | Curated alternatives for deprecated/abandoned packages |
| `get_typosquat` | Suspicious name similarity check |
| `get_breaking_changes` | Migration plan between versions |
| `get_bugs` | Known bugs from GitHub issues |
| `compare_packages` | Side-by-side health/license/vuln comparison |
| `resolve_error` | Map error message → likely cause + fix |
| `search_errors` | Find similar error reports across ecosystems |
| `check_compat` | Stack compatibility check |
| `get_latest_version` | Latest stable + maturity signal |
| ... and 9 more | full list in `tools.js` |

## Ecosystems (19)

`npm` · `pypi` · `cargo` · `go` · `composer` · `maven` · `nuget` · `rubygems` · `pub` · `hex` · `swift` · `cocoapods` · `cpan` · `hackage` · `cran` · `conda` · `homebrew` · `jsr` · `julia`

## Pricing

**Free.** No auth required. Generous rate limits. The MCP server is open-source (AGPL-3.0); the backend (depscope.dev API) is proprietary.

## License

AGPL-3.0-or-later. Backend is proprietary; this client is open.

## Links

- [depscope.dev](https://depscope.dev) — homepage
- [docs](https://depscope.dev/integrate) — integration guide
- [Glama listing](https://glama.ai/mcp/servers/cuttalo/depscope)
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
