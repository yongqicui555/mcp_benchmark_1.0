"""Swiss Cultural Heritage MCP Server."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("swiss-cultural-heritage-mcp")
except PackageNotFoundError:  # not installed (running from source tree)
    __version__ = "0.0.0+local"
