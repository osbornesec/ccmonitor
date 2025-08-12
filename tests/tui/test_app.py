"""Tests for the CCMonitorApp main application class."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tui.app import CCMonitorApp
from src.tui.exceptions import StartupError


class TestCCMonitorApp:
    """Test suite for CCMonitorApp class."""

    def _get_mock_config(self) -> MagicMock:
        """Create a mock configuration for testing."""
        mock_config = MagicMock()
        mock_config.log_level = "INFO"
        # Use proper temporary file handling
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            mock_config.log_file = Path(tmp.name)
        return mock_config

    def test_app_creation(self) -> None:
        """Test app can be instantiated with correct metadata."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()

            assert app.TITLE == "CCMonitor - Multi-Project Monitoring"
            assert app.SUB_TITLE == "Real-time Claude conversation tracker"
            assert app.VERSION == "0.1.0"
            assert app.CSS_PATH == "styles/test.tcss"

    def test_key_bindings_registered(self) -> None:
        """Test all key bindings are properly registered."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            binding_keys = {binding.key for binding in app.BINDINGS}

            expected_keys = {
                "q",
                "ctrl+c",
                "h",
                "p",
                "f",
                "r",
                "d",
                "escape",
            }
            assert expected_keys.issubset(binding_keys)

    def test_screens_registered(self) -> None:
        """Test all screens are properly registered."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()

            assert "main" in app.SCREENS
            assert "help" in app.SCREENS
            assert "error" in app.SCREENS

    @pytest.mark.asyncio
    async def test_state_management(self) -> None:
        """Test state can be saved and loaded."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.app_state.state["test_value"] = "test_data"
            await app.save_state()

            # Create new app instance and load state
            app2 = CCMonitorApp()
            state = await app2.load_state()

            assert state.get("test_value") == "test_data"

    @pytest.mark.asyncio
    async def test_startup_sequence_success(self) -> None:
        """Test successful startup sequence."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()

            # Mock all startup methods
            app.load_configuration = AsyncMock()
            app.check_terminal = AsyncMock()
            app.load_state = AsyncMock()
            app.initialize_screens = AsyncMock()
            app.start_monitoring = AsyncMock()

            await app.on_mount()

            app.load_configuration.assert_called_once()
            app.check_terminal.assert_called_once()
            app.load_state.assert_called_once()
            app.initialize_screens.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_failure_handling(self) -> None:
        """Test startup failure handling."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.exit = MagicMock()
            app.load_configuration = AsyncMock(
                side_effect=StartupError("Test startup error"),
            )

            await app.on_mount()

            app.exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_toggle_pause(self) -> None:
        """Test pause/resume monitoring action."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.notify = MagicMock()
            app.start_monitoring = AsyncMock()
            app.stop_monitoring = AsyncMock()

            # Test pausing
            assert not app.is_paused
            await app.action_toggle_pause()
            assert app.is_paused
            app.stop_monitoring.assert_called_once()

            # Test resuming
            await app.action_toggle_pause()
            assert not app.is_paused
            app.start_monitoring.assert_called()

    def test_action_toggle_dark(self) -> None:
        """Test dark mode toggle."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.notify = MagicMock()

            original_mode = app.dark_mode
            app.action_toggle_dark()
            assert app.dark_mode != original_mode
            app.notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self) -> None:
        """Test graceful shutdown sequence."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.stop_monitoring = AsyncMock()
            app.save_state = AsyncMock()
            app.cleanup = AsyncMock()
            app.exit = MagicMock()

            await app.action_quit()

            app.stop_monitoring.assert_called_once()
            app.save_state.assert_called_once()
            app.cleanup.assert_called_once()
            app.exit.assert_called_once()

    def test_reactive_watchers(self) -> None:
        """Test reactive state watchers."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.is_mounted = True
            app.notify = MagicMock()

            # Test pause state watcher
            app.watch_is_paused(paused=True)
            assert "PAUSED" in app.sub_title

            app.watch_is_paused(paused=False)
            assert "ACTIVE" in app.sub_title

            # Test project watcher
            app.watch_active_project("test_project")
            app.notify.assert_called_with("Switched to project: test_project")

    def test_exception_handling(self) -> None:
        """Test exception handling."""
        with patch("src.tui.app.get_config") as mock_config:
            mock_config.return_value = self._get_mock_config()

            app = CCMonitorApp()
            app.push_screen = MagicMock()
            app.notify = MagicMock()

            # Test startup/config errors
            startup_error = StartupError("Test startup error")
            app.on_exception(startup_error)
            app.push_screen.assert_called_with("error")

            # Test other exceptions
            general_error = ValueError("Test error")
            app.on_exception(general_error)
            app.notify.assert_called()
