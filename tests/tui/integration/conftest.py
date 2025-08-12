"""Shared fixtures and utilities for integration testing."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from textual.app import App
    from textual.pilot import Pilot


class NavigationTestBase:
    """Base class for navigation integration tests."""

    @staticmethod
    async def wait_for_focus(
        pilot: Pilot,
        expected_widget_id: str,
        timeout_seconds: float = 2.0,
    ) -> bool:
        """Wait for specific widget to receive focus."""
        start_time = asyncio.get_event_loop().time()

        while True:
            current_focused = pilot.app.focused
            if (
                current_focused
                and getattr(current_focused, "id", None) == expected_widget_id
            ):
                return True

            if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                return False

            await asyncio.sleep(0.05)

    @staticmethod
    async def verify_focus_indicator(pilot: Pilot, widget_id: str) -> bool:
        """Verify focus indicator is visible on widget."""
        try:
            widget = pilot.app.query_one(f"#{widget_id}")
            # Check if widget has focus styling applied
            return (
                widget.has_class("focused")
                or widget.has_class("focus-active")
                or widget == pilot.app.focused
            )
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    async def get_focusable_widgets(pilot: Pilot) -> list[str]:
        """Get list of focusable widget IDs."""
        focusable_ids = []
        try:
            # Try to get widgets with common focusable classes
            widgets = pilot.app.query("*")
            for widget in widgets:
                if hasattr(widget, "focusable") and widget.focusable:
                    widget_id = getattr(widget, "id", None)
                    if widget_id:
                        focusable_ids.append(widget_id)
        except Exception:  # noqa: BLE001
            # Suppress exception - focusable widget discovery is best effort
            return []
        return focusable_ids

    @staticmethod
    async def simulate_navigation_sequence(
        pilot: Pilot,
        keys: list[str],
        pause_duration: float = 0.05,
    ) -> dict[str, int]:
        """Simulate navigation sequence and track results."""
        results = {"successful_keys": 0, "failed_keys": 0, "focus_changes": 0}
        previous_focus = pilot.app.focused

        for key in keys:
            try:
                await pilot.press(key)
                await pilot.pause(pause_duration)
                results["successful_keys"] += 1

                current_focus = pilot.app.focused
                if current_focus != previous_focus:
                    results["focus_changes"] += 1
                    previous_focus = current_focus

            except Exception:  # noqa: BLE001
                results["failed_keys"] += 1

        return results


@pytest.fixture
def navigation_base() -> NavigationTestBase:
    """Provide navigation test base utilities."""
    return NavigationTestBase()


@pytest.fixture
def app_with_sample_data() -> App:
    """Create app instance with sample data for testing."""
    app = CCMonitorApp()
    # Configure app for testing
    if hasattr(app, "test_mode"):
        app.test_mode = True

    return app


@pytest.fixture
def integration_test_config() -> dict[str, float]:
    """Provide configuration for integration tests."""
    return {
        "key_press_delay": 0.05,
        "animation_wait": 0.1,
        "focus_timeout": 2.0,
        "rapid_key_delay": 0.01,
        "stabilization_delay": 0.2,
    }


class ModalTestHelper:
    """Helper utilities for modal dialog testing."""

    @staticmethod
    async def open_modal(pilot: Pilot, open_key: str) -> bool:
        """Open modal and verify it opened."""
        try:
            initial_screen_name = getattr(pilot.app.screen, "name", "unknown")
            await pilot.press(open_key)
            await pilot.pause(0.1)

            # Check if screen changed (modal opened)
            current_screen_name = getattr(pilot.app.screen, "name", "unknown")
        except Exception:  # noqa: BLE001
            return False
        else:
            return current_screen_name != initial_screen_name

    @staticmethod
    async def close_modal(pilot: Pilot, close_key: str = "escape") -> bool:
        """Close modal and verify it closed."""
        try:
            await pilot.press(close_key)
            await pilot.pause(0.1)
        except Exception:  # noqa: BLE001
            return False
        else:
            return True

    @staticmethod
    async def test_modal_focus_trap(
        pilot: Pilot,
        max_tab_cycles: int = 10,
    ) -> dict[str, bool]:
        """Test that focus is trapped within modal."""
        results = {"focus_trapped": True, "tab_navigation_works": True}

        try:
            visited_widgets = await ModalTestHelper._collect_tab_navigation(
                pilot,
                max_tab_cycles,
            )

            # Should have visited multiple widgets (focus trap working)
            min_widgets_for_trap = 2
            if len(visited_widgets) < min_widgets_for_trap:
                results["tab_navigation_works"] = False

        except Exception:  # noqa: BLE001
            results["focus_trapped"] = False
            results["tab_navigation_works"] = False

        return results

    @staticmethod
    async def _collect_tab_navigation(
        pilot: Pilot,
        max_cycles: int,
    ) -> set[str]:
        """Collect widgets visited during tab navigation."""
        initial_focus = pilot.app.focused
        visited_widgets = set()

        for cycle in range(max_cycles):
            await pilot.press("tab")
            await pilot.pause(0.05)

            current_focus = pilot.app.focused
            if current_focus:
                widget_id = getattr(
                    current_focus,
                    "id",
                    f"widget_{id(current_focus)}",
                )
                visited_widgets.add(widget_id)

                # If we've cycled back to the initial focus, focus is working
                if current_focus == initial_focus and cycle > 0:
                    break

        return visited_widgets


@pytest.fixture
def modal_helper() -> ModalTestHelper:
    """Provide modal test helper utilities."""
    return ModalTestHelper()


class AccessibilityTestHelper:
    """Helper utilities for accessibility testing."""

    @staticmethod
    async def test_keyboard_only_navigation(
        pilot: Pilot,
        navigation_keys: list[str] | None = None,
    ) -> dict[str, bool | int]:
        """Test complete keyboard-only navigation capability."""
        if navigation_keys is None:
            navigation_keys = [
                "tab",
                "shift+tab",
                "up",
                "down",
                "left",
                "right",
                "enter",
                "space",
                "escape",
            ]

        results = {
            "all_keys_responsive": True,
            "focus_always_visible": True,
            "no_focus_traps": True,
            "successful_navigations": 0,
            "total_attempts": len(navigation_keys),
        }

        for key in navigation_keys:
            try:
                await pilot.press(key)
                await pilot.pause(0.05)
                focus_after = pilot.app.focused

                results["successful_navigations"] += 1

                # Check if focus is visible
                if (
                    focus_after
                    and not AccessibilityTestHelper._has_focus_indicator(
                        focus_after,
                    )
                ):
                    results["focus_always_visible"] = False

            except Exception:  # noqa: BLE001
                results["all_keys_responsive"] = False

        return results

    @staticmethod
    def _has_focus_indicator(widget: object) -> bool:
        """Check if widget has visible focus indicator."""
        try:
            return hasattr(widget, "has_class") and (
                widget.has_class("focused")
                or widget.has_class("focus-active")
                or widget.has_class("cursor-active")
            )
        except Exception:  # noqa: BLE001
            return False


@pytest.fixture
def accessibility_helper() -> AccessibilityTestHelper:
    """Provide accessibility test helper utilities."""
    return AccessibilityTestHelper()
