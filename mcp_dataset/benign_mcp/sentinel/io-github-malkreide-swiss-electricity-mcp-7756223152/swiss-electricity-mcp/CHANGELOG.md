# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-03

Audit-remediation release. Closes all critical/high findings from the
`mcp-audit-skill` audit; the re-audit reports **production-ready**
(36 pass · 0 fail · 2 partial · 6 todo, catalog hash `091f446b`,
run-id `2026-06-03T191138-Z-swiss-electricity-mcp`).

### Changed

- **ARCH-004**: Configuration is centralised in a Pydantic-Settings object
  (`config.py`); the shared HTTP clients moved from module-level globals into the
  lifespan context and are accessed by tools via `ctx.request_context.lifespan_context`.

### Documentation

- **OPS-002**: ASCII architecture diagram in the README.
- **OPS-003**: Phase-1 declaration + `docs/roadmap.md` with phase-transition
  criteria.
- **ARCH-008**: README rationale for exposing Tools only (no Resources/Prompts).
- **SEC-019 / SEC-013 / SEC-008**: `docs/security-posture.md` — lethal-trifecta
  assessment, secret-management stance (none required), supply-chain trust.

### Changed

- **ARCH-007**: `tariff_compare_municipalities` fetches municipalities
  concurrently (`asyncio.gather`) instead of sequentially.
- **ARCH-003**: search tools return `match_type` (`results`/`none`) and an
  actionable `suggestion` on zero hits instead of a silent empty list.

### Observability

- **OBS-003 / OBS-004**: Structured JSON logging via `structlog`, written to
  **stderr** so the stdio JSON-RPC channel stays clean. Level via
  `SWISS_ELECTRICITY_LOG_LEVEL`.
- **OBS-006**: Opt-in OpenTelemetry tracing — per-tool spans plus httpx
  auto-instrumentation, enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` is set and
  the `otel` extra is installed. No-op otherwise.
- **OBS-002**: Upstream errors and status-probe failures are logged with full
  detail server-side but return a generic message to the client (no leaked
  stacktrace / internal repr).
- **OBS-001**: Added execution- and protocol-error-path tests.

### SDK

- **SDK-003**: SPARQL-backed tools accept `ctx: Context`; `tariff_compare_*`
  reports per-municipality progress, others emit `ctx.info` start events.
- **SDK-004**: Streamable-HTTP transport now runs behind CORS middleware that
  exposes/allows `Mcp-Session-Id`; origins via `SWISS_ELECTRICITY_CORS_ORIGINS`
  (never a wildcard).

### Security

- **SEC-016**: HTTP host now defaults to `127.0.0.1` instead of `0.0.0.0`.
  Bind to all interfaces explicitly via `SWISS_ELECTRICITY_HOST=0.0.0.0` inside
  a container only (prevents NeighborJack exposure on developer machines).
- **SEC-007**: Added a multi-stage `Dockerfile` that runs as a non-root user
  (UID 10001) with a `HEALTHCHECK`.
- **SEC-018**: The `category` argument is validated against the closed ElCom
  category enumeration and the `canton` argument is SPARQL-escaped before
  interpolation, closing a SPARQL-injection vector. String arguments now carry
  `min_length`/`max_length` bounds.
- **SEC-021 / SEC-004 / SEC-005**: All outbound requests pass through
  `assert_url_allowed()` — an HTTPS-only, host-allow-listed egress gate
  (`frozenset`). Documented in `docs/network-egress.md`.
- **SEC-022**: Tool definitions are pinned in `tool-definitions.lock.json`; a
  test fails if the tool surface drifts without regenerating the lock.

### Added

- **ARCH-011 / OPS-001**: CI workflows — `test.yml` (ruff + `pytest -m "not live"`
  on Python 3.11–3.13) and `publish.yml` (PyPI OIDC Trusted Publisher on release).
- **ARCH-005**: `secret-scan.yml` runs Gitleaks on every push and PR.
- **ARCH-012**: Dependabot (`pip` + `github-actions`, weekly) and a
  "MCP protocol version" section + update policy in the README.

### Changed

- **OPS-001**: Tests split into `tests/test_unit.py` (mocked, CI) and
  `tests/test_live.py` (live, excluded from CI).
- **ARCH-012**: `mcp[cli]` pinned to `>=1.2.0,<2.0.0`.

### Changed

- **ARCH-009**: All 12 tools now declare explicit MCP annotations
  (`readOnlyHint=true`; `openWorldHint=true` for upstream-reaching tools,
  `false` for the static category list).
- **SDK-001**: Shared HTTP clients are now closed cleanly on shutdown via a
  FastMCP `lifespan` context manager.

## [0.1.0] - 2026-05-21

### Added

- Initial release with 12 tools across four groups.
- **Group 1 — Energiedashboard.ch (BFE)**: `dashboard_get_production_mix`,
  `dashboard_get_consumption_forecast`, `dashboard_get_storage_lakes`,
  `dashboard_get_consumer_price_index`.
- **Group 2 — ElCom tariffs (via LINDAS SPARQL)**: `tariff_list_categories`,
  `tariff_get_by_municipality`, `tariff_get_median_swiss`,
  `tariff_get_median_canton`, `tariff_compare_municipalities`.
- **Group 3 — CKAN discovery**: `consumption_search_bfe_datasets`,
  `consumption_search_zurich`.
- **Group 4 — Status**: `electricity_check_status` for liveness probing.
- Dual transport: stdio (default) and Streamable HTTP for cloud deployment.
- Pydantic v2 response envelope with `source` + `provenance` + `retrieved_at`
  on every tool response (no auth required for any endpoint).
- Retry with exponential backoff (3 retries, 2s/4s/8s, 5xx + 429 retried).
- In-memory TTL cache (Dashboard 600s, SPARQL/CKAN 3600s).
- 19 unit tests with respx-mocked happy/retry/timeout/envelope contracts.
- 3 live tests (excluded from CI by default, run with `pytest -m live`).
- GitHub Actions CI matrix for Python 3.11/3.12/3.13.
- OIDC Trusted Publisher workflow for PyPI release-tag publishing.

### Architecture

- **Pattern**: Hybrid (live API + SPARQL + CKAN discovery), no authentication.
- **Endpoints validated live** on 2026-05-21 via the `mcp-data-source-probe` skill.

[0.1.0]: https://github.com/malkreide/swiss-electricity-mcp/releases/tag/v0.1.0
