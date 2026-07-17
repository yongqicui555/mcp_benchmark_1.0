## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-008` |
| **PDF-Reference** | Anhang A2 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Server nutzt das Primitive Tools sauber und konsistent

### Gaps / Abweichung vom Pass-Kriterium

- Nur Tools, keine Resources oder Prompts
- README dokumentiert nicht, warum keine Resources/Prompts (read-only, idempotente Tools waeren Resource-Migrations-Kandidaten)

### Risk Description

MCP definiert drei orthogonale Primitive, von denen die meisten Server nur eines nutzen:

### Remediation

### Schritt 1: Tools-zu-Resources-Audit

Pro Tool prüfen:

```
- Hat Side-Effects? → Tool bleibt
- Ist deterministisch und idempotent? → Resource-Kandidat
- Liefert primär Kontextdaten zum Lesen? → Resource-Kandidat
```

### Schritt 2: URI-Schema definieren

Pro Resource-Klasse ein konsistentes Schema:

```
school://<school_id>/profile
school://<school_id>/classes/<year>
luftqualitaet://<school_id>/<date>
budget://<school_id>/<year>
```

### Schritt 3: Migration

```diff
- @mcp.tool()
- async def get_school_profile(school_id: str) -> dict:
-     return await db.get_school_profile(school_id).dict()

+ @mcp.resource("school://{school_id}/profile")
+ async def school_profile(school_id: str) -> str:
+     profile = await db.get_school_profile(school_id)
+     return profile.as_markdown()
```

### Schritt 4: Prompts-Inventar

Falls wiederkehrende Workflows existieren: pro Workflow ein Prompt-Template, ins README dokumentieren.

### Effort Estimate

M — 1–3 Tage. Audit + Migration einer Handvoll Tools + Doku.

### Verification After Fix

- Re-Audit von `ARCH-008` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
