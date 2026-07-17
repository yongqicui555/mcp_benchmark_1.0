"""
License Validation for Artefact MCP Server

Validates license keys against LemonSqueezy API with local caching.
Free tier (sample data) works without a license key.
Pro/Enterprise tiers require a valid ARTEFACT_LICENSE_KEY.
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx


# --- Configuration ---
LEMONSQUEEZY_STORE_ID = os.getenv("ARTEFACT_LS_STORE_ID", "290340")
LEMONSQUEEZY_PRODUCT_ID = os.getenv("ARTEFACT_LS_PRODUCT_ID", "822853")
LEMONSQUEEZY_VALIDATE_URL = "https://api.lemonsqueezy.com/v1/licenses/validate"
CACHE_TTL_SECONDS = 86400  # 24 hours
CACHE_FILE = Path.home() / ".artefact-mcp" / "license_cache.json"

# Tier mapping from LemonSqueezy variant names
TIER_MAP = {
    "pro": "pro",
    "enterprise": "enterprise",
}


@dataclass
class LicenseInfo:
    """Validated license information."""

    valid: bool
    tier: str  # "free", "pro", "enterprise"
    customer_name: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None


def validate_license(license_key: Optional[str] = None) -> LicenseInfo:
    """Validate a license key. Returns LicenseInfo with tier and validity.

    If no key is provided, returns free tier (sample data only).
    """
    key = license_key or os.getenv("ARTEFACT_LICENSE_KEY")

    if not key:
        return LicenseInfo(valid=True, tier="free")

    # Dev bypass: skip LemonSqueezy validation for local testing.
    # Key is verified by hash only — the actual key is not stored in source.
    if _hash_key(key) == "425e17387f7d9311":
        return LicenseInfo(valid=True, tier="pro", customer_name="Dev Testing")

    # Check local cache first
    cached = _read_cache(key)
    if cached:
        return cached

    # Validate against LemonSqueezy API
    result = _validate_remote(key)

    # Cache the result
    if result.valid:
        _write_cache(key, result)

    return result


def require_license(source: str, license_info: LicenseInfo) -> None:
    """Check if the requested source is allowed by the license tier.

    Raises ValueError if the source requires a higher tier.
    """
    if source == "sample":
        return  # Sample data always allowed

    if source == "hubspot" and license_info.tier == "free":
        raise ValueError(
            "Live HubSpot data requires a Pro license. "
            "Purchase at https://artefactventures.lemonsqueezy.com\n"
            "Set ARTEFACT_LICENSE_KEY in your environment to activate.\n"
            "Use source='sample' for free demo data."
        )


def _validate_remote(license_key: str) -> LicenseInfo:
    """Validate license key against LemonSqueezy API."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                LEMONSQUEEZY_VALIDATE_URL,
                json={
                    "license_key": license_key,
                    "instance_name": "artefact-mcp",
                },
            )

        if response.status_code != 200:
            return LicenseInfo(
                valid=False,
                tier="free",
                error=f"License validation failed (HTTP {response.status_code})",
            )

        data = response.json()

        if not data.get("valid"):
            return LicenseInfo(
                valid=False,
                tier="free",
                error=data.get("error", "Invalid license key"),
            )

        # Verify store + product ID to prevent cross-product key reuse
        meta = data.get("meta", {})
        store_id = str(meta.get("store_id", ""))
        product_id = str(meta.get("product_id", ""))

        if LEMONSQUEEZY_STORE_ID and store_id and store_id != LEMONSQUEEZY_STORE_ID:
            return LicenseInfo(
                valid=False,
                tier="free",
                error=(
                    "License key does not belong to this product. "
                    "Purchase a valid license at https://artefactventures.lemonsqueezy.com"
                ),
            )
        if LEMONSQUEEZY_PRODUCT_ID and product_id and product_id != LEMONSQUEEZY_PRODUCT_ID:
            return LicenseInfo(
                valid=False,
                tier="free",
                error=(
                    "License key does not belong to this product. "
                    "Purchase a valid license at https://artefactventures.lemonsqueezy.com"
                ),
            )

        # Determine tier from variant name
        variant_name = meta.get("variant_name", "").lower()
        tier = TIER_MAP.get(variant_name, "pro")  # Default to pro for valid keys

        customer_name = data.get("license_key", {}).get("customer_name")
        expires_at = data.get("license_key", {}).get("expires_at")

        return LicenseInfo(
            valid=True,
            tier=tier,
            customer_name=customer_name,
            expires_at=expires_at,
        )

    except httpx.ConnectError:
        # If we can't reach LemonSqueezy, check cache with extended TTL
        cached = _read_cache(license_key, grace_ttl=604800)  # 7-day grace
        if cached:
            return cached
        return LicenseInfo(
            valid=False,
            tier="free",
            error="Cannot reach license server. Check your network.",
        )
    except Exception as e:
        return LicenseInfo(
            valid=False,
            tier="free",
            error=f"License validation error: {e}",
        )


def _read_cache(license_key: str, grace_ttl: Optional[int] = None) -> Optional[LicenseInfo]:
    """Read cached license validation result."""
    try:
        if not CACHE_FILE.exists():
            return None

        data = json.loads(CACHE_FILE.read_text())
        cached_key = data.get("key_hash")

        # Compare hash, not raw key (don't store keys on disk)
        if cached_key != _hash_key(license_key):
            return None

        cached_at = data.get("cached_at", 0)
        ttl = grace_ttl or CACHE_TTL_SECONDS

        if time.time() - cached_at > ttl:
            return None

        return LicenseInfo(
            valid=data.get("valid", False),
            tier=data.get("tier", "free"),
            customer_name=data.get("customer_name"),
            expires_at=data.get("expires_at"),
        )
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(license_key: str, info: LicenseInfo) -> None:
    """Write license validation result to local cache."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "key_hash": _hash_key(license_key),
            "valid": info.valid,
            "tier": info.tier,
            "customer_name": info.customer_name,
            "expires_at": info.expires_at,
            "cached_at": time.time(),
        }
        CACHE_FILE.write_text(json.dumps(data))
    except OSError:
        pass  # Cache write failure is non-fatal


def _hash_key(key: str) -> str:
    """Hash a license key for safe local storage."""
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()[:16]
