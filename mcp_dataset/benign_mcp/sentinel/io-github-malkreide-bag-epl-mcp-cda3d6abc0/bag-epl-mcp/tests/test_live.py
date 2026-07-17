"""
Live-Tests gegen die echten BAG-/Fedlex-Quellen (OPS-001).

Opt-in — nur mit ``pytest -m live`` ausgefuehrt; in der CI standardmaessig
ausgeschlossen (``-m "not live"``). Dienen der Schema-Drift-Erkennung und
verifizieren, dass die Egress-Allow-List die echten Hosts zulaesst.
"""

from __future__ import annotations

import pytest

from bag_epl_mcp.server import (
    GGSLAbfrageInput,
    MiGeLSucheInput,
    RechtskontextInput,
    SLSucheInput,
    _sl_website_suche,
    epl_gesuchseingaenge,
    epl_ggsl_abfrage,
    epl_migel_suche,
    epl_rechtskontext,
    epl_server_info,
    epl_sl_suche,
)

pytestmark = [pytest.mark.live, pytest.mark.asyncio]


async def test_live_sl_suche():
    # Echter Netzwerk-/DNS-Pfad: Egress-Guard muss sl.bag.admin.ch zulassen.
    result = await _sl_website_suche("Aspirin")
    assert "direkt_link" in result or "results" in result


async def test_live_dns_pinning_tls_ok():
    # SEC-005: echter Request ueber den gepinnten Transport -> TLS muss gegen den
    # Hostnamen valide bleiben (kein SSL-Fehler), obwohl auf die IP verbunden wird.
    from bag_epl_mcp.server import _new_http_client
    async with _new_http_client() as client:
        resp = await client.get("https://www.fedlex.admin.ch/")
        assert resp.status_code is not None


async def test_live_sl_suche_tool():
    result = await epl_sl_suche(SLSucheInput(suchbegriff="Aspirin"))
    assert "SL-Suche" in result


async def test_live_ggsl():
    result = await epl_ggsl_abfrage(GGSLAbfrageInput(geburtsgebrechen_nr="313"))
    assert "313" in result


async def test_live_migel():
    result = await epl_migel_suche(MiGeLSucheInput(suchbegriff="Rollstuhl"))
    assert "Rollstuhl" in result


async def test_live_gesuchseingaenge():
    result = await epl_gesuchseingaenge()
    assert "Gesuchseingaenge" in result


async def test_live_rechtskontext():
    result = await epl_rechtskontext(RechtskontextInput(frage="Rechtsgrundlage SL?"))
    assert "KVG" in result


async def test_live_server_info():
    result = await epl_server_info()
    assert "BAG ePL MCP Server" in result
