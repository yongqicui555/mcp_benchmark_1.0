"""Unit tests for TTL cache."""

import time

from stocksense.data.cache import TTLCache


def test_cache_set_and_get():
    cache = TTLCache(default_ttl=60)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_miss():
    cache = TTLCache()
    assert cache.get("nonexistent") is None


def test_cache_ttl_expiry():
    cache = TTLCache(default_ttl=1)
    cache.set("key1", "value1", ttl_seconds=1)
    assert cache.get("key1") == "value1"
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_cache_overwrite():
    cache = TTLCache()
    cache.set("key1", "old")
    cache.set("key1", "new")
    assert cache.get("key1") == "new"


def test_cache_custom_ttl_overrides_default():
    cache = TTLCache(default_ttl=1)
    cache.set("short", "val", ttl_seconds=1)
    cache.set("long", "val", ttl_seconds=60)
    time.sleep(1.1)
    assert cache.get("short") is None
    assert cache.get("long") == "val"


def test_cache_clear():
    cache = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
