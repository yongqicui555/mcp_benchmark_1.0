# Mitwirken an hn-tech-signal-mcp

[🇬🇧 English Version](CONTRIBUTING.md)

Vielen Dank für dein Interesse! Dieser Server ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Loslegen

```bash
git clone https://github.com/malkreide/hn-tech-signal-mcp
cd hn-tech-signal-mcp
pip install -e ".[dev]"
```

## Tests ausführen

```bash
# Unit-Tests (kein Netzwerkzugriff nötig)
PYTHONPATH=src pytest tests/ -m "not live"

# Live-Integrationstests (Netzwerkzugriff nötig)
PYTHONPATH=src pytest tests/ -m "live"
```

## Code-Stil

- Python 3.11+, FastMCP, Pydantic v2
- Ruff für Linting: `ruff check src/`
- Alle Tools benötigen Pydantic `BaseModel`-Eingabevalidierung
- Alle Tools brauchen vollständige Docstrings

## Neues Tool hinzufügen

1. Pydantic-Eingabemodell definieren
2. Tool mit `@mcp.tool(name=..., annotations={...})` implementieren
3. Unit-Tests (gemocktes HTTP mit `respx`) und mind. einen `@pytest.mark.live`-Test schreiben
4. `README.md`, `README.de.md` und `CHANGELOG.md` aktualisieren

## Pull Requests

- Eine Funktion pro PR
- Alle Unit-Tests müssen bestehen
- Bestehende Code-Konventionen einhalten
