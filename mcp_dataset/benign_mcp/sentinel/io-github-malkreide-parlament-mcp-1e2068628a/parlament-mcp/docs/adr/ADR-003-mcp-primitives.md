# ADR-003: MCP-Primitive — vorerst nur Tools

## Status
Akzeptiert, 2026-05-30

## Kontext
MCP kennt drei Primitive: Tools (Verben), Resources (Substantive), Prompts
(Vorlagen). Check ARCH-008 verlangt, dass die Wahl begründet wird.

## Entscheidung
`parlament-mcp` nutzt in Phase 1 **ausschliesslich Tools**. Begründung:

- Alle Abfragen sind parametrisierte Suchen/Lookups gegen eine OData-API —
  natürlich als Tools modelliert. Die read-only get_*-Tools sind zwar
  Resource-Kandidaten, aber ihre Eingaben (IDs, Filter) sind dynamisch, nicht
  als statische URI-Hierarchie navigierbar.
- **Resources** werden in Phase 2 geprüft, sobald ein stabiles URI-Schema für
  einzelne Geschäfte/Sessionen feststeht (z.B. `business://<id>`), um
  Tool-Manifest-Tokens zu sparen und Client-Caching zu ermöglichen.
- **Prompts** sind nicht relevant: die Use-Cases sind ad-hoc-Recherche, keine
  wiederkehrenden, kuratierten Workflows.

## Konsequenzen
- Tool-Budget bleibt klein (6 Tools, ARCH-006 ✓).
- Migration ausgewählter get_*-Tools zu Resources ist als Phase-2-Task in
  `docs/roadmap.md` vorgemerkt.
