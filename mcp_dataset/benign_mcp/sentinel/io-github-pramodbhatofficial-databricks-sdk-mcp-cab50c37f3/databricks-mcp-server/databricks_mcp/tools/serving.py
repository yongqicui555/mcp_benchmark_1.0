"""Tools for managing Databricks Model Serving endpoints.

Covers endpoint CRUD, querying, build logs, and Unity Catalog model version listing.
Serving endpoints expose MLflow models (including LLMs, custom models, and external
models) as scalable REST API endpoints using serverless compute managed by Databricks.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all model serving endpoint tools with the MCP server."""

    @mcp.tool()
    def databricks_list_serving_endpoints() -> str:
        """List all model serving endpoints in the workspace.

        Returns summary information for every serving endpoint including name,
        state, creation time, and served entity configuration.
        """
        try:
            w = get_workspace_client()
            endpoints = paginate(w.serving_endpoints.list(), max_items=100)
            return to_json({"endpoints": endpoints, "count": len(endpoints)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_serving_endpoint(name: str) -> str:
        """Get detailed information about a specific serving endpoint.

        Returns the full endpoint configuration including served entities,
        traffic routing, state, pending config changes, and tags.

        Args:
            name: The name of the serving endpoint. Must be unique within the workspace.
        """
        try:
            w = get_workspace_client()
            endpoint = w.serving_endpoints.get(name)
            return to_json(endpoint)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_serving_endpoint(
        name: str,
        model_name: str,
        model_version: str,
        workload_size: str = "Small",
        scale_to_zero: bool = True,
    ) -> str:
        """Create a new model serving endpoint.

        Creates an endpoint that serves a Unity Catalog model or MLflow model.
        The endpoint starts provisioning immediately. This tool returns as soon
        as the creation request is accepted -- it does NOT wait for the endpoint
        to become ready (which can take several minutes).

        Args:
            name: Unique name for the endpoint. Alphanumeric characters, dashes, and
                  underscores only.
            model_name: Full name of the model to serve (e.g. "catalog.schema.model"
                        for Unity Catalog models, or "model_name" for MLflow models).
            model_version: Version of the model to serve (e.g. "1", "2").
            workload_size: Compute size per replica. One of "Small", "Medium", "Large".
                           Defaults to "Small".
            scale_to_zero: Whether the endpoint scales to zero replicas when idle.
                           Defaults to True, which reduces cost but adds cold-start latency.
        """
        try:
            from databricks.sdk.service.serving import (
                EndpointCoreConfigInput,
                ServedEntityInput,
            )

            w = get_workspace_client()
            w.serving_endpoints.create(
                name=name,
                config=EndpointCoreConfigInput(
                    served_entities=[
                        ServedEntityInput(
                            entity_name=model_name,
                            entity_version=model_version,
                            workload_size=workload_size,
                            scale_to_zero_enabled=scale_to_zero,
                        )
                    ]
                ),
            )
            # Return immediately without blocking on .result()
            return to_json({
                "status": "creating",
                "name": name,
                "model_name": model_name,
                "model_version": model_version,
                "message": (
                    f"Serving endpoint '{name}' creation initiated. "
                    "Use databricks_get_serving_endpoint to check readiness."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_serving_endpoint(
        name: str,
        model_name: str,
        model_version: str,
        workload_size: str = "Small",
        scale_to_zero: bool = True,
    ) -> str:
        """Update the configuration of an existing serving endpoint.

        Replaces the served entities with the specified model and version.
        An endpoint that already has an update in progress cannot be updated
        until the current update completes or fails. This tool returns immediately
        without waiting for the update to finish.

        Args:
            name: Name of the existing serving endpoint to update.
            model_name: Full name of the model to serve.
            model_version: Version of the model to serve.
            workload_size: Compute size per replica. One of "Small", "Medium", "Large".
            scale_to_zero: Whether the endpoint scales to zero when idle.
        """
        try:
            from databricks.sdk.service.serving import ServedEntityInput

            w = get_workspace_client()
            w.serving_endpoints.update_config(
                name=name,
                served_entities=[
                    ServedEntityInput(
                        entity_name=model_name,
                        entity_version=model_version,
                        workload_size=workload_size,
                        scale_to_zero_enabled=scale_to_zero,
                    )
                ],
            )
            # Return immediately without blocking on .result()
            return to_json({
                "status": "updating",
                "name": name,
                "model_name": model_name,
                "model_version": model_version,
                "message": (
                    f"Serving endpoint '{name}' update initiated. "
                    "Use databricks_get_serving_endpoint to check progress."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_serving_endpoint(name: str) -> str:
        """Delete a serving endpoint.

        Permanently removes the endpoint and releases all associated compute
        resources. This action cannot be undone.

        Args:
            name: Name of the serving endpoint to delete.
        """
        try:
            w = get_workspace_client()
            w.serving_endpoints.delete(name)
            return to_json({
                "status": "deleted",
                "name": name,
                "message": f"Serving endpoint '{name}' has been deleted.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_query_serving_endpoint(name: str, inputs: str) -> str:
        """Query a model serving endpoint for predictions.

        Sends input data to the serving endpoint and returns model predictions.
        Supports various input formats depending on the model type.

        Args:
            name: Name of the serving endpoint to query.
            inputs: JSON string containing the input data. The format depends on
                    the model type:
                    - For ML models: '[{"col1": val1, "col2": val2}, ...]'
                    - For LLM completions: '{"prompt": "text"}'
                    - For embeddings: '{"input": ["text1", "text2"]}'
                    The string is parsed as JSON and passed as the 'inputs' parameter.
        """
        try:
            w = get_workspace_client()
            parsed_inputs = json.loads(inputs)
            response = w.serving_endpoints.query(name=name, inputs=parsed_inputs)
            return to_json(response)
        except json.JSONDecodeError as e:
            return format_error(ValueError(f"Invalid JSON in 'inputs' parameter: {e}"))
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_serving_endpoint_logs(name: str, served_model_name: str) -> str:
        """Retrieve build logs for a served model within an endpoint.

        Returns the build logs generated during model container creation.
        Useful for debugging deployment failures or checking build progress.

        Args:
            name: Name of the serving endpoint.
            served_model_name: Name of the served model within the endpoint
                               whose build logs you want to retrieve.
        """
        try:
            w = get_workspace_client()
            response = w.serving_endpoints.build_logs(name=name, served_model_name=served_model_name)
            return to_json(response)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_serving_endpoint_permissions(name: str) -> str:
        """List permissions on a serving endpoint.

        Returns the access control list (ACL) for the specified endpoint,
        showing which users and groups have what level of access.

        Args:
            name: Name of the serving endpoint.
        """
        try:
            w = get_workspace_client()
            perms = w.serving_endpoints.get_permission_levels(serving_endpoint_id=name)
            return to_json(perms)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_model_versions(full_model_name: str) -> str:
        """List all versions of a Unity Catalog registered model.

        Returns version numbers, creation timestamps, current stage, and
        source run information for each version of the specified model.
        Useful for finding available versions before creating a serving endpoint.

        Args:
            full_model_name: Full three-level name of the Unity Catalog model
                             in "catalog.schema.model" format.
        """
        try:
            w = get_workspace_client()
            versions = paginate(w.model_versions.list(full_name=full_model_name), max_items=100)
            return to_json({"model": full_model_name, "versions": versions, "count": len(versions)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_serving_endpoint_openapi(name: str) -> str:
        """Get the OpenAPI specification for a serving endpoint.

        Retrieves the auto-generated OpenAPI spec that describes the REST
        API for querying the endpoint. Useful for understanding the expected
        input/output schema of the served model.

        This method may not be available in all SDK versions; if unavailable,
        an informative error is returned.

        Args:
            name: Name of the serving endpoint.
        """
        try:
            w = get_workspace_client()
            if hasattr(w.serving_endpoints, 'get_open_api'):
                result = w.serving_endpoints.get_open_api(name=name)
                return to_json(result)
            else:
                return format_error(Exception("get_open_api not available in this SDK version"))
        except Exception as e:
            return format_error(e)
