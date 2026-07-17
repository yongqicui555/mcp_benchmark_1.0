"""Daten-Zugriff: Cache, CSV-Fetch, Filter-/Jahr-Helfer und Fehler-Sanitisierung."""

from __future__ import annotations

import csv
import io
import time

import httpx

from .constants import BISTA_API, CACHE_TTL
from .http_client import _http_get
from .logging_setup import log

# ─────────────────────────── Cache ─────────────────────────────────────────────
_cache: dict[str, tuple[float, list[dict]]] = {}


def _cache_get(key: str) -> list[dict] | None:
    """Gibt gecachte Daten zurück, falls TTL nicht abgelaufen."""
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, data: list[dict]) -> None:
    """Speichert Daten im Cache mit aktuellem Zeitstempel."""
    _cache[key] = (time.time(), data)


def _handle_error(e: Exception) -> str:
    """Einheitliche, handlungsorientierte Fehlermeldungen (auf Deutsch).

    Der **originale** Fehler wird strukturiert ins stderr-Log geschrieben
    (OBS-002); an den LLM/Client geht ausschliesslich eine sanitisierte
    Meldung ohne Internals (keine Stacktraces, keine ``str(e)``-Leaks).
    """
    log.error("tool_error", error_type=type(e).__name__, error=str(e))

    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 404:
            return "Fehler: Ressource nicht gefunden. Bitte Parameter prüfen."
        if code == 429:
            return "Fehler: Rate-Limit erreicht. Bitte kurz warten und erneut versuchen."
        if code in (502, 503):
            return "Fehler: Dienst vorübergehend nicht verfügbar. Bitte erneut versuchen."
        return f"Fehler: API-Anfrage fehlgeschlagen (HTTP {code})."
    if isinstance(e, httpx.TimeoutException):
        return "Fehler: Zeitüberschreitung. Der Dienst antwortet nicht. Bitte erneut versuchen."
    if isinstance(e, PermissionError):
        return "Fehler: Ausgehende Anfrage durch Egress-Policy blockiert."
    return "Fehler: Unerwarteter interner Fehler. Bitte später erneut versuchen."


async def _fetch_csv(endpoint: str, ctx: object | None = None) -> list[dict]:
    """Holt CSV-Daten von einem BISTA-Endpunkt und gibt eine Liste von Dicts zurück.

    Optionaler ``ctx`` (FastMCP Context) erlaubt Progress-Reports und
    client-seitiges Logging bei nicht-gecachten Fetches (SDK-003).
    """
    cached = _cache_get(endpoint)
    if cached is not None:
        log.debug("cache_hit", endpoint=endpoint, rows=len(cached))
        if ctx is not None:
            await ctx.info(f"Cache-Treffer für {endpoint} ({len(cached)} Zeilen).")
        return cached

    start = time.perf_counter()
    if ctx is not None:
        await ctx.info(f"Lade BISTA-Datensatz {endpoint} …")
        await ctx.report_progress(0.0, 1.0, "Abruf gestartet")
    resp = await _http_get(f"{BISTA_API}/{endpoint}")
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)
    _cache_set(endpoint, rows)
    ms = round((time.perf_counter() - start) * 1000)
    log.info("fetch_ok", endpoint=endpoint, rows=len(rows), ms=ms)
    if ctx is not None:
        await ctx.report_progress(1.0, 1.0, f"{len(rows)} Zeilen geladen")
    return rows


def _filter_rows(rows: list[dict], **filters: str | int | None) -> list[dict]:
    """Filtert Zeilen anhand beliebiger Feld=Wert-Paare (case-insensitive für Strings)."""
    result = rows
    for key, val in filters.items():
        if val is None:
            continue
        if isinstance(val, int):
            result = [r for r in result if r.get(key) == str(val)]
        else:
            val_lower = str(val).lower()
            result = [r for r in result if val_lower in r.get(key, "").lower()]
    return result


def _latest_year(rows: list[dict], year_field: str = "Jahr") -> int | None:
    """Ermittelt das aktuellste Jahr aus den Daten."""
    years = {int(r[year_field]) for r in rows if r.get(year_field, "").isdigit()}
    return max(years) if years else None
