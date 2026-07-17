> 🇨🇭 **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

# 📊 zh-education-mcp

![Version](https://img.shields.io/badge/version-0.2.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![No Auth Required](https://img.shields.io/badge/auth-none%20required-brightgreen)](https://github.com/malkreide/zh-education-mcp)
![CI](https://github.com/malkreide/zh-education-mcp/actions/workflows/ci.yml/badge.svg)

> MCP server for education statistics of the Canton and City of Zurich (BISTA)

[🇩🇪 Deutsche Version](README.de.md)

---

## Overview

`zh-education-mcp` connects AI assistants to the **Bildungsstatistik Kanton Zürich (BISTA)** — the official education statistics of the Canton of Zurich. It provides structured access to pupil numbers, school district trends, secondary school profiles, nationality breakdowns, and gymnasium graduation rates.

| Source | Data | API |
|--------|------|-----|
| **BISTA Kanton Zürich** | Learner statistics (Volksschule, Mittelschulen, Maturität) | REST/CSV |

All data is fetched from the **BISTA public API** (`bista.zh.ch/basicapi/ogd/`) — no API key required. Data is updated annually on 15 September (reference date).

**Anchor demo query:** *"How has the number of pupils in school district Letzi developed over the last 5 years?"*

---

## Demo

<p align="center">
  <img src="assets/demo.png" alt="zh-education-mcp demo: Claude queries BISTA data" width="720">
</p>

---

## Features

- 📊 **8 tools** for education data across all school levels
- 🔍 **School district trends** — pupil numbers for all Schulkreise (Letzi, Glattal, Schwamendingen, Oerlikon, Uto, Waidberg, Zürichberg) from 2000 to present
- 🏫 **Secondary school profiles** — breakdown by requirement type (Sek A/B/C, Mittelschule, special classes)
- 🌐 **Nationality structure** — top nationalities of pupils per school community
- 🎓 **Gymnasium graduation rates** — Maturitätsquote by municipality, district, and canton
- 📈 **Canton-wide overview** — all learners by school level, type, gender, and nationality
- 🏠 **Residence-based trends** — pupil counts by place of residence (Bezirk / Gemeinde)
- 🏛️ **Mittelschulen** — Gymnasium, FMS, HMS statistics
- 🔓 **No API key required** — all data under CC BY 4.0
- ☁️ **Dual transport** — stdio (Claude Desktop) + Streamable HTTP (cloud)

---

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

---

## Installation

```bash
# Clone the repository
git clone https://github.com/malkreide/zh-education-mcp.git
cd zh-education-mcp

# Install
pip install -e .
# or with uv:
uv pip install -e .
```

Or with `uvx` (no permanent installation):

```bash
uvx zh-education-mcp
```

---

## Quickstart

```bash
# stdio (for Claude Desktop)
python -m zh_education_mcp.server

# Streamable HTTP (port 8000)
python -m zh_education_mcp.server --http --port 8000
```

Try it immediately in Claude Desktop:

> *"Wie hat sich die Lernendenzahl im Schulkreis Letzi entwickelt?"*
> *"Zeige die Maturitätsquote der Stadt Zürich"*
> *"Welche Nationalitäten sind in Adliswil am häufigsten?"*

→ [More use cases by audience](EXAMPLES.md) →

---

## Configuration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "zh-education": {
      "command": "python",
      "args": ["-m", "zh_education_mcp.server"]
    }
  }
}
```

Or with `uvx`:

```json
{
  "mcpServers": {
    "zh-education": {
      "command": "uvx",
      "args": ["zh-education-mcp"]
    }
  }
}
```

**Config file locations:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Cloud Deployment (Streamable HTTP for browser access)

For use via **claude.ai in the browser** (e.g. on managed workstations without local software):

**Render.com (recommended):**
1. Push/fork the repository to GitHub
2. On [render.com](https://render.com): New Web Service → runtime **Docker** (uses the provided `Dockerfile`)
3. Set env vars: `MCP_TRANSPORT=streamable-http`, `MCP_HOST=0.0.0.0`, `MCP_PORT=8000`, and `MCP_CORS_ORIGINS=https://claude.ai`
4. In claude.ai under Settings → MCP Servers, add: `https://your-app.onrender.com/mcp`

> 💡 *"stdio for the developer laptop, Streamable HTTP for the browser."*

Health probe: `GET /health`. Full deployment guide (container, load balancing, CORS,
resource limits): [`docs/deployment.md`](docs/deployment.md).

---

## Available Tools

| Tool | Description |
|------|-------------|
| `zh_edu_list_schulgemeinden` | List all school communities / Schulkreise in Canton Zurich |
| `zh_edu_schulkreis_trend` | Pupil trend by Schulkreis (2000–present) |
| `zh_edu_overview` | Canton-wide learner overview by school level |
| `zh_edu_sek1_profil` | Secondary I profile (Sek A/B/C breakdown) |
| `zh_edu_staatsangehoerigkeiten` | Nationality structure of pupils per school community |
| `zh_edu_maturitaetsquote` | Gymnasium graduation rates by municipality / district |
| `zh_edu_wohnort_trend` | Residence-based learner trend (Bezirk / Gemeinde) |
| `zh_edu_mittelschulen` | Secondary school statistics (Gymnasium, FMS, HMS) |

### Example Use Cases

| Query | Tool |
|-------|------|
| *"List all Schulkreise in Zurich"* | `zh_edu_list_schulgemeinden` |
| *"Pupil trend in Letzi over 5 years"* | `zh_edu_schulkreis_trend` |
| *"How many Sek A vs Sek B in Winterthur?"* | `zh_edu_sek1_profil` |
| *"Top nationalities in Zürich-Letzi"* | `zh_edu_staatsangehoerigkeiten` |
| *"Maturitätsquote of Stadt Zürich"* | `zh_edu_maturitaetsquote` |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌──────────────────────────┐
│   Claude / AI   │────▶│  zh-education-mcp            │────▶│  BISTA Kanton Zürich     │
│   (MCP Host)    │◀────│  (MCP Server)                │◀────│  REST/CSV (Public API)   │
└─────────────────┘     │                              │     └──────────────────────────┘
                        │  8 Tools                     │
                        │  Stdio | Streamable HTTP     │
                        │  24h Cache                   │
                        │  No authentication required  │
                        └──────────────────────────────┘
```

### Data Source Characteristics

| Source | Protocol | Coverage | Auth | Update |
|--------|----------|----------|------|--------|
| BISTA Kanton ZH | REST/CSV | Learner statistics 2000–present | None | Annual (15 Sep) |

---

## Project Structure

```
zh-education-mcp/
├── src/zh_education_mcp/
│   ├── __init__.py              # Package
│   ├── config.py               # ENV settings (MCP_*)
│   ├── constants.py            # API base, endpoints, timeouts
│   ├── logging_setup.py        # structured stderr logging
│   ├── provenance.py           # response envelope, license attribution
│   ├── http_client.py          # egress guard, connection pool, lifespan
│   ├── data.py                 # cache, CSV fetch, filters, error handling
│   ├── models.py               # Pydantic input models
│   ├── tools.py                # FastMCP instance, 8 tools, 2 resources
│   └── server.py               # thin composition layer + entrypoint
├── tests/
│   └── test_server.py           # Unit tests (mocked HTTP with respx)
├── docs/                        # deployment, security, egress, roadmap, …
├── Dockerfile                   # multi-stage, non-root, healthcheck
├── docker-compose.yml           # resource limits, read-only rootfs
├── .github/workflows/ci.yml     # GitHub Actions (Python 3.11/3.12/3.13)
├── .github/dependabot.yml       # monthly dependency updates
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md              # + CONTRIBUTING.de.md
├── SECURITY.md                  # + SECURITY.de.md
├── LICENSE
├── README.md                    # This file (English)
└── README.de.md                 # German version
```

---

## Known Limitations

- **Annual updates only:** BISTA data is updated once per year (reference date: 15 September). The 24h in-memory cache matches this cycle.
- **CSV-based API:** The BISTA API returns CSV data; large datasets may take a moment to parse.
- **School community names:** Names must match exactly (use `zh_edu_list_schulgemeinden` to find valid names).

---

## Safety & Limits

| Topic | Details |
|-------|---------|
| **No personal data** | BISTA statistics are aggregated — no individual pupil data is exposed or accessible. All figures are anonymized at the school community level. |
| **Read-only** | All tools are read-only (`readOnlyHint: true`). The server cannot modify, delete, or write any data. |
| **No authentication** | The BISTA API is fully public. No API keys, tokens, or credentials are stored or transmitted. |
| **Rate limits** | The BISTA API has no documented rate limit, but the server uses a 24h in-memory cache to minimize requests. Please use responsibly. |
| **Data license** | All data is published under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) by the Canton of Zurich. Attribution: *Bildungsstatistik Kanton Zürich (BISTA)*. |
| **Terms of Service** | Usage is subject to the [BISTA terms of use](https://pub.bista.zh.ch). The MCP server is an independent open-source project and is not affiliated with the Canton of Zurich. |
| **AI output disclaimer** | Statistics are passed through as-is from the BISTA API. AI-generated interpretations or summaries should be verified against the [official BISTA portal](https://pub.bista.zh.ch). |

---

## Testing

```bash
# Unit tests (no API calls)
PYTHONPATH=src pytest tests/ -m "not live"

# Integration tests (live API calls)
pytest tests/ -m "live"
```

---

## MCP Protocol Version

This server targets the MCP specification as implemented by the pinned `mcp[cli]`
SDK (see `pyproject.toml`). Protocol/spec-version bumps are recorded in
[CHANGELOG.md](CHANGELOG.md). Dependencies (incl. the MCP SDK) receive monthly
update PRs via Dependabot (`.github/dependabot.yml`).

**Project phase:** Phase 1 — *read-only* (all tools `readOnlyHint: true`). See
[docs/roadmap.md](docs/roadmap.md).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) · [🇩🇪 Beitragen](CONTRIBUTING.de.md)

---

## Security

See [SECURITY.md](SECURITY.md) · [🇩🇪 Sicherheit](SECURITY.de.md)

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

Hayal Oezkan · [malkreide](https://github.com/malkreide)

---

## Credits & Related Projects

- **BISTA:** [pub.bista.zh.ch](https://pub.bista.zh.ch) — Bildungsstatistik Kanton Zürich (CC BY 4.0)
- **Protocol:** [Model Context Protocol](https://modelcontextprotocol.io/) — Anthropic / Linux Foundation
- **Related:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) — Zurich city open data (parking, weather, parliament)
- **Related:** [swiss-cultural-heritage-mcp](https://github.com/malkreide/swiss-cultural-heritage-mcp) — Swiss cultural heritage data
- **Related:** [fedlex-mcp](https://github.com/malkreide/fedlex-mcp) — Swiss federal law
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

<!-- mcp-name: io.github.malkreide/zh-education-mcp -->

<!-- BEGIN GENERATED: install -->
## Installation

Run via [`uv`](https://docs.astral.sh/uv/)'s `uvx` — no clone or manual install needed. Add to your MCP client config (`mcpServers` for Claude Desktop, Cursor and Windsurf; use a top-level `servers` key for VS Code in `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "zh-education-mcp": {
      "command": "uvx",
      "args": [
        "zh-education-mcp"
      ]
    }
  }
}
```
<!-- END GENERATED: install -->
