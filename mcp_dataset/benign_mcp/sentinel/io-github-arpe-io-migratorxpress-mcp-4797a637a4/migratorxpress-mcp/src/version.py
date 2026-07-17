"""
Version detection and capabilities registry for MigratorXpress.

This module detects the installed MigratorXpress binary version and maps it
to known capabilities (supported source databases, target databases, migration
database types, tasks, modes, and feature flags).
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from functools import total_ordering
from typing import Dict, FrozenSet, Optional


logger = logging.getLogger(__name__)


@total_ordering
@dataclass(frozen=True)
class MigratorXpressVersion:
    """Represents a MigratorXpress version number (X.Y.Z)."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_string: str) -> "MigratorXpressVersion":
        """Parse a version string like 'migratorxpress 0.6.24' or '0.6.24'.

        Args:
            version_string: Version string to parse

        Returns:
            MigratorXpressVersion instance

        Raises:
            ValueError: If the string cannot be parsed
        """
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_string.strip())
        if not match:
            raise ValueError(f"Cannot parse version from: {version_string!r}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
        )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MigratorXpressVersion):
            return NotImplemented
        return self._tuple == other._tuple

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MigratorXpressVersion):
            return NotImplemented
        return self._tuple < other._tuple

    @property
    def _tuple(self) -> tuple:
        return (self.major, self.minor, self.patch)


@dataclass(frozen=True)
class VersionCapabilities:
    """Capabilities available in a specific MigratorXpress version."""

    source_databases: FrozenSet[str]
    target_databases: FrozenSet[str]
    migration_db_types: FrozenSet[str]
    tasks: FrozenSet[str]
    fk_modes: FrozenSet[str]
    migration_db_modes: FrozenSet[str]
    load_modes: FrozenSet[str]
    supports_no_banner: bool = False
    supports_version_flag: bool = False
    supports_fasttransfer: bool = False
    supports_license: bool = False
    supports_no_progress: bool = False
    supports_quiet_ft: bool = False
    supports_log_dir: bool = False


# Static version registry: version string -> capabilities
VERSION_REGISTRY: Dict[str, VersionCapabilities] = {
    "0.6.24": VersionCapabilities(
        source_databases=frozenset(
            [
                "oracle",
                "postgresql",
                "sqlserver",
                "netezza",
            ]
        ),
        target_databases=frozenset(
            [
                "postgresql",
                "sqlserver",
            ]
        ),
        migration_db_types=frozenset(
            [
                "sqlserver",
            ]
        ),
        tasks=frozenset(
            [
                "translate",
                "create",
                "transfer",
                "diff",
                "copy_pk",
                "copy_ak",
                "copy_fk",
                "all",
            ]
        ),
        fk_modes=frozenset(
            [
                "trusted",
                "untrusted",
                "disabled",
            ]
        ),
        migration_db_modes=frozenset(
            [
                "preserve",
                "truncate",
                "drop",
            ]
        ),
        load_modes=frozenset(
            [
                "truncate",
                "append",
            ]
        ),
        supports_no_banner=True,
        supports_version_flag=True,
        supports_fasttransfer=True,
        supports_license=True,
    ),
    "0.6.26": VersionCapabilities(
        source_databases=frozenset(
            [
                "oracle",
                "postgresql",
                "sqlserver",
                "netezza",
            ]
        ),
        target_databases=frozenset(
            [
                "postgresql",
                "sqlserver",
                "mysql",
                "oracle",
            ]
        ),
        migration_db_types=frozenset(
            [
                "sqlserver",
            ]
        ),
        tasks=frozenset(
            [
                "translate",
                "create",
                "transfer",
                "diff",
                "copy_pk",
                "copy_ak",
                "copy_fk",
                "all",
            ]
        ),
        fk_modes=frozenset(
            [
                "trusted",
                "untrusted",
                "disabled",
            ]
        ),
        migration_db_modes=frozenset(
            [
                "preserve",
                "truncate",
                "drop",
            ]
        ),
        load_modes=frozenset(
            [
                "truncate",
                "append",
            ]
        ),
        supports_no_banner=True,
        supports_version_flag=True,
        supports_fasttransfer=True,
        supports_license=True,
        supports_no_progress=True,
        supports_quiet_ft=True,
        supports_log_dir=True,
    ),
}

# Pre-sorted list of known versions for lookup
_SORTED_VERSIONS = sorted(
    [(MigratorXpressVersion.parse(k), v) for k, v in VERSION_REGISTRY.items()],
    key=lambda x: x[0],
)


class VersionDetector:
    """Detects MigratorXpress binary version and resolves capabilities."""

    def __init__(self, binary_path: str):
        self._binary_path = binary_path
        self._detected_version: Optional[MigratorXpressVersion] = None
        self._detection_done = False

    def detect(self, timeout: int = 10) -> Optional[MigratorXpressVersion]:
        """Detect the MigratorXpress version by running the binary.

        Runs ``[binary_path, "--version", "--no_banner"]`` and parses the output.
        Results are cached after the first call.

        Args:
            timeout: Subprocess timeout in seconds

        Returns:
            MigratorXpressVersion if detected, None otherwise
        """
        if self._detection_done:
            return self._detected_version

        self._detection_done = True

        try:
            result = subprocess.run(
                [self._binary_path, "--version", "--no_banner"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            output = (result.stdout + result.stderr).strip()
            match = re.search(
                r"migratorxpress\s+(\d+)\.(\d+)\.(\d+)", output, re.IGNORECASE
            )
            if match:
                self._detected_version = MigratorXpressVersion(
                    major=int(match.group(1)),
                    minor=int(match.group(2)),
                    patch=int(match.group(3)),
                )
                logger.info(
                    f"Detected MigratorXpress version: {self._detected_version}"
                )
            else:
                logger.warning(f"Could not parse version from output: {output!r}")
        except subprocess.TimeoutExpired:
            logger.warning("Version detection timed out")
        except FileNotFoundError:
            logger.warning(f"Binary not found at: {self._binary_path}")
        except Exception as e:
            logger.warning(f"Version detection failed: {e}")

        return self._detected_version

    @property
    def capabilities(self) -> VersionCapabilities:
        """Resolve capabilities for the detected version.

        If the detected version matches a registry entry exactly, return that.
        If the version is newer than all known entries, return the latest known.
        If detection failed, return the latest known entry as a fallback.
        """
        if not self._detection_done:
            self.detect()

        if not _SORTED_VERSIONS:
            # No registry entries at all — return empty capabilities
            return VersionCapabilities(
                source_databases=frozenset(),
                target_databases=frozenset(),
                migration_db_types=frozenset(),
                tasks=frozenset(),
                fk_modes=frozenset(),
                migration_db_modes=frozenset(),
                load_modes=frozenset(),
            )

        if self._detected_version is None:
            # Detection failed — fall back to latest known
            return _SORTED_VERSIONS[-1][1]

        # Find the highest registry entry <= detected version
        best: Optional[VersionCapabilities] = None
        for ver, caps in _SORTED_VERSIONS:
            if ver <= self._detected_version:
                best = caps
            else:
                break

        # If detected version is older than all known, fall back to latest
        return best if best is not None else _SORTED_VERSIONS[-1][1]


def check_version_compatibility(
    params: dict,
    capabilities: VersionCapabilities,
    detected_version: Optional[MigratorXpressVersion],
) -> list[str]:
    """Check for version-gated features and return warning strings.

    Args:
        params: The parameters dict for the command
        capabilities: Resolved capabilities for the detected version
        detected_version: The detected MigratorXpress version, or None

    Returns:
        List of warning strings (empty if all OK)
    """
    warnings: list[str] = []

    # No version-gated features yet — add checks here as they appear
    # Example pattern:
    # if params.get("some_feature") and not capabilities.supports_some_feature:
    #     ver_str = str(detected_version) if detected_version else "unknown"
    #     warnings.append(f"--some_feature requires MigratorXpress X.Y.Z+, but detected version is {ver_str}")

    return warnings
