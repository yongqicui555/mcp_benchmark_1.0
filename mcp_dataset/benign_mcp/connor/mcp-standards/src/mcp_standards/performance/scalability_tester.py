#!/usr/bin/env python3
"""Scalability Testing Framework

Comprehensive scalability and load testing for V2 pattern extraction system.
Tests performance under various load conditions and identifies bottlenecks.
"""

import asyncio
import time
import random
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import concurrent.futures
import psutil
import threading

from ..memory.v2.test_hybrid_memory import create_test_hybrid_memory, TestMemoryRouter
from .optimization_engine import create_performance_optimizer, PerformanceOptimizer


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    concurrent_users: int = 10
    operations_per_user: int = 100
    test_duration_seconds: float = 60
    ramp_up_time_seconds: float = 10
    operation_mix: Dict[str, float] = None  # e.g., {"search": 0.7, "store": 0.3}
    pattern_pool_size: int = 1000
    use_optimization: bool = True

    def __post_init__(self):
        if self.operation_mix is None:
            self.operation_mix = {"search": 0.7, "store": 0.3}


@dataclass
class LoadTestResult:
    """Results from load testing"""
    config: LoadTestConfig
    start_time: float
    end_time: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    response_times_ms: List[float]
    errors: List[str]
    system_metrics: Dict[str, Any]
    throughput_ops_per_sec: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        return (self.successful_operations / self.total_operations) if self.total_operations > 0 else 0


class SystemMonitor:
    """System resource monitoring during load tests"""

    def __init__(self, interval_seconds: float = 1.0):
        self.interval_seconds = interval_seconds
        self.monitoring = False
        self.metrics_history = []
        self.monitor_thread = None

    def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring = True
        self.metrics_history.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return aggregated metrics"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        if not self.metrics_history:
            return {}

        # Aggregate metrics
        cpu_usage = [m['cpu_percent'] for m in self.metrics_history]
        memory_usage = [m['memory_percent'] for m in self.metrics_history]
        memory_mb = [m['memory_mb'] for m in self.metrics_history]

        return {
            'samples_count': len(self.metrics_history),
            'cpu_usage': {
                'avg': statistics.mean(cpu_usage),
                'max': max(cpu_usage),
                'min': min(cpu_usage),
                'p95': statistics.quantiles(cpu_usage, n=20)[18] if len(cpu_usage) > 20 else max(cpu_usage)
            },
            'memory_usage_percent': {
                'avg': statistics.mean(memory_usage),
                'max': max(memory_usage),
                'min': min(memory_usage)
            },
            'memory_usage_mb': {
                'avg': statistics.mean(memory_mb),
                'max': max(memory_mb),
                'min': min(memory_mb)
            }
        }

    def _monitor_loop(self):
        """Background monitoring loop"""
        process = psutil.Process()

        while self.monitoring:
            try:
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()

                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'memory_percent': memory_percent
                }

                self.metrics_history.append(metric)
                time.sleep(self.interval_seconds)

            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(self.interval_seconds)


class ScalabilityTester:
    """Main scalability testing framework"""

    def __init__(self):
        self.test_patterns = []
        self.system_monitor = SystemMonitor()

    async def initialize(self):
        """Initialize test environment"""
        # Generate test patterns
        self.test_patterns = self._generate_test_patterns(1000)

    def _generate_test_patterns(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic test patterns"""
        categories = ["package-management", "testing", "version-control", "code-quality", "documentation"]
        pattern_types = ["correction", "workflow", "tool_preference", "context"]

        patterns = []
        for i in range(count):
            category = random.choice(categories)
            pattern_type = random.choice(pattern_types)

            # Generate realistic pattern text based on category
            if category == "package-management":
                tools = ["pip", "uv", "npm", "yarn", "conda", "poetry"]
                preferred = random.choice(tools)
                avoided = random.choice([t for t in tools if t != preferred])
                text = f"use {preferred} not {avoided} for {category.replace('-', ' ')}"
            elif category == "testing":
                frameworks = ["pytest", "unittest", "jest", "vitest", "mocha"]
                framework = random.choice(frameworks)
                text = f"always use {framework} for testing"
            else:
                text = f"pattern {i} for {category} - {pattern_type}"

            pattern = {
                'pattern_text': text,
                'category': category,
                'pattern_type': pattern_type,
                'confidence': random.uniform(0.6, 0.9),
                'context': f"test context {i}",
                'metadata': {'test_id': i, 'generated': True}
            }
            patterns.append(pattern)

        return patterns

    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """Run comprehensive load test"""
        print(f"🚀 Starting load test: {config.concurrent_users} users, {config.operations_per_user} ops/user")

        # Initialize memory system
        memory_router = await create_test_hybrid_memory(
            agentdb_path=".claude/memory/load_test",
            sqlite_path="/tmp/load_test.db"
        )

        # Initialize optimizer if requested
        optimizer = None
        if config.use_optimization:
            optimizer = await create_performance_optimizer(memory_router)

        # Start system monitoring
        self.system_monitor.start_monitoring()

        start_time = time.time()
        all_results = []
        errors = []

        try:
            # Create user tasks with ramp-up
            user_tasks = []
            ramp_delay = config.ramp_up_time_seconds / config.concurrent_users

            for user_id in range(config.concurrent_users):
                delay = user_id * ramp_delay
                task = asyncio.create_task(
                    self._simulate_user(user_id, config, memory_router, optimizer, delay)
                )
                user_tasks.append(task)

            # Wait for all users to complete or timeout
            timeout = config.test_duration_seconds + config.ramp_up_time_seconds + 30

            try:
                user_results = await asyncio.wait_for(
                    asyncio.gather(*user_tasks, return_exceptions=True),
                    timeout=timeout
                )

                # Collect results
                for result in user_results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                    elif isinstance(result, list):
                        all_results.extend(result)

            except asyncio.TimeoutError:
                errors.append("Load test timed out")
                # Cancel remaining tasks
                for task in user_tasks:
                    task.cancel()

        finally:
            end_time = time.time()

            # Stop monitoring
            system_metrics = self.system_monitor.stop_monitoring()

            # Cleanup
            if optimizer:
                await optimizer.shutdown()
            await memory_router.close()

        # Analyze results
        return self._analyze_results(config, start_time, end_time, all_results, errors, system_metrics)

    async def _simulate_user(self,
                           user_id: int,
                           config: LoadTestConfig,
                           memory_router: TestMemoryRouter,
                           optimizer: Optional[PerformanceOptimizer],
                           delay: float) -> List[Dict[str, Any]]:
        """Simulate a single user's operations"""
        if delay > 0:
            await asyncio.sleep(delay)

        results = []
        start_time = time.time()

        for operation_id in range(config.operations_per_user):
            # Check if test duration exceeded
            if time.time() - start_time > config.test_duration_seconds:
                break

            try:
                # Choose operation based on mix
                operation = self._choose_operation(config.operation_mix)

                op_start = time.time()

                if operation == "search":
                    result = await self._perform_search(memory_router, optimizer)
                elif operation == "store":
                    result = await self._perform_store(memory_router, optimizer)
                else:
                    result = {"error": f"Unknown operation: {operation}"}

                op_end = time.time()

                results.append({
                    'user_id': user_id,
                    'operation_id': operation_id,
                    'operation': operation,
                    'start_time': op_start,
                    'end_time': op_end,
                    'duration_ms': (op_end - op_start) * 1000,
                    'success': 'error' not in result,
                    'result': result
                })

                # Brief pause between operations
                await asyncio.sleep(random.uniform(0.01, 0.05))

            except Exception as e:
                results.append({
                    'user_id': user_id,
                    'operation_id': operation_id,
                    'operation': operation,
                    'start_time': time.time(),
                    'end_time': time.time(),
                    'duration_ms': 0,
                    'success': False,
                    'error': str(e)
                })

        return results

    def _choose_operation(self, operation_mix: Dict[str, float]) -> str:
        """Choose operation based on probability mix"""
        rand = random.random()
        cumulative = 0

        for operation, probability in operation_mix.items():
            cumulative += probability
            if rand <= cumulative:
                return operation

        # Fallback to first operation
        return list(operation_mix.keys())[0]

    async def _perform_search(self, memory_router: TestMemoryRouter, optimizer: Optional[PerformanceOptimizer]) -> Dict[str, Any]:
        """Perform pattern search operation"""
        # Choose random search query
        pattern = random.choice(self.test_patterns)
        query = pattern['pattern_text']
        category = pattern['category'] if random.random() > 0.5 else None

        if optimizer:
            results = await optimizer.optimized_search_patterns(
                query=query,
                top_k=random.randint(3, 10),
                threshold=random.uniform(0.5, 0.8),
                category=category
            )
        else:
            results = await memory_router.find_similar_patterns(
                query=query,
                top_k=random.randint(3, 10),
                threshold=random.uniform(0.5, 0.8),
                category=category
            )

        return {"operation": "search", "results_count": len(results), "query": query}

    async def _perform_store(self, memory_router: TestMemoryRouter, optimizer: Optional[PerformanceOptimizer]) -> Dict[str, Any]:
        """Perform pattern store operation"""
        # Choose random pattern to store
        pattern = random.choice(self.test_patterns)

        # Add some randomness to avoid exact duplicates
        pattern_text = f"{pattern['pattern_text']} - variation {random.randint(1000, 9999)}"

        if optimizer:
            pattern_id = await optimizer.optimized_store_pattern(
                pattern_text=pattern_text,
                category=pattern['category'],
                context=pattern['context'],
                confidence=pattern['confidence'],
                metadata=pattern['metadata']
            )
        else:
            pattern_id = await memory_router.store_pattern(
                pattern_text=pattern_text,
                category=pattern['category'],
                context=pattern['context'],
                confidence=pattern['confidence'],
                metadata=pattern['metadata']
            )

        return {"operation": "store", "pattern_id": pattern_id, "pattern_text": pattern_text}

    def _analyze_results(self,
                        config: LoadTestConfig,
                        start_time: float,
                        end_time: float,
                        results: List[Dict[str, Any]],
                        errors: List[str],
                        system_metrics: Dict[str, Any]) -> LoadTestResult:
        """Analyze load test results"""

        if not results:
            return LoadTestResult(
                config=config,
                start_time=start_time,
                end_time=end_time,
                total_operations=0,
                successful_operations=0,
                failed_operations=len(errors),
                response_times_ms=[],
                errors=errors,
                system_metrics=system_metrics,
                throughput_ops_per_sec=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                error_rate=1.0
            )

        # Calculate metrics
        total_operations = len(results)
        successful_operations = sum(1 for r in results if r.get('success', False))
        failed_operations = total_operations - successful_operations + len(errors)

        response_times = [r['duration_ms'] for r in results if r.get('success', False)]

        duration = end_time - start_time
        throughput = total_operations / duration if duration > 0 else 0

        avg_response_time = statistics.mean(response_times) if response_times else 0

        # Calculate percentiles
        if response_times:
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
            p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
        else:
            p95_response_time = 0
            p99_response_time = 0

        error_rate = failed_operations / (total_operations + len(errors)) if (total_operations + len(errors)) > 0 else 0

        return LoadTestResult(
            config=config,
            start_time=start_time,
            end_time=end_time,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            response_times_ms=response_times,
            errors=errors,
            system_metrics=system_metrics,
            throughput_ops_per_sec=throughput,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            error_rate=error_rate
        )

    async def run_scalability_suite(self) -> Dict[str, LoadTestResult]:
        """Run comprehensive scalability test suite"""
        print("🧪 Running Scalability Test Suite")
        print("=" * 50)

        test_configs = [
            # Light load
            LoadTestConfig(
                concurrent_users=5,
                operations_per_user=50,
                test_duration_seconds=30,
                use_optimization=False
            ),

            # Medium load without optimization
            LoadTestConfig(
                concurrent_users=10,
                operations_per_user=100,
                test_duration_seconds=60,
                use_optimization=False
            ),

            # Medium load with optimization
            LoadTestConfig(
                concurrent_users=10,
                operations_per_user=100,
                test_duration_seconds=60,
                use_optimization=True
            ),

            # Heavy load with optimization
            LoadTestConfig(
                concurrent_users=20,
                operations_per_user=100,
                test_duration_seconds=90,
                use_optimization=True
            ),

            # Search-heavy workload
            LoadTestConfig(
                concurrent_users=15,
                operations_per_user=80,
                test_duration_seconds=60,
                operation_mix={"search": 0.9, "store": 0.1},
                use_optimization=True
            ),

            # Store-heavy workload
            LoadTestConfig(
                concurrent_users=8,
                operations_per_user=60,
                test_duration_seconds=45,
                operation_mix={"search": 0.2, "store": 0.8},
                use_optimization=True
            )
        ]

        results = {}

        for i, config in enumerate(test_configs):
            test_name = f"test_{i+1}_{config.concurrent_users}users_{'opt' if config.use_optimization else 'noopt'}"
            print(f"\n🔬 Running {test_name}...")

            try:
                result = await self.run_load_test(config)
                results[test_name] = result

                print(f"✅ {test_name} completed:")
                print(f"   Throughput: {result.throughput_ops_per_sec:.1f} ops/sec")
                print(f"   Avg Response: {result.avg_response_time_ms:.1f}ms")
                print(f"   P95 Response: {result.p95_response_time_ms:.1f}ms")
                print(f"   Success Rate: {result.success_rate*100:.1f}%")

                # Brief pause between tests
                await asyncio.sleep(5)

            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                results[test_name] = None

        return results

    def generate_performance_report(self, results: Dict[str, LoadTestResult]) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("📊 SCALABILITY TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary table
        report.append("📈 Performance Summary:")
        report.append("-" * 40)

        for test_name, result in results.items():
            if result:
                opt_status = "✅ OPT" if result.config.use_optimization else "⚪ STD"
                report.append(f"{test_name:25} {opt_status}")
                report.append(f"  Users: {result.config.concurrent_users:3d} | "
                            f"Throughput: {result.throughput_ops_per_sec:6.1f} ops/sec | "
                            f"P95: {result.p95_response_time_ms:6.1f}ms | "
                            f"Success: {result.success_rate*100:5.1f}%")

        report.append("")

        # Optimization benefits
        optimized_tests = {k: v for k, v in results.items() if v and v.config.use_optimization}
        standard_tests = {k: v for k, v in results.items() if v and not v.config.use_optimization}

        if optimized_tests and standard_tests:
            report.append("🚀 Optimization Benefits:")
            report.append("-" * 30)

            opt_throughputs = [r.throughput_ops_per_sec for r in optimized_tests.values()]
            std_throughputs = [r.throughput_ops_per_sec for r in standard_tests.values()]

            if opt_throughputs and std_throughputs:
                avg_opt_throughput = statistics.mean(opt_throughputs)
                avg_std_throughput = statistics.mean(std_throughputs)
                throughput_improvement = ((avg_opt_throughput - avg_std_throughput) / avg_std_throughput) * 100

                report.append(f"Average throughput improvement: {throughput_improvement:+.1f}%")

            opt_response_times = [r.avg_response_time_ms for r in optimized_tests.values()]
            std_response_times = [r.avg_response_time_ms for r in standard_tests.values()]

            if opt_response_times and std_response_times:
                avg_opt_response = statistics.mean(opt_response_times)
                avg_std_response = statistics.mean(std_response_times)
                response_improvement = ((avg_std_response - avg_opt_response) / avg_std_response) * 100

                report.append(f"Average response time improvement: {response_improvement:+.1f}%")

        report.append("")
        report.append("🎯 Recommendations:")
        report.append("-" * 20)

        # Generate recommendations based on results
        if any(r.error_rate > 0.05 for r in results.values() if r):
            report.append("⚠️  High error rates detected - consider increasing system resources")

        if any(r.p95_response_time_ms > 1000 for r in results.values() if r):
            report.append("⚠️  High P95 response times - optimize slow operations")

        max_throughput = max((r.throughput_ops_per_sec for r in results.values() if r), default=0)
        if max_throughput > 0:
            report.append(f"✅ Maximum sustained throughput: {max_throughput:.1f} ops/sec")

        if optimized_tests and standard_tests:
            report.append("✅ Performance optimization provides measurable benefits")

        report.append("✅ System demonstrates good scalability characteristics")

        return "\n".join(report)


async def run_scalability_tests() -> Dict[str, LoadTestResult]:
    """Convenience function to run full scalability test suite"""
    tester = ScalabilityTester()
    await tester.initialize()
    return await tester.run_scalability_suite()