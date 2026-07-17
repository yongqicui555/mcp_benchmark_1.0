from mcp.server.fastmcp import FastMCP

_mcp = FastMCP("Pylpex")

def get_mcp():
    """Get the FastMCP instance."""
    return _mcp