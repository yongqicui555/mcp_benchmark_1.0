"""Pattern Extractor V2 - Semantic pattern detection with hybrid memory

Upgraded pattern extraction using:
1. Semantic similarity clustering (AgentDB) instead of regex-only matching
2. Hybrid memory system (AgentDB + SQLite) for pattern storage
3. Intelligent pattern deduplication using vector search
4. Enhanced context awareness and confidence scoring
5. Backward compatibility with V1 preference system
"""

import json
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..memory.v2.test_hybrid_memory import TestMemoryRouter, create_test_hybrid_memory


@dataclass
class ExtractedPattern:
    """Structured representation of an extracted pattern"""
    pattern_type: str  # correction, workflow, tool_preference, context
    category: str  # python-package, testing, git, etc.
    description: str  # Human-readable description
    text_content: str  # Full text for semantic search
    confidence: float  # Initial confidence (0-1)
    context: Dict[str, Any]  # Additional context
    tool_name: str  # Tool that triggered extraction
    project_path: str = ""
    metadata: Dict[str, Any] = None


class PatternExtractorV2:
    """Enhanced pattern extractor using semantic clustering"""

    # Enhanced correction patterns with semantic understanding
    CORRECTION_PATTERNS = [
        r"actually\s+(?:use|do|need|should)",
        r"instead\s+(?:of|use)",
        r"use\s+(\w+)\s+(?:not|instead\s+of)\s+(\w+)",
        r"don't\s+use\s+(\w+)",
        r"should\s+(?:use|be|have)",
        r"prefer\s+(\w+)\s+(?:over|to)\s+(\w+)",
        r"(?:switch|change)\s+(?:to|from)\s+(\w+)(?:\s+(?:from|to)\s+(\w+))?",
        r"(?:always|never)\s+use\s+(\w+)",
        r"(?:fix|change|update)\s+(?:to|from)",
        r"(?:correct|right|better)\s+(?:way|approach|method)",
        r"(\w+)\s+(?:instead\s+of|not)\s+(\w+)",  # Additional pattern
        r"use\s+(\w+)\s+for\s+(?:better|faster|improved)",  # "use uv for faster installs"
    ]

    # Semantic categories for clustering
    SEMANTIC_CATEGORIES = {
        "package-management": [
            "pip", "uv", "npm", "yarn", "pnpm", "conda", "poetry",
            "package", "dependency", "install", "management"
        ],
        "testing": [
            "test", "pytest", "unittest", "jest", "vitest", "spec",
            "testing", "coverage", "assertion", "mock"
        ],
        "version-control": [
            "git", "commit", "branch", "merge", "pull", "push",
            "repository", "version", "control", "feature"
        ],
        "code-quality": [
            "lint", "format", "style", "prettier", "eslint", "pylint",
            "quality", "convention", "standard", "check"
        ],
        "build-tools": [
            "build", "compile", "bundle", "webpack", "vite", "rollup",
            "setup", "configure", "deploy", "production"
        ],
        "documentation": [
            "docs", "readme", "documentation", "comment", "docstring",
            "guide", "manual", "wiki", "help"
        ]
    }

    # Rate limiting
    MAX_PATTERNS_PER_MINUTE = 100
    RATE_LIMIT_WINDOW_SECONDS = 60

    def __init__(self, memory_router: TestMemoryRouter = None, db_path: Path = None):
        """
        Initialize V2 pattern extractor.

        Args:
            memory_router: Optional hybrid memory router (for testing)
            db_path: Legacy SQLite path (for backward compatibility)
        """
        self.memory_router = memory_router
        self.db_path = db_path
        self._pattern_timestamps: List[datetime] = []

        # Pattern cache to avoid duplicate processing
        self._recent_patterns: Set[str] = set()
        self._cache_ttl = 300  # 5 minutes

    async def initialize(self) -> bool:
        """Initialize the pattern extractor with memory system."""
        if self.memory_router is None:
            # Create default test memory router
            self.memory_router = await create_test_hybrid_memory()

        return True

    @staticmethod
    def _sanitize_description(text: str, max_length: int = 200) -> str:
        """Sanitize pattern descriptions for safe storage."""
        if not text:
            return ""

        # Remove control characters and non-printable characters
        sanitized = "".join(char for char in text if char.isprintable() or char in ['\n', '\t'])

        # Remove potential injection sequences
        sanitized = sanitized.replace('\r', '').replace('\x00', '')

        # Allow alphanumeric, spaces, and common punctuation
        allowed_pattern = r'[a-zA-Z0-9\s\-_→.,:\'"\/()]+$'
        if not re.match(allowed_pattern, sanitized):
            sanitized = "".join(char for char in sanitized if re.match(r'[a-zA-Z0-9\s\-_→.,:\'"\/()]', char))

        return sanitized[:max_length].strip()

    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.RATE_LIMIT_WINDOW_SECONDS)

        # Clean old timestamps
        self._pattern_timestamps = [ts for ts in self._pattern_timestamps if ts > cutoff]

        if len(self._pattern_timestamps) >= self.MAX_PATTERNS_PER_MINUTE:
            return False

        self._pattern_timestamps.append(now)
        return True

    async def extract_patterns(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        project_path: str = ""
    ) -> List[ExtractedPattern]:
        """
        Extract semantic patterns from tool execution.

        Returns:
            List of extracted patterns with semantic clustering
        """
        if not self._check_rate_limit():
            print(f"Warning: Pattern extraction rate limit exceeded ({self.MAX_PATTERNS_PER_MINUTE}/min)")
            return []

        patterns = []

        # 1. Detect correction patterns with semantic understanding
        correction_patterns = await self._detect_semantic_corrections(tool_name, args, result)
        patterns.extend(correction_patterns)

        # 2. Detect workflow patterns
        workflow_patterns = await self._detect_workflow_patterns(tool_name, args, project_path)
        patterns.extend(workflow_patterns)

        # 3. Detect tool preferences with clustering
        tool_prefs = await self._detect_tool_preferences(tool_name, args, result)
        patterns.extend(tool_prefs)

        # 4. Detect contextual patterns
        context_patterns = await self._detect_contextual_patterns(tool_name, args, result, project_path)
        patterns.extend(context_patterns)

        # 5. Store patterns in hybrid memory system
        stored_patterns = []
        for pattern in patterns:
            pattern_id = await self._store_pattern_semantically(pattern)
            if pattern_id:
                pattern.metadata = pattern.metadata or {}
                pattern.metadata['pattern_id'] = pattern_id
                stored_patterns.append(pattern)

        return stored_patterns

    async def _detect_semantic_corrections(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> List[ExtractedPattern]:
        """Detect correction patterns with semantic clustering."""
        patterns = []
        seen_descriptions = set()  # Track descriptions within this call
        combined_text = f"{args} {result}".lower()

        # Check for correction phrases
        for phrase_pattern in self.CORRECTION_PATTERNS:
            matches = re.finditer(phrase_pattern, combined_text, re.IGNORECASE)
            for match in matches:
                correction_text = match.group(0)
                preferred_tool = None
                avoided_tool = None

                # Extract tool names from various correction patterns

                # Pattern 1: "use X not Y" or "use X instead of Y"
                tool_match = re.search(r"use\s+(\w+)\s+(?:not|instead\s+of)\s+(\w+)", correction_text)
                if tool_match:
                    preferred_tool = tool_match.group(1)
                    avoided_tool = tool_match.group(2)

                # Pattern 2: "prefer X over Y" or "prefer X to Y"
                elif re.search(r"prefer\s+(\w+)\s+(?:over|to)\s+(\w+)", correction_text):
                    pref_match = re.search(r"prefer\s+(\w+)\s+(?:over|to)\s+(\w+)", correction_text)
                    preferred_tool = pref_match.group(1)
                    avoided_tool = pref_match.group(2)

                # Pattern 3: "switch to X from Y" or "change to X from Y"
                elif re.search(r"(?:switch|change)\s+to\s+(\w+)\s+from\s+(\w+)", correction_text):
                    switch_match = re.search(r"(?:switch|change)\s+to\s+(\w+)\s+from\s+(\w+)", correction_text)
                    preferred_tool = switch_match.group(1)
                    avoided_tool = switch_match.group(2)

                # Pattern 4: "change from X to Y" or "switch from X to Y"
                elif re.search(r"(?:switch|change)\s+from\s+(\w+)\s+to\s+(\w+)", correction_text):
                    switch_match = re.search(r"(?:switch|change)\s+from\s+(\w+)\s+to\s+(\w+)", correction_text)
                    avoided_tool = switch_match.group(1)
                    preferred_tool = switch_match.group(2)

                # Pattern 5: "always use X" or "never use Y"
                elif re.search(r"always\s+use\s+(\w+)", correction_text):
                    always_match = re.search(r"always\s+use\s+(\w+)", correction_text)
                    preferred_tool = always_match.group(1)
                    # Try to find the context of what not to use from full text
                    broader_text = f"{args} {result}".lower()
                    never_match = re.search(r"never\s+use\s+(\w+)", broader_text)
                    if never_match:
                        avoided_tool = never_match.group(1)

                elif re.search(r"never\s+use\s+(\w+)", correction_text):
                    never_match = re.search(r"never\s+use\s+(\w+)", correction_text)
                    avoided_tool = never_match.group(1)
                    # Try to find what to use instead from full text
                    broader_text = f"{args} {result}".lower()
                    always_match = re.search(r"always\s+use\s+(\w+)", broader_text)
                    if always_match:
                        preferred_tool = always_match.group(1)

                # Pattern 6: "use X for better/faster/improved"
                elif re.search(r"use\s+(\w+)\s+for\s+(?:better|faster|improved)", correction_text):
                    use_match = re.search(r"use\s+(\w+)\s+for\s+(?:better|faster|improved)", correction_text)
                    preferred_tool = use_match.group(1)
                    # Try to infer what it replaces from the command context
                    command = str(args.get('command', '')).lower()
                    if 'pip' in command and preferred_tool != 'pip':
                        avoided_tool = 'pip'
                    elif 'npm' in command and preferred_tool != 'npm':
                        avoided_tool = 'npm'

                # Pattern 7: General "X instead of Y" or "X not Y"
                elif re.search(r"(\w+)\s+(?:instead\s+of|not)\s+(\w+)", correction_text):
                    general_match = re.search(r"(\w+)\s+(?:instead\s+of|not)\s+(\w+)", correction_text)
                    preferred_tool = general_match.group(1)
                    avoided_tool = general_match.group(2)

                # If we found tool names, create a pattern
                if preferred_tool or avoided_tool:
                    # Semantic categorization
                    category = await self._classify_tool_category(preferred_tool or "", avoided_tool or "")

                    # Create description based on what we found and original phrasing
                    base_description = None
                    if preferred_tool and avoided_tool:
                        base_description = f"use {preferred_tool} instead of {avoided_tool}"
                    elif preferred_tool:
                        base_description = f"prefer {preferred_tool}"
                    elif avoided_tool:
                        base_description = f"avoid {avoided_tool}"
                    else:
                        base_description = "correction pattern detected"

                    # Make description more specific based on original correction pattern
                    # Use full result text for keyword detection, not just the matched portion
                    full_result_text = str(result).lower()
                    if "prefer" in correction_text.lower():
                        description = f"prefer {preferred_tool} over {avoided_tool}" if avoided_tool else base_description
                    elif "switch" in correction_text.lower():
                        description = f"switch to {preferred_tool} from {avoided_tool}" if avoided_tool else base_description
                    elif "actually" in full_result_text:
                        description = f"actually use {preferred_tool} not {avoided_tool}" if avoided_tool else base_description
                    elif "faster" in full_result_text or "better" in full_result_text:
                        description = f"use {preferred_tool} for better performance" if preferred_tool else base_description
                    else:
                        description = base_description

                    pattern = ExtractedPattern(
                        pattern_type="correction",
                        category=category,
                        description=self._sanitize_description(description),
                        text_content=f"correction: {description} for {category}",
                        confidence=0.8,  # High confidence for explicit corrections
                        context={
                            "preferred": preferred_tool,
                            "avoided": avoided_tool,
                            "correction_text": correction_text,
                            "full_context": str(result)
                        },
                        tool_name=tool_name
                    )

                    # Check for local duplicates within this call first
                    if description in seen_descriptions:
                        continue  # Skip this duplicate

                    # Check for semantic duplicates in stored patterns
                    if not await self._is_duplicate_pattern(pattern):
                        seen_descriptions.add(description)
                        patterns.append(pattern)

        return patterns

    async def _detect_workflow_patterns(
        self,
        tool_name: str,
        args: Dict[str, Any],
        project_path: str
    ) -> List[ExtractedPattern]:
        """Detect workflow patterns with semantic understanding."""
        patterns = []

        # Get recent tool usage for sequence detection
        recent_tools = await self._get_recent_tools_semantic(minutes=5, project_path=project_path)

        # Pattern: Code change followed by testing
        if tool_name.startswith("Bash") and any(test_word in str(args).lower() for test_word in ["test", "pytest", "jest", "spec"]):
            if any(tool.startswith(("Edit", "Write")) for tool in recent_tools):
                pattern = ExtractedPattern(
                    pattern_type="workflow",
                    category="testing",
                    description="run tests after code changes",
                    text_content="workflow: run tests after code changes for quality assurance",
                    confidence=0.7,
                    context={
                        "sequence": ["code_change", "test_execution"],
                        "tools": [tool for tool in recent_tools if tool.startswith(("Edit", "Write"))] + [tool_name]
                    },
                    tool_name=tool_name,
                    project_path=project_path
                )

                if not await self._is_duplicate_pattern(pattern):
                    patterns.append(pattern)

        # Pattern: Feature development followed by documentation
        file_path = args.get("file_path", "") if isinstance(args, dict) else ""
        if tool_name in ["Edit", "Write"] and any(doc_file in str(file_path).upper() for doc_file in ["README", "DOC", "GUIDE"]):
            if any("src" in str(args) or "lib" in str(args) for args in recent_tools):
                pattern = ExtractedPattern(
                    pattern_type="workflow",
                    category="documentation",
                    description="update documentation after feature changes",
                    text_content="workflow: update documentation after implementing features for maintainability",
                    confidence=0.6,
                    context={
                        "sequence": ["feature_development", "documentation_update"],
                        "file_path": file_path
                    },
                    tool_name=tool_name,
                    project_path=project_path
                )

                if not await self._is_duplicate_pattern(pattern):
                    patterns.append(pattern)

        return patterns

    async def _detect_tool_preferences(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> List[ExtractedPattern]:
        """Detect tool preferences with semantic clustering."""
        patterns = []

        if tool_name.startswith("Bash"):
            command = args.get("command", "")

            # Detect package managers
            if any(pkg_cmd in command.lower() for pkg_cmd in ["install", "add", "update", "upgrade"]):
                for tool_word in ["uv", "pip", "npm", "yarn", "pnpm", "poetry", "conda"]:
                    if tool_word in command.lower():
                        category = await self._classify_tool_category(tool_word, "")

                        pattern = ExtractedPattern(
                            pattern_type="tool_preference",
                            category=category,
                            description=f"use {tool_word} for {category}",
                            text_content=f"tool preference: {tool_word} for {category} package management",
                            confidence=0.5,  # Lower confidence, needs reinforcement
                            context={
                                "tool": tool_word,
                                "command": command,
                                "action": "package_management"
                            },
                            tool_name=tool_name
                        )

                        if not await self._is_duplicate_pattern(pattern):
                            patterns.append(pattern)

        return patterns

    async def _detect_contextual_patterns(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        project_path: str
    ) -> List[ExtractedPattern]:
        """Detect contextual patterns based on project and environment."""
        patterns = []

        # Project-specific patterns (e.g., always use specific tools in this project)
        if project_path:
            # Detect consistent tool usage in this project
            project_tools = await self._get_project_tool_usage(project_path)

            # If a tool is used frequently in this project, create a context pattern
            for tool, usage_count in project_tools.items():
                if usage_count >= 3:  # Used at least 3 times
                    pattern = ExtractedPattern(
                        pattern_type="context",
                        category="project-specific",
                        description=f"use {tool} in this project",
                        text_content=f"context: {tool} is preferred in project {Path(project_path).name}",
                        confidence=min(0.9, usage_count / 10),  # Max confidence at 10 uses
                        context={
                            "tool": tool,
                            "usage_count": usage_count,
                            "project_path": project_path
                        },
                        tool_name=tool_name,
                        project_path=project_path
                    )

                    if not await self._is_duplicate_pattern(pattern):
                        patterns.append(pattern)

        return patterns

    async def _classify_tool_category(self, tool1: str, tool2: str = "") -> str:
        """Classify tools into semantic categories."""
        tools = f"{tool1} {tool2}".lower()

        for category, keywords in self.SEMANTIC_CATEGORIES.items():
            if any(keyword in tools for keyword in keywords):
                return category

        return "general"

    async def _store_pattern_semantically(self, pattern: ExtractedPattern) -> Optional[str]:
        """Store pattern in hybrid memory system with semantic search."""
        try:
            # Store in hybrid memory system
            pattern_id = await self.memory_router.store_pattern(
                pattern_text=pattern.text_content,
                category=pattern.category,
                context=pattern.pattern_type,
                confidence=pattern.confidence,
                metadata={
                    "description": pattern.description,
                    "tool_name": pattern.tool_name,
                    "pattern_type": pattern.pattern_type,
                    "context": pattern.context,
                    "project_path": pattern.project_path,
                    "extracted_at": datetime.now().isoformat()
                }
            )

            return pattern_id

        except Exception as e:
            print(f"Error storing pattern: {e}")
            return None

    async def _is_duplicate_pattern(self, pattern: ExtractedPattern) -> bool:
        """Check if pattern is semantically similar to existing ones."""
        try:
            # Search for similar patterns
            similar_patterns = await self.memory_router.find_similar_patterns(
                query=pattern.text_content,
                top_k=3,
                threshold=0.8,  # High similarity threshold for duplicates
                category=pattern.category
            )

            # Check if any similar pattern is very close
            for similar in similar_patterns:
                if similar['similarity'] > 0.9:
                    # Very similar pattern exists, update its confidence instead
                    await self._reinforce_existing_pattern(similar['pattern_id'], pattern)
                    return True

            return False

        except Exception as e:
            print(f"Error checking pattern duplicates: {e}")
            return False

    async def _reinforce_existing_pattern(self, pattern_id: str, new_pattern: ExtractedPattern):
        """Reinforce an existing pattern with new evidence."""
        try:
            # Record outcome to increase confidence
            await self.memory_router.record_outcome(
                pattern_id=pattern_id,
                application_context=f"reinforcement from {new_pattern.tool_name}",
                outcome="success",
                confidence_before=new_pattern.confidence,
                confidence_after=min(1.0, new_pattern.confidence + 0.1),
                user_feedback="Pattern reinforcement through repeated detection"
            )
        except Exception as e:
            print(f"Error reinforcing pattern: {e}")

    async def _get_recent_tools_semantic(self, minutes: int = 5, project_path: str = "") -> List[str]:
        """Get recent tools with semantic context."""
        # This would integrate with the actual tool logging system
        # For now, return empty list (would be implemented with actual tool logs)
        return []

    async def _get_project_tool_usage(self, project_path: str) -> Dict[str, int]:
        """Get tool usage statistics for a specific project."""
        # This would query actual usage patterns
        # For now, return empty dict (would be implemented with actual data)
        return {}

    async def find_similar_patterns(
        self,
        query: str,
        category: str = None,
        min_confidence: float = 0.7,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find patterns similar to a query using semantic search."""
        try:
            return await self.memory_router.find_similar_patterns(
                query=query,
                top_k=top_k,
                threshold=min_confidence,
                category=category
            )
        except Exception as e:
            print(f"Error finding similar patterns: {e}")
            return []

    async def get_learned_preferences(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get learned preferences using semantic search."""
        try:
            # Use semantic search to find preferences
            query = f"preferences for {category}" if category else "learned preferences"

            patterns = await self.memory_router.find_similar_patterns(
                query=query,
                top_k=50,
                threshold=min_confidence,
                category=category
            )

            # Filter for preference-type patterns
            preferences = []
            for pattern in patterns:
                # Check if pattern has correction or tool_preference metadata
                metadata = pattern.get('metadata', {})
                if isinstance(metadata, dict):
                    pattern_type = metadata.get('pattern_type')
                    if pattern_type in ['correction', 'tool_preference']:
                        preferences.append(pattern)
                # Fallback: check pattern text for preference indicators
                elif any(indicator in pattern.get('pattern_text', '').lower()
                        for indicator in ['preference', 'correction', 'use', 'prefer']):
                    preferences.append(pattern)

            return sorted(preferences, key=lambda x: x.get('confidence', 0), reverse=True)

        except Exception as e:
            print(f"Error getting learned preferences: {e}")
            return []

    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern statistics."""
        try:
            stats = await self.memory_router.get_statistics()

            # Add pattern-specific statistics
            pattern_stats = {
                "total_patterns": stats.get('agentdb_stats', {}).get('total_patterns', 0),
                "categories": {},
                "confidence_distribution": {},
                "pattern_types": {}
            }

            return {
                "memory_stats": stats,
                "pattern_stats": pattern_stats
            }

        except Exception as e:
            print(f"Error getting pattern statistics: {e}")
            return {}

    async def close(self):
        """Clean up resources."""
        if self.memory_router:
            await self.memory_router.close()


# Convenience function for backward compatibility
async def create_pattern_extractor_v2(
    db_path: Path = None,
    memory_router: TestMemoryRouter = None
) -> PatternExtractorV2:
    """Create and initialize a V2 pattern extractor."""
    extractor = PatternExtractorV2(memory_router=memory_router, db_path=db_path)
    await extractor.initialize()
    return extractor