# Contributing to hn-tech-signal-mcp

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing! This server is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Getting Started

```bash
git clone https://github.com/malkreide/hn-tech-signal-mcp
cd hn-tech-signal-mcp
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit tests (no network required)
PYTHONPATH=src pytest tests/ -m "not live"

# Live integration tests (requires network)
PYTHONPATH=src pytest tests/ -m "live"
```

## Code Style

- Python 3.11+, FastMCP, Pydantic v2
- Ruff for linting: `ruff check src/`
- All tools require Pydantic `BaseModel` input validation
- All tools must have comprehensive docstrings

## Adding a New Tool

1. Add a Pydantic input model
2. Implement the tool with `@mcp.tool(name=..., annotations={...})`
3. Add unit tests (mocked HTTP with `respx`) and at least one `@pytest.mark.live` test
4. Update `README.md`, `README.de.md`, and `CHANGELOG.md`

## Pull Requests

- One feature per PR
- All unit tests must pass
- Follow existing code conventions
