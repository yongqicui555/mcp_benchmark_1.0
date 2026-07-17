"""
MCP Dice Roller - A simple MCP server for rolling dice.

This server provides tools for rolling various types of dice,
perfect for tabletop games, random decisions, and more.
"""

from .server import main, mcp

__version__ = "0.1.0"
__all__ = ["main", "mcp"]
