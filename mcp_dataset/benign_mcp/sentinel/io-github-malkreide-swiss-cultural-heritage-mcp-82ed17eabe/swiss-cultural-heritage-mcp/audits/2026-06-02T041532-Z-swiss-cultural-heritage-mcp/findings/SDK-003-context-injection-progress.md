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
