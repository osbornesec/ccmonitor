"""Test suite for CLI configuration management.

Comprehensive testing of configuration loading, saving, validation,
and environment variable handling.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.cli.config import CLIConfig, ConfigManager


class TestCLIConfig:
    """Test suite for CLIConfig dataclass."""

    def test_cli_config_default_initialization(self) -> None:
        """Test CLIConfig initialization with default values."""
        config = CLIConfig()

        # Core settings
        assert config.default_level == "medium"
        assert config.default_backup is True
        assert config.default_progress is True
        assert config.default_verbose is False

        # Batch processing
        assert config.default_parallel_workers == 4
        assert config.default_pattern == "*.jsonl"
        assert config.default_recursive is False

        # Output settings
        assert config.default_output_format == "table"
        assert config.colorize_output is True
        assert config.show_warnings is True

        # Performance
        assert config.chunk_size == 1000
        assert config.memory_limit_mb == 512

        # Safety
        assert config.require_confirmation is True
        assert config.max_file_size_mb == 100
        assert config.backup_retention_days == 30

        # Scheduling
        assert config.schedule_enabled is False
        assert config.schedule_policy == "weekly"
        assert config.schedule_level == "light"
        assert config.schedule_directories == []

    def test_cli_config_custom_initialization(self) -> None:
        """Test CLIConfig initialization with custom values."""
        config = CLIConfig(
            default_level="aggressive",
            default_parallel_workers=8,
            colorize_output=False,
            schedule_directories=["dir1", "dir2"],
        )

        assert config.default_level == "aggressive"
        assert config.default_parallel_workers == 8
        assert config.colorize_output is False
        assert config.schedule_directories == ["dir1", "dir2"]

    def test_cli_config_post_init(self) -> None:
        """Test CLIConfig __post_init__ method."""
        config = CLIConfig()
        # Should initialize empty list for schedule_directories
        assert config.schedule_directories == []

        # Test with explicit None
        config2 = CLIConfig()
        config2.schedule_directories = None
        config2.__post_init__()
        assert config2.schedule_directories == []


class TestConfigManager:
    """Test suite for ConfigManager class."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigManager()

    def test_config_manager_initialization(self) -> None:
        """Test ConfigManager initialization."""
        manager = ConfigManager()

        assert isinstance(manager.config, CLIConfig)
        assert manager.config_file is None

    @patch("src.cli.config.ConfigManager._find_config_file")
    def test_load_default_config_found(self, mock_find: Mock) -> None:
        """Test loading default configuration when file found."""
        config_file = self.temp_dir / ".ccmonitor.yaml"
        config_file.write_text("default_verbose: true\n")
        mock_find.return_value = config_file

        manager = ConfigManager()

        # Should have loaded the configuration
        assert manager.config.default_verbose is True

    @patch("src.cli.config.ConfigManager._find_config_file")
    def test_load_default_config_not_found(self, mock_find: Mock) -> None:
        """Test loading default configuration when no file found."""
        mock_find.return_value = None

        manager = ConfigManager()

        # Should use default values
        assert manager.config.default_verbose is False

    def test_find_config_file_current_dir(self) -> None:
        """Test finding config file in current directory."""
        config_file = self.temp_dir / ".ccmonitor.yaml"
        config_file.write_text("test: value")

        with patch("pathlib.Path.cwd", return_value=self.temp_dir):
            result = self.config_manager._find_config_file()
            assert result == config_file

    def test_find_config_file_home_dir(self) -> None:
        """Test finding config file in home directory."""
        config_file = self.temp_dir / ".ccmonitor.yml"
        config_file.write_text("test: value")

        with (
            patch("pathlib.Path.home", return_value=self.temp_dir),
            patch("pathlib.Path.cwd", return_value=Path("/tmp")),
        ):
            result = self.config_manager._find_config_file()
            assert result == config_file

    def test_find_config_file_config_dir(self) -> None:
        """Test finding config file in .config directory."""
        config_dir = self.temp_dir / ".config" / "ccmonitor"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("test: value")

        with (
            patch("pathlib.Path.home", return_value=self.temp_dir),
            patch("pathlib.Path.cwd", return_value=Path("/tmp")),
        ):
            result = self.config_manager._find_config_file()
            assert result == config_file

    def test_find_config_file_not_found(self) -> None:
        """Test when no config file is found."""
        with (
            patch("pathlib.Path.home", return_value=self.temp_dir),
            patch("pathlib.Path.cwd", return_value=Path("/tmp")),
        ):
            result = self.config_manager._find_config_file()
            assert result is None

    def test_load_config_yaml(self) -> None:
        """Test loading YAML configuration file."""
        config_file = self.temp_dir / "config.yaml"
        config_data = {
            "default_level": "aggressive",
            "default_parallel_workers": 8,
            "colorize_output": False,
        }

        with config_file.open("w") as f:
            yaml.dump(config_data, f)

        result = self.config_manager.load_config(config_file)

        assert result["default_level"] == "aggressive"
        assert result["default_parallel_workers"] == 8
        assert result["colorize_output"] is False
        assert self.config_manager.config_file == config_file

    def test_load_config_json(self) -> None:
        """Test loading JSON configuration file."""
        config_file = self.temp_dir / "config.json"
        config_data = {
            "default_level": "light",
            "chunk_size": 500,
        }

        with config_file.open("w") as f:
            json.dump(config_data, f)

        result = self.config_manager.load_config(config_file)

        assert result["default_level"] == "light"
        assert result["chunk_size"] == 500

    def test_load_config_nonexistent_file(self) -> None:
        """Test loading non-existent configuration file."""
        nonexistent = self.temp_dir / "nonexistent.yaml"

        with pytest.raises(
            FileNotFoundError, match="Configuration file not found"
        ):
            self.config_manager.load_config(nonexistent)

    def test_load_config_invalid_yaml(self) -> None:
        """Test loading invalid YAML configuration."""
        config_file = self.temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Invalid configuration file"):
            self.config_manager.load_config(config_file)

    def test_load_config_empty_file(self) -> None:
        """Test loading empty configuration file."""
        config_file = self.temp_dir / "config.yaml"
        config_file.write_text("")

        result = self.config_manager.load_config(config_file)

        # Should return current config as dict
        assert isinstance(result, dict)

    def test_load_default_config_with_env_overrides(self) -> None:
        """Test loading default config with environment variable overrides."""
        with patch.dict(
            os.environ,
            {
                "CCMONITOR_LEVEL": "aggressive",
                "CCMONITOR_VERBOSE": "true",
                "CCMONITOR_PARALLEL": "8",
            },
        ):
            result = self.config_manager.load_default_config()

            assert result["default_level"] == "aggressive"
            assert result["default_verbose"] is True
            assert result["default_parallel_workers"] == 8

    def test_load_environment_overrides(self) -> None:
        """Test loading environment variable overrides."""
        env_vars = {
            "CCMONITOR_LEVEL": "light",
            "CCMONITOR_BACKUP": "false",
            "CCMONITOR_VERBOSE": "true",
            "CCMONITOR_PARALLEL": "6",
            "CCMONITOR_PATTERN": "*.json",
            "CCMONITOR_RECURSIVE": "true",
            "CCMONITOR_FORMAT": "json",
            "CCMONITOR_COLORIZE": "false",
            "CCMONITOR_CHUNK_SIZE": "2000",
            "CCMONITOR_MEMORY_LIMIT": "1024",
            "CCMONITOR_MAX_FILE_SIZE": "200",
        }

        with patch.dict(os.environ, env_vars):
            result = self.config_manager._load_environment_overrides()

            assert result["default_level"] == "light"
            assert result["default_backup"] is False
            assert result["default_verbose"] is True
            assert result["default_parallel_workers"] == 6
            assert result["default_pattern"] == "*.json"
            assert result["default_recursive"] is True
            assert result["default_output_format"] == "json"
            assert result["colorize_output"] is False
            assert result["chunk_size"] == 2000
            assert result["memory_limit_mb"] == 1024
            assert result["max_file_size_mb"] == 200

    def test_convert_env_value_boolean(self) -> None:
        """Test environment value conversion for boolean types."""
        manager = self.config_manager

        # True values
        for true_val in ["true", "1", "yes", "on"]:
            result = manager._convert_env_value(true_val, "default_backup")
            assert result is True

        # False values
        for false_val in ["false", "0", "no", "off", "anything"]:
            result = manager._convert_env_value(false_val, "default_backup")
            assert result is False

    def test_convert_env_value_integer(self) -> None:
        """Test environment value conversion for integer types."""
        manager = self.config_manager

        # Valid integer
        result = manager._convert_env_value("42", "default_parallel_workers")
        assert result == 42

        # Invalid integer (should return as string)
        result = manager._convert_env_value(
            "invalid", "default_parallel_workers"
        )
        assert result == "invalid"

    def test_convert_env_value_string(self) -> None:
        """Test environment value conversion for string types."""
        manager = self.config_manager

        result = manager._convert_env_value("test_value", "default_level")
        assert result == "test_value"

    def test_update_config_from_dict(self) -> None:
        """Test updating configuration from dictionary."""
        updates = {
            "default_level": "aggressive",
            "chunk_size": 2000,
            "invalid_key": "should_be_ignored",
        }

        self.config_manager._update_config_from_dict(updates)

        assert self.config_manager.config.default_level == "aggressive"
        assert self.config_manager.config.chunk_size == 2000
        # Invalid keys should be ignored
        assert not hasattr(self.config_manager.config, "invalid_key")

    def test_save_config_yaml(self) -> None:
        """Test saving configuration to YAML file."""
        config_file = self.temp_dir / "save_test.yaml"

        # Modify some config values
        self.config_manager.config.default_level = "aggressive"
        self.config_manager.config.chunk_size = 2000

        self.config_manager.save_config(config_file, "yaml")

        assert config_file.exists()

        # Verify saved content
        with config_file.open() as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["default_level"] == "aggressive"
        assert saved_data["chunk_size"] == 2000

    def test_save_config_json(self) -> None:
        """Test saving configuration to JSON file."""
        config_file = self.temp_dir / "save_test.json"

        # Modify some config values
        self.config_manager.config.default_verbose = True
        self.config_manager.config.default_parallel_workers = 6

        self.config_manager.save_config(config_file, "json")

        assert config_file.exists()

        # Verify saved content
        with config_file.open() as f:
            saved_data = json.load(f)

        assert saved_data["default_verbose"] is True
        assert saved_data["default_parallel_workers"] == 6

    def test_save_config_invalid_format(self) -> None:
        """Test saving configuration with invalid format."""
        config_file = self.temp_dir / "test.txt"

        with pytest.raises(ValueError, match="Invalid format"):
            self.config_manager.save_config(config_file, "invalid")

    def test_save_config_default_path(self) -> None:
        """Test saving configuration with default path."""
        with patch("pathlib.Path.home", return_value=self.temp_dir):
            self.config_manager.save_config()

            expected_path = self.temp_dir / ".ccmonitor.yaml"
            assert expected_path.exists()
            assert self.config_manager.config_file == expected_path

    def test_save_config_creates_parent_dir(self) -> None:
        """Test that save_config creates parent directories."""
        nested_config = self.temp_dir / "nested" / "dir" / "config.yaml"

        self.config_manager.save_config(nested_config)

        assert nested_config.exists()
        assert nested_config.parent.exists()

    def test_save_config_write_error(self) -> None:
        """Test save_config with write error."""
        config_file = self.temp_dir / "readonly" / "config.yaml"

        with patch.object(
            Path, "open", side_effect=PermissionError("Permission denied")
        ):
            with pytest.raises(
                ValueError, match="Failed to save configuration"
            ):
                self.config_manager.save_config(config_file)

    def test_get_current_config(self) -> None:
        """Test getting current configuration as dictionary."""
        result = self.config_manager.get_current_config()

        assert isinstance(result, dict)
        assert "default_level" in result
        assert "chunk_size" in result
        assert result["default_level"] == "medium"

    def test_set_config_value_string(self) -> None:
        """Test setting string configuration value."""
        self.config_manager.set_config_value(
            "default_level", value="aggressive"
        )

        assert self.config_manager.config.default_level == "aggressive"

    def test_set_config_value_boolean_from_string(self) -> None:
        """Test setting boolean configuration value from string."""
        self.config_manager.set_config_value("default_verbose", value="true")

        assert self.config_manager.config.default_verbose is True

    def test_set_config_value_integer_from_string(self) -> None:
        """Test setting integer configuration value from string."""
        self.config_manager.set_config_value("chunk_size", value="2000")

        assert self.config_manager.config.chunk_size == 2000

    def test_set_config_value_invalid_key(self) -> None:
        """Test setting invalid configuration key."""
        with pytest.raises(ValueError, match="Invalid configuration key"):
            self.config_manager.set_config_value("invalid_key", value="test")

    def test_set_config_value_invalid_integer(self) -> None:
        """Test setting invalid integer value."""
        with pytest.raises(ValueError, match="Invalid integer value"):
            self.config_manager.set_config_value(
                "chunk_size", value="not_a_number"
            )

    def test_get_config_value(self) -> None:
        """Test getting configuration value."""
        result = self.config_manager.get_config_value("default_level")
        assert result == "medium"

        # Test with default
        result = self.config_manager.get_config_value(
            "nonexistent_key",
            default="default_value",
        )
        assert result == "default_value"

    def test_create_profile(self) -> None:
        """Test creating configuration profile."""
        overrides = {
            "default_level": "aggressive",
            "chunk_size": 2000,
        }

        with patch("pathlib.Path.home", return_value=self.temp_dir):
            profile_path = self.config_manager.create_profile(
                "aggressive", overrides
            )

            expected_path = (
                self.temp_dir
                / ".config"
                / "ccmonitor"
                / "profiles"
                / "aggressive.yaml"
            )
            assert profile_path == expected_path
            assert profile_path.exists()

            # Verify profile content
            with profile_path.open() as f:
                profile_data = yaml.safe_load(f)

            assert profile_data["default_level"] == "aggressive"
            assert profile_data["chunk_size"] == 2000

    def test_create_profile_write_error(self) -> None:
        """Test creating profile with write error."""
        with patch.object(
            Path, "open", side_effect=PermissionError("Permission denied")
        ):
            with pytest.raises(ValueError, match="Failed to create profile"):
                self.config_manager.create_profile("test", {})

    def test_load_profile(self) -> None:
        """Test loading configuration profile."""
        # First create a profile
        profile_dir = self.temp_dir / ".config" / "ccmonitor" / "profiles"
        profile_dir.mkdir(parents=True)
        profile_file = profile_dir / "test.yaml"

        profile_data = {
            "default_level": "light",
            "chunk_size": 500,
        }

        with profile_file.open("w") as f:
            yaml.dump(profile_data, f)

        # Load the profile
        with patch("pathlib.Path.home", return_value=self.temp_dir):
            self.config_manager.load_profile("test")

            assert self.config_manager.config.default_level == "light"
            assert self.config_manager.config.chunk_size == 500

    def test_load_profile_not_found(self) -> None:
        """Test loading non-existent profile."""
        with patch("pathlib.Path.home", return_value=self.temp_dir):
            with pytest.raises(FileNotFoundError, match="Profile not found"):
                self.config_manager.load_profile("nonexistent")

    def test_list_profiles(self) -> None:
        """Test listing available profiles."""
        # Create some test profiles
        profile_dir = self.temp_dir / ".config" / "ccmonitor" / "profiles"
        profile_dir.mkdir(parents=True)

        for name in ["aggressive", "light", "custom"]:
            profile_file = profile_dir / f"{name}.yaml"
            profile_file.write_text("test: value")

        with patch("pathlib.Path.home", return_value=self.temp_dir):
            profiles = self.config_manager.list_profiles()

            assert sorted(profiles) == ["aggressive", "custom", "light"]

    def test_list_profiles_no_dir(self) -> None:
        """Test listing profiles when directory doesn't exist."""
        with patch("pathlib.Path.home", return_value=self.temp_dir):
            profiles = self.config_manager.list_profiles()
            assert profiles == []

    def test_validate_config_valid(self) -> None:
        """Test validating valid configuration."""
        errors = self.config_manager.validate_config()
        assert errors == []

    def test_validate_config_invalid_level(self) -> None:
        """Test validation with invalid analysis level."""
        self.config_manager.config.default_level = "invalid"

        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any("Invalid default_level" in error for error in errors)

    def test_validate_config_invalid_workers(self) -> None:
        """Test validation with invalid parallel workers count."""
        self.config_manager.config.default_parallel_workers = 0

        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any(
            "Invalid default_parallel_workers" in error for error in errors
        )

    def test_validate_config_invalid_format(self) -> None:
        """Test validation with invalid output format."""
        self.config_manager.config.default_output_format = "invalid"

        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any(
            "Invalid default_output_format" in error for error in errors
        )

    def test_validate_config_low_memory_limit(self) -> None:
        """Test validation with low memory limit."""
        self.config_manager.config.memory_limit_mb = 32  # Below minimum

        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any("Memory limit too low" in error for error in errors)

    def test_validate_config_invalid_retention(self) -> None:
        """Test validation with invalid backup retention."""
        self.config_manager.config.backup_retention_days = 0

        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any("Invalid backup retention" in error for error in errors)

    def test_validate_config_invalid_schedule_policy(self) -> None:
        """Test validation with invalid schedule policy."""
        self.config_manager.config.schedule_policy = "invalid"

        errors = self.config_manager.validate_config()
        assert len(errors) > 0
        assert any("Invalid schedule_policy" in error for error in errors)

    def test_get_effective_config_no_overrides(self) -> None:
        """Test getting effective configuration without overrides."""
        result = self.config_manager.get_effective_config()

        assert isinstance(result, dict)
        assert result["default_level"] == "medium"

    def test_get_effective_config_with_overrides(self) -> None:
        """Test getting effective configuration with CLI overrides."""
        overrides = {
            "default_level": "aggressive",
            "chunk_size": 3000,
        }

        result = self.config_manager.get_effective_config(overrides)

        assert result["default_level"] == "aggressive"
        assert result["chunk_size"] == 3000
        # Original values should remain for non-overridden keys
        assert result["default_verbose"] is False


class TestConfigManagerPrivateMethods:
    """Test suite for ConfigManager private methods."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.config_manager = ConfigManager()

    def test_validate_analysis_level(self) -> None:
        """Test analysis level validation."""
        # Valid level
        self.config_manager.config.default_level = "medium"
        errors = self.config_manager._validate_analysis_level()
        assert errors == []

        # Invalid level
        self.config_manager.config.default_level = "invalid"
        errors = self.config_manager._validate_analysis_level()
        assert len(errors) == 1

    def test_validate_parallel_workers(self) -> None:
        """Test parallel workers validation."""
        # Valid count
        self.config_manager.config.default_parallel_workers = 4
        errors = self.config_manager._validate_parallel_workers()
        assert errors == []

        # Too low
        self.config_manager.config.default_parallel_workers = 0
        errors = self.config_manager._validate_parallel_workers()
        assert len(errors) == 1

        # Too high
        self.config_manager.config.default_parallel_workers = 20
        errors = self.config_manager._validate_parallel_workers()
        assert len(errors) == 1

    def test_validate_output_format(self) -> None:
        """Test output format validation."""
        # Valid format
        self.config_manager.config.default_output_format = "table"
        errors = self.config_manager._validate_output_format()
        assert errors == []

        # Invalid format
        self.config_manager.config.default_output_format = "invalid"
        errors = self.config_manager._validate_output_format()
        assert len(errors) == 1

    def test_validate_memory_limits(self) -> None:
        """Test memory limits validation."""
        # Valid limits
        self.config_manager.config.memory_limit_mb = 512
        self.config_manager.config.max_file_size_mb = 100
        errors = self.config_manager._validate_memory_limits()
        assert errors == []

        # Invalid memory limit
        self.config_manager.config.memory_limit_mb = 32
        errors = self.config_manager._validate_memory_limits()
        assert len(errors) >= 1

        # Invalid file size limit
        self.config_manager.config.max_file_size_mb = 0
        errors = self.config_manager._validate_memory_limits()
        assert len(errors) >= 1

    def test_validate_retention_policy(self) -> None:
        """Test retention policy validation."""
        # Valid retention
        self.config_manager.config.backup_retention_days = 30
        errors = self.config_manager._validate_retention_policy()
        assert errors == []

        # Invalid retention
        self.config_manager.config.backup_retention_days = 0
        errors = self.config_manager._validate_retention_policy()
        assert len(errors) == 1

    def test_validate_schedule_policy(self) -> None:
        """Test schedule policy validation."""
        # Valid policy
        self.config_manager.config.schedule_policy = "weekly"
        errors = self.config_manager._validate_schedule_policy()
        assert errors == []

        # Invalid policy
        self.config_manager.config.schedule_policy = "invalid"
        errors = self.config_manager._validate_schedule_policy()
        assert len(errors) == 1
