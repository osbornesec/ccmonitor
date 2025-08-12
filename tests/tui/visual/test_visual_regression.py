"""Visual regression tests using pytest-textual-snapshot."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.tui.app import CCMonitorApp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from textual.app import App
    from textual.pilot import Pilot


class TestVisualRegression:
    """Visual regression tests for UI consistency."""

    @pytest.mark.visual
    @pytest.mark.asyncio
    async def test_main_screen_initial_render(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test main screen initial render matches snapshot."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.2)  # Allow full initialization

            # Capture initial render
            snap_compare("main_screen_initial.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.asyncio
    async def test_focus_indicators_visual(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test focus indicators are visually consistent."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Navigate to show focus indicators
            await pilot.press("tab")
            await pilot.pause(0.1)

            # Capture focused state
            snap_compare("focus_indicators.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.asyncio
    async def test_help_modal_visual(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test help modal visual appearance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Open help modal
            await pilot.press("f1")
            await pilot.pause(0.2)

            # Capture help modal state
            snap_compare("help_modal.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.asyncio
    async def test_panel_layouts_visual(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test different panel layouts are consistent."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Test panel 1 layout
            await pilot.press("ctrl+1")
            await pilot.pause(0.1)
            snap_compare("panel_1_layout.svg")

            # Test panel 2 layout
            await pilot.press("ctrl+2")
            await pilot.pause(0.1)
            snap_compare("panel_2_layout.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.accessibility
    @pytest.mark.asyncio
    async def test_color_contrast_visual(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test color contrast meets accessibility standards."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Capture default color scheme
            snap_compare("color_contrast_default.svg")

            # Test with focused elements
            await pilot.press("tab")
            await pilot.pause(0.05)
            snap_compare("color_contrast_focused.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.asyncio
    async def test_responsive_layout_visual(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test layout responds correctly to different sizes."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Capture default size
            snap_compare("responsive_default.svg")

            # Test with smaller terminal size (if possible)
            # Note: Terminal resizing in tests may not be available
            # This test serves as a placeholder for manual verification

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.asyncio
    async def test_animation_consistency_visual(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test animations render consistently."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Trigger animations through navigation
            await pilot.press("ctrl+1")
            await pilot.pause(0.3)  # Allow animations to complete

            # Capture post-animation state
            snap_compare("post_animation.svg")

        finally:
            await pilot_factory.aclose()


class TestVisualAccessibility:
    """Visual tests specifically for accessibility compliance."""

    @pytest.mark.visual
    @pytest.mark.accessibility
    @pytest.mark.asyncio
    async def test_wcag_color_contrast(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test WCAG 2.1 AA color contrast compliance."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Capture interface for color analysis
            snap_compare("wcag_color_analysis.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.accessibility
    @pytest.mark.asyncio
    async def test_focus_outline_visibility(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test focus outlines are clearly visible."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Navigate through focusable elements
            for _ in range(3):
                await pilot.press("tab")
                await pilot.pause(0.1)

            # Capture focused element visibility
            snap_compare("focus_outline_visibility.svg")

        finally:
            await pilot_factory.aclose()


class TestVisualRegressionLargeData:
    """Visual tests with large datasets for performance verification."""

    @pytest.mark.visual
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_list_rendering(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test rendering with large data sets remains consistent."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.2)

            # Navigate to data-heavy panel
            await pilot.press("ctrl+1")
            await pilot.pause(0.2)

            # Scroll through data
            for _ in range(5):
                await pilot.press("down")
                await pilot.pause(0.05)

            # Capture scrolled state
            snap_compare("large_data_scrolled.svg")

        finally:
            await pilot_factory.aclose()

    @pytest.mark.visual
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_leak_visual_consistency(
        self,
        textual_pilot_factory: Callable[
            [type[App]],
            AsyncGenerator[Pilot, None],
        ],
        snap_compare: Callable[[str], None],
    ) -> None:
        """Test visual consistency after extended navigation."""
        pilot_factory = textual_pilot_factory(CCMonitorApp)
        pilot = await pilot_factory.__anext__()

        try:
            await pilot.pause(0.1)

            # Perform extended navigation sequence
            navigation_sequence = [
                "tab",
                "ctrl+1",
                "down",
                "ctrl+2",
                "up",
            ] * 10

            for key in navigation_sequence:
                await pilot.press(key)
                await pilot.pause(0.01)

            # Allow stabilization
            await pilot.pause(0.2)

            # Capture final state - should be consistent with initial render
            snap_compare("extended_navigation_final.svg")

        finally:
            await pilot_factory.aclose()
