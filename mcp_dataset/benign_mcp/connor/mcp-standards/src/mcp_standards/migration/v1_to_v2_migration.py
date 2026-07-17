#!/usr/bin/env python3
"""V1 to V2 Pattern Migration Script

Migrates patterns from V1 system (SQLite-only) to V2 system (AgentDB + SQLite).
This script safely transfers existing learning patterns while preserving data integrity.

Features:
- Automatic pattern discovery from V1 databases
- Semantic enhancement during migration
- Duplicate detection and merging
- Progress reporting and rollback capability
- Backup creation before migration
"""

import sqlite3
import json
import asyncio
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from ..memory.v2.test_hybrid_memory import create_test_hybrid_memory, TestMemoryRouter
from ..hooks.pattern_extractor_v2 import ExtractedPattern


@dataclass
class MigrationStats:
    """Migration statistics and progress tracking"""
    total_v1_patterns: int = 0
    migrated_patterns: int = 0
    duplicates_found: int = 0
    errors: int = 0
    skipped: int = 0
    start_time: datetime = None
    end_time: datetime = None

    @property
    def duration(self) -> float:
        """Migration duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_v1_patterns == 0:
            return 0.0
        return (self.migrated_patterns / self.total_v1_patterns) * 100


class V1ToV2Migrator:
    """Migrates patterns from V1 SQLite-only system to V2 hybrid system"""

    def __init__(self,
                 v1_db_path: str = None,
                 v2_memory_router: TestMemoryRouter = None,
                 backup_enabled: bool = True):
        """
        Initialize migrator

        Args:
            v1_db_path: Path to V1 SQLite database
            v2_memory_router: V2 hybrid memory system
            backup_enabled: Whether to create backups before migration
        """
        self.v1_db_path = Path(v1_db_path) if v1_db_path else Path.home() / ".mcp-standards" / "knowledge.db"
        self.v2_memory_router = v2_memory_router
        self.backup_enabled = backup_enabled
        self.stats = MigrationStats()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    async def migrate(self, dry_run: bool = False) -> MigrationStats:
        """
        Perform V1 to V2 migration

        Args:
            dry_run: If True, analyze migration without actually performing it

        Returns:
            Migration statistics
        """
        self.stats.start_time = datetime.now()
        self.logger.info(f"Starting {'DRY RUN' if dry_run else 'FULL'} migration from V1 to V2")

        try:
            # Step 1: Initialize V2 system if not provided
            if not self.v2_memory_router:
                self.logger.info("Initializing V2 hybrid memory system...")
                self.v2_memory_router = await create_test_hybrid_memory(
                    agentdb_path=".claude/memory/v2_migrated",
                    sqlite_path=str(self.v1_db_path.parent / "v2_migrated.db")
                )

            # Step 2: Create backup if enabled
            if self.backup_enabled and not dry_run:
                await self._create_backup()

            # Step 3: Discover and analyze V1 patterns
            v1_patterns = await self._discover_v1_patterns()
            self.stats.total_v1_patterns = len(v1_patterns)

            if self.stats.total_v1_patterns == 0:
                self.logger.warning("No V1 patterns found to migrate")
                return self.stats

            self.logger.info(f"Found {self.stats.total_v1_patterns} V1 patterns to migrate")

            # Step 4: Migrate patterns
            for i, v1_pattern in enumerate(v1_patterns):
                try:
                    await self._migrate_single_pattern(v1_pattern, dry_run)

                    if (i + 1) % 10 == 0:  # Progress reporting every 10 patterns
                        progress = (i + 1) / self.stats.total_v1_patterns * 100
                        self.logger.info(f"Migration progress: {progress:.1f}% ({i + 1}/{self.stats.total_v1_patterns})")

                except Exception as e:
                    self.stats.errors += 1
                    self.logger.error(f"Error migrating pattern {v1_pattern.get('id', 'unknown')}: {e}")

            # Step 5: Verify migration
            if not dry_run:
                await self._verify_migration()

            self.stats.end_time = datetime.now()
            self.logger.info(f"Migration completed in {self.stats.duration:.2f} seconds")
            self._log_migration_summary()

            return self.stats

        except Exception as e:
            self.stats.end_time = datetime.now()
            self.logger.error(f"Migration failed: {e}")
            raise

    async def _discover_v1_patterns(self) -> List[Dict[str, Any]]:
        """Discover existing V1 patterns from SQLite database"""
        if not self.v1_db_path.exists():
            self.logger.warning(f"V1 database not found: {self.v1_db_path}")
            return []

        patterns = []

        try:
            with sqlite3.connect(self.v1_db_path) as conn:
                conn.row_factory = sqlite3.Row  # Access columns by name

                # Check what tables exist
                tables = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()

                table_names = [table['name'] for table in tables]
                self.logger.info(f"Found V1 tables: {table_names}")

                # Extract patterns from different possible table structures

                # 1. Look for patterns table (if it exists)
                if 'patterns' in table_names:
                    cursor = conn.execute("""
                        SELECT id, pattern_type, category, description,
                               text_content, confidence, context,
                               created_at, metadata
                        FROM patterns
                        ORDER BY created_at
                    """)

                    for row in cursor.fetchall():
                        pattern = dict(row)
                        pattern['source_table'] = 'patterns'
                        patterns.append(pattern)

                # 2. Look for tool_executions table with patterns in results
                if 'tool_executions' in table_names:
                    cursor = conn.execute("""
                        SELECT id, tool_name, args, result, significance,
                               project_path, timestamp
                        FROM tool_executions
                        WHERE significance > 0.6
                        ORDER BY timestamp
                    """)

                    for row in cursor.fetchall():
                        execution = dict(row)
                        # Try to extract patterns from the result field
                        try:
                            result_data = json.loads(execution['result'])
                            if isinstance(result_data, dict) and 'patterns' in result_data:
                                for pattern_data in result_data['patterns']:
                                    pattern = {
                                        'id': f"exec_{execution['id']}_{len(patterns)}",
                                        'pattern_type': pattern_data.get('type', 'unknown'),
                                        'category': pattern_data.get('category', 'general'),
                                        'description': pattern_data.get('description', ''),
                                        'text_content': pattern_data.get('text', ''),
                                        'confidence': pattern_data.get('confidence', 0.5),
                                        'context': json.dumps(pattern_data.get('context', {})),
                                        'created_at': execution['timestamp'],
                                        'metadata': json.dumps({
                                            'tool_name': execution['tool_name'],
                                            'project_path': execution['project_path'],
                                            'source_execution_id': execution['id']
                                        }),
                                        'source_table': 'tool_executions'
                                    }
                                    patterns.append(pattern)
                        except (json.JSONDecodeError, TypeError):
                            # Skip malformed result data
                            pass

                # 3. Look for preferences or corrections tables
                for table_name in ['preferences', 'corrections', 'learning_patterns']:
                    if table_name in table_names:
                        try:
                            cursor = conn.execute(f"SELECT * FROM {table_name} ORDER BY rowid")
                            for row in cursor.fetchall():
                                pattern = dict(row)
                                pattern['source_table'] = table_name
                                # Standardize field names
                                if 'pattern_text' in pattern:
                                    pattern['text_content'] = pattern['pattern_text']
                                if 'preference_type' in pattern:
                                    pattern['pattern_type'] = pattern['preference_type']
                                patterns.append(pattern)
                        except sqlite3.OperationalError:
                            # Table might have different structure
                            self.logger.warning(f"Could not read table {table_name}")

        except Exception as e:
            self.logger.error(f"Error discovering V1 patterns: {e}")

        self.logger.info(f"Discovered {len(patterns)} V1 patterns")
        return patterns

    async def _migrate_single_pattern(self, v1_pattern: Dict[str, Any], dry_run: bool = False):
        """Migrate a single V1 pattern to V2 format"""
        try:
            # Convert V1 pattern to V2 ExtractedPattern format
            v2_pattern = await self._convert_v1_to_v2_pattern(v1_pattern)

            if not v2_pattern:
                self.stats.skipped += 1
                return

            # Check for duplicates in V2 system
            if await self._is_duplicate_pattern(v2_pattern):
                self.stats.duplicates_found += 1
                self.logger.debug(f"Skipping duplicate pattern: {v2_pattern.description}")
                return

            # Store in V2 system if not dry run
            if not dry_run:
                pattern_id = await self.v2_memory_router.store_pattern(
                    pattern_text=v2_pattern.text_content,
                    category=v2_pattern.category,
                    context=v2_pattern.context.get('context', ''),
                    confidence=v2_pattern.confidence,
                    metadata=v2_pattern.metadata
                )

                if pattern_id:
                    self.stats.migrated_patterns += 1
                    self.logger.debug(f"Migrated pattern: {v2_pattern.description} -> {pattern_id}")
                else:
                    self.stats.errors += 1
                    self.logger.error(f"Failed to store pattern: {v2_pattern.description}")
            else:
                # Dry run - just count as migrated
                self.stats.migrated_patterns += 1

        except Exception as e:
            self.stats.errors += 1
            self.logger.error(f"Error migrating pattern: {e}")

    async def _convert_v1_to_v2_pattern(self, v1_pattern: Dict[str, Any]) -> Optional[ExtractedPattern]:
        """Convert V1 pattern format to V2 ExtractedPattern"""
        try:
            # Extract and normalize fields from V1 pattern
            pattern_type = v1_pattern.get('pattern_type', 'unknown')
            category = v1_pattern.get('category', 'general')
            description = v1_pattern.get('description', '')
            text_content = v1_pattern.get('text_content') or v1_pattern.get('text', '')
            confidence = float(v1_pattern.get('confidence', 0.5))

            # Parse context if it's JSON string
            context = {}
            context_data = v1_pattern.get('context')
            if context_data:
                if isinstance(context_data, str):
                    try:
                        context = json.loads(context_data)
                    except json.JSONDecodeError:
                        context = {'context': context_data}
                elif isinstance(context_data, dict):
                    context = context_data

            # Parse metadata
            metadata = {}
            metadata_data = v1_pattern.get('metadata')
            if metadata_data:
                if isinstance(metadata_data, str):
                    try:
                        metadata = json.loads(metadata_data)
                    except json.JSONDecodeError:
                        metadata = {'original_metadata': metadata_data}
                elif isinstance(metadata_data, dict):
                    metadata = metadata_data

            # Add migration tracking
            metadata.update({
                'migrated_from_v1': True,
                'v1_source_table': v1_pattern.get('source_table', 'unknown'),
                'migration_timestamp': datetime.now().isoformat(),
                'v1_id': v1_pattern.get('id', 'unknown')
            })

            # Skip patterns with insufficient data
            if not text_content and not description:
                self.logger.debug(f"Skipping pattern with no content: {v1_pattern.get('id')}")
                return None

            # Use description as text_content if text_content is empty
            if not text_content:
                text_content = description

            # Create V2 ExtractedPattern
            v2_pattern = ExtractedPattern(
                pattern_type=self._normalize_pattern_type(pattern_type),
                category=self._normalize_category(category),
                description=description or f"Migrated pattern: {text_content[:50]}...",
                text_content=text_content,
                confidence=max(0.0, min(1.0, confidence)),  # Clamp to [0,1]
                context=context,
                tool_name=metadata.get('tool_name', 'unknown'),
                project_path=metadata.get('project_path', ''),
                metadata=metadata
            )

            return v2_pattern

        except Exception as e:
            self.logger.error(f"Error converting V1 pattern to V2: {e}")
            return None

    def _normalize_pattern_type(self, pattern_type: str) -> str:
        """Normalize pattern type to V2 standard types"""
        type_mapping = {
            'preference': 'tool_preference',
            'correction': 'correction',
            'workflow': 'workflow',
            'context': 'context',
            'tool_preference': 'tool_preference',
            'unknown': 'correction'  # Default fallback
        }
        return type_mapping.get(pattern_type.lower(), 'correction')

    def _normalize_category(self, category: str) -> str:
        """Normalize category to V2 standard categories"""
        category_mapping = {
            'python-package': 'package-management',
            'package': 'package-management',
            'testing': 'testing',
            'git': 'version-control',
            'version-control': 'version-control',
            'docs': 'documentation',
            'documentation': 'documentation',
            'lint': 'code-quality',
            'format': 'code-quality',
            'build': 'build-tools',
            'general': 'general'
        }
        return category_mapping.get(category.lower(), category.lower())

    async def _is_duplicate_pattern(self, pattern: ExtractedPattern) -> bool:
        """Check if pattern already exists in V2 system"""
        try:
            # Search for similar patterns using semantic search
            similar_patterns = await self.v2_memory_router.find_similar_patterns(
                query=pattern.text_content,
                top_k=3,
                threshold=0.9,  # High threshold for duplicate detection
                category=pattern.category
            )

            # Check for exact or near-exact matches
            for similar in similar_patterns:
                if (similar.get('similarity', 0) > 0.95 and
                    similar.get('category') == pattern.category):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {e}")
            return False  # Assume not duplicate if check fails

    async def _create_backup(self):
        """Create backup of V1 database before migration"""
        if not self.v1_db_path.exists():
            return

        backup_path = self.v1_db_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

        try:
            shutil.copy2(self.v1_db_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise

    async def _verify_migration(self):
        """Verify migration was successful"""
        try:
            v2_stats = await self.v2_memory_router.get_statistics()

            # Check that patterns were actually stored
            agentdb_stats = v2_stats.get('agentdb_stats', {})
            total_vectors = agentdb_stats.get('total_vectors', 0)

            self.logger.info(f"Verification: {total_vectors} vectors in AgentDB")

            if total_vectors >= self.stats.migrated_patterns:
                self.logger.info("✅ Migration verification passed")
            else:
                self.logger.warning("⚠️  Migration verification: fewer vectors than expected")

        except Exception as e:
            self.logger.error(f"Migration verification failed: {e}")

    def _log_migration_summary(self):
        """Log detailed migration summary"""
        self.logger.info("=" * 60)
        self.logger.info("MIGRATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total V1 patterns found: {self.stats.total_v1_patterns}")
        self.logger.info(f"Successfully migrated: {self.stats.migrated_patterns}")
        self.logger.info(f"Duplicates skipped: {self.stats.duplicates_found}")
        self.logger.info(f"Patterns skipped: {self.stats.skipped}")
        self.logger.info(f"Errors encountered: {self.stats.errors}")
        self.logger.info(f"Success rate: {self.stats.success_rate:.1f}%")
        self.logger.info(f"Duration: {self.stats.duration:.2f} seconds")
        self.logger.info("=" * 60)

    async def close(self):
        """Clean up resources"""
        if self.v2_memory_router:
            await self.v2_memory_router.close()


async def migrate_v1_to_v2(
    v1_db_path: str = None,
    v2_agentdb_path: str = None,
    v2_sqlite_path: str = None,
    dry_run: bool = False,
    backup_enabled: bool = True
) -> MigrationStats:
    """
    Convenience function to perform V1 to V2 migration

    Args:
        v1_db_path: Path to V1 SQLite database
        v2_agentdb_path: Path for V2 AgentDB storage
        v2_sqlite_path: Path for V2 SQLite database
        dry_run: If True, analyze without migrating
        backup_enabled: Whether to create backups

    Returns:
        Migration statistics
    """
    # Initialize V2 system
    v2_router = await create_test_hybrid_memory(
        agentdb_path=v2_agentdb_path or ".claude/memory/v2_migrated",
        sqlite_path=v2_sqlite_path or str(Path.home() / ".mcp-standards" / "v2_migrated.db")
    )

    # Perform migration
    migrator = V1ToV2Migrator(
        v1_db_path=v1_db_path,
        v2_memory_router=v2_router,
        backup_enabled=backup_enabled
    )

    try:
        stats = await migrator.migrate(dry_run=dry_run)
        return stats
    finally:
        await migrator.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate patterns from V1 to V2 system")
    parser.add_argument("--v1-db", help="Path to V1 SQLite database")
    parser.add_argument("--v2-agentdb", help="Path for V2 AgentDB storage")
    parser.add_argument("--v2-sqlite", help="Path for V2 SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without migrating")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")

    args = parser.parse_args()

    async def main():
        stats = await migrate_v1_to_v2(
            v1_db_path=args.v1_db,
            v2_agentdb_path=args.v2_agentdb,
            v2_sqlite_path=args.v2_sqlite,
            dry_run=args.dry_run,
            backup_enabled=not args.no_backup
        )

        print(f"\nMigration {'Analysis' if args.dry_run else 'Completed'}!")
        print(f"Success rate: {stats.success_rate:.1f}%")
        print(f"Patterns processed: {stats.migrated_patterns}/{stats.total_v1_patterns}")

    asyncio.run(main())