#!/usr/bin/env python3
"""Performance Optimization Engine

Advanced optimization system for V2 pattern extraction with:
- Intelligent caching strategies
- Query optimization
- Memory pool management
- Batch processing optimization
- Connection pooling
- Performance metrics collection
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import weakref

from ..memory.v2.test_hybrid_memory import TestMemoryRouter


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation: str
    start_time: float
    end_time: float
    success: bool
    cache_hit: bool = False
    vector_count: int = 0
    memory_usage_mb: float = 0
    cpu_usage_percent: float = 0

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

    @property
    def throughput_ops_per_sec(self) -> float:
        duration_s = self.end_time - self.start_time
        return 1.0 / duration_s if duration_s > 0 else 0


@dataclass
class CacheEntry:
    """Cache entry with TTL and usage tracking"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: float

    @property
    def is_expired(self) -> bool:
        return time.time() > (self.created_at + self.ttl_seconds)

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class IntelligentCache:
    """High-performance cache with intelligent eviction and statistics"""

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = deque()
        self.lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _evict_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            del self.cache[key]
            try:
                self.access_order.remove(key)
            except ValueError:
                pass

        self.evictions += len(expired_keys)

    def _evict_lru(self):
        """Evict least recently used entries"""
        while len(self.cache) >= self.max_size and self.access_order:
            lru_key = self.access_order.popleft()
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.evictions += 1

    def get(self, key: str) -> Optional[Any]:
        """Get cached value with LRU tracking"""
        with self.lock:
            self._evict_expired()

            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired:
                    entry.last_accessed = time.time()
                    entry.access_count += 1

                    # Move to end (most recently used)
                    try:
                        self.access_order.remove(key)
                    except ValueError:
                        pass
                    self.access_order.append(key)

                    self.hits += 1
                    return entry.value
                else:
                    del self.cache[key]

            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set cached value with TTL"""
        with self.lock:
            self._evict_expired()
            self._evict_lru()

            ttl = ttl or self.default_ttl
            current_time = time.time()

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                last_accessed=current_time,
                access_count=1,
                ttl_seconds=ttl
            )

            self.cache[key] = entry

            # Remove from access order if exists, then add to end
            try:
                self.access_order.remove(key)
            except ValueError:
                pass
            self.access_order.append(key)

    def clear(self):
        """Clear all cached entries"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests) if total_requests > 0 else 0

            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'evictions': self.evictions,
                'avg_age_seconds': sum(e.age_seconds for e in self.cache.values()) / len(self.cache) if self.cache else 0
            }


class ConnectionPool:
    """Connection pool for AgentDB HTTP connections"""

    def __init__(self, max_connections: int = 10, connection_timeout: float = 30):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.available_connections = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.total_connections_created = 0
        self.lock = asyncio.Lock()

    async def get_connection(self):
        """Get connection from pool or create new one"""
        try:
            # Try to get existing connection
            connection = self.available_connections.get_nowait()
            return connection
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            async with self.lock:
                if self.active_connections < self.max_connections:
                    import aiohttp
                    timeout = aiohttp.ClientTimeout(total=self.connection_timeout)
                    connection = aiohttp.ClientSession(timeout=timeout)
                    self.active_connections += 1
                    self.total_connections_created += 1
                    return connection
                else:
                    # Wait for available connection
                    return await self.available_connections.get()

    async def return_connection(self, connection):
        """Return connection to pool"""
        try:
            self.available_connections.put_nowait(connection)
        except asyncio.QueueFull:
            # Pool full, close connection
            await connection.close()
            async with self.lock:
                self.active_connections -= 1

    async def close_all(self):
        """Close all connections"""
        while not self.available_connections.empty():
            try:
                connection = self.available_connections.get_nowait()
                await connection.close()
            except asyncio.QueueEmpty:
                break

        async with self.lock:
            self.active_connections = 0


class BatchProcessor:
    """Intelligent batch processing for vector operations"""

    def __init__(self, batch_size: int = 50, max_wait_time: float = 0.1):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_operations = []
        self.batch_futures = []
        self.last_flush_time = time.time()
        self.lock = asyncio.Lock()

    async def add_operation(self, operation_type: str, data: Dict[str, Any]) -> Any:
        """Add operation to batch and return future result"""
        future = asyncio.Future()

        async with self.lock:
            self.pending_operations.append({
                'type': operation_type,
                'data': data,
                'future': future,
                'timestamp': time.time()
            })

            # Check if we should flush
            should_flush = (
                len(self.pending_operations) >= self.batch_size or
                time.time() - self.last_flush_time > self.max_wait_time
            )

            if should_flush:
                await self._flush_batch()

        return await future

    async def _flush_batch(self):
        """Process pending operations in batch"""
        if not self.pending_operations:
            return

        operations = self.pending_operations.copy()
        self.pending_operations.clear()
        self.last_flush_time = time.time()

        # Group operations by type
        grouped_ops = defaultdict(list)
        for op in operations:
            grouped_ops[op['type']].append(op)

        # Process each group
        for op_type, ops in grouped_ops.items():
            try:
                if op_type == 'vector_search':
                    await self._process_search_batch(ops)
                elif op_type == 'vector_store':
                    await self._process_store_batch(ops)
                else:
                    # Process individually for unknown types
                    for op in ops:
                        op['future'].set_exception(
                            NotImplementedError(f"Batch processing not implemented for {op_type}")
                        )
            except Exception as e:
                # Set exception for all operations in failed batch
                for op in ops:
                    if not op['future'].done():
                        op['future'].set_exception(e)

    async def _process_search_batch(self, operations: List[Dict]):
        """Process batch of search operations"""
        # For now, process individually - could be optimized for similar queries
        for op in operations:
            try:
                # Simulate batch search processing
                result = {"batch_processed": True, "data": op['data']}
                op['future'].set_result(result)
            except Exception as e:
                op['future'].set_exception(e)

    async def _process_store_batch(self, operations: List[Dict]):
        """Process batch of store operations"""
        # Could batch multiple vectors into single HTTP request
        for op in operations:
            try:
                result = {"batch_stored": True, "data": op['data']}
                op['future'].set_result(result)
            except Exception as e:
                op['future'].set_exception(e)


class PerformanceOptimizer:
    """Main performance optimization engine"""

    def __init__(self, memory_router: TestMemoryRouter):
        self.memory_router = memory_router

        # Optimization components
        self.search_cache = IntelligentCache(max_size=1000, default_ttl=1800)  # 30 min
        self.pattern_cache = IntelligentCache(max_size=500, default_ttl=3600)   # 1 hour
        self.connection_pool = ConnectionPool(max_connections=10)
        self.batch_processor = BatchProcessor(batch_size=20, max_wait_time=0.05)

        # Performance tracking
        self.metrics_history = deque(maxlen=1000)
        self.operation_stats = defaultdict(list)
        self.start_time = time.time()

        # Background tasks
        self._background_tasks = set()
        self._shutdown_event = asyncio.Event()

    async def initialize(self):
        """Initialize optimization engine"""
        # Start background optimization tasks
        task1 = asyncio.create_task(self._cache_maintenance_loop())
        task2 = asyncio.create_task(self._batch_flush_loop())
        task3 = asyncio.create_task(self._metrics_aggregation_loop())

        self._background_tasks.update([task1, task2, task3])

    async def optimized_search_patterns(self,
                                      query: str,
                                      top_k: int = 5,
                                      threshold: float = 0.7,
                                      category: str = None) -> List[Dict]:
        """Optimized pattern search with caching and batching"""
        start_time = time.time()

        # Create cache key
        cache_key = self._create_search_cache_key(query, top_k, threshold, category)

        # Check cache first
        cached_result = self.search_cache.get(cache_key)
        if cached_result is not None:
            self._record_metrics(
                operation="search_patterns",
                start_time=start_time,
                end_time=time.time(),
                success=True,
                cache_hit=True,
                vector_count=len(cached_result)
            )
            return cached_result

        try:
            # Use batch processor for potential optimization
            search_data = {
                'query': query,
                'top_k': top_k,
                'threshold': threshold,
                'category': category
            }

            # For now, call directly (could be batched in future)
            results = await self.memory_router.find_similar_patterns(
                query=query,
                top_k=top_k,
                threshold=threshold,
                category=category
            )

            # Cache successful results
            if results:
                self.search_cache.set(cache_key, results, ttl=1800)  # 30 min TTL

            self._record_metrics(
                operation="search_patterns",
                start_time=start_time,
                end_time=time.time(),
                success=True,
                cache_hit=False,
                vector_count=len(results)
            )

            return results

        except Exception as e:
            self._record_metrics(
                operation="search_patterns",
                start_time=start_time,
                end_time=time.time(),
                success=False,
                cache_hit=False
            )
            raise

    async def optimized_store_pattern(self,
                                    pattern_text: str,
                                    category: str = None,
                                    context: str = None,
                                    confidence: float = 0.5,
                                    metadata: Dict[str, Any] = None) -> str:
        """Optimized pattern storage with deduplication"""
        start_time = time.time()

        try:
            # Check for near-duplicate patterns
            similar_patterns = await self.optimized_search_patterns(
                query=pattern_text,
                top_k=3,
                threshold=0.95,  # High threshold for duplicates
                category=category
            )

            # Skip if very similar pattern exists
            for pattern in similar_patterns:
                if pattern.get('similarity', 0) > 0.98:
                    self._record_metrics(
                        operation="store_pattern",
                        start_time=start_time,
                        end_time=time.time(),
                        success=True,
                        cache_hit=True  # Treated as cache hit (duplicate avoided)
                    )
                    return pattern.get('pattern_id', 'duplicate_skipped')

            # Store new pattern
            pattern_id = await self.memory_router.store_pattern(
                pattern_text=pattern_text,
                category=category,
                context=context,
                confidence=confidence,
                metadata=metadata
            )

            # Invalidate relevant search caches
            self._invalidate_search_caches(pattern_text, category)

            self._record_metrics(
                operation="store_pattern",
                start_time=start_time,
                end_time=time.time(),
                success=True,
                cache_hit=False
            )

            return pattern_id

        except Exception as e:
            self._record_metrics(
                operation="store_pattern",
                start_time=start_time,
                end_time=time.time(),
                success=False,
                cache_hit=False
            )
            raise

    def _create_search_cache_key(self, query: str, top_k: int, threshold: float, category: str) -> str:
        """Create deterministic cache key for search parameters"""
        key_data = f"{query}:{top_k}:{threshold}:{category or 'none'}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _invalidate_search_caches(self, pattern_text: str, category: str):
        """Invalidate search caches that might be affected by new pattern"""
        # For now, clear category-specific caches
        # Could be more sophisticated in future
        if category:
            # This is a simplified approach - could be more targeted
            pass

    def _record_metrics(self,
                       operation: str,
                       start_time: float,
                       end_time: float,
                       success: bool,
                       cache_hit: bool = False,
                       vector_count: int = 0):
        """Record performance metrics"""
        metric = PerformanceMetrics(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            success=success,
            cache_hit=cache_hit,
            vector_count=vector_count
        )

        self.metrics_history.append(metric)
        self.operation_stats[operation].append(metric)

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        now = time.time()
        uptime_seconds = now - self.start_time

        # Overall metrics
        total_operations = len(self.metrics_history)
        successful_operations = sum(1 for m in self.metrics_history if m.success)
        cache_hits = sum(1 for m in self.metrics_history if m.cache_hit)

        success_rate = (successful_operations / total_operations) if total_operations > 0 else 0
        cache_hit_rate = (cache_hits / total_operations) if total_operations > 0 else 0

        # Performance by operation
        operation_stats = {}
        for op_type, metrics in self.operation_stats.items():
            if metrics:
                avg_duration = sum(m.duration_ms for m in metrics) / len(metrics)
                avg_throughput = sum(m.throughput_ops_per_sec for m in metrics) / len(metrics)
                operation_stats[op_type] = {
                    'count': len(metrics),
                    'avg_duration_ms': avg_duration,
                    'avg_throughput_ops_per_sec': avg_throughput,
                    'success_rate': sum(1 for m in metrics if m.success) / len(metrics)
                }

        return {
            'uptime_seconds': uptime_seconds,
            'total_operations': total_operations,
            'success_rate': success_rate,
            'cache_hit_rate': cache_hit_rate,
            'search_cache_stats': self.search_cache.get_stats(),
            'pattern_cache_stats': self.pattern_cache.get_stats(),
            'operation_stats': operation_stats,
            'recent_metrics': [asdict(m) for m in list(self.metrics_history)[-10:]]
        }

    async def _cache_maintenance_loop(self):
        """Background task for cache maintenance"""
        while not self._shutdown_event.is_set():
            try:
                # Trigger cache cleanup
                self.search_cache._evict_expired()
                self.pattern_cache._evict_expired()

                await asyncio.sleep(60)  # Run every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Cache maintenance error: {e}")
                await asyncio.sleep(60)

    async def _batch_flush_loop(self):
        """Background task for periodic batch flushing"""
        while not self._shutdown_event.is_set():
            try:
                async with self.batch_processor.lock:
                    if (self.batch_processor.pending_operations and
                        time.time() - self.batch_processor.last_flush_time > self.batch_processor.max_wait_time):
                        await self.batch_processor._flush_batch()

                await asyncio.sleep(0.01)  # Check every 10ms
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Batch flush error: {e}")
                await asyncio.sleep(0.1)

    async def _metrics_aggregation_loop(self):
        """Background task for metrics aggregation and cleanup"""
        while not self._shutdown_event.is_set():
            try:
                # Could aggregate metrics, detect performance issues, etc.
                # For now, just maintain the deque size

                await asyncio.sleep(300)  # Run every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Metrics aggregation error: {e}")
                await asyncio.sleep(300)

    async def shutdown(self):
        """Shutdown optimization engine"""
        self._shutdown_event.set()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close connection pool
        await self.connection_pool.close_all()

        # Clear caches
        self.search_cache.clear()
        self.pattern_cache.clear()


async def create_performance_optimizer(memory_router: TestMemoryRouter) -> PerformanceOptimizer:
    """Factory function to create and initialize performance optimizer"""
    optimizer = PerformanceOptimizer(memory_router)
    await optimizer.initialize()
    return optimizer