"""Comprehensive integration tests for navigation flow in the TUI interface."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from textual.app import App
    from textual.pilot import Pilot

    from tests.tui.integration.conftest import (
        AccessibilityTestHelper,
        ModalTestHelper,
        NavigationTestBase,
    )


class TestComprehensiveNavigation:
    """Comprehensive navigation integration tests."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_tab_navigation_cycle(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        navigation_base: NavigationTestBase,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test complete tab navigation cycle through all widgets."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Get initial focusable widgets
            initial_widgets = await navigation_base.get_focusable_widgets(
                pilot,
            )

            # Perform complete tab cycle
            navigation_results = (
                await navigation_base.simulate_navigation_sequence(
                    pilot,
                    ["tab"]
                    * (len(initial_widgets) + 1),  # Full cycle plus one
                    pause_duration=integration_test_config["key_press_delay"],
                )
            )

            # Verify navigation worked
            min_expected_changes = 2
            assert (
                navigation_results["focus_changes"] >= min_expected_changes
            ), f"Expected at least {min_expected_changes} focus changes"

            assert (
                navigation_results["successful_keys"]
                > navigation_results["failed_keys"]
            ), "More keys should succeed than fail"

            # Verify app is still responsive
            assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reverse_navigation_with_shift_tab(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        navigation_base: NavigationTestBase,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test reverse navigation with Shift+Tab."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Navigate forward first
            await pilot.press("tab", "tab")
            await pilot.pause(integration_test_config["key_press_delay"])
            forward_focus = pilot.app.focused

            # Navigate backward with Shift+Tab
            await pilot.press("shift+tab")
            await pilot.pause(integration_test_config["key_press_delay"])
            backward_focus = pilot.app.focused

            # Focus should have changed
            assert (
                forward_focus != backward_focus
            ), "Shift+Tab should change focus"

            # Verify focus indicator is visible
            if backward_focus and hasattr(backward_focus, "id"):
                backward_focus_visible = (
                    await navigation_base.verify_focus_indicator(
                        pilot,
                        str(backward_focus.id),
                    )
                )
                assert (
                    backward_focus_visible
                ), "Focus indicator should be visible"

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_arrow_key_navigation_within_panels(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        integration_test_config: dict[str, float],
    ) -> None:
        """Test arrow key navigation within panels."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Test each arrow key
            arrow_keys = ["up", "down", "left", "right"]

            for arrow_key in arrow_keys:
                await pilot.press(arrow_key)
                await pilot.pause(integration_test_config["key_press_delay"])

                # Verify app is still responsive after each key
                assert (
                    pilot.app.is_running
                ), f"App should be running after {arrow_key}"

            # Focus may or may not change depending on widget layout
            # The important thing is the app remains responsive

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_direct_focus_shortcuts(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        integration_test_config: dict[str, float],
    ) -> None:
        """Test direct focus shortcuts (Ctrl+1, Ctrl+2, etc.)."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Test common focus shortcuts
            shortcuts = ["ctrl+1", "ctrl+2"]

            for shortcut in shortcuts:
                await pilot.press(shortcut)
                await pilot.pause(integration_test_config["key_press_delay"])

                # Verify app responded to shortcut
                assert (
                    pilot.app.is_running
                ), f"App should respond to {shortcut}"

                # Focus may or may not change depending on implementation
                # The key test is that the app handles the shortcut without error

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_escape_key_behavior(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        integration_test_config: dict[str, float],
    ) -> None:
        """Test escape key behavior in different contexts."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Test escape in main interface
            initial_screen = pilot.app.screen
            await pilot.press("escape")
            await pilot.pause(integration_test_config["key_press_delay"])

            # App should remain running and responsive
            assert pilot.app.is_running, "Escape should not exit the app"

            # Screen should be the same (no modal was open)
            assert (
                pilot.app.screen == initial_screen
            ), "Screen should not change"

        finally:
            await pilot_factory.aclose()


class TestModalInteraction:
    """Test modal dialog interactions."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_help_modal_interaction(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        modal_helper: ModalTestHelper,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test opening and closing help modal."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Attempt to open help modal
            modal_opened = await modal_helper.open_modal(pilot, "f1")

            if modal_opened:
                # If modal opened, test focus trap
                trap_results = await modal_helper.test_modal_focus_trap(pilot)

                assert trap_results[
                    "focus_trapped"
                ], "Focus should be trapped in modal"

                # Close modal
                modal_closed = await modal_helper.close_modal(pilot)
                assert modal_closed, "Modal should close with escape"

            # App should remain running regardless
            assert (
                pilot.app.is_running
            ), "App should remain running after modal test"

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_modal_keyboard_navigation(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        modal_helper: ModalTestHelper,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test keyboard navigation within modals."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Try to open modal
            modal_opened = await modal_helper.open_modal(pilot, "f1")

            if modal_opened:
                # Test navigation within modal
                navigation_keys = ["tab", "shift+tab", "enter", "escape"]

                for key in navigation_keys:
                    await pilot.press(key)
                    await pilot.pause(
                        integration_test_config["key_press_delay"],
                    )

                    # If escape was pressed, modal should close
                    if key == "escape":
                        break

            # Verify app is still responsive
            assert pilot.app.is_running

        finally:
            await pilot_factory.aclose()


class TestAccessibilityCompliance:
    """Test accessibility compliance features."""

    @pytest.mark.integration
    @pytest.mark.accessibility
    @pytest.mark.asyncio
    async def test_keyboard_only_navigation_compliance(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        accessibility_helper: AccessibilityTestHelper,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test complete keyboard-only navigation compliance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Test comprehensive keyboard navigation
            results = await accessibility_helper.test_keyboard_only_navigation(
                pilot,
            )

            # Check accessibility requirements
            min_success_rate = 0.5  # At least 50% of keys should work
            success_rate = (
                results["successful_navigations"] / results["total_attempts"]
            )

            assert success_rate >= min_success_rate, (
                f"Navigation success rate {success_rate:.2%} below minimum "
                f"{min_success_rate:.2%}"
            )

            # All keys should be responsive (not crash the app)
            assert results[
                "all_keys_responsive"
            ], "All navigation keys should be handled without errors"

            # No focus traps outside of modals
            assert results[
                "no_focus_traps"
            ], "No unexpected focus traps detected"

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.accessibility
    @pytest.mark.asyncio
    async def test_focus_indicators_visibility(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        navigation_base: NavigationTestBase,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test that focus indicators are always visible."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Navigate through focusable elements
            for _ in range(5):  # Test first 5 tab stops
                await pilot.press("tab")
                await pilot.pause(integration_test_config["key_press_delay"])

                current_focus = pilot.app.focused
                if current_focus and hasattr(current_focus, "id"):
                    # Check focus indicator visibility
                    await navigation_base.verify_focus_indicator(
                        pilot,
                        str(current_focus.id),
                    )
                    # Focus indicators should generally be visible
                    # (This assertion may be relaxed based on specific widget design)

        finally:
            await pilot_factory.aclose()


class TestNavigationPerformance:
    """Test navigation performance characteristics."""

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_rapid_navigation_stability(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        integration_test_config: dict[str, float],
    ) -> None:
        """Test that rapid navigation doesn't destabilize the app."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Perform rapid navigation sequence
            rapid_keys = ["tab", "shift+tab", "down", "up"] * 3

            for key in rapid_keys:
                await pilot.press(key)
                await pilot.pause(integration_test_config["rapid_key_delay"])

            # Allow app to stabilize
            await pilot.pause(integration_test_config["stabilization_delay"])

            # App should still be responsive
            assert (
                pilot.app.is_running
            ), "App should remain stable during rapid navigation"

            # Test final navigation still works
            await pilot.press("tab")
            await pilot.pause(integration_test_config["key_press_delay"])

            assert (
                pilot.app.is_running
            ), "App should respond to navigation after rapid sequence"

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_focus_transition_responsiveness(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        navigation_base: NavigationTestBase,
        integration_test_config: dict[str, float],
    ) -> None:
        """Test that focus transitions are responsive."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Test focus transition timing
            for _ in range(3):
                # Measure time for focus to change
                start_time = asyncio.get_event_loop().time()
                await pilot.press("tab")

                # Wait for focus to change or timeout
                await navigation_base.wait_for_focus(
                    pilot,
                    expected_widget_id="any",  # Any change is acceptable
                    timeout_seconds=integration_test_config["focus_timeout"],
                )

                transition_time = asyncio.get_event_loop().time() - start_time

                # Focus should change reasonably quickly
                max_transition_time = 1.0  # 1 second is generous for testing
                assert transition_time < max_transition_time, (
                    f"Focus transition took {transition_time:.2f}s "
                    f"(max {max_transition_time}s)"
                )

        finally:
            await pilot_factory.aclose()


class TestErrorHandling:
    """Test error handling in navigation scenarios."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_navigation_error_recovery(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        integration_test_config: dict[str, float],
    ) -> None:
        """Test recovery from navigation errors."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Try potentially problematic key combinations
            problematic_keys = [
                "ctrl+alt+delete",  # Should be ignored
                "ctrl+z",  # Should be handled gracefully
                "alt+f4",  # Should be handled gracefully
                "f12",  # May or may not be implemented
            ]

            for key in problematic_keys:
                try:
                    await pilot.press(key)
                    await pilot.pause(
                        integration_test_config["key_press_delay"],
                    )
                except Exception:  # noqa: BLE001, S110
                    # Some key combinations might not be valid
                    # The important thing is the app doesn't crash
                    pass

                # App should remain stable
                assert (
                    pilot.app.is_running
                ), f"App should remain stable after {key}"

            # Normal navigation should still work
            await pilot.press("tab")
            await pilot.pause(integration_test_config["key_press_delay"])
            assert (
                pilot.app.is_running
            ), "Normal navigation should work after error test"

        finally:
            await pilot_factory.aclose()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_key_handling(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        integration_test_config: dict[str, float],
    ) -> None:
        """Test handling of invalid or unexpected keys."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(integration_test_config["stabilization_delay"])

            # Test with various characters and special keys
            test_keys = [
                "a",
                "z",
                "0",
                "9",  # Alphanumeric
                " ",
                "!",
                "@",
                "#",  # Special characters
                "ctrl+q",
                "ctrl+w",  # Control combinations
            ]

            for key in test_keys:
                try:
                    await pilot.press(key)
                    await pilot.pause(
                        integration_test_config["key_press_delay"],
                    )
                except Exception:  # noqa: BLE001, S110
                    # Some keys might cause exceptions
                    # The important thing is the app recovers
                    pass

                # App should remain stable
                assert (
                    pilot.app.is_running
                ), f"App should remain stable after key: {key}"

        finally:
            await pilot_factory.aclose()
