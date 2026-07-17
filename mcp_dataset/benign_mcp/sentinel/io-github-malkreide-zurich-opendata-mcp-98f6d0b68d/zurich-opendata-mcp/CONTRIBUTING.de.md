# Mitwirken an zurich-opendata-mcp

🌐 **[English](CONTRIBUTING.md)** | **Deutsch**

Vielen Dank für Ihr Interesse an einem Beitrag! Dieser Server ist Teil des
[Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Probleme melden

Nutzen Sie die [GitHub Issues](https://github.com/malkreide/zurich-opendata-mcp/issues),
um Fehler zu melden oder Features vorzuschlagen.

Bitte geben Sie an:
- Python-Version und Betriebssystem
- Vollständige Fehlermeldung oder Beschreibung des unerwarteten Verhaltens
- Schritte zur Reproduktion

---

## Entwicklungsumgebung einrichten

```bash
git clone https://github.com/malkreide/zurich-opendata-mcp.git
cd zurich-opendata-mcp

# Virtuelle Umgebung erstellen
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Mit Dev-Dependencies installieren
pip install -e ".[dev]"
```

---

## Pull Requests

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch: `git checkout -b feat/mein-feature`
3. Nehmen Sie Ihre Änderungen vor und fügen Sie Tests hinzu
4. Stellen Sie sicher, dass alle Tests bestehen: `pytest tests/ -m "not live"`
5. Stellen Sie sicher, dass das Linting sauber ist: `ruff check src/ tests/`
6. Committen Sie nach [Conventional Commits](https://www.conventionalcommits.org/): `feat: neues Tool hinzufügen`
7. Pushen Sie und eröffnen Sie einen Pull Request gegen `main`

Pro Feature/Bugfix ein PR, und aktualisieren Sie die Dokumentation **sowohl** auf
Englisch als auch auf Deutsch (`README.md` / `README.de.md`).

---

## Ein neues Tool hinzufügen

1. **API-Client** (`src/zurich_opendata_mcp/clients/`): Bei Anbindung einer neuen
   API das Client-Modul ergänzen und Konstanten in `config.py` hinterlegen.
2. **Tool-Modul** (`src/zurich_opendata_mcp/tools/`):
   - Ein Pydantic-`BaseModel` für die Eingaben definieren (`extra="forbid"`)
   - Eine `@mcp.tool()`-Funktion mit `readOnlyHint: True` implementieren
   - Eine Markdown-formatierte Antwort über die Helfer in `formatters.py` zurückgeben
3. **Tests** (`tests/test_server.py`): Unit-Tests hinzufügen; die Upstream-API mit
   `respx` mocken. Live-Integrationstests sind mit `@pytest.mark.live` markiert.
4. **README.md / README.de.md**: Tool-Beschreibung und eine Beispiel-Abfrage in
   beiden Sprachen ergänzen.
5. **CHANGELOG.md**: Einen Eintrag unter `[Unreleased]` hinzufügen (siehe `CLAUDE.md`).

---

## Code-Stil

- Python 3.11+
- [Ruff](https://github.com/astral-sh/ruff) für Linting und Formatierung
- Type-Hints für alle öffentlichen Funktionen erforderlich
- Tests für neue Tools erforderlich (`tests/test_server.py`)
- Den bestehenden FastMCP- / Pydantic-v2-Mustern in `src/zurich_opendata_mcp/` folgen

---

## Datenquellen

Alle genutzten APIs sind öffentlich zugänglich und erfordern keine
Authentifizierung. Die Daten stehen unter CC0 oder vergleichbaren offenen Lizenzen.

| Quelle | Dokumentation |
|--------|--------------|
| CKAN | [data.stadt-zuerich.ch/api/3/](https://data.stadt-zuerich.ch/api/3/) |
| Geoportal WFS | [www.ogd.stadt-zuerich.ch/wfs/geoportal](https://www.ogd.stadt-zuerich.ch/wfs/geoportal) |
| Paris (Gemeinderat) | [www.gemeinderat-zuerich.ch/api](https://www.gemeinderat-zuerich.ch/api) |
| Zürich Tourismus | [www.zuerich.com/en/api/v2/data](https://www.zuerich.com/en/api/v2/data) |
| SPARQL | [ld.stadt-zuerich.ch/query](https://ld.stadt-zuerich.ch/query) |
| ParkenDD | [api.parkendd.de/Zuerich](https://api.parkendd.de/Zuerich) |

---

## Lizenz

Mit Ihrem Beitrag erklären Sie sich damit einverstanden, dass Ihre Beiträge unter
der [MIT-Lizenz](LICENSE) lizenziert werden.
