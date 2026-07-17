"""Gemeinsame pytest-Fixtures.

Stellt Test-Isolation für den prozessweiten httpx-Client her: pytest-asyncio
gibt jedem Test eine eigene Event-Loop. Ohne Reset würde der in einer früheren,
bereits geschlossenen Loop erzeugte Client wiederverwendet und beim Schliessen
seiner Verbindungen mit ``RuntimeError: Event loop is closed`` fehlschlagen.
"""

import pytest

from swiss_cultural_heritage_mcp import server


@pytest.fixture(autouse=True)
async def _reset_http_client():
    """Schliesst den geteilten httpx-Client nach jedem Test in dessen Loop."""
    yield
    client, server._http_client = server._http_client, None
    if client is not None and not client.is_closed:
        await client.aclose()
