"""FastMCP server for the Lobbywatch.ch lobby database.

Phase 1 tools (No-Auth-First, CC BY-SA attributed). All tool names use the
``lobbywatch_`` namespace prefix to avoid collision with sibling portfolio
servers (audit SEC-022, breaking change in 0.2.0):

    * lobbywatch_get_parlamentarier
    * lobbywatch_list_interessenbindungen
    * lobbywatch_search_parlamentarier_nach_branche
    * lobbywatch_get_lobbygruppe            (live dataIF)
    * lobbywatch_get_ranking
    * lobbywatch_get_transparenzquote
    * lobbywatch_refresh_dump
    * lobbywatch_dump_status

Anchor demo query (Schulamt / KI-Fachgruppe context):

    "Welche Mitglieder der WBK-N haben Interessenbindungen zu Bildungsverlagen
    oder privaten Bildungstraegern, und wie ist ihre Transparenz-Bewertung?"
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal, TypeVar

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData, ToolAnnotations
from pydantic import Field

from lobbywatch_mcp._observability import observed_tool
from lobbywatch_mcp.client import LobbywatchClient
from lobbywatch_mcp.config import ATTRIBUTION
from lobbywatch_mcp.models import (
    BrancheSearchHit,
    BrancheSearchResponse,
    DumpStatusResponse,
    Interessenbindung,
    InteressenbindungenResponse,
    Lobbygruppe,
    LobbygruppeResponse,
    ParlamentarierDetail,
    ParlamentarierResponse,
    ParlamentarierSuggestion,
    ParlamentarierSummary,
    RankingEntry,
    RankingResponse,
    TransparenzResponse,
)

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


async def _coerce_upstream(coro: Awaitable[_T]) -> _T:
    """Run a client coroutine and convert internal/upstream failures into a
    typed protocol-layer ``McpError`` (audit OBS-001).

    FastMCP would otherwise auto-coerce any uncaught ``RuntimeError`` /
    ``httpx.HTTPError`` into a generic INTERNAL_ERROR — surfacing the same
    JSON-RPC code regardless of root cause. By raising ``McpError``
    explicitly here we keep the categorisation intentional and log the
    underlying exception for operators.
    """
    try:
        return await coro
    except McpError:
        raise
    except (RuntimeError, httpx.HTTPError) as exc:
        logger.error("Lobbywatch upstream failure: %r", exc)
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Lobbywatch upstream error: {exc}",
            )
        ) from exc


# ---------------------------------------------------------------------------
# Projection helpers (dump record -> model)
# ---------------------------------------------------------------------------


def _split_kommissionen(record: dict[str, Any]) -> list[str]:
    raw = record.get("kommissionen_abkuerzung_de") or record.get("kommissionen_abkuerzung") or ""
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _to_bool(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "y", "yes", "true", "ja"):
            return True
        if v in ("0", "n", "no", "false", "nein"):
            return False
    return None


def _ib_to_model(ib: dict[str, Any]) -> Interessenbindung:
    organisation = ib.get("organisation") or {}
    return Interessenbindung(
        id=ib.get("id"),
        parlamentarier_id=ib.get("parlamentarier_id"),
        organisation_id=ib.get("organisation_id"),
        organisation_name=organisation.get("anzeige_name") or organisation.get("name"),
        branche=(organisation.get("branche") or {}).get("name")
        if isinstance(organisation.get("branche"), dict)
        else organisation.get("branche"),
        art=ib.get("art"),
        funktion_im_gremium=ib.get("funktion_im_gremium"),
        deklarationstyp=ib.get("deklarationstyp"),
        status=ib.get("status"),
        hauptberuflich=_to_bool(ib.get("hauptberuflich")),
        behoerden_vertreter=_to_bool(ib.get("behoerden_vertreter")),
        beschreibung=ib.get("beschreibung"),
        quelle_url=ib.get("quelle_url"),
        von=ib.get("von"),
        bis=ib.get("bis"),
        aktiv=_to_bool(ib.get("aktiv")),
    )


def _summary_from_record(record: dict[str, Any]) -> ParlamentarierSummary:
    ibs = record.get("interessenbindungen") or []
    hauptberuflich_count = sum(1 for ib in ibs if _to_bool(ib.get("hauptberuflich")))
    return ParlamentarierSummary(
        id=int(record.get("id") or 0),
        anzeige_name=record.get("anzeige_name") or "",
        partei=record.get("partei"),
        kanton=record.get("kanton"),
        rat=record.get("rat_de") or record.get("rat"),
        kommissionen=_split_kommissionen(record),
        anzahl_interessenbindungen=len(ibs),
        anzahl_hauptberuflich=hauptberuflich_count,
        verguetungstransparenz=record.get("verguetungstransparenz_beurteilung"),
    )


def _detail_from_record(record: dict[str, Any]) -> ParlamentarierDetail:
    summary = _summary_from_record(record)
    return ParlamentarierDetail(
        **summary.model_dump(),
        geburtstag=record.get("geburtstag"),
        geschlecht=record.get("geschlecht"),
        beruf=record.get("beruf_de") or record.get("beruf"),
        im_rat_seit=record.get("im_rat_seit"),
        homepage=record.get("homepage"),
        wikipedia=record.get("wikipedia"),
        interessenbindungen=[_ib_to_model(ib) for ib in (record.get("interessenbindungen") or [])],
    )


# ---------------------------------------------------------------------------
# Server builder
# ---------------------------------------------------------------------------


# Common tool input bounds. Centralised so future audits can grep them.
_RankingKriterium = Literal["anzahl_interessenbindungen", "anzahl_hauptberuflich"]
_NameOrId = Annotated[str, Field(min_length=1, max_length=200)]
_OptionalShortString = Annotated[str | None, Field(default=None, max_length=80)]
_BrancheQuery = Annotated[str, Field(min_length=1, max_length=200)]
_LimitSearch = Annotated[int, Field(ge=1, le=200)]
_LimitRanking = Annotated[int, Field(ge=1, le=100)]


def build_server(client: LobbywatchClient | None = None) -> FastMCP:
    """Construct the FastMCP server with all Phase-1 tools registered.

    The server uses an ``@asynccontextmanager`` lifespan (audit SDK-001) to
    own the :class:`LobbywatchClient` lifecycle. When a ``client`` is passed
    in (test fixtures), the lifespan is a no-op pass-through; when called
    without an argument (production), the server creates the client on
    startup and ``aclose()``-s it on shutdown.
    """
    # Mutable holder so the lifespan can lazy-initialise + own teardown
    # while tests pre-fill it via the ``client=`` parameter.
    state: dict[str, LobbywatchClient | None] = {"client": client}
    server_owns_client = client is None

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict[str, LobbywatchClient | None]]:
        if state["client"] is None:
            state["client"] = LobbywatchClient()
        # Pin the protocolVersion at startup (audit ARCH-012). Importing
        # here keeps the test path light when the constant moves between
        # mcp SDK releases.
        try:
            from mcp.types import LATEST_PROTOCOL_VERSION

            logger.info(
                "lobbywatch-mcp ready: protocolVersion=%s, server_owns_client=%s",
                LATEST_PROTOCOL_VERSION,
                server_owns_client,
            )
        except ImportError:  # pragma: no cover — older mcp without the constant
            logger.info(
                "lobbywatch-mcp ready (protocolVersion unknown): server_owns_client=%s",
                server_owns_client,
            )
        try:
            yield state
        finally:
            if server_owns_client and state["client"] is not None:
                await state["client"].aclose()
                state["client"] = None

    mcp: FastMCP = FastMCP(
        name="lobbywatch-mcp",
        lifespan=lifespan,
        instructions=(
            "Lobbywatch.ch MCP server — conflicts of interest of Swiss parliamentarians. "
            "Data is community-researched, updated weekly, and licensed CC BY-SA 4.0. "
            "Attribution is included in every response."
        ),
    )

    def lb() -> LobbywatchClient:
        c = state["client"]
        if c is None:
            raise RuntimeError("LobbywatchClient not initialised; lifespan not started")
        return c

    # -------- parlamentarier --------

    @mcp.tool(
        name="lobbywatch_get_parlamentarier",
        annotations=ToolAnnotations(
            title="Get parliamentarian profile",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def get_parlamentarier(name_or_id: _NameOrId) -> ParlamentarierResponse:
        """Look up a Swiss federal parliamentarian and return their full profile,
        including all declared/researched interessenbindungen.

        On a fuzzy miss, the response surfaces near-miss candidates so the
        LLM can prompt the user with "did you mean…?" suggestions instead of
        treating the empty result as authoritative (audit ARCH-003).

        Args:
            name_or_id: Either the numeric Lobbywatch ID (as string) or a name.
                Name matching is fuzzy — partial last names work.

        Use cases:
            - "Show me Anna Mustermann's full lobbying profile"
            - "What conflicts of interest does parliamentarian #42 declare?"
            - "Look up Wehrli — give me everything you have"
        """
        async with observed_tool("lobbywatch_get_parlamentarier"):
            record = await _coerce_upstream(lb().find_parlamentarier(name_or_id))
            if record is None:
                suggestions = await _coerce_upstream(lb().find_candidates(str(name_or_id)))
                return ParlamentarierResponse(
                    provenance="weekly_dump",
                    parlamentarier=None,
                    suggestions=[
                        ParlamentarierSuggestion(
                            id=int(r.get("id") or 0),
                            anzeige_name=r.get("anzeige_name") or "",
                            score=score,
                        )
                        for r, score in suggestions
                    ],
                )
            return ParlamentarierResponse(
                provenance="weekly_dump",
                parlamentarier=_detail_from_record(record),
            )

    @mcp.tool(
        name="lobbywatch_list_interessenbindungen",
        annotations=ToolAnnotations(
            title="List parliamentarian interessenbindungen",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def list_interessenbindungen(
        name_or_id: _NameOrId, nur_hauptberuflich: bool = False, nur_aktiv: bool = True
    ) -> InteressenbindungenResponse:
        """Return the list of interessenbindungen (conflicts of interest) for one
        parliamentarian, optionally restricted to full-time or currently-active
        mandates.

        On a fuzzy miss, near-miss candidates are returned in
        ``suggestions`` (audit ARCH-003).

        Args:
            name_or_id: ID or name (fuzzy).
            nur_hauptberuflich: If True, only main-occupation mandates.
            nur_aktiv: If True, drop mandates with an end date (bis) set.

        Use cases:
            - "Which active mandates does Jositsch hold today?"
            - "List Anna Mustermann's full-time mandates only"
            - "Give me every IB ever declared by parliamentarian #1"
        """
        async with observed_tool("lobbywatch_list_interessenbindungen"):
            record = await _coerce_upstream(lb().find_parlamentarier(name_or_id))
            if record is None:
                suggestions = await _coerce_upstream(lb().find_candidates(str(name_or_id)))
                return InteressenbindungenResponse(
                    provenance="weekly_dump",
                    parlamentarier_id=-1,
                    count=0,
                    suggestions=[
                        ParlamentarierSuggestion(
                            id=int(r.get("id") or 0),
                            anzeige_name=r.get("anzeige_name") or "",
                            score=score,
                        )
                        for r, score in suggestions
                    ],
                )

            ibs_raw = record.get("interessenbindungen") or []
            ibs = [_ib_to_model(ib) for ib in ibs_raw]
            if nur_hauptberuflich:
                ibs = [ib for ib in ibs if ib.hauptberuflich]
            if nur_aktiv:
                ibs = [ib for ib in ibs if ib.aktiv is not False]
            return InteressenbindungenResponse(
                provenance="weekly_dump",
                parlamentarier_id=int(record.get("id") or 0),
                count=len(ibs),
                interessenbindungen=ibs,
            )

    @mcp.tool(
        name="lobbywatch_search_parlamentarier_nach_branche",
        annotations=ToolAnnotations(
            title="Search parliamentarians by industry / commission",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def search_parlamentarier_nach_branche(
        branche_query: _BrancheQuery,
        kommission: Annotated[str | None, Field(default=None, max_length=80)] = None,
        limit: _LimitSearch = 25,
    ) -> BrancheSearchResponse:
        """Find parliamentarians with interessenbindungen matching a search term
        against the linked organisation's name, alias, and (when available)
        branche field. Optional commission filter.

        Note: the Lobbywatch "essential" dump does not embed a branche taxonomy
        on each organisation — branche is referenced by id and resolved via the
        separate interessengruppe table. Version 0.1 therefore performs a
        substring match against organisation names and the branche field when
        present. Version 0.2 will add full cross-reference resolution.

        Args:
            branche_query: Substring match (case-insensitive) against
                ``organisation.anzeige_name``, ``organisation.name``,
                ``organisation.branche`` (where present), e.g. "Verlag",
                "Pharma", "Bank", "Krankenkasse", "Bildung".
            kommission: Commission abbreviation to restrict the result to,
                e.g. "WBK-N" for the education commission of the National Council.
            limit: Max number of {parlamentarier, ib} pairs returned (1–200).

        Use cases:
            - "Which WBK-N members hold mandates in the publishing industry?"
            - "Cross-filter Pharma × FK-N to surface health-policy lobbyists"
            - "List every parliamentarian with a 'Krankenkasse' connection"
        """
        async with observed_tool("lobbywatch_search_parlamentarier_nach_branche"):
            q = branche_query.strip().lower()
            records = await _coerce_upstream(lb().all_parlamentarier())
            hits: list[BrancheSearchHit] = []

            for r in records:
                if kommission:
                    komm = [k.lower() for k in _split_kommissionen(r)]
                    if kommission.lower() not in komm:
                        continue
                for ib in r.get("interessenbindungen") or []:
                    org = ib.get("organisation") or {}
                    haystack_parts: list[str] = []
                    for key in ("anzeige_name", "name", "name_de", "alias_namen_de"):
                        val = org.get(key)
                        if isinstance(val, str):
                            haystack_parts.append(val)
                    branche_field = org.get("branche")
                    if isinstance(branche_field, dict):
                        n = branche_field.get("name")
                        if isinstance(n, str):
                            haystack_parts.append(n)
                    elif isinstance(branche_field, str):
                        haystack_parts.append(branche_field)
                    # Also match against the denormalised anzeige_name on the IB
                    # itself which includes the organisation name by convention.
                    ib_display = ib.get("anzeige_name")
                    if isinstance(ib_display, str):
                        haystack_parts.append(ib_display)

                    haystack = " | ".join(haystack_parts).lower()
                    if q in haystack:
                        hits.append(
                            BrancheSearchHit(
                                parlamentarier=_summary_from_record(r),
                                interessenbindung=_ib_to_model(ib),
                            )
                        )
                        if len(hits) >= limit:
                            break
                if len(hits) >= limit:
                    break

            return BrancheSearchResponse(
                provenance="weekly_dump",
                query=branche_query,
                count=len(hits),
                treffer=hits,
            )

    # -------- rankings & statistics --------

    @mcp.tool(
        name="lobbywatch_get_ranking",
        annotations=ToolAnnotations(
            title="Rank parliamentarians by criterion",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def get_ranking(
        kriterium: _RankingKriterium = "anzahl_interessenbindungen",
        kommission: Annotated[str | None, Field(default=None, max_length=80)] = None,
        partei: Annotated[str | None, Field(default=None, max_length=80)] = None,
        limit: _LimitRanking = 10,
    ) -> RankingResponse:
        """Rank parliamentarians by a criterion.

        Args:
            kriterium: One of "anzahl_interessenbindungen",
                "anzahl_hauptberuflich".
            kommission: Optional commission abbreviation filter (e.g. "WBK-N").
            partei: Optional party filter (e.g. "SP", "SVP", "Mitte").
            limit: Top-N to return (1–100).

        Use cases:
            - "Top 10 SP MPs by total mandate count"
            - "Which Mitte-Fraktion members have the most full-time mandates?"
            - "Rank WBK-N by IB count — who's most involved?"
        """
        async with observed_tool("lobbywatch_get_ranking", kriterium=kriterium):
            records = await _coerce_upstream(lb().all_parlamentarier())
            summaries = [_summary_from_record(r) for r in records]

            if kommission:
                k = kommission.lower()
                summaries = [s for s in summaries if k in {x.lower() for x in s.kommissionen}]
            if partei:
                summaries = [s for s in summaries if (s.partei or "").lower() == partei.lower()]

            summaries.sort(key=lambda s: getattr(s, kriterium), reverse=True)
            top = summaries[:limit]
            eintraege = [
                RankingEntry(
                    rank=i + 1,
                    parlamentarier=s,
                    wert=getattr(s, kriterium),
                    kriterium=kriterium,
                )
                for i, s in enumerate(top)
            ]
            return RankingResponse(
                provenance="weekly_dump",
                kriterium=kriterium,
                eintraege=eintraege,
            )

    @mcp.tool(
        name="lobbywatch_get_transparenzquote",
        annotations=ToolAnnotations(
            title="Compensation-transparency distribution",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def get_transparenzquote(
        kommission: Annotated[str | None, Field(default=None, max_length=80)] = None,
    ) -> TransparenzResponse:
        """Aggregate the verguetungstransparenz_beurteilung values across all
        parliamentarians (or a commission subset) and return the distribution.

        Useful to answer: 'How transparent is the education commission on
        compensation disclosure?'

        Use cases:
            - "How transparent is the FK-N on compensation disclosure?"
            - "Distribution of transparency labels across the whole parliament"
            - "Compare WBK-N transparency vs the council average"
        """
        async with observed_tool("lobbywatch_get_transparenzquote"):
            records = await _coerce_upstream(lb().all_parlamentarier())
            if kommission:
                k = kommission.lower()
                records = [r for r in records if k in {x.lower() for x in _split_kommissionen(r)}]

            buckets: dict[str, int] = {}
            total = 0
            for r in records:
                label = r.get("verguetungstransparenz_beurteilung") or "nicht_bewertet"
                buckets[label] = buckets.get(label, 0) + 1
                total += 1

            # Simple "acceptable" proxy: anything that is not "ungenuegend" / "nicht_bewertet".
            acceptable = sum(
                v for k, v in buckets.items() if k not in ("ungenuegend", "nicht_bewertet")
            )
            quote = (acceptable / total) if total else None

            return TransparenzResponse(
                provenance="weekly_dump",
                scope=kommission or "all",
                total=total,
                nach_bewertung=buckets,
                quote_ausreichend=quote,
            )

    # -------- lobby group lookup (live dataIF) --------

    @mcp.tool(
        name="lobbywatch_get_lobbygruppe",
        annotations=ToolAnnotations(
            title="Fetch lobby group (live dataIF)",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    async def get_lobbygruppe(name_or_id: _NameOrId) -> LobbygruppeResponse:
        """Fetch a lobby group (interessengruppe) from the live Lobbywatch
        dataIF, including its connected organisations and parliamentarians.

        Uses the live REST API since this endpoint returns fresh data.

        Use cases:
            - "Look up 'economiesuisse' and list connected MPs"
            - "Who's affiliated with the lobby group #42?"
            - "Show me all parliamentarians linked to the pharma lobby"
        """
        async with observed_tool("lobbywatch_get_lobbygruppe"):
            data = await _coerce_upstream(lb().fetch_lobbygruppe(name_or_id))
            if data is None:
                return LobbygruppeResponse(provenance="dataIF_live")

            # Normalise the nested payload into a Lobbygruppe model.
            branche = data.get("branche")
            branche_name = branche.get("name") if isinstance(branche, dict) else branche
            model = Lobbygruppe(
                id=data.get("id"),
                anzeige_name=data.get("anzeige_name") or data.get("anzeige_name_de"),
                name=data.get("name") or data.get("name_de"),
                branche=branche_name,
                beschreibung=data.get("beschreibung"),
                wikipedia=data.get("wikipedia"),
                wikidata_qid=data.get("wikidata_qid"),
                organisationen=data.get("organisationen") or [],
                parlamentarier=data.get("parlamentarier") or [],
            )
            return LobbygruppeResponse(
                provenance="dataIF_live",
                lobbygruppe=model,
            )

    # -------- cache control --------

    @mcp.tool(
        name="lobbywatch_refresh_dump",
        annotations=ToolAnnotations(
            title="Force re-download of weekly dump",
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    async def refresh_dump(ctx: Context) -> DumpStatusResponse:
        """Force re-download of the weekly Lobbywatch dump. Returns the new
        cache status.

        Reports progress via the MCP Context (audit SDK-003) so long-running
        downloads (~17 MB compressed) surface useful feedback to the calling
        LLM and operator.

        Use cases:
            - "Force a fresh download — the data looks stale"
            - "I just heard about a new declaration — refresh and re-check"
        """
        async with observed_tool("lobbywatch_refresh_dump"):
            await ctx.info("Refreshing Lobbywatch weekly dump...")
            await _coerce_upstream(lb().ensure_dump_loaded(force=True))
            status = await lb().status()
            await ctx.info(
                f"Dump refreshed: {status['record_count']} parliamentarians "
                f"(cached at {status['cached_at']})"
            )
            return DumpStatusResponse(provenance="weekly_dump", **status)

    @mcp.tool(
        name="lobbywatch_dump_status",
        annotations=ToolAnnotations(
            title="Dump cache status",
            readOnlyHint=True,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def dump_status() -> DumpStatusResponse:
        """Return current dump cache status without forcing a refresh.

        Use cases:
            - "How fresh is the cached data right now?"
            - "When was the dump last loaded?"
        """
        async with observed_tool("lobbywatch_dump_status"):
            status = await lb().status()
            return DumpStatusResponse(provenance="weekly_dump", **status)

    # -------- resources & prompts (audit ARCH-008) --------

    @mcp.resource(
        "lobbywatch://attribution",
        name="lobbywatch-attribution",
        title="Lobbywatch.ch CC BY-SA 4.0 attribution",
        description=(
            "The full attribution string mandated by the Lobbywatch.ch "
            "data licence. Every tool response embeds this; this resource "
            "lets clients display it as standalone metadata."
        ),
        mime_type="text/plain",
    )
    def attribution_resource() -> str:
        return ATTRIBUTION

    @mcp.prompt(
        name="lobbywatch_anchor_demo",
        title="Anchor demo: WBK-N education-industry conflicts",
        description=(
            "The canonical demo query for the Schulamt / KI-Fachgruppe "
            "context, parameterised by branche. Useful as an opening prompt "
            "in conversational sessions."
        ),
    )
    def anchor_demo_prompt(branche: str = "Bildung") -> str:
        return (
            f"Welche Mitglieder der WBK-N haben Interessenbindungen zu "
            f"{branche}-bezogenen Organisationen, und wie ist ihre "
            f"Vergütungstransparenz-Bewertung? Bitte zuerst "
            f"`lobbywatch_search_parlamentarier_nach_branche` mit "
            f"branche_query='{branche}' und kommission='WBK-N' aufrufen, "
            f"dann pro Treffer `lobbywatch_get_parlamentarier` für die "
            f"Transparenzbewertung."
        )

    @mcp.prompt(
        name="lobbywatch_top_lobbyists_by_party",
        title="Top lobbyists in a party",
        description=(
            "Ranks parliamentarians of a given party by total mandate "
            "count. Useful for transparency-research workflows."
        ),
    )
    def top_lobbyists_prompt(partei: str = "SP") -> str:
        return (
            f"Gib mir die Top-10 Parlamentarier:innen der {partei}-Fraktion "
            f"nach Anzahl Interessenbindungen via "
            f"`lobbywatch_get_ranking` (kriterium='anzahl_interessenbindungen', "
            f"partei='{partei}', limit=10), inkl. Vergütungstransparenz."
        )

    return mcp
