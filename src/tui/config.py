"""Centralized configuration management for the TUI application."""

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class TUIConfig:
    """Configuration settings for the TUI application."""

    # Application metadata
    app_name: str = "CCMonitor"
    app_version: str = "0.1.0"

    # UI settings
    default_theme: str = "dark"
    animation_level: str = "full"  # "full", "reduced", "none"
    auto_refresh_interval: float = 1.0

    # Terminal settings
    min_terminal_width: int = 80
    min_terminal_height: int = 24
    enable_mouse: bool = True
    enable_unicode: bool = True

    # Performance settings
    max_history_lines: int = 1000
    batch_update_threshold: int = 10
    async_worker_threads: int = 4

    # Logging configuration
    log_level: str = "INFO"
    log_file: str | None = None
    log_to_console: bool = False

    # Feature flags
    enable_help_overlay: bool = True
    enable_command_palette: bool = True
    enable_shortcuts_footer: bool = True

    def __post_init__(self) -> None:
        """Set up derived configuration values."""
        if self.log_file is None:
            config_dir = Path.home() / ".config" / "ccmonitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = str(config_dir / "tui.log")


def load_config(config_path: Path | None = None) -> TUIConfig:
    """Load configuration from file or create defaults."""
    if config_path is None:
        config_path = Path.home() / ".config" / "ccmonitor" / "tui_config.yaml"

    if config_path.exists():
        try:
            with config_path.open() as f:
                config_data = yaml.safe_load(f) or {}
            return TUIConfig(**config_data)
        except (OSError, yaml.YAMLError, TypeError, ValueError) as e:
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to load config from %s: %s",
                config_path,
                e,
            )

    return TUIConfig()


def save_config(config: TUIConfig, config_path: Path | None = None) -> None:
    """Save configuration to file."""
    if config_path is None:
        config_path = Path.home() / ".config" / "ccmonitor" / "tui_config.yaml"

    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_dict = {
        field.name: getattr(config, field.name)
        for field in config.__dataclass_fields__.values()
    }

    with config_path.open("w") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False)


# Global configuration instance
_config: TUIConfig | None = None


def get_config() -> TUIConfig:
    """Get global configuration instance."""
    global _config  # noqa: PLW0603
    if _config is None:
        _config = load_config()
    return _config
