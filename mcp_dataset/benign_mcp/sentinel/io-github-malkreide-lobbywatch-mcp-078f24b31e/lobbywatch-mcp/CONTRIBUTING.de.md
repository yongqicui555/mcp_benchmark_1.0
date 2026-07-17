# Mitwirken bei lobbywatch-mcp

[🇬🇧 English version](CONTRIBUTING.md)

Danke für das Interesse an `lobbywatch-mcp`. Das Projekt ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide). Beiträge jeder Grössenordnung — Bug-Reports, Dokumentation, neue Tools, Performance — sind willkommen.

## Entwicklungs-Setup

```bash
git clone https://github.com/malkreide/lobbywatch-mcp.git
cd lobbywatch-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Tests ausführen

Nur offline (schnell, entspricht CI):

```bash
pytest -m "not live"
```

Inklusive Live-Probes gegen API und Dump:

```bash
pytest -m live
```

## Linting

```bash
ruff check .
ruff format .
```

## Design-Prinzipien

1. **No-Auth-First.** Alle Phase-1-Tools müssen ohne Credentials funktionieren.
2. **Live-Validierung vor dem Coden.** Wer ein Tool gegen einen Upstream-Endpoint baut, probiert den Endpoint zuerst live aus und dokumentiert die Erkenntnisse im PR.
3. **Namensnennung ist nicht verhandelbar.** Jede Antwort läuft durch ein Pydantic-Envelope mit der CC-BY-SA-4.0-Attribution. Nicht umgehen.
4. **Portfolio-Synergie.** Wenn ein Feature besser in einen anderen Server passt (`parlament-mcp`, `register-mcp`, …), besser dort einbringen als diesen Server aufblähen.

## Pull Requests

Conventional Commits verwenden (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) und `CHANGELOG.md` unter `[Unreleased]` nachführen.
