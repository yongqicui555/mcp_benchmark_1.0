"""In-memory TTL cache for financial data."""

import time
from typing import Any


class TTLCache:
    """Simple dict-based cache with per-key expiry timestamps."""

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """Return cached value if it exists and hasn't expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value with a TTL (defaults to instance default)."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = (value, time.time() + ttl)

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()


# Shared cache instances
price_cache = TTLCache(default_ttl=300)   # 5 min for price data
quote_cache = TTLCache(default_ttl=60)    # 1 min for live quotes
financials_cache = TTLCache(default_ttl=1800)  # 30 min for financial statements
filings_cache = TTLCache(default_ttl=1800)  # 30 min for filing metadata
cik_cache = TTLCache(default_ttl=86400)   # 24 hr for CIK map
