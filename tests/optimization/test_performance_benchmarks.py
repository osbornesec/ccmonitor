"""Performance benchmarks for recent optimizations."""

from __future__ import annotations

import asyncio
import gc
import time
from typing import TYPE_CHECKING

import psutil
import pytest
from textual.widgets import Label, ListItem

from src.services.jsonl_parser import (
    JSONLParser,
    StreamingJSONLParser,
    get_file_metadata_cached,
)
from src.tui.widgets.navigable_list import NavigableList

if TYPE_CHECKING:
    from pathlib import Path

# Performance benchmarks for Phase 4 optimizations
JSONL_PARSE_SPEED_TARGET = 5.0  # MB/s minimum target
STREAMING_PARSE_IMPROVEMENT = 2.0  # At least 2x faster than sync
CURSOR_UPDATE_TIME_TARGET = 0.001  # 1ms for O(1) cursor updates
LARGE_LIST_SIZE = 1000  # Items for testing O(1) performance
CACHE_TIME_THRESHOLD = 0.1  # Maximum cache time in seconds
NAVIGATION_TIME_THRESHOLD = 0.01  # Navigation time threshold
MEMORY_GROWTH_LIMIT = 50.0  # Memory growth limit in MB
TOTAL_MEMORY_LIMIT = 20.0  # Total memory limit in MB
END_TO_END_TIME_LIMIT = 2.0  # End-to-end time limit in seconds


class TestJSONLParserBenchmarks:
    """Benchmark JSONL parser optimizations."""

    def create_test_jsonl_data(self, size_mb: float = 1.0) -> str:
        """Create test JSONL data of specified size.

        Args:
            size_mb: Target size in megabytes

        Returns:
            JSONL content as string

        """
        # Approximate entry size: ~200 bytes
        entries_needed = int((size_mb * 1024 * 1024) / 200)

        lines = []
        for i in range(entries_needed):
            # Create proper message structure matching JSONLEntry model
            entry = {
                "uuid": f"test-uuid-{i:06d}",
                "type": "user" if i % 2 == 0 else "assistant",
                "timestamp": "2024-01-01T10:00:00Z",
                "sessionId": f"session-{i // 100}",
                "message": {
                    "content": (
                        f"Test message {i} with some content to make it realistic"
                    ),
                    "role": "user" if i % 2 == 0 else "assistant",
                },
                "cwd": "/test/path",
                "version": "1.0.0",
            }
            lines.append(str(entry).replace("'", '"'))

        return "\n".join(lines)

    @pytest.mark.benchmark
    def test_sync_jsonl_parser_performance(self, tmp_path: Path) -> None:
        """Benchmark synchronous JSONL parser performance."""
        # Create 2MB test file
        test_data = self.create_test_jsonl_data(2.0)
        test_file = tmp_path / "test_sync.jsonl"
        test_file.write_text(test_data)

        parser = JSONLParser()

        start_time = time.perf_counter()
        result = parser.parse_file(test_file)
        parse_time = time.perf_counter() - start_time

        # Calculate speed
        file_size_mb = len(test_data) / (1024 * 1024)
        parse_speed = file_size_mb / parse_time

        # Verify performance meets baseline
        assert parse_speed >= 1.0, (
            f"Sync parser too slow: {parse_speed:.2f} MB/s, "
            f"expected >= 1.0 MB/s"
        )

        # Verify correctness
        assert len(result.entries) > 0
        assert result.statistics.valid_entries > 0
        assert result.statistics.parse_errors == 0

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_streaming_parser_performance(self, tmp_path: Path) -> None:
        """Benchmark streaming parser performance improvement."""
        # Create 2MB test file
        test_data = self.create_test_jsonl_data(2.0)
        test_file = tmp_path / "test_streaming.jsonl"
        test_file.write_text(test_data)

        # Test streaming parser
        streaming_parser = StreamingJSONLParser()

        start_time = time.perf_counter()
        entries = [
            entry
            async for entry in streaming_parser.parse_file_async(test_file)
        ]
        streaming_time = time.perf_counter() - start_time

        # Calculate speed
        file_size_mb = len(test_data) / (1024 * 1024)
        streaming_speed = file_size_mb / streaming_time

        # Should be significantly faster than target
        assert streaming_speed >= JSONL_PARSE_SPEED_TARGET, (
            f"Streaming parser too slow: {streaming_speed:.2f} MB/s, "
            f"expected >= {JSONL_PARSE_SPEED_TARGET} MB/s"
        )

        # Verify correctness
        assert len(entries) > 0

    @pytest.mark.benchmark
    def test_lru_cache_performance(self, tmp_path: Path) -> None:
        """Test LRU cache performance for file metadata."""
        # Create test files
        test_files = []
        for i in range(10):
            test_file = tmp_path / f"cache_test_{i}.jsonl"
            test_file.write_text("test content")
            test_files.append(str(test_file))

        # Time cache hits vs misses
        start_time = time.perf_counter()
        for _ in range(100):  # Simulate many accesses
            for file_path in test_files:
                get_file_metadata_cached(file_path)
        cache_time = time.perf_counter() - start_time

        # Should be very fast due to caching
        assert (
            cache_time < CACHE_TIME_THRESHOLD
        ), f"LRU cache too slow: {cache_time:.3f}s for 1000 accesses"


class TestNavigableListBenchmarks:
    """Benchmark NavigableList cursor optimizations."""

    def create_test_list_items(self, count: int) -> list[ListItem]:
        """Create test list items."""
        items = []
        for i in range(count):
            # Create ListItem with Label widget as content
            item = ListItem(Label(f"Test Item {i}"))
            items.append(item)
        return items

    @pytest.mark.benchmark
    def test_cursor_update_o1_performance(self) -> None:
        """Test O(1) cursor update performance."""
        # Create large list
        items = self.create_test_list_items(LARGE_LIST_SIZE)
        nav_list = NavigableList(*items)

        # Test O(1) cursor updates by measuring navigation performance
        cursor_positions = [100, 500, 200, 800, 50, 900, 1]

        start_time = time.perf_counter()
        for pos in cursor_positions:
            # Use public API instead of private methods
            nav_list.set_cursor_index(pos, scroll=False)
        total_time = time.perf_counter() - start_time

        avg_time = total_time / len(cursor_positions)

        # Should be very fast O(1) operations
        assert avg_time < CURSOR_UPDATE_TIME_TARGET, (
            f"Cursor updates too slow: {avg_time:.4f}s per update, "
            f"expected < {CURSOR_UPDATE_TIME_TARGET}s"
        )

    @pytest.mark.benchmark
    def test_large_list_navigation_performance(self) -> None:
        """Test navigation performance on large lists."""
        # Create very large list
        items = self.create_test_list_items(LARGE_LIST_SIZE * 2)
        nav_list = NavigableList(*items)

        # Test rapid navigation
        start_time = time.perf_counter()

        # Simulate rapid user navigation
        for i in range(100):
            nav_list.action_cursor_down()
            if i % 10 == 0:
                nav_list.action_cursor_up()
            if i % 25 == 0:
                nav_list.action_page_down()

        navigation_time = time.perf_counter() - start_time
        avg_per_action = navigation_time / 100

        # Navigation should remain fast even with large lists
        assert (
            avg_per_action < NAVIGATION_TIME_THRESHOLD
        ), f"Navigation too slow on large list: {avg_per_action:.4f}s per action"


class TestMemoryUsageBenchmarks:
    """Test memory usage patterns for optimizations."""

    @pytest.mark.benchmark
    def test_streaming_memory_usage(self, tmp_path: Path) -> None:
        """Test streaming parser uses constant memory."""
        # Create large test file (5MB)
        test_data = TestJSONLParserBenchmarks().create_test_jsonl_data(5.0)
        test_file = tmp_path / "memory_test.jsonl"
        test_file.write_text(test_data)

        process = psutil.Process()

        # Force garbage collection for clean baseline
        gc.collect()
        initial_memory = process.memory_info().rss / (1024 * 1024)

        # Parse with streaming parser
        parser = StreamingJSONLParser()
        entry_count = 0

        async def stream_parse() -> None:
            nonlocal entry_count
            async for _entry in parser.parse_file_async(test_file):
                entry_count += 1
                # Check memory periodically
                if entry_count % 1000 == 0:
                    current_memory = process.memory_info().rss / (1024 * 1024)
                    memory_growth = current_memory - initial_memory

                    # Memory should not grow significantly
                    assert (
                        memory_growth < MEMORY_GROWTH_LIMIT
                    ), f"Memory leak detected: {memory_growth:.1f}MB growth"

        asyncio.run(stream_parse())

        # Final memory check
        final_memory = process.memory_info().rss / (1024 * 1024)
        total_growth = final_memory - initial_memory

        # Should have minimal memory growth
        assert (
            total_growth < TOTAL_MEMORY_LIMIT
        ), f"Excessive memory usage: {total_growth:.1f}MB growth"


@pytest.mark.benchmark
class TestIntegratedPerformance:
    """Integration performance tests combining multiple optimizations."""

    def test_end_to_end_performance(self, tmp_path: Path) -> None:
        """Test complete performance from parsing to UI rendering."""
        # This would test the full pipeline:
        # 1. Streaming JSONL parse
        # 2. NavigableList with O(1) cursor updates
        # 3. Memory efficiency

        # Create realistic test data
        test_data = TestJSONLParserBenchmarks().create_test_jsonl_data(3.0)
        test_file = tmp_path / "integration_test.jsonl"
        test_file.write_text(test_data)

        start_time = time.perf_counter()

        # Parse with streaming parser
        parser = StreamingJSONLParser()

        async def full_pipeline() -> int:
            entries = [
                entry async for entry in parser.parse_file_async(test_file)
            ]

            # Create UI list (simulate)
            items = [
                ListItem(Label(f"Entry {i}"))
                for i in range(min(100, len(entries)))
            ]
            nav_list = NavigableList(*items)

            # Simulate user navigation
            for _i in range(20):
                nav_list.action_cursor_down()

            return len(entries)

        entry_count = asyncio.run(full_pipeline())
        total_time = time.perf_counter() - start_time

        # End-to-end should be fast
        assert (
            total_time < END_TO_END_TIME_LIMIT
        ), f"End-to-end too slow: {total_time:.2f}s for {entry_count} entries"
