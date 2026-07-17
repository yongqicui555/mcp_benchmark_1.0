"""Unity Catalog metastore management tools for Databricks MCP.

Provides tools for listing, creating, updating, deleting, and assigning
Unity Catalog metastores. Metastores are the top-level container for
Unity Catalog metadata — each workspace is assigned to exactly one metastore.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all metastore management tools with the MCP server."""

    @mcp.tool()
    def databricks_list_metastores() -> str:
        """List all Unity Catalog metastores accessible to the caller.

        Returns metastore metadata including name, storage root, owner,
        and region. Typically there is one metastore per region.

        Returns:
            JSON array of metastore objects with metastore_id, name,
            storage_root, owner, region, and other metadata.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.metastores.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_metastore(id: str) -> str:
        """Get detailed information about a specific metastore.

        Args:
            id: The unique identifier (UUID) of the metastore.

        Returns:
            JSON object with metastore details including metastore_id, name,
            storage_root, default_data_access_config_id, owner, region,
            created_at, and updated_at.
        """
        try:
            w = get_workspace_client()
            result = w.metastores.get(id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_current_metastore() -> str:
        """Get the metastore assigned to the current workspace.

        Returns the metastore that is currently assigned to the workspace
        where the API call is made.

        Returns:
            JSON object with the current metastore's details including
            metastore_id, name, storage_root, owner, and region.
        """
        try:
            w = get_workspace_client()
            result = w.metastores.current()
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_metastore_summary() -> str:
        """Get a summary of the metastore assigned to the current workspace.

        Returns summary information about the metastore including its
        configuration and current status.

        Returns:
            JSON object with metastore summary including metastore_id, name,
            storage_root, owner, cloud, and global_metastore_id.
        """
        try:
            w = get_workspace_client()
            result = w.metastores.summary()
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_metastore(name: str, storage_root: str, region: str = "") -> str:
        """Create a new Unity Catalog metastore.

        Creates a metastore with the given name and cloud storage root.
        The caller must be an account admin. Each region typically has
        one metastore.

        Args:
            name: Name for the new metastore. Must be unique within the account.
            storage_root: Cloud storage root URL for the metastore's managed data
                          (e.g. "s3://my-bucket/metastore" or
                          "abfss://container@account.dfs.core.windows.net/metastore").
            region: Optional cloud region for the metastore (e.g. "us-east-1").

        Returns:
            JSON object with the created metastore's details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"name": name, "storage_root": storage_root}
            if region:
                kwargs["region"] = region
            result = w.metastores.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_metastore(
        id: str,
        name: str = "",
        owner: str = "",
        storage_root_credential_id: str = "",
    ) -> str:
        """Update properties of an existing metastore.

        Only provided fields are updated. The caller must be the metastore
        owner or an account admin.

        Args:
            id: The unique identifier (UUID) of the metastore to update.
            name: Optional new name for the metastore.
            owner: Optional new owner of the metastore (user or group name).
            storage_root_credential_id: Optional ID of the storage credential
                                        to use for the metastore's root storage.

        Returns:
            JSON object with the updated metastore details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"id": id}
            if name:
                kwargs["name"] = name
            if owner:
                kwargs["owner"] = owner
            if storage_root_credential_id:
                kwargs["storage_root_credential_id"] = storage_root_credential_id
            result = w.metastores.update(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_metastore(id: str, force: bool = False) -> str:
        """Delete a Unity Catalog metastore.

        This is a destructive operation. If force=True, the metastore is
        deleted even if it contains catalogs, schemas, or tables.
        The caller must be an account admin.

        Args:
            id: The unique identifier (UUID) of the metastore to delete.
            force: If True, forcibly delete the metastore and all its contents.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.metastores.delete(id, force=force)
            return f"Metastore '{id}' deleted successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_assign_metastore(
        workspace_id: int,
        metastore_id: str,
        default_catalog_name: str = "main",
    ) -> str:
        """Assign a metastore to a workspace.

        Each workspace can be assigned to exactly one metastore. This operation
        binds the workspace to the metastore, enabling Unity Catalog features.
        The caller must be an account admin.

        Args:
            workspace_id: The numeric ID of the Databricks workspace.
            metastore_id: The unique identifier (UUID) of the metastore to assign.
            default_catalog_name: The name of the default catalog to use in the
                                  workspace (default: "main").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.metastores.assign(
                workspace_id=workspace_id,
                metastore_id=metastore_id,
                default_catalog_name=default_catalog_name,
            )
            return (
                f"Metastore '{metastore_id}' assigned to workspace {workspace_id} "
                f"with default catalog '{default_catalog_name}'."
            )
        except Exception as e:
            return format_error(e)
