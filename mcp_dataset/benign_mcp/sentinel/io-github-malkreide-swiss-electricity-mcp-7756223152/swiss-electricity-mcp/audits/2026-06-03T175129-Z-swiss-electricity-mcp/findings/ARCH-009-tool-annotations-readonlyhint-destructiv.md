## Finding: ARCH-009 — Tool Annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `ARCH-009` |
| **PDF-Reference** | Anhang A5 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- grep auf readOnlyHint/destructiveHint/idempotentHint/openWorldHint in src/ = 0 Treffer
- Alle 11 @mcp.tool-Decorators setzen nur description, keine annotations (server.py:119, :163, :248, ...)

### Gaps / Abweichung vom Pass-Kriterium

- KEINE Tool-Annotations vorhanden - alle Tools sind read-only und externe-Aufrufe, sollten readOnlyHint=true und openWorldHint=true deklarieren
- Clients koennen read-only-Charakter nicht aus Annotations ableiten

### Risk Description

Die MCP-Spec von 2025-03-26 hat **Tool Annotations** eingeführt — strukturierte Hints, die Hosts (z.B. Claude Desktop) für UI-Entscheidungen verwenden:

### Remediation

### Schritt 1: Annotations-Inventar

Pro Tool eine Tabelle mit den vier Hints. Wenn unsicher: per Default konservativ (alles `false`/weggelassen impliziert «kann gefährlich sein»).

### Schritt 2: Decorator-Helper

```python
from typing import Literal

def read_only_tool(*args, **kwargs):
    """Shortcut für read-only Tools mit konsistenten Annotations."""
    annotations = kwargs.pop("annotations", {})
    annotations.update({
        "readOnlyHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    })
    kwargs["annotations"] = annotations
    return mcp.tool(*args, **kwargs)


@read_only_tool()
async def search_motions(args, ctx):
    ...
```

### Schritt 3: CI-Test gegen Drift

```python
def test_destructive_tools_have_destructive_hint():
    """Tools mit delete/create/update im Namen müssen destructiveHint setzen."""
    suspicious_prefixes = ("delete_", "create_", "update_", "remove_")
    for tool_name, tool in mcp.tools.items():
        if any(tool_name.startswith(p) for p in suspicious_prefixes):
            annotations = tool.annotations or {}
            assert annotations.get("readOnlyHint") is not True, (
                f"{tool_name} suggests write but is marked readOnlyHint"
            )
```

### Effort Estimate

S — < 1 Tag. Annotations-Inventar + Decorator + Tests.

### Verification After Fix

- Re-Audit von `ARCH-009` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)
