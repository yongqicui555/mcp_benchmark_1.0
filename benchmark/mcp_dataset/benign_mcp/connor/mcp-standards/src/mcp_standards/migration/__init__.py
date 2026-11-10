"""Migration utilities for MCP Standards

This module provides tools for migrating between different versions
of the MCP Standards learning system.
"""

from .v1_to_v2_migration import V1ToV2Migrator, migrate_v1_to_v2, MigrationStats

__all__ = [
    'V1ToV2Migrator',
    'migrate_v1_to_v2',
    'MigrationStats',
]

__version__ = "1.0.0"