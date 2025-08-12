"""Fallback mode for limited terminal environments."""

from typing import TYPE_CHECKING, Any

from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import App


class FallbackMode:
    """Simplified UI for limited terminals."""

    def __init__(self, app: "App") -> None:
        """Initialize fallback mode with app reference."""
        self.app = app
        self.original_css = getattr(app, "CSS", "")

    def activate(self) -> None:
        """Switch to fallback mode."""
        # Apply fallback CSS styles
        fallback_css = """
        Screen {
            background: black;
            color: white;
        }

        Container {
            border: solid white;
            padding: 1;
        }

        Button {
            background: white;
            color: black;
        }

        Button:focus {
            background: black;
            color: white;
            border: solid white;
        }
        """

        # Apply CSS using app's stylesheet methods
        if hasattr(self.app, "stylesheet") and hasattr(
            self.app.stylesheet,
            "add_source",
        ):
            self.app.stylesheet.add_source(fallback_css)
        else:
            # Store fallback CSS for manual application
            self._fallback_css = fallback_css

        # Replace complex widgets with simple ones
        self.simplify_ui()

        # Disable animations
        if hasattr(self.app, "animation_level"):
            self.app.animation_level = "none"

        # Use ASCII characters only
        self.use_ascii_only()

    def simplify_ui(self) -> None:
        """Replace complex UI elements with simple ones."""
        # Remove fancy borders
        for widget in self.app.query("*"):
            if hasattr(widget, "border"):
                widget.border = "solid"

        # Replace icons with ASCII
        self.replace_icons()

        # Reduce color usage
        self.reduce_colors()

    def replace_icons(self) -> None:
        """Replace Unicode icons with ASCII alternatives."""
        replacements = {
            "🖥️": "[M]",
            "📁": "[F]",
            "📨": "[MSG]",
            "👤": "[U]",
            "🤖": "[A]",
            "⚙️": "[S]",
            "🔧": "[T]",
            "✓": "[OK]",
            "✗": "[X]",
            "⌘": "Cmd",
            "⏰": "Time:",
        }

        for widget in self.app.query(Static):
            content = widget.renderable
            if isinstance(content, str):
                for unicode_char, ascii_char in replacements.items():
                    content = content.replace(unicode_char, ascii_char)
                widget.update(content)

    def reduce_colors(self) -> None:
        """Reduce to basic color scheme."""
        # Map complex colors to basic ones (black/white only)
        for widget in self.app.query("*"):
            widget.styles.color = "white"
            widget.styles.background = "black"

    def use_ascii_only(self) -> None:
        """Ensure only ASCII characters are used."""
        # Set ASCII-only rendering mode
        if hasattr(self.app, "ascii_mode"):
            self.app.ascii_mode = True

    def restore_original(self) -> None:
        """Restore original CSS and settings."""
        # Restore original CSS if possible
        if (
            hasattr(self.app, "stylesheet")
            and hasattr(self.app.stylesheet, "add_source")
            and self.original_css
        ):
            self.app.stylesheet.add_source(self.original_css)

        if hasattr(self.app, "animation_level"):
            self.app.animation_level = "basic"
        if hasattr(self.app, "ascii_mode"):
            self.app.ascii_mode = False

    def get_status(self) -> dict[str, Any]:
        """Get fallback mode status information."""
        current_css = getattr(self.app, "CSS", "")
        return {
            "active": self.original_css != current_css,
            "original_css_length": len(self.original_css),
            "current_css_length": len(current_css),
            "ascii_mode": getattr(self.app, "ascii_mode", False),
            "animation_level": getattr(self.app, "animation_level", "unknown"),
        }
