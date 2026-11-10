#!/usr/bin/env python3
"""V2 System Status Utilities

Provides status checking, health monitoring, and deployment utilities
for the V2 pattern extraction system.
"""

import asyncio
import aiohttp
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import subprocess
import sys


@dataclass
class SystemStatus:
    """System status information"""
    component: str
    status: str  # "healthy", "degraded", "offline", "unknown"
    message: str
    details: Dict[str, Any]
    checked_at: str
    response_time_ms: float = 0


@dataclass
class V2SystemHealth:
    """Complete V2 system health report"""
    overall_status: str
    agentdb_status: SystemStatus
    sqlite_status: SystemStatus
    hook_status: SystemStatus
    memory_status: SystemStatus
    recommendations: List[str]
    checked_at: str


class V2StatusChecker:
    """Check V2 system health and provide status indicators"""

    def __init__(self,
                 agentdb_url: str = "http://localhost:3002",
                 sqlite_path: str = None):
        self.agentdb_url = agentdb_url
        self.sqlite_path = Path(sqlite_path) if sqlite_path else Path.home() / ".mcp-standards" / "knowledge.db"

    async def check_system_health(self) -> V2SystemHealth:
        """Perform comprehensive V2 system health check"""
        start_time = datetime.now()

        # Check all components
        agentdb_status = await self._check_agentdb_health()
        sqlite_status = await self._check_sqlite_health()
        hook_status = await self._check_hook_system()
        memory_status = await self._check_memory_system()

        # Determine overall status
        statuses = [agentdb_status.status, sqlite_status.status, hook_status.status, memory_status.status]
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "offline" for s in statuses):
            overall_status = "degraded"
        else:
            overall_status = "unknown"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            agentdb_status, sqlite_status, hook_status, memory_status
        )

        return V2SystemHealth(
            overall_status=overall_status,
            agentdb_status=agentdb_status,
            sqlite_status=sqlite_status,
            hook_status=hook_status,
            memory_status=memory_status,
            recommendations=recommendations,
            checked_at=start_time.isoformat()
        )

    async def _check_agentdb_health(self) -> SystemStatus:
        """Check AgentDB HTTP server health"""
        start_time = datetime.now()

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.agentdb_url}/health") as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    if response.status == 200:
                        data = await response.json()
                        return SystemStatus(
                            component="AgentDB",
                            status="healthy",
                            message=f"AgentDB server responding (port {self.agentdb_url.split(':')[-1]})",
                            details={
                                "server_status": data.get("status"),
                                "database": data.get("database"),
                                "stats": data.get("stats", {})
                            },
                            checked_at=datetime.now().isoformat(),
                            response_time_ms=response_time
                        )
                    else:
                        return SystemStatus(
                            component="AgentDB",
                            status="degraded",
                            message=f"AgentDB server returned status {response.status}",
                            details={"http_status": response.status},
                            checked_at=datetime.now().isoformat(),
                            response_time_ms=response_time
                        )

        except aiohttp.ClientConnectorError:
            return SystemStatus(
                component="AgentDB",
                status="offline",
                message="AgentDB server not reachable - is the HTTP server running?",
                details={"url": self.agentdb_url, "error": "connection_refused"},
                checked_at=datetime.now().isoformat()
            )
        except asyncio.TimeoutError:
            return SystemStatus(
                component="AgentDB",
                status="degraded",
                message="AgentDB server timeout - slow response",
                details={"url": self.agentdb_url, "error": "timeout"},
                checked_at=datetime.now().isoformat()
            )
        except Exception as e:
            return SystemStatus(
                component="AgentDB",
                status="unknown",
                message=f"AgentDB health check failed: {e}",
                details={"error": str(e)},
                checked_at=datetime.now().isoformat()
            )

    async def _check_sqlite_health(self) -> SystemStatus:
        """Check SQLite database health"""
        try:
            start_time = datetime.now()

            # Check if database exists and is accessible
            if not self.sqlite_path.exists():
                return SystemStatus(
                    component="SQLite",
                    status="offline",
                    message=f"SQLite database not found: {self.sqlite_path}",
                    details={"path": str(self.sqlite_path)},
                    checked_at=datetime.now().isoformat()
                )

            # Test database connection and basic operations
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute("SELECT 1").fetchone()

                # Check for V2 tables
                tables = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()

                table_names = [table[0] for table in tables]
                response_time = (datetime.now() - start_time).total_seconds() * 1000

                # Check for patterns
                pattern_count = 0
                execution_count = 0

                if "patterns" in table_names:
                    pattern_count = conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]

                if "tool_executions" in table_names:
                    execution_count = conn.execute("SELECT COUNT(*) FROM tool_executions").fetchone()[0]

                return SystemStatus(
                    component="SQLite",
                    status="healthy",
                    message=f"SQLite database operational with {len(table_names)} tables",
                    details={
                        "path": str(self.sqlite_path),
                        "tables": table_names,
                        "pattern_count": pattern_count,
                        "execution_count": execution_count,
                        "size_mb": round(self.sqlite_path.stat().st_size / 1024 / 1024, 2)
                    },
                    checked_at=datetime.now().isoformat(),
                    response_time_ms=response_time
                )

        except sqlite3.DatabaseError as e:
            return SystemStatus(
                component="SQLite",
                status="degraded",
                message=f"SQLite database error: {e}",
                details={"error": str(e), "path": str(self.sqlite_path)},
                checked_at=datetime.now().isoformat()
            )
        except Exception as e:
            return SystemStatus(
                component="SQLite",
                status="unknown",
                message=f"SQLite health check failed: {e}",
                details={"error": str(e)},
                checked_at=datetime.now().isoformat()
            )

    async def _check_hook_system(self) -> SystemStatus:
        """Check V2 hook system availability"""
        try:
            # Check if V2 hook modules can be imported
            from ..hooks.capture_hook_v2 import HookCaptureSystemV2
            from ..hooks.pattern_extractor_v2 import PatternExtractorV2

            # Check if hook files exist
            hook_files = [
                Path(__file__).parent.parent / "hooks" / "capture_hook_v2.py",
                Path(__file__).parent.parent / "hooks" / "pattern_extractor_v2.py",
            ]

            missing_files = [f for f in hook_files if not f.exists()]

            if missing_files:
                return SystemStatus(
                    component="Hooks",
                    status="degraded",
                    message=f"Missing hook files: {[f.name for f in missing_files]}",
                    details={"missing_files": [str(f) for f in missing_files]},
                    checked_at=datetime.now().isoformat()
                )

            return SystemStatus(
                component="Hooks",
                status="healthy",
                message="V2 hook system available and importable",
                details={
                    "v2_hooks_available": True,
                    "hook_files": [str(f) for f in hook_files]
                },
                checked_at=datetime.now().isoformat()
            )

        except ImportError as e:
            return SystemStatus(
                component="Hooks",
                status="offline",
                message=f"V2 hook import failed: {e}",
                details={"import_error": str(e)},
                checked_at=datetime.now().isoformat()
            )
        except Exception as e:
            return SystemStatus(
                component="Hooks",
                status="unknown",
                message=f"Hook system check failed: {e}",
                details={"error": str(e)},
                checked_at=datetime.now().isoformat()
            )

    async def _check_memory_system(self) -> SystemStatus:
        """Check V2 hybrid memory system"""
        try:
            # Test V2 memory system initialization
            from ..memory.v2.test_hybrid_memory import create_test_hybrid_memory

            # Quick test initialization (don't store anything)
            test_router = await create_test_hybrid_memory(
                agentdb_path=".claude/memory/status_test",
                sqlite_path=str(self.sqlite_path.parent / "status_test.db")
            )

            # Test basic operations
            stats = await test_router.get_statistics()
            await test_router.close()

            return SystemStatus(
                component="Memory",
                status="healthy",
                message="V2 hybrid memory system operational",
                details={
                    "router_stats": stats.get("router_stats", {}),
                    "system_status": stats.get("system_status", {}),
                    "agentdb_available": stats.get("system_status", {}).get("agentdb_available", False),
                    "sqlite_available": stats.get("system_status", {}).get("sqlite_available", False)
                },
                checked_at=datetime.now().isoformat()
            )

        except Exception as e:
            return SystemStatus(
                component="Memory",
                status="degraded",
                message=f"V2 memory system test failed: {e}",
                details={"error": str(e)},
                checked_at=datetime.now().isoformat()
            )

    def _generate_recommendations(self,
                                agentdb_status: SystemStatus,
                                sqlite_status: SystemStatus,
                                hook_status: SystemStatus,
                                memory_status: SystemStatus) -> List[str]:
        """Generate recommendations based on system status"""
        recommendations = []

        if agentdb_status.status == "offline":
            recommendations.append(
                "🔧 Start AgentDB HTTP server: 'node agentdb_http_server.cjs' in project root"
            )
            recommendations.append(
                "📦 Ensure AgentDB is installed: 'npm install -g agentdb'"
            )

        if agentdb_status.status == "degraded":
            recommendations.append(
                "⚡ AgentDB server is slow - check system resources and restart if needed"
            )

        if sqlite_status.status == "offline":
            recommendations.append(
                "💾 Initialize SQLite database for V2 system"
            )

        if hook_status.status == "offline" or hook_status.status == "degraded":
            recommendations.append(
                "🔗 Install V2 hook dependencies: 'uv add aiohttp'"
            )
            recommendations.append(
                "🔄 Verify V2 hook integration in Claude Code settings"
            )

        if memory_status.status == "degraded":
            recommendations.append(
                "🧠 V2 memory system issues - check AgentDB connectivity and SQLite permissions"
            )

        if all(status.status == "healthy" for status in [agentdb_status, sqlite_status, hook_status, memory_status]):
            recommendations.append(
                "✅ All systems healthy! V2 pattern extraction is ready for production use"
            )
            recommendations.append(
                "📈 Consider running pattern migration from V1: 'python -m src.mcp_standards.migration.v1_to_v2_migration'"
            )

        return recommendations

    async def check_agentdb_connectivity(self) -> bool:
        """Quick connectivity check for AgentDB"""
        status = await self._check_agentdb_health()
        return status.status == "healthy"

    def format_status_report(self, health: V2SystemHealth) -> str:
        """Format health report for console display"""
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "offline": "❌",
            "unknown": "❓"
        }

        report = []
        report.append("🔍 V2 Pattern Extraction System Status")
        report.append("=" * 50)
        report.append(f"Overall Status: {status_emoji.get(health.overall_status, '❓')} {health.overall_status.upper()}")
        report.append(f"Checked at: {health.checked_at}")
        report.append("")

        # Component statuses
        components = [
            health.agentdb_status,
            health.sqlite_status,
            health.hook_status,
            health.memory_status
        ]

        for status in components:
            emoji = status_emoji.get(status.status, "❓")
            report.append(f"{emoji} {status.component}: {status.message}")
            if status.response_time_ms > 0:
                report.append(f"   Response time: {status.response_time_ms:.1f}ms")

        # Recommendations
        if health.recommendations:
            report.append("")
            report.append("📋 Recommendations:")
            for rec in health.recommendations:
                report.append(f"   {rec}")

        return "\n".join(report)


async def check_v2_status(verbose: bool = False) -> V2SystemHealth:
    """Quick function to check V2 system status"""
    checker = V2StatusChecker()
    health = await checker.check_system_health()

    if verbose:
        print(checker.format_status_report(health))

    return health


async def quick_status_check() -> bool:
    """Quick status check - returns True if V2 system is ready"""
    health = await check_v2_status()
    return health.overall_status == "healthy"


def get_deployment_status() -> Dict[str, Any]:
    """Get deployment readiness status"""
    return {
        "v2_available": True,
        "agentdb_required": True,
        "migration_recommended": True,
        "claude_code_integration": "ready",
        "deployment_steps": [
            "1. Start AgentDB HTTP server",
            "2. Run V2 status check",
            "3. Migrate V1 patterns (optional)",
            "4. Configure Claude Code hooks to use V2",
            "5. Verify pattern extraction is working"
        ]
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check V2 system status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--agentdb-url", default="http://localhost:3002", help="AgentDB server URL")

    args = parser.parse_args()

    async def main():
        checker = V2StatusChecker(agentdb_url=args.agentdb_url)
        health = await checker.check_system_health()

        if args.json:
            print(json.dumps(asdict(health), indent=2))
        else:
            print(checker.format_status_report(health))

        # Exit code based on overall status
        if health.overall_status == "healthy":
            sys.exit(0)
        elif health.overall_status == "degraded":
            sys.exit(1)
        else:
            sys.exit(2)

    asyncio.run(main())