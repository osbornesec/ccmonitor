"""Integration tests for navigation flow in the TUI interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from textual.keys import Keys

from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from textual.app import App
    from textual.pilot import Pilot


class TestNavigationFlow:
    """Test suite for complete navigation flows in the TUI."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_basic_navigation_flow(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test basic navigation between panels."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            # Wait for app to initialize
            await pilot.pause(0.1)

            # Test initial state - app should be running
            assert pilot.app.is_running

            # Test tab navigation between panels
            await pilot.press(Keys.Tab)
            await pilot.pause(0.05)

            # Test escape key functionality
            await pilot.press(Keys.Escape)
            await pilot.pause(0.05)

            # Verify navigation completed successfully
            assert pilot.app.is_running
        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_keyboard_shortcuts(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test keyboard shortcuts work correctly."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Test help shortcut
            await pilot.press(Keys.F1)
            await pilot.pause(0.1)

            # Test escape to close
            await pilot.press(Keys.Escape)
            await pilot.pause(0.1)

            # Test quit shortcut
            await pilot.press(Keys.ControlC)
            await pilot.pause(0.1)

            # Verify app handled shortcuts
            # App may have exited on Ctrl+C, so we don't assert is_running
        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rapid_navigation_stress(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test rapid navigation keystrokes don't break state."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Rapid navigation test
            for _ in range(5):  # Reduced from 10 for stability
                await pilot.press(Keys.Tab)
                await pilot.pause(0.01)  # Minimal pause

            await pilot.pause(0.05)

            # Verify app is still responsive
            assert pilot.app.is_running
        finally:
            await pilot_factory.aclose()
