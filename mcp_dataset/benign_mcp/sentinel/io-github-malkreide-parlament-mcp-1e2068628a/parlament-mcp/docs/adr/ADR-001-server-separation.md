# ADR-001: Read-only-Server, keine Lethal-Trifecta-Kombination

## Status
Akzeptiert, 2026-05-30

## Kontext
Der `mcp-audit-skill`-Check SEC-019 verlangt eine dokumentierte Bewertung der
«Lethal Trifecta» (private Daten + untrusted Content + externe Kommunikation).

## Entscheidung
`parlament-mcp` bleibt ein **reiner Read-only-Server** auf Public Open Data.
Er vereint maximal **eine** der drei Trifecta-Fähigkeiten (Lesen einer festen,
vertrauenswürdigen API) und erhält **keine** Schreib-/Sende-Fähigkeit.

| Fähigkeit | Status |
|---|:--:|
| Zugriff auf private Daten | ❌ (nur Public Open Data) |
| Untrusted Content | ⚠️ begrenzt (feste Curia-Vista-API) |
| Externe Kommunikation / Write | ❌ (read-only) |

## Konsequenzen
- Datenexfiltration via Prompt-Injection ist strukturell ausgeschlossen.
- Sollte je eine schreibende/sendende Funktion gewünscht sein (z.B. Benachrichti-
  gungen), wird diese in einen **separaten** Server mit hartem Empfänger-Allow-List
  ausgelagert — nicht in diesen Server integriert. Siehe `docs/roadmap.md` Phase 3.
