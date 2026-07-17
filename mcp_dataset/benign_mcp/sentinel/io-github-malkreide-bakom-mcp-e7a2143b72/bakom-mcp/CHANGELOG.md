# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-05-09

Audit-driven hardening release. After three full audit runs against
[`malkreide/mcp-audit-skill`](https://github.com/malkreide/mcp-audit-skill) v1.0.0
(catalog v0.5.0, 68 checks), the server reaches **production-ready** status
with 0 findings, 34 of 36 applicable checks passing.

### Added

- **MCP Prompts (3 templates)** — first-class `@mcp.prompt` discovery layer:
  - `schulhaus_konnektivitaet` (Anchor-Demo: Glasfaser+5G für Schulhäuser)
  - `rtv_kanton_uebersicht` (konzessionierte Sender pro Kanton)
  - `standort_konnektivitaet_vergleich` (generischer Standort-Vergleich)
- **Container deployment** — multi-stage `Dockerfile` (slim-bullseye, non-root UID 10001),
  `docker-compose.yml` with sandbox defaults (`read_only`, `cap_drop=ALL`,
  `no-new-privileges`, `mem_limit=256m`), `.dockerignore`, and CI build/smoke job.
- **Egress allow-list** — `ALLOWED_EGRESS_HOSTS` (frozenset) enforced via
  httpx event-hook on the lifespan client. Outbound calls to non-listed hosts
  raise `EgressNotAllowedError` before any TCP connect.
- **CC BY 4.0 attribution** — every Markdown tool output ends with a footer
  citing source (BAKOM via opendata.swiss / geo.admin.ch) and licence.
  README has dedicated "Data Licence" / "Datenlizenz" section.
- **README scope section** — explicit "What this server does / does not"
  (read-only, no filesystem access, no auth tokens, no caching, no `subprocess`).
- **Tool-call lifecycle logging** — decorator `_log_tool_call` emits structured
  records (`tool_call_start`, `tool_call_ok`, `tool_call_failed`) with
  `tool`, `duration_ms`, and `error_class` extras to stderr.
- **Progress reports** — `bakom_multi_standort_konnektivitaet` now calls
  `ctx.report_progress()` per location (visible spinner in Claude Desktop /
  MCP Inspector) plus `ctx.info()` at start.
- **Empty-result heuristics** — `bakom_sendeanlagen_suche` suggests doubling
  the radius (capped at 5000m); `bakom_rtv_suche` suggests targeted filter
  loosening (canton, media-type, query). LLM agents iterate instead of
  bouncing on "no results".
- **Secret-scan CI** — new `.github/workflows/secret-scan.yml` runs
  `gitleaks-action` on every push and pull request.
- **Env vars for HTTP transport** — `BAKOM_MCP_HOST` (default `127.0.0.1`),
  `BAKOM_MCP_PORT` (default `8050`), `BAKOM_MCP_CORS_ORIGINS`
  (comma-separated, default empty = CORS disabled). Explicit `0.0.0.0`-bind
  emits a stderr warning. `.env.example` documents the surface.
- **60 offline unit tests** — mock-based tests for inputs, error masking,
  lifespan, egress, logging, progress, prompts, heuristics, and attribution.
  Live tests now correctly tagged `@pytest.mark.live` and excluded from
  CI default (`pytest -m "not live"`).
- **Audit reports** — `audits/` directory with three full run outputs
  (`audit-report.md`, `summary.json`, `verification-results.json`, raw
  command outputs per check) for reproducible audit trails.

### Changed

- **FastMCP lifespan** — single `httpx.AsyncClient` shared across all tool
  calls (15 s timeout, `User-Agent: bakom-mcp/1.0`, HTTP-event-hook for
  egress). Previously: per-call client construction (TLS handshake on
  every tool invocation; for `bakom_multi_standort_konnektivitaet` with
  20 locations that meant up to 40 new connections per call).
- **Error semantics** — API errors now raise `ToolError` from
  `mcp.server.fastmcp.exceptions`. The wire response carries
  `CallToolResult(isError=True, …)` instead of a plain `"Fehler: …"`
  string with `isError=False`. MCP clients can distinguish data errors
  from successful results and apply retry logic.
- **Error masking** — generic exception catch no longer leaks the raw
  exception message (`f"Fehler: ({type(e).__name__}): {e}"` removed).
  Internal details go to `logger.exception`; the LLM sees
  `"Fehler: Unerwarteter interner Fehler. Bitte erneut versuchen."`
- **HTTP-mode entry point** — switched from `mcp.run(transport=…, port=…)`
  (which became invalid in mcp-SDK ≥ 1.10) to explicit
  `uvicorn.run(mcp.streamable_http_app(), host=…, port=…)` with optional
  CORS middleware. CORS is **off** by default and opt-in via
  `BAKOM_MCP_CORS_ORIGINS`; `expose_headers=["Mcp-Session-Id"]` for
  browser-client reconnect.
- **Status banner** — startup print in `--http` mode now goes to
  `sys.stderr` (was: `stdout`). Enforces stdio discipline so future
  additions cannot accidentally corrupt the JSON-RPC stream.
- **Dependency upper bounds** — `mcp[cli]>=1.10.0,<2.0`,
  `httpx>=0.27.0,<1.0`, `pydantic>=2.7.0,<3.0`. Prevents silent
  acceptance of major-version breaking changes.
- **README** — bilingual updates (EN + DE) with Docker section,
  env-var table, scope section, and data-licence section.

### Fixed

- Latent `TypeError` in `--http` startup path on mcp-SDK ≥ 1.10
  (the previous `mcp.run(port=…)` call was rejected by the new
  signature). The new `uvicorn.run(...)` flow is verified end-to-end
  via the new docker smoke-test CI job.
- Doubled CC BY 4.0 attribution footer in eight tool outputs
  (regression introduced and corrected within v2.0.0 development).

### Security

- **Container hardening** — non-root user, read-only filesystem,
  dropped capabilities, no privilege escalation, resource limits
  (256 MB RAM, 0.5 CPU, 64 PIDs).
- **Code-layer egress allow-list** — every outbound HTTP request is
  validated against a frozenset of six known data-source hosts before
  TCP connect.
- **Secrets hygiene** — `.gitignore` covers `.env`, `.env.*`,
  `*.secrets`, `credentials.json`. CI runs gitleaks on every PR.
- **Default localhost bind** — HTTP server defaults to `127.0.0.1`;
  `0.0.0.0` requires explicit env var and emits a stderr warning.

### Notes

- Two follow-up issues remain open as **conditional TODOs** that only
  become actionable when the deployment profile changes:
  - [#29](https://github.com/malkreide/bakom-mcp/issues/29) — SCALE-002
    Stateful LB for Streamable-HTTP (when `is_cloud_deployed=true`)
  - [#30](https://github.com/malkreide/bakom-mcp/issues/30) — SEC-009
    Session-ID Cryptographic Binding (when `auth_model != "none"`)

## [1.0.0] - 2026-03-13

### Added
- Initial release
- 12 tools in 4 categories: broadband, mobile, media/RTV, statistics
- `bakom_broadband_coverage` – Fixed-line coverage at 30–1000 Mbit/s (geo.admin.ch)
- `bakom_glasfaser_verfuegbarkeit` – FTTB/FTTH fibre availability
- `bakom_multi_standort_konnektivitaet` – Multi-location connectivity comparison (up to 20 locations)
- `bakom_mobilfunk_abdeckung` – 5G/4G/3G outdoor coverage
- `bakom_sendeanlagen_suche` – Mobile antenna search by radius
- `bakom_frequenzdaten` – Radio/TV transmitter sites
- `bakom_rtv_suche` – Licensed broadcaster search (RTV database)
- `bakom_medienstruktur_info` – Swiss media landscape datasets
- `bakom_aktuell` – Current BAKOM topics with opendata.swiss enrichment
- `bakom_telekomstatistik_uebersicht` – Telecom statistics via CKAN API
- `bakom_breitbandatlas_datensaetze` – Full Broadband Atlas layer catalogue
- 2 MCP resources: `bakom://info`, `bakom://demo-standorte`
- 18 integration tests against live APIs
- GitHub Actions CI (Python 3.11–3.13)
- Bilingual documentation (EN/DE, Swiss spelling)
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud)
- WGS84 → LV95 coordinate conversion (swisstopo approximation)
