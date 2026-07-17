"""Export knowledge to markdown files

Creates a human-readable knowledge base from the SQL database
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class MarkdownExporter:
    """Export knowledge episodes to organized markdown files"""
    
    def __init__(self, db_path: Path, export_path: Path):
        self.db_path = db_path
        self.export_path = export_path
        self.export_path.mkdir(parents=True, exist_ok=True)
        
    def export_all(self):
        """Export all knowledge to markdown files"""
        # Create folder structure
        folders = {
            "daily": self.export_path / "daily",
            "projects": self.export_path / "projects",
            "decisions": self.export_path / "decisions",
            "research": self.export_path / "research",
            "tools": self.export_path / "tools",
        }
        
        for folder in folders.values():
            folder.mkdir(exist_ok=True)
            
        # Export different views
        self._export_daily_logs(folders["daily"])
        self._export_by_source(folders["tools"])
        self._export_decisions(folders["decisions"])
        self._create_index()
        
    def _export_daily_logs(self, folder: Path):
        """Export daily activity logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get all dates with activity
            cursor = conn.execute("""
                SELECT DISTINCT date(timestamp) as day
                FROM episodes
                ORDER BY day DESC
            """)
            
            for row in cursor:
                day = row['day']
                day_file = folder / f"{day}.md"
                
                # Get all episodes for this day
                episodes = conn.execute("""
                    SELECT * FROM episodes
                    WHERE date(timestamp) = ?
                    ORDER BY timestamp
                """, (day,)).fetchall()
                
                # Write daily markdown
                content = f"# Daily Log: {day}\n\n"
                
                for episode in episodes:
                    content += f"## {episode['name']}\n"
                    content += f"*{episode['timestamp']} - Source: {episode['source']}*\n\n"
                    content += f"{episode['content']}\n\n"
                    
                    if episode['tags']:
                        tags = json.loads(episode['tags'])
                        content += f"Tags: {', '.join(tags)}\n\n"
                    
                    content += "---\n\n"
                
                day_file.write_text(content)
    
    def _export_by_source(self, folder: Path):
        """Export episodes grouped by source/tool"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get all sources
            sources = conn.execute("""
                SELECT DISTINCT source FROM episodes
            """).fetchall()
            
            for source_row in sources:
                source = source_row['source']
                source_file = folder / f"{source}.md"
                
                # Get episodes for this source
                episodes = conn.execute("""
                    SELECT * FROM episodes
                    WHERE source = ?
                    ORDER BY timestamp DESC
                """, (source,)).fetchall()
                
                # Write source markdown
                content = f"# {source.title()} Knowledge\n\n"
                
                for episode in episodes:
                    content += f"## {episode['name']}\n"
                    content += f"*{episode['timestamp']}*\n\n"
                    content += f"{episode['content']}\n\n"
                    content += "---\n\n"
                
                source_file.write_text(content)
    
    def _export_decisions(self, folder: Path):
        """Export decision-related episodes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Search for decision-related content
            decisions = conn.execute("""
                SELECT * FROM episodes
                WHERE content LIKE '%decision%' 
                   OR content LIKE '%decided%'
                   OR content LIKE '%chose%'
                   OR name LIKE '%decision%'
                ORDER BY timestamp DESC
            """).fetchall()
            
            if decisions:
                content = "# Decisions Log\n\n"
                
                for decision in decisions:
                    content += f"## {decision['name']}\n"
                    content += f"*{decision['timestamp']}*\n\n"
                    content += f"{decision['content']}\n\n"
                    content += "---\n\n"
                
                (folder / "decisions.md").write_text(content)
    
    def _create_index(self):
        """Create main index file"""
        with sqlite3.connect(self.db_path) as conn:
            # Get statistics
            stats = {
                "total_episodes": conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0],
                "total_tools": conn.execute("SELECT COUNT(*) FROM tool_logs").fetchone()[0],
                "sources": conn.execute("SELECT DISTINCT source FROM episodes").fetchall(),
                "recent": conn.execute("""
                    SELECT * FROM episodes 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """).fetchall()
            }
            
        # Create index markdown
        content = f"""# Claude Memory Knowledge Base

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## Statistics

- **Total Episodes**: {stats['total_episodes']}
- **Tool Executions Logged**: {stats['total_tools']}
- **Knowledge Sources**: {len(stats['sources'])}

## Navigation

- [Daily Logs](./daily/) - Day-by-day activity
- [Tools](./tools/) - Knowledge by tool/source
- [Decisions](./decisions/decisions.md) - Key decisions made
- [Research](./research/) - Research findings

## Recent Activity

"""
        
        conn.row_factory = sqlite3.Row
        for episode in stats['recent']:
            content += f"- **{episode[2]}** - {episode[4]} ({episode[1][:10]})\n"
        
        (self.export_path / "README.md").write_text(content)


def export_to_markdown(db_path: Optional[Path] = None, export_path: Optional[Path] = None):
    """Export knowledge base to markdown files"""
    if db_path is None:
        db_path = Path.home() / ".mcp-standards" / "knowledge.db"
    if export_path is None:
        export_path = Path.home() / ".mcp-standards" / "exports"
        
    exporter = MarkdownExporter(db_path, export_path)
    exporter.export_all()
    
    return export_path