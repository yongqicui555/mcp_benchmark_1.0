# MCP Tools

## OVERVIEW

MCP tool implementations. Two modules: metrics (query/search/describe) and system (snapshot/top).

## STRUCTURE

```
tools/
├── __init__.py    # register_tools() → calls both modules
├── metrics.py     # query_metrics, search_metrics, describe_metric
└── system.py      # get_system_snapshot, get_process_top
```

## REGISTRATION PATTERN

Tools use standalone `@tool()` decorator (not method decorator) and are registered via `mcp.add_tool()`:

```python
# In metrics.py or system.py
from fastmcp.tools import tool
from fastmcp.tools.tool import ToolResult
from mcp.types import ToolAnnotations

TOOL_ANNOTATIONS = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
ICON_METRICS = "📊"
TAGS_METRICS = {"metrics", "query"}

@tool(
    annotations=TOOL_ANNOTATIONS,
    icons=[ICON_METRICS],
    tags=TAGS_METRICS,
    timeout=30.0,
)
async def query_metrics(
    ctx: Context,
    names: Annotated[list[str], Field(description="Metric names to fetch")],
) -> ToolResult:
    """Fetch current values for specific PCP metrics."""
    client = get_client(ctx)
    # ...
```

Then in `__init__.py`:

```python
def register_tools(mcp: FastMCP) -> None:
    from pcp_mcp.tools.metrics import query_metrics, search_metrics, describe_metric
    from pcp_mcp.tools.system import get_system_snapshot, get_process_top, ...
    
    mcp.add_tool(query_metrics)
    mcp.add_tool(search_metrics)
    mcp.add_tool(describe_metric)
    mcp.add_tool(get_system_snapshot)
    # ... etc
```

## TOOL REQUIREMENTS

1. **Decorator**: `@tool(annotations=..., icons=..., tags=..., timeout=...)`
2. **Import**: `from fastmcp.tools import tool`
3. **Context**: First param is `ctx: Context`
4. **Annotations**: `Annotated[type, Field(description="...")]` for all params
5. **Return**: `ToolResult` (from `fastmcp.tools.tool`)
6. **Registration**: Call `mcp.add_tool(function_name)` in `__init__.py`
7. **Errors**: Wrap with `handle_pcp_error()`

## TOOLS

| Tool | Purpose | Returns |
|------|---------|---------|
| `query_metrics` | Fetch raw metric values | `ToolResult` |
| `search_metrics` | Find metrics by prefix | `ToolResult` |
| `describe_metric` | Get metric metadata | `ToolResult` |
| `get_system_snapshot` | System overview with rates | `ToolResult` |
| `quick_health` | Fast health check (cached) | `ToolResult` |
| `get_process_top` | Top N processes | `ToolResult` |
| `smart_diagnose` | AI-assisted diagnosis | `ToolResult` |
| `get_filesystem_usage` | Mounted filesystem usage | `ToolResult` |

## ANTI-PATTERNS

- **NEVER** return raw dicts (use Pydantic models)
- **NEVER** skip `Annotated[..., Field(...)]` on params
- **NEVER** let httpx exceptions escape (wrap with `handle_pcp_error`)
- **NEVER** block async (no `time.sleep()`, use `asyncio.sleep()`)

## ADDING NEW TOOL

1. Add function in `metrics.py` or `system.py` with `@tool(...)` decorator
2. Import `tool` from `fastmcp.tools`
3. Return `ToolResult` (not raw dict or Pydantic model)
4. Add response model to `models.py` if needed
5. Import function in `__init__.py` and call `mcp.add_tool(function_name)`
