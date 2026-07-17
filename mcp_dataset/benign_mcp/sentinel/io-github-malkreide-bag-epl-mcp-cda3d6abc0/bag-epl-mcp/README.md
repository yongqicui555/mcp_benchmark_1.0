> \U0001f1e8\U0001f1ed **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

# \U0001f48a bag-epl-mcp

![Version](https://img.shields.io/badge/version-0.1.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![No Auth Required](https://img.shields.io/badge/auth-none%20required-brightgreen)](https://github.com/malkreide/bag-epl-mcp)
![CI](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml/badge.svg)

> MCP Server for the Swiss BAG electronic benefits platform (ePL) \u2014 Spezialitaetenliste, GGSL, MiGeL

[\U0001f1e9\U0001f1ea Deutsche Version](README.de.md)

### Demo

![Demo: Claude using epl_sl_suche and epl_rechtskontext](docs/assets/demo.svg)

---

## Overview

`bag-epl-mcp` enables AI models to answer questions about mandatory health insurance coverage in Switzerland \u2014 in natural language, grounded in real data.

| List | Purpose | Legal basis |
|------|---------|-------------|
| **Spezialitaetenliste (SL)** | Compulsory-insurance medications | KVG Art. 52 |
| **GGSL** | Medications for congenital disorders (IV) | IVG Anhang |
| **MiGeL** | Medical devices & aids | KLV Art. 20 |

**Anchor query:** *"Is this medication covered by mandatory health insurance?"*
\u2192 `epl_sl_suche`: Live lookup in the Spezialitaetenliste (SL)
→ [More use cases by audience →](EXAMPLES.md)

---

## Features

- \U0001f48a **6 tools, 2 resources, 2 prompts** for Swiss health insurance data
- \U0001f50d **`epl_sl_suche`** \u2014 search the Spezialitaetenliste for medications
- \u2696\ufe0f **`epl_rechtskontext`** \u2014 legal context with Fedlex links
- \U0001f513 **No API key required** \u2014 all data publicly accessible
- \u2601\ufe0f **Dual transport** \u2014 stdio (Claude Desktop) + Streamable HTTP (cloud)
- \U0001f4da **Prompt templates** for insurance coverage checks and school health queries

---

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

---

## Installation

```bash
# Clone the repository
git clone https://github.com/malkreide/bag-epl-mcp.git
cd bag-epl-mcp

# Install
pip install -e .
# or with uv:
uv pip install -e .
```

Or with `uvx` (no permanent installation):

```bash
uvx bag-epl-mcp
```

---

## Quickstart

```bash
# stdio (for Claude Desktop) — default, opens no network ports
python -m bag_epl_mcp.server

# Streamable HTTP (cloud) — transport selected via env var
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8000 \
  pip install -e ".[http]" && python -m bag_epl_mcp.server
```

> **Transport & host are configured exclusively via environment variables**
> (`MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`). The default is `stdio` bound to
> nothing; `MCP_HOST` defaults to `127.0.0.1` and should only be set to
> `0.0.0.0` inside a container/cloud environment.

Try it immediately in Claude Desktop:

> *"Is Methylphenidate (Ritalin) covered by mandatory health insurance?"*
> *"Which laws regulate admission to the Spezialitaetenliste?"*
> *"Is a wheelchair covered by mandatory insurance?"*

---

## Configuration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "bag-epl": {
      "command": "python",
      "args": ["-m", "bag_epl_mcp.server"]
    }
  }
}
```

Or with `uvx`:

```json
{
  "mcpServers": {
    "bag-epl": {
      "command": "uvx",
      "args": ["bag-epl-mcp"]
    }
  }
}
```

### Cloud Deployment (Streamable HTTP for browser access)

**Render.com (recommended):**
1. Push/fork the repository to GitHub
2. On [render.com](https://render.com): New Web Service \u2192 connect GitHub repo
3. Build command: `pip install -e ".[http]"`
4. Set the following environment variables:
   - `MCP_TRANSPORT=streamable-http`
   - `MCP_HOST=0.0.0.0` (required so the container accepts external traffic)
   - `MCP_PORT=8000` (or Render's `$PORT`)
   - *(optional)* `MCP_CORS_ORIGINS='["https://claude.ai"]'` to extend the
     browser CORS allow-list
   - *(optional)* OpenTelemetry tracing is **on by default** but a no-op unless
     the tracing deps are installed — build with `pip install -e ".[http,otel]"`
     and point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector. Set
     `MCP_OTEL_ENABLED=0` to disable.
5. Start command: `python -m bag_epl_mcp.server`
6. In claude.ai under Settings \u2192 MCP Servers, add: `https://your-app.onrender.com/mcp`

> **Security note:** the server exposes only public, read-only data and uses no
> authentication. See [`docs/SECURITY.md`](docs/SECURITY.md) for the threat
> model (egress allow-list, host binding, Lethal-Trifecta assessment).

---

## Available Tools

| Tool | Description |
|------|-------------|
| `epl_sl_suche` | Search the Spezialitaetenliste for compulsory-insurance medications |
| `epl_ggsl_abfrage` | Check GGSL coverage for congenital disorders |
| `epl_migel_suche` | Search the MiGeL for medical devices & aids |
| `epl_gesuchseingaenge` | List pending SL admission requests (transparency) |
| `epl_rechtskontext` | Legal context for coverage questions (WZW criteria) |
| `epl_server_info` | Server status and API phase information |

### Example Use Cases

| Query | Tool |
|-------|------|
| *"Is Ritalin covered by insurance?"* | `epl_sl_suche` |
| *"Which medications for congenital disorder GG-313?"* | `epl_ggsl_abfrage` |
| *"Is a wheelchair covered?"* | `epl_migel_suche` |
| *"Which laws regulate the SL?"* | `epl_rechtskontext` |

---

## Architecture

**Data flow (Phase 1):**

```
                         bag-epl-mcp (FastMCP)
 \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510  MCP    \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510  HTTPS GET   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
 \u2502 MCP Client \u2502\u25c0\u2500\u2500\u2500\u2500\u2500\u2500\u25b6\u2502  tools (read-only)             \u2502\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25b6\u2502 sl.bag.admin.ch  \u2502
 \u2502 (Claude    \u2502 stdio / \u2502   \u251c\u2500 epl_sl_suche              \u2502  egress      \u2502 www.bag.admin.ch \u2502
 \u2502  Desktop,  \u2502 Stream- \u2502   \u251c\u2500 epl_ggsl_abfrage          \u2502  allow-list  \u2502 www.fedlex...    \u2502
 \u2502  claude.ai)\u2502 able    \u2502   \u251c\u2500 epl_migel_suche           \u2502\u25c0\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2502 (public OGD)     \u2502
 \u2502            \u2502 HTTP    \u2502   \u251c\u2500 epl_gesuchseingaenge       \u2502  (no auth)   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
 \u2502            \u2502         \u2502   \u251c\u2500 epl_rechtskontext          \u2502
 \u2502            \u2502         \u2502   \u2514\u2500 epl_server_info            \u2502   structured JSON logs \u2192 stderr
 \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518         \u2502  resources: epl://uebersicht \u2026  \u2502
                        \u2502  prompts:   epl_kassenpflicht\u2026  \u2502
                        \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
```

**Phase roadmap** (details in [`docs/ROADMAP.md`](docs/ROADMAP.md)):

```
Phase 1 (current)  \u2192 SL website access + structured legal info
Phase 2 (planned)  \u2192 FHIR/IDMP API (BAG, ~2025/2026)
Phase 3 (vision)   \u2192 MiGeL + AL via ePL-FHIR (2026/2027)
```

The server is **already useful today** and will seamlessly upgrade when the BAG publishes its FHIR API.

**MCP protocol version:** `2025-06-18` (surfaced via `epl_server_info`). SDK
updates are proposed monthly via Dependabot; the protocol version is reviewed on
every `mcp` SDK bump \u2014 see the versioning policy in [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Safety & Limits

- **Read-only:** All tools perform HTTP GET requests only \u2014 no data is written, modified, or deleted.
- **No personal data:** The server accesses public regulatory lists (SL, GGSL, MiGeL). No personally identifiable information (PII) is processed or stored.
- **No medical advice:** This server provides informational access to regulatory data only. For medical or legal decisions, always consult the official BAG sources and qualified professionals.
- **Rate limits:** The SL website (sl.bag.admin.ch) is a public Angular SPA; the server enforces a 30s timeout per request. Use `limit` parameters conservatively.
- **Data freshness:** Phase 1 tools link to live BAG sources. No caching is performed by this server.
- **Data licence (OGD-CH):** The underlying BAG/Fedlex data is Swiss Open Government Data, licensed **CC BY 4.0**. Tool outputs carry a `source` / `provenance` block (JSON) or a source-and-licence footer (Markdown) so attribution is preserved.
- **Structured output:** every tool returns both a human-readable Markdown/JSON block (`content`) and a typed `structuredContent` validated against a per-tool output schema, so MCP clients can consume results programmatically without parsing prose.
- **Terms of service:** Data is subject to the ToS of [sl.bag.admin.ch](https://sl.bag.admin.ch), [bag.admin.ch](https://www.bag.admin.ch), and [fedlex.admin.ch](https://www.fedlex.admin.ch).
- **No guarantees:** This is a community project, not affiliated with the BAG or any government entity. Availability depends on upstream sources.

---

## Testing

```bash
# Unit tests (no API key required)
PYTHONPATH=src pytest tests/ -m "not live"

# Integration tests (live API calls)
pytest tests/ -m "live"
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

MIT License \u2014 see [LICENSE](LICENSE)

---

## Author

Hayal Oezkan \u00b7 [malkreide](https://github.com/malkreide)

---

## Credits & Related Projects

- **BAG Spezialitaetenliste:** [sl.bag.admin.ch](https://sl.bag.admin.ch) \u2014 Federal Office of Public Health
- **KVG:** [SR 832.10](https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de) \u2014 Health Insurance Act
- **KLV:** [SR 832.112.31](https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de) \u2014 Healthcare Benefits Ordinance
- **Protocol:** [Model Context Protocol](https://modelcontextprotocol.io/) \u2014 Anthropic / Linux Foundation
- **Related:** [fedlex-mcp](https://github.com/malkreide/fedlex-mcp) \u2014 Swiss federal law
- **Related:** [swiss-cultural-heritage-mcp](https://github.com/malkreide/swiss-cultural-heritage-mcp) \u2014 Cultural heritage data
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

<!-- mcp-name: io.github.malkreide/bag-epl-mcp -->

<!-- BEGIN GENERATED: install -->
## Installation

Run via [`uv`](https://docs.astral.sh/uv/)'s `uvx` — no clone or manual install needed. Add to your MCP client config (`mcpServers` for Claude Desktop, Cursor and Windsurf; use a top-level `servers` key for VS Code in `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "bag-epl-mcp": {
      "command": "uvx",
      "args": [
        "bag-epl-mcp"
      ]
    }
  }
}
```
<!-- END GENERATED: install -->
