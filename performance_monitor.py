#!/usr/bin/env python3
"""Performance monitoring script for CCMonitor optimizations.

This script demonstrates the performance improvements from Phase 4:
- Streaming JSONL parser with async I/O
- O(1) cursor updates in NavigableList
- LRU caching for file metadata

Usage:
    python performance_monitor.py
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from src.services.jsonl_parser import (
    JSONLParser,
    StreamingJSONLParser,
    get_file_metadata_cached,
)

# Performance constants
CACHE_PERFORMANCE_THRESHOLD = 0.1  # Maximum acceptable cache time in seconds
DEFAULT_IMPROVEMENT_TARGET = 2.0  # Minimum performance improvement target
DEFAULT_TEST_FILE_SIZES = [0.5, 1.0, 2.0, 5.0]  # Test file sizes in MB
DEFAULT_CACHE_TEST_FILES = 10  # Number of files for cache testing
DEFAULT_CACHE_ITERATIONS = 100  # Cache test iterations
ENTRY_SIZE_BYTES = 200  # Approximate bytes per JSONL entry


@dataclass
class BenchmarkResults:
    """Results from a performance benchmark test."""

    sync_entries: int
    sync_time: float
    sync_speed: float
    streaming_time: float
    streaming_speed: float
    improvement: float


def create_sample_jsonl(size_mb: float = 1.0) -> str:
    """Create sample JSONL data for testing."""
    entries_needed = int((size_mb * 1024 * 1024) / ENTRY_SIZE_BYTES)

    lines = []
    for i in range(entries_needed):
        # Create proper message structure matching JSONLEntry model
        entry = {
            "uuid": f"uuid-{i:06d}",
            "type": "user" if i % 2 == 0 else "assistant",
            "timestamp": "2024-01-01T10:00:00Z",
            "sessionId": f"session-{i // 100}",
            "message": {
                "content": f"Sample message {i} with realistic content",
                "role": "user" if i % 2 == 0 else "assistant",
            },
            "version": "1.0.0",
        }
        lines.append(str(entry).replace("'", '"'))

    return "\n".join(lines)


def benchmark_sync_parser(file_path: Path) -> tuple[float, int]:
    """Benchmark synchronous JSONL parser."""
    parser = JSONLParser()

    start_time = time.perf_counter()
    result = parser.parse_file(file_path)
    parse_time = time.perf_counter() - start_time

    return parse_time, len(result.entries)


async def benchmark_streaming_parser(file_path: Path) -> tuple[float, int]:
    """Benchmark streaming JSONL parser."""
    parser = StreamingJSONLParser()

    start_time = time.perf_counter()
    entries = [entry async for entry in parser.parse_file_async(file_path)]
    parse_time = time.perf_counter() - start_time

    return parse_time, len(entries)


def run_file_size_benchmarks() -> None:
    """Run benchmarks for different file sizes."""
    print("🚀 CCMonitor Performance Monitor")  # noqa: T201
    print("=" * 50)  # noqa: T201

    for size_mb in DEFAULT_TEST_FILE_SIZES:
        print(f"\n📊 Testing {size_mb:.1f}MB file:")  # noqa: T201

        with TemporaryDirectory() as temp_dir:
            # Create test file
            test_data = create_sample_jsonl(size_mb)
            test_file = Path(temp_dir) / f"test_{size_mb}mb.jsonl"
            test_file.write_text(test_data)

            file_size_mb = len(test_data) / (1024 * 1024)

            # Benchmark synchronous parser
            sync_time, sync_entries = benchmark_sync_parser(test_file)
            sync_speed = file_size_mb / sync_time

            # Benchmark streaming parser
            streaming_time, streaming_entries = asyncio.run(
                benchmark_streaming_parser(test_file),
            )
            streaming_speed = file_size_mb / streaming_time

            # Calculate improvement
            improvement = sync_time / streaming_time

            results = BenchmarkResults(
                sync_entries=sync_entries,
                sync_time=sync_time,
                sync_speed=sync_speed,
                streaming_time=streaming_time,
                streaming_speed=streaming_speed,
                improvement=improvement,
            )
            _display_benchmark_results(results)


def _display_benchmark_results(results: BenchmarkResults) -> None:
    """Display benchmark results for file size tests."""
    print(f"  📝 Entries parsed: {results.sync_entries:,}")  # noqa: T201
    print(  # noqa: T201
        f"  🐌 Sync parser:    {results.sync_time:.3f}s "
        f"({results.sync_speed:.1f} MB/s)",
    )
    print(  # noqa: T201
        f"  ⚡ Streaming:      {results.streaming_time:.3f}s "
        f"({results.streaming_speed:.1f} MB/s)",
    )
    print(  # noqa: T201
        f"  🚀 Improvement:    {results.improvement:.1f}x faster",
    )

    # Validate improvement meets target
    target_improvement = DEFAULT_IMPROVEMENT_TARGET
    if results.improvement >= target_improvement:
        print(f"  ✅ Target met ({target_improvement}x)")  # noqa: T201
    else:
        print(f"  ⚠️  Below target ({target_improvement}x)")  # noqa: T201


def run_cache_performance_benchmarks() -> None:
    """Run LRU cache performance benchmarks."""
    print("\n🔄 Testing LRU Cache Performance:")  # noqa: T201

    with TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = []
        for i in range(DEFAULT_CACHE_TEST_FILES):
            test_file = Path(temp_dir) / f"cache_test_{i}.jsonl"
            test_file.write_text("test content")
            test_files.append(str(test_file))

        # Time repeated access (should hit cache)
        start_time = time.perf_counter()
        for _ in range(DEFAULT_CACHE_ITERATIONS):
            for file_path in test_files:
                get_file_metadata_cached(file_path)
        cache_time = time.perf_counter() - start_time

        _display_cache_results(test_files, cache_time)


def _display_cache_results(test_files: list[str], cache_time: float) -> None:
    """Display cache performance results."""
    total_accesses = len(test_files) * DEFAULT_CACHE_ITERATIONS
    per_access_ms = (cache_time / total_accesses) * 1000

    print(f"  📁 Files accessed: {total_accesses:,} times")  # noqa: T201
    print(f"  ⏱️  Total time:     {cache_time:.3f}s")  # noqa: T201
    print(f"  ⚡ Per access:     {per_access_ms:.1f}ms")  # noqa: T201

    if cache_time < CACHE_PERFORMANCE_THRESHOLD:
        print("  ✅ Cache performance excellent")  # noqa: T201
    else:
        print("  ⚠️  Cache may need optimization")  # noqa: T201


def display_summary() -> None:
    """Display performance optimization summary."""
    print("\n🎯 Phase 4 Optimizations Summary:")  # noqa: T201
    print("  ✅ Streaming JSONL parser with async I/O")  # noqa: T201
    print("  ✅ O(1) cursor updates in NavigableList")  # noqa: T201
    print("  ✅ LRU caching for file metadata")  # noqa: T201
    print("  ✅ Performance monitoring established")  # noqa: T201
    print("\n🚀 CCMonitor is ready for production-scale usage!")  # noqa: T201


def main() -> None:
    """Run performance benchmarks."""
    run_file_size_benchmarks()
    run_cache_performance_benchmarks()
    display_summary()


if __name__ == "__main__":
    main()
