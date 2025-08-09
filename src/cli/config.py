"""Configuration management for CCMonitor CLI.

Configuration system with profiles and environment integration.
"""

import json
import os
import yaml
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CLIConfig:
    """CLI configuration data structure."""

    # Core settings
    default_level: str = "medium"
    default_backup: bool = True
    default_progress: bool = True
    default_verbose: bool = False

    # Batch processing settings
    default_parallel_workers: int = 4
    default_pattern: str = "*.jsonl"
    default_recursive: bool = False

    # Output settings
    default_output_format: str = "table"
    colorize_output: bool = True
    show_warnings: bool = True

    # Performance settings
    chunk_size: int = 1000
    memory_limit_mb: int = 512

    # Safety settings
    require_confirmation: bool = True
    max_file_size_mb: int = 100
    backup_retention_days: int = 30

    # Scheduling settings
    schedule_enabled: bool = False
    schedule_policy: str = "weekly"
    schedule_level: str = "light"
    schedule_directories: list = None

    def __post_init__(self) -> None:
        """Initialize default values for mutable fields."""
        if self.schedule_directories is None:
            self.schedule_directories = []


class ConfigManager:
    """Configuration manager for CLI application."""

    def __init__(self) -> None:
        """Initialize configuration manager."""
        self.config = CLIConfig()
        self.config_file = None
        self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration from standard locations."""
        config_file = self._find_config_file()
        if config_file:
            with suppress(Exception):
                self.load_config(config_file)

    def _find_config_file(self) -> Path | None:
        """Find configuration file in standard locations."""
        config_locations = [
            Path.cwd() / ".ccmonitor.yaml",
            Path.cwd() / ".ccmonitor.yml",
            Path.home() / ".ccmonitor.yaml",
            Path.home() / ".ccmonitor.yml",
            Path.home() / ".config" / "ccmonitor" / "config.yaml",
            Path.home() / ".config" / "ccmonitor" / "config.yml",
        ]

        for config_path in config_locations:
            if config_path.exists() and config_path.is_file():
                return config_path

        return None

    def load_config(self, config_path: Path) -> dict[str, Any]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid

        """
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)

        try:
            with config_path.open(encoding="utf-8") as f:
                if config_path.suffix.lower() == ".json":
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f)

            # Update configuration
            self._update_config_from_dict(config_data or {})
            self.config_file = config_path

            return asdict(self.config)

        except Exception as e:
            msg = f"Invalid configuration file {config_path}: {e}"
            raise ValueError(msg) from e

    def load_default_config(self) -> dict[str, Any]:
        """Load default configuration with environment variable overrides.

        Returns:
            Configuration dictionary

        """
        # Apply environment variable overrides
        env_overrides = self._load_environment_overrides()
        self._update_config_from_dict(env_overrides)

        return asdict(self.config)

    def _load_environment_overrides(self) -> dict[str, Any]:
        """Load configuration overrides from environment variables."""
        env_overrides = {}

        # Map environment variables to config keys
        env_mappings = {
            "CCMONITOR_LEVEL": "default_level",
            "CCMONITOR_BACKUP": "default_backup",
            "CCMONITOR_VERBOSE": "default_verbose",
            "CCMONITOR_PARALLEL": "default_parallel_workers",
            "CCMONITOR_PATTERN": "default_pattern",
            "CCMONITOR_RECURSIVE": "default_recursive",
            "CCMONITOR_FORMAT": "default_output_format",
            "CCMONITOR_COLORIZE": "colorize_output",
            "CCMONITOR_CHUNK_SIZE": "chunk_size",
            "CCMONITOR_MEMORY_LIMIT": "memory_limit_mb",
            "CCMONITOR_MAX_FILE_SIZE": "max_file_size_mb",
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                env_overrides[config_key] = self._convert_env_value(
                    env_value,
                    config_key,
                )

        return env_overrides

    def _convert_env_value(
        self, value: str, config_key: str
    ) -> str | int | bool:
        """Convert environment variable string to appropriate type."""
        # Boolean conversions
        if config_key in [
            "default_backup",
            "default_verbose",
            "default_recursive",
            "colorize_output",
            "show_warnings",
            "require_confirmation",
            "schedule_enabled",
        ]:
            return value.lower() in ["true", "1", "yes", "on"]

        # Integer conversions
        if config_key in [
            "default_parallel_workers",
            "chunk_size",
            "memory_limit_mb",
            "max_file_size_mb",
            "backup_retention_days",
        ]:
            try:
                return int(value)
            except ValueError:
                return value  # Return as string if conversion fails

        # String values (no conversion needed)
        return value

    def _update_config_from_dict(self, config_dict: dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def save_config(
        self,
        config_path: Path | None = None,
        file_format: str = "yaml",
    ) -> None:
        """Save current configuration to file.

        Args:
            config_path: Path to save configuration (default: current config file)
            file_format: Output format ('yaml' or 'json')

        Raises:
            ValueError: If format is invalid or path is not writable

        """
        if config_path is None:
            config_path = self.config_file or (Path.home() / ".ccmonitor.yaml")

        if file_format not in ["yaml", "json"]:
            msg = f"Invalid format: {file_format}. Must be 'yaml' or 'json'"
            raise ValueError(msg)

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_data = asdict(self.config)

        try:
            with config_path.open("w", encoding="utf-8") as f:
                if file_format == "json":
                    json.dump(config_data, f, indent=2)
                else:
                    yaml.dump(
                        config_data,
                        f,
                        default_flow_style=False,
                        indent=2,
                    )

            self.config_file = config_path

        except Exception as e:
            msg = f"Failed to save configuration to {config_path}: {e}"
            raise ValueError(msg) from e

    def get_current_config(self) -> dict[str, Any]:
        """Get current configuration as dictionary."""
        return asdict(self.config)

    def set_config_value(self, key: str, value: str | int | bool) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Raises:
            ValueError: If key is invalid

        """
        if not hasattr(self.config, key):
            msg = f"Invalid configuration key: {key}"
            raise ValueError(msg)

        # Convert string values if needed
        current_value = getattr(self.config, key)
        if isinstance(current_value, bool) and isinstance(value, str):
            value = value.lower() in ["true", "1", "yes", "on"]
        elif isinstance(current_value, int) and isinstance(value, str):
            try:
                value = int(value)
            except ValueError as e:
                msg = f"Invalid integer value for {key}: {value}"
                raise ValueError(msg) from e

        setattr(self.config, key, value)

    def get_config_value(
        self, key: str, default: str | int | bool = None
    ) -> str | int | bool:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value

        """
        return getattr(self.config, key, default)

    def create_profile(
        self,
        name: str,
        config_overrides: dict[str, Any],
    ) -> Path:
        """Create configuration profile.

        Args:
            name: Profile name
            config_overrides: Configuration overrides for profile

        Returns:
            Path to created profile file

        Raises:
            ValueError: If profile creation fails

        """
        # Create profile directory
        profile_dir = Path.home() / ".config" / "ccmonitor" / "profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)

        # Create profile configuration
        profile_config = asdict(self.config)
        profile_config.update(config_overrides)

        # Save profile
        profile_path = profile_dir / f"{name}.yaml"

        try:
            with profile_path.open("w", encoding="utf-8") as f:
                yaml.dump(
                    profile_config,
                    f,
                    default_flow_style=False,
                    indent=2,
                )
        except Exception as e:
            msg = f"Failed to create profile {name}: {e}"
            raise ValueError(msg) from e
        else:
            return profile_path

    def load_profile(self, name: str) -> None:
        """Load configuration profile.

        Args:
            name: Profile name

        Raises:
            FileNotFoundError: If profile doesn't exist
            ValueError: If profile is invalid

        """
        profile_dir = Path.home() / ".config" / "ccmonitor" / "profiles"
        profile_path = profile_dir / f"{name}.yaml"

        if not profile_path.exists():
            msg = f"Profile not found: {name}"
            raise FileNotFoundError(msg)

        self.load_config(profile_path)

    def list_profiles(self) -> list[str]:
        """List available configuration profiles.

        Returns:
            List of profile names

        """
        profile_dir = Path.home() / ".config" / "ccmonitor" / "profiles"

        if not profile_dir.exists():
            return []

        return sorted(
            [profile_file.stem for profile_file in profile_dir.glob("*.yaml")]
        )

    def validate_config(self) -> list[str]:
        """Validate current configuration.

        Returns:
            List of validation errors (empty if valid)

        """
        errors = []
        max_workers = 16
        min_memory = 64

        # Validate analysis level
        if self.config.default_level not in ["light", "medium", "aggressive"]:
            errors.append(
                f"Invalid default_level: {self.config.default_level}"
            )

        # Validate parallel workers
        if (
            self.config.default_parallel_workers < 1
            or self.config.default_parallel_workers > max_workers
        ):
            errors.append(
                f"Invalid default_parallel_workers: {self.config.default_parallel_workers}",
            )

        # Validate output format
        if self.config.default_output_format not in [
            "table",
            "json",
            "csv",
            "html",
        ]:
            errors.append(
                f"Invalid default_output_format: {self.config.default_output_format}",
            )

        # Validate memory limits
        if self.config.memory_limit_mb < min_memory:
            errors.append(
                f"Memory limit too low: {self.config.memory_limit_mb}MB"
            )

        if self.config.max_file_size_mb < 1:
            errors.append(
                f"Max file size too low: {self.config.max_file_size_mb}MB"
            )

        # Validate retention days
        if self.config.backup_retention_days < 1:
            errors.append(
                f"Invalid backup retention: {self.config.backup_retention_days} days",
            )

        # Validate schedule policy
        if self.config.schedule_policy not in ["daily", "weekly", "monthly"]:
            errors.append(
                f"Invalid schedule_policy: {self.config.schedule_policy}"
            )

        return errors

    def get_effective_config(
        self,
        cli_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get effective configuration with CLI overrides applied.

        Args:
            cli_overrides: CLI argument overrides

        Returns:
            Effective configuration dictionary

        """
        effective_config = asdict(self.config)

        if cli_overrides:
            effective_config.update(cli_overrides)

        return effective_config
