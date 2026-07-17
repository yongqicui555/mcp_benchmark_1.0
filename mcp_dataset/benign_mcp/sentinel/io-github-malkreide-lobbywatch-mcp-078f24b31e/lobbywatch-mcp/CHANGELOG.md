# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `SECURITY.md` / `SECURITY.de.md` — security posture, Lethal Trifecta
  assessment, accepted-risk decisions (SEC-014, SEC-015) and vulnerability
  reporting process, aligned with the portfolio standard.
- `CONTRIBUTING.de.md` — German contributing guide, linked from the English
  `CONTRIBUTING.md`.

### Changed
- Repo docs now follow the portfolio convention of English-primary `.md`
  files with linked German `.de.md` counterparts: `CONTRIBUTING.md` is now
  English-only and links to `CONTRIBUTING.de.md` (previously a single combined
  bilingual file). READMEs gained a Security section.
- `LICENSE` copyright holder updated to "Hayal Oezkan".

## [0.3.1] - 2026-05-10

Documentation + release-pipeline catch-up. No functional code changes
since 0.3.0 — same 41 / 0 / 1 / 2 audit posture, same `production_ready: true`.

### Added
- `.github/workflows/publish.yml` — tag-triggered PyPI release via
  Trusted Publisher (OIDC, no API token in repo secrets). Verifies that
  the pushed tag matches `pyproject.toml`'s `version` before publishing.
  One-time setup on PyPI: register `malkreide/lobbywatch-mcp` ·
  `publish.yml` · environment `pypi` as a pending publisher. Closes the
  README/CHANGELOG-0.1.0 promise that was never actually committed.
- ASCII architecture diagram in README.md / README.de.md (audit OPS-002
  closure — the last cosmetic finding from the 2026-05-09 re-audit).
  Visualises the dump-first / dataIF-fallback split plus the SSRF-guarded
  outbound HTTP path. With this, **all 25 originally-applicable findings
  from the initial audit are closed**.

### Changed
- `USER_AGENT` bumped to `lobbywatch-mcp/0.3.1`.

## [0.3.0] - 2026-05-09

Audit-driven hardening release. Closes 24 of 25 findings from the
initial mcp-audit-skill v1.0.0 run; the re-audit
(`audits/2026-05-09T133506-Z-lobbywatch-mcp/`) reports
`production_ready: true` (41 pass, 0 fail, 1 cosmetic partial).

### Added
- Structured JSON logging via structlog (audit OBS-003). Opt-in with
  `LOBBYWATCH_MCP_LOG_FORMAT=json` — default stays `text` to preserve
  the quiet stdio experience. Each tool invocation generates a
  16-char correlation id that's bound into the structlog context vars
  and surfaces in every JSON line as `correlation_id`.
- OpenTelemetry distributed tracing (audit OBS-006). Opt-in with
  `LOBBYWATCH_MCP_OTEL_ENABLED=1`; OTel is an optional dep installed
  via `pip install 'lobbywatch-mcp[obs]'`. Wraps each tool call in a
  `tool.<name>` span and auto-instruments the httpx client. The
  `_observability.observed_tool` async context manager keeps OBS-003
  + OBS-006 in sync — every tool body is wrapped exactly once.
- Lifespan startup now logs the active MCP `protocolVersion` (audit
  ARCH-012 closure: SDK upper-bound was already pinned in 0.2.0; this
  closes the remaining "log it for operators" gap).
- New optional dependency group `obs` covering
  `opentelemetry-api`, `opentelemetry-sdk`,
  `opentelemetry-exporter-otlp-proto-http`,
  `opentelemetry-instrumentation-httpx`. Without it, tracing config
  warns and no-ops; logging stays available either way.
- Multi-stage `Dockerfile` and `.dockerignore` (audit SCALE-004). Runtime
  image runs as `uid 1000`, read-only-rootfs compatible, no build
  toolchain in the final stage (audit SEC-007).
- `deploy/docker-compose.example.yml` with hardening defaults:
  `read_only`, `cap_drop: [ALL]`, `no-new-privileges`, tmpfs cache,
  loopback-only port bind, healthcheck, and `deploy.resources` limits
  (256 MiB / 0.1 CPU request, 512 MiB / 0.5 CPU limit) — audit SCALE-006.
- `docs/deployment.md`: trust-model recap, container build/run commands,
  resource-sizing rationale, HAProxy stick-table example for sticky LBs
  (audit SCALE-002, SCALE-003), and a Kubernetes egress `NetworkPolicy`
  template (audit SEC-021).
- SSRF / DNS-rebinding guard in the httpx client: an event hook re-resolves
  every outbound host and refuses connections to RFC1918 / link-local /
  loopback / cloud-metadata addresses (audit SEC-005). Hardcoded URL
  allow-list + `follow_redirects=False` + this guard provide
  defence-in-depth.
- Optional CORS support for HTTP/SSE deployments via the
  `LOBBYWATCH_MCP_CORS_ORIGINS` env var (comma-separated origin list).
  When set, the FastMCP ASGI app is wrapped with a Starlette
  `CORSMiddleware` that exposes `Mcp-Session-Id` to browser clients
  (audit SDK-004). Default (empty) emits no CORS headers.
- `lobbywatch_refresh_dump` now accepts a `Context` parameter and emits
  `ctx.info` start/end notifications around the dump download (audit
  SDK-003), giving long-running clients useful progress feedback.
- Fuzzy-match suggestions on missed lookups (audit ARCH-003).
  `lobbywatch_get_parlamentarier` and `lobbywatch_list_interessenbindungen`
  return up to three near-miss candidates (rapidfuzz WRatio in
  [50, 70)) in a new `suggestions` field, so the LLM can offer
  "did you mean…?" instead of treating the empty result as truth. New
  `LobbywatchClient.find_candidates()` powers this.
- MCP Resources and Prompts (audit ARCH-008):
  - Resource `lobbywatch://attribution` (text/plain) — the CC BY-SA 4.0
    licence string for clients that want to display it standalone.
  - Prompt `lobbywatch_anchor_demo` — parameterised by `branche`, scaffolds
    the canonical Schulamt / KI-Fachgruppe demo query.
  - Prompt `lobbywatch_top_lobbyists_by_party` — parameterised by `partei`,
    surfaces the top-10 ranking with transparency metadata.

### Changed
- Tool-boundary error handling: upstream `RuntimeError` /
  `httpx.HTTPError` are explicitly converted to `McpError` with code
  `INTERNAL_ERROR` (audit OBS-001). Previously these fell through to
  FastMCP's auto-coercion — same wire effect, but the categorisation is
  now intentional and operators get a structured `logger.error` for the
  underlying exception.
- HTTP/SSE transport now runs through `uvicorn.run` directly on
  `mcp.streamable_http_app()` / `mcp.sse_app()` so middleware can be
  attached. `stdio` transport is unchanged.
- All eight tools now declare typed Pydantic return models instead of
  `dict[str, Any]` (audit SDK-002). FastMCP synthesises a real JSON
  schema for each tool's output, giving downstream clients (Inspector,
  custom UIs, schema-aware LLMs) field-level type information instead
  of opaque `additionalProperties: true`. Wire format is unchanged.
- Tool docstrings now carry `Use cases:` blocks (audit ARCH-002) with
  three concrete example queries each, sharpening LLM tool selection.
- `USER_AGENT` bumped to `lobbywatch-mcp/0.3.0`.

### Audit verification

- **Production-ready:** ✅ yes
- **Audit run-id:** `2026-05-09T133506-Z-lobbywatch-mcp`
- **Skill version:** `1.0.0`
- **Catalog hash:** `091f446b27965044…`
- **Check results:** 41 pass · 0 fail · 1 partial · 2 todo
- **Remaining finding:** `OPS-002` — README ASCII architecture diagram
  (cosmetic, ~10 min effort).

## [0.2.0] - 2026-05-09

### Changed (Breaking)
- **Tool names now carry a `lobbywatch_` namespace prefix** (audit SEC-022).
  All eight tools were renamed:
  `get_parlamentarier` → `lobbywatch_get_parlamentarier`,
  `list_interessenbindungen` → `lobbywatch_list_interessenbindungen`,
  `search_parlamentarier_nach_branche` → `lobbywatch_search_parlamentarier_nach_branche`,
  `get_lobbygruppe` → `lobbywatch_get_lobbygruppe`,
  `get_ranking` → `lobbywatch_get_ranking`,
  `get_transparenzquote` → `lobbywatch_get_transparenzquote`,
  `refresh_dump` → `lobbywatch_refresh_dump`,
  `dump_status` → `lobbywatch_dump_status`.
  Existing clients referencing the old names must be updated.

### Added
- FastMCP `lifespan` context manager owns the `LobbywatchClient` lifecycle
  (audit SDK-001). The shared `httpx.AsyncClient` is now closed cleanly on
  server shutdown; previously it leaked at process exit.
- Input validation at tool boundaries (audit SEC-018):
  `name_or_id` and `branche_query` bound to 1–200 chars; `kommission` /
  `partei` bound to ≤80 chars; `limit` bounded to 1–200 (search) /
  1–100 (ranking); `kriterium` is now a `Literal` enum so invalid values
  are rejected at the schema layer instead of via runtime `ValueError`.

### Changed
- `mcp[cli]` dependency is now bounded `<2.0.0` (audit ARCH-012).
- `USER_AGENT` bumped to `lobbywatch-mcp/0.2.0`.

## [0.1.0] - 2026-04-21

### Added
- Initial scaffold for `lobbywatch-mcp`, part of the Swiss Public Data MCP Portfolio.
- Hybrid data access: dump-first (weekly Lobbywatch JSON export) with live
  `dataIF` fallback for lobby groups.
- Phase 1 tools:
  - `get_parlamentarier` — profile lookup with fuzzy name match
  - `list_interessenbindungen` — conflict-of-interest records per MP
  - `search_parlamentarier_nach_branche` — branche + commission filter
  - `get_lobbygruppe` — live lobby group fetch via dataIF
  - `get_ranking` — top-N by criterion, commission/party filters
  - `get_transparenzquote` — distribution of verguetungstransparenz labels
  - `refresh_dump`, `dump_status` — cache control
- Retry + exponential backoff (2s/4s/8s) for dump downloads — tolerant of upstream HTTP 503 blips observed live.
- Dual transport: `stdio` (default) and `streamable-http` / `sse`.
- Pydantic v2 response envelopes carrying CC BY-SA 4.0 attribution.
- CI matrix (Python 3.11–3.13), ruff lint/format, respx-mocked unit tests.
- Tag-triggered PyPI publish workflow via OIDC Trusted Publisher.
- Live test suite (`@pytest.mark.live`) excluded from CI.

### Known limitations
- The upstream `/table/parlamentarier/...` dataIF endpoint returns empty
  responses at release time; all parliamentarian-facing tools therefore use
  the weekly dump. Lobby group lookups go through the live API.
- `zutrittsberechtigungen` are present in the data model but empty in the
  essential dump used here — surfaced as a stub for future expansion.
