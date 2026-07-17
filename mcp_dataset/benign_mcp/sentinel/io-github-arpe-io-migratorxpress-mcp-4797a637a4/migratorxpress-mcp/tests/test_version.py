"""Tests for version detection and capabilities registry."""

import subprocess
from unittest.mock import patch, Mock

import pytest

from src.version import (
    MigratorXpressVersion,
    VersionDetector,
    VERSION_REGISTRY,
    check_version_compatibility,
)


class TestMigratorXpressVersion:
    """Tests for MigratorXpressVersion dataclass."""

    def test_parse_full_version_string(self):
        """Test parsing a full 'migratorxpress X.Y.Z' string."""
        v = MigratorXpressVersion.parse("migratorxpress 0.6.24")
        assert v.major == 0
        assert v.minor == 6
        assert v.patch == 24

    def test_parse_numeric_only(self):
        """Test parsing a bare version number."""
        v = MigratorXpressVersion.parse("0.6.24")
        assert v == MigratorXpressVersion(0, 6, 24)

    def test_parse_with_whitespace(self):
        """Test parsing a version string with leading/trailing whitespace."""
        v = MigratorXpressVersion.parse("  migratorxpress 1.2.3  ")
        assert v == MigratorXpressVersion(1, 2, 3)

    def test_parse_case_insensitive(self):
        """Test parsing is case-insensitive for the prefix."""
        v = MigratorXpressVersion.parse("MigratorXpress 0.6.24")
        assert v == MigratorXpressVersion(0, 6, 24)

    def test_parse_invalid_string(self):
        """Test that an unparseable string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse version"):
            MigratorXpressVersion.parse("no version here")

    def test_parse_incomplete_version(self):
        """Test that an incomplete version string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse version"):
            MigratorXpressVersion.parse("0.6")

    def test_str_representation(self):
        """Test string representation."""
        v = MigratorXpressVersion(0, 6, 24)
        assert str(v) == "0.6.24"

    def test_equality(self):
        """Test equality comparison."""
        a = MigratorXpressVersion(0, 6, 24)
        b = MigratorXpressVersion(0, 6, 24)
        assert a == b

    def test_inequality(self):
        """Test inequality comparison."""
        a = MigratorXpressVersion(0, 6, 24)
        b = MigratorXpressVersion(0, 7, 0)
        assert a != b

    def test_less_than(self):
        """Test less-than comparison."""
        a = MigratorXpressVersion(0, 6, 23)
        b = MigratorXpressVersion(0, 6, 24)
        assert a < b

    def test_greater_than(self):
        """Test greater-than comparison (via total_ordering)."""
        a = MigratorXpressVersion(0, 6, 24)
        b = MigratorXpressVersion(0, 6, 23)
        assert a > b

    def test_comparison_across_fields(self):
        """Test comparison across major/minor/patch."""
        versions = [
            MigratorXpressVersion(0, 1, 0),
            MigratorXpressVersion(0, 6, 0),
            MigratorXpressVersion(0, 6, 24),
            MigratorXpressVersion(0, 7, 0),
            MigratorXpressVersion(1, 0, 0),
        ]
        for i in range(len(versions) - 1):
            assert versions[i] < versions[i + 1]


class TestVersionDetector:
    """Tests for VersionDetector class."""

    @patch("src.version.subprocess.run")
    def test_detect_success(self, mock_run):
        """Test successful version detection."""
        mock_result = Mock()
        mock_result.stdout = "migratorxpress 0.6.24\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        detector = VersionDetector("/fake/binary")
        version = detector.detect()

        assert version == MigratorXpressVersion(0, 6, 24)
        mock_run.assert_called_once_with(
            ["/fake/binary", "--version", "--no_banner"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    @patch("src.version.subprocess.run")
    def test_detect_failure_no_match(self, mock_run):
        """Test detection when output doesn't match version pattern."""
        mock_result = Mock()
        mock_result.stdout = "Unknown output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        detector = VersionDetector("/fake/binary")
        version = detector.detect()

        assert version is None

    @patch("src.version.subprocess.run")
    def test_detect_timeout(self, mock_run):
        """Test detection handles timeout gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=10)

        detector = VersionDetector("/fake/binary")
        version = detector.detect()

        assert version is None

    @patch("src.version.subprocess.run")
    def test_detect_binary_not_found(self, mock_run):
        """Test detection handles missing binary gracefully."""
        mock_run.side_effect = FileNotFoundError("No such file")

        detector = VersionDetector("/fake/binary")
        version = detector.detect()

        assert version is None

    @patch("src.version.subprocess.run")
    def test_detect_caching(self, mock_run):
        """Test that second call returns cached result without re-running subprocess."""
        mock_result = Mock()
        mock_result.stdout = "migratorxpress 0.6.24\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        detector = VersionDetector("/fake/binary")
        v1 = detector.detect()
        v2 = detector.detect()

        assert v1 == v2
        assert mock_run.call_count == 1

    @patch("src.version.subprocess.run")
    def test_capabilities_known_version(self, mock_run):
        """Test capabilities resolution for a known version."""
        mock_result = Mock()
        mock_result.stdout = "migratorxpress 0.6.24\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        detector = VersionDetector("/fake/binary")
        detector.detect()
        caps = detector.capabilities

        assert "oracle" in caps.source_databases
        assert "postgresql" in caps.target_databases
        assert "sqlserver" in caps.migration_db_types
        assert "translate" in caps.tasks
        assert "trusted" in caps.fk_modes
        assert caps.supports_no_banner is True
        assert caps.supports_version_flag is True
        assert caps.supports_fasttransfer is True
        assert caps.supports_license is True

    @patch("src.version.subprocess.run")
    def test_capabilities_newer_unknown_version(self, mock_run):
        """Test capabilities falls back to latest known for newer unknown version."""
        mock_result = Mock()
        mock_result.stdout = "migratorxpress 1.0.0\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        detector = VersionDetector("/fake/binary")
        detector.detect()
        caps = detector.capabilities

        # Should get the latest known capabilities (0.6.26)
        assert caps == VERSION_REGISTRY["0.6.26"]

    @patch("src.version.subprocess.run")
    def test_capabilities_undetected_version(self, mock_run):
        """Test capabilities falls back to latest known when detection fails."""
        mock_run.side_effect = FileNotFoundError("No such file")

        detector = VersionDetector("/fake/binary")
        detector.detect()
        caps = detector.capabilities

        # Should fall back to latest known
        assert caps == VERSION_REGISTRY["0.6.26"]

    def test_registry_0624_source_completeness(self):
        """Test that 0.6.24 registry has all 4 expected source databases."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {"oracle", "postgresql", "sqlserver", "netezza"}
        assert caps.source_databases == expected
        assert len(caps.source_databases) == 4

    def test_registry_0624_target_completeness(self):
        """Test that 0.6.24 registry has all 2 expected target databases."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {"postgresql", "sqlserver"}
        assert caps.target_databases == expected
        assert len(caps.target_databases) == 2

    def test_registry_0624_migration_db_completeness(self):
        """Test that 0.6.24 registry has 1 migration database type."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {"sqlserver"}
        assert caps.migration_db_types == expected
        assert len(caps.migration_db_types) == 1

    def test_registry_0624_task_completeness(self):
        """Test that 0.6.24 registry has all 8 tasks."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {
            "translate",
            "create",
            "transfer",
            "diff",
            "copy_pk",
            "copy_ak",
            "copy_fk",
            "all",
        }
        assert caps.tasks == expected
        assert len(caps.tasks) == 8

    def test_registry_0624_fk_modes_completeness(self):
        """Test that 0.6.24 registry has all 3 FK modes."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {"trusted", "untrusted", "disabled"}
        assert caps.fk_modes == expected
        assert len(caps.fk_modes) == 3

    def test_registry_0624_migration_db_modes_completeness(self):
        """Test that 0.6.24 registry has all 3 migration DB modes."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {"preserve", "truncate", "drop"}
        assert caps.migration_db_modes == expected
        assert len(caps.migration_db_modes) == 3

    def test_registry_0624_load_modes_completeness(self):
        """Test that 0.6.24 registry has all 2 load modes."""
        caps = VERSION_REGISTRY["0.6.24"]
        expected = {"truncate", "append"}
        assert caps.load_modes == expected
        assert len(caps.load_modes) == 2


class TestCheckVersionCompatibility:
    """Tests for check_version_compatibility function."""

    def test_basic_params_no_warnings(self):
        """Basic params produce no warnings."""
        caps = VERSION_REGISTRY["0.6.24"]
        version = MigratorXpressVersion(0, 6, 24)
        warnings = check_version_compatibility(
            {"source_db_name": "mydb"}, caps, version
        )
        assert warnings == []

    def test_empty_params_no_warnings(self):
        """Empty params produce no warnings."""
        caps = VERSION_REGISTRY["0.6.24"]
        version = MigratorXpressVersion(0, 6, 24)
        warnings = check_version_compatibility({}, caps, version)
        assert warnings == []

    def test_none_version_no_warnings(self):
        """None detected version with basic params produces no warnings."""
        caps = VERSION_REGISTRY["0.6.24"]
        warnings = check_version_compatibility(
            {"source_db_name": "mydb"}, caps, None
        )
        assert warnings == []
