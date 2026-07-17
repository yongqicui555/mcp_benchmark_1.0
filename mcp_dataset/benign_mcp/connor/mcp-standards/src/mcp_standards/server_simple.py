"""
MCP Standards - Simple Personal Memory Server

Zero-config automatic preference learning with AgentDB.
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

# Import AgentDB integration
from .agentdb_client import AgentDBClient
from .hooks.auto_memory import AutoMemoryHook


class SimpleMemoryMCP:
    """
    Simple personal memory MCP server.

    Features:
    - Auto-detects corrections (zero manual calls)
    - Semantic memory via AgentDB
    - Config file parsing (minimal CLAUDE.md)
    - Personal knowledge graph
    """

    def __init__(self, db_path: Optional[str] = None):
        self.server = Server("mcp-standards-simple")

        # Use centralized location
        if db_path is None:
            self.db_path = Path.home() / ".mcp-standards" / "knowledge.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize AgentDB client
        self.agentdb = AgentDBClient()

        # Initialize auto-memory hook
        self.auto_memory = AutoMemoryHook(self.agentdb)

        # Initialize autologger (existing)
        self.autologger = get_autologger(self.db_path)

        # Setup database and handlers
        self._setup_database()
        self._setup_handlers()

    def _setup_database(self):
        """Setup SQLite database (keep for legacy/fallback)"""
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

            conn.commit()

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                # Personal Memory Tools (NEW - AgentDB)
                Tool(
                    name="remember",
                    description=(
                        "Store user preferences, corrections, and workflow rules in semantic memory. "
                        "Use when user explicitly shares preferences or corrects your suggestions. "
                        "**Trigger phrases**: 'remember', 'I prefer', 'always use', 'never use', "
                        "'my workflow', 'instead of', 'not X, use Y'. "
                        "**Examples**: 'Remember: use uv not pip', 'I prefer conventional commits', "
                        "'Always run tests before committing', 'Use Docker Compose v2 only'. "
                        "**Categories**: python (pip/uv/poetry/conda), git (commit style, branch naming), "
                        "docker (commands, compose versions), general (any dev preferences)."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "User's preference or correction (e.g., 'use uv not pip', 'prefer async/await over callbacks')"
                            },
                            "category": {
                                "type": "string",
                                "description": "Category: python, git, docker, or general",
                                "default": "general"
                            },
                        },
                        "required": ["content"],
                    },
                ),
                Tool(
                    name="recall",
                    description=(
                        "Search user's stored preferences using semantic search. "
                        "**IMPORTANT: Use this BEFORE making any tool/command recommendations.** "
                        "Check if user has preferences for: Python package managers (pip/uv/poetry/conda), "
                        "Git workflows (commit styles, branch naming, merge vs rebase), "
                        "Docker commands (compose versions, container preferences), "
                        "or general development patterns. "
                        "**Always use when**: suggesting a package manager, recommending git commands, "
                        "proposing Docker setup, choosing between tool alternatives, or making workflow suggestions. "
                        "**Query examples**: 'python package manager', 'git commit style', 'docker compose preference'."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query (e.g., 'python package manager', 'git workflow preferences')"
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional filter: python, git, docker, or general"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return (default: 5)",
                                "default": 5
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="list_categories",
                    description="List all memory categories",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="memory_stats",
                    description="Get memory statistics (AgentDB + SQLite)",
                    inputSchema={"type": "object", "properties": {}},
                ),

                # Config Standards (KEEP - works well)
                Tool(
                    name="generate_ai_standards",
                    description="Auto-generate minimal CLAUDE.md from project config files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Project root path", "default": "."},
                            "formats": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["claude", "copilot", "cursor"]},
                                "description": "Which formats to generate",
                            },
                        },
                    },
                ),

                # Legacy Tools (KEEP for backward compatibility)
                Tool(
                    name="add_episode",
                    description="Add knowledge episode (legacy - use 'remember' instead)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "content": {"type": "string"},
                            "source": {"type": "string", "default": "user"},
                        },
                        "required": ["name", "content"],
                    },
                ),
                Tool(
                    name="search_episodes",
                    description="Search episodes (legacy - use 'recall' instead)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["query"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""

            # === NEW AGENTDB TOOLS ===

            if name == "remember":
                result = await self._remember(
                    arguments["content"],
                    arguments.get("category", "general")
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "recall":
                results = await self._recall(
                    arguments["query"],
                    arguments.get("category"),
                    arguments.get("top_k", 5)
                )
                return [TextContent(type="text", text=json.dumps(results))]

            elif name == "list_categories":
                categories = await self.agentdb.get_all_categories()
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "categories": categories,
                    "count": len(categories)
                }))]

            elif name == "memory_stats":
                agentdb_stats = await self.agentdb.get_stats()
                auto_memory_stats = self.auto_memory.get_stats()

                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "agentdb": agentdb_stats,
                    "auto_detection": auto_memory_stats
                }))]

            # === CONFIG STANDARDS (KEEP) ===

            elif name == "generate_ai_standards":
                result = await self._generate_ai_standards(
                    arguments.get("project_path", "."),
                    arguments.get("formats")
                )
                return [TextContent(type="text", text=json.dumps(result))]

            # === LEGACY TOOLS (KEEP) ===

            elif name == "add_episode":
                # Redirect to AgentDB
                result = await self._remember(
                    arguments["content"],
                    category="general"
                )
                return [TextContent(type="text", text=json.dumps(result))]

            elif name == "search_episodes":
                # Redirect to AgentDB
                results = await self._recall(
                    arguments["query"],
                    category=None,
                    top_k=arguments.get("limit", 10)
                )
                return [TextContent(type="text", text=json.dumps(results))]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    # === NEW AGENTDB METHODS ===

    async def _remember(self, content: str, category: str = "general") -> Dict[str, Any]:
        """Store preference in AgentDB"""
        try:
            success = await self.agentdb.remember(content, category)

            if success:
                return {
                    "success": True,
                    "message": f"✓ Remembered: '{content}' ({category})",
                    "category": category
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store in AgentDB"
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _recall(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Recall preferences from AgentDB"""
        try:
            results = await self.agentdb.recall(
                query=query,
                top_k=top_k,
                category=category
            )

            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
                "category": category or "all"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # === CONFIG STANDARDS (KEEP - SIMPLIFIED) ===

    async def _generate_ai_standards(
        self, project_path: str = ".", formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate minimal CLAUDE.md from config files"""
        try:
            project_path_obj = Path(project_path).resolve()

            if not project_path_obj.exists():
                return {"success": False, "error": f"Project path not found: {project_path}"}

            # Parse config files
            config_parser = ConfigParser(str(project_path_obj))
            standards = config_parser.parse_all()

            # Extract conventions
            standards_extractor = StandardsExtractor(str(project_path_obj))
            conventions = standards_extractor.extract_all()

            # Generate MINIMAL instruction files (not bloated)
            instruction_generator = InstructionGenerator(standards, conventions)
            generated_files = instruction_generator.generate_all(project_path_obj, formats)

            return {
                "success": True,
                "generated_files": generated_files,
                "message": f"Generated {len(generated_files)} minimal instruction file(s)",
                "note": "Kept output minimal to avoid context bloat"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


async def main():
    """Run the MCP server"""
    memory_server = SimpleMemoryMCP()

    print("✓ MCP Standards (Simple) initialized")
    print("✓ AgentDB personal memory enabled")
    print("✓ Auto-detection active")

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
