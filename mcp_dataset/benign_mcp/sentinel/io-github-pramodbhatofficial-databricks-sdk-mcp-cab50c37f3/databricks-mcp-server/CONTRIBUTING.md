# Contributing to Databricks MCP Server

Thanks for your interest in contributing! This project aims to be the most comprehensive MCP server for Databricks.

## Getting Started

1. **Fork and clone**

   ```bash
   git clone https://github.com/YOUR_USERNAME/databricks-mcp-server.git
   cd databricks-mcp-server
   ```

2. **Set up your environment**

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Run tests**

   ```bash
   pytest tests/ -v
   ```

4. **Run lint**

   ```bash
   ruff check databricks_mcp/
   ```

## Making Changes

### Adding a New Tool

Each tool module lives in `databricks_mcp/tools/` and follows this pattern:

```python
"""Module docstring describing the tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register tools with the MCP server."""

    @mcp.tool()
    def databricks_your_tool(param: str) -> str:
        """Tool description that the LLM will see.

        Args:
            param: What this parameter does.
        """
        try:
            w = get_workspace_client()
            result = w.some_service.some_method(param)
            return to_json(result)
        except Exception as e:
            return format_error(e)
```

Key conventions:
- All tool names start with `databricks_`
- SDK imports from `databricks.sdk.service.*` go **inside** the function (lazy imports)
- Every tool wraps its body in `try/except Exception`
- Use `paginate()` for list operations, `to_json()` for responses, `format_error()` for errors
- Long-running operations (create, start, stop) return immediately without calling `.result()`

### Adding a New Tool Module

1. Create `databricks_mcp/tools/your_module.py` following the pattern above
2. Add the module to `_TOOL_MODULES` in `databricks_mcp/server.py`
3. Add tests in `tests/test_your_module.py`
4. Update the tool count and table in `README.md`

### Writing Tests

Tests use `pytest` with a mock `WorkspaceClient`. See `tests/conftest.py` for shared fixtures:

- `mcp` — fresh FastMCP instance
- `mock_workspace_client` — MagicMock with all service attributes
- `patched_client` — patches `get_workspace_client` across all modules

Example test:

```python
def test_list_something(mcp, patched_client):
    from databricks_mcp.tools.your_module import register_tools

    register_tools(mcp)

    patched_client.some_service.list.return_value = iter([mock_item])
    tool_fn = mcp._tool_manager._tools["databricks_list_something"].fn
    result = tool_fn()

    patched_client.some_service.list.assert_called_once()
    assert "expected_field" in result
```

## Pull Request Process

1. **Create a branch** from `main`

   ```bash
   git checkout -b feature/add-new-tools
   ```

2. **Make your changes** — keep PRs focused on one thing

3. **Ensure quality**

   ```bash
   ruff check databricks_mcp/    # zero errors
   pytest tests/ -v               # all passing
   ```

4. **Write a clear PR description**
   - What does this change?
   - Why is it needed?
   - How was it tested?

5. **Submit the PR** against `main`

## What to Contribute

Here are some ways to help:

### Good First Issues

- Add tests for tool modules that don't have dedicated test files yet
- Improve tool docstrings (these are what LLMs see when choosing tools)
- Fix typos or improve README documentation

### Feature Ideas

- Add more tools for existing modules (e.g., `update_catalog`, `clone_job`)
- Add new service modules (e.g., Feature Store, Model Registry v2)
- Add SSE transport support alongside stdio
- Add GitHub Actions CI workflow
- Add integration tests (require a live Databricks workspace)

### Bug Reports

Open an issue with:
- What you expected to happen
- What actually happened
- Your Python version and `databricks-sdk` version
- Steps to reproduce

## Code Style

- **Line length**: 120 characters
- **Linter**: ruff (configured in `pyproject.toml`)
- **Python**: 3.10+ with `from __future__ import annotations`
- **Docstrings**: Google style, focused on what LLMs need to understand the tool

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
