"""Temporal Knowledge Graph - Tracks how preferences evolve over time

Implements bi-temporal tracking:
1. Event time: When the preference change actually occurred
2. Record time: When we recorded the change in the system

Inspired by Zep/Graphiti's temporal knowledge graphs.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class TemporalKnowledgeGraph:
    """Tracks preference evolution over time"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def record_preference_change(
        self,
        preference_id: int,
        change_type: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: str = "",
        event_time: Optional[datetime] = None
    ) -> int:
        """
        Record a preference change in the temporal graph

        Args:
            preference_id: ID of the preference that changed
            change_type: "created", "updated", "deprecated", "invalidated"
            old_value: Previous value (for updates)
            new_value: New value (for updates)
            reason: Why this change occurred
            event_time: When the change actually happened (defaults to now)

        Returns:
            Evolution record ID
        """
        if event_time is None:
            event_time = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO knowledge_evolution (
                    preference_id,
                    change_type,
                    old_value,
                    new_value,
                    reason,
                    event_time,
                    record_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                preference_id,
                change_type,
                old_value,
                new_value,
                reason,
                event_time.isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            return cursor.lastrowid

    def get_preference_history(
        self,
        preference_id: int
    ) -> List[Dict[str, Any]]:
        """Get full evolution history for a preference"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT * FROM knowledge_evolution
                WHERE preference_id = ?
                ORDER BY event_time ASC
            """, (preference_id,))

            return [dict(row) for row in cursor.fetchall()]

    def find_conflicting_preferences(
        self,
        category: str,
        time_window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Find preferences that conflict or have changed frequently

        Returns preferences in the same category that have been
        updated/changed multiple times recently, indicating instability
        """
        # TODO: Implement conflict detection logic
        # - Find preferences with multiple updates in time window
        # - Detect contradictory preferences in same category
        # - Flag preferences that keep getting invalidated
        pass

    def invalidate_preference(
        self,
        preference_id: int,
        reason: str
    ) -> bool:
        """
        Mark a preference as no longer valid

        This doesn't delete it, but marks it as deprecated
        for historical tracking
        """
        with sqlite3.connect(self.db_path) as conn:
            # Record the invalidation
            self.record_preference_change(
                preference_id=preference_id,
                change_type="invalidated",
                reason=reason
            )

            # Update the preference confidence to 0
            conn.execute("""
                UPDATE tool_preferences
                SET confidence = 0,
                    last_validated = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), preference_id))

            conn.commit()
            return True
