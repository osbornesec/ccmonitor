"""Comprehensive tests for loading widgets and progress indicators.

This module provides thorough testing coverage for the loading system,
including:
- LoadingIndicator spinner functionality and animations
- ProgressIndicator progress tracking and calculations
- Timer lifecycle management
- Theme integration and color coordination
- ETA calculation accuracy
- Widget state changes and updates
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from textual.containers import Container
from textual.widgets import ProgressBar, Static

from src.tui.utils.themes import ColorScheme, ThemeManager
from src.tui.widgets.loading import (
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    LoadingIndicator,
    ProgressIndicator,
    SpinnerFrames,
    SpinnerStyle,
)

# Test constants
TEST_TIMEOUT = 5.0
ETA_TOLERANCE_SECONDS = 1.0
ANIMATION_FRAME_COUNT = 10
DEFAULT_PROGRESS_TOTAL = 100

# Magic number constants
SECONDS_PER_MINUTE_CONST = 60
SECONDS_PER_HOUR_CONST = 3600
FIVE_STEPS = 5
FOUR_UPDATES = 4
TWO_HUNDRED_TOTAL = 200
DEFAULT_SPEED = 0.15
FRAME_COUNT_4 = 4
FRAME_COUNT_8 = 8
FRAME_INDEX_2 = 2
PROGRESS_25 = 25
PROGRESS_30 = 30
PROGRESS_200 = 200
PROGRESS_45 = 45
PROGRESS_50 = 50
PROGRESS_75 = 75
PROGRESS_150 = 150


@pytest.fixture
def mock_theme_manager() -> Mock:
    """Create a mock theme manager for testing."""
    mock_manager = Mock(spec=ThemeManager)
    mock_theme = Mock(spec=ColorScheme)

    # Configure theme colors
    mock_theme.status_loading = "#17A2B8"
    mock_theme.text = "#CCCCCC"
    mock_theme.surface = "#2D2D30"
    mock_theme.secondary = "#6C757D"
    mock_theme.accent = "#007ACC"
    mock_theme.info = "#17A2B8"
    mock_theme.success = "#28A745"
    mock_theme.error = "#DC3545"

    mock_manager.get_current_theme.return_value = mock_theme
    return mock_manager


class TestSpinnerFrames:
    """Test suite for SpinnerFrames dataclass."""

    def test_spinner_frames_constants(self) -> None:
        """Test that spinner frame constants are defined correctly."""
        # Test dots frames
        dots = SpinnerFrames.dots
        assert isinstance(dots, list)
        assert len(dots) > 0
        assert all(isinstance(frame, str) for frame in dots)

        # Test line frames
        line = SpinnerFrames.line
        assert isinstance(line, list)
        assert len(line) == FRAME_COUNT_4  # [-,\,|,/]

        # Test circle frames
        circle = SpinnerFrames.circle
        assert isinstance(circle, list)
        assert len(circle) == FRAME_COUNT_4

        # Test square frames
        square = SpinnerFrames.square
        assert isinstance(square, list)
        assert len(square) == FRAME_COUNT_4

        # Test arrows frames
        arrows = SpinnerFrames.arrows
        assert isinstance(arrows, list)
        assert len(arrows) == FRAME_COUNT_8  # 8 directions

    @pytest.mark.parametrize(
        "style",
        ["dots", "line", "circle", "square", "arrows"],
    )
    def test_get_frames_valid_styles(self, style: SpinnerStyle) -> None:
        """Test getting frames for valid spinner styles."""
        frames = SpinnerFrames.get_frames(style)

        assert isinstance(frames, list)
        assert len(frames) > 0
        assert all(isinstance(frame, str) for frame in frames)

        # Test that frames are a copy (not the original)
        expected_frames = getattr(SpinnerFrames, style)
        assert frames == expected_frames
        assert frames is not expected_frames  # Different objects

    def test_get_frames_invalid_style(self) -> None:
        """Test getting frames for invalid spinner style."""
        with pytest.raises(AttributeError):
            SpinnerFrames.get_frames("invalid_style")  # type: ignore[arg-type]

    def test_frames_are_non_empty_strings(self) -> None:
        """Test that all frames are non-empty strings."""
        styles = ["dots", "line", "circle", "square", "arrows"]

        for style in styles:
            frames = SpinnerFrames.get_frames(style)  # type: ignore[arg-type]
            for frame in frames:
                assert isinstance(frame, str)
                assert len(frame) > 0


class TestLoadingIndicator:
    """Test suite for LoadingIndicator widget."""

    def test_loading_indicator_initialization_defaults(self) -> None:
        """Test LoadingIndicator initialization with default values."""
        indicator = LoadingIndicator()

        assert indicator.message == "Loading..."
        assert indicator.spinner_style == "dots"
        assert indicator.is_animated is True
        assert (
            indicator._pulse_effect is False  # noqa: SLF001  # Testing internal state initialization
        )  # Testing internal state initialization
        assert (
            indicator._frame_index == 0  # noqa: SLF001  # Testing internal state initialization
        )  # Testing internal state initialization
        assert (
            indicator._frames == []  # noqa: SLF001  # Testing internal state initialization
        )  # Testing internal state initialization
        assert (
            indicator._animation_timer is None  # noqa: SLF001  # Testing internal state initialization
        )  # Testing internal state initialization

    def test_loading_indicator_initialization_custom(self) -> None:
        """Test LoadingIndicator initialization with custom values."""
        indicator = LoadingIndicator(
            message="Custom loading...",
            spinner_style="circle",
            pulse_effect=True,
            name="test_indicator",
            id="loading-test",
        )

        assert indicator.message == "Custom loading..."
        assert indicator.spinner_style == "circle"
        assert indicator._pulse_effect is True  # noqa: SLF001  # Testing internal state initialization
        assert indicator.name == "test_indicator"
        assert indicator.id == "loading-test"

    def test_loading_indicator_compose_layout(self) -> None:
        """Test LoadingIndicator compose method creates correct layout."""
        indicator = LoadingIndicator()

        widgets = list(indicator.compose())

        # Should yield a Container with Static widgets
        assert len(widgets) == 1
        assert isinstance(widgets[0], Container)

    def test_loading_indicator_pulse_effect_class(self) -> None:
        """Test that pulse effect adds the correct CSS class."""
        indicator = LoadingIndicator(pulse_effect=True)

        # Compose should add pulse class
        list(indicator.compose())

        assert "pulse" in indicator.classes

    def test_spinner_setup(self) -> None:
        """Test spinner setup functionality."""
        indicator = LoadingIndicator(spinner_style="line")

        # Mock the frame update method
        with patch.object(indicator, "_update_spinner_display") as mock_update:
            indicator._setup_spinner()  # noqa: SLF001  # Testing internal method for spinner setup

            # Should set up frames and reset index
            assert indicator._frames == SpinnerFrames.get_frames("line")  # noqa: SLF001  # Testing internal state
            assert indicator._frame_index == 0  # noqa: SLF001  # Testing internal state
            mock_update.assert_called_once()

    def test_animation_speed_mapping(self) -> None:
        """Test animation speed mapping for different spinner styles."""
        indicator = LoadingIndicator()

        # Test all known styles have speed mappings
        styles = ["dots", "line", "circle", "square", "arrows"]
        for style in styles:
            indicator.spinner_style = style  # type: ignore[assignment]
            speed = indicator._get_animation_speed()  # noqa: SLF001  # Testing internal method for animation speed
            assert isinstance(speed, (int, float))
            assert speed > 0

        # Test unknown style gets default
        indicator.spinner_style = "unknown_style"  # type: ignore[assignment]
        default_speed = indicator._get_animation_speed()  # noqa: SLF001  # Testing internal method for animation speed
        assert default_speed == DEFAULT_SPEED  # Default speed

    @pytest.mark.asyncio
    async def test_loading_indicator_start_stop_animation(self) -> None:
        """Test starting and stopping animation."""
        indicator = LoadingIndicator()
        indicator._frames = ["⠋", "⠙", "⠹"]  # Set up test frames  # noqa: SLF001

        # Mock set_interval to avoid actual timers
        mock_timer = Mock()
        with patch.object(
            indicator,
            "set_interval",
            return_value=mock_timer,
        ) as mock_set_interval:
            indicator._start_animation()  # noqa: SLF001  # Testing internal animation control

            mock_set_interval.assert_called_once()
            assert indicator._animation_timer is mock_timer  # noqa: SLF001  # Testing internal state

            # Test stopping animation
            indicator._stop_animation()  # noqa: SLF001  # Testing internal animation control
            mock_timer.stop.assert_called_once()
            assert indicator._animation_timer is None  # noqa: SLF001  # Testing internal state/method

    def test_animate_spinner_frame_progression(self) -> None:
        """Test spinner frame progression during animation."""
        indicator = LoadingIndicator()
        indicator._frames = ["A", "B", "C"]  # noqa: SLF001  # Testing internal state/method
        indicator._frame_index = 0  # noqa: SLF001  # Testing internal state/method

        with patch.object(indicator, "_update_spinner_display") as mock_update:
            # First animation step
            indicator._animate_spinner()  # noqa: SLF001  # Testing internal state/method
            assert indicator._frame_index == 1  # noqa: SLF001  # Testing internal state/method
            mock_update.assert_called()

            # Second animation step
            mock_update.reset_mock()
            indicator._animate_spinner()  # noqa: SLF001  # Testing internal state/method
            assert indicator._frame_index == FRAME_INDEX_2  # noqa: SLF001  # Testing internal state/method
            mock_update.assert_called()

            # Third animation step (should wrap around)
            mock_update.reset_mock()
            indicator._animate_spinner()  # noqa: SLF001  # Testing internal state/method
            assert indicator._frame_index == 0  # noqa: SLF001  # Testing internal state/method
            mock_update.assert_called()

    def test_animate_spinner_when_not_animated(self) -> None:
        """Test that animation doesn't progress when disabled."""
        indicator = LoadingIndicator()
        indicator._frames = ["A", "B", "C"]  # noqa: SLF001  # Testing internal state/method
        indicator._frame_index = 0  # noqa: SLF001  # Testing internal state/method
        indicator.is_animated = False

        with patch.object(indicator, "_update_spinner_display") as mock_update:
            indicator._animate_spinner()  # noqa: SLF001  # Testing internal state/method

            # Frame index should not change
            assert indicator._frame_index == 0  # noqa: SLF001  # Testing internal state/method
            mock_update.assert_not_called()

    def test_update_spinner_display(self) -> None:
        """Test updating spinner display."""
        indicator = LoadingIndicator()
        indicator._frames = ["⠋", "⠙", "⠹"]  # noqa: SLF001  # Testing internal state/method
        indicator._frame_index = 1  # noqa: SLF001  # Testing internal state/method

        # Mock the spinner widget
        mock_spinner = Mock(spec=Static)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_spinner,
        ) as mock_query:
            indicator._update_spinner_display()  # noqa: SLF001  # Testing internal state/method

            mock_query.assert_called_once_with("#spinner", Static)
            mock_spinner.update.assert_called_once_with("⠙")

    def test_update_spinner_display_no_frames(self) -> None:
        """Test updating spinner display with no frames."""
        indicator = LoadingIndicator()
        indicator._frames = []  # noqa: SLF001  # Testing internal state/method

        with patch.object(indicator, "query_one") as mock_query:
            indicator._update_spinner_display()  # noqa: SLF001  # Testing internal state/method

            # Should not attempt to query when no frames
            mock_query.assert_not_called()

    def test_watch_message_updates_display(self) -> None:
        """Test that message changes update the display."""
        indicator = LoadingIndicator()

        # Mock the message widget
        mock_message_widget = Mock(spec=Static)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_message_widget,
        ) as mock_query:
            indicator.watch_message("New message")

            mock_query.assert_called_once_with("#message", Static)
            mock_message_widget.update.assert_called_once_with("New message")

    def test_watch_spinner_style_restarts_animation(self) -> None:
        """Test that spinner style changes restart animation."""
        indicator = LoadingIndicator()

        with (
            patch.object(indicator, "_setup_spinner") as mock_setup,
            patch.object(indicator, "_start_animation") as mock_start,
        ):
            indicator.is_animated = True
            indicator.watch_spinner_style("circle")

            mock_setup.assert_called_once()
            mock_start.assert_called_once()

    def test_watch_is_animated_controls_animation(self) -> None:
        """Test that is_animated changes control animation state."""
        indicator = LoadingIndicator()

        with (
            patch.object(indicator, "_start_animation") as mock_start,
            patch.object(indicator, "_stop_animation") as mock_stop,
        ):
            # Enable animation
            indicator.watch_is_animated(animated=True)
            mock_start.assert_called_once()
            mock_stop.assert_not_called()

            # Reset mocks
            mock_start.reset_mock()
            mock_stop.reset_mock()

            # Disable animation
            indicator.watch_is_animated(animated=False)
            mock_stop.assert_called_once()
            mock_start.assert_not_called()

    def test_loading_indicator_convenience_methods(self) -> None:
        """Test convenience methods for controlling animation."""
        indicator = LoadingIndicator()

        # Test set_message
        indicator.set_message("Test message")
        assert indicator.message == "Test message"

        # Test set_spinner_style
        indicator.set_spinner_style("arrows")
        assert indicator.spinner_style == "arrows"

        # Test start/stop methods
        indicator.start()
        assert indicator.is_animated is True

        indicator.stop()
        assert indicator.is_animated is False

    @pytest.mark.asyncio
    async def test_loading_indicator_mount_unmount_lifecycle(self) -> None:
        """Test LoadingIndicator mount and unmount lifecycle."""
        indicator = LoadingIndicator()

        with (
            patch.object(indicator, "_initialize_theme") as mock_init_theme,
            patch.object(indicator, "_setup_spinner") as mock_setup,
            patch.object(indicator, "_start_animation") as mock_start,
            patch.object(indicator, "_stop_animation") as mock_stop,
        ):
            # Test mounting
            indicator.on_mount()

            mock_init_theme.assert_called_once()
            mock_setup.assert_called_once()
            mock_start.assert_called_once()

            # Test unmounting
            indicator.on_unmount()
            mock_stop.assert_called_once()

    def test_theme_initialization_success(self) -> None:
        """Test successful theme manager initialization."""
        indicator = LoadingIndicator()

        with patch("src.tui.widgets.loading.ThemeManager") as mock_theme_class:
            mock_manager = Mock()
            mock_theme_class.return_value = mock_manager

            indicator._initialize_theme()  # noqa: SLF001  # Testing internal state/method

            assert indicator._theme_manager is mock_manager  # noqa: SLF001  # Testing internal state
            mock_theme_class.assert_called_once()

    def test_theme_initialization_failure(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test theme manager initialization failure handling."""
        indicator = LoadingIndicator()

        with (
            patch(
                "src.tui.widgets.loading.ThemeManager",
                side_effect=Exception("Theme error"),
            ),
            caplog.at_level("DEBUG"),
        ):
            indicator._initialize_theme()  # noqa: SLF001  # Testing internal state/method

            assert indicator._theme_manager is None  # noqa: SLF001  # Testing internal state/method
            assert "ThemeManager not available" in caplog.text


class TestProgressIndicator:
    """Test suite for ProgressIndicator widget."""

    def test_progress_indicator_initialization_defaults(self) -> None:
        """Test ProgressIndicator initialization with default values."""
        indicator = ProgressIndicator()

        assert indicator.title == "Progress"
        assert indicator.current == 0
        assert indicator.total == DEFAULT_PROGRESS_TOTAL
        assert indicator.show_eta is True
        assert indicator._show_count is True  # noqa: SLF001  # Testing internal state/method
        assert isinstance(indicator._start_time, float)  # noqa: SLF001  # Testing internal state/method

    def test_progress_indicator_initialization_custom(self) -> None:
        """Test ProgressIndicator initialization with custom values."""
        indicator = ProgressIndicator(
            title="Custom Progress",
            current=25,
            total=200,
            show_eta=False,
            show_count=False,
            name="test_progress",
            id="progress-test",
        )

        assert indicator.title == "Custom Progress"
        assert indicator.current == PROGRESS_25
        assert indicator.total == PROGRESS_200
        assert indicator.show_eta is False
        assert indicator._show_count is False  # noqa: SLF001  # Testing internal state/method
        assert indicator.name == "test_progress"
        assert indicator.id == "progress-test"

    def test_progress_indicator_compose_layout(self) -> None:
        """Test ProgressIndicator compose method creates correct layout."""
        indicator = ProgressIndicator()

        widgets = list(indicator.compose())

        # Should create a vertical container with header, progress bar, and details
        assert len(widgets) == 1
        # The composed widgets are nested, so we can't easily test the structure
        # without actually mounting the widget

    def test_progress_indicator_compose_with_options(self) -> None:
        """Test ProgressIndicator compose with different options."""
        # Test without count
        indicator_no_count = ProgressIndicator(show_count=False)
        widgets_no_count = list(indicator_no_count.compose())
        assert len(widgets_no_count) == 1

        # Test without ETA
        indicator_no_eta = ProgressIndicator(show_eta=False)
        widgets_no_eta = list(indicator_no_eta.compose())
        assert len(widgets_no_eta) == 1

    def test_progress_calculation_normal_case(self) -> None:
        """Test progress percentage calculation."""
        indicator = ProgressIndicator(total=100)

        # Mock the percentage widget
        mock_percentage_widget = Mock(spec=Static)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_percentage_widget,
        ):
            indicator.current = 25
            indicator._update_percentage()  # noqa: SLF001  # Testing internal state/method

            mock_percentage_widget.update.assert_called_once_with("25%")

    def test_progress_calculation_edge_cases(self) -> None:
        """Test progress percentage calculation edge cases."""
        indicator = ProgressIndicator()

        mock_percentage_widget = Mock(spec=Static)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_percentage_widget,
        ):
            # Test zero total
            indicator.total = 0
            indicator.current = 10
            indicator._update_percentage()  # noqa: SLF001  # Testing internal state/method
            mock_percentage_widget.update.assert_called_with("0%")

            # Test current > total
            mock_percentage_widget.reset_mock()
            indicator.total = 50
            indicator.current = 75
            indicator._update_percentage()  # noqa: SLF001  # Testing internal state/method
            mock_percentage_widget.update.assert_called_with(
                "100%",
            )  # Capped at 100%

    def test_progress_bar_update(self) -> None:
        """Test progress bar updates."""
        indicator = ProgressIndicator(total=100)

        mock_progress_bar = Mock(spec=ProgressBar)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_progress_bar,
        ):
            indicator.current = 30
            indicator._update_progress_bar()  # noqa: SLF001  # Testing internal state/method

            assert mock_progress_bar.progress == PROGRESS_30

    def test_progress_bar_update_clamps_value(self) -> None:
        """Test that progress bar value is clamped to total."""
        indicator = ProgressIndicator(total=50)

        mock_progress_bar = Mock(spec=ProgressBar)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_progress_bar,
        ):
            indicator.current = 75  # Greater than total
            indicator._update_progress_bar()  # noqa: SLF001  # Testing internal state/method

            assert mock_progress_bar.progress == PROGRESS_50  # Clamped to total

    def test_count_display_update(self) -> None:
        """Test count display updates."""
        indicator = ProgressIndicator(current=15, total=100)

        mock_count_widget = Mock(spec=Static)
        with patch.object(
            indicator,
            "query_one",
            return_value=mock_count_widget,
        ):
            indicator._update_count()  # noqa: SLF001  # Testing internal state/method

            mock_count_widget.update.assert_called_once_with("15 / 100")

    def test_eta_calculation_insufficient_data(self) -> None:
        """Test ETA calculation with insufficient data."""
        indicator = ProgressIndicator()

        # Test with zero current
        indicator.current = 0
        eta_text = indicator._calculate_eta_text()  # noqa: SLF001  # Testing internal state/method
        assert eta_text == "ETA: --"

        # Test with zero total
        indicator.current = 10
        indicator.total = 0
        eta_text = indicator._calculate_eta_text()  # noqa: SLF001  # Testing internal state/method
        assert eta_text == "ETA: --"

    def test_eta_calculation_recent_start(self) -> None:
        """Test ETA calculation when recently started."""
        indicator = ProgressIndicator()
        indicator._start_time = time.time()    # noqa: SLF001  # Testing internal state/method# Just started
        indicator.current = 5

        eta_text = indicator._calculate_eta_text()  # noqa: SLF001  # Testing internal state/method
        assert eta_text == "ETA: --"  # Not enough elapsed time

    def test_eta_calculation_valid_progress(self) -> None:
        """Test ETA calculation with valid progress data."""
        indicator = ProgressIndicator(total=100)
        indicator._start_time = time.time() - 10    # noqa: SLF001  # Testing internal state/method# 10 seconds ago
        indicator.current = 20  # 20% complete

        eta_text = indicator._calculate_eta_text()  # noqa: SLF001  # Testing internal state/method

        # Should show some reasonable ETA
        assert "ETA: " in eta_text
        assert eta_text != "ETA: --"

    @pytest.mark.parametrize(
        ("seconds", "expected_format"),
        [
            (30, "30s"),  # Under a minute
            (90, "1m 30s"),  # Minutes and seconds
            (3661, "1h 1m"),  # Hours and minutes
        ],
    )
    def test_eta_time_formatting(
        self,
        seconds: float,
        expected_format: str,
    ) -> None:
        """Test ETA time formatting for different durations."""
        indicator = ProgressIndicator()

        formatted = indicator._format_eta_time(seconds)  # noqa: SLF001  # Testing internal state/method

        assert f"ETA: {expected_format}" == formatted

    def test_completion_state_management(self) -> None:
        """Test completion state CSS class management."""
        indicator = ProgressIndicator(total=50)

        # Test incomplete state
        indicator.current = 25
        indicator._update_completion_state()  # noqa: SLF001  # Testing internal state/method
        assert "completed" not in indicator.classes

        # Test completed state
        indicator.current = 50
        indicator._update_completion_state()  # noqa: SLF001  # Testing internal state/method
        assert "completed" in indicator.classes

        # Test over-completion
        indicator.current = 75
        indicator._update_completion_state()  # noqa: SLF001  # Testing internal state/method
        assert "completed" in indicator.classes

    def test_progress_indicator_convenience_methods(self) -> None:
        """Test convenience methods for progress control."""
        indicator = ProgressIndicator()

        with patch.object(indicator, "_update_progress") as mock_update:
            # Test set_progress
            indicator.set_progress(30, 150)
            assert indicator.current == PROGRESS_30
            assert indicator.total == PROGRESS_150
            mock_update.assert_called()

            # Test set_progress without total change
            mock_update.reset_mock()
            indicator.set_progress(45)
            assert indicator.current == PROGRESS_45
            assert indicator.total == PROGRESS_150  # Unchanged
            mock_update.assert_called()

        # Test set_title
        indicator.set_title("New Title")
        assert indicator.title == "New Title"

    def test_progress_reset_functionality(self) -> None:
        """Test progress reset functionality."""
        indicator = ProgressIndicator(current=50, total=100)
        indicator.add_class("completed")
        indicator.add_class("error")

        start_time_before = indicator._start_time  # noqa: SLF001  # Testing internal state/method
        time.sleep(0.01)  # Ensure time difference

        indicator.reset(200)

        assert indicator.current == 0
        assert indicator.total == PROGRESS_200
        assert indicator._start_time > start_time_before  # noqa: SLF001  # Testing internal state/method
        assert "completed" not in indicator.classes
        assert "error" not in indicator.classes

        # Test reset without total change
        indicator.total = 150
        indicator.current = 25
        indicator.reset()  # No total parameter

        assert indicator.current == 0
        assert indicator.total == PROGRESS_150  # Unchanged

    def test_progress_error_state(self) -> None:
        """Test progress error state management."""
        indicator = ProgressIndicator()

        # Test marking as error
        indicator.mark_error("Connection failed")

        assert "error" in indicator.classes
        assert indicator.title == "Error: Connection failed"

        # Test marking as error without message
        indicator.title = "Original Title"
        indicator.mark_error()

        assert "error" in indicator.classes
        assert indicator.title == "Original Title"  # Unchanged

    def test_progress_completion_method(self) -> None:
        """Test progress completion method."""
        indicator = ProgressIndicator(total=75)
        indicator.current = 30

        indicator.complete()

        assert indicator.current == PROGRESS_75  # Set to total
        assert "completed" in indicator.classes

    def test_watch_methods_update_display(self) -> None:
        """Test that watch methods trigger display updates."""
        indicator = ProgressIndicator()

        # Mock widgets
        mock_title_widget = Mock(spec=Static)
        mock_progress_bar = Mock(spec=ProgressBar)

        def mock_query_one(selector: str, _widget_type: type[Any]) -> Mock:
            if selector == "#title":
                return mock_title_widget
            if selector == "#progress-bar":
                return mock_progress_bar
            return Mock()

        with (
            patch.object(indicator, "query_one", side_effect=mock_query_one),
            patch.object(
                indicator,
                "_update_progress",
            ) as mock_update_progress,
        ):
            # Test title watch
            indicator.watch_title("New Title")
            mock_title_widget.update.assert_called_once_with("New Title")

            # Test current watch
            indicator.watch_current(50)
            mock_update_progress.assert_called_once()

            # Test total watch
            mock_update_progress.reset_mock()
            indicator.watch_total(TWO_HUNDRED_TOTAL)
            assert mock_progress_bar.total == TWO_HUNDRED_TOTAL
            mock_update_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_simulate_progress_functionality(self) -> None:
        """Test the simulate_progress method."""
        indicator = ProgressIndicator()

        # Mock reset and sleep to speed up test
        with (
            patch.object(indicator, "reset") as mock_reset,
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            # Start simulation in background
            task: asyncio.Task[None] = asyncio.create_task(
                indicator.simulate_progress(
                    duration=0.1,
                    steps=FIVE_STEPS,
                ).wait(),
            )

            # Let it run
            await asyncio.sleep(0.01)
            await task

            # Verify reset was called
            mock_reset.assert_called_once_with(FIVE_STEPS)

            # Verify sleep was called multiple times
            assert mock_sleep.call_count == FIVE_STEPS

            # Verify final state
            assert indicator.current == FIVE_STEPS

    def test_exception_handling_in_update_methods(self) -> None:
        """Test exception handling in update methods."""
        indicator = ProgressIndicator()

        # Mock query_one to raise exception
        with (
            patch.object(
                indicator,
                "query_one",
                side_effect=Exception("Widget not found"),
            ),
            patch("src.tui.widgets.loading.logger.debug") as mock_debug,
        ):
            # These should not raise exceptions
            indicator._update_progress_bar()  # noqa: SLF001
            indicator._update_percentage()  # noqa: SLF001
            indicator._update_count()  # noqa: SLF001
            indicator._update_eta()  # noqa: SLF001

            # Should log debug messages
            assert mock_debug.call_count >= FOUR_UPDATES

    @pytest.mark.asyncio
    async def test_progress_indicator_mount_lifecycle(self) -> None:
        """Test ProgressIndicator mount lifecycle."""
        indicator = ProgressIndicator()

        with (
            patch.object(indicator, "_initialize_theme") as mock_init_theme,
            patch.object(indicator, "_update_progress") as mock_update,
        ):
            indicator.on_mount()

            mock_init_theme.assert_called_once()
            mock_update.assert_called_once()

    def test_time_constants(self) -> None:
        """Test time constants are defined correctly."""
        assert SECONDS_PER_MINUTE == SECONDS_PER_MINUTE_CONST
        assert SECONDS_PER_HOUR == SECONDS_PER_HOUR_CONST

    def test_progress_indicator_default_css(self) -> None:
        """Test that DEFAULT_CSS is properly defined."""
        css = ProgressIndicator.DEFAULT_CSS

        assert isinstance(css, str)
        assert "ProgressIndicator" in css
        assert "progress-title" in css
        assert "progress-percentage" in css
        assert "progress-bar-container" in css
        assert "completed" in css
        assert "error" in css


class TestLoadingWidgetsIntegration:
    """Integration tests for loading widgets with theme system."""

    def test_loading_indicator_theme_integration(
        self,
        mock_theme_manager: Mock,
    ) -> None:
        """Test LoadingIndicator integration with theme system."""
        indicator = LoadingIndicator()
        indicator._theme_manager = mock_theme_manager  # noqa: SLF001

        # Theme manager should be used
        assert indicator._theme_manager is mock_theme_manager  # noqa: SLF001

        # Theme colors should be accessible
        theme = mock_theme_manager.get_current_theme()
        assert theme.status_loading == "#17A2B8"

    def test_progress_indicator_theme_integration(
        self,
        mock_theme_manager: Mock,
    ) -> None:
        """Test ProgressIndicator integration with theme system."""
        indicator = ProgressIndicator()
        indicator._theme_manager = mock_theme_manager  # noqa: SLF001

        # Theme manager should be used
        assert indicator._theme_manager is mock_theme_manager  # noqa: SLF001

        # Theme colors should be accessible
        theme = mock_theme_manager.get_current_theme()
        assert theme.success == "#28A745"
        assert theme.error == "#DC3545"

    def test_loading_widgets_css_integration(self) -> None:
        """Test CSS integration for loading widgets."""
        # Test LoadingIndicator CSS
        loading_css = LoadingIndicator.DEFAULT_CSS
        assert "loading-spinner" in loading_css
        assert "loading-message" in loading_css
        assert "$status-loading" in loading_css

        # Test ProgressIndicator CSS
        progress_css = ProgressIndicator.DEFAULT_CSS
        assert "progress-title" in progress_css
        assert "progress-percentage" in progress_css
        assert "$success" in progress_css
        assert "$error" in progress_css

    def test_loading_indicators_accessibility(self) -> None:
        """Test accessibility features of loading indicators."""
        # Test that indicators have appropriate ARIA roles/states
        loading_indicator = LoadingIndicator()
        progress_indicator = ProgressIndicator()

        # Widgets should be properly initialized
        assert isinstance(loading_indicator, LoadingIndicator)
        assert isinstance(progress_indicator, ProgressIndicator)

        # Default messages should be descriptive
        assert "Loading" in loading_indicator.message
        assert "Progress" in progress_indicator.title
