#!/usr/bin/env python3
"""Capture Hook - Main entry point for PostToolUse hooks

This script is called by Claude Code after every tool execution.
It receives tool execution data via stdin and decides whether to:
1. Store it in memory
2. Extract learning patterns
3. Update CLAUDE.md files
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .significance_scorer import SignificanceScorer
from .pattern_extractor import PatternExtractor


class HookCaptureSystem:
    """Manages automatic capture and learning from tool executions"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path.home() / ".mcp-standards" / "knowledge.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.scorer = SignificanceScorer()
        self.extractor = PatternExtractor(self.db_path)

    def capture_tool_execution(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main capture logic for tool executions

        Args:
            tool_data: JSON data from Claude Code hook
                {
                    "tool": "tool_name",
                    "args": {...},
                    "result": {...},
                    "timestamp": "ISO8601",
                    "projectPath": "/path/to/project"
                }

        Returns:
            Status dict with capture results
        """
        tool_name = tool_data.get("tool", "unknown")
        args = tool_data.get("args", {})
        result = tool_data.get("result", {})
        project_path = tool_data.get("projectPath", "")

        # Calculate significance
        significance = self.scorer.calculate_significance(
            tool_name=tool_name,
            args=args,
            result=result,
            project_path=project_path
        )

        # Skip low-significance executions
        if significance < 0.3:
            return {
                "captured": False,
                "reason": "low_significance",
                "score": significance
            }

        # Store in database
        log_id = self._store_execution(tool_data, significance)

        # Extract patterns if highly significant
        patterns = []
        if significance > 0.6:
            patterns = self.extractor.extract_patterns(
                tool_name=tool_name,
                args=args,
                result=result,
                project_path=project_path
            )

        return {
            "captured": True,
            "log_id": log_id,
            "significance": significance,
            "patterns_found": len(patterns),
            "patterns": patterns
        }

    def _store_execution(self, tool_data: Dict[str, Any], significance: float) -> int:
        """Store tool execution in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO tool_executions (
                    tool_name,
                    args,
                    result,
                    significance,
                    project_path,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tool_data.get("tool"),
                json.dumps(tool_data.get("args", {})),
                json.dumps(str(tool_data.get("result", ""))[:1000]),
                significance,
                tool_data.get("projectPath", ""),
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid


def capture_tool_execution(hook_input: Dict[str, Any]) -> None:
    """
    Main entry point called by Claude Code hooks

    Reads JSON from stdin, processes it, and outputs results
    """
    try:
        system = HookCaptureSystem()
        result = system.capture_tool_execution(hook_input)

        # Output results for Claude Code
        print(json.dumps(result, indent=2))

        # Exit code 0 = success, don't block execution
        sys.exit(0)

    except Exception as e:
        # Log error but don't block Claude Code
        error_result = {
            "captured": False,
            "error": str(e),
            "reason": "exception"
        }
        print(json.dumps(error_result, indent=2), file=sys.stderr)
        sys.exit(0)  # Still exit 0 to not block Claude


if __name__ == "__main__":
    # Read hook data from stdin
    hook_data = json.load(sys.stdin)
    capture_tool_execution(hook_data)
