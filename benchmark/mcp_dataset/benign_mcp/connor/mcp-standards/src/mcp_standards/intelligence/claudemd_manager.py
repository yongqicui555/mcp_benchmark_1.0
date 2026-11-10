"""CLAUDE.md Manager - Intelligent management of Claude Code project memory files

Automatically:
1. Generates CLAUDE.md content from learned preferences
2. Updates existing files without breaking manual edits
3. Distinguishes global vs project-specific preferences
4. Promotes patterns from project → global when repeated
5. Provides smart merging and conflict resolution
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import sqlite3


class ClaudeMdManager:
    """Manages CLAUDE.md files based on learned patterns"""

    # Template for CLAUDE.md structure
    GLOBAL_TEMPLATE = """# Claude Code - Global Configuration

This file was auto-generated from learned preferences.
You can edit it manually - the system will preserve your changes.

Last updated: {timestamp}

## Tool Preferences

{tool_preferences}

## Workflow Patterns

{workflow_patterns}

## Quality Standards

{quality_standards}

## Project-Specific Notes

For project-specific settings, create CLAUDE.md in your project root.
"""

    PROJECT_TEMPLATE = """# {project_name} - Project Configuration

Auto-generated from learned project patterns.
Last updated: {timestamp}

## Project Overview

{project_overview}

## Tool Preferences

{tool_preferences}

## Workflow Patterns

{workflow_patterns}

## Quality Gates

{quality_gates}

## Agent Preferences

{agent_preferences}
"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def generate_claudemd_content(
        self,
        project_path: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> str:
        """
        Generate CLAUDE.md content from learned preferences

        Args:
            project_path: If provided, generates project-specific content
            min_confidence: Minimum confidence threshold for inclusion

        Returns:
            Markdown content for CLAUDE.md
        """
        if project_path:
            return self._generate_project_content(project_path, min_confidence)
        else:
            return self._generate_global_content(min_confidence)

    def _generate_global_content(self, min_confidence: float) -> str:
        """Generate global CLAUDE.md content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get high-confidence global preferences
            cursor = conn.execute("""
                SELECT category, preference, confidence, apply_count
                FROM tool_preferences
                WHERE project_specific = FALSE
                  AND confidence >= ?
                ORDER BY category, confidence DESC
            """, (min_confidence,))

            preferences = cursor.fetchall()

        # Group preferences by category
        by_category = {}
        for pref in preferences:
            category = pref["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pref)

        # Build sections - combine all tool-related categories
        tool_prefs = []
        for cat in ["tool-preference", "python-package", "javascript-package", "tool-correction"]:
            tool_prefs.extend(by_category.get(cat, []))

        tool_preferences = self._format_preferences_section(tool_prefs)
        workflow_patterns = self._format_preferences_section(by_category.get("workflow", []))
        quality_standards = self._format_preferences_section(by_category.get("quality", []))

        return self.GLOBAL_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            tool_preferences=tool_preferences or "_No learned preferences yet_",
            workflow_patterns=workflow_patterns or "_No learned workflows yet_",
            quality_standards=quality_standards or "_No learned standards yet_"
        )

    def _generate_project_content(self, project_path: str, min_confidence: float) -> str:
        """Generate project-specific CLAUDE.md content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get project-specific preferences
            cursor = conn.execute("""
                SELECT category, preference, confidence, apply_count
                FROM tool_preferences
                WHERE project_path = ?
                  AND confidence >= ?
                ORDER BY category, confidence DESC
            """, (project_path, min_confidence))

            preferences = cursor.fetchall()

            # Get validation gates for this project
            cursor = conn.execute("""
                SELECT gate_type, check_command, required
                FROM validation_gates
                WHERE project_path = ?
                  AND auto_check = TRUE
            """, (project_path,))

            gates = cursor.fetchall()

        # Group preferences by category
        by_category = {}
        for pref in preferences:
            category = pref["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pref)

        # Format sections
        project_name = Path(project_path).name
        tool_preferences = self._format_preferences_section(by_category.get("tool-preference", []))
        workflow_patterns = self._format_preferences_section(by_category.get("workflow", []))
        quality_gates = self._format_gates_section(gates)
        agent_preferences = self._format_preferences_section(by_category.get("agent", []))

        return self.PROJECT_TEMPLATE.format(
            project_name=project_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            project_overview=f"Path: `{project_path}`",
            tool_preferences=tool_preferences or "_Inherits from global preferences_",
            workflow_patterns=workflow_patterns or "_Inherits from global patterns_",
            quality_gates=quality_gates or "_No project-specific gates_",
            agent_preferences=agent_preferences or "_No agent preferences learned yet_"
        )

    def _format_preferences_section(self, preferences: List[sqlite3.Row]) -> str:
        """Format preferences as markdown list"""
        if not preferences:
            return ""

        lines = []
        for pref in preferences:
            confidence_badge = self._confidence_badge(pref["confidence"])
            apply_count = pref["apply_count"]

            lines.append(
                f"- **{pref['preference']}** {confidence_badge} "
                f"_(applied {apply_count}x)_"
            )

        return "\n".join(lines)

    def _format_gates_section(self, gates: List[sqlite3.Row]) -> str:
        """Format validation gates as markdown checklist"""
        if not gates:
            return ""

        lines = []
        for gate in gates:
            required_mark = "✓ Required" if gate["required"] else "○ Optional"
            command = gate["check_command"] or "_auto-detected_"

            lines.append(
                f"- [ ] **{gate['gate_type']}** {required_mark}\n"
                f"  - Check: `{command}`"
            )

        return "\n".join(lines)

    def _confidence_badge(self, confidence: float) -> str:
        """Generate confidence badge emoji"""
        if confidence >= 0.9:
            return "🟢"  # Very high confidence
        elif confidence >= 0.7:
            return "🟡"  # High confidence
        elif confidence >= 0.5:
            return "🟠"  # Medium confidence
        else:
            return "🔴"  # Low confidence

    def update_claudemd_file(
        self,
        file_path: Path,
        project_path: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> Tuple[bool, str]:
        """
        Update CLAUDE.md file with learned preferences

        Performs smart merging:
        1. Preserves manual edits
        2. Updates auto-generated sections
        3. Handles conflicts gracefully

        Args:
            file_path: Path to CLAUDE.md file
            project_path: Project path for project-specific file
            min_confidence: Minimum confidence for inclusion

        Returns:
            (success, message) tuple
        """
        # Generate new content
        new_content = self.generate_claudemd_content(project_path, min_confidence)

        # Check if file exists
        if not file_path.exists():
            # Create new file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(new_content)
            return (True, f"Created {file_path}")

        # File exists - smart merge
        existing_content = file_path.read_text()

        # Check for manual edits marker
        if "<!-- MANUAL EDITS BELOW -->" in existing_content:
            # Preserve everything after the marker
            manual_section = existing_content.split("<!-- MANUAL EDITS BELOW -->")[1]
            merged_content = new_content + "\n<!-- MANUAL EDITS BELOW -->\n" + manual_section
        else:
            # No manual edits marker - append manual edits warning
            merged_content = (
                new_content +
                "\n<!-- MANUAL EDITS BELOW -->\n"
                "<!-- Your manual edits will be preserved below this line -->\n\n"
                + self._extract_manual_sections(existing_content, new_content)
            )

        # Write merged content
        # Create backup first
        backup_path = file_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
        backup_path.write_text(existing_content)

        file_path.write_text(merged_content)

        return (True, f"Updated {file_path} (backup: {backup_path})")

    def _extract_manual_sections(self, existing: str, new_template: str) -> str:
        """Extract manual edits that aren't in the template"""
        # Split into sections
        existing_sections = self._extract_sections(existing)
        template_sections = self._extract_sections(new_template)

        manual_sections = []

        for section_name, section_content in existing_sections.items():
            # Check if this section was auto-generated or manual
            if section_name not in template_sections:
                # Completely manual section
                manual_sections.append(f"## {section_name}\n\n{section_content}")
            else:
                # Check for manual additions within the section
                template_content = template_sections[section_name]
                if section_content != template_content and "_No learned" not in template_content:
                    # Has manual modifications
                    manual_sections.append(f"## {section_name} (Manual Edits)\n\n{section_content}")

        return "\n\n".join(manual_sections) if manual_sections else ""

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract markdown sections from content"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            # Check for section header (## Section Name)
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def suggest_updates(
        self,
        project_path: Optional[str] = None,
        min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions for CLAUDE.md updates without applying them

        Returns:
            List of suggested updates with metadata
        """
        suggestions = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find preferences not yet in CLAUDE.md
            if project_path:
                where_clause = "project_path = ? AND project_specific = TRUE"
                params = (project_path, min_confidence)
            else:
                where_clause = "project_specific = FALSE"
                params = (min_confidence,)

            cursor = conn.execute(f"""
                SELECT category, preference, confidence, apply_count, learned_from
                FROM tool_preferences
                WHERE {where_clause}
                  AND confidence >= ?
                  AND last_validated IS NULL
                ORDER BY confidence DESC, apply_count DESC
                LIMIT 10
            """, params)

            for row in cursor.fetchall():
                suggestions.append({
                    "category": row["category"],
                    "preference": row["preference"],
                    "confidence": row["confidence"],
                    "apply_count": row["apply_count"],
                    "learned_from": row["learned_from"],
                    "recommended": row["confidence"] >= 0.8
                })

        return suggestions

    def check_for_promotion(self, project_path: str, threshold: int = 3) -> List[Dict[str, Any]]:
        """
        Check if project-specific preferences should be promoted to global

        Args:
            project_path: Project to check
            threshold: Number of projects with same preference needed

        Returns:
            List of preferences ready for promotion
        """
        promotable = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find project-specific preferences
            cursor = conn.execute("""
                SELECT category, preference, COUNT(DISTINCT project_path) as project_count,
                       AVG(confidence) as avg_confidence
                FROM tool_preferences
                WHERE project_specific = TRUE
                GROUP BY category, preference
                HAVING project_count >= ?
            """, (threshold,))

            for row in cursor.fetchall():
                promotable.append({
                    "category": row["category"],
                    "preference": row["preference"],
                    "project_count": row["project_count"],
                    "avg_confidence": row["avg_confidence"]
                })

        return promotable

    def promote_to_global(self, category: str, preference: str) -> bool:
        """
        Promote a project-specific preference to global

        Args:
            category: Preference category
            preference: Preference text

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if global version already exists
                cursor = conn.execute("""
                    SELECT id FROM tool_preferences
                    WHERE category = ?
                      AND preference = ?
                      AND project_specific = FALSE
                """, (category, preference))

                if cursor.fetchone():
                    # Already exists globally
                    return False

                # Find all project-specific instances
                cursor = conn.execute("""
                    SELECT AVG(confidence) as avg_conf, SUM(apply_count) as total_applies
                    FROM tool_preferences
                    WHERE category = ?
                      AND preference = ?
                      AND project_specific = TRUE
                """, (category, preference))

                row = cursor.fetchone()

                if row:
                    # Create global preference
                    conn.execute("""
                        INSERT INTO tool_preferences (
                            category, context, preference, confidence, apply_count,
                            project_specific, created_at
                        ) VALUES (?, ?, ?, ?, ?, FALSE, ?)
                    """, (
                        category,
                        f"Promoted from {row['total_applies']} project applications",
                        preference,
                        row['avg_conf'],
                        row['total_applies'],
                        datetime.now().isoformat()
                    ))

                    conn.commit()
                    return True

            return False

        except Exception as e:
            print(f"Error promoting preference: {e}")
            return False
