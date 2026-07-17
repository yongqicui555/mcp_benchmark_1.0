# MCP-Server Audit-Report — `swiss-cultural-heritage-mcp`

**Audit-Datum:** 2026-06-02
**Skill-Version:** 1.0.0
**Catalog-Version:** v0.5.0 (68 checks)

---

## 1. Executive Summary

Server `swiss-cultural-heritage-mcp` wurde gegen 41 anwendbare Best-Practice-Checks geprüft. 20 bestanden, 21 Findings dokumentiert (2 critical, 9 high, 10 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: OBS-002.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `swiss-cultural-heritage-mcp` |
| Audit-Datum | 2026-06-02 |
| Skill-Version | 1.0.0 |
| Catalog-Version | v0.5.0 (68 checks) |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'Render', 'Docker']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 7 | 1 | 3 | 0 | 0 |
| CH | 0 | 0 | 1 | 0 | 0 |
| OBS | 1 | 3 | 1 | 0 | 0 |
| OPS | 2 | 0 | 1 | 0 | 0 |
| SCALE | 1 | 0 | 4 | 0 | 0 |
| SDK | 1 | 0 | 3 | 0 | 0 |
| SEC | 8 | 0 | 4 | 0 | 3 |
| **Total** | **20** | **4** | **17** | **0** | **3** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-004 | SEC | critical | partial |
| SEC-019 | SEC | critical | partial |
| ARCH-004 | ARCH | high | partial |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | fail |
| OPS-003 | OPS | high | partial |
| SCALE-002 | SCALE | high | partial |
| SCALE-003 | SCALE | high | partial |
| SDK-004 | SDK | high | partial |
| SEC-005 | SEC | high | partial |
| SEC-022 | SEC | high | partial |
| ARCH-003 | ARCH | medium | partial |
| ARCH-011 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | fail |
| CH-004 | CH | medium | partial |
| OBS-003 | OBS | medium | fail |
| OBS-006 | OBS | medium | fail |
| SCALE-004 | SCALE | medium | partial |
| SCALE-006 | SCALE | medium | partial |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | partial |

**Gesamt:** 21 Findings

---

## 5. Detail-Findings

### ARCH-003

## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-003` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Empty-result paths return actionable hints, not bare empties (heritage_browse_collection tip to check resource IDs server.py:646; helveticat tip server.py:783)

### Gaps vs. Pass Criteria

- No match_type field (exact/fuzzy/none) in responses
- No fuzzy-match or suggestion mechanism on zero hits

### Expected Behavior

Search tools that return no results should offer a fuzzy match or a suggestion mechanism and expose a match_type field (exact/fuzzy/none); on none, give an actionable hint.

### Risk Description

On a typo or near-miss query the LLM gets a flat «keine Treffer» and tends to give up or hallucinate, instead of being steered to a corrected term or a sibling tool.

### Remediation

Add a `match_type` field to JSON responses; on zero exact hits for SIKART/SNM, retry with a loosened CKAN `q` (partial/OR) and label results `fuzzy`. Keep the existing textual tips. OAI-PMH (NB) has no server-side search, so document the exact-only behaviour there.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### ARCH-004

## Finding: ARCH-004 — Inversion of Control: Settings-Objekt statt globale Module-Vars

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-004` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Tool handlers are transport-agnostic; none read the raw request object
- Single shared lifespan covers both transports (server.py:75-89)
- dual transport selectable at entrypoint (server.py:1318-1326)

### Gaps vs. Pass Criteria

- Configuration uses module-level constants (CKAN_API, HTTP_TIMEOUT, ALLOWED_HOSTS, server.py:30-48), not a Pydantic-Settings object — criterion explicitly requires a settings object over global module vars
- Transport selected via sys.argv flag rather than ENV var

### Expected Behavior

Configuration (endpoints, timeouts, allow-list, host/port) should come from a Pydantic-Settings object loaded once, not from module-level constants; transport selectable via ENV.

### Risk Description

Module-global config cannot be overridden per environment without editing code; tests and multi-env deploys monkeypatch globals, which is brittle.

### Remediation

Introduce a `Settings(BaseSettings)` with fields for CKAN base URL, timeout, allow-list, transport, host, port (env-prefixed). Instantiate once at startup and inject. Replace the `sys.argv` flag parsing with `MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT` env vars.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### ARCH-011

## Finding: ARCH-011 — Repo-Struktur: tools/-Aufteilung bei > 5 Tools

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- All mandatory top-level files present: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- src/ layout correct, tests/ and .github/workflows/ present
- README.de.md mirrors README.md sections
- CI (ci.yml) + publish.yml present

### Gaps vs. Pass Criteria

- 8 tools in a single server.py (>5-tool threshold) with no tools/ package split and no README justification for the deviation

### Expected Behavior

With more than 5 tools, split tool definitions into a tools/ package (file per group), or justify the single-file layout in the README.

### Risk Description

A 1300-line single module is harder to navigate and review; the >5-tool guideline exists to keep per-group ownership clear.

### Remediation

Either split server.py into `tools/sik_isea.py`, `tools/snm.py`, `tools/nb.py`, `tools/cross.py` registered on the shared `mcp`, or add a short 'Project Structure' note in README explaining the deliberate single-file choice.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-011` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + SDK-Update-Disziplin

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `ARCH-012` |
| **PDF-Reference** | Sec 2.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- CHANGELOG.md present and in Keep-a-Changelog format with SemVer

### Gaps vs. Pass Criteria

- protocolVersion is NOT explicitly pinned in server code (relies on SDK default)
- No 'MCP Protocol Version' section in README
- No Dependabot/Renovate config for monthly SDK update PRs

### Expected Behavior

protocolVersion explicitly pinned in code; a README 'MCP Protocol Version' section with an update policy; Dependabot/Renovate for monthly SDK PRs.

### Risk Description

An SDK upgrade can silently bump the negotiated protocol version; without pinning and a changelog discipline, behaviour drifts between releases unnoticed.

### Remediation

Document and (where the SDK exposes it) pin the supported MCP protocol version; add a 'MCP Protocol Version' README section; add `.github/dependabot.yml` (pip, weekly/monthly) so `mcp` upgrades arrive as reviewable PRs.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `ARCH-012` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### CH-004

## Finding: CH-004 — OGD-CH Lizenz-Compliance: CC BY Attribution pro Datensatz

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `CH-004` |
| **PDF-Reference** | CH custom |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- README documents all three sources and notes open licences (CC0/CC BY, README.md:241)
- Per-record SIKART links and NUTZUNGSLIZENZ/rights fields surfaced in detail views (server.py:440,974)

### Gaps vs. Pass Criteria

- Tool responses carry no consistent structured source+licence field per dataset; provenance is incidental, not guaranteed per record (esp. in cross_search aggregation)

### Expected Behavior

Tool responses carry a structured source+licence field per dataset; provenance preserved per record in aggregation; attribution text per the licence (author, source, licence).

### Risk Description

Open-government data under CC BY requires attribution; aggregated answers that drop the source/licence per record put the consumer at risk of a licence breach.

### Remediation

Add a `source` block (`{name, url, license}`) to every JSON response and a footer line in markdown; in `heritage_cross_search` keep provenance per item, not just per section header.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `CH-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: isError-Flagging

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OBS-001` |
| **PDF-Reference** | Sec 6.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Narrow ExpectedUpstreamError tuple catches only upstream/parse/value errors; programming errors (KeyError/TypeError) propagate to the framework (server.py:103-109)
- Execution-error path covered by test_get_artist_http_error (test_server.py:528)

### Gaps vs. Pass Criteria

- Handled upstream failures are returned as plain German strings (server.py:142-161), not as tool results flagged isError:true — the LLM cannot distinguish an error result from a successful one

### Expected Behavior

Handled application errors should be returned as tool results flagged isError:true (not as plain success strings), so the client can distinguish failure from content.

### Risk Description

A German «Fehler: …» string is indistinguishable to the LLM from a normal answer; it may relay the error as fact or retry incorrectly.

### Remediation

Return execution errors via the FastMCP error path (raise a McpError / return an error-flagged result) instead of `return _handle_error(e)` strings, or wrap the string in a structured `{is_error: true, message}` envelope. Add a test asserting the error result is flagged.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OBS-001` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### OBS-002

## Finding: OBS-002 — Mask Error Details: keine internen Exceptions ans LLM

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OBS-002` |
| **PDF-Reference** | Sec 6.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- FastMCP is constructed without mask_error_details (server.py:89: FastMCP(name, lifespan=lifespan))
- Handled errors via _handle_error never include tracebacks (good)

### Gaps vs. Pass Criteria

- mask_error_details=True is NOT set; combined with OBS-001's deliberate propagation of programming errors, an unhandled exception's raw message is surfaced to the client by FastMCP's default behaviour — internal detail leak to the LLM

### Expected Behavior

FastMCP initialised with mask_error_details=True so that unhandled exceptions surface a generic message to the client, with the real error only in server logs.

### Risk Description

BLOCKING. OBS-001 deliberately lets programming errors (KeyError/TypeError/…) propagate. Without mask_error_details, FastMCP's default puts the raw exception text into the client-visible error — internal detail (field names, code paths) leaks to the LLM/end user.

### Remediation

Set `mcp = FastMCP("swiss_cultural_heritage_mcp", lifespan=lifespan, mask_error_details=True)`. Add a test that triggers a programming error and asserts the client message is generic. This single change unblocks production-readiness.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OBS-002` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### OBS-003

## Finding: OBS-003 — Structured Logging mit Severity-Stufen

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OBS-003` |
| **PDF-Reference** | Sec 6.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- grep confirms no logging framework imported and no logger usage anywhere in src/

### Gaps vs. Pass Criteria

- No structured logger (structlog/loguru) in dependencies
- Zero log statements: no per-tool-call bound context (tool name, session id), no severity levels

### Expected Behavior

A structured logger (structlog/loguru) emitting JSON/logfmt to stderr, with per-tool-call bound context (tool name, session id) and >=4 severity levels.

### Risk Description

With zero logging, operational incidents in the cloud deployment are undiagnosable: no record of which tool ran, which upstream failed, or how often.

### Remediation

Add structlog configured with `WriteLoggerFactory(file=sys.stderr)` (keeps stdout clean — see OBS-004); bind tool name + session id per call; log upstream failures at warning/error. Keep payloads out of logs (no PII).

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OBS-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### OBS-006

## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Sec 6.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- No OpenTelemetry SDK in dependencies; no tracer/exporter setup in src/

### Gaps vs. Pass Criteria

- No distributed tracing, no per-tool-call spans, no httpx auto-instrumentation — relevant for the cloud (Render) deployment target

### Expected Behavior

OTel SDK + OTLP exporter, httpx auto-instrumentation, one span per tool call (mcp.tool.name, is_error), OTLP endpoint via env var, no sensitive data in attributes.

### Risk Description

No tracing means upstream latency (SIKART/SNM/NB) and cross-search fan-out cannot be observed in production; slow-source diagnosis is guesswork.

### Remediation

Add opentelemetry-sdk + opentelemetry-instrumentation-httpx; wrap each tool body in a span; configure the OTLP endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT`; set service.name + environment. Gate it behind the env var so stdio/local stays zero-overhead.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OBS-006` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### OPS-003

## Finding: OPS-003 — Phasenarchitektur: Phase explizit deklarieren

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `OPS-003` |
| **PDF-Reference** | App. C |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Server is consistently Phase 1 (read-only): all tools readOnlyHint:true, no destructive/write tools — annotations match the phase
- CHANGELOG 0.1.0 references 'Phase 1 implementation'

### Gaps vs. Pass Criteria

- Current phase is not explicitly declared in README
- No roadmap file with phase-specific tasks / transition prerequisites

### Expected Behavior

Current phase (1/2/3) declared in README; a roadmap file with phase-specific tasks and documented transition prerequisites.

### Risk Description

Without an explicit phase declaration, contributors may add write/destructive tools without triggering the Phase 1->2 gate (audit, ISDS, DSG processing record).

### Remediation

Add a 'Phase' line to the README ('Phase 1 — read-only') and a `docs/roadmap.md` listing Phase 1 scope and the Phase 2 prerequisites. Record phase transitions in CHANGELOG.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `OPS-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SCALE-002

## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Server tool logic is stateless; no per-tool persistent session state to lose

### Gaps vs. Pass Criteria

- No sticky-session / shared-state (Redis/Durable Objects) session affinity for Streamable HTTP, and no documented single-instance constraint or session TTL — must be addressed before horizontal scaling

### Expected Behavior

Sticky sessions on Mcp-Session-Id at the edge LB, or a shared-state session manager (Redis/Durable Objects), with an explicit session TTL — or a documented single-instance constraint.

### Risk Description

If the Render service is scaled to >1 instance without affinity, a client's follow-up request can land on an instance that does not know its session, breaking the stream.

### Remediation

For now, document the single-instance constraint and the session TTL in docs/. Before horizontal scaling, add sticky sessions on `Mcp-Session-Id` (Variant A) or a Redis session backend (Variant B).

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-002` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SCALE-003

## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-003` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Single-instance Render/Docker deployment documented as the target

### Gaps vs. Pass Criteria

- No edge-LB Mcp-Session-Id routing / stick-table config documented; same horizontal-scaling concern as SCALE-002 (operator-scope, currently single-instance)

### Expected Behavior

Edge LB reads Mcp-Session-Id and routes via a stick-table/hash with adequate capacity and an explicit TTL; failover tested so sessions are not silently re-homed without shared state.

### Risk Description

Same horizontal-scaling failure mode as SCALE-002, viewed from the LB layer.

### Remediation

When moving beyond single-instance: configure HAProxy/Nginx/Ingress to hash on `Mcp-Session-Id` with TTL ~= session TTL, and test backend-failover behaviour. Until then, document that the deployment is single-instance.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SCALE-004

## Finding: SCALE-004 — Containerization: Multi-Stage-Build + HEALTHCHECK

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-004` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Dockerfile uses a slim base (python:3.13-slim) and a non-root user UID 10001 (Dockerfile)

### Gaps vs. Pass Criteria

- Single-stage build (one FROM, no AS builder/runtime split)
- No HEALTHCHECK directive in the Dockerfile (a /health route exists in-app)

### Expected Behavior

Dockerfile with >=2 named stages (builder/runtime), slim/alpine final base, non-root user, and a HEALTHCHECK directive; final image < 200 MB.

### Risk Description

A single-stage image can carry build artefacts into the runtime layer (larger surface); a missing HEALTHCHECK means orchestrators cannot detect a wedged process.

### Remediation

Split the Dockerfile into `AS builder` (pip install/wheel) and `AS runtime` (copy site-packages only); add `HEALTHCHECK --interval=30s CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/health')"` (or curl).

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SCALE-006

## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-006` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- docs/security.md and network-egress.md document k8s securityContext and NetworkPolicy

### Gaps vs. Pass Criteria

- No explicit memory/CPU resource limits or requests documented; no FD-limit/OOM guidance for the container

### Expected Behavior

Explicit memory and CPU limits (requests < limits), FD limit >= 4096 for many outbound connections, and tested clean OOM/restart behaviour.

### Risk Description

Without limits a runaway request (e.g. large OAI-PMH ListRecords parse) can exhaust the host; without a restart policy a crash means downtime.

### Remediation

Document recommended `resources.requests/limits` (e.g. 128Mi/256Mi, 100m/500m) in docs/, set `restartPolicy`, and note `ulimit -n` guidance. For Render, document the chosen instance size.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-006` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SDK-002

## Finding: SDK-002 — Strukturierte Tool-Returns / Response-Envelope

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SDK-002` |
| **PDF-Reference** | Sec 3.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Pydantic >=2 in dependencies; all *Input classes are typed Pydantic v2 models with Field defaults and a ResponseFormat StrEnum (server.py:93)

### Gaps vs. Pass Criteria

- All tools are annotated -> str and return formatted markdown / json-as-string, not structured Pydantic/TypedDict objects
- No consistent response envelope (source/provenance/results/count) on search/list tools

### Expected Behavior

Tools return typed objects (Pydantic/TypedDict/dict[str,X]) with a consistent envelope (source, provenance, results, count), not hand-built strings.

### Risk Description

String returns force the client to re-parse markdown; there is no machine-stable contract, so downstream automation is fragile and counts/provenance are inconsistent.

### Remediation

Define a `SearchResult`/`ResultEnvelope` Pydantic model (`source`, `count`, `results`, optional `has_more`) and return it from search/list tools; keep a `response_format='markdown'` rendering as a thin view over the structured object.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SDK-002` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SDK-003

## Finding: SDK-003 — Context Injection für Progress und Logging

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SDK-003` |
| **PDF-Reference** | Sec 3.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Most tools are single fast upstream calls

### Gaps vs. Pass Criteria

- No tool accepts ctx: Context; heritage_cross_search fans out to 3 upstreams (likely >2s) without ctx.report_progress() or ctx.warning() for the per-source failures it currently swallows into the result string (server.py:1059)

### Expected Behavior

Tools expected to run >2s take ctx: Context and call ctx.report_progress(); non-fatal issues logged via ctx.warning()/ctx.error() rather than swallowed.

### Risk Description

heritage_cross_search fans out to three upstreams and silently folds per-source errors into the result text; the client gets no progress signal and no structured warning.

### Remediation

Add `ctx: Context` to heritage_cross_search; call `await ctx.report_progress()` per completed source and `await ctx.warning(...)` for each failing source instead of only embedding the error string.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SDK-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SDK-004` |
| **PDF-Reference** | Sec 3.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Streamable HTTP transport is offered and the README advertises browser/SSE access (README.md:131)

### Gaps vs. Pass Criteria

- No CORS middleware configured; Mcp-Session-Id is not in expose_headers/allow_headers, so browser clients cannot read the session id across requests — needs explicit Starlette CORSMiddleware with a non-wildcard origin list in production

### Expected Behavior

CORS middleware configured for HTTP/SSE; expose_headers and allow_headers include Mcp-Session-Id; allow_origins is an explicit non-wildcard list in production.

### Risk Description

The README advertises browser access, but browsers cannot read Mcp-Session-Id unless it is in expose_headers — SSE session continuity breaks for browser clients.

### Remediation

Mount Starlette `CORSMiddleware` on the Streamable-HTTP app with `expose_headers=['Mcp-Session-Id']`, `allow_headers=['Mcp-Session-Id','Content-Type']`, and an env-driven `allow_origins` allow-list (no `*` in prod).

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SDK-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SEC-004

## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforce + IP-Blocklisting (Defense-in-Depth)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-004` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Host egress allow-list enforced before every request and re-checked on every redirect hop (server.py:112-139); a redirect to 169.254.169.254 would be rejected because it is not in ALLOWED_HOSTS
- All request hosts are built from module constants; no user input controls the host (only query/resource_id params)

### Gaps vs. Pass Criteria

- No explicit https-scheme assertion in _assert_allowed
- No resolved-IP blocklist (private/link-local/loopback/IPv6) and no DNS-pin against TOCTOU — the SSRF vector is closed in practice by the 2-host allow-list, so IP-level controls are defense-in-depth, not a live exposure

### Expected Behavior

Explicit https-scheme check before each request; resolved-IP blocklist for private/link-local/loopback incl. 169.254.169.254 and IPv6 (::1, fe80::/10); single DNS resolution reused (no TOCTOU).

### Risk Description

Low live risk: the 2-host egress allow-list already blocks metadata IPs and there is no user-controlled host. The gap is missing belt-and-suspenders IP-level controls should the allow-list ever widen or a host be added carelessly.

### Remediation

In _assert_allowed also assert `httpx.URL(url).scheme == 'https'`; optionally add a resolved-IP blocklist guard for defense-in-depth. Keep the host allow-list as the primary control. Prioritise below the code-finding backlog given the closed allow-list.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SEC-005

## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-005` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Only two fixed Swiss-federal hosts are reachable (ALLOWED_HOSTS), so a rebinding attack would require compromising DNS for ckan.opendata.swiss or helveticat.nb.admin.ch

### Gaps vs. Pass Criteria

- No DNS pinning: httpx resolves per request, so a strict reading leaves a theoretical TOCTOU window (low real risk given the closed allow-list)

### Expected Behavior

DNS resolved once per request and the resolved IP pinned for the TCP connection; original hostname kept for SNI/Host/cert validation.

### Risk Description

Theoretical TOCTOU only: an attacker would need to control DNS for one of the two fixed Swiss-federal hosts. Real-world risk is minimal given the closed allow-list.

### Remediation

If hardening to spec: use a custom httpx transport/resolver that pins the first resolved A/AAAA record and validates the certificate against the original hostname. Treat as low priority while the allow-list holds two trusted hosts.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-005` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SEC-019

## Finding: SEC-019 — Lethal Trifecta: Bewertung dokumentieren

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-019` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Server has at most ONE leg of the lethal trifecta: it reads only PUBLIC data (no private data), has no write/send/exfiltration channel, and returns results only to the calling LLM
- Receiver allow-list present as a frozenset (ALLOWED_HOSTS, server.py:45)

### Gaps vs. Pass Criteria

- No explicit lethal-trifecta assessment / ADR in docs/security.md (the threat model exists but does not state the trifecta evaluation) — remediation is a short documentation addition; the server does NOT possess the trifecta

### Expected Behavior

An explicit lethal-trifecta assessment in docs/ confirming the server holds at most two of {private-data access, untrusted-content exposure, exfiltration}; receiver allow-lists as frozensets.

### Risk Description

The server does NOT possess the trifecta (public data only, no send/write channel), but the absence of a written assessment means a future contributor could add an exfiltration-capable tool without re-evaluating.

### Remediation

Add a short 'Lethal Trifecta' subsection to docs/security.md stating: data is public (not private), no outbound send/write capability, egress restricted to ALLOWED_HOSTS — therefore the trifecta is not present. Re-evaluate on any new tool with a send/write side effect.

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-019` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Sec 4.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- All tools share a consistent heritage_ namespace prefix
- Breaking tool changes are tracked in CHANGELOG with SemVer major bumps (e.g. removal of period/technique params)

### Gaps vs. Pass Criteria

- Prefix is heritage_, not the server-identity form <server>__<tool>
- No tool-definition hash snapshot generated at release for rug-pull detection
- No explicit user re-approval note on description changes

### Expected Behavior

Tools namespaced with server identity (<server>__<tool>); a tool-definition hash snapshot generated per release; CHANGELOG flags tool-description changes with a re-approval note.

### Risk Description

A silently changed tool description (rug pull) could re-task the LLM. The heritage_ prefix is consistent but not server-identified, and there is no release-time hash to detect definition drift.

### Remediation

Optionally adopt a `<server>__<tool>` prefix (breaking — major bump); add a release step that hashes tool names+descriptions+schemas into `audits/tool-pins/<version>.json`; add a CHANGELOG note when any tool description changes, prompting user re-approval.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SEC-022` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-004** (critical, partial)
2. **SEC-019** (critical, partial)
3. **ARCH-004** (high, partial)
4. **OBS-001** (high, partial)
5. **OBS-002** (high, fail)
6. **OPS-003** (high, partial)
7. **SCALE-002** (high, partial)
8. **SCALE-003** (high, partial)
9. **SDK-004** (high, partial)
10. **SEC-005** (high, partial)
11. **SEC-022** (high, partial)
12. **ARCH-003** (medium, partial)
13. **ARCH-011** (medium, partial)
14. **ARCH-012** (medium, fail)
15. **CH-004** (medium, partial)
16. **OBS-003** (medium, fail)
17. **OBS-006** (medium, fail)
18. **SCALE-004** (medium, partial)
19. **SCALE-006** (medium, partial)
20. **SDK-002** (medium, partial)
21. **SDK-003** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `v0.5.0 (68 checks)` |
| policy | `fail-or-partial` |
| audit_date | `2026-06-02` |


_Generated by tools/build_report.py — do not edit by hand._
