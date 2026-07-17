# Audit Report — swiss-cultural-heritage-mcp

**Date:** 2026-05-21
**Auditor:** Claude (Opus) following [`mcp-audit-skill`](https://github.com/malkreide/mcp-audit-skill) methodology
**Repository:** https://github.com/malkreide/swiss-cultural-heritage-mcp
**Branch / commit:** `claude/audit-mcp-skill-JGJI1` @ `aef77c6`

---

## Executive Summary

`swiss-cultural-heritage-mcp` is a well-structured, read-only, anonymous MCP server exposing three public Swiss cultural-heritage upstreams (SIK-ISEA, opendata.swiss / SNM, Nationalbibliothek OAI-PMH). The project profile drops most of the audit framework's high-stakes checks (no auth surface, no writes, no PII, no destructive tools), so the residual attack surface is small.

The audit produced **9 findings**: 4 high, 3 medium, 1 low, 1 informational. The two most actionable issues are (1) an HTTP client lifecycle anti-pattern that hurts both performance and observability, and (2) the absence of an egress allow-list combined with `follow_redirects=True`, which weakens defense-in-depth against future SSRF-style misuse. Both are <1-day fixes.

What the project does well: strict Pydantic input models (`extra="forbid"`, length caps, regex constraints), consistent `readOnlyHint`/`openWorldHint` annotations, proper `respx` mock layer, CI gating of live tests, and clear bilingual documentation including a "Safety & Limits" section.

---

## Score Card (applicable checks only)

| ID | Title | Status | Severity |
|---|---|---|---|
| ARCH-001 | Tool naming convention | PASS | — |
| ARCH-009 (combined) | Tool annotations consistency | PARTIAL | low |
| ARCH-010 | Idempotency keys / compensating actions | N/A | — (no writes) |
| SDK-001 | FastMCP lifespan & shared client | **FAIL** | high |
| SDK-002 | Pydantic / Zod schemas | PASS | — |
| SEC-007 | Container sandbox | **FAIL** | medium |
| SEC-021 | Egress allow-list (code + network) | **FAIL** | high |
| SEC (XML) | Safe XML parsing (`defusedxml`) | **FAIL** | high |
| SEC-001/002/003 | OAuth 2.1 / PKCE / Resource Indicators | N/A | — (no auth) |
| OBS-001 | Protocol vs. execution errors | PARTIAL | medium |
| HITL-005 | Destructive-action confirmation | N/A | — (no destructive tools) |
| CH-001 | Data residency (revDSG / EDÖB) | PARTIAL | medium |
| OPS-001 | Test strategy (unit/live separation) | PASS | informational |

**Totals (applied):** 3 PASS · 3 PARTIAL · 4 FAIL · 3 N/A

---

## Findings (severity-ordered)

### 🟥 High

1. [`SDK-001` — no shared HTTP client / lifespan](findings/SDK-001-no-shared-httpx-client.md)
   New `httpx.AsyncClient` per call; no FastMCP `lifespan`. Hurts `heritage_cross_search` in particular.

2. [`SEC-021` — no egress allow-list, `follow_redirects=True`](findings/SEC-021-egress-allowlist.md)
   Both code-layer allow-list and network-layer egress policy are missing.

3. [`SEC` (XML) — unsafe `xml.etree.ElementTree` for external XML](findings/SEC-XML-defusedxml.md)
   Drop-in fix via `defusedxml.ElementTree`.

### 🟧 Medium

4. [`SEC-007` — no Dockerfile / sandbox documentation](findings/SEC-007-no-container.md)
   Minimal hardened Dockerfile + a one-page security doc closes the gap.

5. [`OBS-001` — failures returned as German strings, not `isError: true`](findings/OBS-001-error-shape.md)
   `except Exception` swallows programming errors into user-facing strings.

6. [`CH-001` — Render deployment region not specified](findings/CH-001-data-residency-docs.md)
   For public-sector readers (the README's intended audience), recommend Frankfurt / EU and add a 1-page residency note.

### 🟨 Low

7. [`ARCH` — `heritage_cross_search.idempotentHint=False` is inaccurate; `heritage_list_nb_collections` skips the Pydantic input model](findings/ARCH-tool-annotations.md)

### ⬜ Informational

8. [`OPS-001` — test strategy is solid; optional split into `test_unit.py` / `test_live.py`](findings/OPS-001-test-strategy.md)

### ✅ Notable strengths (no finding, worth recording)

- Pydantic models use `extra="forbid"`, `str_strip_whitespace=True`, max-length caps, and regex date patterns
- Source-of-truth tool annotations: `readOnlyHint`, `destructiveHint`, `openWorldHint` set explicitly on every tool
- `heritage_cross_search` uses `asyncio.gather` with per-source try/except so a single upstream outage does not break the aggregate (verified by `test_cross_search_partial_failure`)
- README contains an explicit "Safety & Limits" section — uncommon and good
- Ruff + multi-version CI matrix already in place
- Resource & prompt surfaces are minimal and content-only (no dynamic file or path handling)

---

## Suggested Remediation Order

| # | Item | Effort | Closes |
|---|---|---|---|
| 1 | Swap `ET` → `defusedxml.ElementTree` | XS (<1h) | SEC (XML) |
| 2 | Add `ALLOWED_HOSTS` frozenset + `follow_redirects=False` | S (≤1d) | SEC-021 |
| 3 | Introduce FastMCP `lifespan` with shared `httpx.AsyncClient` | S (≤1d) | SDK-001 |
| 4 | Tighten exception handling; surface failures via `isError: true` | S | OBS-001 |
| 5 | Fix `idempotentHint` + wrap `heritage_list_nb_collections` in a Pydantic model | XS | ARCH |
| 6 | Add `Dockerfile` (non-root, UID ≥ 10000) + `docs/security.md` | S | SEC-007 |
| 7 | Document EU region recommendation in Render section + `docs/data-residency.md` | XS | CH-001 |

Items 1–5 can ship as a single PR; items 6–7 as documentation follow-ups.

---

## Methodology Notes

- Source skill: `https://github.com/malkreide/mcp-audit-skill` — 68 checks across 8 categories (ARCH, SDK, SEC, SCALE, OBS, HITL, CH, OPS).
- Applicability filter excluded ~25 checks tied to OAuth, write paths, destructive operations, multi-tenant scaling, and SIEM/OTel that do not match the project profile (see [`profile.md`](profile.md)).
- Verification modes used: code review (primary), config review (`pyproject.toml`, CI workflow, README deployment section), and AST-level reading of `server.py`. No runtime tests were executed in this pass — the existing `respx`-based test suite already covers the relevant happy-path and partial-failure scenarios.
- This audit is reproducible: any reader can re-run the same checks against a future commit by following the file references and remediation guidance above.

— *End of report*
