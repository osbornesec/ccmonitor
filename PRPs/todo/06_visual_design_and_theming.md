# PRP: Visual Design and Theming System

## Goal
Implement a comprehensive visual design system with consistent color schemes, professional styling, message type differentiation, and smooth UI transitions.

## Why
Professional visual design is crucial for user experience and productivity. A well-designed interface reduces cognitive load, improves information hierarchy, and makes the application pleasant to use for extended periods.

## What
### Requirements
- Implement consistent color scheme across all components
- Add message type colors (user, assistant, system, tool)
- Create professional border styles with rounded corners
- Implement loading states and progress indicators
- Add smooth transitions between UI states
- Create theme system for customization
- Ensure accessibility with proper contrast ratios

### Success Criteria
- [ ] Consistent color scheme applied throughout
- [ ] Message types visually distinct
- [ ] Professional appearance competitive with modern TUI tools
- [ ] Loading states clearly indicate activity
- [ ] Transitions smooth without flicker
- [ ] Theme system allows customization
- [ ] Colors meet WCAG contrast requirements

## All Needed Context

### Technical Specifications

#### Theme System Architecture
```python
# src/tui/utils/themes.py
from dataclasses import dataclass
from typing import Dict, Optional
import json
from pathlib import Path

@dataclass
class ColorScheme:
    """Defines a color scheme for the application."""
    # Base colors
    primary: str = "#0066CC"
    secondary: str = "#6C757D"
    success: str = "#28A745"
    warning: str = "#FFC107"
    danger: str = "#DC3545"
    info: str = "#17A2B8"
    
    # UI colors
    background: str = "#1E1E1E"
    surface: str = "#2D2D30"
    border: str = "#3E3E42"
    text: str = "#CCCCCC"
    text_muted: str = "#858585"
    
    # Message type colors
    user_message: str = "#0066CC"
    assistant_message: str = "#28A745"
    system_message: str = "#FFC107"
    tool_message: str = "#FF6B35"
    error_message: str = "#DC3545"
    
    # Syntax highlighting
    syntax_keyword: str = "#569CD6"
    syntax_string: str = "#CE9178"
    syntax_number: str = "#B5CEA8"
    syntax_comment: str = "#6A9955"
    syntax_function: str = "#DCDCAA"

class ThemeManager:
    """Manages application themes and color schemes."""
    
    THEMES = {
        'dark': ColorScheme(),  # Default dark theme
        'light': ColorScheme(
            background="#FFFFFF",
            surface="#F5F5F5",
            border="#E0E0E0",
            text="#212121",
            text_muted="#757575",
            primary="#1976D2",
            user_message="#1976D2",
            assistant_message="#388E3C",
        ),
        'monokai': ColorScheme(
            background="#272822",
            surface="#3E3D32",
            text="#F8F8F2",
            primary="#66D9EF",
            user_message="#66D9EF",
            assistant_message="#A6E22E",
            system_message="#E6DB74",
            tool_message="#FD971F",
        ),
        'solarized': ColorScheme(
            background="#002B36",
            surface="#073642",
            text="#839496",
            primary="#268BD2",
            user_message="#268BD2",
            assistant_message="#859900",
            system_message="#B58900",
            tool_message="#CB4B16",
        ),
    }
    
    def __init__(self):
        self.current_theme = 'dark'
        self.custom_themes = self.load_custom_themes()
    
    def load_custom_themes(self) -> Dict[str, ColorScheme]:
        """Load user-defined custom themes."""
        themes_file = Path.home() / ".config" / "ccmonitor" / "themes.json"
        if themes_file.exists():
            with open(themes_file) as f:
                data = json.load(f)
                return {
                    name: ColorScheme(**colors)
                    for name, colors in data.items()
                }
        return {}
    
    def get_theme(self, name: str) -> ColorScheme:
        """Get theme by name."""
        if name in self.custom_themes:
            return self.custom_themes[name]
        return self.THEMES.get(name, self.THEMES['dark'])
    
    def generate_css(self, theme_name: str) -> str:
        """Generate CSS for a theme."""
        theme = self.get_theme(theme_name)
        return f"""
        /* Auto-generated theme CSS */
        :root {{
            --primary: {theme.primary};
            --secondary: {theme.secondary};
            --success: {theme.success};
            --warning: {theme.warning};
            --danger: {theme.danger};
            --info: {theme.info};
            --background: {theme.background};
            --surface: {theme.surface};
            --border: {theme.border};
            --text: {theme.text};
            --text-muted: {theme.text_muted};
        }}
        
        Screen {{
            background: {theme.background};
            color: {theme.text};
        }}
        
        .message-user {{ color: {theme.user_message}; }}
        .message-assistant {{ color: {theme.assistant_message}; }}
        .message-system {{ color: {theme.system_message}; }}
        .message-tool {{ color: {theme.tool_message}; }}
        .message-error {{ color: {theme.error_message}; }}
        """
```

#### Message Rendering with Syntax Highlighting
```python
# src/tui/widgets/message_display.py
from textual.widgets import Static
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
import re

class MessageDisplay(Static):
    """Display messages with proper formatting and colors."""
    
    DEFAULT_CSS = """
    MessageDisplay {
        padding: 1;
        margin-bottom: 1;
    }
    
    .message-container {
        border: rounded $border;
        padding: 1;
    }
    
    .message-user {
        border-color: $user-message;
        background: $user-message 10%;
    }
    
    .message-assistant {
        border-color: $assistant-message;
        background: $assistant-message 10%;
    }
    
    .message-system {
        border-color: $system-message;
        background: $system-message 10%;
    }
    
    .message-tool {
        border-color: $tool-message;
        background: $tool-message 10%;
    }
    """
    
    def __init__(self, message_type: str, content: str, timestamp: str):
        super().__init__()
        self.message_type = message_type
        self.content = content
        self.timestamp = timestamp
        self.add_class(f"message-{message_type}")
    
    def render_message(self) -> Panel:
        """Render message with appropriate formatting."""
        # Create header with icon and timestamp
        icons = {
            'user': '👤',
            'assistant': '🤖',
            'system': '⚙️',
            'tool': '🔧',
            'error': '❌',
        }
        
        icon = icons.get(self.message_type, '📝')
        header = f"{icon} {self.message_type.title()} • {self.timestamp}"
        
        # Process content for code blocks
        formatted_content = self.format_content(self.content)
        
        # Create panel with border style
        border_colors = {
            'user': 'blue',
            'assistant': 'green',
            'system': 'yellow',
            'tool': 'orange',
            'error': 'red',
        }
        
        return Panel(
            formatted_content,
            title=header,
            border_style=border_colors.get(self.message_type, 'white'),
            padding=(0, 1),
        )
    
    def format_content(self, content: str):
        """Format content with syntax highlighting."""
        # Detect code blocks
        code_pattern = r'```(\w+)?\n(.*?)```'
        
        def replace_code(match):
            lang = match.group(1) or 'python'
            code = match.group(2)
            return Syntax(code, lang, theme='monokai')
        
        # Replace code blocks with syntax-highlighted versions
        formatted = re.sub(code_pattern, replace_code, content, flags=re.DOTALL)
        
        return formatted
```

#### Loading States and Progress Indicators
```python
# src/tui/widgets/loading.py
from textual.widgets import Static, ProgressBar
from textual.timer import Timer
from textual.app import ComposeResult
import itertools

class LoadingIndicator(Static):
    """Animated loading indicator."""
    
    DEFAULT_CSS = """
    LoadingIndicator {
        height: 3;
        align: center middle;
        background: $surface;
        border: rounded $primary;
        padding: 1;
    }
    
    .loading-spinner {
        text-align: center;
        color: $primary;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading-pulse {
        animation: pulse 1.5s infinite;
    }
    """
    
    SPINNERS = {
        'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
        'line': ['-', '\\', '|', '/'],
        'circle': ['◐', '◓', '◑', '◒'],
        'square': ['◰', '◳', '◲', '◱'],
        'arrows': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    }
    
    def __init__(self, message: str = "Loading...", spinner: str = "dots"):
        super().__init__()
        self.message = message
        self.spinner_frames = self.SPINNERS.get(spinner, self.SPINNERS['dots'])
        self.spinner_cycle = itertools.cycle(self.spinner_frames)
        self.timer: Optional[Timer] = None
    
    def on_mount(self) -> None:
        """Start animation on mount."""
        self.timer = self.set_interval(0.1, self.update_spinner)
        self.add_class("loading-pulse")
    
    def update_spinner(self) -> None:
        """Update spinner animation."""
        frame = next(self.spinner_cycle)
        self.update(f"{frame} {self.message}")
    
    def on_unmount(self) -> None:
        """Stop animation on unmount."""
        if self.timer:
            self.timer.stop()

class ProgressIndicator(Static):
    """Progress bar with percentage and ETA."""
    
    DEFAULT_CSS = """
    ProgressIndicator {
        height: 4;
        padding: 1;
        background: $surface;
        border: rounded $primary;
    }
    
    .progress-label {
        text-align: center;
        margin-bottom: 1;
    }
    
    .progress-bar {
        bar-color: $success;
        bar-background: $border;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose progress indicator."""
        yield Static("", classes="progress-label", id="progress-label")
        yield ProgressBar(id="progress-bar", classes="progress-bar")
    
    def update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update progress display."""
        percentage = (current / total) * 100 if total > 0 else 0
        
        # Update label
        label = self.query_one("#progress-label", Static)
        label_text = f"{message} - {percentage:.1f}% ({current}/{total})"
        label.update(label_text)
        
        # Update progress bar
        bar = self.query_one("#progress-bar", ProgressBar)
        bar.update(progress=current, total=total)
```

#### Smooth Transitions
```python
# src/tui/utils/transitions.py
from textual.widgets import Widget
from textual.animate import Animation
from textual.css.scalar import Scalar

class TransitionManager:
    """Manages smooth UI transitions."""
    
    @staticmethod
    async def fade_in(widget: Widget, duration: float = 0.3) -> None:
        """Fade in a widget."""
        widget.styles.opacity = 0
        widget.visible = True
        await widget.animate("opacity", 1.0, duration=duration)
    
    @staticmethod
    async def fade_out(widget: Widget, duration: float = 0.3) -> None:
        """Fade out a widget."""
        await widget.animate("opacity", 0.0, duration=duration)
        widget.visible = False
    
    @staticmethod
    async def slide_in(widget: Widget, direction: str = "left", duration: float = 0.3) -> None:
        """Slide in a widget from specified direction."""
        offsets = {
            'left': ('-100%', '0'),
            'right': ('100%', '0'),
            'top': ('0', '-100%'),
            'bottom': ('0', '100%'),
        }
        
        start_x, start_y = offsets.get(direction, ('-100%', '0'))
        widget.styles.offset = (start_x, start_y)
        widget.visible = True
        await widget.animate("offset", (0, 0), duration=duration)
    
    @staticmethod
    async def highlight(widget: Widget, color: str = "#FFC107", duration: float = 0.5) -> None:
        """Briefly highlight a widget."""
        original_border = widget.styles.border
        widget.styles.border = f"thick {color}"
        await widget.animate("border", original_border, duration=duration)
```

### Enhanced CSS with Visual Polish
```css
/* src/tui/styles/ccmonitor.css (enhanced) */

/* Border styles */
* {
    border-title-align: center;
    border-subtitle-align: center;
}

/* Rounded corners for panels */
.panel {
    border: rounded $primary;
}

/* Shadow effects */
.elevated {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.elevated-high {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* Smooth transitions */
* {
    transition: background 0.2s, border 0.2s, color 0.2s;
}

/* Hover effects */
Button:hover {
    background: $primary 80%;
    text-style: bold;
}

ListItem:hover {
    background: $surface;
}

/* Active states */
Button:active {
    background: $primary;
    offset: 0 1;
}

/* Disabled states */
*:disabled {
    opacity: 0.5;
    text-style: dim;
}

/* Focus glow effect */
*:focus {
    box-shadow: 0 0 0 2px $warning 50%;
}

/* Message animations */
@keyframes message-appear {
    from {
        opacity: 0;
        offset-y: -10;
    }
    to {
        opacity: 1;
        offset-y: 0;
    }
}

.new-message {
    animation: message-appear 0.3s ease-out;
}

/* Loading animations */
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.spinning {
    animation: spin 1s linear infinite;
}

/* Status indicators */
.status-online {
    color: $success;
}

.status-offline {
    color: $danger;
}

.status-warning {
    color: $warning;
}

/* Gradient backgrounds */
.gradient-primary {
    background: linear-gradient(135deg, $primary, $primary 50%);
}

.gradient-surface {
    background: linear-gradient(180deg, $surface, $background);
}
```

### Gotchas and Considerations
- **Color Contrast**: Ensure sufficient contrast for readability
- **Animation Performance**: Too many animations can cause lag
- **Terminal Color Support**: Not all terminals support 24-bit color
- **Theme Switching**: CSS must be reloaded when theme changes
- **Accessibility**: Consider colorblind users in color choices
- **Unicode Support**: Fancy characters may not render in all terminals

## Implementation Blueprint

### Phase 1: Theme System (1 hour)
1. Create ThemeManager class
2. Define color schemes
3. Implement CSS generation
4. Add theme switching logic
5. Test theme application

### Phase 2: Message Styling (45 min)
1. Create MessageDisplay widget
2. Implement message type colors
3. Add syntax highlighting
4. Style message containers
5. Test different message types

### Phase 3: Loading States (45 min)
1. Create LoadingIndicator widget
2. Implement spinner animations
3. Create ProgressIndicator widget
4. Add progress calculations
5. Test various loading scenarios

### Phase 4: Transitions (30 min)
1. Create TransitionManager
2. Implement fade effects
3. Add slide animations
4. Create highlight effects
5. Test transition smoothness

### Phase 5: Visual Polish (30 min)
1. Apply enhanced CSS
2. Add hover effects
3. Implement focus indicators
4. Test visual consistency
5. Optimize performance

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_theming.py
import pytest
from src.tui.utils.themes import ThemeManager, ColorScheme

def test_theme_loading():
    """Test theme system loads correctly."""
    manager = ThemeManager()
    dark_theme = manager.get_theme('dark')
    assert dark_theme.background == "#1E1E1E"
    
def test_css_generation():
    """Test CSS generation from theme."""
    manager = ThemeManager()
    css = manager.generate_css('dark')
    assert "--primary: #0066CC" in css
    
def test_message_colors():
    """Test message type differentiation."""
    from src.tui.widgets.message_display import MessageDisplay
    msg = MessageDisplay('user', 'Test', '10:00')
    assert 'message-user' in msg.classes

def test_loading_animation():
    """Test loading indicator updates."""
    from src.tui.widgets.loading import LoadingIndicator
    loader = LoadingIndicator("Loading...")
    # Test spinner updates
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/utils/themes.py src/tui/widgets/
uv run ruff format src/tui/utils/themes.py src/tui/widgets/
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/utils/themes.py src/tui/widgets/
```

### Level 3: Integration Testing
```python
# tests/tui/test_visual_integration.py
@pytest.mark.asyncio
async def test_theme_switching():
    """Test runtime theme switching."""
    from src.tui.app import CCMonitorApp
    app = CCMonitorApp()
    
    async with app.run_test() as pilot:
        # Switch theme
        app.theme_manager.apply_theme('light')
        # Verify colors changed
```

### Level 4: Visual Testing Checklist
- [ ] Color scheme consistent across components
- [ ] Message types clearly distinguishable
- [ ] Borders render with rounded corners
- [ ] Loading indicators animate smoothly
- [ ] Transitions occur without flicker
- [ ] Focus indicators clearly visible
- [ ] Hover effects work as expected
- [ ] Theme switching applies immediately
- [ ] Contrast ratios adequate for readability

## Dependencies
- PRP 01: Project Setup and Structure (must be complete)
- PRP 02: Application Framework (must be complete)
- PRP 03: Layout System (must be complete)

## Estimated Effort
3.5 hours total:
- 1 hour: Theme system
- 45 minutes: Message styling
- 45 minutes: Loading states
- 30 minutes: Transitions
- 30 minutes: Visual polish

## Agent Recommendations
- **ui-ux-designer**: For color scheme and visual hierarchy
- **css-specialist**: For advanced styling and animations
- **accessibility-specialist**: For contrast and colorblind considerations
- **python-specialist**: For theme system implementation

## Risk Mitigation
- **Risk**: Poor color contrast
  - **Mitigation**: Use WCAG contrast checker, provide high-contrast theme
- **Risk**: Animation performance issues
  - **Mitigation**: Limit concurrent animations, provide option to disable
- **Risk**: Terminal color limitations
  - **Mitigation**: Detect capabilities, provide fallback colors
- **Risk**: Theme switching bugs
  - **Mitigation**: Thorough testing, clean CSS reload

## Definition of Done
- [ ] Theme system fully functional
- [ ] All color schemes implemented
- [ ] Message types visually distinct
- [ ] Loading indicators animate smoothly
- [ ] Transitions work without flicker
- [ ] CSS properly organized and maintainable
- [ ] All visual tests pass
- [ ] Manual testing confirms professional appearance
- [ ] Accessibility requirements met
- [ ] Performance remains smooth with all effects