"""Tests for core metric tools."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastmcp.exceptions import ToolError

from pcp_mcp.tools.metrics import (
    describe_metric,
    query_metrics,
    search_metrics,
)


class TestQueryMetrics:
    async def test_query_metrics_returns_values(
        self,
        mock_context: MagicMock,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].fetch.return_value = {
            "values": [
                {
                    "name": "kernel.all.load",
                    "instances": [
                        {"instance": "1 minute", "value": 1.5},
                        {"instance": "5 minute", "value": 1.2},
                    ],
                }
            ]
        }

        result = await query_metrics(mock_context, names=["kernel.all.load"])

        assert result.structured_content is not None
        assert len(result.structured_content["metrics"]) == 2
        assert result.structured_content["metrics"][0]["name"] == "kernel.all.load"
        assert result.structured_content["metrics"][0]["value"] == 1.5
        assert result.structured_content["metrics"][0]["instance"] == "1 minute"
        assert result.structured_content["metrics"][1]["instance"] == "5 minute"

    async def test_query_metrics_handles_no_instance(
        self,
        mock_context: MagicMock,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].fetch.return_value = {
            "values": [
                {
                    "name": "hinv.ncpu",
                    "instances": [{"instance": -1, "value": 8}],
                }
            ]
        }

        result = await query_metrics(mock_context, names=["hinv.ncpu"])

        assert result.structured_content is not None
        assert len(result.structured_content["metrics"]) == 1
        assert result.structured_content["metrics"][0]["instance"] is None
        assert result.structured_content["metrics"][0]["value"] == 8

    async def test_query_metrics_raises_on_error(
        self,
        mock_context: MagicMock,
    ) -> None:
        import httpx

        mock_context.request_context.lifespan_context[
            "client"
        ].fetch.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ToolError, match="Cannot connect to pmproxy"):
            await query_metrics(mock_context, names=["kernel.all.load"])


class TestSearchMetrics:
    async def test_search_metrics_returns_results(
        self,
        mock_context: MagicMock,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].search.return_value = [
            {"name": "kernel.all.cpu.user", "text-oneline": "User CPU time"},
            {"name": "kernel.all.cpu.sys", "text-help": "System CPU time"},
        ]

        result = await search_metrics(mock_context, pattern="kernel.all.cpu")

        assert result.structured_content is not None
        assert len(result.structured_content["results"]) == 2
        assert result.structured_content["results"][0]["name"] == "kernel.all.cpu.user"
        assert result.structured_content["results"][0]["help_text"] == "User CPU time"
        assert result.structured_content["results"][1]["help_text"] == "System CPU time"

    async def test_search_metrics_empty_results(
        self,
        mock_context: MagicMock,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].search.return_value = []

        result = await search_metrics(mock_context, pattern="nonexistent")

        assert result.structured_content is not None
        assert result.structured_content["results"] == []

    async def test_search_metrics_raises_on_error(
        self,
        mock_context: MagicMock,
    ) -> None:
        import httpx

        mock_context.request_context.lifespan_context[
            "client"
        ].search.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ToolError, match="Cannot connect to pmproxy"):
            await search_metrics(mock_context, pattern="kernel")


class TestDescribeMetric:
    async def test_describe_metric_returns_info(
        self,
        mock_context: MagicMock,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].describe.return_value = {
            "name": "kernel.all.cpu.user",
            "type": "U64",
            "sem": "counter",
            "units": "millisec",
            "text-help": "Time spent in user mode",
        }

        result = await describe_metric(mock_context, name="kernel.all.cpu.user")

        assert result.structured_content is not None
        assert result.structured_content["name"] == "kernel.all.cpu.user"
        assert result.structured_content["type"] == "U64"
        assert result.structured_content["semantics"] == "counter"
        assert result.structured_content["units"] == "millisec"
        assert result.structured_content["help_text"] == "Time spent in user mode"

    async def test_describe_metric_not_found(
        self,
        mock_context: MagicMock,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].describe.return_value = {}

        with pytest.raises(ToolError, match="Metric not found"):
            await describe_metric(mock_context, name="nonexistent.metric")

    @pytest.mark.parametrize(
        ("metric_info", "expected_units"),
        [
            ({"units": "millisec"}, "millisec"),
            ({"units": "", "units-space": "Kbyte", "units-time": "sec"}, "Kbyte / sec"),
            ({"units": "", "units-count": "count"}, "count"),
            ({"units": ""}, "none"),
            ({}, "none"),
        ],
    )
    async def test_describe_metric_formats_units(
        self,
        mock_context: MagicMock,
        metric_info: dict,
        expected_units: str,
    ) -> None:
        mock_context.request_context.lifespan_context["client"].describe.return_value = {
            "name": "test.metric",
            "type": "U64",
            "sem": "counter",
            **metric_info,
        }

        result = await describe_metric(mock_context, name="test.metric")

        assert result.structured_content is not None
        assert result.structured_content["units"] == expected_units

    async def test_describe_metric_raises_on_error(
        self,
        mock_context: MagicMock,
    ) -> None:
        import httpx

        mock_context.request_context.lifespan_context[
            "client"
        ].describe.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ToolError, match="Cannot connect to pmproxy"):
            await describe_metric(mock_context, name="kernel.all.load")
