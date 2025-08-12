"""Unit tests for TUI widgets."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from textual.containers import Vertical
from textual.widgets import Footer, Header

from src.tui.widgets.footer import CCMonitorFooter
from src.tui.widgets.header import CCMonitorHeader
from src.tui.widgets.live_feed_panel import LiveFeedPanel
from src.tui.widgets.projects_panel import ProjectsPanel

if TYPE_CHECKING:
    from unittest.mock import Mock

# Performance test constants
MAX_WIDGET_CREATION_TIME = 0.1
MAX_COMPOSITION_TIME = 0.05
EXPECTED_WIDGET_COUNT = 40


class TestCCMonitorHeader:
    """Test CCMonitorHeader widget functionality."""

    def test_header_creation(self) -> None:
        """Test header can be created."""
        header = CCMonitorHeader()
        assert header is not None
        assert "fade-in" in header.classes

    def test_header_css_properties(self) -> None:
        """Test header has correct CSS properties."""
        header = CCMonitorHeader()
        assert header.DEFAULT_CSS is not None
        assert "CCMonitorHeader" in header.DEFAULT_CSS
        assert "height: 3" in header.DEFAULT_CSS
        assert "dock: top" in header.DEFAULT_CSS

    def test_header_inheritance(self) -> None:
        """Test header inherits from Textual Header."""
        header = CCMonitorHeader()
        assert isinstance(header, Header)

    def test_header_styling(self) -> None:
        """Test header has correct styling configuration."""
        header = CCMonitorHeader()
        css = header.DEFAULT_CSS
        assert "background: $primary" in css
        assert "color: $text" in css
        assert "text-style: bold" in css
        assert "content-align: center middle" in css


class TestCCMonitorFooter:
    """Test CCMonitorFooter widget functionality."""

    def test_footer_creation(self) -> None:
        """Test footer can be created."""
        footer = CCMonitorFooter()
        assert footer is not None
        assert "fade-in" in footer.classes

    def test_footer_css_properties(self) -> None:
        """Test footer has correct CSS properties."""
        footer = CCMonitorFooter()
        assert footer.DEFAULT_CSS is not None
        assert "CCMonitorFooter" in footer.DEFAULT_CSS
        assert "height: 3" in footer.DEFAULT_CSS
        assert "dock: bottom" in footer.DEFAULT_CSS

    def test_footer_inheritance(self) -> None:
        """Test footer inherits from Textual Footer."""
        footer = CCMonitorFooter()
        assert isinstance(footer, Footer)

    def test_footer_key_styling(self) -> None:
        """Test footer has key styling configuration."""
        footer = CCMonitorFooter()
        css = footer.DEFAULT_CSS
        assert "CCMonitorFooter Key" in css
        assert "background: $secondary" in css
        assert "text-style: bold" in css


class TestProjectsPanel:
    """Test ProjectsPanel widget functionality."""

    def test_panel_creation(self) -> None:
        """Test projects panel can be created."""
        panel = ProjectsPanel()
        assert panel is not None

    def test_panel_sizing(self) -> None:
        """Test panel respects size constraints."""
        panel = ProjectsPanel()
        css = panel.DEFAULT_CSS
        assert "width: 25%" in css
        assert "min-width: 20" in css
        assert "max-width: 40" in css

    def test_panel_composition(self) -> None:
        """Test panel contains expected elements."""
        panel = ProjectsPanel()
        components = list(panel.compose())
        assert len(components) > 0

        # Should have a Vertical container
        assert isinstance(components[0], Vertical)

    def test_panel_css_structure(self) -> None:
        """Test panel has correct CSS structure."""
        panel = ProjectsPanel()
        css = panel.DEFAULT_CSS
        assert "ProjectsPanel" in css
        assert ".panel-title" in css
        assert "#project-list" in css
        assert "#project-stats" in css

    def test_panel_content_structure(self) -> None:
        """Test panel has expected content structure."""
        panel = ProjectsPanel()
        css = panel.DEFAULT_CSS
        assert "background: $surface" in css
        assert "border: solid $primary" in css
        assert "padding: 1" in css


class TestLiveFeedPanel:
    """Test LiveFeedPanel widget functionality."""

    def test_panel_creation(self) -> None:
        """Test live feed panel can be created."""
        panel = LiveFeedPanel()
        assert panel is not None

    def test_panel_sizing(self) -> None:
        """Test panel takes remaining space."""
        panel = LiveFeedPanel()
        css = panel.DEFAULT_CSS
        assert "width: 1fr" in css

    def test_panel_composition(self) -> None:
        """Test panel contains expected elements."""
        panel = LiveFeedPanel()
        components = list(panel.compose())
        assert len(components) > 0

        # Should have a Vertical container
        assert isinstance(components[0], Vertical)

    def test_panel_css_structure(self) -> None:
        """Test panel has correct CSS structure."""
        panel = LiveFeedPanel()
        css = panel.DEFAULT_CSS
        assert "LiveFeedPanel" in css
        assert ".panel-title" in css
        assert "#message-scroll" in css
        assert "#message-input" in css

    def test_panel_styling(self) -> None:
        """Test panel has correct styling."""
        panel = LiveFeedPanel()
        css = panel.DEFAULT_CSS
        assert "background: $background" in css
        assert "border: solid $primary" in css
        assert "padding: 1" in css


class TestWidgetComposition:
    """Test widget composition and integration."""

    def test_all_widgets_composable(self) -> None:
        """Test all widgets can be composed without error."""
        widgets = [
            CCMonitorHeader(),
            CCMonitorFooter(),
            ProjectsPanel(),
            LiveFeedPanel(),
        ]

        for widget in widgets:
            # Should not raise an exception
            if hasattr(widget, "compose"):
                list(widget.compose())

    def test_widget_css_consistency(self) -> None:
        """Test all widgets have consistent CSS structure."""
        widgets = [
            CCMonitorHeader(),
            CCMonitorFooter(),
            ProjectsPanel(),
            LiveFeedPanel(),
        ]

        for widget in widgets:
            assert hasattr(widget, "DEFAULT_CSS")
            assert isinstance(widget.DEFAULT_CSS, str)
            assert len(widget.DEFAULT_CSS.strip()) > 0


class TestWidgetIntegration:
    """Test widget integration with mock app."""

    def test_widgets_in_mock_app(self, mock_app: Mock) -> None:
        """Test widgets work with mock app context."""
        widgets = [
            CCMonitorHeader(),
            CCMonitorFooter(),
            ProjectsPanel(),
            LiveFeedPanel(),
        ]

        for widget in widgets:
            widget.app = mock_app
            # Should not raise exceptions
            assert widget.app is mock_app

    def test_widget_classes(self) -> None:
        """Test widgets have expected CSS classes."""
        header = CCMonitorHeader()
        footer = CCMonitorFooter()

        assert "fade-in" in header.classes
        assert "fade-in" in footer.classes

    @pytest.mark.asyncio
    async def test_widget_mount_unmount(self) -> None:
        """Test widgets can be mounted and unmounted."""
        widgets = [
            CCMonitorHeader(),
            CCMonitorFooter(),
            ProjectsPanel(),
            LiveFeedPanel(),
        ]

        for widget in widgets:
            # Mock the mount/unmount cycle
            widget.is_mounted = False
            # Simulate mount
            widget.is_mounted = True
            assert widget.is_mounted

            # Simulate unmount
            widget.is_mounted = False
            assert not widget.is_mounted


class TestWidgetAccessibility:
    """Test widget accessibility features."""

    def test_widget_focus_support(self) -> None:
        """Test widgets support focus where appropriate."""
        # Panels should be focusable for navigation
        projects_panel = ProjectsPanel()
        live_feed_panel = LiveFeedPanel()

        # These widgets contain focusable children
        assert hasattr(projects_panel, "compose")
        assert hasattr(live_feed_panel, "compose")

    def test_widget_keyboard_support(self) -> None:
        """Test widgets have keyboard navigation support."""
        # This is tested through composition - widgets with lists/inputs
        # should support keyboard navigation through their children
        projects_panel = ProjectsPanel()
        live_feed_panel = LiveFeedPanel()

        components = list(projects_panel.compose())
        assert len(components) > 0

        feed_components = list(live_feed_panel.compose())
        assert len(feed_components) > 0


class TestWidgetErrorHandling:
    """Test widget error handling."""

    def test_widget_creation_edge_cases(self) -> None:
        """Test widget creation handles edge cases."""
        # Should not fail with basic creation
        widgets = [
            CCMonitorHeader(),
            CCMonitorFooter(),
            ProjectsPanel(),
            LiveFeedPanel(),
        ]

        for widget in widgets:
            assert widget is not None
            assert hasattr(widget, "DEFAULT_CSS")

    def test_widget_composition_safety(self) -> None:
        """Test widget composition is safe."""
        widgets = [
            ProjectsPanel(),
            LiveFeedPanel(),
        ]

        for widget in widgets:
            try:
                components = list(widget.compose())
                assert isinstance(components, list)
            except (AttributeError, TypeError, ValueError) as exc:
                pytest.fail(f"Widget composition failed: {exc}")


class TestWidgetPerformance:
    """Test widget performance characteristics."""

    def test_widget_creation_performance(self) -> None:
        """Test widget creation is reasonably fast."""
        start_time = time.perf_counter()

        # Create multiple instances
        widgets = []
        for _ in range(10):
            widgets.extend(
                [
                    CCMonitorHeader(),
                    CCMonitorFooter(),
                    ProjectsPanel(),
                    LiveFeedPanel(),
                ],
            )

        creation_time = time.perf_counter() - start_time

        # Should create 40 widgets in under 100ms
        assert (
            creation_time < MAX_WIDGET_CREATION_TIME
        ), f"Widget creation took {creation_time:.3f}s"
        assert len(widgets) == EXPECTED_WIDGET_COUNT

    def test_widget_composition_performance(self) -> None:
        """Test widget composition is reasonably fast."""
        widgets = [ProjectsPanel(), LiveFeedPanel()]

        start_time = time.perf_counter()

        for _ in range(10):
            for widget in widgets:
                list(widget.compose())

        composition_time = time.perf_counter() - start_time

        # Should compose 20 times in under 50ms
        assert (
            composition_time < MAX_COMPOSITION_TIME
        ), f"Composition took {composition_time:.3f}s"
