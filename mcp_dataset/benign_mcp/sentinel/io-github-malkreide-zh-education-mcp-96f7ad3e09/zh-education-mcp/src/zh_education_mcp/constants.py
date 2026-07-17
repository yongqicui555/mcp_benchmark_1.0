"""Konstanten: API-Basis, Timeouts, Cache-TTL, BISTA-Endpunkte."""

from __future__ import annotations

BISTA_API = "https://www.bista.zh.ch/basicapi/ogd"
HTTP_TIMEOUT = 30.0
CACHE_TTL = 86_400  # 24 Stunden — passend zum jährlichen Stichtag

# Endpunkte
EP_SEK1 = "data_lernende_sekundarstufe_i_anforderungstyp"
EP_UEBERSICHT = "data_uebersicht_alle_lernende"
EP_NAT_REGIONAL = "data_lernende_regelschule_regional_staatsangehoerigkeit"
EP_MATURITAET = "data_maturitaetsquote_gemeinden_und_kanton"
EP_WOHNORT = "data_lernende_nach_wohngemeinde"
EP_MITTELSCHULEN = "data_lernende_mittelschulen"
