"""Significance Scorer - Determines which tool executions are worth learning from

Uses multi-factor scoring to identify high-value learning opportunities:
1. Tool type importance
2. File/path significance
3. Operation type (create/modify/delete)
4. Error patterns
5. Repetition frequency
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
import re


class SignificanceScorer:
    """Calculates significance scores for tool executions"""

    # Memory management settings
    MAX_TRACKER_SIZE = 1000  # Maximum number of patterns to track
    PATTERN_EXPIRY_HOURS = 24  # Expire patterns after 24 hours

    # Base scores by tool type
    TOOL_SCORES = {
        # High value - direct code changes
        "Edit": 0.8,
        "Write": 0.8,
        "MultiEdit": 0.9,

        # Medium-high - git operations
        "Bash(git": 0.7,

        # Medium - agent spawning (track which agents used)
        "Task": 0.6,

        # Medium - file operations
        "Read": 0.4,
        "Glob": 0.3,
        "Grep": 0.3,

        # Lower - informational
        "WebSearch": 0.2,
        "WebFetch": 0.2,
    }

    # Significant file patterns
    SIGNIFICANT_FILES = {
        "CLAUDE.md": 1.0,
        ".claude.md": 1.0,
        "CLAUDE.local.md": 0.9,
        "package.json": 0.8,
        "pyproject.toml": 0.8,
        "requirements.txt": 0.7,
        "Dockerfile": 0.7,
        "docker-compose.yml": 0.7,
        ".env": 0.7,
        "README.md": 0.6,
        ".gitignore": 0.5,
        "tsconfig.json": 0.5,
        ".mcp.json": 0.9,
        "hooks.json": 0.9,
    }

    # Operation boost modifiers
    OPERATION_BOOSTS = {
        "create": 0.3,
        "write": 0.3,
        "edit": 0.2,
        "update": 0.2,
        "delete": 0.3,
        "commit": 0.4,
        "fix": 0.3,
        "refactor": 0.2,
    }

    def __init__(self):
        # Use OrderedDict for LRU-style eviction
        # Format: {pattern_key: {"count": int, "timestamp": datetime}}
        self.repetition_tracker: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.last_cleanup = datetime.now()

    def calculate_significance(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        project_path: str = ""
    ) -> float:
        """
        Calculate overall significance score (0.0 - 1.0)

        Args:
            tool_name: Name of the tool executed
            args: Tool arguments
            result: Tool result/output
            project_path: Current project path

        Returns:
            Significance score between 0.0 and 1.0
        """
        score = 0.0

        # 1. Base score from tool type
        score = self._get_tool_base_score(tool_name)

        # 2. Boost for significant files
        file_boost = self._get_file_significance(args)
        score = min(1.0, score + file_boost)

        # 3. Boost for operation type
        operation_boost = self._get_operation_boost(tool_name, args, result)
        score = min(1.0, score + operation_boost)

        # 4. Boost for corrections/fixes (indicates learning opportunity)
        if self._is_correction(args, result):
            score = min(1.0, score + 0.3)

        # 5. Boost for repeated patterns (strong signal)
        repetition_boost = self._get_repetition_boost(tool_name, args)
        score = min(1.0, score + repetition_boost)

        # 6. Boost for agent usage (track performance)
        if tool_name == "Task":
            score = min(1.0, score + 0.2)

        # 7. Penalty for read-only operations
        if tool_name in ["Read", "Glob", "Grep"] and not self._has_significant_context(args):
            score *= 0.5

        return round(score, 2)

    def _get_tool_base_score(self, tool_name: str) -> float:
        """Get base significance score for tool type"""
        # Exact match
        if tool_name in self.TOOL_SCORES:
            return self.TOOL_SCORES[tool_name]

        # Prefix match (e.g., "Bash(git commit)" matches "Bash(git")
        for pattern, score in self.TOOL_SCORES.items():
            if tool_name.startswith(pattern):
                return score

        # Default for unknown tools
        return 0.2

    def _get_file_significance(self, args: Dict[str, Any]) -> float:
        """Check if operation involves significant files"""
        boost = 0.0

        # Check all possible file path arguments
        path_keys = ["file_path", "path", "files", "directory", "paths"]

        for key in path_keys:
            if key in args:
                path_value = args[key]

                # Handle both string and list paths
                paths = [path_value] if isinstance(path_value, str) else path_value

                for path_str in paths:
                    filename = Path(str(path_str)).name.lower()

                    # Check against significant file patterns
                    for pattern, score in self.SIGNIFICANT_FILES.items():
                        if pattern.lower() in filename:
                            boost = max(boost, score)

        return boost

    def _get_operation_boost(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> float:
        """Boost score based on operation type"""
        boost = 0.0

        # Check tool name for operation keywords
        tool_lower = tool_name.lower()
        for operation, op_boost in self.OPERATION_BOOSTS.items():
            if operation in tool_lower:
                boost = max(boost, op_boost)

        # Check args for operation indicators
        args_str = str(args).lower()
        for operation, op_boost in self.OPERATION_BOOSTS.items():
            if operation in args_str:
                boost = max(boost, op_boost * 0.5)  # Half boost for args

        # Check if result indicates success (completed operation)
        result_str = str(result).lower()
        if any(word in result_str for word in ["success", "completed", "created", "modified"]):
            boost += 0.1

        return boost

    def _is_correction(self, args: Dict[str, Any], result: Any) -> bool:
        """Detect if this is likely a correction/fix"""
        correction_indicators = [
            "fix",
            "correct",
            "actually",
            "instead",
            "should use",
            "use this instead",
            "wrong",
            "error",
            "mistake"
        ]

        combined_text = f"{args} {result}".lower()
        return any(indicator in combined_text for indicator in correction_indicators)

    def _get_repetition_boost(self, tool_name: str, args: Dict[str, Any]) -> float:
        """Boost score for repeated patterns (strong learning signal)"""
        # Periodic cleanup to prevent memory leaks
        self._cleanup_expired_patterns()

        # Create a simple pattern key
        pattern_key = f"{tool_name}:{self._get_pattern_fingerprint(args)}"
        now = datetime.now()

        # Track repetition with timestamp
        if pattern_key not in self.repetition_tracker:
            self.repetition_tracker[pattern_key] = {
                "count": 1,
                "timestamp": now
            }
            self._enforce_size_limit()
            return 0.0
        else:
            # Update existing pattern
            entry = self.repetition_tracker[pattern_key]
            entry["count"] += 1
            entry["timestamp"] = now  # Refresh timestamp

            # Move to end (LRU behavior)
            self.repetition_tracker.move_to_end(pattern_key)

            count = entry["count"]

            # Boost increases with repetition (up to 0.3)
            # 2 times: +0.1, 3 times: +0.2, 4+ times: +0.3
            return min(0.3, (count - 1) * 0.1)

    def _get_pattern_fingerprint(self, args: Dict[str, Any]) -> str:
        """Create a simple fingerprint for pattern matching"""
        # Extract key indicators from args
        indicators = []

        if "file_path" in args:
            # Use file extension as pattern
            ext = Path(str(args["file_path"])).suffix
            indicators.append(f"ext:{ext}")

        if "command" in args:
            # Extract first word of command
            cmd = str(args["command"]).split()[0]
            indicators.append(f"cmd:{cmd}")

        return "|".join(indicators) if indicators else "generic"

    def _has_significant_context(self, args: Dict[str, Any]) -> bool:
        """Check if read operation has significant context"""
        # Reading CLAUDE.md or config files is significant
        if "file_path" in args:
            path = str(args["file_path"]).lower()
            return any(sig_file.lower() in path for sig_file in self.SIGNIFICANT_FILES.keys())

        return False

    def _cleanup_expired_patterns(self) -> None:
        """
        Remove expired patterns from tracker to prevent memory leaks.
        Runs at most once per hour to avoid overhead.
        """
        now = datetime.now()

        # Only cleanup once per hour
        if (now - self.last_cleanup).total_seconds() < 3600:
            return

        self.last_cleanup = now
        expiry_threshold = now - timedelta(hours=self.PATTERN_EXPIRY_HOURS)

        # Remove expired entries
        expired_keys = [
            key for key, entry in self.repetition_tracker.items()
            if entry["timestamp"] < expiry_threshold
        ]

        for key in expired_keys:
            del self.repetition_tracker[key]

    def _enforce_size_limit(self) -> None:
        """
        Enforce maximum tracker size using LRU eviction.
        Removes oldest entries when size limit is exceeded.
        """
        if len(self.repetition_tracker) > self.MAX_TRACKER_SIZE:
            # Remove oldest 10% of entries (100 items if max is 1000)
            num_to_remove = max(1, self.MAX_TRACKER_SIZE // 10)

            for _ in range(num_to_remove):
                if self.repetition_tracker:
                    # Remove oldest (first) item
                    self.repetition_tracker.popitem(last=False)
