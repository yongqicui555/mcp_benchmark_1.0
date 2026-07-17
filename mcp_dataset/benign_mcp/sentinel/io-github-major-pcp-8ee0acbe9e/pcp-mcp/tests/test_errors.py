"""Tests for error handling and mapping.

Note: These tests import error classes inside test methods to avoid stale class
references after FastMCP's FileSystemProvider reloads modules during test runs.
"""

from __future__ import annotations

import httpx
import pytest
from fastmcp.exceptions import ToolError

import pcp_mcp.errors


class TestPCPErrorClasses:
    def test_pcp_error_is_base_exception(self) -> None:
        err = pcp_mcp.errors.PCPError("base error")
        assert isinstance(err, Exception)
        assert str(err) == "base error"

    def test_pcp_connection_error_inherits_from_pcp_error(self) -> None:
        err = pcp_mcp.errors.PCPConnectionError("cannot connect")
        assert isinstance(err, pcp_mcp.errors.PCPError)
        assert str(err) == "cannot connect"

    def test_pcp_metric_not_found_error_inherits_from_pcp_error(self) -> None:
        err = pcp_mcp.errors.PCPMetricNotFoundError("metric.not.found")
        assert isinstance(err, pcp_mcp.errors.PCPError)
        assert str(err) == "metric.not.found"


class TestHandlePCPError:
    def test_handles_httpx_connect_error(self) -> None:
        err = httpx.ConnectError("Connection refused")
        result = pcp_mcp.errors.handle_pcp_error(err, "fetching metrics")

        assert isinstance(result, ToolError)
        assert "Cannot connect to pmproxy" in str(result)
        assert "systemctl start pmproxy" in str(result)

    def test_handles_httpx_400_bad_request(self) -> None:
        response = httpx.Response(400, text="Invalid metric name")
        request = httpx.Request("GET", "http://localhost/pmapi/fetch")
        err = httpx.HTTPStatusError("Bad request", request=request, response=response)

        result = pcp_mcp.errors.handle_pcp_error(err, "fetching metrics")

        assert isinstance(result, ToolError)
        assert "Bad request during fetching metrics" in str(result)
        assert "Invalid metric name" in str(result)

    def test_handles_httpx_404_not_found(self) -> None:
        response = httpx.Response(404, text="Not found")
        request = httpx.Request("GET", "http://localhost/pmapi/fetch")
        err = httpx.HTTPStatusError("Not found", request=request, response=response)

        result = pcp_mcp.errors.handle_pcp_error(err, "describing metric")

        assert isinstance(result, ToolError)
        assert "Metric not found during describing metric" in str(result)

    def test_handles_httpx_500_server_error(self) -> None:
        response = httpx.Response(500, text="Internal server error")
        request = httpx.Request("GET", "http://localhost/pmapi/fetch")
        err = httpx.HTTPStatusError("Server error", request=request, response=response)

        result = pcp_mcp.errors.handle_pcp_error(err, "fetching")

        assert isinstance(result, ToolError)
        assert "pmproxy error (500)" in str(result)
        assert "Internal server error" in str(result)

    def test_handles_httpx_timeout(self) -> None:
        err = httpx.TimeoutException("Request timed out")

        result = pcp_mcp.errors.handle_pcp_error(err, "searching metrics")

        assert isinstance(result, ToolError)
        assert "Request timed out during searching metrics" in str(result)

    def test_handles_pcp_connection_error(self) -> None:
        err = pcp_mcp.errors.PCPConnectionError("Custom connection failure")

        result = pcp_mcp.errors.handle_pcp_error(err, "connecting")

        assert isinstance(result, ToolError)
        assert "Custom connection failure" in str(result)

    def test_handles_pcp_metric_not_found_error(self) -> None:
        err = pcp_mcp.errors.PCPMetricNotFoundError("kernel.nonexistent")

        result = pcp_mcp.errors.handle_pcp_error(err, "fetching")

        assert isinstance(result, ToolError)
        assert "Metric not found: kernel.nonexistent" in str(result)

    def test_handles_generic_exception(self) -> None:
        err = ValueError("Unexpected value")

        result = pcp_mcp.errors.handle_pcp_error(err, "processing data")

        assert isinstance(result, ToolError)
        assert "Error during processing data" in str(result)
        assert "Unexpected value" in str(result)

    @pytest.mark.parametrize(
        ("status_code", "expected_substring"),
        [
            (401, "pmproxy error (401)"),
            (403, "pmproxy error (403)"),
            (502, "pmproxy error (502)"),
            (503, "pmproxy error (503)"),
        ],
    )
    def test_handles_various_http_status_codes(
        self, status_code: int, expected_substring: str
    ) -> None:
        response = httpx.Response(status_code, text="Error response")
        request = httpx.Request("GET", "http://localhost/pmapi/fetch")
        err = httpx.HTTPStatusError("HTTP error", request=request, response=response)

        result = pcp_mcp.errors.handle_pcp_error(err, "operation")

        assert isinstance(result, ToolError)
        assert expected_substring in str(result)
