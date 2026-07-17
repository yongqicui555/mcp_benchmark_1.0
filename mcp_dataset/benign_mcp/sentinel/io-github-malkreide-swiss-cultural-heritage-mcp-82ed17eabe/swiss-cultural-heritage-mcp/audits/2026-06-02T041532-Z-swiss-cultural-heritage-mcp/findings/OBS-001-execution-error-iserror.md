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
