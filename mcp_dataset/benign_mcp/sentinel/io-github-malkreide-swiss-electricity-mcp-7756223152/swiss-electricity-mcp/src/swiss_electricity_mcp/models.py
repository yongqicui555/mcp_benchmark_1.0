"""Pydantic v2 models for swiss-electricity-mcp.

Every response inherits from ResponseEnvelope to enforce attribution and provenance.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ATTRIBUTION_BFE = (
    "Daten: Bundesamt für Energie (BFE), Energie-Dashboard Schweiz "
    "— Open Government Data (OGD-CH). https://www.energiedashboard.admin.ch/"
)
ATTRIBUTION_ELCOM = (
    "Daten: Eidgenössische Elektrizitätskommission ElCom via LINDAS "
    "— Open Government Data (OGD-CH). https://www.elcom.admin.ch/"
)
ATTRIBUTION_ZURICH = (
    "Daten: Stadt Zürich Open Data Portal — CC0/OGD-CH. https://data.stadt-zuerich.ch/"
)
ATTRIBUTION_OPENDATA_SWISS = (
    "Daten: opendata.swiss CKAN-Katalog (BFE-Datensätze) — OGD-CH. https://opendata.swiss/"
)

Provenance = Literal["live_api", "sparql", "weekly_dump", "cached", "stale_cache_fallback"]


class ResponseEnvelope(BaseModel):
    """Common base for all tool responses — attribution + provenance always present."""

    source: str = Field(description="Source attribution string.")
    provenance: Provenance = Field(description="How the data was retrieved.")
    retrieved_at: str = Field(description="ISO-8601 UTC timestamp.")


class ProductionMixYear(BaseModel):
    year: int
    kumuliert_kernkraft_twh: float | None = None
    kumuliert_thermische_twh: float | None = None
    kumuliert_flusskraft_twh: float | None = None
    kumuliert_speicherkraft_twh: float | None = None
    kumuliert_wind_twh: float | None = None
    kumuliert_photovoltaik_twh: float | None = None
    kumuliert_eigenproduktion_twh: float | None = None
    anteil_kernkraft_pct: float | None = None
    anteil_thermische_pct: float | None = None
    anteil_flusskraft_pct: float | None = None
    anteil_speicherkraft_pct: float | None = None
    anteil_wind_pct: float | None = None
    anteil_photovoltaik_pct: float | None = None


class ProductionMixResponse(ResponseEnvelope):
    years: list[ProductionMixYear]


class ConsumptionEntry(BaseModel):
    date: str
    landesverbrauch_gwh: float | None = None
    landesverbrauch_geschaetzt_gwh: float | None = None
    landesverbrauch_prognose_gwh: float | None = None
    five_year_min_gwh: float | None = None
    five_year_max_gwh: float | None = None
    five_year_mittelwert_gwh: float | None = None


class ConsumptionForecastResponse(ResponseEnvelope):
    current_forecast_gwh: float | None = None
    forecast_in_five_days_gwh: float | None = None
    trend: str | None = None
    trend_rating: str | None = None
    series: list[ConsumptionEntry]


class StorageLakeEntry(BaseModel):
    date: str
    speicherstand_prozent: float | None = None
    speicherstand_gwh: float | None = None
    five_year_min_pct: float | None = None
    five_year_max_pct: float | None = None
    five_year_mittelwert_pct: float | None = None


class StorageLakesResponse(ResponseEnvelope):
    region: str
    current_fill_pct: float | None = None
    current_fill_gwh: float | None = None
    capacity_gwh: float | None = None
    series: list[StorageLakeEntry]


class IndexedPriceEntry(BaseModel):
    date: str
    preis_indexiert: float | None = None


class IndexedPriceResponse(ResponseEnvelope):
    base_year: str = Field(default="2020-01-01")
    series: list[IndexedPriceEntry]


class TariffObservation(BaseModel):
    period: int
    municipality_bfs_nr: int
    municipality_name: str | None = None
    operator_id: str
    operator_name: str | None = None
    category: str
    product: str
    total_rp_per_kwh: float | None = None
    energy_rp_per_kwh: float | None = None
    gridusage_rp_per_kwh: float | None = None
    charge_rp_per_kwh: float | None = None
    aidfee_rp_per_kwh: float | None = None
    energy_name: str | None = None
    gridusage_name: str | None = None


class TariffResponse(ResponseEnvelope):
    municipality_name: str | None = None
    municipality_bfs_nr: int | None = None
    observations: list[TariffObservation]


class TariffCategory(BaseModel):
    code: str
    description_de: str
    typical_consumption_kwh: str


class TariffCategoriesResponse(ResponseEnvelope):
    categories: list[TariffCategory]


class MedianTariffEntry(BaseModel):
    period: int
    category: str
    median_total_rp_per_kwh: float


class MedianTariffResponse(ResponseEnvelope):
    scope: Literal["canton", "swiss"]
    canton_id: str | None = None
    observations: list[MedianTariffEntry]


class TariffComparisonRow(BaseModel):
    municipality_bfs_nr: int
    municipality_name: str | None = None
    period: int
    category: str
    total_rp_per_kwh: float | None = None


class TariffComparisonResponse(ResponseEnvelope):
    rows: list[TariffComparisonRow]


class CkanDataset(BaseModel):
    name: str
    title_de: str
    organization: str
    description_de: str | None = None
    resources_count: int
    landing_page: str | None = None


class DatasetSearchResponse(ResponseEnvelope):
    query: str
    total_hits: int
    match_type: Literal["results", "none"] = "results"
    suggestion: str | None = None
    datasets: list[CkanDataset]


class SourceStatus(BaseModel):
    name: str
    url: str
    reachable: bool
    http_status: int | None = None
    latency_ms: int | None = None
    note: str | None = None


class StatusResponse(BaseModel):
    """No envelope — this IS the health check."""

    checked_at: str
    sources: list[SourceStatus]
    overall_healthy: bool
