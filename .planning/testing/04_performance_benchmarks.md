# Performance Benchmarking & Load Testing

## Overview

This document outlines comprehensive performance testing strategies for CCMonitor's navigation system. These tests ensure responsive keyboard navigation, efficient focus management, and smooth animations under various load conditions.

## Performance Testing Architecture

### Testing Framework Setup
```python
# tests/tui/performance/conftest.py
import pytest
import time
import psutil
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass
from src.tui.app import CCMonitorApp

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

class PerformanceBenchmark:
    """Base class for performance benchmarking."""
    
    def __init__(self):
        self.results: List[PerformanceMetrics] = []
        self.process = psutil.Process()
    
    async def measure_operation(
        self,
        operation_name: str,
        operation_func,
        iterations: int = 100,
        warmup_iterations: int = 10
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
            cpu_times.append(cpu_after - cpu_before)
        
        # Measure memory after
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return PerformanceMetrics(
            operation=operation_name,
            avg_time_ms=sum(times) / len(times),
            max_time_ms=max(times),
            min_time_ms=min(times),
            memory_usage_mb=memory_after - memory_before,
            cpu_percent=sum(cpu_times) / len(cpu_times),
            iterations=iterations
        )
    
    def assert_performance_requirements(
        self,
        metrics: PerformanceMetrics,
        max_avg_time_ms: float,
        max_p95_time_ms: float,
        max_memory_mb: float = None
    ):
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
def perf_benchmark():
    """Performance benchmark fixture."""
    return PerformanceBenchmark()
```

## 1. Focus Management Performance Tests

### Focus Chain Building and Navigation
```python
# tests/tui/performance/test_focus_performance.py
import pytest
import asyncio
from tests.tui.performance.conftest import PerformanceBenchmark
from src.tui.utils.focus import FocusManager, FocusableWidget
from src.tui.app import CCMonitorApp

class TestFocusPerformance:
    """Test focus management performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_tab_navigation_speed(self, perf_benchmark: PerformanceBenchmark):
        """Test Tab navigation response time meets performance requirements."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            async def tab_navigation():
                await pilot.press("tab")
                await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "tab_navigation",
                tab_navigation,
                iterations=50
            )
            
            # Requirements: Tab navigation < 50ms avg, < 100ms p95
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=50.0,
                max_p95_time_ms=100.0
            )
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio  
    async def test_direct_focus_shortcuts(self, perf_benchmark: PerformanceBenchmark):
        """Test direct focus shortcuts (Ctrl+1, Ctrl+2) performance."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            shortcuts = ["ctrl+1", "ctrl+2"]
            
            for shortcut in shortcuts:
                async def direct_focus():
                    await pilot.press(shortcut)
                    await pilot.wait_for_animation()
                
                metrics = await perf_benchmark.measure_operation(
                    f"direct_focus_{shortcut}",
                    direct_focus,
                    iterations=30
                )
                
                # Direct shortcuts should be even faster
                perf_benchmark.assert_performance_requirements(
                    metrics,
                    max_avg_time_ms=30.0,
                    max_p95_time_ms=60.0
                )
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_focus_chain_rebuild_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test focus chain rebuilding after layout changes."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            async def rebuild_focus_chain():
                # Trigger focus chain rebuild
                main_screen = pilot.app.screen
                if hasattr(main_screen, 'focus_manager'):
                    main_screen.focus_manager.rebuild_focus_chains()
                await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "focus_chain_rebuild",
                rebuild_focus_chain,
                iterations=20
            )
            
            # Focus chain rebuild should be fast
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=20.0,
                max_p95_time_ms=50.0,
                max_memory_mb=5.0  # Should not use much memory
            )
    
    @pytest.mark.benchmark
    def test_focus_manager_registration_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test performance of registering many focusable widgets."""
        focus_manager = FocusManager()
        
        def register_widget_batch():
            # Register batch of 100 widgets
            for i in range(100):
                widget = FocusableWidget(f"widget_{i}", f"Widget {i}")
                focus_manager.register_focusable("test_group", widget)
        
        # This is synchronous, so we measure differently
        times = []
        for _ in range(10):  # 10 batches of 100 widgets each
            start_time = time.perf_counter()
            register_widget_batch()
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Should handle 100 widgets in < 10ms
        assert avg_time < 10.0, f"Widget registration too slow: {avg_time:.2f}ms"
        assert max_time < 20.0, f"Max registration time too slow: {max_time:.2f}ms"
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_arrow_navigation_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test arrow key navigation within lists performance."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus projects panel first
            await pilot.press("ctrl+1")
            await pilot.wait_for_animation()
            
            async def arrow_navigation():
                await pilot.press("down")
                await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "arrow_navigation",
                arrow_navigation,
                iterations=50
            )
            
            # Arrow navigation should be very responsive
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=25.0,
                max_p95_time_ms=50.0
            )


class TestFocusScalabilityPerformance:
    """Test focus management under scale."""
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_large_focus_group_performance(self):
        """Test performance with large numbers of focusable widgets."""
        focus_manager = FocusManager()
        
        # Create large focus group
        large_group_sizes = [100, 500, 1000, 2000]
        
        for size in large_group_sizes:
            # Setup
            group_name = f"large_group_{size}"
            widgets = [
                FocusableWidget(f"widget_{i}", f"Widget {i}")
                for i in range(size)
            ]
            
            # Measure registration time
            start_time = time.perf_counter()
            for widget in widgets:
                focus_manager.register_focusable(group_name, widget)
            registration_time = (time.perf_counter() - start_time) * 1000
            
            # Measure focus operations
            start_time = time.perf_counter()
            focus_manager.focus_first_available()
            focus_first_time = (time.perf_counter() - start_time) * 1000
            
            start_time = time.perf_counter()
            next_widget = focus_manager.move_focus(FocusDirection.NEXT)
            focus_next_time = (time.perf_counter() - start_time) * 1000
            
            # Performance should scale reasonably
            # O(log n) or O(1) ideally, O(n) acceptable for some operations
            print(f"Size {size}: Registration {registration_time:.2f}ms, "
                  f"Focus First {focus_first_time:.2f}ms, "
                  f"Focus Next {focus_next_time:.2f}ms")
            
            # Assertions for performance requirements
            assert registration_time < size * 0.1, f"Registration too slow for {size} widgets"
            assert focus_first_time < 10.0, f"Focus first too slow for {size} widgets"
            assert focus_next_time < 5.0, f"Focus next too slow for {size} widgets"
            
            # Cleanup
            focus_manager.clear_all()
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rapid_navigation_stress(self, perf_benchmark: PerformanceBenchmark):
        """Test performance under rapid navigation stress."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Rapid navigation sequence
            rapid_keys = ["tab", "ctrl+1", "down", "ctrl+2", "up", "tab", "shift+tab"] * 10
            
            async def rapid_navigation_sequence():
                for key in rapid_keys:
                    await pilot.press(key)
                    # Minimal wait to simulate rapid input
                    await asyncio.sleep(0.01)
                await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "rapid_navigation_stress",
                rapid_navigation_sequence,
                iterations=5  # Fewer iterations due to complexity
            )
            
            # Should handle rapid navigation without degradation
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=500.0,  # Total sequence time
                max_p95_time_ms=800.0,
                max_memory_mb=10.0  # Should not leak memory
            )
```

## 2. Animation and Visual Performance Tests

### Focus Indicator Animations
```python
# tests/tui/performance/test_animation_performance.py
import pytest
from tests.tui.performance.conftest import PerformanceBenchmark
from src.tui.app import CCMonitorApp

class TestAnimationPerformance:
    """Test visual animation performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_focus_animation_smoothness(self, perf_benchmark: PerformanceBenchmark):
        """Test focus indicator animations are smooth."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            async def focus_with_animation():
                await pilot.press("ctrl+1")
                # Wait for animation to complete
                await asyncio.sleep(0.4)  # Animation duration
            
            metrics = await perf_benchmark.measure_operation(
                "focus_animation",
                focus_with_animation,
                iterations=20
            )
            
            # Animation should be smooth and consistent
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=450.0,  # Includes animation time
                max_p95_time_ms=500.0
            )
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cursor_animation_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test NavigableList cursor animations."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus projects list
            await pilot.press("ctrl+1")
            await pilot.wait_for_animation()
            
            async def cursor_move_with_animation():
                await pilot.press("down")
                await asyncio.sleep(0.3)  # Cursor animation time
            
            metrics = await perf_benchmark.measure_operation(
                "cursor_animation",
                cursor_move_with_animation,
                iterations=25
            )
            
            # Cursor animation should be responsive
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=350.0,
                max_p95_time_ms=400.0
            )
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_theme_transition_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test dark/light mode transition performance."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            async def theme_transition():
                await pilot.press("d")  # Toggle theme
                await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "theme_transition",
                theme_transition,
                iterations=10  # Fewer iterations, expensive operation
            )
            
            # Theme transitions should be reasonably fast
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=200.0,
                max_p95_time_ms=300.0,
                max_memory_mb=15.0  # Theme changes may use more memory
            )


class TestModalPerformance:
    """Test modal dialog performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_help_modal_open_close_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test help modal open/close performance."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            async def modal_cycle():
                await pilot.press("h")  # Open help
                await pilot.wait_for_screen("help")
                await pilot.press("escape")  # Close help
                await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "help_modal_cycle",
                modal_cycle,
                iterations=15
            )
            
            # Modal operations should be fast
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=150.0,
                max_p95_time_ms=250.0
            )
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_modal_focus_trap_performance(self, perf_benchmark: PerformanceBenchmark):
        """Test modal focus trapping performance."""
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Open help modal
            await pilot.press("h")
            await pilot.wait_for_screen("help")
            
            async def modal_tab_cycle():
                # Tab through modal elements
                for _ in range(4):  # Number of focusable elements
                    await pilot.press("tab")
                    await pilot.wait_for_animation()
            
            metrics = await perf_benchmark.measure_operation(
                "modal_focus_cycling",
                modal_tab_cycle,
                iterations=20
            )
            
            # Focus cycling within modal should be fast
            perf_benchmark.assert_performance_requirements(
                metrics,
                max_avg_time_ms=100.0,
                max_p95_time_ms=150.0
            )
```

## 3. Memory Performance Tests

### Memory Usage and Leak Detection
```python
# tests/tui/performance/test_memory_performance.py
import pytest
import gc
import psutil
from tests.tui.performance.conftest import PerformanceBenchmark
from src.tui.app import CCMonitorApp
from src.tui.utils.focus import FocusManager

class TestMemoryPerformance:
    """Test memory usage and leak detection."""
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_navigation_memory_stability(self):
        """Test navigation doesn't cause memory leaks."""
        process = psutil.Process()
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Get baseline memory
            gc.collect()  # Force garbage collection
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform extensive navigation
            navigation_cycles = 50
            for cycle in range(navigation_cycles):
                # Navigation sequence
                await pilot.press("tab")
                await pilot.press("ctrl+1")
                await pilot.press("down", "down", "up")
                await pilot.press("ctrl+2")
                await pilot.press("up", "down")
                await pilot.press("h")  # Open help
                await pilot.wait_for_screen("help")
                await pilot.press("2", "3", "1")  # Switch tabs
                await pilot.press("escape")  # Close help
                await pilot.wait_for_animation()
                
                # Check memory every 10 cycles
                if cycle % 10 == 0:
                    gc.collect()
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - baseline_memory
                    
                    print(f"Cycle {cycle}: Memory {current_memory:.2f}MB "
                          f"(+{memory_growth:.2f}MB from baseline)")
                    
                    # Memory growth should be bounded
                    assert memory_growth < 50.0, f"Memory leak detected: {memory_growth:.2f}MB growth"
            
            # Final memory check
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            total_growth = final_memory - baseline_memory
            
            assert total_growth < 20.0, f"Total memory growth too high: {total_growth:.2f}MB"
    
    @pytest.mark.benchmark
    def test_focus_manager_memory_efficiency(self):
        """Test FocusManager memory efficiency with many widgets."""
        import sys
        
        focus_manager = FocusManager()
        
        # Measure memory before
        gc.collect()
        initial_refs = len(gc.get_objects())
        
        # Add many widgets
        widget_count = 1000
        for i in range(widget_count):
            from src.tui.utils.focus import FocusableWidget
            widget = FocusableWidget(f"widget_{i}", f"Widget {i}")
            focus_manager.register_focusable("test_group", widget)
        
        # Measure memory after
        gc.collect()
        after_refs = len(gc.get_objects())
        ref_growth = after_refs - initial_refs
        
        # Should not create excessive object references
        # Allow some growth but not linear with widget count
        assert ref_growth < widget_count * 2, f"Too many object references: {ref_growth}"
        
        # Cleanup and verify references are released
        focus_manager.clear_all()
        gc.collect()
        
        cleanup_refs = len(gc.get_objects())
        remaining_growth = cleanup_refs - initial_refs
        
        # Most references should be cleaned up
        assert remaining_growth < widget_count * 0.1, f"Memory not properly cleaned up"
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_widget_lifecycle_memory(self):
        """Test widget creation/destruction doesn't leak memory."""
        from src.tui.widgets.navigable_list import NavigableList
        from textual.widgets import ListItem, Static
        
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        # Create and destroy widgets repeatedly
        for cycle in range(20):
            # Create large NavigableList
            items = [
                ListItem(Static(f"Item {i}"), id=f"item-{i}")
                for i in range(100)
            ]
            nav_list = NavigableList(*items, id="test-list")
            
            # Use the widget briefly
            async with nav_list.run_test() as pilot:
                await pilot.press("down", "down", "up")
                await pilot.wait_for_animation()
            
            # Widget should be garbage collected
            del nav_list
            del items
            gc.collect()
        
        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory
        
        # Should not accumulate significant memory
        assert memory_growth < 10.0, f"Widget lifecycle memory leak: {memory_growth:.2f}MB"


class TestResourceUsagePerformance:
    """Test CPU and resource usage performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cpu_usage_during_navigation(self):
        """Test CPU usage remains reasonable during navigation."""
        process = psutil.Process()
        app = CCMonitorApp()
        
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Monitor CPU usage during navigation
            cpu_samples = []
            navigation_keys = ["tab", "ctrl+1", "down", "ctrl+2", "up"] * 10
            
            for key in navigation_keys:
                cpu_before = process.cpu_percent()
                await pilot.press(key)
                await pilot.wait_for_animation()
                cpu_after = process.cpu_percent()
                
                cpu_usage = cpu_after - cpu_before
                cpu_samples.append(cpu_usage)
            
            # CPU usage should be reasonable
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            assert avg_cpu < 10.0, f"Average CPU usage too high: {avg_cpu:.2f}%"
            assert max_cpu < 25.0, f"Peak CPU usage too high: {max_cpu:.2f}%"
```

## 4. Benchmark Reporting and CI Integration

### Performance Report Generation
```python
# tests/tui/performance/generate_report.py
import json
import time
from pathlib import Path
from typing import List
from tests.tui.performance.conftest import PerformanceMetrics

class PerformanceReporter:
    """Generate performance test reports."""
    
    def __init__(self, output_dir: Path = Path("performance_reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, metrics: List[PerformanceMetrics]) -> Path:
        """Generate comprehensive performance report."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"performance_report_{timestamp}.json"
        
        report_data = {
            "timestamp": timestamp,
            "summary": self._generate_summary(metrics),
            "detailed_results": [
                {
                    "operation": m.operation,
                    "avg_time_ms": m.avg_time_ms,
                    "p95_time_ms": m.p95_time_ms,
                    "max_time_ms": m.max_time_ms,
                    "min_time_ms": m.min_time_ms,
                    "memory_usage_mb": m.memory_usage_mb,
                    "cpu_percent": m.cpu_percent,
                    "iterations": m.iterations
                }
                for m in metrics
            ],
            "performance_requirements": {
                "tab_navigation": {"max_avg_ms": 50, "max_p95_ms": 100},
                "direct_focus": {"max_avg_ms": 30, "max_p95_ms": 60},
                "arrow_navigation": {"max_avg_ms": 25, "max_p95_ms": 50},
                "focus_chain_rebuild": {"max_avg_ms": 20, "max_p95_ms": 50},
                "modal_operations": {"max_avg_ms": 150, "max_p95_ms": 250}
            }
        }
        
        report_file.write_text(json.dumps(report_data, indent=2))
        return report_file
    
    def _generate_summary(self, metrics: List[PerformanceMetrics]) -> dict:
        """Generate summary statistics."""
        if not metrics:
            return {}
        
        return {
            "total_operations": len(metrics),
            "avg_response_time_ms": sum(m.avg_time_ms for m in metrics) / len(metrics),
            "slowest_operation": max(metrics, key=lambda m: m.avg_time_ms).operation,
            "fastest_operation": min(metrics, key=lambda m: m.avg_time_ms).operation,
            "total_memory_usage_mb": sum(m.memory_usage_mb for m in metrics),
            "avg_cpu_usage": sum(m.cpu_percent for m in metrics) / len(metrics)
        }

# Performance test runner
if __name__ == "__main__":
    import pytest
    import sys
    
    # Run performance tests and generate report
    pytest.main([
        "tests/tui/performance/",
        "-m", "benchmark",
        "--json-report",
        "--json-report-file=performance_results.json"
    ])
```

### CI/CD Integration
```yaml
# .github/workflows/performance-tests.yml
name: Performance Benchmarks

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM

jobs:
  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need full history for comparison
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --dev
      
      - name: Run performance benchmarks
        run: |
          uv run pytest tests/tui/performance/ \
            -m benchmark \
            --benchmark-json=benchmark_results.json \
            --benchmark-compare-fail=mean:20%  # Fail if 20% slower
      
      - name: Generate performance report
        run: |
          python tests/tui/performance/generate_report.py
      
      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: performance-benchmarks
          path: |
            benchmark_results.json
            performance_reports/
      
      - name: Compare with baseline
        if: github.event_name == 'pull_request'
        run: |
          # Compare PR performance with main branch
          uv run pytest tests/tui/performance/ \
            -m benchmark \
            --benchmark-compare=baseline_benchmarks.json \
            --benchmark-compare-fail=mean:15%
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('benchmark_results.json'));
            
            let comment = '## Performance Benchmark Results\n\n';
            comment += '| Operation | Avg Time (ms) | P95 Time (ms) | Status |\n';
            comment += '|-----------|---------------|---------------|--------|\n';
            
            // Add benchmark results to comment
            // (Implementation depends on benchmark JSON structure)
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });

  memory-leak-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --dev
          uv add memory-profiler pytest-memray
      
      - name: Run memory leak tests
        run: |
          uv run python -m memray run --output=memory_profile.bin \
            -m pytest tests/tui/performance/test_memory_performance.py
      
      - name: Generate memory report
        run: |
          uv run memray flamegraph memory_profile.bin
      
      - name: Upload memory analysis
        uses: actions/upload-artifact@v3
        with:
          name: memory-analysis
          path: |
            memory_profile.bin
            memray-*.html
```

### Performance Dashboard
```python
# scripts/performance_dashboard.py
"""Generate performance dashboard for tracking over time."""
import sqlite3
import json
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

class PerformanceDashboard:
    """Track performance metrics over time."""
    
    def __init__(self, db_path: Path = Path("performance_history.db")):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize performance tracking database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                operation TEXT,
                avg_time_ms REAL,
                p95_time_ms REAL,
                memory_usage_mb REAL,
                cpu_percent REAL,
                git_commit TEXT,
                branch TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def record_metrics(self, metrics: List[PerformanceMetrics], git_info: dict):
        """Record performance metrics."""
        conn = sqlite3.connect(self.db_path)
        timestamp = datetime.now().isoformat()
        
        for metric in metrics:
            conn.execute("""
                INSERT INTO performance_metrics 
                (timestamp, operation, avg_time_ms, p95_time_ms, 
                 memory_usage_mb, cpu_percent, git_commit, branch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, metric.operation, metric.avg_time_ms,
                metric.p95_time_ms, metric.memory_usage_mb,
                metric.cpu_percent, git_info.get('commit'),
                git_info.get('branch')
            ))
        
        conn.commit()
        conn.close()
    
    def generate_trend_charts(self, output_dir: Path):
        """Generate performance trend charts."""
        conn = sqlite3.connect(self.db_path)
        
        # Get data for major operations
        operations = [
            "tab_navigation", "direct_focus_ctrl+1", "arrow_navigation",
            "focus_chain_rebuild", "help_modal_cycle"
        ]
        
        for operation in operations:
            cursor = conn.execute("""
                SELECT timestamp, avg_time_ms, p95_time_ms 
                FROM performance_metrics 
                WHERE operation = ?
                ORDER BY timestamp
            """, (operation,))
            
            data = cursor.fetchall()
            if not data:
                continue
            
            timestamps = [row[0] for row in data]
            avg_times = [row[1] for row in data]
            p95_times = [row[2] for row in data]
            
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps, avg_times, label='Average Time', marker='o')
            plt.plot(timestamps, p95_times, label='95th Percentile', marker='s')
            plt.title(f'{operation.replace("_", " ").title()} Performance Trend')
            plt.xlabel('Time')
            plt.ylabel('Response Time (ms)')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_file = output_dir / f'{operation}_trend.png'
            plt.savefig(chart_file)
            plt.close()
        
        conn.close()
```

This comprehensive performance testing strategy ensures CCMonitor's navigation system maintains responsive performance under all conditions, with automated monitoring and regression detection.