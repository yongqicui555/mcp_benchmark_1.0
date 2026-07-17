"""HTTP-Client mit Egress-Guard, Connection-Pooling und Lifespan (SDK-001, SEC-004/021)."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx

from .constants import HTTP_TIMEOUT
from .logging_setup import log

# Egress-Allow-List (SEC-004/SEC-021): nur diese Hosts dürfen kontaktiert werden,
# als unveränderliches frozenset im Code (nicht zur Laufzeit mutierbar).
ALLOWED_HOSTS: frozenset[str] = frozenset({"www.bista.zh.ch"})


def _ip_is_blocked(ip: str) -> bool:
    """True, wenn die IP nicht öffentlich routbar ist (private/loopback/
    link-local/metadata/reserved) — gegen SSRF auf interne Ziele (SEC-005)."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local  # deckt 169.254.169.254 (Cloud-Metadata) ab
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _resolve_and_validate(host: str) -> list[str]:
    """Löst ``host`` auf und validiert ALLE resolved IPs gegen die Blocklist.

    Wird vor dem Request aufgerufen (DNS-Pinning-Kern gegen TOCTOU/DNS-Rebinding,
    SEC-005): Auflösung erfolgt einmal hier; eine aufgelöste interne IP führt zum
    harten Abbruch, bevor überhaupt verbunden wird. Gibt die geprüften IPs zurück.
    """
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise PermissionError(f"DNS-Auflösung für {host} fehlgeschlagen: {exc}") from exc

    ips = sorted({info[4][0] for info in infos})
    blocked = [ip for ip in ips if _ip_is_blocked(ip)]
    if blocked:
        log.warning("egress_ip_blocked", host=host, blocked=blocked, resolved=ips)
        raise PermissionError(
            f"Egress blockiert: {host} löst auf interne/nicht-routbare IP(s) auf {blocked}"
        )
    return ips


async def _egress_guard(request: httpx.Request) -> None:
    """Prüft JEDEN ausgehenden Request (inkl. Redirect-Hops, SEC-004):

    1. HTTPS erzwingen, Host gegen Allow-List (SEC-004/021).
    2. Host auflösen und alle resolved IPs gegen die Blocklist prüfen
       (SEC-005): blockt DNS-Rebinding/Metadata-IPs vor dem Verbindungsaufbau.
    """
    if request.url.scheme != "https" or request.url.host not in ALLOWED_HOSTS:
        raise PermissionError(
            f"Egress blockiert: {request.url.scheme}://{request.url.host} "
            f"nicht in Allow-List {sorted(ALLOWED_HOSTS)}"
        )
    _resolve_and_validate(request.url.host)


def _new_client() -> httpx.AsyncClient:
    """Erzeugt einen HTTP-Client mit Egress-Guard und einheitlichem Timeout."""
    return httpx.AsyncClient(
        follow_redirects=True,
        timeout=HTTP_TIMEOUT,
        event_hooks={"request": [_egress_guard]},
    )


@dataclass
class AppContext:
    """Geteilte Ressourcen über die Server-Laufzeit (via lifespan injiziert)."""

    client: httpx.AsyncClient


# Lifespan-verwalteter, wiederverwendeter HTTP-Client (Connection-Pooling).
# Kein httpx.AsyncClient pro Tool-Call mehr (siehe Audit SDK-001).
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Gibt den gepoolten HTTP-Client zurück.

    Im Server-Betrieb wird der Client einmalig im :func:`lifespan` erzeugt.
    Für direkte/Unit-Test-Aufrufe ausserhalb der Lifespan wird er lazy
    erzeugt — in beiden Fällen genau **ein** Client statt einer pro Request.
    """
    global _client
    if _client is None or _client.is_closed:
        _client = _new_client()
    return _client


@asynccontextmanager
async def lifespan(_server: object) -> AsyncIterator[AppContext]:
    """Erzeugt den geteilten HTTP-Client beim Start, schliesst ihn beim Stop."""
    global _client
    _client = _new_client()
    try:
        yield AppContext(client=_client)
    finally:
        await _client.aclose()
        _client = None


async def _http_get(url: str, params: dict | None = None) -> httpx.Response:
    """HTTP-GET über den gepoolten, lifespan-verwalteten Client."""
    client = _get_client()
    return await client.get(url, params=params, timeout=HTTP_TIMEOUT)
