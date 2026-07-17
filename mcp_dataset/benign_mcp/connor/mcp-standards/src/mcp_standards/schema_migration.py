"""Database Schema Migration for Self-Learning Features

Extends the existing MCP Standards schema with new tables for:
- Tool execution tracking
- Pattern frequency analysis
- Tool preferences (learned rules)
- Agent performance tracking
- Validation gates
- Knowledge evolution (temporal tracking)
- Spec validation
"""

import sqlite3
from pathlib import Path
from datetime import datetime


class SchemaMigration:
    """Handles database schema migrations"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def migrate(self) -> bool:
        """
        Run all migrations

        Returns:
            True if migrations successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create migrations table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY,
                        version INTEGER NOT NULL UNIQUE,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Run migrations in order
                self._migrate_v1_tool_executions(conn)
                self._migrate_v2_pattern_frequency(conn)
                self._migrate_v3_tool_preferences(conn)
                self._migrate_v4_agent_performance(conn)
                self._migrate_v5_validation_gates(conn)
                self._migrate_v6_knowledge_evolution(conn)
                self._migrate_v7_spec_validation(conn)

                conn.commit()
                return True

        except Exception as e:
            print(f"Migration error: {e}")
            return False

    def _is_migration_applied(self, conn: sqlite3.Connection, version: int) -> bool:
        """Check if a migration version has been applied"""
        cursor = conn.execute("""
            SELECT COUNT(*) FROM schema_migrations WHERE version = ?
        """, (version,))
        return cursor.fetchone()[0] > 0

    def _record_migration(self, conn: sqlite3.Connection, version: int, description: str):
        """Record that a migration has been applied"""
        conn.execute("""
            INSERT INTO schema_migrations (version, description)
            VALUES (?, ?)
        """, (version, description))

    def _migrate_v1_tool_executions(self, conn: sqlite3.Connection):
        """Migration 1: Tool executions table"""
        if self._is_migration_applied(conn, 1):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                args TEXT NOT NULL,
                result TEXT,
                significance REAL NOT NULL,
                project_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_exec_sig ON tool_executions(significance DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_exec_time ON tool_executions(timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_exec_project ON tool_executions(project_path)")

        self._record_migration(conn, 1, "Tool executions tracking table")

    def _migrate_v2_pattern_frequency(self, conn: sqlite3.Connection):
        """Migration 2: Pattern frequency tracking"""
        if self._is_migration_applied(conn, 2):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pattern_frequency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_key TEXT NOT NULL UNIQUE,
                tool_name TEXT NOT NULL,
                pattern_type TEXT,
                pattern_description TEXT,
                occurrence_count INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                promoted_to_preference BOOLEAN DEFAULT FALSE,
                confidence REAL DEFAULT 0.0,
                examples TEXT
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_pattern_freq ON pattern_frequency(occurrence_count DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pattern_tool ON pattern_frequency(tool_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pattern_type ON pattern_frequency(pattern_type)")

        self._record_migration(conn, 2, "Pattern frequency tracking")

    def _migrate_v3_tool_preferences(self, conn: sqlite3.Connection):
        """Migration 3: Tool preferences (learned rules)"""
        if self._is_migration_applied(conn, 3):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tool_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                context TEXT NOT NULL,
                preference TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                examples TEXT,
                learned_from TEXT,
                last_validated TIMESTAMP,
                last_applied TIMESTAMP,
                apply_count INTEGER DEFAULT 0,
                project_specific BOOLEAN DEFAULT FALSE,
                project_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_pref_confidence ON tool_preferences(confidence DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pref_category ON tool_preferences(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pref_project ON tool_preferences(project_path)")

        self._record_migration(conn, 3, "Tool preferences (learned rules)")

    def _migrate_v4_agent_performance(self, conn: sqlite3.Connection):
        """Migration 4: Agent performance tracking"""
        if self._is_migration_applied(conn, 4):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                task_category TEXT,
                success BOOLEAN,
                correction_count INTEGER DEFAULT 0,
                execution_time REAL,
                context TEXT,
                project_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_perf_type ON agent_performance(agent_type, success)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_perf_time ON agent_performance(timestamp DESC)")

        self._record_migration(conn, 4, "Agent performance tracking")

    def _migrate_v5_validation_gates(self, conn: sqlite3.Connection):
        """Migration 5: Validation gates"""
        if self._is_migration_applied(conn, 5):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                gate_type TEXT NOT NULL,
                required BOOLEAN DEFAULT TRUE,
                auto_check BOOLEAN DEFAULT TRUE,
                check_command TEXT,
                failure_count INTEGER DEFAULT 0,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_gate_project_type
            ON validation_gates(project_path, gate_type)
        """)

        self._record_migration(conn, 5, "Validation gates")

    def _migrate_v6_knowledge_evolution(self, conn: sqlite3.Connection):
        """Migration 6: Knowledge evolution (temporal tracking)"""
        if self._is_migration_applied(conn, 6):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_evolution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_id INTEGER,
                change_type TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                event_time TIMESTAMP,
                record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(preference_id) REFERENCES tool_preferences(id)
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_evo_pref ON knowledge_evolution(preference_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_evo_time ON knowledge_evolution(event_time)")

        self._record_migration(conn, 6, "Knowledge evolution (temporal tracking)")

    def _migrate_v7_spec_validation(self, conn: sqlite3.Connection):
        """Migration 7: Spec validation tracking"""
        if self._is_migration_applied(conn, 7):
            return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS spec_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_description TEXT NOT NULL,
                spec_captured TEXT NOT NULL,
                deliverable_summary TEXT,
                validation_status TEXT,
                gaps_found TEXT,
                project_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_val_status ON spec_validations(validation_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_spec_val_project ON spec_validations(project_path)")

        self._record_migration(conn, 7, "Spec validation tracking")

    def get_schema_version(self) -> int:
        """Get current schema version"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT MAX(version) FROM schema_migrations
                """)
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return 0


def migrate_database(db_path: Path = None) -> bool:
    """
    Convenience function to migrate database

    Args:
        db_path: Path to database (defaults to ~/.mcp-standards/knowledge.db)

    Returns:
        True if successful, False otherwise
    """
    if db_path is None:
        db_path = Path.home() / ".mcp-standards" / "knowledge.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    migration = SchemaMigration(db_path)
    success = migration.migrate()

    if success:
        version = migration.get_schema_version()
        print(f"✓ Database migrated to version {version}")
    else:
        print("✗ Migration failed")

    return success


if __name__ == "__main__":
    # Run migration when script is executed directly
    import sys

    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = None

    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
