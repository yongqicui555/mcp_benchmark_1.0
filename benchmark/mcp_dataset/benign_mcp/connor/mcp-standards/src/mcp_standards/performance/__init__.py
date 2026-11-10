"""Performance optimization and monitoring for V2 pattern extraction

This module provides advanced performance optimization, caching, batch processing,
and scalability testing for the V2 pattern extraction system.
"""

from .optimization_engine import (
    PerformanceOptimizer,
    IntelligentCache,
    ConnectionPool,
    BatchProcessor,
    PerformanceMetrics,
    CacheEntry,
    create_performance_optimizer
)

__all__ = [
    'PerformanceOptimizer',
    'IntelligentCache',
    'ConnectionPool',
    'BatchProcessor',
    'PerformanceMetrics',
    'CacheEntry',
    'create_performance_optimizer',
]

__version__ = "3.0.0"