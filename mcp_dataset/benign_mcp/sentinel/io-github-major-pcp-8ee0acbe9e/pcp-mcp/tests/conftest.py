"""Pytest fixtures for pcp-mcp tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import FastMCP

from pcp_mcp.client import PCPClient
from pcp_mcp.config import PCPMCPSettings
from pcp_mcp.models import (
    CPUMetrics,
    FilesystemInfo,
    LoadMetrics,
    MemoryMetrics,
    SystemSnapshot,
)

# =============================================================================
# Smoke Test Server Fixture - Server without real pmproxy connection
# =============================================================================


@asynccontextmanager
async def _mock_lifespan(mcp: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """No-op lifespan for smoke tests that doesn't connect to pmproxy.

    Yields a mock context with AsyncMock client and real settings.
    Allows testing tool/prompt registration without network access.
    """
    mock_client = AsyncMock(spec=PCPClient)
    mock_client.target_host = "localhost"
    mock_client.context_id = 12345
    yield {"client": mock_client, "settings": PCPMCPSettings()}


@pytest.fixture
def smoke_test_server() -> FastMCP:
    """Create a server with mock lifespan for smoke tests.

    This server uses a no-op lifespan that doesn't connect to pmproxy,
    allowing smoke tests to run in CI without a real PCP installation.
    Uses FileSystemProvider for tool/prompt discovery just like production.
    """
    from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
    from fastmcp.server.providers import FileSystemProvider

    from pcp_mcp.middleware import MetricCacheMiddleware

    mcp = FastMCP(name="pcp", lifespan=_mock_lifespan)
    mcp.add_middleware(StructuredLoggingMiddleware(include_payload_length=True))
    mcp.add_middleware(MetricCacheMiddleware())

    # Use FileSystemProvider same as production server
    base_dir = Path(__file__).parent.parent / "src" / "pcp_mcp"
    provider = FileSystemProvider(root=base_dir, reload=False)
    mcp.add_provider(provider)

    return mcp


# =============================================================================
# Metric Data Factories - Use these like to build test data without duplication
# =============================================================================
# Metric Data Factories - Use these to build test data without duplication
# =============================================================================


@pytest.fixture
def cpu_metrics_data() -> Callable[..., dict]:
    """Factory for CPU metrics data with configurable values."""

    def _make(
        user: float = 20.0,
        sys: float = 10.0,
        idle: float = 65.0,
        iowait: float = 5.0,
        ncpu: int = 4,
    ) -> dict:
        return {
            "kernel.all.cpu.user": {"instances": {-1: user}},
            "kernel.all.cpu.sys": {"instances": {-1: sys}},
            "kernel.all.cpu.idle": {"instances": {-1: idle}},
            "kernel.all.cpu.wait.total": {"instances": {-1: iowait}},
            "hinv.ncpu": {"instances": {-1: ncpu}},
        }

    return _make


@pytest.fixture
def memory_metrics_data() -> Callable[..., dict]:
    """Factory for memory metrics data with configurable values."""

    def _make(
        physmem: int = 16_000_000,
        free: int = 4_000_000,
        available: int = 6_000_000,
        cached: int = 2_000_000,
        bufmem: int = 1_000_000,
        swap_total: int = 8_000_000,
        swap_free: int = 7_000_000,
    ) -> dict:
        return {
            "mem.physmem": {"instances": {-1: physmem}},
            "mem.util.free": {"instances": {-1: free}},
            "mem.util.available": {"instances": {-1: available}},
            "mem.util.cached": {"instances": {-1: cached}},
            "mem.util.bufmem": {"instances": {-1: bufmem}},
            "mem.util.swapTotal": {"instances": {-1: swap_total}},
            "mem.util.swapFree": {"instances": {-1: swap_free}},
        }

    return _make


@pytest.fixture
def load_metrics_data() -> Callable[..., dict]:
    """Factory for load metrics data with configurable values."""

    def _make(
        load_1m: float = 1.5,
        load_5m: float = 1.2,
        load_15m: float = 1.0,
        runnable: int = 3,
        nprocs: int = 200,
        ncpu: int = 4,
    ) -> dict:
        return {
            "kernel.all.load": {"instances": {1: load_1m, 5: load_5m, 15: load_15m}},
            "kernel.all.runnable": {"instances": {-1: runnable}},
            "kernel.all.nprocs": {"instances": {-1: nprocs}},
            "hinv.ncpu": {"instances": {-1: ncpu}},
        }

    return _make


@pytest.fixture
def disk_metrics_data() -> Callable[..., dict]:
    """Factory for disk metrics data with configurable values."""

    def _make(
        read_bytes: float = 1_000_000.0,
        write_bytes: float = 500_000.0,
        reads: float = 100.0,
        writes: float = 50.0,
    ) -> dict:
        return {
            "disk.all.read_bytes": {"instances": {-1: read_bytes}},
            "disk.all.write_bytes": {"instances": {-1: write_bytes}},
            "disk.all.read": {"instances": {-1: reads}},
            "disk.all.write": {"instances": {-1: writes}},
        }

    return _make


@pytest.fixture
def network_metrics_data() -> Callable[..., dict]:
    """Factory for network metrics data with configurable values."""

    def _make(
        in_bytes: dict | None = None,
        out_bytes: dict | None = None,
        in_packets: dict | None = None,
        out_packets: dict | None = None,
    ) -> dict:
        return {
            "network.interface.in.bytes": {
                "instances": in_bytes or {"eth0": 100_000.0, "lo": 1_000.0}
            },
            "network.interface.out.bytes": {
                "instances": out_bytes or {"eth0": 50_000.0, "lo": 1_000.0}
            },
            "network.interface.in.packets": {
                "instances": in_packets or {"eth0": 1_000.0, "lo": 10.0}
            },
            "network.interface.out.packets": {
                "instances": out_packets or {"eth0": 500.0, "lo": 10.0}
            },
        }

    return _make


@pytest.fixture
def process_metrics_data() -> Callable[..., dict]:
    """Factory for process metrics data with configurable values."""

    def _make(
        processes: list[dict] | None = None,
    ) -> dict:
        if processes is None:
            processes = [
                {
                    "inst": 1,
                    "pid": 1234,
                    "cmd": "python",
                    "args": "python app.py",
                    "rss": 1_000_000,
                },
                {"inst": 2, "pid": 5678, "cmd": "nginx", "args": "nginx -g daemon", "rss": 500_000},
            ]

        return {
            "proc.psinfo.pid": {"instances": {p["inst"]: p["pid"] for p in processes}},
            "proc.psinfo.cmd": {"instances": {p["inst"]: p["cmd"] for p in processes}},
            "proc.psinfo.psargs": {"instances": {p["inst"]: p["args"] for p in processes}},
            "proc.memory.rss": {"instances": {p["inst"]: p["rss"] for p in processes}},
            "proc.psinfo.utime": {
                "instances": {p["inst"]: p.get("utime", 100.0) for p in processes}
            },
            "proc.psinfo.stime": {
                "instances": {p["inst"]: p.get("stime", 50.0) for p in processes}
            },
            "proc.io.read_bytes": {
                "instances": {p["inst"]: p.get("io_read", 1000.0) for p in processes}
            },
            "proc.io.write_bytes": {
                "instances": {p["inst"]: p.get("io_write", 500.0) for p in processes}
            },
        }

    return _make


@pytest.fixture
def full_system_snapshot_data(
    cpu_metrics_data,
    memory_metrics_data,
    load_metrics_data,
    disk_metrics_data,
    network_metrics_data,
) -> Callable[..., dict]:
    """Factory for full system snapshot data combining all metric types."""

    def _make(**overrides) -> dict:
        data = {}
        data.update(cpu_metrics_data())
        data.update(memory_metrics_data())
        data.update(load_metrics_data())
        data.update(disk_metrics_data())
        data.update(network_metrics_data())
        for key, value in overrides.items():
            if key in data:
                data[key] = value
        return data

    return _make


@pytest.fixture
def filesystem_metrics_response() -> Callable[..., dict]:
    """Factory for filesystem metrics pmproxy response format."""

    def _make(
        filesystems: list[dict] | None = None,
    ) -> dict:
        if filesystems is None:
            filesystems = [
                {
                    "instance": 0,
                    "mountdir": "/",
                    "type": "ext4",
                    "capacity": 100_000_000,
                    "used": 20_000_000,
                    "avail": 75_000_000,
                    "full": 20.0,
                },
                {
                    "instance": 1,
                    "mountdir": "/boot",
                    "type": "ext4",
                    "capacity": 1_000_000,
                    "used": 500_000,
                    "avail": 450_000,
                    "full": 50.0,
                },
            ]

        return {
            "values": [
                {
                    "name": "filesys.mountdir",
                    "instances": [
                        {"instance": fs["instance"], "value": fs["mountdir"]} for fs in filesystems
                    ],
                },
                {
                    "name": "filesys.capacity",
                    "instances": [
                        {"instance": fs["instance"], "value": fs["capacity"]} for fs in filesystems
                    ],
                },
                {
                    "name": "filesys.used",
                    "instances": [
                        {"instance": fs["instance"], "value": fs["used"]} for fs in filesystems
                    ],
                },
                {
                    "name": "filesys.avail",
                    "instances": [
                        {"instance": fs["instance"], "value": fs["avail"]} for fs in filesystems
                    ],
                },
                {
                    "name": "filesys.full",
                    "instances": [
                        {"instance": fs["instance"], "value": fs["full"]} for fs in filesystems
                    ],
                },
                {
                    "name": "filesys.type",
                    "instances": [
                        {"instance": fs["instance"], "value": fs["type"]} for fs in filesystems
                    ],
                },
            ]
        }

    return _make


@pytest.fixture
def pmproxy_fetch_response() -> Callable[..., dict]:
    """Factory for pmproxy fetch API response format."""

    def _make(
        values: list[dict],
        timestamp_s: int = 1000,
        timestamp_us: int = 0,
    ) -> dict:
        return {
            "timestamp": {"s": timestamp_s, "us": timestamp_us},
            "values": values,
        }

    return _make


@pytest.fixture
def mock_settings() -> PCPMCPSettings:
    """Create mock settings for testing."""
    return PCPMCPSettings(
        host="localhost",
        port=44322,
        target_host="localhost",
    )


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mock PCPClient."""
    client = AsyncMock(spec=PCPClient)
    client.target_host = "localhost"
    client.context_id = 12345
    return client


@pytest.fixture
def mock_lifespan_context(
    mock_client: AsyncMock,
    mock_settings: PCPMCPSettings,
) -> dict[str, Any]:
    """Create mock lifespan context."""
    return {"client": mock_client, "settings": mock_settings}


@pytest.fixture
def mock_context(mock_lifespan_context: dict[str, Any]) -> MagicMock:
    """Create a mock MCP Context."""
    from fastmcp import Context

    ctx = MagicMock(spec=Context)
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = mock_lifespan_context
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.fixture
def namespace_search_response() -> Callable[..., list[dict]]:
    def _make(namespaces: list[str] | None = None) -> list[dict]:
        if namespaces is None:
            namespaces = ["kernel.all.load", "kernel.all.cpu.user", "mem.physmem", "disk.all.read"]
        return [{"name": ns} for ns in namespaces]

    return _make


@pytest.fixture
def pmda_status_response() -> Callable[..., dict]:
    def _make(pmdas: list[tuple[str | int, int]] | None = None) -> dict:
        if pmdas is None:
            pmdas = [("linux", 0), ("pmcd", 0)]
        return {
            "values": [
                {
                    "name": "pmcd.agent.status",
                    "instances": [{"instance": name, "value": status} for name, status in pmdas],
                }
            ]
        }

    return _make


@pytest.fixture
def filesystem_info_factory() -> Callable[..., FilesystemInfo]:
    def _make(
        mount_point: str = "/",
        fs_type: str = "ext4",
        capacity_bytes: int = 100_000,
        used_bytes: int = 20_000,
        available_bytes: int = 80_000,
        percent_full: float = 20.0,
    ) -> FilesystemInfo:
        return FilesystemInfo(
            mount_point=mount_point,
            fs_type=fs_type,
            capacity_bytes=capacity_bytes,
            used_bytes=used_bytes,
            available_bytes=available_bytes,
            percent_full=percent_full,
        )

    return _make


@pytest.fixture
def system_snapshot_factory() -> Callable[..., SystemSnapshot]:
    def _make(
        hostname: str = "testhost",
        cpu_idle: float = 80.0,
        mem_used_percent: float = 50.0,
        load_1m: float = 1.0,
        ncpu: int = 4,
    ) -> SystemSnapshot:
        total_mem = 16 * 1024**3
        return SystemSnapshot(
            timestamp="2025-01-18T12:00:00Z",
            hostname=hostname,
            cpu=CPUMetrics(
                user_percent=100 - cpu_idle - 5,
                system_percent=5.0,
                idle_percent=cpu_idle,
                iowait_percent=0.0,
                ncpu=ncpu,
                assessment="test",
            ),
            memory=MemoryMetrics(
                total_bytes=total_mem,
                used_bytes=int(total_mem * mem_used_percent / 100),
                free_bytes=int(total_mem * (100 - mem_used_percent) / 100),
                available_bytes=int(total_mem * (100 - mem_used_percent) / 100),
                cached_bytes=0,
                buffers_bytes=0,
                swap_used_bytes=0,
                swap_total_bytes=0,
                used_percent=mem_used_percent,
                assessment="test",
            ),
            load=LoadMetrics(
                load_1m=load_1m,
                load_5m=load_1m,
                load_15m=load_1m,
                runnable=1,
                nprocs=100,
                assessment="test",
            ),
        )

    return _make
