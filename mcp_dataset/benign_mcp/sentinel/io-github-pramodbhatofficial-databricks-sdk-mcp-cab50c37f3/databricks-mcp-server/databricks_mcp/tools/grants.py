"""Unity Catalog grants (permission) management tools for Databricks MCP.

Provides tools for viewing and updating permissions on Unity Catalog securables
such as catalogs, schemas, tables, volumes, functions, and registered models.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all grants management tools with the MCP server."""

    @mcp.tool()
    def databricks_get_grants(securable_type: str, full_name: str) -> str:
        """Get the permissions granted on a Unity Catalog securable.

        Returns all privilege assignments for the specified securable object,
        showing which principals have which privileges.

        Args:
            securable_type: The type of the securable object. Must be one of:
                            "CATALOG", "SCHEMA", "TABLE", "VOLUME", "FUNCTION",
                            "REGISTERED_MODEL", "EXTERNAL_LOCATION",
                            "STORAGE_CREDENTIAL", "METASTORE", "CONNECTION",
                            "SHARE", "RECIPIENT", "PROVIDER".
            full_name: The full name of the securable. Format depends on type:
                       - CATALOG: "my_catalog"
                       - SCHEMA: "my_catalog.my_schema"
                       - TABLE: "my_catalog.my_schema.my_table"
                       - METASTORE: the metastore ID

        Returns:
            JSON object with privilege_assignments, each containing a principal
            and their list of privileges.
        """
        try:
            from databricks.sdk.service.catalog import SecurableType

            w = get_workspace_client()
            result = w.grants.get(
                securable_type=SecurableType(securable_type),
                full_name=full_name,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_effective_grants(securable_type: str, full_name: str) -> str:
        """Get the effective (inherited + direct) permissions on a securable.

        Returns the effective permissions for the calling user on the specified
        securable, including permissions inherited from parent objects.

        Args:
            securable_type: The type of the securable object. Must be one of:
                            "CATALOG", "SCHEMA", "TABLE", "VOLUME", "FUNCTION",
                            "REGISTERED_MODEL", "EXTERNAL_LOCATION",
                            "STORAGE_CREDENTIAL", "METASTORE", "CONNECTION",
                            "SHARE", "RECIPIENT", "PROVIDER".
            full_name: The full name of the securable. Format depends on type:
                       - CATALOG: "my_catalog"
                       - SCHEMA: "my_catalog.my_schema"
                       - TABLE: "my_catalog.my_schema.my_table"
                       - METASTORE: the metastore ID

        Returns:
            JSON object with privilege_assignments showing effective permissions
            including those inherited from parent securables.
        """
        try:
            from databricks.sdk.service.catalog import SecurableType

            w = get_workspace_client()
            result = w.grants.get_effective(
                securable_type=SecurableType(securable_type),
                full_name=full_name,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_grants(securable_type: str, full_name: str, changes_json: str) -> str:
        """Update (grant or revoke) permissions on a Unity Catalog securable.

        Applies a list of permission changes. Each change specifies a principal,
        a list of privileges to add, and a list of privileges to remove.

        Args:
            securable_type: The type of the securable object. Must be one of:
                            "CATALOG", "SCHEMA", "TABLE", "VOLUME", "FUNCTION",
                            "REGISTERED_MODEL", "EXTERNAL_LOCATION",
                            "STORAGE_CREDENTIAL", "METASTORE", "CONNECTION",
                            "SHARE", "RECIPIENT", "PROVIDER".
            full_name: The full name of the securable. Format depends on type.
            changes_json: A JSON string representing a list of permission changes.
                          Each element must have "principal" (str) and optionally
                          "add" (list of privilege strings) and "remove" (list of
                          privilege strings).
                          Example: '[{"principal": "user@example.com",
                          "add": ["SELECT", "MODIFY"], "remove": []}]'

        Returns:
            JSON object with the updated privilege_assignments.
        """
        try:
            import json

            from databricks.sdk.service.catalog import (
                PermissionsChange,
                Privilege,
                SecurableType,
            )

            w = get_workspace_client()
            raw_changes = json.loads(changes_json)

            changes = []
            for entry in raw_changes:
                change = PermissionsChange(
                    principal=entry["principal"],
                    add=[Privilege(p) for p in entry.get("add", [])],
                    remove=[Privilege(p) for p in entry.get("remove", [])],
                )
                changes.append(change)

            result = w.grants.update(
                securable_type=SecurableType(securable_type),
                full_name=full_name,
                changes=changes,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)
