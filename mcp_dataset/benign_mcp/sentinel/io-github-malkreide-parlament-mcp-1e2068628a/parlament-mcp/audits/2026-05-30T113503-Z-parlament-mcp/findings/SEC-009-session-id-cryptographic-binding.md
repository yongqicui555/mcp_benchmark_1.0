## Finding: SEC-009 — Session-ID Cryptographic Binding

**Severity:** critical
**Status:** accepted-risk (dokumentiert)
**Server:** parlament-mcp
**Verification-Status:** partial

### Observed Behavior / Evidence
- HTTP-Session-IDs vom SDK kryptografisch sicher generiert; Posture dokumentiert (docs/security.md)

### Gaps vs. Best-Practice
- Kein User-gebundenes Session-Binding möglich ohne Auth (No-Auth-Profil); wird in Phase 3 mit OAuth verpflichtend (docs/roadmap.md)

### Remediation
Bewusst zurückgestellt — siehe docs/roadmap.md (Phase 3) bzw. ADR. Kein
Blocker für die aktuelle read-only/no-auth Phase-1-Anbindung.

### Effort Estimate
M (an Auth/Phase-3 gekoppelt)
