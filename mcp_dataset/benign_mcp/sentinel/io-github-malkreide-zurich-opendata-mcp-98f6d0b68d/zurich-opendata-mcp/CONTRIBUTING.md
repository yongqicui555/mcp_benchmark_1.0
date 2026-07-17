# Contributing to zurich-opendata-mcp

🌐 **English** | **[Deutsch](CONTRIBUTING.de.md)**

Thank you for your interest in contributing! This server is part of the
[Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Reporting Issues

Use [GitHub Issues](https://github.com/malkreide/zurich-opendata-mcp/issues) to
report bugs or request features.

Please include:
- Python version and OS
- Full error message or description of unexpected behaviour
- Steps to reproduce

---

## Setting Up the Development Environment

```bash
git clone https://github.com/malkreide/zurich-opendata-mcp.git
cd zurich-opendata-mcp

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install with dev dependencies
pip install -e ".[dev]"
```

---

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest tests/ -m "not live"`
5. Ensure linting is clean: `ruff check src/ tests/`
6. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add new tool`
7. Push and open a Pull Request against `main`

Keep one PR per feature/bugfix, and update documentation in **both** English
and German (`README.md` / `README.de.md`).

---

## Adding a New Tool

1. **API client** (`src/zurich_opendata_mcp/clients/`): if connecting a new API,
   add the client module and any constants to `config.py`.
2. **Tool module** (`src/zurich_opendata_mcp/tools/`):
   - Define a Pydantic `BaseModel` for the inputs (`extra="forbid"`)
   - Implement an `@mcp.tool()` function with `readOnlyHint: True`
   - Return a Markdown-formatted response via the helpers in `formatters.py`
3. **Tests** (`tests/test_server.py`): add unit tests; use `respx` to mock the
   upstream API. Live integration tests are marked with `@pytest.mark.live`.
4. **README.md / README.de.md**: add the tool description and an example query
   in both languages.
5. **CHANGELOG.md**: add an entry under `[Unreleased]` (see `CLAUDE.md`).

---

## Code Style

- Python 3.11+
- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Type hints required for all public functions
- Tests required for new tools (`tests/test_server.py`)
- Follow the existing FastMCP / Pydantic v2 patterns in `src/zurich_opendata_mcp/`

---

## Data Sources

All APIs used are publicly accessible and require no authentication. Data is
published under CC0 or comparable open licenses.

| Source | Documentation |
|--------|--------------|
| CKAN | [data.stadt-zuerich.ch/api/3/](https://data.stadt-zuerich.ch/api/3/) |
| Geoportal WFS | [www.ogd.stadt-zuerich.ch/wfs/geoportal](https://www.ogd.stadt-zuerich.ch/wfs/geoportal) |
| Paris (City Parliament) | [www.gemeinderat-zuerich.ch/api](https://www.gemeinderat-zuerich.ch/api) |
| Zürich Tourism | [www.zuerich.com/en/api/v2/data](https://www.zuerich.com/en/api/v2/data) |
| SPARQL | [ld.stadt-zuerich.ch/query](https://ld.stadt-zuerich.ch/query) |
| ParkenDD | [api.parkendd.de/Zuerich](https://api.parkendd.de/Zuerich) |

---

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
