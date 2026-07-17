# Finding: OBS-002 — Roh-Exception-Details an LLM exponiert

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `OBS-002` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

```python
# server.py:385
return f"Fehler: Unerwarteter Fehler ({type(e).__name__}): {e}"

# server.py:643
"fehler": str(e)[:100],
```

Beide Stellen leiten den Exception-String direkt an das LLM weiter (nur Z. 643 mit Truncate auf 100 Zeichen).

### Expected Behavior

Generische Fehlermeldung nach aussen, Details intern in strukturierten Logs (mit Severity, Tool-Name, Request-ID).

### Evidence

- File: `src/bakom_mcp/server.py:385` — Generic-Catch-Branch im Helper
- File: `src/bakom_mcp/server.py:643` — Multi-Standort-Loop pro Standort

### Risk Description

Exception-Strings können enthalten:
- Stack-Pfade (`/home/user/...`)
- Library-Versionen (Vector für CVE-Mining)
- Interne URLs / IPs bei DNS-Fehler
- Pydantic-Validation-Errors mit Field-Snippets aus User-Input (PII unwahrscheinlich, aber möglich)

Bei Adversarial-Prompt-Injection könnten diese Strings vom LLM extrahiert werden.

### Remediation

```python
import logging
logger = logging.getLogger("bakom_mcp")

def _handle_api_error(e: Exception, *, request_id: str | None = None) -> str:
    # Detaillierte Logs intern
    logger.exception("Tool error", extra={"request_id": request_id})

    # Generische User-Message
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Fehler: Ressource nicht gefunden."
        if e.response.status_code == 429:
            return "Fehler: Rate-Limit erreicht."
        return "Fehler: Externe API antwortet nicht wie erwartet."
    if isinstance(e, httpx.TimeoutException):
        return "Fehler: Zeitüberschreitung."
    if isinstance(e, httpx.ConnectError):
        return "Fehler: Verbindung zur API fehlgeschlagen."
    return "Fehler: Unerwarteter interner Fehler."  # KEIN {e} mehr

# server.py:643 ersetzen:
"fehler": "Standort konnte nicht abgefragt werden",  # statt str(e)[:100]
```

### Effort Estimate

**S** — 2 Code-Stellen + Logger-Setup.

### Verification After Fix

`grep -E 'str\(e\)|({e})' src/bakom_mcp/server.py` liefert nur noch Logger-Stellen, keine Returns.
