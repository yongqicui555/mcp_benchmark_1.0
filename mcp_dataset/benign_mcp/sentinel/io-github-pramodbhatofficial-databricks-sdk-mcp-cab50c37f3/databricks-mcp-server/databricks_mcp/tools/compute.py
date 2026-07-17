"""Compute cluster and instance pool tools for Databricks MCP.

Provides tools for managing all-purpose and job compute clusters,
instance pools, and cluster policies.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all compute tools with the MCP server."""

    # ── Clusters ────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_clusters() -> str:
        """List all compute clusters in the workspace.

        Returns both running and terminated clusters, including all-purpose
        and job clusters. Each entry includes the cluster's current state.

        Returns:
            JSON array of cluster objects with cluster_id, cluster_name,
            state, spark_version, node_type_id, and autoscale config.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.clusters.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_cluster(cluster_id: str) -> str:
        """Get detailed information about a specific compute cluster.

        Args:
            cluster_id: The unique identifier of the cluster.

        Returns:
            JSON object with full cluster details including cluster_name,
            state, state_message, spark_version, node_type_id, driver_node_type_id,
            num_workers, autoscale, spark_conf, and runtime information.
        """
        try:
            w = get_workspace_client()
            result = w.clusters.get(cluster_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_cluster(
        cluster_name: str,
        spark_version: str,
        node_type_id: str,
        num_workers: int = 0,
        autoscale_min: int = 0,
        autoscale_max: int = 0,
    ) -> str:
        """Create a new compute cluster.

        Creates an all-purpose cluster with either a fixed number of workers
        or autoscaling. If autoscale_min and autoscale_max are both greater
        than 0, autoscaling is enabled and num_workers is ignored. Otherwise,
        a fixed-size cluster is created with num_workers.

        Args:
            cluster_name: Display name for the cluster.
            spark_version: Spark runtime version string
                           (e.g. "14.3.x-scala2.12", "15.0.x-scala2.12").
                           Use the Spark version key from your workspace.
            node_type_id: Instance type for worker nodes
                          (e.g. "i3.xlarge", "Standard_DS3_v2").
            num_workers: Number of worker nodes for a fixed-size cluster.
                         Ignored if autoscaling is configured. Use 0 for
                         single-node clusters.
            autoscale_min: Minimum number of workers when autoscaling is enabled.
                           Set both autoscale_min and autoscale_max > 0 to enable.
            autoscale_max: Maximum number of workers when autoscaling is enabled.
                           Set both autoscale_min and autoscale_max > 0 to enable.

        Returns:
            JSON object with the created cluster details including cluster_id.
        """
        try:
            from databricks.sdk.service.compute import AutoScale

            w = get_workspace_client()
            kwargs = {
                "cluster_name": cluster_name,
                "spark_version": spark_version,
                "node_type_id": node_type_id,
            }

            # Use autoscaling if both min and max are specified and positive
            if autoscale_min > 0 and autoscale_max > 0:
                kwargs["autoscale"] = AutoScale(
                    min_workers=autoscale_min,
                    max_workers=autoscale_max,
                )
            else:
                kwargs["num_workers"] = num_workers

            result = w.clusters.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_start_cluster(cluster_id: str) -> str:
        """Start a terminated compute cluster.

        Initiates the start process for a previously terminated cluster.
        The cluster may take several minutes to become fully running.
        This call returns immediately without blocking.

        Args:
            cluster_id: The unique identifier of the cluster to start.

        Returns:
            Confirmation that the start was initiated.
        """
        try:
            w = get_workspace_client()
            w.clusters.start(cluster_id=cluster_id)
            return (
                f"Cluster '{cluster_id}' start initiated. "
                "It may take several minutes to become running."
            )
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_terminate_cluster(cluster_id: str) -> str:
        """Terminate a running compute cluster.

        Stops all Spark workloads and releases the cloud resources. The
        cluster configuration is preserved and it can be restarted later.
        This call returns immediately without blocking.

        Args:
            cluster_id: The unique identifier of the cluster to terminate.

        Returns:
            Confirmation that termination was initiated.
        """
        try:
            w = get_workspace_client()
            w.clusters.delete(cluster_id=cluster_id)
            return f"Cluster '{cluster_id}' termination initiated."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_restart_cluster(cluster_id: str) -> str:
        """Restart a running compute cluster.

        Restarts the Spark driver and all workers. Use this to clear
        cached state or apply configuration changes. This call returns
        immediately without blocking.

        Args:
            cluster_id: The unique identifier of the cluster to restart.

        Returns:
            Confirmation that the restart was initiated.
        """
        try:
            w = get_workspace_client()
            w.clusters.restart(cluster_id=cluster_id)
            return (
                f"Cluster '{cluster_id}' restart initiated. "
                "It may take a few minutes to become running again."
            )
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_resize_cluster(cluster_id: str, num_workers: int) -> str:
        """Resize a running cluster to a different number of workers.

        Changes the number of worker nodes in a running cluster. The
        resize happens gracefully — existing tasks are not interrupted.

        Args:
            cluster_id: The unique identifier of the cluster to resize.
            num_workers: The new number of worker nodes. Use 0 for a
                         single-node cluster (driver only).

        Returns:
            Confirmation that the resize was initiated.
        """
        try:
            w = get_workspace_client()
            w.clusters.resize(cluster_id=cluster_id, num_workers=num_workers)
            return f"Cluster '{cluster_id}' resize to {num_workers} workers initiated."
        except Exception as e:
            return format_error(e)

    # ── Instance Pools ──────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_instance_pools() -> str:
        """List all instance pools in the workspace.

        Instance pools reduce cluster start and auto-scaling times by
        maintaining a set of idle, ready-to-use cloud instances.

        Returns:
            JSON array of instance pool objects with instance_pool_id,
            instance_pool_name, node_type_id, min_idle_instances, and
            state. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.instance_pools.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_instance_pool(instance_pool_id: str) -> str:
        """Get detailed information about a specific instance pool.

        Args:
            instance_pool_id: The unique identifier of the instance pool.

        Returns:
            JSON object with pool details including instance_pool_name,
            node_type_id, min_idle_instances, max_capacity, idle_instance_autotermination_minutes,
            and stats about pending/used/idle instances.
        """
        try:
            w = get_workspace_client()
            result = w.instance_pools.get(instance_pool_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    # ── Cluster Policies ────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_cluster_policies() -> str:
        """List all cluster policies in the workspace.

        Cluster policies constrain the attributes available during cluster
        creation, enforcing organizational standards and cost controls.

        Returns:
            JSON array of policy objects with policy_id, name, description,
            definition, and creator information. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.cluster_policies.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_edit_cluster(
        cluster_id: str,
        cluster_name: str,
        spark_version: str,
        node_type_id: str,
        num_workers: int = 0,
    ) -> str:
        """Edit the configuration of an existing compute cluster.

        Updates the cluster definition. The cluster may be restarted to apply
        changes if it is currently running. This call returns immediately
        without blocking.

        Args:
            cluster_id: The unique identifier of the cluster to edit.
            cluster_name: New display name for the cluster.
            spark_version: Spark runtime version string
                           (e.g. "14.3.x-scala2.12", "15.0.x-scala2.12").
            node_type_id: Instance type for worker nodes
                          (e.g. "i3.xlarge", "Standard_DS3_v2").
            num_workers: Number of worker nodes. Use 0 for a single-node
                         cluster (driver only). Defaults to 0.

        Returns:
            Confirmation that the cluster edit was initiated.
        """
        try:
            w = get_workspace_client()
            w.clusters.edit(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                spark_version=spark_version,
                node_type_id=node_type_id,
                num_workers=num_workers,
            )
            return f"Cluster '{cluster_id}' edit initiated with name '{cluster_name}'."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_pin_cluster(cluster_id: str) -> str:
        """Pin a compute cluster to prevent it from being auto-deleted.

        Pinned clusters are retained even after being terminated for an
        extended period. This is useful for clusters that are used
        intermittently but should not be cleaned up.

        Args:
            cluster_id: The unique identifier of the cluster to pin.

        Returns:
            Confirmation that the cluster has been pinned.
        """
        try:
            w = get_workspace_client()
            w.clusters.pin(cluster_id=cluster_id)
            return f"Cluster '{cluster_id}' has been pinned."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_unpin_cluster(cluster_id: str) -> str:
        """Unpin a compute cluster, allowing it to be auto-deleted.

        Removes the pin from a cluster so that it follows the normal
        auto-deletion policy for terminated clusters.

        Args:
            cluster_id: The unique identifier of the cluster to unpin.

        Returns:
            Confirmation that the cluster has been unpinned.
        """
        try:
            w = get_workspace_client()
            w.clusters.unpin(cluster_id=cluster_id)
            return f"Cluster '{cluster_id}' has been unpinned."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_cluster_events(cluster_id: str, limit: int = 50) -> str:
        """List recent events for a compute cluster.

        Returns events such as creation, configuration changes, state
        transitions, and errors. Useful for auditing and troubleshooting
        cluster behavior.

        Args:
            cluster_id: The unique identifier of the cluster.
            limit: Maximum number of events to return. Defaults to 50.

        Returns:
            JSON object with an array of cluster event objects, each
            containing timestamp, type, and details.
        """
        try:
            w = get_workspace_client()
            events = paginate(w.clusters.events(cluster_id=cluster_id), max_items=limit)
            return to_json({"cluster_id": cluster_id, "events": events, "count": len(events)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_node_types() -> str:
        """List all available node types for compute clusters.

        Returns the available instance types that can be used as worker
        or driver nodes when creating or editing clusters. Each entry
        includes instance type ID, memory, CPU cores, and availability.

        Returns:
            JSON object with available node types and their specifications.
        """
        try:
            w = get_workspace_client()
            result = w.clusters.list_node_types()
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_spark_versions() -> str:
        """List all available Spark runtime versions.

        Returns the Spark versions available for creating or editing clusters.
        Each entry includes the version key (used in cluster configuration)
        and a human-readable name.

        Returns:
            JSON object with available Spark versions and their display names.
        """
        try:
            w = get_workspace_client()
            result = w.clusters.spark_versions()
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_instance_pool(
        instance_pool_name: str,
        node_type_id: str,
        min_idle_instances: int = 0,
        max_capacity: int = 0,
        idle_instance_autotermination_minutes: int = 60,
    ) -> str:
        """Create a new instance pool.

        Instance pools reduce cluster start and auto-scaling times by
        maintaining a set of idle, ready-to-use cloud instances. Clusters
        can be configured to use an instance pool for faster provisioning.

        Args:
            instance_pool_name: Display name for the instance pool.
            node_type_id: Instance type for pool instances
                          (e.g. "i3.xlarge", "Standard_DS3_v2").
            min_idle_instances: Minimum number of idle instances to maintain
                                in the pool. Defaults to 0.
            max_capacity: Maximum total instances the pool can hold (idle +
                          in-use). Set to 0 for no limit. Defaults to 0.
            idle_instance_autotermination_minutes: Minutes before idle instances
                                                   are terminated. Defaults to 60.

        Returns:
            JSON object with the created instance pool's details including
            instance_pool_id.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {
                "instance_pool_name": instance_pool_name,
                "node_type_id": node_type_id,
                "min_idle_instances": min_idle_instances,
                "idle_instance_autotermination_minutes": idle_instance_autotermination_minutes,
            }
            if max_capacity > 0:
                kwargs["max_capacity"] = max_capacity
            result = w.instance_pools.create(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_instance_pool(instance_pool_id: str) -> str:
        """Delete an instance pool.

        Permanently removes the instance pool and terminates all idle
        instances. Clusters currently using this pool are not affected
        but will not be able to scale using the pool after deletion.

        Args:
            instance_pool_id: The unique identifier of the instance pool
                              to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.instance_pools.delete(instance_pool_id=instance_pool_id)
            return f"Instance pool '{instance_pool_id}' deleted successfully."
        except Exception as e:
            return format_error(e)
