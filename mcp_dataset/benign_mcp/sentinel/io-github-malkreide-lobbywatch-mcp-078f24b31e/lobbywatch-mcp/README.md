# 🏛️ lobbywatch-mcp

[![CI](https://github.com/malkreide/lobbywatch-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/lobbywatch-mcp/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/lobbywatch-mcp.svg)](https://badge.fury.io/py/lobbywatch-mcp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Data: CC BY-SA 4.0](https://img.shields.io/badge/Data-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Swiss Public Data MCP Portfolio](https://img.shields.io/badge/Portfolio-Swiss%20Public%20Data%20MCP-blue)](https://github.com/malkreide)

> An MCP server that connects AI models to **Lobbywatch.ch**, the largest lobby database of the Swiss Federal Parliament — conflicts of interest, lobby groups, access badges, and transparency scores.

[🇩🇪 Deutsche Version](README.de.md)

> **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)** — connecting AI models to Swiss public data sources.

---

## 🎯 Anchor Demo Query

> *"Welche Mitglieder der WBK-N haben Interessenbindungen zu Bildungsverlagen oder privaten Bildungsträgern, und wie ist ihre Transparenz-Bewertung?"*

Which members of the National Council's Education Commission have declared conflicts of interest with educational publishers or private education providers, and how does their compensation transparency score compare?

[→ More use cases by audience →](EXAMPLES.md)

---

## Overview

Lobbywatch.ch maintains the largest public database on Swiss federal parliamentarians and their connections to lobby organisations: 245 parliamentarians, ~7'800 interessenbindungen (declared mandates), 139 lobby groups, 368 access-badge holders, updated weekly, licensed CC BY-SA 4.0.

`lobbywatch-mcp` exposes this data to Large Language Models via the Model Context Protocol. It is designed to be used alongside [`parlament-mcp`](https://github.com/malkreide/parlament-mcp) (the official Swiss Parliament's Curia Vista data): the pair makes it possible to ask *what* a parliamentarian did officially and *who* they are connected to — in a single conversation.

## Features

- **Dump-first, API-fallback architecture.** The weekly JSON dump is the primary source (stable, verified in production); the live `dataIF` REST API is used only where it returns reliable data (lobby groups, search).
- **Seven Phase 1 tools** — parliamentarian lookup, conflict-of-interest listing, branche search, lobby group fetch, rankings, transparency quota, cache control.
- **CC BY-SA 4.0 attribution** baked into every response via Pydantic envelopes.
- **Dual transport** — `stdio` for Claude Desktop, `streamable-http` / `sse` for cloud deployments.
- **Fuzzy name matching** via rapidfuzz for natural LLM input like "Jositsch" or "Wehrli".
- **No authentication required** (Phase 1 — No-Auth-First).

## Architecture

```
                    ┌─────────────────────────────┐
   LLM client       │     LobbywatchClient        │
  (Claude Desktop,  │                             │
   Inspector, …)    │   ┌───────────────────┐     │
        │           │   │  Dump cache       │     │      cms.lobbywatch.ch
        │  MCP      │   │  (24 h TTL,       │     │      ┌──────────────────┐
        ▼  stdio /  │   │   ~80 MB resident)├─────┼─────►│ weekly JSON      │
   ┌─────────┐ HTTP │   └───────────────────┘     │      │ export (~17 MB)  │
   │ FastMCP │◄────►│                             │      └──────────────────┘
   │ server  │      │   ┌───────────────────┐     │      ┌──────────────────┐
   └─────────┘      │   │  dataIF REST      ├─────┼─────►│ /interface/v1/   │
                    │   │  (live fallback)  │     │      │   json/…         │
                    │   └───────────────────┘     │      └──────────────────┘
                    └─────────────────────────────┘
```

Outbound HTTP runs through a single `httpx.AsyncClient` with `follow_redirects=False`, an SSRF guard that blocks RFC1918 / link-local / metadata IPs, and an httpx event hook that re-resolves on every request. The dump path is the primary source of truth for parliamentarian queries; `dataIF` is only used for lobby group lookups and the search endpoint.

## Prerequisites

- Python 3.11 or newer
- Internet access to download the weekly Lobbywatch JSON export (~17 MB zipped)

## Installation

From PyPI (after first release):

```bash
pip install lobbywatch-mcp
```

From source:

```bash
git clone https://github.com/malkreide/lobbywatch-mcp.git
cd lobbywatch-mcp
pip install -e ".[dev]"
```

## Usage

### Standalone

```bash
lobbywatch-mcp
```

This starts the server in `stdio` mode. For HTTP:

```bash
LOBBYWATCH_MCP_TRANSPORT=http LOBBYWATCH_MCP_PORT=8000 lobbywatch-mcp
```

### Container

A hardened multi-stage `Dockerfile` ships with the repo (non-root,
read-only-rootfs compatible). See [`docs/deployment.md`](docs/deployment.md)
and [`deploy/docker-compose.example.yml`](deploy/docker-compose.example.yml)
for resource limits, sticky-LB guidance and egress hardening.

```bash
docker build -t lobbywatch-mcp:0.2.0 .
docker run --rm -p 127.0.0.1:8000:8000 lobbywatch-mcp:0.2.0
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lobbywatch": {
      "command": "uvx",
      "args": ["lobbywatch-mcp"]
    }
  }
}
```

A full example is provided in [`claude_desktop_config.json`](claude_desktop_config.json).

### Example Queries

Once connected, try prompts such as:

- *"Give me the top 10 parliamentarians by number of interessenbindungen in the SP party."*
- *"Which WBK-N members have mandates in the publishing or education industry?"*
- *"Look up the lobby group 'economiesuisse' and list its connected parliamentarians."*
- *"What is the compensation-transparency score distribution for the finance commission (FK-N)?"*

## Tools

All tool names use the `lobbywatch_` namespace prefix (since 0.2.0) to
avoid collisions with sibling portfolio servers.

| Tool | Purpose | Source |
|---|---|---|
| `lobbywatch_get_parlamentarier(name_or_id)` | Full profile + all conflicts of interest | Dump |
| `lobbywatch_list_interessenbindungen(name_or_id, nur_hauptberuflich, nur_aktiv)` | Filtered mandate list | Dump |
| `lobbywatch_search_parlamentarier_nach_branche(branche_query, kommission, limit)` | Cross-filter by industry and commission | Dump |
| `lobbywatch_get_lobbygruppe(name_or_id)` | Lobby group with connected MPs and organisations | Live dataIF |
| `lobbywatch_get_ranking(kriterium, kommission, partei, limit)` | Top-N by criterion | Dump |
| `lobbywatch_get_transparenzquote(kommission)` | Distribution of compensation transparency labels | Dump |
| `lobbywatch_refresh_dump()` / `lobbywatch_dump_status()` | Cache control | Dump |

## Configuration

All behaviour is controlled via environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `LOBBYWATCH_MCP_TRANSPORT` | `stdio` | Transport (`stdio`, `http`, `sse`) |
| `LOBBYWATCH_MCP_HOST` | `127.0.0.1` | HTTP bind host (set to `0.0.0.0` only behind an auth gateway) |
| `LOBBYWATCH_MCP_PORT` | `8000` | HTTP bind port |
| `LOBBYWATCH_MCP_CACHE_DIR` | `~/.cache/lobbywatch-mcp` | Dump cache location |
| `LOBBYWATCH_MCP_CACHE_TTL` | `86400` (24h) | Cache time-to-live in seconds |
| `LOBBYWATCH_MCP_HTTP_TIMEOUT` | `60` | HTTP timeout in seconds |
| `LOBBYWATCH_MCP_CORS_ORIGINS` | _(unset)_ | Comma-separated origin allow-list for HTTP/SSE; when set, exposes `Mcp-Session-Id` to browsers |
| `LOBBYWATCH_MCP_LOG_FORMAT` | `text` | `text` (stdlib formatter) or `json` (structured via structlog) |
| `LOBBYWATCH_MCP_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOBBYWATCH_MCP_OTEL_ENABLED` | `0` | Set to `1` to enable OpenTelemetry tracing (requires `pip install 'lobbywatch-mcp[obs]'`) |
| `LOBBYWATCH_MCP_OTEL_ENDPOINT` | _(unset)_ | OTLP/HTTP collector endpoint (e.g. `http://localhost:4318/v1/traces`) |

## Project Structure

```
lobbywatch-mcp/
├── src/lobbywatch_mcp/
│   ├── __init__.py
│   ├── __main__.py        # CLI + transport selection
│   ├── config.py          # URLs, cache paths, attribution
│   ├── client.py          # Dump download + dataIF client
│   ├── models.py          # Pydantic v2 response envelopes
│   └── server.py          # FastMCP tool registrations
├── tests/
│   ├── conftest.py        # Fixture parliamentarians
│   ├── test_client.py     # Respx-mocked unit tests
│   ├── test_server.py     # Tool integration tests
│   └── test_live.py       # @pytest.mark.live — excluded from CI
├── .github/workflows/
│   ├── ci.yml             # Test matrix + ruff
│   └── publish.yml        # PyPI OIDC Trusted Publisher
├── claude_desktop_config.json
├── pyproject.toml
└── ...
```

## Data License & Attribution

**The code** is released under the MIT License.

**The data** served through this MCP is © Lobbywatch.ch and licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Every response envelope includes the attribution string. Downstream users must:

1. Credit Lobbywatch.ch as the data source.
2. Share derivative datasets under the same CC BY-SA 4.0 terms.
3. Understand that Lobbywatch is a **community-researched database** — not an official register. It is authoritative for transparency research but should not be confused with the Federal Parliament's own declarations.

## Known Limitations

- The upstream `/table/parlamentarier/...` `dataIF` REST endpoint currently returns empty result sets. The server works around this by using the weekly JSON dump instead.
- `zutrittsberechtigungen` (access badges) are not populated in the "essential" dump variant used here. A future release will add a dedicated tool using the non-essential dump.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for the security posture, accepted-risk
decisions, and how to report a vulnerability.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT License — see [LICENSE](LICENSE). Data CC BY-SA 4.0 — see [LICENSE](LICENSE) § Data notice.

## Author

**malkreide** · [GitHub](https://github.com/malkreide)

---

*Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).*

<!-- mcp-name: io.github.malkreide/lobbywatch-mcp -->

<!-- BEGIN GENERATED: install -->
## Installation

Run via [`uv`](https://docs.astral.sh/uv/)'s `uvx` — no clone or manual install needed. Add to your MCP client config (`mcpServers` for Claude Desktop, Cursor and Windsurf; use a top-level `servers` key for VS Code in `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "lobbywatch-mcp": {
      "command": "uvx",
      "args": [
        "lobbywatch-mcp"
      ]
    }
  }
}
```
<!-- END GENERATED: install -->
