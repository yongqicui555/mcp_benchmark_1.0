"""Unit tests for LobbywatchClient (respx-mocked HTTP)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from lobbywatch_mcp.client import LobbywatchClient, _is_forbidden_address, _ssrf_guard
from lobbywatch_mcp.config import API_BASE, DUMP_URL


@respx.mock
async def test_dump_download_and_parse(tmp_path: Path, dump_zip_bytes: bytes) -> None:
    respx.get(DUMP_URL).mock(return_value=httpx.Response(200, content=dump_zip_bytes))

    client = LobbywatchClient(cache_dir=tmp_path)
    await client.ensure_dump_loaded()

    records = await client.all_parlamentarier()
    assert len(records) == 3
    assert records[0]["anzeige_name"] == "Mustermann, Anna"
    await client.aclose()


async def test_find_by_id(primed_client: LobbywatchClient) -> None:
    r = await primed_client.find_parlamentarier(2)
    assert r is not None
    assert r["anzeige_name"] == "Beispiel, Beat"


async def test_find_by_name_exact(primed_client: LobbywatchClient) -> None:
    r = await primed_client.find_parlamentarier("Mustermann, Anna")
    assert r is not None
    assert r["id"] == 1


async def test_find_by_name_fuzzy(primed_client: LobbywatchClient) -> None:
    r = await primed_client.find_parlamentarier("Mustermann")
    assert r is not None
    assert r["id"] == 1


async def test_find_returns_none_on_miss(primed_client: LobbywatchClient) -> None:
    r = await primed_client.find_parlamentarier("Nonexistent Person")
    assert r is None


@respx.mock
async def test_fetch_lobbygruppe_by_id(tmp_path: Path) -> None:
    respx.get(f"{API_BASE}/table/interessengruppe/aggregated/id/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "data": {"id": 1, "anzeige_name": "Beispielgruppe", "organisationen": []},
            },
        )
    )

    client = LobbywatchClient(cache_dir=tmp_path)
    result = await client.fetch_lobbygruppe(1)
    assert result is not None
    assert result["anzeige_name"] == "Beispielgruppe"
    await client.aclose()


@pytest.mark.parametrize(
    "ip,forbidden",
    [
        ("169.254.169.254", True),  # AWS / GCP metadata
        ("127.0.0.1", True),
        ("10.0.0.5", True),
        ("192.168.1.1", True),
        ("172.16.0.1", True),
        ("::1", True),
        ("8.8.8.8", False),  # public DNS
        ("1.1.1.1", False),
    ],
)
def test_ssrf_guard_classifies_addresses(ip: str, forbidden: bool) -> None:
    """SEC-005: forbidden CIDRs must be flagged."""
    assert _is_forbidden_address(ip) is forbidden


async def test_ssrf_guard_blocks_metadata_ip() -> None:
    """SEC-005: an httpx request to a literal forbidden IP raises before connecting."""
    request = httpx.Request("GET", "http://169.254.169.254/latest/meta-data/")
    with pytest.raises(RuntimeError, match="forbidden address"):
        await _ssrf_guard(request)


@respx.mock
async def test_dump_download_retries_on_503(
    tmp_path: Path, dump_zip_bytes: bytes, monkeypatch
) -> None:
    """A transient 503 must be retried; the second attempt succeeds."""
    # Short-circuit the backoff sleep so the test stays fast.
    import lobbywatch_mcp.client as client_mod

    async def _instant(_seconds: float) -> None:
        return None

    monkeypatch.setattr(client_mod.asyncio, "sleep", _instant)

    respx.get(DUMP_URL).mock(
        side_effect=[
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, content=dump_zip_bytes),
        ]
    )

    client = LobbywatchClient(cache_dir=tmp_path)
    await client.ensure_dump_loaded()
    records = await client.all_parlamentarier()
    assert len(records) == 3
    await client.aclose()
