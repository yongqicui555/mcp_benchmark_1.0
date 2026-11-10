from .mcp import get_mcp

# Load MCP components
from . import (
    prompts,
    resources,
    tools,
)

__all = [
    "get_mcp",
]