"""Tests for system health tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest
from fastmcp.exceptions import ToolError

from pcp_mcp.models import DiagnosisResult
from pcp_mcp.tools.system import (
    _assess_filesystems,
    _build_fallback_diagnosis,
    _build_filesystem_list,
    _format_snapshot_for_llm,
    get_filesystem_usage,
    get_process_top,
    get_system_snapshot,
    quick_health,
    smart_diagnose,
)


@pytest.fixture
def system_tools() -> dict:
    """Fixture providing all system tools as a dictionary."""
    return {
        "get_system_snapshot": get_system_snapshot,
        "quick_health": quick_health,
        "get_process_top": get_process_top,
        "smart_diagnose": smart_diagnose,
        "get_filesystem_usage": get_filesystem_usage,
    }


class TestToolErrorHandling:
    @pytest.mark.parametrize(
        ("tool_name", "client_method", "tool_kwargs"),
        [
            ("get_system_snapshot", "fetch_with_rates", {}),
            ("get_process_top", "fetch_with_rates", {}),
            ("smart_diagnose", "fetch_with_rates", {}),
            ("get_filesystem_usage", "fetch", {}),
        ],
    )
    async def test_handles_connection_error(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        tool_name: str,
        client_method: str,
        tool_kwargs: dict,
    ) -> None:
        getattr(
            mock_context.request_context.lifespan_context["client"], client_method
        ).side_effect = httpx.ConnectError("Connection refused")

        tools = system_tools

        with pytest.raises(ToolError, match="Cannot connect to pmproxy"):
            await tools[tool_name](mock_context, **tool_kwargs)


class TestGetSystemSnapshot:
    async def test_returns_all_categories(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        full_system_snapshot_data,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_system_snapshot_data()

        tools = system_tools
        result = await tools["get_system_snapshot"](mock_context)

        assert result.structured_content["cpu"] is not None
        assert result.structured_content["memory"] is not None
        assert result.structured_content["load"] is not None
        assert result.structured_content["disk"] is not None
        assert result.structured_content["network"] is not None
        assert result.structured_content["hostname"] == "localhost"

    async def test_returns_subset_categories(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        cpu_metrics_data,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = cpu_metrics_data()

        tools = system_tools
        result = await tools["get_system_snapshot"](mock_context, categories=["cpu"])

        assert result.structured_content["cpu"] is not None
        assert result.structured_content["memory"] is None
        assert result.structured_content["load"] is None
        assert result.structured_content["disk"] is None
        assert result.structured_content["network"] is None

    async def test_ignores_unknown_categories(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        cpu_metrics_data,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = cpu_metrics_data()

        tools = system_tools
        result = await tools["get_system_snapshot"](
            mock_context, categories=["cpu", "invalid_category", "also_invalid"]
        )

        assert result.structured_content["cpu"] is not None
        assert result.structured_content["memory"] is None

    async def test_reports_progress(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        full_system_snapshot_data,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_system_snapshot_data()
        mock_context.report_progress = AsyncMock()

        tools = system_tools
        await tools["get_system_snapshot"](mock_context)

        assert mock_context.report_progress.call_count >= 2
        calls = mock_context.report_progress.call_args_list
        assert calls[-1] == call(100, 100, "Complete")


class TestQuickHealth:
    async def test_returns_only_cpu_and_memory(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        cpu_metrics_data,
        memory_metrics_data,
    ) -> None:
        combined_data = {**cpu_metrics_data(), **memory_metrics_data()}
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = combined_data

        tools = system_tools
        result = await tools["quick_health"](mock_context)

        assert result.structured_content["cpu"] is not None
        assert result.structured_content["memory"] is not None
        assert result.structured_content["load"] is None
        assert result.structured_content["disk"] is None
        assert result.structured_content["network"] is None

    async def test_uses_shorter_sample_interval(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        cpu_metrics_data,
        memory_metrics_data,
    ) -> None:
        combined_data = {**cpu_metrics_data(), **memory_metrics_data()}
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = combined_data

        tools = system_tools
        await tools["quick_health"](mock_context)

        call_args = mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.call_args
        sample_interval_arg = call_args[0][2]
        assert sample_interval_arg == 0.5


class TestGetProcessTop:
    @pytest.fixture
    def system_info_response(self) -> dict:
        return {
            "values": [
                {"name": "hinv.ncpu", "instances": [{"value": 4}]},
                {"name": "mem.physmem", "instances": [{"value": 16000000}]},
            ]
        }

    @pytest.mark.parametrize(
        ("sort_by", "expected_field"),
        [
            ("cpu", "cpu_percent"),
            ("memory", "rss_bytes"),
            ("io", "io_read_bytes_per_sec"),
        ],
    )
    async def test_returns_top_processes_sorted(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        process_metrics_data,
        system_info_response: dict,
        sort_by: str,
        expected_field: str,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = process_metrics_data()
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch.return_value = system_info_response

        tools = system_tools
        result = await tools["get_process_top"](mock_context, sort_by=sort_by, limit=2)

        assert len(result.structured_content["processes"]) == 2
        assert result.structured_content["sort_by"] == sort_by
        assert result.structured_content["ncpu"] == 4
        assert result.structured_content["processes"][0][expected_field] is not None

    async def test_reports_progress(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        process_metrics_data,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = process_metrics_data()
        mock_context.request_context.lifespan_context["client"].fetch.return_value = {
            "values": [
                {"name": "hinv.ncpu", "instances": [{"value": 4}]},
                {"name": "mem.physmem", "instances": [{"value": 16000000}]},
            ]
        }
        mock_context.report_progress = AsyncMock()

        tools = system_tools
        await tools["get_process_top"](mock_context)

        assert mock_context.report_progress.call_count >= 2
        calls = mock_context.report_progress.call_args_list
        assert calls[-1] == call(100, 100, "Complete")


class TestSmartDiagnose:
    async def test_returns_llm_diagnosis(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        cpu_metrics_data,
        memory_metrics_data,
        load_metrics_data,
    ) -> None:
        combined_data = {
            **cpu_metrics_data(),
            **memory_metrics_data(),
            **load_metrics_data(),
        }
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = combined_data

        llm_result = DiagnosisResult(
            timestamp="ignored",
            hostname="ignored",
            diagnosis="System is healthy with normal resource usage.",
            severity="healthy",
            recommendations=["Continue monitoring"],
        )
        mock_sampling_result = MagicMock()
        mock_sampling_result.result = llm_result
        mock_context.sample = AsyncMock(return_value=mock_sampling_result)

        tools = system_tools
        result = await tools["smart_diagnose"](mock_context)

        assert result.structured_content["severity"] == "healthy"
        assert "healthy" in result.structured_content["diagnosis"].lower()
        assert result.structured_content["hostname"] == "localhost"
        mock_context.sample.assert_called_once()

    async def test_uses_fallback_when_llm_fails(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        cpu_metrics_data,
        memory_metrics_data,
        load_metrics_data,
    ) -> None:
        combined_data = {
            **cpu_metrics_data(idle=5.0),
            **memory_metrics_data(physmem=16_000_000, available=800_000, free=500_000),
            **load_metrics_data(load_1m=16.0),
        }
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = combined_data
        mock_context.sample = AsyncMock(side_effect=RuntimeError("LLM not available"))

        tools = system_tools
        result = await tools["smart_diagnose"](mock_context)

        assert result.structured_content["severity"] == "critical"
        assert result.structured_content["hostname"] == "localhost"
        assert len(result.structured_content["recommendations"]) > 0


class TestFormatSnapshotForLlm:
    def test_formats_all_sections(self, full_system_snapshot_data) -> None:
        from pcp_mcp.models import SystemSnapshot
        from pcp_mcp.utils.builders import (
            build_cpu_metrics,
            build_load_metrics,
            build_memory_metrics,
        )

        data = full_system_snapshot_data()
        snapshot = SystemSnapshot(
            timestamp="2025-01-18T12:00:00Z",
            hostname="testhost",
            cpu=build_cpu_metrics(data),
            memory=build_memory_metrics(data),
            load=build_load_metrics(data),
        )

        result = _format_snapshot_for_llm(snapshot)

        assert "testhost" in result
        assert "CPU:" in result
        assert "Memory:" in result
        assert "Load:" in result

    def test_handles_partial_snapshot(self) -> None:
        from pcp_mcp.models import SystemSnapshot

        snapshot = SystemSnapshot(
            timestamp="2025-01-18T12:00:00Z",
            hostname="testhost",
        )

        result = _format_snapshot_for_llm(snapshot)

        assert "testhost" in result
        assert "CPU:" not in result


class TestGetFilesystemUsage:
    async def test_returns_filesystem_info(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        filesystem_metrics_response,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch.return_value = filesystem_metrics_response()

        tools = system_tools
        result = await tools["get_filesystem_usage"](mock_context)

        assert len(result.structured_content["filesystems"]) == 2
        assert result.structured_content["hostname"] == "localhost"
        assert result.structured_content["filesystems"][0]["mount_point"] == "/"
        assert result.structured_content["filesystems"][0]["fs_type"] == "ext4"
        assert result.structured_content["filesystems"][0]["capacity_bytes"] == 100_000_000 * 1024
        assert result.structured_content["filesystems"][0]["percent_full"] == 20.0

    async def test_handles_empty_filesystems(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        filesystem_metrics_response,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch.return_value = filesystem_metrics_response(filesystems=[])

        tools = system_tools
        result = await tools["get_filesystem_usage"](mock_context)

        assert len(result.structured_content["filesystems"]) == 0
        assert "No filesystems found" in result.structured_content["assessment"]

    async def test_sorts_by_mount_point(
        self,
        mock_context: MagicMock,
        system_tools: dict,
        filesystem_metrics_response,
    ) -> None:
        filesystems = [
            {
                "instance": 0,
                "mountdir": "/var",
                "type": "ext4",
                "capacity": 100,
                "used": 50,
                "avail": 50,
                "full": 50.0,
            },
            {
                "instance": 1,
                "mountdir": "/",
                "type": "ext4",
                "capacity": 100,
                "used": 20,
                "avail": 80,
                "full": 20.0,
            },
            {
                "instance": 2,
                "mountdir": "/home",
                "type": "ext4",
                "capacity": 100,
                "used": 30,
                "avail": 70,
                "full": 30.0,
            },
        ]
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch.return_value = filesystem_metrics_response(filesystems=filesystems)

        tools = system_tools
        result = await tools["get_filesystem_usage"](mock_context)

        mount_points = [fs["mount_point"] for fs in result.structured_content["filesystems"]]
        assert mount_points == ["/", "/home", "/var"]


class TestBuildFilesystemList:
    def test_builds_from_pmproxy_response(self, filesystem_metrics_response) -> None:
        response = filesystem_metrics_response()
        result = _build_filesystem_list(response)

        assert len(result) == 2
        assert result[0].mount_point == "/"
        assert result[0].capacity_bytes == 100_000_000 * 1024
        assert result[0].used_bytes == 20_000_000 * 1024
        assert result[0].available_bytes == 75_000_000 * 1024
        assert result[0].percent_full == 20.0
        assert result[0].fs_type == "ext4"

    def test_handles_empty_response(self) -> None:
        result = _build_filesystem_list({"values": []})
        assert result == []

    def test_handles_missing_metrics(self) -> None:
        response = {
            "values": [
                {
                    "name": "filesys.mountdir",
                    "instances": [{"instance": 0, "value": "/"}],
                },
            ]
        }
        result = _build_filesystem_list(response)

        assert len(result) == 1
        assert result[0].mount_point == "/"
        assert result[0].capacity_bytes == 0
        assert result[0].fs_type == "unknown"


class TestAssessFilesystems:
    @pytest.mark.parametrize(
        ("percent_full", "mount_point", "expected_indicator", "expected_mount"),
        [
            (20.0, "/", "🟢", None),
            (85.0, "/boot", "🟡", "/boot"),
            (95.0, "/var", "🔴", "/var"),
        ],
    )
    def test_filesystem_assessment_levels(
        self,
        filesystem_info_factory,
        percent_full: float,
        mount_point: str,
        expected_indicator: str,
        expected_mount: str | None,
    ) -> None:
        used = int(100_000 * percent_full / 100)
        fs = filesystem_info_factory(
            mount_point=mount_point,
            percent_full=percent_full,
            used_bytes=used,
            available_bytes=100_000 - used,
        )
        result = _assess_filesystems([fs])

        assert expected_indicator in result
        if expected_mount:
            assert expected_mount in result

    def test_empty_filesystems(self) -> None:
        result = _assess_filesystems([])
        assert "No filesystems found" in result


class TestBuildFallbackDiagnosis:
    @pytest.mark.parametrize(
        ("cpu_idle", "mem_used", "load_1m", "ncpu", "expected_severity"),
        [
            (80.0, 50.0, 1.0, 4, "healthy"),
            (25.0, 50.0, 1.0, 4, "warning"),
            (5.0, 50.0, 1.0, 4, "critical"),
            (80.0, 80.0, 1.0, 4, "warning"),
            (80.0, 95.0, 1.0, 4, "critical"),
            (80.0, 50.0, 12.0, 4, "critical"),
            (80.0, 50.0, 6.0, 4, "warning"),  # load_per_cpu = 1.5, elevated but not critical
        ],
    )
    def test_severity_levels(
        self,
        system_snapshot_factory,
        cpu_idle: float,
        mem_used: float,
        load_1m: float,
        ncpu: int,
        expected_severity: str,
    ) -> None:
        snapshot = system_snapshot_factory(
            cpu_idle=cpu_idle,
            mem_used_percent=mem_used,
            load_1m=load_1m,
            ncpu=ncpu,
        )

        result = _build_fallback_diagnosis(snapshot)

        assert result.severity == expected_severity
        assert result.hostname == "testhost"
        assert len(result.recommendations) > 0
