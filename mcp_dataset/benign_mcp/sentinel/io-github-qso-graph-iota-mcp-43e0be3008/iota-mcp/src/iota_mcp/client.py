"""IOTA API client — bulk JSON download, in-memory indexes, 24h cache."""

from __future__ import annotations

import json
import math
import os
import threading
import time
import urllib.request
from typing import Any

from . import __version__

_BASE = "https://www.iota-world.org/islands-on-the-air/downloads/download-file.html?path="
_FULLLIST_PATH = "fulllist.json"
_DXCC_MAP_PATH = "dxcc_matches_one_iota.json"

_FULLLIST_TTL = 86400.0  # 24 hours — data refreshes daily at 00:00 UTC
_MIN_DELAY = 0.2  # 200ms between requests (good neighbor)


def _is_mock() -> bool:
    return os.getenv("IOTA_MCP_MOCK") == "1"


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

_MOCK_FULLLIST: list[dict[str, Any]] = [
    {
        "refno": "OC-001",
        "name": "Australian Mainland",
        "dxcc_num": "150",
        "latitude_max": "-10.00",
        "latitude_min": "-44.00",
        "longitude_max": "154.00",
        "longitude_min": "113.00",
        "grp_region": "",
        "whitelist": "0",
        "pc_credited": "92.1",
        "comment": "",
        "sub_groups": [
            {
                "subref": "OC-001-0-0",
                "subname": "[No sub-group]",
                "status": "Active",
                "islands": [
                    {"id": "1001", "island_name": "Australia", "comment": "", "excluded": "0"},
                    {"id": "1002", "island_name": "Tasmania", "comment": "", "excluded": "0"},
                ],
            }
        ],
    },
    {
        "refno": "OC-019",
        "name": "Hawaiian Islands",
        "dxcc_num": "110",
        "latitude_max": "22.50",
        "latitude_min": "18.50",
        "longitude_max": "-154.50",
        "longitude_min": "-160.50",
        "grp_region": "",
        "whitelist": "0",
        "pc_credited": "88.5",
        "comment": "",
        "sub_groups": [
            {
                "subref": "OC-019-0-0",
                "subname": "[No sub-group]",
                "status": "Active",
                "islands": [
                    {"id": "2001", "island_name": "Oahu", "comment": "", "excluded": "0"},
                    {"id": "2002", "island_name": "Maui", "comment": "", "excluded": "0"},
                    {"id": "2003", "island_name": "Hawaii (Big Island)", "comment": "", "excluded": "0"},
                ],
            }
        ],
    },
    {
        "refno": "EU-005",
        "name": "British Isles",
        "dxcc_num": "223,114",
        "latitude_max": "61.00",
        "latitude_min": "49.50",
        "longitude_max": "2.00",
        "longitude_min": "-11.00",
        "grp_region": "",
        "whitelist": "0",
        "pc_credited": "95.3",
        "comment": "",
        "sub_groups": [
            {
                "subref": "EU-005-1-0",
                "subname": "England",
                "status": "Active",
                "islands": [
                    {"id": "3001", "island_name": "Great Britain", "comment": "", "excluded": "0"},
                ],
            },
            {
                "subref": "EU-005-2-0",
                "subname": "Scotland",
                "status": "Active",
                "islands": [
                    {"id": "3002", "island_name": "Shetland", "comment": "", "excluded": "0"},
                    {"id": "3003", "island_name": "Orkney", "comment": "", "excluded": "0"},
                ],
            },
        ],
    },
    {
        "refno": "AF-007",
        "name": "Comoro Islands",
        "dxcc_num": "411",
        "latitude_max": "-11.25",
        "latitude_min": "-13.00",
        "longitude_max": "44.75",
        "longitude_min": "43.00",
        "grp_region": "",
        "whitelist": "0",
        "pc_credited": "45.6",
        "comment": "",
        "sub_groups": [
            {
                "subref": "AF-007-0-0",
                "subname": "[No sub-group]",
                "status": "Active",
                "islands": [
                    {"id": "4001", "island_name": "Grande Comore", "comment": "", "excluded": "0"},
                    {"id": "4002", "island_name": "Moheli", "comment": "", "excluded": "0"},
                    {"id": "4003", "island_name": "Anjouan", "comment": "", "excluded": "0"},
                ],
            }
        ],
    },
]

_MOCK_DXCC_MAP: list[dict[str, str]] = [
    {"dxcc_num": "150", "refno": "OC-001"},
    {"dxcc_num": "110", "refno": "OC-019"},
    {"dxcc_num": "223", "refno": "EU-005"},
    {"dxcc_num": "114", "refno": "EU-005"},
    {"dxcc_num": "411", "refno": "AF-007"},
]


class IOTAClient:
    """IOTA data client with bulk download, in-memory indexes, and 24h cache."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_request: float = 0.0
        self._loaded_at: float = 0.0
        # Indexes
        self._by_refno: dict[str, dict[str, Any]] = {}
        self._by_dxcc: dict[str, list[str]] = {}
        self._name_index: list[tuple[str, str]] = []
        self._island_index: list[tuple[str, str, str]] = []

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Load data if not yet loaded or cache expired."""
        now = time.monotonic()
        if self._by_refno and (now - self._loaded_at) < _FULLLIST_TTL:
            return
        self._load_data()

    def _load_data(self) -> None:
        """Download JSON files (or use mock) and build indexes."""
        if _is_mock():
            fulllist = list(_MOCK_FULLLIST)
            dxcc_map = list(_MOCK_DXCC_MAP)
        else:
            fulllist = self._get_json(f"{_BASE}{_FULLLIST_PATH}") or []
            dxcc_map = self._get_json(f"{_BASE}{_DXCC_MAP_PATH}") or []
        self._build_indexes(fulllist, dxcc_map)
        self._loaded_at = time.monotonic()

    def _build_indexes(
        self,
        fulllist: list[dict[str, Any]],
        dxcc_map: list[dict[str, str]],
    ) -> None:
        """Build all in-memory indexes from raw data."""
        by_refno: dict[str, dict[str, Any]] = {}
        by_dxcc: dict[str, list[str]] = {}
        name_index: list[tuple[str, str]] = []
        island_index: list[tuple[str, str, str]] = []

        for group in fulllist:
            refno = group.get("refno", "")
            if not refno:
                continue
            by_refno[refno] = group
            name_index.append((group.get("name", "").lower(), refno))

            # Index DXCC from fulllist (can be comma-separated)
            dxcc_str = group.get("dxcc_num", "")
            for dxcc in dxcc_str.split(","):
                dxcc = dxcc.strip()
                if dxcc:
                    by_dxcc.setdefault(dxcc, [])
                    if refno not in by_dxcc[dxcc]:
                        by_dxcc[dxcc].append(refno)

            # Index islands
            for sg in group.get("sub_groups", []):
                for isl in sg.get("islands", []):
                    iname = isl.get("island_name", "")
                    iid = isl.get("id", "")
                    if iname:
                        island_index.append((iname.lower(), iid, refno))

        # Merge 1:1 DXCC map entries
        for entry in dxcc_map:
            dxcc = entry.get("dxcc_num", "").strip()
            refno = entry.get("refno", "").strip()
            if dxcc and refno:
                by_dxcc.setdefault(dxcc, [])
                if refno not in by_dxcc[dxcc]:
                    by_dxcc[dxcc].append(refno)

        self._by_refno = by_refno
        self._by_dxcc = by_dxcc
        self._name_index = name_index
        self._island_index = island_index

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Enforce minimum delay between requests."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < _MIN_DELAY:
                time.sleep(_MIN_DELAY - elapsed)
            self._last_request = time.monotonic()

    def _get_json(self, url: str) -> Any:
        """HTTP GET, return parsed JSON."""
        self._rate_limit()
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", f"iota-mcp/{__version__}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch IOTA data") from exc
        if not body or body.strip() == "":
            return None
        return json.loads(body)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _center(group: dict[str, Any]) -> tuple[float, float]:
        """Compute center lat/lon from bounding box."""
        try:
            lat = (float(group["latitude_min"]) + float(group["latitude_max"])) / 2.0
            lon = (float(group["longitude_min"]) + float(group["longitude_max"])) / 2.0
            return lat, lon
        except (KeyError, ValueError, TypeError):
            return 0.0, 0.0

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance in km between two points."""
        R = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _island_count(group: dict[str, Any]) -> int:
        """Count total islands across all subgroups."""
        total = 0
        for sg in group.get("sub_groups", []):
            total += len(sg.get("islands", []))
        return total

    def _format_group(self, group: dict[str, Any]) -> dict[str, Any]:
        """Format a group for API output."""
        lat, lon = self._center(group)
        return {
            "refno": group.get("refno", ""),
            "name": group.get("name", ""),
            "dxcc_num": group.get("dxcc_num", ""),
            "continent": group.get("refno", "")[:2],
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "bbox": {
                "lat_min": group.get("latitude_min", ""),
                "lat_max": group.get("latitude_max", ""),
                "lon_min": group.get("longitude_min", ""),
                "lon_max": group.get("longitude_max", ""),
            },
            "region": group.get("grp_region", ""),
            "pc_credited": group.get("pc_credited", ""),
            "island_count": self._island_count(group),
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def lookup(self, refno: str) -> dict[str, Any]:
        """Look up an IOTA group by reference number."""
        self._ensure_loaded()
        ref = refno.upper().strip()
        group = self._by_refno.get(ref)
        if not group:
            return {"refno": ref, "error": "Not found"}
        result = self._format_group(group)
        result["comment"] = group.get("comment", "")
        result["subgroup_count"] = len(group.get("sub_groups", []))
        return result

    def search(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        """Search groups and islands by name substring."""
        self._ensure_loaded()
        q = query.lower().strip()
        if not q:
            return []

        seen: set[str] = set()
        results: list[dict[str, Any]] = []

        # Search group names
        for name_lower, refno in self._name_index:
            if q in name_lower and refno not in seen:
                group = self._by_refno.get(refno)
                if group:
                    results.append(self._format_group(group))
                    seen.add(refno)

        # Search island names
        for iname_lower, _iid, refno in self._island_index:
            if q in iname_lower and refno not in seen:
                group = self._by_refno.get(refno)
                if group:
                    entry = self._format_group(group)
                    entry["matched_island"] = iname_lower.title()
                    results.append(entry)
                    seen.add(refno)

        return results[:limit]

    def islands(self, refno: str) -> dict[str, Any]:
        """List all islands and subgroups in an IOTA group."""
        self._ensure_loaded()
        ref = refno.upper().strip()
        group = self._by_refno.get(ref)
        if not group:
            return {"refno": ref, "error": "Not found"}

        subgroups = []
        for sg in group.get("sub_groups", []):
            islands = []
            for isl in sg.get("islands", []):
                islands.append({
                    "id": isl.get("id", ""),
                    "name": isl.get("island_name", ""),
                    "excluded": isl.get("excluded", "0") == "1",
                })
            subgroups.append({
                "subref": sg.get("subref", ""),
                "name": sg.get("subname", ""),
                "status": sg.get("status", ""),
                "island_count": len(islands),
                "islands": islands,
            })

        return {
            "refno": ref,
            "group_name": group.get("name", ""),
            "subgroup_count": len(subgroups),
            "total_islands": self._island_count(group),
            "subgroups": subgroups,
        }

    def dxcc_lookup(
        self,
        dxcc_num: str = "",
        refno: str = "",
    ) -> dict[str, Any]:
        """Bidirectional DXCC-to-IOTA mapping."""
        self._ensure_loaded()

        if dxcc_num and not refno:
            dxcc = dxcc_num.strip()
            refnos = self._by_dxcc.get(dxcc, [])
            groups = []
            for ref in refnos:
                group = self._by_refno.get(ref)
                if group:
                    groups.append(self._format_group(group))
            return {
                "dxcc_num": dxcc,
                "iota_count": len(groups),
                "groups": groups,
            }

        if refno and not dxcc_num:
            ref = refno.upper().strip()
            group = self._by_refno.get(ref)
            if not group:
                return {"refno": ref, "error": "Not found"}
            dxcc_str = group.get("dxcc_num", "")
            dxcc_list = [d.strip() for d in dxcc_str.split(",") if d.strip()]
            return {
                "refno": ref,
                "name": group.get("name", ""),
                "dxcc_entities": dxcc_list,
            }

        return {"error": "Provide either dxcc_num or refno (not both)"}

    def stats(self) -> dict[str, Any]:
        """Programme summary statistics."""
        self._ensure_loaded()

        continents: dict[str, int] = {}
        total_islands = 0
        most_credited = ("", 0.0)
        least_credited = ("", 100.0)

        for refno, group in self._by_refno.items():
            continent = refno[:2]
            continents[continent] = continents.get(continent, 0) + 1
            total_islands += self._island_count(group)
            try:
                pc = float(group.get("pc_credited", "0"))
            except (ValueError, TypeError):
                pc = 0.0
            if pc > most_credited[1]:
                most_credited = (refno, pc)
            if 0 < pc < least_credited[1]:
                least_credited = (refno, pc)

        return {
            "total_groups": len(self._by_refno),
            "total_islands": total_islands,
            "total_dxcc_entities": len(self._by_dxcc),
            "groups_by_continent": dict(sorted(continents.items())),
            "most_credited": {
                "refno": most_credited[0],
                "name": self._by_refno.get(most_credited[0], {}).get("name", ""),
                "pc_credited": most_credited[1],
            },
            "least_credited": {
                "refno": least_credited[0],
                "name": self._by_refno.get(least_credited[0], {}).get("name", ""),
                "pc_credited": least_credited[1],
            },
        }

    def nearby(
        self,
        latitude: float,
        longitude: float,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find IOTA groups nearest to a lat/lon point."""
        self._ensure_loaded()

        distances: list[tuple[float, str]] = []
        for refno, group in self._by_refno.items():
            clat, clon = self._center(group)
            if clat == 0.0 and clon == 0.0:
                continue
            dist = self._haversine(latitude, longitude, clat, clon)
            distances.append((dist, refno))

        distances.sort()
        results = []
        for dist, refno in distances[:limit]:
            group = self._by_refno[refno]
            entry = self._format_group(group)
            entry["distance_km"] = round(dist, 1)
            results.append(entry)

        return results
