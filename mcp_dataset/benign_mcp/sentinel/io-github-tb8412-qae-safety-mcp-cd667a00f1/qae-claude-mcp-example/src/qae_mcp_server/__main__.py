"""
Entry point for the QAE Safety Certification MCP Server.

This module allows the server to be run directly via:
    python -m qae_mcp_server

Or via the entry point defined in pyproject.toml:
    qae-mcp-server
"""

from qae_mcp_server.server import main

if __name__ == "__main__":
    main()
