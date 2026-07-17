"""HTTP clients for the three upstream sources.

Eselsbrücke: «Drei Mal anklopfen, dann höflich aufgeben.»
- 3 retries with 2s/4s/8s waits
- 5xx + network errors retry; 4xx (except 429) raise immediately
- In-memory TTL cache to reduce redundant fetches
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from .models import (
    ATTRIBUTION_BFE,
    ATTRIBUTION_ELCOM,
    ATTRIBUTION_OPENDATA_SWISS,
    ATTRIBUTION_ZURICH,
)
from .observability import get_logger

DASHBOARD_BASE = "https://www.energiedashboard.admin.ch/api"
LINDAS_SPARQL = "https://lindas.admin.ch/query"
OPENDATA_SWISS_CKAN = "https://opendata.swiss/api/3/action"
ZURICH_OGD_CKAN = "https://data.stadt-zuerich.ch/api/3/action"

DEFAULT_USER_AGENT = (
    "swiss-electricity-mcp/0.2.0 (+https://github.com/malkreide/swiss-electricity-mcp)"
)
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
BACKOFF_BASE = 2

# SEC-021 egress allow-list: the only hosts this server is ever allowed to reach.
# Code-layer control as a frozenset, not config-mutable at runtime. Network-layer
# egress control (NetworkPolicy / firewall) is the complementary defense-in-depth
# layer documented in docs/network-egress.md.
ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "www.energiedashboard.admin.ch",
        "lindas.admin.ch",
        "opendata.swiss",
        "data.stadt-zuerich.ch",
    }
)


class UpstreamUnreachableError(Exception):
    """Raised when an upstream is unreachable after exhausted retries."""


class EgressNotAllowedError(ValueError):
    """Raised when an outbound request targets a non-allow-listed host or scheme."""


def assert_url_allowed(url: str) -> None:
    """Pre-request gate (SEC-004/005/021): enforce HTTPS + host allow-list.

    Raises EgressNotAllowedError for any non-HTTPS scheme or any host that is
    not in ALLOWED_HOSTS. Call this before every outbound request.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise EgressNotAllowedError(
            f"Only HTTPS is allowed, got scheme {parsed.scheme!r} for {url!r}"
        )
    host = parsed.hostname
    if host not in ALLOWED_HOSTS:
        raise EgressNotAllowedError(
            f"Host {host!r} is not in the egress allow-list {sorted(ALLOWED_HOSTS)}"
        )


def _sparql_escape_literal(value: str) -> str:
    """Escape a string for safe inclusion in a SPARQL double-quoted literal.

    Prevents SPARQL injection (SEC-018) via interpolated tool arguments such as
    canton/category. Control characters are rejected outright; backslash and
    double-quote are escaped per SPARQL 1.1 string-literal grammar.
    """
    if any(ord(c) < 0x20 for c in value):
        raise ValueError("Control characters are not allowed in query values")
    return value.replace("\\", "\\\\").replace('"', '\\"')


# SEC-018: ElCom Verbrauchskategorien form a closed enumeration. The `category`
# tool argument is validated against this allow-list before it ever reaches a
# SPARQL query, rejecting typos and injection attempts alike.
VALID_CATEGORY_CODES: frozenset[str] = frozenset(
    {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8",
     "C1", "C2", "C3", "C4", "C5", "C6", "C7"}
)


def _category_filter(category: str | None) -> str:
    """Build a validated, escaped SPARQL FILTER clause for a category code."""
    if not category:
        return ""
    if category not in VALID_CATEGORY_CODES:
        raise ValueError(
            f"Unknown category {category!r}; expected one of "
            f"{sorted(VALID_CATEGORY_CODES)}"
        )
    return f'FILTER(STR(?categoryCode) = "{_sparql_escape_literal(category)}")'


async def _fetch_with_retry(
    http: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """Retry 3 times on 5xx + network errors; 4xx (except 429) raise immediately."""
    assert_url_allowed(url)
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            await asyncio.sleep(BACKOFF_BASE**attempt)
        try:
            resp = await http.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            last_error = exc
            status = exc.response.status_code
            if 400 <= status < 500 and status != 429:
                raise
        except (httpx.RequestError, httpx.TimeoutException) as exc:
            last_error = exc
    # OBS-002: log the internal detail server-side, return a generic message to
    # the client so no stacktrace / internal repr leaks through the tool result.
    get_logger().error(
        "upstream_unreachable",
        url=url,
        method=method,
        attempts=MAX_RETRIES + 1,
        error=repr(last_error),
    )
    raise UpstreamUnreachableError(
        "Upstream temporarily unavailable after retries; see server logs."
    ) from last_error


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_iso() -> str:
    """Public re-export."""
    return _utc_now_iso()


class _TTLCache:
    """Simple in-process TTL cache."""

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl_seconds

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = (time.monotonic() + ttl, value)

    def clear(self) -> None:
        self._store.clear()


class EnergyDashboardClient:
    """Client for the BFE Energie-Dashboard API."""

    PRODUCTION_MIX = "/strom/strom-produktionsmix"
    CONSUMPTION_FORECAST = "/strom/v2/strom-verbrauch/landesverbrauch-mit-prognose"
    STORAGE_LAKES = "/strom/v2/fuellungsgrad-speicherseen"
    CONSUMER_PRICE_INDEX = "/preise/strom-endverbrauch"

    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        cache: _TTLCache | None = None,
    ) -> None:
        self._http = http or httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"},
        )
        self._owns_http = http is None
        self._cache = cache or _TTLCache(default_ttl_seconds=600)

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _get(self, path: str, ttl: int = 600) -> tuple[Any, str]:
        cached = self._cache.get(path)
        if cached is not None:
            return cached, "cached"
        resp = await _fetch_with_retry(self._http, "GET", f"{DASHBOARD_BASE}{path}")
        data = resp.json()
        self._cache.set(path, data, ttl_seconds=ttl)
        return data, "live_api"

    async def get_production_mix(self) -> tuple[dict, str, str]:
        data, prov = await self._get(self.PRODUCTION_MIX)
        return data, prov, _utc_now_iso()

    async def get_consumption_forecast(self) -> tuple[dict, str, str]:
        data, prov = await self._get(self.CONSUMPTION_FORECAST)
        return data, prov, _utc_now_iso()

    async def get_storage_lakes(self) -> tuple[dict, str, str]:
        data, prov = await self._get(self.STORAGE_LAKES)
        return data, prov, _utc_now_iso()

    async def get_consumer_price_index(self) -> tuple[list[dict], str, str]:
        data, prov = await self._get(self.CONSUMER_PRICE_INDEX)
        return data, prov, _utc_now_iso()

    @staticmethod
    def attribution() -> str:
        return ATTRIBUTION_BFE


class ElComSparqlClient:
    """Client for ElCom electricity-price cubes via LINDAS SPARQL."""

    CATEGORIES: list[dict[str, str]] = [
        {"code": "H1", "desc": "Wohnung mit 2 Zimmern (1'600 kWh/a)", "kwh": "1600"},
        {"code": "H2", "desc": "4-Zimmer-Wohnung mit Elektroherd (2'500 kWh/a)", "kwh": "2500"},
        {"code": "H3", "desc": "4-Zimmer-Wohnung mit Elektroherd und Boiler (4'500 kWh/a)", "kwh": "4500"},
        {"code": "H4", "desc": "5-Zimmer-Wohnung mit Elektroherd, Boiler, Tumbler (4'500 kWh/a)", "kwh": "4500"},
        {"code": "H5", "desc": "5-Zimmer-Einfamilienhaus mit Elektroherd, Boiler, Tumbler (7'500 kWh/a)", "kwh": "7500"},
        {"code": "H6", "desc": "5-Zimmer-Einfamilienhaus mit Elektroherd und Elektroboiler-Heizung (25'000 kWh/a)", "kwh": "25000"},
        {"code": "H7", "desc": "5-Zimmer-Einfamilienhaus mit Waermepumpe (13'000 kWh/a)", "kwh": "13000"},
        {"code": "H8", "desc": "Grosser Haushalt mit hohem Verbrauch (7'500 kWh/a)", "kwh": "7500"},
        {"code": "C1", "desc": "Kleiner Gewerbebetrieb (8'000 kWh/a)", "kwh": "8000"},
        {"code": "C2", "desc": "Mittlerer Gewerbebetrieb (30'000 kWh/a)", "kwh": "30000"},
        {"code": "C3", "desc": "Groesserer Gewerbebetrieb (150'000 kWh/a, z. B. Schule)", "kwh": "150000"},
        {"code": "C4", "desc": "Grosser Gewerbebetrieb mit Niederspannungsmessung (500'000 kWh/a)", "kwh": "500000"},
        {"code": "C5", "desc": "Grosser Gewerbebetrieb mit Mittelspannungsmessung (500'000 kWh/a)", "kwh": "500000"},
        {"code": "C6", "desc": "Grosser Gewerbebetrieb mit Mittelspannungsmessung (1'500'000 kWh/a)", "kwh": "1500000"},
        {"code": "C7", "desc": "Grossbetrieb mit eigener Transformatorenstation (7'500'000 kWh/a)", "kwh": "7500000"},
    ]

    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        cache: _TTLCache | None = None,
    ) -> None:
        self._http = http or httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/sparql-results+json",
            },
        )
        self._owns_http = http is None
        self._cache = cache or _TTLCache(default_ttl_seconds=3600)

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _sparql(self, query: str) -> tuple[list[dict], str]:
        cache_key = query.strip()
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached, "cached"
        resp = await _fetch_with_retry(
            self._http, "GET", LINDAS_SPARQL, params={"query": query}
        )
        bindings = resp.json().get("results", {}).get("bindings", [])
        self._cache.set(cache_key, bindings)
        return bindings, "sparql"

    async def get_tariffs_by_municipality(
        self,
        bfs_nr: int,
        category: str | None = None,
        period_from: int | None = None,
        period_to: int | None = None,
        limit: int = 100,
    ) -> tuple[list[dict], str, str]:
        category_filter = _category_filter(category)
        period_filter = ""
        if period_from is not None:
            period_filter += f"FILTER(?period >= {period_from}) "
        if period_to is not None:
            period_filter += f"FILTER(?period <= {period_to}) "
        query = f"""
PREFIX schema: <http://schema.org/>
SELECT ?period ?categoryCode ?productLabel ?operator ?operatorLabel
       ?total ?energy ?gridusage ?charge ?aidfee
       ?energyName ?gridusageName ?munLabel
WHERE {{
  ?obs <https://energy.ld.admin.ch/elcom/electricityprice/dimension/period> ?period ;
       <https://energy.ld.admin.ch/elcom/electricityprice/dimension/municipality> <https://ld.admin.ch/municipality/{bfs_nr}> ;
       <https://energy.ld.admin.ch/elcom/electricityprice/dimension/category> ?category ;
       <https://energy.ld.admin.ch/elcom/electricityprice/dimension/operator> ?operator ;
       <https://energy.ld.admin.ch/elcom/electricityprice/dimension/product> ?product ;
       <https://energy.ld.admin.ch/elcom/electricityprice/measure/total> ?total .
  OPTIONAL {{ ?obs <https://energy.ld.admin.ch/elcom/electricityprice/measure/energy> ?energy }}
  OPTIONAL {{ ?obs <https://energy.ld.admin.ch/elcom/electricityprice/measure/gridusage> ?gridusage }}
  OPTIONAL {{ ?obs <https://energy.ld.admin.ch/elcom/electricityprice/measure/charge> ?charge }}
  OPTIONAL {{ ?obs <https://energy.ld.admin.ch/elcom/electricityprice/measure/aidfee> ?aidfee }}
  OPTIONAL {{ ?obs <https://energy.ld.admin.ch/elcom/electricityprice/measure/energyname> ?energyName }}
  OPTIONAL {{ ?obs <https://energy.ld.admin.ch/elcom/electricityprice/measure/gridusagename> ?gridusageName }}
  BIND(REPLACE(STR(?category), ".*/", "") AS ?categoryCode)
  BIND(REPLACE(STR(?product), ".*/", "") AS ?productLabel)
  OPTIONAL {{ <https://ld.admin.ch/municipality/{bfs_nr}> schema:name ?munLabel }}
  OPTIONAL {{ ?operator schema:name ?operatorLabel }}
  {category_filter}
  {period_filter}
}}
ORDER BY DESC(?period) ?categoryCode
LIMIT {limit}
"""
        bindings, prov = await self._sparql(query)
        return bindings, prov, _utc_now_iso()

    async def get_median_swiss(
        self,
        category: str | None = None,
        period_from: int | None = None,
        period_to: int | None = None,
        limit: int = 200,
    ) -> tuple[list[dict], str, str]:
        category_filter = _category_filter(category)
        period_filter = ""
        if period_from is not None:
            period_filter += f"FILTER(?period >= {period_from}) "
        if period_to is not None:
            period_filter += f"FILTER(?period <= {period_to}) "
        query = f"""
SELECT ?period ?categoryCode ?total
WHERE {{
  ?obs <https://energy.ld.admin.ch/elcom/electricityprice-swiss/dimension/period> ?period ;
       <https://energy.ld.admin.ch/elcom/electricityprice-swiss/dimension/category> ?category ;
       <https://energy.ld.admin.ch/elcom/electricityprice-swiss/measure/total> ?total .
  BIND(REPLACE(STR(?category), ".*/", "") AS ?categoryCode)
  {category_filter}
  {period_filter}
}}
ORDER BY DESC(?period) ?categoryCode
LIMIT {limit}
"""
        bindings, prov = await self._sparql(query)
        return bindings, prov, _utc_now_iso()

    async def get_median_canton(
        self,
        canton: str,
        category: str | None = None,
        period_from: int | None = None,
        period_to: int | None = None,
        limit: int = 200,
    ) -> tuple[list[dict], str, str]:
        category_filter = _category_filter(category)
        period_filter = ""
        if period_from is not None:
            period_filter += f"FILTER(?period >= {period_from}) "
        if period_to is not None:
            period_filter += f"FILTER(?period <= {period_to}) "
        query = f"""
PREFIX schema: <http://schema.org/>
SELECT ?period ?categoryCode ?total ?cantonLabel
WHERE {{
  ?obs <https://energy.ld.admin.ch/elcom/electricityprice-canton/dimension/period> ?period ;
       <https://energy.ld.admin.ch/elcom/electricityprice-canton/dimension/canton> ?cantonURI ;
       <https://energy.ld.admin.ch/elcom/electricityprice-canton/dimension/category> ?category ;
       <https://energy.ld.admin.ch/elcom/electricityprice-canton/measure/total> ?total .
  ?cantonURI schema:name ?cantonLabel .
  FILTER(STR(?cantonLabel) = "{_sparql_escape_literal(canton)}")
  BIND(REPLACE(STR(?category), ".*/", "") AS ?categoryCode)
  {category_filter}
  {period_filter}
}}
ORDER BY DESC(?period) ?categoryCode
LIMIT {limit}
"""
        bindings, prov = await self._sparql(query)
        return bindings, prov, _utc_now_iso()

    @staticmethod
    def attribution() -> str:
        return ATTRIBUTION_ELCOM


class CkanDiscoveryClient:
    """CKAN client for opendata.swiss and Stadt Zuerich OGD."""

    def __init__(
        self,
        http: httpx.AsyncClient | None = None,
        cache: _TTLCache | None = None,
    ) -> None:
        self._http = http or httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"},
        )
        self._owns_http = http is None
        self._cache = cache or _TTLCache(default_ttl_seconds=3600)

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def search_opendata_swiss(
        self,
        query: str,
        rows: int = 20,
        offset: int = 0,
        bfe_only: bool = False,
    ) -> tuple[dict, str, str]:
        params: dict[str, Any] = {"q": query, "rows": rows, "start": offset}
        if bfe_only:
            params["fq"] = "organization:bundesamt-fur-energie-bfe"
        cache_key = f"opendata:{query}:{rows}:{offset}:{bfe_only}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached, "cached", _utc_now_iso()
        resp = await _fetch_with_retry(
            self._http, "GET", f"{OPENDATA_SWISS_CKAN}/package_search", params=params
        )
        data = resp.json()
        self._cache.set(cache_key, data)
        return data, "live_api", _utc_now_iso()

    async def search_zurich(
        self,
        query: str,
        rows: int = 20,
        offset: int = 0,
    ) -> tuple[dict, str, str]:
        params = {"q": query, "rows": rows, "start": offset}
        cache_key = f"zurich:{query}:{rows}:{offset}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached, "cached", _utc_now_iso()
        resp = await _fetch_with_retry(
            self._http, "GET", f"{ZURICH_OGD_CKAN}/package_search", params=params
        )
        data = resp.json()
        self._cache.set(cache_key, data)
        return data, "live_api", _utc_now_iso()

    @staticmethod
    def attribution_opendata() -> str:
        return ATTRIBUTION_OPENDATA_SWISS

    @staticmethod
    def attribution_zurich() -> str:
        return ATTRIBUTION_ZURICH


def sparql_value(binding: dict, key: str) -> Any | None:
    """Extract value from a SPARQL binding dict; coerce numeric datatypes."""
    entry = binding.get(key)
    if entry is None:
        return None
    value = entry.get("value")
    if value is None or value == "":
        return None
    datatype = entry.get("datatype", "")
    if "decimal" in datatype or "float" in datatype or "double" in datatype:
        try:
            return float(value)
        except ValueError:
            return None
    if "integer" in datatype or "int" in datatype:
        try:
            return int(value)
        except ValueError:
            return None
    return value
