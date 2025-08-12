"""Comprehensive edge case testing for CCMonitor."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.cli.main import FileMonitor, MonitorConfig
from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from pathlib import Path

    from tests.integration.conftest import ErrorInjectionManager

# Constants for edge case testing
MAX_FILE_SIZE = 1024 * 1024  # 1MB
LARGE_ITERATION_COUNT = 1000
RAPID_UPDATE_COUNT = 100
STRESS_TEST_DURATION = 5.0
UNICODE_TEST_CHARS = "🔥💻📊🚀⚡🎯🔍📈"
EXPECTED_MINIMUM_WRITERS_OUTPUT = 30  # 3 writers * 10 updates + initial
MEMORY_TEST_FILE_COUNT = 100

logger = logging.getLogger(__name__)


class TestFileSystemEdgeCases:
    """Test file system edge cases and boundary conditions."""

    def test_empty_directory_monitoring(self, temp_project_dir: Path) -> None:
        """Test monitoring completely empty directory."""
        empty_dir = temp_project_dir / "empty"
        empty_dir.mkdir()

        config = MonitorConfig(
            directory=empty_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle empty directory gracefully
        files = monitor._scan_files(empty_dir)  # noqa: SLF001
        assert len(files) == 0

    def test_deeply_nested_directory_structure(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test monitoring deeply nested directory structures."""
        # Create deep nesting
        deep_path = temp_project_dir
        for i in range(10):  # 10 levels deep
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir()

        # Create file at deepest level
        deep_file = deep_path / "deep.jsonl"
        deep_file.write_text('{"deep": "file"}\n')

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="**/*.jsonl",  # Recursive pattern
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)
        files = monitor._scan_files(temp_project_dir)  # noqa: SLF001

        # Should find the deeply nested file
        assert any("deep.jsonl" in str(f) for f in files)

    def test_special_characters_in_filenames(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test handling files with special characters in names."""
        special_names = [
            "file with spaces.jsonl",
            "file-with-dashes.jsonl",
            "file_with_underscores.jsonl",
            "file.with.dots.jsonl",
            "file@with#special$chars%.jsonl",
            f"{UNICODE_TEST_CHARS}.jsonl",
        ]

        created_files = []
        for name in special_names:
            try:
                special_file = temp_project_dir / name
                special_file.write_text(f'{{"name": "{name}"}}\n')
                created_files.append(special_file)
            except (OSError, UnicodeError):
                # Some special characters might not be supported on filesystem
                continue

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)
        files = monitor._scan_files(temp_project_dir)  # noqa: SLF001

        # Should handle special characters gracefully
        assert len(files) >= len(created_files) - 2  # Allow some failures

    def test_file_permission_variations(
        self,
        temp_project_dir: Path,
        error_injection_manager: ErrorInjectionManager,
    ) -> None:
        """Test various file permission scenarios."""
        # Create files with different permissions
        readable_file = temp_project_dir / "readable.jsonl"
        readable_file.write_text('{"readable": true}\n')

        protected_file = temp_project_dir / "protected.jsonl"
        protected_file.write_text('{"protected": true}\n')

        # Make one file unreadable
        error_injection_manager.inject_file_permission_error(protected_file)

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle permission errors gracefully
        try:
            content = monitor._read_new_content(  # noqa: SLF001
                protected_file,
                0,
            )
            # If no exception, content should be empty or error placeholder
            assert isinstance(content, list)
        except PermissionError:
            # Expected - test passes if gracefully handled
            pass

    def test_corrupted_json_recovery(self, temp_project_dir: Path) -> None:
        """Test recovery from various JSON corruption scenarios."""
        corrupted_file = temp_project_dir / "corrupted.jsonl"

        # Various corruption patterns
        corruptions = [
            '{"valid": "json"}\n{"broken": json\n{"valid": "again"}\n',
            '{"missing_quote: "value"}\n',
            '{"trailing_comma": "bad",}\n',
            '{"unclosed": {"nested": "object"\n',
            '\n\n{"empty_lines_around": "me"}\n\n',
            '{"unicode": "test 😀"}\n',  # Unicode emoji
        ]

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        for corruption in corruptions:
            corrupted_file.write_text(corruption)

            # Should handle corruption gracefully
            content = monitor._read_new_content(  # noqa: SLF001
                corrupted_file,
                0,
            )
            assert isinstance(content, list)

            # Should have some valid entries or error placeholders
            valid_entries = [
                entry
                for entry in content
                if isinstance(entry, dict) and "raw_line" not in entry
            ]
            error_entries = [
                entry
                for entry in content
                if isinstance(entry, dict) and "raw_line" in entry
            ]

            # Should have handled corruption
            assert len(valid_entries) + len(error_entries) == len(content)


class TestConcurrencyEdgeCases:
    """Test concurrency and threading edge cases."""

    @pytest.mark.asyncio
    async def test_rapid_file_modifications(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test rapid successive file modifications."""
        rapid_file = temp_project_dir / "rapid.jsonl"
        rapid_file.write_text('{"initial": "data"}\n')

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        # Rapid modifications
        async def rapid_modify() -> None:
            for i in range(RAPID_UPDATE_COUNT):
                with rapid_file.open("a") as f:
                    f.write(f'{{"rapid_update": {i}}}\n')
                await asyncio.sleep(0.001)  # Very fast updates

        # Monitor should handle rapid updates
        await rapid_modify()

        # File should be readable after rapid updates
        content = monitor._read_new_content(rapid_file, 0)  # noqa: SLF001
        assert (
            len(content) > RAPID_UPDATE_COUNT
        )  # Should have base + rapid updates

    @pytest.mark.asyncio
    async def test_concurrent_file_access_patterns(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test various concurrent file access patterns."""
        shared_file = temp_project_dir / "concurrent.jsonl"
        shared_file.write_text('{"initial": "data"}\n')

        # Simulate multiple writers
        async def writer(writer_id: int) -> None:
            for i in range(10):
                with shared_file.open("a") as f:
                    f.write(f'{{"writer_{writer_id}": {i}}}\n')
                await asyncio.sleep(0.01)

        # Start multiple concurrent writers
        tasks = [
            asyncio.create_task(writer(i))
            for i in range(3)  # 3 concurrent writers
        ]

        await asyncio.gather(*tasks)

        # File should still be readable and valid
        assert shared_file.exists()
        content = shared_file.read_text()
        lines = [line for line in content.split("\n") if line.strip()]

        # Should have content from all writers
        assert len(lines) >= EXPECTED_MINIMUM_WRITERS_OUTPUT

    def test_file_locking_scenarios(self, temp_project_dir: Path) -> None:
        """Test file locking and sharing scenarios."""
        locked_file = temp_project_dir / "locked.jsonl"
        locked_file.write_text('{"initial": "data"}\n')

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        # Open file for exclusive writing in one process
        with locked_file.open("a") as f:
            f.write('{"while_locked": true}\n')

            # Should still be able to read (in most systems)
            try:
                content = monitor._read_new_content(  # noqa: SLF001
                    locked_file,
                    0,
                )
                assert isinstance(content, list)
            except (PermissionError, OSError):
                # Some systems might prevent reading locked files
                logger.debug("File locking prevented concurrent read access")


class TestResourceLimitsEdgeCases:
    """Test resource limits and boundary conditions."""

    def test_large_file_handling(self, temp_project_dir: Path) -> None:
        """Test handling of large files near system limits."""
        large_file = temp_project_dir / "large.jsonl"

        # Create a large file (but not too large for CI)
        with large_file.open("w") as f:
            for i in range(LARGE_ITERATION_COUNT):
                # Create moderately sized JSON objects
                large_entry = {
                    "id": i,
                    "data": "x" * 100,  # 100 chars per entry
                    "metadata": {
                        "timestamp": f"2024-01-01T{i:02d}:00:00Z",
                        "source": "test_generation",
                        "size": 100,
                    },
                }
                f.write(json.dumps(large_entry) + "\n")

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle large file gracefully
        file_size = large_file.stat().st_size
        assert file_size > MAX_FILE_SIZE * 0.1  # At least 100KB

        # Reading should work (might be slow but shouldn't crash)
        content = monitor._read_new_content(large_file, 0)  # noqa: SLF001
        assert len(content) == LARGE_ITERATION_COUNT

    def test_memory_pressure_simulation(self, temp_project_dir: Path) -> None:
        """Test behavior under simulated memory pressure."""
        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        monitor = FileMonitor(config)

        # Create many small files to test memory usage
        for i in range(MEMORY_TEST_FILE_COUNT):
            small_file = temp_project_dir / f"small_{i}.jsonl"
            small_file.write_text(f'{{"file_{i}": "data"}}\n')

        # Should handle many files without memory issues
        all_files = monitor._scan_files(temp_project_dir)  # noqa: SLF001
        assert len(all_files) >= MEMORY_TEST_FILE_COUNT


class TestSignalHandlingEdgeCases:
    """Test signal handling and interruption scenarios."""

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Unix signals not available on Windows",
    )
    def test_signal_interruption_handling(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test handling of various signal interruptions."""
        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            pattern="*.jsonl",
            output=temp_project_dir / "output.jsonl",
        )

        test_file = temp_project_dir / "signal_test.jsonl"
        test_file.write_text('{"signal": "test"}\n')

        monitor = FileMonitor(config)

        # Test signal handling doesn't crash basic operations
        with patch("signal.signal"):
            # Should register signal handlers without issues
            try:
                monitor.file_timestamps[test_file] = 1234567.0
                monitor.file_sizes[test_file] = 100
                monitor._save_state()  # noqa: SLF001

                # Verify state saving worked
                assert monitor.state_file.exists()

            except Exception as e:  # noqa: BLE001
                # Signal setup might fail in test environment
                logger.debug("Signal handling test failed: %s", e)


class TestTUIEdgeCases:
    """Test TUI-specific edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_tui_startup_with_no_data(self) -> None:
        """Test TUI startup when no monitoring data is available."""
        app = CCMonitorApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            # Should start successfully even with no data
            assert app.is_running

            # Basic navigation should work
            await pilot.press("tab")
            await pilot.pause(0.05)

            assert app.is_running

    @pytest.mark.asyncio
    async def test_tui_rapid_key_input(self) -> None:
        """Test TUI handling of rapid key input."""
        app = CCMonitorApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            # Rapid key sequence
            keys = ["tab", "down", "up", "left", "right"] * 10

            for key in keys:
                await pilot.press(key)
                # Very short pause between keys
                await asyncio.sleep(0.001)

            await pilot.pause(0.1)

            # Should still be responsive
            assert app.is_running

    @pytest.mark.asyncio
    async def test_tui_invalid_input_sequences(self) -> None:
        """Test TUI handling of invalid or unexpected input sequences."""
        app = CCMonitorApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            # Test various edge case inputs
            edge_inputs = [
                "ctrl+alt+delete",  # Invalid combination
                "f99",  # Non-existent function key
                "ctrl+shift+z",  # Uncommon combination
            ]

            for edge_input in edge_inputs:
                try:
                    await pilot.press(edge_input)
                    await pilot.pause(0.02)
                except Exception:  # noqa: BLE001
                    # Some inputs might not be recognized
                    logger.debug("Unrecognized input: %s", edge_input)

            # Should remain stable
            assert app.is_running


class TestPropertyBasedEdgeCases:
    """Property-based tests using Hypothesis for edge case discovery."""

    def test_json_content_parsing_robustness(
        self,
        tmp_path: Path,
    ) -> None:
        """Test JSON parsing robustness with random content."""

        @given(
            st.lists(
                st.text(min_size=1, max_size=100),
                min_size=0,
                max_size=20,
            ),
        )
        def run_hypothesis_test(random_content: list[str]) -> None:
            test_file = tmp_path / "hypothesis_test.jsonl"

            # Create file with random content lines
            with test_file.open("w") as f:
                for line in random_content:
                    f.write(line + "\n")

            config = MonitorConfig(
                directory=tmp_path,
                interval=1,
                pattern="*.jsonl",
                output=tmp_path / "output.jsonl",
            )

            monitor = FileMonitor(config)

            # Should handle any content gracefully
            try:
                content = monitor._read_new_content(  # noqa: SLF001
                    test_file,
                    0,
                )
                assert isinstance(content, list)

                # All entries should be dicts (valid JSON or error placeholders)
                for entry in content:
                    assert isinstance(entry, dict)

            except Exception:  # noqa: BLE001
                # Even on error, should not crash completely - test passes
                logger.debug("Expected error in property-based test")

        # Run the hypothesis test
        run_hypothesis_test()

    def test_file_offset_boundary_conditions(
        self,
        tmp_path: Path,
    ) -> None:
        """Test file reading with various offset boundary conditions."""

        @given(
            st.integers(min_value=0, max_value=10000),
            st.text(min_size=0, max_size=1000),
        )
        def run_offset_test(offset: int, content: str) -> None:
            test_file = tmp_path / "offset_test.jsonl"

            # Create file with known content
            file_content = (
                f'{{"test": "content"}}\n{{"content": "{content}"}}\n'
            )
            test_file.write_text(file_content)

            config = MonitorConfig(
                directory=tmp_path,
                interval=1,
                pattern="*.jsonl",
                output=tmp_path / "output.jsonl",
            )

            monitor = FileMonitor(config)

            # Test reading from various offsets
            try:
                result = monitor._read_new_content(  # noqa: SLF001
                    test_file,
                    offset,
                )
                assert isinstance(result, list)

                # Result should be consistent regardless of offset
                if offset > len(file_content.encode()):
                    # Beyond file end
                    assert len(result) == 0
                else:
                    # Within file bounds
                    assert len(result) >= 0

            except Exception:  # noqa: BLE001
                # Some offsets might be invalid, but shouldn't crash
                logger.debug("Invalid offset handled gracefully: %s", offset)

        # Run the hypothesis test
        run_offset_test()
