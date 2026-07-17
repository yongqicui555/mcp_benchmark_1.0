"""Live integration tests against the real Lobbywatch dataIF and dump.

These tests are marked ``live`` and excluded from CI (``pytest -m 'not live'``).
Run locally with ``pytest -m live`` to verify that upstream endpoints are still
behaving as documented.
"""

from __future__ import annotations

import pytest

from lobbywatch_mcp.client import LobbywatchClient

pytestmark = pytest.mark.live


async def test_weekly_dump_downloads_and_parses(tmp_path):
    client = LobbywatchClient(cache_dir=tmp_path)
    try:
        await client.ensure_dump_loaded()
        records = await client.all_parlamentarier()
        # Homepage as of writing claimed 246; accept any value >= 200.
        assert len(records) >= 200, f"Dump unexpectedly small: {len(records)} records"
        # Spot-check structure
        sample = records[0]
        assert "anzeige_name" in sample
        assert "interessenbindungen" in sample
    finally:
        await client.aclose()


async def test_lobbygruppe_live_fetch():
    client = LobbywatchClient()
    try:
        # ID 1 exists per the documented example.
        data = await client.fetch_lobbygruppe(1)
        assert data is not None
        assert "anzeige_name" in data
    finally:
        await client.aclose()
