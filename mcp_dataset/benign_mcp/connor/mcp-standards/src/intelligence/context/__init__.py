"""
Intelligent Context Management System

Automatic CLAUDE.md optimization with:
- Event-driven updates via file watchers
- Token reduction (23K → 5K)
- Dynamic context loading (/prime commands)
- Diff-based learning from manual edits
- Semantic template selection

Usage:
    from intelligence.context import ContextManager

    # Initialize system
    manager = ContextManager(project_path="./myproject")
    await manager.start()

    # Auto-optimization is now active
    # Edit .editorconfig, pyproject.toml, etc. → automatic CLAUDE.md update

    # Load task-specific context
    bug_context = await manager.load_prime_context('bug')

    # Get suggestions
    suggestions = await manager.suggest_improvements()
"""

from .optimizer import ContextOptimizer, ContextMetrics, TemplateMatch
from .watcher import ConfigFileWatcher, FileChangeEvent, WatcherConfig
from .learner import DiffBasedLearner, EditPattern, DiffAnalysis
from .prime_loader import PrimeContextLoader, PrimeContext
from .manager import ContextManager

__all__ = [
    # Main interface
    'ContextManager',

    # Core components
    'ContextOptimizer',
    'ConfigFileWatcher',
    'DiffBasedLearner',
    'PrimeContextLoader',

    # Data classes
    'ContextMetrics',
    'TemplateMatch',
    'FileChangeEvent',
    'WatcherConfig',
    'EditPattern',
    'DiffAnalysis',
    'PrimeContext',
]

__version__ = '2.0.0'
