"""
bakom-mcp: MCP Server für BAKOM Open Data (Bundesamt für Kommunikation)

Stellt KI-Modellen Zugriff auf Schweizer Telekommunikations-,
Breitband- und Mediendaten via geo.admin.ch, opendata.swiss und BAKOM-APIs.

12 Tools in 4 Kategorien:
  - Breitband & Konnektivität (3 Tools)
  - Mobilfunk & Sendeanlagen (3 Tools)
  - Medien & RTV (3 Tools)
  - Telekommunikationsstatistik (3 Tools)
"""

from __future__ import annotations

import functools
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, NoReturn, TypeVar

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bakom_mcp")


# Decorator fuer Tool-Call-Lifecycle-Logs (OBS-003).
# Loggt start/ok/failed mit Tool-Name, Duration und Error-Class auf stderr.
# Wird auf alle 11 Tools angewendet — `functools.wraps` erhaelt die
# Signatur, sodass FastMCP weiterhin Pydantic-Inputs/Outputs introspizieren kann.
T = TypeVar("T")


def _log_tool_call(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Wraps a tool function with start/ok/failed structured logs."""
    tool_name = fn.__name__

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.monotonic()
        logger.info("tool_call_start", extra={"tool": tool_name})
        try:
            result = await fn(*args, **kwargs)
        except Exception as exc:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.warning(
                "tool_call_failed",
                extra={
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "error_class": type(exc).__name__,
                },
            )
            raise
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(
            "tool_call_ok",
            extra={"tool": tool_name, "duration_ms": duration_ms},
        )
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Lifespan: ein httpx.AsyncClient für die gesamte Server-Lebensdauer
# ---------------------------------------------------------------------------
HTTP_TIMEOUT_SEC = 15.0
HTTP_USER_AGENT = "bakom-mcp/1.0 (+https://github.com/malkreide/bakom-mcp)"


# Code-Layer-Egress-Allowlist (SEC-021).
# Jeder Outbound-HTTP-Call wird gegen diese Liste validiert; Aufrufe an
# Hosts ausserhalb des Sets werfen httpx.RequestError und gehen nicht raus.
# Bei Erweiterung um neue Datenquellen muss diese Liste explizit erweitert
# werden — das macht jeden neuen Egress-Punkt im Diff sichtbar (Review-Signal).
ALLOWED_EGRESS_HOSTS: frozenset[str] = frozenset(
    {
        "api3.geo.admin.ch",
        "wms.geo.admin.ch",
        "geodesy.geo.admin.ch",
        "ckan.opendata.swiss",
        "rtvdb.ofcomnet.ch",
        "www.bakom.admin.ch",
    }
)


class EgressNotAllowedError(httpx.RequestError):
    """Outbound-Call an einen nicht in ALLOWED_EGRESS_HOSTS gelisteten Host."""


async def _enforce_egress_allowlist(request: httpx.Request) -> None:
    """httpx-Event-Hook: prueft jedes Request-Ziel gegen die Allow-List.

    Wird beim Client-Setup im lifespan registriert. Greift unabhaengig
    davon, ob ein Tool client.get/post/stream/request nutzt.
    """
    host = request.url.host
    if host not in ALLOWED_EGRESS_HOSTS:
        logger.warning("Egress blocked", extra={"host": host, "url": str(request.url)})
        raise EgressNotAllowedError(
            f"Egress blocked: host '{host}' not in ALLOWED_EGRESS_HOSTS",
            request=request,
        )


@dataclass
class AppContext:
    """Lifespan-Context, via FastMCP an alle Tools gereicht."""

    http: httpx.AsyncClient


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialisiert einen einzigen httpx.AsyncClient für alle Tool-Calls.

    Vorher: jeder Tool-Aufruf öffnete und schloss eine eigene Connection
    (TLS-Handshake pro Call). Mit Lifespan wird genau eine Connection
    aufgebaut und bei Server-Shutdown sauber geschlossen.
    """
    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT_SEC,
        headers={"User-Agent": HTTP_USER_AGENT},
        event_hooks={"request": [_enforce_egress_allowlist]},
    ) as client:
        yield AppContext(http=client)


@asynccontextmanager
async def _shared_client(ctx: Context) -> AsyncIterator[httpx.AsyncClient]:
    """Yieldet den Lifespan-Client, ohne ihn zu schliessen.

    Behält die `async with`-Form in Tool-Funktionen bei (kein Dedent
    grosser Blöcke), während der Client server-weit wiederverwendet wird.
    Aclose erfolgt im Lifespan-Hook, nicht hier.
    """
    yield ctx.request_context.lifespan_context.http


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
GEO_ADMIN_API = "https://api3.geo.admin.ch/rest/services/api/MapServer"
GEO_ADMIN_IDENTIFY = "https://api3.geo.admin.ch/rest/services/api/MapServer/identify"
GEO_ADMIN_FIND = "https://api3.geo.admin.ch/rest/services/api/MapServer/find"
OPENDATA_SWISS_API = "https://ckan.opendata.swiss/api/3/action"
RTV_DB_API = "https://rtvdb.ofcomnet.ch/api"
BAKOM_INFOMAILING = "https://www.bakom.admin.ch/de/bakom-infomailing"

TIMEOUT = 20.0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# OGD-CH Lizenz-Attribution (CH-004): BAKOM-Daten auf opendata.swiss /
# geo.admin.ch sind unter CC BY 4.0 verfuegbar. Tool-Outputs zeigen die
# Quelle und Lizenz im Footer, damit nachgelagerte Verwendungen die
# Attribution-Pflicht erfuellen koennen.
LICENSE_NAME = "CC BY 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/deed.de"
ATTRIBUTION_FOOTER_MD = (
    "\n\n---\n"
    "**Quelle:** Bundesamt für Kommunikation (BAKOM) "
    "via opendata.swiss / geo.admin.ch · "
    f"**Lizenz:** [{LICENSE_NAME}]({LICENSE_URL})"
)

# geo.admin.ch Layer-IDs für BAKOM-Daten
LAYER_MOBILFUNKANLAGEN = "ch.bakom.standorte-mobilfunkanlagen"
WMS_GEO_ADMIN = "https://wms.geo.admin.ch/"
LAYER_RADIO_TV = "ch.bakom.radio-fernsehsender"
LAYER_BROADBAND_5G = "ch.bakom.netzabdeckung-5g"
LAYER_BROADBAND_4G = "ch.bakom.netzabdeckung-4g"
LAYER_BROADBAND_FESTNETZ = "ch.bakom.anschlussart-verfuegbarkeit"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ResponseFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"


class MobilGenerations(StrEnum):
    G5 = "5G"
    G4 = "4G"
    G3 = "3G"


class BroadbandSpeed(StrEnum):
    S30 = "30"
    S100 = "100"
    S300 = "300"
    S500 = "500"
    S1000 = "1000"


class MediaType(StrEnum):
    RADIO = "radio"
    TV = "tv"
    ALLE = "alle"


# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------
class CoordinateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    latitude: float = Field(
        ...,
        description="Breitengrad in WGS84 (z.B. 47.3769 für Zürich)",
        ge=45.8,
        le=47.9,
    )
    longitude: float = Field(
        ...,
        description="Längengrad in WGS84 (z.B. 8.5417 für Zürich)",
        ge=5.9,
        le=10.6,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class BroadbandCoverageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    latitude: float = Field(
        ...,
        description="Breitengrad WGS84 (z.B. 47.3769 für Zürich)",
        ge=45.8,
        le=47.9,
    )
    longitude: float = Field(
        ...,
        description="Längengrad WGS84 (z.B. 8.5417 für Zürich)",
        ge=5.9,
        le=10.6,
    )
    min_speed_mbps: BroadbandSpeed = Field(
        default=BroadbandSpeed.S100,
        description="Minimale Downloadgeschwindigkeit: '30', '100', '300', '500' oder '1000' Mbit/s",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class MobileCoverageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    latitude: float = Field(
        ...,
        description="Breitengrad WGS84 (z.B. 47.3769 für Zürich)",
        ge=45.8,
        le=47.9,
    )
    longitude: float = Field(
        ...,
        description="Längengrad WGS84 (z.B. 8.5417 für Zürich)",
        ge=5.9,
        le=10.6,
    )
    generation: MobilGenerations = Field(
        default=MobilGenerations.G5,
        description="Mobilfunkgeneration: '5G', '4G' oder '3G'",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class AntennaSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    latitude: float = Field(
        ...,
        description="Breitengrad WGS84 (Suchzentrum)",
        ge=45.8,
        le=47.9,
    )
    longitude: float = Field(
        ...,
        description="Längengrad WGS84 (Suchzentrum)",
        ge=5.9,
        le=10.6,
    )
    radius_m: int = Field(
        default=1000,
        description="Suchradius in Metern (100–5000)",
        ge=100,
        le=5000,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class RTVSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str | None = Field(
        default=None,
        description="Suchbegriff (Name des Senders, z.B. 'SRF', 'Radio 1', 'Tele Züri')",
        max_length=100,
    )
    media_type: MediaType = Field(
        default=MediaType.ALLE,
        description="Medientyp: 'radio', 'tv' oder 'alle'",
    )
    kanton: str | None = Field(
        default=None,
        description="Kantonskürzel (z.B. 'ZH', 'BE', 'GE')",
        max_length=2,
    )
    limit: int = Field(
        default=20,
        description="Maximale Anzahl Resultate (1–50)",
        ge=1,
        le=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )

    @field_validator("kanton")
    @classmethod
    def kanton_uppercase(cls, v: str | None) -> str | None:
        return v.upper() if v else v


class TelekomStatInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    thema: str = Field(
        default="breitband",
        description=(
            "Statistikthema: 'breitband', 'mobilfunk', 'festnetz', "
            "'marktanteile', 'haushaltszugang'"
        ),
        max_length=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class MultiLocationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    locations: list[dict[str, Any]] = Field(
        ...,
        description=(
            "Liste von Standorten mit 'name', 'latitude', 'longitude'. "
            "Beispiel: [{'name': 'Schulhaus Leutschenbach', 'latitude': 47.415, 'longitude': 8.565}]"
        ),
        min_length=1,
        max_length=20,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
async def _geo_identify(
    client: httpx.AsyncClient,
    layer: str,
    lat: float,
    lon: float,
    tolerance: int = 10,
) -> dict[str, Any]:
    """Identifiziere Features an einer Koordinate via geo.admin.ch."""
    # WGS84 → LV95 Konvertierung via geo.admin.ch Reframe-API
    reframe_url = "https://geodesy.geo.admin.ch/reframe/wgs84tolv95"
    r = await client.get(
        reframe_url,
        params={"easting": lon, "northing": lat, "altitude": 0, "format": "json"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    coords = r.json()
    east = coords.get("easting", lon)
    north = coords.get("northing", lat)

    identify_url = f"{GEO_ADMIN_API}/identify"
    params = {
        "geometry": f"{east - 200},{north - 200},{east + 200},{north + 200}",
        "geometryType": "esriGeometryEnvelope",
        "imageDisplay": "1000,1000,96",
        "mapExtent": f"{east - 1000},{north - 1000},{east + 1000},{north + 1000}",
        "tolerance": tolerance,
        "layers": f"all:{layer}",
        "sr": "2056",
        "returnGeometry": "false",
        "lang": "de",
    }
    r2 = await client.get(identify_url, params=params, timeout=TIMEOUT)
    r2.raise_for_status()
    return r2.json()


async def _wms_abgedeckt(
    client: httpx.AsyncClient,
    layer: str,
    east: float,
    north: float,
    radius: int = 200,
) -> bool:
    """
    Prüft via WMS GetFeatureInfo ob ein Rasterlayer an einer LV95-Koordinate
    Daten enthält (= Abdeckung vorhanden).
    Gibt True zurück wenn mindestens 1 Feature gefunden wird.
    """
    bbox = f"{east - radius},{north - radius},{east + radius},{north + radius}"
    r = await client.get(
        WMS_GEO_ADMIN,
        params={
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer,
            "QUERY_LAYERS": layer,
            "INFO_FORMAT": "application/json",
            "I": "500",
            "J": "500",
            "WIDTH": "1000",
            "HEIGHT": "1000",
            "CRS": "EPSG:2056",
            "BBOX": bbox,
        },
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        return False
    try:
        data = r.json()
        return len(data.get("features", [])) > 0
    except Exception:
        return False


async def _opendata_dataset_info(client: httpx.AsyncClient, dataset_id: str) -> dict[str, Any]:
    """Metadaten eines opendata.swiss-Datensatzes abrufen."""
    url = f"{OPENDATA_SWISS_API}/package_show"
    r = await client.get(url, params={"id": dataset_id}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _point_to_envelope(east: float, north: float, tolerance: int = 100) -> str:
    """Erstellt eine Bounding-Box-Geometrie um einen LV95-Punkt (für geo.admin.ch identify)."""
    return f"{east - tolerance},{north - tolerance},{east + tolerance},{north + tolerance}"


def _wgs84_to_lv95_approx(lat: float, lon: float) -> tuple[float, float]:
    """
    Näherungsformel WGS84 → LV95 (ausreichend für Bounding-Box-Anfragen).
    Quelle: swisstopo approximation.
    """
    lat_aux = (lat * 3600 - 169028.66) / 10000
    lon_aux = (lon * 3600 - 26782.5) / 10000

    east = (
        2600072.37
        + 211455.93 * lon_aux
        - 10938.51 * lon_aux * lat_aux
        - 0.36 * lon_aux * lat_aux**2
        - 44.54 * lon_aux**3
    )
    north = (
        1200147.07
        + 308807.95 * lat_aux
        + 3745.25 * lon_aux**2
        + 76.63 * lat_aux**2
        - 194.56 * lon_aux**2 * lat_aux
        + 119.79 * lat_aux**3
    )
    return east, north


def _handle_api_error(e: Exception) -> str:
    """Generische, LLM-sichere Fehlermeldung ohne Stack/URL-Leak (OBS-002).

    Reine Klassifikations-Funktion — ruft kein raise. Genutzt von
    `_raise_api_error` (Standardpfad) und von Test-Suiten, die den
    Klassifikator direkt verifizieren wollen.
    """
    if isinstance(e, EgressNotAllowedError):
        return "Fehler: Datenquelle nicht in Egress-Allowlist (Konfigurationsproblem)."
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Fehler: Ressource nicht gefunden. Bitte Koordinaten oder Parameter prüfen."
        if e.response.status_code == 429:
            return "Fehler: Rate-Limit erreicht. Bitte kurz warten."
        if e.response.status_code >= 500:
            return f"Fehler: API-Server nicht erreichbar (HTTP {e.response.status_code})."
        return f"Fehler: API-Anfrage fehlgeschlagen (HTTP {e.response.status_code})."
    if isinstance(e, httpx.TimeoutException):
        return "Fehler: Zeitüberschreitung. API antwortet nicht – bitte erneut versuchen."
    if isinstance(e, httpx.ConnectError):
        return "Fehler: Keine Verbindung zur API. Netzwerk prüfen."
    logger.exception("Unerwarteter Fehler in Tool-Aufruf")
    return "Fehler: Unerwarteter interner Fehler. Bitte erneut versuchen."


def _raise_api_error(e: Exception) -> NoReturn:
    """Klassifiziert einen API-Fehler und raise't `ToolError` (OBS-001).

    Resultat auf der Wire: `CallToolResult(isError=True, ...)` — der Client
    kann zwischen "Tool lief, Daten OK" und "Tool-Aufruf fehlgeschlagen"
    unterscheiden und Retry-Logik anwenden. Generische Messages stellen
    sicher, dass keine Stack/URL/Class-Details leaken (OBS-002).
    """
    raise ToolError(_handle_api_error(e)) from e


# ---------------------------------------------------------------------------
# Server-Initialisierung
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "bakom_mcp",
    instructions=(
        "Dieser Server bietet Zugriff auf Schweizer Telekommunikations-, "
        "Breitband- und Mediendaten des Bundesamts für Kommunikation (BAKOM). "
        "Koordinaten müssen im WGS84-Format angegeben werden (Schweiz: "
        "lat 45.8–47.9, lon 5.9–10.6). Alle Daten sind öffentlich und "
        "kostenlos verfügbar (Open Government Data)."
    ),
    lifespan=lifespan,
)


# ===========================================================================
# KATEGORIE 1: BREITBAND & KONNEKTIVITÄT
# ===========================================================================


@mcp.tool(
    name="bakom_broadband_coverage",
    annotations={
        "title": "Breitbandversorgung für einen Standort",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_broadband_coverage(params: BroadbandCoverageInput, ctx: Context) -> str:
    """Breitbandversorgung (Festnetz) für einen Standort in der Schweiz abfragen.

    Zeigt, ob ein Gebäude am angegebenen Standort mit einer bestimmten
    Downloadgeschwindigkeit versorgt wird. Nutzt den BAKOM Breitbandatlas
    via geo.admin.ch API (Rasterauflösung: 250×250 Meter).

    Args:
        params (BroadbandCoverageInput): Eingabeparameter mit:
            - latitude (float): Breitengrad WGS84 (45.8–47.9)
            - longitude (float): Längengrad WGS84 (5.9–10.6)
            - min_speed_mbps (str): Mindestgeschwindigkeit ('30','100','300','500','1000')
            - response_format (str): 'markdown' oder 'json'

    Returns:
        str: Breitbandverfügbarkeit mit Abdeckungsprozentsatz und
             verfügbaren Technologien (DSL, Kabel, Glasfaser).

    Schema:
        {
          "standort": {"lat": float, "lon": float},
          "geschwindigkeit_mbps": int,
          "abdeckung_prozent": float,
          "glasfaser_verfuegbar": bool,
          "technologien": list[str],
          "datenquelle": str
        }
    """
    speed_to_layer = {
        "30": "ch.bakom.downlink30",
        "100": "ch.bakom.downlink100",
        "300": "ch.bakom.downlink300",
        "500": "ch.bakom.downlink500",
        "1000": "ch.bakom.downlink1000",
    }
    layer = speed_to_layer.get(params.min_speed_mbps.value, speed_to_layer["100"])

    try:
        async with _shared_client(ctx) as client:
            east, north = _wgs84_to_lv95_approx(params.latitude, params.longitude)
            abgedeckt = await _wms_abgedeckt(client, layer, east, north)

            result = {
                "standort": {"lat": params.latitude, "lon": params.longitude},
                "geschwindigkeit_mbps": int(params.min_speed_mbps.value),
                "abgedeckt": abgedeckt,
                "datenquelle": f"BAKOM Breitbandatlas – {params.min_speed_mbps.value} Mbit/s",
                "geodaten_api": f"https://map.geo.admin.ch/?layers={layer}",
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            speed = params.min_speed_mbps.value
            status = "✅ Versorgt" if abgedeckt else "❌ Nicht versorgt"
            md = f"""## Breitbandversorgung – {speed} Mbit/s
**Standort:** {params.latitude:.4f}° N, {params.longitude:.4f}° E
**Mindestgeschwindigkeit:** {speed} Mbit/s (Festnetz, Download)

### Versorgungsstatus
| Merkmal | Wert |
|---------|------|
| Abdeckung {speed} Mbit/s | {status} |

**Datenquelle:** {result["datenquelle"]}  
**Karte:** {result["geodaten_api"]}"""
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_glasfaser_verfuegbarkeit",
    annotations={
        "title": "Glasfasernetz-Verfügbarkeit (FTTB/FTTH)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_glasfaser_verfuegbarkeit(params: CoordinateInput, ctx: Context) -> str:
    """Glasfaserverfügbarkeit (FTTB/FTTH) für einen Schweizer Standort prüfen.

    Zeigt, ob Glasfaseranschluss bis zum Gebäude (FTTB) oder in die
    Wohnung/das Büro (FTTH) verfügbar ist. Nutzt BAKOM Breitbandatlas
    via geo.admin.ch (Rasterauflösung: 250×250 Meter).

    Args:
        params (CoordinateInput): Standortkoordinaten WGS84 + Ausgabeformat.

    Returns:
        str: Glasfaserverfügbarkeit mit Technologiedetails.

    Schema:
        {
          "standort": {"lat": float, "lon": float},
          "fttb_verfuegbar": bool | None,
          "ftth_verfuegbar": bool | None,
          "anbieter_anzahl": int | None,
          "datenquelle": str
        }
    """
    layer = "ch.bakom.anschlussart-glasfaser"
    try:
        async with _shared_client(ctx) as client:
            east, north = _wgs84_to_lv95_approx(params.latitude, params.longitude)
            abgedeckt = await _wms_abgedeckt(client, layer, east, north)

            result = {
                "standort": {"lat": params.latitude, "lon": params.longitude},
                "glasfaser_verfuegbar": abgedeckt,
                "datenquelle": "BAKOM Breitbandatlas – Glasfaser (FTTB/FTTH)",
                "opendata_swiss": "https://opendata.swiss/de/dataset/verfugbare-anschlussarten-glasfaser-fttb-ftth",
                "geodaten_api": f"https://map.geo.admin.ch/?layers={layer}",
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            status = "✅ Verfügbar" if abgedeckt else "❌ Nicht verfügbar"
            md = f"""## Glasfaserverfügbarkeit (FTTB/FTTH)
**Standort:** {params.latitude:.4f}° N, {params.longitude:.4f}° E

| Technologie | Status |
|-------------|--------|
| Glasfaser (FTTB/FTTH) | {status} |

**Datenquelle:** {result["datenquelle"]}  
**Karte:** {result["geodaten_api"]}"""
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_multi_standort_konnektivitaet",
    annotations={
        "title": "Konnektivitätsvergleich mehrerer Standorte",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_multi_standort_konnektivitaet(params: MultiLocationInput, ctx: Context) -> str:
    """Breitband- und Mobilfunkversorgung für mehrere Standorte gleichzeitig vergleichen.

    Ideal für Schulhausvergleiche, Standortentscheide oder
    Digitale-Chancengleichheit-Analysen im Schulamt-/Stadtverwaltungskontext.
    Pro Standort werden 5G-Abdeckung und Glasfaserstatus abgefragt.

    Args:
        params (MultiLocationInput): Liste von Standorten (max. 20) mit
            'name', 'latitude', 'longitude' + Ausgabeformat.

    Returns:
        str: Vergleichstabelle mit Konnektivitätsstatus pro Standort.

    Schema:
        {
          "standorte": [
            {
              "name": str,
              "lat": float,
              "lon": float,
              "5g_abdeckung": bool | None,
              "glasfaser_fttb": bool | None,
              "fehler": str | None
            }
          ],
          "zusammenfassung": {
            "total": int,
            "mit_5g": int,
            "mit_glasfaser": int
          }
        }
    """
    standort_results = []
    total = len(params.locations)
    await ctx.info(f"Verarbeite {total} Standort(e)…")

    async with _shared_client(ctx) as client:
        for index, loc in enumerate(params.locations):
            name = loc.get("name", "Unbekannt")
            lat = float(loc.get("latitude", 0))
            lon = float(loc.get("longitude", 0))

            # SDK-003: Progress-Report fuer Long-Running-Tools.
            # Claude-Desktop / MCP-Inspector zeigt 0/total → total/total Spinner.
            await ctx.report_progress(progress=index, total=total)

            if not (45.8 <= lat <= 47.9) or not (5.9 <= lon <= 10.6):
                standort_results.append(
                    {
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "5g_abdeckung": None,
                        "glasfaser_fttb": None,
                        "fehler": "Koordinaten ausserhalb Schweiz",
                    }
                )
                continue

            try:
                east, north = _wgs84_to_lv95_approx(lat, lon)
                has_5g = await _wms_abgedeckt(client, "ch.bakom.mobilnetz-5g", east, north)
                fttb = await _wms_abgedeckt(client, "ch.bakom.anschlussart-glasfaser", east, north)

                standort_results.append(
                    {
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "5g_abdeckung": has_5g,
                        "glasfaser_fttb": fttb,
                        "fehler": None,
                    }
                )

            except Exception:
                logger.exception("Multi-Standort-Abfrage fehlgeschlagen", extra={"standort": name})
                standort_results.append(
                    {
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "5g_abdeckung": None,
                        "glasfaser_fttb": None,
                        "fehler": "Standort konnte nicht abgefragt werden",
                    }
                )

    # SDK-003: Final-Progress signalisiert "fertig" an die UI.
    await ctx.report_progress(progress=total, total=total)

    mit_5g = sum(1 for s in standort_results if s.get("5g_abdeckung") is True)
    mit_glasfaser = sum(1 for s in standort_results if s.get("glasfaser_fttb") is True)

    output = {
        "standorte": standort_results,
        "zusammenfassung": {
            "total": len(standort_results),
            "mit_5g": mit_5g,
            "mit_glasfaser": mit_glasfaser,
        },
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(output, indent=2, ensure_ascii=False)

    # Markdown-Tabelle
    md = "## Konnektivitätsvergleich – Mehrere Standorte\n\n"
    md += "| Standort | 5G | Glasfaser (FTTB) | Hinweis |\n"
    md += "|----------|----|-----------------|---------|\n"
    for s in standort_results:
        g5 = "✅" if s.get("5g_abdeckung") else ("❌" if s.get("5g_abdeckung") is False else "–")
        fib = (
            "✅" if s.get("glasfaser_fttb") else ("❌" if s.get("glasfaser_fttb") is False else "–")
        )
        err = s.get("fehler") or ""
        md += f"| {s['name']} | {g5} | {fib} | {err} |\n"

    md += f"\n**Zusammenfassung:** {mit_5g}/{len(standort_results)} Standorte mit 5G, "
    md += f"{mit_glasfaser}/{len(standort_results)} mit Glasfaser.\n"
    md += "\n**Datenquelle:** BAKOM Breitbandatlas via geo.admin.ch"
    return md + ATTRIBUTION_FOOTER_MD


# ===========================================================================
# KATEGORIE 2: MOBILFUNK & SENDEANLAGEN
# ===========================================================================


@mcp.tool(
    name="bakom_mobilfunk_abdeckung",
    annotations={
        "title": "Mobilfunkabdeckung für einen Standort",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_mobilfunk_abdeckung(params: MobileCoverageInput, ctx: Context) -> str:
    """Mobilfunkabdeckung (5G/4G/3G) für einen Schweizer Standort abfragen.

    Zeigt, wie viele Anbieter den angegebenen Standort mit der gewählten
    Mobilfunkgeneration versorgen (Aussenbereich/Outdoor).
    Rastergrösse: 100×100 Meter.

    Args:
        params (MobileCoverageInput): Koordinaten WGS84, Generation, Format.

    Returns:
        str: Mobilfunkabdeckung mit Anbieteranzahl.

    Schema:
        {
          "standort": {"lat": float, "lon": float},
          "generation": str,
          "anbieter_anzahl": int | None,
          "abgedeckt": bool,
          "datenquelle": str
        }
    """
    gen_to_layer = {
        "5G": "ch.bakom.mobilnetz-5g",
        "4G": "ch.bakom.mobilnetz-4g",
        "3G": "ch.bakom.mobilnetz-3g",
    }
    layer = gen_to_layer.get(params.generation.value, gen_to_layer["5G"])

    try:
        async with _shared_client(ctx) as client:
            east, north = _wgs84_to_lv95_approx(params.latitude, params.longitude)
            abgedeckt = await _wms_abgedeckt(client, layer, east, north)
            gen = params.generation.value

            result = {
                "standort": {"lat": params.latitude, "lon": params.longitude},
                "generation": gen,
                "abgedeckt": abgedeckt,
                "datenquelle": f"BAKOM Breitbandatlas – {gen} Mobilfunk",
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(result, indent=2, ensure_ascii=False)

            abgedeckt_str = "✅ Ja" if abgedeckt else "❌ Nein"
            md = f"""## {gen}-Mobilfunkabdeckung
**Standort:** {params.latitude:.4f}° N, {params.longitude:.4f}° E

| Merkmal | Wert |
|---------|------|
| Abgedeckt ({gen}) | {abgedeckt_str} |

> ℹ️ Abdeckungsangaben beziehen sich auf den Aussenbereich (Outdoor).
> Gebäudedämpfung kann die Innenabdeckung reduzieren.

**Datenquelle:** {result["datenquelle"]}  
**Karte:** https://map.geo.admin.ch/?layers={layer}"""
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_sendeanlagen_suche",
    annotations={
        "title": "Mobilfunkanlagen und Sendeanlagen in der Nähe",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_sendeanlagen_suche(params: AntennaSearchInput, ctx: Context) -> str:
    """Mobilfunkanlagen und Sendeanlagen in einem Umkreis suchen.

    Findet Antennenstandorte (Mobilfunk und Rundfunk) in der Nähe eines
    Standorts. Nützlich für Schulhäuser (Strahlungsquellen), Medienplanung
    oder technische Infrastrukturanalysen.

    Args:
        params (AntennaSearchInput): Koordinaten WGS84, Suchradius, Format.

    Returns:
        str: Liste von Sendeanlagen im Umkreis mit Betreiber und Typ.

    Schema:
        {
          "suchzentrum": {"lat": float, "lon": float},
          "radius_m": int,
          "anlagen": [
            {
              "id": str,
              "typ": str,
              "betreiber": str | None,
              "distanz_m": float | None,
              "koordinaten": {"east": float, "north": float}
            }
          ],
          "total": int
        }
    """
    try:
        async with _shared_client(ctx) as client:
            east, north = _wgs84_to_lv95_approx(params.latitude, params.longitude)
            radius = params.radius_m

            # Bounding Box für die Suche
            bbox = f"{east - radius},{north - radius},{east + radius},{north + radius}"

            r = await client.get(
                f"{GEO_ADMIN_API}/identify",
                params={
                    "geometry": f"{east - radius},{north - radius},{east + radius},{north + radius}",
                    "geometryType": "esriGeometryEnvelope",
                    "imageDisplay": "1000,1000,96",
                    "mapExtent": bbox,
                    "tolerance": 10,
                    "layers": f"all:{LAYER_MOBILFUNKANLAGEN}",
                    "sr": "2056",
                    "returnGeometry": "true",
                    "lang": "de",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            results = r.json().get("results", [])

            anlagen = []
            for item in results[:50]:  # Max 50 Anlagen
                attrs = item.get("attributes", {})
                geom = item.get("geometry", {})
                item_east = geom.get("x", None)
                item_north = geom.get("y", None)

                # Euklidische Distanz in LV95
                distanz = None
                if item_east and item_north:
                    import math

                    distanz = round(
                        math.sqrt((item_east - east) ** 2 + (item_north - north) ** 2), 0
                    )

                anlagen.append(
                    {
                        "id": str(item.get("id", "")),
                        "typ": attrs.get("type", attrs.get("label", "Mobilfunkanlage")),
                        "betreiber": attrs.get("operator", attrs.get("betreiber")),
                        "adresse": attrs.get("address", attrs.get("adresse")),
                        "distanz_m": distanz,
                        "koordinaten": {"east": item_east, "north": item_north},
                    }
                )

            # Nach Distanz sortieren
            anlagen.sort(key=lambda x: x.get("distanz_m") or float("inf"))

            # ARCH-003: Heuristik-Hinweis bei leerem Resultat — schlage einen
            # groesseren Radius vor, falls noch nicht am 5-km-Maximum.
            hinweis: str | None = None
            if not anlagen and params.radius_m < 5000:
                vorschlag_radius = min(params.radius_m * 2, 5000)
                hinweis = (
                    f"Keine Anlagen im Radius {params.radius_m} m gefunden. "
                    f"Empfehlung: Radius auf {vorschlag_radius} m erhoehen "
                    f"und erneut abfragen."
                )
            elif not anlagen:
                hinweis = (
                    "Keine Anlagen im maximalen Radius (5000 m) gefunden — "
                    "Standort ist vermutlich abgelegen."
                )

            output: dict[str, Any] = {
                "suchzentrum": {"lat": params.latitude, "lon": params.longitude},
                "radius_m": params.radius_m,
                "anlagen": anlagen,
                "total": len(anlagen),
                "datenquelle": "BAKOM Mobilfunkanlagen via geo.admin.ch",
            }
            if hinweis:
                output["hinweis"] = hinweis

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(output, indent=2, ensure_ascii=False)

            md = "## Mobilfunkanlagen im Umkreis\n"
            md += f"**Standort:** {params.latitude:.4f}° N, {params.longitude:.4f}° E  \n"
            md += f"**Suchradius:** {params.radius_m} m  \n"
            md += f"**Gefunden:** {len(anlagen)} Anlage(n)\n\n"

            if not anlagen:
                md += f"> **Hinweis:** {hinweis}\n"
            else:
                md += "| # | Typ | Betreiber | Distanz |\n"
                md += "|---|-----|-----------|--------|\n"
                for i, a in enumerate(anlagen[:20], 1):
                    typ = a.get("typ") or "–"
                    betreiber = a.get("betreiber") or "–"
                    dist = f"{int(a['distanz_m'])} m" if a.get("distanz_m") else "–"
                    md += f"| {i} | {typ} | {betreiber} | {dist} |\n"
                if len(anlagen) > 20:
                    md += f"\n_... und {len(anlagen) - 20} weitere Anlagen._\n"

            md += "\n**Datenquelle:** BAKOM Mobilfunkanlagen  \n"
            md += f"**Karte:** https://map.geo.admin.ch/?layers={LAYER_MOBILFUNKANLAGEN}"
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_frequenzdaten",
    annotations={
        "title": "Frequenzdaten und Sendeanlagen-Standorte",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_frequenzdaten(params: CoordinateInput, ctx: Context) -> str:
    """UKW-Radio- und TV-Sendeanlagen für einen Standort abfragen.

    Zeigt Radio- und Fernsehsendeanlagen in der Nähe mit Frequenz-
    und Betreiberinformationen. Nutzt den BAKOM-Layer
    ch.bakom.radio-fernsehsender via geo.admin.ch.

    Args:
        params (CoordinateInput): Standortkoordinaten WGS84 + Format.

    Returns:
        str: Sendeanlagen mit Frequenz, Typ und Betreiber.

    Schema:
        {
          "standort": {"lat": float, "lon": float},
          "sender": [
            {
              "typ": str,
              "frequenz": str | None,
              "betreiber": str | None,
              "programm": str | None
            }
          ],
          "total": int
        }
    """
    try:
        async with _shared_client(ctx) as client:
            east, north = _wgs84_to_lv95_approx(params.latitude, params.longitude)
            radius = 2000  # 2 km für Sender-Suche

            r = await client.get(
                f"{GEO_ADMIN_API}/identify",
                params={
                    "geometry": f"{east - radius},{north - radius},{east + radius},{north + radius}",
                    "geometryType": "esriGeometryEnvelope",
                    "imageDisplay": "1000,1000,96",
                    "mapExtent": f"{east - radius},{north - radius},{east + radius},{north + radius}",
                    "tolerance": 10,
                    "layers": f"all:{LAYER_RADIO_TV}",
                    "sr": "2056",
                    "returnGeometry": "false",
                    "lang": "de",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            results = r.json().get("results", [])

            sender = []
            for item in results[:30]:
                attrs = item.get("attributes", {})
                sender.append(
                    {
                        "typ": attrs.get("type", "Sender"),
                        "frequenz": attrs.get("frequency", attrs.get("frequenz")),
                        "betreiber": attrs.get("operator", attrs.get("betreiber")),
                        "programm": attrs.get("programme", attrs.get("programm")),
                        "label": attrs.get("label"),
                    }
                )

            output = {
                "standort": {"lat": params.latitude, "lon": params.longitude},
                "sender": sender,
                "total": len(sender),
                "suchradius_m": radius,
                "datenquelle": "BAKOM Radio-/TV-Sendeanlagen via geo.admin.ch",
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(output, indent=2, ensure_ascii=False)

            md = "## Radio- und TV-Sendeanlagen\n"
            md += f"**Standort:** {params.latitude:.4f}° N, {params.longitude:.4f}° E  \n"
            md += f"**Suchradius:** {radius // 1000} km  \n"
            md += f"**Gefunden:** {len(sender)} Anlage(n)\n\n"

            if not sender:
                md += "> Keine Sendeanlagen im 2-km-Radius gefunden.\n"
            else:
                md += "| Typ | Programm | Frequenz | Betreiber |\n"
                md += "|-----|----------|----------|-----------|\n"
                for s in sender:
                    typ = s.get("typ") or "–"
                    prog = s.get("programm") or s.get("label") or "–"
                    freq = s.get("frequenz") or "–"
                    betr = s.get("betreiber") or "–"
                    md += f"| {typ} | {prog} | {freq} | {betr} |\n"

            md += "\n**Datenquelle:** BAKOM Radio-/TV-Sendeanlagen  \n"
            md += f"**Karte:** https://map.geo.admin.ch/?layers={LAYER_RADIO_TV}"
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


# ===========================================================================
# KATEGORIE 3: MEDIEN & RTV
# ===========================================================================


@mcp.tool(
    name="bakom_rtv_suche",
    annotations={
        "title": "Radio- und Fernsehsender in der Schweiz suchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_rtv_suche(params: RTVSearchInput, ctx: Context) -> str:
    """Konzessionierte und gemeldete Radio- und TV-Sender in der Schweiz suchen.

    Durchsucht die BAKOM RTV-Datenbank nach lizenzierten Rundfunkveranstaltern.
    Filtermöglichkeiten nach Name, Medientyp (Radio/TV) und Kanton.

    Args:
        params (RTVSearchInput): Suchbegriff, Medientyp, Kanton, Limit, Format.

    Returns:
        str: Liste von Rundfunkveranstaltern mit Kontakt und Konzessionsinfos.

    Schema:
        {
          "resultate": [
            {
              "name": str,
              "typ": str,
              "kanton": str | None,
              "konzession": str | None,
              "url": str | None,
              "sprache": str | None
            }
          ],
          "total": int
        }
    """
    try:
        async with _shared_client(ctx) as client:
            # RTV-Datenbank API
            search_params: dict[str, Any] = {
                "format": "json",
                "limit": params.limit,
            }
            if params.query:
                search_params["search"] = params.query
            if params.media_type != MediaType.ALLE:
                search_params["type"] = params.media_type.value
            if params.kanton:
                search_params["canton"] = params.kanton

            try:
                r = await client.get(
                    f"{RTV_DB_API}/broadcasters",
                    params=search_params,
                    timeout=TIMEOUT,
                )
                r.raise_for_status()
                data = r.json()
                resultate = data.get("results", data.get("data", []))
            except Exception:
                # Fallback: opendata.swiss CKAN für RTV-Metadaten
                r2 = await client.get(
                    f"{OPENDATA_SWISS_API}/package_search",
                    params={
                        "fq": "organization:bundesamt-fur-kommunikation-bakom",
                        "q": f"rtv radio fernsehen {params.query or ''}",
                        "rows": params.limit,
                    },
                    timeout=TIMEOUT,
                )
                r2.raise_for_status()
                ckan_data = r2.json()
                datasets = ckan_data.get("result", {}).get("results", [])
                resultate = [
                    {
                        "name": ds.get("title", {}).get("de", ds.get("name", "")),
                        "typ": "Datensatz",
                        "beschreibung": ds.get("notes", {}).get("de", ""),
                        "url": f"https://opendata.swiss/de/dataset/{ds.get('name', '')}",
                    }
                    for ds in datasets
                ]

            # ARCH-003: Heuristik bei leerem Resultat — schlage gezielte
            # Filter-Lockerungen vor, damit der LLM-Agent nicht einfach
            # "Keine Treffer" zurueckmeldet, sondern iteriert.
            hinweis: str | None = None
            if not resultate:
                vorschlaege = []
                if params.kanton:
                    vorschlaege.append(f"ohne Kanton-Filter (kanton={params.kanton}) suchen")
                if params.media_type != MediaType.ALLE:
                    vorschlaege.append(
                        f"alle Medientypen einschliessen (statt nur {params.media_type.value})"
                    )
                if params.query and len(params.query) > 3:
                    vorschlaege.append(f"Suchbegriff '{params.query}' kuerzen oder als Praefix")
                if not vorschlaege:
                    vorschlaege.append(
                        "Suchbegriff anpassen — Datenbank scheint leer fuer diese Anfrage"
                    )
                hinweis = "Keine Treffer. Empfehlung: " + ", oder ".join(vorschlaege) + "."

            output: dict[str, Any] = {
                "suchanfrage": {
                    "query": params.query,
                    "typ": params.media_type.value,
                    "kanton": params.kanton,
                },
                "resultate": resultate,
                "total": len(resultate),
                "datenquelle": "BAKOM RTV-Datenbank",
                "rtv_datenbank": "https://rtvdb.ofcomnet.ch/de",
            }
            if hinweis:
                output["hinweis"] = hinweis

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(output, indent=2, ensure_ascii=False)

            md = "## BAKOM RTV-Datenbank – Suchergebnisse\n"
            md += f"**Suche:** «{params.query or 'alle'}»"
            if params.kanton:
                md += f" | **Kanton:** {params.kanton}"
            if params.media_type != MediaType.ALLE:
                md += f" | **Typ:** {params.media_type.value.upper()}"
            md += f"  \n**Treffer:** {len(resultate)}\n\n"

            if not resultate:
                md += f"> **Hinweis:** {hinweis}\n"
            else:
                for r_item in resultate[: params.limit]:
                    name = r_item.get("name", "–")
                    typ = r_item.get("typ", "–")
                    kanton = r_item.get("kanton", r_item.get("canton", "–"))
                    url = r_item.get("url", "")
                    md += f"**{name}**  \n"
                    md += f"Typ: {typ} | Kanton: {kanton}"
                    if url:
                        md += f" | [Website]({url})"
                    md += "  \n\n"

            md += "**Vollständige Datenbank:** https://rtvdb.ofcomnet.ch/de"
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_medienstruktur_info",
    annotations={
        "title": "Schweizer Medienlandschaft – Strukturberichte und Statistiken",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_medienstruktur_info(params: TelekomStatInput, ctx: Context) -> str:
    """Informationen zur Schweizer Medienlandschaft aus BAKOM-Berichten.

    Gibt strukturierte Informationen zu Mediensektoren (Radio, TV, Online,
    Print) basierend auf BAKOM-Medienstrukturberichten und opendata.swiss-
    Metadaten zurück. Ideal für Medienbildung und strategische Analysen.

    Args:
        params (TelekomStatInput): Thema ('radio', 'tv', 'online',
            'print', 'medien') + Ausgabeformat.

    Returns:
        str: Strukturinformationen zur Schweizer Medienlandschaft.

    Schema:
        {
          "thema": str,
          "datensaetze": [
            {"titel": str, "beschreibung": str, "url": str, "aktualisiert": str}
          ],
          "weiterführende_links": list[str]
        }
    """
    try:
        async with _shared_client(ctx) as client:
            # Suche auf opendata.swiss nach BAKOM-Medien-Datensätzen
            r = await client.get(
                f"{OPENDATA_SWISS_API}/package_search",
                params={
                    "fq": "organization:bundesamt-fur-kommunikation-bakom",
                    "q": params.thema,
                    "rows": 10,
                    "sort": "metadata_modified desc",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            datasets = data.get("result", {}).get("results", [])

            datensaetze = []
            for ds in datasets:
                titel = ds.get("title", {})
                titel_de = titel.get("de") if isinstance(titel, dict) else str(titel)
                notes = ds.get("notes", {})
                notes_de = notes.get("de") if isinstance(notes, dict) else str(notes)
                datensaetze.append(
                    {
                        "titel": titel_de or ds.get("name", ""),
                        "beschreibung": (notes_de or "")[:200],
                        "url": f"https://opendata.swiss/de/dataset/{ds.get('name', '')}",
                        "aktualisiert": ds.get("metadata_modified", ""),
                    }
                )

            medienlinks = {
                "bakom_medienstruktur": "https://www.bakom.admin.ch/de/medien-strukturbericht",
                "bakom_rtv_db": "https://rtvdb.ofcomnet.ch/de",
                "srg_initiative": "https://www.bakom.admin.ch/de/volksabstimmung-zur-srg-initiative",
                "pressefoerderung": "https://www.bakom.admin.ch/de/pressefoerderung",
                "opendata_bakom": "https://opendata.swiss/de/organization/bundesamt-fur-kommunikation-bakom",
            }

            output = {
                "thema": params.thema,
                "datensaetze": datensaetze,
                "total_datensaetze": len(datensaetze),
                "weiterfuehrende_links": medienlinks,
                "datenquelle": "opendata.swiss – BAKOM",
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(output, indent=2, ensure_ascii=False)

            md = f"## Schweizer Medienlandschaft – {params.thema.title()}\n\n"
            md += f"**{len(datensaetze)} Datensätze** auf opendata.swiss gefunden.\n\n"

            for ds in datensaetze:
                md += f"### {ds['titel']}\n"
                if ds["beschreibung"]:
                    md += f"{ds['beschreibung']}...\n"
                md += f"[Datensatz]({ds['url']})\n\n"

            md += "### Weiterführende Links\n"
            for key, url in medienlinks.items():
                md += f"- [{key.replace('_', ' ').title()}]({url})\n"

            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_aktuell",
    annotations={
        "title": "Aktuelle BAKOM-Medienmitteilungen und Themen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_aktuell(params: TelekomStatInput, ctx: Context) -> str:
    """Aktuelle Themen, News und Regulierungen des BAKOM abrufen.

    Gibt aktuelle Informationen zu BAKOM-Tätigkeitsbereichen zurück:
    Telekommunikation, Frequenzvergabe, Medienregulierung, Post.
    Nützlich für strategische Lageberichte und Regulierungsmonitoring.

    Args:
        params (TelekomStatInput): Thema (z.B. 'ki', '5g', 'frequenz',
            'medien', 'post', 'breitband') + Ausgabeformat.

    Returns:
        str: Aktuelle BAKOM-Informationen mit Links.

    Schema:
        {
          "thema": str,
          "highlights": [{"titel": str, "datum": str, "url": str}],
          "regulierungskalender": list[str],
          "datenquelle": str
        }
    """
    # Statische Highlights aus dem aktuellen Wissensstand
    highlights_db: dict[str, list[dict[str, str]]] = {
        "5g": [
            {
                "titel": "Vergabe der Mobilfunkfrequenzen 2029",
                "datum": "2025-10",
                "beschreibung": "ComCom beauftragt BAKOM mit Vorbereitung der Frequenzvergabe für 800 MHz, 900 MHz, 1800 MHz, 2100 MHz und 2600 MHz (auslaufend Ende 2028).",
                "url": "https://www.bakom.admin.ch/de/vergabe-der-mobilfunkfrequenzen",
            },
            {
                "titel": "5G adaptive Antennen – Auf dem Weg zu 5G",
                "datum": "2025-04",
                "beschreibung": "Informationen zu adaptiven Antennen im 5G-Ausbau.",
                "url": "https://www.bakom.admin.ch/de/5g-de",
            },
        ],
        "ki": [
            {
                "titel": "KI-Gipfel 2027 in Genf",
                "datum": "2026-02-19",
                "beschreibung": "Die Schweiz richtet 2027 in Genf einen KI-Gipfel aus nach dem AI Impact Summit in Neu-Delhi.",
                "url": "https://www.bakom.admin.ch/de/newnsb/YZYU1gmqW9vcPFMl2VroY",
            },
        ],
        "medien": [
            {
                "titel": "Nein zur SRG-Initiative (März 2026)",
                "datum": "2026-03-09",
                "beschreibung": "61,9% Nein-Stimmen. Bundesrat beschliesst moderates Gegenprojekt zur Haushaltsentlastung.",
                "url": "https://www.bakom.admin.ch/de/volksabstimmung-zur-srg-initiative",
            },
            {
                "titel": "Medienstruktur-Bericht 2025",
                "datum": "2025-12-08",
                "beschreibung": "Analyse der Mediengattungen TV, Radio, Online und Print in der Schweiz.",
                "url": "https://www.bakom.admin.ch/de/medien-strukturbericht",
            },
            {
                "titel": "Förderung der Frühzustellung",
                "datum": "2026-02-18",
                "beschreibung": "25 Mio. CHF jährlich für vergünstigte Frühzustellung von Zeitungen/Zeitschriften (7 Jahre).",
                "url": "https://www.bakom.admin.ch/de/newnsb/wphaV8KF6y4FXxR55NIlD",
            },
        ],
        "post": [
            {
                "titel": "Presseförderung – Frühzustellung",
                "datum": "2026-02-18",
                "beschreibung": "Revision Postverordnung in Vernehmlassung – 25 Mio. CHF für Presseförderung.",
                "url": "https://www.bakom.admin.ch/de/newnsb/wphaV8KF6y4FXxR55NIlD",
            },
        ],
    }

    # Thema-Mapping
    thema_lower = params.thema.lower()
    matched_key = next((k for k in highlights_db if k in thema_lower or thema_lower in k), None)
    highlights = highlights_db.get(matched_key or "medien", [])

    # Ergänzend: opendata.swiss-Suche
    try:
        async with _shared_client(ctx) as client:
            r = await client.get(
                f"{OPENDATA_SWISS_API}/package_search",
                params={
                    "fq": "organization:bundesamt-fur-kommunikation-bakom",
                    "q": params.thema,
                    "rows": 5,
                    "sort": "metadata_modified desc",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            datasets = r.json().get("result", {}).get("results", [])
            for ds in datasets:
                titel = ds.get("title", {})
                titel_de = titel.get("de") if isinstance(titel, dict) else str(titel)
                highlights.append(
                    {
                        "titel": f"[Datensatz] {titel_de}",
                        "datum": ds.get("metadata_modified", "")[:10],
                        "beschreibung": "",
                        "url": f"https://opendata.swiss/de/dataset/{ds.get('name', '')}",
                    }
                )
    except Exception:
        pass

    output = {
        "thema": params.thema,
        "highlights": highlights,
        "total": len(highlights),
        "bakom_homepage": "https://www.bakom.admin.ch/de",
        "opendata_swiss_bakom": "https://opendata.swiss/de/organization/bundesamt-fur-kommunikation-bakom",
        "datenquelle": "BAKOM + opendata.swiss",
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(output, indent=2, ensure_ascii=False)

    md = f"## BAKOM Aktuell – {params.thema.title()}\n\n"
    md += f"**{len(highlights)} Einträge** gefunden.\n\n"

    for h in highlights:
        md += f"### {h.get('titel', 'Thema')}\n"
        if h.get("datum"):
            md += f"*{h['datum']}*  \n"
        if h.get("beschreibung"):
            md += f"{h['beschreibung']}  \n"
        if h.get("url"):
            md += f"[Mehr erfahren]({h['url']})\n"
        md += "\n"

    md += "**BAKOM:** https://www.bakom.admin.ch/de  \n"
    md += "**Open Data:** https://opendata.swiss/de/organization/bundesamt-fur-kommunikation-bakom"
    return md + ATTRIBUTION_FOOTER_MD


# ===========================================================================
# KATEGORIE 4: TELEKOMMUNIKATIONSSTATISTIK
# ===========================================================================


@mcp.tool(
    name="bakom_telekomstatistik_uebersicht",
    annotations={
        "title": "Schweizer Telekommunikationsstatistik – Übersicht",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_telekomstatistik_uebersicht(params: TelekomStatInput, ctx: Context) -> str:
    """Schweizer Telekommunikationsstatistiken aus BAKOM-Datensätzen abrufen.

    Gibt Übersichten zu Telekommunikationsstatistiken (Festnetz, Mobilfunk,
    Breitband, Marktanteile) via opendata.swiss CKAN API zurück.
    Nützlich für Marktanalysen, politische Berichte und KI-Fachgruppe-Demos.

    Args:
        params (TelekomStatInput): Thema ('breitband', 'mobilfunk',
            'festnetz', 'marktanteile', 'haushaltszugang') + Format.

    Returns:
        str: Verfügbare Statistikdatensätze mit Downloadlinks.

    Schema:
        {
          "thema": str,
          "datensaetze": [
            {
              "titel": str,
              "beschreibung": str,
              "url": str,
              "ressourcen": list[dict]
            }
          ]
        }
    """
    try:
        async with _shared_client(ctx) as client:
            r = await client.get(
                f"{OPENDATA_SWISS_API}/package_search",
                params={
                    "fq": "organization:bundesamt-fur-kommunikation-bakom",
                    "q": params.thema,
                    "rows": 10,
                    "sort": "score desc, metadata_modified desc",
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            datasets = data.get("result", {}).get("results", [])
            total = data.get("result", {}).get("count", 0)

            datensaetze = []
            for ds in datasets:
                titel = ds.get("title", {})
                titel_de = titel.get("de") if isinstance(titel, dict) else str(titel)
                notes = ds.get("notes", {})
                notes_de = notes.get("de") if isinstance(notes, dict) else str(notes)

                # Ressourcen-URLs extrahieren
                ressourcen = []
                for res in ds.get("resources", [])[:3]:
                    ressourcen.append(
                        {
                            "format": res.get("format", ""),
                            "name": res.get("name", {}).get("de")
                            if isinstance(res.get("name"), dict)
                            else str(res.get("name", "")),
                            "url": res.get("url", ""),
                        }
                    )

                datensaetze.append(
                    {
                        "titel": titel_de or ds.get("name", ""),
                        "beschreibung": (notes_de or "")[:300],
                        "url": f"https://opendata.swiss/de/dataset/{ds.get('name', '')}",
                        "organisation": "BAKOM",
                        "ressourcen": ressourcen,
                    }
                )

            output = {
                "thema": params.thema,
                "datensaetze": datensaetze,
                "total_auf_opendata_swiss": total,
                "datenquelle": "opendata.swiss – BAKOM",
                "bakom_statistik": "https://www.bakom.admin.ch/de/telekommunikation/zahlen-und-fakten",
            }

            if params.response_format == ResponseFormat.JSON:
                return json.dumps(output, indent=2, ensure_ascii=False)

            md = f"## BAKOM Telekommunikationsstatistik – {params.thema.title()}\n\n"
            md += f"**{total} Datensätze** auf opendata.swiss (zeige {len(datensaetze)}).\n\n"

            for ds in datensaetze:
                md += f"### {ds['titel']}\n"
                if ds["beschreibung"]:
                    md += f"{ds['beschreibung']}...\n\n"
                if ds["ressourcen"]:
                    md += "**Downloads:**\n"
                    for res in ds["ressourcen"]:
                        fmt = res.get("format", "").upper()
                        url = res.get("url", "")
                        name = res.get("name", "Datei")
                        if url:
                            md += f"- [{fmt} – {name}]({url})\n"
                md += f"[Zum Datensatz]({ds['url']})\n\n"

            md += "**Weitere Statistiken:** https://www.bakom.admin.ch/de/telekommunikation/zahlen-und-fakten"
            return md + ATTRIBUTION_FOOTER_MD

    except Exception as e:
        _raise_api_error(e)


@mcp.tool(
    name="bakom_breitbandatlas_datensaetze",
    annotations={
        "title": "Alle Breitbandatlas-Datensätze auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_log_tool_call
async def bakom_breitbandatlas_datensaetze(params: TelekomStatInput) -> str:
    """Alle verfügbaren BAKOM Breitbandatlas-Datensätze auf opendata.swiss auflisten.

    Gibt eine vollständige Übersicht aller Datensätze des BAKOM-Breitbandatlas
    zurück – Festnetz, Mobilfunk, Glasfaser, verschiedene Geschwindigkeitsstufen.
    Nützlich für Datenauswahl vor dem Download oder der API-Abfrage.

    Args:
        params (TelekomStatInput): Thema (z.B. 'breitband') + Format.

    Returns:
        str: Katalog der Breitbandatlas-Datensätze mit Layer-IDs.

    Schema:
        {
          "datensaetze": [
            {"titel": str, "layer_id": str, "url": str, "kategorie": str}
          ]
        }
    """
    # Statischer Katalog der bekannten BAKOM-Breitbandatlas-Datensätze
    katalog = [
        {
            "titel": "5G-NR-Verfügbarkeit",
            "layer_id": "ch.bakom.netzabdeckung-5g",
            "kategorie": "Mobilfunk",
            "url": "https://opendata.swiss/de/dataset/5g-nr-verfugbarkeit",
            "aufloesung": "100×100 m",
        },
        {
            "titel": "4G-LTE/LTE-A-Verfügbarkeit",
            "layer_id": "ch.bakom.netzabdeckung-4g",
            "kategorie": "Mobilfunk",
            "url": "https://opendata.swiss/de/dataset/4g-lte-lte-a-verfugbarkeit",
            "aufloesung": "100×100 m",
        },
        {
            "titel": "3G-UMTS/HSPA-Verfügbarkeit",
            "layer_id": "ch.bakom.netzabdeckung-3g",
            "kategorie": "Mobilfunk",
            "url": "https://opendata.swiss/de/dataset/3g-umts-hspa-verfugbarkeit",
            "aufloesung": "100×100 m",
        },
        {
            "titel": "Festnetz ≥30 Mbit/s",
            "layer_id": "ch.bakom.verfuegbarkeit-einzelner-technologien_30",
            "kategorie": "Festnetz",
            "url": "https://opendata.swiss/de/dataset/internet-verfugbarkeit-via-festnetz-download-geschwindigkeit-30-mbit-s",
            "aufloesung": "250×250 m",
        },
        {
            "titel": "Festnetz ≥100 Mbit/s",
            "layer_id": "ch.bakom.verfuegbarkeit-einzelner-technologien_100",
            "kategorie": "Festnetz",
            "url": "https://opendata.swiss/de/dataset/internet-verfugbarkeit-via-festnetz-download-geschwindigkeit-100-mbit-s",
            "aufloesung": "250×250 m",
        },
        {
            "titel": "Festnetz ≥300 Mbit/s",
            "layer_id": "ch.bakom.verfuegbarkeit-einzelner-technologien_300",
            "kategorie": "Festnetz",
            "url": "https://opendata.swiss/de/dataset/internet-verfugbarkeit-via-festnetz-download-geschwindigkeit-300-mbit-s",
            "aufloesung": "250×250 m",
        },
        {
            "titel": "Festnetz ≥500 Mbit/s",
            "layer_id": "ch.bakom.verfuegbarkeit-einzelner-technologien_500",
            "kategorie": "Festnetz",
            "url": "https://opendata.swiss/de/dataset/internet-verfugbarkeit-via-festnetz-download-geschwindigkeit-500-mbit-s",
            "aufloesung": "250×250 m",
        },
        {
            "titel": "Festnetz ≥1000 Mbit/s (Gigabit)",
            "layer_id": "ch.bakom.verfuegbarkeit-einzelner-technologien_1000",
            "kategorie": "Festnetz",
            "url": "https://opendata.swiss/de/dataset/internet-verfugbarkeit-via-festnetz-download-geschwindigkeit-1000-mbit-s",
            "aufloesung": "250×250 m",
        },
        {
            "titel": "Glasfaser FTTB/FTTH",
            "layer_id": "ch.bakom.anschlussart-verfuegbarkeit",
            "kategorie": "Glasfaser",
            "url": "https://opendata.swiss/de/dataset/verfugbare-anschlussarten-glasfaser-fttb-ftth",
            "aufloesung": "250×250 m",
        },
        {
            "titel": "Mobilfunkanlagen (Antennenstandorte)",
            "layer_id": "ch.bakom.standorte-mobilfunkanlagen",
            "kategorie": "Infrastruktur",
            "url": "https://opendata.swiss/de/dataset/mobilfunkanlagen",
            "aufloesung": "Punktdaten",
        },
        {
            "titel": "4G Mobilfunknetze (LTE) – Antennenstandorte",
            "layer_id": "ch.bakom.standorte-mobilfunkanlagen-4g",
            "kategorie": "Infrastruktur",
            "url": "https://opendata.swiss/de/dataset/4g-mobilfunknetze-lte-antennenstandorte",
            "aufloesung": "Punktdaten",
        },
        {
            "titel": "Radio- und Fernsehsender",
            "layer_id": "ch.bakom.radio-fernsehsender",
            "kategorie": "Medien",
            "url": "https://rtvdb.ofcomnet.ch/de",
            "aufloesung": "Punktdaten",
        },
    ]

    # Optional filtern nach Thema
    thema_lower = params.thema.lower()
    if thema_lower not in ("alle", "breitband", "übersicht", "uebersicht"):
        katalog = [
            d
            for d in katalog
            if thema_lower in d["titel"].lower() or thema_lower in d["kategorie"].lower()
        ]

    output = {
        "thema": params.thema,
        "datensaetze": katalog,
        "total": len(katalog),
        "geo_admin_api": "https://api3.geo.admin.ch/rest/services/api/MapServer/identify",
        "datenquelle": "BAKOM Breitbandatlas – opendata.swiss + geo.admin.ch",
    }

    if params.response_format == ResponseFormat.JSON:
        return json.dumps(output, indent=2, ensure_ascii=False)

    md = "## BAKOM Breitbandatlas – Datensatzkatalog\n\n"

    kategorien: dict[str, list] = {}
    for ds in katalog:
        kat = ds["kategorie"]
        kategorien.setdefault(kat, []).append(ds)

    for kat, items in kategorien.items():
        md += f"### {kat}\n"
        md += "| Datensatz | Layer-ID | Auflösung |\n"
        md += "|-----------|----------|-----------|\n"
        for item in items:
            md += f"| [{item['titel']}]({item['url']}) | `{item['layer_id']}` | {item['aufloesung']} |\n"
        md += "\n"

    md += "**API:** `https://api3.geo.admin.ch/rest/services/api/MapServer/identify`  \n"
    md += "**Karte:** https://map.geo.admin.ch/"
    return md + ATTRIBUTION_FOOTER_MD


# ===========================================================================
# MCP RESOURCES
# ===========================================================================


@mcp.resource("bakom://info")
def bakom_server_info() -> str:
    """BAKOM MCP Server – Überblick über verfügbare Tools und Datenquellen."""
    return json.dumps(
        {
            "server": "bakom-mcp",
            "version": "1.0.0",
            "beschreibung": "MCP Server für BAKOM Open Data – Breitband, Mobilfunk, Medien, Telekommunikationsstatistik",
            "tools": {
                "breitband": [
                    "bakom_broadband_coverage",
                    "bakom_glasfaser_verfuegbarkeit",
                    "bakom_multi_standort_konnektivitaet",
                ],
                "mobilfunk_sendeanlagen": [
                    "bakom_mobilfunk_abdeckung",
                    "bakom_sendeanlagen_suche",
                    "bakom_frequenzdaten",
                ],
                "medien_rtv": [
                    "bakom_rtv_suche",
                    "bakom_medienstruktur_info",
                    "bakom_aktuell",
                ],
                "statistik": [
                    "bakom_telekomstatistik_uebersicht",
                    "bakom_breitbandatlas_datensaetze",
                ],
            },
            "apis": {
                "geo_admin": "https://api3.geo.admin.ch",
                "opendata_swiss": "https://ckan.opendata.swiss/api/3/action",
                "rtv_db": "https://rtvdb.ofcomnet.ch/api",
            },
            "koordinaten_format": "WGS84 (lat: 45.8–47.9, lon: 5.9–10.6)",
            "auth_erforderlich": False,
            "lizenz": "Open Government Data (CC0 / OGD)",
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.resource("bakom://demo-standorte")
def bakom_demo_standorte() -> str:
    """Demo-Koordinaten für häufig genutzte Schweizer Standorte."""
    return json.dumps(
        {
            "zuerich_zentrum": {"lat": 47.3769, "lon": 8.5417, "beschreibung": "Zürich HB"},
            "schulhaus_leutschenbach": {
                "lat": 47.4148,
                "lon": 8.5654,
                "beschreibung": "Schulhaus Leutschenbach, Zürich",
            },
            "bern_bundeshaus": {"lat": 46.9467, "lon": 7.4444, "beschreibung": "Bundeshaus Bern"},
            "genf_cern": {"lat": 46.2330, "lon": 6.0560, "beschreibung": "CERN Genf"},
            "basel_messe": {"lat": 47.5596, "lon": 7.5886, "beschreibung": "Messe Basel"},
            "luzern_bahnhof": {"lat": 47.0505, "lon": 8.3099, "beschreibung": "Bahnhof Luzern"},
            "st_gallen_uni": {
                "lat": 47.4242,
                "lon": 9.3728,
                "beschreibung": "Universität St. Gallen",
            },
            "zuerich_waedenswil": {"lat": 47.2254, "lon": 8.6697, "beschreibung": "Wädenswil"},
        },
        indent=2,
        ensure_ascii=False,
    )


# ===========================================================================
# PROMPTS — wiederverwendbare LLM-Templates für häufige BAKOM-Use-Cases
# ===========================================================================


@mcp.prompt(
    name="schulhaus_konnektivitaet",
    title="Schulhaus-Konnektivität analysieren",
    description=(
        "Anchor-Demo des Servers: prüft Glasfaser- und 5G-Status mehrerer "
        "Schulhäuser in einer Gemeinde / einem Schulkreis und liefert eine "
        "priorisierte Ausbau-Empfehlung."
    ),
)
def prompt_schulhaus_konnektivitaet(
    gemeinde: str = "Zürich",
    schulkreis: str = "Kreis 7",
) -> str:
    """Anchor-Demo: Schulhäuser-Glasfaser-Vergleich."""
    return (
        f"Untersuche die Konnektivität (Glasfaser FTTH/FTTB sowie 5G-Outdoor) "
        f"der öffentlichen Schulhäuser in {gemeinde} ({schulkreis}).\n\n"
        "1. Identifiziere die Schulhäuser im genannten Schulkreis (nutze "
        "öffentliche Quellen, falls keine Liste vorgegeben ist).\n"
        "2. Rufe `bakom_multi_standort_konnektivitaet` mit den WGS84-Koordinaten "
        "auf — bis zu 20 Standorte pro Aufruf.\n"
        "3. Erstelle eine Tabelle: Schulname | Glasfaser-Status | 5G-Versorgung | "
        "Empfehlung.\n"
        "4. Priorisiere Schulhäuser ohne FTTH für den Glasfaser-Ausbau.\n"
        "5. Verweise im Footer auf die Quelle (BAKOM via opendata.swiss / "
        "geo.admin.ch, Lizenz CC BY 4.0)."
    )


@mcp.prompt(
    name="rtv_kanton_uebersicht",
    title="RTV-Veranstalter pro Kanton",
    description=(
        "Listet konzessionierte und gemeldete Radio- und TV-Veranstalter "
        "in einem Schweizer Kanton aus der BAKOM RTV-Datenbank."
    ),
)
def prompt_rtv_kanton_uebersicht(
    kanton: str = "ZH",
    medientyp: str = "alle",
) -> str:
    """Übersicht der Konzessionsträger pro Kanton."""
    return (
        f"Erstelle eine Übersicht der konzessionierten Radio- und TV-Veranstalter "
        f"im Kanton {kanton.upper()}.\n\n"
        f"1. Rufe `bakom_rtv_suche` mit `kanton='{kanton.upper()}'` und "
        f"`media_type='{medientyp}'` auf.\n"
        "2. Gruppiere die Ergebnisse nach Medientyp (Radio / TV).\n"
        "3. Zeige Name, Konzessionsstatus und Link auf die RTV-Datenbank in einer "
        "Tabelle.\n"
        "4. Ergänze einen Kontext-Absatz: was bedeutet «konzessioniert» vs. "
        "«gemeldet» nach Schweizer Medienrecht?\n"
        "5. Quelle und CC BY 4.0-Lizenz im Footer angeben."
    )


@mcp.prompt(
    name="standort_konnektivitaet_vergleich",
    title="Konnektivitätsvergleich mehrerer Standorte",
    description=(
        "Allgemeine Variante des Anchor-Demos: vergleicht beliebige Standorte "
        "auf Breitband- und Mobilfunkversorgung mit strukturierter Empfehlung."
    ),
)
def prompt_standort_konnektivitaet_vergleich(
    standorte_beschreibung: str = "Liste der zu vergleichenden Standorte (Name + Adresse)",
    fokus: str = "Glasfaser und 5G",
) -> str:
    """Generischer Standort-Vergleich für Verwaltungen, Immobilien, Standortwahl."""
    return (
        f"Vergleiche die Konnektivität ({fokus}) der folgenden Standorte:\n\n"
        f"{standorte_beschreibung}\n\n"
        "Vorgehen:\n"
        "1. Bestimme die WGS84-Koordinaten (lat/lon) jedes Standorts; falls nur "
        "Adressen vorliegen, geocodiere sie zuerst.\n"
        "2. Rufe `bakom_multi_standort_konnektivitaet` (max. 20 Standorte) mit "
        "`response_format='json'` auf — strukturiert ist besser für die Tabelle.\n"
        "3. Bei mehr als 20 Standorten: in Batches aufrufen.\n"
        "4. Erstelle eine Tabelle: Standort | 5G | Glasfaser | Empfehlung.\n"
        "5. Falls Ergebnisse fehlen oder Koordinaten ausserhalb der Schweiz "
        "liegen, zeige das transparent als 'n/a'.\n"
        "6. Schliesse mit einer kurzen Empfehlung pro Standort und der Quellen-"
        "Attribution (BAKOM via opendata.swiss / geo.admin.ch, CC BY 4.0)."
    )


# ===========================================================================
# ENTRY POINT
# ===========================================================================
if __name__ == "__main__":
    import os
    import sys

    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    if transport == "streamable-http":
        import uvicorn
        from starlette.middleware.cors import CORSMiddleware

        host = os.environ.get("BAKOM_MCP_HOST", "127.0.0.1")
        port = int(os.environ.get("BAKOM_MCP_PORT", "8050"))
        cors_env = os.environ.get("BAKOM_MCP_CORS_ORIGINS", "").strip()
        cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()]

        if host == "0.0.0.0":  # noqa: S104
            print(
                "WARNUNG: Server bindet auf 0.0.0.0 (alle Interfaces). "
                "Ohne Auth nur in vertrauenswürdigen Netzen sicher.",
                file=sys.stderr,
            )

        app = mcp.streamable_http_app()
        if cors_origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["Mcp-Session-Id"],
            )
            print(
                f"CORS aktiv für Origins: {', '.join(cors_origins)} "
                "(expose_headers=Mcp-Session-Id)",
                file=sys.stderr,
            )
        else:
            print(
                "CORS deaktiviert. Für Browser-Clients setze "
                "BAKOM_MCP_CORS_ORIGINS=https://example.com,https://other.com",
                file=sys.stderr,
            )

        print(f"BAKOM MCP Server läuft auf http://{host}:{port}/mcp", file=sys.stderr)
        uvicorn.run(app, host=host, port=port, log_level="info")
    else:
        mcp.run()
