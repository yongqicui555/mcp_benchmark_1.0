"""Autolog system for Claude Memory

Automatically captures and centralizes knowledge across all Claude instances
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Significant tool patterns to auto-capture
TOOL_SIGNIFICANCE = {
    # High priority (always log)
    "github_issue": 0.9,
    "github_pr": 0.9,
    "notion_create": 0.8,
    "notion_update": 0.8,
    "file_write": 0.7,
    "file_edit": 0.7,
    
    # Medium priority (log if significant file)
    "bash_command": 0.5,
    "file_read": 0.3,
    
    # Low priority (rarely log)
    "list_files": 0.1,
    "search": 0.1,
}

# Important files to track
SIGNIFICANT_FILES = {
    "claude.md": 1.0,
    "readme.md": 0.9,
    "package.json": 0.8,
    "pyproject.toml": 0.8,
    "dockerfile": 0.8,
    ".env": 0.7,
    "requirements.txt": 0.7,
}


class AutoLogger:
    """Automatic knowledge capture from tool executions"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_db()
        
    def _ensure_db(self):
        """Ensure database exists with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Tool execution logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tool_name TEXT NOT NULL,
                    args TEXT,
                    result TEXT,
                    significance REAL,
                    session_id TEXT,
                    metadata TEXT
                )
            """)
            
            # Extracted knowledge episodes  
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    tool_log_id INTEGER,
                    tags TEXT,
                    FOREIGN KEY(tool_log_id) REFERENCES tool_logs(id)
                )
            """)
            
            # Search index
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                    name, content, tags, content=episodes
                )
            """)
            
            conn.commit()
    
    def should_log(self, tool_name: str, args: Dict[str, Any]) -> float:
        """Calculate if tool execution should be logged"""
        # Base significance from tool type
        base_score = TOOL_SIGNIFICANCE.get(tool_name, 0.2)
        
        # Boost for significant files
        if "file_path" in args or "path" in args:
            file_path = str(args.get("file_path", args.get("path", ""))).lower()
            for pattern, boost in SIGNIFICANT_FILES.items():
                if pattern in file_path:
                    base_score = min(1.0, base_score + boost)
                    break
        
        # Boost for create/update operations
        if any(word in tool_name for word in ["create", "write", "update", "commit"]):
            base_score = min(1.0, base_score + 0.3)
            
        return base_score
    
    def log_tool_execution(
        self, 
        tool_name: str, 
        args: Dict[str, Any], 
        result: Any,
        session_id: Optional[str] = None
    ) -> Optional[int]:
        """Log tool execution if significant"""
        significance = self.should_log(tool_name, args)
        
        if significance < 0.3:  # Skip low significance
            return None
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO tool_logs (tool_name, args, result, significance, session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                tool_name,
                json.dumps(args),
                json.dumps(str(result)[:1000]),  # Truncate large results
                significance,
                session_id or "default"
            ))
            
            log_id = cursor.lastrowid
            
            # Extract episode if highly significant
            if significance > 0.6:
                episode = self._extract_episode(tool_name, args, result)
                if episode:
                    conn.execute("""
                        INSERT INTO episodes (name, content, source, tool_log_id, tags)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        episode["name"],
                        episode["content"],
                        episode["source"],
                        log_id,
                        json.dumps(episode.get("tags", []))
                    ))
                    
                    # Update FTS index
                    conn.execute("""
                        INSERT INTO episodes_fts (name, content, tags)
                        VALUES (?, ?, ?)
                    """, (
                        episode["name"],
                        episode["content"],
                        " ".join(episode.get("tags", []))
                    ))
            
            conn.commit()
            return log_id
    
    def _extract_episode(self, tool_name: str, args: Dict[str, Any], result: Any) -> Optional[Dict[str, Any]]:
        """Extract knowledge episode from tool execution"""
        if tool_name.startswith("github"):
            return self._extract_github_episode(tool_name, args, result)
        elif tool_name.startswith("notion"):
            return self._extract_notion_episode(tool_name, args, result)
        elif "file" in tool_name:
            return self._extract_file_episode(tool_name, args, result)
        return None
    
    def _extract_github_episode(self, tool_name: str, args: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Extract GitHub knowledge"""
        if "issue" in tool_name:
            return {
                "name": f"GitHub Issue: {args.get('title', 'Unknown')}",
                "content": f"Issue #{args.get('number', '?')} in {args.get('repo', 'unknown repo')}\n{args.get('body', '')}",
                "source": "github",
                "tags": ["github", "issue", args.get('repo', '')]
            }
        elif "pr" in tool_name:
            return {
                "name": f"Pull Request: {args.get('title', 'Unknown')}",
                "content": f"PR #{args.get('number', '?')} in {args.get('repo', 'unknown repo')}",
                "source": "github", 
                "tags": ["github", "pr", args.get('repo', '')]
            }
        return None
    
    def _extract_notion_episode(self, tool_name: str, args: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Extract Notion knowledge"""
        return {
            "name": f"Notion: {args.get('title', 'Untitled')}",
            "content": args.get('content', ''),
            "source": "notion",
            "tags": ["notion", "documentation"]
        }
    
    def _extract_file_episode(self, tool_name: str, args: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Extract file operation knowledge"""
        file_path = args.get('file_path', args.get('path', 'unknown'))
        file_name = Path(file_path).name
        
        return {
            "name": f"File: {file_name}",
            "content": f"Modified {file_path}",
            "source": "file_operation",
            "tags": ["file", file_name.split('.')[-1]]  # Extension as tag
        }


# Global autologger instance
_autologger = None

def get_autologger(db_path: Optional[Path] = None) -> AutoLogger:
    """Get or create global autologger instance"""
    global _autologger
    if _autologger is None:
        if db_path is None:
            db_path = Path.home() / ".mcp-standards" / "knowledge.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _autologger = AutoLogger(db_path)
    return _autologger


def autolog_tool(tool_name: str, args: Dict[str, Any], result: Any):
    """Simple interface for autologging tool executions"""
    logger = get_autologger()
    return logger.log_tool_execution(tool_name, args, result)