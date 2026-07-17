"""Lakehouse quality monitor tools for Databricks MCP.

Provides tools for creating and managing data quality monitors on
Unity Catalog tables. Quality monitors track data quality metrics,
detect drift, and generate profile and drift tables that can be
queried for analysis.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all quality monitor tools with the MCP server."""

    # ── Quality Monitors ─────────────────────────────────────────────────

    @mcp.tool()
    def databricks_create_quality_monitor(
        table_name: str,
        output_schema_name: str,
        assets_dir: str,
        monitor_type: str = "SNAPSHOT",
        slicing_exprs: str = "",
        baseline_table_name: str = "",
    ) -> str:
        """Create a quality monitor on a Unity Catalog table.

        Sets up automated data quality monitoring that generates profile
        and drift metrics tables. The monitor must be refreshed to compute
        initial metrics.

        Args:
            table_name: Full three-level name of the table to monitor in
                        "catalog.schema.table" format.
            output_schema_name: Full name of the schema where profile and
                                drift tables will be created, in
                                "catalog.schema" format.
            assets_dir: Path in the workspace where monitor dashboard and
                        configuration assets are stored (e.g. "/Shared/monitors").
            monitor_type: Type of monitor. One of "SNAPSHOT" (point-in-time
                          profile), "TIME_SERIES" (time-based analysis), or
                          "INFERENCE" (ML model monitoring). Defaults to
                          "SNAPSHOT".
            slicing_exprs: Optional comma-separated list of column expressions
                           to slice metrics by (e.g. "col1,col2"). Leave empty
                           for no slicing.
            baseline_table_name: Optional full name of a baseline table for
                                 drift comparison in "catalog.schema.table"
                                 format. Leave empty for no baseline.

        Returns:
            JSON object with the created monitor's configuration details.
        """
        try:
            from databricks.sdk.service.catalog import MonitorSnapshot

            w = get_workspace_client()
            kwargs: dict = {
                "table_name": table_name,
                "output_schema_name": output_schema_name,
                "assets_dir": assets_dir,
            }

            # Configure the monitor type-specific settings
            if monitor_type == "SNAPSHOT":
                kwargs["snapshot"] = MonitorSnapshot()

            if slicing_exprs:
                kwargs["slicing_exprs"] = [s.strip() for s in slicing_exprs.split(",")]

            if baseline_table_name:
                kwargs["baseline_table_name"] = baseline_table_name

            result = w.quality_monitors.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_quality_monitor(table_name: str) -> str:
        """Get the quality monitor configuration for a table.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.

        Returns:
            JSON object with monitor configuration including output_schema_name,
            assets_dir, monitor_type, schedule, and status information.
        """
        try:
            w = get_workspace_client()
            result = w.quality_monitors.get(table_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_quality_monitor(
        table_name: str,
        output_schema_name: str,
        assets_dir: str,
        slicing_exprs: str = "",
        baseline_table_name: str = "",
    ) -> str:
        """Update the quality monitor configuration for a table.

        Modifies the monitor's output schema, assets directory, slicing
        expressions, or baseline table. A refresh is needed after the
        update for changes to take effect on metrics.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.
            output_schema_name: Full name of the schema for profile and
                                drift tables in "catalog.schema" format.
            assets_dir: Path for monitor dashboard and config assets.
            slicing_exprs: Optional comma-separated list of column expressions
                           to slice metrics by. Leave empty for no slicing.
            baseline_table_name: Optional full name of a baseline table for
                                 drift comparison. Leave empty to remove baseline.

        Returns:
            JSON object with the updated monitor configuration.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {
                "table_name": table_name,
                "output_schema_name": output_schema_name,
                "assets_dir": assets_dir,
            }

            if slicing_exprs:
                kwargs["slicing_exprs"] = [s.strip() for s in slicing_exprs.split(",")]

            if baseline_table_name:
                kwargs["baseline_table_name"] = baseline_table_name

            result = w.quality_monitors.update(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_quality_monitor(table_name: str) -> str:
        """Delete the quality monitor from a table.

        Removes the monitor configuration. The profile and drift metric
        tables in the output schema are NOT deleted and can be cleaned
        up separately if desired.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.quality_monitors.delete(table_name)
            return f"Quality monitor on '{table_name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Monitor Refreshes ────────────────────────────────────────────────

    @mcp.tool()
    def databricks_run_quality_monitor_refresh(table_name: str) -> str:
        """Trigger a refresh of the quality monitor for a table.

        Starts an asynchronous computation of data quality metrics. The
        refresh updates the profile and drift tables in the output schema.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.

        Returns:
            JSON object with refresh details including refresh_id and state.
        """
        try:
            w = get_workspace_client()
            result = w.quality_monitors.run_refresh(table_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_quality_monitor_refresh(
        table_name: str,
        refresh_id: str,
    ) -> str:
        """Get the status of a specific quality monitor refresh.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.
            refresh_id: The unique identifier of the refresh run.

        Returns:
            JSON object with refresh details including refresh_id, state
            (PENDING, RUNNING, SUCCESS, FAILED, CANCELED), start_time,
            and end_time.
        """
        try:
            w = get_workspace_client()
            result = w.quality_monitors.get_refresh(table_name, refresh_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_quality_monitor_refreshes(table_name: str) -> str:
        """List all refresh runs for a quality monitor.

        Returns the history of refresh runs for the specified monitor,
        including completed, running, and failed refreshes.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.

        Returns:
            JSON array of refresh objects with refresh_id, state,
            start_time, and end_time. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            result = w.quality_monitors.list_refreshes(table_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_cancel_quality_monitor_refresh(
        table_name: str,
        refresh_id: str,
    ) -> str:
        """Cancel a running quality monitor refresh.

        Attempts to cancel a refresh that is currently in progress. If the
        refresh has already completed or failed, this has no effect.

        Args:
            table_name: Full three-level name of the monitored table in
                        "catalog.schema.table" format.
            refresh_id: The unique identifier of the refresh run to cancel.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.quality_monitors.cancel_refresh(table_name, refresh_id)
            return f"Refresh '{refresh_id}' on monitor '{table_name}' cancellation requested."
        except Exception as e:
            return format_error(e)
