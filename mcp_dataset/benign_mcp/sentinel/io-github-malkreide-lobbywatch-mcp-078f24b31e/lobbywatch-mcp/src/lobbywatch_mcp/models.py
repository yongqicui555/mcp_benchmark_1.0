"""Pydantic v2 response models for lobbywatch-mcp.

Every tool response carries the CC BY-SA attribution. The Pydantic layer keeps
this invariant — it cannot be forgotten in an ad-hoc response.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from lobbywatch_mcp.config import ATTRIBUTION


class LobbywatchResponse(BaseModel):
    """Base envelope. Always includes attribution plus a provenance hint."""

    model_config = ConfigDict(extra="allow")

    source: str = Field(default=ATTRIBUTION)
    provenance: str = Field(description="Which endpoint / dump the payload came from")


class Interessenbindung(BaseModel):
    """A single declared (or researched) conflict of interest of a parliamentarian."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    parlamentarier_id: int | None = None
    organisation_id: int | None = None
    organisation_name: str | None = None
    branche: str | None = None
    art: str | None = Field(default=None, description="e.g. vorstand, mitgliedschaft, beirat")
    funktion_im_gremium: str | None = None
    deklarationstyp: str | None = None
    status: str | None = None
    hauptberuflich: bool | None = None
    behoerden_vertreter: bool | None = None
    beschreibung: str | None = None
    quelle_url: str | None = None
    von: str | None = None
    bis: str | None = None
    aktiv: bool | None = None


class ParlamentarierSummary(BaseModel):
    """Lightweight parliamentarian projection used for lists and rankings."""

    model_config = ConfigDict(extra="allow")

    id: int
    anzeige_name: str
    partei: str | None = None
    kanton: str | None = None
    rat: str | None = None
    kommissionen: list[str] = Field(default_factory=list)
    anzahl_interessenbindungen: int = 0
    anzahl_hauptberuflich: int = 0
    verguetungstransparenz: str | None = None


class ParlamentarierDetail(ParlamentarierSummary):
    """Full projection with interessenbindungen expanded."""

    model_config = ConfigDict(extra="allow")

    geburtstag: str | None = None
    geschlecht: str | None = None
    beruf: str | None = None
    im_rat_seit: str | None = None
    homepage: str | None = None
    wikipedia: str | None = None
    interessenbindungen: list[Interessenbindung] = Field(default_factory=list)


class Lobbygruppe(BaseModel):
    """An interessengruppe (lobby group) fetched from the live dataIF."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    anzeige_name: str | None = None
    name: str | None = None
    branche: str | None = None
    beschreibung: str | None = None
    wikipedia: str | None = None
    wikidata_qid: str | None = None
    organisationen: list[dict[str, Any]] = Field(default_factory=list)
    parlamentarier: list[dict[str, Any]] = Field(default_factory=list)


class RankingEntry(BaseModel):
    rank: int
    parlamentarier: ParlamentarierSummary
    wert: float | int
    kriterium: str


class RankingResponse(LobbywatchResponse):
    kriterium: str
    eintraege: list[RankingEntry] = Field(default_factory=list)


class ParlamentarierSuggestion(BaseModel):
    """A near-miss candidate offered when the requested name was not found.

    Surfaced by ``lobbywatch_get_parlamentarier`` /
    ``lobbywatch_list_interessenbindungen`` (audit ARCH-003) so the LLM can
    suggest a corrected lookup instead of treating an empty hit as truth.
    """

    id: int
    anzeige_name: str
    score: int = Field(ge=0, le=100, description="rapidfuzz WRatio score (0-100)")


class ParlamentarierResponse(LobbywatchResponse):
    parlamentarier: ParlamentarierDetail | None = None
    suggestions: list[ParlamentarierSuggestion] = Field(
        default_factory=list,
        description="Near-miss fuzzy candidates when the lookup failed (ARCH-003)",
    )


class InteressenbindungenResponse(LobbywatchResponse):
    parlamentarier_id: int
    count: int
    interessenbindungen: list[Interessenbindung] = Field(default_factory=list)
    suggestions: list[ParlamentarierSuggestion] = Field(
        default_factory=list,
        description="Near-miss fuzzy candidates when the lookup failed (ARCH-003)",
    )


class BrancheSearchHit(BaseModel):
    parlamentarier: ParlamentarierSummary
    interessenbindung: Interessenbindung


class BrancheSearchResponse(LobbywatchResponse):
    query: str
    count: int
    treffer: list[BrancheSearchHit] = Field(
        default_factory=list,
        description="List of {parlamentarier, interessenbindung} pairs matching the branche",
    )


class LobbygruppeResponse(LobbywatchResponse):
    lobbygruppe: Lobbygruppe | None = None


class TransparenzResponse(LobbywatchResponse):
    scope: str
    total: int
    nach_bewertung: dict[str, int] = Field(default_factory=dict)
    quote_ausreichend: float | None = None


class DumpStatusResponse(LobbywatchResponse):
    loaded: bool
    cached_at: str | None = None
    age_seconds: int | None = None
    record_count: int = 0
