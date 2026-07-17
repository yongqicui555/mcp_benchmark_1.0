# Contributing to parlament-mcp

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing! This server is part of the
[Swiss Public Data MCP Portfolio](https://github.com/malkreide).

## Getting Started

```bash
git clone https://github.com/malkreide/parlament-mcp
cd parlament-mcp
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit + mocked integration tests (no network)
pytest tests/ -m "not live" -v

# Live API tests (requires internet)
pytest tests/ -m live -v
```

## Code Style

```bash
python -m ruff check src/ tests/
python -m ruff format src/ tests/
```

## Adding a New Tool

1. Define a Pydantic v2 `BaseModel` for inputs in `server.py`
2. Implement the tool with `@mcp.tool(name=..., annotations={...})`
3. Always include `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`
4. Add unit tests (mocked) and a `@pytest.mark.live` integration test
5. Document the new tool in both `README.md` and `README.de.md`

## Portfolio Conventions

- **No-Auth-First**: Phase 1 tools must work without any API key
- **Language filter**: Always include `Language eq 'DE'` as default OData filter
- **Error handling**: Return human-readable German error strings, never raise exceptions to the host
- **Pagination**: All list tools must support `limit` and `offset` parameters
- **Response formats**: Support both `markdown` (default) and `json`

## Reporting Issues

Please open a GitHub issue with:
- The tool name and parameters used
- The actual vs. expected output
- The relevant API endpoint (if known)
