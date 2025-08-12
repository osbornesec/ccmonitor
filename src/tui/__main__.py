"""Run the CCMonitor TUI application."""

from src.tui.app import CCMonitorApp


def main() -> None:
    """Run the TUI application."""
    app = CCMonitorApp()
    app.run()


if __name__ == "__main__":
    main()
