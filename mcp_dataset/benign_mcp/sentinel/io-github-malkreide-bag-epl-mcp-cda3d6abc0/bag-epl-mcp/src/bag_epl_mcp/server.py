#!/usr/bin/env python3
"""
BAG ePL MCP Server — v0.2.0

KI-nativer Zugang zur elektronischen Plattform Leistungen (ePL) des BAG:
  · Spezialitaetenliste (SL):   Kassenpflichtige Medikamente (KVG Art. 52)
  · GGSL:                       Medikamente bei Geburtsgebrechen (IVG)
  · MiGeL:                      Medizinprodukte und Hilfsmittel (KLV Art. 20)

Kein API-Schluessel erforderlich. Alle Daten oeffentlich zugaenglich.
"""

from __future__ import annotations

import ipaddress
import json
import socket
import sys
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from enum import StrEnum
from typing import Literal
from urllib.parse import urlsplit

import httpcore
import httpx
import structlog
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ─────────────────────────── Logging (OBS-003/004) ─────────────────────────────
# Strukturierte JSON-Logs ausschliesslich nach STDERR — STDOUT ist beim
# stdio-Transport fuer den JSON-RPC-Stream reserviert (OBS-004).
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)
log = structlog.get_logger("bag_epl_mcp")


def _bind_call_context(ctx: Context | None, tool: str) -> None:
    """
    OBS-003/SDK-003: bindet pro Tool-Call strukturierten Kontext (Tool-Name,
    Correlation-ID und — falls eine MCP-Session aktiv ist — Request-/Client-ID)
    an den Logger. Alle nachfolgenden ``log.*``-Aufrufe tragen diesen Kontext.
    """
    structlog.contextvars.clear_contextvars()
    fields: dict[str, str] = {"tool": tool, "correlation_id": uuid.uuid4().hex}
    if ctx is not None:
        # Zugriff nur innerhalb eines echten Requests gueltig -> defensiv.
        with suppress(Exception):
            fields["request_id"] = str(ctx.request_id)
        with suppress(Exception):
            fields["client_id"] = str(ctx.client_id)
    structlog.contextvars.bind_contextvars(**fields)
    log.info("tool_call", tool=tool)


# ─────────────────────────── Settings (ARCH-004) ───────────────────────────────
class ServerSettings(BaseSettings):
    """
    Laufzeit-Konfiguration via Umgebungsvariablen (Prefix ``MCP_``).

    Transport- und Host-Wahl erfolgt ausschliesslich ueber Env-Vars, damit die
    Server-Logik transport-agnostisch bleibt (keine globalen Schalter im Code).
    """
    model_config = SettingsConfigDict(env_prefix="MCP_", extra="ignore")

    # "stdio" (Default, lokal/Claude Desktop) | "streamable-http" (Cloud)
    transport: str = "stdio"
    # SEC-016: Default 127.0.0.1 — 0.0.0.0 nur explizit im Container setzen.
    host: str = "127.0.0.1"
    # MCP_PORT bevorzugt; faellt auf PORT zurueck (von Render/PaaS injiziert).
    port: int = Field(default=8000, validation_alias=AliasChoices("MCP_PORT", "PORT"))
    # SDK-004: explizite Origin-Allow-List statt Wildcard.
    cors_origins: list[str] = ["https://claude.ai"]
    # OBS-006: OpenTelemetry-Tracing standardmaessig aktiv. Greift nur, wenn das
    # [otel]-Extra installiert ist (sonst stiller No-op); mit MCP_OTEL_ENABLED=0
    # deaktivierbar. Exporter-Endpoint via OTEL_EXPORTER_OTLP_ENDPOINT.
    otel_enabled: bool = True


settings = ServerSettings()


# ─────────────────────────── Lifespan / HTTP-Client-Pool (SDK-001) ─────────────
# Ein einziger, wiederverwendeter AsyncClient (Connection-Pooling/Keep-Alive)
# statt pro Tool-Call einen neuen Client zu erzeugen. Wird beim Server-Start
# initialisiert und beim Shutdown sauber geschlossen.
_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[dict]:
    """Initialisiert den gepoolten HTTP-Client und raeumt ihn beim Shutdown ab."""
    global _http_client
    _http_client = _new_http_client()
    log.info("server_startup", transport=settings.transport)
    try:
        yield {"http_client": _http_client}
    finally:
        await _http_client.aclose()
        _http_client = None
        log.info("server_shutdown")


# ─────────────────────────── Server ────────────────────────────────────────────
mcp = FastMCP("bag_epl_mcp", host=settings.host, port=settings.port, lifespan=_lifespan)

# ─────────────────────────── Konstanten ────────────────────────────────────────
SL_BASE_URL       = "https://sl.bag.admin.ch"
SL_API_URL        = "https://sl.bag.admin.ch/api"
BAG_DOWNLOAD_URL  = "https://www.bag.admin.ch/bag/de/home/versicherungen/krankenversicherung/krankenversicherung-leistungen-tarife"
GGSL_INFO_URL     = "https://www.bag.admin.ch/bag/de/home/versicherungen/krankenversicherung/krankenversicherung-leistungen-tarife/Arzneimittel/geburtsgebrechen-spezialitaetenliste.html"
MIGEL_INFO_URL    = "https://www.bag.admin.ch/bag/de/home/versicherungen/krankenversicherung/krankenversicherung-leistungen-tarife/Mittel-und-Gegenstaendeliste.html"
HTTP_TIMEOUT      = 30.0
DEFAULT_LIMIT     = 20
MAX_LIMIT         = 100

# ARCH-012: dokumentierte/„gepinnte" MCP-Protokoll-Version (Update-Policy: README).
PROTOCOL_VERSION = "2025-06-18"
# CH-004: OGD-CH-Standardlizenz fuer die zugrundeliegenden BAG-Open-Data.
OGD_LICENSE = "CC BY 4.0"

# Phase 2: FHIR-API-Endpunkt (wird aktiviert, sobald BAG publiziert)
FHIR_BASE_URL = "https://epl.bag.admin.ch/fhir"  # Platzhalter


# ─────────────────────────── Provenance / Envelope (SDK-002/CH-004) ─────────────
# Treffer-Klassifikation fuer Such-Tools (ARCH-003): exakt / unscharf / keine.
MatchType = Literal["exact", "fuzzy", "none"]


class Provenance(BaseModel):
    """Herkunft und Lizenz einer Antwort (CH-004 / SDK-002)."""
    source: str
    url: str
    license: str = OGD_LICENSE
    phase: str = "Phase 1"


def _provenance(source: str, url: str) -> Provenance:
    """Erzeugt einen Provenance-Block (Quelle + Lizenz) fuer Tool-Antworten."""
    return Provenance(source=source, url=url)


# ─────────── Strukturierte Tool-Ausgaben / Output-Schemas (SDK-002) ─────────────
# Jedes Tool deklariert ein getyptes Envelope als Output-Schema und liefert es als
# `structuredContent` zurueck — zusaetzlich zur kuratierten Markdown-Ausgabe im
# `content`-Block (Hybrid, kein UX-Verlust). Siehe `_structured_result`.

class BaseEnvelope(BaseModel):
    """Gemeinsame Huelle aller strukturierten Tool-Ausgaben (SDK-002 / CH-004)."""
    source: str
    provenance: Provenance


class SLTreffer(BaseModel):
    """Ein SL-Suchtreffer. ``extra='allow'``, da die Upstream-API zusaetzliche
    Felder liefern kann, sobald sie oeffentlich ist."""
    model_config = ConfigDict(extra="allow")
    name: str | None = None


class SLSucheEnvelope(BaseEnvelope):
    suchbegriff: str
    match_type: MatchType
    count: int
    results: list[SLTreffer] = Field(default_factory=list)
    hinweis: str | None = None
    direkt_link: str | None = None
    fhir_status: str | None = None


class GGSLEnvelope(BaseEnvelope):
    geburtsgebrechen_nr: str
    status: str
    erklaerung: str
    link: str
    rechtsgrundlage: str
    hinweis: str


class MiGeLEnvelope(BaseEnvelope):
    suchbegriff: str
    status: str
    erklaerung: str
    link: str
    rechtsgrundlage: str
    migel_integration: str
    match_type: MatchType = "none"
    count: int = 0
    results: list[dict] = Field(default_factory=list)


class GesuchseingaengeEnvelope(BaseEnvelope):
    beschreibung: str
    link: str
    direkt_link_bag: str
    hinweis: str


class Gesetz(BaseModel):
    kuerzel: str
    titel: str
    sr_nummer: str
    fedlex: str
    relevante_artikel: list[str]


class RechtskontextEnvelope(BaseEnvelope):
    frage: str
    gesetze: list[Gesetz]
    wzw_kriterien: dict[str, str]
    hinweis: str


class ServerInfoEnvelope(BaseEnvelope):
    server: str
    version: str
    protocol_version: str
    license: str
    phase: str
    tools: dict[str, str]
    phasen: dict[str, str]
    datenquellen: dict[str, str]


def _structured_result(text: str, envelope: BaseModel) -> CallToolResult:
    """
    SDK-002: liefert beides zurueck — die kuratierte, menschenlesbare Ausgabe als
    ``content`` (Markdown oder JSON je nach ``format``) **und** das getypte Envelope
    als ``structuredContent`` (validiert gegen das Output-Schema des Tools).
    """
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structuredContent=envelope.model_dump(mode="json"),
    )

# SEC-004 / SEC-021: Egress-Allow-List auf Code-Ebene (immutable).
# Jeder ausgehende Request muss gegen diese Liste vertrauenswuerdiger
# BAG-/Fedlex-Hosts validiert werden. Netzwerk-Layer-Egress (NetworkPolicy)
# ergaenzt dies im Deployment.
ALLOWED_HOSTS: frozenset[str] = frozenset({
    "sl.bag.admin.ch",
    "www.bag.admin.ch",
    "www.fedlex.admin.ch",
})


# ─────────────────────────── Egress-Guard (SEC-004/005/021) ─────────────────────

def _assert_safe_url(url: str) -> None:
    """
    Schnelle Vorpruefung vor jedem ausgehenden Request (ohne DNS):

    * Schema muss ``https`` sein (SEC-004).
    * Host muss in :data:`ALLOWED_HOSTS` stehen — Default-Deny (SEC-021).

    Die DNS-Aufloesung + IP-Validierung + das Pinning erfolgen in
    :func:`_resolve_and_validate` bzw. :class:`_PinnedNetworkBackend` (SEC-005).
    """
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise ToolError("Ausgehende Requests sind nur ueber HTTPS erlaubt.")

    host = parts.hostname or ""
    if host not in ALLOWED_HOSTS:
        log.warning("egress_blocked", reason="host_not_allowed", host=host)
        raise ToolError("Ziel-Host ist nicht in der erlaubten Egress-Liste.")


def _resolve_and_validate(host: str, port: int) -> str:
    """
    Loest ``host`` **genau einmal** auf, validiert alle zurueckgegebenen IPs gegen
    die SSRF-Blocklist (privat/loopback/link-local/reserved, u.a. 169.254.169.254,
    ::1, fe80::/10) und gibt die zu verwendende (gepinnte) IP zurueck (SEC-004/005).
    """
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise ToolError("Host-Aufloesung fehlgeschlagen.") from exc

    for *_, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            log.warning("egress_blocked", reason="unsafe_ip", host=host, ip=str(ip))
            raise ToolError("Aufgeloeste IP-Adresse ist nicht erlaubt (SSRF-Schutz).")
    return infos[0][4][0]


class _PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    """
    SEC-005 (DNS-Rebinding-Prevention): loest den Hostnamen einmal auf, validiert
    die IP und pinnt die TCP-Verbindung auf genau diese IP. TLS-SNI und
    Zertifikatspruefung verwenden weiterhin den urspruenglichen Hostnamen, da
    httpcore ``start_tls`` separat mit dem Origin-Host aufruft.
    """

    def __init__(self, inner: httpcore.AsyncNetworkBackend) -> None:
        self._inner = inner

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        pinned_ip = _resolve_and_validate(host, port)
        return await self._inner.connect_tcp(
            pinned_ip, port, timeout=timeout,
            local_address=local_address, socket_options=socket_options,
        )

    async def connect_unix_socket(self, *args, **kwargs):  # pragma: no cover - unused
        return await self._inner.connect_unix_socket(*args, **kwargs)

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


def _new_http_client() -> httpx.AsyncClient:
    """
    Erzeugt einen AsyncClient, dessen Verbindungen DNS-gepinnt und SSRF-validiert
    sind (SEC-004/005). Faellt defensiv auf einen ungepinnten Client zurueck, falls
    sich die httpx-Internas aendern — die Allow-List (SEC-021) bleibt aktiv.
    """
    transport = httpx.AsyncHTTPTransport()
    pool = getattr(transport, "_pool", None)
    backend = getattr(pool, "_network_backend", None)
    if backend is not None:
        pool._network_backend = _PinnedNetworkBackend(backend)
    else:  # pragma: no cover - defensive
        log.warning("dns_pinning_unavailable")
    return httpx.AsyncClient(timeout=HTTP_TIMEOUT, transport=transport)

# ─────────────────────────── Enum ──────────────────────────────────────────────
class ResponseFormat(StrEnum):
    """Ausgabeformat fuer Tool-Antworten."""
    MARKDOWN = "markdown"
    JSON     = "json"


# ─────────────────────────── Hilfsfunktionen ───────────────────────────────────

async def _http_get(url: str, params: dict | None = None) -> httpx.Response:
    """
    Async HTTP GET mit Timeout. Validiert die Ziel-URL gegen die Egress-Allow-List
    und nutzt — falls vorhanden — den gepoolten Lifespan-Client (SDK-001).
    """
    _assert_safe_url(url)
    log.debug("http_get", url=url)
    if _http_client is not None:
        return await _http_client.get(url, params=params)
    # Fallback (z.B. Direktaufruf ausserhalb des Server-Lifespans / Tests).
    async with _new_http_client() as client:
        return await client.get(url, params=params)


def _handle_error(error: Exception, context: str = "") -> str:
    """Einheitliche Fehlerbehandlung mit deutschen Meldungen."""
    prefix = f"Fehler bei {context}: " if context else "Fehler: "

    # OBS-002: vollstaendige Details NUR serverseitig (stderr) protokollieren,
    # niemals an den LLM zurueckgeben.
    log.error("tool_error", context=context or None,
              error_type=type(error).__name__, detail=str(error))

    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        if status == 404:
            return f"{prefix}Ressource nicht gefunden (404)."
        if status == 429:
            return f"{prefix}Zu viele Anfragen — bitte spaeter erneut versuchen (429)."
        if status in (502, 503):
            return f"{prefix}Dienst voruebergehend nicht erreichbar ({status})."
        return f"{prefix}HTTP-Fehler {status}."
    if isinstance(error, httpx.TimeoutException):
        return f"{prefix}Zeitueberschreitung — der Server antwortet nicht innerhalb von {HTTP_TIMEOUT}s."
    if isinstance(error, httpx.ConnectError):
        return f"{prefix}Verbindung fehlgeschlagen — Server nicht erreichbar."
    # OBS-002: keine internen Details (rohe Exception-Message / Stacktrace / Pfade)
    # an den LLM zurueckgeben — nur der Exception-Typ als grobe Kategorie.
    return f"{prefix}Unerwarteter Fehler ({type(error).__name__})."


def _paginate(total: int, limit: int, offset: int) -> dict:
    """Standard-Paginierungshelfer."""
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "hat_mehr": offset + limit < total,
    }


# ─────────────────────────── SL-Website-Suche (Phase 1) ───────────────────────

async def _sl_website_suche(suchbegriff: str, limit: int = DEFAULT_LIMIT) -> dict:
    """
    Versucht, die SL-Website nach einem Medikament zu durchsuchen.
    Phase 1: Die interne API ist nicht dokumentiert — Fallback auf Info-Links.
    Phase 2: Wird durch FHIR-API-Aufrufe ersetzt.
    """
    try:
        resp = await _http_get(
            f"{SL_API_URL}/search",
            params={"query": suchbegriff, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Phase 1 Fallback: API nicht oeffentlich zugaenglich
        return {
            "hinweis": (
                "Die SL-Datenbank-API ist derzeit nicht oeffentlich dokumentiert. "
                "Bitte verwenden Sie den direkten Link fuer eine manuelle Suche."
            ),
            "direkt_link": f"{SL_BASE_URL}/#/search/{suchbegriff}",
            "phase": "Phase 1 — Website-Zugriff",
            "fhir_status": "FHIR/IDMP-API noch nicht publiziert (erwartet ~2025/2026)",
        }


# ─────────────────────────── Input-Modelle ─────────────────────────────────────

class SLSucheInput(BaseModel):
    """Eingabe fuer die Medikamentensuche in der Spezialitaetenliste."""
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid", strict=True
    )

    suchbegriff: str = Field(
        ..., min_length=1, max_length=200,
        description="Name oder Wirkstoff des Medikaments (z.B. 'Methylphenidat', 'Aspirin')",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT,
        description="Maximale Anzahl Ergebnisse (1-100)",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, strict=False,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class GGSLAbfrageInput(BaseModel):
    """Eingabe fuer GGSL-Abfrage bei Geburtsgebrechen."""
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid", strict=True
    )

    geburtsgebrechen_nr: str = Field(
        ..., min_length=1, max_length=10,
        description="Geburtsgebrechen-Nummer (z.B. '313' fuer Diabetes, '404' fuer Zystische Fibrose)",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, strict=False,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class MiGeLSucheInput(BaseModel):
    """Eingabe fuer die MiGeL-Suche."""
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid", strict=True
    )

    suchbegriff: str = Field(
        ..., min_length=1, max_length=200,
        description="Suchbegriff fuer Medizinprodukte (z.B. 'Rollstuhl', 'Hoergeraet')",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT,
        description="Maximale Anzahl Ergebnisse (1-100)",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, strict=False,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit(cls, v: int) -> int:
        return min(max(v, 1), MAX_LIMIT)


class RechtskontextInput(BaseModel):
    """Eingabe fuer rechtliche Kontext-Abfrage."""
    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid", strict=True
    )

    frage: str = Field(
        ..., min_length=1, max_length=500,
        description="Rechtliche Frage zur Kassenpflicht (z.B. 'Welche Gesetze regeln die SL-Aufnahme?')",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN, strict=False,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


# ─────────────────────────── Tools ─────────────────────────────────────────────

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True), structured_output=True)
async def epl_sl_suche(eingabe: SLSucheInput, ctx: Context | None = None) -> SLSucheEnvelope:
    """
    Suche in der Spezialitaetenliste (SL) nach kassenpflichtigen Medikamenten.

    Die SL enthaelt alle Arzneimittel, die von der obligatorischen
    Krankenpflegeversicherung (OKP) verguetet werden (KVG Art. 52).

    <use_case>Beantwortet \u00abIst Medikament X kassenpflichtig?\u00bb. Liefert Treffer
    aus der SL bzw. \u2014 solange die BAG-API nicht oeffentlich ist \u2014 einen
    Direktlink plus Rechtsgrundlage. Fuer Geburtsgebrechen siehe
    epl_ggsl_abfrage, fuer Hilfsmittel epl_migel_suche.</use_case>
    """
    _bind_call_context(ctx, "epl_sl_suche")
    try:
        ergebnis = await _sl_website_suche(eingabe.suchbegriff, eingabe.limit)
        results = ergebnis.get("results", [])
        # ARCH-003: Treffer klassifizieren; bei "none" Handlungshinweis mitgeben.
        match_type: MatchType = "exact" if results else "none"

        envelope = SLSucheEnvelope(
            source="BAG Spezialitaetenliste (SL)",
            provenance=_provenance("BAG Spezialitaetenliste (SL)", SL_BASE_URL),
            suchbegriff=eingabe.suchbegriff,
            match_type=match_type,
            count=len(results),
            results=[SLTreffer(**r) for r in results],
            hinweis=ergebnis.get("hinweis"),
            direkt_link=ergebnis.get("direkt_link"),
            fhir_status=ergebnis.get("fhir_status"),
        )

        if eingabe.format == ResponseFormat.JSON:
            text = json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, indent=2)
            return _structured_result(text, envelope)

        # Markdown-Ausgabe
        md = f"## SL-Suche: \u00ab{eingabe.suchbegriff}\u00bb\n\n"

        if "hinweis" in ergebnis:
            md += f"> **Hinweis:** {ergebnis['hinweis']}\n\n"
            md += f"**Direkte Suche:** [{eingabe.suchbegriff} auf sl.bag.admin.ch]({ergebnis['direkt_link']})\n\n"
            md += f"**API-Status:** {ergebnis['fhir_status']}\n\n"
            md += "### Rechtsgrundlage\n"
            md += "- KVG Art. 52: Spezialitaetenliste\n"
            md += "- KLV Art. 30ff: Aufnahme-Kriterien (WZW: Wirksamkeit, Zweckmaessigkeit, Wirtschaftlichkeit)\n"
        else:
            md += f"Gefundene Medikamente: {len(results)}\n\n"
            for item in results:
                md += f"- **{item.get('name', 'Unbekannt')}**\n"

        md += f"\n---\n*Quelle: BAG Spezialitaetenliste \u00b7 Lizenz: {OGD_LICENSE} \u00b7 {SL_BASE_URL}*\n"
        return _structured_result(md, envelope)

    except ToolError:
        raise
    except Exception as e:
        raise ToolError(_handle_error(e, "SL-Suche")) from e


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False), structured_output=True)
async def epl_ggsl_abfrage(eingabe: GGSLAbfrageInput, ctx: Context | None = None) -> GGSLEnvelope:
    """
    GGSL-Deckung bei Geburtsgebrechen pruefen.

    Die Geburtsgebrechen-Spezialitaetenliste (GGSL) enthaelt Arzneimittel,
    die bei anerkannten Geburtsgebrechen von der Invalidenversicherung (IV)
    uebernommen werden.

    <use_case>Beantwortet \u00abWelche Medikamente uebernimmt die IV bei
    Geburtsgebrechen Nr. X?\u00bb. Liefert Rechtsgrundlage (IVG/GgV) und die
    offizielle BAG-Quelle. Im Gegensatz zu epl_sl_suche geht es hier um
    IV- statt OKP-Leistungen.</use_case>
    """
    _bind_call_context(ctx, "epl_ggsl_abfrage")
    try:
        gg_nr = eingabe.geburtsgebrechen_nr

        envelope = GGSLEnvelope(
            source="BAG GGSL",
            provenance=_provenance("BAG GGSL", GGSL_INFO_URL),
            geburtsgebrechen_nr=gg_nr,
            status="Phase 1 \u2014 Statische Information",
            erklaerung=(
                f"Die GGSL listet Medikamente, die bei Geburtsgebrechen Nr. {gg_nr} "
                "von der IV uebernommen werden. Die vollstaendige Liste ist beim BAG einsehbar."
            ),
            link=GGSL_INFO_URL,
            rechtsgrundlage="IVG Art. 13 / GgV (Geburtsgebrechen-Verordnung)",
            hinweis=(
                "Fuer die aktuelle Medikamentenliste zu diesem Geburtsgebrechen "
                "konsultieren Sie bitte die offizielle BAG-Seite."
            ),
        )

        if eingabe.format == ResponseFormat.JSON:
            text = json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, indent=2)
            return _structured_result(text, envelope)

        md = f"## GGSL-Abfrage: Geburtsgebrechen Nr. {gg_nr}\n\n"
        md += f"> {envelope.erklaerung}\n\n"
        md += f"**Offizielle Quelle:** [BAG GGSL]({envelope.link})\n\n"
        md += f"**Rechtsgrundlage:** {envelope.rechtsgrundlage}\n\n"
        md += f"**Hinweis:** {envelope.hinweis}\n"
        md += f"\n---\n*Quelle: BAG GGSL \u00b7 Lizenz: {OGD_LICENSE} \u00b7 {GGSL_INFO_URL}*\n"
        return _structured_result(md, envelope)

    except ToolError:
        raise
    except Exception as e:
        raise ToolError(_handle_error(e, "GGSL-Abfrage")) from e


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False), structured_output=True)
async def epl_migel_suche(eingabe: MiGeLSucheInput, ctx: Context | None = None) -> MiGeLEnvelope:
    """
    Suche in der Mittel- und Gegenstaendeliste (MiGeL) nach Medizinprodukten.

    Die MiGeL enthaelt alle von der OKP vergueteten Mittel und Gegenstaende
    (KLV Art. 20), z.B. Rollstuehle, Hoergeraete, Inkontinenzprodukte.

    <use_case>Beantwortet \u00abUebernimmt die OKP das Hilfsmittel X (z.B.
    Rollstuhl, Hoergeraet)?\u00bb. Liefert Rechtsgrundlage (KLV Art. 20) und die
    offizielle MiGeL-Quelle. Fuer Medikamente stattdessen epl_sl_suche.
    </use_case>
    """
    _bind_call_context(ctx, "epl_migel_suche")
    try:
        # ARCH-003: Phase 1 liefert noch keine Live-Treffer -> match_type "none"
        # mit Handlungshinweis (offizieller Link).
        envelope = MiGeLEnvelope(
            source="BAG MiGeL",
            provenance=_provenance("BAG MiGeL", MIGEL_INFO_URL),
            suchbegriff=eingabe.suchbegriff,
            status="Phase 1 \u2014 Kategorie-basierte Information",
            erklaerung=(
                f"Die MiGeL-Suche nach \u00ab{eingabe.suchbegriff}\u00bb liefert Informationen "
                "zu vergueteten Medizinprodukten und Hilfsmitteln."
            ),
            link=MIGEL_INFO_URL,
            rechtsgrundlage="KLV Art. 20 / MiGeL-Verordnung",
            migel_integration="MiGeL wird voraussichtlich 2026/2027 in die ePL integriert.",
        )

        if eingabe.format == ResponseFormat.JSON:
            text = json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, indent=2)
            return _structured_result(text, envelope)

        md = f"## MiGeL-Suche: \u00ab{eingabe.suchbegriff}\u00bb\n\n"
        md += f"> {envelope.erklaerung}\n\n"
        md += f"**Offizielle Quelle:** [BAG MiGeL]({envelope.link})\n\n"
        md += f"**Rechtsgrundlage:** {envelope.rechtsgrundlage}\n\n"
        md += f"**ePL-Integration:** {envelope.migel_integration}\n"
        md += f"\n---\n*Quelle: BAG MiGeL \u00b7 Lizenz: {OGD_LICENSE} \u00b7 {MIGEL_INFO_URL}*\n"
        return _structured_result(md, envelope)

    except ToolError:
        raise
    except Exception as e:
        raise ToolError(_handle_error(e, "MiGeL-Suche")) from e


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False), structured_output=True)
async def epl_gesuchseingaenge(ctx: Context | None = None) -> GesuchseingaengeEnvelope:
    """
    Aktuelle Gesuchseingaenge fuer die Spezialitaetenliste abrufen.

    Transparenzliste: Zeigt, welche Medikamente aktuell zur Aufnahme
    in die SL beantragt sind.

    <use_case>Beantwortet «Welche Medikamente sind aktuell zur Aufnahme in die
    SL beantragt?» (Transparenz/Monitoring). Verweist auf die offizielle
    BAG-Transparenzliste.</use_case>
    """
    _bind_call_context(ctx, "epl_gesuchseingaenge")
    try:
        envelope = GesuchseingaengeEnvelope(
            source="BAG Spezialitaetenliste (SL)",
            provenance=_provenance("BAG Spezialitaetenliste (SL)", SL_BASE_URL),
            beschreibung=(
                "Die Gesuchseingaenge zeigen, welche Arzneimittel aktuell zur Aufnahme "
                "in die Spezialitaetenliste beantragt wurden. Diese Transparenzliste wird "
                "periodisch vom BAG aktualisiert."
            ),
            link=f"{SL_BASE_URL}/#/applications",
            direkt_link_bag=f"{BAG_DOWNLOAD_URL}/Arzneimittel/gesuchseingaenge.html",
            hinweis=(
                "Die vollstaendige Liste der Gesuchseingaenge ist auf sl.bag.admin.ch einsehbar. "
                "Die API-basierte Abfrage wird mit Phase 2 (FHIR) verfuegbar."
            ),
        )

        md = "## Gesuchseingaenge Spezialitaetenliste\n\n"
        md += f"> {envelope.beschreibung}\n\n"
        md += f"**SL-Portal:** [Gesuchseingaenge ansehen]({envelope.link})\n\n"
        md += f"**BAG-Seite:** [Offizielle BAG-Seite]({envelope.direkt_link_bag})\n\n"
        md += f"**Hinweis:** {envelope.hinweis}\n"
        md += f"\n---\n*Quelle: BAG Spezialitaetenliste · Lizenz: {OGD_LICENSE} · {SL_BASE_URL}*\n"
        return _structured_result(md, envelope)

    except ToolError:
        raise
    except Exception as e:
        raise ToolError(_handle_error(e, "Gesuchseingaenge")) from e


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False), structured_output=True)
async def epl_rechtskontext(eingabe: RechtskontextInput, ctx: Context | None = None) -> RechtskontextEnvelope:
    """
    Rechtlichen Kontext zur Kassenpflicht liefern.

    Gibt strukturierte Informationen zu den Rechtsgrundlagen der
    obligatorischen Krankenpflegeversicherung (WZW-Kriterien, KVG, KLV).

    <use_case>Beantwortet «Auf welcher rechtlichen Grundlage beruht die
    Kassenpflicht?» und erklaert die WZW-Kriterien (Wirksamkeit,
    Zweckmaessigkeit, Wirtschaftlichkeit) mit Fedlex-Verweisen. Ergaenzt die
    Such-Tools um den juristischen Kontext.</use_case>
    """
    _bind_call_context(ctx, "epl_rechtskontext")
    try:
        envelope = RechtskontextEnvelope(
            source="Fedlex (Bundesrecht)",
            provenance=_provenance("Fedlex (Bundesrecht)", "https://www.fedlex.admin.ch"),
            frage=eingabe.frage,
            gesetze=[
                Gesetz(
                    kuerzel="KVG",
                    titel="Bundesgesetz ueber die Krankenversicherung",
                    sr_nummer="SR 832.10",
                    fedlex="https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de",
                    relevante_artikel=["Art. 25 (Leistungen)", "Art. 32 (WZW)", "Art. 52 (SL)"],
                ),
                Gesetz(
                    kuerzel="KLV",
                    titel="Krankenpflege-Leistungsverordnung",
                    sr_nummer="SR 832.112.31",
                    fedlex="https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de",
                    relevante_artikel=["Art. 20 (MiGeL)", "Art. 30ff (SL-Aufnahme)"],
                ),
                Gesetz(
                    kuerzel="IVG",
                    titel="Bundesgesetz ueber die Invalidenversicherung",
                    sr_nummer="SR 831.20",
                    fedlex="https://www.fedlex.admin.ch/eli/cc/1959/827_857_845/de",
                    relevante_artikel=["Art. 13 (Geburtsgebrechen)"],
                ),
                Gesetz(
                    kuerzel="GgV",
                    titel="Verordnung ueber Geburtsgebrechen",
                    sr_nummer="SR 831.232.21",
                    fedlex="https://www.fedlex.admin.ch/eli/cc/1986/40_40_40/de",
                    relevante_artikel=["Anhang (Liste der Geburtsgebrechen)"],
                ),
            ],
            wzw_kriterien={
                "wirksamkeit": "Das Arzneimittel muss wirksam sein (klinische Studien).",
                "zweckmaessigkeit": "Der Einsatz muss zweckmaessig sein (Nutzen-Risiko).",
                "wirtschaftlichkeit": "Die Kosten muessen in einem angemessenen Verhaeltnis stehen.",
            },
            hinweis="Fuer verbindliche Rechtsauskunft konsultieren Sie die offiziellen Fedlex-Quellen.",
        )

        if eingabe.format == ResponseFormat.JSON:
            text = json.dumps(envelope.model_dump(mode="json"), ensure_ascii=False, indent=2)
            return _structured_result(text, envelope)

        md = f"## Rechtskontext: {eingabe.frage}\n\n"
        md += "### Relevante Gesetze\n\n"
        for g in envelope.gesetze:
            md += f"#### {g.kuerzel} \u2014 {g.titel}\n"
            md += f"- **SR-Nummer:** {g.sr_nummer}\n"
            md += f"- **Fedlex:** [{g.kuerzel} auf Fedlex]({g.fedlex})\n"
            md += f"- **Relevante Artikel:** {', '.join(g.relevante_artikel)}\n\n"

        md += "### WZW-Kriterien (KVG Art. 32)\n\n"
        for k, v in envelope.wzw_kriterien.items():
            md += f"- **{k.capitalize()}:** {v}\n"

        md += f"\n> **Hinweis:** {envelope.hinweis}\n"
        return _structured_result(md, envelope)

    except ToolError:
        raise
    except Exception as e:
        raise ToolError(_handle_error(e, "Rechtskontext")) from e


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False), structured_output=True)
async def epl_server_info(ctx: Context | None = None) -> ServerInfoEnvelope:
    """
    Serverstatus und API-Phaseninformation anzeigen.

    Liefert Informationen zum aktuellen Funktionsumfang und den geplanten
    Erweiterungen des BAG-ePL-MCP-Servers.

    <use_case>Beantwortet \u00abWas kann dieser Server, welche MCP-Version und welche
    Phase?\u00bb. Nuetzlich zum Discovery der verfuegbaren Tools und des
    Roadmap-Stands.</use_case>
    """
    _bind_call_context(ctx, "epl_server_info")
    envelope = ServerInfoEnvelope(
        source="bag-epl-mcp",
        provenance=_provenance("bag-epl-mcp", "https://github.com/malkreide/bag-epl-mcp"),
        server="bag-epl-mcp",
        version="0.2.0",
        protocol_version=PROTOCOL_VERSION,
        license=OGD_LICENSE,
        phase="Phase 1 \u2014 XML/XLSX-Downloads + SL-Website-Zugriff",
        tools={
            "epl_sl_suche": "Medikamentensuche in der Spezialitaetenliste (SL)",
            "epl_ggsl_abfrage": "GGSL-Deckung bei Geburtsgebrechen pruefen",
            "epl_migel_suche": "Medizinprodukte in der MiGeL suchen",
            "epl_gesuchseingaenge": "SL-Gesuchseingaenge (Transparenz)",
            "epl_rechtskontext": "Rechtliche Grundlagen zur Kassenpflicht",
            "epl_server_info": "Serverstatus (dieses Tool)",
        },
        phasen={
            "phase_1": "XML/XLSX-Downloads + SL-Website (aktuell)",
            "phase_2": "FHIR/IDMP-API des BAG (~2025/2026)",
            "phase_3": "MiGeL + AL via ePL-FHIR (2026/2027)",
        },
        datenquellen={
            "sl": f"{SL_BASE_URL} \u2014 Spezialitaetenliste",
            "ggsl": GGSL_INFO_URL,
            "migel": MIGEL_INFO_URL,
        },
    )

    md = "## BAG ePL MCP Server \u2014 Status\n\n"
    md += f"**Version:** {envelope.version}\n\n"
    md += f"**MCP-Protokoll:** {envelope.protocol_version}\n\n"
    md += f"**Aktuelle Phase:** {envelope.phase}\n\n"
    md += "### Verfuegbare Tools\n\n"
    for tool, desc in envelope.tools.items():
        md += f"| `{tool}` | {desc} |\n"
    md += "\n### Phasenplan\n\n"
    for phase, desc in envelope.phasen.items():
        md += f"- **{phase}:** {desc}\n"
    return _structured_result(md, envelope)


# ─────────────────────────── Resources ─────────────────────────────────────────

@mcp.resource("epl://uebersicht")
def epl_uebersicht() -> str:
    """Uebersicht ueber die ePL-Datenquellen und den aktuellen Funktionsumfang."""
    return (
        "# BAG ePL \u2014 Uebersicht\n\n"
        "Die elektronische Plattform Leistungen (ePL) des BAG umfasst drei Listen:\n\n"
        "1. **Spezialitaetenliste (SL)** \u2014 Kassenpflichtige Medikamente (KVG Art. 52)\n"
        "2. **GGSL** \u2014 Medikamente bei Geburtsgebrechen (IVG)\n"
        "3. **MiGeL** \u2014 Medizinprodukte und Hilfsmittel (KLV Art. 20)\n\n"
        "## Aktueller Stand\n"
        "- Phase 1: SL-Website-Zugriff + strukturierte Rechtsinfo\n"
        "- Phase 2 (geplant): FHIR/IDMP-API\n"
        "- Phase 3 (Vision): Volle ePL-Integration\n"
    )


@mcp.resource("epl://rechtsrahmen")
def epl_rechtsrahmen() -> str:
    """Rechtsrahmen der obligatorischen Krankenpflegeversicherung."""
    return (
        "# Rechtsrahmen OKP\n\n"
        "| Gesetz | SR-Nummer | Thema |\n"
        "|--------|-----------|-------|\n"
        "| KVG | SR 832.10 | Krankenversicherungsgesetz |\n"
        "| KLV | SR 832.112.31 | Leistungsverordnung |\n"
        "| IVG | SR 831.20 | Invalidenversicherung |\n"
        "| GgV | SR 831.232.21 | Geburtsgebrechen |\n\n"
        "## WZW-Kriterien (KVG Art. 32)\n"
        "- **Wirksamkeit** \u2014 klinisch belegt\n"
        "- **Zweckmaessigkeit** \u2014 angemessenes Nutzen-Risiko-Verhaeltnis\n"
        "- **Wirtschaftlichkeit** \u2014 Kosten im Verhaeltnis zum Nutzen\n"
    )


# ─────────────────────────── Prompts ───────────────────────────────────────────

@mcp.prompt()
def epl_kassenpflicht_check(medikament: str) -> str:
    """Strukturierter Workflow: Ist ein Medikament kassenpflichtig?"""
    return (
        f"Pruefe, ob \u00ab{medikament}\u00bb von der obligatorischen Krankenpflegeversicherung "
        "verguetet wird. Gehe dabei wie folgt vor:\n\n"
        f"1. Suche \u00ab{medikament}\u00bb in der Spezialitaetenliste (epl_sl_suche)\n"
        "2. Pruefe die Rechtsgrundlage (epl_rechtskontext)\n"
        "3. Falls fuer Geburtsgebrechen relevant: GGSL pruefen (epl_ggsl_abfrage)\n"
        "4. Falls Medizinprodukt: MiGeL pruefen (epl_migel_suche)\n"
        "5. Fasse die Ergebnisse zusammen mit Quellenangaben\n"
    )


@mcp.prompt()
def epl_schulgesundheit_recherche(thema: str) -> str:
    """Recherche-Workflow fuer Schulgesundheitsdienst-Anfragen."""
    return (
        f"Recherchiere zum Thema \u00ab{thema}\u00bb im Kontext des Schulgesundheitsdienstes:\n\n"
        "1. Pruefe Medikamenten-Kassenpflicht (epl_sl_suche)\n"
        "2. Klaere rechtliche Grundlagen (epl_rechtskontext)\n"
        "3. Bei Hilfsmitteln: MiGeL-Abdeckung pruefen (epl_migel_suche)\n"
        "4. Bei Geburtsgebrechen: IV-Deckung klaeren (epl_ggsl_abfrage)\n"
        "5. Gib eine strukturierte Zusammenfassung fuer Schulleitung/Eltern\n"
    )


# ─────────────────────────── Einstiegspunkt ────────────────────────────────────

def _build_http_app():
    """
    Baut die Streamable-HTTP-Starlette-App fuer Cloud-Deployments.

    * Health-Endpoint ``/healthz`` fuer Load-Balancer (SCALE-004) — das
      ``/mcp``-Endpoint verlangt Session-Header und eignet sich nicht als Probe.
    * CORS-Middleware, damit Browser-Clients (claude.ai) den
      ``Mcp-Session-Id``-Header lesen koennen (SDK-004); Origins aus der
      expliziten Allow-List (kein Wildcard).
    """
    from starlette.middleware.cors import CORSMiddleware
    from starlette.requests import Request
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def _healthz(_request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    app = mcp.streamable_http_app()
    app.router.routes.append(Route("/healthz", _healthz, methods=["GET"]))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Mcp-Session-Id", "Content-Type", "Authorization"],
        expose_headers=["Mcp-Session-Id"],
    )
    return app


def _init_otel(app) -> None:
    """
    OBS-006: OpenTelemetry-Tracing, standardmaessig aktiv (mit ``MCP_OTEL_ENABLED=0``
    abschaltbar).

    Auto-Instrumentierung der ASGI-App und des HTTP-Clients erzeugt Spans pro
    Request bzw. ausgehendem Backend-Call. Exporter/Endpoint werden ueber die
    Standard-``OTEL_*``-Umgebungsvariablen konfiguriert. Keine sensiblen Daten
    (PII/Credentials) in Span-Attributen — die Auto-Instrumentierung loggt nur
    Methode/Status/URL.

    Ist das ``[otel]``-Extra nicht installiert, ist dies ein stiller No-op
    (Base-Installs bleiben unveraendert), damit „aktiv per Default" nicht zur
    harten Abhaengigkeit wird.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.starlette import StarletteInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        log.debug("otel_unavailable", hint="install the '[otel]' extra to enable tracing")
        return
    # TracerProvider + OTLP-Exporter; Endpoint via OTEL_EXPORTER_OTLP_ENDPOINT.
    provider = TracerProvider(resource=Resource.create({"service.name": "bag-epl-mcp"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    StarletteInstrumentor().instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    log.info("otel_enabled")


def _run_http() -> None:
    """Streamable-HTTP-Transport fuer Cloud-Deployments (Render etc.) starten."""
    import uvicorn

    app = _build_http_app()
    if settings.otel_enabled:
        _init_otel(app)
    log.info("http_listen", host=settings.host, port=settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port)


def main() -> None:
    """
    Einstiegspunkt. Transport-Wahl ausschliesslich ueber ``MCP_TRANSPORT``:

    * ``stdio`` (Default) — lokal / Claude Desktop. Oeffnet keine Netzwerk-Ports.
    * ``streamable-http`` / ``http`` — Cloud (Render), bindet an ``MCP_HOST``/``MCP_PORT``.
    """
    if settings.transport in ("http", "streamable-http"):
        _run_http()
    else:
        mcp.run()  # stdio (Default)


if __name__ == "__main__":
    main()
