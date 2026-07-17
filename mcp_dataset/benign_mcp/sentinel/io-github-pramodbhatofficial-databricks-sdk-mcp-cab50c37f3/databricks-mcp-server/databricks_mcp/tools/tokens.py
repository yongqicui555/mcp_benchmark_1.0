"""Personal access token management tools for Databricks MCP.

Provides tools for managing personal access tokens (PATs) for the current
user via the Tokens API, and for workspace admins to manage all users'
tokens via the Token Management API.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all token management tools with the MCP server."""

    # ── Personal Access Tokens (current user) ────────────────────────────

    @mcp.tool()
    def databricks_list_tokens() -> str:
        """List all personal access tokens for the current user.

        Returns metadata about each token including its ID, comment,
        creation time, and expiry. Token values are never returned.

        Returns:
            JSON array of token info objects with token_id, comment,
            creation_time, and expiry_time. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.tokens.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_token(
        comment: str = "",
        lifetime_seconds: int = 0,
    ) -> str:
        """Create a new personal access token for the current user.

        The token value is only returned once at creation time and cannot
        be retrieved later. Store it securely.

        Args:
            comment: Optional description of the token's intended use
                     (e.g. "CI/CD pipeline" or "local development").
            lifetime_seconds: Token lifetime in seconds. Use 0 or omit for
                              no expiry (the token never expires).

        Returns:
            JSON object with the token_value (the actual secret -- store it
            securely!) and token_info containing token_id, comment, and
            expiry_time.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {}
            if comment:
                kwargs["comment"] = comment
            if lifetime_seconds > 0:
                kwargs["lifetime_seconds"] = lifetime_seconds
            result = w.tokens.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_token(token_id: str) -> str:
        """Revoke (delete) a personal access token for the current user.

        The token will immediately stop working for authentication.

        Args:
            token_id: The unique identifier of the token to revoke.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.tokens.delete(token_id)
            return f"Token '{token_id}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Token Management (admin) ─────────────────────────────────────────

    @mcp.tool()
    def databricks_list_token_management() -> str:
        """List all personal access tokens in the workspace (admin only).

        Workspace admins can use this to audit all tokens across all users.
        Returns metadata about each token including owner, creation time,
        and expiry.

        Returns:
            JSON array of token info objects with token_id, owner,
            comment, creation_time, and expiry_time.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.token_management.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_token_management(token_id: str) -> str:
        """Revoke any user's personal access token (admin only).

        Workspace admins can use this to revoke tokens belonging to any
        user. The token will immediately stop working for authentication.

        Args:
            token_id: The unique identifier of the token to revoke.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.token_management.delete(token_id)
            return f"Token '{token_id}' deleted via token management successfully."
        except Exception as e:
            return format_error(e)
