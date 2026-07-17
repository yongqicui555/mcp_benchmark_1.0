"""
Event-Driven File Watcher for CLAUDE.md Optimization

Monitors project configuration files and automatically triggers
CLAUDE.md updates when changes are detected.

Watched files:
- .editorconfig
- pyproject.toml
- package.json
- tsconfig.json
- .prettierrc*
- .eslintrc*
- CLAUDE.md (for manual edit detection)

Events:
- file_created: New config file added
- file_modified: Config file changed
- file_deleted: Config file removed
- manual_edit: CLAUDE.md manually edited
"""

import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Dict, Set, Optional, Callable, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


@dataclass
class FileChangeEvent:
    """Represents a file change event."""
    event_type: str  # created, modified, deleted
    file_path: Path
    timestamp: datetime
    file_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['file_path'] = str(self.file_path)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class WatcherConfig:
    """Configuration for file watcher."""
    watch_patterns: List[str]
    debounce_seconds: float
    auto_optimize: bool
    backup_on_change: bool
    notification_callback: Optional[Callable] = None


class ConfigFileWatcher:
    """
    Event-driven file watcher for project configuration files.

    Features:
    - Efficient polling with configurable intervals
    - File content hashing to detect real changes
    - Debouncing to avoid excessive triggers
    - Event callbacks for extensibility
    - Change history tracking
    """

    # Default files to watch
    DEFAULT_WATCH_PATTERNS = [
        '.editorconfig',
        'pyproject.toml',
        'package.json',
        'tsconfig.json',
        'package-lock.json',
        'yarn.lock',
        'pnpm-lock.yaml',
        '.prettierrc*',
        '.eslintrc*',
        'jest.config.*',
        'vitest.config.*',
        'vite.config.*',
        'CLAUDE.md',
        '.claude/**/*.md',
        'Makefile',
        'docker-compose.yml',
        'Dockerfile'
    ]

    def __init__(
        self,
        project_path: Path,
        config: Optional[WatcherConfig] = None,
        memory_system=None,
        optimizer=None
    ):
        """
        Initialize file watcher.

        Args:
            project_path: Root path of project to watch
            config: Watcher configuration
            memory_system: PersistentMemory for event storage
            optimizer: ContextOptimizer for automatic optimization
        """
        self.project_path = project_path
        self.memory = memory_system
        self.optimizer = optimizer

        # Use provided config or defaults
        self.config = config or WatcherConfig(
            watch_patterns=self.DEFAULT_WATCH_PATTERNS,
            debounce_seconds=2.0,
            auto_optimize=True,
            backup_on_change=True
        )

        # Track file states
        self._file_hashes: Dict[Path, str] = {}
        self._pending_events: Dict[Path, FileChangeEvent] = {}
        self._last_process_time: Dict[Path, datetime] = {}

        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {
            'file_created': [],
            'file_modified': [],
            'file_deleted': [],
            'manual_edit': []
        }

        # Watcher state
        self._running = False
        self._watch_task: Optional[asyncio.Task] = None

        # Statistics
        self._stats = {
            'events_detected': 0,
            'events_processed': 0,
            'optimizations_triggered': 0,
            'errors': 0
        }

    async def start(self):
        """Start watching for file changes."""
        if self._running:
            logger.warning("Watcher already running")
            return

        self._running = True

        # Initialize file hashes
        await self._initialize_hashes()

        # Start watch loop
        self._watch_task = asyncio.create_task(self._watch_loop())

        logger.info(f"Started watching {self.project_path} for config changes")

    async def stop(self):
        """Stop watching for file changes."""
        if not self._running:
            return

        self._running = False

        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped file watcher")

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler.

        Args:
            event_type: Type of event (file_created, file_modified, etc.)
            handler: Async callable to handle event
        """
        if event_type not in self._event_handlers:
            raise ValueError(f"Unknown event type: {event_type}")

        self._event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    async def _initialize_hashes(self):
        """Initialize file content hashes."""
        watched_files = self._get_watched_files()

        for file_path in watched_files:
            if file_path.exists():
                file_hash = self._calculate_hash(file_path)
                self._file_hashes[file_path] = file_hash

        logger.info(f"Initialized {len(self._file_hashes)} file hashes")

    def _get_watched_files(self) -> Set[Path]:
        """Get all files matching watch patterns."""
        watched_files = set()

        for pattern in self.config.watch_patterns:
            if '*' in pattern:
                # Glob pattern
                matches = self.project_path.glob(pattern)
                watched_files.update(matches)
            else:
                # Direct file
                file_path = self.project_path / pattern
                if file_path.exists():
                    watched_files.add(file_path)

        return watched_files

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks for memory efficiency
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return ""

    async def _watch_loop(self):
        """Main watch loop - polls for file changes."""
        poll_interval = 1.0  # Check every second

        while self._running:
            try:
                await self._check_for_changes()
                await self._process_pending_events()
                await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                self._stats['errors'] += 1
                await asyncio.sleep(poll_interval)

    async def _check_for_changes(self):
        """Check all watched files for changes."""
        current_files = self._get_watched_files()
        previous_files = set(self._file_hashes.keys())

        # Check for new files
        new_files = current_files - previous_files
        for file_path in new_files:
            await self._handle_file_created(file_path)

        # Check for deleted files
        deleted_files = previous_files - current_files
        for file_path in deleted_files:
            await self._handle_file_deleted(file_path)

        # Check for modified files
        for file_path in current_files & previous_files:
            current_hash = self._calculate_hash(file_path)
            previous_hash = self._file_hashes.get(file_path)

            if current_hash != previous_hash:
                await self._handle_file_modified(file_path, previous_hash, current_hash)

    async def _handle_file_created(self, file_path: Path):
        """Handle file creation event."""
        file_hash = self._calculate_hash(file_path)
        self._file_hashes[file_path] = file_hash

        event = FileChangeEvent(
            event_type='file_created',
            file_path=file_path,
            timestamp=datetime.now(),
            file_hash=file_hash,
            metadata={'size': file_path.stat().st_size}
        )

        self._pending_events[file_path] = event
        self._stats['events_detected'] += 1

        logger.info(f"Detected new file: {file_path.name}")

    async def _handle_file_modified(
        self,
        file_path: Path,
        previous_hash: str,
        current_hash: str
    ):
        """Handle file modification event."""
        self._file_hashes[file_path] = current_hash

        # Check if this is a manual edit to CLAUDE.md
        event_type = 'manual_edit' if file_path.name == 'CLAUDE.md' else 'file_modified'

        event = FileChangeEvent(
            event_type=event_type,
            file_path=file_path,
            timestamp=datetime.now(),
            file_hash=current_hash,
            previous_hash=previous_hash,
            metadata={
                'size': file_path.stat().st_size,
                'mtime': datetime.fromtimestamp(file_path.stat().st_mtime)
            }
        )

        self._pending_events[file_path] = event
        self._stats['events_detected'] += 1

        logger.info(f"Detected change in: {file_path.name}")

    async def _handle_file_deleted(self, file_path: Path):
        """Handle file deletion event."""
        previous_hash = self._file_hashes.pop(file_path, None)

        event = FileChangeEvent(
            event_type='file_deleted',
            file_path=file_path,
            timestamp=datetime.now(),
            previous_hash=previous_hash
        )

        self._pending_events[file_path] = event
        self._stats['events_detected'] += 1

        logger.info(f"Detected deletion: {file_path.name}")

    async def _process_pending_events(self):
        """Process pending events after debounce period."""
        now = datetime.now()
        debounce_delta = timedelta(seconds=self.config.debounce_seconds)

        events_to_process = []

        for file_path, event in list(self._pending_events.items()):
            # Check if event is old enough to process
            if now - event.timestamp >= debounce_delta:
                events_to_process.append(event)
                del self._pending_events[file_path]

        # Process events
        for event in events_to_process:
            await self._process_event(event)

    async def _process_event(self, event: FileChangeEvent):
        """Process a file change event."""
        try:
            # Store event in memory
            if self.memory:
                await self.memory.store(
                    key=f"file_event_{event.timestamp.timestamp()}",
                    value=event.to_dict(),
                    namespace="file_events",
                    ttl_seconds=86400 * 30  # Keep for 30 days
                )

            # Call registered handlers
            handlers = self._event_handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type}: {e}")

            # Auto-optimize if configured
            if self.config.auto_optimize and self._should_trigger_optimization(event):
                await self._trigger_optimization(event)

            self._stats['events_processed'] += 1

            # Notification callback
            if self.config.notification_callback:
                await self.config.notification_callback(event)

        except Exception as e:
            logger.error(f"Failed to process event: {e}")
            self._stats['errors'] += 1

    def _should_trigger_optimization(self, event: FileChangeEvent) -> bool:
        """Determine if event should trigger CLAUDE.md optimization."""
        # Don't optimize on CLAUDE.md manual edits (would be circular)
        if event.file_path.name == 'CLAUDE.md':
            return False

        # Optimize on config file changes
        config_files = {
            '.editorconfig', 'pyproject.toml', 'package.json',
            'tsconfig.json', '.prettierrc', '.eslintrc'
        }

        file_name = event.file_path.name

        # Check exact match or pattern match
        if file_name in config_files:
            return True

        # Check patterns
        if any(file_name.startswith(cf) for cf in config_files):
            return True

        return False

    async def _trigger_optimization(self, event: FileChangeEvent):
        """Trigger CLAUDE.md optimization based on config change."""
        if not self.optimizer:
            logger.warning("No optimizer configured - skipping optimization")
            return

        try:
            # Check rate limiting
            last_optimize = self._last_process_time.get(self.project_path)
            if last_optimize:
                time_since_last = datetime.now() - last_optimize
                if time_since_last < timedelta(minutes=5):
                    logger.debug("Skipping optimization - too soon since last")
                    return

            logger.info(f"Triggering optimization due to {event.file_path.name} change")

            # Find CLAUDE.md
            claudemd_path = self.project_path / 'CLAUDE.md'

            if not claudemd_path.exists():
                logger.info("No CLAUDE.md found - creating new one")
                # Could trigger initial generation here
                return

            # Read current content
            current_content = claudemd_path.read_text()

            # Backup if configured
            if self.config.backup_on_change:
                backup_path = claudemd_path.with_suffix(
                    f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
                )
                backup_path.write_text(current_content)
                logger.info(f"Created backup: {backup_path.name}")

            # Optimize content
            optimized_content, metrics = self.optimizer.optimize_content(
                current_content,
                target_tokens=self.optimizer.TOKEN_BUDGET['project']
            )

            # Write optimized content
            claudemd_path.write_text(optimized_content)

            # Update timestamp
            self._last_process_time[self.project_path] = datetime.now()
            self._stats['optimizations_triggered'] += 1

            logger.info(
                f"Optimized CLAUDE.md: {metrics.token_count} tokens "
                f"({metrics.compression_ratio:.2f}x compression)"
            )

            # Store optimization metrics
            if self.memory:
                await self.memory.store(
                    key=f"optimization_{datetime.now().timestamp()}",
                    value={
                        'trigger_event': event.to_dict(),
                        'metrics': metrics.to_dict(),
                        'project_path': str(self.project_path)
                    },
                    namespace="optimizations",
                    ttl_seconds=86400 * 90  # Keep for 90 days
                )

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            self._stats['errors'] += 1

    async def detect_manual_edits(
        self,
        current_content: str,
        previous_content: str
    ) -> Dict[str, Any]:
        """
        Detect and analyze manual edits to CLAUDE.md.

        This enables learning from user corrections.

        Returns:
            Dictionary with edit analysis
        """
        import difflib

        # Calculate diff
        diff = list(difflib.unified_diff(
            previous_content.splitlines(keepends=True),
            current_content.splitlines(keepends=True),
            lineterm=''
        ))

        # Analyze changes
        additions = []
        deletions = []

        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:].strip())

        # Detect patterns in edits
        patterns = {
            'preference_changes': [],
            'new_sections': [],
            'removed_sections': [],
            'style_changes': []
        }

        # Check for preference changes (e.g., "use X not Y")
        for addition in additions:
            if any(kw in addition.lower() for kw in ['use', 'prefer', 'always', 'never']):
                patterns['preference_changes'].append(addition)

        # Check for new sections
        for addition in additions:
            if addition.startswith('##'):
                patterns['new_sections'].append(addition[2:].strip())

        # Check for removed sections
        for deletion in deletions:
            if deletion.startswith('##'):
                patterns['removed_sections'].append(deletion[2:].strip())

        return {
            'total_additions': len(additions),
            'total_deletions': len(deletions),
            'patterns': patterns,
            'diff_lines': len(diff),
            'significant': len(additions) > 3 or len(deletions) > 3
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        return {
            **self._stats,
            'watching': self._running,
            'files_tracked': len(self._file_hashes),
            'pending_events': len(self._pending_events),
            'project_path': str(self.project_path)
        }

    async def force_optimization(self):
        """Force immediate optimization regardless of debounce."""
        logger.info("Forcing CLAUDE.md optimization")

        # Create synthetic event
        claudemd_path = self.project_path / 'CLAUDE.md'

        event = FileChangeEvent(
            event_type='file_modified',
            file_path=claudemd_path,
            timestamp=datetime.now()
        )

        await self._trigger_optimization(event)
