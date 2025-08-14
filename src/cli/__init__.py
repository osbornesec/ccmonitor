"""CLI module for ccmonitor.

Command-line interface components for Claude Code conversation monitoring.

API STABILITY NOTICE:
- Direct imports from this module are deprecated as of v0.2.0
- Use specific imports instead:
  * CLIContext, MonitorConfig: from src.cli.types
  * FileMonitor: from src.cli.handlers.file_handler
- Compatibility shims will be removed in v1.0.0
- See __getattr__ implementation below for deprecation warnings
"""

import warnings

# CLI package for CCMonitor tool
# Import at module level to avoid PLC0415 violations
from .handlers.file_handler import FileMonitor
from .types import CLIContext, MonitorConfig


# Compatibility shims with deprecation warnings (to be removed in v1.0.0)
def __getattr__(name: str) -> object:
    """Handle deprecated imports with warnings."""
    if name == "CLIContext":
        warnings.warn(
            "Importing CLIContext from src.cli is deprecated. "
            "Use 'from src.cli.types import CLIContext' instead. "
            "This compatibility import will be removed in v1.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return CLIContext
    if name == "MonitorConfig":
        warnings.warn(
            "Importing MonitorConfig from src.cli is deprecated. "
            "Use 'from src.cli.types import MonitorConfig' instead. "
            "This compatibility import will be removed in v1.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return MonitorConfig
    if name == "FileMonitor":
        warnings.warn(
            "Importing FileMonitor from src.cli is deprecated. "
            "Use 'from src.cli.handlers.file_handler import FileMonitor' instead. "
            "This compatibility import will be removed in v1.0.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return FileMonitor
    msg = f"module '{__name__}' has no attribute '{name}'"
    raise AttributeError(msg)


__all__ = [
    # Deprecated re-exports (will be removed in v1.0.0)
    "CLIContext",
    "FileMonitor",
    "MonitorConfig",
]
