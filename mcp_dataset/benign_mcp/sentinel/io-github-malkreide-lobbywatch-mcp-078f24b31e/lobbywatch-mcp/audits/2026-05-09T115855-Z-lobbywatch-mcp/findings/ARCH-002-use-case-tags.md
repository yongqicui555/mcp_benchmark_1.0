## Finding: ARCH-002 — Tool-Beschreibung mit Use-Case-Tags

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-002

### Observed Behavior

Tool-Docstrings enthalten keine strukturierten Use-Case-Tags.

### Expected Behavior

Best-Practice-Katalog (ARCH-002). Siehe checks/ARCH-002.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/server.py:147-401 — alle Docstrings beschreiben Args, keiner enthält 'Use cases:'

### Risk Description

LLM-Tool-Auswahl-Heuristik schlechter; weniger zielgenaue Routing-Entscheidung.

### Remediation

```
Use cases: Sektion am Ende jedes Docstrings, z.B.
  Use cases:
  - 'Welche IBs hat MP X?'
  - 'Show me all WBK-N Bildungs-Mandate'
```

### Effort Estimate

S (< 1d)
