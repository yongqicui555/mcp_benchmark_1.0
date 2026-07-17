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
