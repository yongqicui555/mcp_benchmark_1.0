"""Online table management tools for Databricks MCP.

Provides tools for creating, retrieving, and deleting online tables.
Online tables are optimized read replicas of Delta tables that provide
low-latency, high-throughput access for real-time serving use cases
such as feature serving and RAG applications.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all online table tools with the MCP server."""

    @mcp.tool()
    def databricks_create_online_table(
        name: str,
        source_table_full_name: str,
        primary_key_columns_json: str,
        run_triggered: bool = False,
    ) -> str:
        """Create a new online table backed by a Delta table.

        Creates a read-optimized replica of the source Delta table for
        low-latency lookups. The online table automatically syncs with
        the source table.

        Args:
            name: Full three-level name for the online table
                  (e.g. "my_catalog.my_schema.my_online_table").
            source_table_full_name: Full three-level name of the source Delta table
                                    (e.g. "my_catalog.my_schema.my_source_table").
            primary_key_columns_json: JSON array of column names that form the
                                      primary key (e.g. '["id"]' or '["user_id", "item_id"]').
            run_triggered: If True, use triggered (manual) sync mode instead of
                           continuous. Defaults to False (continuous sync).

        Returns:
            JSON object with the created online table's details including
            name, status, and sync configuration.
        """
        try:
            import json

            from databricks.sdk.service.catalog import (
                OnlineTable,
                OnlineTableSpec,
            )

            w = get_workspace_client()
            primary_key_columns = json.loads(primary_key_columns_json)

            spec_kwargs: dict = {
                "source_table_full_name": source_table_full_name,
                "primary_key_columns": primary_key_columns,
            }

            # Set sync mode: triggered or continuous (default)
            if run_triggered:
                from databricks.sdk.service.catalog import OnlineTableSpecTriggeredSchedulingPolicy

                spec_kwargs["run_triggered"] = OnlineTableSpecTriggeredSchedulingPolicy()
            else:
                from databricks.sdk.service.catalog import OnlineTableSpecContinuousSchedulingPolicy

                spec_kwargs["run_continuously"] = OnlineTableSpecContinuousSchedulingPolicy()

            table = OnlineTable(
                name=name,
                spec=OnlineTableSpec(**spec_kwargs),
            )

            result = w.online_tables.create(table=table)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_online_table(name: str) -> str:
        """Get detailed information about a specific online table.

        Returns the online table's configuration, sync status, and metadata.

        Args:
            name: Full three-level name of the online table
                  (e.g. "my_catalog.my_schema.my_online_table").

        Returns:
            JSON object with online table details including name, spec
            (source table, primary key columns, sync mode), status, and
            table_serving_url.
        """
        try:
            w = get_workspace_client()
            result = w.online_tables.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_online_table(name: str) -> str:
        """Delete an online table.

        Removes the online table and stops syncing from the source Delta table.
        The source Delta table is not affected.

        Args:
            name: Full three-level name of the online table to delete
                  (e.g. "my_catalog.my_schema.my_online_table").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.online_tables.delete(name)
            return f"Online table '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)
