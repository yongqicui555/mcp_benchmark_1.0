"""
Unit-Tests fuer den BAG ePL MCP Server — gemockt, kein Netzwerk (OPS-001).

Live-Tests gegen die echten BAG-Quellen siehe ``test_live.py``.
"""

from __future__ import annotations

import json
import socket

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError

from bag_epl_mcp.server import (
    ALLOWED_HOSTS,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    OGD_LICENSE,
    PROTOCOL_VERSION,
    SL_API_URL,
    GGSLAbfrageInput,
    MiGeLSucheInput,
    RechtskontextInput,
    ResponseFormat,
    ServerSettings,
    SLSucheInput,
    _assert_safe_url,
    _handle_error,
    _paginate,
    _sl_website_suche,
    epl_gesuchseingaenge,
    epl_ggsl_abfrage,
    epl_migel_suche,
    epl_rechtskontext,
    epl_server_info,
    epl_sl_suche,
    mcp,
)


def _fake_getaddrinfo(ip: str):
    """getaddrinfo-Stub, das immer ``ip`` zurueckgibt."""
    def _inner(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 443))]
    return _inner


def _text(result):
    """Menschenlesbarer content-Block einer Tool-Antwort (SDK-002 CallToolResult)."""
    return result.content[0].text


def _struct(result):
    """structuredContent einer Tool-Antwort (SDK-002)."""
    return result.structuredContent


# ─────────────────────────── Hilfsfunktionen ───────────────────────────────────

class TestPaginateHelper:
    def test_erste_seite(self):
        result = _paginate(total=50, limit=10, offset=0)
        assert result["hat_mehr"] is True

    def test_letzte_seite(self):
        assert _paginate(total=50, limit=10, offset=40)["hat_mehr"] is False

    def test_einzelnes_ergebnis(self):
        assert _paginate(total=1, limit=10, offset=0)["hat_mehr"] is False

    def test_leere_ergebnisse(self):
        assert _paginate(total=0, limit=10, offset=0)["hat_mehr"] is False


class TestHandleError:
    def test_timeout(self):
        msg = _handle_error(httpx.TimeoutException("t"), "Test")
        assert "Zeitueberschreitung" in msg and "Test" in msg

    def test_connect_error(self):
        assert "Verbindung fehlgeschlagen" in _handle_error(httpx.ConnectError("c"), "Test")

    def test_http_404(self):
        resp = httpx.Response(404, request=httpx.Request("GET", "https://example.com"))
        err = httpx.HTTPStatusError("nf", request=resp.request, response=resp)
        assert "404" in _handle_error(err)

    def test_http_429(self):
        resp = httpx.Response(429, request=httpx.Request("GET", "https://example.com"))
        err = httpx.HTTPStatusError("rl", request=resp.request, response=resp)
        assert "429" in _handle_error(err)

    def test_http_503(self):
        resp = httpx.Response(503, request=httpx.Request("GET", "https://example.com"))
        err = httpx.HTTPStatusError("u", request=resp.request, response=resp)
        assert "503" in _handle_error(err)

    def test_generic_error_maskiert_details(self):
        # OBS-002: rohe Message darf nicht an den LLM gelangen.
        err = ValueError("SELECT * FROM users; /secret/path leaked")
        msg = _handle_error(err, "Kontext")
        assert "ValueError" in msg and "Kontext" in msg
        assert "SELECT" not in msg and "/secret/path" not in msg


# ─────────────────────────── Input-Modelle (SEC-018) ──────────────────────────

class TestSLSucheInput:
    def test_gueltige_eingabe(self):
        inp = SLSucheInput(suchbegriff="Aspirin")
        assert inp.suchbegriff == "Aspirin" and inp.limit == DEFAULT_LIMIT

    def test_whitespace_stripping(self):
        assert SLSucheInput(suchbegriff="  Aspirin  ").suchbegriff == "Aspirin"

    def test_limit_bounds(self):
        assert SLSucheInput(suchbegriff="Test", limit=50).limit == 50

    def test_leerer_suchbegriff_rejected(self):
        with pytest.raises(Exception):
            SLSucheInput(suchbegriff="")

    def test_extra_fields_rejected(self):
        with pytest.raises(Exception):
            SLSucheInput(suchbegriff="Test", unbekannt="x")

    def test_strict_lehnt_falschen_typ_ab(self):
        # SEC-018: strict=True -> String fuer int-Feld wird abgelehnt.
        with pytest.raises(Exception):
            SLSucheInput(suchbegriff="Test", limit="50")

    def test_format_als_string_akzeptiert(self):
        # format ist bewusst strict=False, damit Clients "json"/"markdown" senden koennen.
        assert SLSucheInput(suchbegriff="x", format="json").format == ResponseFormat.JSON


class TestGGSLAbfrageInput:
    def test_gueltige_eingabe(self):
        assert GGSLAbfrageInput(geburtsgebrechen_nr="313").geburtsgebrechen_nr == "313"

    def test_format_json(self):
        assert GGSLAbfrageInput(geburtsgebrechen_nr="313", format=ResponseFormat.JSON).format == ResponseFormat.JSON


class TestMiGeLSucheInput:
    def test_gueltige_eingabe(self):
        assert MiGeLSucheInput(suchbegriff="Rollstuhl").suchbegriff == "Rollstuhl"

    def test_limit_clamp(self):
        assert MiGeLSucheInput(suchbegriff="Test", limit=MAX_LIMIT).limit == MAX_LIMIT


# ─────────────────────────── SL-Suche (Mocked) ────────────────────────────────

class TestSLSucheMocked:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_fallback(self):
        respx.get(f"{SL_API_URL}/search").mock(side_effect=httpx.ConnectError("no api"))
        result = await _sl_website_suche("Aspirin")
        assert "hinweis" in result and "Aspirin" in result["direkt_link"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_tool_markdown(self):
        respx.get(f"{SL_API_URL}/search").mock(side_effect=httpx.ConnectError("no api"))
        result = await epl_sl_suche(SLSucheInput(suchbegriff="Methylphenidat"))
        text = _text(result)
        assert "SL-Suche" in text and "Methylphenidat" in text
        # CH-004: Quelle/Lizenz im Markdown-Footer
        assert OGD_LICENSE in text and "sl.bag.admin.ch" in text
        # SDK-002: getyptes structuredContent immer mitgeliefert
        assert _struct(result)["match_type"] == "none"

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_tool_json_envelope(self):
        respx.get(f"{SL_API_URL}/search").mock(side_effect=httpx.ConnectError("no api"))
        result = await epl_sl_suche(SLSucheInput(suchbegriff="Aspirin", format=ResponseFormat.JSON))
        # SDK-002: content-Text ist JSON, structuredContent das getypte Envelope
        data = json.loads(_text(result))
        assert data == _struct(result)
        # ARCH-003 match_type + CH-004 provenance/license
        assert data["match_type"] == "none"
        assert data["count"] == 0 and data["results"] == []
        assert data["provenance"]["license"] == OGD_LICENSE
        assert data["source"].startswith("BAG")

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_api_success_match_exact(self):
        respx.get(f"{SL_API_URL}/search").mock(
            return_value=httpx.Response(200, json={"results": [{"name": "Aspirin Cardio"}]})
        )
        result = await _sl_website_suche("Aspirin")
        assert result["results"][0]["name"] == "Aspirin Cardio"
        # Tool klassifiziert echte Treffer als "exact"
        tool = await epl_sl_suche(SLSucheInput(suchbegriff="Aspirin", format=ResponseFormat.JSON))
        assert _struct(tool)["match_type"] == "exact"
        assert _struct(tool)["results"][0]["name"] == "Aspirin Cardio"


# ─────────────────────────── GGSL / MiGeL / Gesuche / Recht ────────────────────

class TestGGSL:
    @pytest.mark.asyncio
    async def test_ggsl_markdown(self):
        result = await epl_ggsl_abfrage(GGSLAbfrageInput(geburtsgebrechen_nr="313"))
        text = _text(result)
        assert "313" in text and "IVG" in text and OGD_LICENSE in text
        assert _struct(result)["geburtsgebrechen_nr"] == "313"

    @pytest.mark.asyncio
    async def test_ggsl_json(self):
        result = await epl_ggsl_abfrage(GGSLAbfrageInput(geburtsgebrechen_nr="404", format=ResponseFormat.JSON))
        data = json.loads(_text(result))
        assert data == _struct(result)
        assert data["geburtsgebrechen_nr"] == "404" and "rechtsgrundlage" in data
        assert data["provenance"]["license"] == OGD_LICENSE


class TestMiGeL:
    @pytest.mark.asyncio
    async def test_migel_markdown(self):
        result = await epl_migel_suche(MiGeLSucheInput(suchbegriff="Rollstuhl"))
        text = _text(result)
        assert "Rollstuhl" in text and "KLV" in text
        assert _struct(result)["suchbegriff"] == "Rollstuhl"

    @pytest.mark.asyncio
    async def test_migel_json_envelope(self):
        result = await epl_migel_suche(MiGeLSucheInput(suchbegriff="Hoergeraet", format=ResponseFormat.JSON))
        data = json.loads(_text(result))
        assert data == _struct(result)
        assert data["suchbegriff"] == "Hoergeraet"
        assert data["match_type"] == "none" and data["results"] == []
        assert data["provenance"]["source"] == "BAG MiGeL"


class TestGesuchseingaenge:
    @pytest.mark.asyncio
    async def test_gesuchseingaenge(self):
        result = await epl_gesuchseingaenge()
        assert "Gesuchseingaenge" in _text(result) and "sl.bag.admin.ch" in _text(result)
        assert _struct(result)["link"].startswith("https://sl.bag.admin.ch")


class TestRechtskontext:
    @pytest.mark.asyncio
    async def test_rechtskontext_markdown(self):
        result = await epl_rechtskontext(RechtskontextInput(frage="Welche Gesetze regeln die SL?"))
        text = _text(result)
        assert "KVG" in text and "KLV" in text and "WZW" in text
        assert len(_struct(result)["gesetze"]) >= 3

    @pytest.mark.asyncio
    async def test_rechtskontext_json(self):
        result = await epl_rechtskontext(RechtskontextInput(frage="Rechtsgrundlage SL", format=ResponseFormat.JSON))
        data = json.loads(_text(result))
        assert data == _struct(result)
        assert len(data["gesetze"]) >= 3 and "wzw_kriterien" in data
        assert "provenance" in data


class TestServerInfo:
    @pytest.mark.asyncio
    async def test_server_info(self):
        result = await epl_server_info()
        text = _text(result)
        assert "BAG ePL MCP Server" in text and "Phase 1" in text
        # ARCH-012: Protokoll-Version dokumentiert
        assert PROTOCOL_VERSION in text
        # SDK-002: getyptes structuredContent
        assert _struct(result)["protocol_version"] == PROTOCOL_VERSION
        assert "epl_sl_suche" in _struct(result)["tools"]


# ─────────────────────────── Egress-Guard (SEC-004/005/021) ───────────────────

class TestEgressGuard:
    def test_https_und_erlaubter_host_ok(self):
        _assert_safe_url("https://sl.bag.admin.ch/api/search")

    def test_http_schema_abgelehnt(self):
        with pytest.raises(ToolError):
            _assert_safe_url("http://sl.bag.admin.ch/api/search")

    def test_unerlaubter_host_abgelehnt(self):
        with pytest.raises(ToolError):
            _assert_safe_url("https://evil.example.com/steal")

    def test_private_ip_abgelehnt(self, monkeypatch):
        from bag_epl_mcp.server import _resolve_and_validate
        monkeypatch.setattr("bag_epl_mcp.server.socket.getaddrinfo", _fake_getaddrinfo("127.0.0.1"))
        with pytest.raises(ToolError):
            _resolve_and_validate("sl.bag.admin.ch", 443)

    def test_metadata_ip_abgelehnt(self, monkeypatch):
        from bag_epl_mcp.server import _resolve_and_validate
        monkeypatch.setattr("bag_epl_mcp.server.socket.getaddrinfo", _fake_getaddrinfo("169.254.169.254"))
        with pytest.raises(ToolError):
            _resolve_and_validate("www.bag.admin.ch", 443)

    def test_resolve_and_validate_gibt_pinned_ip(self, monkeypatch):
        from bag_epl_mcp.server import _resolve_and_validate
        monkeypatch.setattr("bag_epl_mcp.server.socket.getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
        assert _resolve_and_validate("sl.bag.admin.ch", 443) == "93.184.216.34"

    @pytest.mark.asyncio
    async def test_http_get_ruft_guard_auf(self):
        from bag_epl_mcp.server import _http_get
        with pytest.raises(ToolError):
            await _http_get("https://evil.example.com")

    def test_allowed_hosts_nur_admin_ch(self):
        assert all(h.endswith(".admin.ch") for h in ALLOWED_HOSTS)


# ─────────────────────────── DNS-Pinning (SEC-005) ────────────────────────────

class TestDnsPinning:
    """Die TCP-Verbindung wird auf die validierte IP gepinnt (SEC-005)."""

    @pytest.mark.asyncio
    async def test_pinned_backend_waehlt_validierte_ip(self, monkeypatch):
        from bag_epl_mcp.server import _PinnedNetworkBackend
        monkeypatch.setattr("bag_epl_mcp.server.socket.getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
        dialed = {}

        class _Inner:
            async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
                dialed["host"] = host
                dialed["port"] = port
                return object()

        backend = _PinnedNetworkBackend(_Inner())
        await backend.connect_tcp("sl.bag.admin.ch", 443)
        # Es wird die aufgeloeste IP gewaehlt, nicht der Hostname.
        assert dialed["host"] == "93.184.216.34" and dialed["port"] == 443

    @pytest.mark.asyncio
    async def test_pinned_backend_blockt_private_ip(self, monkeypatch):
        from bag_epl_mcp.server import _PinnedNetworkBackend
        monkeypatch.setattr("bag_epl_mcp.server.socket.getaddrinfo", _fake_getaddrinfo("10.0.0.5"))

        class _Inner:
            async def connect_tcp(self, *a, **k):  # pragma: no cover - darf nicht erreicht werden
                raise AssertionError("connect_tcp duerfte nicht aufgerufen werden")

        with pytest.raises(ToolError):
            await _PinnedNetworkBackend(_Inner()).connect_tcp("sl.bag.admin.ch", 443)

    def test_new_http_client_ist_gepinnt(self):
        from bag_epl_mcp.server import _new_http_client, _PinnedNetworkBackend
        client = _new_http_client()
        try:
            backend = client._transport._pool._network_backend
            assert isinstance(backend, _PinnedNetworkBackend)
        finally:
            pass


# ─────────────────────────── Settings & Transport ─────────────────────────────

class TestSettings:
    def test_defaults_sicher(self):
        s = ServerSettings()
        assert s.transport == "stdio" and s.host == "127.0.0.1"
        # OBS-006: Tracing standardmaessig aktiv (stiller No-op ohne [otel]-Extra).
        assert s.otel_enabled is True

    def test_otel_abschaltbar(self, monkeypatch):
        monkeypatch.setenv("MCP_OTEL_ENABLED", "false")
        assert ServerSettings().otel_enabled is False

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_PORT", "9000")
        s = ServerSettings()
        assert s.transport == "streamable-http" and s.host == "0.0.0.0" and s.port == 9000


# ─────────────────────────── Tool-Annotations (ARCH-009) ───────────────────────

class TestToolAnnotations:
    @pytest.mark.asyncio
    async def test_alle_tools_read_only(self):
        tools = await mcp.list_tools()
        assert tools
        for t in tools:
            assert t.annotations is not None and t.annotations.readOnlyHint is True

    @pytest.mark.asyncio
    async def test_sl_suche_open_world(self):
        tools = {t.name: t for t in await mcp.list_tools()}
        assert tools["epl_sl_suche"].annotations.openWorldHint is True
        assert tools["epl_server_info"].annotations.openWorldHint is False

    @pytest.mark.asyncio
    async def test_use_case_tag_in_beschreibungen(self):
        # ARCH-002: Use-Case-Tag in >=80% der Tools.
        tools = await mcp.list_tools()
        mit_tag = sum(1 for t in tools if t.description and "<use_case>" in t.description)
        assert mit_tag / len(tools) >= 0.8


# ─────────────────────────── Lifespan / HTTP-App ──────────────────────────────

class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_oeffnet_und_schliesst_client(self):
        import bag_epl_mcp.server as srv
        assert srv._http_client is None
        async with srv._lifespan(srv.mcp) as ctx:
            assert isinstance(srv._http_client, httpx.AsyncClient)
            assert ctx["http_client"] is srv._http_client
        assert srv._http_client is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_get_nutzt_pool_client(self):
        import bag_epl_mcp.server as srv
        respx.get(f"{SL_API_URL}/search").mock(return_value=httpx.Response(200, json={"results": []}))
        async with srv._lifespan(srv.mcp):
            pooled = srv._http_client
            await srv._http_get(f"{SL_API_URL}/search")
            assert srv._http_client is pooled


class TestHttpApp:
    @pytest.fixture(scope="class")
    def client(self):
        from starlette.testclient import TestClient

        from bag_epl_mcp.server import _build_http_app
        with TestClient(_build_http_app()) as c:
            yield c

    def test_healthz_endpoint(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200 and resp.text == "ok"

    def test_cors_preflight_exposes_session_id(self, client):
        resp = client.options(
            "/mcp",
            headers={
                "Origin": "https://claude.ai",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "mcp-session-id",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "https://claude.ai"
        assert "mcp-session-id" in resp.headers.get("access-control-allow-headers", "").lower()


# ─────────────────────────── Observability (SDK-003 / OBS-003) ─────────────────

class TestObservability:
    """Per-Call-Logging-Kontext + Context-Injection."""

    def test_bind_call_context_setzt_felder(self):
        import structlog

        from bag_epl_mcp.server import _bind_call_context
        _bind_call_context(None, "epl_sl_suche")
        ctxvars = structlog.contextvars.get_contextvars()
        assert ctxvars["tool"] == "epl_sl_suche"
        assert "correlation_id" in ctxvars
        structlog.contextvars.clear_contextvars()

    @pytest.mark.asyncio
    async def test_tools_akzeptieren_ctx_injection(self):
        # FastMCP injiziert Context; defensiver Zugriff -> kein Crash.
        from mcp.types import CallToolResult
        res = await mcp.call_tool("epl_server_info", {})
        if isinstance(res, CallToolResult):          # SDK-002: content + structuredContent
            text = res.content[0].text
            assert res.structuredContent["protocol_version"] == PROTOCOL_VERSION
        elif isinstance(res, tuple):
            text = res[0][0].text
        else:
            text = res[0].text
        assert "BAG ePL MCP Server" in text

    def test_alle_tools_haben_ctx_param(self):
        import inspect

        from bag_epl_mcp import server as srv
        for name in ("epl_sl_suche", "epl_ggsl_abfrage", "epl_migel_suche",
                     "epl_gesuchseingaenge", "epl_rechtskontext", "epl_server_info"):
            fn = getattr(srv, name).fn if hasattr(getattr(srv, name), "fn") else getattr(srv, name)
            assert "ctx" in inspect.signature(fn).parameters, f"{name}: kein ctx-Parameter"
