"""External connection management tools for Databricks MCP.

Provides tools for managing connections to external data sources via
Lakehouse Federation, including databases (MySQL, PostgreSQL, SQL Server,
Snowflake, BigQuery, etc.), HTTP endpoints, and other external systems.
Connections store authentication credentials and configuration needed to
access external data through Unity Catalog.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all connection management tools with the MCP server."""

    @mcp.tool()
    def databricks_list_connections() -> str:
        """List all external connections in the workspace.

        Returns connections configured for Lakehouse Federation and other
        external data access patterns. Each connection stores the type,
        host, port, and credential information needed to reach an external
        system.

        Returns:
            JSON array of connection objects, each containing name,
            connection_type, host, port, comment, owner, and created/updated
            timestamps. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.connections.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_connection(name: str) -> str:
        """Get detailed information about a specific connection.

        Args:
            name: The name of the connection to retrieve.

        Returns:
            JSON object with full connection details including name,
            connection_type, options (host, port, etc.), owner, comment,
            and timestamps.
        """
        try:
            w = get_workspace_client()
            result = w.connections.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_connection(
        name: str,
        connection_type: str,
        host: str,
        port: int = 443,
        options_json: str = "",
        comment: str = "",
    ) -> str:
        """Create a new external connection.

        Creates a connection object storing the credentials and configuration
        needed to access an external data source. The caller must have the
        CREATE_CONNECTION privilege on the metastore.

        Args:
            name: Unique name for the connection within the metastore.
            connection_type: The type of external system to connect to.
                             Valid values include: "BIGQUERY", "DATABRICKS",
                             "GLUE", "HIVE_METASTORE", "HTTP", "MYSQL",
                             "POSTGRESQL", "REDSHIFT", "SNOWFLAKE",
                             "SQLDW" (Azure Synapse), "SQLSERVER".
            host: Hostname or IP address of the external system.
            port: Port number for the connection (default 443).
            options_json: Optional JSON string of additional key-value options.
                          These vary by connection type but commonly include
                          authentication credentials. Example:
                          '{"user": "admin", "password": "secret"}'
            comment: Optional human-readable description of the connection.

        Returns:
            JSON object with the created connection's details.
        """
        try:
            from databricks.sdk.service.catalog import ConnectionType

            w = get_workspace_client()

            # Build options dict starting with host and port
            options: dict[str, str] = {"host": host, "port": str(port)}
            if options_json:
                extra = json.loads(options_json)
                options.update(extra)

            result = w.connections.create(
                name=name,
                connection_type=ConnectionType[connection_type],
                options=options,
                comment=comment,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_connection(
        name: str,
        options_json: str = "",
        new_name: str = "",
    ) -> str:
        """Update an existing connection's options or name.

        Updates the connection configuration. At least one of options_json or
        new_name must be provided. The caller must be the connection owner or
        a metastore admin.

        Args:
            name: Current name of the connection to update.
            options_json: Optional JSON string of key-value options to set.
                          This replaces the existing options entirely, so
                          include all desired options. Example:
                          '{"host": "new-host.example.com", "port": "5432"}'
            new_name: Optional new name for the connection. Leave empty to
                      keep the current name.

        Returns:
            JSON object with the updated connection's details.
        """
        try:
            w = get_workspace_client()

            # Build the options dict from JSON if provided
            options: dict[str, str] = {}
            if options_json:
                options = json.loads(options_json)

            kwargs: dict = {"name": name, "options": options}
            if new_name:
                kwargs["new_name"] = new_name

            result = w.connections.update(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_connection(name: str) -> str:
        """Delete an external connection.

        Permanently removes the connection and its stored credentials. Foreign
        catalogs that depend on this connection will no longer function. The
        caller must be the connection owner or a metastore admin.

        Args:
            name: Name of the connection to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.connections.delete(name)
            return f"Connection '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)
