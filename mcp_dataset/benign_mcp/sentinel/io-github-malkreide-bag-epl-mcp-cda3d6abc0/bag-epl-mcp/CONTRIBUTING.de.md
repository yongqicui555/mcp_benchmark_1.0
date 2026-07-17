# Mitwirken an bag-epl-mcp

[:gb: English Version](CONTRIBUTING.md)

Vielen Dank für Ihr Interesse an einem Beitrag! Dieser Server ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Fehler melden

Verwenden Sie [GitHub Issues](https://github.com/malkreide/bag-epl-mcp/issues), um Fehler zu melden oder Funktionen vorzuschlagen.

Bitte geben Sie an:
- Python-Version und Betriebssystem
- Vollständige Fehlermeldung oder Beschreibung des unerwarteten Verhaltens
- Schritte zur Reproduktion

---

## Pull Requests

1. Repository forken
2. Feature-Branch erstellen: `git checkout -b feat/ihr-feature`
3. Änderungen vornehmen und Tests ergänzen
4. Sicherstellen, dass alle Tests bestehen: `PYTHONPATH=src pytest tests/ -m "not live"`
5. Commit nach [Conventional Commits](https://www.conventionalcommits.org/): `feat: add new tool`
6. Pushen und einen Pull Request gegen `main` eröffnen

---

## Code-Stil

- Python 3.11+
- [Ruff](https://github.com/astral-sh/ruff) für Linting und Formatierung
- Type Hints für alle öffentlichen Funktionen erforderlich
- Tests für neue Tools erforderlich (`tests/test_server.py`)
- Den bestehenden FastMCP-/Pydantic-v2-Mustern in `server.py` folgen

---

## Datenquellen

Dieser Server greift auf Daten des BAG (Bundesamt für Gesundheit) zu — alle ohne Authentifizierung:

| Quelle | Dokumentation |
|--------|--------------|
| Spezialitätenliste (SL) | [sl.bag.admin.ch](https://sl.bag.admin.ch) |
| GGSL | [BAG GGSL Info](https://www.bag.admin.ch) |
| MiGeL | [BAG MiGeL Info](https://www.bag.admin.ch) |

### Phase 2: FHIR-API

Sobald das BAG seine FHIR/IDMP-API für die ePL veröffentlicht, sind Beiträge zur Umstellung der Tools sehr willkommen. Die Architektur ist so ausgelegt, dass dieses Upgrade minimal ausfällt — siehe die Konstante `FHIR_BASE_URL` und die Funktion `_sl_website_suche` in `server.py`.

Beim Hinzufügen neuer Datenquellen gilt das **No-Auth-First-Prinzip**: Phase 1 nutzt ausschliesslich offene, authentifizierungsfreie Endpunkte. Authentifizierte APIs werden in späteren Phasen mit Graceful Degradation eingeführt.

---

## Lizenz

Mit Ihrem Beitrag erklären Sie sich damit einverstanden, dass Ihre Beiträge unter der [MIT-Lizenz](LICENSE) lizenziert werden.
