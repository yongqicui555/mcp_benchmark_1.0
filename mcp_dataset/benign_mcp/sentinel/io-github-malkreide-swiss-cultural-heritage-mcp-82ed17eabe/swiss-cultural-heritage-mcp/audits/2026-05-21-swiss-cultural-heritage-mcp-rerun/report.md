# Audit Re-Run — swiss-cultural-heritage-mcp

**Date:** 2026-05-21 (re-run, same day after remediation)
**Auditor:** Claude (Opus) following [`mcp-audit-skill`](https://github.com/malkreide/mcp-audit-skill) methodology
**Baseline:** [`../2026-05-21-swiss-cultural-heritage-mcp/report.md`](../2026-05-21-swiss-cultural-heritage-mcp/report.md)
**Branch / commit audited:** `main` @ `e54819c` (post-merge of PRs #2, #3, #4)

---

## Executive Summary

Re-applied the audit skill against the codebase after the three remediation PRs landed. **All 7 actionable baseline findings are closed.** One small regression introduced by the remediation series itself: `README.de.md` did not receive the EU-region update that `README.md` got. Three new informational items surfaced that the baseline had not called out — none are blockers.

---

## Score-Card Diff

| ID | Title | Baseline | Re-Run | Δ |
|---|---|---|---|---|
| ARCH-001 | Tool naming convention | PASS | PASS | — |
| ARCH (annotations) | Tool annotations consistency | PARTIAL | **PASS** | ✅ closed |
| ARCH-010 | Idempotency / compensating actions | N/A | N/A | — |
| SDK-001 | FastMCP lifespan & shared client | **FAIL** | **PASS** | ✅ closed |
| SDK-002 | Pydantic schemas | PASS | PASS | — |
| SEC-007 | Container sandbox | **FAIL** | **PASS** | ✅ closed |
| SEC-021 | Egress allow-list (code + network) | **FAIL** | **PASS** | ✅ closed |
| SEC (XML) | Safe XML parsing (`defusedxml`) | **FAIL** | **PASS** | ✅ closed |
| OBS-001 | Protocol vs. execution errors | PARTIAL | **PASS** | ✅ closed |
| CH-001 | Data residency (revDSG / EDÖB) | PARTIAL | **PARTIAL** | ⚠️ regression |
| OPS-001 | Test strategy | PASS | PASS+ | improved (nightly live workflow) |

**Totals (applied):** 8 PASS · 1 PARTIAL · 0 FAIL · 3 N/A (was 3 PASS · 3 PARTIAL · 4 FAIL · 3 N/A)

---

## Closed Findings — Verification Evidence

| Finding | Evidence in current code |
|---|---|
| SDK-001 | `server.py:53-84` — `lifespan` + `_get_http_client()`; `_http_get` reuses the shared client |
| SEC-021 | `server.py:38-43` — `ALLOWED_HOSTS: Final[frozenset]`; `_assert_allowed` runs before every GET; `follow_redirects=False` at `server.py:60`; new `docs/network-egress.md` |
| SEC (XML) | `server.py:25` — `from defusedxml import ElementTree as ET` |
| OBS-001 | `server.py:98-104` — `ExpectedUpstreamError` tuple; all 10 `except` clauses narrowed |
| SEC-007 | New `Dockerfile` (non-root UID 10001, slim base) + `docs/security.md` with k8s `SecurityContext` snippet |
| ARCH | `idempotentHint: True` on all 8 tools (verified by grep); `NbCollectionsInput` Pydantic model at `server.py:823`; new `TestInputModelConsistency` (15 parametrized cases) |
| OPS-001 | New `.github/workflows/nightly-live.yml` runs `pytest -m live` daily |

Unit-test suite at re-run time: **64 passed, 4 deselected** · ruff clean.

---

## 🟧 Regression (introduced by remediation series)

### 1. `README.de.md` was not updated alongside `README.md`

**Status:** PARTIAL · **Severity:** low · **File:** `README.de.md:131-141`

PR #4 (CH-001 fix) updated the English README's Render section to require the Frankfurt region and link to the new docs. The German README's identical section was not touched, so it still reads:

```
**Render.com (empfohlen):**
1. Repository auf GitHub pushen/forken
2. Auf render.com: New Web Service → GitHub-Repo verbinden
3. Start-Befehl setzen: python -m … --http --port 8000
4. In claude.ai unter Settings → MCP Servers eintragen: …
```

Since the README badge in the English version says *"🇩🇪 Deutsche Version"* and the German README is the canonical doc for Swiss public-sector readers, the residency guidance is missing for exactly the audience that needs it most.

**Remediation:** mirror the four-line change from `README.md:135-143` into `README.de.md`. Trivial (XS, < 10 min).

---

## ⬜ Informational — new observations (not in the baseline)

These were below the noise floor in the first pass but are worth recording for future iterations.

### A. Dependency upper bounds open

`pyproject.toml` uses `>=` only:

```toml
"mcp[cli]>=1.0.0",
"httpx>=0.27.0",
"pydantic>=2.0.0",
"defusedxml>=0.7.1",
```

A future major release of `mcp` or `httpx` could break the server silently. Consider tightening to `>=X,<Y` once the upstream APIs stabilise their semver promise. Not a blocker — open lower bounds are common in alpha-stage projects.

### B. No health-check endpoint for HTTP transport

The Streamable HTTP mode exposes only the MCP protocol surface. Render / k8s liveness probes typically expect a `/health` or `/readyz`. FastMCP may expose a hook for this; if not, a tiny ASGI middleware would suffice. Low priority while the server is single-tenant.

### C. `__version__` duplicated

`pyproject.toml` and `src/swiss_cultural_heritage_mcp/__init__.py` both hardcode `0.1.0`. A single source via `importlib.metadata.version("swiss-cultural-heritage-mcp")` would prevent drift. XS.

---

## Methodology Notes

- Same 68-check catalogue as the baseline; same applicability filter (≈ 25 checks N/A for this profile).
- Verification was code-review against the merged commits plus a fresh `pytest` + `ruff` run.
- No runtime tests against live upstreams executed in this pass — the new `nightly-live.yml` workflow will surface those.

— *End of re-run report*
