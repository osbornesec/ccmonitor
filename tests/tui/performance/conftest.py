"""Shared fixtures and utilities for performance testing."""

from __future__ import annotations

import asyncio
import gc
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import psutil
import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


@dataclass
class PerformanceMetrics:
    """Container for performance test results."""

    operation: str
    avg_time_ms: float
    max_time_ms: float
    min_time_ms: float
    memory_usage_mb: float
    cpu_percent: float
    iterations: int

    @property
    def p95_time_ms(self) -> float:
        """Calculate 95th percentile (approximated)."""
        return self.avg_time_ms + (self.max_time_ms - self.avg_time_ms) * 0.95

    def meets_requirements(
        self,
        max_avg_time_ms: float,
        max_p95_time_ms: float,
        max_memory_mb: float | None = None,
    ) -> bool:
        """Check if metrics meet performance requirements."""
        if self.avg_time_ms > max_avg_time_ms:
            return False
        if self.p95_time_ms > max_p95_time_ms:
            return False
        return not (
            max_memory_mb is not None and self.memory_usage_mb > max_memory_mb
        )


class PerformanceBenchmark:
    """Base class for performance benchmarking."""

    def __init__(self) -> None:
        """Initialize performance benchmark."""
        self.results: list[PerformanceMetrics] = []
        self.process = psutil.Process()

    async def measure_operation(
        self,
        operation_name: str,
        operation_func: Callable[[], Awaitable[Any]],
        iterations: int = 100,
        warmup_iterations: int = 10,
    ) -> PerformanceMetrics:
        """Measure performance of an async operation."""
        # Warmup
        for _ in range(warmup_iterations):
            await operation_func()

        # Measure memory before
        self.process.memory_info()  # Trigger memory update
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB

        # Measure performance
        times = []
        cpu_times = []

        for _ in range(iterations):
            cpu_before = self.process.cpu_percent()
            start_time = time.perf_counter()

            await operation_func()

            end_time = time.perf_counter()
            cpu_after = self.process.cpu_percent()

            times.append((end_time - start_time) * 1000)  # Convert to ms
            cpu_times.append(max(0, cpu_after - cpu_before))

        # Measure memory after
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB

        metrics = PerformanceMetrics(
            operation=operation_name,
            avg_time_ms=sum(times) / len(times),
            max_time_ms=max(times),
            min_time_ms=min(times),
            memory_usage_mb=memory_after - memory_before,
            cpu_percent=sum(cpu_times) / len(cpu_times),
            iterations=iterations,
        )

        self.results.append(metrics)
        return metrics

    def assert_performance_requirements(
        self,
        metrics: PerformanceMetrics,
        max_avg_time_ms: float,
        max_p95_time_ms: float,
        max_memory_mb: float | None = None,
    ) -> None:
        """Assert performance meets requirements."""
        assert metrics.avg_time_ms <= max_avg_time_ms, (
            f"{metrics.operation} avg time {metrics.avg_time_ms:.2f}ms "
            f"exceeds limit {max_avg_time_ms}ms"
        )

        assert metrics.p95_time_ms <= max_p95_time_ms, (
            f"{metrics.operation} p95 time {metrics.p95_time_ms:.2f}ms "
            f"exceeds limit {max_p95_time_ms}ms"
        )

        if max_memory_mb:
            assert metrics.memory_usage_mb <= max_memory_mb, (
                f"{metrics.operation} memory usage {metrics.memory_usage_mb:.2f}MB "
                f"exceeds limit {max_memory_mb}MB"
            )


@pytest.fixture
def perf_benchmark() -> PerformanceBenchmark:
    """Provide performance benchmark utility."""
    return PerformanceBenchmark()


@pytest.fixture
def memory_monitor() -> Callable[[], float]:
    """Monitor memory usage during tests."""
    process = psutil.Process()

    def get_memory_usage() -> float:
        """Get current memory usage in MB."""
        return float(process.memory_info().rss / 1024 / 1024)

    # Force garbage collection before measurement
    gc.collect()
    return get_memory_usage


@pytest.fixture
def performance_threshold() -> dict[str, float]:
    """Define performance thresholds for testing."""
    return {
        "navigation_response_ms": 50.0,
        "startup_time_ms": 200.0,
        "memory_usage_mb": 100.0,
        "animation_frame_ms": 16.67,  # 60fps
        "focus_transition_ms": 25.0,
        "modal_open_close_ms": 150.0,
    }


class StressTestRunner:
    """Utility for running stress tests on navigation system."""

    def __init__(self, pilot: Any) -> None:  # noqa: ANN401
        """Initialize stress test runner."""
        self.pilot = pilot
        self.operation_count = 0
        self.error_count = 0

    async def rapid_navigation_sequence(
        self,
        keys: list[str],
        repetitions: int = 10,
        delay_ms: float = 0.01,
    ) -> None:
        """Execute rapid navigation sequence."""
        for _ in range(repetitions):
            for key in keys:
                try:
                    await self.pilot.press(key)
                    await asyncio.sleep(delay_ms / 1000)  # Convert to seconds
                    self.operation_count += 1
                except Exception:  # noqa: BLE001
                    self.error_count += 1

        # Final stabilization wait
        await self.pilot.wait_for_animation()

    @property
    def success_rate(self) -> float:
        """Calculate success rate of operations."""
        if self.operation_count == 0:
            return 0.0
        return (self.operation_count - self.error_count) / self.operation_count


@pytest.fixture
def stress_test_runner() -> Callable[[Any], StressTestRunner]:
    """Create stress test runner for navigation testing."""

    def _create_runner(pilot: Any) -> StressTestRunner:  # noqa: ANN401
        return StressTestRunner(pilot)

    return _create_runner
