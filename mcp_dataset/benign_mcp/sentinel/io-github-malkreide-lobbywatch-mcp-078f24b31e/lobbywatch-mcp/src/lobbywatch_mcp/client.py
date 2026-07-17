"""Data access layer for lobbywatch-mcp.

Design: dump-first, API-fallback.

Rationale (verified live on 2026-04-21):
    * The weekly aggregated JSON dump is stable, contains 245 parliamentarians
      with 113 scalar fields and 7'780 interessenbindungen total, and is
      refreshed every Monday morning by Lobbywatch.
    * The live dataIF REST API currently returns 0 records for the
      ``/table/parlamentarier/...`` endpoints. Other tables (interessengruppe,
      branche) work. So we use the dump for parliamentarian queries and fall
      back to the live API only for lobby groups and search.
"""

from __future__ import annotations

import asyncio
import io
import ipaddress
import json
import logging
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from lobbywatch_mcp.config import (
    API_BASE,
    CACHE_DIR,
    CACHE_TTL_SECONDS,
    DUMP_INNER_FILE,
    DUMP_URL,
    HTTP_TIMEOUT_SECONDS,
    USER_AGENT,
)

logger = logging.getLogger(__name__)


# Networks an outbound MCP request must never reach: RFC1918 / link-local /
# loopback / cloud-metadata. Pre-built once because each request goes through
# the SSRF guard hook below (audit SEC-005).
_SSRF_FORBIDDEN_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = tuple(
    ipaddress.ip_network(cidr)
    for cidr in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",  # link-local incl. cloud metadata (169.254.169.254)
        "127.0.0.0/8",
        "0.0.0.0/8",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)


def _is_forbidden_address(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return any(addr in net for net in _SSRF_FORBIDDEN_NETWORKS)


async def _ssrf_guard(request: httpx.Request) -> None:
    """httpx event hook: refuse requests whose host resolves to a private,
    link-local, or loopback address (audit SEC-005, defense-in-depth against
    DNS rebinding / SSRF).

    The host is already constrained by the hardcoded ``API_BASE`` /
    ``DUMP_URL`` constants, but the resolver could still drift between
    process start and any individual request — this hook catches that.
    """
    host = request.url.host
    if not host:
        return
    # Allow literal IP URLs only if they are not in a forbidden network.
    try:
        ipaddress.ip_address(host)
        if _is_forbidden_address(host):
            raise RuntimeError(f"Refusing to connect to forbidden address {host}")
        return
    except ValueError:
        pass  # not a literal IP — resolve below

    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(host, None)
    except OSError:
        # Resolver failure: let httpx surface its own error rather than
        # masking it here.
        return
    resolved = sorted({info[4][0] for info in infos})
    bad = [ip for ip in resolved if _is_forbidden_address(ip)]
    if bad:
        logger.error(
            "SSRF guard blocked %s — resolved to forbidden addresses %s",
            host,
            bad,
        )
        raise RuntimeError(f"Refusing to connect to {host}: resolved to forbidden addresses {bad}")


class LobbywatchClient:
    """Access layer around the weekly dump and the live dataIF."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_seconds: int = CACHE_TTL_SECONDS,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._cache_dir = cache_dir or CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl_seconds
        self._dump_path = self._cache_dir / "aggregated.json"
        self._records: list[dict[str, Any]] | None = None
        self._loaded_at: float | None = None
        self._lock = asyncio.Lock()
        self._http = http_client or httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=False,
            event_hooks={"request": [_ssrf_guard]},
        )
        self._owns_http = http_client is None

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    # ------------------------------------------------------------------
    # Dump handling
    # ------------------------------------------------------------------

    async def ensure_dump_loaded(self, force: bool = False) -> None:
        """Download, cache, and load the weekly JSON dump if needed."""
        async with self._lock:
            if not force and self._records is not None and self._is_fresh():
                return

            if force or not self._dump_path.exists() or self._file_stale(self._dump_path):
                await self._download_dump()

            self._records = self._parse_dump(self._dump_path)
            self._loaded_at = time.time()
            logger.info("Dump loaded: %d parliamentarians", len(self._records))

    def _is_fresh(self) -> bool:
        return self._loaded_at is not None and (time.time() - self._loaded_at) < self._ttl

    def _file_stale(self, path: Path) -> bool:
        try:
            age = time.time() - path.stat().st_mtime
        except OSError:
            return True
        return age > self._ttl

    async def _download_dump(self) -> None:
        """Download the weekly dump with retry + exponential backoff.

        The Lobbywatch CMS occasionally returns HTTP 503 during maintenance
        windows. Three retries with 2s / 4s / 8s wait smooth over these blips.
        """
        last_error: Exception | None = None
        resp: httpx.Response | None = None
        for attempt in range(4):
            if attempt > 0:
                wait_seconds = 2**attempt
                logger.warning(
                    "Dump download attempt %d failed (%s); retrying in %ds",
                    attempt,
                    type(last_error).__name__ if last_error else "?",
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)
            try:
                logger.info("Downloading Lobbywatch dump from %s", DUMP_URL)
                resp = await self._http.get(DUMP_URL)
                resp.raise_for_status()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_error = exc
                # 4xx responses other than 429 should not be retried.
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status is not None and 400 <= status < 500 and status != 429:
                    raise
        if resp is None:
            assert last_error is not None
            logger.error("Lobbywatch dump unreachable after retries: %r", last_error)
            raise RuntimeError("Lobbywatch dump unreachable after retries") from last_error

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            # The dump contains a few files; we want the essential nested variant.
            inner_name = DUMP_INNER_FILE
            if inner_name not in zf.namelist():
                # Some weeks ship slightly different inner names — take the first
                # JSON with "parlamentarier_nested" in it.
                candidates = [
                    n for n in zf.namelist() if n.endswith(".json") and "parlamentarier_nested" in n
                ]
                if not candidates:
                    logger.error("Dump archive members: %s", zf.namelist())
                    raise RuntimeError("Lobbywatch dump format unexpected")
                inner_name = candidates[0]
            with zf.open(inner_name) as src, self._dump_path.open("wb") as dst:
                dst.write(src.read())

    @staticmethod
    def _parse_dump(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.error("Unexpected dump shape: %s", type(data).__name__)
            raise RuntimeError("Lobbywatch dump shape invalid")
        return data

    # ------------------------------------------------------------------
    # Accessors (dump-based)
    # ------------------------------------------------------------------

    async def all_parlamentarier(self) -> list[dict[str, Any]]:
        await self.ensure_dump_loaded()
        assert self._records is not None
        return self._records

    async def find_parlamentarier(self, id_or_name: int | str) -> dict[str, Any] | None:
        records = await self.all_parlamentarier()
        if isinstance(id_or_name, int) or (isinstance(id_or_name, str) and id_or_name.isdigit()):
            wanted = int(id_or_name)
            for r in records:
                if r.get("id") == wanted:
                    return r
            return None

        # String search: try exact anzeige_name, then fuzzy on nachname/vorname.
        from rapidfuzz import fuzz, process

        query = str(id_or_name).strip().lower()

        exact = [r for r in records if (r.get("anzeige_name", "") or "").lower() == query]
        if exact:
            return exact[0]

        names = [(r.get("anzeige_name") or "", r) for r in records]
        best = process.extractOne(query, [n for n, _ in names], scorer=fuzz.WRatio, score_cutoff=70)
        if not best:
            return None
        _matched_name, _score, idx = best
        return names[idx][1]

    async def find_candidates(
        self,
        query: str,
        *,
        min_score: int = 50,
        max_score_excl: int = 70,
        top_k: int = 3,
    ) -> list[tuple[dict[str, Any], int]]:
        """Return up to ``top_k`` near-miss parliamentarian records ranked by
        rapidfuzz WRatio (audit ARCH-003 — avoid the silent "not found" by
        offering "did you mean…?" candidates).

        Only results in ``[min_score, max_score_excl)`` are returned: the
        upper bound stays below ``find_parlamentarier``'s 70 threshold so
        these are *misses*, not silently competing matches.
        """
        if not query.strip() or query.isdigit():
            return []
        from rapidfuzz import fuzz, process

        records = await self.all_parlamentarier()
        names = [(r.get("anzeige_name") or "", r) for r in records]
        candidates = process.extract(
            query.strip().lower(),
            [n for n, _ in names],
            scorer=fuzz.WRatio,
            limit=top_k,
            score_cutoff=min_score,
        )
        return [
            (names[idx][1], int(score))
            for _name, score, idx in candidates
            if score < max_score_excl
        ]

    async def status(self) -> dict[str, Any]:
        loaded = self._records is not None
        age = int(time.time() - self._loaded_at) if self._loaded_at else None
        return {
            "loaded": loaded,
            "age_seconds": age,
            "record_count": len(self._records) if self._records else 0,
            "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._loaded_at))
            if self._loaded_at
            else None,
        }

    # ------------------------------------------------------------------
    # Live dataIF (fallback path)
    # ------------------------------------------------------------------

    async def api_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{API_BASE}/{path.lstrip('/')}"
        resp = await self._http.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def fetch_lobbygruppe(self, id_or_name: int | str) -> dict[str, Any] | None:
        """Use the live dataIF — this endpoint was verified working."""
        if isinstance(id_or_name, int) or (isinstance(id_or_name, str) and id_or_name.isdigit()):
            data = await self.api_get(f"table/interessengruppe/aggregated/id/{int(id_or_name)}")
            return data.get("data")

        # Search by name first, then fetch aggregated. URL-encode user input to
        # prevent path traversal — the host is hardcoded but path segments still
        # warrant escaping (audit SEC-004).
        search = await self.api_get(
            f"search/default/{quote(str(id_or_name), safe='')}",
            params={"limit": 5},
        )
        hits = search.get("data") or []
        for hit in hits:
            if hit.get("table") == "interessengruppe":
                data = await self.api_get(f"table/interessengruppe/aggregated/id/{hit.get('id')}")
                return data.get("data")
        return None
