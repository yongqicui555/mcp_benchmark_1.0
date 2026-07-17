# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-18
**Commit:** bb3250e
**Branch:** main

## OVERVIEW

MCP server for Performance Co-Pilot (PCP) metrics. Exposes system performance data (CPU, memory, disk, network, processes) via Model Context Protocol tools and resources. Built on FastMCP 3.1+ with httpx async client for pmproxy REST API.

## STRUCTURE

```
pcp-mcp/
├── src/pcp_mcp/           # Core package (see src/pcp_mcp/AGENTS.md)
│   ├── tools/             # MCP tools (see src/pcp_mcp/tools/AGENTS.md)
│   ├── utils/             # Extractors, builders
│   └── prompts/           # LLM system prompts
├── tests/                 # Test suite (see tests/AGENTS.md)
├── docs/                  # MkDocs source
└── site/                  # Generated docs (gitignored)
```

See subdirectory AGENTS.md files for detailed guidance on each module.

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new tool | `src/pcp_mcp/tools/` |
| Modify HTTP client | `src/pcp_mcp/client.py` |
| Change config | `src/pcp_mcp/config.py` |
| Add response model | `src/pcp_mcp/models.py` |
| Map exceptions | `src/pcp_mcp/errors.py` |
| CLI changes | `src/pcp_mcp/__init__.py` |
| Server setup | `src/pcp_mcp/server.py` |

## CONVENTIONS

### Code Style
- **Line length**: 100 chars
- **Docstrings**: Google-style (enforced by ruff D rules)
- **Imports**: `from __future__ import annotations` at top
- **Async**: Default for I/O operations

### Ruff Rules
`E, F, I, UP, B, SIM, ASYNC, D` — tests exempt from D rules

### Type Checking
- **Tool**: ty (not pyright, not mypy)
- **Target**: Python 3.14
- **Mode**: standard

### Environment Variables
All prefixed with `PCP_`:
- `PCP_HOST`, `PCP_PORT` — pmproxy connection
- `PCP_TARGET_HOST` — remote pmcd host
- `PCP_USE_TLS`, `PCP_TIMEOUT` — connection options
- `PCP_USERNAME`, `PCP_PASSWORD` — auth (optional)

## ANTI-PATTERNS

### Counter Metrics (CRITICAL)
These are CUMULATIVE (since boot), NOT per-second rates:
- `kernel.all.cpu.*`
- `disk.all.read_bytes`, `disk.all.write_bytes`
- `network.interface.in.bytes`, `network.interface.out.bytes`
- `proc.psinfo.utime`, `proc.psinfo.stime`

**DO NOT** query with `query_metrics()` expecting rates.
**USE** `get_system_snapshot()` or `get_process_top()` instead.

### Tool Patterns
- **NEVER** use empty `except:` blocks
- **ALWAYS** wrap exceptions with `handle_pcp_error()`
- **ALWAYS** return Pydantic models from tools
- **ALWAYS** use `Annotated[type, Field(...)]` for tool params



## COMMANDS

```bash
make check        # Full CI: lint + format-check + typecheck + test
make lint         # ruff check .
make format       # ruff format .
make typecheck    # ty check
make test         # pytest with coverage
make fix          # Auto-fix lint + format
make complexity   # Fail on D+ complexity functions
```

## NOTES

- **Python**: 3.10+ required (3.14 target)
- **FastMCP**: 3.1+ required
- **pmproxy**: Must be running for tests against real PCP
- **Tests**: Use `respx` for httpx mocking, not real network
- **Coverage**: Uploaded to Codecov on Python 3.14 only

## REVIEW GUIDELINES

Guidelines for AI code review (Codex `@codex review`, Copilot, Claude).

### Security (P0)

Flag immediately:
- Credentials in logs or error messages (check f-strings, exception args)
- `PCP_USERNAME`/`PCP_PASSWORD` exposed anywhere except config loading
- User-supplied hostspecs not validated against `PCP_ALLOWED_HOSTS`
- TLS verification disabled without explicit user opt-in
- Empty `except:` blocks that swallow errors silently

### Usability (P1)

MCP tools must be LLM-friendly:
- Tool responses MUST be Pydantic models with `assessment` fields for quick triage
- Error messages MUST explain what failed AND suggest remediation
- Tool parameter descriptions MUST use `Annotated[type, Field(description=...)]`
- Counter metrics (CPU, disk, network) MUST use rate-calculating tools, not raw `query_metrics()`

### Correctness (P1)

- All httpx exceptions MUST be caught and converted via `handle_pcp_error()`
- Async functions MUST NOT contain blocking calls
- Exception chains MUST be preserved with `raise ... from e`
- Rate calculations MUST handle elapsed_time=0 (division by zero)

### Simplification (P2)

Flag duplication opportunities:
- Similar test patterns across 3+ tests → parameterize with `@pytest.mark.parametrize`
- Repeated model construction in tests → add factory fixture to `conftest.py`
- Similar error handling across tools → extract to shared helper
- Inline imports in tests → move to module level or conftest

### What NOT to Flag

Automated tools handle these—skip them in review:
- Style/formatting (ruff)
- Type errors (ty)
- Import order (ruff isort)
- Line length (ruff)
