"""Unity Catalog management tools for Databricks MCP.

Provides tools for managing catalogs, schemas, tables, volumes, functions,
and registered models within Unity Catalog.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Unity Catalog tools with the MCP server."""

    # ── Catalogs ────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_catalogs() -> str:
        """List all catalogs in the Unity Catalog metastore.

        Returns a JSON array of catalog objects, each containing name, owner,
        comment, and other metadata. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.catalogs.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_catalog(name: str) -> str:
        """Get detailed information about a specific catalog.

        Args:
            name: The name of the catalog to retrieve (e.g. "my_catalog").

        Returns:
            JSON object with catalog details including name, owner, comment,
            created_at, updated_at, and properties.
        """
        try:
            w = get_workspace_client()
            result = w.catalogs.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_catalog(name: str, comment: str = "") -> str:
        """Create a new catalog in the Unity Catalog metastore.

        The caller must be a metastore admin or have the CREATE_CATALOG privilege.

        Args:
            name: Name for the new catalog. Must be unique within the metastore.
            comment: Optional human-readable description of the catalog.

        Returns:
            JSON object with the created catalog's details.
        """
        try:
            w = get_workspace_client()
            result = w.catalogs.create(name=name, comment=comment)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_catalog(name: str, force: bool = False) -> str:
        """Delete a catalog from the Unity Catalog metastore.

        The caller must be the catalog owner or a metastore admin.

        Args:
            name: Name of the catalog to delete.
            force: If True, delete the catalog even if it contains schemas.
                   All child schemas (and their tables) will also be deleted.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.catalogs.delete(name, force=force)
            return f"Catalog '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Schemas ─────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_schemas(catalog_name: str) -> str:
        """List all schemas within a catalog.

        Args:
            catalog_name: Name of the parent catalog to list schemas from.

        Returns:
            JSON array of schema objects with name, catalog_name, comment,
            and other metadata. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.schemas.list(catalog_name=catalog_name))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_schema(full_name: str) -> str:
        """Get detailed information about a specific schema.

        Args:
            full_name: Full name of the schema in "catalog.schema" format
                       (e.g. "my_catalog.my_schema").

        Returns:
            JSON object with schema details including name, catalog_name,
            owner, comment, and properties.
        """
        try:
            w = get_workspace_client()
            result = w.schemas.get(full_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_schema(name: str, catalog_name: str, comment: str = "") -> str:
        """Create a new schema within a catalog.

        The caller must be a metastore admin or have the CREATE_SCHEMA privilege
        on the parent catalog.

        Args:
            name: Name for the new schema, relative to the parent catalog.
            catalog_name: Name of the parent catalog.
            comment: Optional human-readable description of the schema.

        Returns:
            JSON object with the created schema's details.
        """
        try:
            w = get_workspace_client()
            result = w.schemas.create(name=name, catalog_name=catalog_name, comment=comment)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_schema(full_name: str) -> str:
        """Delete a schema from Unity Catalog.

        The caller must be the schema owner or an owner of the parent catalog.

        Args:
            full_name: Full name of the schema in "catalog.schema" format
                       (e.g. "my_catalog.my_schema").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.schemas.delete(full_name)
            return f"Schema '{full_name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Tables ──────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_tables(catalog_name: str, schema_name: str) -> str:
        """List all tables within a schema.

        Args:
            catalog_name: Name of the parent catalog.
            schema_name: Name of the schema to list tables from.

        Returns:
            JSON array of table objects with name, catalog_name, schema_name,
            table_type, and other metadata. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.tables.list(catalog_name=catalog_name, schema_name=schema_name))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_table(full_name: str) -> str:
        """Get detailed information about a specific table.

        Args:
            full_name: Full three-level name of the table in
                       "catalog.schema.table" format
                       (e.g. "my_catalog.my_schema.my_table").

        Returns:
            JSON object with table details including columns, table_type,
            data_source_format, storage_location, and properties.
        """
        try:
            w = get_workspace_client()
            result = w.tables.get(full_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_table(full_name: str) -> str:
        """Delete a table from Unity Catalog.

        The caller must be the table owner or a metastore admin.

        Args:
            full_name: Full three-level name of the table in
                       "catalog.schema.table" format
                       (e.g. "my_catalog.my_schema.my_table").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.tables.delete(full_name)
            return f"Table '{full_name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Volumes ─────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_volumes(catalog_name: str, schema_name: str) -> str:
        """List all volumes within a schema.

        Volumes are Unity Catalog objects that provide access to cloud storage
        locations for data files.

        Args:
            catalog_name: Name of the parent catalog.
            schema_name: Name of the schema to list volumes from.

        Returns:
            JSON array of volume objects with name, catalog_name, schema_name,
            volume_type, and storage_location. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.volumes.list(catalog_name=catalog_name, schema_name=schema_name))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_volume(
        name: str,
        catalog_name: str,
        schema_name: str,
        volume_type: str = "MANAGED",
        comment: str = "",
    ) -> str:
        """Create a new volume within a schema.

        Volumes provide governed access to cloud storage locations for data files.

        Args:
            name: Name for the new volume.
            catalog_name: Name of the parent catalog.
            schema_name: Name of the parent schema.
            volume_type: Type of volume — "MANAGED" (default, Databricks-managed
                         storage) or "EXTERNAL" (external storage location).
            comment: Optional human-readable description of the volume.

        Returns:
            JSON object with the created volume's details.
        """
        try:
            from databricks.sdk.service.catalog import VolumeType

            w = get_workspace_client()
            result = w.volumes.create(
                name=name,
                catalog_name=catalog_name,
                schema_name=schema_name,
                volume_type=VolumeType(volume_type),
                comment=comment,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_volume(full_name: str) -> str:
        """Delete a volume from Unity Catalog.

        The caller must be the volume owner or a metastore admin.

        Args:
            full_name: Full three-level name of the volume in
                       "catalog.schema.volume" format
                       (e.g. "my_catalog.my_schema.my_volume").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.volumes.delete(full_name)
            return f"Volume '{full_name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Functions ───────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_functions(catalog_name: str, schema_name: str) -> str:
        """List all user-defined functions within a schema.

        Args:
            catalog_name: Name of the parent catalog.
            schema_name: Name of the schema to list functions from.

        Returns:
            JSON array of function objects with name, catalog_name,
            schema_name, input_params, and return type info.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.functions.list(catalog_name=catalog_name, schema_name=schema_name))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_function(full_name: str) -> str:
        """Get detailed information about a specific function.

        Args:
            full_name: Full three-level name of the function in
                       "catalog.schema.function" format
                       (e.g. "my_catalog.my_schema.my_function").

        Returns:
            JSON object with function details including name, input_params,
            data_type, full_data_type, and routine_body.
        """
        try:
            w = get_workspace_client()
            result = w.functions.get(full_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_function(full_name: str) -> str:
        """Delete a user-defined function from Unity Catalog.

        The caller must be the function owner or a metastore admin.

        Args:
            full_name: Full three-level name of the function in
                       "catalog.schema.function" format
                       (e.g. "my_catalog.my_schema.my_function").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.functions.delete(full_name)
            return f"Function '{full_name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Registered Models ───────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_registered_models(
        catalog_name: str = "",
        schema_name: str = "",
    ) -> str:
        """List registered models in Unity Catalog.

        Can optionally filter by catalog and schema. If both are empty,
        lists all registered models accessible to the caller.

        Args:
            catalog_name: Optional catalog name to filter models.
                          If provided with schema_name, lists models in that schema.
            schema_name: Optional schema name to filter models.
                         Requires catalog_name to also be provided.

        Returns:
            JSON array of registered model objects with name, catalog_name,
            schema_name, owner, and comment. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            kwargs = {}
            if catalog_name:
                kwargs["catalog_name"] = catalog_name
            if schema_name:
                kwargs["schema_name"] = schema_name
            results = paginate(w.registered_models.list(**kwargs))
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_registered_model(full_name: str) -> str:
        """Get detailed information about a specific registered model.

        Args:
            full_name: Full three-level name of the registered model in
                       "catalog.schema.model" format
                       (e.g. "my_catalog.my_schema.my_model").

        Returns:
            JSON object with model details including name, catalog_name,
            schema_name, owner, comment, and version information.
        """
        try:
            w = get_workspace_client()
            result = w.registered_models.get(full_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_catalog(name: str, comment: str = "", owner: str = "") -> str:
        """Update properties of an existing catalog.

        The caller must be the catalog owner or a metastore admin.
        Only non-empty fields are updated; other fields remain unchanged.

        Args:
            name: Name of the catalog to update.
            comment: Optional new description for the catalog. If empty,
                     the comment is not changed.
            owner: Optional new owner for the catalog. If empty, the
                   owner is not changed.

        Returns:
            JSON object with the updated catalog's details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {}
            if comment:
                kwargs["comment"] = comment
            if owner:
                kwargs["owner"] = owner
            if not kwargs:
                return to_json({
                    "status": "no_change",
                    "message": "No fields provided to update. Specify comment and/or owner.",
                })
            result = w.catalogs.update(name, **kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_schema(full_name: str, comment: str = "", owner: str = "") -> str:
        """Update properties of an existing schema.

        The caller must be the schema owner or an owner of the parent catalog.
        Only non-empty fields are updated; other fields remain unchanged.

        Args:
            full_name: Full name of the schema in "catalog.schema" format
                       (e.g. "my_catalog.my_schema").
            comment: Optional new description for the schema. If empty,
                     the comment is not changed.
            owner: Optional new owner for the schema. If empty, the
                   owner is not changed.

        Returns:
            JSON object with the updated schema's details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {}
            if comment:
                kwargs["comment"] = comment
            if owner:
                kwargs["owner"] = owner
            if not kwargs:
                return to_json({
                    "status": "no_change",
                    "message": "No fields provided to update. Specify comment and/or owner.",
                })
            result = w.schemas.update(full_name, **kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_registered_model(
        name: str,
        catalog_name: str,
        schema_name: str,
        comment: str = "",
    ) -> str:
        """Create a new registered model in Unity Catalog.

        Registered models are containers for ML model versions. They live
        within a catalog and schema, and each version can be served via
        a model serving endpoint.

        Args:
            name: Name for the new registered model.
            catalog_name: Name of the parent catalog.
            schema_name: Name of the parent schema.
            comment: Optional human-readable description of the model.

        Returns:
            JSON object with the created registered model's details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {
                "name": name,
                "catalog_name": catalog_name,
                "schema_name": schema_name,
            }
            if comment:
                kwargs["comment"] = comment
            result = w.registered_models.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_registered_model(full_name: str) -> str:
        """Delete a registered model from Unity Catalog.

        Permanently removes the registered model and all its versions.
        The caller must be the model owner or a metastore admin.
        This action cannot be undone.

        Args:
            full_name: Full three-level name of the registered model in
                       "catalog.schema.model" format
                       (e.g. "my_catalog.my_schema.my_model").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.registered_models.delete(full_name)
            return f"Registered model '{full_name}' deleted successfully."
        except Exception as e:
            return format_error(e)
