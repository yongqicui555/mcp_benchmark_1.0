"""Tests for network protocol statistics tools."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest
from fastmcp.exceptions import ToolError

from pcp_mcp.tools.network import _assess_network_stats, get_network_stats
from pcp_mcp.utils.builders import build_interface_errors, build_tcp_stats, build_udp_stats

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def network_tools() -> dict:
    """Fixture providing network tools as a dictionary."""
    return {
        "get_network_stats": get_network_stats,
    }


@pytest.fixture
def tcp_metrics_data() -> Callable[..., dict]:
    """Factory for TCP metrics data with configurable values."""

    def _make(
        active_opens: float = 5.0,
        passive_opens: float = 10.0,
        attempt_fails: float = 0.5,
        estab_resets: float = 0.2,
        current_estab: int = 150,
        retrans: float = 1.0,
        in_errs: float = 0.0,
        out_rsts: float = 0.3,
    ) -> dict:
        return {
            "network.tcp.activeopens": {"instances": {-1: active_opens}},
            "network.tcp.passiveopens": {"instances": {-1: passive_opens}},
            "network.tcp.attemptfails": {"instances": {-1: attempt_fails}},
            "network.tcp.estabresets": {"instances": {-1: estab_resets}},
            "network.tcp.currestab": {"instances": {-1: current_estab}},
            "network.tcp.retranssegs": {"instances": {-1: retrans}},
            "network.tcp.inerrs": {"instances": {-1: in_errs}},
            "network.tcp.outrsts": {"instances": {-1: out_rsts}},
        }

    return _make


@pytest.fixture
def udp_metrics_data() -> Callable[..., dict]:
    """Factory for UDP metrics data with configurable values."""

    def _make(
        in_dgrams: float = 500.0,
        out_dgrams: float = 300.0,
        in_errs: float = 0.0,
        no_ports: float = 2.0,
    ) -> dict:
        return {
            "network.udp.indatagrams": {"instances": {-1: in_dgrams}},
            "network.udp.outdatagrams": {"instances": {-1: out_dgrams}},
            "network.udp.inerrors": {"instances": {-1: in_errs}},
            "network.udp.noports": {"instances": {-1: no_ports}},
        }

    return _make


@pytest.fixture
def interface_error_metrics_data() -> Callable[..., dict]:
    """Factory for interface error metrics data with configurable values."""

    def _make(
        in_errors: dict[str, float] | None = None,
        out_errors: dict[str, float] | None = None,
        in_drops: dict[str, float] | None = None,
    ) -> dict:
        return {
            "network.interface.in.errors": {"instances": in_errors or {"eth0": 0.0, "lo": 0.0}},
            "network.interface.out.errors": {"instances": out_errors or {"eth0": 0.0, "lo": 0.0}},
            "network.interface.in.drops": {"instances": in_drops or {"eth0": 0.0, "lo": 0.0}},
        }

    return _make


@pytest.fixture
def full_network_stats_data(
    tcp_metrics_data,
    udp_metrics_data,
    interface_error_metrics_data,
) -> Callable[..., dict]:
    """Factory for full network stats data combining TCP, UDP, and interface errors."""

    def _make(**overrides) -> dict:
        data = {}
        data.update(tcp_metrics_data())
        data.update(udp_metrics_data())
        data.update(interface_error_metrics_data())
        for key, value in overrides.items():
            if key in data:
                data[key] = value
        return data

    return _make


# =============================================================================
# Tool Tests
# =============================================================================


class TestGetNetworkStats:
    async def test_returns_all_sections(
        self,
        mock_context: MagicMock,
        network_tools: dict,
        full_network_stats_data: Callable[..., dict],
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_network_stats_data()

        result = await network_tools["get_network_stats"](mock_context)

        assert result.structured_content["tcp"] is not None
        assert result.structured_content["udp"] is not None
        assert result.structured_content["interface_errors"] is not None
        assert result.structured_content["hostname"] == "localhost"
        assert result.structured_content["assessment"] is not None

    async def test_tcp_fields_present(
        self,
        mock_context: MagicMock,
        network_tools: dict,
        full_network_stats_data: Callable[..., dict],
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_network_stats_data()

        result = await network_tools["get_network_stats"](mock_context)
        tcp = result.structured_content["tcp"]

        assert "active_opens_per_sec" in tcp
        assert "passive_opens_per_sec" in tcp
        assert "attempt_fails_per_sec" in tcp
        assert "estab_resets_per_sec" in tcp
        assert "current_established" in tcp
        assert "retransmits_per_sec" in tcp
        assert "in_errors_per_sec" in tcp
        assert "out_resets_per_sec" in tcp
        assert "assessment" in tcp

    async def test_udp_fields_present(
        self,
        mock_context: MagicMock,
        network_tools: dict,
        full_network_stats_data: Callable[..., dict],
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_network_stats_data()

        result = await network_tools["get_network_stats"](mock_context)
        udp = result.structured_content["udp"]

        assert "in_datagrams_per_sec" in udp
        assert "out_datagrams_per_sec" in udp
        assert "in_errors_per_sec" in udp
        assert "no_ports_per_sec" in udp
        assert "assessment" in udp

    async def test_interface_errors_present(
        self,
        mock_context: MagicMock,
        network_tools: dict,
        full_network_stats_data: Callable[..., dict],
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_network_stats_data()

        result = await network_tools["get_network_stats"](mock_context)
        iface_errors = result.structured_content["interface_errors"]

        assert len(iface_errors) == 2
        assert iface_errors[0]["interface"] in ("eth0", "lo")

    async def test_reports_progress(
        self,
        mock_context: MagicMock,
        network_tools: dict,
        full_network_stats_data: Callable[..., dict],
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.return_value = full_network_stats_data()
        mock_context.report_progress = AsyncMock()

        await network_tools["get_network_stats"](mock_context)

        assert mock_context.report_progress.call_count >= 2
        calls = mock_context.report_progress.call_args_list
        assert calls[-1] == call(100, 100, "Complete")

    async def test_handles_connection_error(
        self,
        mock_context: MagicMock,
        network_tools: dict,
    ) -> None:
        mock_context.request_context.lifespan_context[
            "client"
        ].fetch_with_rates.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ToolError, match="Cannot connect to pmproxy"):
            await network_tools["get_network_stats"](mock_context)


# =============================================================================
# Builder Tests
# =============================================================================


class TestBuildTcpStats:
    def test_builds_from_normal_data(self, tcp_metrics_data) -> None:
        result = build_tcp_stats(tcp_metrics_data())

        assert result.active_opens_per_sec == 5.0
        assert result.passive_opens_per_sec == 10.0
        assert result.current_established == 150
        assert result.retransmits_per_sec == 1.0
        assert "normal" in result.assessment.lower()

    @pytest.mark.parametrize(
        ("retrans", "expected_keyword"),
        [
            (150.0, "heavy"),
            (15.0, "moderate"),
            (0.0, "normal"),
        ],
    )
    def test_retransmit_assessment(
        self, tcp_metrics_data, retrans: float, expected_keyword: str
    ) -> None:
        result = build_tcp_stats(tcp_metrics_data(retrans=retrans))
        assert expected_keyword.lower() in result.assessment.lower()

    def test_high_attempt_fails(self, tcp_metrics_data) -> None:
        result = build_tcp_stats(tcp_metrics_data(attempt_fails=20.0))
        assert "failure" in result.assessment.lower()

    def test_high_estab_resets(self, tcp_metrics_data) -> None:
        result = build_tcp_stats(tcp_metrics_data(estab_resets=15.0))
        assert "reset" in result.assessment.lower()

    def test_in_errors(self, tcp_metrics_data) -> None:
        result = build_tcp_stats(tcp_metrics_data(in_errs=5.0))
        assert "malformed" in result.assessment.lower()


class TestBuildUdpStats:
    def test_builds_from_normal_data(self, udp_metrics_data) -> None:
        result = build_udp_stats(udp_metrics_data())

        assert result.in_datagrams_per_sec == 500.0
        assert result.out_datagrams_per_sec == 300.0
        assert result.in_errors_per_sec == 0.0
        assert "normal" in result.assessment.lower()

    def test_high_in_errors(self, udp_metrics_data) -> None:
        result = build_udp_stats(udp_metrics_data(in_errs=20.0))
        assert "error" in result.assessment.lower()

    def test_high_no_ports(self, udp_metrics_data) -> None:
        result = build_udp_stats(udp_metrics_data(no_ports=200.0))
        assert "closed ports" in result.assessment.lower()

    def test_some_errors(self, udp_metrics_data) -> None:
        result = build_udp_stats(udp_metrics_data(in_errs=3.0))
        assert "some" in result.assessment.lower()


class TestBuildInterfaceErrors:
    def test_builds_from_normal_data(self, interface_error_metrics_data) -> None:
        result = build_interface_errors(interface_error_metrics_data())

        assert len(result) == 2
        iface_names = [ie.interface for ie in result]
        assert "eth0" in iface_names
        assert "lo" in iface_names

    def test_sorted_by_interface_name(self, interface_error_metrics_data) -> None:
        result = build_interface_errors(interface_error_metrics_data())
        names = [ie.interface for ie in result]
        assert names == sorted(names)

    def test_captures_error_values(self, interface_error_metrics_data) -> None:
        data = interface_error_metrics_data(
            in_errors={"eth0": 5.0, "lo": 0.0},
            out_errors={"eth0": 2.0, "lo": 0.0},
            in_drops={"eth0": 1.0, "lo": 0.0},
        )
        result = build_interface_errors(data)

        eth0 = next(ie for ie in result if ie.interface == "eth0")
        assert eth0.in_errors_per_sec == 5.0
        assert eth0.out_errors_per_sec == 2.0
        assert eth0.in_drops_per_sec == 1.0

    def test_handles_empty_data(self) -> None:
        data = {
            "network.interface.in.errors": {"instances": {}},
            "network.interface.out.errors": {"instances": {}},
            "network.interface.in.drops": {"instances": {}},
        }
        result = build_interface_errors(data)
        assert result == []


# =============================================================================
# Assessment Tests
# =============================================================================


class TestAssessNetworkStats:
    def test_healthy_assessment(self, tcp_metrics_data, udp_metrics_data) -> None:
        tcp = build_tcp_stats(tcp_metrics_data())
        udp = build_udp_stats(udp_metrics_data())
        iface_errors = []

        result = _assess_network_stats(tcp, udp, iface_errors)
        assert "normal" in result.lower()

    def test_retransmit_issue(self, tcp_metrics_data, udp_metrics_data) -> None:
        tcp = build_tcp_stats(tcp_metrics_data(retrans=50.0))
        udp = build_udp_stats(udp_metrics_data())
        iface_errors = []

        result = _assess_network_stats(tcp, udp, iface_errors)
        assert "retransmission" in result.lower()

    def test_interface_error_issue(
        self, tcp_metrics_data, udp_metrics_data, interface_error_metrics_data
    ) -> None:
        tcp = build_tcp_stats(tcp_metrics_data())
        udp = build_udp_stats(udp_metrics_data())
        iface_errors = build_interface_errors(
            interface_error_metrics_data(in_errors={"eth0": 5.0, "lo": 0.0})
        )

        result = _assess_network_stats(tcp, udp, iface_errors)
        assert "eth0" in result

    def test_multiple_issues(self, tcp_metrics_data, udp_metrics_data) -> None:
        tcp = build_tcp_stats(tcp_metrics_data(retrans=200.0, attempt_fails=20.0))
        udp = build_udp_stats(udp_metrics_data(in_errs=15.0))
        iface_errors = []

        result = _assess_network_stats(tcp, udp, iface_errors)
        assert "retransmission" in result.lower()
        assert "failure" in result.lower()
        assert "udp" in result.lower()
