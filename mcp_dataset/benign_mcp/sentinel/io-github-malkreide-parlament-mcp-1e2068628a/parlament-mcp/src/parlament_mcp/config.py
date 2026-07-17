"""Zentrale Konfiguration via pydantic-settings (ARCH-004).

Statt verstreuter ``os.environ``-Zugriffe wird die Server-Konfiguration in
einem einzigen, typgeprüften ``Settings``-Objekt gebündelt. Felder werden aus
``MCP_*``-Environment-Variablen geladen (z.B. ``MCP_TRANSPORT``, ``MCP_HOST``).
"""

from __future__ import annotations

import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

# MCP-Spec-Version, gegen die dieser Server getestet/gepinnt ist (ARCH-012).
# Wird im README und CHANGELOG referenziert; das SDK handhabt die eigentliche
# Protokoll-Negotiation, hier dokumentieren wir die getestete Ziel-Version.
PROTOCOL_VERSION = "2025-06-18"

# Datenquelle / Lizenz (CH-004 — OGD-CH-Attribution).
DATA_SOURCE = "Curia Vista – Schweizer Parlament (ws.parlament.ch)"
DATA_LICENSE = "CC BY 4.0"


class Settings(BaseSettings):
    """Server-Laufzeitkonfiguration. Defaults sind lokal-sicher."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8080
    log_level: str = "INFO"
    json_logs: bool = True
    otel_enabled: bool = True


def warn_on_dangerous_binding(host: str) -> None:
    """Warnt, wenn ausserhalb eines Container-Kontexts an 0.0.0.0 gebunden wird
    (SEC-016, NeighborJack)."""
    import os

    if host in ("0.0.0.0", "::"):
        in_container = (
            os.path.exists("/.dockerenv")
            or os.environ.get("KUBERNETES_SERVICE_HOST")
            or os.environ.get("RAILWAY_PROJECT_ID")
            or os.environ.get("RENDER")
        )
        if not in_container:
            sys.stderr.write(
                f"WARNUNG: Bindung an {host} ausserhalb eines Container-Kontexts "
                "exponiert den Server im lokalen Netzwerk (NeighborJack-Risiko). "
                "Für lokale Nutzung MCP_HOST=127.0.0.1 setzen.\n"
            )
