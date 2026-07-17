#!/usr/bin/env python3
"""
parlament-mcp – Schweizer Parlament MCP Server

AI-nativer Zugang zum Schweizer Bundesparlament via Curia Vista OData API:
  · Vorstösse (Motionen, Postulate, Interpellationen, Anfragen)
  · Abstimmungen im Rat
  · Ratsmitglieder (National- und Ständerat)
  · Sessionen
  · Debatten-Transkripte (Amtliches Bulletin)

Kein API-Schlüssel erforderlich. Alle Daten öffentlich zugänglich.

Tools liefern strukturierte Pydantic-Modelle (typisierte `results` + Envelope
mit source/license/provenance/match_type/count). FastMCP exponiert daraus ein
Output-Schema.
"""

from __future__ import annotations

import asyncio
import functools
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field

from parlament_mcp.config import (
    DATA_LICENSE,
    DATA_SOURCE,
    PROTOCOL_VERSION,
    Settings,
    warn_on_dangerous_binding,
)
from parlament_mcp.logging_setup import configure_logging, get_logger
from parlament_mcp.observability import setup_tracing, tool_span
from parlament_mcp.security import assert_host_allowed

# ─────────────────────────── Konstanten ────────────────────────────────────────
BASE_URL = "https://ws.parlament.ch/odata.svc"
DEFAULT_LANG = "DE"
HTTP_TIMEOUT = 20.0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# Stichwort-Vorschläge bei leeren Treffern (ARCH-003 — kein blankes "not found").
_SEARCH_SUGGESTIONS = [
    "Künstliche Intelligenz",
    "Bildung",
    "Digitalisierung",
    "Klima",
    "Gesundheit",
]

# Strukturiertes Logging auf stderr aktivieren (OBS-003/OBS-004) — beim Import,
# damit stdout-Verschmutzung im stdio-Modus ausgeschlossen ist.
configure_logging()
_logger = get_logger("parlament_mcp")

# ─────────────────────────── HTTP-Client (geteilt) ─────────────────────────────
# Ein gepoolter AsyncClient über die Server-Lebensdauer statt ein neuer Client
# pro Tool-Call. Der Lifespan baut den Connection-Pool auf und schliesst ihn.
_http_client: httpx.AsyncClient | None = None
# Event-Loop, an den der gepoolte Client gebunden ist. Ein httpx-Client (bzw.
# sein Connection-Pool) gehört dem Loop, auf dem er erzeugt wurde. Wird er auf
# einem anderen Loop weiterverwendet (z. B. function-scoped Test-Loops),
# schlägt das Schliessen der Pool-Verbindungen mit "Event loop is closed" fehl.
_http_client_loop: asyncio.AbstractEventLoop | None = None


def _get_client() -> httpx.AsyncClient:
    """Geteilten AsyncClient zurückgeben (lazy, falls kein Lifespan aktiv ist).

    Erkennt einen Loop-Wechsel und baut den Client neu auf, damit der
    Connection-Pool nie über die Grenze eines bereits geschlossenen Loops
    hinweg verwendet wird.
    """
    global _http_client, _http_client_loop
    running_loop = asyncio.get_running_loop()
    if (
        _http_client is None
        or _http_client.is_closed
        or _http_client_loop is not running_loop
    ):
        _http_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
        _http_client_loop = running_loop
    return _http_client


@asynccontextmanager
async def _lifespan(_server: FastMCP):
    """FastMCP-Lifespan: HTTP-Connection-Pool auf- und sauber wieder abbauen."""
    global _http_client, _http_client_loop
    _http_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    _http_client_loop = asyncio.get_running_loop()
    try:
        yield
    finally:
        await _http_client.aclose()
        _http_client = None
        _http_client_loop = None


# ─────────────────────────── Server ────────────────────────────────────────────
mcp = FastMCP("parlament_mcp", lifespan=_lifespan)

# Geschäftstyp-IDs (Curia Vista)
BUSINESS_TYPE_NAMES = {
    5: "Motion",
    6: "Postulat",
    8: "Interpellation",
    9: "Dringliche Interpellation",
    12: "Einfache Anfrage",
    18: "Anfrage",
    4: "Parlamentarische Initiative",
    3: "Standesinitiative",
    1: "Geschäft des Bundesrates",
}

_CURIA_URL = "https://www.parlament.ch/de/ratsbetrieb/suche-curia-vista/geschaeft?AffairId={}"


# ─────────────────────────── Enums ─────────────────────────────────────────────
class Language(StrEnum):
    """Verfügbare Sprachen der Curia Vista API."""
    DE = "DE"
    FR = "FR"
    IT = "IT"


# ─────────────────────────── Hilfsfunktionen ───────────────────────────────────
async def _odata_get(
    entity: str,
    filters: list[str] | None = None,
    orderby: str | None = None,
    top: int = DEFAULT_LIMIT,
    skip: int = 0,
    select: list[str] | None = None,
    lang: str = DEFAULT_LANG,
) -> list[dict[str, Any]]:
    """OData-GET-Anfrage ausführen und Ergebnisliste zurückgeben."""
    params: dict[str, str] = {
        "$format": "json",
        "$top": str(min(top, MAX_LIMIT)),
    }
    if skip:
        params["$skip"] = str(skip)

    # Immer nach Sprache filtern
    lang_filter = f"Language eq '{lang}'"
    all_filters = [lang_filter] + (filters or [])
    params["$filter"] = " and ".join(f"({f})" for f in all_filters)

    if orderby:
        params["$orderby"] = orderby
    if select:
        params["$select"] = ",".join(select)

    url = f"{BASE_URL}/{entity}"
    assert_host_allowed(url)  # Egress-Allow-List (SEC-021)
    client = _get_client()
    request = client.build_request("GET", url, params=params)
    response = await client.send(request)
    response.raise_for_status()
    data = response.json()
    return data.get("d", [])


def _handle_error(e: Exception) -> str:
    """Einheitliche, handlungsorientierte Fehlermeldungen (auf Deutsch)."""
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
    return f"Fehler: Unerwarteter Fehler ({type(e).__name__}): {e}"


def _tool_error(e: Exception) -> ToolError:
    """Ausführungsfehler in eine maskierte ToolError übersetzen (OBS-001/OBS-002).

    FastMCP liefert das dem Client als `isError`-Tool-Result (kein Protokoll-
    Fehler) – mit einer sauberen Meldung, ohne Stacktrace.
    """
    return ToolError(_handle_error(e))


def _parse_date(ms_date: str | None) -> str:
    """OData /Date(...)/ in ISO-String umwandeln."""
    if not ms_date:
        return ""
    try:
        ms = int(ms_date.replace("/Date(", "").replace(")/", ""))
        return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d")
    except Exception:
        return ms_date


def _fmt_business(b: dict) -> dict:
    """Geschäft-Dict für Tool-Antworten aufbereiten."""
    return {
        "id": b.get("ID"),
        "short_number": b.get("BusinessShortNumber"),
        "type": b.get("BusinessTypeName"),
        "title": b.get("Title"),
        "status": b.get("BusinessStatusText"),
        "status_date": _parse_date(b.get("BusinessStatusDate")),
        "submitted_by": b.get("SubmittedBy"),
        "submission_date": _parse_date(b.get("SubmissionDate")),
        "council": b.get("SubmissionCouncilAbbreviation"),
        "department": b.get("ResponsibleDepartmentAbbreviation"),
        "description": (b.get("Description") or "")[:400],
        "tags": b.get("TagNames"),
    }


def _instrument(name: str):
    """Decorator: pro Tool-Call ein OTel-Span + strukturiertes Logging (OBS-003/006)
    und – sofern verfügbar – ein ctx.info-Lifecycle-Event (SDK-003).

    Lässt die Signatur via functools.wraps intakt, damit FastMCP weiterhin das
    Pydantic-Eingabeschema baut und ``ctx`` injiziert.
    """

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(params, ctx: Context | None = None):
            log = _logger.bind(tool=name)
            if ctx is not None:
                try:
                    await ctx.info(f"{name} aufgerufen")
                except Exception:  # ctx-Logging darf den Tool-Call nie brechen
                    pass
            with tool_span(f"mcp.tool.{name}", **{"mcp.tool.name": name}):
                log.info("tool_invoked")
                try:
                    result = await fn(params, ctx)
                except ToolError:
                    log.warning("tool_failed")
                    raise
                except Exception as exc:  # noqa: BLE001 — in ToolError übersetzen
                    log.warning("tool_failed", error=type(exc).__name__)
                    raise _tool_error(exc) from exc
                log.info("tool_succeeded")
                return result

        return wrapper

    return decorator


# ─────────────────────────── Ausgabemodelle (SDK-002) ──────────────────────────
class ResponseEnvelope(BaseModel):
    """Konsistenter Envelope für Such-/Listen-Tools (SDK-002 + CH-004)."""

    source: str = DATA_SOURCE
    license: str = DATA_LICENSE
    provenance: Literal["live_api", "cached"] = "live_api"
    match_type: Literal["exact", "fuzzy", "none"] = "exact"
    count: int = 0
    offset: int = 0
    note: str | None = None
    suggestions: list[str] = Field(default_factory=list)


class BusinessSummary(BaseModel):
    id: int | None = None
    short_number: str | None = None
    type: str | None = None
    title: str | None = None
    status: str | None = None
    status_date: str | None = None
    submitted_by: str | None = None
    submission_date: str | None = None
    council: str | None = None
    department: str | None = None
    description: str | None = None
    tags: str | None = None
    url: str | None = None


class BusinessSearchResponse(ResponseEnvelope):
    results: list[BusinessSummary] = Field(default_factory=list)


class BusinessDetail(BaseModel):
    found: bool = True
    source: str = DATA_SOURCE
    license: str = DATA_LICENSE
    id: int | None = None
    short_number: str | None = None
    title: str | None = None
    type: str | None = None
    status: str | None = None
    status_date: str | None = None
    submitted_by: str | None = None
    council: str | None = None
    submission_date: str | None = None
    department: str | None = None
    url: str | None = None
    description: str | None = None
    initial_situation: str | None = None
    submitted_text: str | None = None
    motion_text: str | None = None
    federal_council_response: str | None = None
    proceedings: str | None = None
    tags: str | None = None


class MemberResult(BaseModel):
    id: int | None = None
    name: str | None = None
    council: str | None = None
    canton: str | None = None
    party: str | None = None
    group: str | None = None
    active: bool | None = None
    joining: str | None = None


class MemberSearchResponse(ResponseEnvelope):
    results: list[MemberResult] = Field(default_factory=list)


class VoteResult(BaseModel):
    id: int | None = None
    business_number: str | None = None
    business_title: str | None = None
    session: str | int | None = None
    meaning_yes: str | None = None
    meaning_no: str | None = None
    vote_end: str | None = None


class VotesResponse(ResponseEnvelope):
    results: list[VoteResult] = Field(default_factory=list)


class SessionResult(BaseModel):
    id: int | None = None
    name: str | None = None
    start: str | None = None
    end: str | None = None
    type: str | None = None
    legislative_period: int | None = None


class SessionsResponse(ResponseEnvelope):
    results: list[SessionResult] = Field(default_factory=list)


class TranscriptResult(BaseModel):
    speaker: str | None = None
    function: str | None = None
    canton: str | None = None
    group: str | None = None
    council: str | None = None
    date: str | None = None
    session: int | None = None
    business_title: str | None = None
    text_snippet: str | None = None


class TranscriptsResponse(ResponseEnvelope):
    results: list[TranscriptResult] = Field(default_factory=list)


def _none_envelope(cls, message: str):
    """Leer-Antwort mit Vorschlägen statt blankem „not found“ (ARCH-003)."""
    return cls(match_type="none", count=0, note=message, suggestions=_SEARCH_SUGGESTIONS)


# ─────────────────────────── Eingabemodelle ────────────────────────────────────
class SearchBusinessInput(BaseModel):
    """Eingabe für die Suche nach parlamentarischen Vorstössen."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str | None = Field(
        default=None,
        description=(
            "Stichwort für die Titelsuche. "
            "Beispiele: 'Künstliche Intelligenz', 'Bildung', 'Digitalisierung', 'Schule', 'KI'"
        ),
        min_length=1,
        max_length=200,
    )
    keyword2: str | None = Field(
        default=None,
        description="Zweites Stichwort (UND-verknüpft). Beispiel: 'Schule' wenn keyword='KI'.",
        min_length=1,
        max_length=200,
    )
    business_type: str | None = Field(
        default=None,
        description=(
            "Nach Geschäftstyp filtern. Gültige Werte: 'Motion', 'Postulat', 'Interpellation', "
            "'Parlamentarische Initiative', 'Standesinitiative', 'Anfrage', 'Einfache Anfrage'"
        ),
        max_length=60,
    )
    status: str | None = Field(
        default=None,
        description=(
            "Nach Status filtern. Häufige Werte: 'Eingereicht' (hängig), "
            "'Erledigt' (abgeschlossen), 'Überwiesen an den Bundesrat', "
            "'Angenommen', 'Abgelehnt'"
        ),
        max_length=80,
    )
    submitted_after: str | None = Field(
        default=None,
        description="Vorstösse nach diesem Datum (ISO-Format JJJJ-MM-TT).",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    council: str | None = Field(
        default=None,
        description="Nach Rat filtern: 'NR' (Nationalrat) oder 'SR' (Ständerat).",
        max_length=20,
    )
    limit: int = Field(
        default=20, description="Maximale Anzahl Ergebnisse (1–100).", ge=1, le=MAX_LIMIT, strict=True
    )
    offset: int = Field(default=0, description="Offset für Paginierung.", ge=0, strict=True)


class GetBusinessInput(BaseModel):
    """Eingabe zum Abrufen eines einzelnen Vorstosses nach ID."""

    model_config = ConfigDict(extra="forbid")

    business_id: int = Field(
        ..., description="Numerische Curia Vista Geschäfts-ID (z.B. 20254750).", gt=0, strict=True
    )
    language: Language = Field(default=Language.DE, description="Antwortsprache.")


class SearchMembersInput(BaseModel):
    """Eingabe für die Suche nach Ratsmitgliedern (Parlamentarier·innen)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    canton: str | None = Field(
        default=None, description="Nach Kanton filtern, z.B. 'ZH', 'BE', 'GE', 'AG'.", min_length=2, max_length=2
    )
    last_name: str | None = Field(
        default=None, description="Nach Nachname filtern (Teilübereinstimmung).", min_length=1, max_length=100
    )
    council: str | None = Field(
        default=None, description="Nach Rat filtern: 'NR' (Nationalrat) oder 'SR' (Ständerat).", max_length=20
    )
    party: str | None = Field(
        default=None, description="Nach Partei filtern, z.B. 'SP', 'SVP', 'FDP', 'Mitte', 'Grüne'.", max_length=20
    )
    active_only: bool = Field(default=True, description="Nur aktive Ratsmitglieder zurückgeben.")
    limit: int = Field(default=20, ge=1, le=MAX_LIMIT, strict=True)
    offset: int = Field(default=0, ge=0, strict=True)


class GetVotesInput(BaseModel):
    """Eingabe zum Abrufen parlamentarischer Abstimmungen."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str | None = Field(
        default=None, description="Stichwort im Geschäftstitel der Abstimmung (z.B. 'Bildung', 'KI').", min_length=1, max_length=200
    )
    session_id: int | None = Field(
        default=None, description="Abstimmungen einer bestimmten Session filtern.", gt=0, strict=True
    )
    limit: int = Field(default=20, ge=1, le=50, strict=True)
    offset: int = Field(default=0, ge=0, strict=True)


class GetSessionsInput(BaseModel):
    """Eingabe zum Auflisten parlamentarischer Sessionen."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=50, strict=True)
    offset: int = Field(default=0, ge=0, strict=True)


class GetTranscriptsInput(BaseModel):
    """Eingabe zum Abrufen von Debatten-Transkripten."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    keyword: str | None = Field(
        default=None, description="Stichwort im Transkripttext (z.B. 'KI', 'Schule').", min_length=1, max_length=200
    )
    speaker_name: str | None = Field(
        default=None, description="Nach Nachname des Redners filtern.", min_length=1, max_length=100
    )
    session_id: int | None = Field(
        default=None, description="Transkripte einer bestimmten Session filtern.", gt=0, strict=True
    )
    council: str | None = Field(default=None, description="Nach Rat filtern: 'NR' oder 'SR'.", max_length=20)
    limit: int = Field(default=15, ge=1, le=50, strict=True)
    offset: int = Field(default=0, ge=0, strict=True)


# ─────────────────────────── Tools ─────────────────────────────────────────────


@mcp.tool(
    name="parlament_search_business",
    annotations={
        "title": "Parlamentarische Vorstösse suchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_instrument("parlament_search_business")
async def parlament_search_business(
    params: SearchBusinessInput, ctx: Context | None = None
) -> BusinessSearchResponse:
    """Parlamentarische Vorstösse suchen (Motionen, Interpellationen, Postulate usw.).

    Durchsucht Curia Vista Geschäftsdaten von ws.parlament.ch.

    <use_case>Politische Recherche zu Bildungs-, Datenschutz- oder
    Verwaltungsthemen; hängige Vorstösse zu KI in der Bildung,
    Digitalisierungsinitiativen oder beliebigen Politikthemen finden.</use_case>

    <important_notes>Titel-Suche via OData substringof() (gross-/klein-sensitiv).
    Maximal 100 Treffer pro Aufruf; mit `offset` paginieren.</important_notes>

    <example>keyword='KI', keyword2='Schule', status='Eingereicht'</example>
    """
    filters: list[str] = []
    if params.keyword:
        filters.append(f"substringof('{params.keyword.replace(chr(39), chr(39) * 2)}',Title)")
    if params.keyword2:
        filters.append(f"substringof('{params.keyword2.replace(chr(39), chr(39) * 2)}',Title)")
    if params.business_type:
        filters.append(f"BusinessTypeName eq '{params.business_type.replace(chr(39), chr(39) * 2)}'")
    if params.status:
        filters.append(f"BusinessStatusText eq '{params.status.replace(chr(39), chr(39) * 2)}'")
    if params.council:
        council_map = {"NR": "Nationalrat", "SR": "Ständerat"}
        council_name = council_map.get(params.council.upper(), params.council)
        filters.append(f"SubmissionCouncilName eq '{council_name}'")
    if params.submitted_after:
        filters.append(f"SubmissionDate gt datetime'{params.submitted_after}T00:00:00'")

    results = await _odata_get(
        "Business", filters=filters, orderby="SubmissionDate desc", top=params.limit, skip=params.offset
    )
    if not results:
        return _none_envelope(BusinessSearchResponse, "Keine Vorstösse gefunden für die angegebenen Suchkriterien.")

    items = []
    for b in results:
        d = _fmt_business(b)
        d["url"] = _CURIA_URL.format(d["id"])
        items.append(BusinessSummary(**d))
    return BusinessSearchResponse(count=len(items), offset=params.offset, results=items)


@mcp.tool(
    name="parlament_get_business",
    annotations={
        "title": "Vorstoss-Details abrufen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_instrument("parlament_get_business")
async def parlament_get_business(
    params: GetBusinessInput, ctx: Context | None = None
) -> BusinessDetail:
    """Vollständige Details eines parlamentarischen Vorstosses nach Curia Vista ID abrufen.

    <use_case>Nach einer Suche verwenden, um vollständige Informationen inkl.
    Ausgangslage, Vorstosstext und Antwort des Bundesrats zu erhalten.</use_case>

    <important_notes>Benötigt die numerische Geschäfts-ID (aus
    parlament_search_business). `found=false` bei unbekannter ID.</important_notes>
    """
    url = f"{BASE_URL}/Business(ID={params.business_id},Language='{params.language.value}')"
    assert_host_allowed(url)
    client = _get_client()
    resp = await client.get(url, params={"$format": "json"})
    resp.raise_for_status()
    data = resp.json()

    b = data.get("d", data)
    if not b or not b.get("ID"):
        return BusinessDetail(found=False, id=params.business_id)

    return BusinessDetail(
        found=True,
        id=b.get("ID"),
        short_number=b.get("BusinessShortNumber"),
        title=b.get("Title"),
        type=b.get("BusinessTypeName"),
        status=b.get("BusinessStatusText"),
        status_date=_parse_date(b.get("BusinessStatusDate")),
        submitted_by=b.get("SubmittedBy"),
        council=b.get("SubmissionCouncilName"),
        submission_date=_parse_date(b.get("SubmissionDate")),
        department=b.get("ResponsibleDepartmentName"),
        url=_CURIA_URL.format(b.get("ID")),
        description=b.get("Description") or None,
        initial_situation=b.get("InitialSituation") or None,
        submitted_text=b.get("SubmittedText") or None,
        motion_text=b.get("MotionText") or None,
        federal_council_response=b.get("FederalCouncilResponseText") or None,
        proceedings=b.get("Proceedings") or None,
        tags=b.get("TagNames") or None,
    )


@mcp.tool(
    name="parlament_search_members",
    annotations={
        "title": "Ratsmitglieder suchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_instrument("parlament_search_members")
async def parlament_search_members(
    params: SearchMembersInput, ctx: Context | None = None
) -> MemberSearchResponse:
    """National- und Ständeräte suchen.

    <use_case>Alle Zürcher Ratsmitglieder ('ZH') oder Mitglieder einer
    bestimmten Partei finden. Synergie: mit parlament_search_business
    kombinieren, um Urheber von Vorstössen zu identifizieren.</use_case>

    <important_notes>`active_only=True` (Default) liefert nur amtierende
    Mitglieder. Kanton als 2-Buchstaben-Kürzel.</important_notes>
    """
    filters: list[str] = []
    if params.active_only:
        filters.append("Active eq true")
    if params.canton:
        filters.append(f"CantonAbbreviation eq '{params.canton.upper()}'")
    if params.last_name:
        filters.append(f"substringof('{params.last_name.replace(chr(39), chr(39) * 2)}',LastName)")
    if params.council:
        council_map = {"NR": "Nationalrat", "SR": "Ständerat"}
        filters.append(f"CouncilName eq '{council_map.get(params.council.upper(), params.council)}'")
    if params.party:
        filters.append(f"PartyAbbreviation eq '{params.party.replace(chr(39), chr(39) * 2)}'")

    results = await _odata_get(
        "MemberCouncil", filters=filters, orderby="LastName asc", top=params.limit, skip=params.offset
    )
    if not results:
        return _none_envelope(MemberSearchResponse, "Keine Ratsmitglieder gefunden.")

    items = [
        MemberResult(
            id=m.get("ID"),
            name=f"{m.get('FirstName')} {m.get('LastName')}",
            council=m.get("CouncilAbbreviation"),
            canton=m.get("CantonAbbreviation"),
            party=m.get("PartyAbbreviation"),
            group=m.get("ParlGroupAbbreviation"),
            active=m.get("Active"),
            joining=_parse_date(m.get("DateJoining")),
        )
        for m in results
    ]
    return MemberSearchResponse(count=len(items), offset=params.offset, results=items)


@mcp.tool(
    name="parlament_get_votes",
    annotations={
        "title": "Parlamentarische Abstimmungen abrufen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_instrument("parlament_get_votes")
async def parlament_get_votes(params: GetVotesInput, ctx: Context | None = None) -> VotesResponse:
    """Parlamentarische Abstimmungen (im Rat) mit Ja/Nein-Bedeutung abrufen.

    <use_case>Zeigt, wie der Rat über Themen wie KI-Regulierung,
    Bildungsfinanzierung oder Digitalisierungsprojekte abgestimmt hat.</use_case>

    <important_notes>`meaning_yes`/`meaning_no` erklären, was ein Ja/Nein im
    konkreten Geschäft bedeutet – wichtig zur korrekten Interpretation.</important_notes>
    """
    filters: list[str] = []
    if params.keyword:
        filters.append(f"substringof('{params.keyword.replace(chr(39), chr(39) * 2)}',BusinessTitle)")
    if params.session_id:
        filters.append(f"IdSession eq {params.session_id}")

    results = await _odata_get(
        "Vote", filters=filters, orderby="ID desc", top=params.limit, skip=params.offset
    )
    if not results:
        return _none_envelope(VotesResponse, "Keine Abstimmungen gefunden.")

    items = [
        VoteResult(
            id=v.get("ID"),
            business_number=v.get("BusinessShortNumber"),
            business_title=v.get("BusinessTitle"),
            session=v.get("SessionName") or v.get("IdSession"),
            meaning_yes=v.get("MeaningYes"),
            meaning_no=v.get("MeaningNo"),
            vote_end=_parse_date(v.get("VoteEnd")),
        )
        for v in results
    ]
    return VotesResponse(count=len(items), offset=params.offset, results=items)


@mcp.tool(
    name="parlament_get_sessions",
    annotations={
        "title": "Parlamentarische Sessionen auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_instrument("parlament_get_sessions")
async def parlament_get_sessions(params: GetSessionsInput, ctx: Context | None = None) -> SessionsResponse:
    """Aktuelle parlamentarische Sessionen mit Daten auflisten.

    <use_case>Session-IDs aus dieser Liste zum Filtern von Abstimmungen oder
    Transkripten verwenden.</use_case>

    <important_notes>Session-Namen können für sehr aktuelle Sessionen `null`
    sein – dann die Session-ID verwenden.</important_notes>
    """
    results = await _odata_get("Session", orderby="ID desc", top=params.limit, skip=params.offset)
    if not results:
        return _none_envelope(SessionsResponse, "Keine Sessionen gefunden.")

    items = [
        SessionResult(
            id=s.get("ID"),
            name=s.get("SessionName") or s.get("Abbreviation"),
            start=_parse_date(s.get("StartDate")),
            end=_parse_date(s.get("EndDate")),
            type=s.get("TypeName"),
            legislative_period=s.get("LegislativePeriodNumber"),
        )
        for s in results
    ]
    return SessionsResponse(count=len(items), offset=params.offset, results=items)


@mcp.tool(
    name="parlament_get_transcripts",
    annotations={
        "title": "Debatten-Transkripte abrufen (Amtliches Bulletin)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@_instrument("parlament_get_transcripts")
async def parlament_get_transcripts(
    params: GetTranscriptsInput, ctx: Context | None = None
) -> TranscriptsResponse:
    """Auszüge aus parlamentarischen Debatten-Transkripten (Amtliches Bulletin) abrufen.

    <use_case>Finden, was bestimmte Ratsmitglieder zu KI, Digitalisierung in der
    Schule oder anderen Themen gesagt haben. Synergie mit fedlex-mcp: vom
    Gesetzestext zur parlamentarischen Debatte.</use_case>

    <important_notes>Volltext-Suche kann bei breiten Abfragen langsam sein –
    `limit` setzen und Begriff eingrenzen.</important_notes>
    """
    filters: list[str] = []
    if params.keyword:
        filters.append(f"substringof('{params.keyword.replace(chr(39), chr(39) * 2)}',Text)")
    if params.speaker_name:
        filters.append(f"substringof('{params.speaker_name.replace(chr(39), chr(39) * 2)}',SpeakerLastName)")
    if params.session_id:
        filters.append(f"IdSession eq {params.session_id}")
    if params.council:
        council_map = {"NR": "Nationalrat", "SR": "Ständerat"}
        filters.append(f"CouncilName eq '{council_map.get(params.council.upper(), params.council)}'")

    results = await _odata_get(
        "Transcript", filters=filters, orderby="MeetingDate desc", top=params.limit, skip=params.offset
    )
    if not results:
        return _none_envelope(TranscriptsResponse, "Keine Transkripte gefunden für die angegebenen Kriterien.")

    items = []
    total = len(results)
    for i, t in enumerate(results):
        if ctx is not None and i % 5 == 0:  # Fortschritt (SDK-003)
            try:
                await ctx.report_progress(progress=i, total=total)
            except Exception:
                pass
        items.append(
            TranscriptResult(
                speaker=t.get("SpeakerFullName"),
                function=t.get("SpeakerFunction"),
                canton=t.get("CantonAbbreviation"),
                group=t.get("ParlGroupAbbreviation"),
                council=t.get("CouncilName"),
                date=(t.get("MeetingDate") or "")[:10],
                session=t.get("IdSession"),
                business_title=t.get("VoteBusinessTitle"),
                text_snippet=(t.get("Text") or "")[:500],
            )
        )
    return TranscriptsResponse(count=len(items), offset=params.offset, results=items)


# ─────────────────────────── HTTP-App mit CORS + Auth ──────────────────────────
def create_http_app():
    """Starlette-ASGI-App für Streamable HTTP mit CORS (SDK-004) und optionaler
    Bearer-Auth/Session-Bindung (SEC-009).

    - CORS exponiert ``Mcp-Session-Id`` (sonst können Browser-Clients die Session
      nicht lesen); Origins via ``MCP_ALLOWED_ORIGINS`` (CSV).
    - Wenn ``MCP_BEARER_TOKENS`` gesetzt ist, wird pro Request ein gültiges
      Bearer-Token verlangt; die User-Identität kommt aus dem validierten Token,
      nicht aus einem Session-Header.

    Verwendung::

        uvicorn parlament_mcp.server:create_http_app --factory --host 0.0.0.0 --port 8080
    """
    import os

    from starlette.middleware.cors import CORSMiddleware

    from parlament_mcp.auth import build_bearer_middleware

    origins = [o.strip() for o in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    app = mcp.streamable_http_app()
    # Auth zuerst registrieren (läuft als äusserste Schicht vor CORS-geschütztem Handler).
    app.add_middleware(build_bearer_middleware())
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Mcp-Session-Id", "Authorization"],
        expose_headers=["Mcp-Session-Id"],  # ← kritisch für Browser-Clients
        allow_credentials=bool(origins),
    )
    return app


# ─────────────────────────── Einstiegspunkt ────────────────────────────────────
def _resolve_settings() -> Settings:
    """Settings laden und CLI-Aliasse (--http/--port) + Railway-PORT verrechnen."""
    import os
    import sys

    settings = Settings()
    if "--http" in sys.argv and "MCP_TRANSPORT" not in os.environ:
        settings.transport = "streamable-http"
    if settings.transport == "http":
        settings.transport = "streamable-http"
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            settings.port = int(sys.argv[i + 1])
    if "MCP_PORT" not in os.environ and os.environ.get("PORT"):
        settings.port = int(os.environ["PORT"])
    return settings


def main() -> None:
    settings = _resolve_settings()
    configure_logging(level=settings.log_level, json_logs=settings.json_logs)
    if settings.otel_enabled:
        setup_tracing()

    _logger.info("server_start", transport=settings.transport, protocol_version=PROTOCOL_VERSION)

    if settings.transport == "stdio":
        mcp.run(transport="stdio")
    elif settings.transport in ("sse", "streamable-http"):
        warn_on_dangerous_binding(settings.host)
        mcp.run(transport=settings.transport, host=settings.host, port=settings.port)
    else:
        raise SystemExit(
            f"Unbekannter MCP_TRANSPORT: {settings.transport!r} "
            "(erlaubt: stdio, sse, streamable-http)"
        )


if __name__ == "__main__":
    main()
