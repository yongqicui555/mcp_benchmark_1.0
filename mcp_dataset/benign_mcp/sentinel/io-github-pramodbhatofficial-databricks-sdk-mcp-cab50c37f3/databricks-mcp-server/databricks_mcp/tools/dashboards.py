"""Databricks Lakeview (AI/BI) dashboard management tools.

Provides MCP tools for creating, updating, publishing, and managing
Lakeview dashboards. Lakeview is the next-generation dashboarding
experience in Databricks, supporting AI-powered analytics and
scheduled delivery.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Databricks Lakeview dashboard tools with the MCP server."""

    @mcp.tool()
    def databricks_list_dashboards() -> str:
        """List all Lakeview dashboards in the workspace.

        Returns a paginated list of dashboards with their IDs, display names,
        paths, and lifecycle status. Only active (non-trashed) dashboards are
        returned by default.

        Returns:
            JSON array of dashboard objects with dashboard_id, display_name,
            path, lifecycle_state, and warehouse_id. Limited to 100 results.
        """
        try:
            w = get_workspace_client()
            dashboards = paginate(w.lakeview.list())
            return to_json({"dashboards": dashboards, "count": len(dashboards)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_dashboard(dashboard_id: str) -> str:
        """Get detailed information about a specific Lakeview dashboard.

        Retrieves the full dashboard configuration including its display name,
        serialized layout, datasets, warehouse binding, and lifecycle state.

        Args:
            dashboard_id: The UUID identifying the dashboard
                          (e.g., "01ef1234-5678-abcd-ef90-1234567890ab").

        Returns:
            JSON object with complete dashboard details including dashboard_id,
            display_name, serialized_dashboard (layout JSON), warehouse_id,
            path, and lifecycle_state.
        """
        try:
            w = get_workspace_client()
            result = w.lakeview.get(dashboard_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_dashboard(
        display_name: str,
        warehouse_id: str,
        serialized_dashboard: str = "",
        parent_path: str = "",
    ) -> str:
        """Create a new Lakeview dashboard.

        Creates a draft dashboard with the specified name and warehouse.
        Optionally provide a serialized dashboard layout (JSON) to pre-populate
        the dashboard content, and a parent path for workspace organization.

        Args:
            display_name: The human-readable name for the dashboard
                          (e.g., "Sales Analytics Q4").
            warehouse_id: The ID of the SQL warehouse to use for executing
                          dashboard queries.
            serialized_dashboard: Optional JSON string containing the dashboard
                                  layout definition. If empty, creates a blank
                                  dashboard.
            parent_path: Optional workspace folder path where the dashboard
                         should be created (e.g., "/Workspace/Dashboards").

        Returns:
            JSON object with the created dashboard's details including its
            new dashboard_id.
        """
        try:
            from databricks.sdk.service.dashboards import Dashboard

            w = get_workspace_client()

            # Build the dashboard object with only non-empty fields
            dashboard_kwargs: dict = {
                "display_name": display_name,
                "warehouse_id": warehouse_id,
            }
            if serialized_dashboard:
                dashboard_kwargs["serialized_dashboard"] = serialized_dashboard
            if parent_path:
                dashboard_kwargs["parent_path"] = parent_path

            result = w.lakeview.create(dashboard=Dashboard(**dashboard_kwargs))
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_dashboard(
        dashboard_id: str,
        display_name: str = "",
        serialized_dashboard: str = "",
    ) -> str:
        """Update an existing Lakeview dashboard draft.

        Updates the specified dashboard with new display name and/or layout.
        Only the provided non-empty fields will be updated; other fields
        remain unchanged.

        Args:
            dashboard_id: The UUID identifying the dashboard to update.
            display_name: New display name for the dashboard. If empty,
                          the name is not changed.
            serialized_dashboard: New JSON string containing the updated
                                  dashboard layout. If empty, the layout
                                  is not changed.

        Returns:
            JSON object with the updated dashboard's details.
        """
        try:
            from databricks.sdk.service.dashboards import Dashboard

            w = get_workspace_client()

            # Build update with only non-empty fields
            dashboard_kwargs: dict = {}
            if display_name:
                dashboard_kwargs["display_name"] = display_name
            if serialized_dashboard:
                dashboard_kwargs["serialized_dashboard"] = serialized_dashboard

            if not dashboard_kwargs:
                return to_json({
                    "status": "no_change",
                    "message": "No fields provided to update. Specify display_name "
                               "and/or serialized_dashboard.",
                })

            result = w.lakeview.update(
                dashboard_id=dashboard_id,
                dashboard=Dashboard(**dashboard_kwargs),
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_trash_dashboard(dashboard_id: str) -> str:
        """Move a Lakeview dashboard to the trash.

        Soft-deletes the dashboard by moving it to the trash. Trashed
        dashboards can potentially be recovered. The published version
        (if any) remains accessible until explicitly unpublished.

        Args:
            dashboard_id: The UUID identifying the dashboard to trash.

        Returns:
            Confirmation that the dashboard has been moved to the trash.
        """
        try:
            w = get_workspace_client()
            w.lakeview.trash(dashboard_id)
            return to_json({
                "status": "trashed",
                "message": f"Dashboard '{dashboard_id}' has been moved to the trash.",
                "dashboard_id": dashboard_id,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_publish_dashboard(
        dashboard_id: str,
        warehouse_id: str = "",
        embed_credentials: bool = True,
    ) -> str:
        """Publish a Lakeview dashboard draft.

        Makes the current draft version of the dashboard publicly accessible
        (within the workspace). Published dashboards can be viewed by users
        who have access, and can use embedded credentials for query execution.

        Args:
            dashboard_id: The UUID identifying the dashboard to publish.
            warehouse_id: Optional warehouse ID to override the warehouse set
                          in the draft. If empty, uses the draft's warehouse.
            embed_credentials: If True (default), the publisher's credentials
                               are embedded so viewers can run queries without
                               their own warehouse access.

        Returns:
            JSON object with published dashboard details including the
            publish timestamp and embed_credentials status.
        """
        try:
            w = get_workspace_client()

            publish_kwargs: dict = {
                "dashboard_id": dashboard_id,
                "embed_credentials": embed_credentials,
            }
            if warehouse_id:
                publish_kwargs["warehouse_id"] = warehouse_id

            result = w.lakeview.publish(**publish_kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_unpublish_dashboard(dashboard_id: str) -> str:
        """Unpublish a Lakeview dashboard.

        Removes the published version of the dashboard, making it no longer
        accessible to viewers. The draft version is retained and can be
        re-published later.

        Args:
            dashboard_id: The UUID identifying the dashboard to unpublish.

        Returns:
            Confirmation that the dashboard has been unpublished.
        """
        try:
            w = get_workspace_client()
            w.lakeview.unpublish(dashboard_id)
            return to_json({
                "status": "unpublished",
                "message": f"Dashboard '{dashboard_id}' has been unpublished.",
                "dashboard_id": dashboard_id,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_migrate_dashboard(
        source_dashboard_id: str,
        display_name: str = "",
        parent_path: str = "",
    ) -> str:
        """Migrate a classic SQL dashboard to Lakeview format.

        Converts an existing classic (legacy) SQL dashboard into a new
        Lakeview dashboard. The original dashboard is not modified. The
        migration creates a new Lakeview dashboard with the converted
        content.

        Args:
            source_dashboard_id: The UUID of the classic SQL dashboard to
                                 migrate.
            display_name: Optional display name for the new Lakeview dashboard.
                          If empty, uses the original dashboard's name.
            parent_path: Optional workspace folder path for the new dashboard.

        Returns:
            JSON object with the newly created Lakeview dashboard's details,
            including its new dashboard_id.
        """
        try:
            w = get_workspace_client()

            migrate_kwargs: dict = {
                "source_dashboard_id": source_dashboard_id,
            }
            if display_name:
                migrate_kwargs["display_name"] = display_name
            if parent_path:
                migrate_kwargs["parent_path"] = parent_path

            result = w.lakeview.migrate(**migrate_kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_published_dashboard(dashboard_id: str) -> str:
        """Get the published version of a Lakeview dashboard.

        Retrieves the published (live) version of a dashboard, which may
        differ from the current draft. Returns the published dashboard's
        configuration, embed credentials setting, and warehouse binding.

        This method may not be available in all SDK versions; if unavailable,
        an informative error is returned.

        Args:
            dashboard_id: The UUID identifying the dashboard whose published
                          version to retrieve.

        Returns:
            JSON object with the published dashboard details including
            embed_credentials, warehouse_id, and publish timestamp.
        """
        try:
            w = get_workspace_client()
            if hasattr(w.lakeview, 'get_published'):
                result = w.lakeview.get_published(dashboard_id=dashboard_id)
                return to_json(result)
            else:
                return format_error(Exception("get_published not available in this SDK version"))
        except Exception as e:
            return format_error(e)
