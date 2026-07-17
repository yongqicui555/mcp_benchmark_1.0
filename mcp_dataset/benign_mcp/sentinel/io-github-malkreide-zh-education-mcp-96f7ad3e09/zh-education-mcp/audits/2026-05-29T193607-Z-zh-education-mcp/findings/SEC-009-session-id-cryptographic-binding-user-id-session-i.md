## Finding: SEC-009 — Session-ID Cryptographic Binding (user_id:session_id)

**Severity:** critical
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-009
**PDF-Reference:** Sec 4.6

### Observed Behavior / Evidence
- Kein eigenes Session-Handling — Session-IDs werden an den FastMCP-streamable-http-Stack delegiert (secrets-basiert)
- Datenklasse Public Open Data, read-only ⇒ Impact eines Session-Leaks minimal (nur öffentliche Daten)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine kryptografische Bindung Session-ID↔User, da auth_model=none (keine User-Identität vorhanden)
- Bei öffentlicher Cloud-Exposition ohne Auth: Endpoint für jeden erreichbar — akzeptabel nur für öffentliche read-only Daten, sonst Auth/Netzkontrolle nötig

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)
