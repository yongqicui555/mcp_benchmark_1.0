# Development Guide

## Setup

1. Clone or download the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running the Server

### Option 1: Direct Python
```bash
python -m qae_mcp_server
```

### Option 2: Entry Point
```bash
qae-mcp-server
```

### Option 3: From Claude Desktop
1. Configure `claude_desktop_config.json` (see README.md)
2. Restart Claude Desktop
3. Tools will be available in the tool menu

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=qae_mcp_server tests/
```

## Code Style

Format code with black:
```bash
black src/ tests/
```

Sort imports with isort:
```bash
isort src/ tests/
```

Lint with flake8:
```bash
flake8 src/ tests/
```

Type check with mypy:
```bash
mypy src/
```

Run all checks:
```bash
black --check src/ tests/
isort --check src/ tests/
flake8 src/ tests/
mypy src/
```

## Project Structure

```
qae-claude-mcp-example/
├── README.md                          # User-facing documentation
├── DEVELOPMENT.md                     # This file
├── requirements.txt                   # Production dependencies
├── pyproject.toml                     # Python project metadata
├── setup.cfg                          # Tool configuration
├── .gitignore                         # Git ignore rules
├── claude_desktop_config.example.json # MCP server configuration template
└── src/
    ├── __init__.py                    # Package initialization
    ├── __main__.py                    # Entry point
    └── server.py                      # MCP server implementation
```

## Key Components

### `src/qae_mcp_server/server.py`
The main MCP server implementation. Contains:
- `FastMCP` server instance
- `_certifier`: Global SafetyCertifier instance
- `_certification_history`: Deque of recent certifications
- Three tools:
  1. `certify_action()` — Main certification endpoint
  2. `check_budget()` — Budget status
  3. `get_certification_history()` — Audit trail

### Server Initialization
- Uses lazy initialization: certifier is created on first tool call
- Maintains state in module globals
- Logs all operations for debugging

## Extending the Server

### Adding a New Tool

1. Import required dependencies
2. Define a function decorated with `@server.tool()`
3. Add docstring with Args and Returns sections
4. Return a dict (will be converted to JSON)

Example:
```python
@server.tool()
def my_new_tool(param1: str, param2: float) -> Dict[str, Any]:
    """
    Brief description.

    Args:
        param1: First parameter
        param2: Second parameter

    Returns:
        Dictionary with result
    """
    return {"result": "value"}
```

### Customizing the Adapter

Edit `_initialize_certifier()` in `src/qae_mcp_server/server.py`:

```python
adapter = AgenticAdapter(
    budget_limit=200.0,  # Increase budget
    rate_limit=100.0,    # Increase rate limit
)

config = CertifierConfig(
    safe_threshold=0.7,      # Higher bar for "Certified"
    caution_threshold=0.4,   # Wider caution zone
    block_threshold=0.2,     # Lower bar for "Blocked"
)
```

## Troubleshooting

### `qae-safety` import fails
- Ensure `qae-safety` is installed: `pip install qae-safety`
- Check Python version: requires Python 3.9+

### Server won't start
- Check logs for errors: `python -m qae_mcp_server`
- Verify dependencies: `pip install -e .`

### Claude doesn't see tools
- Restart Claude Desktop
- Check `claude_desktop_config.json` syntax
- Run server manually to see errors: `python -m qae_mcp_server`

### Budget always showing 0 remaining
- Certifications are cumulative; budget resets per period
- Default period is 24 hours from first certification

## Debugging

Enable debug logging by modifying `src/qae_mcp_server/server.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # Change from INFO
```

Monitor logs to see:
- Certification decisions
- Budget consumption
- Tool invocations
- Errors and exceptions

## Performance

The MCP server is lightweight:
- Initialization: ~100ms (on first tool call)
- Certification: ~5-20ms (depends on qae-safety kernel)
- Memory: ~50MB base + ~1MB per 100 certifications

For high-volume use:
- Increase `rate_limit` in AgenticAdapter
- Increase `maxlen` of `_certification_history` deque if retaining more history
- Consider running multiple server instances behind a load balancer

## License

Apache-2.0. See parent repository for full details.
