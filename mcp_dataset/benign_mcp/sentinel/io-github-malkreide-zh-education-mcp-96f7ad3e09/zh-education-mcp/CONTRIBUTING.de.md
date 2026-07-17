# Mitwirken bei zh-education-mcp

Vielen Dank für dein Interesse an einem Beitrag!

🇬🇧 [English version](CONTRIBUTING.md)

## Entwicklungs-Setup

```bash
git clone https://github.com/malkreide/zh-education-mcp.git
cd zh-education-mcp
pip install -e ".[dev]"
```

## Tests ausführen

```bash
# Unit-Tests (gemockt, kein Netzwerk)
pytest tests/ -m "not live"

# Alle Tests inkl. Live-API-Aufrufe
pytest tests/
```

## Code-Stil

```bash
python -m ruff check src/
python -m ruff format src/
```

## Datenquellen

Dieser Server nutzt die öffentliche BISTA-API (`bista.zh.ch/basicapi/ogd/`) — keine Authentifizierung nötig.

**No-Auth-First-Prinzip**: Phase-1-Tools müssen ohne API-Schlüssel funktionieren.

## Neue Tools hinzufügen

1. API-Endpunkt zuerst mit `curl` validieren
2. Pydantic-v2-Input-Modell hinzufügen
3. Tool mit `@mcp.tool`-Decorator und vollständigem Docstring ergänzen
4. Gemockte Unit-Tests mit `respx` schreiben
5. Live-Tests mit `@pytest.mark.live` markieren
6. CHANGELOG.md aktualisieren

## Änderungen einreichen

1. Repo forken
2. Branch erstellen: `git checkout -b feat/dein-feature`
3. Commit: `git commit -m "feat: add xyz tool"`
4. Pushen und einen Pull Request öffnen
