## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Server tool logic is stateless; no per-tool persistent session state to lose

### Gaps vs. Pass Criteria

- No sticky-session / shared-state (Redis/Durable Objects) session affinity for Streamable HTTP, and no documented single-instance constraint or session TTL — must be addressed before horizontal scaling

### Expected Behavior

Sticky sessions on Mcp-Session-Id at the edge LB, or a shared-state session manager (Redis/Durable Objects), with an explicit session TTL — or a documented single-instance constraint.

### Risk Description

If the Render service is scaled to >1 instance without affinity, a client's follow-up request can land on an instance that does not know its session, breaking the stream.

### Remediation

For now, document the single-instance constraint and the session TTL in docs/. Before horizontal scaling, add sticky sessions on `Mcp-Session-Id` (Variant A) or a Redis session backend (Variant B).

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-002` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
