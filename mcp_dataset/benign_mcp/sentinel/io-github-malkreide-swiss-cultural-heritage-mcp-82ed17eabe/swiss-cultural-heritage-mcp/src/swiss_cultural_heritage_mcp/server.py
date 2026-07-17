#!/usr/bin/env python3
"""
Swiss Cultural Heritage MCP Server

AI-nativer Zugang zu drei Schweizer Kulturerbe-Quellen:
  · SIK-ISEA:          SIKART-Künstlerdaten (~17'000) via opendata.swiss CKAN DataStore
  · Nationalmuseum:    Sammlungsdaten via opendata.swiss CKAN API
  · Nationalbibliothek: Helveticat (Schweizerische Nationalbibliografie) via OAI-PMH

Kein API-Schlüssel erforderlich. Alle Daten öffentlich zugänglich unter offenen Lizenzen.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, contextmanager
from enum import StrEnum
from typing import Any, Final, Literal, NoReturn, TypeVar

import httpx
import structlog
from defusedxml import ElementTree as ET
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─────────────────────────── Konfiguration (ARCH-004) ──────────────────────────
# Einziger Konfig-Ladepunkt: alle Endpunkte, Timeouts, die Egress-Allow-List sowie
# Host/Port/Transport/Log-Level kommen aus diesem Settings-Objekt (statt aus frei
# verstreuten Modul-Globals). Jedes Feld ist per Umgebungsvariable mit Präfix
# ``MCP_`` überschreibbar (z. B. ``MCP_HTTP_TIMEOUT=10``), ohne Code zu ändern.
class Settings(BaseSettings):
    """Zentrale, env-überschreibbare Server-Konfiguration (Präfix ``MCP_``)."""
    model_config = SettingsConfigDict(env_prefix="MCP_", extra="ignore")

    # Upstream-Endpunkte / Ressourcen
    ckan_api:           str = "https://ckan.opendata.swiss/api/3/action"
    snm_org:            str = "schweizerisches-nationalmuseum"
    sikart_resource_id: str = "ef3a9fd2-2fb3-49ee-bfba-75d58e40b2ea"
    nb_oai_pmh:         str = "https://helveticat.nb.admin.ch/view/oai/41SNL_51_INST/request"

    # HTTP-Verhalten
    http_timeout:  float = 30.0
    default_limit: int = 20
    max_limit:     int = 100
    max_redirects: int = 5

    # Egress-Allow-List (SEC-021)
    allowed_hosts: frozenset[str] = frozenset({
        "ckan.opendata.swiss",
        "helveticat.nb.admin.ch",
    })

    # Transport / Netzwerk
    transport:    Literal["stdio", "http"] = "stdio"
    host:         str = "127.0.0.1"   # SEC-016: loopback-Default; Container setzt 0.0.0.0
    port:         int = 8000
    cors_origins: str = ""            # komma-separiert; leer = keine Cross-Origin-Freigabe
    log_level:    str = "INFO"


settings = Settings()


# ─────────────────────────── Structured Logging (OBS-003) ──────────────────────
def _configure_logging(stream=sys.stderr, level: int | None = None) -> None:
    """Strukturiertes JSON-Logging nach stderr (OBS-003).

    JSON-Logs gehen ausschliesslich nach stderr; stdout bleibt für das
    MCP-Protokoll (stdio-Transport) reserviert (OBS-004). Bewusst werden *keine*
    Payloads/PII geloggt — nur Tool-Name, Request-ID, Fehlerklasse und HTTP-Status.
    Das Log-Level steuert ``MCP_LOG_LEVEL`` (debug/info/warning/error/critical).
    """
    if level is None:
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.WriteLoggerFactory(file=stream),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


_configure_logging()
log = structlog.get_logger("swiss_cultural_heritage_mcp")


# ─────────────────────────── Distributed Tracing (OBS-006) ─────────────────────
# OpenTelemetry ist ein *optionales* Extra (`pip install '...[otel]'`) und wird
# nur aktiv, wenn ``OTEL_EXPORTER_OTLP_ENDPOINT`` gesetzt ist. Ohne Endpoint (z. B.
# stdio/lokal) bleibt Tracing komplett aus — kein Overhead, keine Pflichtabhängig-
# keit. ``_otel_span`` ist entweder ``tracer.start_as_current_span`` oder ``None``.
_otel_span = None


def _init_tracing(*, exporter=None) -> bool:
    """Aktiviert OpenTelemetry-Tracing (OBS-006); gated über Env-Var.

    Setzt einen Span pro Tool-Call (siehe ``mask_unexpected_errors``) und
    instrumentiert httpx automatisch, sodass jede Upstream-Anfrage (SIKART/SNM/NB)
    als Child-Span erscheint. Es werden keine sensiblen Daten als Attribute
    gesetzt — nur Tool-Name und ``is_error``. Fehlen die OTel-Pakete, wird eine
    Warnung geloggt und ohne Tracing weitergemacht.
    """
    global _otel_span
    if exporter is None and not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
    except ImportError:
        log.warning(
            "otel.unavailable",
            reason="opentelemetry nicht installiert — `pip install '.[otel]'`",
        )
        return False

    try:
        from importlib.metadata import version as _pkg_version
        svc_version = _pkg_version("swiss-cultural-heritage-mcp")
    except Exception:
        svc_version = "0.0.0+local"

    resource = Resource.create({
        "service.name":           "swiss-cultural-heritage-mcp",
        "service.version":        svc_version,
        "deployment.environment": os.getenv("DEPLOYMENT_ENV", "production"),
    })
    provider = TracerProvider(resource=resource)
    if exporter is None:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    else:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    HTTPXClientInstrumentor().instrument()
    _otel_span = trace.get_tracer("swiss_cultural_heritage_mcp").start_as_current_span
    log.info("otel.enabled")
    return True


@contextmanager
def _tool_span(name: str):
    """Span pro Tool-Call (no-op, solange Tracing nicht aktiv ist)."""
    if _otel_span is None:
        yield None
        return
    with _otel_span(f"mcp.tool.{name}") as span:
        span.set_attribute("mcp.tool.name", name)
        yield span


def _is_error_result(result: object) -> bool:
    """True, wenn ein Tool eine (behandelte) Fehlermeldung als Text zurückgibt."""
    return isinstance(result, str) and result.startswith("Fehler")


# Beim Import aktivieren — no-op, solange OTEL_EXPORTER_OTLP_ENDPOINT nicht gesetzt ist.
_init_tracing()

# ─────────────────────────── Konstanten (aus Settings abgeleitet) ──────────────
# Modulweite Aliase für die Konfigwerte — Quelle der Wahrheit ist ``settings``
# (ARCH-004); diese Namen bleiben für Tools, Tests und Importeure stabil.
CKAN_API           = settings.ckan_api
SNM_ORG            = settings.snm_org
SIKART_RESOURCE_ID = settings.sikart_resource_id
NB_OAI_PMH         = settings.nb_oai_pmh

HTTP_TIMEOUT  = settings.http_timeout
DEFAULT_LIMIT = settings.default_limit
MAX_LIMIT     = settings.max_limit
MAX_REDIRECTS = settings.max_redirects

# Egress-Allow-List (SEC-021): nur diese Hosts dürfen kontaktiert werden.
ALLOWED_HOSTS: Final[frozenset[str]] = settings.allowed_hosts

# OAI-PMH XML-Namespaces
OAI_NS = {
    "oai":    "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc":     "http://purl.org/dc/elements/1.1/",
}


# ─────────────────────────── HTTP-Client-Lifecycle (SDK-001) ───────────────────
# Genau ein httpx.AsyncClient pro Serverprozess. Der Lifespan erzeugt/schliesst
# ihn; ausserhalb des Lifespans (z. B. in Unit-Tests) wird lazy initialisiert.
_http_client: httpx.AsyncClient | None = None


def _new_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=False)


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = _new_client()
    return _http_client


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[None]:
    """Erzeugt einen geteilten httpx-Client für die Lebensdauer des Servers."""
    global _http_client
    _http_client = _new_client()
    try:
        yield
    finally:
        client, _http_client = _http_client, None
        if client is not None:
            await client.aclose()


# ─────────────────────────── Server ────────────────────────────────────────────
mcp = FastMCP("swiss_cultural_heritage_mcp", lifespan=lifespan)


# ─────────────────────────── Fehler-Maskierung (OBS-002) ───────────────────────
# Die offizielle mcp-SDK (mcp.server.fastmcp) kennt kein `mask_error_details`-Flag
# (das gibt es nur im eigenständigen `fastmcp`-Paket). Stattdessen verpackt sie
# jede Tool-Exception als ``ToolError(f"Error executing tool {name}: {e}")`` und
# leitet den Original-Text an den Client/das LLM weiter.
#
# Erwartete Upstream-Fehler fangen die Tools selbst ab und geben saubere Meldungen
# zurück (siehe ``_handle_error``). Programmierfehler sollen weiterhin als Fehler-
# Ergebnis propagieren (OBS-001) — aber mit einer generischen, internen-frei
# maskierten Meldung. Der vollständige Stacktrace landet nur im Server-Log (stderr).
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _request_log_context(tool: str) -> dict[str, str]:
    """Pro-Aufruf-Kontext fürs Logging (OBS-003): Tool-Name + Request-ID.

    Die Request-ID wird best-effort aus dem MCP-Request gezogen; bei direkten
    Aufrufen ausserhalb eines Requests (z. B. Tests) fehlt sie einfach.
    """
    data = {"tool": tool}
    try:
        data["request_id"] = str(mcp.get_context().request_context.request_id)
    except Exception:
        pass
    return data


def mask_unexpected_errors(fn: F) -> F:
    """Maskiert unerwartete Exceptions: Detail ins Server-Log, generisch an den Client."""
    name = getattr(fn, "__name__", "?")

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        bound = log.bind(tool=name)
        # contextvars sorgen dafür, dass auch tief im Tool-Body emittierte Logs
        # (z. B. aus _handle_error) Tool-Name + Request-ID mittragen.
        with structlog.contextvars.bound_contextvars(**_request_log_context(name)), \
                _tool_span(name) as span:
            bound.info("tool.call")
            try:
                result = await fn(*args, **kwargs)
            except ToolError:
                if span is not None:
                    span.set_attribute("mcp.tool.is_error", True)
                raise
            except Exception as e:
                if span is not None:
                    span.set_attribute("mcp.tool.is_error", True)
                    span.set_attribute("error.type", type(e).__name__)
                bound.error("tool.unexpected_error", error_type=type(e).__name__, exc_info=True)
                raise ToolError(
                    "Interner Fehler bei der Tool-Ausführung. "
                    "Details wurden serverseitig protokolliert."
                ) from None
            if span is not None:
                span.set_attribute("mcp.tool.is_error", _is_error_result(result))
            return result

    return wrapper  # type: ignore[return-value]


# ─────────────────────────── Enum ──────────────────────────────────────────────
class ResponseFormat(StrEnum):
    """Ausgabeformat für Tool-Antworten."""
    MARKDOWN = "markdown"
    JSON     = "json"


# ─────────────────────────── Response-Envelope (SDK-002) ───────────────────────
# Konsistenter, typisierter Envelope für alle Such-/Listen-Tools. Im JSON-Modus
# geben die Tools dieses Modell zurück — das offizielle mcp-SDK erzeugt daraus
# echten *structured output* inkl. ``outputSchema``. Im Markdown-Modus rendern die
# Tools eine menschenlesbare Ansicht über denselben Daten (``str``). Der
# Rückgabetyp ist deshalb ``ResultEnvelope | str``.
class SourceInfo(BaseModel):
    """Provenienz und Lizenz einer Datenquelle."""
    name:    str
    license: str
    url:     str | None = None


class ResultEnvelope(BaseModel):
    """Einheitlicher Response-Envelope für Such-/Listen-Tools."""
    source:   SourceInfo | list[SourceInfo] = Field(description="Quelle(n) inkl. Lizenz")
    count:    int = Field(description="Anzahl zurückgegebener Einträge")
    total:    int | None = Field(default=None, description="Gesamtzahl upstream verfügbar")
    offset:   int | None = Field(default=None, description="Paginierungs-Offset")
    has_more: bool = Field(default=False, description="Weitere Ergebnisse verfügbar")
    match_type: Literal["exact", "fuzzy", "none"] = Field(
        default="exact",
        description=(
            "Trefferart (ARCH-003): 'exact' = direkte Suche, 'fuzzy' = gelockerte/"
            "erweiterte Suche nach 0 exakten Treffern, 'none' = keine Treffer"
        ),
    )
    results:  list[dict] = Field(default_factory=list, description="Datensätze (quellnah)")
    meta:     dict | None = Field(default=None, description="Tool-spezifische Zusatzfelder")


# Quellen-/Lizenz-Konstanten (Provenienz + Lizenz pro Datensatz, CH-004).
# Lizenzangaben spiegeln die im Projekt dokumentierten OGD-Bedingungen wider
# (vgl. heritage://*/overview-Ressourcen). Wo ein Datensatz/Record ein eigenes
# Lizenzfeld trägt (SIKART `NUTZUNGSLIZENZ`, DC `rights`), ist dieses massgeblich
# und wird in den Detailansichten zusätzlich ausgewiesen.
SOURCE_SIKART: Final = SourceInfo(
    name="SIK-ISEA / SIKART", license="CC BY", url="https://www.sik-isea.ch"
)
SOURCE_SNM: Final = SourceInfo(
    name="Schweizerisches Nationalmuseum (opendata.swiss)",
    license="CC BY / CC0 (pro Datensatz)", url="https://www.nationalmuseum.ch",
)
SOURCE_NB: Final = SourceInfo(
    name="Schweizerische Nationalbibliothek (Helveticat OAI-PMH)",
    license="offen / pro Datensatz", url="https://www.nb.admin.ch",
)


def _attribution(source: SourceInfo | list[SourceInfo]) -> str:
    """Markdown-Attributionsfooter (CH-004).

    Open-Government-Data unter CC BY verlangt die Nennung von Quelle und Lizenz.
    Dieser Footer stellt sicher, dass *jede* Antwort ihre Provenienz mitführt —
    auch dann, wenn einzelne Datensätze aus dem Kontext kopiert werden.
    """
    sources = source if isinstance(source, list) else [source]
    rows = "\n".join(
        f"- {s.name} — Lizenz: {s.license}" + (f" · <{s.url}>" if s.url else "")
        for s in sources
    )
    return f"\n\n---\n**Datenquelle & Lizenz:**\n{rows}\n"


# Markdown-Hinweis, wenn nur über eine gelockerte (fuzzy) Suche Treffer gefunden
# wurden — damit das LLM weiss, dass es sich um erweiterte und nicht um exakte
# Treffer handelt (ARCH-003).
_FUZZY_NOTE: Final = (
    "> ℹ️ *Keine exakten Treffer — Ergebnisse stammen aus einer gelockerten Suche "
    "(`match_type: fuzzy`). Bitte Relevanz prüfen.*\n"
)


def _no_match(
    source: SourceInfo, response_format: ResponseFormat, hint: str
) -> ResultEnvelope | str:
    """Null-Treffer-Antwort (ARCH-003).

    Im JSON-Modus ein strukturierter Envelope mit ``match_type='none'`` (statt
    eines blanken Strings), im Markdown-Modus der bestehende, handlungsleitende
    Hinweistext.
    """
    if response_format == ResponseFormat.JSON:
        return ResultEnvelope(source=source, count=0, total=0, results=[], match_type="none")
    return hint


# ─────────────────────────── Shared Utilities ──────────────────────────────────
# Tupel der erwarteten Upstream-Fehler. Andere Exceptions (KeyError, TypeError, …)
# sind Programmierfehler und sollen propagieren, damit sie nicht in
# Benutzer-Strings versteckt werden (OBS-001).
ExpectedUpstreamError = (
    httpx.HTTPStatusError,
    httpx.TimeoutException,
    httpx.RequestError,
    ET.ParseError,
    ValueError,
)


def _assert_allowed(url: str) -> None:
    """Egress-Guard: nur HTTPS und nur Hosts aus der statischen Allow-List.

    - SEC-021: Host muss in ``ALLOWED_HOSTS`` sein (greift via ``_http_get`` auch
      auf jedem Redirect-Hop).
    - SEC-004: zusätzlich HTTPS erzwingen (Defense-in-Depth) — blockiert u. a.
      einen Redirect-Downgrade auf ``http://`` oder ein ``file://``-Schema, selbst
      wenn der Host erlaubt wäre.
    """
    parsed = httpx.URL(url)
    if parsed.scheme != "https":
        raise ValueError(f"Nur HTTPS erlaubt, nicht: {parsed.scheme or '(leer)'}")
    if parsed.host not in ALLOWED_HOSTS:
        raise ValueError(f"Host nicht in Allow-List: {parsed.host}")


async def _http_get(url: str, params: dict | None = None) -> httpx.Response:
    """HTTP-GET über den geteilten Client, mit Egress-Allow-List.

    Redirects werden manuell verfolgt, damit die Allow-List (SEC-021) bei
    *jedem* Hop greift. Automatisches ``follow_redirects`` würde nur die
    Start-URL prüfen und so ein SSRF-Schlupfloch über einen Redirect öffnen.
    """
    _assert_allowed(url)
    client = _get_http_client()
    resp   = await client.get(url, params=params)
    for _ in range(MAX_REDIRECTS):
        if not resp.is_redirect:
            break
        location = resp.headers.get("location")
        if not location:
            break
        next_url = str(resp.url.join(location))
        _assert_allowed(next_url)
        await resp.aclose()
        resp = await client.get(next_url)
    return resp


def _handle_error(e: Exception) -> str:
    """Einheitliche, handlungsorientierte Fehlermeldungen (auf Deutsch)."""
    # Strukturierte Warnung für jeden Upstream-Fehler (OBS-003) — nur Fehlerklasse
    # und HTTP-Status, keine Payloads. Tool-Name/Request-ID kommen via contextvars.
    log.warning(
        "upstream.error",
        error_kind=type(e).__name__,
        status=getattr(getattr(e, "response", None), "status_code", None),
    )
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 404:
            return "Fehler: Ressource nicht gefunden. Bitte ID oder Parameter prüfen."
        if code == 429:
            return "Fehler: Rate-Limit erreicht. Bitte kurz warten und erneut versuchen."
        if code in (503, 502):
            return "Fehler: Dienst vorübergehend nicht verfügbar. Bitte erneut versuchen."
        return f"Fehler: API-Anfrage fehlgeschlagen (HTTP {code})."
    if isinstance(e, httpx.TimeoutException):
        return "Fehler: Zeitüberschreitung. Der Dienst antwortet nicht. Bitte erneut versuchen."
    if isinstance(e, ET.ParseError):
        return "Fehler: XML-Antwort konnte nicht verarbeitet werden. Möglicherweise vorübergehend."
    if isinstance(e, ValueError):
        return f"Fehler: {e}"
    if isinstance(e, httpx.RequestError):
        return f"Fehler: Netzwerkfehler ({type(e).__name__}): {e}"
    return f"Fehler: Unerwarteter Fehler ({type(e).__name__}): {e}"


def _raise_tool_error(e: Exception) -> NoReturn:
    """Behandelten Upstream-Fehler als *isError*-Tool-Ergebnis melden (OBS-001).

    ``_handle_error`` baut die handlungsorientierte deutsche Meldung (und loggt
    strukturiert); diese wird als ``ToolError`` geworfen. ``mask_unexpected_errors``
    reicht ``ToolError`` unverändert durch, und das MCP-SDK verpackt sie in ein
    ``CallToolResult`` mit ``isError: true`` — so unterscheidet der Client einen
    Fehler von einem normalen (leeren) Ergebnis, statt eine «Fehler: …»-Zeichen-
    kette wie Inhalt zu lesen.
    """
    raise ToolError(_handle_error(e))


def _parse_oai_records(xml_text: str) -> list[dict]:
    """Parsed OAI-PMH ListRecords/GetRecord-Antwort in eine Liste von Dicts."""
    root = ET.fromstring(xml_text)
    records = []
    for record in root.findall(".//oai:record", OAI_NS):
        header = record.find("oai:header", OAI_NS)
        if header is not None and header.get("status") == "deleted":
            continue
        identifier_el = record.find("oai:header/oai:identifier", OAI_NS)
        datestamp_el  = record.find("oai:header/oai:datestamp",  OAI_NS)
        metadata_el   = record.find("oai:metadata/oai_dc:dc",    OAI_NS)

        rec: dict = {
            "oai_identifier": identifier_el.text if identifier_el is not None else "",
            "datestamp":      datestamp_el.text  if datestamp_el  is not None else "",
        }

        if metadata_el is not None:
            for child in metadata_el:
                tag = child.tag.split("}")[-1]  # Namespace entfernen
                val = (child.text or "").strip()
                if not val:
                    continue
                if tag in rec:
                    existing = rec[tag]
                    if isinstance(existing, list):
                        existing.append(val)
                    else:
                        rec[tag] = [existing, val]
                else:
                    rec[tag] = val

        records.append(rec)
    return records


def _extract_resumption_token(xml_text: str) -> str | None:
    """Extrahiert OAI-PMH Resumption Token für Paginierung."""
    root    = ET.fromstring(xml_text)
    token_el = root.find(".//oai:resumptionToken", OAI_NS)
    if token_el is not None and token_el.text and token_el.text.strip():
        return token_el.text.strip()
    return None


def _normalize_ckan_title(title) -> str:
    """Normalisiert CKAN-Titel (dict mit Sprachschlüsseln oder String)."""
    if isinstance(title, dict):
        return title.get("de") or title.get("fr") or title.get("en") or next(iter(title.values()), "—")
    return str(title) if title else "—"


# ══════════════════════════════════════════════════════════════════════════════
#  MODUL 1 — SIK-ISEA / SIKART  (Schweizerisches Institut für Kunstwissenschaft)
# ══════════════════════════════════════════════════════════════════════════════
# Datenquelle: SIKART-Künstlerdaten (~17'000 Einträge) als DataStore-Ressource
# auf opendata.swiss. Abfrage über die CKAN-DataStore-API (datastore_search) mit
# serverseitiger Volltextsuche und Paginierung.


def _artist_full_name(rec: dict) -> str:
    """Setzt Vor- und Nachname eines SIKART-Records zusammen."""
    name    = (rec.get("NAME") or "").strip()
    vorname = (rec.get("VORNAME") or "").strip()
    full    = f"{vorname} {name}".strip()
    return full or (rec.get("NAMIDENT") or "").strip() or "(Unbekannt)"


def _artist_lifespan(rec: dict) -> str:
    """Liefert eine Lebensdaten-Zeile aus einem SIKART-Record."""
    lebensdaten = (rec.get("LEBENSDATEN") or "").strip()
    if lebensdaten:
        return lebensdaten
    birth = (rec.get("GEBURTSJAHR") or "").strip()
    death = (rec.get("STERBEJAHR") or "").strip()
    if birth or death:
        return f"{birth or '?'}–{death or '?'}"
    return ""


class ArtistSearchInput(BaseModel):
    """Input für die SIKART-Künstler·innen-Suche."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    query:  str | None = Field(
        default=None, max_length=200,
        description="Name, Beruf oder Stichwort (z. B. 'Hodler', 'Bildhauer', 'Taeuber-Arp')"
    )
    region: str | None = Field(
        default=None, max_length=100,
        description="Geburts-/Sterbeort oder Kanton (z. B. 'Basel', 'Genf', 'BE', 'Zürich')"
    )
    limit:  int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max. Ergebnisse (1–100)")
    offset: int = Field(default=0, ge=0, description="Offset für Paginierung")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)

    @field_validator("query", "region")
    @classmethod
    def not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Darf nicht leer sein.")
        return v


@mcp.tool(
    name="heritage_search_artists",
    annotations={
        "title": "Schweizer Künstler·innen suchen (SIKART)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_search_artists(params: ArtistSearchInput) -> ResultEnvelope | str:
    """Sucht Schweizer Künstler·innen in den SIKART-Daten (~17'000 Einträge).

    SIKART (Lexikon zur Kunst in der Schweiz, herausgegeben vom Schweizerischen
    Institut für Kunstwissenschaft SIK-ISEA) dokumentiert historische und
    zeitgenössische Kunstschaffende mit biografischen Grunddaten. Die Suche läuft
    als CKAN-DataStore-Volltextsuche über alle Felder; mehrere Begriffe werden
    UND-verknüpft. Liefert die exakte Suche keine Treffer, wird automatisch
    breiter mit dem spezifischsten Begriff gesucht und das Resultat als
    `match_type: fuzzy` markiert (ARCH-003); bleibt es leer, `match_type: none`.

    Args:
        params (ArtistSearchInput):
            - query (str | None):  Name, Beruf oder Stichwort (z. B. 'Hodler')
            - region (str | None): Geburts-/Sterbeort oder Kanton (z. B. 'Basel')
            - limit (int):         Max. Ergebnisse (Standard: 20)
            - offset (int):        Paginierungs-Offset
            - response_format:     'markdown' oder 'json'

    Returns:
        str: Liste gefundener Künstler·innen mit Name, Lebensdaten, Kanton, Kurzbiografie.
    """
    try:
        async def _query(q: str | None) -> tuple[list[dict], int]:
            api_params: dict = {
                "resource_id": SIKART_RESOURCE_ID,
                "limit":       params.limit,
                "offset":      params.offset,
            }
            if q:
                api_params["q"] = q
            resp = await _http_get(f"{CKAN_API}/datastore_search", params=api_params)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise ValueError("CKAN-DataStore-Anfrage fehlgeschlagen.")
            res  = data.get("result", {})
            recs = res.get("records", [])
            return recs, res.get("total", len(recs))

        q_terms = [t for t in (params.query, params.region) if t]
        records, total = await _query(" ".join(q_terms) if q_terms else None)
        match_type: Literal["exact", "fuzzy", "none"] = "exact"

        # Fuzzy-Retry (ARCH-003): bei 0 Treffern und mehreren Begriffen breiter
        # mit dem spezifischsten (längsten) Begriff suchen.
        if not records and len(q_terms) >= 2:
            records, total = await _query(max(q_terms, key=len))
            if records:
                match_type = "fuzzy"

        if not records:
            return _no_match(
                SOURCE_SIKART, params.response_format,
                "Keine Künstler·innen gefunden für die angegebenen Suchkriterien.",
            )

        if params.response_format == ResponseFormat.JSON:
            return ResultEnvelope(
                source=SOURCE_SIKART,
                count=len(records),
                total=total,
                offset=params.offset,
                has_more=(params.offset + len(records)) < total,
                results=records,
                match_type=match_type,
            )

        filters = []
        if params.query:
            filters.append(f"Stichwort: *{params.query}*")
        if params.region:
            filters.append(f"Ort/Kanton: *{params.region}*")

        lines = ["# SIKART — Schweizer Künstler·innen-Suche\n"]
        if filters:
            lines.append("**Filter:** " + " · ".join(filters))
        if match_type == "fuzzy":
            lines.append(_FUZZY_NOTE)
        lines.append(f"\nGefunden: {total} Einträge (zeige {len(records)})\n")
        lines.append("---\n")

        for rec in records:
            lines.append(f"## {_artist_full_name(rec)}")
            meta: list = []
            lifespan_line = _artist_lifespan(rec)
            if lifespan_line:
                meta.append(f"**Lebensdaten:** {lifespan_line}")
            canton = (rec.get("GEBURTSKANTON") or rec.get("STERBEKANTON") or "").strip()
            if canton:
                meta.append(f"**Kanton:** {canton}")
            meta.append(f"**SIKART-ID:** `{rec.get('HAUPTNR', '—')}`")
            lines.append("  ·  ".join(meta))
            vita = (rec.get("VITAZEILE") or "").strip()
            if vita:
                lines.append(f"*{vita}*")
            link = (rec.get("SIKART_LINK") or "").strip()
            if link:
                lines.append(f"[SIKART-Eintrag]({link})")
            lines.append("")

        if (params.offset + len(records)) < total:
            lines.append(f"*Weitere Ergebnisse ab Offset {params.offset + len(records)}*")

        return "\n".join(lines) + _attribution(SOURCE_SIKART)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


class ArtistDetailInput(BaseModel):
    """Input für SIKART Künstler·in-Detailabfrage."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    artist_id: str = Field(
        ..., min_length=1,
        description="SIKART-ID (HAUPTNR aus heritage_search_artists, z. B. '4023584')"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="heritage_get_artist",
    annotations={
        "title": "Künstler·in-Details abrufen (SIKART)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_get_artist(params: ArtistDetailInput) -> ResultEnvelope | str:
    """Ruft den vollständigen SIKART-Datensatz zu einer Künstler·in ab.

    Args:
        params (ArtistDetailInput):
            - artist_id (str): SIKART-ID (HAUPTNR aus heritage_search_artists)
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Vollständiges Profil mit Lebensdaten, Orten, Kurzbiografie und Links.
    """
    try:
        resp = await _http_get(
            f"{CKAN_API}/datastore_search",
            params={
                "resource_id": SIKART_RESOURCE_ID,
                "filters":     json.dumps({"HAUPTNR": params.artist_id}),
                "limit":       1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            _raise_tool_error(ValueError("CKAN-DataStore-Anfrage fehlgeschlagen."))

        records = data.get("result", {}).get("records", [])
        if not records:
            return f"Keine Daten gefunden für SIKART-ID `{params.artist_id}`."

        artist = records[0]

        if params.response_format == ResponseFormat.JSON:
            return ResultEnvelope(source=SOURCE_SIKART, count=1, total=1, results=[artist])

        lines = [
            f"# {_artist_full_name(artist)}\n",
            f"**SIKART-ID:** `{params.artist_id}`\n",
        ]
        field_map = [
            ("LEBENSDATEN",    "Lebensdaten"),
            ("GEBURTSDATUM",   "Geburtsdatum"),
            ("GEBURTSORT",     "Geburtsort"),
            ("GEBURTSKANTON",  "Geburtskanton"),
            ("GEBURTSLAND",    "Geburtsland"),
            ("STERBEDATUM",    "Sterbedatum"),
            ("STERBEORT",      "Sterbeort"),
            ("STERBEKANTON",   "Sterbekanton"),
            ("STERBELAND",     "Sterbeland"),
            ("TYPUS",          "Typus"),
            ("VITAZEILE",      "Kurzbiografie"),
            ("NUTZUNGSLIZENZ", "Lizenz"),
            ("GND",            "GND"),
            ("HLS_ID",         "HLS-ID"),
            ("SIKART_LINK",    "SIKART-Eintrag"),
            ("WEBSITE",        "Website"),
        ]
        for field, label in field_map:
            val = artist.get(field)
            if val and str(val).strip():
                lines.append(f"**{label}:** {str(val).strip()}")

        return "\n".join(lines) + _attribution(SOURCE_SIKART)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


# ══════════════════════════════════════════════════════════════════════════════
#  MODUL 2 — NATIONALMUSEUM (SNM) via opendata.swiss CKAN API
# ══════════════════════════════════════════════════════════════════════════════

class MuseumSearchInput(BaseModel):
    """Input für SNM-Datensatzsuche."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    query:      str | None = Field(
        default=None, max_length=200,
        description="Suchbegriff (z. B. 'Münzen', 'Siegel', 'Mittelalter', 'Waffen', 'Textil')"
    )
    collection: str | None = Field(
        default=None, max_length=100,
        description="Sammlungsfilter (z. B. 'numismatik', 'siegelsammlung', 'spezialsammlungen')"
    )
    limit:  int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="heritage_search_museum_datasets",
    annotations={
        "title": "SNM-Datensätze suchen (opendata.swiss)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_search_museum_datasets(params: MuseumSearchInput) -> ResultEnvelope | str:
    """Sucht Datensätze des Schweizerischen Nationalmuseums (SNM) auf opendata.swiss.

    Das SNM publiziert Sammlungsdaten als Open Data: Numismatik (~100'000 Münzen),
    Siegelsammlung (~80'000 Objekte), Spezialsammlungen und weitere. Bei 0
    exakten Treffern wird die Solr-Suche automatisch gelockert (OR-verknüpfte
    Präfix-Wildcards) und das Resultat als `match_type: fuzzy` markiert (ARCH-003).

    Args:
        params (MuseumSearchInput):
            - query (str | None):      Suchbegriff über Titel/Beschreibung
            - collection (str | None): Sammlungsfilter (z. B. 'numismatik')
            - limit / offset:             Paginierung
            - response_format:            'markdown' oder 'json'

    Returns:
        str: Liste verfügbarer SNM-Datensätze mit Titel, Beschreibung und
             Download-URLs (CSV, XLSX, JSON).
    """
    try:
        org_filter = f"organization:{SNM_ORG}"
        extra      = f" {params.collection}" if params.collection else ""

        async def _query(query: str | None, fuzzy: bool = False) -> tuple[list[dict], int]:
            if query and fuzzy:
                # Gelockerte Solr-Suche: OR-verknüpfte Präfix-Wildcards je Wort.
                words  = [w for w in query.split() if w]
                q_part = "(" + " OR ".join(f"{w}*" for w in words) + ") " if words else ""
            elif query:
                q_part = f"{query} "
            else:
                q_part = ""
            search_q = f"{q_part}{org_filter}{extra}"
            resp = await _http_get(
                f"{CKAN_API}/package_search",
                params={"q": search_q, "rows": params.limit, "start": params.offset},
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                raise ValueError(f"CKAN-API-Anfrage fehlgeschlagen — {data.get('error', 'Unbekannt')}")
            res = data.get("result", {})
            return res.get("results", []), res.get("count", 0)

        packages, total = await _query(params.query)
        match_type: Literal["exact", "fuzzy", "none"] = "exact"

        # Fuzzy-Retry (ARCH-003): bei 0 Treffern die Suchbegriffe lockern.
        if not packages and params.query:
            packages, total = await _query(params.query, fuzzy=True)
            if packages:
                match_type = "fuzzy"

        if not packages:
            return _no_match(
                SOURCE_SNM, params.response_format,
                "Keine SNM-Datensätze gefunden für die angegebenen Kriterien.",
            )

        if params.response_format == ResponseFormat.JSON:
            simplified = [
                {
                    "name":  pkg.get("name", ""),
                    "title": _normalize_ckan_title(pkg.get("title")),
                    "description": _normalize_ckan_title(pkg.get("notes")) if pkg.get("notes") else "",
                    "resources": [
                        {
                            "name":   r.get("name") or r.get("title") or "Unbenannt",
                            "format": r.get("format") or r.get("media_type", ""),
                            "url":    r.get("download_url") or r.get("url") or "",
                        }
                        for r in pkg.get("resources", [])
                    ],
                }
                for pkg in packages
            ]
            return ResultEnvelope(
                source=SOURCE_SNM,
                count=len(packages),
                total=total,
                offset=params.offset,
                has_more=total > params.offset + len(packages),
                results=simplified,
                match_type=match_type,
            )

        lines = ["# Schweizerisches Nationalmuseum (SNM) — Open Data\n"]
        if params.query:
            lines.append(f"**Suche:** *{params.query}*\n")
        if match_type == "fuzzy":
            lines.append(_FUZZY_NOTE)
        lines.append(f"Gefunden: {total} Datensätze (zeige {len(packages)})\n")
        lines.append("---\n")

        for pkg in packages:
            title    = _normalize_ckan_title(pkg.get("title"))
            pkg_name = pkg.get("name", "")
            notes    = pkg.get("notes")
            desc     = _normalize_ckan_title(notes) if notes else ""
            if desc and len(desc) > 200:
                desc = desc[:200] + "…"
            resources = pkg.get("resources", [])

            lines.append(f"## {title}")
            lines.append(f"**Paket-ID:** `{pkg_name}`")
            if desc:
                lines.append(f"{desc}")
            if resources:
                lines.append(f"**{len(resources)} Ressource(n):**")
                for r in resources[:4]:
                    r_name   = r.get("name") or r.get("title") or "Unbenannt"
                    r_format = r.get("format") or r.get("media_type", "?")
                    r_url    = r.get("download_url") or r.get("url") or ""
                    lines.append(f"  - [{r_name}]({r_url}) `{r_format}`")
            lines.append("")

        if total > params.offset + len(packages):
            lines.append(f"*Weitere Datensätze ab Offset {params.offset + len(packages)}*")

        return "\n".join(lines) + _attribution(SOURCE_SNM)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


class CollectionBrowseInput(BaseModel):
    """Input für SNM-Sammlungsobjekt-Suche via CKAN DataStore."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    resource_id: str = Field(
        ..., min_length=1,
        description="CKAN Resource-ID (aus heritage_search_museum_datasets, z. B. 'abc123-...')"
    )
    query:  str | None = Field(default=None, max_length=200, description="Suchbegriff im Datensatz")
    limit:  int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="heritage_browse_collection",
    annotations={
        "title": "SNM-Sammlungsobjekte durchsuchen (CKAN DataStore)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_browse_collection(params: CollectionBrowseInput) -> ResultEnvelope | str:
    """Durchsucht Objekte innerhalb eines SNM-Sammlungsdatensatzes via CKAN DataStore.

    Voraussetzung: Resource-ID aus `heritage_search_museum_datasets`.

    Args:
        params (CollectionBrowseInput):
            - resource_id (str): CKAN Resource-ID (aus heritage_search_museum_datasets)
            - query (str | None): Suchbegriff (z. B. 'Zürich', 'Karl der Grosse', 'Gold')
            - limit / offset: Paginierung
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Liste von Sammlungsobjekten mit verfügbaren Feldern.
    """
    try:
        api_params: dict = {
            "resource_id": params.resource_id,
            "limit":       params.limit,
            "offset":      params.offset,
        }
        if params.query:
            api_params["q"] = params.query

        resp = await _http_get(f"{CKAN_API}/datastore_search", params=api_params)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            _raise_tool_error(
                ValueError(f"DataStore-Anfrage fehlgeschlagen — {data.get('error', 'Unbekannt')}")
            )

        result  = data.get("result", {})
        records = result.get("records", [])
        total   = result.get("total", 0)
        fields  = [f["id"] for f in result.get("fields", []) if f["id"] != "_id"]

        if not records:
            return (
                f"Keine Objekte gefunden in Ressource `{params.resource_id}`.\n\n"
                "Tipp: Prüfe mit `heritage_search_museum_datasets` die verfügbaren Resource-IDs."
            )

        if params.response_format == ResponseFormat.JSON:
            return ResultEnvelope(
                source=SOURCE_SNM,
                count=len(records),
                total=total,
                offset=params.offset,
                has_more=(params.offset + len(records)) < total,
                results=records,
                meta={"resource_id": params.resource_id, "fields": fields},
            )

        # Titelfeld ermitteln (erste sinnvolle Spalte)
        title_field = next(
            (f for f in ["Titel", "Title", "Bezeichnung", "Name", "Objekt", "Beschriftung"] if f in fields),
            fields[0] if fields else None,
        )

        lines = ["# SNM-Sammlung: Objekte\n"]
        lines.append(f"**Ressource:** `{params.resource_id}`")
        if params.query:
            lines.append(f"**Suche:** *{params.query}*")
        lines.append(f"Gefunden: {total} Objekte (zeige {len(records)})\n")
        lines.append("---\n")

        display_fields = [f for f in fields if f != title_field][:7]

        for rec in records:
            title = rec.get(title_field, f"Objekt #{rec.get('_id', '?')}") if title_field else f"#{rec.get('_id', '?')}"
            lines.append(f"## {title}")
            for f in display_fields:
                if rec.get(f):
                    lines.append(f"**{f}:** {rec[f]}")
            lines.append("")

        if (params.offset + len(records)) < total:
            lines.append(f"*Weitere Objekte ab Offset {params.offset + len(records)}*")

        return "\n".join(lines) + _attribution(SOURCE_SNM)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


# ══════════════════════════════════════════════════════════════════════════════
#  MODUL 3 — NATIONALBIBLIOTHEK (NB) via OAI-PMH
# ══════════════════════════════════════════════════════════════════════════════

class HelvticatSearchInput(BaseModel):
    """Input für die OAI-PMH-Suche in der Nationalbibliothek."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    query:      str | None = Field(
        default=None, max_length=300,
        description=(
            "Suchbegriff für clientseitige Filterung (Titel, Autor, Schlagwort) — "
            "z. B. 'Volksschule Zürich', 'Gottfried Keller', 'Bildungspolitik'. "
            "Hinweis: OAI-PMH unterstützt keine serverseitige Volltextsuche."
        )
    )
    set_spec:   str | None = Field(
        default=None, max_length=100,
        description="OAI-Set-Bezeichner (aus heritage_list_nb_collections) — z. B. 'swissbook'"
    )
    from_date:  str | None = Field(
        default=None,
        description="Publikationen ab diesem Datum (YYYY oder YYYY-MM-DD)",
        pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$",
    )
    until_date: str | None = Field(
        default=None,
        description="Publikationen bis zu diesem Datum (YYYY oder YYYY-MM-DD)",
        pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$",
    )
    limit: int = Field(default=10, ge=1, le=50, description="Max. Ergebnisse (1–50, Standard: 10)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="heritage_search_helveticat",
    annotations={
        "title": "Helveticat durchsuchen (Nationalbibliothek OAI-PMH)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_search_helveticat(params: HelvticatSearchInput) -> ResultEnvelope | str:
    """Durchsucht die Schweizerische Nationalbibliothek (Helveticat) via OAI-PMH.

    Args:
        params (HelvticatSearchInput):
            - query (str | None):      Clientseitige Filterung (Titel, Autor)
            - set_spec (str | None):   OAI-Set-ID (aus heritage_list_nb_collections)
            - from_date (str | None):  Datum von (YYYY oder YYYY-MM-DD)
            - until_date (str | None): Datum bis (YYYY oder YYYY-MM-DD)
            - limit (int):                Max. Ergebnisse 1–50 (Standard: 10)
            - response_format:            'markdown' oder 'json'

    Returns:
        str: Liste von Publikationen mit Titel, Autor, Jahr, Schlagwörtern und Identifier.
    """
    try:
        oai_params: dict = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}
        if params.set_spec:
            oai_params["set"] = params.set_spec
        if params.from_date:
            oai_params["from"] = params.from_date
        if params.until_date:
            oai_params["until"] = params.until_date

        resp = await _http_get(NB_OAI_PMH, params=oai_params)
        resp.raise_for_status()

        records    = _parse_oai_records(resp.text)
        resumption = _extract_resumption_token(resp.text)

        # Clientseitige Filterung nach query
        if params.query:
            q_lower = params.query.lower()
            def _matches(r: dict) -> bool:
                blob = " ".join([
                    str(r.get("title", "")),
                    str(r.get("creator", "")),
                    str(r.get("subject", "")),
                    str(r.get("description", "")),
                ]).lower()
                return q_lower in blob
            records = [r for r in records if _matches(r)]

        records = records[:params.limit]

        if not records:
            return _no_match(
                SOURCE_NB, params.response_format,
                "Keine Publikationen gefunden für die angegebenen Kriterien.\n\n"
                "**Tipp:** OAI-PMH unterstützt keine serverseitige Volltextsuche, daher "
                "gibt es hier keine unscharfe Suche (`match_type` ist immer `exact`). "
                "Für komplexe Abfragen: [helveticat.ch](https://www.helveticat.ch)",
            )

        if params.response_format == ResponseFormat.JSON:
            return ResultEnvelope(
                source=SOURCE_NB,
                count=len(records),
                has_more=bool(resumption),
                results=records,
            )

        lines = ["# Nationalbibliothek — Helveticat\n"]
        if params.query:
            lines.append(f"**Suche:** *{params.query}*")
        if params.from_date or params.until_date:
            lines.append(f"**Zeitraum:** {params.from_date or '—'} bis {params.until_date or 'heute'}")
        if params.set_spec:
            lines.append(f"**Sammlung:** `{params.set_spec}`")
        lines.append(f"\nGefunden: {len(records)} Einträge\n")
        lines.append("---\n")

        for rec in records:
            title = rec.get("title") or "Ohne Titel"
            if isinstance(title, list):
                title = title[0]
            creator = rec.get("creator", "")
            if isinstance(creator, list):
                creator = " / ".join(creator)
            date        = rec.get("date", "")
            description = rec.get("description", "")
            if isinstance(description, list):
                description = description[0]
            subject = rec.get("subject", "")
            if isinstance(subject, list):
                subject = " | ".join(subject[:4])
            identifier = rec.get("oai_identifier", "") or rec.get("identifier", "")
            language   = rec.get("language", "")

            lines.append(f"## {title}")
            if creator:
                lines.append(f"**Autor·in:** {creator}")
            if date:
                lines.append(f"**Jahr:** {date}")
            if language:
                lines.append(f"**Sprache:** {language}")
            if subject:
                lines.append(f"**Schlagwörter:** {subject}")
            if description:
                short = str(description)[:280] + "…" if len(str(description)) > 280 else str(description)
                lines.append(f"*{short}*")
            if identifier:
                lines.append(f"**OAI-ID:** `{identifier}`")
            lines.append("")

        if resumption:
            lines.append("*Weitere Ergebnisse verfügbar (OAI Resumption Token vorhanden).*")

        return "\n".join(lines) + _attribution(SOURCE_NB)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


class NbCollectionsInput(BaseModel):
    """Input für die OAI-PMH ListSets-Abfrage der Nationalbibliothek."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="heritage_list_nb_collections",
    annotations={
        "title": "NB-Sammlungen auflisten (OAI-PMH ListSets)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_list_nb_collections(
    params: NbCollectionsInput | None = None,
) -> ResultEnvelope | str:
    """Listet verfügbare Sammlungen/Sets der Nationalbibliothek auf (OAI-PMH ListSets).

    Args:
        params (NbCollectionsInput | None):
            - response_format: 'markdown' (Standard) oder 'json'

    Returns:
        str: Liste aller OAI-PMH Sets mit Bezeichner (setSpec) und Name.
    """
    params = params or NbCollectionsInput()
    try:
        resp = await _http_get(NB_OAI_PMH, params={"verb": "ListSets"})
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        sets = []
        for s in root.findall(".//oai:set", OAI_NS):
            spec_el = s.find("oai:setSpec", OAI_NS)
            name_el = s.find("oai:setName", OAI_NS)
            sets.append({
                "spec": spec_el.text if spec_el is not None else "",
                "name": name_el.text if name_el is not None else "",
            })

        if params.response_format == ResponseFormat.JSON:
            return ResultEnvelope(source=SOURCE_NB, count=len(sets), results=sets)

        lines = ["# Nationalbibliothek — Verfügbare Sammlungen (OAI-PMH Sets)\n"]
        lines.append(f"Insgesamt {len(sets)} Sets\n")
        for s in sets:
            lines.append(f"- **{s['name']}** — `{s['spec']}`")
        lines.append(
            "\n*Verwende den `set_spec`-Wert als Parameter `set_spec` in `heritage_search_helveticat`.*"
        )
        return "\n".join(lines) + _attribution(SOURCE_NB)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


class PublicationDetailInput(BaseModel):
    """Input für NB OAI-PMH GetRecord."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    identifier: str = Field(
        ..., min_length=5,
        description="OAI-Identifier aus heritage_search_helveticat (z. B. 'oai:helveticat.ch:...')"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


@mcp.tool(
    name="heritage_get_publication",
    annotations={
        "title": "Publikationsdetails abrufen (NB OAI-PMH GetRecord)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_get_publication(params: PublicationDetailInput) -> ResultEnvelope | str:
    """Ruft vollständige Dublin-Core-Metadaten einer Publikation der NB ab.

    Args:
        params (PublicationDetailInput):
            - identifier (str): OAI-ID aus heritage_search_helveticat
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Vollständige DC-Metadaten (Titel, Autor, Verlag, Sprache, Rechte, etc.).
    """
    try:
        resp = await _http_get(
            NB_OAI_PMH,
            params={"verb": "GetRecord", "identifier": params.identifier, "metadataPrefix": "oai_dc"},
        )
        resp.raise_for_status()

        records = _parse_oai_records(resp.text)
        if not records:
            return f"Keine Publikation gefunden mit OAI-ID `{params.identifier}`."

        rec = records[0]

        if params.response_format == ResponseFormat.JSON:
            return ResultEnvelope(source=SOURCE_NB, count=1, total=1, results=[rec])

        title = rec.get("title") or "Ohne Titel"
        if isinstance(title, list):
            title = title[0]

        lines = [f"# {title}\n"]

        dc_fields = [
            ("creator",     "Autor·in / Urheber·in"),
            ("contributor", "Mitwirkende"),
            ("publisher",   "Verlag / Herausgeber"),
            ("date",        "Erscheinungsjahr"),
            ("type",        "Typ"),
            ("format",      "Format"),
            ("language",    "Sprache"),
            ("subject",     "Schlagwörter"),
            ("description", "Beschreibung"),
            ("source",      "Quelle"),
            ("relation",    "Verwandte Ressourcen"),
            ("coverage",    "Abdeckung (Zeit/Raum)"),
            ("rights",      "Rechte / Lizenz"),
            ("oai_identifier", "OAI-Identifier"),
            ("identifier",  "Identifier (DC)"),
        ]
        for key, label in dc_fields:
            val = rec.get(key)
            if val:
                if isinstance(val, list):
                    val = " | ".join(v for v in val if v)
                lines.append(f"**{label}:** {val}")

        return "\n".join(lines) + _attribution(SOURCE_NB)

    except ExpectedUpstreamError as e:
        _raise_tool_error(e)


# ══════════════════════════════════════════════════════════════════════════════
#  MODUL 4 — QUELLENÜBERGREIFENDE SUCHE
# ══════════════════════════════════════════════════════════════════════════════

class CrossSearchInput(BaseModel):
    """Input für quellenübergreifende Suche."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    query: str = Field(
        ..., min_length=2, max_length=200,
        description=(
            "Suchbegriff (z. B. 'Ferdinand Hodler', 'Volksschule Zürich', 'Mittelalter', "
            "'Industrialisierung Schweiz')"
        )
    )
    sources: list[str] = Field(
        default=["sik_isea", "snm", "nb"],
        description="Quellen: 'sik_isea', 'snm', 'nb' (Standard: alle drei)",
    )
    limit_per_source: int = Field(
        default=5, ge=1, le=20,
        description="Max. Ergebnisse pro Quelle (Standard: 5)"
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[str]) -> list[str]:
        valid   = {"sik_isea", "snm", "nb"}
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Ungültige Quellen: {invalid}. Gültig: {valid}")
        return list(dict.fromkeys(v))  # Deduplizieren, Reihenfolge erhalten


@mcp.tool(
    name="heritage_cross_search",
    annotations={
        "title": "Quellenübergreifende Kulturerbe-Suche (SIK-ISEA + SNM + NB)",
        "readOnlyHint":    True,
        "destructiveHint": False,
        "idempotentHint":  True,
        "openWorldHint":   True,
    },
)
@mask_unexpected_errors
async def heritage_cross_search(
    params: CrossSearchInput, ctx: Context = None
) -> ResultEnvelope | str:
    """Durchsucht SIK-ISEA, SNM und NB gleichzeitig nach einem Begriff.

    Fächert auf drei Upstreams auf (i. d. R. > 2 s). Sofern der Client einen
    Progress-Token gesendet hat, wird nach jeder abgeschlossenen Quelle
    `ctx.report_progress()` gemeldet; fehlgeschlagene Quellen werden zusätzlich
    über `ctx.warning()` als strukturierte Warnung signalisiert (SDK-003),
    statt nur als Text im Ergebnis zu erscheinen.

    Args:
        params (CrossSearchInput):
            - query (str): Suchbegriff
            - sources (list[str]): ['sik_isea', 'snm', 'nb'] (Standard: alle)
            - limit_per_source (int): Max. Ergebnisse je Quelle (Standard: 5)
            - response_format: 'markdown' (Standard) oder 'json'
        ctx (Context): Vom MCP-SDK injiziert (Progress/Logging); bei direkten
            Aufrufen ohne Request `None`.

    Returns:
        ResultEnvelope | str: Aggregierte Ergebnisse aus allen gewählten Quellen.
    """
    n    = params.limit_per_source
    q    = params.query

    async def _sik_isea() -> dict:
        try:
            resp = await _http_get(
                f"{CKAN_API}/datastore_search",
                params={"resource_id": SIKART_RESOURCE_ID, "q": q, "limit": n},
            )
            resp.raise_for_status()
            records = resp.json().get("result", {}).get("records", [])
            return {"source": "SIK-ISEA", "label": "Künstler·innen",
                    "license": SOURCE_SIKART.license, "url": SOURCE_SIKART.url, "items": records}
        except ExpectedUpstreamError as e:
            return {"source": "SIK-ISEA", "license": SOURCE_SIKART.license,
                    "url": SOURCE_SIKART.url, "error": str(e)}

    async def _snm() -> dict:
        try:
            resp = await _http_get(
                f"{CKAN_API}/package_search",
                params={"q": f"{q} organization:{SNM_ORG}", "rows": n},
            )
            resp.raise_for_status()
            pkgs = resp.json().get("result", {}).get("results", [])
            return {"source": "SNM", "label": "Museumsdatensätze",
                    "license": SOURCE_SNM.license, "url": SOURCE_SNM.url, "items": pkgs}
        except ExpectedUpstreamError as e:
            return {"source": "SNM", "license": SOURCE_SNM.license,
                    "url": SOURCE_SNM.url, "error": str(e)}

    async def _nb() -> dict:
        try:
            resp = await _http_get(NB_OAI_PMH, params={"verb": "ListRecords", "metadataPrefix": "oai_dc"})
            resp.raise_for_status()
            records  = _parse_oai_records(resp.text)
            q_lower  = q.lower()
            filtered = [r for r in records if q_lower in json.dumps(r, ensure_ascii=False).lower()][:n]
            return {"source": "NB", "label": "Publikationen",
                    "license": SOURCE_NB.license, "url": SOURCE_NB.url, "items": filtered}
        except ExpectedUpstreamError as e:
            return {"source": "NB", "license": SOURCE_NB.license,
                    "url": SOURCE_NB.url, "error": str(e)}

    task_map   = {"sik_isea": _sik_isea, "snm": _snm, "nb": _nb}
    source_map = {"sik_isea": SOURCE_SIKART, "snm": SOURCE_SNM, "nb": SOURCE_NB}
    keys       = [s for s in params.sources if s in task_map]
    used_sources = [source_map[s] for s in keys]

    # Fan-out mit Progress je abgeschlossener Quelle (SDK-003). as_completed
    # erlaubt inkrementelle Fortschrittsmeldungen; die Ergebnisreihenfolge wird
    # anschliessend wieder auf die angeforderte Quellenreihenfolge normalisiert.
    async def _run(key: str) -> tuple[str, dict]:
        return key, await task_map[key]()

    pending   = [asyncio.create_task(_run(k)) for k in keys]
    collected: dict[str, dict] = {}
    for done, fut in enumerate(asyncio.as_completed(pending), start=1):
        key, res = await fut
        collected[key] = res
        if ctx is not None:
            label = res.get("source", key)
            status = "Fehler" if "error" in res else f"{len(res.get('items', []))} Treffer"
            await ctx.report_progress(
                progress=done, total=len(keys), message=f"{label}: {status}"
            )
            if "error" in res:
                await ctx.warning(f"Quelle '{label}' fehlgeschlagen: {res['error']}")

    results = [collected[k] for k in keys]

    if params.response_format == ResponseFormat.JSON:
        return ResultEnvelope(
            source=used_sources,
            count=sum(len(r.get("items", [])) for r in results),
            results=list(results),
        )

    lines = [f"# Kulturerbe-Suche: *{q}*\n"]
    lines.append(f"Quellen: {', '.join(params.sources)}  ·  Max. {n} Ergebnisse/Quelle\n")
    lines.append("---\n")

    for res in results:
        src   = res.get("source", "?")
        label = res.get("label", "Einträge")

        if "error" in res:
            lines.append(f"## {src}\n⚠️ Fehler: {res['error']}\n")
            continue

        items = res.get("items", [])
        lines.append(f"## {src} — {label} ({len(items)})\n")

        if not items:
            lines.append("*Keine Treffer*\n")
            continue

        for item in items:
            if src == "SIK-ISEA":
                full   = _artist_full_name(item)
                span   = _artist_lifespan(item)
                canton = (item.get("GEBURTSKANTON") or "").strip()
                dating = f" ({span})" if span else ""
                ctxt   = f" · {canton}" if canton else ""
                lines.append(f"- `[{src}]` **{full}**{dating}{ctxt}")

            elif src == "SNM":
                title = _normalize_ckan_title(item.get("title"))
                lines.append(f"- `[{src}]` {title}")

            elif src == "NB":
                title = item.get("title") or "Ohne Titel"
                if isinstance(title, list):
                    title = title[0]
                creator = item.get("creator", "")
                if isinstance(creator, list):
                    creator = creator[0]
                date = item.get("date", "")
                auth = f" — {creator}" if creator else ""
                yr   = f" ({date})" if date else ""
                lines.append(f"- `[{src}]` **{title}**{auth}{yr}")

        lines.append("")

    return "\n".join(lines) + _attribution(used_sources)


# ══════════════════════════════════════════════════════════════════════════════
#  RESOURCES
# ══════════════════════════════════════════════════════════════════════════════

@mcp.resource("heritage://sik-isea/overview")
async def sik_isea_overview() -> str:
    """Übersicht SIK-ISEA: Datenquelle, Umfang und verfügbare Tools."""
    return """# SIK-ISEA / SIKART — Schweizer Künstler·innen

## Was ist SIKART?
SIKART (Lexikon zur Kunst in der Schweiz) ist das Online-Nachschlagewerk des
Schweizerischen Instituts für Kunstwissenschaft (SIK-ISEA). Der hier genutzte
Datensatz umfasst rund 17'000 Einträge mit den biografischen Grunddaten zu
historischen und zeitgenössischen Kunstschaffenden.

## Verfügbare Daten
- Name, Vorname, Namensvarianten
- Lebensdaten (Geburts-/Sterbejahr, -datum, -ort, -kanton, -land)
- Kurzbiografie (`VITAZEILE`, enthält oft die Berufsbezeichnung)
- Verknüpfungen: SIKART-Eintrag, GND, HLS-ID

## API-Zugang
- Quelle:        opendata.swiss — Datensatz «kuenstlernamen-aus-sikart-lexikon-zur-kunst-in-der-schweiz»
- Endpoint:      https://ckan.opendata.swiss/api/3/action/datastore_search
- Format:        JSON (CKAN DataStore)
- Authentifizierung: Keine (Open Data)
- Lizenz:        CC BY (opendata.swiss Nutzungsbedingungen)

## Verfügbare MCP-Tools
| Tool                      | Funktion                                  |
|---------------------------|-------------------------------------------|
| `heritage_search_artists` | Künstler·innen suchen (Name, Ort/Kanton)  |
| `heritage_get_artist`     | Detaildaten zu einer Künstler·in (HAUPTNR)|
| `heritage_cross_search`   | Suche über alle drei Quellen              |

## Demo-Abfragen
- «Suche Künstler·innen mit Geburtsort Basel»
- «Zeige mir Einträge zu Ferdinand Hodler»
- «Finde Schweizer Bildhauer·innen»
"""


@mcp.resource("heritage://nb/collections")
async def nb_collections_overview() -> str:
    """Statische Übersicht der Nationalbibliothek-Sammlungen und OAI-PMH-Endpunkte."""
    return """# Schweizerische Nationalbibliothek (NB) — Sammlungsübersicht

## OAI-PMH Endpunkt
- URL:           https://helveticat.nb.admin.ch/view/oai/41SNL_51_INST/request
- Protokoll:     OAI-PMH 2.0
- Metadaten:     Dublin Core (oai_dc)
- Authentifizierung: Keine

## Bekannte OAI-Sets
| Set         | Inhalt                                           |
|-------------|--------------------------------------------------|
| swissbook   | Das Schweizer Buch (Schweizerische Nationalbibliografie) |
| xsichler    | Sammlung zur Geschichte der Erziehung und Bildung |
| xrara       | Seltene Bücher (Helvetica Rara)                  |
| xdigicoll   | Alle digitalisierten Bücher                      |
| xmundart    | Sammlung zu Patois und Dialekten                 |
| xsgg        | Publikationen der Schweiz. Gesellschaft für Geschichte |
| xlivcar     | Auf Nutzeranfrage digitalisierte Bücher          |

Die jeweils aktuelle Liste liefert `heritage_list_nb_collections` (OAI-PMH ListSets).

## Verfügbare MCP-Tools
| Tool                          | Funktion                                  |
|-------------------------------|-------------------------------------------|
| `heritage_search_helveticat`  | Suche in der Nationalbibliografie         |
| `heritage_list_nb_collections`| Alle verfügbaren OAI-Sets auflisten       |
| `heritage_get_publication`    | Vollständige Metadaten einer Publikation  |

## Wichtiger Hinweis zu OAI-PMH
OAI-PMH unterstützt keine Volltextsuche. Die effektivsten Filter sind
Datum (`from_date`/`until_date`) und Sammlung (`set_spec`).
Für komplexe Suchen: https://www.helveticat.ch

## Nutzungsrechte
- Metadaten: Frei verwendbar (kommerziell und nicht-kommerziell)
- Digitalisate: Individuelle Lizenzprüfung erforderlich
"""


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

@mcp.prompt()
def heritage_research_artist(
    artist_name: str,
    context: str = "allgemein",
) -> str:
    """Strukturierter Recherche-Prompt zu einer Schweizer Künstler·in.

    Args:
        artist_name: Name der zu recherchierenden Künstler·in
        context: Forschungskontext (z. B. 'Unterricht Sek I', 'Ausstellung', 'Monografie')
    """
    return f"""Führe eine strukturierte Recherche zu **{artist_name}** durch.
Kontext: {context}

## Schritt 1 — Basisrecherche SIK-ISEA
Rufe `heritage_search_artists` auf (query="{artist_name}").
Falls mehrere Treffer: `heritage_get_artist` für den relevantesten Eintrag.

## Schritt 2 — Quellenübergreifende Suche
Rufe `heritage_cross_search` auf (query="{artist_name}", sources=["sik_isea","snm","nb"]).
Notiere alle Treffer aus SNM und NB.

## Schritt 3 — Vertiefung
- Für interessante NB-Einträge: `heritage_get_publication` aufrufen
- Falls SNM-Treffer: `heritage_search_museum_datasets` für Sammlungsdetails

## Gewünschte Ausgabe
1. **Biografie**: Lebensdaten, Herkunft, Ausbildung, Kanton
2. **Künstlerisches Werk**: Technik, Epoche, wichtige Werke
3. **Museale Präsenz**: SNM-Sammlungen
4. **Bibliografie**: Relevante Publikationen aus Helveticat
5. **Relevanz für Kontext**: {context}

Antworte auf Deutsch, präzise und quellenbasiert. Zitiere SIK-IDs und OAI-Identifier."""


@mcp.prompt()
def heritage_find_educational_resources(
    topic: str,
    school_level: str = "Sekundarstufe I",
) -> str:
    """Prompt zur Suche nach Bildungsressourcen aus Schweizer Kulturerbe-Quellen.

    Args:
        topic: Thema für den Unterricht (z. B. 'Mittelalter', 'Schweizer Kunst', 'Migration')
        school_level: Schulstufe (z. B. 'Primarstufe', 'Sekundarstufe I', 'Gymnasium')
    """
    return f"""Suche Bildungsressourcen zum Thema **{topic}** für die **{school_level}**.

## Suchstrategie

1. **Überblick** — `heritage_cross_search` (query="{topic}", limit_per_source=5)
   → Verschaffe dir einen Überblick über alle drei Quellen

2. **Fachliteratur** — `heritage_search_helveticat` (query="{topic}", from_date="2000-01-01")
   → Neuere Publikationen bevorzugen

3. **Anschauungsmaterial** — `heritage_search_museum_datasets` (query="{topic}")
   → Museumsobjekte als didaktische Primärquellen

4. **Kunstbezug** — Falls relevant: `heritage_search_artists` (technique oder period passend zu "{topic}")

## Auswahlkriterien
- Altersgerecht für **{school_level}**
- Bezug zum Schweizer Lehrplan 21 / Bildungsplan Gymnasien
- Open Access oder über Schulbibliotheken zugänglich
- Schweizer Perspektive / lokaler Bezug bevorzugt

## Ausgabeformat
Strukturiere die Antwort nach:
1. 📚 Empfohlene Publikationen (mit NB-OAI-Identifikatoren)
2. 🏛️ Museumsobjekte als Unterrichtsmaterial (mit SNM-Ressourcen-Links)
3. 🎨 Künstlerische Beispiele (falls themenrelevant)
4. 🔗 Weiterführende Online-Ressourcen (Open Access)

Antworte auf Deutsch."""


# ══════════════════════════════════════════════════════════════════════════════
#  HEALTH-ENDPOINT (nur im HTTP-Transport sichtbar)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.custom_route("/health", methods=["GET"])
async def health(_request):
    """Liveness-Probe für Render / Kubernetes / Cloud Run."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "service": "swiss-cultural-heritage-mcp"})


# ══════════════════════════════════════════════════════════════════════════════
#  HTTP-APP (Streamable HTTP) — CORS (SDK-004)
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_HTTP_PORT: Final[int] = settings.port


def cors_origins_from_env() -> list[str]:
    """Liest die erlaubten CORS-Origins aus ``MCP_CORS_ORIGINS`` (komma-separiert).

    Default ist eine leere Liste — also keine Cross-Origin-Freigabe. Browser-Zugriff
    erfordert das explizite Setzen der erlaubten Origins (kein Wildcard in Produktion).
    """
    return [o.strip() for o in settings.cors_origins.split(",") if o.strip()]


def build_http_app(cors_origins: list[str] | None = None):
    """Baut die Streamable-HTTP-Starlette-App inkl. CORS-Middleware (SDK-004).

    ``Mcp-Session-Id`` wird via ``expose_headers`` freigegeben, damit Browser-Clients
    die Session-ID über mehrere Requests hinweg lesen und mitsenden können — ohne das
    bricht die Session-Kontinuität im Browser. ``allow_origins`` ist eine explizite
    Allow-List (kein ``*`` in Produktion), konfigurierbar über ``MCP_CORS_ORIGINS``.
    """
    from starlette.middleware.cors import CORSMiddleware

    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or [],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Mcp-Session-Id", "Content-Type"],
        expose_headers=["Mcp-Session-Id"],
    )
    return app


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ARCH-004: Transport/Host/Port kommen aus Settings (MCP_TRANSPORT/MCP_HOST/
    # MCP_PORT); `--http` bleibt als bequemes CLI-Alias erhalten.
    if settings.transport == "http" or "--http" in sys.argv:
        import uvicorn

        # SEC-016: loopback-Default; der Container setzt MCP_HOST=0.0.0.0 explizit.
        mcp.settings.host = settings.host
        mcp.settings.port = settings.port
        app = build_http_app(cors_origins_from_env())
        uvicorn.run(
            app, host=settings.host, port=settings.port,
            log_level=mcp.settings.log_level.lower(),
        )
    else:
        mcp.run()
