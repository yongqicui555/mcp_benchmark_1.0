# Contributing to bag-epl-mcp

[:de: Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing! This server is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Reporting Issues

Use [GitHub Issues](https://github.com/malkreide/bag-epl-mcp/issues) to report bugs or request features.

Please include:
- Python version and OS
- Full error message or description of unexpected behaviour
- Steps to reproduce

---

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `PYTHONPATH=src pytest tests/ -m "not live"`
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add new tool`
6. Push and open a Pull Request against `main`

---

## Code Style

- Python 3.11+
- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Type hints required for all public functions
- Tests required for new tools (`tests/test_server.py`)
- Follow the existing FastMCP / Pydantic v2 patterns in `server.py`

---

## Data Sources

This server accesses Swiss BAG (Federal Office of Public Health) data — all without authentication:

| Source | Documentation |
|--------|--------------|
| Spezialitaetenliste (SL) | [sl.bag.admin.ch](https://sl.bag.admin.ch) |
| GGSL | [BAG GGSL Info](https://www.bag.admin.ch) |
| MiGeL | [BAG MiGeL Info](https://www.bag.admin.ch) |

### Phase 2: FHIR API

When the BAG publishes its FHIR/IDMP API for the ePL, contributions updating the tools to use it are very welcome. The architecture is designed to make this upgrade minimal — see the `FHIR_BASE_URL` constant and the `_sl_website_suche` function in `server.py`.

When adding new data sources, follow the **No-Auth-First** principle: Phase 1 uses only open, authentication-free endpoints. Authenticated APIs are introduced in later phases with graceful degradation.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
