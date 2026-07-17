## Finding: SEC-018 — Input-Validation an Tool-Boundaries

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-018
**Verification-Status:** partial

### Observed Behavior / Evidence
- Alle Tools haben Pydantic-v2-Input-Modelle mit extra='forbid' (server.py:151,206,217,250,269,279)
- Numerische Felder mit ge/le-Constraints (limit ge=1/le=100, offset ge=0); String max_length; Datum mit Whitelist-Pattern (server.py:184)

### Gaps vs. Best-Practice
- model_config setzt strict=True NICHT → Pydantic-Coercion ('1'→1) aktiv
- Keine Tests gegen Input-Edge-Cases (zu lang, out-of-range, unbekannte Felder)

### Remediation
Siehe Check `SEC-018` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S
