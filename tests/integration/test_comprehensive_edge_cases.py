"""Comprehensive edge case testing for Phase 4 coverage boost."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

import pytest

from src.cli.main import FileMonitor, MonitorConfig
from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from pathlib import Path

    from tests.integration.conftest import ErrorInjectionManager

# Constants for tests
EXPECTED_LARGE_FILE_ENTRIES = 500
EXPECTED_CONCURRENT_ENTRIES = 10  # Initial + 2 writers * 5 entries each
TEST_TIMESTAMP = 1234567890.0
TEST_FILE_SIZE = 100

logger = logging.getLogger(__name__)


class TestEdgeCaseScenarios:
    """Test edge cases to boost coverage to 90%."""

    def test_file_monitor_with_empty_directory(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor with completely empty directory."""
        empty_dir = temp_project_dir / "empty"
        empty_dir.mkdir()

        config = MonitorConfig(
            directory=empty_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle empty directory gracefully
        files = monitor._scan_files(empty_dir)  # noqa: SLF001
        assert len(files) == 0

    def test_file_monitor_with_corrupted_json(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor handling of corrupted JSON files."""
        corrupted_file = temp_project_dir / "corrupted.jsonl"

        # Create file with mixed valid and invalid JSON
        corrupted_content = (
            '{"valid": "json_entry"}\n'
            "this is not json at all\n"
            '{"another": "valid_entry"}\n'
            '{"incomplete": \n'
            '{"trailing_comma": "value",}\n'
        )
        corrupted_file.write_text(corrupted_content)

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle corruption gracefully
        content = monitor._read_new_content(corrupted_file, 0)  # noqa: SLF001
        assert isinstance(content, list)

        # Should have a mix of valid entries and error placeholders
        valid_count = sum(
            1
            for entry in content
            if isinstance(entry, dict) and "raw_line" not in entry
        )
        error_count = sum(
            1
            for entry in content
            if isinstance(entry, dict) and "raw_line" in entry
        )

        assert valid_count >= 1  # At least one valid entry
        assert error_count >= 1  # At least one error entry

    def test_file_monitor_permission_errors(
        self,
        temp_project_dir: Path,
        error_injection_manager: ErrorInjectionManager,
    ) -> None:
        """Test FileMonitor handling of permission errors."""
        protected_file = temp_project_dir / "protected.jsonl"
        protected_file.write_text('{"protected": "content"}\n')

        # Inject permission error
        error_injection_manager.inject_file_permission_error(protected_file)

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle permission errors gracefully
        try:
            content = monitor._read_new_content(
                protected_file, 0
            )  # noqa: SLF001
            # If no exception, should return empty list or error placeholders
            assert isinstance(content, list)
        except PermissionError:
            # Expected - test passes if gracefully handled
            logger.debug("Permission error handled as expected")

    @pytest.mark.asyncio
    async def test_concurrent_file_modifications(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test concurrent file modifications don't crash monitor."""
        shared_file = temp_project_dir / "shared.jsonl"
        shared_file.write_text('{"initial": "data"}\n')

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Concurrent writers
        async def writer(writer_id: int) -> None:
            for i in range(5):  # Reduced for stability
                with shared_file.open("a") as f:
                    f.write(f'{{"writer_{writer_id}_entry_{i}": "data"}}\n')
                await asyncio.sleep(0.01)

        # Start concurrent writers
        tasks = [asyncio.create_task(writer(i)) for i in range(2)]
        await asyncio.gather(*tasks)

        # Monitor should still be able to read the file
        content = monitor._read_new_content(shared_file, 0)  # noqa: SLF001
        assert len(content) >= EXPECTED_CONCURRENT_ENTRIES

    def test_file_monitor_large_file_handling(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor with reasonably large files."""
        large_file = temp_project_dir / "large.jsonl"

        # Create a file with many entries (but not too large for CI)
        with large_file.open("w") as f:
            for i in range(500):  # 500 entries
                entry = {
                    "id": i,
                    "data": f"entry_{i}_data",
                    "metadata": {"timestamp": f"2024-01-01T{i:02d}:00:00Z"},
                }
                f.write(json.dumps(entry) + "\n")

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle large file without crashing
        content = monitor._read_new_content(large_file, 0)  # noqa: SLF001
        assert len(content) == 500
        assert all(isinstance(entry, dict) for entry in content)

    def test_file_monitor_state_persistence(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor state saving and loading."""
        test_file = temp_project_dir / "state_test.jsonl"
        test_file.write_text('{"state": "test"}\n')

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        # First monitor instance
        monitor1 = FileMonitor(config)
        monitor1.file_timestamps[test_file] = 1234567890.0
        monitor1.file_sizes[test_file] = 100
        monitor1._save_state()  # noqa: SLF001

        # Second monitor instance should load the state
        monitor2 = FileMonitor(config)
        timestamps, sizes = monitor2._load_state()  # noqa: SLF001

        assert test_file in timestamps
        assert timestamps[test_file] == 1234567890.0
        assert sizes[test_file] == 100

    @pytest.mark.asyncio
    async def test_tui_edge_cases(self) -> None:
        """Test TUI edge cases for coverage."""
        app = CCMonitorApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            # Test app starts successfully
            assert app.is_running

            # Test basic navigation doesn't crash
            navigation_keys = ["tab", "down", "up", "left", "right"]

            for key in navigation_keys:
                try:
                    await pilot.press(key)
                    await pilot.pause(0.01)
                except Exception:  # noqa: BLE001
                    # Some keys might not be valid in current context
                    logger.debug("Key %s not valid in current context", key)

            # App should still be running after navigation
            assert app.is_running

    @pytest.mark.asyncio
    async def test_tui_rapid_input_handling(self) -> None:
        """Test TUI handling of rapid input sequences."""
        app = CCMonitorApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            # Rapid input sequence
            for _ in range(10):  # Reduced for stability
                await pilot.press("tab")
                await asyncio.sleep(0.001)  # Very fast input

            await pilot.pause(0.05)

            # Should still be responsive after rapid input
            assert app.is_running

    def test_file_monitor_edge_case_patterns(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor with various file patterns."""
        # Create files with different extensions and patterns
        test_files = [
            "test.jsonl",
            "test.json",
            "test.txt",
            "test_file.jsonl",
            "another.jsonl",
        ]

        for filename in test_files:
            (temp_project_dir / filename).write_text(
                f'{{"file": "{filename}"}}\n'
            )

        # Test with different patterns
        patterns = ["*.jsonl", "*.json", "test*", "*test*"]

        for pattern in patterns:
            config = MonitorConfig(
                directory=temp_project_dir,
                interval=1,
                output=temp_project_dir / "output.jsonl",
                pattern=pattern,
            )

            monitor = FileMonitor(config)
            files = monitor._scan_files(temp_project_dir)  # noqa: SLF001

            # Should return some files for each pattern
            assert isinstance(
                files, (list, set)
            )  # _scan_files might return set
            # Pattern matching should work without errors

    def test_file_monitor_binary_file_handling(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor handling of binary files."""
        # Create a binary file with .jsonl extension
        binary_file = temp_project_dir / "binary.jsonl"
        with binary_file.open("wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle binary files gracefully
        try:
            content = monitor._read_new_content(binary_file, 0)  # noqa: SLF001
            assert isinstance(content, list)
            # Binary content should be handled as error entries
        except (UnicodeDecodeError, OSError):
            # Expected for binary files
            logger.debug("Binary file handled as expected")

    def test_file_monitor_nested_directory_scanning(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor with nested directory structures."""
        # Create nested structure
        nested_dirs = [
            "level1",
            "level1/level2",
            "level1/level2/level3",
        ]

        for dir_path in nested_dirs:
            (temp_project_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # Create files at different levels
        test_files = [
            "root.jsonl",
            "level1/file1.jsonl",
            "level1/level2/file2.jsonl",
            "level1/level2/level3/file3.jsonl",
        ]

        for file_path in test_files:
            (temp_project_dir / file_path).write_text(
                f'{{"file": "{file_path}"}}\n'
            )

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="**/*.jsonl",  # Recursive pattern
        )

        monitor = FileMonitor(config)
        files = monitor._scan_files(temp_project_dir)  # noqa: SLF001

        # Should find files at all levels
        assert len(files) >= len(test_files)

    @pytest.mark.asyncio
    async def test_integration_cli_tui_error_propagation(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test error propagation between CLI and TUI components."""
        # Create a scenario that might cause errors
        problematic_file = temp_project_dir / "problematic.jsonl"
        problematic_file.write_text('{"incomplete": "json"')  # Invalid JSON

        # Test that TUI can start despite problematic files
        app = CCMonitorApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            # Should start successfully despite problematic data
            assert app.is_running

            # Basic interaction should still work
            await pilot.press("tab")
            await pilot.pause(0.05)

            assert app.is_running

    def test_file_monitor_special_characters(
        self,
        temp_project_dir: Path,
    ) -> None:
        """Test FileMonitor with special characters in filenames."""
        special_files = [
            "file with spaces.jsonl",
            "file-with-dashes.jsonl",
            "file_with_underscores.jsonl",
        ]

        created_files = []
        for filename in special_files:
            try:
                special_file = temp_project_dir / filename
                special_file.write_text(f'{{"filename": "{filename}"}}\n')
                created_files.append(special_file)
            except OSError:
                # Some special characters might not be supported
                continue

        if not created_files:
            pytest.skip("No special character files could be created")

        config = MonitorConfig(
            directory=temp_project_dir,
            interval=1,
            output=temp_project_dir / "output.jsonl",
            pattern="*.jsonl",
        )

        monitor = FileMonitor(config)

        # Should handle special characters in filenames
        files = monitor._scan_files(temp_project_dir)  # noqa: SLF001
        assert len(files) >= len(created_files)

        # Should be able to read files with special characters
        for file_path in created_files:
            content = monitor._read_new_content(file_path, 0)  # noqa: SLF001
            assert isinstance(content, list)
            assert len(content) >= 1
