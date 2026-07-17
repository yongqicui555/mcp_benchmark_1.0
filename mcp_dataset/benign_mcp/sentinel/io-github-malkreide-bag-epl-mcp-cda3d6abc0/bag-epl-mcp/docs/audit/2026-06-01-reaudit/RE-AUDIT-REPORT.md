# MCP-Server Re-Audit — `bag-epl-mcp`

> Re-audit with the [mcp-audit-skill](https://github.com/malkreide/mcp-audit-skill) (v1.0.0, 68-check catalog) after Phase 1–3 remediation (PRs #2, #3, #4).
> Baseline: [`../2026-06-01/AUDIT-REPORT.md`](../2026-06-01/AUDIT-REPORT.md). All numbers derive from [`summary.json`](./summary.json).
>
> **Follow-up (same day):** a post-re-audit remediation closed **SDK-003**, **OBS-003**, **SEC-005** (DNS-pinning), **SDK-002** (typed output schemas + structuredContent) and **OBS-006** (tracing on by default), and added a sticky-session config for SCALE-002/003 — see §9. The headline figures below reflect that follow-up: **39 pass / 5 partial / 0 fail**.

---

## 1. Executive Summary

After three remediation phases plus a same-day follow-up, the server moved from **11 pass / 26 partial / 7 fail** to **39 pass / 5 partial / 0 fail** across the 44 applicable checks. **All 7 failed checks and 21 partials were resolved**, including the advertised-but-unimplemented cloud transport (the baseline's headline defect) and 3 of the 4 critical items.

**Production-readiness: `true`** for the documented **Phase-1, single-instance** deployment. There are **no failed checks** and no unaddressed criticals. The single remaining critical (SEC-009) is a **documented accepted-risk** (no authentication, public read-only data). The other 9 partials are either documented accepted-risk or deferred to Phase 2 / multi-instance scaling — none block a Phase-1 release.

---

## 2. Score Delta vs. Baseline

| Status | Baseline (2026-06-01) | Re-audit (incl. follow-up) | Δ |
|--------|:---:|:---:|:---:|
| Pass | 11 | **39** | **+28** |
| Partial | 26 | **5** | **−21** |
| Fail | 7 | **0** | **−7** |
| Findings (partial+fail) | 33 | **5** | **−28** |

| Findings by severity | Baseline | Re-audit |
|---|:---:|:---:|
| Critical | 4 | **1** (accepted-risk) |
| High | 16 | **2** (deferred multi-instance) |
| Medium | 13 | **2** (accepted-risk) |
| Low | 0 | 0 |

Profile unchanged: dual transport · no auth · Public Open Data · read-only · Render + local-stdio.

---

## 3. Resolved Findings (23)

| ID | Title | Baseline → Re-audit | Evidence |
|----|-------|:---:|----------|
| SCALE-001 | Streamable HTTP for cloud | fail → **pass** | `MCP_TRANSPORT` selection in `server.py`; `initialize`/`/healthz` → 200 (smoke-tested) |
| ARCH-009 | Tool annotations | fail → **pass** | `ToolAnnotations(readOnlyHint=True, …)` on all 6 tools |
| SDK-004 | CORS `Mcp-Session-Id` | fail → **pass** | `expose_headers=["Mcp-Session-Id"]` + explicit origin list |
| SEC-007 | Container sandboxing | fail → **pass** | `Dockerfile` non-root UID 10001 + `HEALTHCHECK`; runtime hardening in `docs/SECURITY.md` |
| SCALE-004 | Multi-stage container | fail → **pass** | 2-stage slim `Dockerfile`, non-root, healthcheck |
| OBS-003 | Structured logging | fail → **partial** | structlog JSON → stderr, ≥4 RFC-5424 levels (correlation_id pending) |
| OBS-006 | OpenTelemetry | fail → **partial** | `[otel]` extra + `MCP_OTEL_ENABLED` auto-instrumentation (opt-in) |
| SEC-004 | SSRF prevention | partial → **pass** | `_assert_safe_url`: HTTPS + allow-list + resolved-IP blocklist |
| SEC-016 | 0.0.0.0 binding | partial → **pass** | `MCP_HOST` default `127.0.0.1`; `0.0.0.0` only in container |
| SEC-018 | Input validation strict | partial → **pass** | `ConfigDict(strict=True)` on all 4 input models (+ tests) |
| SEC-019 | Lethal trifecta | partial → **pass** | Documented 2/3 assessment in `docs/SECURITY.md` |
| SEC-021 | Egress allow-list | partial → **pass** | Immutable `ALLOWED_HOSTS` frozenset; network layer documented |
| SEC-022 | Tool hash-pinning | partial → **pass** | `scripts/snapshot_tool_hashes.py` + release-workflow step; `epl_` namespace |
| SCALE-006 | Resource limits | partial → **pass** | `render.yaml` plan + documented `docker run` mem/cpu/ulimit |
| OBS-001 | Protocol vs execution errors | partial → **pass** | Tool failures raised as `ToolError` (isError); no stack traces |
| OBS-002 | Mask error details | partial → **pass** | Generic path no longer leaks repr; full detail logged server-side |
| ARCH-002 | Use-case tags | partial → **pass** | `<use_case>` in all 6 docstrings (100%) |
| ARCH-003 | Not-found / match_type | partial → **pass** | `match_type` (exact/none) + actionable guidance |
| ARCH-004 | IoC / transport-agnostic | partial → **pass** | `pydantic-settings` `ServerSettings`; env transport selection |
| ARCH-012 | protocolVersion + SDK discipline | partial → **pass** | `PROTOCOL_VERSION` + policy + `dependabot.yml` |
| SDK-001 | Lifespan + pooled client | partial → **pass** | `@asynccontextmanager` lifespan; pooled `httpx.AsyncClient` |
| CH-004 | OGD-CH licence | partial → **pass** | `provenance` block + CC BY 4.0 footer; README sources |
| OPS-001/002/003 | Test split / docs / roadmap | partial → **pass** | `test_unit.py`+`test_live.py`; data-flow diagram; `docs/ROADMAP.md` |

---

## 4. Remaining Findings (5) — none blocking Phase 1

| ID | Sev | Status | Disposition | Note |
|----|----|--------|-------------|------|
| SEC-009 | critical | partial | **accepted-risk** | No auth → no session binding by design (public read-only, single instance). Documented in `docs/SECURITY.md §3`. Re-introduce signed binding if auth is ever added. |
| SCALE-002 | high | partial | **deferred (multi-instance)** | Sticky sessions only needed when scaled; reference config in `deploy/haproxy.cfg`, full pass needs a real multi-instance failover test. |
| SCALE-003 | high | partial | **deferred (multi-instance)** | Edge-LB session routing only for >1 replica; `deploy/haproxy.cfg` documents the routing + TTL. |
| SEC-014 | medium | partial | accepted-risk | No gateway allow-list; documented (single public read-only server). |
| SEC-015 | medium | partial | accepted-risk | No pre-flight tool-poisoning detection; static own tools. |

> **SDK-003**, **OBS-003**, **SEC-005**, **SDK-002** and **OBS-006** were closed in a same-day follow-up (§9).

**Recommended next steps (optional, non-blocking):** implement DNS-pinning (SEC-005) and `ctx`-based per-call logging (SDK-003 + OBS-003) in a small follow-up; address SCALE-002/003 only when moving to multi-instance; configure OTel at deploy time if tracing is desired.

---

## 5. Non-Applicable Categories (24) — unchanged

All OAuth/auth checks (`auth_model == none`), PII/DSG/residency/SIEM/DLP/breach checks (`Public Open Data`), Volksschule/Stadt-Zürich/Schulamt/enterprise context, all HITL (no sampling, read-only), `write_capable == false` (ARCH-010, HITL-005), filesystem (SEC-017), TypeScript (SDK-005). See baseline report §7.

---

## 6. Release Proposal (Step 7 — requires confirmation)

`production_ready == true`, so a release is proposed. **Not executed** — awaiting explicit confirmation; nothing is tagged or pushed automatically.

| Field | Value |
|-------|-------|
| Current version | `0.1.0` |
| Recommended | **`0.2.0`** (minor) |
| Rationale | Backward-compatible feature additions (env-based HTTP transport, security hardening, structured envelopes, Docker, structured logging). No breaking changes to existing tool signatures. |
| Action on confirm | Bump `pyproject.toml` + `__init__`/`epl_server_info` version, move the CHANGELOG `[Unreleased]` block to `[0.2.0] - <date>`, create a `v0.2.0` git tag + GitHub release draft (which triggers the PyPI publish workflow + tool-hash snapshot). |

> Scope note: the readiness verdict covers **Phase-1, single-instance** deployment as documented in `docs/SECURITY.md` and `docs/ROADMAP.md`. Horizontal scaling requires SCALE-002/003; adding authentication requires revisiting SEC-009.

---

## 7. Audit Metadata

| Field | Value |
|-------|-------|
| Skill / catalog | mcp-audit-skill v1.0.0 / 68 checks, 8 categories |
| Audit date | 2026-06-01 (re-audit) |
| Audited ref | `main` (PRs #2/#3/#4 merged) |
| Verification | code review + automated grep + `pytest -m "not live"` (49 pass) + HTTP smoke test |
| Production-ready | **true** (Phase-1 single-instance) |
| Next re-audit | on auth/write/transport change, on move to multi-instance, or before Phase 2 |

## 9. Follow-up Remediation (post-re-audit, same day)

After the re-audit, the cleanly-fixable open items were addressed in a follow-up PR (the architectural / accepted-risk / multi-instance items were intentionally left, see their dispositions in §4):

| ID | Sev | Before → After | Change |
|----|----|:---:|--------|
| SDK-003 | medium | partial → **pass** | `ctx: Context` injected into all 6 tools; per-call context bound to the structured logger. |
| OBS-003 | medium | partial → **pass** | Per-tool-call bound logging context (`tool`, `correlation_id`, `request_id`/`client_id` when a session is active). |
| SEC-005 | high | partial → **pass** | DNS-pinned transport (`_PinnedNetworkBackend`): single resolution, IP pinned for the TCP connection, TLS/cert still validated against the hostname. Verified end-to-end against a real host. |
| SDK-002 | medium | partial → **pass** | All 6 tools now declare typed Pydantic output schemas and return `structuredContent` **plus** the curated Markdown in `content` (hybrid via `CallToolResult` — no UX loss). |
| OBS-006 | medium | partial → **pass** | OpenTelemetry on by default (`MCP_OTEL_ENABLED=0` to disable); silent no-op when the `[otel]` extra isn't installed, so base installs are unaffected and stdout stays clean. |
| SCALE-002/003 | high | partial (improved) | Reference HAProxy sticky-session config (`deploy/haproxy.cfg`); full pass needs a real multi-instance failover test. |

**Updated totals: 39 pass / 5 partial / 0 fail.** Remaining 5 partials: SEC-009 (critical, accepted-risk), SCALE-002 / SCALE-003 (high, deferred — multi-instance), SEC-014 / SEC-015 (medium, accepted-risk). None block a Phase-1 release.

## 8. Sign-Off

- [x] Profile re-validated (unchanged)
- [x] Applicability re-confirmed (24 N/A)
- [x] All applicable checks re-executed in severity order
- [x] Each remaining partial has a documented disposition (accepted-risk / deferred / by-design / open)
- [x] Numbers derived from `summary.json`
- [x] Release proposal prepared (v0.2.0) — **pending user confirmation, not executed**
- [ ] Stakeholder acceptance (owner: @malkreide)
