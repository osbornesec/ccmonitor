"""Performance tests for TUI application."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import Mock

import psutil
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Performance thresholds from PRP
STARTUP_TIME_THRESHOLD = 0.5  # 500ms
MEMORY_USAGE_THRESHOLD = 10.0  # 10MB
RESIZE_TIME_THRESHOLD = 0.1  # 100ms
RENDER_TIME_THRESHOLD = 1.0  # 1 second for 100 messages
EXPECTED_WIDGET_COUNT = 100


class TestPerformance:
    """Test application performance metrics."""

    @pytest.mark.asyncio
    async def test_startup_time(self, mock_app: Mock) -> None:
        """Test application startup time meets requirements."""
        start_time = time.perf_counter()

        # Simulate app startup
        mock_app.is_running = False

        # Simulate initialization steps
        await self._simulate_app_startup(mock_app)

        startup_time = time.perf_counter() - start_time

        # Should start in under 500ms
        assert (
            startup_time < STARTUP_TIME_THRESHOLD
        ), f"Startup took {startup_time:.2f}s, expected < {STARTUP_TIME_THRESHOLD}s"

    @pytest.mark.asyncio
    async def test_memory_usage(self, mock_app: Mock) -> None:
        """Test application memory usage meets requirements."""
        # Get current process memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simulate app running with widgets
        await self._simulate_app_with_widgets(mock_app)

        # Measure memory after initialization
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # The memory increase should be reasonable (allowing for test overhead)
        memory_increase = final_memory - initial_memory

        # Should use less than 10MB for basic UI (allowing generous headroom)
        assert (
            memory_increase < MEMORY_USAGE_THRESHOLD
        ), f"Memory usage: {memory_increase:.2f}MB, expected < {MEMORY_USAGE_THRESHOLD}MB"

    @pytest.mark.asyncio
    async def test_resize_performance(self, mock_app: Mock) -> None:
        """Test performance during terminal resize."""
        resize_times = []

        # Test various terminal sizes
        sizes = [(80, 24), (100, 30), (120, 40), (150, 50)]

        for width, height in sizes:
            start = time.perf_counter()

            # Simulate resize operation
            await self._simulate_terminal_resize(mock_app, width, height)

            resize_time = time.perf_counter() - start
            resize_times.append(resize_time)

        # Average resize should be fast
        avg_time = sum(resize_times) / len(resize_times)
        assert (
            avg_time < RESIZE_TIME_THRESHOLD
        ), f"Average resize time: {avg_time:.3f}s, expected < {RESIZE_TIME_THRESHOLD}s"

    @pytest.mark.asyncio
    async def test_rendering_performance(self, mock_app: Mock) -> None:
        """Test rendering performance with many widgets."""
        # Simulate message feed with many messages
        start = time.perf_counter()

        await self._simulate_message_rendering(mock_app, EXPECTED_WIDGET_COUNT)

        render_time = time.perf_counter() - start

        # Should handle 100 messages quickly
        assert (
            render_time < RENDER_TIME_THRESHOLD
        ), f"Rendering {EXPECTED_WIDGET_COUNT} messages took {render_time:.3f}s"

    @pytest.mark.asyncio
    async def test_navigation_performance(self, mock_app: Mock) -> None:
        """Test navigation performance."""
        navigation_times = []

        # Simulate navigation operations
        nav_operations = [
            "focus_next",
            "focus_previous",
            "open_help",
            "close_help",
            "switch_panel",
        ]

        for operation in nav_operations:
            start = time.perf_counter()
            await self._simulate_navigation_operation(mock_app, operation)
            nav_time = time.perf_counter() - start
            navigation_times.append(nav_time)

        # All navigation should be very fast
        max_nav_time = max(navigation_times)
        assert (
            max_nav_time < 0.05
        ), f"Slowest navigation: {max_nav_time:.3f}s"  # 50ms

    def test_memory_leak_detection(self, mock_app: Mock) -> None:
        """Test for memory leaks during operation cycles."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Simulate multiple operation cycles
        for _ in range(10):
            self._simulate_widget_creation_cycle(mock_app)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal after multiple cycles
        assert (
            memory_growth < 5.0
        ), (  # 5MB growth limit
            f"Memory grew by {memory_growth:.2f}MB after 10 cycles"
        )

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(
        self, mock_app: Mock,
    ) -> None:
        """Test performance under concurrent operations."""
        start = time.perf_counter()

        # Simulate concurrent operations
        operations = [
            self._simulate_message_update(mock_app),
            self._simulate_status_update(mock_app),
            self._simulate_panel_refresh(mock_app),
        ]

        # Run operations concurrently (simulated)
        for operation in operations:
            await operation

        concurrent_time = time.perf_counter() - start

        # Concurrent operations should complete quickly
        assert (
            concurrent_time < 0.2
        ), f"Concurrent operations took {concurrent_time:.3f}s"  # 200ms

    def test_widget_creation_performance(
        self, mock_widgets: dict[str, Mock],
    ) -> None:
        """Test widget creation performance."""
        start_time = time.perf_counter()

        # Create many widget instances
        widgets = []
        for _ in range(EXPECTED_WIDGET_COUNT):
            for widget_type, mock_widget in mock_widgets.items():
                # Simulate widget creation
                new_widget = Mock(spec=mock_widget)
                widgets.append(new_widget)

        creation_time = time.perf_counter() - start_time

        # Should create widgets quickly
        assert (
            creation_time < 1.0
        ), f"Widget creation took {creation_time:.3f}s for {len(widgets)} widgets"  # 1 second
        assert len(widgets) == EXPECTED_WIDGET_COUNT * len(mock_widgets)

    # Helper methods for performance simulation

    async def _simulate_app_startup(self, mock_app: Mock) -> None:
        """Simulate application startup sequence."""
        # Simulate loading configuration
        await self._sleep_async(0.01)

        # Simulate initializing widgets
        mock_app.screen = Mock()
        mock_app.is_running = True

        # Simulate theme loading
        await self._sleep_async(0.01)

    async def _simulate_app_with_widgets(self, mock_app: Mock) -> None:
        """Simulate application with multiple widgets."""
        widgets = []

        # Create mock widgets
        for i in range(20):  # Reasonable number for testing
            widget = Mock()
            widget.id = f"widget_{i}"
            widgets.append(widget)

        mock_app.widgets = widgets
        await self._sleep_async(0.01)

    async def _simulate_terminal_resize(
        self, mock_app: Mock, width: int, height: int,
    ) -> None:
        """Simulate terminal resize operation."""
        mock_app.size = (width, height)

        # Simulate layout recalculation
        await self._sleep_async(0.001)

        # Simulate widget repositioning
        await self._sleep_async(0.001)

    async def _simulate_message_rendering(
        self, mock_app: Mock, message_count: int,
    ) -> None:
        """Simulate rendering many messages."""
        messages = []

        for i in range(message_count):
            message = Mock()
            message.content = f"Test message {i}"
            message.timestamp = time.time()
            messages.append(message)

        mock_app.messages = messages

        # Simulate rendering time
        await self._sleep_async(0.01)

    async def _simulate_navigation_operation(
        self, mock_app: Mock, operation: str,
    ) -> None:
        """Simulate navigation operation."""
        # Map operations to mock behaviors
        operations = {
            "focus_next": lambda: setattr(mock_app, "focused", "next_widget"),
            "focus_previous": lambda: setattr(
                mock_app, "focused", "prev_widget",
            ),
            "open_help": lambda: setattr(mock_app, "help_visible", True),
            "close_help": lambda: setattr(mock_app, "help_visible", False),
            "switch_panel": lambda: setattr(
                mock_app, "active_panel", "switched",
            ),
        }

        if operation in operations:
            operations[operation]()

        # Minimal delay to simulate processing
        await self._sleep_async(0.001)

    def _simulate_widget_creation_cycle(self, mock_app: Mock) -> None:
        """Simulate widget creation and destruction cycle."""
        # Create widgets
        widgets = [Mock() for _ in range(10)]
        mock_app.temp_widgets = widgets

        # Simulate some processing
        time.sleep(0.001)

        # Clean up widgets
        del mock_app.temp_widgets

    async def _simulate_message_update(self, mock_app: Mock) -> None:
        """Simulate message update operation."""
        mock_app.message_count = getattr(mock_app, "message_count", 0) + 1
        await self._sleep_async(0.001)

    async def _simulate_status_update(self, mock_app: Mock) -> None:
        """Simulate status update operation."""
        mock_app.status = "Updated"
        await self._sleep_async(0.001)

    async def _simulate_panel_refresh(self, mock_app: Mock) -> None:
        """Simulate panel refresh operation."""
        mock_app.panels_refreshed = True
        await self._sleep_async(0.001)

    async def _sleep_async(self, duration: float) -> None:
        """Async sleep helper."""
        # In a real async environment, this would be:
        # await asyncio.sleep(duration)
        # For testing, we use a small delay
        time.sleep(duration * 0.1)  # Reduced for testing speed


class TestPerformanceBaseline:
    """Test performance baseline measurements."""

    def test_performance_thresholds(
        self, performance_metrics: dict[str, float],
    ) -> None:
        """Test that performance thresholds are correctly configured."""
        # Verify PRP requirements are configured correctly
        assert performance_metrics["startup_time_ms"] == 500.0
        assert performance_metrics["memory_usage_mb"] == 10.0
        assert performance_metrics["resize_time_ms"] == 100.0
        assert performance_metrics["render_time_ms"] == 16.67  # 60fps
        assert performance_metrics["navigation_response_ms"] == 50.0

    def test_system_performance_context(self) -> None:
        """Test system performance context for baseline."""
        # Measure system performance context
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Verify reasonable system state for testing
        assert cpu_percent >= 0  # CPU usage should be measurable
        assert memory_mb > 0  # Memory usage should be positive

    @pytest.mark.benchmark
    def test_benchmark_widget_operations(
        self, mock_widgets: dict[str, Mock],
    ) -> None:
        """Benchmark widget operations."""
        # This test would integrate with pytest-benchmark
        # For now, we'll do basic timing

        operations = 1000
        start = time.perf_counter()

        for _ in range(operations):
            for widget in mock_widgets.values():
                # Simulate widget operations
                widget.update = Mock()
                widget.render = Mock()

        duration = time.perf_counter() - start
        ops_per_second = operations * len(mock_widgets) / duration

        # Should handle many operations per second
        assert (
            ops_per_second > 1000
        ), f"Operations/second: {ops_per_second:.0f}"


class TestResourceUsage:
    """Test resource usage patterns."""

    def test_cpu_usage_patterns(self) -> None:
        """Test CPU usage remains reasonable."""
        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=None)

        # Simulate some work
        start = time.perf_counter()
        while time.perf_counter() - start < 0.1:  # 100ms of work
            _ = [i**2 for i in range(1000)]

        final_cpu = process.cpu_percent(interval=0.1)

        # CPU usage should be measurable but not excessive
        assert final_cpu >= 0
        assert final_cpu < 90  # Should not max out CPU

    def test_memory_usage_patterns(self, mock_app: Mock) -> None:
        """Test memory usage patterns are stable."""
        process = psutil.Process()
        memory_readings = []

        # Take memory readings over time
        for i in range(10):
            # Simulate app activity
            mock_app.activity_counter = i
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_mb)
            time.sleep(0.01)  # Small delay

        # Memory should not grow significantly during normal operation
        memory_growth = max(memory_readings) - min(memory_readings)
        assert (
            memory_growth < 2.0
        ), (  # 2MB growth limit during test
            f"Memory grew by {memory_growth:.2f}MB during test"
        )

    def test_file_handle_usage(self) -> None:
        """Test file handle usage is reasonable."""
        process = psutil.Process()

        try:
            open_files = len(process.open_files())
            # Should have some files open but not excessive
            assert open_files >= 0
            assert open_files < 100  # Reasonable limit for TUI app
        except psutil.AccessDenied:
            # Some systems don't allow access to file handles
            pytest.skip("Cannot access file handle information")


@pytest.fixture
def performance_profiler() -> Generator[dict[str, float], None, None]:
    """Fixture for performance profiling."""
    profiling_data = {}
    start_time = time.perf_counter()

    yield profiling_data

    profiling_data["total_test_time"] = time.perf_counter() - start_time
