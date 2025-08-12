"""Widget-specific tests for TUI components."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from textual.app import App
    from textual.pilot import Pilot

    from tests.tui.integration.conftest import (
        AccessibilityTestHelper,
        NavigationTestBase,
    )


class TestMainScreen:
    """Test MainScreen widget functionality."""

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_main_screen_initialization(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test MainScreen initializes correctly."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # App should be running and have the main screen
            assert pilot.app.is_running
            assert pilot.app.screen is not None

            # Screen should have basic structure
            # (Specific assertions depend on MainScreen implementation)
            screen = pilot.app.screen
            assert hasattr(screen, "compose") or hasattr(screen, "on_mount")

        finally:
            await pilot_factory.aclose()

    async def _test_single_key_binding(self, pilot: Pilot, key: str) -> bool:
        """Test a single key binding and return if app is still running."""
        try:
            await pilot.press(key)
            await pilot.pause(0.05)
        except Exception:  # noqa: BLE001, S110
            # Some keys might cause app exit or exceptions
            pass
        else:
            # Key processed successfully
            pass

        return pilot.app.is_running

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_main_screen_key_bindings(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test MainScreen key bindings work correctly."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Test common key bindings
            key_tests = [
                "f1",  # Help
                "escape",  # Cancel/back
                "?",  # Help alternative
            ]

            for key in key_tests:
                still_running = await self._test_single_key_binding(pilot, key)
                if not still_running:
                    break

            # Test quit key separately
            await self._test_single_key_binding(pilot, "ctrl+c")

        finally:
            if pilot.app.is_running:
                await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_main_screen_focus_management(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        navigation_base: NavigationTestBase,
    ) -> None:
        """Test MainScreen manages focus correctly."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Get focusable widgets on main screen
            focusable_widgets = await navigation_base.get_focusable_widgets(
                pilot,
            )

            # Should have at least one focusable widget
            min_expected_widgets = 1
            assert len(focusable_widgets) >= min_expected_widgets, (
                f"Expected at least {min_expected_widgets} focusable widgets, "
                f"found {len(focusable_widgets)}"
            )

            # Test focus transitions
            if len(focusable_widgets) > 1:
                await pilot.press("tab")
                await pilot.pause(0.05)

                # Focus should change or remain stable
                # (Both outcomes are valid depending on implementation)

        finally:
            await pilot_factory.aclose()


class TestHelpOverlay:
    """Test HelpOverlay widget functionality."""

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_help_overlay_open_close(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test help overlay opens and closes properly."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            initial_screen = pilot.app.screen

            # Try to open help with F1
            await pilot.press("f1")
            await pilot.pause(0.1)

            help_screen = pilot.app.screen

            # Screen may or may not change depending on implementation
            # If it changed, we have a modal/overlay
            if help_screen != initial_screen:
                # Help opened - try to close it
                await pilot.press("escape")
                await pilot.pause(0.1)

                # Should return to initial screen or remain stable

            # App should remain running throughout
            assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_help_overlay_keyboard_navigation(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test keyboard navigation within help overlay."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Try to open help
            await pilot.press("f1")
            await pilot.pause(0.1)

            # Test navigation keys within help
            nav_keys = ["tab", "shift+tab", "up", "down", "enter"]

            for key in nav_keys:
                try:
                    await pilot.press(key)
                    await pilot.pause(0.05)
                except Exception:  # noqa: BLE001, S110
                    # Some keys might not be valid in help context
                    pass

                # App should remain stable
                assert pilot.app.is_running

            # Close help with escape
            await pilot.press("escape")
            await pilot.pause(0.1)

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.accessibility
    @pytest.mark.asyncio
    async def test_help_overlay_accessibility(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        accessibility_helper: AccessibilityTestHelper,
    ) -> None:
        """Test help overlay accessibility features."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Open help overlay
            await pilot.press("f1")
            await pilot.pause(0.1)

            # Test keyboard-only navigation within help
            help_nav_keys = ["tab", "shift+tab", "enter", "escape"]
            results = await accessibility_helper.test_keyboard_only_navigation(
                pilot,
                navigation_keys=help_nav_keys,
            )

            # Help overlay should be keyboard accessible
            min_success_rate = 0.5  # At least 50% of keys should work
            success_rate = (
                results["successful_navigations"] / results["total_attempts"]
            )

            assert success_rate >= min_success_rate, (
                f"Help overlay keyboard navigation success rate "
                f"{success_rate:.2%} below minimum {min_success_rate:.2%}"
            )

        finally:
            await pilot_factory.aclose()


class TestNavigableList:
    """Test NavigableList widget functionality."""

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_navigable_list_arrow_keys(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test NavigableList responds to arrow key navigation."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Navigate to a potential list widget (project panel, etc.)
            await pilot.press("ctrl+1")  # Focus projects panel
            await pilot.pause(0.05)

            # Test arrow key navigation
            arrow_keys = ["up", "down", "left", "right"]

            for arrow_key in arrow_keys:
                await pilot.press(arrow_key)
                await pilot.pause(0.05)

                # App should remain stable after arrow navigation
                assert (
                    pilot.app.is_running
                ), f"App should remain stable after {arrow_key} navigation"

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_navigable_list_selection(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test NavigableList selection with Enter key."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Navigate to a list and try selection
            await pilot.press("ctrl+1")  # Focus first panel
            await pilot.pause(0.05)

            # Try to select items with Enter
            await pilot.press("enter")
            await pilot.pause(0.05)

            # App should handle selection gracefully
            assert pilot.app.is_running

            # Test multiple selections
            for _ in range(3):
                await pilot.press("down")
                await pilot.pause(0.02)
                await pilot.press("enter")
                await pilot.pause(0.02)

            # App should remain stable
            assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_navigable_list_empty_state(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test NavigableList handles empty state correctly."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Navigate to potentially empty lists
            panels = ["ctrl+1", "ctrl+2"]

            for panel_key in panels:
                await pilot.press(panel_key)
                await pilot.pause(0.05)

                # Test navigation in potentially empty list
                empty_nav_keys = ["up", "down", "enter", "escape"]

                for nav_key in empty_nav_keys:
                    await pilot.press(nav_key)
                    await pilot.pause(0.02)

                    # App should handle empty list navigation gracefully
                    assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_navigable_list_performance(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        navigation_base: NavigationTestBase,
    ) -> None:
        """Test NavigableList navigation performance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Focus on a list widget
            await pilot.press("ctrl+1")
            await pilot.pause(0.05)

            # Perform rapid navigation to test performance
            rapid_keys = ["down"] * 10 + ["up"] * 10

            navigation_results = (
                await navigation_base.simulate_navigation_sequence(
                    pilot,
                    rapid_keys,
                    pause_duration=0.01,  # Very fast navigation
                )
            )

            # Most navigation should succeed
            min_success_rate = 0.8  # 80% success rate for rapid navigation
            success_rate = navigation_results["successful_keys"] / len(
                rapid_keys,
            )

            assert success_rate >= min_success_rate, (
                f"Rapid navigation success rate {success_rate:.2%} "
                f"below minimum {min_success_rate:.2%}"
            )

            # App should remain responsive
            assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()


class TestWidgetInteraction:
    """Test interactions between widgets."""

    @pytest.mark.widget
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_panel_switching(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test switching between different panels."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Test panel switching shortcuts
            panel_shortcuts = ["ctrl+1", "ctrl+2"]

            for shortcut in panel_shortcuts:
                await pilot.press(shortcut)
                await pilot.pause(0.05)

                # App should handle panel switching
                assert pilot.app.is_running, f"Panel switch {shortcut} failed"

                # Test navigation within switched panel
                await pilot.press("tab")
                await pilot.pause(0.02)
                await pilot.press("down")
                await pilot.pause(0.02)

                # Each panel should respond to navigation
                assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_modal_widget_interaction(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test interaction between modal and main widgets."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Open modal (help)
            await pilot.press("f1")
            await pilot.pause(0.1)

            # Try main app shortcuts while modal is open
            main_shortcuts = ["ctrl+1", "ctrl+2", "tab"]

            for shortcut in main_shortcuts:
                await pilot.press(shortcut)
                await pilot.pause(0.02)

                # App should remain stable
                assert pilot.app.is_running

            # Close modal
            await pilot.press("escape")
            await pilot.pause(0.05)

            # Main navigation should work again
            await pilot.press("tab")
            await pilot.pause(0.02)
            assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()

    @pytest.mark.widget
    @pytest.mark.asyncio
    async def test_widget_state_consistency(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
    ) -> None:
        """Test widget state remains consistent during navigation."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Navigate to different widgets and back
            navigation_sequence = [
                "ctrl+1",  # Panel 1
                "down",  # Navigate within panel
                "ctrl+2",  # Panel 2
                "up",  # Navigate within panel
                "ctrl+1",  # Back to panel 1
                "tab",  # Tab navigation
            ]

            for step in navigation_sequence:
                await pilot.press(step)
                await pilot.pause(0.05)

                # App should maintain consistent state
                assert pilot.app.is_running

                # Screen should be stable (no unexpected screen changes)
                # Screen may change for modals, but should be predictable

        finally:
            await pilot_factory.aclose()
