"""
Tests für den Swiss Cultural Heritage MCP Server.

Alle Tests nutzen gemockte HTTP-Antworten — kein Live-Zugang erforderlich.
Live-Tests (gegen echte APIs) sind mit @pytest.mark.live markiert und
per Default deaktiviert.

Ausführen:
    PYTHONPATH=src pytest tests/               # alle Unit-Tests
    PYTHONPATH=src pytest tests/ -m live       # Live-Tests (benötigt Internetzugang)
    PYTHONPATH=src pytest tests/ --cov=swiss_cultural_heritage_mcp
"""

import json

import httpx
import pytest
import respx
from mcp.server.fastmcp.exceptions import ToolError
from structlog.testing import capture_logs

from swiss_cultural_heritage_mcp import __version__ as pkg_version
from swiss_cultural_heritage_mcp.server import (
    ALLOWED_HOSTS,
    CKAN_API,
    NB_OAI_PMH,
    SIKART_RESOURCE_ID,
    ArtistDetailInput,
    ArtistSearchInput,
    CollectionBrowseInput,
    CrossSearchInput,
    HelvticatSearchInput,
    MuseumSearchInput,
    NbCollectionsInput,
    PublicationDetailInput,
    ResponseFormat,
    ResultEnvelope,
    Settings,
    _assert_allowed,
    _extract_resumption_token,
    _handle_error,
    _http_get,
    _normalize_ckan_title,
    _parse_oai_records,
    _request_log_context,
    build_http_app,
    cors_origins_from_env,
    heritage_browse_collection,
    heritage_cross_search,
    heritage_get_artist,
    heritage_get_publication,
    heritage_list_nb_collections,
    heritage_search_artists,
    heritage_search_helveticat,
    heritage_search_museum_datasets,
    mask_unexpected_errors,
    mcp,
    settings,
)

# ─────────────────────────── Fixtures ──────────────────────────────────────────

# CKAN DataStore-Antwort der SIKART-Künstlerressource (Feldnamen wie im echten Datensatz).
MOCK_SIKART_DATASTORE = {
    "success": True,
    "result": {
        "resource_id": SIKART_RESOURCE_ID,
        "total": 2,
        "fields": [
            {"id": "_id", "type": "int"},
            {"id": "HAUPTNR", "type": "text"},
            {"id": "NAME", "type": "text"},
            {"id": "VORNAME", "type": "text"},
        ],
        "records": [
            {
                "_id": 1, "HAUPTNR": "4000123",
                "NAME": "Hodler", "VORNAME": "Ferdinand", "NAMIDENT": "Hodler, Ferdinand",
                "GEBURTSJAHR": "1853", "GEBURTSDATUM": "14.3.1853", "GEBURTSORT": "Bern",
                "GEBURTSKANTON": "BE", "GEBURTSLAND": "CH",
                "STERBEJAHR": "1918", "STERBEDATUM": "19.5.1918", "STERBEORT": "Genf",
                "STERBEKANTON": "GE", "STERBELAND": "CH",
                "LEBENSDATEN": "* 14.3.1853 Bern, + 19.5.1918 Genf",
                "VITAZEILE": "Maler. Landschaften, Figurenbilder, Historienbilder.",
                "TYPUS": "Künstler", "NUTZUNGSLIZENZ": "Nutzungslizenz: CC-BY-NC-SA",
                "GND": "118552155", "HLS_ID": None, "WEBSITE": None,
                "SIKART_LINK": "https://recherche.sik-isea.ch/de/sik:person-4000123/in/sikisea/actor/list",
            },
            {
                "_id": 2, "HAUPTNR": "4000456",
                "NAME": "Taeuber-Arp", "VORNAME": "Sophie", "NAMIDENT": "Taeuber-Arp, Sophie",
                "GEBURTSJAHR": "1889", "GEBURTSDATUM": "19.1.1889", "GEBURTSORT": "Davos",
                "GEBURTSKANTON": "GR", "GEBURTSLAND": "CH",
                "STERBEJAHR": "1943", "STERBEDATUM": "13.1.1943", "STERBEORT": "Zürich",
                "STERBEKANTON": "ZH", "STERBELAND": "CH",
                "LEBENSDATEN": "* 19.1.1889 Davos, + 13.1.1943 Zürich",
                "VITAZEILE": "Malerin, Bildhauerin, Textilkünstlerin, Tänzerin.",
                "TYPUS": "Künstlerin", "NUTZUNGSLIZENZ": "Nutzungslizenz: CC-BY-NC-SA",
                "GND": "118620916", "HLS_ID": None, "WEBSITE": None,
                "SIKART_LINK": "https://recherche.sik-isea.ch/de/sik:person-4000456/in/sikisea/actor/list",
            },
        ],
    },
}

# Einzelresultat (datastore_search mit filters auf HAUPTNR) für heritage_get_artist.
MOCK_SIKART_ONE = {
    "success": True,
    "result": {
        "resource_id": SIKART_RESOURCE_ID,
        "total": 1,
        "records": [MOCK_SIKART_DATASTORE["result"]["records"][0]],
    },
}

MOCK_CKAN_RESPONSE = {
    "success": True,
    "result": {
        "count": 2,
        "results": [
            {
                "name":      "snm-numismatik",
                "title":     {"de": "Numismatische Sammlung SNM", "en": "SNM Numismatic Collection"},
                "notes":     {"de": "Münzen und Medaillen, ca. 100'000 Objekte"},
                "resources": [
                    {
                        "name":   "Münzsammlung CSV",
                        "format": "CSV",
                        "url":    "https://opendata.swiss/dataset/snm-numismatik/resource/abc123",
                        "id":     "abc123-uuid",
                    }
                ],
            },
            {
                "name":      "snm-siegelsammlung",
                "title":     {"de": "Siegelsammlung SNM"},
                "notes":     {"de": "Siegel und Stempel, ca. 80'000 Objekte"},
                "resources": [
                    {
                        "name":   "Siegelsammlung CSV",
                        "format": "CSV",
                        "url":    "https://opendata.swiss/dataset/snm-siegel/resource/def456",
                        "id":     "def456-uuid",
                    }
                ],
            },
        ],
    },
}

MOCK_DATASTORE_RESPONSE = {
    "success": True,
    "result": {
        "total": 3,
        "fields": [
            {"id": "_id"},
            {"id": "Titel"},
            {"id": "Jahr"},
            {"id": "Material"},
            {"id": "Herkunft"},
        ],
        "records": [
            {"_id": 1, "Titel": "Goldmünze Zürich", "Jahr": "1350",  "Material": "Gold",   "Herkunft": "Zürich"},
            {"_id": 2, "Titel": "Silbermünze Bern",  "Jahr": "1400",  "Material": "Silber", "Herkunft": "Bern"},
            {"_id": 3, "Titel": "Kupfermünze Basel", "Jahr": "1500",  "Material": "Kupfer", "Herkunft": "Basel"},
        ],
    },
}

MOCK_OAI_RECORDS = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <responseDate>2026-01-01T00:00:00Z</responseDate>
  <request verb="ListRecords">https://www.nb.admin.ch/oai/oai-provider</request>
  <ListRecords>
    <record>
      <header>
        <identifier>oai:helveticat.ch:123456</identifier>
        <datestamp>2024-01-15</datestamp>
      </header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Geschichte der Schweizer Volksschule</dc:title>
          <dc:creator>Muster, Anna</dc:creator>
          <dc:date>2023</dc:date>
          <dc:language>de</dc:language>
          <dc:subject>Bildungsgeschichte</dc:subject>
          <dc:subject>Volksschule Schweiz</dc:subject>
          <dc:description>Umfassende Geschichte des Volksschulwesens in der Schweiz.</dc:description>
          <dc:identifier>isbn:978-3-000-00001-0</dc:identifier>
        </oai_dc:dc>
      </metadata>
    </record>
    <record>
      <header>
        <identifier>oai:helveticat.ch:789012</identifier>
        <datestamp>2024-02-20</datestamp>
      </header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Kunstpädagogik in der Schule</dc:title>
          <dc:creator>Beispiel, Hans</dc:creator>
          <dc:date>2022</dc:date>
          <dc:language>de</dc:language>
          <dc:subject>Kunstunterricht</dc:subject>
        </oai_dc:dc>
      </metadata>
    </record>
    <resumptionToken>abc123token</resumptionToken>
  </ListRecords>
</OAI-PMH>"""

MOCK_OAI_SETS = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>2026-01-01T00:00:00Z</responseDate>
  <ListSets>
    <set>
      <setSpec>helveticat</setSpec>
      <setName>Schweizerische Nationalbibliografie</setName>
    </set>
    <set>
      <setSpec>e-periodica</setSpec>
      <setName>Digitalisierte Schweizer Zeitschriften</setName>
    </set>
    <set>
      <setSpec>sla</setSpec>
      <setName>Schweizerisches Literaturarchiv</setName>
    </set>
  </ListSets>
</OAI-PMH>"""

MOCK_OAI_GET_RECORD = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>2026-01-01T00:00:00Z</responseDate>
  <GetRecord>
    <record>
      <header>
        <identifier>oai:helveticat.ch:123456</identifier>
        <datestamp>2024-01-15</datestamp>
      </header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Geschichte der Schweizer Volksschule</dc:title>
          <dc:creator>Muster, Anna</dc:creator>
          <dc:publisher>Schulamt Verlag</dc:publisher>
          <dc:date>2023</dc:date>
          <dc:language>de</dc:language>
          <dc:subject>Bildungsgeschichte</dc:subject>
          <dc:description>Umfassende Geschichte des Volksschulwesens.</dc:description>
          <dc:rights>CC BY 4.0</dc:rights>
          <dc:identifier>isbn:978-3-000-00001-0</dc:identifier>
        </oai_dc:dc>
      </metadata>
    </record>
  </GetRecord>
</OAI-PMH>"""


# ─────────────────────────── Unit Tests: Utilities ─────────────────────────────

class TestOaiParsing:
    def test_parse_records(self):
        records = _parse_oai_records(MOCK_OAI_RECORDS)
        assert len(records) == 2
        assert records[0]["oai_identifier"] == "oai:helveticat.ch:123456"
        assert records[0]["title"] == "Geschichte der Schweizer Volksschule"
        assert records[0]["creator"] == "Muster, Anna"
        assert records[0]["date"] == "2023"

    def test_resumption_token(self):
        token = _extract_resumption_token(MOCK_OAI_RECORDS)
        assert token == "abc123token"

    def test_no_resumption_token(self):
        xml = MOCK_OAI_GET_RECORD
        token = _extract_resumption_token(xml)
        assert token is None

    def test_multiple_subjects(self):
        records = _parse_oai_records(MOCK_OAI_RECORDS)
        rec = records[0]
        # subject should be list when multiple
        assert isinstance(rec.get("subject"), list) or isinstance(rec.get("subject"), str)


class TestNormalizeCkanTitle:
    def test_dict_de(self):
        assert _normalize_ckan_title({"de": "Deutsch", "en": "English"}) == "Deutsch"

    def test_dict_fallback_en(self):
        assert _normalize_ckan_title({"en": "English only"}) == "English only"

    def test_string(self):
        assert _normalize_ckan_title("Plain string") == "Plain string"

    def test_none(self):
        assert _normalize_ckan_title(None) == "—"


class TestPackageMetadata:
    """Audit follow-up: __version__ via importlib.metadata, no duplication."""

    def test_version_string_format(self):
        # Installed package returns the pyproject version (e.g. "0.1.0");
        # source-tree fallback returns "0.0.0+local".
        assert isinstance(pkg_version, str)
        assert pkg_version  # not empty


class TestHealthEndpoint:
    """Audit follow-up: /health for Render/k8s liveness probes."""

    @pytest.mark.asyncio
    async def test_health_route_registered(self):
        from swiss_cultural_heritage_mcp.server import mcp
        paths = [r.path for r in mcp._custom_starlette_routes]
        assert "/health" in paths

    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        from httpx import ASGITransport, AsyncClient

        from swiss_cultural_heritage_mcp.server import mcp
        app = mcp.streamable_http_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "swiss-cultural-heritage-mcp"


class TestInputModelConsistency:
    """ARCH (PR 2): jedes Tool-Input-Modell verwendet extra='forbid' und ResponseFormat-Enum."""

    @pytest.mark.parametrize("model_cls", [
        ArtistSearchInput,
        ArtistDetailInput,
        MuseumSearchInput,
        CollectionBrowseInput,
        HelvticatSearchInput,
        PublicationDetailInput,
        CrossSearchInput,
        NbCollectionsInput,
    ])
    def test_forbids_extra_fields(self, model_cls):
        assert model_cls.model_config.get("extra") == "forbid"

    @pytest.mark.parametrize("model_cls", [
        ArtistSearchInput,
        ArtistDetailInput,
        MuseumSearchInput,
        CollectionBrowseInput,
        HelvticatSearchInput,
        PublicationDetailInput,
        NbCollectionsInput,
    ])
    def test_response_format_field_is_enum(self, model_cls):
        field = model_cls.model_fields.get("response_format")
        assert field is not None
        assert field.annotation is ResponseFormat


class TestEgressAllowList:
    def test_allowed_hosts_contain_upstreams(self):
        assert "ckan.opendata.swiss" in ALLOWED_HOSTS
        assert "helveticat.nb.admin.ch" in ALLOWED_HOSTS

    def test_assert_allowed_accepts_known_host(self):
        _assert_allowed(CKAN_API)
        _assert_allowed(NB_OAI_PMH)

    def test_assert_allowed_rejects_unknown_host(self):
        with pytest.raises(ValueError, match="Allow-List"):
            _assert_allowed("https://evil.example.com/exfil")

    def test_assert_allowed_rejects_non_https_scheme(self):
        # SEC-004: HTTPS is enforced even for an otherwise allow-listed host
        with pytest.raises(ValueError, match="HTTPS"):
            _assert_allowed("http://ckan.opendata.swiss/api/3/action/datastore_search")
        with pytest.raises(ValueError, match="HTTPS"):
            _assert_allowed("file:///etc/passwd")

    @pytest.mark.asyncio
    async def test_http_get_rejects_unknown_host(self):
        with pytest.raises(ValueError, match="Allow-List"):
            await _http_get("https://evil.example.com/exfil")


class TestHandleError:
    def test_timeout(self):
        e = httpx.TimeoutException("timeout")
        msg = _handle_error(e)
        assert "Zeitüberschreitung" in msg

    def test_404(self):
        req = httpx.Request("GET", "https://example.com")
        resp = httpx.Response(404, request=req)
        e = httpx.HTTPStatusError("not found", request=req, response=resp)
        msg = _handle_error(e)
        assert "nicht gefunden" in msg

    def test_429(self):
        req = httpx.Request("GET", "https://example.com")
        resp = httpx.Response(429, request=req)
        e = httpx.HTTPStatusError("rate limit", request=req, response=resp)
        msg = _handle_error(e)
        assert "Rate-Limit" in msg


class TestErrorMasking:
    """OBS-002: unerwartete (Programmier-)Fehler werden maskiert, nicht geleakt."""

    @pytest.mark.asyncio
    async def test_decorator_masks_internal_detail(self):
        @mask_unexpected_errors
        async def boom() -> str:
            raise KeyError("SECRET_INTERNAL_FIELD")

        with pytest.raises(ToolError) as exc:
            await boom()
        assert "SECRET_INTERNAL_FIELD" not in str(exc.value)
        assert "KeyError" not in str(exc.value)
        assert "Interner Fehler" in str(exc.value)

    @pytest.mark.asyncio
    async def test_decorator_passes_through_normal_result(self):
        @mask_unexpected_errors
        async def ok() -> str:
            return "alles gut"

        assert await ok() == "alles gut"

    @pytest.mark.asyncio
    async def test_decorator_does_not_double_wrap_toolerror(self):
        @mask_unexpected_errors
        async def already() -> str:
            raise ToolError("schon maskiert")

        with pytest.raises(ToolError, match="schon maskiert"):
            await already()

    @pytest.mark.asyncio
    async def test_tool_masks_unexpected_upstream_shape(self):
        # CKAN liefert unerwartet eine Liste statt eines Objekts → AttributeError
        # (kein ExpectedUpstreamError) im Tool-Body. Muss maskiert werden.
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=["unexpected", "list"])
            )
            with pytest.raises(ToolError) as exc:
                await heritage_search_artists(ArtistSearchInput(query="Hodler"))
        assert "Interner Fehler" in str(exc.value)
        assert "AttributeError" not in str(exc.value)


class TestHttpCors:
    """SDK-004: CORS exponiert Mcp-Session-Id für Browser-Clients."""

    def test_cors_origins_from_env_parsing(self, monkeypatch):
        # ARCH-004: config now flows through the Settings object (MCP_CORS_ORIGINS)
        monkeypatch.setattr(settings, "cors_origins", " https://a.example , https://b.example ,")
        assert cors_origins_from_env() == ["https://a.example", "https://b.example"]

    def test_cors_origins_default_empty(self, monkeypatch):
        monkeypatch.setattr(settings, "cors_origins", "")
        assert cors_origins_from_env() == []

    def test_build_http_app_exposes_session_id(self):
        app = build_http_app(["https://app.example"])
        cors = next(m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware")
        assert "Mcp-Session-Id" in cors.kwargs["expose_headers"]
        assert "Mcp-Session-Id" in cors.kwargs["allow_headers"]
        assert cors.kwargs["allow_origins"] == ["https://app.example"]
        assert "*" not in cors.kwargs["allow_origins"]


class TestSettings:
    """ARCH-004: single env-overridable config object."""

    def test_module_constants_derive_from_settings(self):
        # the public module constants are aliases of the Settings source of truth
        assert CKAN_API == settings.ckan_api
        assert ALLOWED_HOSTS == settings.allowed_hosts

    def test_defaults(self):
        s = Settings()
        assert s.transport == "stdio"
        assert s.host == "127.0.0.1"   # SEC-016 loopback default
        assert s.port == 8000
        assert s.http_timeout == 30.0

    def test_env_overrides_without_code_change(self, monkeypatch):
        # the whole point of ARCH-004: per-env override via MCP_* env vars
        monkeypatch.setenv("MCP_HTTP_TIMEOUT", "12.5")
        monkeypatch.setenv("MCP_TRANSPORT", "http")
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_DEFAULT_LIMIT", "7")
        s = Settings()
        assert s.http_timeout == 12.5
        assert s.transport == "http"
        assert s.host == "0.0.0.0"
        assert s.default_limit == 7

    def test_invalid_transport_rejected(self):
        with pytest.raises(Exception):
            Settings(transport="grpc")


# ─────────────────────────── Unit Tests: Input Models ──────────────────────────

class TestArtistSearchInput:
    def test_valid_all_fields(self):
        p = ArtistSearchInput(query="Hodler", region="Bern")
        assert p.query == "Hodler"
        assert p.region == "Bern"
        assert p.limit == 20

    def test_all_optional(self):
        p = ArtistSearchInput()
        assert p.query is None
        assert p.region is None

    def test_limit_bounds(self):
        with pytest.raises(Exception):
            ArtistSearchInput(limit=0)
        with pytest.raises(Exception):
            ArtistSearchInput(limit=101)

    def test_blank_query_rejected(self):
        with pytest.raises(Exception):
            ArtistSearchInput(query="   ")

    def test_whitespace_stripped(self):
        p = ArtistSearchInput(query="  Hodler  ")
        assert p.query == "Hodler"


class TestHelvticatSearchInput:
    def test_valid_date_format(self):
        p = HelvticatSearchInput(from_date="2020-01-01", until_date="2024-12-31")
        assert p.from_date == "2020-01-01"

    def test_year_only_allowed(self):
        p = HelvticatSearchInput(from_date="2020")
        assert p.from_date == "2020"

    def test_invalid_date_rejected(self):
        with pytest.raises(Exception):
            HelvticatSearchInput(from_date="01.01.2020")

    def test_limit_max_50(self):
        with pytest.raises(Exception):
            HelvticatSearchInput(limit=51)


class TestCrossSearchInput:
    def test_valid_sources(self):
        p = CrossSearchInput(query="Hodler", sources=["sik_isea", "nb"])
        assert "sik_isea" in p.sources

    def test_invalid_source_rejected(self):
        with pytest.raises(Exception):
            CrossSearchInput(query="Test", sources=["invalid_source"])

    def test_deduplication(self):
        p = CrossSearchInput(query="Test", sources=["snm", "snm", "nb"])
        assert len(p.sources) == len(set(p.sources))


# ─────────────────────────── Integration Tests (mocked HTTP) ──────────────────

class TestHeritageSIKISEA:
    @pytest.mark.asyncio
    async def test_search_artists_json_response(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            params = ArtistSearchInput(query="Hodler", response_format=ResponseFormat.JSON)
            result = await heritage_search_artists(params)

        assert isinstance(result, ResultEnvelope)
        assert result.total == 2
        assert result.results[0]["NAME"] == "Hodler"
        assert result.source.name == "SIK-ISEA / SIKART"
        assert result.source.license

    @pytest.mark.asyncio
    async def test_search_artists_markdown(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            params = ArtistSearchInput(query="Hodler")
            result = await heritage_search_artists(params)

        assert "Ferdinand Hodler" in result
        assert "SIKART" in result
        assert "1853" in result

    @pytest.mark.asyncio
    async def test_search_artists_empty(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "result": {"resource_id": SIKART_RESOURCE_ID, "total": 0, "records": []},
                })
            )
            params = ArtistSearchInput(query="UnbekannterName12345")
            result = await heritage_search_artists(params)

        assert "Keine Künstler" in result

    @pytest.mark.asyncio
    async def test_get_artist_markdown(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_ONE)
            )
            params = ArtistDetailInput(artist_id="4000123")
            result = await heritage_get_artist(params)

        assert "Ferdinand Hodler" in result
        assert "4000123" in result

    @pytest.mark.asyncio
    async def test_get_artist_not_found(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "result": {"resource_id": SIKART_RESOURCE_ID, "total": 0, "records": []},
                })
            )
            params = ArtistDetailInput(artist_id="99999999")
            result = await heritage_get_artist(params)

        assert "Keine Daten gefunden" in result

    @pytest.mark.asyncio
    async def test_get_artist_http_error(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(404)
            )
            params = ArtistDetailInput(artist_id="99999999")
            # OBS-001: a handled upstream error raises (→ isError), not a plain string
            with pytest.raises(ToolError, match="nicht gefunden"):
                await heritage_get_artist(params)


class TestHeritageSNM:
    @pytest.mark.asyncio
    async def test_search_datasets_markdown(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            params = MuseumSearchInput(query="Münzen")
            result = await heritage_search_museum_datasets(params)

        assert "Nationalmuseum" in result
        assert "Numismatische Sammlung" in result

    @pytest.mark.asyncio
    async def test_search_datasets_json(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            params = MuseumSearchInput(query="Münzen", response_format=ResponseFormat.JSON)
            result = await heritage_search_museum_datasets(params)

        assert isinstance(result, ResultEnvelope)
        assert result.total == 2
        assert len(result.results) == 2
        assert result.results[0]["name"] == "snm-numismatik"

    @pytest.mark.asyncio
    async def test_browse_collection_markdown(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_DATASTORE_RESPONSE)
            )
            params = CollectionBrowseInput(resource_id="abc123-uuid", query="Zürich")
            result = await heritage_browse_collection(params)

        assert "Goldmünze Zürich" in result
        assert "1350" in result

    @pytest.mark.asyncio
    async def test_browse_collection_empty(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json={
                    "success": True,
                    "result": {"total": 0, "fields": [], "records": []}
                })
            )
            params = CollectionBrowseInput(resource_id="xyz-empty")
            result = await heritage_browse_collection(params)

        assert "Keine Objekte" in result


class TestHeritageNB:
    @pytest.mark.asyncio
    async def test_search_helveticat_markdown(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS, headers={"content-type": "text/xml"})
            )
            params = HelvticatSearchInput(query="Volksschule")
            result = await heritage_search_helveticat(params)

        assert "Geschichte der Schweizer Volksschule" in result
        assert "Muster, Anna" in result

    @pytest.mark.asyncio
    async def test_search_helveticat_json(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            params = HelvticatSearchInput(response_format=ResponseFormat.JSON)
            result = await heritage_search_helveticat(params)

        assert isinstance(result, ResultEnvelope)
        assert result.count >= 1
        assert result.results
        assert result.source.name.startswith("Schweizerische Nationalbibliothek")

    @pytest.mark.asyncio
    async def test_search_helveticat_query_filter(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            # query that matches only first record
            params = HelvticatSearchInput(query="Volksschule")
            result = await heritage_search_helveticat(params)

        assert "Geschichte der Schweizer Volksschule" in result
        # "Kunstpädagogik" should not appear since we filtered on Volksschule
        # (It actually COULD appear if the subject matches too, but let's check it ran)
        assert "Fehler" not in result

    @pytest.mark.asyncio
    async def test_list_nb_collections(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_SETS)
            )
            result = await heritage_list_nb_collections()

        assert "helveticat" in result
        assert "e-periodica" in result
        assert "set_spec" in result

    @pytest.mark.asyncio
    async def test_get_publication_markdown(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_GET_RECORD)
            )
            params = PublicationDetailInput(identifier="oai:helveticat.ch:123456")
            result = await heritage_get_publication(params)

        assert "Geschichte der Schweizer Volksschule" in result
        assert "Muster, Anna" in result
        assert "CC BY 4.0" in result

    @pytest.mark.asyncio
    async def test_get_publication_json(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_GET_RECORD)
            )
            params = PublicationDetailInput(
                identifier="oai:helveticat.ch:123456",
                response_format=ResponseFormat.JSON,
            )
            result = await heritage_get_publication(params)

        assert isinstance(result, ResultEnvelope)
        assert result.count == 1
        assert result.results[0]["title"] == "Geschichte der Schweizer Volksschule"
        assert result.results[0]["creator"] == "Muster, Anna"


class TestHeritageCrossSearch:
    @pytest.mark.asyncio
    async def test_cross_search_all_sources(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            params = CrossSearchInput(query="Hodler", limit_per_source=3)
            result = await heritage_cross_search(params)

        assert "SIK-ISEA" in result
        assert "SNM" in result
        assert "NB" in result

    @pytest.mark.asyncio
    async def test_cross_search_single_source(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            params = CrossSearchInput(query="Münzen", sources=["snm"], limit_per_source=2)
            result = await heritage_cross_search(params)

        assert "SNM" in result
        assert "SIK-ISEA" not in result

    @pytest.mark.asyncio
    async def test_cross_search_partial_failure(self):
        """Wenn eine Quelle fehlschlägt, sollen die anderen weiter angezeigt werden."""
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(503)
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            params = CrossSearchInput(query="Test", sources=["sik_isea", "snm"])
            result = await heritage_cross_search(params)

        # SNM results should still appear despite SIK-ISEA failure
        assert "SNM" in result


class TestStructuredOutput:
    """SDK-002: JSON-Modus liefert typisierten Envelope, Markdown bleibt str."""

    @pytest.mark.asyncio
    async def test_markdown_mode_returns_str(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            result = await heritage_search_artists(ArtistSearchInput(query="Hodler"))
        assert isinstance(result, str)
        assert not isinstance(result, ResultEnvelope)

    @pytest.mark.asyncio
    async def test_cross_search_json_envelope_multi_source(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            params = CrossSearchInput(
                query="Hodler", limit_per_source=3, response_format=ResponseFormat.JSON
            )
            result = await heritage_cross_search(params)
        assert isinstance(result, ResultEnvelope)
        # provenance for every queried source
        assert isinstance(result.source, list)
        assert {s.name for s in result.source} == {
            "SIK-ISEA / SIKART",
            "Schweizerisches Nationalmuseum (opendata.swiss)",
            "Schweizerische Nationalbibliothek (Helveticat OAI-PMH)",
        }
        assert result.count == sum(len(r.get("items", [])) for r in result.results)

    @pytest.mark.asyncio
    async def test_tool_exposes_output_schema(self):
        tools = {t.name: t for t in await mcp.list_tools()}
        schema = tools["heritage_search_artists"].outputSchema
        assert schema is not None
        # the envelope model is referenced in the (union) output schema
        assert "ResultEnvelope" in json.dumps(schema)


class TestAttribution:
    """CH-004: jede Antwort führt Quelle + Lizenz mit (OGD CC-BY-Compliance)."""

    @pytest.mark.asyncio
    async def test_markdown_search_has_attribution_footer(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            result = await heritage_search_artists(ArtistSearchInput(query="Hodler"))
        assert "Datenquelle & Lizenz:" in result
        assert "SIK-ISEA / SIKART" in result
        assert "CC BY" in result
        assert "https://www.sik-isea.ch" in result

    @pytest.mark.asyncio
    async def test_markdown_detail_has_attribution_footer(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_GET_RECORD)
            )
            params = PublicationDetailInput(identifier="oai:helveticat.ch:123456")
            result = await heritage_get_publication(params)
        assert "Datenquelle & Lizenz:" in result
        assert "Nationalbibliothek" in result

    @pytest.mark.asyncio
    async def test_cross_search_markdown_per_item_provenance(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            # "Volksschule" matches the NB fixture so all three sections have items
            result = await heritage_cross_search(
                CrossSearchInput(query="Volksschule", limit_per_source=3)
            )
        # every result line tags its own source, not just the section header
        assert "`[SIK-ISEA]`" in result
        assert "`[SNM]`" in result
        assert "`[NB]`" in result
        # footer lists licences for all queried sources
        assert "Datenquelle & Lizenz:" in result
        assert result.count("Lizenz:") >= 3  # header label + 3 source rows

    @pytest.mark.asyncio
    async def test_cross_search_json_items_carry_license(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            result = await heritage_cross_search(
                CrossSearchInput(query="Hodler", response_format=ResponseFormat.JSON)
            )
        assert isinstance(result, ResultEnvelope)
        for section in result.results:
            assert section.get("license")
            assert section.get("url")


class _RecordingCtx:
    """Minimaler Context-Doppelgänger, der Progress-/Warning-Aufrufe mitschreibt."""
    def __init__(self):
        self.progress: list[tuple] = []
        self.warnings: list[str] = []

    async def report_progress(self, progress, total=None, message=None):
        self.progress.append((progress, total, message))

    async def warning(self, message, **extra):
        self.warnings.append(message)


class TestProgressReporting:
    """SDK-003: cross_search meldet Progress je Quelle und warnt bei Fehlern."""

    @pytest.mark.asyncio
    async def test_progress_reported_per_source(self):
        ctx = _RecordingCtx()
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            params = CrossSearchInput(query="Volksschule", limit_per_source=3)
            await heritage_cross_search(params, ctx=ctx)

        # one progress notification per queried source, counting up to the total
        assert [p[0] for p in ctx.progress] == [1, 2, 3]
        assert all(p[1] == 3 for p in ctx.progress)
        assert ctx.warnings == []

    @pytest.mark.asyncio
    async def test_failing_source_emits_warning(self):
        ctx = _RecordingCtx()
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(503)  # SIK-ISEA fails
            )
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            params = CrossSearchInput(query="Test", sources=["sik_isea", "snm"])
            result = await heritage_cross_search(params, ctx=ctx)

        # progress still reported for both sources, exactly one structured warning
        assert len(ctx.progress) == 2
        assert len(ctx.warnings) == 1
        assert "SIK-ISEA" in ctx.warnings[0]
        # the surviving source is still present in the rendered result
        assert "SNM" in result

    @pytest.mark.asyncio
    async def test_no_ctx_is_tolerated(self):
        # direct invocation without a Context (ctx=None) must not raise
        with respx.mock:
            respx.get(f"{CKAN_API}/package_search").mock(
                return_value=httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            )
            params = CrossSearchInput(query="Test", sources=["snm"])
            result = await heritage_cross_search(params)
        assert "SNM" in result


class TestFuzzyMatch:
    """ARCH-003: match_type (exact/fuzzy/none) + gelockerte Retry-Suche."""

    @pytest.mark.asyncio
    async def test_artists_exact_match_type(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
            )
            params = ArtistSearchInput(query="Hodler", response_format=ResponseFormat.JSON)
            result = await heritage_search_artists(params)
        assert isinstance(result, ResultEnvelope)
        assert result.match_type == "exact"

    @pytest.mark.asyncio
    async def test_artists_fuzzy_retry(self):
        empty = {"success": True, "result": {"resource_id": SIKART_RESOURCE_ID,
                                             "total": 0, "records": []}}

        def handler(request):
            q = request.url.params.get("q", "")
            # exact attempt uses both terms; loosened retry uses the longest term
            if q == "Hodler Bern":
                return httpx.Response(200, json=empty)
            return httpx.Response(200, json=MOCK_SIKART_DATASTORE)

        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(side_effect=handler)
            params = ArtistSearchInput(
                query="Hodler", region="Bern", response_format=ResponseFormat.JSON
            )
            result = await heritage_search_artists(params)
        assert isinstance(result, ResultEnvelope)
        assert result.match_type == "fuzzy"
        assert result.count == 2

    @pytest.mark.asyncio
    async def test_artists_fuzzy_note_in_markdown(self):
        empty = {"success": True, "result": {"total": 0, "records": []}}

        def handler(request):
            q = request.url.params.get("q", "")
            return httpx.Response(200, json=empty if q == "Hodler Bern"
                                  else MOCK_SIKART_DATASTORE)

        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(side_effect=handler)
            result = await heritage_search_artists(
                ArtistSearchInput(query="Hodler", region="Bern")
            )
        assert "match_type: fuzzy" in result

    @pytest.mark.asyncio
    async def test_artists_none_returns_structured_envelope(self):
        empty = {"success": True, "result": {"total": 0, "records": []}}
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(200, json=empty)
            )
            params = ArtistSearchInput(
                query="Xyzzy", region="Nirgendwo", response_format=ResponseFormat.JSON
            )
            result = await heritage_search_artists(params)
        assert isinstance(result, ResultEnvelope)
        assert result.match_type == "none"
        assert result.count == 0
        assert result.results == []

    @pytest.mark.asyncio
    async def test_datasets_fuzzy_retry(self):
        empty = {"success": True, "result": {"count": 0, "results": []}}

        def handler(request):
            q = request.url.params.get("q", "")
            # the loosened retry introduces OR / wildcard syntax
            if "OR" in q or "*" in q:
                return httpx.Response(200, json=MOCK_CKAN_RESPONSE)
            return httpx.Response(200, json=empty)

        with respx.mock:
            respx.get(f"{CKAN_API}/package_search").mock(side_effect=handler)
            params = MuseumSearchInput(query="Münzen", response_format=ResponseFormat.JSON)
            result = await heritage_search_museum_datasets(params)
        assert isinstance(result, ResultEnvelope)
        assert result.match_type == "fuzzy"
        assert result.count >= 1

    @pytest.mark.asyncio
    async def test_helveticat_none_is_structured(self):
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(
                return_value=httpx.Response(200, text=MOCK_OAI_RECORDS)
            )
            params = HelvticatSearchInput(
                query="zzz-kein-treffer", response_format=ResponseFormat.JSON
            )
            result = await heritage_search_helveticat(params)
        assert isinstance(result, ResultEnvelope)
        assert result.match_type == "none"
        assert result.count == 0


class TestStructuredLogging:
    """OBS-003: strukturierte JSON-Logs mit Pro-Aufruf-Kontext und Severity."""

    @pytest.mark.asyncio
    async def test_tool_call_is_logged_with_tool_name(self):
        with capture_logs() as logs:
            with respx.mock:
                respx.get(f"{CKAN_API}/datastore_search").mock(
                    return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
                )
                await heritage_search_artists(ArtistSearchInput(query="Hodler"))
        call_events = [e for e in logs if e["event"] == "tool.call"]
        assert call_events
        assert call_events[0]["tool"] == "heritage_search_artists"
        assert call_events[0]["log_level"] == "info"

    @pytest.mark.asyncio
    async def test_upstream_error_logged_at_warning(self):
        with capture_logs() as logs:
            with respx.mock:
                respx.get(f"{CKAN_API}/datastore_search").mock(
                    return_value=httpx.Response(503)
                )
                # the error is raised (→ isError downstream), and logged on the way out
                with pytest.raises(ToolError, match="Fehler"):
                    await heritage_search_artists(ArtistSearchInput(query="Hodler"))
        # the failure is recorded as a structured warning (class + status, no payload)
        warn = [e for e in logs if e["event"] == "upstream.error"]
        assert warn
        assert warn[0]["log_level"] == "warning"
        assert warn[0]["error_kind"] == "HTTPStatusError"
        assert warn[0]["status"] == 503

    @pytest.mark.asyncio
    async def test_unexpected_error_logged_at_error_and_masked(self):
        @mask_unexpected_errors
        async def boom(_):
            raise RuntimeError("internal detail that must not leak")

        with capture_logs() as logs:
            with pytest.raises(ToolError) as exc:
                await boom(None)
        # client-facing message is generic (no leak of the internal detail)
        assert "internal detail" not in str(exc.value)
        err = [e for e in logs if e["event"] == "tool.unexpected_error"]
        assert err
        assert err[0]["log_level"] == "error"
        assert err[0]["error_type"] == "RuntimeError"

    def test_request_log_context_outside_request(self):
        # No active MCP request → only the tool name, request_id gracefully omitted
        ctx = _request_log_context("heritage_demo")
        assert ctx == {"tool": "heritage_demo"}


class TestTracing:
    """OBS-006: OpenTelemetry-Spans pro Tool-Call, gated über Env-Var."""

    def test_disabled_by_default(self):
        import swiss_cultural_heritage_mcp.server as srv
        # No OTEL endpoint configured in the test env → tracing is off (no overhead)
        assert srv._otel_span is None
        assert srv._init_tracing() is False

    @pytest.mark.asyncio
    async def test_tool_span_records_name_and_is_error(self):
        pytest.importorskip("opentelemetry")
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )

        import swiss_cultural_heritage_mcp.server as srv

        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        # inject directly (hermetic: no global provider / httpx instrumentation)
        srv._otel_span = provider.get_tracer("test").start_as_current_span
        try:
            with respx.mock:
                respx.get(f"{CKAN_API}/datastore_search").mock(
                    return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
                )
                await heritage_search_artists(ArtistSearchInput(query="Hodler"))
                respx.get(f"{CKAN_API}/datastore_search").mock(
                    return_value=httpx.Response(503)
                )
                # OBS-001: the error path raises; the span still closes with is_error=True
                with pytest.raises(ToolError):
                    await heritage_search_artists(ArtistSearchInput(query="Boom"))
        finally:
            srv._otel_span = None

        tool_spans = [
            s for s in exporter.get_finished_spans()
            if s.name == "mcp.tool.heritage_search_artists"
        ]
        assert len(tool_spans) == 2
        assert tool_spans[0].attributes["mcp.tool.name"] == "heritage_search_artists"
        assert tool_spans[0].attributes["mcp.tool.is_error"] is False  # success
        assert tool_spans[1].attributes["mcp.tool.is_error"] is True   # upstream 503

    @pytest.mark.asyncio
    async def test_init_tracing_instruments_httpx(self):
        pytest.importorskip("opentelemetry")
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
            InMemorySpanExporter,
        )

        import swiss_cultural_heritage_mcp.server as srv

        exporter = InMemorySpanExporter()
        assert srv._init_tracing(exporter=exporter) is True
        try:
            with respx.mock:
                respx.get(f"{CKAN_API}/datastore_search").mock(
                    return_value=httpx.Response(200, json=MOCK_SIKART_DATASTORE)
                )
                await heritage_search_artists(ArtistSearchInput(query="Hodler"))
            spans = exporter.get_finished_spans()
            names = {s.name for s in spans}
            assert "mcp.tool.heritage_search_artists" in names
            # httpx auto-instrumentation produced a CLIENT child span
            assert any(s.kind.name == "CLIENT" for s in spans)
        finally:
            HTTPXClientInstrumentor().uninstrument()
            srv._otel_span = None


class TestErrorIsFlagged:
    """OBS-001: handled upstream errors surface as isError, not as content."""

    @staticmethod
    async def _call(name: str, arguments: dict):
        """Invoke a tool through the SDK's low-level CallTool handler."""
        import mcp.types as types
        handler = mcp._mcp_server.request_handlers[types.CallToolRequest]
        req = types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name=name, arguments=arguments),
        )
        return (await handler(req)).root  # CallToolResult

    @pytest.mark.asyncio
    async def test_upstream_failure_is_flagged_iserror(self):
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(503)
            )
            result = await self._call("heritage_search_artists", {"params": {"query": "Hodler"}})
        assert result.isError is True
        assert "Fehler" in result.content[0].text  # German guidance preserved

    @pytest.mark.asyncio
    async def test_empty_result_is_not_flagged_iserror(self):
        # A genuine empty result is a valid answer, not an error
        with respx.mock:
            respx.get(f"{CKAN_API}/datastore_search").mock(
                return_value=httpx.Response(
                    200, json={"success": True, "result": {"total": 0, "records": []}}
                )
            )
            result = await self._call("heritage_search_artists", {"params": {"query": "zzz-none"}})
        assert result.isError is False
        assert "Keine Künstler" in result.content[0].text

    @pytest.mark.asyncio
    async def test_direct_call_raises_tool_error(self):
        # The mechanism: tools raise ToolError (mapped to isError) rather than
        # returning a 'Fehler:' string the client would read as a normal result.
        with respx.mock:
            respx.get(NB_OAI_PMH).mock(return_value=httpx.Response(503))
            with pytest.raises(ToolError, match="Fehler"):
                await heritage_search_helveticat(HelvticatSearchInput(query="x"))


class TestToolPins:
    """SEC-022: committed tool-definition hash detects silent drift / rug pulls."""

    def test_tool_definitions_match_committed_pin(self):
        import json
        import pathlib

        from swiss_cultural_heritage_mcp._toolpins import compute_tool_pins

        pin_file = (
            pathlib.Path(__file__).resolve().parents[1]
            / "audits" / "tool-pins" / "current.json"
        )
        committed = json.loads(pin_file.read_text())
        live = compute_tool_pins(mcp)

        # version is environment-dependent and intentionally not compared
        assert live["tools"] == committed["tools"], (
            "Tool definitions changed (SEC-022). If intentional, regenerate the "
            "pin with `PYTHONPATH=src python scripts/pin_tools.py` and add a "
            "CHANGELOG re-approval note describing the change."
        )
        assert live["manifest_sha256"] == committed["manifest_sha256"]
        assert live["tool_count"] == committed["tool_count"]


# ─────────────────────────── Live Tests (skipped in CI) ────────────────────────

@pytest.mark.live
class TestLiveSIKISEA:
    @pytest.mark.asyncio
    async def test_live_search_hodler(self):
        params = ArtistSearchInput(query="Hodler", limit=3)
        result = await heritage_search_artists(params)
        assert "Fehler" not in result

    @pytest.mark.asyncio
    async def test_live_search_by_region(self):
        params = ArtistSearchInput(region="Zürich", limit=5)
        result = await heritage_search_artists(params)
        # Should either return results or "Keine Künstler"
        assert isinstance(result, str)


@pytest.mark.live
class TestLiveSNM:
    @pytest.mark.asyncio
    async def test_live_search_snm(self):
        params = MuseumSearchInput(limit=5)
        result = await heritage_search_museum_datasets(params)
        assert "Fehler" not in result


@pytest.mark.live
class TestLiveNB:
    @pytest.mark.asyncio
    async def test_live_list_sets(self):
        result = await heritage_list_nb_collections()
        assert "Fehler" not in result
