"""Claude Memory MCP Server

Simple knowledge storage using Claude Code SDK - no external dependencies
"""
import asyncio
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from .autolog import get_autologger, autolog_tool
from .export import export_to_markdown
from .standards import ConfigParser, StandardsExtractor, InstructionGenerator

# Import pattern learning components
from .hooks.pattern_extractor import PatternExtractor
from .intelligence.claudemd_manager import ClaudeMdManager


class ClaudeMemoryMCP:
    """Simple Claude-native knowledge storage"""

    def __init__(self, db_path: Optional[str] = None):
        self.server = Server("mcp-standards")
        # Use centralized location
        if db_path is None:
            self.db_path = Path.home() / ".mcp-standards" / "knowledge.db"
        else:
            self.db_path = Path(db_path)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize autologger with same DB
        self.autologger = get_autologger(self.db_path)

        # Initialize pattern learning components
        self.pattern_extractor = PatternExtractor(self.db_path)
        self.claudemd_manager = ClaudeMdManager(self.db_path)

        self._setup_database()
        self._setup_handlers()

    def _setup_database(self):
        """Setup SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    args TEXT,
                    result TEXT,
                    significance_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create search index for content
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS episodes_search USING fts5(
                    name, content, source, content=episodes
                )
            """)

            # Audit log table for tracking modifications
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_path TEXT,
                    details TEXT,
                    user_context TEXT,
                    success BOOLEAN DEFAULT TRUE
                )
            """)

            conn.commit()

    def _audit_log(
        self,
        action: str,
        target_type: str,
        target_path: Optional[str] = None,
        details: Optional[str] = None,
        success: bool = True
    ) -> None:
        """
        Log audit trail for sensitive operations

        Args:
            action: Action performed (e.g., "update_claudemd", "promote_pattern")
            target_type: Type of target (e.g., "file", "preference", "pattern")
            target_path: Path or identifier of target
            details: Additional details about the action
            success: Whether the action succeeded
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO audit_log (action, target_type, target_path, details, success)
                    VALUES (?, ?, ?, ?, ?)
                """, (action, target_type, target_path, details, success))
                conn.commit()
        except Exception as e:
            # Don't fail the operation if audit logging fails
            print(f"Warning: Audit logging failed: {e}")

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="add_episode",
                    description="Add knowledge episode to memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Episode name"},
                            "content": {"type": "string", "description": "Episode content"},
                            "source": {"type": "string", "description": "Source of episode", "default": "user"},
                        },
                        "required": ["name", "content"],
                    },
                ),
                Tool(
                    name="search_episodes",
                    description="Search knowledge episodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results", "default": 10},
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="list_recent",
                    description="List recent episodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Max results", "default": 10},
                        },
                    },
                ),
                Tool(
                    name="log_tool_execution",
                    description="Log tool execution for learning",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "args": {"type": "object"},
                            "result": {"type": "object"},
                        },
                        "required": ["tool_name", "args", "result"],
                    },
                ),
                Tool(
                    name="export_to_markdown",
                    description="Export knowledge base to markdown files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "export_path": {"type": "string", "description": "Path to export to (optional)"},
                        },
                    },
                ),
                Tool(
                    name="generate_ai_standards",
                    description="Auto-generate AI assistant instruction files (CLAUDE.md, .github/copilot-instructions.md, .cursor/rules/standards.mdc) from existing project config files (.editorconfig, .prettierrc, ESLint, pyproject.toml, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to project root (default: current directory)"},
                            "formats": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["claude", "copilot", "cursor"]},
                                "description": "Which instruction formats to generate (default: all)",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_learned_preferences",
                    description="Get all learned preferences with confidence scores (automatically learned from corrections)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "Filter by category (optional)"},
                            "min_confidence": {"type": "number", "description": "Minimum confidence threshold", "default": 0.7},
                        },
                    },
                ),
                Tool(
                    name="suggest_claudemd_update",
                    description="Get suggestions for CLAUDE.md updates based on learned patterns (does not apply them)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Project path for project-specific suggestions (optional)"},
                            "min_confidence": {"type": "number", "description": "Minimum confidence threshold", "default": 0.7},
                        },
                    },
                ),
                Tool(
                    name="update_claudemd",
                    description="Update CLAUDE.md file with learned preferences (creates backup first)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to CLAUDE.md file"},
                            "project_path": {"type": "string", "description": "Project path for project-specific content (optional)"},
                            "min_confidence": {"type": "number", "description": "Minimum confidence threshold", "default": 0.7},
                        },
                        "required": ["file_path"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if name == "add_episode":
                result = await self._add_episode(
                    arguments["name"],
                    arguments["content"],
                    arguments.get("source", "user"),
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "search_episodes":
                results = await self._search_episodes(
                    arguments["query"], 
                    arguments.get("limit", 10)
                )
                return [TextContent(type="text", text=json.dumps(results))]

            elif name == "list_recent":
                results = await self._list_recent(arguments.get("limit", 10))
                return [TextContent(type="text", text=json.dumps(results))]

            elif name == "log_tool_execution":
                result = await self._log_tool_execution(
                    arguments["tool_name"], 
                    arguments["args"], 
                    arguments["result"]
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "export_to_markdown":
                result = await self._export_to_markdown(
                    arguments.get("export_path")
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "generate_ai_standards":
                result = await self._generate_ai_standards(
                    arguments.get("project_path", "."),
                    arguments.get("formats")
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "get_learned_preferences":
                result = await self._get_learned_preferences(
                    arguments.get("category"),
                    arguments.get("min_confidence", 0.7)
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "suggest_claudemd_update":
                result = await self._suggest_claudemd_update(
                    arguments.get("project_path"),
                    arguments.get("min_confidence", 0.7)
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "update_claudemd":
                result = await self._update_claudemd(
                    arguments["file_path"],
                    arguments.get("project_path"),
                    arguments.get("min_confidence", 0.7)
                )
                return [TextContent(type="text", text=json.dumps(result))]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _add_episode(self, name: str, content: str, source: str = "user") -> Dict[str, Any]:
        """Add episode to memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO episodes (name, content, source) VALUES (?, ?, ?)",
                    (name, content, source)
                )
                episode_id = cursor.lastrowid
                
                # Update search index
                conn.execute(
                    "INSERT INTO episodes_search (rowid, name, content, source) VALUES (?, ?, ?, ?)",
                    (episode_id, name, content, source)
                )
                
                conn.commit()
                
                return {
                    "success": True,
                    "id": episode_id,
                    "message": f"Episode '{name}' added successfully"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_episodes(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search episodes using FTS"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Use FTS search if available, fallback to LIKE
                try:
                    cursor = conn.execute("""
                        SELECT e.id, e.name, e.content, e.source, e.timestamp,
                               rank
                        FROM episodes_search 
                        JOIN episodes e ON episodes_search.rowid = e.id
                        WHERE episodes_search MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """, (query, limit))
                except sqlite3.OperationalError:
                    # Fallback to simple search
                    cursor = conn.execute("""
                        SELECT id, name, content, source, timestamp
                        FROM episodes 
                        WHERE name LIKE ? OR content LIKE ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (f"%{query}%", f"%{query}%", limit))
                
                episodes = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "success": True,
                    "query": query,
                    "results": episodes,
                    "count": len(episodes)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _list_recent(self, limit: int = 10) -> Dict[str, Any]:
        """List recent episodes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, name, content, source, timestamp
                    FROM episodes 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                episodes = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "success": True,
                    "results": episodes,
                    "count": len(episodes)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _log_tool_execution(self, tool_name: str, args: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Log tool execution for learning"""
        try:
            # ALWAYS extract patterns first (regardless of significance)
            # Pattern learning happens even for low-significance events if they contain corrections
            patterns = self.pattern_extractor.extract_patterns(
                tool_name,
                args,
                result,
                project_path=args.get("project_path", "") if isinstance(args, dict) else ""
            )

            # Then use autologger for high-significance events
            log_id = self.autologger.log_tool_execution(tool_name, args, result)

            if log_id is None:
                # Low significance for logging, but may have detected patterns
                return {
                    "success": True,
                    "skipped_logging": True,
                    "reason": "Low significance for full logging",
                    "patterns_detected": len(patterns),
                    "patterns": [p.get("description", p.get("pattern_key")) for p in patterns] if patterns else []
                }

            return {
                "success": True,
                "logged": True,
                "log_id": log_id,
                "patterns_detected": len(patterns),
                "patterns": [p.get("description", p.get("pattern_key")) for p in patterns] if patterns else []
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_significance(self, tool_name: str, args: Dict[str, Any], result: Any) -> float:
        """Calculate significance score for tool execution"""
        score = 0.0
        
        # Base score by tool type
        tool_scores = {
            "github": 0.7,
            "notion": 0.6,
            "file": 0.5,
            "bash": 0.4,
            "search": 0.3,
        }
        
        for prefix, base_score in tool_scores.items():
            if tool_name.lower().startswith(prefix):
                score = base_score
                break
        else:
            score = 0.2  # Default
        
        # Boost for create/modify operations
        if any(word in tool_name.lower() for word in ["create", "edit", "update", "commit"]):
            score += 0.3
        
        # Boost for significant file types
        if "args" in args:
            file_path = str(args.get("file_path", ""))
            important_files = ["claude.md", "package.json", "dockerfile", "readme"]
            if any(important in file_path.lower() for important in important_files):
                score += 0.2
        
        return min(score, 1.0)
    
    async def _export_to_markdown(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """Export knowledge base to markdown"""
        try:
            if export_path:
                path = Path(export_path)
            else:
                path = None
                
            export_location = export_to_markdown(self.db_path, path)
            
            return {
                "success": True,
                "exported_to": str(export_location),
                "message": f"Knowledge base exported to {export_location}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_ai_standards(
        self, project_path: str = ".", formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate AI assistant instruction files from project config files."""
        try:
            project_path_obj = Path(project_path).resolve()

            if not project_path_obj.exists():
                return {"success": False, "error": f"Project path not found: {project_path}"}

            # Parse config files
            config_parser = ConfigParser(str(project_path_obj))
            standards = config_parser.parse_all()

            # Extract project conventions
            standards_extractor = StandardsExtractor(str(project_path_obj))
            conventions = standards_extractor.extract_all()

            # Generate instruction files
            instruction_generator = InstructionGenerator(standards, conventions)
            generated_files = instruction_generator.generate_all(project_path_obj, formats)

            # Store in memory for future reference
            summary = self._create_standards_summary(standards, conventions, generated_files)
            await self._add_episode(
                name=f"AI Standards Generated - {project_path_obj.name}",
                content=summary,
                source="generate_ai_standards",
            )

            return {
                "success": True,
                "generated_files": generated_files,
                "standards_found": {
                    "formatting_rules": len(standards.get("formatting", {})),
                    "project_type": conventions.get("project_type"),
                    "package_manager": conventions.get("package_manager"),
                    "test_framework": conventions.get("test_framework"),
                    "conventions_count": len(conventions.get("conventions", [])),
                },
                "message": f"Generated {len(generated_files)} instruction file(s)",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_standards_summary(
        self, standards: Dict[str, Any], conventions: Dict[str, Any], generated_files: Dict[str, str]
    ) -> str:
        """Create a human-readable summary of extracted standards."""
        lines = ["# Project Coding Standards Summary", ""]

        # Project info
        if conventions.get("project_type"):
            lines.append(f"**Project Type**: {conventions['project_type']}")
        if conventions.get("package_manager"):
            lines.append(f"**Package Manager**: {conventions['package_manager']}")
        if conventions.get("test_framework"):
            lines.append(f"**Test Framework**: {conventions['test_framework']}")
        lines.append("")

        # Formatting rules
        if standards.get("formatting"):
            lines.append("## Formatting Rules")
            for key, data in standards["formatting"].items():
                value = data["value"]
                source = data["source"]
                lines.append(f"- {key}: {value} (from {source})")
            lines.append("")

        # Generated files
        lines.append("## Generated Files")
        for format_name, file_path in generated_files.items():
            lines.append(f"- {format_name}: {file_path}")
        lines.append("")

        return "\n".join(lines)

    async def _get_learned_preferences(
        self, category: Optional[str] = None, min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """Get learned preferences with confidence scores"""
        try:
            preferences = self.pattern_extractor.get_learned_preferences(
                category=category,
                min_confidence=min_confidence
            )

            return {
                "success": True,
                "preferences": preferences,
                "count": len(preferences),
                "category": category or "all"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _suggest_claudemd_update(
        self, project_path: Optional[str] = None, min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """Get suggestions for CLAUDE.md updates"""
        try:
            suggestions = self.claudemd_manager.suggest_updates(
                project_path=project_path,
                min_confidence=min_confidence
            )

            return {
                "success": True,
                "suggestions": suggestions,
                "count": len(suggestions),
                "project_path": project_path or "global",
                "message": f"Found {len(suggestions)} suggestion(s) for CLAUDE.md update"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _update_claudemd(
        self, file_path: str, project_path: Optional[str] = None, min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """Update CLAUDE.md file with learned preferences"""
        try:
            file_path_obj = Path(file_path).resolve()

            # Security: Explicit path whitelist
            allowed_dirs = [
                Path.cwd(),  # Current working directory
                Path.home() / ".claude",  # Global Claude config
                Path.home(),  # User home (for any project)
            ]

            # Check if path is within allowed directories
            is_allowed = any(
                file_path_obj.is_relative_to(allowed_dir)
                for allowed_dir in allowed_dirs
            )

            if not is_allowed:
                # Audit failed attempt
                self._audit_log(
                    action="update_claudemd",
                    target_type="file",
                    target_path=str(file_path_obj),
                    details="Path not in whitelist",
                    success=False
                )
                return {
                    "success": False,
                    "error": f"Path not in allowed directories. File must be in: {', '.join(str(d) for d in allowed_dirs)}"
                }

            # Additional check: Only allow CLAUDE.md or .claude.md files
            allowed_names = ["CLAUDE.md", "CLAUDE.local.md", ".claude.md"]
            if file_path_obj.name not in allowed_names:
                # Audit failed attempt
                self._audit_log(
                    action="update_claudemd",
                    target_type="file",
                    target_path=str(file_path_obj),
                    details=f"Invalid filename: {file_path_obj.name}",
                    success=False
                )
                return {
                    "success": False,
                    "error": f"Only {', '.join(allowed_names)} files can be updated. Got: {file_path_obj.name}"
                }

            # Update the file
            success, message = self.claudemd_manager.update_claudemd_file(
                file_path_obj,
                project_path=project_path,
                min_confidence=min_confidence
            )

            # Audit the update attempt
            self._audit_log(
                action="update_claudemd",
                target_type="file",
                target_path=str(file_path_obj),
                details=f"min_confidence={min_confidence}, project_path={project_path or 'global'}",
                success=success
            )

            if success:
                # Store in memory that we updated CLAUDE.md
                await self._add_episode(
                    name=f"CLAUDE.md Updated - {file_path_obj.name}",
                    content=f"Updated {file_path} with learned preferences (min confidence: {min_confidence})",
                    source="claudemd_update"
                )

            return {
                "success": success,
                "message": message,
                "file_path": str(file_path_obj),
                "project_path": project_path or "global"
            }
        except Exception as e:
            # Audit exception
            self._audit_log(
                action="update_claudemd",
                target_type="file",
                target_path=file_path,
                details=f"Exception: {str(e)}",
                success=False
            )
            return {"success": False, "error": str(e)}


async def main():
    """Run the MCP server"""
    # Create memory server
    memory_server = ClaudeMemoryMCP()
    
    print("✓ Claude Memory MCP Server initialized")
    
    # Run MCP server
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await memory_server.server.run(
            read_stream,
            write_stream,
            memory_server.server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())