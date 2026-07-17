# Mitwirken an parlament-mcp

[🇬🇧 English Version](CONTRIBUTING.md)

Vielen Dank für Ihr Interesse an einem Beitrag! Dieser Server ist Teil des
[Swiss Public Data MCP Portfolio](https://github.com/malkreide).

## Erste Schritte

```bash
git clone https://github.com/malkreide/parlament-mcp
cd parlament-mcp
pip install -e ".[dev]"
```

## Tests ausführen

```bash
# Unit- + gemockte Integrationstests (ohne Netzwerk)
pytest tests/ -m "not live" -v

# Live-API-Tests (Internet erforderlich)
pytest tests/ -m live -v
```

## Code-Stil

```bash
python -m ruff check src/ tests/
python -m ruff format src/ tests/
```

## Ein neues Tool hinzufügen

1. Definieren Sie ein Pydantic-v2-`BaseModel` für die Eingaben in `server.py`
2. Implementieren Sie das Tool mit `@mcp.tool(name=..., annotations={...})`
3. Geben Sie immer `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` an
4. Ergänzen Sie Unit-Tests (gemockt) und einen `@pytest.mark.live`-Integrationstest
5. Dokumentieren Sie das neue Tool in `README.md` **und** `README.de.md`

## Portfolio-Konventionen

- **No-Auth-First**: Phase-1-Tools müssen ohne API-Schlüssel funktionieren
- **Sprachfilter**: Immer `Language eq 'DE'` als Default-OData-Filter setzen
- **Fehlerbehandlung**: Menschenlesbare deutsche Fehlertexte zurückgeben, niemals Exceptions an den Host werfen
- **Pagination**: Alle List-Tools müssen `limit` und `offset` unterstützen
- **Antwortformate**: Sowohl `markdown` (Default) als auch `json` unterstützen

## Probleme melden

Bitte eröffnen Sie ein GitHub-Issue mit:
- Dem verwendeten Tool-Namen und den Parametern
- Der tatsächlichen vs. erwarteten Ausgabe
- Dem relevanten API-Endpoint (falls bekannt)
