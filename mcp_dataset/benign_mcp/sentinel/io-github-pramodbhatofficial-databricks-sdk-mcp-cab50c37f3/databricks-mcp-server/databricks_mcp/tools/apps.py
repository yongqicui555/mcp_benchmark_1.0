"""Databricks Apps lifecycle management tools.

Provides MCP tools for creating, deploying, starting, stopping, and managing
Databricks Apps. Apps run directly on a customer's Databricks instance,
integrate with their data, and enable single sign-on access.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Databricks Apps tools with the MCP server."""

    @mcp.tool()
    def databricks_list_apps() -> str:
        """List all Databricks Apps in the workspace.

        Returns a paginated list of apps with their names, descriptions,
        status, and URLs. Use this to discover what apps exist in the
        workspace before performing operations on them.

        Returns:
            JSON array of app objects, each containing name, description,
            active deployment info, and compute status. Limited to 100 results.
        """
        try:
            w = get_workspace_client()
            apps = paginate(w.apps.list())
            return to_json({"apps": apps, "count": len(apps)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_app(name: str) -> str:
        """Get detailed information about a specific Databricks App.

        Retrieves the full configuration and status of an app including its
        active deployment, compute status, URL, creator, and resources.

        Args:
            name: The name of the app. Must be a lowercase alphanumeric string
                  with hyphens (e.g., "my-dashboard-app").

        Returns:
            JSON object with complete app details including name, description,
            url, compute_status, active_deployment, and pending_deployment.
        """
        try:
            w = get_workspace_client()
            result = w.apps.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_app(name: str, description: str = "") -> str:
        """Create a new Databricks App.

        Creates a new app in the workspace. The app name must be unique,
        contain only lowercase alphanumeric characters and hyphens, and
        will become part of the app's URL.

        This is an asynchronous operation. The app will be provisioned in
        the background. Use databricks_get_app to check its status.

        Args:
            name: The name of the app. Must contain only lowercase alphanumeric
                  characters and hyphens (e.g., "my-new-app").
            description: Optional human-readable description of the app's purpose.

        Returns:
            Confirmation message that the app creation has been initiated,
            along with the app name for status checking.
        """
        try:
            from databricks.sdk.service.apps import App

            w = get_workspace_client()
            # Initiate creation without waiting for completion
            w.apps.create(app=App(name=name, description=description or None))
            return to_json({
                "status": "creating",
                "message": f"App '{name}' creation initiated. Use databricks_get_app to check status.",
                "name": name,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_deploy_app(
        name: str,
        source_code_path: str,
        mode: str = "SNAPSHOT",
    ) -> str:
        """Deploy source code to a Databricks App.

        Creates a new deployment for the specified app. The source code at the
        given workspace path will be packaged and deployed.

        This is an asynchronous operation. The deployment will proceed in the
        background. Use databricks_get_app or databricks_list_app_deployments
        to monitor progress.

        Args:
            name: The name of the app to deploy to.
            source_code_path: The workspace filesystem path of the source code
                              (e.g., "/Workspace/Users/me@company.com/my-app").
            mode: Deployment mode. "SNAPSHOT" (default) creates an immutable copy
                  of the source. "AUTO_SYNC" keeps the deployment in sync with
                  source changes.

        Returns:
            Confirmation message that the deployment has been initiated.
        """
        try:
            from databricks.sdk.service.apps import AppDeployment, AppDeploymentMode

            w = get_workspace_client()
            deployment_mode = AppDeploymentMode[mode]
            app_deployment = AppDeployment(
                source_code_path=source_code_path,
                mode=deployment_mode,
            )
            # Initiate deployment without waiting for completion
            w.apps.deploy(app_name=name, app_deployment=app_deployment)
            return to_json({
                "status": "deploying",
                "message": f"Deployment to app '{name}' initiated from '{source_code_path}' in {mode} mode.",
                "app_name": name,
                "source_code_path": source_code_path,
                "mode": mode,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_app(name: str) -> str:
        """Delete a Databricks App.

        Permanently deletes the app and all its deployments. This action
        cannot be undone. The app's URL will become unavailable immediately.

        Args:
            name: The name of the app to delete.

        Returns:
            Confirmation that the app has been deleted, or an error if
            the app was not found.
        """
        try:
            w = get_workspace_client()
            result = w.apps.delete(name)
            return to_json({
                "status": "deleted",
                "message": f"App '{name}' has been deleted.",
                "result": result,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_start_app(name: str) -> str:
        """Start a Databricks App.

        Starts the last active deployment of the app. If the app is already
        running, this has no effect.

        This is an asynchronous operation. Use databricks_get_app to check
        when the app becomes active.

        Args:
            name: The name of the app to start.

        Returns:
            Confirmation that the app start has been initiated.
        """
        try:
            w = get_workspace_client()
            # Initiate start without waiting for completion
            w.apps.start(name)
            return to_json({
                "status": "starting",
                "message": f"App '{name}' start initiated. Use databricks_get_app to check status.",
                "name": name,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_stop_app(name: str) -> str:
        """Stop a running Databricks App.

        Stops the active deployment of the app. The app's URL will become
        unavailable. Use databricks_start_app to restart it later.

        This is an asynchronous operation. Use databricks_get_app to confirm
        the app has stopped.

        Args:
            name: The name of the app to stop.

        Returns:
            Confirmation that the app stop has been initiated.
        """
        try:
            w = get_workspace_client()
            # Initiate stop without waiting for completion
            w.apps.stop(name)
            return to_json({
                "status": "stopping",
                "message": f"App '{name}' stop initiated. Use databricks_get_app to check status.",
                "name": name,
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_app_deployments(name: str) -> str:
        """List all deployments for a Databricks App.

        Returns the deployment history for the specified app, including
        both active and past deployments with their status, timestamps,
        and source code paths.

        Args:
            name: The name of the app whose deployments to list.

        Returns:
            JSON array of deployment objects with deployment_id, status,
            source_code_path, mode, and creation timestamps.
        """
        try:
            w = get_workspace_client()
            deployments = paginate(w.apps.list_deployments(app_name=name))
            return to_json({
                "app_name": name,
                "deployments": deployments,
                "count": len(deployments),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_app_deployment(app_name: str, deployment_id: str) -> str:
        """Get details of a specific app deployment.

        Retrieves complete information about a single deployment including
        its status, source code path, deployment mode, and any error messages.

        Args:
            app_name: The name of the app.
            deployment_id: The unique identifier of the deployment to retrieve.

        Returns:
            JSON object with full deployment details including status,
            source_code_path, mode, create_time, and update_time.
        """
        try:
            w = get_workspace_client()
            result = w.apps.get_deployment(
                app_name=app_name,
                deployment_id=deployment_id,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_app_environment(name: str) -> str:
        """Get the environment configuration for a Databricks App.

        Retrieves the app's environment variables, secrets, and resource
        bindings. Useful for understanding what configuration an app has
        access to at runtime.

        Args:
            name: The name of the app whose environment to retrieve.

        Returns:
            JSON object with environment variables, secret references,
            and resource bindings configured for the app.
        """
        try:
            w = get_workspace_client()
            if hasattr(w.apps, 'get_environment'):
                result = w.apps.get_environment(name=name)
                return to_json(result)
            else:
                return format_error(Exception("get_environment not available in this SDK version"))
        except Exception as e:
            return format_error(e)
