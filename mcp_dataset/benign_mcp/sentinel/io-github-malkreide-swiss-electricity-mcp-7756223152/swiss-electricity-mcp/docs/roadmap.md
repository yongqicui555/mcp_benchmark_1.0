# Roadmap & phase architecture

This server follows a **read-only-first** phase model. A server may only advance
a phase once the listed preconditions are met and recorded in `CHANGELOG.md`.

## Phase 1 — Read-only (current)

All tools are read-only (`readOnlyHint=true`), reaching public Swiss open-data
upstreams (`openWorldHint=true`). No authentication, no write paths, no PII.

Done / in place:

- 12 read-only tools across `dashboard_*`, `tariff_*`, `consumption_*`, status.
- Egress allow-list + HTTPS gate, SPARQL-injection-safe query building.
- Structured logging (stderr) and opt-in OpenTelemetry tracing.
- CI (ruff + tests on 3.11–3.13), Gitleaks, Dependabot, tool-definition lock.

## Phase 2 — Write-capable (not planned)

Preconditions before any write/destructive tool is added:

- Audit re-run with the [mcp-audit-skill](https://github.com/malkreide/mcp-audit-skill).
- HITL confirmation (`ctx.elicit`) for every destructive operation.
- Idempotency keys / compensating actions where applicable.
- Auth model decided and the corresponding SEC OAuth/session checks satisfied.

There is currently **no plan** to move to Phase 2 — the data sources are
read-only open data.

## Phase 3 — Semantic / enrichment (not planned)

Would require a semantic layer, identity resolution, and sign-off from data
governance. Out of scope for an open-data aggregator.
