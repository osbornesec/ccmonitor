"""Main CCMonitor TUI application using Textual framework."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import var
from textual.widgets import Footer, Header, Static

from .config import get_config
from .exceptions import ConfigurationError, StartupError, TUIError
from .screens.help_screen import HelpOverlay
from .screens.main_screen import MainScreen
from .utils.error_handler import ErrorHandler
from .utils.fallback import FallbackMode
from .utils.focus import focus_manager
from .utils.startup import StartupValidator
from .utils.state import AppState


class CCMonitorApp(App[None]):
    """Main TUI application for CCMonitor."""

    # Application metadata
    TITLE = "CCMonitor - Multi-Project Monitoring"
    SUB_TITLE = "Real-time Claude conversation tracker"
    VERSION = "0.1.0"

    # CSS configuration - using test CSS until main CSS is fixed
    CSS_PATH = "styles/test.tcss"
    ENABLE_COMMAND_PALETTE = True

    # Global key bindings
    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
        Binding("h", "toggle_help", "Help"),
        Binding("p", "toggle_pause", "Pause/Resume"),
        Binding("f", "show_filter", "Filter"),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("d", "toggle_dark", "Dark Mode", show=False),
        Binding("escape", "pop_screen", "Go back", show=False),
    ]

    # Screen registry
    # Screen registry defined as strings for lazy loading
    # Textual supports string imports at runtime
    SCREENS: ClassVar[dict[str, str]] = {  # type: ignore[assignment]
        "main": "src.tui.screens.main_screen:MainScreen",
        "help": "src.tui.screens.help_screen:HelpOverlay",
        "error": "src.tui.screens.error_screen:ErrorScreen",
    }

    # Application reactive state
    is_paused = var(default=False)
    dark_mode = var(default=True)
    active_project = var(default=None)

    def __init__(self, *, test_mode: bool = False) -> None:
        """Initialize the application with configuration."""
        super().__init__()
        self.config = get_config()
        self.app_state = AppState()
        self.projects: list[str] = []
        self._help_visible = False
        self._monitoring_task: asyncio.Task[None] | None = None
        self._monitoring_event = asyncio.Event()
        self.test_mode = test_mode

        # Initialize error handling system
        self.error_handler = ErrorHandler(self)
        self.fallback_mode = FallbackMode(self)
        self.startup_validator = StartupValidator()

        self.setup_logging()

    def setup_logging(self) -> None:
        """Configure application logging."""
        log_path = Path.home() / ".config" / "ccmonitor" / "app.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            filename=log_path,
            level=getattr(logging, self.config.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("ccmonitor.tui")
        self.logger.info("CCMonitor TUI v%s initializing", self.VERSION)

    async def on_mount(self) -> None:
        """Mount app and initialize all components."""
        try:
            await self._perform_startup_sequence()
        except (StartupError, ConfigurationError) as e:
            # Use comprehensive error handling
            self.error_handler.handle_error(e)
        except (OSError, ImportError, RuntimeError) as e:
            # Handle specific expected errors during startup
            wrapped_error = TUIError(f"Unexpected startup error: {e!s}")
            self.error_handler.handle_error(wrapped_error)

    async def _perform_startup_sequence(self) -> None:
        """Perform the startup sequence steps."""
        # Comprehensive startup validation
        valid, message = self.startup_validator.validate()
        if not valid:
            raise StartupError(message or "Startup validation failed")

        # Report warnings but continue
        report = self.startup_validator.get_validation_report()
        if report["has_warnings"]:
            self.logger.warning("Startup warnings: %s", report["warnings"])

        # Startup sequence
        await self.load_configuration()
        await self.load_state()
        await self.initialize_screens()

        # Initialize focus manager with app reference
        focus_manager.set_app(self)

        # Switch to main screen
        self.push_screen(MainScreen())

        # Start monitoring if not paused
        if not self.is_paused:
            await self.start_monitoring()

        self.logger.info("Application mounted successfully")

    def compose(self) -> ComposeResult:
        """Create the application layout with enhanced styling."""
        yield Header(classes="fade-in")
        yield Container(
            Static("🖥️  Welcome to CCMonitor", id="welcome", classes="fade-in"),
            Static(
                "⏳ Loading application...",
                id="status",
                classes="loading",
            ),
            id="main_container",
            classes="fade-in",
        )
        yield Footer(classes="fade-in")

    async def load_configuration(self) -> None:
        """Load application configuration."""
        # Configuration is already loaded in __init__
        self.logger.debug("Configuration loaded")

    def enter_fallback_mode(self) -> None:
        """Enter fallback mode for limited terminals."""
        self.logger.warning(
            "Entering fallback mode due to terminal limitations",
        )
        self.fallback_mode.activate()

    def load_default_config(self) -> None:
        """Load default configuration after config error."""
        self.logger.info("Loading default configuration")
        self.config = get_config()  # This will load defaults

    def reduce_visual_complexity(self) -> None:
        """Reduce visual complexity after multiple rendering errors."""
        self.logger.warning(
            "Reducing visual complexity due to rendering issues",
        )
        # Disable animations and complex styling
        if hasattr(self, "animation_level"):
            self.animation_level = "none"

    async def load_state(self) -> dict[str, object] | None:
        """Load saved application state."""
        try:
            state = await self.app_state.load()
            if state is not None:
                self.dark_mode = state.get("dark_mode", True)
                self.is_paused = state.get("is_paused", False)
                self.active_project = state.get("active_project")
                self.dark = self.dark_mode
                self.logger.debug("Application state loaded")
                return state
        except OSError as e:
            self.logger.warning("Failed to load state: %s", e)
        return None

    async def save_state(self) -> None:
        """Save current application state."""
        try:
            self.app_state.state.update(
                {
                    "dark_mode": self.dark_mode,
                    "is_paused": self.is_paused,
                    "active_project": self.active_project,
                },
            )
            await self.app_state.save()
            self.logger.debug("Application state saved")
        except OSError as e:
            self.logger.warning("Failed to save state: %s", e)

    async def initialize_screens(self) -> None:
        """Initialize application screens."""
        # Screens are registered in SCREENS class variable
        self.logger.debug("Screens initialized")

    async def start_monitoring(self) -> None:
        """Start the monitoring task."""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_event.clear()
            self._monitoring_task = asyncio.create_task(self._monitor_loop())
            self.logger.info("Monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_event.set()
            self._monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitoring_task
            self.logger.info("Monitoring stopped")

    async def _monitor_loop(self) -> None:
        """Execute main monitoring loop."""
        try:
            while not self.is_paused and not self._monitoring_event.is_set():
                await self._monitoring_event.wait()
                # Monitoring logic will be implemented in future PRPs
        except asyncio.CancelledError:
            self.logger.debug("Monitor loop cancelled")

    async def cleanup(self) -> None:
        """Cleanup application resources."""
        await self.stop_monitoring()
        self.logger.debug("Application cleanup completed")

    # Action handlers
    async def action_quit(self) -> None:
        """Execute graceful shutdown sequence."""
        try:
            await self.stop_monitoring()
            await self.save_state()
            await self.cleanup()
            self.exit()
        except OSError as e:
            self.logger.exception("Shutdown error")
            self.exit(message=f"Shutdown error: {e}")

    def action_toggle_help(self) -> None:
        """Toggle help overlay visibility."""
        if self._help_visible:
            self.pop_screen()
            self._help_visible = False
        else:
            # Use the enhanced HelpOverlay
            help_screen = HelpOverlay()
            self.push_screen(help_screen)
            self._help_visible = True

    async def action_toggle_pause(self) -> None:
        """Toggle pause/resume monitoring."""
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"

        if self.is_paused:
            await self.stop_monitoring()
        else:
            await self.start_monitoring()

        self.notify(f"Monitoring {status}")
        self.logger.info("Monitoring %s", status)

    def action_show_filter(self) -> None:
        """Show filter dialog."""
        self.notify("Filter dialog - coming soon!")

    def action_refresh(self) -> None:
        """Refresh the current view."""
        self.notify("Refreshing...")
        # Refresh logic will be implemented in future PRPs

    def action_toggle_dark(self) -> None:
        """Toggle between dark and light themes."""
        self.dark_mode = not self.dark_mode
        self.dark = self.dark_mode
        theme = "dark" if self.dark_mode else "light"
        self.notify(f"Switched to {theme} theme")
        self.logger.debug("Theme changed to %s", theme)

    @property
    def dark(self) -> bool:
        """Compatibility property for dark mode state."""
        return bool(self.dark_mode)

    @dark.setter
    def dark(self, value: bool) -> None:
        """Compatibility setter for dark mode state."""
        self.dark_mode = value

    # Reactive state watchers
    def watch_is_paused(self, paused: bool) -> None:  # noqa: FBT001
        """React to pause state changes."""
        # Update subtitle to reflect pause state
        status = "PAUSED" if paused else "ACTIVE"
        self.sub_title = f"Real-time Claude conversation tracker - {status}"

    def watch_active_project(self, project: str | None) -> None:
        """React to active project changes."""
        if project:
            self.notify(f"Switched to project: {project}")

    def on_exception(self, exception: Exception) -> None:
        """Handle unhandled exceptions gracefully."""
        self.logger.critical("Unhandled exception: %s", exception)

        if isinstance(exception, (StartupError, ConfigurationError)):
            self.push_screen("error")
        else:
            self.notify(f"Error: {exception}", severity="error")
