"""Global init script management tools for Databricks MCP.

Provides tools for managing workspace-level global init scripts that run on
every cluster at startup. Scripts are stored as base64-encoded content and
can be enabled/disabled and ordered by position.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all global init script tools with the MCP server."""

    # ── Global Init Scripts ──────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_global_init_scripts() -> str:
        """List all global init scripts in the workspace.

        Global init scripts run on every cluster in the workspace at startup,
        in the order specified by their position. Each entry includes the
        script's name, enabled status, and position.

        Returns:
            JSON array of global init script objects with script_id, name,
            enabled, position, created_at, and updated_at.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.global_init_scripts.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_global_init_script(script_id: str) -> str:
        """Get detailed information about a specific global init script.

        Returns the full script metadata including its base64-encoded content.

        Args:
            script_id: The unique identifier of the global init script.

        Returns:
            JSON object with script details including script_id, name,
            enabled, position, script (base64-encoded content), created_at,
            created_by, updated_at, and updated_by.
        """
        try:
            w = get_workspace_client()
            result = w.global_init_scripts.get(script_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_global_init_script(
        name: str,
        script: str,
        enabled: bool = False,
        position: int = 0,
    ) -> str:
        """Create a new global init script.

        Global init scripts run on every cluster in the workspace at startup.
        The script content must be base64-encoded. Scripts are disabled by
        default and can be positioned to control execution order.

        Args:
            name: Display name for the init script. Must be unique within
                  the workspace.
            script: The script content, base64-encoded. For example, a bash
                    script that installs a library.
            enabled: Whether the script should be active. Defaults to False
                     so you can review before enabling.
            position: Execution order position (0-based). Lower positions run
                      first. Defaults to 0.

        Returns:
            JSON object with the created script's details including script_id.
        """
        try:
            w = get_workspace_client()
            result = w.global_init_scripts.create(
                name=name,
                script=script,
                enabled=enabled,
                position=position,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_global_init_script(
        script_id: str,
        name: str,
        script: str,
        enabled: bool = False,
        position: int = 0,
    ) -> str:
        """Update an existing global init script.

        Replaces the script's name, content, enabled status, and position.
        All fields are required -- any omitted optional fields will be reset
        to their defaults.

        Args:
            script_id: The unique identifier of the script to update.
            name: New display name for the script.
            script: New script content, base64-encoded.
            enabled: Whether the script should be active after the update.
            position: New execution order position (0-based).

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.global_init_scripts.update(
                script_id=script_id,
                name=name,
                script=script,
                enabled=enabled,
                position=position,
            )
            return f"Global init script '{script_id}' updated successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_global_init_script(script_id: str) -> str:
        """Delete a global init script from the workspace.

        The script will no longer run on new cluster starts. Clusters that
        are already running are not affected until they are restarted.

        Args:
            script_id: The unique identifier of the script to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.global_init_scripts.delete(script_id)
            return f"Global init script '{script_id}' deleted successfully."
        except Exception as e:
            return format_error(e)
