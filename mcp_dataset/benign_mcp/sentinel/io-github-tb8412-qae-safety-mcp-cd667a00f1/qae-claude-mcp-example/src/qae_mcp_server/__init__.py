"""
QAE Safety Certification MCP Server

A Model Context Protocol server that exposes the QAE safety certification
kernel as tools Claude can use to evaluate autonomous action safety.

Version: 0.1.0
License: Apache-2.0
"""

__version__ = "0.1.0"
__author__ = "Northbeam Solutions LLC"
__license__ = "Apache-2.0"

from qae_mcp_server.server import main, certify_action, check_budget, get_certification_history

__all__ = [
    "main",
    "certify_action",
    "check_budget",
    "get_certification_history",
]
