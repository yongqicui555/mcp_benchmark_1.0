[🇬🇧 English Version](README.md)

> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# 📡 bakom-mcp

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/malkreide/bakom-mcp/releases)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Auth](https://img.shields.io/badge/auth-nicht%20erforderlich-brightgreen)](https://www.bakom.admin.ch/bakom/de/home/digitale-schweiz-und-internet/open-data.html)
![CI](https://github.com/malkreide/bakom-mcp/actions/workflows/ci.yml/badge.svg)

> MCP-Server für BAKOM Open Data – Breitband, Mobilfunk, Medien und Schweizer Telekommunikationsstatistiken.

<p align="center">
  <img src="assets/demo.svg" alt="Demo: Claude fragt Glasfaser- und 5G-Abdeckung via MCP Tool Call ab" width="720">
</p>

---

## Übersicht

**bakom-mcp** verbindet KI-Assistenten wie Claude mit der Open-Data-Infrastruktur des Bundesamts für Kommunikation (BAKOM). Ermöglicht Abfragen in natürlicher Sprache zu Breitbandverfügbarkeit, 5G/4G-Abdeckung, Mobilfunkstandorten, konzessionierten Rundfunkveranstaltern (RTV-Datenbank) und Telekommunikationsstatistiken – ohne API-Schlüssel.

Alle Daten sind als Open Government Data (OGD) auf opendata.swiss / geo.admin.ch unter **CC BY 4.0** veröffentlicht — siehe Sektion [Datenlizenz](#datenlizenz) für die Attribution-Anforderungen.

**Anker-Demo-Abfrage:** *«Welche Schulhäuser im Schulkreis 7 haben noch kein Glasfaser?»*

> `bakom_multi_standort_konnektivitaet` liefert die Vergleichstabelle automatisch.

[→ Weitere Anwendungsbeispiele nach Zielgruppe →](EXAMPLES.md)

---

## Geltungsbereich

### Was dieser Server tut

✓ Read-only-Abfragen gegen drei öffentliche BAKOM-/Bund-APIs:
  - `api3.geo.admin.ch` / `wms.geo.admin.ch` (Breitband, Mobilfunkabdeckung, Antennen)
  - `ckan.opendata.swiss` (Telekomstatistiken, Datensatz-Metadaten)
  - `rtvdb.ofcomnet.ch` (Konzessionierte Radio-/TV-Veranstalter)

✓ Liefert aggregierte, anonyme Daten — keine Personendaten, keine Haushalts-Identifikation.

✓ Auf Schweizer WGS84-Koordinaten begrenzt (lat 45.8–47.9, lon 5.9–10.6) via Pydantic-Input-Validation.

✓ Egress ist auf eine [Code-Layer-Allow-List](src/bakom_mcp/server.py) der sechs bekannten Datenquellen-Hosts beschränkt.

### Was dieser Server nicht tut

✗ Daten irgendwohin senden (read-only, keine Schreibtools).

✗ Auf das lokale Dateisystem zugreifen (kein Path-Traversal-Vektor).

✗ Authentifizierungs-Tokens nutzen (nicht nötig — alle Quellen sind öffentliche OGD).

✗ User-Eingaben über Calls hinweg cachen oder persistieren.

✗ Shell-Befehle oder beliebigen Code ausführen (kein `subprocess`/`os.system`/`eval`).

---

## Funktionen

- 📶 **Breitbandverfügbarkeit** – Festnetzabdeckung bei 30/100/300/500/1000 Mbit/s (250×250m-Raster)
- 🔌 **Glasfaserstatus** – FTTB/FTTH-Verfügbarkeit pro Standort
- 📍 **Multi-Standort-Vergleich** – Konnektivitätsprüfung für bis zu 20 Standorte gleichzeitig
- 📱 **Mobilfunkabdeckung** – 5G/4G/3G Outdoor-Abdeckung (100×100m-Raster)
- 📡 **Antennensuche** – Mobil- und Sendeanlagen im konfigurierbaren Radius
- 📺 **RTV-Datenbank** – Konzessionierte Radio- und TV-Sender nach Name, Typ, Kanton
- 🗞️ **Medienlandschaft** – BAKOM-Medienstrukturberichte und Datensätze
- 📊 **Telekommunikationsstatistik** – Festnetz, Mobilfunk, Breitband-Marktdaten via opendata.swiss
- 🗂️ **Breitbandatlas-Katalog** – Alle BAKOM-Datensatz-Layer mit direkten API-Links
- 🔓 **Keine Authentifizierung** – Alle Daten sind Open Government Data (OGD)

---

## Voraussetzungen

- Python 3.11+
- `uv` oder `pip` für die Installation
- Internetverbindung (Live-APIs: geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch)

---

## Installation

```bash
# Empfohlen: uvx (keine dauerhafte Installation nötig)
uvx bakom-mcp

# Oder mit pip installieren
pip install bakom-mcp

# Entwicklungs-Installation
git clone https://github.com/malkreide/bakom-mcp
cd bakom-mcp
pip install -e ".[dev]"
```

---

## Quickstart

### Claude Desktop

In `claude_desktop_config.json` eintragen:

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

**Pfad zur Konfigurationsdatei:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Cloud / HTTP-Transport

```bash
python -m bakom_mcp.server --http
# Server läuft auf http://localhost:8050/mcp
```

Konfiguration über Umgebungsvariablen (siehe [`.env.example`](.env.example)):

| Variable | Default | Zweck |
|---|---|---|
| `BAKOM_MCP_HOST` | `127.0.0.1` | Bind-Adresse. Nur in vertrauenswürdigen Netzen auf `0.0.0.0` setzen (Warnung wird geloggt). |
| `BAKOM_MCP_PORT` | `8050` | TCP-Port. |
| `BAKOM_MCP_CORS_ORIGINS` | _(leer)_ | Kommagetrennte erlaubte Origins für Browser-Clients. Leer = CORS deaktiviert. |

### Docker

Ein gehärtetes Container-Image steht bereit. Geeignet für Cloud-Deployments hinter einem Reverse-Proxy (Caddy, Traefik, nginx).

```bash
# Mit compose (empfohlen)
docker compose up --build

# Oder direkt mit docker run
docker build -t bakom-mcp:latest .
docker run --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --tmpfs /tmp:rw,size=16M \
  -p 127.0.0.1:8050:8050 \
  bakom-mcp:latest
```

Das Image läuft als **non-root** (UID 10001), nutzt ein **read-only-Dateisystem**, entzieht **alle Linux-Capabilities** und verbietet **Privilege-Escalation**. Resource-Limits sind in [`docker-compose.yml`](docker-compose.yml) konfiguriert (256 MB Memory, 0.5 CPU, 64 PIDs). Das Default-Port-Mapping bindet nur auf `127.0.0.1` — für öffentliche Erreichbarkeit ist ein Reverse-Proxy mit TLS- und CORS-Terminierung vorzuschalten.

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

> 💡 *«stdio für den Entwickler-Laptop, HTTP/SSE für den Browser.»*

---

## Verfügbare Tools (12)

### Breitband & Konnektivität

| Tool | Beschreibung |
|------|--------------|
| `bakom_broadband_coverage` | Festnetzabdeckung an einer Koordinate (30–1000 Mbit/s) |
| `bakom_glasfaser_verfuegbarkeit` | FTTB/FTTH-Glasfaserstatus |
| `bakom_multi_standort_konnektivitaet` | Konnektivitätsvergleich für bis zu 20 Standorte |

### Mobilfunk & Sendeanlagen

| Tool | Beschreibung |
|------|--------------|
| `bakom_mobilfunk_abdeckung` | 5G/4G/3G Outdoor-Abdeckung |
| `bakom_sendeanlagen_suche` | Mobilfunkanlagen im konfigurierbaren Radius |
| `bakom_frequenzdaten` | Radio-/TV-Sendeanlagen in der Nähe |

### Medien & RTV

| Tool | Beschreibung |
|------|--------------|
| `bakom_rtv_suche` | Konzessionierte Sender suchen (RTV-Datenbank) |
| `bakom_medienstruktur_info` | Schweizer Medienlandschaft – Datensätze |
| `bakom_aktuell` | Aktuelle BAKOM-Themen (5G, Medien, KI, Post) |

### Statistik & Katalog

| Tool | Beschreibung |
|------|--------------|
| `bakom_telekomstatistik_uebersicht` | Telekommunikationsstatistik von opendata.swiss |
| `bakom_breitbandatlas_datensaetze` | Vollständiger Katalog aller Breitbandatlas-Layer |
| `bakom_check_api_status` | 🔍 Systemstatus aller konfigurierten Datenquellen |

---

## Beispiel-Prompts

```
Wie ist die Breitbandversorgung beim Schulhaus Leutschenbach (47.4148, 8.5654)?

Vergleiche 5G und Glasfaserabdeckung für diese drei Schulhäuser: [Koordinaten]

Welche Radiosender sind im Kanton Zürich konzessioniert?

Was ist die aktuelle BAKOM-Haltung zur 5G-Frequenzvergabe?

Liste alle Breitbandatlas-Datensätze auf, die via geo.admin.ch verfügbar sind.
```

---

## Sicherheit & Limits

| Aspekt | Details |
|--------|---------|
| **Zugriff** | Nur lesend (`readOnlyHint: true`) — der Server kann keine Daten verändern oder löschen |
| **Personendaten** | Keine Personendaten — alle Quellen sind aggregierte, öffentliche Open Data |
| **Rate Limits** | Eingebaute Abfrage-Limits (max. 50 Antennen, max. 20 Standorte, max. 50 RTV-Resultate) |
| **Timeout** | 20 Sekunden pro API-Aufruf |
| **Authentifizierung** | Keine API-Schlüssel nötig — alle 3 APIs sind öffentlich zugänglich |
| **Lizenzen** | Alle Daten unter CC0 / offenen Lizenzen (Open Government Data) |
| **Nutzungsbedingungen** | Unterliegt den Nutzungsbedingungen der Datenquellen: [geo.admin.ch](https://www.geo.admin.ch/de/allgemeine-nutzungsbedingungen-bgdi), [opendata.swiss](https://opendata.swiss/de/terms-of-use), [rtvdb.ofcomnet.ch](https://rtvdb.ofcomnet.ch) |

---

## Datenquellen

| Quelle | Daten | Authentifizierung |
|--------|-------|-------------------|
| [geo.admin.ch](https://api3.geo.admin.ch) | Breitbandatlas, Mobilfunkabdeckung, Antennenstandorte | Keine |
| [opendata.swiss](https://opendata.swiss) | BAKOM-Datensätze, Telekommunikationsstatistik | Keine |
| [rtvdb.ofcomnet.ch](https://rtvdb.ofcomnet.ch) | Konzessionierte Radio-/TV-Sender | Keine |

Alle Daten stehen unter offenen Lizenzen (CC0 / OGD).

---

## Synergien mit dem MCP-Portfolio

**bakom-mcp** lässt sich mit anderen Servern des Portfolios verketten:

```
zurich-opendata-mcp  →  Schulhausadressen
         +
    bakom-mcp         →  Glasfaser- und 5G-Status
         =
«Digitale Chancengerechtigkeit»-Dashboard für alle Schulkreise
```

Weitere Kombinationen:
- `srgssr-mcp` + `bakom-mcp` → Medienabdeckung und Sendernetz
- `swiss-statistics-mcp` + `bakom-mcp` → Telekom-Marktentwicklung
- `fedlex-mcp` + `bakom-mcp` → Regulierungskontext (RTVG, FMG)

---

## Projektstruktur

```
bakom-mcp/
├── src/bakom_mcp/
│   ├── __init__.py          # Paket
│   ├── server.py            # MCP-Server (12 Tools, 2 Resources)
│   └── py.typed             # PEP 561 Type-Marker
├── tests/
│   └── test_integration.py  # Integrationstests (Live-APIs)
├── assets/
│   └── demo.svg             # Demo-Flow-Diagramm
├── .github/workflows/
│   ├── ci.yml               # CI: Lint, Syntax, Import, Tests
│   └── publish.yml          # PyPI-Publish bei Release
├── .gitignore
├── pyproject.toml           # Build-Konfiguration (hatchling)
├── CHANGELOG.md
├── CONTRIBUTING.md          # Beitragsleitfaden (Englisch)
├── CONTRIBUTING.de.md       # Beitragsleitfaden (Deutsch)
├── SECURITY.md              # Sicherheitsrichtlinie (Englisch)
├── SECURITY.de.md           # Sicherheitsrichtlinie (Deutsch)
├── LICENSE                  # MIT-Lizenz
├── README.md                # Englische Hauptversion
└── README.de.md             # Diese Datei (Deutsch)
```

---

## Tests

```bash
# Unit-Tests (kein Netzwerk erforderlich)
PYTHONPATH=src pytest tests/ -m "not live"

# Integrationstests (Live-APIs, Internetverbindung erforderlich)
PYTHONPATH=src pytest tests/ -m "live"
```

---

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

---

## Mitwirken

Beiträge sind willkommen! Hinweise zu Fehlerberichten, Feature-Vorschlägen und Pull Requests finden sich in [CONTRIBUTING.de.md](CONTRIBUTING.de.md) ([🇬🇧 English](CONTRIBUTING.md)).

---

## Sicherheit

Um eine Schwachstelle zu melden, siehe die [Sicherheitsrichtlinie](SECURITY.de.md) ([🇬🇧 English](SECURITY.md)). Bitte melde Sicherheitsprobleme vertraulich über GitHub Security Advisories statt über öffentliche Issues.

---

## Software-Lizenz

MIT-Lizenz – siehe [LICENSE](LICENSE).

## Datenlizenz

Die BAKOM-Open-Data, die dieser Server liefert, sind unter **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de)** publiziert. Bei Verwendung oder Weiterveröffentlichung der Tool-Outputs bitte folgende Quellenangabe machen:

> *Quelle: Bundesamt für Kommunikation (BAKOM) via opendata.swiss / geo.admin.ch · Lizenz: CC BY 4.0*

Tool-Outputs enthalten diesen Footer bereits automatisch. Markdown-Antworten enden mit der Attribution-Zeile; nachgelagerte Anwendungen, die das JSON-Format konsumieren, sollten die Quellen- und Lizenz-Information an ihre Endnutzer weiterreichen.

---

## Autor

Hayal Oezkan · [github.com/malkreide](https://github.com/malkreide)

---

## Credits & Verwandte Projekte

- **Daten:** [BAKOM Open Data](https://www.bakom.admin.ch/bakom/de/home/digitale-schweiz-und-internet/open-data.html) – Bundesamt für Kommunikation (BAKOM)
- **Geodaten:** [geo.admin.ch](https://api3.geo.admin.ch) – swisstopo / Bundesinfrastruktur für Geodaten
- **Protokoll:** [Model Context Protocol](https://modelcontextprotocol.io/) – Anthropic / Linux Foundation
- **Verwandt:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) – MCP-Server für Zürcher Stadtdaten
- **Verwandt:** [swiss-transport-mcp](https://github.com/malkreide/swiss-transport-mcp) – MCP-Server für den Schweizer ÖV
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

---

*Teil des Schweizer Open-Data-MCP-Portfolios — öffentliche Daten verdienen öffentliche Schnittstellen.*
