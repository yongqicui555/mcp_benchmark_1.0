"""Feedback Synthesis MCP — Customer feedback intelligence for AI agents via x402 micropayments."""


def main() -> None:
    """Start the Feedback Synthesis MCP thin client (stdio transport)."""
    from feedback_synthesis_mcp.server import mcp
    mcp.run()
