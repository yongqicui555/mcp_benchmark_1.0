"""Tests for PCPClient using respx to mock httpx requests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from pcp_mcp.client import PCPClient


class TestPCPClientInit:
    """Tests for PCPClient initialization."""

    def test_init_defaults(self) -> None:
        """Test default initialization values."""
        client = PCPClient(base_url="http://localhost:44322")
        assert client.target_host == "localhost"
        assert client.context_id is None
        assert client._timeout == 30.0
        assert client._auth is None

    def test_init_custom_values(self) -> None:
        """Test initialization with custom values."""
        client = PCPClient(
            base_url="http://pmproxy.example.com:8080",
            target_host="webserver1",
            auth=("user", "pass"),
            timeout=60.0,
        )
        assert client.target_host == "webserver1"
        assert client._timeout == 60.0
        assert client._auth == ("user", "pass")


class TestPCPClientContextManager:
    """Tests for async context manager protocol."""

    @respx.mock
    async def test_aenter_creates_context(self) -> None:
        """Test that __aenter__ creates a pmapi context."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 42}))

        async with PCPClient(base_url="http://localhost:44322") as client:
            assert client.context_id == 42
            assert client._client is not None

    @respx.mock
    async def test_aexit_closes_client(self) -> None:
        """Test that __aexit__ closes the httpx client."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 42}))

        client = PCPClient(base_url="http://localhost:44322")
        await client.__aenter__()
        assert client._client is not None

        await client.__aexit__(None, None, None)
        assert client._client is None

    @respx.mock
    async def test_aenter_raises_on_connection_error(self) -> None:
        """Test that connection errors propagate."""
        import httpx

        respx.get("/pmapi/context").mock(side_effect=httpx.ConnectError("Connection refused"))

        with pytest.raises(httpx.ConnectError):
            async with PCPClient(base_url="http://localhost:44322"):
                pass

    @respx.mock
    async def test_aenter_raises_on_http_error(self) -> None:
        """Test that HTTP errors propagate."""
        import httpx

        respx.get("/pmapi/context").mock(return_value=Response(500, text="Internal error"))

        with pytest.raises(httpx.HTTPStatusError):
            async with PCPClient(base_url="http://localhost:44322"):
                pass


class TestPCPClientFetch:
    """Tests for fetch method."""

    @respx.mock
    async def test_fetch_single_metric(self) -> None:
        """Test fetching a single metric."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/fetch").mock(
            return_value=Response(
                200,
                json={
                    "timestamp": {"s": 1000, "us": 0},
                    "values": [
                        {
                            "name": "kernel.all.load",
                            "instances": [{"instance": 1, "value": 1.5}],
                        }
                    ],
                },
            )
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch(["kernel.all.load"])
            assert "values" in result
            assert result["values"][0]["name"] == "kernel.all.load"

    @respx.mock
    async def test_fetch_multiple_metrics(self) -> None:
        """Test fetching multiple metrics."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/fetch").mock(
            return_value=Response(
                200,
                json={
                    "timestamp": {"s": 1000, "us": 0},
                    "values": [
                        {"name": "hinv.ncpu", "instances": [{"instance": -1, "value": 4}]},
                        {"name": "mem.physmem", "instances": [{"instance": -1, "value": 16000000}]},
                    ],
                },
            )
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch(["hinv.ncpu", "mem.physmem"])
            assert len(result["values"]) == 2

    @pytest.mark.parametrize(
        ("method_name", "args"),
        [
            ("fetch", (["kernel.all.load"],)),
            ("search", ("kernel",)),
            ("describe", ("kernel.all.load",)),
        ],
    )
    async def test_method_raises_if_not_connected(
        self,
        method_name: str,
        args: tuple,
    ) -> None:
        client = PCPClient(base_url="http://localhost:44322")

        with pytest.raises(RuntimeError, match="Client not connected"):
            method = getattr(client, method_name)
            await method(*args)


class TestPCPClientSearch:
    """Tests for search method."""

    @respx.mock
    async def test_search_returns_metrics(self) -> None:
        """Test searching for metrics by prefix."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/metric").mock(
            return_value=Response(
                200,
                json={
                    "metrics": [
                        {"name": "kernel.all.load", "text-oneline": "Load average"},
                        {"name": "kernel.all.cpu.user", "text-oneline": "User CPU"},
                    ]
                },
            )
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.search("kernel.all")
            assert len(result) == 2
            assert result[0]["name"] == "kernel.all.load"

    @respx.mock
    async def test_search_empty_result(self) -> None:
        """Test searching for non-existent metrics."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/metric").mock(return_value=Response(200, json={"metrics": []}))

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.search("nonexistent.metric")
            assert result == []


class TestPCPClientDescribe:
    """Tests for describe method."""

    @respx.mock
    async def test_describe_returns_metadata(self) -> None:
        """Test describing a metric returns metadata."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/metric").mock(
            return_value=Response(
                200,
                json={
                    "metrics": [
                        {
                            "name": "kernel.all.load",
                            "text-oneline": "Load average",
                            "sem": "instant",
                            "type": "float",
                        }
                    ]
                },
            )
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.describe("kernel.all.load")
            assert result["name"] == "kernel.all.load"
            assert result["sem"] == "instant"

    @respx.mock
    async def test_describe_returns_empty_for_unknown(self) -> None:
        """Test describing unknown metric returns empty dict."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/metric").mock(return_value=Response(200, json={"metrics": []}))

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.describe("nonexistent.metric")
            assert result == {}


class TestPCPClientContextRecreation:
    """Tests for automatic context recreation on expiration."""

    @pytest.mark.parametrize(
        ("method_name", "args", "endpoint", "expired_response", "success_response", "verify"),
        [
            pytest.param(
                "fetch",
                (["hinv.ncpu"],),
                "/pmapi/fetch",
                Response(400, json={"message": "unknown context identifier"}),
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1000, "us": 0},
                        "values": [{"name": "hinv.ncpu", "instances": [{"value": 4}]}],
                    },
                ),
                lambda r: r["values"][0]["instances"][0]["value"] == 4,
                id="fetch",
            ),
            pytest.param(
                "search",
                ("kernel",),
                "/pmapi/metric",
                Response(400, json={"message": "unknown context identifier"}),
                Response(200, json={"metrics": [{"name": "kernel.all.load"}]}),
                lambda r: len(r) == 1,
                id="search",
            ),
            pytest.param(
                "describe",
                ("hinv.ncpu",),
                "/pmapi/metric",
                Response(400, json={"message": "unknown context identifier"}),
                Response(200, json={"metrics": [{"name": "hinv.ncpu", "sem": "instant"}]}),
                lambda r: r.get("sem") == "instant",
                id="describe",
            ),
        ],
    )
    @respx.mock
    async def test_recreates_context_on_expiration(
        self,
        method_name: str,
        args: tuple,
        endpoint: str,
        expired_response: Response,
        success_response: Response,
        verify,
    ) -> None:
        """Test that methods recreate context when it expires."""
        respx.get("/pmapi/context").mock(
            side_effect=[
                Response(200, json={"context": 1}),
                Response(200, json={"context": 2}),
            ]
        )
        respx.get(endpoint).mock(side_effect=[expired_response, success_response])

        async with PCPClient(base_url="http://localhost:44322") as client:
            assert client.context_id == 1
            method = getattr(client, method_name)
            result = await method(*args)
            assert client.context_id == 2
            assert verify(result)

    @respx.mock
    async def test_does_not_recreate_on_other_400_errors(self) -> None:
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/fetch").mock(
            return_value=Response(400, json={"message": "invalid metric name"})
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            resp = await client._request_with_retry(
                "GET", url="/pmapi/fetch", params={"context": 1, "names": "bad.metric"}
            )
            assert resp.status_code == 400


class TestPCPClientFetchWithRates:
    """Tests for fetch_with_rates method."""

    @respx.mock
    async def test_fetch_with_rates_calculates_rate_for_counters(self) -> None:
        """Test that counter metrics are converted to rates."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))

        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1000, "us": 0},
                        "values": [
                            {
                                "name": "disk.all.read_bytes",
                                "instances": [{"instance": -1, "value": 1000000}],
                            }
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1001, "us": 0},
                        "values": [
                            {
                                "name": "disk.all.read_bytes",
                                "instances": [{"instance": -1, "value": 1100000}],
                            }
                        ],
                    },
                ),
            ]
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["disk.all.read_bytes"],
                counter_metrics={"disk.all.read_bytes"},
                sample_interval=0.01,
            )

            assert "disk.all.read_bytes" in result
            assert result["disk.all.read_bytes"]["is_rate"] is True
            assert result["disk.all.read_bytes"]["instances"][-1] == pytest.approx(100000.0)

    @respx.mock
    async def test_fetch_with_rates_returns_instant_for_gauges(self) -> None:
        """Test that gauge metrics return instant values."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))

        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1000, "us": 0},
                        "values": [
                            {
                                "name": "mem.util.used",
                                "instances": [{"instance": -1, "value": 8000000}],
                            }
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1001, "us": 0},
                        "values": [
                            {
                                "name": "mem.util.used",
                                "instances": [{"instance": -1, "value": 8500000}],
                            }
                        ],
                    },
                ),
            ]
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["mem.util.used"],
                counter_metrics=set(),
                sample_interval=0.01,
            )

            assert "mem.util.used" in result
            assert result["mem.util.used"]["is_rate"] is False
            assert result["mem.util.used"]["instances"][-1] == 8500000

    @respx.mock
    async def test_fetch_with_rates_handles_counter_wraparound(self) -> None:
        """Test that counter wraparound is handled gracefully."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))

        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1000, "us": 0},
                        "values": [
                            {
                                "name": "network.interface.in.bytes",
                                "instances": [{"instance": 0, "value": 4294967290}],
                            }
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1001, "us": 0},
                        "values": [
                            {
                                "name": "network.interface.in.bytes",
                                "instances": [{"instance": 0, "value": 100}],
                            }
                        ],
                    },
                ),
            ]
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["network.interface.in.bytes"],
                counter_metrics={"network.interface.in.bytes"},
                sample_interval=0.01,
            )

            assert result["network.interface.in.bytes"]["instances"][0] == pytest.approx(100.0)

    @respx.mock
    async def test_fetch_with_rates_multiple_instances(self) -> None:
        """Test rate calculation with multiple instances (per-CPU, per-disk)."""
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))

        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1000, "us": 0},
                        "values": [
                            {
                                "name": "kernel.percpu.cpu.user",
                                "instances": [
                                    {"instance": 0, "value": 1000},
                                    {"instance": 1, "value": 2000},
                                ],
                            }
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1001, "us": 0},
                        "values": [
                            {
                                "name": "kernel.percpu.cpu.user",
                                "instances": [
                                    {"instance": 0, "value": 1100},
                                    {"instance": 1, "value": 2300},
                                ],
                            }
                        ],
                    },
                ),
            ]
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["kernel.percpu.cpu.user"],
                counter_metrics={"kernel.percpu.cpu.user"},
                sample_interval=0.01,
            )

            instances = result["kernel.percpu.cpu.user"]["instances"]
            assert instances[0] == pytest.approx(100.0)
            assert instances[1] == pytest.approx(300.0)

    @respx.mock
    async def test_fetch_with_rates_handles_float_timestamps(self) -> None:
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))

        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": 1000.0,
                        "values": [
                            {
                                "name": "disk.all.read_bytes",
                                "instances": [{"instance": -1, "value": 1000000}],
                            }
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": 1001.5,
                        "values": [
                            {
                                "name": "disk.all.read_bytes",
                                "instances": [{"instance": -1, "value": 1150000}],
                            }
                        ],
                    },
                ),
            ]
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["disk.all.read_bytes"],
                counter_metrics={"disk.all.read_bytes"},
                sample_interval=0.01,
            )

            assert result["disk.all.read_bytes"]["instances"][-1] == pytest.approx(100000.0)

    @respx.mock
    async def test_fetch_with_rates_uses_sample_interval_when_timestamps_invalid(self) -> None:
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))

        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": 0.0,
                        "values": [
                            {
                                "name": "disk.all.read_bytes",
                                "instances": [{"instance": -1, "value": 1000000}],
                            }
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": 0.0,
                        "values": [
                            {
                                "name": "disk.all.read_bytes",
                                "instances": [{"instance": -1, "value": 1100000}],
                            }
                        ],
                    },
                ),
            ]
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["disk.all.read_bytes"],
                counter_metrics={"disk.all.read_bytes"},
                sample_interval=1.0,
            )

            assert result["disk.all.read_bytes"]["instances"][-1] == pytest.approx(100000.0)

    @respx.mock
    async def test_fetch_with_rates_calls_progress_callback(self) -> None:
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/fetch").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1000, "us": 0},
                        "values": [
                            {"name": "hinv.ncpu", "instances": [{"instance": -1, "value": 4}]}
                        ],
                    },
                ),
                Response(
                    200,
                    json={
                        "timestamp": {"s": 1001, "us": 0},
                        "values": [
                            {"name": "hinv.ncpu", "instances": [{"instance": -1, "value": 4}]}
                        ],
                    },
                ),
            ]
        )

        progress_calls: list[tuple[float, float, str]] = []

        async def track_progress(current: float, total: float, message: str) -> None:
            progress_calls.append((current, total, message))

        async with PCPClient(base_url="http://localhost:44322") as client:
            await client.fetch_with_rates(
                metric_names=["hinv.ncpu"],
                counter_metrics=set(),
                sample_interval=0.01,
                progress_callback=track_progress,
            )

        assert len(progress_calls) == 4
        assert progress_calls[0][0] == 0
        assert progress_calls[-1][0] == 90
        assert "first sample" in progress_calls[0][2].lower()
        assert "rate" in progress_calls[1][2].lower()

    @respx.mock
    async def test_fetch_with_rates_works_without_progress_callback(self) -> None:
        respx.get("/pmapi/context").mock(return_value=Response(200, json={"context": 1}))
        respx.get("/pmapi/fetch").mock(
            return_value=Response(
                200,
                json={
                    "timestamp": {"s": 1000, "us": 0},
                    "values": [{"name": "hinv.ncpu", "instances": [{"instance": -1, "value": 4}]}],
                },
            )
        )

        async with PCPClient(base_url="http://localhost:44322") as client:
            result = await client.fetch_with_rates(
                metric_names=["hinv.ncpu"],
                counter_metrics=set(),
                sample_interval=0.01,
            )

        assert "hinv.ncpu" in result
