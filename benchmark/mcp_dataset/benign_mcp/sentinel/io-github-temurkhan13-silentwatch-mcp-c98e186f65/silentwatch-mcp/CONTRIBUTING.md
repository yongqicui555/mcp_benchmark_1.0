# Contributing to silentwatch-mcp

Thanks for considering a contribution. This is a small project intentionally —
the goal is to keep the core small enough that adding a new scheduler backend
is a single-PR affair.

## What contributions are most useful

- **New backend adapters** — if you run a scheduler that isn't covered (Cowork
  scheduler, Hangfire, AWS EventBridge, GCP Cloud Scheduler, Apache Airflow,
  etc.), a backend that conforms to the `CronBackend` ABC is the highest-value
  contribution. See `src/silentwatch_mcp/backends/` for examples.
- **Silent-fail detection rules** — if you've debugged a production silent
  failure that the existing rules wouldn't have caught, a new rule (and the
  test that exercises it) is welcome.
- **Real-world test fixtures** — a sanitized JSONL or systemctl output sample
  that we can use for regression testing.
- **Bug reports** with reproducible inputs (a JSONL file or systemctl output
  that produces unexpected behavior).

## What's out of scope

- **Metrics push to Prometheus / InfluxDB / time-series stores** — `silentwatch`
  is read-only on cron state; metrics integration is intentionally a separate
  project.
- **Alert routing logic** (PagerDuty / Slack / email rules) — this MCP exposes
  data; alert delivery is the client's job.
- **Web UI dashboard** — MCP is the surface; if you want a dashboard, build it
  on top.
- **Generic time-series storage** — see above.

For features that fall outside scope but you want for your stack, that's a
[Custom MCP Build](./README.md#need-this-adapted-to-your-stack) engagement.

## Development setup

```bash
git clone https://github.com/temurkhan/silentwatch-mcp.git
cd silentwatch-mcp
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/                # all tests
pytest tests/test_backend_crontab.py -v   # one suite
pytest -k silent_fail        # tests matching pattern
```

Target coverage at v1.0: ≥85% line coverage on `src/`.

## Adding a new backend

1. **Create** `src/silentwatch_mcp/backends/<your_backend>.py`
2. **Subclass** `CronBackend` (from `backends.base`)
3. **Implement** three methods:
   - `async def list_jobs(self) -> list[CronJob]`
   - `async def get_job_runs(self, job_id: str, limit: int) -> list[CronRun]`
   - `async def tail_logs(self, job_id: str, lines: int) -> list[str]`
4. **Register** in `src/silentwatch_mcp/backends/__init__.py` `BACKEND_REGISTRY`
5. **Add tests** in `tests/test_backend_<your_backend>.py` — use `unittest.mock.patch`
   on `subprocess.run` so tests are platform-agnostic
6. **Document** the backend's environment variables in README.md § Backends and
   in SPEC.md § Backend selection

The existing `crontab.py` and `systemd.py` backends are good templates.

## Style

- **Formatter:** ruff (config in `pyproject.toml`)
- **Type checker:** mypy strict mode
- **Test framework:** pytest with `pytest-asyncio` (asyncio_mode = "auto")
- **Naming:** snake_case for functions/modules, PascalCase for classes
- **Docstrings:** brief module + class docstrings; function docstrings only when
  the name + signature don't make the behavior obvious

Run before committing:
```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/silentwatch_mcp
pytest tests/ -v
```

## Pull requests

- One concept per PR. If you want to add three backends, that's three PRs.
- Tests required for new code; bug fixes need a regression test.
- Update CHANGELOG.md under `[Unreleased]` with one bullet describing the change.
- Update README and/or SPEC.md if you change user-facing behavior.

## Issues

Bug reports are most useful with:
- Backend in use (`SILENTWATCH_BACKEND` value)
- Python version + OS
- A minimal example that reproduces the issue (a JSONL line, a systemctl JSON
  blob, etc.)
- What you expected vs what you got

Feature requests are most useful with:
- The scheduler / use case it addresses
- A sketch of the API change you'd want
- Whether you'd be willing to implement it (helpful for prioritization)

## Code of conduct

Be helpful and direct. No drive-by lectures, no gatekeeping. PRs are evaluated
on technical merit; identity of the contributor doesn't enter into it.

## License

By contributing, you agree your contributions are licensed under the MIT License
that covers the project (see [LICENSE](./LICENSE)).
