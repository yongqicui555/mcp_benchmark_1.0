# pcp_mcp Core Package

## OVERVIEW

Core MCP server package. Entry point, HTTP client, configuration, models, error handling.

## STRUCTURE

```
pcp_mcp/
├── __init__.py     # CLI entry (main() with argparse)
├── server.py       # FastMCP setup, lifespan context
├── client.py       # PCPClient async httpx wrapper
├── config.py       # PCPMCPSettings (Pydantic)
├── models.py       # Response models (SystemSnapshot, ProcessInfo, etc.)
├── errors.py       # Exception → ToolError mapping
├── context.py      # get_client(), get_settings() helpers
├── middleware.py   # Request caching middleware
├── icons.py        # System assessment icons (emoji mappings)
├── tools/          # MCP tools (see tools/AGENTS.md)
├── utils/          # Extractors, builders
└── prompts/        # LLM system prompts
```

## KEY PATTERNS

### Server Lifespan
```python
@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[dict]:
    async with PCPClient(...) as client:
        yield {"client": client, "settings": settings}
```
Tools access via `ctx.request_context.lifespan_context["client"]`.

### Client Rate Calculation
`fetch_with_rates()` takes two samples, calculates per-second rates for counters.
Handles counter wrap-around (reset to 0) gracefully.

### Error Mapping
```python
try:
    result = await client.fetch(names)
except Exception as e:
    raise handle_pcp_error(e, "fetching metrics") from e
```

### Configuration
Pydantic settings with `env_prefix="PCP_"`. Computed properties: `base_url`, `auth`.

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add CLI flag | `__init__.py` | argparse in `main()` |
| Change transport | `__init__.py` | `server.run(transport=...)` |
| Add env var | `config.py` | Add field with `Field(default=...)` |
| New response type | `models.py` | Inherit `BaseModel` |
| Map new exception | `errors.py` | Add case to `handle_pcp_error()` |
| Access client in tool | `context.py` | Use `get_client(ctx)` |
| Add caching | `middleware.py` | Request caching layer |
| System icons | `icons.py` | Assessment emoji mappings |

## ANTI-PATTERNS

- **NEVER** call `client.fetch()` for counter metrics expecting rates
- **NEVER** use client outside `async with` context
- **NEVER** log credentials from settings
- **ALWAYS** use `handle_pcp_error()` for exception wrapping
