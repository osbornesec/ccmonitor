"""Tests for responsive layout system."""

from __future__ import annotations

from src.tui.utils.responsive import (
    LayoutConfig,
    ResponsiveBreakpoints,
    ResponsiveManager,
    ScreenSize,
    create_responsive_config,
    responsive_manager,
)

# Test constants to avoid magic numbers
DEFAULT_TINY_MAX = 59
DEFAULT_SMALL_MAX = 79
DEFAULT_MEDIUM_MAX = 119
DEFAULT_LARGE_MAX = 159

CUSTOM_TINY_MAX = 40
CUSTOM_SMALL_MAX = 60
CUSTOM_MEDIUM_MAX = 100
CUSTOM_LARGE_MAX = 140

TEST_MEDIUM_WIDTH = 80
TEST_MEDIUM_HEIGHT = 24
TEST_LARGE_WIDTH = 140
TEST_LARGE_HEIGHT = 40
EXPECTED_UPDATE_COUNT = 2

TEST_DIMENSION_SMALL = 30
TEST_DIMENSION_TINY_MAX = 59
TEST_DIMENSION_SMALL_START = 60
TEST_DIMENSION_SMALL_MAX = 79
TEST_DIMENSION_MEDIUM_START = 80
TEST_DIMENSION_MEDIUM_MAX = 119
TEST_DIMENSION_LARGE_START = 120
TEST_DIMENSION_LARGE_MAX = 159
TEST_DIMENSION_XLARGE_START = 160
TEST_DIMENSION_XLARGE_LARGE = 200
TEST_DIMENSION_VERY_LARGE = 10000

TEST_RESIZE_WIDTH = 100
TEST_RESIZE_HEIGHT = 30


class TestScreenSize:
    """Test ScreenSize enum values."""

    def test_screen_size_values(self) -> None:
        """Test that screen size enum has expected values."""
        assert ScreenSize.TINY.value == "tiny"
        assert ScreenSize.SMALL.value == "small"
        assert ScreenSize.MEDIUM.value == "medium"
        assert ScreenSize.LARGE.value == "large"
        assert ScreenSize.XLARGE.value == "xlarge"


class TestResponsiveBreakpoints:
    """Test responsive breakpoint system."""

    def test_default_breakpoints(self) -> None:
        """Test default breakpoint values."""
        breakpoints = ResponsiveBreakpoints()
        assert breakpoints.tiny_max == DEFAULT_TINY_MAX
        assert breakpoints.small_max == DEFAULT_SMALL_MAX
        assert breakpoints.medium_max == DEFAULT_MEDIUM_MAX
        assert breakpoints.large_max == DEFAULT_LARGE_MAX

    def test_custom_breakpoints(self) -> None:
        """Test custom breakpoint values."""
        breakpoints = ResponsiveBreakpoints(
            tiny_max=CUSTOM_TINY_MAX,
            small_max=CUSTOM_SMALL_MAX,
            medium_max=CUSTOM_MEDIUM_MAX,
            large_max=CUSTOM_LARGE_MAX,
        )
        assert breakpoints.tiny_max == CUSTOM_TINY_MAX
        assert breakpoints.small_max == CUSTOM_SMALL_MAX
        assert breakpoints.medium_max == CUSTOM_MEDIUM_MAX
        assert breakpoints.large_max == CUSTOM_LARGE_MAX

    def test_get_screen_size_tiny(self) -> None:
        """Test screen size detection for tiny screens."""
        breakpoints = ResponsiveBreakpoints()
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_SMALL)
            == ScreenSize.TINY
        )
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_TINY_MAX)
            == ScreenSize.TINY
        )

    def test_get_screen_size_small(self) -> None:
        """Test screen size detection for small screens."""
        breakpoints = ResponsiveBreakpoints()
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_SMALL_START)
            == ScreenSize.SMALL
        )
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_SMALL_MAX)
            == ScreenSize.SMALL
        )

    def test_get_screen_size_medium(self) -> None:
        """Test screen size detection for medium screens."""
        breakpoints = ResponsiveBreakpoints()
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_MEDIUM_START)
            == ScreenSize.MEDIUM
        )
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_MEDIUM_MAX)
            == ScreenSize.MEDIUM
        )

    def test_get_screen_size_large(self) -> None:
        """Test screen size detection for large screens."""
        breakpoints = ResponsiveBreakpoints()
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_LARGE_START)
            == ScreenSize.LARGE
        )
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_LARGE_MAX)
            == ScreenSize.LARGE
        )

    def test_get_screen_size_xlarge(self) -> None:
        """Test screen size detection for xlarge screens."""
        breakpoints = ResponsiveBreakpoints()
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_XLARGE_START)
            == ScreenSize.XLARGE
        )
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_XLARGE_LARGE)
            == ScreenSize.XLARGE
        )


class TestLayoutConfig:
    """Test layout configuration system."""

    def test_default_layout_config(self) -> None:
        """Test default layout configuration."""
        config = LayoutConfig()

        # Check default panel widths
        assert config.panel_widths is not None
        assert config.panel_widths[ScreenSize.TINY] == "100%"
        assert config.panel_widths[ScreenSize.SMALL] == "30"
        assert config.panel_widths[ScreenSize.MEDIUM] == "25%"
        assert config.panel_widths[ScreenSize.LARGE] == "20%"
        assert config.panel_widths[ScreenSize.XLARGE] == "300px"

    def test_default_panel_heights(self) -> None:
        """Test default panel height configuration."""
        config = LayoutConfig()

        assert config.panel_heights is not None
        assert config.panel_heights[ScreenSize.TINY] == "8"
        assert config.panel_heights[ScreenSize.SMALL] == "10"
        assert config.panel_heights[ScreenSize.MEDIUM] == "1fr"
        assert config.panel_heights[ScreenSize.LARGE] == "1fr"
        assert config.panel_heights[ScreenSize.XLARGE] == "1fr"

    def test_default_layout_modes(self) -> None:
        """Test default layout mode configuration."""
        config = LayoutConfig()

        assert config.layout_modes is not None
        assert config.layout_modes[ScreenSize.TINY] == "vertical"
        assert config.layout_modes[ScreenSize.SMALL] == "vertical"
        assert config.layout_modes[ScreenSize.MEDIUM] == "horizontal"
        assert config.layout_modes[ScreenSize.LARGE] == "horizontal"
        assert config.layout_modes[ScreenSize.XLARGE] == "horizontal"

    def test_default_visibility(self) -> None:
        """Test default visibility configuration."""
        config = LayoutConfig()

        assert config.visibility is not None
        for size in ScreenSize:
            assert config.visibility[size] is True

    def test_custom_layout_config(self) -> None:
        """Test custom layout configuration."""
        panel_widths: dict[ScreenSize, str | int] = {ScreenSize.MEDIUM: "50%"}
        config = LayoutConfig(panel_widths=panel_widths)

        assert config.panel_widths == panel_widths
        # Other configs should still be defaults
        assert config.panel_heights is not None
        assert config.layout_modes is not None
        assert config.visibility is not None


class MockResponsiveWidget:
    """Mock widget for testing responsive behavior."""

    def __init__(self) -> None:
        """Initialize mock widget."""
        self.last_size: ScreenSize | None = None
        self.last_width: int | None = None
        self.last_height: int | None = None
        self.update_count = 0

    def on_screen_size_change(
        self,
        size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Handle screen size change."""
        self.last_size = size
        self.last_width = width
        self.last_height = height
        self.update_count += 1


class TestResponsiveManager:
    """Test responsive manager functionality."""

    def test_default_initialization(self) -> None:
        """Test responsive manager default initialization."""
        manager = ResponsiveManager()
        assert isinstance(manager.breakpoints, ResponsiveBreakpoints)
        assert manager.current_screen_size is None
        assert len(manager.registered_widgets) == 0
        assert len(manager.layout_configs) == 0

    def test_widget_registration(self) -> None:
        """Test widget registration and unregistration."""
        manager = ResponsiveManager()
        widget = MockResponsiveWidget()

        # Test registration
        manager.register_widget(widget)
        assert widget in manager.registered_widgets

        # Test duplicate registration (should not add twice)
        manager.register_widget(widget)
        assert len(manager.registered_widgets) == 1

        # Test unregistration
        manager.unregister_widget(widget)
        assert widget not in manager.registered_widgets

    def test_layout_config_management(self) -> None:
        """Test layout configuration management."""
        manager = ResponsiveManager()
        config = LayoutConfig()

        manager.set_layout_config("test-widget", config)
        assert manager.layout_configs["test-widget"] == config

    def test_resize_handling_no_change(self) -> None:
        """Test resize handling when size category doesn't change."""
        manager = ResponsiveManager()
        widget = MockResponsiveWidget()
        manager.register_widget(widget)

        # Start with medium screen
        manager.handle_resize_sync(TEST_MEDIUM_WIDTH, TEST_MEDIUM_HEIGHT)
        assert manager.current_screen_size == ScreenSize.MEDIUM
        assert widget.update_count == 1

        # Resize within same category
        manager.handle_resize_sync(TEST_RESIZE_WIDTH, TEST_RESIZE_HEIGHT)
        assert manager.current_screen_size == ScreenSize.MEDIUM
        assert widget.update_count == 1  # Should not update again

    def test_resize_handling_with_change(self) -> None:
        """Test resize handling when size category changes."""
        manager = ResponsiveManager()
        widget = MockResponsiveWidget()
        manager.register_widget(widget)

        # Start with medium screen
        manager.handle_resize_sync(TEST_MEDIUM_WIDTH, TEST_MEDIUM_HEIGHT)
        assert manager.current_screen_size == ScreenSize.MEDIUM
        assert widget.last_size == ScreenSize.MEDIUM
        assert widget.update_count == 1

        # Change to large screen
        manager.handle_resize_sync(TEST_LARGE_WIDTH, TEST_LARGE_HEIGHT)
        # Manager should now be in large screen size
        assert manager.current_screen_size == ScreenSize.LARGE  # type: ignore[comparison-overlap]
        assert widget.last_size == ScreenSize.LARGE
        assert widget.last_width == TEST_LARGE_WIDTH
        assert widget.last_height == TEST_LARGE_HEIGHT
        assert widget.update_count == EXPECTED_UPDATE_COUNT

    def test_widget_notification_error_handling(self) -> None:
        """Test that widget notification errors don't break the system."""
        manager = ResponsiveManager()

        class FailingWidget:
            def on_screen_size_change(
                self,
                size: ScreenSize,  # noqa: ARG002
                width: int,  # noqa: ARG002
                height: int,  # noqa: ARG002
            ) -> None:
                msg = "Widget update failed"
                raise RuntimeError(msg)

        failing_widget = FailingWidget()
        working_widget = MockResponsiveWidget()

        manager.register_widget(failing_widget)
        manager.register_widget(working_widget)

        # This should not raise an exception
        manager.handle_resize_sync(TEST_MEDIUM_WIDTH, TEST_MEDIUM_HEIGHT)

        # Working widget should still be updated
        assert working_widget.update_count == 1

    def test_get_adaptive_styles_no_config(self) -> None:
        """Test adaptive styles with no configuration."""
        manager = ResponsiveManager()
        styles = manager.get_adaptive_styles(
            "unknown-widget",
            ScreenSize.MEDIUM,
        )
        assert styles == {}

    def test_get_adaptive_styles_with_config(self) -> None:
        """Test adaptive styles with configuration."""
        manager = ResponsiveManager()
        config = LayoutConfig()
        manager.set_layout_config("test-widget", config)

        styles = manager.get_adaptive_styles("test-widget", ScreenSize.MEDIUM)
        assert styles["width"] == "25%"
        assert styles["height"] == "1fr"
        assert styles["display"] == "block"

    def test_should_stack_vertically(self) -> None:
        """Test vertical stacking logic."""
        manager = ResponsiveManager()

        assert manager.should_stack_vertically(ScreenSize.TINY) is True
        assert manager.should_stack_vertically(ScreenSize.SMALL) is True
        assert manager.should_stack_vertically(ScreenSize.MEDIUM) is False
        assert manager.should_stack_vertically(ScreenSize.LARGE) is False
        assert manager.should_stack_vertically(ScreenSize.XLARGE) is False

    def test_get_content_priority(self) -> None:
        """Test content priority ordering."""
        manager = ResponsiveManager()

        tiny_priority = manager.get_content_priority(ScreenSize.TINY)
        assert tiny_priority == ["main-content", "status", "navigation"]

        small_priority = manager.get_content_priority(ScreenSize.SMALL)
        assert small_priority == ["main-content", "navigation", "status"]

        medium_priority = manager.get_content_priority(ScreenSize.MEDIUM)
        assert medium_priority == ["navigation", "main-content", "status"]


class TestCreateResponsiveConfig:
    """Test responsive configuration helper function."""

    def test_create_responsive_config_defaults(self) -> None:
        """Test creating responsive config with default values."""
        config = create_responsive_config()

        assert config.panel_widths is not None
        assert config.panel_widths[ScreenSize.TINY] == "100%"
        assert config.panel_widths[ScreenSize.SMALL] == "30"
        assert config.panel_widths[ScreenSize.MEDIUM] == "25%"
        assert config.panel_widths[ScreenSize.LARGE] == "20%"
        assert config.panel_widths[ScreenSize.XLARGE] == "300px"

    def test_create_responsive_config_custom(self) -> None:
        """Test creating responsive config with custom values."""
        config = create_responsive_config(
            tiny_width="90%",
            small_width="40",
            medium_width="35%",
            large_width="30%",
            xlarge_width="400px",
        )

        assert config.panel_widths is not None
        assert config.panel_widths[ScreenSize.TINY] == "90%"
        assert config.panel_widths[ScreenSize.SMALL] == "40"
        assert config.panel_widths[ScreenSize.MEDIUM] == "35%"
        assert config.panel_widths[ScreenSize.LARGE] == "30%"
        assert config.panel_widths[ScreenSize.XLARGE] == "400px"


class TestGlobalResponsiveManager:
    """Test global responsive manager instance."""

    def test_global_manager_exists(self) -> None:
        """Test that global responsive manager exists."""
        assert responsive_manager is not None
        assert isinstance(responsive_manager, ResponsiveManager)

    def test_global_manager_isolation(self) -> None:
        """Test that global manager doesn't affect local instances."""
        local_manager = ResponsiveManager()
        widget = MockResponsiveWidget()

        # Register widget only to local manager
        local_manager.register_widget(widget)

        # Global manager should not have the widget
        assert widget not in responsive_manager.registered_widgets
        assert widget in local_manager.registered_widgets


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_dimensions(self) -> None:
        """Test handling of zero dimensions."""
        breakpoints = ResponsiveBreakpoints()
        assert breakpoints.get_screen_size(0) == ScreenSize.TINY

    def test_negative_dimensions(self) -> None:
        """Test handling of negative dimensions."""
        manager = ResponsiveManager()
        widget = MockResponsiveWidget()
        manager.register_widget(widget)

        negative_width = -10
        negative_height = -5

        # Should not crash with negative dimensions
        manager.handle_resize_sync(negative_width, negative_height)
        # Still should be tiny (smallest category)
        assert manager.current_screen_size == ScreenSize.TINY

    def test_very_large_dimensions(self) -> None:
        """Test handling of very large dimensions."""
        breakpoints = ResponsiveBreakpoints()
        assert (
            breakpoints.get_screen_size(TEST_DIMENSION_VERY_LARGE)
            == ScreenSize.XLARGE
        )

    def test_empty_widget_list(self) -> None:
        """Test resize handling with no registered widgets."""
        manager = ResponsiveManager()

        # Should not crash with no widgets
        manager.handle_resize_sync(TEST_RESIZE_WIDTH, TEST_RESIZE_HEIGHT)
        assert manager.current_screen_size == ScreenSize.MEDIUM

    def test_config_with_none_values(self) -> None:
        """Test layout config with None values."""
        config = LayoutConfig(
            panel_widths=None,
            panel_heights=None,
            layout_modes=None,
            visibility=None,
        )

        # __post_init__ should set defaults
        assert config.panel_widths is not None
        assert config.panel_heights is not None
        assert config.layout_modes is not None
        assert config.visibility is not None
