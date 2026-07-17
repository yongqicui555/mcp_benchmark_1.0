# Mitwirken bei bakom-mcp

[🇬🇧 English Version](CONTRIBUTING.md)

Vielen Dank für dein Interesse, zu **bakom-mcp** beizutragen! Dieser Server ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide) und verbindet KI-Assistenten mit den Open Data des Bundesamts für Kommunikation (BAKOM).

---

## Inhaltsverzeichnis

- [Verhaltenskodex](#verhaltenskodex)
- [Fehler melden](#fehler-melden)
- [Funktionen vorschlagen](#funktionen-vorschlagen)
- [Entwicklungsumgebung](#entwicklungsumgebung)
- [Code-Stil](#code-stil)
- [Tests](#tests)
- [Pull-Request-Prozess](#pull-request-prozess)
- [Datenquellen & APIs](#datenquellen--apis)

---

## Verhaltenskodex

Dieses Projekt folgt den üblichen Normen der Open-Source-Community: respektvoll, konstruktiv und kollaborativ. Issues und Pull Requests, die beleidigend oder themenfremd sind, werden geschlossen.

---

## Fehler melden

1. **Bestehende Issues prüfen** – dein Fehler wurde möglicherweise bereits gemeldet.
2. Eröffne ein [neues Issue](https://github.com/malkreide/bakom-mcp/issues/new) und gib an:
   - Einen klaren Titel und eine Beschreibung
   - Schritte zur Reproduktion
   - Erwartetes vs. tatsächliches Verhalten
   - Python-Version (`python --version`)
   - Fehlerausgabe / Stack-Trace (falls zutreffend)
   - Den Namen des fehlerhaften Tools (z.B. `bakom_mobilfunk_abdeckung`)

> **Tipp:** Bei Problemen mit vorgelagerten APIs (geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch) vermerke bitte auch, ob der API-Endpunkt selbst einen Fehler zurückgibt, wenn er direkt aufgerufen wird.

---

## Funktionen vorschlagen

Eröffne ein [neues Issue](https://github.com/malkreide/bakom-mcp/issues/new) mit dem Label `enhancement` und beschreibe:

- Den Anwendungsfall (wer profitiert, in welchem Kontext?)
- Die BAKOM-Datenquelle, die du im Sinn hast
- Ob die Daten ohne Authentifizierung verfügbar sind (OGD/CC0 bevorzugt)

Priorität haben Tools, die zum **Anker-Anwendungsfall** passen: Analyse der Breitband- und Mobilfunkabdeckung für öffentliche Infrastruktur (z.B. Schulhäuser, kommunale Einrichtungen).

---

## Entwicklungsumgebung

```bash
# 1. Repository forken und klonen
git clone https://github.com/<dein-benutzername>/bakom-mcp.git
cd bakom-mcp

# 2. Im editierbaren Modus mit Dev-Abhängigkeiten installieren
pip install -e ".[dev]"

# 3. Setup verifizieren
PYTHONPATH=src pytest tests/ -m "not live" -v
```

### Voraussetzungen

- Python 3.11+
- `uv` oder `pip`
- Internetverbindung für Live-API-Tests

---

## Code-Stil

Dieses Projekt verwendet [Ruff](https://docs.astral.sh/ruff/) für Linting und Formatierung.

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Beides in einem Schritt (CI-Äquivalent)
ruff check src/ tests/ && ruff format --check src/ tests/
```

**Wichtige Konventionen:**
- Dem bestehenden `src/`-Layout folgen (`src/bakom_mcp/`)
- Type-Hints für alle Funktionssignaturen
- Docstrings für alle öffentlichen Tool-Funktionen (werden von MCP-Clients als Tool-Beschreibungen genutzt)
- Tool-Namen folgen dem Muster `bakom_<resource>_<action>` (snake_case)
- Keine API-Schlüssel oder Credentials — alle BAKOM-Tools dürfen nur offene Endpunkte nutzen

---

## Tests

Tests sind in Unit-/Mock-Tests und Live-API-Tests aufgeteilt:

```bash
# Unit-Tests (kein Netzwerk erforderlich — laufen immer in der CI)
PYTHONPATH=src pytest tests/ -m "not live" -v

# Live-Integrationstests (Internetzugang erforderlich)
PYTHONPATH=src pytest tests/ -m "live" -v
```

Live-Tests mit `@pytest.mark.live` markieren:

```python
import pytest

@pytest.mark.live
def test_broadband_coverage_live():
    # ruft den echten geo.admin.ch-Endpunkt auf
    ...
```

**CI-Matrix:** Tests laufen über GitHub Actions auf Python 3.11, 3.12 und 3.13. Alle PRs müssen die Nicht-Live-Test-Suite bestehen.

---

## Pull-Request-Prozess

1. **Branch** von `main` mit einem beschreibenden Namen:
   - `feat/bakom-5g-indoor-coverage`
   - `fix/rtv-search-canton-filter`
   - `docs/update-readme-synergies`

2. **Commit-Messages** folgen [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add indoor 5G coverage tool`
   - `fix: handle empty RTV search results`
   - `docs: add synergies section to README`
   - `test: add live test for broadband atlas`

3. **CHANGELOG.md aktualisieren** – füge deine Änderung unter `[Unreleased]` hinzu.

4. **Pull Request eröffnen** und das Template ausfüllen:
   - Was ändert dieser PR?
   - Welchen BAKOM-Endpunkt / welche Datenquelle nutzt er?
   - Wurden Live-API-Tests ausgeführt?

5. PRs werden vom Maintainer (`malkreide`) geprüft. Mit Feedback ist innerhalb weniger Tage zu rechnen.

---

## Datenquellen & APIs

Alle Tools in `bakom-mcp` müssen **öffentlich zugängliche, authentifizierungsfreie** Endpunkte nutzen:

| Quelle | Basis-URL | Lizenz |
|--------|-----------|--------|
| geo.admin.ch (Breitbandatlas, Mobilfunkabdeckung, Antennen) | `https://api3.geo.admin.ch` | OGD (CC0) |
| opendata.swiss (BAKOM-Datensätze, Telekommunikationsstatistik) | `https://opendata.swiss/api/3/action/` | OGD (CC0) |
| RTV-Datenbank (konzessionierte Veranstalter) | `https://rtvdb.ofcomnet.ch` | OGD |

Wenn du ein Tool hinzufügen möchtest, das Authentifizierung erfordert, eröffne bitte zuerst ein Feature-Request-Issue, um den Ansatz zu besprechen (z.B. das Graceful-Degradation-Muster aus `swiss-transport-mcp`).

---

## Verwandte Projekte

- [swiss-transport-mcp](https://github.com/malkreide/swiss-transport-mcp) – Schweizer öffentlicher Verkehr
- [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) – Zürcher Stadtdaten (Open Data)
- [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

---

*Fragen? Eröffne ein Issue oder starte eine Diskussion auf GitHub.*
