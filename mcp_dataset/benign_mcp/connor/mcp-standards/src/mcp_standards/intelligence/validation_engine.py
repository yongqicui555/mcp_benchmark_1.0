"""Validation Engine - Validates deliverables against specs and enforces quality gates

Provides:
1. Spec capture and comparison
2. Quality gate checking (tests, docs, build)
3. Gap detection and reporting
4. Learning from validation failures
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class ValidationEngine:
    """Validates deliverables and enforces quality gates"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def capture_spec(
        self,
        task_description: str,
        project_path: str = ""
    ) -> int:
        """
        Capture a task specification for later validation

        Call this when a task is started to store the requirements
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO spec_validations (
                    task_description,
                    spec_captured,
                    project_path,
                    validation_status
                ) VALUES (?, ?, ?, 'pending')
            """, (
                task_description,
                task_description,  # For now, store as-is
                project_path
            ))

            conn.commit()
            return cursor.lastrowid

    def validate_spec(
        self,
        spec_id: int,
        deliverable_summary: str
    ) -> Dict[str, Any]:
        """
        Validate a deliverable against its original spec

        Returns validation result with gaps identified
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get original spec
            cursor = conn.execute("""
                SELECT * FROM spec_validations WHERE id = ?
            """, (spec_id,))

            spec_row = cursor.fetchone()

            if not spec_row:
                return {"error": "Spec not found"}

            # Perform validation (simplified for now)
            gaps = self._find_gaps(
                spec_row["spec_captured"],
                deliverable_summary
            )

            # Determine status
            if not gaps:
                status = "matched"
            elif len(gaps) > 3:
                status = "significant_gaps"
            else:
                status = "minor_gaps"

            # Update record
            conn.execute("""
                UPDATE spec_validations
                SET deliverable_summary = ?,
                    validation_status = ?,
                    gaps_found = ?
                WHERE id = ?
            """, (
                deliverable_summary,
                status,
                json.dumps(gaps),
                spec_id
            ))

            conn.commit()

            return {
                "status": status,
                "gaps": gaps,
                "spec_id": spec_id
            }

    def _find_gaps(self, spec: str, deliverable: str) -> List[str]:
        """
        Find gaps between specification and deliverable

        TODO: Implement smarter gap detection:
        - Extract requirements from spec
        - Check if each requirement is mentioned in deliverable
        - Use LLM for semantic comparison
        """
        gaps = []

        # Simple keyword checking for now
        keywords = ["test", "documentation", "error handling", "validation"]

        for keyword in keywords:
            if keyword in spec.lower() and keyword not in deliverable.lower():
                gaps.append(f"Missing: {keyword}")

        return gaps

    def check_quality_gates(
        self,
        project_path: str,
        gate_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check if quality gates are satisfied for a project

        Args:
            project_path: Path to project
            gate_types: Specific gates to check (None = all)

        Returns:
            Dictionary with gate statuses
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get gates for this project
            if gate_types:
                placeholders = ','.join('?' * len(gate_types))
                query = f"""
                    SELECT * FROM validation_gates
                    WHERE project_path = ?
                      AND gate_type IN ({placeholders})
                """
                params = [project_path] + gate_types
            else:
                query = """
                    SELECT * FROM validation_gates
                    WHERE project_path = ?
                """
                params = [project_path]

            cursor = conn.execute(query, params)
            gates = cursor.fetchall()

            results = {}
            all_passed = True

            for gate in gates:
                gate_result = self._check_gate(gate)
                results[gate["gate_type"]] = gate_result

                if gate["required"] and not gate_result["passed"]:
                    all_passed = False

            return {
                "all_passed": all_passed,
                "gates": results,
                "project_path": project_path
            }

    def _check_gate(self, gate: sqlite3.Row) -> Dict[str, Any]:
        """Check a single quality gate"""
        # TODO: Implement actual checking
        # - Run check_command if provided
        # - Auto-detect common gates (tests, docs, build)
        # - Return status and details

        return {
            "gate_type": gate["gate_type"],
            "passed": True,  # Placeholder
            "required": bool(gate["required"]),
            "details": "Not yet implemented"
        }

    def add_quality_gate(
        self,
        project_path: str,
        gate_type: str,
        required: bool = True,
        check_command: Optional[str] = None
    ) -> int:
        """Add a quality gate for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO validation_gates (
                    project_path,
                    gate_type,
                    required,
                    check_command,
                    auto_check
                ) VALUES (?, ?, ?, ?, TRUE)
            """, (project_path, gate_type, required, check_command))

            conn.commit()
            return cursor.lastrowid
