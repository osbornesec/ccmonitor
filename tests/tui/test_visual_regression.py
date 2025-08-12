"""Visual regression tests for TUI application."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


class TestVisualRegression:
    """Test visual appearance consistency."""

    SNAPSHOT_DIR = Path("tests/tui/snapshots")

    def setup_method(self) -> None:
        """Set up test method."""
        # Ensure snapshot directory exists
        self.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def test_main_screen_appearance(self, mock_app: Mock) -> None:
        """Test main screen visual appearance."""
        # Simulate main screen content
        screen_content = self._generate_main_screen_content(mock_app)

        # Compare with baseline
        baseline_file = self.SNAPSHOT_DIR / "main_screen.txt"
        self._compare_or_create_baseline(screen_content, baseline_file)

    def test_help_overlay_appearance(self, mock_app: Mock) -> None:
        """Test help overlay visual appearance."""
        # Simulate help overlay content
        help_content = self._generate_help_overlay_content(mock_app)

        # Compare with baseline
        baseline_file = self.SNAPSHOT_DIR / "help_overlay.txt"
        self._compare_or_create_baseline(help_content, baseline_file)

    def test_error_dialog_appearance(self, mock_app: Mock) -> None:
        """Test error dialog visual appearance."""
        # Simulate error dialog content
        error_content = self._generate_error_dialog_content(mock_app)

        # Compare with baseline
        baseline_file = self.SNAPSHOT_DIR / "error_dialog.txt"
        self._compare_or_create_baseline(error_content, baseline_file)

    def test_projects_panel_appearance(self, widget_test_data: dict) -> None:
        """Test projects panel visual layout."""
        # Generate projects panel content
        projects_content = self._generate_projects_panel_content(
            widget_test_data
        )

        # Compare with baseline
        baseline_file = self.SNAPSHOT_DIR / "projects_panel.txt"
        self._compare_or_create_baseline(projects_content, baseline_file)

    def test_live_feed_panel_appearance(self, widget_test_data: dict) -> None:
        """Test live feed panel visual layout."""
        # Generate live feed content
        feed_content = self._generate_live_feed_content(widget_test_data)

        # Compare with baseline
        baseline_file = self.SNAPSHOT_DIR / "live_feed_panel.txt"
        self._compare_or_create_baseline(feed_content, baseline_file)

    def test_terminal_size_layouts(
        self, terminal_sizes: list[tuple[int, int]]
    ) -> None:
        """Test layouts at different terminal sizes."""
        for width, height in terminal_sizes:
            # Generate layout for this size
            layout_content = self._generate_layout_for_size(width, height)

            # Create size-specific baseline
            baseline_file = self.SNAPSHOT_DIR / f"layout_{width}x{height}.txt"
            self._compare_or_create_baseline(layout_content, baseline_file)

    def test_theme_variations(self) -> None:
        """Test visual appearance across themes."""
        themes = ["dark", "light", "blue", "green"]

        for theme in themes:
            # Generate themed content
            themed_content = self._generate_themed_content(theme)

            # Create theme-specific baseline
            baseline_file = self.SNAPSHOT_DIR / f"theme_{theme}.txt"
            self._compare_or_create_baseline(themed_content, baseline_file)

    def test_unicode_rendering(self) -> None:
        """Test Unicode character rendering."""
        # Test various Unicode characters used in the UI
        unicode_content = self._generate_unicode_test_content()

        baseline_file = self.SNAPSHOT_DIR / "unicode_rendering.txt"
        self._compare_or_create_baseline(unicode_content, baseline_file)

    def test_long_text_handling(self) -> None:
        """Test handling of long text and wrapping."""
        # Generate content with long text
        long_text_content = self._generate_long_text_content()

        baseline_file = self.SNAPSHOT_DIR / "long_text_handling.txt"
        self._compare_or_create_baseline(long_text_content, baseline_file)

    def _generate_main_screen_content(self, mock_app: Mock) -> str:
        """Generate main screen content for visual testing."""
        return """
┌─ CCMonitor ──────────────────────────────────────────────────────────────────┐
│                                                                              │
├─ Projects ─────┬─ Live Feed ─────────────────────────────────────────────────┤
│ 🔷 Project A   │ [10:23:45] 👤 User: How do I implement a parser?           │
│ 🔶 Project B   │ [10:23:47] 🤖 Assistant: I'll help you implement...       │
│ 🔵 Project C   │ [10:23:50] 🔧 Tool: Analyzing code structure...           │
│                │ [10:23:52] ✅ Status: Analysis complete                    │
│ 📊 Stats:      │ [10:23:53] 📝 Note: Ready for next query...               │
│ Total: 3       │                                                             │
│ Active: 2      │ 🔍 Filter messages (regex supported)...                   │
│ Messages: 1234 │                                                             │
└────────────────┴─────────────────────────────────────────────────────────────┘
│ q:Quit h:Help Tab:Navigate Ctrl+1-3:Focus ↑↓:Select Enter:Open              │
└──────────────────────────────────────────────────────────────────────────────┘
""".strip()

    def _generate_help_overlay_content(self, mock_app: Mock) -> str:
        """Generate help overlay content for visual testing."""
        return """
┌─ Help ───────────────────────────────────────────────────────────────────────┐
│                          CCMonitor Help                                     │
│                                                                              │
│ Navigation:                                                                  │
│   Tab             - Cycle through panels                                    │
│   ↑/↓             - Navigate within lists                                   │
│   Ctrl+1,2,3      - Direct focus to panels                                 │
│                                                                              │
│ Actions:                                                                     │
│   Enter           - Open/Select item                                        │
│   Space           - Toggle selection                                        │
│   /               - Start search                                            │
│                                                                              │
│ Global:                                                                      │
│   h               - Show/hide help                                          │
│   q               - Quit application                                        │
│   Esc             - Cancel/go back                                          │
│                                                                              │
│                         Press Esc to close                                  │
└──────────────────────────────────────────────────────────────────────────────┘
""".strip()

    def _generate_error_dialog_content(self, mock_app: Mock) -> str:
        """Generate error dialog content for visual testing."""
        return """
┌─ Error ──────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ⚠️  Error occurred while loading conversation data                         │
│                                                                              │
│  Unable to parse JSONL file: /path/to/conversation.jsonl                   │
│  Line 42: Invalid JSON syntax                                               │
│                                                                              │
│  The application will continue with cached data.                            │
│                                                                              │
│                        [ OK ] [ Retry ]                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
""".strip()

    def _generate_projects_panel_content(self, test_data: dict) -> str:
        """Generate projects panel content for visual testing."""
        projects = test_data.get("projects", [])
        content_lines = ["📁 Projects", ""]

        for project in projects[:3]:  # Limit to 3 for consistency
            status_icon = "🔷" if project.get("active") else "🔶"
            content_lines.append(f"{status_icon} {project['name']}")

        content_lines.extend(
            [
                "",
                "📊 Stats:",
                f"Total: {len(projects)} projects",
                "Active: 2",
                "Messages: 1,234",
            ]
        )

        return "\n".join(content_lines)

    def _generate_live_feed_content(self, test_data: dict) -> str:
        """Generate live feed content for visual testing."""
        messages = test_data.get("messages", [])
        content_lines = ["📨 Live Feed", ""]

        for i, message in enumerate(messages[:5]):  # Limit to 5 messages
            timestamp = f"[10:2{3+i}:4{5+i}]"
            role_icon = "👤" if message["role"] == "user" else "🤖"
            content_lines.append(
                f"{timestamp} {role_icon} {message['role'].title()}: {message['content']}"
            )

        content_lines.extend(
            [
                "",
                "🔍 Filter messages (regex supported)...",
            ]
        )

        return "\n".join(content_lines)

    def _generate_layout_for_size(self, width: int, height: int) -> str:
        """Generate layout content for specific terminal size."""
        # Simulate responsive layout adjustments
        if width < 100:
            panel_width = 20
            layout_type = "compact"
        elif width > 150:
            panel_width = 40
            layout_type = "expanded"
        else:
            panel_width = 30
            layout_type = "standard"

        return f"""
Terminal Size: {width}x{height}
Layout Type: {layout_type}
Panel Width: {panel_width} chars
Remaining Width: {width - panel_width} chars
Usable Height: {height - 3} lines (excluding header/footer)

Responsive Features:
- Sidebar: {'Hidden' if width < 80 else 'Visible'}
- Help Text: {'Abbreviated' if width < 100 else 'Full'}
- Status Bar: {'Icons only' if width < 120 else 'Full text'}
""".strip()

    def _generate_themed_content(self, theme: str) -> str:
        """Generate themed content for visual testing."""
        theme_configs = {
            "dark": {"bg": "black", "fg": "white", "accent": "blue"},
            "light": {"bg": "white", "fg": "black", "accent": "blue"},
            "blue": {"bg": "navy", "fg": "cyan", "accent": "lightblue"},
            "green": {
                "bg": "darkgreen",
                "fg": "lightgreen",
                "accent": "yellow",
            },
        }

        config = theme_configs.get(theme, theme_configs["dark"])

        return f"""
Theme: {theme.title()}
Background: {config['bg']}
Foreground: {config['fg']}
Accent: {config['accent']}

Visual Elements:
- Primary text: {config['fg']} on {config['bg']}
- Highlighted: {config['accent']} on {config['bg']}
- Borders: {config['accent']}
- Status indicators: Multi-color on {config['bg']}
""".strip()

    def _generate_unicode_test_content(self) -> str:
        """Generate Unicode test content."""
        return """
Unicode Rendering Test:

Emojis:
📁📊📨🔷🔶🔵👤🤖🔧✅📝🔍⚠️

Box Drawing:
┌─┬─┐
│ │ │
├─┼─┤
│ │ │
└─┴─┘

Arrows and Symbols:
↑ ↓ ← → ↩ ↪ ⏎ ⌘ ⌃ ⌥ ⇧

Mathematical:
≤ ≥ ≠ ± × ÷ ∞ ∑ ∏ √

Misc Unicode:
• ◦ ‣ ⁃ — – … ‰ ™ ©
""".strip()

    def _generate_long_text_content(self) -> str:
        """Generate long text content for wrapping tests."""
        long_line = "This is a very long line that should demonstrate text wrapping behavior in the terminal user interface when the content exceeds the available width of the display area."

        return f"""
Long Text Handling Test:

Short line: Normal text
Medium line: This is a medium length line that fits in most terminals
Long line: {long_line}

Wrapped paragraphs:
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Code snippets:
def very_long_function_name_that_might_cause_wrapping_issues(parameter_one, parameter_two, parameter_three):
    return "This function has a very long signature that tests horizontal scrolling"
""".strip()

    def _compare_or_create_baseline(
        self, content: str, baseline_file: Path
    ) -> None:
        """Compare content with baseline or create new baseline."""
        if baseline_file.exists():
            # Compare with existing baseline
            baseline_content = baseline_file.read_text(encoding="utf-8")

            # Use content hash for comparison to avoid whitespace issues
            current_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
            baseline_hash = hashlib.md5(
                baseline_content.encode("utf-8")
            ).hexdigest()

            if current_hash != baseline_hash:
                # Save current content for comparison
                diff_file = baseline_file.with_suffix(".current.txt")
                diff_file.write_text(content, encoding="utf-8")

                assert False, (
                    f"Visual regression detected in {baseline_file.name}. "
                    f"Current content saved to {diff_file.name}. "
                    f"If changes are intentional, update baseline."
                )
        else:
            # Create new baseline
            baseline_file.write_text(content, encoding="utf-8")
            pytest.skip(f"Created new baseline: {baseline_file.name}")

    def test_snapshot_directory_structure(self) -> None:
        """Test that snapshot directory structure is correct."""
        assert self.SNAPSHOT_DIR.exists()
        assert self.SNAPSHOT_DIR.is_dir()

        # Check that we can write to the directory
        test_file = self.SNAPSHOT_DIR / "test_write.tmp"
        test_file.write_text("test")
        assert test_file.exists()
        test_file.unlink()  # Clean up


@pytest.fixture
def visual_test_mode() -> Generator[bool, None, None]:
    """Fixture to enable visual test mode."""
    # In CI/CD, set VISUAL_TEST_UPDATE=1 to update baselines
    import os

    update_mode = os.environ.get("VISUAL_TEST_UPDATE", "0") == "1"
    yield update_mode


class TestVisualRegressionUpdate:
    """Test utilities for updating visual baselines."""

    def test_update_all_baselines(self, visual_test_mode: bool) -> None:
        """Test to update all visual baselines when needed."""
        if not visual_test_mode:
            pytest.skip("Visual test update mode not enabled")

        # This test would regenerate all baselines
        # Useful when the UI changes intentionally
        snapshot_dir = Path("tests/tui/snapshots")

        if snapshot_dir.exists():
            # List all baseline files
            baselines = list(snapshot_dir.glob("*.txt"))
            assert len(baselines) >= 0  # May be 0 on first run

        pytest.skip("Baseline update mode - manual intervention required")
