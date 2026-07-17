"""Pattern Extractor - Detects and learns from repeated patterns

Identifies learning opportunities from tool executions:
1. Repeated corrections (user says "use X not Y")
2. Workflow patterns (always run tests after code changes)
3. Tool preferences (prefer certain tools for tasks)
4. Agent performance (which agents work well for what)
5. Project conventions (code style, naming, structure)
"""

import json
import sqlite3
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta


class PatternExtractor:
    """Extracts learning patterns from tool executions"""

    # Correction indicator phrases
    CORRECTION_PHRASES = [
        r"actually\s+(?:use|do|need|should)",
        r"instead\s+(?:of|use)",
        r"use\s+(\w+)\s+not\s+(\w+)",
        r"don't\s+use\s+(\w+)",
        r"should\s+(?:use|be|have)",
        r"correct\s+(?:way|approach|method)",
        r"(?:fix|change|update)\s+(?:to|from)",
    ]

    # Tool preference patterns
    TOOL_PATTERNS = {
        "python-package": [
            (r"use\s+uv\s+not\s+pip", "use uv for Python package management"),
            (r"use\s+poetry\s+not\s+pip", "use poetry for Python package management"),
            (r"use\s+conda", "use conda for Python environment management"),
        ],
        "testing": [
            (r"always\s+run\s+(?:tests|pytest)", "always run tests after code changes"),
            (r"run\s+tests\s+before", "run tests before committing"),
        ],
        "git": [
            (r"always\s+(?:use|create)\s+(?:feature\s+)?branch", "always use feature branches"),
            (r"commit\s+message\s+format", "follow commit message format"),
        ],
        "docs": [
            (r"update\s+readme", "update README after feature changes"),
            (r"update\s+docs", "update documentation when adding features"),
        ],
    }

    # Rate limiting settings
    MAX_PATTERNS_PER_MINUTE = 100
    RATE_LIMIT_WINDOW_SECONDS = 60

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_tables()
        # Rate limiting tracker: {timestamp: count}
        self._pattern_timestamps: List[datetime] = []

    @staticmethod
    def _sanitize_description(text: str, max_length: int = 200) -> str:
        """
        Sanitize pattern descriptions to prevent log injection and control characters

        Args:
            text: Raw text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text safe for storage and display
        """
        if not text:
            return ""

        # Remove control characters and non-printable characters
        sanitized = "".join(char for char in text if char.isprintable() or char in ['\n', '\t'])

        # Remove potential log injection sequences
        sanitized = sanitized.replace('\r', '').replace('\x00', '')

        # Allow alphanumeric, spaces, and common punctuation
        # Keep: letters, numbers, spaces, -, _, →, ., comma, colon, quotes
        allowed_pattern = r'[a-zA-Z0-9\s\-_→.,:\'"\/()]+$'
        if not re.match(allowed_pattern, sanitized):
            # If pattern doesn't match, extract only allowed chars
            sanitized = "".join(char for char in sanitized if re.match(r'[a-zA-Z0-9\s\-_→.,:\'"\/()]', char))

        # Truncate to max length
        sanitized = sanitized[:max_length].strip()

        return sanitized

    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit is exceeded

        Returns:
            True if within rate limit, False if exceeded
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.RATE_LIMIT_WINDOW_SECONDS)

        # Remove old timestamps outside the window
        self._pattern_timestamps = [
            ts for ts in self._pattern_timestamps
            if ts > cutoff
        ]

        # Check if we're over the limit
        if len(self._pattern_timestamps) >= self.MAX_PATTERNS_PER_MINUTE:
            return False

        # Record this attempt
        self._pattern_timestamps.append(now)
        return True

    def _ensure_tables(self):
        """Ensure pattern tracking tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Pattern frequency tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pattern_frequency (
                    id INTEGER PRIMARY KEY,
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

            # Tool preferences (learned rules)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_preferences (
                    id INTEGER PRIMARY KEY,
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

            conn.commit()

    def extract_patterns(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        project_path: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Extract learning patterns from tool execution

        Returns:
            List of detected patterns with metadata
        """
        # Security: Rate limiting check
        if not self._check_rate_limit():
            # Rate limit exceeded - return empty list and log warning
            print(f"Warning: Pattern extraction rate limit exceeded ({self.MAX_PATTERNS_PER_MINUTE}/min)")
            return []

        patterns = []

        # 1. Check for correction patterns
        correction_patterns = self._detect_corrections(tool_name, args, result)
        patterns.extend(correction_patterns)

        # 2. Check for workflow patterns
        workflow_patterns = self._detect_workflow_patterns(tool_name, args, project_path)
        patterns.extend(workflow_patterns)

        # 3. Check for tool preferences
        tool_prefs = self._detect_tool_preferences(tool_name, args, result)
        patterns.extend(tool_prefs)

        # 4. Update frequency tracking for all patterns
        for pattern in patterns:
            self._update_pattern_frequency(pattern, project_path)

        # 5. Check if any patterns should be promoted to preferences
        self._check_promotion_threshold()

        return patterns

    def _detect_corrections(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> List[Dict[str, Any]]:
        """Detect correction patterns in tool execution"""
        patterns = []
        combined_text = f"{args} {result}".lower()

        # Check for correction phrases
        for phrase_pattern in self.CORRECTION_PHRASES:
            matches = re.finditer(phrase_pattern, combined_text, re.IGNORECASE)
            for match in matches:
                # Extract the correction
                correction_text = match.group(0)

                # Try to extract tool names (e.g., "use uv not pip")
                tool_match = re.search(r"use\s+(\w+)\s+not\s+(\w+)", correction_text)
                if tool_match:
                    preferred_tool = tool_match.group(1)
                    avoided_tool = tool_match.group(2)

                    # Sanitize tool names and description
                    preferred_clean = self._sanitize_description(preferred_tool, max_length=50)
                    avoided_clean = self._sanitize_description(avoided_tool, max_length=50)
                    description = self._sanitize_description(
                        f"use {preferred_tool} instead of {avoided_tool}",
                        max_length=200
                    )

                    patterns.append({
                        "type": "correction",
                        "pattern_key": f"correction:{avoided_clean}→{preferred_clean}",
                        "tool_name": tool_name,
                        "category": self._categorize_tool(preferred_clean, avoided_clean),
                        "description": description,
                        "preferred": preferred_clean,
                        "avoided": avoided_clean,
                        "full_text": self._sanitize_description(correction_text, max_length=500)
                    })

        return patterns

    def _detect_workflow_patterns(
        self,
        tool_name: str,
        args: Dict[str, Any],
        project_path: str
    ) -> List[Dict[str, Any]]:
        """Detect workflow patterns (e.g., always run tests after edits)"""
        patterns = []

        # Track sequential tool patterns (e.g., Edit followed by Bash(pytest))
        recent_tools = self._get_recent_tools(minutes=5, project_path=project_path)

        # Pattern: Edit/Write followed by test command
        if tool_name.startswith("Bash") and "test" in str(args).lower():
            # Check if preceded by Edit/Write
            if any(t.startswith(("Edit", "Write")) for t in recent_tools):
                patterns.append({
                    "type": "workflow",
                    "pattern_key": "workflow:code-change→test",
                    "tool_name": tool_name,
                    "category": "testing",
                    "description": "run tests after code changes",
                    "sequence": ["Edit/Write", "Test"]
                })

        # Pattern: Feature implementation followed by docs update
        file_path = args.get("file_path", "") if isinstance(args, dict) else ""
        if tool_name in ["Edit", "Write"] and "README" in str(file_path):
            if any("src" in str(t) or "lib" in str(t) for t in recent_tools):
                patterns.append({
                    "type": "workflow",
                    "pattern_key": "workflow:feature→docs",
                    "tool_name": tool_name,
                    "category": "documentation",
                    "description": "update docs after feature changes",
                    "sequence": ["Code Change", "Docs Update"]
                })

        return patterns

    def _detect_tool_preferences(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any
    ) -> List[Dict[str, Any]]:
        """Detect tool preference patterns"""
        patterns = []

        # Check command args for known preference patterns
        if tool_name.startswith("Bash"):
            command = args.get("command", "")

            for category, pattern_list in self.TOOL_PATTERNS.items():
                for pattern_regex, description in pattern_list:
                    if re.search(pattern_regex, command, re.IGNORECASE):
                        patterns.append({
                            "type": "tool_preference",
                            "pattern_key": f"pref:{category}:{pattern_regex}",
                            "tool_name": tool_name,
                            "category": category,
                            "description": description,
                            "command": command
                        })

        return patterns

    def _update_pattern_frequency(
        self,
        pattern: Dict[str, Any],
        project_path: str
    ) -> None:
        """Update frequency tracking for a pattern"""
        pattern_key = pattern["pattern_key"]

        with sqlite3.connect(self.db_path) as conn:
            # Check if pattern exists
            cursor = conn.execute("""
                SELECT id, occurrence_count FROM pattern_frequency
                WHERE pattern_key = ?
            """, (pattern_key,))

            row = cursor.fetchone()

            if row:
                # Increment existing pattern
                pattern_id, count = row
                new_count = count + 1

                # Calculate confidence (maxes at 1.0 after 10 occurrences)
                confidence = min(1.0, new_count / 10)

                conn.execute("""
                    UPDATE pattern_frequency
                    SET occurrence_count = ?,
                        last_seen = ?,
                        confidence = ?,
                        pattern_description = ?
                    WHERE id = ?
                """, (
                    new_count,
                    datetime.now().isoformat(),
                    confidence,
                    pattern.get("description", ""),
                    pattern_id
                ))
            else:
                # Insert new pattern
                conn.execute("""
                    INSERT INTO pattern_frequency (
                        pattern_key,
                        tool_name,
                        pattern_type,
                        pattern_description,
                        occurrence_count,
                        confidence,
                        examples
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern_key,
                    pattern["tool_name"],
                    pattern["type"],
                    pattern.get("description", ""),
                    1,
                    0.1,
                    json.dumps([pattern])
                ))

            conn.commit()

    def _check_promotion_threshold(self) -> None:
        """Check if any patterns should be promoted to preferences"""
        PROMOTION_THRESHOLD = 3  # Promote after 3 occurrences

        with sqlite3.connect(self.db_path) as conn:
            # Find patterns ready for promotion
            cursor = conn.execute("""
                SELECT id, pattern_key, tool_name, pattern_type, pattern_description,
                       occurrence_count, confidence, examples
                FROM pattern_frequency
                WHERE occurrence_count >= ?
                  AND promoted_to_preference = FALSE
            """, (PROMOTION_THRESHOLD,))

            patterns_to_promote = cursor.fetchall()

            for pattern_data in patterns_to_promote:
                (pattern_id, pattern_key, tool_name, pattern_type,
                 description, count, confidence, examples_json) = pattern_data

                # Create preference entry
                category = self._extract_category_from_pattern(pattern_key, pattern_type)

                conn.execute("""
                    INSERT INTO tool_preferences (
                        category,
                        context,
                        preference,
                        confidence,
                        examples,
                        learned_from,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    category,
                    f"Learned from {count} occurrences",
                    description,
                    confidence,
                    examples_json,
                    f"pattern:{pattern_id}",
                    datetime.now().isoformat()
                ))

                # Mark as promoted
                conn.execute("""
                    UPDATE pattern_frequency
                    SET promoted_to_preference = TRUE
                    WHERE id = ?
                """, (pattern_id,))

                # Audit the promotion
                conn.execute("""
                    INSERT INTO audit_log (action, target_type, target_path, details, success)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    "promote_pattern",
                    "preference",
                    pattern_key,
                    f"Promoted to {category} after {count} occurrences (confidence: {confidence:.2f})",
                    True
                ))

            conn.commit()

    def _get_recent_tools(self, minutes: int = 5, project_path: str = "") -> List[str]:
        """Get list of recently executed tools"""
        cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Use tool_logs table (created by autologger)
                cursor = conn.execute("""
                    SELECT tool_name FROM tool_logs
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (cutoff,))

                return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []

    def _categorize_tool(self, preferred: str, avoided: str) -> str:
        """Categorize a tool preference"""
        tool_categories = {
            ("uv", "pip"): "python-package",
            ("poetry", "pip"): "python-package",
            ("npm", "yarn"): "javascript-package",
            ("pnpm", "npm"): "javascript-package",
            ("pytest", "unittest"): "testing",
            ("vitest", "jest"): "testing",
        }

        key = (preferred.lower(), avoided.lower())
        return tool_categories.get(key, "tool-preference")

    def _extract_category_from_pattern(self, pattern_key: str, pattern_type: str) -> str:
        """Extract category from pattern key"""
        # Pattern keys are like "pref:category:..." or "workflow:action"
        parts = pattern_key.split(":")

        if len(parts) >= 2:
            if pattern_type == "tool_preference" and parts[0] == "pref":
                return parts[1]
            elif pattern_type == "workflow":
                return parts[1].split("→")[0] if "→" in parts[1] else "workflow"
            elif pattern_type == "correction":
                return "tool-correction"

        return "general"

    def get_learned_preferences(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get all learned preferences, optionally filtered"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if category:
                cursor = conn.execute("""
                    SELECT * FROM tool_preferences
                    WHERE category = ? AND confidence >= ?
                    ORDER BY confidence DESC, apply_count DESC
                """, (category, min_confidence))
            else:
                cursor = conn.execute("""
                    SELECT * FROM tool_preferences
                    WHERE confidence >= ?
                    ORDER BY confidence DESC, apply_count DESC
                """, (min_confidence,))

            return [dict(row) for row in cursor.fetchall()]
