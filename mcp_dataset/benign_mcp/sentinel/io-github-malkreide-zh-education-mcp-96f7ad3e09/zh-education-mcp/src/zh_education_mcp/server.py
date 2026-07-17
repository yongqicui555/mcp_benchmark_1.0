#!/usr/bin/env python3
"""
zh-education-mcp — Bildungsstatistik Kanton & Stadt Zürich (BISTA)

AI-nativer Zugang zu den Bildungsstatistiken des Kantons Zürich:
  · Lernende nach Schulgemeinde, Schulkreis, Stufe und Anforderungstyp
  · Maturitätsquoten nach Gemeinde, Bezirk und Kanton
  · Staatsangehörigkeiten der Lernenden
  · Mittelschulstatistiken (Gymnasium, FMS, HMS)

Datenquelle: BISTA Public API (bista.zh.ch/basicapi/ogd/)
Kein API-Schlüssel erforderlich. Stichtag: 15. September (jährlich).

Dieses Modul ist die schlanke Kompositions-/Einstiegsschicht. Die Logik ist
auf fokussierte Submodule aufgeteilt (ARCH-011):

  · config         — ENV-Settings
  · constants       — API-Basis, Endpunkte, Timeouts
  · logging_setup   — strukturiertes stderr-Logging
  · provenance      — Response-Envelope, Lizenz-Attribution, ResponseFormat
  · http_client     — Egress-Guard, Connection-Pool, Lifespan
  · data            — Cache, CSV-Fetch, Filter, Fehler-Sanitisierung
  · models          — Pydantic-Input-Modelle
  · tools           — FastMCP-Instanz + die 8 Tools
"""

from __future__ import annotations

import sys

# Re-Exports für Abwärtskompatibilität (`from zh_education_mcp.server import ...`).
# Die Logik lebt in Submodulen; dieses Modul bündelt sie. F401/F403 bewusst
# unterdrückt, da es sich um absichtliche Re-Exports handelt.
from .config import Settings, settings  # noqa: F401
from .constants import (  # noqa: F401
    BISTA_API,
    CACHE_TTL,
    EP_MATURITAET,
    EP_MITTELSCHULEN,
    EP_NAT_REGIONAL,
    EP_SEK1,
    EP_UEBERSICHT,
    EP_WOHNORT,
    HTTP_TIMEOUT,
)
from .data import (  # noqa: F401
    _cache,
    _fetch_csv,
    _filter_rows,
    _handle_error,
    _latest_year,
)
from .http_client import (  # noqa: F401
    ALLOWED_HOSTS,
    AppContext,
    _egress_guard,
    _get_client,
    _http_get,
    lifespan,
)
from .logging_setup import log  # noqa: F401
from .models import (  # noqa: F401
    ListSchulgemeindensInput,
    MaturitaetsquoteInput,
    MittelschulenInput,
    SchulkreisTrendInput,
    Sek1ProfilInput,
    StaatsangehoerigkeitInput,
    UebersichtInput,
    WohnortTrendInput,
)
from .provenance import (  # noqa: F401
    PROVENANCE,
    SOURCE_LICENSE,
    SOURCE_NAME,
    SOURCE_URL,
    ResponseFormat,
    _envelope,
    _not_found,
    _source_footer,
)
from .tools import (  # noqa: F401
    mcp,
    zh_edu_list_schulgemeinden,
    zh_edu_maturitaetsquote,
    zh_edu_mittelschulen,
    zh_edu_overview,
    zh_edu_schulkreis_trend,
    zh_edu_sek1_profil,
    zh_edu_staatsangehoerigkeiten,
    zh_edu_wohnort_trend,
)

__all__ = [
    "ALLOWED_HOSTS",
    "AppContext",
    "BISTA_API",
    "CACHE_TTL",
    "HTTP_TIMEOUT",
    "PROVENANCE",
    "ResponseFormat",
    "SOURCE_LICENSE",
    "SOURCE_NAME",
    "SOURCE_URL",
    "Settings",
    "ListSchulgemeindensInput",
    "MaturitaetsquoteInput",
    "MittelschulenInput",
    "Sek1ProfilInput",
    "SchulkreisTrendInput",
    "StaatsangehoerigkeitInput",
    "UebersichtInput",
    "WohnortTrendInput",
    "main",
    "mcp",
    "settings",
    "log",
    "zh_edu_list_schulgemeinden",
    "zh_edu_maturitaetsquote",
    "zh_edu_mittelschulen",
    "zh_edu_overview",
    "zh_edu_schulkreis_trend",
    "zh_edu_sek1_profil",
    "zh_edu_staatsangehoerigkeiten",
    "zh_edu_wohnort_trend",
]


# ─────────────────────────── Einstiegspunkt ────────────────────────────────────
def main() -> None:
    """Startet den Server.

    Konfiguration primär über ENV-Vars (``MCP_TRANSPORT``/``MCP_HOST``/``MCP_PORT``).
    CLI-Flags ``--http``/``--sse``/``--port``/``--host`` überschreiben die ENV-Werte
    (Abwärtskompatibilität mit der README-Doku). Default bleibt lokal: stdio + Loopback.
    """
    from .telemetry import setup_telemetry

    setup_telemetry()  # opt-in via MCP_OTEL_ENABLED; No-Op sonst (OBS-006)

    transport = settings.transport
    host = settings.host
    port = settings.port

    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--http":
            transport = "streamable-http"
        elif arg == "--sse":
            transport = "sse"
        elif arg == "--port" and i + 1 < len(argv):
            port = int(argv[i + 1])
        elif arg == "--host" and i + 1 < len(argv):
            host = argv[i + 1]

    # Netzwerk-Binding nur für HTTP-Transporte relevant.
    mcp.settings.host = host
    mcp.settings.port = port

    if transport in ("streamable-http", "sse"):
        _run_http(transport, host, port)
    else:
        mcp.run(transport="stdio")


def _run_http(transport: str, host: str, port: int) -> None:
    """Startet einen HTTP-Transport mit CORS-Middleware (SDK-004).

    Die Starlette-App wird um ``CORSMiddleware`` gewickelt, die ``Mcp-Session-Id``
    explizit exponiert und akzeptiert (sonst brechen Browser-Clients wie claude.ai).
    Origins kommen aus ``MCP_CORS_ORIGINS`` — keine Wildcard in Produktion.
    """
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware

    app = mcp.sse_app() if transport == "sse" else mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Mcp-Session-Id", "Last-Event-ID"],
        expose_headers=["Mcp-Session-Id"],
        max_age=86_400,
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
