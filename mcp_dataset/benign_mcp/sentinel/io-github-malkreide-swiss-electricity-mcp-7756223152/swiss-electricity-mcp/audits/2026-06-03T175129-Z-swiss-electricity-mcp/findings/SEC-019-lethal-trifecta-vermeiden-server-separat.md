## Finding: SEC-019 — Lethal Trifecta vermeiden: Server-Separation Read vs Write/Send

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-019` |
| **PDF-Reference** | Anhang B1 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Trifecta-Bewertung: (1) nur Public Open Data, keine privaten Daten; (2) liest externe API-Daten; (3) kein Exfiltrations-Kanal (Egress hardcodiert) -> maximal 1-2 Faehigkeiten, Risiko niedrig

### Gaps / Abweichung vom Pass-Kriterium

- Trifecta-Assessment ist nicht im README/docs dokumentiert (Katalog verlangt explizite Dokumentation/ADR)

### Risk Description

Simon Willisons «Lethal Trifecta»-Konzept beschreibt drei Fähigkeiten, die einzeln harmlos, **kombiniert** aber den Server zur Waffe in der Hand eines Prompt-Injection-Angreifers machen:

### Remediation

### Schritt 1: Trifecta-Audit pro Server

Für jeden Server im Portfolio die drei Fragen beantworten:

| Frage | Antwort | Score-Beitrag |
|---|---|---|
| Liest privater Daten? | ja/nein | +1 wenn ja |
| Untrusted Content? | ja/nein | +1 wenn ja |
| Externe Kommunikation? | ja/nein | +1 wenn ja |

Score 0–1: sicher. Score 2: ADR + Compensating Controls. Score 3: Server splitten.

### Schritt 2: Server-Splittung (bei Score 3)

Beispiel — aus einem hypothetischen `eltern-comm-mcp`:

```diff
- # Vorher: ein Server liest UND sendet
- @mcp.tool() def get_eltern_data(klassenid): ...
- @mcp.tool() def send_eltern_mail(recipient, body): ...

+ # Nachher: zwei Server
+ # eltern-data-mcp/
+ @mcp.tool() def get_eltern_data(klassenid): ...
+
+ # eltern-mail-mcp/  (separater Repo, separate Service-Identity)
+ ALLOWED_DOMAINS = frozenset({"schulen.zuerich.ch"})
+ @mcp.tool() def send_eltern_mail(recipient, body):
+     if recipient.split("@")[-1] not in ALLOWED_DOMAINS:
+         raise PermissionError(...)
```

### Schritt 3: ADR dokumentieren

Wie im Pass-Pattern Modus 2.

### Schritt 4: Audit-Trail

Bei Score-2-Servern: alle Tool-Calls werden geloggt, SIEM-Alerts (siehe OBS-005) auf ungewöhnliche Pattern (z.B. Recipients ausserhalb Allow-List).

### Effort Estimate

L — 1–2 Wochen bei nötiger Server-Splittung. S — < 1 Tag für reine Bewertung und ADR.

### Verification After Fix

- Re-Audit von `SEC-019` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
