"""Unit-Tests fuer bakom-mcp — laufen offline, ohne Live-APIs.

Komplementiert die `live`-markierten Integrationstests (siehe conftest.py).
Diese Suite verifiziert:
- Pydantic-Input-Validation und Field-Constraints
- Error-Masking-Verhalten von _handle_api_error (OBS-002)
- Lifespan-managed shared httpx-Client (SDK-001) via Mock-Patch
- Edge-Cases: 404 / 429 / Timeout / ConnectError / leere Resultate

Diese Tests sind NICHT mit @pytest.mark.live versehen — sie laufen
in CI bei jedem PR.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import ValidationError

from bakom_mcp.server import (
    ALLOWED_EGRESS_HOSTS,
    AntennaSearchInput,
    AppContext,
    BroadbandCoverageInput,
    BroadbandSpeed,
    CoordinateInput,
    EgressNotAllowedError,
    MediaType,
    MobilGenerations,
    MultiLocationInput,
    ResponseFormat,
    RTVSearchInput,
    TelekomStatInput,
    _handle_api_error,
    _raise_api_error,
    bakom_breitbandatlas_datensaetze,
    bakom_broadband_coverage,
    bakom_multi_standort_konnektivitaet,
    bakom_rtv_suche,
    bakom_sendeanlagen_suche,
    lifespan,
    mcp,
)


# ---------------------------------------------------------------------------
# Helper: Build a Context-like object that exposes the lifespan AppContext
# ---------------------------------------------------------------------------
def _ctx_with(client: httpx.AsyncClient | AsyncMock) -> MagicMock:
    """Erzeuge ein Mock-Context-Objekt, wie FastMCP es an Tools reicht."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = AppContext(http=client)
    return ctx


# ---------------------------------------------------------------------------
# Pydantic Input-Validation
# ---------------------------------------------------------------------------
class TestInputValidation:
    """Inputs sind die Tool-Boundary — Pydantic-Validation muss greifen (SEC-018)."""

    def test_coordinate_within_swiss_bounds_ok(self) -> None:
        params = CoordinateInput(latitude=47.3769, longitude=8.5417)
        assert params.latitude == 47.3769
        assert params.response_format == ResponseFormat.MARKDOWN

    @pytest.mark.parametrize("lat", [45.7, 48.0, -1.0, 100.0])
    def test_coordinate_out_of_swiss_bounds_rejected(self, lat: float) -> None:
        with pytest.raises(ValidationError):
            CoordinateInput(latitude=lat, longitude=8.5)

    @pytest.mark.parametrize("lon", [5.8, 10.7, -1.0, 100.0])
    def test_longitude_out_of_swiss_bounds_rejected(self, lon: float) -> None:
        with pytest.raises(ValidationError):
            CoordinateInput(latitude=47.0, longitude=lon)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CoordinateInput(latitude=47.0, longitude=8.5, malicious="payload")  # type: ignore[call-arg]

    def test_antenna_radius_clamped_to_5km(self) -> None:
        with pytest.raises(ValidationError):
            AntennaSearchInput(latitude=47.0, longitude=8.5, radius_m=10_000)

    def test_antenna_radius_minimum(self) -> None:
        with pytest.raises(ValidationError):
            AntennaSearchInput(latitude=47.0, longitude=8.5, radius_m=50)

    def test_rtv_kanton_uppercased(self) -> None:
        params = RTVSearchInput(kanton="zh")
        assert params.kanton == "ZH"

    def test_rtv_kanton_max_length_2(self) -> None:
        with pytest.raises(ValidationError):
            RTVSearchInput(kanton="ZHX")

    def test_rtv_query_max_length(self) -> None:
        with pytest.raises(ValidationError):
            RTVSearchInput(query="X" * 101)

    def test_rtv_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            RTVSearchInput(limit=0)
        with pytest.raises(ValidationError):
            RTVSearchInput(limit=51)

    def test_multi_location_max_20(self) -> None:
        too_many = [{"name": f"S{i}", "latitude": 47.0, "longitude": 8.5} for i in range(21)]
        with pytest.raises(ValidationError):
            MultiLocationInput(locations=too_many)

    def test_multi_location_min_1(self) -> None:
        with pytest.raises(ValidationError):
            MultiLocationInput(locations=[])

    def test_telekom_thema_max_length(self) -> None:
        with pytest.raises(ValidationError):
            TelekomStatInput(thema="X" * 51)


# ---------------------------------------------------------------------------
# OBS-002: Error-Masking
# ---------------------------------------------------------------------------
class TestErrorMasking:
    """_handle_api_error darf keine sensitiven Exception-Details ans LLM leaken."""

    def test_404_returns_generic_message(self) -> None:
        request = httpx.Request("GET", "https://api3.geo.admin.ch/secret-internal-path")
        response = httpx.Response(status_code=404, request=request)
        err = httpx.HTTPStatusError("404 Not Found", request=request, response=response)
        result = _handle_api_error(err)
        assert "Ressource nicht gefunden" in result
        assert "secret-internal-path" not in result

    def test_429_rate_limit_message(self) -> None:
        request = httpx.Request("GET", "https://example/x")
        response = httpx.Response(status_code=429, request=request)
        err = httpx.HTTPStatusError("429", request=request, response=response)
        assert "Rate-Limit" in _handle_api_error(err)

    def test_500_server_error_message(self) -> None:
        request = httpx.Request("GET", "https://example/x")
        response = httpx.Response(status_code=503, request=request)
        err = httpx.HTTPStatusError("503", request=request, response=response)
        result = _handle_api_error(err)
        assert "503" in result
        assert "API-Server" in result

    def test_timeout_returns_generic_message(self) -> None:
        result = _handle_api_error(httpx.TimeoutException("timed out reading /secret/path"))
        assert "Zeitüberschreitung" in result
        assert "secret" not in result.lower()

    def test_connect_error_returns_generic_message(self) -> None:
        result = _handle_api_error(httpx.ConnectError("could not connect to 10.0.0.5:5432"))
        assert "Keine Verbindung" in result
        assert "10.0.0.5" not in result

    def test_unknown_exception_returns_generic_message(self) -> None:
        secret_payload = "/etc/passwd contains root:x:0:0:..."
        result = _handle_api_error(ValueError(secret_payload))
        assert "/etc/passwd" not in result
        assert "ValueError" not in result
        assert "interner fehler" in result.lower()


# ---------------------------------------------------------------------------
# OBS-001: _raise_api_error -> ToolError (Execution-Error Trennung)
# ---------------------------------------------------------------------------
class TestRaiseApiError:
    """Tools nutzen _raise_api_error fuer Execution-Errors → isError=True wire."""

    def test_raises_tool_error_for_timeout(self) -> None:
        with pytest.raises(ToolError) as exc_info:
            _raise_api_error(httpx.TimeoutException("read timeout on /secret"))
        msg = str(exc_info.value)
        assert "Zeitüberschreitung" in msg
        assert "/secret" not in msg

    def test_raises_tool_error_for_connect_error(self) -> None:
        with pytest.raises(ToolError) as exc_info:
            _raise_api_error(httpx.ConnectError("connect to 192.168.1.1 failed"))
        msg = str(exc_info.value)
        assert "Keine Verbindung" in msg
        assert "192.168.1.1" not in msg

    def test_raises_tool_error_for_404(self) -> None:
        request = httpx.Request("GET", "https://api3.geo.admin.ch/secret")
        response = httpx.Response(status_code=404, request=request)
        err = httpx.HTTPStatusError("404", request=request, response=response)
        with pytest.raises(ToolError) as exc_info:
            _raise_api_error(err)
        assert "Ressource nicht gefunden" in str(exc_info.value)

    def test_raises_tool_error_for_egress_block(self) -> None:
        evil = httpx.Request("GET", "https://attacker.example/x")
        err = EgressNotAllowedError("blocked", request=evil)
        with pytest.raises(ToolError) as exc_info:
            _raise_api_error(err)
        msg = str(exc_info.value)
        assert "Egress-Allowlist" in msg
        # Original-Host darf nicht in der ToolError-Message landen
        assert "attacker.example" not in msg

    def test_raises_tool_error_for_unknown_exception(self) -> None:
        with pytest.raises(ToolError) as exc_info:
            _raise_api_error(ValueError("/etc/passwd contains root:x"))
        msg = str(exc_info.value)
        assert "/etc/passwd" not in msg
        assert "ValueError" not in msg
        assert "interner fehler" in msg.lower()

    def test_chain_preserves_original_exception(self) -> None:
        """`from e` erhaelt __cause__ fuer Server-seitige Diagnose."""
        original = httpx.TimeoutException("internal trace")
        try:
            _raise_api_error(original)
        except ToolError as te:
            assert te.__cause__ is original


# ---------------------------------------------------------------------------
# SDK-001: Lifespan + shared httpx client
# ---------------------------------------------------------------------------
class TestLifespan:
    """Verifiziert, dass lifespan einen einzelnen Client verwaltet."""

    @pytest.mark.asyncio
    async def test_lifespan_yields_app_context(self) -> None:
        async with lifespan(mcp) as app_ctx:
            assert isinstance(app_ctx, AppContext)
            assert isinstance(app_ctx.http, httpx.AsyncClient)
            assert not app_ctx.http.is_closed

    @pytest.mark.asyncio
    async def test_lifespan_closes_client_on_exit(self) -> None:
        async with lifespan(mcp) as app_ctx:
            client = app_ctx.http
        assert client.is_closed

    @pytest.mark.asyncio
    async def test_lifespan_user_agent_set(self) -> None:
        async with lifespan(mcp) as app_ctx:
            ua = app_ctx.http.headers.get("User-Agent", "")
        assert "bakom-mcp" in ua


# ---------------------------------------------------------------------------
# Tool-Call mit gemocktem httpx-Client
# ---------------------------------------------------------------------------
class TestToolCallsWithMockedHttpx:
    """End-to-end Tool-Calls ohne Live-API."""

    @pytest.mark.asyncio
    async def test_broadband_coverage_handles_404(self) -> None:
        """Tool raise't ToolError bei 404 — isError=True auf der Wire (OBS-001)."""
        client = AsyncMock(spec=httpx.AsyncClient)
        request = httpx.Request("GET", "https://wms.geo.admin.ch/?LAYERS=ch.bakom.downlink100")
        response = httpx.Response(status_code=404, request=request)
        client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("404", request=request, response=response)
        )

        params = BroadbandCoverageInput(
            latitude=47.3769, longitude=8.5417, min_speed_mbps=BroadbandSpeed.S100
        )
        with pytest.raises(ToolError) as exc_info:
            await bakom_broadband_coverage(params, _ctx_with(client))
        msg = str(exc_info.value)
        assert "Ressource nicht gefunden" in msg
        # Kein Layer/URL-Leak (OBS-002)
        assert "ch.bakom.downlink100" not in msg
        assert "wms.geo.admin.ch" not in msg

    @pytest.mark.asyncio
    async def test_broadband_coverage_handles_timeout(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(side_effect=httpx.TimeoutException("read timeout on /etc/passwd"))

        params = BroadbandCoverageInput(
            latitude=47.3769, longitude=8.5417, min_speed_mbps=BroadbandSpeed.S100
        )
        with pytest.raises(ToolError) as exc_info:
            await bakom_broadband_coverage(params, _ctx_with(client))
        msg = str(exc_info.value)
        assert "Zeitüberschreitung" in msg
        assert "/etc/passwd" not in msg

    @pytest.mark.asyncio
    async def test_broadband_coverage_handles_connect_error(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(side_effect=httpx.ConnectError("network unreachable to 10.0.0.5"))

        params = BroadbandCoverageInput(
            latitude=47.3769, longitude=8.5417, min_speed_mbps=BroadbandSpeed.S100
        )
        with pytest.raises(ToolError) as exc_info:
            await bakom_broadband_coverage(params, _ctx_with(client))
        msg = str(exc_info.value)
        assert "Keine Verbindung" in msg
        assert "10.0.0.5" not in msg


# ---------------------------------------------------------------------------
# Statisches Tool ohne httpx
# ---------------------------------------------------------------------------
class TestStaticTool:
    """bakom_breitbandatlas_datensaetze nutzt keine API, sollte deterministisch sein."""

    @pytest.mark.asyncio
    async def test_breitbandatlas_returns_dataset_list(self) -> None:
        params = TelekomStatInput()
        result = await bakom_breitbandatlas_datensaetze(params)
        assert isinstance(result, str)
        assert len(result) > 100
        # Alle dokumentierten Layer muessen erwaehnt sein
        assert "5g" in result.lower()
        assert "fttb" in result.lower() or "glasfaser" in result.lower()

    @pytest.mark.asyncio
    async def test_markdown_output_includes_cc_by_attribution(self) -> None:
        """CH-004: Markdown-Tool-Outputs enthalten CC BY 4.0 Attribution-Footer."""
        params = TelekomStatInput()
        result = await bakom_breitbandatlas_datensaetze(params)
        assert "CC BY 4.0" in result
        assert "BAKOM" in result
        assert "creativecommons.org" in result

    @pytest.mark.asyncio
    async def test_breitbandatlas_json_format(self) -> None:
        import json

        params = TelekomStatInput(response_format=ResponseFormat.JSON)
        result = await bakom_breitbandatlas_datensaetze(params)
        # JSON-Mode muss valides JSON liefern
        parsed = json.loads(result)
        assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# SEC-021: Egress-Allow-List
# ---------------------------------------------------------------------------
class TestEgressAllowlist:
    """Outbound-Calls duerfen nur an gelistete Hosts gehen."""

    def test_allowlist_includes_known_data_sources(self) -> None:
        """Verifiziert, dass alle bestehenden Datenquellen in der Liste sind."""
        for host in (
            "api3.geo.admin.ch",
            "wms.geo.admin.ch",
            "geodesy.geo.admin.ch",
            "ckan.opendata.swiss",
            "rtvdb.ofcomnet.ch",
            "www.bakom.admin.ch",
        ):
            assert host in ALLOWED_EGRESS_HOSTS, f"missing: {host}"

    def test_allowlist_is_frozen(self) -> None:
        """Eine frozenset garantiert Immutabilitaet zur Laufzeit."""
        assert isinstance(ALLOWED_EGRESS_HOSTS, frozenset)

    @pytest.mark.asyncio
    async def test_allowed_host_passes_through(self) -> None:
        """Ein erlaubter Host wird vom Hook nicht blockiert."""
        from bakom_mcp.server import _enforce_egress_allowlist

        allowed = httpx.Request("GET", "https://api3.geo.admin.ch/some/path")
        # Should not raise
        await _enforce_egress_allowlist(allowed)

    @pytest.mark.asyncio
    async def test_disallowed_host_raises(self) -> None:
        """Ein nicht-gelisteter Host wirft EgressNotAllowedError."""
        from bakom_mcp.server import _enforce_egress_allowlist

        evil = httpx.Request("GET", "https://evil.example.com/exfil")
        with pytest.raises(EgressNotAllowedError) as exc_info:
            await _enforce_egress_allowlist(evil)
        # Fehlermeldung enthaelt Host (fuers Log/Debug), aber EgressNotAllowedError
        # ist eine httpx.RequestError-Subklasse — wird vom Tool-Code-Catch eingefangen
        assert "evil.example.com" in str(exc_info.value)
        assert isinstance(exc_info.value, httpx.RequestError)

    @pytest.mark.asyncio
    async def test_lifespan_client_blocks_disallowed_url(self) -> None:
        """End-to-end: der Lifespan-Client blockiert disallowed URLs auf Request-Ebene."""
        async with lifespan(mcp) as app_ctx:
            with pytest.raises(EgressNotAllowedError):
                await app_ctx.http.get("https://attacker.example/data", timeout=2.0)


# ---------------------------------------------------------------------------
# OBS-003: Tool-Call Lifecycle-Logs (Decorator)
# ---------------------------------------------------------------------------
class TestToolCallLogging:
    """_log_tool_call Decorator emittiert start/ok/failed Log-Records."""

    @pytest.mark.asyncio
    async def test_log_records_on_success(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        caplog.set_level(logging.INFO, logger="bakom_mcp")
        params = TelekomStatInput()
        await bakom_breitbandatlas_datensaetze(params)

        msgs = [r.msg for r in caplog.records if hasattr(r, "tool")]
        assert "tool_call_start" in msgs
        assert "tool_call_ok" in msgs
        # tool_call_ok carries duration_ms
        ok = next(r for r in caplog.records if r.msg == "tool_call_ok")
        assert hasattr(ok, "tool")
        assert ok.tool == "bakom_breitbandatlas_datensaetze"
        assert hasattr(ok, "duration_ms")
        assert ok.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_log_records_on_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(side_effect=httpx.TimeoutException("test"))

        caplog.set_level(logging.INFO, logger="bakom_mcp")
        params = BroadbandCoverageInput(latitude=47.0, longitude=8.5)
        with pytest.raises(ToolError):
            await bakom_broadband_coverage(params, _ctx_with(client))

        # tool_call_failed should be present with error_class
        failed = [r for r in caplog.records if r.msg == "tool_call_failed"]
        assert len(failed) == 1
        assert failed[0].tool == "bakom_broadband_coverage"
        assert failed[0].error_class == "ToolError"
        assert failed[0].duration_ms >= 0


# ---------------------------------------------------------------------------
# SDK-003: ctx.report_progress + ctx.info in multi_standort
# ---------------------------------------------------------------------------
class TestProgressReports:
    """bakom_multi_standort_konnektivitaet ruft ctx.report_progress + ctx.info."""

    @pytest.mark.asyncio
    async def test_progress_called_per_location(self) -> None:
        # Mock client that immediately fails each lookup so we don't hit live APIs
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(side_effect=httpx.ConnectError("offline"))

        ctx = MagicMock()
        ctx.request_context.lifespan_context = AppContext(http=client)
        ctx.info = AsyncMock()
        ctx.report_progress = AsyncMock()

        params = MultiLocationInput(
            locations=[
                {"name": "A", "latitude": 47.0, "longitude": 8.5},
                {"name": "B", "latitude": 47.1, "longitude": 8.6},
                {"name": "C", "latitude": 47.2, "longitude": 8.7},
            ]
        )
        # Tool catches per-location exceptions itself → no raise
        result = await bakom_multi_standort_konnektivitaet(params, ctx)

        # 3 per-location progress + 1 final = 4 calls
        assert ctx.report_progress.call_count == 4
        # Final progress is total/total
        last_call = ctx.report_progress.call_args_list[-1]
        assert last_call.kwargs["progress"] == 3
        assert last_call.kwargs["total"] == 3
        # ctx.info called once at the start
        assert ctx.info.call_count == 1
        # Result still serializable
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# ARCH-008: @mcp.prompt-Templates
# ---------------------------------------------------------------------------
class TestPromptTemplates:
    """Drei Prompt-Templates fuer haeufige BAKOM-Use-Cases registriert + rendern."""

    def test_three_prompts_registered(self) -> None:
        names = set(mcp._prompt_manager._prompts.keys())
        assert {
            "schulhaus_konnektivitaet",
            "rtv_kanton_uebersicht",
            "standort_konnektivitaet_vergleich",
        } <= names

    @pytest.mark.asyncio
    async def test_schulhaus_prompt_renders_with_defaults(self) -> None:
        res = await mcp._prompt_manager.render_prompt("schulhaus_konnektivitaet", {})
        text = res[0].content.text
        # Defaults von Zürich/Kreis 7 müssen drin sein
        assert "Zürich" in text
        assert "Kreis 7" in text
        # Tool-Hinweis (LLM weiss welches Tool)
        assert "bakom_multi_standort_konnektivitaet" in text
        # CC BY 4.0 Attribution-Erinnerung
        assert "CC BY 4.0" in text

    @pytest.mark.asyncio
    async def test_schulhaus_prompt_with_custom_args(self) -> None:
        res = await mcp._prompt_manager.render_prompt(
            "schulhaus_konnektivitaet",
            {"gemeinde": "Bern", "schulkreis": "Kreis Mitte"},
        )
        text = res[0].content.text
        assert "Bern" in text
        assert "Kreis Mitte" in text

    @pytest.mark.asyncio
    async def test_rtv_kanton_prompt_uppercases_canton(self) -> None:
        res = await mcp._prompt_manager.render_prompt(
            "rtv_kanton_uebersicht",
            {"kanton": "ge"},
        )
        text = res[0].content.text
        # Prompt soll uppercased GE im Tool-Aufruf erwähnen
        assert "GE" in text
        assert "bakom_rtv_suche" in text

    @pytest.mark.asyncio
    async def test_vergleich_prompt_mentions_max_20(self) -> None:
        res = await mcp._prompt_manager.render_prompt("standort_konnektivitaet_vergleich", {})
        text = res[0].content.text
        # Wichtige Limit-Doku im Prompt
        assert "20" in text
        assert "bakom_multi_standort_konnektivitaet" in text


# ---------------------------------------------------------------------------
# ARCH-003: «Not-Found»-Heuristiken bei leeren Resultaten
# ---------------------------------------------------------------------------
def _ckan_empty_response() -> MagicMock:
    """Mock-httpx-Response with empty CKAN search results."""
    resp = MagicMock(spec=httpx.Response)
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"result": {"results": []}})
    return resp


def _identify_empty_response() -> MagicMock:
    """Mock geo.admin.ch identify response with empty results."""
    resp = MagicMock(spec=httpx.Response)
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"results": []})
    return resp


class TestNotFoundHeuristics:
    """ARCH-003: Tools liefern bei leeren Resultaten konkrete Empfehlungen."""

    @pytest.mark.asyncio
    async def test_sendeanlagen_empty_suggests_larger_radius(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=_identify_empty_response())

        params = AntennaSearchInput(latitude=47.0, longitude=8.5, radius_m=200)
        result = await bakom_sendeanlagen_suche(params, _ctx_with(client))
        # Hinweis soll konkreten Radius vorschlagen (200 -> 400)
        assert "400 m" in result
        assert "Empfehlung" in result

    @pytest.mark.asyncio
    async def test_sendeanlagen_empty_at_max_radius_says_remote(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=_identify_empty_response())

        params = AntennaSearchInput(latitude=47.0, longitude=8.5, radius_m=5000)
        result = await bakom_sendeanlagen_suche(params, _ctx_with(client))
        # Bei 5000 m max kein doppelt-Vorschlag, sondern "abgelegen"-Hinweis
        assert "abgelegen" in result.lower()

    @pytest.mark.asyncio
    async def test_rtv_empty_suggests_dropping_kanton_filter(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        # Primary RTV API returns empty broadcasters list.
        primary_resp = MagicMock(spec=httpx.Response)
        primary_resp.raise_for_status = MagicMock()
        primary_resp.json = MagicMock(return_value={"results": []})
        client.get = AsyncMock(return_value=primary_resp)

        params = RTVSearchInput(query="Tele Inexistent", kanton="ZH", media_type=MediaType.TV)
        result = await bakom_rtv_suche(params, _ctx_with(client))
        # Hinweis schlägt Kanton-Lockerung und Medientyp-Lockerung vor
        assert "Kanton-Filter" in result or "kanton=ZH" in result
        assert "Empfehlung" in result

    @pytest.mark.asyncio
    async def test_rtv_empty_with_no_filters_still_helpful(self) -> None:
        client = AsyncMock(spec=httpx.AsyncClient)
        empty_resp = MagicMock(spec=httpx.Response)
        empty_resp.raise_for_status = MagicMock()
        empty_resp.json = MagicMock(return_value={"results": []})
        client.get = AsyncMock(return_value=empty_resp)

        params = RTVSearchInput()  # alle defaults
        result = await bakom_rtv_suche(params, _ctx_with(client))
        # Auch ohne Filter-Vorschläge soll Hinweis-Text auftauchen
        assert "Hinweis" in result or "Empfehlung" in result


# ---------------------------------------------------------------------------
# Enum / Konstanten-Sanity
# ---------------------------------------------------------------------------
class TestEnumValues:
    def test_broadband_speed_values(self) -> None:
        assert BroadbandSpeed.S100.value == "100"
        assert BroadbandSpeed.S1000.value == "1000"

    def test_mobile_generations_present(self) -> None:
        assert MobilGenerations.G5.value == "5G"
        assert MobilGenerations.G4.value == "4G"

    def test_media_type_includes_alle(self) -> None:
        assert MediaType.ALLE.value == "alle"
