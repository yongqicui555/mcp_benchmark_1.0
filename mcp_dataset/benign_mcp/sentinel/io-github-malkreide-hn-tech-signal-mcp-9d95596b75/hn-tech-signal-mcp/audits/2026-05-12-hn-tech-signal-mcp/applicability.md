# Applicability Matrix — hn-tech-signal-mcp

Profil-getriebene Auswahl gemäss `applies_when`-Klauseln aus `checks/MANIFEST.txt`
(`mcp-audit-skill` v0.5.0). Bei einem reinen Read-Only-Server ohne Auth und ohne
Personendaten fallen `HITL` weitgehend, `CH` (DSG/ISDS) vollständig und Teile
von `SEC` weg.

| Kategorie | Im Katalog | Anwendbar | Pass | Fail | Begründung Ausschluss |
|---|---:|---:|---:|---:|---|
| ARCH  | 12 | 10 | 8 | 2 | ARCH-009 (Stateful Sessions), ARCH-011 (Multi-Tenant) entfallen — stateless, single-tenant |
| SDK   |  5 |  5 | 4 | 1 | — |
| SEC   | 23 | 14 | 10 | 4 | OAuth/JWT/PII-spezifische Checks (SEC-007, -009, -012, -014, -016, -018, -020, -021, -022) entfallen mangels Auth/PII |
| SCALE |  6 |  5 | 4 | 1 | SCALE-006 (Sharding) N/A für stdio |
| OBS   |  6 |  5 | 3 | 2 | OBS-005 (Trace-Propagation Cross-Service) N/A |
| HITL  |  5 |  1 | 1 | 0 | 4× N/A — keine destruktiven oder zustandsändernden Tools |
| CH    |  8 |  0 | 0 | 0 | DSG/ISDS nicht relevant — nur öffentliche Drittland-Daten, keine Personendaten |
| OPS   |  3 |  3 | 1 | 2 | — |
| **Σ** | **68** | **43** | **31** | **12** | |

10 Findings dokumentiert (zwei Fail-Checks teilen je ein Finding mit anderem Check).
