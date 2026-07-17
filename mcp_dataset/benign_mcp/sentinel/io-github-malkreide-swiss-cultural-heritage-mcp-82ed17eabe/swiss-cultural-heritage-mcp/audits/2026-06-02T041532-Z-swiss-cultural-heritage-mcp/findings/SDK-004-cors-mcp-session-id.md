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
