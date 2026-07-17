"""Code-Layer Egress-Allow-List (SEC-021).

Defense-in-Depth: vor jedem ausgehenden HTTP-Request wird geprüft, ob der
Ziel-Host in einer **unveränderlichen** Allow-List steht. Verhindert, dass der
Server – etwa durch einen Bug oder Prompt-Injection – beliebige Hosts
kontaktiert. Die Network-Layer-Ergänzung (Kubernetes NetworkPolicy) liegt unter
``deploy/k8s/`` und ist in ``docs/network-egress.md`` dokumentiert.
"""

from __future__ import annotations

from urllib.parse import urlparse

# Unveränderliche Allow-List (frozenset, nicht zur Laufzeit mutierbar/config-bar).
ALLOWED_HOSTS: frozenset[str] = frozenset({"ws.parlament.ch"})


class EgressNotAllowed(Exception):
    """Wird geworfen, wenn ein nicht erlaubter Host kontaktiert werden soll."""


def assert_host_allowed(url: str) -> None:
    """Bricht ab, wenn der Host der URL nicht in ``ALLOWED_HOSTS`` ist."""
    host = (urlparse(url).hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise EgressNotAllowed(
            f"Host nicht in Egress-Allow-List: {host!r} "
            f"(erlaubt: {sorted(ALLOWED_HOSTS)})"
        )
