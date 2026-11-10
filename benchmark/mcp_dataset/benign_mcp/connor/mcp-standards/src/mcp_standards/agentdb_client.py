"""
AgentDB Client - Simple wrapper for personal memory

Uses AgentDB npm package for ultra-fast semantic vector search.
Zero configuration, automatic embedding generation.
"""
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class AgentDBClient:
    """
    Simple client for AgentDB vector memory.

    Features:
    - <10ms startup time
    - <1ms semantic search
    - Automatic embedding generation
    - Personal knowledge graph

    Usage:
        client = AgentDBClient()

        # Store preference
        await client.remember("use uv not pip", category="python")

        # Recall preference
        results = await client.recall("package manager", top_k=3)
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize AgentDB client.

        Args:
            db_path: Path to AgentDB storage (default: ~/.mcp-standards/agentdb)
        """
        if db_path is None:
            self.db_path = Path.home() / ".mcp-standards" / "agentdb"
        else:
            self.db_path = Path(db_path)

        self.db_path.mkdir(parents=True, exist_ok=True)

        # Check if AgentDB is available
        self._check_agentdb_installed()

        logger.info(f"AgentDB client initialized at {self.db_path}")

    def _check_agentdb_installed(self):
        """Check if AgentDB is available via npx."""
        try:
            result = subprocess.run(
                ["npx", "agentdb", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"AgentDB available: {result.stdout.strip()}")
            else:
                logger.warning("AgentDB not installed. Install: npm install -g agentdb")

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not verify AgentDB installation: {e}")

    async def remember(
        self,
        content: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a preference/correction in AgentDB.

        Args:
            content: The preference text (e.g., "use uv not pip")
            category: Category for organization (e.g., "python", "git")
            metadata: Additional metadata to store

        Returns:
            Success status

        Example:
            await client.remember("use uv not pip", category="python")
        """
        try:
            # Prepare metadata
            meta = {
                "category": category,
                "content": content,
                **(metadata or {})
            }

            # Store in AgentDB via CLI
            cmd = [
                "npx", "agentdb",
                "store",
                "--key", f"{category}:{hash(content)}",
                "--value", content,
                "--metadata", json.dumps(meta),
                "--path", str(self.db_path)
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                logger.info(f"✓ Remembered: '{content}' ({category})")
                return True
            else:
                logger.error(f"AgentDB store failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Failed to remember: {e}")
            return False

    async def recall(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar preferences.

        Args:
            query: Search query (natural language)
            top_k: Number of results to return
            category: Filter by category (optional)
            min_similarity: Minimum similarity score (0.0-1.0)

        Returns:
            List of matching preferences with similarity scores

        Example:
            results = await client.recall("package manager", top_k=3)
            # Returns: [{"content": "use uv not pip", "similarity": 0.95, ...}]
        """
        try:
            # Build command
            cmd = [
                "npx", "agentdb",
                "query",
                "--query", query,
                "--top-k", str(top_k),
                "--threshold", str(min_similarity),
                "--path", str(self.db_path)
            ]

            if category:
                cmd.extend(["--filter", f"category:{category}"])

            # Execute query
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                results = json.loads(stdout.decode())
                logger.info(f"✓ Recalled {len(results)} preferences for: '{query}'")
                return results
            else:
                logger.error(f"AgentDB query failed: {stderr.decode()}")
                return []

        except Exception as e:
            logger.error(f"Failed to recall: {e}")
            return []

    async def get_all_categories(self) -> List[str]:
        """Get all unique categories stored."""
        try:
            # Query all entries
            all_results = await self.recall("*", top_k=1000, min_similarity=0.0)

            # Extract unique categories
            categories = set()
            for result in all_results:
                if "metadata" in result and "category" in result["metadata"]:
                    categories.add(result["metadata"]["category"])

            return sorted(list(categories))

        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get AgentDB statistics."""
        try:
            cmd = [
                "npx", "agentdb",
                "stats",
                "--path", str(self.db_path)
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                return json.loads(stdout.decode())
            else:
                return {"error": stderr.decode()}

        except Exception as e:
            return {"error": str(e)}


# Convenience functions for simple usage
async def remember_preference(content: str, category: str = "general") -> bool:
    """
    Quick function to remember a preference.

    Usage:
        await remember_preference("use uv not pip", "python")
    """
    client = AgentDBClient()
    return await client.remember(content, category)


async def recall_preferences(query: str, top_k: int = 5) -> List[Dict]:
    """
    Quick function to recall preferences.

    Usage:
        prefs = await recall_preferences("package manager")
    """
    client = AgentDBClient()
    return await client.recall(query, top_k)
