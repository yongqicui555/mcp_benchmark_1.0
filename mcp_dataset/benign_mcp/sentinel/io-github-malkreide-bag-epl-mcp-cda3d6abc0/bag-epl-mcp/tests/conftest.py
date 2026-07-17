"""Gemeinsame Test-Fixtures."""

from __future__ import annotations

import socket

import pytest


def _fake_getaddrinfo(ip: str):
    """getaddrinfo-Stub, das immer ``ip`` zurueckgibt."""
    def _inner(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 443))]
    return _inner


@pytest.fixture(autouse=True)
def _stub_dns(request, monkeypatch):
    """
    Haelt Unit-Tests hermetisch: der Egress-Guard loest DNS sonst echt auf.
    Live-Tests (Marker ``live``) nutzen weiterhin echtes DNS.
    """
    if request.node.get_closest_marker("live"):
        return
    monkeypatch.setattr(
        "bag_epl_mcp.server.socket.getaddrinfo", _fake_getaddrinfo("93.184.216.34")
    )
