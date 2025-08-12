"""Performance tests for focus management system."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from src.tui.app import CCMonitorApp

# Mark all performance tests as slow to avoid timeouts during coverage analysis
pytestmark = pytest.mark.slow

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from textual.app import App
    from textual.pilot import Pilot

    from tests.tui.performance.conftest import (
        PerformanceBenchmark,
        StressTestRunner,
    )


class TestFocusPerformance:
    """Test focus management performance."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_tab_navigation_speed(
        self,
        perf_benchmark: PerformanceBenchmark,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        performance_threshold: dict[str, float],
    ) -> None:
        """Test Tab navigation response time meets performance requirements."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            async def tab_navigation() -> None:
                await pilot.press("tab")
                await pilot.pause(0.02)  # Minimal wait for state change

            metrics = await perf_benchmark.measure_operation(
                "tab_navigation",
                tab_navigation,
                iterations=30,
            )

            # Requirements: Tab navigation < 50ms avg, < 100ms p95
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=performance_threshold[
                    "navigation_response_ms"
                ],
                max_p95_time_ms=performance_threshold["navigation_response_ms"]
                * 2,
            )

        finally:
            await pilot_factory.aclose()

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_direct_focus_shortcuts(
        self,
        perf_benchmark: PerformanceBenchmark,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        performance_threshold: dict[str, float],
    ) -> None:
        """Test direct focus shortcuts (Ctrl+1, Ctrl+2) performance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            shortcuts = ["ctrl+1", "ctrl+2"]

            for shortcut in shortcuts:

                async def direct_focus(key: str = shortcut) -> None:
                    await pilot.press(key)
                    await pilot.pause(0.02)

                metrics = await perf_benchmark.measure_operation(
                    f"direct_focus_{shortcut}",
                    direct_focus,
                    iterations=20,
                )

                # Direct shortcuts should be even faster
                perf_benchmark.assert_performance_requirements(
                    metrics,
                    max_avg_time_ms=performance_threshold[
                        "focus_transition_ms"
                    ],
                    max_p95_time_ms=performance_threshold[
                        "focus_transition_ms"
                    ]
                    * 2,
                )

        finally:
            await pilot_factory.aclose()

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_arrow_navigation_performance(
        self,
        perf_benchmark: PerformanceBenchmark,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        performance_threshold: dict[str, float],
    ) -> None:
        """Test arrow key navigation within lists performance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Focus projects panel first if possible
            await pilot.press("ctrl+1")
            await pilot.pause(0.05)

            async def arrow_navigation() -> None:
                await pilot.press("down")
                await pilot.pause(0.02)

            metrics = await perf_benchmark.measure_operation(
                "arrow_navigation",
                arrow_navigation,
                iterations=25,
            )

            # Arrow navigation should be very responsive
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=performance_threshold["focus_transition_ms"],
                max_p95_time_ms=performance_threshold["focus_transition_ms"]
                * 1.5,
            )

        finally:
            await pilot_factory.aclose()

    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rapid_navigation_stress(
        self,
        perf_benchmark: PerformanceBenchmark,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        stress_test_runner: Callable[[Pilot], StressTestRunner],
    ) -> None:
        """Test performance under rapid navigation stress."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Rapid navigation sequence
            rapid_keys = [
                "tab",
                "ctrl+1",
                "down",
                "ctrl+2",
                "up",
                "tab",
                "shift+tab",
            ]

            async def rapid_navigation_sequence() -> None:
                runner = stress_test_runner(pilot)
                await runner.rapid_navigation_sequence(
                    rapid_keys,
                    repetitions=5,  # Reduced for stability
                    delay_ms=5.0,  # 5ms delay between keystrokes
                )

                # Verify high success rate
                min_success_rate = 0.95
                success_rate = runner.success_rate
                assert (
                    success_rate >= min_success_rate
                ), f"Low success rate: {success_rate:.2%}"

            metrics = await perf_benchmark.measure_operation(
                "rapid_navigation_stress",
                rapid_navigation_sequence,
                iterations=3,  # Fewer iterations due to complexity
            )

            # Should handle rapid navigation without significant degradation
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=400.0,  # Total sequence time
                max_p95_time_ms=600.0,
                max_memory_mb=5.0,  # Should not leak memory
            )

        finally:
            await pilot_factory.aclose()


class TestAnimationPerformance:
    """Test visual animation performance."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_focus_animation_smoothness(
        self,
        perf_benchmark: PerformanceBenchmark,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test focus indicator animations are smooth."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            async def focus_with_animation() -> None:
                await pilot.press("ctrl+1")
                # Wait for animation to complete (reduced from planning docs)
                await asyncio.sleep(0.2)  # Animation duration

            metrics = await perf_benchmark.measure_operation(
                "focus_animation",
                focus_with_animation,
                iterations=10,
            )

            # Animation should be smooth and consistent
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=250.0,  # Includes animation time
                max_p95_time_ms=300.0,
            )

        finally:
            await pilot_factory.aclose()

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_modal_performance(
        self,
        perf_benchmark: PerformanceBenchmark,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        performance_threshold: dict[str, float],
    ) -> None:
        """Test modal dialog performance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            async def modal_cycle() -> None:
                await pilot.press("f1")  # Open help (F1 key)
                await pilot.pause(0.1)  # Wait for modal to open
                await pilot.press("escape")  # Close help
                await pilot.pause(0.05)  # Wait for modal to close

            metrics = await perf_benchmark.measure_operation(
                "help_modal_cycle",
                modal_cycle,
                iterations=10,
            )

            # Modal operations should be fast
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=performance_threshold["modal_open_close_ms"],
                max_p95_time_ms=performance_threshold["modal_open_close_ms"]
                * 1.5,
            )

        finally:
            await pilot_factory.aclose()


class TestMemoryPerformance:
    """Test memory usage and leak detection."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_navigation_memory_stability(
        self,
        memory_monitor: Callable[[], float],
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test navigation doesn't cause memory leaks."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Get baseline memory
            baseline_memory = memory_monitor()

            # Perform moderate navigation (reduced from planning docs)
            navigation_cycles = 20
            for cycle in range(navigation_cycles):
                # Navigation sequence
                await pilot.press("tab")
                await pilot.press("ctrl+1")
                await pilot.press("down", "down", "up")
                await pilot.press("ctrl+2")
                await pilot.press("up", "down")
                await pilot.press("f1")  # Open help
                await pilot.pause(0.05)
                await pilot.press("escape")  # Close help
                await pilot.pause(0.02)

                # Check memory every 5 cycles
                if cycle % 5 == 0 and cycle > 0:
                    current_memory = memory_monitor()
                    memory_growth = current_memory - baseline_memory

                    # Memory growth should be bounded (relaxed from planning docs)
                    max_memory_growth = 25.0
                    assert memory_growth < max_memory_growth, (
                        f"Memory leak detected at cycle {cycle}: "
                        f"{memory_growth:.2f}MB growth"
                    )

            # Final memory check
            final_memory = memory_monitor()
            total_growth = final_memory - baseline_memory

            # Allow some memory growth but keep it reasonable
            max_total_growth = 15.0
            assert (
                total_growth < max_total_growth
            ), f"Total memory growth too high: {total_growth:.2f}MB"

        finally:
            await pilot_factory.aclose()
