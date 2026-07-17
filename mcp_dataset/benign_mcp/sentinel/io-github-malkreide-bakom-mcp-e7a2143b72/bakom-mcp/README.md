> 🇨🇭 **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

# 📡 bakom-mcp

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/malkreide/bakom-mcp/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Auth](https://img.shields.io/badge/auth-none%20required-brightgreen)](https://www.bakom.admin.ch/bakom/en/home/digital-switzerland-and-internet/open-data.html)
![CI](https://github.com/malkreide/bakom-mcp/actions/workflows/ci.yml/badge.svg)

> MCP server for BAKOM open data – broadband, mobile coverage, media and Swiss telecom statistics.

[🇩🇪 Deutsche Version](README.de.md)

<p align="center">
  <img src="assets/demo.svg" alt="Demo: Claude queries fibre and 5G coverage via MCP tool call" width="720">
</p>

---

## Overview

**bakom-mcp** connects AI assistants like Claude to the Swiss Federal Office of Communications (BAKOM) open data infrastructure. It enables natural-language queries about broadband availability, 5G/4G coverage, mobile antenna locations, licensed broadcasters (RTV database), and telecommunications statistics — all without API keys.

All data is published as Open Government Data (OGD) on opendata.swiss / geo.admin.ch under **CC BY 4.0** — see the [Data Licence](#data-licence) section below for attribution requirements.

**Anchor demo query:** *"Which school buildings in district 7 do not yet have fibre optic connectivity?"*

> `bakom_multi_standort_konnektivitaet` delivers the comparison table automatically.

[→ More use cases by audience →](EXAMPLES.md)

---

## Scope

### What this server does

✓ Read-only queries against three public BAKOM/Confederation APIs:
  - `api3.geo.admin.ch` / `wms.geo.admin.ch` (broadband, mobile coverage, antennas)
  - `ckan.opendata.swiss` (telecom statistics, dataset metadata)
  - `rtvdb.ofcomnet.ch` (licensed radio/TV broadcasters)

✓ Returns aggregated, anonymous data — no personal data, no household-level identification.

✓ Bound to Swiss WGS84 coordinates (lat 45.8–47.9, lon 5.9–10.6) via Pydantic input validation.

✓ Egress is locked to a [code-layer allow-list](src/bakom_mcp/server.py) of the six known data-source hosts.

### What this server does not

✗ Send data anywhere (read-only, no write tools).

✗ Access the local filesystem (no path-traversal surface).

✗ Use authentication tokens (none required — all sources are public OGD).

✗ Cache or persist user inputs across calls.

✗ Execute shell commands or arbitrary code (no `subprocess`/`os.system`/`eval`).

---

## Features

- 📶 **Broadband availability** – Fixed-line coverage at 30/100/300/500/1000 Mbit/s (250×250m grid)
- 🔌 **Fibre status** – FTTB/FTTH availability per location
- 📍 **Multi-location comparison** – Connectivity check for up to 20 locations simultaneously
- 📱 **Mobile coverage** – 5G/4G/3G outdoor coverage (100×100m grid)
- 📡 **Antenna search** – Mobile and broadcast transmitters within a configurable radius
- 📺 **RTV database** – Search licensed radio and TV broadcasters by name, type, canton
- 🗞️ **Media landscape** – BAKOM media structure reports and datasets
- 📊 **Telecom statistics** – Fixed-line, mobile, broadband market data via opendata.swiss
- 🗂️ **Broadband Atlas catalogue** – All BAKOM dataset layers with direct API links
- 🔓 **No authentication required** – All data is Open Government Data (OGD)

---

## Prerequisites

- Python 3.11+
- `uv` or `pip` for installation
- Internet connection (live APIs: geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch)

---

## Installation

```bash
# Recommended: uvx (no permanent installation required)
uvx bakom-mcp

# Or install with pip
pip install bakom-mcp

# Development install
git clone https://github.com/malkreide/bakom-mcp
cd bakom-mcp
pip install -e ".[dev]"
```

---

## Quickstart

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bakom": {
      "command": "uvx",
      "args": ["bakom-mcp"]
    }
  }
}
```

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Cloud / HTTP Transport

```bash
python -m bakom_mcp.server --http
# Server running at http://localhost:8050/mcp
```

Configuration via environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Purpose |
|---|---|---|
| `BAKOM_MCP_HOST` | `127.0.0.1` | Bind address. Set to `0.0.0.0` only on trusted networks (warning logged). |
| `BAKOM_MCP_PORT` | `8050` | TCP port. |
| `BAKOM_MCP_CORS_ORIGINS` | _(empty)_ | Comma-separated allowed origins for browser clients. Empty = CORS disabled. |

### Docker

A hardened container image is provided. Suitable for cloud deployments behind a reverse proxy (Caddy, Traefik, nginx).

```bash
# Build & run via compose (recommended)
docker compose up --build

# Or via docker run
docker build -t bakom-mcp:latest .
docker run --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --tmpfs /tmp:rw,size=16M \
  -p 127.0.0.1:8050:8050 \
  bakom-mcp:latest
```

The image runs as **non-root** (UID 10001), uses a **read-only filesystem**, drops **all Linux capabilities** and refuses **privilege escalation**. Resource limits are configured in [`docker-compose.yml`](docker-compose.yml) (256 MB memory, 0.5 CPU, 64 PIDs). The default port mapping binds to `127.0.0.1` only — for public exposure, terminate TLS and CORS at a reverse proxy.

### Cursor / VS Code / LibreChat

```json
{
  "bakom": {
    "command": "uvx",
    "args": ["bakom-mcp"],
    "transport": "stdio"
  }
}
```

> 💡 *"stdio for the developer laptop, HTTP/SSE for the browser."*

---

## Available Tools (12)

### Broadband & Connectivity

| Tool | Description |
|------|-------------|
| `bakom_broadband_coverage` | Fixed-line coverage at a coordinate (30–1000 Mbit/s) |
| `bakom_glasfaser_verfuegbarkeit` | FTTB/FTTH fibre availability |
| `bakom_multi_standort_konnektivitaet` | Connectivity comparison for up to 20 locations |

### Mobile & Transmitters

| Tool | Description |
|------|-------------|
| `bakom_mobilfunk_abdeckung` | 5G/4G/3G outdoor coverage |
| `bakom_sendeanlagen_suche` | Mobile antennas within a configurable radius |
| `bakom_frequenzdaten` | Radio/TV transmitter sites near a location |

### Media & RTV

| Tool | Description |
|------|-------------|
| `bakom_rtv_suche` | Search licensed broadcasters (RTV database) |
| `bakom_medienstruktur_info` | Swiss media landscape datasets |
| `bakom_aktuell` | Current BAKOM topics (5G, media, AI, postal) |

### Statistics & Catalogue

| Tool | Description |
|------|-------------|
| `bakom_telekomstatistik_uebersicht` | Telecom statistics from opendata.swiss |
| `bakom_breitbandatlas_datensaetze` | Full catalogue of Broadband Atlas layers |
| `bakom_check_api_status` | 🔍 Health check for all configured data sources |

---

## Example Prompts

```
What is the broadband situation at Schulhaus Leutschenbach (47.4148, 8.5654)?

Compare 5G and fibre coverage for these three school buildings: [coordinates]

Which radio stations are licensed in canton Zurich?

Show me the current BAKOM position on 5G frequency allocation.

List all Broadband Atlas datasets available via geo.admin.ch.
```

---

## Safety & Limits

| Aspect | Details |
|--------|---------|
| **Access** | Read-only (`readOnlyHint: true`) — the server cannot modify or delete any data |
| **Personal data** | No personal data — all sources are aggregated, public open data |
| **Rate limits** | Built-in per-query caps (max 50 antennas, max 20 locations, max 50 RTV results) |
| **Timeout** | 20 seconds per API call |
| **Authentication** | No API keys required — all 3 APIs are publicly accessible |
| **Licences** | All data under CC0 / open licences (Open Government Data) |
| **Terms of Service** | Subject to ToS of the respective data sources: [geo.admin.ch](https://www.geo.admin.ch/en/general-terms-and-conditions-fsdi), [opendata.swiss](https://opendata.swiss/en/terms-of-use), [rtvdb.ofcomnet.ch](https://rtvdb.ofcomnet.ch) |

---

## Data Sources

| Source | Data | Authentication |
|--------|------|----------------|
| [geo.admin.ch](https://api3.geo.admin.ch) | Broadband Atlas, mobile coverage, antenna locations | None |
| [opendata.swiss](https://opendata.swiss) | BAKOM datasets, telecom statistics | None |
| [rtvdb.ofcomnet.ch](https://rtvdb.ofcomnet.ch) | Licensed radio/TV broadcasters | None |

All data is published under open licences (CC0 / OGD).

---

## Synergies with the MCP Portfolio

**bakom-mcp** can be combined with other servers in the portfolio for multi-dimensional queries:

```
zurich-opendata-mcp  →  school building addresses
         +
    bakom-mcp         →  fibre and 5G status
         =
"Digital equity" dashboard for all school districts
```

Further combinations:
- `srgssr-mcp` + `bakom-mcp` → Media coverage and broadcast network
- `swiss-statistics-mcp` + `bakom-mcp` → Telecom market development
- `fedlex-mcp` + `bakom-mcp` → Regulatory context (RTVG, FMG)

---

## Project Structure

```
bakom-mcp/
├── src/bakom_mcp/
│   ├── __init__.py          # Package
│   ├── server.py            # MCP server (12 tools, 2 resources)
│   └── py.typed             # PEP 561 type marker
├── tests/
│   └── test_integration.py  # Integration tests (live APIs)
├── assets/
│   └── demo.svg             # Demo flow diagram
├── .github/workflows/
│   ├── ci.yml               # CI: lint, syntax, import, tests
│   └── publish.yml          # PyPI publish on release
├── .gitignore
├── pyproject.toml           # Build config (hatchling)
├── CHANGELOG.md
├── CONTRIBUTING.md          # Contribution guide (English)
├── CONTRIBUTING.de.md       # Contribution guide (German)
├── SECURITY.md              # Security policy (English)
├── SECURITY.de.md           # Security policy (German)
├── LICENSE                  # MIT License
├── README.md                # This file (English)
└── README.de.md             # German version
```

---

## Testing

```bash
# Unit tests (no network required)
PYTHONPATH=src pytest tests/ -m "not live"

# Integration tests (live APIs, internet required)
PYTHONPATH=src pytest tests/ -m "live"
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) ([🇩🇪 Deutsch](CONTRIBUTING.de.md)) for guidelines on reporting bugs, suggesting features, and submitting pull requests.

---

## Security

To report a vulnerability, see the [Security Policy](SECURITY.md) ([🇩🇪 Deutsch](SECURITY.de.md)). Please report security issues privately via GitHub Security Advisories rather than public issues.

---

## Software Licence

MIT License — see [LICENSE](LICENSE).

## Data Licence

The BAKOM open data delivered through this server is published under **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de)**. When using or redistributing tool outputs, attribute the source as:

> *Source: Federal Office of Communications (BAKOM) via opendata.swiss / geo.admin.ch · Licence: CC BY 4.0*

Tool outputs already include this footer automatically. The Markdown response format ends with the attribution line; downstream applications that consume the JSON format should propagate the source/licence metadata to their end users.

---

## Author

Hayal Oezkan · [github.com/malkreide](https://github.com/malkreide)

---

## Credits & Related Projects

- **Data:** [BAKOM Open Data](https://www.bakom.admin.ch/bakom/en/home/digital-switzerland-and-internet/open-data.html) – Federal Office of Communications (OFCOM/BAKOM)
- **Geodata:** [geo.admin.ch](https://api3.geo.admin.ch) – swisstopo / Federal Geodata Infrastructure
- **Protocol:** [Model Context Protocol](https://modelcontextprotocol.io/) – Anthropic / Linux Foundation
- **Related:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) – MCP server for Zurich city open data
- **Related:** [swiss-transport-mcp](https://github.com/malkreide/swiss-transport-mcp) – Swiss public transport MCP server
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

---

*Part of the Swiss Open Data MCP portfolio — public data deserves public interfaces.*

<!-- mcp-name: io.github.malkreide/bakom-mcp -->

<!-- BEGIN GENERATED: install -->
## Installation

Run via [`uv`](https://docs.astral.sh/uv/)'s `uvx` — no clone or manual install needed. Add to your MCP client config (`mcpServers` for Claude Desktop, Cursor and Windsurf; use a top-level `servers` key for VS Code in `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "bakom-mcp": {
      "command": "uvx",
      "args": [
        "bakom-mcp"
      ]
    }
  }
}
```
<!-- END GENERATED: install -->
