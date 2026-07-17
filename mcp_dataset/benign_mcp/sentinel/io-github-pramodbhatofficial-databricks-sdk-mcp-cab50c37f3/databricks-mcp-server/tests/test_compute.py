"""Tests for databricks_mcp.tools.compute — cluster, instance pool, and policy tools.

Tests cover cluster CRUD, lifecycle operations (start/stop/restart/resize),
instance pool listing, and cluster policy listing.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp.server.fastmcp import FastMCP

from databricks_mcp.tools.compute import register_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tool_fn(mcp: FastMCP, name: str):
    """Retrieve a registered tool's underlying function by name."""
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"Tool '{name}' not found in registered tools"
    return tool.fn


def _tool_names(mcp: FastMCP) -> set[str]:
    """Return the set of all registered tool names."""
    return {t.name for t in mcp._tool_manager.list_tools()}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    """Verify register_tools() adds all expected compute tools."""

    def test_all_tools_registered(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        names = _tool_names(mcp)

        expected = {
            # Clusters
            "databricks_list_clusters",
            "databricks_get_cluster",
            "databricks_create_cluster",
            "databricks_start_cluster",
            "databricks_terminate_cluster",
            "databricks_restart_cluster",
            "databricks_resize_cluster",
            # Instance pools
            "databricks_list_instance_pools",
            "databricks_get_instance_pool",
            # Cluster policies
            "databricks_list_cluster_policies",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"


# ---------------------------------------------------------------------------
# Cluster CRUD tools
# ---------------------------------------------------------------------------

class TestClusterCrudTools:
    """Test cluster list, get, and create operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_clusters(self) -> None:
        self.client.clusters.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_clusters")
        result = fn()
        self.client.clusters.list.assert_called_once()
        parsed = json.loads(result)
        assert parsed == []

    def test_get_cluster(self) -> None:
        mock_cluster = SimpleNamespace(
            cluster_id="c-1", cluster_name="dev", state="RUNNING"
        )
        self.client.clusters.get.return_value = mock_cluster
        fn = _get_tool_fn(self.mcp, "databricks_get_cluster")
        result = fn(cluster_id="c-1")
        self.client.clusters.get.assert_called_once_with("c-1")

    def test_create_cluster_fixed_size(self) -> None:
        """Create a fixed-size cluster (no autoscaling)."""
        mock_result = SimpleNamespace(cluster_id="new-c")
        self.client.clusters.create.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_create_cluster")
        with patch("databricks.sdk.service.compute.AutoScale") as MockAutoScale:
            result = fn(
                cluster_name="test-cluster",
                spark_version="14.3.x-scala2.12",
                node_type_id="i3.xlarge",
                num_workers=4,
            )
            # AutoScale should NOT have been used
            MockAutoScale.assert_not_called()

        self.client.clusters.create.assert_called_once_with(
            cluster_name="test-cluster",
            spark_version="14.3.x-scala2.12",
            node_type_id="i3.xlarge",
            num_workers=4,
        )

    def test_create_cluster_with_autoscale(self) -> None:
        """Create a cluster with autoscaling enabled."""
        mock_result = SimpleNamespace(cluster_id="new-c")
        self.client.clusters.create.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_create_cluster")
        with patch("databricks.sdk.service.compute.AutoScale") as MockAutoScale:
            MockAutoScale.return_value = "autoscale_obj"
            result = fn(
                cluster_name="auto-cluster",
                spark_version="15.0.x-scala2.12",
                node_type_id="i3.xlarge",
                autoscale_min=2,
                autoscale_max=10,
            )
            MockAutoScale.assert_called_once_with(min_workers=2, max_workers=10)

        self.client.clusters.create.assert_called_once_with(
            cluster_name="auto-cluster",
            spark_version="15.0.x-scala2.12",
            node_type_id="i3.xlarge",
            autoscale="autoscale_obj",
        )

    def test_create_cluster_defaults(self) -> None:
        """Default num_workers=0 creates a single-node cluster."""
        mock_result = SimpleNamespace(cluster_id="single")
        self.client.clusters.create.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_create_cluster")
        with patch("databricks.sdk.service.compute.AutoScale"):
            result = fn(
                cluster_name="single-node",
                spark_version="14.3.x-scala2.12",
                node_type_id="i3.xlarge",
            )

        call_kwargs = self.client.clusters.create.call_args[1]
        assert call_kwargs["num_workers"] == 0

    def test_create_cluster_autoscale_only_min(self) -> None:
        """If only autoscale_min > 0 but autoscale_max is 0, falls back to fixed size."""
        mock_result = SimpleNamespace(cluster_id="c")
        self.client.clusters.create.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_create_cluster")
        with patch("databricks.sdk.service.compute.AutoScale") as MockAutoScale:
            result = fn(
                cluster_name="c",
                spark_version="14.3.x-scala2.12",
                node_type_id="i3.xlarge",
                autoscale_min=2,
                autoscale_max=0,
            )
            # AutoScale should NOT be used since max is 0
            MockAutoScale.assert_not_called()

        call_kwargs = self.client.clusters.create.call_args[1]
        assert "num_workers" in call_kwargs
        assert "autoscale" not in call_kwargs

    def test_list_clusters_error(self) -> None:
        self.client.clusters.list.side_effect = RuntimeError("permission denied")
        fn = _get_tool_fn(self.mcp, "databricks_list_clusters")
        result = fn()
        assert "RuntimeError" in result
        assert "permission denied" in result


# ---------------------------------------------------------------------------
# Cluster Lifecycle tools
# ---------------------------------------------------------------------------

class TestClusterLifecycleTools:
    """Test start, terminate, restart, and resize operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_start_cluster(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_start_cluster")
        result = fn(cluster_id="c-1")
        self.client.clusters.start.assert_called_once_with(cluster_id="c-1")
        assert "start initiated" in result

    def test_terminate_cluster(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_terminate_cluster")
        result = fn(cluster_id="c-1")
        # The source code calls clusters.delete() for termination
        self.client.clusters.delete.assert_called_once_with(cluster_id="c-1")
        assert "termination initiated" in result

    def test_restart_cluster(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_restart_cluster")
        result = fn(cluster_id="c-1")
        self.client.clusters.restart.assert_called_once_with(cluster_id="c-1")
        assert "restart initiated" in result

    def test_resize_cluster(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_resize_cluster")
        result = fn(cluster_id="c-1", num_workers=8)
        self.client.clusters.resize.assert_called_once_with(cluster_id="c-1", num_workers=8)
        assert "resize to 8 workers" in result

    def test_resize_cluster_to_zero(self) -> None:
        """Resize to 0 workers creates a single-node cluster."""
        fn = _get_tool_fn(self.mcp, "databricks_resize_cluster")
        result = fn(cluster_id="c-1", num_workers=0)
        self.client.clusters.resize.assert_called_once_with(cluster_id="c-1", num_workers=0)
        assert "resize to 0 workers" in result

    def test_start_cluster_error(self) -> None:
        self.client.clusters.start.side_effect = RuntimeError("cluster not found")
        fn = _get_tool_fn(self.mcp, "databricks_start_cluster")
        result = fn(cluster_id="bad")
        assert "RuntimeError" in result
        assert "cluster not found" in result

    def test_terminate_cluster_error(self) -> None:
        self.client.clusters.delete.side_effect = RuntimeError("already terminated")
        fn = _get_tool_fn(self.mcp, "databricks_terminate_cluster")
        result = fn(cluster_id="c-2")
        assert "RuntimeError" in result


# ---------------------------------------------------------------------------
# Instance Pool tools
# ---------------------------------------------------------------------------

class TestInstancePoolTools:
    """Test instance pool list and get operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_instance_pools(self) -> None:
        self.client.instance_pools.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_instance_pools")
        result = fn()
        self.client.instance_pools.list.assert_called_once()
        parsed = json.loads(result)
        assert parsed == []

    def test_get_instance_pool(self) -> None:
        mock_pool = SimpleNamespace(
            instance_pool_id="pool-1", instance_pool_name="dev-pool"
        )
        self.client.instance_pools.get.return_value = mock_pool
        fn = _get_tool_fn(self.mcp, "databricks_get_instance_pool")
        result = fn(instance_pool_id="pool-1")
        self.client.instance_pools.get.assert_called_once_with("pool-1")

    def test_list_instance_pools_error(self) -> None:
        self.client.instance_pools.list.side_effect = ConnectionError("timeout")
        fn = _get_tool_fn(self.mcp, "databricks_list_instance_pools")
        result = fn()
        assert "ConnectionError" in result
        assert "timeout" in result


# ---------------------------------------------------------------------------
# Cluster Policy tools
# ---------------------------------------------------------------------------

class TestClusterPolicyTools:
    """Test cluster policy list operation."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_cluster_policies(self) -> None:
        self.client.cluster_policies.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_cluster_policies")
        result = fn()
        self.client.cluster_policies.list.assert_called_once()
        parsed = json.loads(result)
        assert parsed == []

    def test_list_cluster_policies_error(self) -> None:
        self.client.cluster_policies.list.side_effect = RuntimeError("unauthorized")
        fn = _get_tool_fn(self.mcp, "databricks_list_cluster_policies")
        result = fn()
        assert "RuntimeError" in result
        assert "unauthorized" in result
