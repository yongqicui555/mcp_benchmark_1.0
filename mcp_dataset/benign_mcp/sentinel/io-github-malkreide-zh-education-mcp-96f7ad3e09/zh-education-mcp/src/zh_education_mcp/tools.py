"""MCP-Server-Instanz, Health-Route und die 8 Bildungsstatistik-Tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from starlette.responses import JSONResponse

from .config import settings
from .constants import (
    EP_MATURITAET,
    EP_MITTELSCHULEN,
    EP_NAT_REGIONAL,
    EP_SEK1,
    EP_UEBERSICHT,
    EP_WOHNORT,
)
from .data import _fetch_csv, _filter_rows, _handle_error, _latest_year
from .http_client import lifespan
from .models import (
    ListSchulgemeindensInput,
    MaturitaetsquoteInput,
    MittelschulenInput,
    SchulkreisTrendInput,
    Sek1ProfilInput,
    StaatsangehoerigkeitInput,
    UebersichtInput,
    WohnortTrendInput,
)
from .provenance import PROVENANCE, ResponseFormat, _envelope, _not_found, _source_footer
from .telemetry import traced

# ─────────────────────────── Server ────────────────────────────────────────────
# stateless_http=True ⇒ kein serverseitiger Session-State ⇒ horizontal
# skalierbar ohne Sticky Sessions (SCALE-002/003), passend zu read-only Daten.
mcp = FastMCP(
    "zh_education_mcp",
    lifespan=lifespan,
    stateless_http=settings.stateless_http,
    json_response=settings.json_response,
)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request):  # noqa: ANN001 — Starlette Request
    """Health-Probe für Load-Balancer und Docker HEALTHCHECK (SCALE-004)."""
    return JSONResponse({"status": "ok", "service": "zh-education-mcp"})


# ══════════════════════════════════════════════════════════════════════════════
#  RESOURCES — zweites MCP-Primitiv neben Tools (ARCH-008)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.resource(
    "zh-edu://datenquellen",
    name="BISTA-Datenquellen",
    description="Katalog der verfügbaren BISTA-Datensätze und ihrer Tool-Zuordnung.",
    mime_type="application/json",
)
def datenquellen_resource() -> str:
    """Statischer Katalog der angebundenen BISTA-Datensätze (read-only Resource)."""
    return json.dumps(
        {
            "source": PROVENANCE,
            "datasets": [
                {"endpoint": EP_SEK1, "tools": ["zh_edu_list_schulgemeinden", "zh_edu_schulkreis_trend", "zh_edu_sek1_profil"]},
                {"endpoint": EP_UEBERSICHT, "tools": ["zh_edu_overview"]},
                {"endpoint": EP_NAT_REGIONAL, "tools": ["zh_edu_staatsangehoerigkeiten"]},
                {"endpoint": EP_MATURITAET, "tools": ["zh_edu_maturitaetsquote"]},
                {"endpoint": EP_WOHNORT, "tools": ["zh_edu_wohnort_trend"]},
                {"endpoint": EP_MITTELSCHULEN, "tools": ["zh_edu_mittelschulen"]},
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.resource(
    "zh-edu://lizenz",
    name="Lizenz & Attribution",
    description="Quelle, Lizenz (CC BY 4.0) und Modifikationshinweis für alle Daten.",
    mime_type="application/json",
)
def lizenz_resource() -> str:
    """Provenance-/Lizenz-Information als read-only Resource (CH-004)."""
    return json.dumps(PROVENANCE, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 1 — Schulgemeinden auflisten
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_list_schulgemeinden",
    annotations={
        "title": "Schulgemeinden auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_list_schulgemeinden")
async def zh_edu_list_schulgemeinden(
    params: ListSchulgemeindensInput, ctx: Context | None = None
) -> str:
    """Listet alle Schulgemeinden und Schulkreise im Kanton Zürich auf.

    Extrahiert die eindeutigen Schulgemeinden aus den Sekundarstufe-I-Daten.
    Nützlich als Einstieg, um gültige Namen für andere Tools zu finden.

    Args:
        params (ListSchulgemeindensInput):
            - suchbegriff (str | None): Filter nach Teilstring (z. B. 'Zürich')
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Alphabetische Liste aller Schulgemeinden.
    """
    try:
        rows = await _fetch_csv(EP_SEK1, ctx)
        gemeinden = sorted({r["Schulgemeinde"] for r in rows if r.get("Schulgemeinde")})

        if params.suchbegriff:
            needle = params.suchbegriff.lower()
            gemeinden = [g for g in gemeinden if needle in g.lower()]

        if not gemeinden:
            return _not_found(
                params.response_format,
                "Keine Schulgemeinden gefunden für den angegebenen Suchbegriff.",
                filter=params.suchbegriff,
            )

        if params.response_format == ResponseFormat.JSON:
            return _envelope(gemeinden, match_type="exact", filter=params.suchbegriff)

        lines = ["# Schulgemeinden Kanton Zürich\n"]
        if params.suchbegriff:
            lines.append(f"**Filter:** *{params.suchbegriff}*\n")
        lines.append(f"Gefunden: **{len(gemeinden)}** Schulgemeinden\n")
        for g in gemeinden:
            lines.append(f"- {g}")
        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 2 — Schulkreis-Trend
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_schulkreis_trend",
    annotations={
        "title": "Lernenden-Trend nach Schulkreis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_schulkreis_trend")
async def zh_edu_schulkreis_trend(
    params: SchulkreisTrendInput, ctx: Context | None = None
) -> str:
    """Zeigt den Lernenden-Trend für eine Schulgemeinde / einen Schulkreis.

    Liefert die Entwicklung der Lernendenzahlen (Sek I) über die letzten N Jahre,
    aufgeschlüsselt nach Anforderungstyp (Sek A, Sek B, Sek C etc.).

    Args:
        params (SchulkreisTrendInput):
            - schulgemeinde (str): Name der Schulgemeinde (z. B. 'Zürich-Letzi')
            - letzte_n_jahre (int): Anzahl Jahre rückwärts (Standard: 5)
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Trend-Übersicht mit Jahresvergleich und Gesamtentwicklung.
    """
    try:
        rows = await _fetch_csv(EP_SEK1, ctx)
        matched = _filter_rows(rows, Schulgemeinde=params.schulgemeinde)

        if not matched:
            gemeinden = sorted({r["Schulgemeinde"] for r in rows if r.get("Schulgemeinde")})
            suggestions = [
                g for g in gemeinden if params.schulgemeinde.lower()[:4] in g.lower()
            ][:5]
            hint = f" Meinten Sie: {', '.join(suggestions)}?" if suggestions else ""
            return _not_found(
                params.response_format,
                f"Schulgemeinde '{params.schulgemeinde}' nicht gefunden.{hint}\n\n"
                f"Tipp: Verwende `zh_edu_list_schulgemeinden`, um gültige Namen zu sehen.",
                suggestions=suggestions,
                schulgemeinde=params.schulgemeinde,
            )

        latest = _latest_year(matched)
        if latest is None:
            return "Keine Jahresdaten verfügbar."

        cutoff = latest - params.letzte_n_jahre + 1
        filtered = [r for r in matched if r.get("Jahr", "").isdigit() and int(r["Jahr"]) >= cutoff]
        filtered.sort(key=lambda r: (int(r.get("Jahr", 0)), r.get("Anforderungstyp", "")))

        if params.response_format == ResponseFormat.JSON:
            return _envelope(filtered, schulgemeinde=params.schulgemeinde)

        lines = [f"# Trend {params.schulgemeinde} ({cutoff}–{latest})\n"]

        by_year: dict[int, dict[str, int]] = {}
        for r in filtered:
            yr = int(r["Jahr"])
            typ = r.get("Anforderungstyp", "Unbekannt")
            anzahl = int(r.get("Anzahl", 0))
            by_year.setdefault(yr, {})[typ] = anzahl

        typen = sorted({r.get("Anforderungstyp", "") for r in filtered} - {""})
        header = "| Jahr | " + " | ".join(typen) + " | Total |"
        sep = "|------|" + "|".join(["------:"] * len(typen)) + "|------:|"
        lines.extend([header, sep])

        for yr in sorted(by_year):
            vals = by_year[yr]
            total = sum(vals.values())
            cells = [str(vals.get(t, 0)) for t in typen]
            lines.append(f"| {yr} | " + " | ".join(cells) + f" | **{total}** |")

        years_list = sorted(by_year.keys())
        if len(years_list) >= 2:
            first_total = sum(by_year[years_list[0]].values())
            last_total = sum(by_year[years_list[-1]].values())
            diff = last_total - first_total
            sign = "+" if diff >= 0 else ""
            lines.append(
                f"\n**Veränderung {years_list[0]}→{years_list[-1]}:** {sign}{diff} Lernende"
            )

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 3 — Kantonsweite Übersicht
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_overview",
    annotations={
        "title": "Kantonsweite Lernenden-Übersicht",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_overview")
async def zh_edu_overview(
    params: UebersichtInput, ctx: Context | None = None
) -> str:
    """Gibt eine kantonsweite Übersicht aller Lernenden nach Stufe, Typ und Geschlecht.

    Datenquelle: BISTA-Übersicht aller Lernenden im Kanton Zürich.
    Umfasst Primarstufe, Sekundarstufe I, Sekundarstufe II und Tertiärstufe.

    Args:
        params (UebersichtInput):
            - jahr (int | None): Bestimmtes Jahr (leer = aktuellstes)
            - stufe (str | None): Filter nach Schulstufe
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Übersichtstabelle mit Lernenden nach Stufe und Schultyp.
    """
    try:
        rows = await _fetch_csv(EP_UEBERSICHT, ctx)

        jahr = params.jahr or _latest_year(rows)
        if jahr is None:
            return "Keine Jahresdaten verfügbar."

        filtered = [r for r in rows if r.get("Jahr") == str(jahr)]
        if params.stufe:
            filtered = _filter_rows(filtered, Stufe=params.stufe)

        if not filtered:
            return _not_found(params.response_format, f"Keine Daten für Jahr {jahr} gefunden.", jahr=jahr)

        if params.response_format == ResponseFormat.JSON:
            return _envelope(filtered, jahr=jahr)

        lines = [f"# Übersicht Lernende Kanton Zürich — {jahr}\n"]

        by_stufe: dict[str, int] = {}
        for r in filtered:
            stufe = r.get("Stufe", "Unbekannt")
            anzahl = int(r.get("Anzahl", 0))
            by_stufe[stufe] = by_stufe.get(stufe, 0) + anzahl

        lines.append("| Stufe | Lernende |")
        lines.append("|-------|--------:|")
        total = 0
        for stufe in sorted(by_stufe):
            lines.append(f"| {stufe} | {by_stufe[stufe]:,} |")
            total += by_stufe[stufe]
        lines.append(f"| **Total** | **{total:,}** |")

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 4 — Sek-I-Profil
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_sek1_profil",
    annotations={
        "title": "Sekundarstufe I Profil",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_sek1_profil")
async def zh_edu_sek1_profil(
    params: Sek1ProfilInput, ctx: Context | None = None
) -> str:
    """Zeigt das Sek-I-Profil einer Schulgemeinde (Anforderungstypen A/B/C).

    Schlüsselt die Lernenden der Sekundarstufe I nach Anforderungstyp auf:
    Sek A (höchste Anforderungen), Sek B, Sek C, Mittelschule, Sonderklassen.

    Args:
        params (Sek1ProfilInput):
            - schulgemeinde (str): Schulgemeinde (z. B. 'Zürich-Letzi')
            - jahr (int | None): Bestimmtes Jahr (leer = aktuellstes)
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Profil mit Anzahl und Anteil pro Anforderungstyp.
    """
    try:
        rows = await _fetch_csv(EP_SEK1, ctx)
        matched = _filter_rows(rows, Schulgemeinde=params.schulgemeinde)

        if not matched:
            return _not_found(
                params.response_format,
                f"Schulgemeinde '{params.schulgemeinde}' nicht gefunden.\n\n"
                f"Tipp: Verwende `zh_edu_list_schulgemeinden`, um gültige Namen zu sehen.",
                schulgemeinde=params.schulgemeinde,
            )

        jahr = params.jahr or _latest_year(matched)
        if jahr is None:
            return "Keine Jahresdaten verfügbar."

        year_data = [r for r in matched if r.get("Jahr") == str(jahr)]
        if not year_data:
            return _not_found(
                params.response_format,
                f"Keine Daten für {params.schulgemeinde} im Jahr {jahr}.",
                schulgemeinde=params.schulgemeinde,
                jahr=jahr,
            )

        if params.response_format == ResponseFormat.JSON:
            return _envelope(year_data, schulgemeinde=params.schulgemeinde, jahr=jahr)

        lines = [f"# Sek-I-Profil {params.schulgemeinde} — {jahr}\n"]
        lines.append("| Anforderungstyp | Lernende | Anteil |")
        lines.append("|-----------------|--------:|-------:|")

        total = sum(int(r.get("Anzahl", 0)) for r in year_data)
        for r in sorted(year_data, key=lambda x: int(x.get("Anzahl", 0)), reverse=True):
            typ = r.get("Anforderungstyp", "Unbekannt")
            anzahl = int(r.get("Anzahl", 0))
            pct = f"{anzahl / total * 100:.1f}%" if total > 0 else "—"
            lines.append(f"| {typ} | {anzahl:,} | {pct} |")
        lines.append(f"| **Total** | **{total:,}** | **100%** |")

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 5 — Staatsangehörigkeiten
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_staatsangehoerigkeiten",
    annotations={
        "title": "Staatsangehörigkeiten der Lernenden",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_staatsangehoerigkeiten")
async def zh_edu_staatsangehoerigkeiten(
    params: StaatsangehoerigkeitInput, ctx: Context | None = None
) -> str:
    """Zeigt die Staatsangehörigkeitsstruktur der Lernenden einer Schulgemeinde.

    Liefert die häufigsten Nationalitäten der Schüler·innen in einer
    Schulgemeinde, inkl. ISO2-Ländercode und Anteil.

    Args:
        params (StaatsangehoerigkeitInput):
            - schulgemeinde (str): Schulgemeinde (z. B. 'Zürich-Letzi')
            - top_n (int): Anzahl Top-Nationalitäten (Standard: 10)
            - jahr (int | None): Bestimmtes Jahr (leer = aktuellstes)
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Rangliste der häufigsten Nationalitäten mit Anteil.
    """
    try:
        rows = await _fetch_csv(EP_NAT_REGIONAL, ctx)
        matched = _filter_rows(rows, Schulgemeinde=params.schulgemeinde)

        if not matched:
            return _not_found(
                params.response_format,
                f"Schulgemeinde '{params.schulgemeinde}' nicht gefunden.\n\n"
                f"Tipp: Verwende `zh_edu_list_schulgemeinden`, um gültige Namen zu sehen.",
                schulgemeinde=params.schulgemeinde,
            )

        jahr = params.jahr or _latest_year(matched)
        if jahr is None:
            return "Keine Jahresdaten verfügbar."

        year_data = [r for r in matched if r.get("Jahr") == str(jahr)]
        year_data.sort(key=lambda r: int(r.get("Anzahl", 0)), reverse=True)
        top = year_data[: params.top_n]

        if params.response_format == ResponseFormat.JSON:
            return _envelope(
                top, schulgemeinde=params.schulgemeinde, jahr=jahr, top_n=params.top_n
            )

        total = sum(int(r.get("Anzahl", 0)) for r in year_data)
        lines = [f"# Staatsangehörigkeiten {params.schulgemeinde} — {jahr}\n"]
        lines.append(
            f"Top {params.top_n} von {len(year_data)} Nationalitäten "
            f"(Total: {total:,} Lernende)\n"
        )
        lines.append("| # | Staatsangehörigkeit | ISO2 | Lernende | Anteil |")
        lines.append("|---|---------------------|------|--------:|-------:|")

        for i, r in enumerate(top, 1):
            nat = r.get("Staatsangehoerigkeit", "Unbekannt")
            iso2 = r.get("Staatsangehoerigkeit_ISO2_Code", "—")
            anzahl = int(r.get("Anzahl", 0))
            pct = f"{anzahl / total * 100:.1f}%" if total > 0 else "—"
            lines.append(f"| {i} | {nat} | {iso2} | {anzahl:,} | {pct} |")

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 6 — Maturitätsquote
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_maturitaetsquote",
    annotations={
        "title": "Gymnasiale Maturitätsquote",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_maturitaetsquote")
async def zh_edu_maturitaetsquote(
    params: MaturitaetsquoteInput, ctx: Context | None = None
) -> str:
    """Zeigt die gymnasiale Maturitätsquote nach Gemeinde, Bezirk und Kanton.

    Die Maturitätsquote berechnet sich als Anteil der gymnasialen Abschlüsse
    an der 19-jährigen Wohnbevölkerung einer Gemeinde.

    Args:
        params (MaturitaetsquoteInput):
            - gemeinde (str | None): Gemeindename filtern
            - bezirk (str | None): Bezirk filtern
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Maturitätsquoten-Tabelle mit Abschlüssen und Quote pro Gemeinde.
    """
    try:
        rows = await _fetch_csv(EP_MATURITAET, ctx)

        filtered = rows
        if params.gemeinde:
            filtered = _filter_rows(filtered, Gemeinde=params.gemeinde)
        if params.bezirk:
            filtered = _filter_rows(filtered, Bezirk=params.bezirk)

        if not filtered:
            return _not_found(
                params.response_format, "Keine Daten für die angegebenen Filter gefunden."
            )

        filtered.sort(key=lambda r: float(r.get("Maturitaetsquote_gymnasial", 0)), reverse=True)

        if params.response_format == ResponseFormat.JSON:
            return _envelope(filtered)

        lines = ["# Gymnasiale Maturitätsquote Kanton Zürich\n"]
        if params.gemeinde:
            lines.append(f"**Filter Gemeinde:** *{params.gemeinde}*")
        if params.bezirk:
            lines.append(f"**Filter Bezirk:** *{params.bezirk}*")
        lines.append(f"\nGefunden: **{len(filtered)}** Gemeinden\n")

        lines.append("| Gemeinde | Bezirk | Abschlüsse | 19-Jährige | Quote |")
        lines.append("|----------|--------|----------:|-----------:|------:|")

        for r in filtered[:50]:
            gem = r.get("Gemeinde", "—")
            bez = r.get("Bezirk", "—")
            abschl = r.get("Total_Abschluss_gymnasial", "—")
            pop = r.get("Total_19_Jahre_alt", "—")
            quote = r.get("Maturitaetsquote_gymnasial", "—")
            try:
                quote_str = f"{float(quote) * 100:.1f}%" if quote != "—" else "—"
            except (ValueError, TypeError):
                quote_str = f"{quote}%"
            lines.append(f"| {gem} | {bez} | {abschl} | {pop} | {quote_str} |")

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 7 — Wohnort-Trend
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_wohnort_trend",
    annotations={
        "title": "Lernenden-Trend nach Wohnort",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_wohnort_trend")
async def zh_edu_wohnort_trend(
    params: WohnortTrendInput, ctx: Context | None = None
) -> str:
    """Zeigt die Entwicklung der Lernendenzahlen nach Wohnort (Bezirk/Gemeinde).

    Basiert auf dem Wohnort der Lernenden, nicht dem Schulort.
    Aufschlüsselung nach Gebietstyp (Kanton, Bezirk, Gemeinde) und Schulstufe.

    Args:
        params (WohnortTrendInput):
            - gebiet (str | None): Gebietsbezeichnung filtern
            - stufe (str | None): Schulstufe filtern
            - letzte_n_jahre (int): Anzahl Jahre (Standard: 5)
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Trend-Tabelle der Lernenden nach Wohnort und Stufe.
    """
    try:
        rows = await _fetch_csv(EP_WOHNORT, ctx)

        filtered = rows
        if params.gebiet:
            filtered = _filter_rows(filtered, Gebiet_Bezeichnung=params.gebiet)
        if params.stufe:
            filtered = _filter_rows(filtered, Stufe=params.stufe)

        if not filtered:
            return _not_found(
                params.response_format, "Keine Daten für die angegebenen Filter gefunden."
            )

        latest = _latest_year(filtered)
        if latest is None:
            return "Keine Jahresdaten verfügbar."

        cutoff = latest - params.letzte_n_jahre + 1
        filtered = [r for r in filtered if r.get("Jahr", "").isdigit() and int(r["Jahr"]) >= cutoff]

        if not filtered:
            return f"Keine Daten im Zeitraum {cutoff}–{latest} gefunden."

        if params.response_format == ResponseFormat.JSON:
            return _envelope(filtered)

        lines = [f"# Lernende nach Wohnort ({cutoff}–{latest})\n"]
        if params.gebiet:
            lines.append(f"**Filter Gebiet:** *{params.gebiet}*")
        if params.stufe:
            lines.append(f"**Filter Stufe:** *{params.stufe}*")

        by_year: dict[int, int] = {}
        for r in filtered:
            yr = int(r["Jahr"])
            by_year[yr] = by_year.get(yr, 0) + int(r.get("Anzahl", 0))

        lines.append("\n| Jahr | Lernende |")
        lines.append("|------|--------:|")
        for yr in sorted(by_year):
            lines.append(f"| {yr} | {by_year[yr]:,} |")

        years_list = sorted(by_year.keys())
        if len(years_list) >= 2:
            diff = by_year[years_list[-1]] - by_year[years_list[0]]
            sign = "+" if diff >= 0 else ""
            lines.append(
                f"\n**Veränderung {years_list[0]}→{years_list[-1]}:** {sign}{diff} Lernende"
            )

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e


# ══════════════════════════════════════════════════════════════════════════════
#  TOOL 8 — Mittelschulen
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="zh_edu_mittelschulen",
    annotations={
        "title": "Mittelschulstatistiken",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced("zh_edu_mittelschulen")
async def zh_edu_mittelschulen(
    params: MittelschulenInput, ctx: Context | None = None
) -> str:
    """Zeigt Statistiken zu Mittelschulen (Gymnasium, FMS, HMS) im Kanton Zürich.

    Umfasst Lernendenzahlen nach Mittelschultyp, Bildungsart, Geschlecht
    und Staatsangehörigkeit.

    Args:
        params (MittelschulenInput):
            - mittelschultyp (str | None): Schultyp filtern (z. B. 'Gymnasium')
            - jahr (int | None): Bestimmtes Jahr (leer = aktuellstes)
            - response_format: 'markdown' oder 'json'

    Returns:
        str: Mittelschulstatistiken nach Typ und Bildungsart.
    """
    try:
        rows = await _fetch_csv(EP_MITTELSCHULEN, ctx)

        jahr = params.jahr or _latest_year(rows)
        if jahr is None:
            return "Keine Jahresdaten verfügbar."

        filtered = [r for r in rows if r.get("Jahr") == str(jahr)]
        if params.mittelschultyp:
            filtered = _filter_rows(filtered, Mittelschultyp=params.mittelschultyp)

        if not filtered:
            return _not_found(
                params.response_format,
                f"Keine Mittelschuldaten für Jahr {jahr} gefunden.",
                jahr=jahr,
            )

        if params.response_format == ResponseFormat.JSON:
            return _envelope(filtered, jahr=jahr)

        lines = [f"# Mittelschulen Kanton Zürich — {jahr}\n"]
        if params.mittelschultyp:
            lines.append(f"**Filter:** *{params.mittelschultyp}*\n")

        by_typ: dict[str, int] = {}
        for r in filtered:
            typ = r.get("Mittelschultyp", "Unbekannt")
            by_typ[typ] = by_typ.get(typ, 0) + int(r.get("Anzahl", 0))

        lines.append("| Mittelschultyp | Lernende |")
        lines.append("|----------------|--------:|")
        total = 0
        for typ in sorted(by_typ):
            lines.append(f"| {typ} | {by_typ[typ]:,} |")
            total += by_typ[typ]
        lines.append(f"| **Total** | **{total:,}** |")

        return "\n".join(lines) + _source_footer()

    except Exception as e:
        # Execution-Error sauber als isError:true tool-result signalisieren
        # (OBS-001). Die Meldung ist bereits sanitisiert (OBS-002).
        raise ToolError(_handle_error(e)) from e
