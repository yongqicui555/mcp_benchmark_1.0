# Repository Guidelines

This repository hosts the Data Commons MCP server and tooling as a Python (uv) workspace. The primary package lives under `packages/un-datacommons-mcp`.

## Project Structure & Module Organization
- `packages/un-datacommons-mcp/datacommons_mcp/`: core code — `server.py` (FastAPI server), `cli.py` (entrypoint), `services.py`, `clients.py`, `topics.py`, `data_models/*`, `data/*`.
- `packages/un-datacommons-mcp/tests/`: pytest tests.
- `docs/`: user and internal docs; images in `docs/*.png`.
- `.github/workflows/`: CI, build, and publish workflows.
- Root `pyproject.toml`: uv workspace + shared tools; package-specific `pyproject.toml` in `packages/un-datacommons-mcp`.

## Build, Test, and Development Commands
- Install deps: `uv sync`
- Format: `uv run ruff format` (check only: `uv run ruff format --check`)
- Lint: `uv run ruff check`
- Tests (skip evals): `uv run --extra test pytest -k "not eval"`
- Run server (HTTP): `uvx un-datacommons-mcp serve http --port 8080`
- Run server (stdio): `uvx un-datacommons-mcp serve stdio`

## Coding Style & Naming Conventions
- Python 3.11–3.12, 4‑space indentation, one import per line (isort via Ruff).
- Prefer type hints for public APIs; follow `N*` and `ANN*` rules in `pyproject.toml`.
- Use double quotes; keep functions small and explicit (avoid broad `except` where practical).
- Module naming: `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`.
- Location: `packages/un-datacommons-mcp/tests/`; name tests `test_*.py`.
- Run unit tests locally: `uv run --extra test pytest -k "not eval"`.
- Add tests for new features/bugfixes; prefer fast, deterministic tests. Mark or separate any network-dependent tests.

## Commit & Pull Request Guidelines
- Commits: imperative, present tense (e.g., "Add settings validation"); group related changes. Reference issues (e.g., `#123`).
- Before pushing: run formatter, linter, and tests.
- Optional hook: `uv run pre-commit install --hook-type pre-push` then rely on configured `ruff` and `pytest` checks.
- PRs: clear description, rationale, linked issues, and test updates. CI must pass.

## Security & Configuration Tips
- Never commit secrets. Use `packages/un-datacommons-mcp/.env.sample` as a template: `cp packages/un-datacommons-mcp/.env.sample packages/un-datacommons-mcp/.env`.
- Set `DC_API_KEY` (required) and other `DC_*` variables as needed; environment variables override `.env`.
- For local HTTP serve, the MCP endpoint is `http://localhost:<port>/mcp`.
