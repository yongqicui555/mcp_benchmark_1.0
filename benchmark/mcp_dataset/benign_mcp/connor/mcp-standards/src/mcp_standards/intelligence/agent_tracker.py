"""Agent Performance Tracker - Tracks which agents work well for which tasks

Provides:
1. Agent execution logging
2. Success/failure tracking
3. Performance analytics
4. Agent recommendations based on history
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


class AgentPerformanceTracker:
    """Tracks agent performance and provides recommendations"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def log_agent_execution(
        self,
        agent_type: str,
        task_category: str,
        success: bool,
        correction_count: int = 0,
        execution_time: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None,
        project_path: str = ""
    ) -> int:
        """
        Log an agent execution for performance tracking

        Args:
            agent_type: Type of agent (e.g., "coder", "researcher")
            task_category: Category of task (e.g., "code-review", "debugging")
            success: Whether the agent completed successfully
            correction_count: Number of corrections needed
            execution_time: Time taken in seconds
            context: Additional context about the task
            project_path: Project where agent was used

        Returns:
            Log entry ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO agent_performance (
                    agent_type,
                    task_category,
                    success,
                    correction_count,
                    execution_time,
                    context,
                    project_path,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_type,
                task_category,
                success,
                correction_count,
                execution_time,
                json.dumps(context) if context else None,
                project_path,
                datetime.now().isoformat()
            ))

            conn.commit()
            return cursor.lastrowid

    def get_agent_stats(
        self,
        agent_type: Optional[str] = None,
        task_category: Optional[str] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance statistics for agents

        Args:
            agent_type: Filter by specific agent (None = all agents)
            task_category: Filter by task category (None = all categories)
            time_range_days: How far back to look

        Returns:
            Statistics dictionary with success rates, avg corrections, etc
        """
        cutoff = (datetime.now() - timedelta(days=time_range_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Build query based on filters
            conditions = ["timestamp > ?"]
            params = [cutoff]

            if agent_type:
                conditions.append("agent_type = ?")
                params.append(agent_type)

            if task_category:
                conditions.append("task_category = ?")
                params.append(task_category)

            where_clause = " AND ".join(conditions)

            # Get aggregate statistics
            query = f"""
                SELECT
                    agent_type,
                    task_category,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    AVG(correction_count) as avg_corrections,
                    AVG(execution_time) as avg_execution_time
                FROM agent_performance
                WHERE {where_clause}
                GROUP BY agent_type, task_category
            """

            cursor = conn.execute(query, params)

            stats = []
            for row in cursor.fetchall():
                agent, category, total, successes, avg_corr, avg_time = row
                success_rate = (successes / total) if total > 0 else 0

                stats.append({
                    "agent_type": agent,
                    "task_category": category,
                    "total_executions": total,
                    "success_rate": round(success_rate, 2),
                    "avg_corrections": round(avg_corr, 2) if avg_corr else 0,
                    "avg_execution_time": round(avg_time, 2) if avg_time else None
                })

            return {
                "stats": stats,
                "time_range_days": time_range_days
            }

    def recommend_agent(
        self,
        task_category: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend best agents for a task based on historical performance

        Args:
            task_category: Type of task
            context: Additional context (optional)

        Returns:
            List of recommended agents sorted by performance
        """
        stats = self.get_agent_stats(task_category=task_category)

        if not stats["stats"]:
            return []

        # Sort by success rate, then by avg corrections (lower is better)
        recommendations = sorted(
            stats["stats"],
            key=lambda x: (x["success_rate"], -x["avg_corrections"]),
            reverse=True
        )

        # Format recommendations
        return [
            {
                "agent_type": rec["agent_type"],
                "confidence": rec["success_rate"],
                "reason": f"Success rate: {rec['success_rate']:.0%}, Avg corrections: {rec['avg_corrections']:.1f}",
                "total_uses": rec["total_executions"]
            }
            for rec in recommendations[:5]  # Top 5
        ]

    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """
        Get overall agent performance summary

        Returns summary of all agents with their performance metrics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    agent_type,
                    COUNT(*) as uses,
                    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(correction_count) as avg_corrections
                FROM agent_performance
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY agent_type
                ORDER BY uses DESC
            """)

            agents = []
            for row in cursor.fetchall():
                agent_type, uses, success_rate, avg_corr = row
                agents.append({
                    "agent_type": agent_type,
                    "total_uses": uses,
                    "success_rate": round(success_rate, 2),
                    "avg_corrections": round(avg_corr, 2) if avg_corr else 0,
                    "rating": self._calculate_rating(success_rate, avg_corr, uses)
                })

            return {
                "agents": agents,
                "summary": {
                    "total_agents": len(agents),
                    "total_executions": sum(a["total_uses"] for a in agents)
                }
            }

    def _calculate_rating(
        self,
        success_rate: float,
        avg_corrections: float,
        uses: int
    ) -> str:
        """Calculate agent rating (Excellent/Good/Fair/Poor)"""
        # Weight success rate heavily, penalize high correction counts
        score = success_rate * 100 - (avg_corrections * 10)

        # Adjust for sample size (less confident with fewer uses)
        if uses < 5:
            score *= 0.7

        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
