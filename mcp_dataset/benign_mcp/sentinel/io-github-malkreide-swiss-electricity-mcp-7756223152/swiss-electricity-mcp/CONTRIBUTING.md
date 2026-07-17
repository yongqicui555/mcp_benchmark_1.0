# 🤝 Contributing to swiss-electricity-mcp

🌍 **Read this in your language:** [🇩🇪 Deutsch](CONTRIBUTING.de.md)

Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide/swiss-public-data-mcp).
This portfolio follows shared conventions so that all servers compose cleanly into
multi-source AI agent workflows.

## Portfolio conventions

- **No-Auth-First**: Phase 1 servers use only unauthenticated public endpoints.
- **Live-probe before code**: every new endpoint is validated against the real
  upstream before being added to the client.
- **Envelope discipline**: every Pydantic response inherits from `ResponseEnvelope`
  with `source` + `provenance` + `retrieved_at` — accidental omission is impossible.
- **Retry-with-backoff**: 3 retries, 2/4/8 seconds, 5xx + 429 retried.
- **Dual transport**: stdio for Claude Desktop, Streamable HTTP for cloud.
- **Bilingual docs**: English `README.md` primary, German `README.de.md` mirror
  in Swiss spelling (no eszett).
- **CI**: ruff + pytest (excluding `@pytest.mark.live`) on push.
- **Release**: tagged release on GitHub triggers PyPI publish via OIDC.

## Setup

```bash
git clone https://github.com/malkreide/swiss-electricity-mcp.git
cd swiss-electricity-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Test

```bash
# Unit tests (mocked, fast)
PYTHONPATH=src pytest tests/ -m "not live" -v

# Live tests (hits real upstreams — only when needed)
PYTHONPATH=src pytest tests/ -m live -v
```

## Lint

```bash
ruff check src tests
```

## Adding a tool

1. Live-probe the endpoint (`curl`, check response shape, status, latency).
2. Add a Pydantic response model in `models.py` (inherit `ResponseEnvelope`).
3. Add the client method in `api_client.py` (use `_fetch_with_retry`).
4. Register the `@mcp.tool` in `server.py` with German docstring + English
   tool description.
5. Add a mocked happy-path test and at least one live test in
   `tests/test_server.py`.
6. Update `CHANGELOG.md`.

## Releasing

1. Bump `version` in `pyproject.toml` and `__init__.py`.
2. Update `CHANGELOG.md` with a new section.
3. Commit, push, create a GitHub Release with tag `v0.X.Y`.
4. GitHub Actions publishes to PyPI automatically.

## Code style

- Use Swiss German spelling conventions in user-facing strings (no eszett).
- Field descriptions in models: German first (since it's the source language
  of most datasets), English in tool descriptions for LLM clarity.
