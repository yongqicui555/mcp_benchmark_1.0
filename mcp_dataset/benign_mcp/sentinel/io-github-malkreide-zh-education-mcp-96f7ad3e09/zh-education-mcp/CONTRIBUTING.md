# Contributing to zh-education-mcp

🇩🇪 [Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/malkreide/zh-education-mcp.git
cd zh-education-mcp
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit tests (mocked, no network)
pytest tests/ -m "not live"

# All tests including live API calls
pytest tests/
```

## Code Style

```bash
python -m ruff check src/
python -m ruff format src/
```

## Data Sources

This server uses the BISTA public API (`bista.zh.ch/basicapi/ogd/`) — no authentication required.

**No-Auth-First principle**: Phase 1 tools must work without any API key.

## Adding New Tools

1. Validate the API endpoint with `curl` first
2. Add a Pydantic v2 input model
3. Add the tool with `@mcp.tool` decorator and full docstring
4. Add mocked unit tests using `respx`
5. Mark live tests with `@pytest.mark.live`
6. Update CHANGELOG.md

## Submitting Changes

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Commit: `git commit -m "feat: add xyz tool"`
4. Push and open a Pull Request
