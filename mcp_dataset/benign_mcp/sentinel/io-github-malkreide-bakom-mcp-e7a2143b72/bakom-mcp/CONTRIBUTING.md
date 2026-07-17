# Contributing to bakom-mcp

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing to **bakom-mcp**! This server is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide) and connects AI assistants to Swiss Federal Office of Communications (BAKOM) open data.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Report Bugs](#how-to-report-bugs)
- [How to Suggest Features](#how-to-suggest-features)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Data Sources & APIs](#data-sources--apis)

---

## Code of Conduct

This project follows the standard open-source community norms: be respectful, constructive, and collaborative. Issues and pull requests that are abusive or off-topic will be closed.

---

## How to Report Bugs

1. **Check existing issues** first – your bug may already be reported.
2. Open a [new issue](https://github.com/malkreide/bakom-mcp/issues/new) and include:
   - A clear title and description
   - Steps to reproduce
   - Expected vs. actual behaviour
   - Python version (`python --version`)
   - Error output / stack trace (if applicable)
   - The tool name that is failing (e.g. `bakom_mobilfunk_abdeckung`)

> **Tip:** For issues related to upstream APIs (geo.admin.ch, opendata.swiss, rtvdb.ofcomnet.ch), please also note whether the API endpoint itself returns an error when accessed directly.

---

## How to Suggest Features

Open a [new issue](https://github.com/malkreide/bakom-mcp/issues/new) with the label `enhancement` and describe:

- The use case (who benefits, in what context?)
- The BAKOM data source you have in mind
- Whether the data is available without authentication (OGD/CC0 preferred)

Priority is given to tools that align with the **anchor use case**: broadband and mobile coverage analysis for public infrastructure (e.g. school buildings, municipal facilities).

---

## Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/bakom-mcp.git
cd bakom-mcp

# 2. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 3. Verify the setup
PYTHONPATH=src pytest tests/ -m "not live" -v
```

### Requirements

- Python 3.11+
- `uv` or `pip`
- Internet connection for live API tests

---

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Both in one step (CI equivalent)
ruff check src/ tests/ && ruff format --check src/ tests/
```

**Key conventions:**
- Follow the existing `src/` layout (`src/bakom_mcp/`)
- Type hints for all function signatures
- Docstrings for all public tool functions (used by MCP clients as tool descriptions)
- Tool names follow the pattern `bakom_<resource>_<action>` (snake_case)
- No API keys or credentials — all BAKOM tools must use open endpoints only

---

## Testing

Tests are split into unit/mock tests and live API tests:

```bash
# Unit tests (no network required — always run in CI)
PYTHONPATH=src pytest tests/ -m "not live" -v

# Live integration tests (require internet access)
PYTHONPATH=src pytest tests/ -m "live" -v
```

Mark live tests with `@pytest.mark.live`:

```python
import pytest

@pytest.mark.live
def test_broadband_coverage_live():
    # calls actual geo.admin.ch endpoint
    ...
```

**CI matrix:** Tests run on Python 3.11, 3.12, and 3.13 via GitHub Actions. All PRs must pass the non-live test suite.

---

## Pull Request Process

1. **Branch** from `main` with a descriptive name:
   - `feat/bakom-5g-indoor-coverage`
   - `fix/rtv-search-canton-filter`
   - `docs/update-readme-synergies`

2. **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add indoor 5G coverage tool`
   - `fix: handle empty RTV search results`
   - `docs: add synergies section to README`
   - `test: add live test for broadband atlas`

3. **Update CHANGELOG.md** – add your change under `[Unreleased]`.

4. **Open a Pull Request** and fill in the template:
   - What does this PR change?
   - Which BAKOM endpoint / data source does it use?
   - Were live API tests run?

5. PRs are reviewed by the maintainer (`malkreide`). Expect feedback within a few days.

---

## Data Sources & APIs

All tools in `bakom-mcp` must use **publicly accessible, authentication-free** endpoints:

| Source | Base URL | Licence |
|--------|----------|---------|
| geo.admin.ch (Broadband Atlas, mobile coverage, antennas) | `https://api3.geo.admin.ch` | OGD (CC0) |
| opendata.swiss (BAKOM datasets, telecom statistics) | `https://opendata.swiss/api/3/action/` | OGD (CC0) |
| RTV database (licensed broadcasters) | `https://rtvdb.ofcomnet.ch` | OGD |

If you want to add a tool that requires authentication, please open a feature request issue first to discuss the approach (e.g. graceful degradation pattern used in `swiss-transport-mcp`).

---

## Related Projects

- [swiss-transport-mcp](https://github.com/malkreide/swiss-transport-mcp) – Swiss public transport
- [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) – Zurich city open data
- [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

---

*Questions? Open an issue or start a discussion on GitHub.*
