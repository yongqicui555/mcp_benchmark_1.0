# GitHub Copilot Code Review Instructions

## Review Philosophy: Invert, Always Invert

Apply Charlie Munger's inversion principle: Instead of asking "Is this code good?", ask **"What would make this code fail?"**

Focus on preventing failure rather than achieving brilliance:
- What edge cases would break this?
- What would cause this to fail in production?
- What would make this unmaintainable in 6 months?
- What security holes does this open?

When something could fail, explain **HOW** it would fail and suggest the prevention.

---

## Project Context: pcp-mcp

MCP (Model Context Protocol) server for Performance Co-Pilot (PCP). Python 3.10+, FastMCP 3.1+.

### Tech Stack
- **MCP Framework**: FastMCP 3.1+
- **HTTP Client**: httpx (async)
- **Backend**: pmproxy REST API
- **Type checking**: ty
- **Linting/Formatting**: ruff
- **Testing**: pytest + pytest-asyncio + respx
- **Package manager**: uv

### Key Design Decisions
- Clumped tools (get_system_snapshot) instead of per-metric tools
- Client-side rate calculation for counter metrics
- Configurable target_host for remote monitoring
- Pydantic response models with assessment fields

---

## Inversion Checklists by File Type

### Source Code (`src/pcp_mcp/**/*.py`)

**MCP server failures to prevent:**
- Tools not returning proper Pydantic response models
- Not handling httpx exceptions (must convert to `ToolError`)
- Blocking calls in async tool functions
- Missing type hints or docstrings
- Rate calculation errors (counter vs gauge metrics)

**FastMCP patterns to enforce:**
- Tools use `@mcp.tool()` decorator with proper type hints
- Resources use `@mcp.resource()` decorator
- Context accessed via `ctx.request_context.lifespan_context`
- Errors raised as `ToolError` or `ResourceError`

### Client (`src/pcp_mcp/client.py`)

**What would cause the client to fail?**
- Not creating pmapi context on `__aenter__`
- Not closing httpx client on `__aexit__`
- Rate calculation with wrong elapsed time
- Not handling counter wrap-around
- Timeout not respected

### Tools (`src/pcp_mcp/tools/**/*.py`)

**What would cause tools to fail?**
- Exceptions not mapped to `ToolError` via `handle_pcp_error()`
- Missing `Annotated[type, Field(...)]` for parameter descriptions
- sample_interval too short for accurate rates
- Not awaiting async calls

### Resources (`src/pcp_mcp/resources/**/*.py`)

**What would cause resources to fail?**
- Resources attempting write operations (they're read-only!)
- Resource URI patterns not matching expected format
- Not handling missing metrics gracefully

### Configuration (`src/pcp_mcp/config.py`)

**What would cause config to fail?**
- Missing `env_prefix="PCP_"` (env vars won't load)
- Credentials logged or exposed in error messages
- Invalid defaults for pmproxy connection

### Error Handling (`src/pcp_mcp/errors.py`)

**What would make error handling fail?**
- Not handling all httpx exception types
- Generic `except` clauses hiding real errors
- Error messages too vague for debugging
- Not preserving exception chains (use `from e`)

### Tests (`tests/**/*.py`)

**What would make these tests meaningless?**
- Tests that pass but don't assert meaningful outcomes
- Mocks without `spec=` (won't catch attribute errors)
- Missing edge cases: empty responses, network errors, invalid data
- Not testing both success and failure paths
- Not using respx for httpx mocking

### Project Config (`pyproject.toml`)

**What would break the build/test cycle?**
- Missing dev dependencies
- Incompatible version constraints
- pytest-asyncio missing `asyncio_mode = "auto"`
- Coverage excluding important paths

---

## What NOT to Review

Don't nitpick these—automated tools handle them:
- **Style issues**: ruff handles formatting and linting
- **Type errors**: ty handles type checking
- **Import order**: ruff's isort handles this

Focus review time on logic, architecture, and failure modes.
