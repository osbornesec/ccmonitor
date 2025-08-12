"""Advanced loading indicators and progress widgets for CCMonitor TUI.

This module provides sophisticated loading and progress components with:
- Animated spinners with multiple styles (dots, line, circle, square, arrows)
- Progress indicators with ETA calculations and percentage display
- Professional theming and responsive design
- Efficient timer-based animations with proper cleanup
- CSS animations and smooth transitions
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal

from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import ProgressBar, Static

from src.tui.utils.themes import ThemeManager

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.timer import Timer

logger = logging.getLogger(__name__)

# Constants for time calculations
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600

SpinnerStyle = Literal["dots", "line", "circle", "square", "arrows"]


@dataclass
class SpinnerFrames:
    """Animation frames for different spinner styles."""

    dots: ClassVar[list[str]] = [
        "⠋",
        "⠙",
        "⠹",
        "⠸",
        "⠼",
        "⠴",
        "⠦",
        "⠧",
        "⠇",
        "⠏",
    ]
    line: ClassVar[list[str]] = ["-", "\\", "|", "/"]
    circle: ClassVar[list[str]] = ["◐", "◓", "◑", "◒"]
    square: ClassVar[list[str]] = ["■", "□", "▪", "▫"]
    arrows: ClassVar[list[str]] = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]

    @classmethod
    def get_frames(cls, style: SpinnerStyle) -> list[str]:
        """Get animation frames for the specified style."""
        frames = getattr(cls, style)
        return list(frames)


class LoadingIndicator(Widget):
    """Advanced loading indicator with animated spinner and configurable styling.

    Features:
    - Multiple spinner animation styles (dots, line, circle, square, arrows)
    - Configurable message display with theme integration
    - Smooth timer-based animations with proper cleanup
    - CSS styling with theme system colors
    - Performance optimized updates
    """

    DEFAULT_CSS = """
    LoadingIndicator {
        layout: horizontal;
        height: auto;
        width: auto;
        align: center middle;
        content-align: center middle;
        background: transparent;
    }

    LoadingIndicator .loading-spinner {
        width: 3;
        height: 1;
        content-align: center middle;
        color: $status-loading;
        text-style: bold;
        margin-right: 1;
    }

    LoadingIndicator .loading-message {
        height: 1;
        width: auto;
        color: $text;
        text-style: italic;
        content-align: left middle;
        background: transparent;
    }

    LoadingIndicator.pulse .loading-spinner {
        background: $status-loading 20%;
        border: solid $status-loading 50%;
        border-radius: 1;
    }

    LoadingIndicator.pulse .loading-message {
        color: $status-loading;
    }
    """

    # Reactive attributes for automatic UI updates
    message: reactive[str] = reactive("Loading...")
    spinner_style: reactive[SpinnerStyle] = reactive("dots")
    is_animated: reactive[bool] = reactive(default=True, init=False)

    def __init__(
        self,
        message: str = "Loading...",
        *,
        spinner_style: SpinnerStyle = "dots",
        pulse_effect: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialize loading indicator.

        Args:
            message: Loading message to display
            spinner_style: Animation style (dots, line, circle, square, arrows)
            pulse_effect: Whether to add pulse animation effect
            **kwargs: Additional keyword arguments passed to Widget

        """
        name = kwargs.get("name")
        id_val = kwargs.get("id")
        classes = kwargs.get("classes")
        disabled = kwargs.get("disabled", False)

        super().__init__(
            name=name if isinstance(name, (str, type(None))) else None,
            id=id_val if isinstance(id_val, (str, type(None))) else None,
            classes=(
                classes if isinstance(classes, (str, type(None))) else None
            ),
            disabled=disabled if isinstance(disabled, bool) else False,
        )
        self.message = message
        self.spinner_style = spinner_style
        self._pulse_effect = pulse_effect
        self._animation_timer: Timer | None = None
        self._frame_index = 0
        self._frames: list[str] = []
        self._theme_manager: ThemeManager | None = None

    def compose(self) -> ComposeResult:
        """Create the loading indicator layout."""
        # Apply pulse effect class if enabled
        if self._pulse_effect:
            self.add_class("pulse")

        with Container():
            yield Static("", classes="loading-spinner", id="spinner")
            yield Static(self.message, classes="loading-message", id="message")

    def on_mount(self) -> None:
        """Initialize spinner animation when widget is mounted."""
        self._initialize_theme()
        self._setup_spinner()
        if self.is_animated:
            self._start_animation()

    def on_unmount(self) -> None:
        """Clean up timers when widget is unmounted."""
        self._stop_animation()

    def _initialize_theme(self) -> None:
        """Initialize theme manager for color coordination."""
        try:
            self._theme_manager = ThemeManager()
        except Exception:  # noqa: BLE001
            # Fallback if theme manager is not available
            logger.debug("ThemeManager not available, using default styling")
            self._theme_manager = None

    def _setup_spinner(self) -> None:
        """Set up spinner frames and initial display."""
        self._frames = SpinnerFrames.get_frames(self.spinner_style)
        self._frame_index = 0
        self._update_spinner_display()

    def _start_animation(self) -> None:
        """Start the spinner animation timer."""
        self._stop_animation()  # Ensure no duplicate timers
        if self._frames:
            # Different animation speeds for different styles
            animation_speed = self._get_animation_speed()
            self._animation_timer = self.set_interval(
                animation_speed,
                self._animate_spinner,
                repeat=True,
            )

    def _stop_animation(self) -> None:
        """Stop the spinner animation timer."""
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer = None

    def _get_animation_speed(self) -> float:
        """Get animation speed based on spinner style."""
        speed_map = {
            "dots": 0.1,  # Fast for smooth braille dots
            "line": 0.15,  # Medium for classic line spinner
            "circle": 0.2,  # Slower for circle rotation
            "square": 0.25,  # Slowest for square pattern
            "arrows": 0.12,  # Fast for arrow rotation
        }
        return speed_map.get(self.spinner_style, 0.15)

    def _animate_spinner(self) -> None:
        """Update spinner to next frame."""
        if not self._frames or not self.is_animated:
            return

        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self._update_spinner_display()

    def _update_spinner_display(self) -> None:
        """Update the spinner display with current frame."""
        if not self._frames:
            return

        spinner_widget = self.query_one("#spinner", Static)
        current_frame = self._frames[self._frame_index]
        spinner_widget.update(current_frame)

    def watch_message(self, new_message: str) -> None:
        """Update message display when message changes."""
        try:
            message_widget = self.query_one("#message", Static)
            message_widget.update(new_message)
        except Exception:  # noqa: BLE001
            # Widget may not be mounted yet, ignore silently
            logger.debug(
                "Message widget not yet available during watch update",
            )

    def watch_spinner_style(self, _new_style: SpinnerStyle) -> None:
        """Update spinner style and restart animation."""
        self._setup_spinner()
        if self.is_animated:
            self._start_animation()

    def watch_is_animated(self, *, animated: bool) -> None:
        """Start or stop animation based on animated state."""
        if animated:
            self._start_animation()
        else:
            self._stop_animation()

    def set_message(self, message: str) -> None:
        """Update the loading message."""
        self.message = message

    def set_spinner_style(self, style: SpinnerStyle) -> None:
        """Change the spinner animation style."""
        self.spinner_style = style

    def start(self) -> None:
        """Start the loading animation."""
        self.is_animated = True

    def stop(self) -> None:
        """Stop the loading animation."""
        self.is_animated = False


class ProgressIndicator(Widget):
    """Advanced progress indicator with ETA calculation and professional styling.

    Features:
    - ProgressBar integration with percentage display
    - ETA calculation and display based on progress rate
    - Current/total progress counters
    - Professional styling with theme integration
    - Real-time updates with reactive attributes
    """

    DEFAULT_CSS = """
    ProgressIndicator {
        layout: vertical;
        height: auto;
        width: 100%;
        background: transparent;
        padding: 1;
        border: solid $secondary;
        border-radius: 1;
    }

    ProgressIndicator .progress-header {
        layout: horizontal;
        height: 1;
        width: 100%;
        margin-bottom: 1;
    }

    ProgressIndicator .progress-title {
        width: 1fr;
        color: $text;
        text-style: bold;
        content-align: left middle;
    }

    ProgressIndicator .progress-percentage {
        width: auto;
        color: $accent;
        text-style: bold;
        content-align: right middle;
        margin-left: 2;
    }

    ProgressIndicator .progress-bar-container {
        height: 1;
        width: 100%;
        margin-bottom: 1;
        border: solid $secondary 50%;
        background: $surface;
    }

    ProgressIndicator .progress-details {
        layout: horizontal;
        height: 1;
        width: 100%;
    }

    ProgressIndicator .progress-count {
        width: 1fr;
        color: $text-muted;
        content-align: left middle;
    }

    ProgressIndicator .progress-eta {
        width: auto;
        color: $info;
        content-align: right middle;
        text-style: italic;
    }

    ProgressIndicator.completed {
        border: solid $success;
        background: $success 5%;
    }

    ProgressIndicator.completed .progress-title {
        color: $success;
    }

    ProgressIndicator.completed .progress-percentage {
        color: $success;
    }

    ProgressIndicator.error {
        border: solid $error;
        background: $error 5%;
    }

    ProgressIndicator.error .progress-title {
        color: $error;
    }
    """

    # Reactive attributes for automatic UI updates
    title: reactive[str] = reactive("Progress")
    current: reactive[int] = reactive(0)
    total: reactive[int] = reactive(100)
    show_eta: reactive[bool] = reactive(default=True, init=False)

    def __init__(
        self,
        title: str = "Progress",
        *,
        current: int = 0,
        total: int = 100,
        show_eta: bool = True,
        show_count: bool = True,
        **kwargs: object,
    ) -> None:
        """Initialize progress indicator.

        Args:
            title: Progress indicator title
            current: Current progress value
            total: Total progress value
            show_eta: Whether to show ETA calculation
            show_count: Whether to show current/total count
            **kwargs: Additional keyword arguments passed to Widget

        """
        name = kwargs.get("name")
        id_val = kwargs.get("id")
        classes = kwargs.get("classes")
        disabled = kwargs.get("disabled", False)

        super().__init__(
            name=name if isinstance(name, (str, type(None))) else None,
            id=id_val if isinstance(id_val, (str, type(None))) else None,
            classes=(
                classes if isinstance(classes, (str, type(None))) else None
            ),
            disabled=disabled if isinstance(disabled, bool) else False,
        )
        self.title = title
        self.current = current
        self.total = total
        self.show_eta = show_eta
        self._show_count = show_count
        self._start_time = time.time()
        self._theme_manager: ThemeManager | None = None

    def compose(self) -> ComposeResult:
        """Create the progress indicator layout."""
        with Vertical():
            # Header with title and percentage
            with Horizontal(classes="progress-header"):
                yield Static(self.title, classes="progress-title", id="title")
                yield Static(
                    "0%",
                    classes="progress-percentage",
                    id="percentage",
                )

            # Progress bar
            with Container(classes="progress-bar-container"):
                yield ProgressBar(
                    total=self.total,
                    show_bar=True,
                    show_percentage=False,
                    show_eta=False,
                    id="progress-bar",
                )

            # Details with count and ETA
            with Horizontal(classes="progress-details"):
                if self._show_count:
                    yield Static(
                        f"{self.current} / {self.total}",
                        classes="progress-count",
                        id="count",
                    )
                else:
                    yield Static("", classes="progress-count", id="count")

                if self.show_eta:
                    yield Static("ETA: --", classes="progress-eta", id="eta")
                else:
                    yield Static("", classes="progress-eta", id="eta")

    def on_mount(self) -> None:
        """Initialize progress indicator when mounted."""
        self._initialize_theme()
        self._update_progress()

    def _initialize_theme(self) -> None:
        """Initialize theme manager for color coordination."""
        try:
            self._theme_manager = ThemeManager()
        except Exception:  # noqa: BLE001
            # Fallback if theme manager is not available
            logger.debug("ThemeManager not available, using default styling")
            self._theme_manager = None

    def watch_title(self, new_title: str) -> None:
        """Update title when it changes."""
        try:
            title_widget = self.query_one("#title", Static)
            title_widget.update(new_title)
        except Exception:  # noqa: BLE001
            # Widget may not be mounted yet, ignore silently
            logger.debug("Title widget not yet available during watch update")

    def watch_current(self, _new_current: int) -> None:
        """Update progress when current value changes."""
        self._update_progress()

    def watch_total(self, new_total: int) -> None:
        """Update progress when total value changes."""
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.total = new_total
        self._update_progress()

    def _update_progress(self) -> None:
        """Update all progress displays."""
        self._update_progress_bar()
        self._update_percentage()
        if self._show_count:
            self._update_count()
        if self.show_eta:
            self._update_eta()
        self._update_completion_state()

    def _update_progress_bar(self) -> None:
        """Update the progress bar value."""
        try:
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.progress = min(self.current, self.total)
        except Exception:  # noqa: BLE001
            # Handle case where progress bar is not yet available
            logger.debug("Progress bar not yet available during update")

    def _update_percentage(self) -> None:
        """Update the percentage display."""
        try:
            percentage_widget = self.query_one("#percentage", Static)
            if self.total > 0:
                percentage = min(100, (self.current * 100) // self.total)
            else:
                percentage = 0
            percentage_widget.update(f"{percentage}%")
        except Exception:  # noqa: BLE001
            logger.debug("Percentage widget not yet available during update")

    def _update_count(self) -> None:
        """Update the current/total count display."""
        try:
            count_widget = self.query_one("#count", Static)
            count_widget.update(f"{self.current} / {self.total}")
        except Exception:  # noqa: BLE001
            logger.debug("Count widget not yet available during update")

    def _update_eta(self) -> None:
        """Update the ETA display based on current progress rate."""
        try:
            eta_widget = self.query_one("#eta", Static)
            eta_text = self._calculate_eta_text()
            eta_widget.update(eta_text)
        except Exception:  # noqa: BLE001
            logger.debug("ETA widget not yet available during update")

    def _calculate_eta_text(self) -> str:
        """Calculate ETA text based on current progress."""
        if self.current <= 0 or self.total <= 0:
            return "ETA: --"

        elapsed = time.time() - self._start_time
        if elapsed < 1:  # Not enough data yet
            return "ETA: --"

        rate = self.current / elapsed
        if rate <= 0:
            return "ETA: --"

        remaining = self.total - self.current
        eta_seconds = remaining / rate

        return self._format_eta_time(eta_seconds)

    def _format_eta_time(self, eta_seconds: float) -> str:
        """Format ETA seconds into human readable time."""
        if eta_seconds < SECONDS_PER_MINUTE:
            return f"ETA: {int(eta_seconds)}s"
        if eta_seconds < SECONDS_PER_HOUR:
            minutes = int(eta_seconds // SECONDS_PER_MINUTE)
            seconds = int(eta_seconds % SECONDS_PER_MINUTE)
            return f"ETA: {minutes}m {seconds}s"
        hours = int(eta_seconds // SECONDS_PER_HOUR)
        minutes = int(
            (eta_seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE,
        )
        return f"ETA: {hours}h {minutes}m"

    def _update_completion_state(self) -> None:
        """Update visual state based on completion."""
        if self.current >= self.total and self.total > 0:
            self.add_class("completed")
        else:
            self.remove_class("completed")

    def set_progress(self, current: int, total: int | None = None) -> None:
        """Update progress values.

        Args:
            current: Current progress value
            total: Total progress value (optional, keeps existing if None)

        """
        if total is not None:
            self.total = total
        self.current = current

    def set_title(self, title: str) -> None:
        """Update the progress title."""
        self.title = title

    def reset(self, total: int | None = None) -> None:
        """Reset progress to beginning.

        Args:
            total: New total value (optional, keeps existing if None)

        """
        if total is not None:
            self.total = total
        self.current = 0
        self._start_time = time.time()
        self.remove_class("completed")
        self.remove_class("error")

    def mark_error(self, error_message: str | None = None) -> None:
        """Mark progress as error state.

        Args:
            error_message: Optional error message to display in title

        """
        self.add_class("error")
        if error_message:
            self.title = f"Error: {error_message}"

    def complete(self) -> None:
        """Mark progress as completed."""
        self.current = self.total
        self.add_class("completed")

    @work(exclusive=True, thread=True)
    async def simulate_progress(
        self,
        duration: float = 5.0,
        steps: int = 100,
    ) -> None:
        """Simulate progress for demonstration purposes.

        Args:
            duration: Total duration in seconds
            steps: Number of progress steps

        """
        self.reset(steps)
        step_duration = duration / steps

        for i in range(1, steps + 1):
            await asyncio.sleep(step_duration)
            self.current = i
