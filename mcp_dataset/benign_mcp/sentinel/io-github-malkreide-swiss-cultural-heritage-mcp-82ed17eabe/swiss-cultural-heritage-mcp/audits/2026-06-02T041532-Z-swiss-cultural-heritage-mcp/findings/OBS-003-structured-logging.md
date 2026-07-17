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
