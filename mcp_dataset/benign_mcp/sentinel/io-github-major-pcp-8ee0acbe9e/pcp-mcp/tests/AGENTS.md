# Test Suite

## OVERVIEW

pytest + pytest-asyncio + respx. Factory fixtures in conftest.py. 100% async tests.

## STRUCTURE

```
tests/
├── conftest.py           # Fixtures: factories, mocks, context helpers
├── test_client.py        # PCPClient tests with respx mocking
├── test_config.py        # Settings loading tests
├── test_errors.py        # Exception mapping tests
├── test_context.py       # Context helper tests
├── test_tools_metrics.py # Metrics tools tests
├── test_tools_system.py  # System tools tests
├── test_resources.py     # Resource tests
├── test_utils.py         # Utility function tests
├── test_cli.py           # CLI argument tests
├── test_middleware.py    # Caching middleware tests
├── test_icons.py         # Icon mapping tests
├── test_prompts.py       # Prompt tests
└── test_smoke.py         # Server startup smoke tests (catches registration errors)
```

## KEY FIXTURES

### Data Factories
```python
@pytest.fixture
def cpu_metrics_data() -> Callable[..., dict]:
    def _make(user=20.0, sys=10.0, idle=65.0, ...) -> dict:
        return {"kernel.all.cpu.user": {"instances": {-1: user}}, ...}
    return _make
```

### Mock Client
```python
@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock(spec=PCPClient)  # spec= enforces interface
    client.target_host = "localhost"
    return client
```

### MCP Context
```python
@pytest.fixture
def mock_context(mock_lifespan_context) -> MagicMock:
    ctx = MagicMock(spec=Context)
    ctx.request_context.lifespan_context = mock_lifespan_context
    return ctx
```

### Tool Capture
```python
@pytest.fixture
def capture_tools() -> Callable[[RegisterFn], ToolDict]:
    # Captures @mcp.tool() decorated functions for testing
```

## PATTERNS

### HTTP Mocking (respx)
```python
async def test_fetch(self, respx_mock):
    respx_mock.get("/pmapi/fetch").respond(json={...})
    async with PCPClient(...) as client:
        result = await client.fetch(["metric"])
```

### Tool Testing
```python
async def test_tool(self, mock_context, capture_tools):
    mock_context...lifespan_context["client"].fetch.return_value = {...}
    tools = capture_tools(register_system_tools)
    result = await tools["get_system_snapshot"](mock_context)
    assert result.cpu is not None
```

### Smoke Testing (FastMCP Client)
```python
async def test_tools_are_registered(self):
    server = create_server()
    async with Client(server) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} >= {"get_system_snapshot", ...}
```
Uses FastMCP's in-process Client to verify server starts and tools register correctly.
Catches import errors, type annotation issues, and registration failures.

## ANTI-PATTERNS

- **NEVER** use real network calls (use respx)
- **NEVER** create mocks without `spec=` (misses interface errors)
- **NEVER** duplicate test data (use factory fixtures)
- **ALWAYS** test both success and error paths
- **ALWAYS** test edge cases: empty responses, timeouts, invalid data
