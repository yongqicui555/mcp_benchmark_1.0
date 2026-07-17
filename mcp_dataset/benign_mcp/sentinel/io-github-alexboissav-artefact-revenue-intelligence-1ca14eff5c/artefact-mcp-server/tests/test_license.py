"""Tests for license validation module."""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from artefact_mcp.core.license import (
    validate_license,
    require_license,
    LicenseInfo,
    _hash_key,
    _read_cache,
    _write_cache,
)


class TestLicenseInfo:
    def test_free_tier_no_key(self):
        """No license key = free tier, still valid."""
        with patch.dict("os.environ", {}, clear=True):
            result = validate_license(None)
            assert result.valid is True
            assert result.tier == "free"

    def test_free_tier_from_env_missing(self):
        """Missing env var = free tier."""
        with patch.dict("os.environ", {}, clear=True):
            result = validate_license()
            assert result.valid is True
            assert result.tier == "free"

    def test_dev_bypass(self):
        """Dev bypass key (hash-verified) returns pro."""
        result = validate_license("artefact-internal-qa-2026")
        assert result.valid is True
        assert result.tier == "pro"
        assert result.customer_name == "Dev Testing"

    def test_dev_bypass_from_env(self):
        """Dev bypass key works via env var."""
        with patch.dict("os.environ", {"ARTEFACT_LICENSE_KEY": "artefact-internal-qa-2026"}):
            result = validate_license()
            assert result.valid is True
            assert result.tier == "pro"

    def test_dev_bypass_wrong_key(self):
        """Old plaintext bypass no longer works."""
        # This would hit LemonSqueezy (mocked to fail), proving hash-only check
        with patch("artefact_mcp.core.license._validate_remote") as mock_remote:
            mock_remote.return_value = LicenseInfo(valid=False, tier="free", error="Invalid")
            with patch("artefact_mcp.core.license._read_cache", return_value=None):
                result = validate_license("dev-testing")
                assert result.tier == "free"
                mock_remote.assert_called_once()


class TestRequireLicense:
    def test_sample_always_allowed(self):
        """Sample data works on any tier."""
        free = LicenseInfo(valid=True, tier="free")
        pro = LicenseInfo(valid=True, tier="pro")
        enterprise = LicenseInfo(valid=True, tier="enterprise")

        # Should not raise
        require_license("sample", free)
        require_license("sample", pro)
        require_license("sample", enterprise)

    def test_hubspot_blocked_on_free(self):
        """HubSpot source requires paid license."""
        free = LicenseInfo(valid=True, tier="free")
        with pytest.raises(ValueError, match="Pro license"):
            require_license("hubspot", free)

    def test_hubspot_allowed_on_pro(self):
        """Pro tier can access HubSpot."""
        pro = LicenseInfo(valid=True, tier="pro")
        require_license("hubspot", pro)  # Should not raise

    def test_hubspot_allowed_on_enterprise(self):
        """Enterprise tier can access HubSpot."""
        enterprise = LicenseInfo(valid=True, tier="enterprise")
        require_license("hubspot", enterprise)  # Should not raise


class TestHashKey:
    def test_consistent(self):
        """Same key produces same hash."""
        h1 = _hash_key("test-key-123")
        h2 = _hash_key("test-key-123")
        assert h1 == h2

    def test_different_keys(self):
        """Different keys produce different hashes."""
        h1 = _hash_key("key-1")
        h2 = _hash_key("key-2")
        assert h1 != h2

    def test_truncated(self):
        """Hash is truncated to 16 chars."""
        h = _hash_key("any-key")
        assert len(h) == 16


class TestCache:
    def test_write_and_read(self, tmp_path):
        """Write then read a cached license."""
        cache_file = tmp_path / "license_cache.json"
        info = LicenseInfo(valid=True, tier="pro", customer_name="Test Corp")

        with patch("artefact_mcp.core.license.CACHE_FILE", cache_file):
            _write_cache("test-key", info)
            result = _read_cache("test-key")

        assert result is not None
        assert result.valid is True
        assert result.tier == "pro"
        assert result.customer_name == "Test Corp"

    def test_cache_miss_wrong_key(self, tmp_path):
        """Wrong key returns None."""
        cache_file = tmp_path / "license_cache.json"
        info = LicenseInfo(valid=True, tier="pro")

        with patch("artefact_mcp.core.license.CACHE_FILE", cache_file):
            _write_cache("key-1", info)
            result = _read_cache("key-2")

        assert result is None

    def test_cache_expired(self, tmp_path):
        """Expired cache returns None."""
        cache_file = tmp_path / "license_cache.json"
        info = LicenseInfo(valid=True, tier="pro")

        with patch("artefact_mcp.core.license.CACHE_FILE", cache_file):
            _write_cache("test-key", info)

            # Manually expire the cache
            data = json.loads(cache_file.read_text())
            data["cached_at"] = time.time() - 100000
            cache_file.write_text(json.dumps(data))

            result = _read_cache("test-key")

        assert result is None

    def test_cache_no_file(self, tmp_path):
        """Missing cache file returns None."""
        cache_file = tmp_path / "nonexistent" / "cache.json"
        with patch("artefact_mcp.core.license.CACHE_FILE", cache_file):
            result = _read_cache("any-key")
        assert result is None
