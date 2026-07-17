"""Git credential management tools for Databricks MCP.

Provides tools for managing Git credentials used by Databricks Repos
and Git folders. Each credential stores authentication details for a
specific Git provider (GitHub, GitLab, Bitbucket, Azure DevOps, etc.).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Git credential tools with the MCP server."""

    # ── Git Credentials ──────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_git_credentials() -> str:
        """List all Git credentials for the current user.

        Returns metadata about each stored Git credential including the
        provider, username, and credential ID.

        Returns:
            JSON array of Git credential objects with credential_id,
            git_provider, and git_username. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.git_credentials.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_git_credential(credential_id: int) -> str:
        """Get detailed information about a specific Git credential.

        Args:
            credential_id: The unique numeric identifier of the Git credential.

        Returns:
            JSON object with credential details including credential_id,
            git_provider, and git_username.
        """
        try:
            w = get_workspace_client()
            result = w.git_credentials.get(credential_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_git_credential(
        git_provider: str,
        git_username: str,
        personal_access_token: str,
    ) -> str:
        """Create a new Git credential for the current user.

        Stores authentication details for a Git provider. This credential
        will be used when cloning repos or syncing Git folders from the
        specified provider.

        Args:
            git_provider: The Git provider name. Common values: "gitHub",
                          "gitLab", "bitbucketCloud", "bitbucketServer",
                          "azureDevOpsServices", "awsCodeCommit".
            git_username: The Git username for authentication.
            personal_access_token: A personal access token or app password
                                   for the Git provider. This is stored
                                   securely and never returned in responses.

        Returns:
            JSON object with the created credential's details including
            credential_id, git_provider, and git_username.
        """
        try:
            w = get_workspace_client()
            result = w.git_credentials.create(
                git_provider=git_provider,
                git_username=git_username,
                personal_access_token=personal_access_token,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_git_credential(
        credential_id: int,
        git_provider: str,
        git_username: str,
        personal_access_token: str,
    ) -> str:
        """Update an existing Git credential.

        Replaces the provider, username, and token for the specified
        credential. All fields are required.

        Args:
            credential_id: The unique numeric identifier of the credential
                           to update.
            git_provider: The Git provider name (e.g. "gitHub", "gitLab").
            git_username: The new Git username.
            personal_access_token: The new personal access token. Stored
                                   securely and never returned in responses.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.git_credentials.update(
                credential_id=credential_id,
                git_provider=git_provider,
                git_username=git_username,
                personal_access_token=personal_access_token,
            )
            return f"Git credential '{credential_id}' updated successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_git_credential(credential_id: int) -> str:
        """Delete a Git credential.

        Removes the stored authentication details. Any Repos or Git folders
        using this credential will no longer be able to sync until a new
        credential is configured.

        Args:
            credential_id: The unique numeric identifier of the credential
                           to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.git_credentials.delete(credential_id)
            return f"Git credential '{credential_id}' deleted successfully."
        except Exception as e:
            return format_error(e)
