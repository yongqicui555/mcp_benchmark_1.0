# Audit Re-Run — swiss-cultural-heritage-mcp

**Date:** 2026-06-02 (re-run, same day after the remediation series)
**Auditor:** Claude (Opus) following [`mcp-audit-skill`](https://github.com/malkreide/mcp-audit-skill) methodology
**Baseline:** [`../2026-06-02T041532-Z-swiss-cultural-heritage-mcp/audit-report.md`](../2026-06-02T041532-Z-swiss-cultural-heritage-mcp/audit-report.md)
**Branch / commit audited:** `main` @ `787dab4` (post-merge of PRs #19–#30)

> **Update (final):** this report was first written at `e9ee21b` with 3 findings
> still open (OBS-001, ARCH-004, SEC-022). Those have since been closed by PRs
> #27 / #28 / #29+#30 and the scorecard below reflects the final state.

---

## Executive Summary

Re-applied the audit against the codebase after the full remediation series landed (18 PRs). Of the **21 baseline findings**, **19 are now closed** and **2 are accepted-risk / documented-deferred** (the heavier SSRF defense-in-depth measures). **Nothing remains open.**

No regressions were introduced. The unit suite grew from the baseline to **103 passing** (4 live-gated), ruff clean, `main` green on Python 3.11/3.12/3.13. Two findings the baseline marked `partial` (SCALE-004 multistage Dockerfile/HEALTHCHECK, ARCH-011 single-file justification) were found already satisfied in `main`.

**Verdict:** every `critical`/`high`/`medium` finding is resolved or a documented accepted-risk decision. The server is in a strong posture for a read-only, anonymous, closed-allow-list Phase 1 deployment.

---

## Score-Card Diff

| ID | Category | Sev | Baseline | Re-Run | Δ |
|---|---|---|---|---|---|
| SEC-004 | SEC | critical | partial | **partial (mitigated + documented)** | ✅ HTTPS-only enforced; IP-blocklist/DNS-pin deferred w/ rationale |
| SEC-019 | SEC | critical | partial | **PASS** | ✅ lethal-trifecta assessment documented |
| ARCH-004 | ARCH | high | partial | **PASS** | ✅ single env-overridable `Settings(BaseSettings)` |
| OBS-001 | OBS | high | partial | **PASS** | ✅ handled errors raised as `ToolError` → `isError: true` |
| OBS-002 | OBS | high | fail | **PASS** | ✅ `mask_unexpected_errors` |
| OPS-003 | OPS | high | partial | **PASS** | ✅ `docs/roadmap.md` + phase declared |
| SCALE-002 | SCALE | high | partial | **PASS (documented)** | ✅ single-instance constraint in `docs/scaling.md` |
| SCALE-003 | SCALE | high | partial | **PASS (documented)** | ✅ edge-routing / affinity path documented |
| SDK-004 | SDK | high | partial | **PASS** | ✅ CORS exposes `Mcp-Session-Id` |
| SEC-005 | SEC | high | partial | **partial (documented)** | ⚠️ DNS-pinning deferred w/ trigger |
| SEC-022 | SEC | high | partial | **PASS** | ✅ tool-prompt hash pin + CI drift guard; rename deferred |
| ARCH-003 | ARCH | medium | partial | **PASS** | ✅ `match_type` + fuzzy fallback |
| ARCH-011 | ARCH | medium | partial | **PASS** | ✅ README "Single-file server" justification |
| ARCH-012 | ARCH | medium | fail | **PASS** | ✅ dependabot + protocol-version docs |
| CH-004 | CH | medium | partial | **PASS** | ✅ per-response source + licence footer |
| OBS-003 | OBS | medium | fail | **PASS** | ✅ structlog JSON to stderr |
| OBS-006 | OBS | medium | fail | **PASS** | ✅ optional OpenTelemetry tracing |
| SCALE-004 | SCALE | medium | partial | **PASS** | ✅ multistage Dockerfile + HEALTHCHECK |
| SCALE-006 | SCALE | medium | partial | **PASS (documented)** | ✅ resource-limit guidance |
| SDK-002 | SDK | medium | partial | **PASS** | ✅ typed `ResultEnvelope` + `outputSchema` |
| SDK-003 | SDK | medium | partial | **PASS** | ✅ `ctx` progress + structured warnings |

**Totals:** 19 PASS · 2 PARTIAL (accepted-risk/documented) · 0 open · 0 FAIL
**Baseline was:** 0 PASS · 17 PARTIAL · 4 FAIL.

---

## Closed Findings — Verification Evidence

| Finding | Evidence in current code (`main` @ `787dab4`) |
|---|---|
| SEC-019 | `docs/security.md` "Lethal Trifecta assessment" — at most one leg present |
| ARCH-004 | `server.py:Settings(BaseSettings)` (env prefix `MCP_`); module constants derived from `settings`; `TestSettings` |
| OBS-001 | `server.py:_raise_tool_error` — handled upstream errors raised as `ToolError` → SDK `isError: true`; `TestErrorIsFlagged` |
| OBS-002 | `server.py:mask_unexpected_errors` — full detail to stderr, generic `ToolError` to client |
| OPS-003 | `docs/roadmap.md`; "Phase 1 — read-only" stated in both READMEs |
| SCALE-002/003 | `docs/scaling.md` — single-instance constraint, `Mcp-Session-Id` session model, Variant A/B scaling path |
| SDK-004 | `server.py:build_http_app` — CORS exposes `Mcp-Session-Id`, non-wildcard origin allow-list |
| SEC-022 | `audits/tool-pins/current.json` + `_toolpins.py` (name + docstring hash); `TestToolPins` drift guard; rename deferred in `docs/security.md` |
| ARCH-003 | `ResultEnvelope.match_type` (`exact`/`fuzzy`/`none`); loosened-query retry in artists + datasets tools |
| ARCH-011 | `README.md` "Project Structure" → "Single-file server" justification |
| ARCH-012 | `.github/dependabot.yml`; "MCP Protocol Version" section in both READMEs |
| CH-004 | `server.py:_attribution` footer on every markdown response; per-source provenance in `cross_search` |
| OBS-003 | `server.py:_configure_logging` — structlog JSON→stderr; per-call `tool`/`request_id` binding |
| OBS-006 | `server.py:_init_tracing` — gated OTLP + httpx instrumentation; `mcp.tool.*` span per call |
| SCALE-004 | `Dockerfile` — `AS builder`/`AS runtime` + `HEALTHCHECK` on `/health` |
| SCALE-006 | `docs/security.md` "Resource limits" table |
| SDK-002 | `ResultEnvelope` returned in JSON mode → real structured content + `outputSchema` |
| SDK-003 | `heritage_cross_search(ctx: Context)` — `report_progress()` per source, `warning()` on failure |
| SEC-004 (HTTPS leg) | `server.py:_assert_allowed` — `scheme != "https"` rejected; `test_assert_allowed_rejects_non_https_scheme` |

Unit-test suite at re-run time: **103 passed, 4 deselected** · ruff clean · CI green on 3.11/3.12/3.13.

---

## Accepted-Risk / Documented-Deferred

| Finding | Decision | Rationale & trigger |
|---|---|---|
| SEC-004 (IP blocklist) | Deferred | The closed two-host egress allow-list + no user-controlled host already block metadata IPs; resolved-IP blocklisting is belt-and-suspenders. **Trigger:** a tool accepts a user-supplied host, or the allow-list widens. Documented in `docs/security.md` (SSRF & DNS rebinding). |
| SEC-005 (DNS pinning) | Deferred | Theoretical TOCTOU only; an attacker would need to control DNS for a Swiss-federal host. **Trigger:** same as above. Documented alongside SEC-004. |
| SEC-022 (`<server>__<tool>` rename) | Deferred | The server-identity prefix renames every tool id — breaking for client configs (major bump). The non-breaking half (tool-prompt hash pin + CI drift guard) is implemented; the rename is a documented Phase-2 decision. |

---

## Remaining Open Findings

**None.** Every baseline finding is resolved or recorded above as an explicit accepted-risk / deferred decision with a documented trigger.

---

## Conclusion

The remediation series closed every `fail` and every actionable `partial` finding. The server is structured + traceable, licence-compliant, surfaces errors as `isError`, degrades gracefully on near-miss searches, masks internal errors, is configured through a single env-overridable object, and guards its tool prompts against silent drift. The only residual items are two SSRF defense-in-depth measures, deferred by design with documented triggers while the closed two-host allow-list holds.
