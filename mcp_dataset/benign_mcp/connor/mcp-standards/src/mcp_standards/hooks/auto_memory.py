"""
Auto Memory Hook - Detects corrections and stores them automatically

Watches for patterns like:
- "Actually, use X not Y"
- "Use X instead of Y"
- "Prefer X over Y"
- "Always use X for Y"

Automatically stores in AgentDB without manual MCP calls.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoMemoryHook:
    """
    Automatic correction detection and memory storage.

    Monitors tool execution and natural language for correction patterns.
    Stores detected corrections in AgentDB automatically.
    """

    # Correction phrases (semantic patterns)
    CORRECTION_PATTERNS = [
        # Explicit corrections
        r"actually,?\s+(?:use|do|need|should|prefer)\s+(.+?)(?:\s+not\s+|\s+instead\s+of\s+|\s+over\s+)(.+?)(?:\s|$|\.|\,)",
        r"use\s+(\w+)\s+not\s+(\w+)",
        r"use\s+(\w+)\s+instead\s+of\s+(\w+)",
        r"prefer\s+(\w+)\s+(?:over|to)\s+(\w+)",
        r"don't\s+use\s+(\w+),?\s+use\s+(\w+)",
        r"always\s+use\s+(\w+)\s+(?:for|when)\s+(.+?)(?:\s|$|\.|\,)",

        # Tool-specific patterns
        r"(?:npm|pip|cargo|gem)\s+install\s+(\w+)",  # Package installations
        r"git\s+(\w+)",  # Git commands
    ]

    # Context categories (auto-detect from content)
    CATEGORY_KEYWORDS = {
        "python": ["pip", "uv", "poetry", "python", "pytest", "virtualenv"],
        "javascript": ["npm", "yarn", "pnpm", "node", "jest", "webpack"],
        "git": ["git", "commit", "branch", "merge", "rebase", "push"],
        "testing": ["test", "spec", "assert", "mock", "coverage"],
        "docker": ["docker", "dockerfile", "container", "image", "compose"],
        "general": []  # Fallback
    }

    def __init__(self, agentdb_client):
        """
        Initialize auto memory hook.

        Args:
            agentdb_client: AgentDBClient instance for storage
        """
        self.agentdb = agentdb_client
        self.detection_count = 0

    def detect_correction(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> Optional[Tuple[str, str, str]]:
        """
        Detect if tool execution contains a correction pattern.

        Args:
            tool_name: Name of tool executed
            args: Tool arguments
            result: Tool result

        Returns:
            Tuple of (preferred, deprecated, content) if correction found, else None

        Example:
            ("uv", "pip", "use uv not pip")
        """
        # Combine all text for analysis
        combined_text = self._extract_text(tool_name, args, result)

        # Check each pattern
        for pattern in self.CORRECTION_PATTERNS:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                # Extract correction
                if len(match.groups()) >= 2:
                    preferred = match.group(1).strip()
                    deprecated = match.group(2).strip()
                    content = match.group(0).strip()

                    logger.info(f"🎯 Detected correction: '{preferred}' over '{deprecated}'")
                    return (preferred, deprecated, content)

        return None

    def detect_preference(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> Optional[Tuple[str, str]]:
        """
        Detect positive preferences (not corrections).

        Example: "always run tests before commit"

        Returns:
            Tuple of (preference, content) if found
        """
        combined_text = self._extract_text(tool_name, args, result)

        # Preference patterns
        preference_patterns = [
            r"always\s+(.+?)(?:\s+before\s+|\s+after\s+|\s+when\s+)(.+?)(?:\s|$|\.)",
            r"(?:should|must)\s+(?:always\s+)?(.+?)(?:\s|$|\.)",
            r"(?:prefer|like)\s+to\s+(.+?)(?:\s|$|\.)",
        ]

        for pattern in preference_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                preference = match.group(1).strip()
                content = match.group(0).strip()

                logger.info(f"💡 Detected preference: '{preference}'")
                return (preference, content)

        return None

    async def auto_store(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> bool:
        """
        Auto-detect and store corrections/preferences.

        This is the main entry point - call after every tool execution.

        Args:
            tool_name: Tool that was executed
            args: Tool arguments
            result: Tool result

        Returns:
            True if something was stored, False otherwise
        """
        stored = False

        # Detect correction
        correction = self.detect_correction(tool_name, args, result)
        if correction:
            preferred, deprecated, content = correction

            # Determine category
            category = self._detect_category(content, tool_name)

            # Store in AgentDB
            success = await self.agentdb.remember(
                content=f"Use {preferred} instead of {deprecated}",
                category=category,
                metadata={
                    "type": "correction",
                    "preferred": preferred,
                    "deprecated": deprecated,
                    "tool_name": tool_name,
                    "detected_at": datetime.now().isoformat(),
                    "original_text": content
                }
            )

            if success:
                self.detection_count += 1
                stored = True

        # Detect preference
        preference = self.detect_preference(tool_name, args, result)
        if preference and not correction:  # Don't double-store
            pref_text, content = preference

            category = self._detect_category(content, tool_name)

            success = await self.agentdb.remember(
                content=pref_text,
                category=category,
                metadata={
                    "type": "preference",
                    "tool_name": tool_name,
                    "detected_at": datetime.now().isoformat(),
                    "original_text": content
                }
            )

            if success:
                self.detection_count += 1
                stored = True

        return stored

    def _extract_text(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> str:
        """
        Extract searchable text from tool execution.

        Combines tool name, args, and result into single string.
        """
        parts = [tool_name]

        # Extract from args
        if isinstance(args, dict):
            for key, value in args.items():
                parts.append(f"{key}:{value}")
        else:
            parts.append(str(args))

        # Extract from result
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (str, int, float, bool)):
                    parts.append(f"{key}:{value}")
        else:
            parts.append(str(result))

        return " ".join(str(p) for p in parts)

    def _detect_category(self, content: str, tool_name: str) -> str:
        """
        Auto-detect category from content and tool name.

        Args:
            content: Text content to analyze
            tool_name: Tool that was executed

        Returns:
            Category name (e.g., "python", "git", "general")
        """
        content_lower = content.lower()
        tool_lower = tool_name.lower()

        # Check each category's keywords
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in content_lower or keyword in tool_lower:
                    return category

        # Fallback
        return "general"

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "total_detections": self.detection_count,
            "patterns_count": len(self.CORRECTION_PATTERNS),
            "categories": list(self.CATEGORY_KEYWORDS.keys())
        }


# Convenience function for standalone usage
async def detect_and_store(
    tool_name: str,
    args: Dict[str, Any],
    result: Any,
    agentdb_client
) -> bool:
    """
    Quick function to detect and store in one call.

    Usage:
        from mcp_standards.agentdb_client import AgentDBClient
        from mcp_standards.hooks.auto_memory import detect_and_store

        client = AgentDBClient()
        stored = await detect_and_store(
            tool_name="Bash",
            args={"command": "uv pip install pytest"},
            result="success",
            agentdb_client=client
        )
    """
    hook = AutoMemoryHook(agentdb_client)
    return await hook.auto_store(tool_name, args, result)
