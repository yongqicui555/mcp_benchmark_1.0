"""
Diff-Based Learning System for CLAUDE.md Optimization

Analyzes manual edits to CLAUDE.md and automatically learns:
1. User preferences and patterns
2. Common corrections
3. Section importance
4. Token optimization strategies

Implements the "stop telling Claude to use uv not pip" solution by
automatically detecting and applying recurring corrections.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter
import difflib

logger = logging.getLogger(__name__)


@dataclass
class EditPattern:
    """Represents a learned pattern from manual edits."""
    pattern_type: str  # preference, rule, removal, addition
    content: str
    frequency: int
    confidence: float
    first_seen: datetime
    last_seen: datetime
    contexts: List[str]  # Where this pattern appears

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['first_seen'] = self.first_seen.isoformat()
        result['last_seen'] = self.last_seen.isoformat()
        return result


@dataclass
class DiffAnalysis:
    """Analysis of a CLAUDE.md diff."""
    timestamp: datetime
    additions_count: int
    deletions_count: int
    modifications_count: int
    patterns_detected: List[EditPattern]
    sections_added: List[str]
    sections_removed: List[str]
    preferences_changed: List[Dict[str, str]]
    token_impact: int  # Estimated token change

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['patterns_detected'] = [p.to_dict() for p in self.patterns_detected]
        return result


class DiffBasedLearner:
    """
    Learn from manual edits to CLAUDE.md files.

    Capabilities:
    - Detect recurring corrections (e.g., "use uv not pip")
    - Learn section importance from user edits
    - Identify token-saving strategies
    - Build preference database automatically
    - Auto-apply learned patterns
    """

    # Pattern detection rules
    PREFERENCE_PATTERNS = [
        r'(?:use|prefer|always use|default to)\s+(\w+)(?:\s+(?:not|instead of|over)\s+(\w+))?',
        r'(?:never|don\'t|avoid)\s+(?:use\s+)?(\w+)',
        r'(?:must|should|required to)\s+use\s+(\w+)',
    ]

    TOOL_PATTERNS = [
        r'(uv|pip|npm|yarn|pnpm|poetry|pipenv)',
        r'(pytest|jest|vitest|mocha|jasmine)',
        r'(ruff|eslint|pylint|flake8|black)',
        r'(mypy|typescript|flow|pyright)',
    ]

    def __init__(self, memory_system=None, agentdb=None):
        """
        Initialize diff-based learner.

        Args:
            memory_system: PersistentMemory for storing learned patterns
            agentdb: AgentDB for semantic pattern matching
        """
        self.memory = memory_system
        self.agentdb = agentdb

        # Pattern database
        self._learned_patterns: Dict[str, EditPattern] = {}

        # Statistics
        self._stats = {
            'diffs_analyzed': 0,
            'patterns_learned': 0,
            'auto_applications': 0,
            'confidence_improvements': 0
        }

    async def analyze_diff(
        self,
        previous_content: str,
        current_content: str,
        project_path: Optional[str] = None
    ) -> DiffAnalysis:
        """
        Analyze differences between two versions of CLAUDE.md.

        Args:
            previous_content: Previous version content
            current_content: Current version content
            project_path: Optional project path for context

        Returns:
            DiffAnalysis with detected patterns
        """
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            previous_content.splitlines(keepends=True),
            current_content.splitlines(keepends=True),
            lineterm=''
        ))

        # Parse diff
        additions = []
        deletions = []

        for line in diff_lines:
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:].strip())

        # Detect patterns
        patterns_detected = []

        # 1. Preference changes
        preference_patterns = self._detect_preference_changes(additions, deletions)
        patterns_detected.extend(preference_patterns)

        # 2. Section changes
        sections_added = self._extract_section_headers(additions)
        sections_removed = self._extract_section_headers(deletions)

        # 3. Tool preferences
        tool_patterns = self._detect_tool_preferences(additions, deletions)
        patterns_detected.extend(tool_patterns)

        # 4. Rule additions
        rule_patterns = self._detect_rules(additions)
        patterns_detected.extend(rule_patterns)

        # 5. Token optimization moves
        optimization_patterns = self._detect_optimizations(additions, deletions)
        patterns_detected.extend(optimization_patterns)

        # Calculate token impact
        token_impact = self._estimate_token_impact(additions, deletions)

        # Build analysis
        analysis = DiffAnalysis(
            timestamp=datetime.now(),
            additions_count=len(additions),
            deletions_count=len(deletions),
            modifications_count=len(diff_lines),
            patterns_detected=patterns_detected,
            sections_added=sections_added,
            sections_removed=sections_removed,
            preferences_changed=self._extract_preferences(preference_patterns),
            token_impact=token_impact
        )

        # Learn from patterns
        await self._learn_patterns(patterns_detected, project_path)

        # Store analysis
        if self.memory:
            await self.memory.store(
                key=f"diff_analysis_{analysis.timestamp.timestamp()}",
                value=analysis.to_dict(),
                namespace="learning",
                metadata={
                    'project_path': project_path,
                    'pattern_count': len(patterns_detected),
                    'significant': len(patterns_detected) > 0
                }
            )

        self._stats['diffs_analyzed'] += 1

        logger.info(
            f"Analyzed diff: {len(additions)} additions, {len(deletions)} deletions, "
            f"{len(patterns_detected)} patterns detected"
        )

        return analysis

    def _detect_preference_changes(
        self,
        additions: List[str],
        deletions: List[str]
    ) -> List[EditPattern]:
        """Detect preference changes from diff."""
        patterns = []

        # Look for "use X not Y" patterns in additions
        for addition in additions:
            for pattern_re in self.PREFERENCE_PATTERNS:
                matches = re.finditer(pattern_re, addition, re.IGNORECASE)

                for match in matches:
                    preferred = match.group(1)
                    avoided = match.group(2) if match.lastindex > 1 else None

                    # Check if this corrects something in deletions
                    is_correction = False
                    if avoided:
                        for deletion in deletions:
                            if avoided.lower() in deletion.lower():
                                is_correction = True
                                break

                    pattern = EditPattern(
                        pattern_type='preference_correction' if is_correction else 'preference',
                        content=addition.strip(),
                        frequency=1,
                        confidence=0.8 if is_correction else 0.5,
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        contexts=[f"preferred={preferred}", f"avoided={avoided}" if avoided else ""]
                    )

                    patterns.append(pattern)

        return patterns

    def _detect_tool_preferences(
        self,
        additions: List[str],
        deletions: List[str]
    ) -> List[EditPattern]:
        """Detect tool preference patterns."""
        patterns = []

        # Extract tools from additions and deletions
        added_tools = set()
        removed_tools = set()

        for addition in additions:
            for tool_pattern in self.TOOL_PATTERNS:
                matches = re.findall(tool_pattern, addition, re.IGNORECASE)
                added_tools.update(m.lower() for m in matches)

        for deletion in deletions:
            for tool_pattern in self.TOOL_PATTERNS:
                matches = re.findall(tool_pattern, deletion, re.IGNORECASE)
                removed_tools.update(m.lower() for m in matches)

        # Find tools that were added but removed elsewhere (corrections)
        for tool in added_tools:
            # Check if mentioned in context of preference
            for addition in additions:
                if tool in addition.lower() and any(
                    kw in addition.lower() for kw in ['use', 'prefer', 'always', 'default']
                ):
                    # This is a tool preference
                    pattern = EditPattern(
                        pattern_type='tool_preference',
                        content=addition.strip(),
                        frequency=1,
                        confidence=0.7,
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        contexts=[f"tool={tool}"]
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_rules(self, additions: List[str]) -> List[EditPattern]:
        """Detect rule additions."""
        patterns = []

        rule_keywords = [
            'must', 'should', 'required', 'always', 'never',
            'mandatory', 'forbidden', 'prohibited'
        ]

        for addition in additions:
            # Check if this looks like a rule
            if any(kw in addition.lower() for kw in rule_keywords):
                # Check if it's in a list format
                if addition.strip().startswith('-') or addition.strip().startswith('*'):
                    pattern = EditPattern(
                        pattern_type='rule',
                        content=addition.strip(),
                        frequency=1,
                        confidence=0.6,
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        contexts=['rule_addition']
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_optimizations(
        self,
        additions: List[str],
        deletions: List[str]
    ) -> List[EditPattern]:
        """Detect token optimization strategies."""
        patterns = []

        # Check if content was moved to progressive disclosure
        if any('/prime' in add.lower() for add in additions):
            # User is manually adding /prime commands
            pattern = EditPattern(
                pattern_type='progressive_disclosure',
                content='User manually added /prime command references',
                frequency=1,
                confidence=0.9,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                contexts=['optimization']
            )
            patterns.append(pattern)

        # Check if examples were removed (common optimization)
        example_removed = False
        for deletion in deletions:
            if '```' in deletion or 'example:' in deletion.lower():
                example_removed = True
                break

        if example_removed and not any('```' in add for add in additions):
            pattern = EditPattern(
                pattern_type='example_removal',
                content='Removed examples for token optimization',
                frequency=1,
                confidence=0.7,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                contexts=['optimization', 'token_saving']
            )
            patterns.append(pattern)

        return patterns

    def _extract_section_headers(self, lines: List[str]) -> List[str]:
        """Extract section headers from lines."""
        headers = []

        for line in lines:
            if line.strip().startswith('##'):
                # Extract section name
                header = line.strip().lstrip('#').strip()
                headers.append(header)

        return headers

    def _extract_preferences(
        self,
        patterns: List[EditPattern]
    ) -> List[Dict[str, str]]:
        """Extract preference dictionaries from patterns."""
        preferences = []

        for pattern in patterns:
            if pattern.pattern_type in ['preference', 'preference_correction', 'tool_preference']:
                # Parse contexts
                pref_dict = {'content': pattern.content, 'type': pattern.pattern_type}

                for context in pattern.contexts:
                    if '=' in context:
                        key, value = context.split('=', 1)
                        pref_dict[key] = value

                preferences.append(pref_dict)

        return preferences

    def _estimate_token_impact(
        self,
        additions: List[str],
        deletions: List[str]
    ) -> int:
        """Estimate token impact of changes."""
        # Simple estimation: 4 chars per token
        added_chars = sum(len(line) for line in additions)
        deleted_chars = sum(len(line) for line in deletions)

        added_tokens = added_chars / 4
        deleted_tokens = deleted_chars / 4

        return int(added_tokens - deleted_tokens)

    async def _learn_patterns(
        self,
        patterns: List[EditPattern],
        project_path: Optional[str]
    ):
        """Learn from detected patterns."""
        for pattern in patterns:
            # Generate pattern key
            pattern_key = self._generate_pattern_key(pattern)

            # Check if we've seen this pattern before
            if pattern_key in self._learned_patterns:
                # Update existing pattern
                existing = self._learned_patterns[pattern_key]
                existing.frequency += 1
                existing.last_seen = datetime.now()

                # Increase confidence with frequency
                # Bayesian update: +20% on success
                existing.confidence = min(0.95, existing.confidence + 0.2)

                self._stats['confidence_improvements'] += 1

                logger.info(
                    f"Pattern reinforced: {pattern_key} "
                    f"(frequency: {existing.frequency}, confidence: {existing.confidence:.2f})"
                )
            else:
                # New pattern
                self._learned_patterns[pattern_key] = pattern
                self._stats['patterns_learned'] += 1

                logger.info(f"New pattern learned: {pattern_key}")

            # Store in memory if available
            if self.memory:
                await self.memory.store(
                    key=f"pattern_{pattern_key}",
                    value=self._learned_patterns[pattern_key].to_dict(),
                    namespace="learned_patterns",
                    metadata={
                        'project_path': project_path,
                        'pattern_type': pattern.pattern_type
                    }
                )

    def _generate_pattern_key(self, pattern: EditPattern) -> str:
        """Generate a unique key for a pattern."""
        # Use content hash + type for uniqueness
        content_normalized = re.sub(r'\s+', ' ', pattern.content.lower()).strip()
        return f"{pattern.pattern_type}:{content_normalized[:100]}"

    async def get_learned_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.5,
        min_frequency: int = 1
    ) -> List[EditPattern]:
        """
        Get learned patterns with filtering.

        Args:
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence threshold
            min_frequency: Minimum frequency threshold

        Returns:
            List of matching patterns
        """
        patterns = []

        for pattern in self._learned_patterns.values():
            # Apply filters
            if pattern_type and pattern.pattern_type != pattern_type:
                continue

            if pattern.confidence < min_confidence:
                continue

            if pattern.frequency < min_frequency:
                continue

            patterns.append(pattern)

        # Sort by confidence * frequency
        patterns.sort(
            key=lambda p: p.confidence * p.frequency,
            reverse=True
        )

        return patterns

    async def auto_apply_patterns(
        self,
        content: str,
        min_confidence: float = 0.8,
        project_path: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        Automatically apply learned patterns to content.

        This is the "stop telling Claude to use uv not pip" solution.

        Args:
            content: Content to apply patterns to
            min_confidence: Minimum confidence for auto-application
            project_path: Optional project path for filtering

        Returns:
            (modified_content, applied_patterns) tuple
        """
        modified_content = content
        applied_patterns = []

        # Get high-confidence patterns
        patterns = await self.get_learned_patterns(
            min_confidence=min_confidence,
            min_frequency=2  # Must have been seen at least twice
        )

        for pattern in patterns:
            if pattern.pattern_type == 'preference_correction':
                # Extract what to prefer and what to avoid
                preferred = None
                avoided = None

                for context in pattern.contexts:
                    if context.startswith('preferred='):
                        preferred = context.split('=', 1)[1]
                    elif context.startswith('avoided='):
                        avoided = context.split('=', 1)[1]

                if preferred and avoided:
                    # Check if content mentions the avoided tool
                    if re.search(rf'\b{re.escape(avoided)}\b', modified_content, re.IGNORECASE):
                        # Check if preference is already stated
                        if not re.search(
                            rf'(?:use|prefer).*{re.escape(preferred)}.*(?:not|instead of).*{re.escape(avoided)}',
                            modified_content,
                            re.IGNORECASE
                        ):
                            # Add preference statement
                            preference_statement = f"- **Tool Preference**: Use {preferred} (not {avoided})\n"

                            # Try to add to tool preferences section
                            if '## Tool Preferences' in modified_content:
                                # Add after the header
                                modified_content = modified_content.replace(
                                    '## Tool Preferences\n',
                                    f'## Tool Preferences\n\n{preference_statement}'
                                )
                                applied_patterns.append(pattern.content)
                                self._stats['auto_applications'] += 1

                                logger.info(f"Auto-applied pattern: {preferred} not {avoided}")

            elif pattern.pattern_type == 'rule':
                # Check if rule already exists
                if pattern.content not in modified_content:
                    # Try to add to appropriate section
                    if '## Essential Rules' in modified_content:
                        modified_content = modified_content.replace(
                            '## Essential Rules\n',
                            f'## Essential Rules\n\n{pattern.content}\n'
                        )
                        applied_patterns.append(pattern.content)
                        self._stats['auto_applications'] += 1

        return modified_content, applied_patterns

    async def suggest_improvements(
        self,
        content: str,
        project_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest improvements based on learned patterns.

        Args:
            content: Content to analyze
            project_path: Optional project path

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Get learned patterns
        patterns = await self.get_learned_patterns(min_confidence=0.6)

        for pattern in patterns:
            # Check if pattern is relevant but not applied
            if pattern.pattern_type == 'preference_correction':
                # Extract tools
                preferred = avoided = None
                for context in pattern.contexts:
                    if context.startswith('preferred='):
                        preferred = context.split('=', 1)[1]
                    elif context.startswith('avoided='):
                        avoided = context.split('=', 1)[1]

                if preferred and avoided:
                    # Check if content uses avoided tool without preference stated
                    uses_avoided = bool(re.search(
                        rf'\b{re.escape(avoided)}\b',
                        content,
                        re.IGNORECASE
                    ))

                    has_preference = bool(re.search(
                        rf'(?:use|prefer).*{re.escape(preferred)}',
                        content,
                        re.IGNORECASE
                    ))

                    if uses_avoided and not has_preference:
                        suggestions.append({
                            'type': 'preference_missing',
                            'pattern': pattern.content,
                            'confidence': pattern.confidence,
                            'suggestion': f"Add preference: Use {preferred} instead of {avoided}",
                            'priority': 'high' if pattern.frequency > 3 else 'medium'
                        })

            elif pattern.pattern_type == 'progressive_disclosure':
                # Suggest sections that could be moved to /prime
                if len(content) > 20000:  # Rough token estimate
                    suggestions.append({
                        'type': 'token_optimization',
                        'pattern': pattern.content,
                        'confidence': pattern.confidence,
                        'suggestion': 'Consider using /prime commands for extended sections',
                        'priority': 'medium'
                    })

        # Sort by priority and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        suggestions.sort(
            key=lambda s: (priority_order.get(s['priority'], 0), s['confidence']),
            reverse=True
        )

        return suggestions

    def get_statistics(self) -> Dict[str, Any]:
        """Get learner statistics."""
        return {
            **self._stats,
            'patterns_in_database': len(self._learned_patterns),
            'high_confidence_patterns': sum(
                1 for p in self._learned_patterns.values() if p.confidence >= 0.8
            ),
            'pattern_types': Counter(
                p.pattern_type for p in self._learned_patterns.values()
            )
        }
