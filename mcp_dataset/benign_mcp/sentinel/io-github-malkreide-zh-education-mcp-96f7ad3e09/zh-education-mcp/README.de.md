> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# 📊 zh-education-mcp

![Version](https://img.shields.io/badge/version-0.2.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![No Auth Required](https://img.shields.io/badge/auth-none%20required-brightgreen)](https://github.com/malkreide/zh-education-mcp)
![CI](https://github.com/malkreide/zh-education-mcp/actions/workflows/ci.yml/badge.svg)

> MCP-Server für Bildungsstatistiken des Kantons und der Stadt Zürich (BISTA)

[🇬🇧 English Version](README.md)

---

## Überblick

`zh-education-mcp` verbindet KI-Assistenten mit der **Bildungsstatistik Kanton Zürich (BISTA)** — den offiziellen Bildungsdaten des Kantons Zürich. Der Server bietet strukturierten Zugang zu Lernendenzahlen, Schulkreis-Trends, Sekundarschulprofilen, Nationalitätenstrukturen und Maturitätsquoten.

| Quelle | Daten | API |
|--------|-------|-----|
| **BISTA Kanton Zürich** | Lernenden-Statistiken (Volksschule, Mittelschulen, Maturität) | REST/CSV |

Alle Daten stammen von der **BISTA Public API** (`bista.zh.ch/basicapi/ogd/`) — kein API-Schlüssel erforderlich. Stichtag: 15. September (jährlich).

**Anker-Abfrage:** *«Wie hat sich die Anzahl Lernender im Schulkreis Letzi in den letzten 5 Jahren entwickelt?»*

---

## Demo

<p align="center">
  <img src="assets/demo.png" alt="zh-education-mcp Demo: Claude fragt BISTA-Daten ab" width="720">
</p>

---

## Funktionen

- 📊 **8 Tools** für Bildungsdaten über alle Schulstufen
- 🔍 **Schulkreis-Trends** — Lernendenzahlen für alle Schulkreise (Letzi, Glattal, Schwamendingen, Oerlikon, Uto, Waidberg, Zürichberg) ab 2000
- 🏫 **Sekundarschulprofile** — Aufschlüsselung nach Anforderungstyp (Sek A/B/C, Mittelschule, Sonderklassen)
- 🌐 **Nationalitätenstruktur** — Häufigste Staatsangehörigkeiten der Lernenden pro Schulgemeinde
- 🎓 **Maturitätsquoten** — Gymnasiale Maturitätsquote nach Gemeinde, Bezirk und Kanton
- 📈 **Kantonsweite Übersicht** — Alle Lernenden nach Stufe, Schultyp, Geschlecht und Staatsangehörigkeit
- 🏠 **Wohnort-Trends** — Lernendenzahlen nach Wohnort (Bezirk / Gemeinde)
- 🏛️ **Mittelschulen** — Gymnasium, FMS, HMS Statistiken
- 🔓 **Kein API-Schlüssel** — alle Daten unter CC BY 4.0
- ☁️ **Dual Transport** — stdio (Claude Desktop) + Streamable HTTP (Cloud)

---

## Voraussetzungen

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (empfohlen) oder pip

---

## Installation

```bash
# Repository klonen
git clone https://github.com/malkreide/zh-education-mcp.git
cd zh-education-mcp

# Installieren
pip install -e .
# oder mit uv:
uv pip install -e .
```

Oder mit `uvx` (ohne permanente Installation):

```bash
uvx zh-education-mcp
```

---

## Schnellstart

```bash
# stdio (für Claude Desktop)
python -m zh_education_mcp.server

# Streamable HTTP (Port 8000)
python -m zh_education_mcp.server --http --port 8000
```

Sofort ausprobieren in Claude Desktop:

> *«Wie hat sich die Lernendenzahl im Schulkreis Letzi entwickelt?»*
> *«Zeige die Maturitätsquote der Stadt Zürich»*
> *«Welche Nationalitäten sind in Adliswil am häufigsten?»*

→ [Weitere Anwendungsbeispiele nach Zielgruppe](EXAMPLES.md) →

---

## Konfiguration

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) oder `%APPDATA%\Claude\claude_desktop_config.json` (Windows) bearbeiten:

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

Oder mit `uvx`:

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

### Cloud-Deployment (Streamable HTTP für Browser-Zugang)

Für die Nutzung via **claude.ai im Browser** (z. B. auf verwalteten Arbeitsplätzen ohne lokale Software):

**Render.com (empfohlen):**
1. Repository auf GitHub pushen/forken
2. Auf [render.com](https://render.com): New Web Service → Runtime **Docker** (nutzt das mitgelieferte `Dockerfile`)
3. Env-Vars setzen: `MCP_TRANSPORT=streamable-http`, `MCP_HOST=0.0.0.0`, `MCP_PORT=8000`, `MCP_CORS_ORIGINS=https://claude.ai`
4. In claude.ai unter Einstellungen → MCP Servers hinzufügen: `https://your-app.onrender.com/mcp`

> 💡 *«stdio für den Entwickler-Laptop, Streamable HTTP für den Browser.»*

Health-Probe: `GET /health`. Vollständiger Deployment-Guide (Container, Load Balancing,
CORS, Resource-Limits): [`docs/deployment.md`](docs/deployment.md).

---

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `zh_edu_list_schulgemeinden` | Alle Schulgemeinden / Schulkreise im Kanton Zürich auflisten |
| `zh_edu_schulkreis_trend` | Lernenden-Trend nach Schulkreis (ab 2000) |
| `zh_edu_overview` | Kantonsweite Lernenden-Übersicht nach Schulstufe |
| `zh_edu_sek1_profil` | Sekundarstufe-I-Profil (Sek A/B/C Aufschlüsselung) |
| `zh_edu_staatsangehoerigkeiten` | Staatsangehörigkeitsstruktur pro Schulgemeinde |
| `zh_edu_maturitaetsquote` | Gymnasiale Maturitätsquote nach Gemeinde / Bezirk |
| `zh_edu_wohnort_trend` | Lernenden-Trend nach Wohnort (Bezirk / Gemeinde) |
| `zh_edu_mittelschulen` | Mittelschulstatistiken (Gymnasium, FMS, HMS) |

### Beispiel-Abfragen

| Abfrage | Tool |
|---------|------|
| *«Alle Schulkreise in Zürich auflisten»* | `zh_edu_list_schulgemeinden` |
| *«Lernenden-Trend Letzi über 5 Jahre»* | `zh_edu_schulkreis_trend` |
| *«Wie viele Sek A vs Sek B in Winterthur?»* | `zh_edu_sek1_profil` |
| *«Top-Nationalitäten in Zürich-Letzi»* | `zh_edu_staatsangehoerigkeiten` |
| *«Maturitätsquote der Stadt Zürich»* | `zh_edu_maturitaetsquote` |

---

## Architektur

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌──────────────────────────┐
│   Claude / AI   │────▶│  zh-education-mcp            │────▶│  BISTA Kanton Zürich     │
│   (MCP Host)    │◀────│  (MCP Server)                │◀────│  REST/CSV (Public API)   │
└─────────────────┘     │                              │     └──────────────────────────┘
                        │  8 Tools                     │
                        │  Stdio | Streamable HTTP     │
                        │  24h Cache                   │
                        │  Keine Auth erforderlich     │
                        └──────────────────────────────┘
```

---

## Projektstruktur

```
zh-education-mcp/
├── src/zh_education_mcp/
│   ├── __init__.py              # Package
│   ├── config.py               # ENV-Settings (MCP_*)
│   ├── constants.py            # API-Basis, Endpunkte, Timeouts
│   ├── logging_setup.py        # strukturiertes stderr-Logging
│   ├── provenance.py           # Response-Envelope, Lizenz-Attribution
│   ├── http_client.py          # Egress-Guard, Connection-Pool, Lifespan
│   ├── data.py                 # Cache, CSV-Fetch, Filter, Fehlerbehandlung
│   ├── models.py               # Pydantic-Input-Modelle
│   ├── tools.py                # FastMCP-Instanz, 8 Tools, 2 Resources
│   └── server.py               # schlanke Kompositionsschicht + Einstieg
├── tests/
│   └── test_server.py           # Unit-Tests (gemocktes HTTP mit respx)
├── docs/                        # Deployment, Security, Egress, Roadmap, …
├── Dockerfile                   # Multi-Stage, non-root, Healthcheck
├── docker-compose.yml           # Resource-Limits, read-only rootfs
├── .github/workflows/ci.yml     # GitHub Actions (Python 3.11/3.12/3.13)
├── .github/dependabot.yml       # monatliche Dependency-Updates
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md              # + CONTRIBUTING.de.md
├── SECURITY.md                  # + SECURITY.de.md
├── LICENSE
├── README.md                    # English Version
└── README.de.md                 # Diese Datei (Deutsch)
```

---

## Bekannte Einschränkungen

- **Jährliche Aktualisierung:** BISTA-Daten werden einmal jährlich aktualisiert (Stichtag: 15. September). Der 24h-In-Memory-Cache passt zu diesem Zyklus.
- **CSV-basierte API:** Die BISTA-API liefert CSV-Daten; grosse Datensätze können einen Moment zum Parsen brauchen.
- **Schulgemeinde-Namen:** Namen müssen exakt übereinstimmen (`zh_edu_list_schulgemeinden` zeigt gültige Namen).

---

## Sicherheit & Grenzen

| Thema | Details |
|-------|---------|
| **Keine Personendaten** | BISTA-Statistiken sind aggregiert — es werden keine individuellen Schülerdaten offengelegt. Alle Zahlen sind auf Ebene Schulgemeinde anonymisiert. |
| **Nur lesend** | Alle Tools sind schreibgeschützt (`readOnlyHint: true`). Der Server kann keine Daten verändern, löschen oder schreiben. |
| **Keine Authentifizierung** | Die BISTA-API ist vollständig öffentlich. Es werden keine API-Schlüssel, Tokens oder Zugangsdaten gespeichert oder übertragen. |
| **Rate Limits** | Die BISTA-API hat kein dokumentiertes Rate Limit. Der Server nutzt einen 24h-In-Memory-Cache, um Anfragen zu minimieren. Bitte verantwortungsvoll nutzen. |
| **Datenlizenz** | Alle Daten stehen unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) des Kantons Zürich. Quellenangabe: *Bildungsstatistik Kanton Zürich (BISTA)*. |
| **Nutzungsbedingungen** | Die Nutzung unterliegt den [BISTA-Nutzungsbedingungen](https://pub.bista.zh.ch). Der MCP-Server ist ein unabhängiges Open-Source-Projekt ohne Verbindung zum Kanton Zürich. |
| **KI-Ausgabe-Hinweis** | Statistiken werden 1:1 von der BISTA-API durchgereicht. KI-generierte Interpretationen oder Zusammenfassungen sollten am [offiziellen BISTA-Portal](https://pub.bista.zh.ch) verifiziert werden. |

---

## Testen

```bash
# Unit-Tests (keine API-Aufrufe)
PYTHONPATH=src pytest tests/ -m "not live"

# Integrationstests (echte API-Aufrufe)
pytest tests/ -m "live"
```

---

## MCP-Protokoll-Version

Dieser Server zielt auf die MCP-Spezifikation in der Fassung des gepinnten
`mcp[cli]`-SDK (siehe `pyproject.toml`). Protokoll-/Spec-Versionssprünge werden
im [CHANGELOG.md](CHANGELOG.md) dokumentiert. Abhängigkeiten (inkl. MCP-SDK)
erhalten monatliche Update-PRs via Dependabot (`.github/dependabot.yml`).

**Projektphase:** Phase 1 — *read-only* (alle Tools `readOnlyHint: true`). Siehe
[docs/roadmap.md](docs/roadmap.md).

---

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

---

## Mitmachen

Siehe [CONTRIBUTING.de.md](CONTRIBUTING.de.md) · [🇬🇧 Contributing](CONTRIBUTING.md)

---

## Sicherheit

Siehe [SECURITY.de.md](SECURITY.de.md) · [🇬🇧 Security](SECURITY.md)

---

## Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)

---

## Autor

Hayal Oezkan · [malkreide](https://github.com/malkreide)

---

## Credits & Verwandte Projekte

- **BISTA:** [pub.bista.zh.ch](https://pub.bista.zh.ch) — Bildungsstatistik Kanton Zürich (CC BY 4.0)
- **Protokoll:** [Model Context Protocol](https://modelcontextprotocol.io/) — Anthropic / Linux Foundation
- **Verwandt:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) — Zürcher Open Data (Parking, Wetter, Parlament)
- **Verwandt:** [swiss-cultural-heritage-mcp](https://github.com/malkreide/swiss-cultural-heritage-mcp) — Schweizer Kulturerbe-Daten
- **Verwandt:** [fedlex-mcp](https://github.com/malkreide/fedlex-mcp) — Schweizer Bundesrecht
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)
