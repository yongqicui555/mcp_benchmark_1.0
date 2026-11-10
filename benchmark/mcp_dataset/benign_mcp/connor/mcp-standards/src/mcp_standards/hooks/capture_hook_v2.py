#!/usr/bin/env python3
"""Capture Hook V2 - Claude Code hooks with V2 pattern extractor

Enhanced version that uses the V2 hybrid memory system (AgentDB + SQLite)
for semantic pattern detection and learning. Falls back to V1 if V2 unavailable.
"""

import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from .significance_scorer import SignificanceScorer
from .pattern_extractor import PatternExtractor  # V1 fallback
from .pattern_extractor_v2 import PatternExtractorV2, ExtractedPattern
from ..memory.v2.test_hybrid_memory import create_test_hybrid_memory, TestMemoryRouter


class HookCaptureSystemV2:
    """Enhanced capture system using V2 semantic pattern extraction"""

    def __init__(self, db_path: Optional[Path] = None, force_v1: bool = False):
        if db_path is None:
            self.db_path = Path.home() / ".mcp-standards" / "knowledge.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.scorer = SignificanceScorer()

        # V2 system setup
        self.v2_available = False
        self.memory_router: Optional[TestMemoryRouter] = None
        self.extractor_v2: Optional[PatternExtractorV2] = None

        # V1 fallback
        self.extractor_v1 = PatternExtractor(self.db_path)
        self.force_v1 = force_v1

        # Initialize V2 system asynchronously (done later)
        self._v2_init_attempted = False

    async def _initialize_v2_system(self) -> bool:
        """Initialize V2 hybrid memory system"""
        if self._v2_init_attempted or self.force_v1:
            return self.v2_available

        self._v2_init_attempted = True

        try:
            # Check if AgentDB HTTP server is available
            import aiohttp
            import asyncio

            timeout = aiohttp.ClientTimeout(total=2)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get('http://localhost:3002/health') as response:
                    if response.status != 200:
                        print("⚠️  AgentDB server not available, falling back to V1", file=sys.stderr)
                        return False

            # Initialize hybrid memory system
            self.memory_router = await create_test_hybrid_memory(
                agentdb_path=".claude/memory/v2_agentdb",
                sqlite_path=str(self.db_path.parent / "v2_audit.db")
            )

            # Initialize V2 extractor
            self.extractor_v2 = PatternExtractorV2(
                memory_router=self.memory_router,
                db_path=self.db_path
            )

            self.v2_available = True
            print("✅ V2 pattern extraction system initialized", file=sys.stderr)
            return True

        except Exception as e:
            print(f"⚠️  V2 initialization failed: {e}, falling back to V1", file=sys.stderr)
            self.v2_available = False
            return False

    async def capture_tool_execution(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main capture logic using V2 system with V1 fallback

        Args:
            tool_data: JSON data from Claude Code hook

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
                "score": significance,
                "system_version": "v2"
            }

        # Store in database
        log_id = self._store_execution(tool_data, significance)

        # Extract patterns if highly significant
        patterns = []
        system_used = "v1"  # Default fallback

        if significance > 0.6:
            # Try V2 first
            if not self.v2_available:
                await self._initialize_v2_system()

            if self.v2_available and self.extractor_v2:
                try:
                    extracted_patterns = await self.extractor_v2.extract_patterns(
                        tool_name=tool_name,
                        args=args,
                        result=result,
                        project_path=project_path
                    )

                    # Convert V2 ExtractedPattern objects to dict format
                    patterns = self._convert_v2_patterns_to_dict(extracted_patterns)
                    system_used = "v2"

                except Exception as e:
                    print(f"⚠️  V2 pattern extraction failed: {e}, using V1", file=sys.stderr)
                    # Fall back to V1
                    patterns = self.extractor_v1.extract_patterns(
                        tool_name=tool_name,
                        args=args,
                        result=result,
                        project_path=project_path
                    )
                    system_used = "v1_fallback"
            else:
                # Use V1
                patterns = self.extractor_v1.extract_patterns(
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
            "patterns": patterns,
            "system_version": system_used,
            "v2_available": self.v2_available
        }

    def _convert_v2_patterns_to_dict(self, extracted_patterns: List[ExtractedPattern]) -> List[Dict[str, Any]]:
        """Convert V2 ExtractedPattern objects to dict format for compatibility"""
        patterns = []

        for pattern in extracted_patterns:
            pattern_dict = {
                "type": pattern.pattern_type,
                "category": pattern.category,
                "description": pattern.description,
                "text": pattern.text_content,
                "confidence": pattern.confidence,
                "context": pattern.context,
                "tool_name": pattern.tool_name,
                "project_path": pattern.project_path,
                "metadata": pattern.metadata or {},
                "extracted_at": datetime.now().isoformat(),
                "system": "v2"
            }
            patterns.append(pattern_dict)

        return patterns

    def _store_execution(self, tool_data: Dict[str, Any], significance: float) -> int:
        """Store tool execution in database (shared by V1 and V2)"""
        # Ensure the table exists
        self._ensure_table_exists()

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

    def _ensure_table_exists(self):
        """Ensure the tool_executions table exists"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    args TEXT,
                    result TEXT,
                    significance REAL,
                    project_path TEXT,
                    timestamp TEXT
                )
            """)
            conn.commit()

    async def close(self):
        """Clean up V2 resources"""
        if self.memory_router:
            await self.memory_router.close()


def capture_tool_execution_sync(hook_input: Dict[str, Any]) -> None:
    """
    Synchronous wrapper for async V2 capture system

    Called by Claude Code hooks - runs the async capture in an event loop
    """
    async def async_capture():
        system = HookCaptureSystemV2()
        try:
            result = await system.capture_tool_execution(hook_input)

            # Output results for Claude Code
            print(json.dumps(result, indent=2))

            return result

        except Exception as e:
            # Log error but don't block Claude Code
            error_result = {
                "captured": False,
                "error": str(e),
                "reason": "exception",
                "system_version": "v2_error"
            }
            print(json.dumps(error_result, indent=2), file=sys.stderr)
            return error_result

        finally:
            await system.close()

    try:
        # Run the async capture
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(async_capture())
        finally:
            loop.close()

        # Exit code 0 = success, don't block execution
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error in V2 capture system: {e}", file=sys.stderr)
        sys.exit(0)  # Still exit 0 to not block Claude


# Legacy function name for compatibility
def capture_tool_execution(hook_input: Dict[str, Any]) -> None:
    """Legacy entry point - redirects to V2 system"""
    capture_tool_execution_sync(hook_input)


if __name__ == "__main__":
    # Read hook data from stdin
    hook_data = json.load(sys.stdin)
    capture_tool_execution_sync(hook_data)