## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | partial |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SEC-018` |
| **PDF-Reference** | Sec 3 / Sec 4 (Defense-in-Depth) |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- Numerische Felder mit ge/le-Constraints (server.py:171 limit_days ge=1 le=400; :308 bfs_nr ge=1; :443 bfs_numbers min/max_length)
- Pydantic-Field-Validierung an allen Tool-Boundaries; Literal-Types fuer Enums

### Gaps / Abweichung vom Pass-Kriterium

- String-Parameter category/canton/query ohne max_length/pattern (server.py:309/401/485)
- category/canton werden ungeprueft in SPARQL-Query-Strings interpoliert (api_client.py:218/312) -> SPARQL-Injection-Risiko
- Kein strict=True/extra='forbid' an den Modellen

### Risk Description

Tool-Argumente kommen vom LLM — einer probabilistischen Quelle, die halluzinieren, formattieren-falsch oder von Prompt-Injection beeinflusst sein kann. Ohne strikte Input-Validation am Tool-Boundary werden invalide oder bösartige Inputs in die Geschäftslogik weitergereicht und können dort:

### Remediation

### Schritt 1: Schema pro Tool extrahieren

```diff
+ from typing import Annotated
+ from pydantic import BaseModel, Field, StringConstraints
+
+ class SearchArgs(BaseModel):
+     model_config = {"strict": True, "extra": "forbid"}
+     query: Annotated[str, StringConstraints(min_length=2, max_length=200)]
+     limit: Annotated[int, Field(ge=1, le=100)] = 10

  @mcp.tool()
- async def search(query: str, limit: int = 10) -> dict:
+ async def search(args: SearchArgs, ctx: Context) -> dict:
-     return await db.search(query, limit=limit)
+     return await db.search(args.query, limit=args.limit)
```

### Schritt 2: ValidationError sauber behandeln

```python
from pydantic import ValidationError

@mcp.tool()
async def search(args: SearchArgs, ctx: Context) -> dict:
    try:
        # Pydantic validiert beim Parsing automatisch — kein Aufruf nötig
        # Falls manuell aus dict gebaut: SearchArgs.model_validate(raw_dict)
        return await db.search(args.query, limit=args.limit)
    except ValidationError as e:
        # Wird normal nicht erreicht (FastMCP fängt das ab),
        # aber Defense-in-Depth:
        return {
            "isError": True,
            "content": [TextContent(
                type="text",
                text=f"Invalid arguments: {e.errors()[0]['msg']}"
            )],
        }
```

### Schritt 3: Tests gegen Edge-Cases

```python
@pytest.mark.parametrize("invalid_args,expected_error", [
    ({"query": "a", "limit": 10}, "min_length"),       # zu kurz
    ({"query": "x"*500, "limit": 10}, "max_length"),   # zu lang
    ({"query": "test", "limit": 0}, "greater_than_or_equal"),
    ({"query": "test", "limit": 99999}, "less_than_or_equal"),
    ({"query": "test", "limit": 10, "evil": "field"}, "extra_forbidden"),
])

_(... vollstaendige Remediation siehe checks/SEC-018.md)_

### Effort Estimate

S — < 1 Tag pro Server bei wenigen Tools, M bei vielen Tools (10+).

### Verification After Fix

- Re-Audit von `SEC-018` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
