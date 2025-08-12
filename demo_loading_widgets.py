#!/usr/bin/env python3
"""Demonstration of the CCMonitor loading widgets."""

from __future__ import annotations

import asyncio

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static

from src.tui.widgets.loading import LoadingIndicator, ProgressIndicator


class LoadingDemoApp(App[None]):
    """Demo app showing loading indicators and progress widgets."""

    CSS_PATH = "src/tui/styles/ccmonitor.tcss"

    def compose(self) -> ComposeResult:
        """Create the demo layout."""
        with Vertical():
            yield Static("CCMonitor Loading Widgets Demo", id="title")

            with Horizontal():
                # Different spinner styles
                yield LoadingIndicator("Dots Loading...", spinner_style="dots")
                yield LoadingIndicator("Line Loading...", spinner_style="line")
                yield LoadingIndicator(
                    "Circle Loading...", spinner_style="circle"
                )

            with Horizontal():
                yield LoadingIndicator(
                    "Square Loading...", spinner_style="square"
                )
                yield LoadingIndicator(
                    "Arrow Loading...", spinner_style="arrows"
                )
                yield LoadingIndicator("Pulse Effect...", pulse_effect=True)

            # Progress indicators
            yield ProgressIndicator("File Processing", id="progress1")
            yield ProgressIndicator(
                "Data Transfer", show_eta=True, show_count=True, id="progress2"
            )

    def on_mount(self) -> None:
        """Start demo progress when app mounts."""
        self.simulate_progress()

    @work(exclusive=True)
    async def simulate_progress(self) -> None:
        """Simulate progress for demo purposes."""
        progress1 = self.query_one("#progress1", ProgressIndicator)
        progress2 = self.query_one("#progress2", ProgressIndicator)

        # Simulate different progress rates
        for i in range(101):
            await asyncio.sleep(0.1)
            progress1.current = i
            if i % 2 == 0:  # Update progress2 at half speed
                progress2.current = i // 2

        # Mark first as completed, second as error for demo
        progress1.complete()
        progress2.mark_error("Network timeout")


if __name__ == "__main__":
    app = LoadingDemoApp()
    app.run()
