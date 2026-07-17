"""Tests for error handling and formatting."""

from __future__ import annotations

import pytest
from httpx import Response

from youfiliate_mcp.errors import format_error, handle_http_error, parse_drf_errors
import httpx


class TestParseDrfErrors:
    def test_detail_field(self) -> None:
        resp = Response(404, json={"detail": "Not found."})
        assert parse_drf_errors(resp) == "Not found."

    def test_field_errors(self) -> None:
        resp = Response(400, json={
            "slug": ["This slug is already taken."],
            "default_url": ["Enter a valid URL."],
        })
        result = parse_drf_errors(resp)
        assert "slug" in result
        assert "already taken" in result
        assert "default_url" in result

    def test_list_errors(self) -> None:
        resp = Response(400, json=["Error 1", "Error 2"])
        result = parse_drf_errors(resp)
        assert "Error 1" in result
        assert "Error 2" in result

    def test_non_json_response(self) -> None:
        resp = Response(500, text="Internal Server Error")
        result = parse_drf_errors(resp)
        assert "Internal Server Error" in result

    def test_empty_response(self) -> None:
        resp = Response(500, text="")
        result = parse_drf_errors(resp)
        assert result == "Unknown error"


class TestFormatError:
    def test_401(self) -> None:
        result = format_error(401)
        assert "Authentication failed" in result
        assert "API key" in result

    def test_403(self) -> None:
        result = format_error(403, "Insufficient plan.")
        assert "Permission denied" in result
        assert "Insufficient plan" in result

    def test_404(self) -> None:
        result = format_error(404)
        assert "not found" in result.lower()
        assert "youfiliate_list_smart_links" in result

    def test_429_with_retry(self) -> None:
        result = format_error(429, "", retry_after=30)
        assert "Rate limit" in result
        assert "30 seconds" in result

    def test_500(self) -> None:
        result = format_error(500)
        assert "unavailable" in result.lower()

    def test_unknown_4xx(self) -> None:
        result = format_error(418, "I'm a teapot")
        assert "418" in result
        assert "teapot" in result


class TestHandleHttpError:
    def test_404_error(self) -> None:
        request = httpx.Request("GET", "https://api.test/smart-links/bad/")
        response = Response(404, json={"detail": "Not found."}, request=request)
        exc = httpx.HTTPStatusError("Not found", request=request, response=response)
        result = handle_http_error(exc)
        assert "not found" in result.lower()

    def test_429_with_retry_after_header(self) -> None:
        request = httpx.Request("POST", "https://api.test/smart-links/1/check-health/")
        response = Response(
            429,
            json={"detail": "Too many requests"},
            headers={"Retry-After": "60"},
            request=request,
        )
        exc = httpx.HTTPStatusError("Too many", request=request, response=response)
        result = handle_http_error(exc)
        assert "60 seconds" in result
