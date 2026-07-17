"""Shared test fixtures for Databricks MCP server tests."""

from contextlib import ExitStack

import pytest
from unittest.mock import MagicMock, patch

from mcp.server.fastmcp import FastMCP

# Every module that does ``from databricks_mcp.config import get_workspace_client``
# captures a local reference. We must patch the name in each module so that calls
# inside registered tool functions resolve to our mock.
_MODULES_USING_GET_WORKSPACE_CLIENT = [
    "databricks_mcp.config",
    "databricks_mcp.tools.unity_catalog",
    "databricks_mcp.tools.sql",
    "databricks_mcp.tools.workspace",
    "databricks_mcp.tools.compute",
    "databricks_mcp.tools.jobs",
    "databricks_mcp.tools.pipelines",
    "databricks_mcp.tools.serving",
    "databricks_mcp.tools.vector_search",
    "databricks_mcp.tools.apps",
    "databricks_mcp.tools.database",
    "databricks_mcp.tools.dashboards",
    "databricks_mcp.tools.genie",
    "databricks_mcp.tools.secrets",
    "databricks_mcp.tools.iam",
    "databricks_mcp.tools.connections",
    "databricks_mcp.tools.experiments",
    "databricks_mcp.tools.sharing",
    "databricks_mcp.resources.workspace_info",
]


@pytest.fixture
def mcp():
    """Create a fresh FastMCP instance for testing."""
    return FastMCP("test-databricks")


@pytest.fixture
def mock_workspace_client():
    """Create a mock WorkspaceClient with all service attributes.

    Each attribute is a MagicMock that can be inspected for calls made by
    tool functions.  Services listed here cover every tool module in
    ``databricks_mcp/tools/``.
    """
    client = MagicMock()

    # Unity Catalog
    client.catalogs = MagicMock()
    client.schemas = MagicMock()
    client.tables = MagicMock()
    client.volumes = MagicMock()
    client.functions = MagicMock()
    client.registered_models = MagicMock()

    # SQL
    client.warehouses = MagicMock()
    client.statement_execution = MagicMock()
    client.queries = MagicMock()
    client.alerts = MagicMock()
    client.query_history = MagicMock()

    # Workspace
    client.workspace = MagicMock()
    client.repos = MagicMock()

    # Compute
    client.clusters = MagicMock()
    client.instance_pools = MagicMock()
    client.cluster_policies = MagicMock()

    # Jobs & Pipelines
    client.jobs = MagicMock()
    client.pipelines = MagicMock()

    # Serving & ML
    client.serving_endpoints = MagicMock()
    client.model_versions = MagicMock()
    client.vector_search_endpoints = MagicMock()
    client.vector_search_indexes = MagicMock()

    # Apps & Database (Lakebase)
    client.apps = MagicMock()
    client.database = MagicMock()

    # Dashboards
    client.lakeview = MagicMock()

    # Genie
    client.genie = MagicMock()

    # Secrets
    client.secrets = MagicMock()

    # IAM
    client.users = MagicMock()
    client.groups = MagicMock()
    client.service_principals = MagicMock()
    client.permissions = MagicMock()

    # Connections
    client.connections = MagicMock()

    # Experiments (MLflow)
    client.experiments = MagicMock()

    # Delta Sharing
    client.shares = MagicMock()
    client.recipients = MagicMock()
    client.providers = MagicMock()

    # Workspace info resource
    client.current_user = MagicMock()
    client.config = MagicMock()
    client.config.host = "https://test.databricks.com"
    client.config.auth_type = "pat"

    return client


@pytest.fixture
def patched_client(mock_workspace_client):
    """Patch ``get_workspace_client`` everywhere it is imported.

    Because each tool module does ``from databricks_mcp.config import
    get_workspace_client``, patching only the config module is insufficient --
    the local name in each tool module still points to the real function.
    This fixture patches the name in every module that imports it.
    """
    with ExitStack() as stack:
        for module_path in _MODULES_USING_GET_WORKSPACE_CLIENT:
            stack.enter_context(
                patch(
                    f"{module_path}.get_workspace_client",
                    return_value=mock_workspace_client,
                )
            )
        yield mock_workspace_client
