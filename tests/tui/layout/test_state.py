"""Tests for application state management system."""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.tui.utils.state import AppState

# Test constants
DEFAULT_DARK_MODE = True
DEFAULT_IS_PAUSED = False
DEFAULT_ACTIVE_PROJECT = None
DEFAULT_WINDOW_SIZE = None
TEST_PROJECT_NAME = "test-project"
TEST_WINDOW_WIDTH = 120
TEST_WINDOW_HEIGHT = 40
TEST_FILTER_LIMIT = 100


class TestAppState:
    """Test AppState functionality."""

    def test_initialization(self) -> None:
        """Test app state initialization."""
        state = AppState()

        # Test state file path
        expected_path = Path.home() / ".config" / "ccmonitor" / "state.json"
        assert state.state_file == expected_path

        # Test default state values
        assert state.state["dark_mode"] is DEFAULT_DARK_MODE
        assert state.state["is_paused"] is DEFAULT_IS_PAUSED
        assert state.state["active_project"] is DEFAULT_ACTIVE_PROJECT
        assert state.state["filter_settings"] == {}
        assert state.state["window_size"] is DEFAULT_WINDOW_SIZE

        # Test logger is initialized
        assert state.logger is not None
        assert "ccmonitor.state" in state.logger.name

    @pytest.mark.asyncio
    async def test_load_no_file_exists(self) -> None:
        """Test loading state when no file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state = AppState()
            state.state_file = Path(temp_dir) / "nonexistent" / "state.json"

            loaded_state = await state.load()

            # Should return default state
            assert loaded_state["dark_mode"] is DEFAULT_DARK_MODE
            assert loaded_state["is_paused"] is DEFAULT_IS_PAUSED
            assert loaded_state["active_project"] is DEFAULT_ACTIVE_PROJECT

    @pytest.mark.asyncio
    async def test_load_valid_file(self) -> None:
        """Test loading state from valid file."""
        test_state = {
            "dark_mode": False,
            "is_paused": True,
            "active_project": TEST_PROJECT_NAME,
            "window_size": [TEST_WINDOW_WIDTH, TEST_WINDOW_HEIGHT],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            # Write test state to file
            with state_file.open("w") as f:
                json.dump(test_state, f)

            state = AppState()
            state.state_file = state_file

            loaded_state = await state.load()

            # Should load values from file
            assert loaded_state["dark_mode"] is False
            assert loaded_state["is_paused"] is True
            assert loaded_state["active_project"] == TEST_PROJECT_NAME
            assert loaded_state["window_size"] == [
                TEST_WINDOW_WIDTH,
                TEST_WINDOW_HEIGHT,
            ]
            # Default values should still be present
            assert "filter_settings" in loaded_state

    @pytest.mark.asyncio
    async def test_load_partial_file(self) -> None:
        """Test loading state from partial file (missing some keys)."""
        partial_state = {
            "dark_mode": False,
            "active_project": TEST_PROJECT_NAME,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            with state_file.open("w") as f:
                json.dump(partial_state, f)

            state = AppState()
            state.state_file = state_file

            loaded_state = await state.load()

            # Should merge with defaults
            assert loaded_state["dark_mode"] is False  # From file
            assert (
                loaded_state["active_project"] == TEST_PROJECT_NAME
            )  # From file
            assert loaded_state["is_paused"] is DEFAULT_IS_PAUSED  # Default
            assert loaded_state["filter_settings"] == {}  # Default

    @pytest.mark.asyncio
    async def test_load_invalid_json(self) -> None:
        """Test loading state from file with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            # Write invalid JSON
            with state_file.open("w") as f:
                f.write("{ invalid json }")

            state = AppState()
            state.state_file = state_file

            with patch.object(state.logger, "warning") as mock_warning:
                loaded_state = await state.load()

                # Should return defaults and log warning
                assert loaded_state["dark_mode"] is DEFAULT_DARK_MODE
                mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_permission_error(self) -> None:
        """Test loading state when file cannot be read."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            state_file.touch()
            state_file.chmod(0o000)  # Remove all permissions

            state = AppState()
            state.state_file = state_file

            try:
                with patch.object(state.logger, "warning") as mock_warning:
                    loaded_state = await state.load()

                    # Should return defaults and log warning
                    assert loaded_state["dark_mode"] is DEFAULT_DARK_MODE
                    mock_warning.assert_called_once()
            finally:
                # Restore permissions for cleanup
                state_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_save_new_file(self) -> None:
        """Test saving state to new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "ccmonitor" / "state.json"

            state = AppState()
            state.state_file = state_file
            state.state["dark_mode"] = False
            state.state["active_project"] = TEST_PROJECT_NAME

            await state.save()

            # File should be created
            assert state_file.exists()

            # Content should match state
            with state_file.open() as f:
                saved_data = json.load(f)

            assert saved_data["dark_mode"] is False
            assert saved_data["active_project"] == TEST_PROJECT_NAME

    @pytest.mark.asyncio
    async def test_save_creates_directory(self) -> None:
        """Test that save creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = (
                Path(temp_dir) / "deep" / "nested" / "path" / "state.json"
            )

            state = AppState()
            state.state_file = nested_path

            await state.save()

            # Directory and file should be created
            assert nested_path.parent.exists()
            assert nested_path.exists()

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self) -> None:
        """Test that save overwrites existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            # Create existing file with different content
            with state_file.open("w") as f:
                json.dump({"old": "data"}, f)

            state = AppState()
            state.state_file = state_file
            state.state["dark_mode"] = False

            await state.save()

            # Should contain new state, not old data
            with state_file.open() as f:
                saved_data = json.load(f)

            assert "old" not in saved_data
            assert saved_data["dark_mode"] is False

    @pytest.mark.asyncio
    async def test_save_permission_error(self) -> None:
        """Test save when file cannot be written."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only
            temp_path = Path(temp_dir)
            temp_path.chmod(0o555)

            state_file = temp_path / "state.json"

            state = AppState()
            state.state_file = state_file

            try:
                with patch.object(state.logger, "warning") as mock_warning:
                    with pytest.raises(OSError, match="Permission denied"):
                        await state.save()

                    # Should log warning and raise exception
                    mock_warning.assert_called_once()
            finally:
                # Restore permissions for cleanup
                temp_path.chmod(0o755)

    @pytest.mark.asyncio
    async def test_round_trip_save_load(self) -> None:
        """Test saving and loading state maintains data integrity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            # Create state with modified values
            state = AppState()
            state.state_file = state_file
            state.state["dark_mode"] = False
            state.state["is_paused"] = True
            state.state["active_project"] = TEST_PROJECT_NAME
            state.state["filter_settings"] = {
                "type": "error",
                "limit": TEST_FILTER_LIMIT,
            }
            state.state["window_size"] = [
                TEST_WINDOW_WIDTH,
                TEST_WINDOW_HEIGHT,
            ]

            # Save state
            await state.save()

            # Create new state instance and load
            new_state = AppState()
            new_state.state_file = state_file
            loaded_data = await new_state.load()

            # Should match original state
            assert loaded_data["dark_mode"] is False
            assert loaded_data["is_paused"] is True
            assert loaded_data["active_project"] == TEST_PROJECT_NAME
            assert loaded_data["filter_settings"]["type"] == "error"
            assert loaded_data["filter_settings"]["limit"] == TEST_FILTER_LIMIT
            assert loaded_data["window_size"] == [
                TEST_WINDOW_WIDTH,
                TEST_WINDOW_HEIGHT,
            ]


class TestAppStateEdgeCases:
    """Test edge cases and error conditions."""

    def test_state_modification(self) -> None:
        """Test that state can be modified after initialization."""
        state = AppState()

        # Modify state
        state.state["dark_mode"] = False
        state.state["active_project"] = TEST_PROJECT_NAME
        state.state["custom_key"] = "custom_value"

        # Verify modifications
        assert state.state["dark_mode"] is False
        assert state.state["active_project"] == TEST_PROJECT_NAME
        assert state.state["custom_key"] == "custom_value"

    @pytest.mark.asyncio
    async def test_load_empty_file(self) -> None:
        """Test loading from empty file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            state_file.touch()  # Create empty file

            state = AppState()
            state.state_file = state_file

            with patch.object(state.logger, "warning") as mock_warning:
                loaded_state = await state.load()

                # Should use defaults and log warning
                assert loaded_state["dark_mode"] is DEFAULT_DARK_MODE
                mock_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_json_with_extra_keys(self) -> None:
        """Test loading JSON with extra keys not in defaults."""
        extra_state = {
            "dark_mode": False,
            "extra_key": "extra_value",
            "nested": {"key": "value"},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            with state_file.open("w") as f:
                json.dump(extra_state, f)

            state = AppState()
            state.state_file = state_file

            loaded_state = await state.load()

            # Should include both defaults and extra keys
            assert loaded_state["dark_mode"] is False
            assert loaded_state["extra_key"] == "extra_value"
            assert loaded_state["nested"]["key"] == "value"
            assert loaded_state["is_paused"] is DEFAULT_IS_PAUSED  # Default

    def test_logger_configuration(self) -> None:
        """Test that logger is properly configured."""
        state = AppState()

        assert state.logger is not None
        assert hasattr(state.logger, "debug")
        assert hasattr(state.logger, "warning")
        assert "ccmonitor.state" in state.logger.name

    def test_multiple_instances(self) -> None:
        """Test that multiple AppState instances are independent."""
        state1 = AppState()
        state2 = AppState()

        # Modify first instance
        state1.state["dark_mode"] = False

        # Second instance should have defaults
        assert state1.state["dark_mode"] is False
        assert state2.state["dark_mode"] is DEFAULT_DARK_MODE

        # File paths should be the same
        assert state1.state_file == state2.state_file

    @pytest.mark.asyncio
    async def test_concurrent_operations(self) -> None:
        """Test that concurrent save operations work correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"

            state = AppState()
            state.state_file = state_file

            # Run multiple saves concurrently
            tasks = []
            for i in range(5):
                state.state["counter"] = i
                tasks.append(state.save())

            # Should not raise exceptions
            await asyncio.gather(*tasks)

            # File should exist
            assert state_file.exists()
