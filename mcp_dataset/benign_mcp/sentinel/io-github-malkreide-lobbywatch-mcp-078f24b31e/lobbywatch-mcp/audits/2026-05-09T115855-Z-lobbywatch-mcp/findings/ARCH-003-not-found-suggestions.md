## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

**Severity:** medium
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** ARCH-003

### Observed Behavior

Bei Fuzzy-Miss (score < 70) liefert get_parlamentarier nur None ohne Suggestion.

### Expected Behavior

Best-Practice-Katalog (ARCH-003). Siehe checks/ARCH-003.md für volle Pass-Criteria.

### Evidence

src/lobbywatch_mcp/client.py:184 best = process.extractOne(..., score_cutoff=70); if not best: return None
server.py:156-160 returns ParlamentarierResponse(parlamentarier=None) — kein 'did you mean'

### Risk Description

Schlechtes UX bei Tippfehlern; LLM muss reaktiv neu suchen statt direkt korrigiert zu werden.

### Remediation

```
Bei score zwischen 50–70: liefere top_3 candidates als Suggestion-Liste im Response-Envelope.
```

### Effort Estimate

S (< 1d)
