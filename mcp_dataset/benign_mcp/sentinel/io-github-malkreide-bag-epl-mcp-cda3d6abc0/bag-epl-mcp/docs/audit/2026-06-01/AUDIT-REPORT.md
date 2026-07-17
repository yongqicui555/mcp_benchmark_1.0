# MCP-Server Audit-Report — `bag-epl-mcp`

> Generated with the [mcp-audit-skill](https://github.com/malkreide/mcp-audit-skill) (v1.0.0, 68-check catalog, 8 categories).
> All numbers in this report derive from [`summary.json`](./summary.json) — the single source of truth.

---

## 1. Executive Summary

Of **68** catalog checks, **44** apply to this server's profile. Of those, **11 pass**, **26 are partial**, and **7 fail** — yielding **33 findings** (4 critical, 16 high, 13 medium, 0 low).

The server is **well-engineered for its Phase-1, local, read-only purpose**: strong Pydantic input validation, no command-injection/secret/`print()` issues, three MCP primitives, a clean `src`-layout, CI, and bilingual docs. The dominant theme across the findings is a **gap between the advertised "dual transport / cloud" deployment and the actual implementation**: `src/bag_epl_mcp/server.py` only ever calls `mcp.run()` (stdio), with no argument/env parsing — so the README's `--http --port 8000` cloud instructions are non-functional, and every HTTP/cloud-specific control (CORS, session binding, host-binding, load-balancing, containerization, egress) is consequently absent.

**Production-readiness: `false`.** Safe for local single-user stdio (Phase 1) use today; **not** ready for the multi-user cloud deployment described in the README until the transport gap and the four critical-severity items are addressed.

---

## 2. Profil-Snapshot

| Field | Value |
|-------|-------|
| Server | `bag-epl-mcp` (v0.1.0) |
| Repository | https://github.com/malkreide/bag-epl-mcp |
| Transport | **dual** (stdio + Streamable HTTP — HTTP *advertised but not implemented*) |
| Auth Model | **none** (public, no API key) |
| Data Class | **Public Open Data** (BAG SL / GGSL / MiGeL, Fedlex) |
| Write Capable | **false** (HTTP GET only) |
| Deployment | Render.com (cloud) + local stdio (Claude Desktop) |
| `is_cloud_deployed` | true |
| Tools make external requests | true (`sl.bag.admin.ch`) |
| SDK / Language | Python · FastMCP · Pydantic v2 |
| Sampling / Sequential-Thinking | none |
| CH context | none (no Stadt Zürich / Volksschule / Schulamt / PII) |

---

## 3. Applicability Overview

| Category | In catalog | Applicable | Pass | Partial | Fail | N/A |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| ARCH | 12 | 11 | 6 | 4 | 1 | 1 |
| SDK  | 5  | 4  | 0 | 3 | 1 | 1 |
| SEC  | 23 | 15 | 4 | 10 | 1 | 8 |
| SCALE| 6  | 5  | 0 | 3 | 2 | 1 |
| OBS  | 6  | 5  | 1 | 2 | 2 | 1 |
| HITL | 5  | 0  | 0 | 0 | 0 | 5 |
| CH   | 8  | 1  | 0 | 1 | 0 | 7 |
| OPS  | 3  | 3  | 0 | 3 | 0 | 0 |
| **Total** | **68** | **44** | **11** | **26** | **7** | **24** |

---

## 4. Findings-Übersicht (sorted by severity)

### Critical (4)

| ID | Title | Status | Effort |
|----|-------|--------|:---:|
| SEC-004 | SSRF-Prevention (HTTPS + IP-Blocklist) | partial | S |
| SEC-009 | Session-ID Cryptographic Binding | partial | M |
| SEC-016 | 0.0.0.0-Binding-Prevention (NeighborJack) | partial | S |
| SEC-019 | Lethal Trifecta — documented capability assessment | partial | S |

### High (16)

| ID | Title | Status | Effort |
|----|-------|--------|:---:|
| SCALE-001 | Streamable HTTP transport for cloud **not implemented** | fail | M |
| ARCH-009 | Tool annotations (`readOnlyHint`/`openWorldHint`) | fail | S |
| SDK-004 | CORS `Mcp-Session-Id` exposure | fail | S |
| SEC-007 | Container-Sandboxing | fail | M |
| ARCH-004 | Inversion of Control / transport selection via env | partial | M |
| SDK-001 | FastMCP lifespan + pooled httpx client | partial | S |
| SEC-005 | DNS-Rebinding-Prevention | partial | M |
| SEC-018 | Input validation — explicit `strict=True` | partial | S |
| SEC-021 | Egress allow-list (code + network) | partial | M |
| SEC-022 | Tool-hash-pinning + namespace prefix | partial | S |
| SCALE-002 | Stateful load balancing (sticky sessions) | partial | M |
| SCALE-003 | `Mcp-Session-Id` routing via edge-LB | partial | M |
| OBS-001 | Protocol vs. execution errors (`isError`) | partial | M |
| OBS-002 | Mask error details (`mask_error_details=True`) | partial | S |
| OPS-001 | Test strategy (≥5 mocked + ≥1 live per tool) | partial | M |
| OPS-003 | Phase architecture — roadmap file + sign-off gates | partial | S |

### Medium (13)

| ID | Title | Status | Effort |
|----|-------|--------|:---:|
| SCALE-004 | Containerization (multi-stage Dockerfile) | fail | M |
| OBS-003 | Structured logging (structlog/JSON) | fail | S |
| OBS-006 | OpenTelemetry distributed tracing | fail | M |
| ARCH-002 | Tool descriptions with `<use_case>` tags | partial | S |
| ARCH-003 | Not-Found anti-pattern (`match_type` field) | partial | S |
| ARCH-012 | `protocolVersion` pinning + Dependabot | partial | S |
| SDK-002 | Structured tool returns (BaseModel envelope) | partial | M |
| SDK-003 | Context injection (progress/logging) | partial | S |
| SEC-014 | Tool allow-listing (gateway / default-deny) | partial | M |
| SEC-015 | Pre-flight tool-poisoning detection | partial | M |
| SCALE-006 | Container resource limits | partial | S |
| CH-004 | OGD-CH licence attribution (CC BY 4.0) | partial | S |
| OPS-002 | Data-flow architecture diagram | partial | S |

---

## 5. Detail-Findings

> Full write-ups for the 4 critical findings and the highest-leverage high findings. Evidence cites `file:line` against the audited tree (commit on branch `claude/cool-rubin-0gH4z`).

### Finding: SCALE-001 — Streamable HTTP transport for cloud is not implemented `[HIGH]` `[fail]`

**This is the root cause of most HTTP/cloud findings below and is listed first despite its severity because of its blast radius.**

- **Observed behavior:** The entrypoint runs stdio only. `src/bag_epl_mcp/server.py:511-512`:
  ```python
  if __name__ == "__main__":
      mcp.run()            # FastMCP default transport == "stdio"
  ```
  `pyproject.toml` console-script is `bag-epl-mcp = "bag_epl_mcp.server:mcp.run"` — again stdio. A repo-wide search finds **no** `argparse`, `--http`, `--port`, `transport=`, `streamable`, or `sys.argv` handling.
- **Expected behavior:** README → "Cloud Deployment" instructs `python -m bag_epl_mcp.server --http --port 8000`, and README/CHANGELOG claim "Dual transport: stdio + Streamable HTTP". For Render, the server must select `streamable-http` (e.g. via `MCP_TRANSPORT`/CLI) and respond to `initialize` over HTTP.
- **Evidence:** `server.py:511`; README "Cloud Deployment (SSE…)" section; `CHANGELOG.md` "Dual transport" line. No `--http` parsing exists.
- **Risk:** The documented cloud deployment path silently does not work — the process starts in stdio mode and never opens an HTTP listener, so the Render service / `claude.ai` MCP connection fails. Also makes SEC-016, SDK-004, SEC-009, SCALE-002/003 untestable.
- **Remediation:** Add explicit transport selection, e.g.:
  ```python
  import os
  if __name__ == "__main__":
      transport = os.getenv("MCP_TRANSPORT", "stdio")
      if transport in ("http", "streamable-http"):
          mcp.run(transport="streamable-http")
      else:
          mcp.run()  # stdio default
  ```
  Default stays stdio (preserves SEC-006). Document `MCP_TRANSPORT=streamable-http` for Render; update the README command to match the real flag. Add a smoke test that `initialize` returns HTTP 200.
- **Effort:** M · **Verification:** start with `MCP_TRANSPORT=streamable-http`, curl `initialize`, expect 200.

---

### Finding: SEC-004 — SSRF-Prevention `[CRITICAL]` `[partial]`

- **Observed behavior:** Outbound requests are built from **hardcoded** `https://` constants (`SL_API_URL` at `server.py:27`) via `_http_get` (`server.py:47-50`). Only the *query string* is user/LLM-controlled (`suchbegriff`), never the host/scheme. There is **no** explicit HTTPS-scheme assertion, **no** resolved-IP blocklist (private/link-local/`169.254.169.254`/IPv6), and **no** egress proxy.
- **Expected behavior:** Explicit `https` validation before each request, resolved-IP blocklisting, single DNS resolution, egress proxy as defense-in-depth.
- **Evidence:** `server.py:26-31`, `47-50`, `92-95`.
- **Risk:** **Low in current code** because hosts are fixed constants — there is no user-controlled URL to pivot SSRF through. Residual risk arises only if a future phase (FHIR, `FHIR_BASE_URL` at `server.py:36`) introduces dynamic hosts. The check is *partial* (mitigated-by-design, controls not explicit).
- **Remediation:** Add a small egress guard that asserts `scheme == "https"` and validates the resolved IP against a private/loopback blocklist before any GET; wire it into `_http_get`. Combine with the SEC-021 frozenset host allow-list (one helper covers both).
- **Effort:** S · **Verification:** unit test that a `http://` or `127.0.0.1`/`169.254.169.254` target is rejected.

---

### Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack) `[CRITICAL]` `[partial]`

- **Observed behavior:** No host binding is configured anywhere (HTTP transport not implemented). When the documented `--http` path is eventually wired, FastMCP's HTTP host default and Render's `0.0.0.0` exposure are **undefined/uncontrolled** — there is no env-driven host defaulting to `127.0.0.1`, and no documentation of local-vs-container binding.
- **Expected behavior:** No hardcoded `0.0.0.0`; host via env var defaulting to `127.0.0.1`; `0.0.0.0` only in the container context; docs explain the difference.
- **Evidence:** absence of any `host=`/`0.0.0.0` in `src/` (repo-wide grep); `server.py:511`.
- **Risk:** Once HTTP is enabled, an unintended `0.0.0.0` bind exposes all six tools to network neighbors on shared infrastructure. Currently *partial* because no HTTP listener exists yet.
- **Remediation:** Introduce `MCP_HOST` (default `127.0.0.1`); set `MCP_HOST=0.0.0.0` only in the Render/Docker environment. Document the distinction. Couple with SCALE-001 remediation.
- **Effort:** S · **Verification:** default launch binds loopback only.

---

### Finding: SEC-009 — Session-ID Cryptographic Binding `[CRITICAL]` `[partial]`

- **Observed behavior:** With dual transport and `auth_model == none`, there is no user identity and no custom session binding; the server relies entirely on FastMCP's default session handling. No JWT/`user_id:session_id` binding, TTL, or server-side invalidation is configured.
- **Expected behavior:** Cryptographically secure session IDs, identity sourced from validated token claims, session bound to user, mismatches rejected (401/403), explicit TTL.
- **Evidence:** `server.py:23` (`FastMCP("bag_epl_mcp")`, no session/auth config); no auth layer in repo.
- **Risk:** **Reduced by design** — the server exposes only public, read-only data with no per-user state, so cross-session leakage carries no confidentiality impact today. The check applies because `transport != stdio-only`; status is *partial* (relies on SDK defaults, no explicit binding).
- **Remediation:** Document the no-auth/public-data threat model as an Architecture Decision Record (why session binding is out of scope for Phase 1). If/when auth or per-user state is introduced, implement signed `user_id:session_id` binding with TTL. Until then, ensure single-instance deployment (see SCALE-002).
- **Effort:** M · **Verification:** ADR present; re-audit on auth introduction.

---

### Finding: SEC-019 — Lethal Trifecta capability assessment `[CRITICAL]` `[partial]`

- **Observed behavior:** No documented trifecta assessment exists. In practice the server holds at most **two** of the three dangerous capabilities: it is exposed to (somewhat) untrusted LLM-supplied query strings and can make external HTTP calls, but it accesses **no private data** and cannot **write/send**. It is therefore safe by construction.
- **Expected behavior:** Trifecta assessment documented in README/`docs`; each server holds ≤2 of {private-data, untrusted-content, external-comms}.
- **Evidence:** `server.py` tools are all GET-only to fixed public hosts; no private datastore.
- **Risk:** Low — exfiltration requires private data, which is absent. The gap is purely the **missing documented assessment**.
- **Remediation:** Add a short "Security model / Lethal Trifecta" subsection to README or `docs/security.md` stating the capability score (2/3) and rationale.
- **Effort:** S · **Verification:** section present; re-audit.

---

### Finding: ARCH-009 — Tool Annotations `[HIGH]` `[fail]`

- **Observed behavior:** All six tools are declared with a bare `@mcp.tool()` (`server.py:184, 219, 260, 295, 329, 400`) — **no annotations**. Every tool is read-only and five make external HTTP calls, but neither `readOnlyHint=True` nor `openWorldHint=True` is set.
- **Expected behavior:** Explicit annotations on every tool; `readOnlyHint: true` for non-mutating tools; `openWorldHint: true` for tools hitting external systems.
- **Evidence:** `server.py:184/219/260/295/329/400`.
- **Risk:** Without `readOnlyHint`, hosts treat each call as potentially dangerous → confirmation fatigue, undermining real safety prompts. Easy, high-value fix for a fully read-only server.
- **Remediation:** Annotate each tool, e.g. `@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))` (external tools); `epl_server_info` / `epl_rechtskontext` may set `openWorldHint=False`.
- **Effort:** S · **Verification:** inspect tool manifest for annotations.

---

### Finding: SDK-004 — CORS `Mcp-Session-Id` exposure `[HIGH]` `[fail]`

- **Observed behavior:** No CORS middleware is configured (consistent with HTTP transport being unimplemented). Browser-based `claude.ai` clients (the documented SSE use case) cannot read the `Mcp-Session-Id` response header.
- **Expected:** CORS `expose_headers` includes `Mcp-Session-Id`; request allowlist includes it; explicit origin list (no wildcard with credentials).
- **Evidence:** no CORS config in `src/`; README "SSE for browser access".
- **Risk:** Stateful HTTP sessions break in browsers while server-side tests pass — silent failure for the advertised cloud path.
- **Remediation:** When wiring SCALE-001, add Starlette `CORSMiddleware` with `expose_headers=["Mcp-Session-Id"]` and an explicit origin allowlist (e.g. `https://claude.ai`).
- **Effort:** S · **Verification:** browser client reads session header.

---

### Finding: SEC-007 — Container-Sandboxing `[HIGH]` `[fail]`

- **Observed:** No `Dockerfile`, `render.yaml`, or any container/runtime hardening (non-root UID, dropped capabilities, seccomp, read-only rootfs) exists. Render builds run as default user.
- **Expected:** Non-root user (UID ≥ 10000), dropped Linux capabilities, seccomp `RuntimeDefault`, read-only rootfs.
- **Evidence:** repo file list (no `Dockerfile`/deploy config).
- **Risk:** A compromise of the process runs with default privileges; no isolation layer. Lower impact given read-only/no-secrets, but the check applies for Render deployment.
- **Remediation:** Add a multi-stage `Dockerfile` (covers SCALE-004 too) with `USER nobody`, `HEALTHCHECK`, slim base; document Render container settings and resource limits (SCALE-006).
- **Effort:** M · **Verification:** `docker run` as non-root; image < 200 MB.

---

### Finding: SDK-001 — FastMCP lifespan + pooled httpx client `[HIGH]` `[partial]`

- **Observed:** No `lifespan` is passed to `FastMCP` (`server.py:23`). `_http_get` opens and closes a **new** `httpx.AsyncClient` on every call (`server.py:49-50`). Cleanup is handled (the `async with` closes the client), so 1 of 4 criteria is met — hence *partial*.
- **Expected:** `@asynccontextmanager` lifespan creating a shared, pooled `AsyncClient` injected via context, torn down on shutdown.
- **Evidence:** `server.py:23, 47-50`.
- **Risk:** Per-request connection setup adds latency and forfeits connection reuse/keep-alive to `sl.bag.admin.ch`; under load this is wasteful.
- **Remediation:** Add a lifespan that initializes one `AsyncClient(timeout=HTTP_TIMEOUT)` and store it on the app context; reuse it in `_http_get`.
- **Effort:** S · **Verification:** single client instantiated at startup; tests still green.

---

### Finding: OBS-001 / OBS-002 — Error handling to the LLM `[HIGH]` `[partial]`

- **Observed:** `_handle_error` (`server.py:53-70`) returns a German error **string**, which tools return as a *normal* (success) tool result (e.g. `server.py:216`) — it is never surfaced as `isError`. `FastMCP(...)` is created without `mask_error_details=True` (`server.py:23`). The generic branch returns `f"{prefix}{type(error).__name__}: {error}"` (`server.py:70`), which can echo raw exception text. No tests distinguish protocol vs. execution error paths.
- **Expected:** Execution errors via `isError: true`; protocol errors via JSON-RPC codes; `mask_error_details=True`; no internal detail leakage; tests for both paths.
- **Evidence:** `server.py:23, 53-70, 216, 257, 292, 326, 397`; `tests/test_server.py` (`TestHandleError` checks strings, not `isError`).
- **Risk:** The LLM may interpret an error string as valid content; the generic branch can leak exception internals.
- **Remediation:** Set `mask_error_details=True`; raise typed errors (or return an `isError` structured result) instead of plain strings; drop `{error}` repr from the generic branch; add a protocol-error test.
- **Effort:** S–M · **Verification:** triggered error returns `isError`; no exception text reaches output.

---

### Concise findings (remaining high & medium)

| ID | Observed → Expected (one-line) | Remediation | Effort |
|----|--------------------------------|-------------|:---:|
| ARCH-004 | Transport-agnostic handlers ✓, but no env-var transport selection and config via module-level constants (`server.py:26-36`) → Settings object + env transport | Pydantic-Settings + `MCP_TRANSPORT` | M |
| SEC-005 | No DNS pinning before GET (`server.py:47-50`) → resolve once, pin IP, keep SNI/Host | Add to egress helper | M |
| SEC-018 | `extra="forbid"`+bounds ✓ but no `strict=True` (`server.py:115,133,147,170`) → add strict | `ConfigDict(strict=True, …)` | S |
| SEC-021 | Hosts hardcoded but no `frozenset` allow-list / network egress policy → explicit allow-list + doc | `ALLOWED_HOSTS = frozenset({...})` | M |
| SEC-022 | Consistent `epl_` prefix ✓ but no `server__tool` convention / no SHA-256 tool-def snapshot in release | hash snapshot in `publish.yml` | S |
| SCALE-002 | No sticky sessions / shared session store / TTL → document single-instance or add Redis affinity | doc + LB config | M |
| SCALE-003 | No edge-LB `Mcp-Session-Id` routing → only needed for >1 replica; document constraint | doc / HAProxy stick-table | M |
| OPS-001 | Mocked+live split, marker, CI `-m "not live"` ✓; but single `tests/` file, <5 tests/tool, 1 live test total → add per-tool live tests | expand tests | M |
| OPS-003 | Phase 1 declared ✓, tools read-only ✓; no dedicated roadmap file with sign-off gates → add `docs/ROADMAP.md` | roadmap file | S |
| SCALE-004 | No `Dockerfile` → add multi-stage slim image, `USER nobody`, `HEALTHCHECK` | Dockerfile | M |
| OBS-003 | No logging at all → add structlog JSON, ≥4 RFC-5424 levels, per-call context | structlog | S |
| OBS-006 | No tracing → optional OTel spans per tool-call for cloud | OTel SDK | M |
| ARCH-002 | Descriptions rich (>100 chars) but no explicit `<use_case>` tags in ≥80% → add tags | edit docstrings | S |
| ARCH-003 | SL fallback gives a link but no `match_type` field / fuzzy suggestions (`server.py:100-108`) → add `match_type` | response field | S |
| ARCH-012 | `protocolVersion` not pinned; no Dependabot; no protocol-version/update policy in README | pin + `dependabot.yml` | S |
| SDK-002 | Tools return `str` (`server.py:185…`), not BaseModel/TypedDict envelope w/ `source`/`provenance`/`results`/`count` | structured returns | M |
| SDK-003 | Long (≤30 s) HTTP ops lack `ctx: Context`/progress/`ctx.info` logging | add Context param | S |
| SEC-014 | No gateway tool allow-list / default-deny (cloud) → low impact for single public server; document | config/doc | M |
| SEC-015 | No pre-flight tool-poisoning detection (cloud) → low impact (own tools); note in security doc | doc | M |
| SCALE-006 | No container resource limits (mem/CPU/FDs) → set on Render/Docker | deploy config | S |
| CH-004 | Sources linked in README/markdown but no structured `source`/licence field; OGD-CH/CC BY 4.0 not stated → add `source`+licence to outputs and README | add field + README licence row | S |
| OPS-002 | Bilingual README ✓, anchor query ✓, limits ✓, CHANGELOG ✓; "Architecture" is a phase block, not a component **data-flow** diagram → add Mermaid/ASCII data-flow | add diagram | S |

---

## 6. Remediation Plan (prioritized)

**Sprint 1 — unblock cloud + quick critical wins (mostly S):**
1. **SCALE-001** — implement `MCP_TRANSPORT` transport selection; fix README command. *(unblocks SEC-016, SDK-004, SCALE-002/003)*
2. **ARCH-009** — add `readOnlyHint`/`openWorldHint` to all tools. *(S, high value)*
3. **SEC-016** — `MCP_HOST` default `127.0.0.1`; `0.0.0.0` only in container.
4. **SEC-004 + SEC-005 + SEC-021** — one egress helper: HTTPS assert + IP blocklist + DNS pin + `frozenset` host allow-list.
5. **SEC-019 + SEC-009** — document security/threat model (trifecta 2/3; no-auth/public-data ADR).
6. **OBS-002** — `mask_error_details=True`; stop leaking exception repr.

**Sprint 2 — robustness & deployment (M):**
7. **SEC-007 + SCALE-004 + SCALE-006** — multi-stage `Dockerfile` (non-root, healthcheck) + Render resource limits.
8. **SDK-004 + OBS-001** — CORS `Mcp-Session-Id` exposure + `isError` error semantics + protocol-error test.
9. **SDK-001** — lifespan-pooled httpx client.
10. **OBS-003** — structured logging.

**Backlog — polish (S/M):**
11. **SDK-002 / SDK-003 / ARCH-002 / ARCH-003 / ARCH-012 / OPS-001 / OPS-002 / OPS-003 / CH-004 / SEC-014 / SEC-015 / SEC-018 / SEC-022 / OBS-006.**

**Aggregate effort:** ~6 × S + ~10 × M ≈ 2 focused sprints to reach cloud-production-ready.

---

## 7. Non-Applicable Categories (24 checks excluded)

- **All OAuth/auth checks** (SEC-001/002/003/010/011/012, ARCH-... ) — `auth_model == none`.
- **SEC-023, OBS-005, CH-001/002/007/008** — `data_class == "Public Open Data"` (no PII/admin data ⇒ no DLP, SIEM, residency, breach-notification duty).
- **CH-003/005/006** — no Volksschule / Stadt Zürich / Schulamt context.
- **SCALE-005** — no enterprise/Stadt-Zürich gateway context.
- **All HITL** (001–005) — no sampling, no sequential thinking, `write_capable == false`.
- **ARCH-010 / HITL-005** — `write_capable == false` (no write/destructive tools, no idempotency or confirmation needed).
- **SEC-017** — no filesystem tools.
- **SDK-005** — Python, not TypeScript.

These exclusions are the single biggest reason the server's risk surface is small: no auth, no PII, no writes, no filesystem.

---

## 8. Audit Metadata

| Field | Value |
|-------|-------|
| Skill | mcp-audit-skill |
| Skill version | 1.0.0 |
| Catalog | 68 checks / 8 categories (`malkreide/mcp-audit-skill@main`) |
| Methodology | Profile → applicability filter → severity-descending execution → evidence-based findings → report from `summary.json` |
| Audit date | 2026-06-01 |
| Audited ref | branch `claude/cool-rubin-0gH4z` |
| Verification modes | code review + automated grep (no live runtime test executed) |
| Production-ready | **false** |
| Recommended re-audit | after Sprint 1, and on any auth/write/transport change |

---

## 9. Sign-Off

- [x] Profile complete and validated
- [x] Applicability report generated (24 N/A documented in §7)
- [x] Applicable checks executed in severity order
- [x] Each failed/partial check has ≥1 finding with `file:line` evidence
- [x] Report numbers derived from `summary.json`
- [ ] Production-ready release proposal — **skipped** (`production_ready == false`)
- [ ] Stakeholder acceptance (owner: @malkreide)
