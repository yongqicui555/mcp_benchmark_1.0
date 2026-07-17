"""End-to-end stdio protocol test.

Spawns `python -m minuet_mcp.server` as a subprocess, exchanges real MCP
JSON-RPC messages over stdin/stdout, and asserts the server speaks the
protocol correctly. This is machine-independent — any spec-compliant MCP
client (Claude Desktop, Codex, Cursor, etc.) drives the server the same way.
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
from collections.abc import Iterator
from typing import Any

import pytest


READ_TIMEOUT = 10.0  # seconds per line


def _read_line(proc: subprocess.Popen[bytes], timeout: float = READ_TIMEOUT) -> bytes:
    assert proc.stdout is not None
    ready, _, _ = select.select([proc.stdout], [], [], timeout)
    if not ready:
        stderr = b""
        if proc.stderr is not None:
            try:
                stderr = proc.stderr.read() or b""
            except Exception:
                pass
        raise TimeoutError(
            f"no stdout line within {timeout}s; stderr={stderr!r}"
        )
    line = proc.stdout.readline()
    if not line:
        raise EOFError("server closed stdout")
    return line


def _send(proc: subprocess.Popen[bytes], message: dict[str, Any]) -> None:
    assert proc.stdin is not None
    proc.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
    proc.stdin.flush()


def _recv(proc: subprocess.Popen[bytes]) -> dict[str, Any]:
    return json.loads(_read_line(proc).decode("utf-8"))


@pytest.fixture
def server() -> Iterator[subprocess.Popen[bytes]]:
    # Use the same interpreter running the tests — works in any CI or local env.
    # Point the client at a non-routable address so a rogue `tools/call` that
    # slipped past our checks can't accidentally hit production during the test.
    env = {**os.environ, "MINUET_API_URL": "http://127.0.0.1:1"}
    proc = subprocess.Popen(
        [sys.executable, "-m", "minuet_mcp.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        yield proc
    finally:
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


EXPECTED_TOOLS = {
    "search_agents",
    "get_agent",
    "get_agent_relationships",
    "get_hub_agents",
    "get_owner_ecosystems",
    "get_relationship_graph",
    "get_network_stats",
    "get_recent_relationships",
}


def test_initialize_and_list_tools(server: subprocess.Popen[bytes]) -> None:
    # 1. initialize handshake
    _send(
        server,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "minuet-mcp-test", "version": "0.0.0"},
            },
        },
    )
    init_response = _recv(server)
    assert init_response["jsonrpc"] == "2.0"
    assert init_response["id"] == 1
    assert "result" in init_response, f"initialize failed: {init_response}"
    result = init_response["result"]
    assert "protocolVersion" in result
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "minuet-mcp"
    assert "capabilities" in result
    assert "tools" in result["capabilities"], "server must advertise tools capability"

    # 2. initialized notification (no response expected)
    _send(
        server,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    )

    # 3. tools/list
    _send(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    list_response = _recv(server)
    assert list_response["id"] == 2
    assert "result" in list_response, f"tools/list failed: {list_response}"
    tools = list_response["result"]["tools"]
    assert isinstance(tools, list)
    names = {t["name"] for t in tools}
    assert EXPECTED_TOOLS <= names, f"missing tools: {EXPECTED_TOOLS - names}"

    # Every tool must have a non-empty description and a valid JSON Schema.
    for tool in tools:
        assert tool.get("description"), f"tool {tool['name']} missing description"
        schema = tool.get("inputSchema")
        assert isinstance(schema, dict), f"tool {tool['name']} missing inputSchema"
        assert schema.get("type") == "object", (
            f"tool {tool['name']} inputSchema.type must be 'object'"
        )


def test_unknown_method_returns_error(server: subprocess.Popen[bytes]) -> None:
    # Initialize first — servers may refuse other methods pre-handshake.
    _send(
        server,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "minuet-mcp-test", "version": "0.0.0"},
            },
        },
    )
    _recv(server)
    _send(server, {"jsonrpc": "2.0", "method": "notifications/initialized"})

    _send(server, {"jsonrpc": "2.0", "id": 99, "method": "does/not/exist"})
    response = _recv(server)
    assert response["id"] == 99
    assert "error" in response, f"expected error for unknown method, got: {response}"
    assert "code" in response["error"]
