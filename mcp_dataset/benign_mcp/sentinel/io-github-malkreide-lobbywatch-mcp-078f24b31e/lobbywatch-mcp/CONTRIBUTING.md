# Contributing to lobbywatch-mcp

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thanks for your interest in improving `lobbywatch-mcp`. This project is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide). Contributions of any size — bug reports, documentation fixes, new tools, performance work — are welcome.

## Development setup

```bash
git clone https://github.com/malkreide/lobbywatch-mcp.git
cd lobbywatch-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

Offline only (fast, what CI runs):

```bash
pytest -m "not live"
```

Including live API + dump probes:

```bash
pytest -m live
```

## Linting

```bash
ruff check .
ruff format .
```

## Design principles

1. **No-Auth-First.** All Phase 1 tools must work without credentials.
2. **Live validation before coding.** If you add a tool that hits an upstream endpoint, verify the endpoint with a live probe first and document what you found in the PR.
3. **Attribution is non-negotiable.** Every response goes through a Pydantic envelope that carries the CC BY-SA 4.0 credit. Don't route around it.
4. **Portfolio synergy.** If a feature fits better in another server (`parlament-mcp`, `register-mcp`, …), suggest that instead of growing this one.

## Pull requests

Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) and update `CHANGELOG.md` under `[Unreleased]`.
