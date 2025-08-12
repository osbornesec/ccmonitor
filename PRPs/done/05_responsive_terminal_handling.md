# PRP: Responsive Design and Terminal Handling

## Goal
Implement comprehensive terminal resize handling with dynamic panel sizing, minimum size constraints, and graceful degradation for limited terminal capabilities.

## Why
Terminal applications must adapt to various terminal sizes and capabilities. Users resize terminals frequently, and the application must maintain usability across different dimensions while providing clear feedback when constraints are violated.

## What
### Requirements
- Implement terminal resize event handling
- Add dynamic panel sizing based on terminal dimensions
- Enforce minimum size constraints (80x24)
- Create adaptive layouts for different terminal sizes
- Add scrolling when content exceeds panel dimensions
- Implement graceful degradation for limited terminals
- Provide clear user feedback for size constraints

### Success Criteria
- [ ] Layout adapts smoothly to terminal resize
- [ ] Minimum terminal size (80x24) enforced with warnings
- [ ] Panels resize proportionally with constraints
- [ ] Content scrolls when exceeding panel bounds
- [ ] No content cutoff or overlap at any size
- [ ] Performance remains smooth during resize
- [ ] Clear feedback when terminal too small

## All Needed Context

### Technical Specifications

#### Resize Event Handler
```python
# src/tui/utils/responsive.py
from textual.geometry import Size
from typing import Tuple, Optional
import logging

class ResponsiveManager:
    """Manages responsive layout and terminal sizing."""
    
    # Size breakpoints
    MINIMUM_SIZE = Size(80, 24)
    SMALL_SIZE = Size(100, 30)
    MEDIUM_SIZE = Size(120, 40)
    LARGE_SIZE = Size(150, 50)
    
    # Panel size configurations
    PANEL_CONFIGS = {
        'minimum': {
            'sidebar_width': 20,
            'header_height': 2,
            'footer_height': 1,
        },
        'small': {
            'sidebar_width': 25,
            'header_height': 3,
            'footer_height': 1,
        },
        'medium': {
            'sidebar_width': 30,
            'header_height': 3,
            'footer_height': 2,
        },
        'large': {
            'sidebar_width': 40,
            'header_height': 4,
            'footer_height': 2,
        }
    }
    
    def __init__(self, app):
        self.app = app
        self.current_size: Optional[Size] = None
        self.size_category: str = 'medium'
        
    def get_size_category(self, size: Size) -> str:
        """Determine size category from terminal dimensions."""
        if size.width < 100 or size.height < 30:
            return 'minimum'
        elif size.width < 120 or size.height < 40:
            return 'small'
        elif size.width < 150 or size.height < 50:
            return 'medium'
        else:
            return 'large'
    
    def validate_minimum_size(self, size: Size) -> Tuple[bool, Optional[str]]:
        """Check if terminal meets minimum requirements."""
        if size.width < self.MINIMUM_SIZE.width:
            return False, f"Terminal too narrow! Minimum width: {self.MINIMUM_SIZE.width}"
        if size.height < self.MINIMUM_SIZE.height:
            return False, f"Terminal too short! Minimum height: {self.MINIMUM_SIZE.height}"
        return True, None
    
    def calculate_panel_sizes(self, size: Size) -> dict:
        """Calculate optimal panel sizes for current terminal."""
        category = self.get_size_category(size)
        config = self.PANEL_CONFIGS[category]
        
        # Calculate actual sizes
        sidebar_width = min(
            config['sidebar_width'],
            int(size.width * 0.3)  # Max 30% of width
        )
        
        content_width = size.width - sidebar_width - 2  # Account for borders
        content_height = size.height - config['header_height'] - config['footer_height'] - 2
        
        return {
            'sidebar_width': sidebar_width,
            'content_width': content_width,
            'content_height': content_height,
            'header_height': config['header_height'],
            'footer_height': config['footer_height'],
        }
    
    async def handle_resize(self, size: Size) -> None:
        """Handle terminal resize event."""
        # Validate minimum size
        valid, message = self.validate_minimum_size(size)
        if not valid:
            self.app.notify(message, severity="warning", timeout=3)
            return
        
        # Calculate new sizes
        panel_sizes = self.calculate_panel_sizes(size)
        
        # Apply sizes to panels
        await self.apply_panel_sizes(panel_sizes)
        
        # Update current state
        self.current_size = size
        self.size_category = self.get_size_category(size)
        
        # Log resize
        logging.info(f"Terminal resized to {size.width}x{size.height} ({self.size_category})")
    
    async def apply_panel_sizes(self, sizes: dict) -> None:
        """Apply calculated sizes to panels."""
        # Update sidebar
        if sidebar := self.app.query_one("#projects-panel", None):
            sidebar.styles.width = sizes['sidebar_width']
        
        # Update header
        if header := self.app.query_one("Header", None):
            header.styles.height = sizes['header_height']
        
        # Update footer
        if footer := self.app.query_one("Footer", None):
            footer.styles.height = sizes['footer_height']
```

#### Enhanced Main Screen with Resize Handling
```python
# src/tui/screens/main.py (enhanced)
from textual.reactive import reactive

class MainScreen(Screen):
    """Main screen with responsive behavior."""
    
    # Reactive size tracking
    terminal_size = reactive(Size(80, 24))
    
    def __init__(self):
        super().__init__()
        self.responsive_manager = None
    
    async def on_mount(self) -> None:
        """Initialize responsive manager on mount."""
        from ..utils.responsive import ResponsiveManager
        self.responsive_manager = ResponsiveManager(self.app)
        
        # Get initial size
        self.terminal_size = self.app.size
        await self.responsive_manager.handle_resize(self.terminal_size)
    
    async def on_resize(self, event) -> None:
        """Handle terminal resize events."""
        self.terminal_size = event.size
        
        if self.responsive_manager:
            await self.responsive_manager.handle_resize(event.size)
        
        # Refresh layout
        self.refresh(layout=True)
    
    def watch_terminal_size(self, old_size: Size, new_size: Size) -> None:
        """React to terminal size changes."""
        # Update status bar with size info
        if footer := self.query_one("Footer", None):
            footer.update_message(f"Terminal: {new_size.width}x{new_size.height}")
```

#### Adaptive Panel Layouts
```python
# src/tui/widgets/adaptive_panel.py
from textual.widget import Widget
from textual.scroll_view import ScrollView

class AdaptivePanel(Widget):
    """Panel that adapts to available space."""
    
    DEFAULT_CSS = """
    AdaptivePanel {
        layout: vertical;
        overflow: hidden;
    }
    
    .panel-content {
        height: 1fr;
        overflow-y: auto;
    }
    
    .panel-compact {
        padding: 0;
        border: none;
    }
    
    .panel-normal {
        padding: 1;
        border: solid $primary;
    }
    
    .panel-spacious {
        padding: 2;
        border: thick $primary;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.compact_mode = False
        
    def on_resize(self, event) -> None:
        """Adapt panel based on available space."""
        width, height = event.size
        
        # Switch to compact mode if space limited
        if width < 30 or height < 10:
            self.enter_compact_mode()
        elif width < 50 or height < 20:
            self.enter_normal_mode()
        else:
            self.enter_spacious_mode()
    
    def enter_compact_mode(self) -> None:
        """Switch to compact display mode."""
        self.remove_class("panel-normal", "panel-spacious")
        self.add_class("panel-compact")
        self.compact_mode = True
        
        # Hide non-essential elements
        for element in self.query(".optional"):
            element.display = False
    
    def enter_normal_mode(self) -> None:
        """Switch to normal display mode."""
        self.remove_class("panel-compact", "panel-spacious")
        self.add_class("panel-normal")
        self.compact_mode = False
        
        # Show all elements
        for element in self.query(".optional"):
            element.display = True
    
    def enter_spacious_mode(self) -> None:
        """Switch to spacious display mode."""
        self.remove_class("panel-compact", "panel-normal")
        self.add_class("panel-spacious")
        self.compact_mode = False
        
        # Show all elements with extra spacing
        for element in self.query(".optional"):
            element.display = True
```

#### Scrolling Management
```python
# src/tui/widgets/scrollable_content.py
from textual.widgets import ScrollView
from textual.containers import VerticalScroll

class SmartScrollView(ScrollView):
    """ScrollView with intelligent scrolling behavior."""
    
    DEFAULT_CSS = """
    SmartScrollView {
        scrollbar-gutter: stable;
        scrollbar-size: 1 1;
    }
    
    SmartScrollView:focus {
        scrollbar-color: $warning;
    }
    
    /* Compact scrollbar for small terminals */
    .compact-scroll {
        scrollbar-size: 0 0;
    }
    
    /* Show scrollbar on hover/focus only */
    .auto-hide-scroll {
        scrollbar-size: 0 0;
    }
    
    .auto-hide-scroll:hover,
    .auto-hide-scroll:focus {
        scrollbar-size: 1 1;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_scroll = True
        self.compact_mode = False
    
    def on_resize(self, event) -> None:
        """Adjust scrolling based on available space."""
        width, height = event.size
        
        # Use compact scrollbars in small spaces
        if width < 40:
            self.add_class("compact-scroll")
            self.compact_mode = True
        else:
            self.remove_class("compact-scroll")
            self.compact_mode = False
        
        # Auto-hide scrollbars if space is premium
        if width < 60:
            self.add_class("auto-hide-scroll")
        else:
            self.remove_class("auto-hide-scroll")
    
    def scroll_to_bottom(self) -> None:
        """Scroll to bottom of content."""
        self.scroll_end(animate=True)
    
    def ensure_visible(self, widget) -> None:
        """Ensure widget is visible in viewport."""
        self.scroll_to_widget(widget, animate=True)
```

#### Terminal Capability Detection
```python
# src/tui/utils/terminal.py
import os
import sys
from typing import Dict, Any

class TerminalCapabilities:
    """Detect and handle terminal capabilities."""
    
    def __init__(self):
        self.capabilities = self.detect_capabilities()
    
    def detect_capabilities(self) -> Dict[str, Any]:
        """Detect current terminal capabilities."""
        caps = {
            'colors': self.detect_color_support(),
            'unicode': self.detect_unicode_support(),
            'mouse': self.detect_mouse_support(),
            'size': self.get_terminal_size(),
            'term_type': os.environ.get('TERM', 'unknown'),
            'is_tty': sys.stdout.isatty(),
        }
        
        return caps
    
    def detect_color_support(self) -> int:
        """Detect number of colors supported."""
        term = os.environ.get('TERM', '')
        colorterm = os.environ.get('COLORTERM', '')
        
        if 'truecolor' in colorterm or '24bit' in colorterm:
            return 16777216  # 24-bit color
        elif '256' in term:
            return 256
        elif 'color' in term:
            return 16
        else:
            return 8
    
    def detect_unicode_support(self) -> bool:
        """Check if terminal supports Unicode."""
        try:
            # Try to encode a Unicode character
            '🖥️'.encode(sys.stdout.encoding or 'utf-8')
            return True
        except (UnicodeEncodeError, AttributeError):
            return False
    
    def detect_mouse_support(self) -> bool:
        """Check if terminal supports mouse input."""
        term = os.environ.get('TERM', '')
        return 'xterm' in term or 'screen' in term
    
    def get_terminal_size(self) -> tuple:
        """Get current terminal size."""
        try:
            import shutil
            return shutil.get_terminal_size()
        except:
            return (80, 24)  # Default fallback
    
    def get_fallback_mode(self) -> str:
        """Determine appropriate fallback mode."""
        if not self.capabilities['is_tty']:
            return 'headless'
        elif self.capabilities['colors'] < 16:
            return 'monochrome'
        elif not self.capabilities['unicode']:
            return 'ascii'
        else:
            return 'normal'
```

### Responsive CSS
```css
/* src/tui/styles/responsive.css */

/* Minimum size constraints */
Screen {
    min-width: 80;
    min-height: 24;
}

/* Responsive breakpoints */
@media (max-width: 100) {
    /* Small terminal adjustments */
    ProjectsPanel {
        width: 20;
    }
    
    .panel-title {
        text-style: normal;
        padding: 0;
    }
    
    .optional {
        display: none;
    }
}

@media (max-width: 80) {
    /* Minimum terminal adjustments */
    ProjectsPanel {
        width: 18;
    }
    
    Header {
        height: 2;
    }
    
    Footer {
        height: 1;
    }
    
    * {
        padding: 0;
        margin: 0;
    }
}

@media (min-width: 150) {
    /* Large terminal enhancements */
    ProjectsPanel {
        width: 35%;
        max-width: 50;
    }
    
    .panel-title {
        text-style: bold;
        padding: 1 2;
    }
    
    * {
        padding: 1;
    }
}

/* Adaptive scrollbar */
@media (max-width: 100) {
    ScrollView {
        scrollbar-size: 0 0;
    }
}

/* Compact borders for small screens */
@media (max-height: 30) {
    * {
        border: solid;
    }
}
```

### Gotchas and Considerations
- **Resize Event Flooding**: Resize events can fire rapidly - debounce if needed
- **Calculation Timing**: Size calculations must account for borders and padding
- **Platform Differences**: Terminal size detection varies by OS
- **Minimum Size Enforcement**: Can't prevent resize, only warn user
- **Scroll Position**: Preserve scroll position during resize
- **Focus Preservation**: Maintain focus on current widget during resize

## Implementation Blueprint

### Phase 1: Responsive Manager (1 hour)
1. Create ResponsiveManager class
2. Implement size categorization
3. Add panel size calculations
4. Create resize event handler
5. Test with different sizes

### Phase 2: Terminal Capabilities (45 min)
1. Create TerminalCapabilities class
2. Implement capability detection
3. Add fallback mode determination
4. Test across terminals
5. Handle edge cases

### Phase 3: Adaptive Panels (1 hour)
1. Create AdaptivePanel base class
2. Implement compact/normal/spacious modes
3. Add element hiding/showing logic
4. Update existing panels
5. Test mode transitions

### Phase 4: Smart Scrolling (45 min)
1. Create SmartScrollView widget
2. Implement auto-hide scrollbars
3. Add scroll position preservation
4. Test overflow scenarios
5. Optimize performance

### Phase 5: Integration and Polish (30 min)
1. Integrate all components
2. Add responsive CSS rules
3. Test complete resize flow
4. Add user notifications
5. Performance optimization

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_responsive.py
import pytest
from src.tui.utils.responsive import ResponsiveManager
from textual.geometry import Size

def test_size_categorization():
    """Test terminal size categorization."""
    manager = ResponsiveManager(mock_app)
    assert manager.get_size_category(Size(80, 24)) == 'minimum'
    assert manager.get_size_category(Size(120, 40)) == 'medium'
    assert manager.get_size_category(Size(200, 60)) == 'large'

def test_minimum_size_validation():
    """Test minimum size enforcement."""
    manager = ResponsiveManager(mock_app)
    valid, msg = manager.validate_minimum_size(Size(70, 20))
    assert not valid
    assert "too narrow" in msg.lower()

def test_panel_size_calculation():
    """Test panel size calculations."""
    manager = ResponsiveManager(mock_app)
    sizes = manager.calculate_panel_sizes(Size(120, 40))
    assert sizes['sidebar_width'] <= 36  # 30% of 120
    assert sizes['content_width'] > 0

@pytest.mark.asyncio
async def test_resize_handling():
    """Test complete resize handling."""
    manager = ResponsiveManager(mock_app)
    await manager.handle_resize(Size(100, 30))
    assert manager.current_size == Size(100, 30)
    assert manager.size_category == 'small'
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/utils/responsive.py src/tui/utils/terminal.py
uv run ruff format src/tui/utils/responsive.py src/tui/utils/terminal.py
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/utils/responsive.py src/tui/utils/terminal.py
```

### Level 3: Integration Testing
```python
# tests/tui/test_responsive_integration.py
@pytest.mark.asyncio
async def test_app_resize():
    """Test app handles resize correctly."""
    from src.tui.app import CCMonitorApp
    app = CCMonitorApp()
    
    async with app.run_test(size=(120, 40)) as pilot:
        # Simulate resize
        await pilot.resize_terminal(100, 30)
        
        # Verify layout adjusted
        sidebar = app.query_one("#projects-panel")
        assert sidebar.styles.width == 25
```

### Level 4: Manual Testing Matrix
| Terminal Size | Expected Behavior |
|--------------|------------------|
| 80x24 | Minimum mode, compact display |
| 100x30 | Small mode, reduced padding |
| 120x40 | Medium mode, normal display |
| 150x50 | Large mode, spacious display |
| 60x20 | Warning shown, degraded mode |

## Dependencies
- PRP 01: Project Setup and Structure (must be complete)
- PRP 02: Application Framework (must be complete)
- PRP 03: Layout System (must be complete)

## Estimated Effort
4 hours total:
- 1 hour: Responsive manager
- 45 minutes: Terminal capabilities
- 1 hour: Adaptive panels
- 45 minutes: Smart scrolling
- 30 minutes: Integration and polish

## Agent Recommendations
- **python-specialist**: For resize event handling and calculations
- **css-specialist**: For responsive CSS rules and media queries
- **performance-optimizer**: For efficient resize handling
- **test-writer**: For comprehensive resize scenario testing

## Risk Mitigation
- **Risk**: Resize event flooding
  - **Mitigation**: Implement debouncing, batch updates
- **Risk**: Layout calculation errors
  - **Mitigation**: Add bounds checking, fallback values
- **Risk**: Terminal capability misdetection
  - **Mitigation**: Provide manual override options
- **Risk**: Performance degradation during resize
  - **Mitigation**: Optimize calculations, use caching

## Definition of Done
- [ ] Terminal resize events handled smoothly
- [ ] Minimum size (80x24) enforced with warnings
- [ ] Panels resize proportionally with constraints
- [ ] Content scrolls appropriately
- [ ] No content cutoff at any size
- [ ] Terminal capabilities detected correctly
- [ ] Fallback modes work for limited terminals
- [ ] All responsive tests pass
- [ ] Manual testing confirms smooth resizing
- [ ] Performance remains acceptable during resize