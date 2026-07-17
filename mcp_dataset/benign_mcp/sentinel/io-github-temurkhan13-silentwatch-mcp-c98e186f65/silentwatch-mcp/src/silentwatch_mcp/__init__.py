"""silentwatch-mcp — MCP server for OpenClaw and system cron visibility."""

__version__ = "1.0.11"

from silentwatch_mcp.server import build_server

__all__ = ["__version__", "build_server"]
