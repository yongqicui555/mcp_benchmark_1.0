from __future__ import annotations

from asuswrt_mcp.server import _call


async def failing() -> dict:
    raise RuntimeError("boom")


async def test_call_converts_errors() -> None:
    response = await _call("test", failing())

    assert response["ok"] is False
    assert response["error"]["code"] == "unexpected_error"

