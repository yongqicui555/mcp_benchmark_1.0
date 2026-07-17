"""Secret scope and secret management tools for Databricks MCP.

Provides tools for creating and managing secret scopes, storing and deleting
secrets, and controlling access to secrets via ACLs. Secret values are
write-only through the API -- listing secrets returns metadata (key names
and last-updated timestamps) but never the secret values themselves.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all secret management tools with the MCP server."""

    # -- Secret Scopes --------------------------------------------------------

    @mcp.tool()
    def databricks_list_secret_scopes() -> str:
        """List all secret scopes in the workspace.

        Secret scopes are containers for secrets. Each scope has a name and a
        backend type (DATABRICKS or AZURE_KEYVAULT).

        Returns:
            JSON array of secret scope objects, each containing name,
            backend_type, and keyvault_metadata (if applicable).
        """
        try:
            w = get_workspace_client()
            results = paginate(w.secrets.list_scopes())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_secret_scope(scope: str) -> str:
        """Create a new Databricks-backed secret scope.

        The scope name must be unique within the workspace. The caller must have
        workspace-level MANAGE permission or be an admin.

        Args:
            scope: Name for the new secret scope. Must be unique within the
                   workspace and consist of alphanumeric characters, dashes,
                   underscores, and periods.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.secrets.create_scope(scope=scope)
            return f"Secret scope '{scope}' created successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_secret_scope(scope: str) -> str:
        """Delete a secret scope and all of its secrets.

        This is a destructive operation -- all secrets within the scope will be
        permanently deleted. The caller must have MANAGE permission on the scope.

        Args:
            scope: Name of the secret scope to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.secrets.delete_scope(scope=scope)
            return f"Secret scope '{scope}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # -- Secrets ---------------------------------------------------------------

    @mcp.tool()
    def databricks_list_secrets(scope: str) -> str:
        """List the metadata of all secrets within a scope.

        Returns key names and last-updated timestamps only. Secret values are
        never returned through the API for security reasons.

        Args:
            scope: Name of the secret scope to list secrets from.

        Returns:
            JSON array of secret metadata objects, each containing the key name
            and last_updated_timestamp. Does NOT include secret values.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.secrets.list_secrets(scope=scope))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_put_secret(scope: str, key: str, string_value: str) -> str:
        """Store a secret value in a scope, creating or overwriting the key.

        If the key already exists, its value is overwritten. The caller must
        have WRITE or MANAGE permission on the scope.

        Args:
            scope: Name of the secret scope to store the secret in.
            key: Name of the secret key. Must be unique within the scope.
            string_value: The secret value to store as a UTF-8 string.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.secrets.put_secret(scope=scope, key=key, string_value=string_value)
            return f"Secret '{key}' stored in scope '{scope}' successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_secret(scope: str, key: str) -> str:
        """Delete a secret from a scope.

        The caller must have WRITE or MANAGE permission on the scope.

        Args:
            scope: Name of the secret scope containing the secret.
            key: Name of the secret key to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.secrets.delete_secret(scope=scope, key=key)
            return f"Secret '{key}' deleted from scope '{scope}' successfully."
        except Exception as e:
            return format_error(e)

    # -- Secret ACLs -----------------------------------------------------------

    @mcp.tool()
    def databricks_list_secret_acls(scope: str) -> str:
        """List access control entries for a secret scope.

        Returns all ACLs that have been set on the given scope, showing which
        principals have READ, WRITE, or MANAGE permissions.

        Args:
            scope: Name of the secret scope to list ACLs for.

        Returns:
            JSON array of ACL objects, each containing principal and permission.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.secrets.list_acls(scope=scope))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_put_secret_acl(scope: str, principal: str, permission: str) -> str:
        """Set an access control entry on a secret scope.

        Creates or overwrites the ACL for the given principal on the scope.
        The caller must have MANAGE permission on the scope.

        Args:
            scope: Name of the secret scope to set the ACL on.
            principal: The principal (user or group) to grant access to.
                       Use the user's email address or the group name.
            permission: Permission level to grant. Must be one of:
                        "READ" (can read secrets), "WRITE" (can read and write
                        secrets), or "MANAGE" (full control including ACLs).

        Returns:
            Confirmation message on success.
        """
        try:
            from databricks.sdk.service.workspace import AclPermission

            w = get_workspace_client()
            w.secrets.put_acl(
                scope=scope,
                principal=principal,
                permission=AclPermission[permission],
            )
            return f"ACL set on scope '{scope}': {principal} -> {permission}."
        except Exception as e:
            return format_error(e)
