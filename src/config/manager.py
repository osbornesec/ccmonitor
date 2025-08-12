"""Unified configuration management for CLI and TUI."""

import sys
from pathlib import Path
from typing import Any, ClassVar

import yaml


class ConfigManager:
    """Unified configuration management for CLI and TUI."""

    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "ccmonitor" / "config.yaml"

    DEFAULT_CONFIG: ClassVar[dict[str, Any]] = {
        "general": {
            "default_mode": "tui",  # 'tui' or 'cli'
            "verbose": False,
            "log_level": "INFO",
        },
        "cli": {
            "output_format": "json",
            "color_output": True,
            "pager": "less",
            "default_level": "medium",
            "default_backup": True,
            "default_progress": True,
            "default_parallel_workers": 4,
            "default_pattern": "*.jsonl",
            "default_recursive": False,
            "colorize_output": True,
            "show_warnings": True,
            "chunk_size": 1000,
            "memory_limit_mb": 512,
            "require_confirmation": True,
            "max_file_size_mb": 100,
            "backup_retention_days": 30,
            "schedule_enabled": False,
            "schedule_policy": "weekly",
            "schedule_level": "light",
            "schedule_directories": [],
        },
        "tui": {
            "theme": "dark",
            "start_maximized": False,
            "show_help_on_start": False,
            "animation_level": "full",  # 'full', 'reduced', 'none'
            "autosave_state": True,
            "auto_refresh_interval": 1.0,
            "min_terminal_width": 80,
            "min_terminal_height": 24,
            "enable_mouse": True,
            "enable_unicode": True,
            "max_history_lines": 1000,
            "batch_update_threshold": 10,
            "async_worker_threads": 4,
            "enable_help_overlay": True,
            "enable_command_palette": True,
            "enable_shortcuts_footer": True,
        },
        "monitoring": {
            "watch_paths": [],
            "poll_interval": 1.0,
            "max_history": 1000,
        },
        "database": {
            "path": "~/.config/ccmonitor/conversations.db",
            "auto_vacuum": True,
        },
    }

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the configuration manager."""
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self.load_config()

    def load_config(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()

        try:
            with self.config_path.open(encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}

            # Merge with defaults
            config = self.DEFAULT_CONFIG.copy()
            self.deep_merge(config, user_config)

        except (OSError, yaml.YAMLError) as e:
            # Write to stderr instead of print
            sys.stderr.write(f"Warning: Failed to load config: {e}\n")
            return self.DEFAULT_CONFIG.copy()
        else:
            return config

    def save_config(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with self.config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def get(self, key: str, default: object = None) -> object:
        """Get configuration value using dot notation."""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: object) -> None:
        """Set configuration value using dot notation."""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_cli_config(self) -> dict[str, Any]:
        """Get CLI-specific configuration."""
        return self.get("cli", {})  # type: ignore[return-value]

    def get_tui_config(self) -> dict[str, Any]:
        """Get TUI-specific configuration."""
        return self.get("tui", {})  # type: ignore[return-value]

    def get_general_config(self) -> dict[str, Any]:
        """Get general configuration."""
        return self.get("general", {})  # type: ignore[return-value]

    def should_use_tui_by_default(self) -> bool:
        """Check if TUI should be used by default."""
        return self.get("general.default_mode", "tui") == "tui"

    @staticmethod
    def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
        """Deep merge override into base."""
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                ConfigManager.deep_merge(base[key], value)
            else:
                base[key] = value

    def _validate_general_settings(self, errors: list[str]) -> None:
        """Validate general configuration settings."""
        default_mode = self.get("general.default_mode")
        if default_mode not in ["cli", "tui"]:
            errors.append(f"Invalid default_mode: {default_mode}")

    def _validate_cli_settings(self, errors: list[str]) -> None:
        """Validate CLI configuration settings."""
        cli_format = self.get("cli.default_output_format")
        if cli_format and cli_format not in ["table", "json", "csv", "html"]:
            errors.append(f"Invalid CLI output format: {cli_format}")

    def _validate_tui_settings(self, errors: list[str]) -> None:
        """Validate TUI configuration settings."""
        tui_theme = self.get("tui.theme")
        if tui_theme and tui_theme not in [
            "dark",
            "light",
            "monokai",
            "solarized",
        ]:
            errors.append(f"Invalid TUI theme: {tui_theme}")

        animation_level = self.get("tui.animation_level")
        if animation_level and animation_level not in [
            "full",
            "reduced",
            "none",
        ]:
            errors.append(f"Invalid animation level: {animation_level}")

    def _validate_numeric_settings(self, errors: list[str]) -> None:
        """Validate numeric configuration settings."""
        poll_interval = self.get("monitoring.poll_interval")
        if poll_interval and (
            not isinstance(poll_interval, (int, float)) or poll_interval <= 0
        ):
            errors.append("Poll interval must be a positive number")

    def validate_config(self) -> list[str]:
        """Validate current configuration and return any errors."""
        errors: list[str] = []

        self._validate_general_settings(errors)
        self._validate_cli_settings(errors)
        self._validate_tui_settings(errors)
        self._validate_numeric_settings(errors)

        return errors


def load_config(config_path: Path | None = None) -> ConfigManager:
    """Load configuration manager instance."""
    return ConfigManager(config_path)


def load_default_config() -> dict[str, Any]:
    """Load default configuration as dictionary."""
    manager = ConfigManager()
    return manager.config


# Global instance for backwards compatibility
_global_manager: ConfigManager | None = None


def get_global_config() -> ConfigManager:
    """Get global configuration manager instance."""
    global _global_manager  # noqa: PLW0603
    if _global_manager is None:
        _global_manager = ConfigManager()
    return _global_manager
