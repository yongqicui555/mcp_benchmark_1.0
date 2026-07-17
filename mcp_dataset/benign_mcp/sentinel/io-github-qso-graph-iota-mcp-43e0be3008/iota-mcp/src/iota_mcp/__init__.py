"""MCP server for Islands on the Air — group lookup, island search, DXCC mapping"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Final

try:
    _pkg_version = version("iota-mcp")
except PackageNotFoundError:  # local dev / editable installs without dist metadata
    _pkg_version = "0.0.0-dev"

__version__: Final[str] = _pkg_version

# Upstream data spec the server is bound to. Pinned to the IOTA programme
# data revision we consume — bump this when iota-world.org publishes a
# new programme data set. Reported by the get_version_info tool so agents
# can detect fleet drift without going outside the MCP protocol.
__spec_version__: Final[str] = "iota-programme-v1"
