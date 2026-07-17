"""lobbywatch-mcp — MCP server for the Lobbywatch.ch lobby database.

Part of the Swiss Public Data MCP Portfolio (https://github.com/malkreide).

Data © Lobbywatch.ch, licensed CC BY-SA 4.0.
Code licensed MIT.
"""

__version__ = "0.1.0"
__all__ = ["LobbywatchClient", "build_server"]

from lobbywatch_mcp.client import LobbywatchClient
from lobbywatch_mcp.server import build_server
