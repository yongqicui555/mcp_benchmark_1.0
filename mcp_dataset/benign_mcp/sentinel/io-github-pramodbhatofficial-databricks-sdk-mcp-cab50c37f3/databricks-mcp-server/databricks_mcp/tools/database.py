"""Databricks Lakebase (PostgreSQL) database management tools.

Provides MCP tools for managing Lakebase database instances, catalogs,
tables, credentials, and roles. Lakebase is Databricks' managed PostgreSQL
service that integrates with Unity Catalog for governance.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Databricks Lakebase database tools with the MCP server."""

    @mcp.tool()
    def databricks_list_database_instances() -> str:
        """List all Lakebase PostgreSQL database instances in the workspace.

        Returns all database instances with their names, states, connection
        info, and capacity. Use this to discover available database instances
        before performing operations on them.

        Returns:
            JSON array of database instance objects with instance name, state,
            connection details, and capacity information.
        """
        try:
            w = get_workspace_client()
            instances = paginate(w.database.list_database_instances())
            return to_json({"instances": instances, "count": len(instances)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_database_instance(name: str) -> str:
        """Get detailed information about a specific Lakebase database instance.

        Retrieves the full configuration, status, and connection details for
        a database instance. Includes hostname, port, and connection strings
        needed to connect to the PostgreSQL instance.

        Args:
            name: The name of the database instance to retrieve.

        Returns:
            JSON object with instance name, state, hostname, port,
            connection_string, jdbc_connection_url, and capacity details.
        """
        try:
            w = get_workspace_client()
            result = w.database.get_database_instance(name=name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_database_instance(name: str, capacity: int = 1) -> str:
        """Create a new Lakebase PostgreSQL database instance.

        Provisions a new managed PostgreSQL instance in the workspace. The
        instance will be integrated with Unity Catalog for governance.

        This is an asynchronous operation. The instance will be provisioned
        in the background. Use databricks_get_database_instance to check
        its status.

        Args:
            name: The name for the new database instance. Must be unique
                  within the workspace.
            capacity: The compute capacity for the instance. Defaults to 1
                      (smallest size). Higher values provide more resources.

        Returns:
            Confirmation that instance creation has been initiated, along with
            the instance name for status checking.
        """
        try:
            from databricks.sdk.service.database import DatabaseInstance

            w = get_workspace_client()
            result = w.database.create_database_instance(
                database_instance=DatabaseInstance(name=name, capacity=capacity),
            )
            return to_json({
                "status": "creating",
                "message": f"Database instance '{name}' creation initiated. "
                           f"Use databricks_get_database_instance to check status.",
                "instance": result,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_database_instance(
        name: str,
        force: bool = False,
        purge: bool = True,
    ) -> str:
        """Delete a Lakebase PostgreSQL database instance.

        Deletes the specified database instance. By default this is a hard
        delete (purge=True). Use force=True to also delete any descendant
        instances.

        WARNING: This permanently destroys the database and all its data.
        This action cannot be undone when purge is True.

        Args:
            name: The name of the database instance to delete.
            force: If True, also delete any descendant instances. Defaults to
                   False, which prevents deletion if descendants exist.
            purge: If True (default), hard delete the instance permanently.
                   If False, soft delete (may be recoverable).

        Returns:
            Confirmation that the deletion has been initiated.
        """
        try:
            w = get_workspace_client()
            w.database.delete_database_instance(
                name=name,
                force=force,
                purge=purge,
            )
            return to_json({
                "status": "deleting",
                "message": f"Database instance '{name}' deletion initiated "
                           f"(force={force}, purge={purge}).",
                "name": name,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_database_catalogs(instance_name: str) -> str:
        """List all catalogs in a Lakebase database instance.

        Returns the catalogs (logical databases) within the specified
        database instance. Each catalog can contain multiple schemas
        and tables.

        Args:
            instance_name: The name of the database instance whose catalogs
                           to list.

        Returns:
            JSON array of catalog objects with names and properties.
        """
        try:
            w = get_workspace_client()
            # The SDK may return a list or an iterator depending on version
            result = w.database.list_database_catalogs(instance_name=instance_name)
            # Handle both iterator and direct response patterns
            if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                catalogs = paginate(result)
            else:
                catalogs = to_json(result)
                return catalogs
            return to_json({
                "instance_name": instance_name,
                "catalogs": catalogs,
                "count": len(catalogs),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_database_catalog(
        instance_name: str,
        catalog_name: str,
    ) -> str:
        """Create a new catalog in a Lakebase database instance.

        Creates a logical database (catalog) within the specified instance.
        Catalogs are the top-level organizational unit and contain schemas,
        which in turn contain tables.

        Args:
            instance_name: The name of the database instance in which to
                           create the catalog.
            catalog_name: The name for the new catalog. Must be unique within
                          the instance.

        Returns:
            JSON object with the created catalog's details.
        """
        try:
            from databricks.sdk.service.database import DatabaseCatalog

            w = get_workspace_client()
            result = w.database.create_database_catalog(
                instance_name=instance_name,
                catalog=DatabaseCatalog(name=catalog_name),
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_database_tables(
        instance_name: str,
        catalog_name: str,
        schema_name: str = "public",
    ) -> str:
        """List tables in a Lakebase database schema.

        Returns all tables within the specified catalog and schema of a
        database instance. Defaults to the "public" schema.

        Args:
            instance_name: The name of the database instance.
            catalog_name: The name of the catalog containing the tables.
            schema_name: The schema to list tables from. Defaults to "public".

        Returns:
            JSON array of table objects with names, columns, and metadata.
        """
        try:
            w = get_workspace_client()
            result = w.database.list_database_tables(
                instance_name=instance_name,
                catalog_name=catalog_name,
                schema_name=schema_name,
            )
            # Handle both iterator and direct response patterns
            if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                tables = paginate(result)
            else:
                return to_json(result)
            return to_json({
                "instance_name": instance_name,
                "catalog_name": catalog_name,
                "schema_name": schema_name,
                "tables": tables,
                "count": len(tables),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_database_table(
        instance_name: str,
        catalog_name: str,
        table_name: str,
        columns_json: str,
        schema_name: str = "public",
    ) -> str:
        """Create a new table in a Lakebase database schema.

        Creates a table by registering it in Unity Catalog. The columns
        should be specified as a JSON array of column definitions.

        Args:
            instance_name: The name of the database instance.
            catalog_name: The name of the catalog to create the table in.
            table_name: The name for the new table.
            columns_json: A JSON string representing the column definitions.
                          Format: [{"name": "id", "type": "INTEGER"},
                          {"name": "email", "type": "TEXT"}]
                          Supported types depend on the PostgreSQL version.
            schema_name: The schema to create the table in. Defaults to "public".

        Returns:
            JSON object with the created table's details, or an error message
            if the columns_json is malformed or the operation fails.
        """
        try:
            # Parse and validate the columns JSON
            try:
                columns = json.loads(columns_json)
            except json.JSONDecodeError as parse_err:
                return format_error(
                    ValueError(f"Invalid columns_json: {parse_err}. "
                               f"Expected format: [{{'name': 'col', 'type': 'TEXT'}}]")
                )

            from databricks.sdk.service.database import DatabaseTable

            w = get_workspace_client()

            # Build the fully qualified table name: instance.catalog.schema.table
            full_name = f"{instance_name}.{catalog_name}.{schema_name}.{table_name}"

            result = w.database.create_database_table(
                table=DatabaseTable(
                    name=full_name,
                    columns=columns,
                ),
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_generate_database_credential(instance_names: str) -> str:
        """Generate temporary PostgreSQL credentials for Lakebase instances.

        Generates short-lived credentials that can be used to connect directly
        to the PostgreSQL instances using standard PG clients (psql, psycopg, etc.).

        The returned credentials include the username, password, and connection
        parameters needed for direct database access. Credentials are temporary
        and will expire after a set period.

        Args:
            instance_names: Comma-separated list of database instance names to
                            scope the credential to (e.g., "my-instance" or
                            "instance-1,instance-2").

        Returns:
            JSON object with temporary credential details including username,
            password (token), host, port, and SSL mode for PostgreSQL connections.
        """
        try:
            w = get_workspace_client()
            names = [n.strip() for n in instance_names.split(",") if n.strip()]
            result = w.database.generate_database_credential(
                instance_names=names,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_database_roles(instance_name: str) -> str:
        """List all roles for a Lakebase database instance.

        Returns the database roles configured for the specified instance.
        Roles control access permissions within the PostgreSQL database.

        Args:
            instance_name: The name of the database instance whose roles to list.

        Returns:
            JSON array of role objects with names and permissions.
        """
        try:
            w = get_workspace_client()
            result = w.database.list_database_roles(instance_name=instance_name)
            # Handle both iterator and direct response patterns
            if hasattr(result, '__iter__') and not isinstance(result, (str, dict)):
                roles = paginate(result)
            else:
                return to_json(result)
            return to_json({
                "instance_name": instance_name,
                "roles": roles,
                "count": len(roles),
            })
        except Exception as e:
            return format_error(e)
