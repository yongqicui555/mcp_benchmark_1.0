## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-003` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Single-instance Render/Docker deployment documented as the target

### Gaps vs. Pass Criteria

- No edge-LB Mcp-Session-Id routing / stick-table config documented; same horizontal-scaling concern as SCALE-002 (operator-scope, currently single-instance)

### Expected Behavior

Edge LB reads Mcp-Session-Id and routes via a stick-table/hash with adequate capacity and an explicit TTL; failover tested so sessions are not silently re-homed without shared state.

### Risk Description

Same horizontal-scaling failure mode as SCALE-002, viewed from the LB layer.

### Remediation

When moving beyond single-instance: configure HAProxy/Nginx/Ingress to hash on `Mcp-Session-Id` with TTL ~= session TTL, and test backend-failover behaviour. Until then, document that the deployment is single-instance.

### Effort Estimate

**M**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-003` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.
