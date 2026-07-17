"""
Context Manager - Unified Interface for CLAUDE.md Optimization

Orchestrates all context optimization components:
- File watching and event handling
- Context optimization and compression
- Learning from manual edits
- Dynamic context loading
- AgentDB integration for semantic operations
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .optimizer import ContextOptimizer, ContextMetrics, TemplateMatch
from .watcher import ConfigFileWatcher, FileChangeEvent, WatcherConfig
from .learner import DiffBasedLearner, EditPattern
from .prime_loader import PrimeContextLoader

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Unified context management system.

    Features:
    1. **Automatic Optimization**
       - Watches config files (.editorconfig, pyproject.toml, etc.)
       - Triggers CLAUDE.md optimization on changes
       - Token reduction: 23K → 5K

    2. **Learning from Edits**
       - Detects manual edits to CLAUDE.md
       - Learns preferences (e.g., "use uv not pip")
       - Auto-applies learned patterns

    3. **Dynamic Loading**
       - /prime-<context> commands
       - Load 2K token contexts on-demand
       - Reduce base context by 80%

    4. **Semantic Operations**
       - AgentDB integration
       - Template selection
       - Pattern matching
    """

    def __init__(
        self,
        project_path: Path,
        memory_system=None,
        agentdb=None,
        auto_start: bool = False
    ):
        """
        Initialize context manager.

        Args:
            project_path: Root path of project to manage
            memory_system: PersistentMemory instance
            agentdb: AgentDB instance for semantic operations
            auto_start: Whether to start watching immediately
        """
        self.project_path = Path(project_path)
        self.memory = memory_system
        self.agentdb = agentdb

        # Initialize components
        self.optimizer = ContextOptimizer(
            memory_system=memory_system,
            agentdb=agentdb
        )

        self.learner = DiffBasedLearner(
            memory_system=memory_system,
            agentdb=agentdb
        )

        self.prime_loader = PrimeContextLoader(
            memory_system=memory_system,
            optimizer=self.optimizer
        )

        # File watcher (initialized in start())
        self.watcher: Optional[ConfigFileWatcher] = None

        # State tracking
        self._running = False
        self._last_claudemd_content: Optional[str] = None

        # Statistics
        self._stats = {
            'optimizations': 0,
            'patterns_learned': 0,
            'contexts_loaded': 0,
            'auto_applications': 0,
            'start_time': None
        }

        if auto_start:
            asyncio.create_task(self.start())

    async def start(self):
        """Start the context management system."""
        if self._running:
            logger.warning("Context manager already running")
            return

        logger.info(f"Starting context manager for {self.project_path}")

        # Initialize watcher
        watcher_config = WatcherConfig(
            watch_patterns=ConfigFileWatcher.DEFAULT_WATCH_PATTERNS,
            debounce_seconds=2.0,
            auto_optimize=True,
            backup_on_change=True,
            notification_callback=self._handle_notification
        )

        self.watcher = ConfigFileWatcher(
            project_path=self.project_path,
            config=watcher_config,
            memory_system=self.memory,
            optimizer=self.optimizer
        )

        # Register event handlers
        self.watcher.register_handler('manual_edit', self._handle_manual_edit)
        self.watcher.register_handler('file_modified', self._handle_config_change)

        # Load current CLAUDE.md content for diff tracking
        claudemd_path = self.project_path / 'CLAUDE.md'
        if claudemd_path.exists():
            self._last_claudemd_content = claudemd_path.read_text()

        # Start watching
        await self.watcher.start()

        self._running = True
        self._stats['start_time'] = datetime.now()

        logger.info("Context manager started successfully")

    async def stop(self):
        """Stop the context management system."""
        if not self._running:
            return

        logger.info("Stopping context manager")

        if self.watcher:
            await self.watcher.stop()

        self._running = False

        logger.info("Context manager stopped")

    async def _handle_manual_edit(self, event: FileChangeEvent):
        """Handle manual edits to CLAUDE.md."""
        logger.info(f"Detected manual edit to {event.file_path.name}")

        # Read current content
        current_content = event.file_path.read_text()

        # Analyze diff if we have previous content
        if self._last_claudemd_content:
            analysis = await self.learner.analyze_diff(
                previous_content=self._last_claudemd_content,
                current_content=current_content,
                project_path=str(self.project_path)
            )

            logger.info(
                f"Learned {len(analysis.patterns_detected)} patterns from manual edit"
            )

            self._stats['patterns_learned'] += len(analysis.patterns_detected)

            # Check if we should auto-apply patterns to other projects
            if len(analysis.patterns_detected) > 0:
                await self._consider_global_promotion(analysis)

        # Update stored content
        self._last_claudemd_content = current_content

    async def _handle_config_change(self, event: FileChangeEvent):
        """Handle configuration file changes."""
        logger.info(f"Config file changed: {event.file_path.name}")

        # Optimization will be triggered by watcher if auto_optimize is enabled
        # Just track statistics here
        self._stats['optimizations'] += 1

    async def _handle_notification(self, event: FileChangeEvent):
        """Handle notifications from watcher."""
        # Could integrate with notification systems, logging, etc.
        logger.debug(f"Event: {event.event_type} on {event.file_path.name}")

    async def _consider_global_promotion(self, analysis):
        """Consider promoting patterns to global preferences."""
        # Check if patterns should be promoted from project → global
        for pattern in analysis.patterns_detected:
            if pattern.pattern_type in ['preference_correction', 'tool_preference']:
                if pattern.confidence > 0.8:
                    logger.info(
                        f"High-confidence pattern detected: {pattern.content[:100]}"
                    )
                    # Could trigger promotion workflow here

    async def optimize_claudemd(
        self,
        target_tokens: Optional[int] = None,
        preserve_sections: Optional[List[str]] = None
    ) -> ContextMetrics:
        """
        Manually trigger CLAUDE.md optimization.

        Args:
            target_tokens: Target token count (defaults to project budget)
            preserve_sections: Sections to preserve

        Returns:
            ContextMetrics with optimization results
        """
        claudemd_path = self.project_path / 'CLAUDE.md'

        if not claudemd_path.exists():
            logger.warning("No CLAUDE.md found")
            # Could trigger generation here
            return None

        # Read current content
        current_content = claudemd_path.read_text()

        # Set target tokens
        if target_tokens is None:
            target_tokens = self.optimizer.TOKEN_BUDGET['project']

        # Apply learned patterns first
        auto_applied_content, applied_patterns = await self.learner.auto_apply_patterns(
            current_content,
            min_confidence=0.8,
            project_path=str(self.project_path)
        )

        if applied_patterns:
            logger.info(f"Auto-applied {len(applied_patterns)} learned patterns")
            self._stats['auto_applications'] += len(applied_patterns)
            current_content = auto_applied_content

        # Optimize
        optimized_content, metrics = self.optimizer.optimize_content(
            current_content,
            target_tokens=target_tokens,
            preserve_sections=preserve_sections
        )

        # Backup current version
        backup_path = claudemd_path.with_suffix(
            f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        )
        backup_path.write_text(current_content)

        # Write optimized content
        claudemd_path.write_text(optimized_content)

        # Update tracking
        self._last_claudemd_content = optimized_content
        self._stats['optimizations'] += 1

        logger.info(
            f"Optimized CLAUDE.md: {metrics.token_count} tokens "
            f"({metrics.compression_ratio:.2f}x compression)"
        )

        return metrics

    async def load_prime_context(
        self,
        context_id: str,
        include_dependencies: bool = True
    ) -> Optional[str]:
        """
        Load a prime context.

        Args:
            context_id: Context identifier (bug, feature, refactor, etc.)
            include_dependencies: Whether to include dependencies

        Returns:
            Context content or None if not found
        """
        context = await self.prime_loader.load_context(
            context_id=context_id,
            include_dependencies=include_dependencies
        )

        if context:
            self._stats['contexts_loaded'] += 1

        return context

    async def suggest_improvements(self) -> List[Dict[str, Any]]:
        """
        Get improvement suggestions for CLAUDE.md.

        Returns:
            List of suggestions with priorities
        """
        claudemd_path = self.project_path / 'CLAUDE.md'

        if not claudemd_path.exists():
            return []

        current_content = claudemd_path.read_text()

        # Get suggestions from learner
        suggestions = await self.learner.suggest_improvements(
            content=current_content,
            project_path=str(self.project_path)
        )

        return suggestions

    async def analyze_project(self) -> Dict[str, Any]:
        """
        Analyze project to determine optimal configuration.

        Returns:
            Analysis results with template recommendations
        """
        # Get template match
        template_match = self.optimizer.analyze_project_type(self.project_path)

        # Get current CLAUDE.md metrics
        claudemd_path = self.project_path / 'CLAUDE.md'
        current_metrics = None

        if claudemd_path.exists():
            current_content = claudemd_path.read_text()
            current_tokens = self.optimizer.estimate_tokens(current_content)

            current_metrics = {
                'token_count': current_tokens,
                'section_count': current_content.count('\n## '),
                'optimization_potential': max(
                    0,
                    current_tokens - self.optimizer.TOKEN_BUDGET['project']
                )
            }

        # Get learned patterns
        patterns = await self.learner.get_learned_patterns(min_confidence=0.7)

        return {
            'project_path': str(self.project_path),
            'template_match': {
                'template_id': template_match.template_id,
                'confidence': template_match.confidence,
                'project_type': template_match.project_type,
                'detected_patterns': template_match.detected_patterns,
                'estimated_tokens': template_match.estimated_tokens
            },
            'current_metrics': current_metrics,
            'learned_patterns': len(patterns),
            'high_confidence_patterns': sum(1 for p in patterns if p.confidence > 0.8),
            'available_contexts': len(self.prime_loader.list_available_contexts()),
            'recommendations': self._generate_recommendations(
                template_match,
                current_metrics,
                patterns
            )
        }

    def _generate_recommendations(
        self,
        template_match: TemplateMatch,
        current_metrics: Optional[Dict],
        patterns: List[EditPattern]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Token optimization
        if current_metrics and current_metrics['optimization_potential'] > 5000:
            recommendations.append({
                'type': 'optimization',
                'priority': 'high',
                'message': f"CLAUDE.md can be reduced by ~{current_metrics['optimization_potential']} tokens",
                'action': 'Run optimize_claudemd() to apply token reduction'
            })

        # Template alignment
        if template_match.confidence < 0.7:
            recommendations.append({
                'type': 'template',
                'priority': 'medium',
                'message': f"Project type unclear (confidence: {template_match.confidence:.0%})",
                'action': 'Consider creating project-specific CLAUDE.md sections'
            })

        # Pattern application
        high_conf_patterns = [p for p in patterns if p.confidence > 0.8 and p.frequency > 2]
        if high_conf_patterns:
            recommendations.append({
                'type': 'patterns',
                'priority': 'high',
                'message': f"{len(high_conf_patterns)} high-confidence patterns ready to apply",
                'action': 'Run optimize_claudemd() to auto-apply learned patterns'
            })

        # Progressive disclosure
        if current_metrics and current_metrics['token_count'] > 7000:
            recommendations.append({
                'type': 'prime_contexts',
                'priority': 'medium',
                'message': 'Large context detected - consider using /prime commands',
                'action': 'Move extended sections to prime contexts'
            })

        return recommendations

    def get_prime_menu(self) -> str:
        """Get the prime context menu."""
        return self.prime_loader.get_context_menu()

    def list_available_contexts(self) -> List[Dict[str, Any]]:
        """List all available prime contexts."""
        return self.prime_loader.list_available_contexts()

    async def suggest_contexts(self, query: str) -> List:
        """Suggest relevant contexts based on query."""
        return await self.prime_loader.suggest_contexts(query)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            'manager': self._stats.copy(),
            'running': self._running
        }

        if self.watcher:
            stats['watcher'] = self.watcher.get_statistics()

        stats['learner'] = self.learner.get_statistics()
        stats['prime_loader'] = self.prime_loader.get_statistics()

        # Calculate uptime
        if self._stats['start_time']:
            uptime = datetime.now() - self._stats['start_time']
            stats['uptime_seconds'] = uptime.total_seconds()

        return stats

    async def force_optimization(self):
        """Force immediate optimization (bypasses debounce)."""
        if self.watcher:
            await self.watcher.force_optimization()
        else:
            await self.optimize_claudemd()

    async def export_learned_patterns(self, output_path: Path):
        """Export learned patterns to file."""
        patterns = await self.learner.get_learned_patterns()

        export_data = {
            'export_date': datetime.now().isoformat(),
            'project_path': str(self.project_path),
            'pattern_count': len(patterns),
            'patterns': [p.to_dict() for p in patterns]
        }

        with open(output_path, 'w') as f:
            import json
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(patterns)} patterns to {output_path}")

    async def import_learned_patterns(self, input_path: Path):
        """Import learned patterns from file."""
        with open(input_path, 'r') as f:
            import json
            import_data = json.load(f)

        patterns = import_data.get('patterns', [])

        for pattern_dict in patterns:
            pattern = EditPattern(
                pattern_type=pattern_dict['pattern_type'],
                content=pattern_dict['content'],
                frequency=pattern_dict['frequency'],
                confidence=pattern_dict['confidence'],
                first_seen=datetime.fromisoformat(pattern_dict['first_seen']),
                last_seen=datetime.fromisoformat(pattern_dict['last_seen']),
                contexts=pattern_dict['contexts']
            )

            # Store in learner
            pattern_key = self.learner._generate_pattern_key(pattern)
            self.learner._learned_patterns[pattern_key] = pattern

        logger.info(f"Imported {len(patterns)} patterns from {input_path}")


# Convenience function for quick setup
async def setup_context_manager(
    project_path: str,
    memory_system=None,
    agentdb=None,
    auto_start: bool = True
) -> ContextManager:
    """
    Quick setup for context management.

    Args:
        project_path: Path to project root
        memory_system: Optional PersistentMemory instance
        agentdb: Optional AgentDB instance
        auto_start: Whether to start immediately

    Returns:
        Configured and optionally started ContextManager
    """
    manager = ContextManager(
        project_path=Path(project_path),
        memory_system=memory_system,
        agentdb=agentdb
    )

    if auto_start:
        await manager.start()

    return manager
