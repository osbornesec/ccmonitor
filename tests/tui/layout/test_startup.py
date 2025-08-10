"""Tests for startup validation system."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

from src.tui.utils.startup import StartupValidator

# Test constants
MIN_TERMINAL_WIDTH = 80
MIN_TERMINAL_HEIGHT = 24
MOCK_LARGE_WIDTH = 120
MOCK_LARGE_HEIGHT = 40
MOCK_SMALL_WIDTH = 60
MOCK_SMALL_HEIGHT = 20
EXPECTED_TWO_ERRORS = 2


class TestStartupValidator:
    """Test StartupValidator functionality."""

    def test_initialization(self) -> None:
        """Test startup validator initialization."""
        validator = StartupValidator()

        # Test constants
        assert validator.MIN_TERMINAL_WIDTH == MIN_TERMINAL_WIDTH
        assert validator.MIN_TERMINAL_HEIGHT == MIN_TERMINAL_HEIGHT

        # Test initial state
        assert isinstance(validator.errors, list)
        assert len(validator.errors) == 0

    def test_validate_terminal_capabilities_success(self) -> None:
        """Test successful terminal validation."""
        validator = StartupValidator()

        # Mock terminal size to be large enough
        mock_size = Mock()
        mock_size.columns = MOCK_LARGE_WIDTH
        mock_size.lines = MOCK_LARGE_HEIGHT

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is True
            assert len(validator.errors) == 0

    def test_validate_terminal_capabilities_too_small(self) -> None:
        """Test terminal validation with too small terminal."""
        validator = StartupValidator()

        # Mock terminal size to be too small
        mock_size = Mock()
        mock_size.columns = MOCK_SMALL_WIDTH
        mock_size.lines = MOCK_SMALL_HEIGHT

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is False
            assert len(validator.errors) == 1
            assert "Terminal too small" in validator.errors[0]
            assert (
                f"{MIN_TERMINAL_WIDTH}x{MIN_TERMINAL_HEIGHT}"
                in validator.errors[0]
            )

    def test_validate_terminal_capabilities_width_too_small(self) -> None:
        """Test terminal validation with width too small but height OK."""
        validator = StartupValidator()

        # Mock terminal size with small width but OK height
        mock_size = Mock()
        mock_size.columns = MOCK_SMALL_WIDTH
        mock_size.lines = MOCK_LARGE_HEIGHT

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is False
            assert len(validator.errors) == 1
            assert "Terminal too small" in validator.errors[0]

    def test_validate_terminal_capabilities_height_too_small(self) -> None:
        """Test terminal validation with height too small but width OK."""
        validator = StartupValidator()

        # Mock terminal size with OK width but small height
        mock_size = Mock()
        mock_size.columns = MOCK_LARGE_WIDTH
        mock_size.lines = MOCK_SMALL_HEIGHT

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is False
            assert len(validator.errors) == 1
            assert "Terminal too small" in validator.errors[0]

    def test_validate_terminal_capabilities_exact_minimum(self) -> None:
        """Test terminal validation with exact minimum size."""
        validator = StartupValidator()

        # Mock terminal size to be exactly minimum
        mock_size = Mock()
        mock_size.columns = MIN_TERMINAL_WIDTH
        mock_size.lines = MIN_TERMINAL_HEIGHT

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is True
            assert len(validator.errors) == 0

    def test_validate_terminal_capabilities_os_error(self) -> None:
        """Test terminal validation when OS error occurs."""
        validator = StartupValidator()

        with patch(
            "shutil.get_terminal_size",
            side_effect=OSError("No terminal"),
        ):
            result = validator.validate_terminal_capabilities()

            assert result is False
            assert len(validator.errors) == 1
            assert "Unable to determine terminal size" in validator.errors[0]

    def test_validate_environment_success(self) -> None:
        """Test successful environment validation."""
        validator = StartupValidator()

        with patch.dict(os.environ, {"TERM": "xterm-256color"}):
            result = validator.validate_environment()

            assert result is True
            assert len(validator.errors) == 0

    def test_validate_environment_no_term(self) -> None:
        """Test environment validation when TERM is not set."""
        validator = StartupValidator()

        with patch.dict(os.environ, {}, clear=True):
            result = validator.validate_environment()

            assert result is False
            assert len(validator.errors) == 1
            assert "TERM environment variable not set" in validator.errors[0]

    def test_validate_environment_empty_term(self) -> None:
        """Test environment validation when TERM is empty."""
        validator = StartupValidator()

        with patch.dict(os.environ, {"TERM": ""}):
            result = validator.validate_environment()

            assert result is False
            assert len(validator.errors) == 1
            assert "TERM environment variable not set" in validator.errors[0]

    def test_validate_all_success(self) -> None:
        """Test successful validation of all components."""
        validator = StartupValidator()

        # Mock successful terminal size
        mock_size = Mock()
        mock_size.columns = MOCK_LARGE_WIDTH
        mock_size.lines = MOCK_LARGE_HEIGHT

        with (
            patch("shutil.get_terminal_size", return_value=mock_size),
            patch.dict(os.environ, {"TERM": "xterm-256color"}),
        ):

            result = validator.validate_all()

            assert result is True
            assert len(validator.errors) == 0

    def test_validate_all_terminal_failure(self) -> None:
        """Test validation when terminal check fails."""
        validator = StartupValidator()

        # Mock small terminal size
        mock_size = Mock()
        mock_size.columns = MOCK_SMALL_WIDTH
        mock_size.lines = MOCK_SMALL_HEIGHT

        with (
            patch("shutil.get_terminal_size", return_value=mock_size),
            patch.dict(os.environ, {"TERM": "xterm-256color"}),
        ):

            result = validator.validate_all()

            assert result is False
            assert len(validator.errors) == 1
            assert "Terminal too small" in validator.errors[0]

    def test_validate_all_environment_failure(self) -> None:
        """Test validation when environment check fails."""
        validator = StartupValidator()

        # Mock good terminal size
        mock_size = Mock()
        mock_size.columns = MOCK_LARGE_WIDTH
        mock_size.lines = MOCK_LARGE_HEIGHT

        with (
            patch("shutil.get_terminal_size", return_value=mock_size),
            patch.dict(os.environ, {}, clear=True),
        ):

            result = validator.validate_all()

            assert result is False
            assert len(validator.errors) == 1
            assert "TERM environment variable not set" in validator.errors[0]

    def test_validate_all_both_failures(self) -> None:
        """Test validation when both checks fail."""
        validator = StartupValidator()

        # Mock small terminal size
        mock_size = Mock()
        mock_size.columns = MOCK_SMALL_WIDTH
        mock_size.lines = MOCK_SMALL_HEIGHT

        with (
            patch("shutil.get_terminal_size", return_value=mock_size),
            patch.dict(os.environ, {}, clear=True),
        ):

            result = validator.validate_all()

            assert result is False
            # Should have both errors
            assert len(validator.errors) >= EXPECTED_TWO_ERRORS
            error_messages = " ".join(validator.errors)
            assert "Terminal too small" in error_messages
            assert "TERM environment variable not set" in error_messages

    def test_validate_all_clears_previous_errors(self) -> None:
        """Test that validate_all clears previous errors."""
        validator = StartupValidator()

        # Add some initial errors
        validator.errors.append("Previous error")
        validator.errors.append("Another error")
        assert len(validator.errors) == EXPECTED_TWO_ERRORS

        # Mock successful validation
        mock_size = Mock()
        mock_size.columns = MOCK_LARGE_WIDTH
        mock_size.lines = MOCK_LARGE_HEIGHT

        with (
            patch("shutil.get_terminal_size", return_value=mock_size),
            patch.dict(os.environ, {"TERM": "xterm-256color"}),
        ):

            result = validator.validate_all()

            assert result is True
            assert len(validator.errors) == 0

    def test_get_errors(self) -> None:
        """Test getting validation errors."""
        validator = StartupValidator()

        # Add some errors
        error1 = "First error"
        error2 = "Second error"
        validator.errors.append(error1)
        validator.errors.append(error2)

        # Get errors
        errors = validator.get_errors()

        # Should return copy of errors
        assert errors == [error1, error2]
        assert errors is not validator.errors  # Should be a copy

        # Modifying returned list shouldn't affect original
        errors.append("Third error")
        assert (
            len(validator.errors) == EXPECTED_TWO_ERRORS
        )  # Original unchanged

    def test_get_errors_empty(self) -> None:
        """Test getting errors when none exist."""
        validator = StartupValidator()

        errors = validator.get_errors()
        assert errors == []
        assert errors is not validator.errors  # Should be a copy


class TestStartupValidatorEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiple_validators_independence(self) -> None:
        """Test that multiple validators are independent."""
        validator1 = StartupValidator()
        validator2 = StartupValidator()

        # Add error to first validator
        validator1.errors.append("Error in validator 1")

        # Second validator should be unaffected
        assert len(validator1.errors) == 1
        assert len(validator2.errors) == 0

    def test_terminal_size_zero_dimensions(self) -> None:
        """Test terminal validation with zero dimensions."""
        validator = StartupValidator()

        # Mock terminal size with zero dimensions
        mock_size = Mock()
        mock_size.columns = 0
        mock_size.lines = 0

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is False
            assert len(validator.errors) == 1
            assert "Terminal too small" in validator.errors[0]

    def test_terminal_size_negative_dimensions(self) -> None:
        """Test terminal validation with negative dimensions."""
        validator = StartupValidator()

        # Mock terminal size with negative dimensions
        mock_size = Mock()
        mock_size.columns = -1
        mock_size.lines = -1

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is False
            assert len(validator.errors) == 1
            assert "Terminal too small" in validator.errors[0]

    def test_very_large_terminal_size(self) -> None:
        """Test terminal validation with very large dimensions."""
        validator = StartupValidator()

        # Mock very large terminal size
        large_size = 10000
        mock_size = Mock()
        mock_size.columns = large_size
        mock_size.lines = large_size

        with patch("shutil.get_terminal_size", return_value=mock_size):
            result = validator.validate_terminal_capabilities()

            assert result is True
            assert len(validator.errors) == 0

    def test_environment_with_special_term_values(self) -> None:
        """Test environment validation with various TERM values."""
        validator = StartupValidator()

        special_terms = [
            "xterm",
            "xterm-256color",
            "screen",
            "screen-256color",
            "tmux",
            "tmux-256color",
            "dumb",
        ]

        for term_value in special_terms:
            validator.errors.clear()  # Clear previous errors

            with patch.dict(os.environ, {"TERM": term_value}):
                result = validator.validate_environment()

                assert result is True, f"Failed for TERM={term_value}"
                assert len(validator.errors) == 0

    def test_repeated_validations(self) -> None:
        """Test running validations multiple times."""
        validator = StartupValidator()

        # Mock successful conditions
        mock_size = Mock()
        mock_size.columns = MOCK_LARGE_WIDTH
        mock_size.lines = MOCK_LARGE_HEIGHT

        with (
            patch("shutil.get_terminal_size", return_value=mock_size),
            patch.dict(os.environ, {"TERM": "xterm-256color"}),
        ):

            # Run validation multiple times
            for _ in range(5):
                result = validator.validate_all()
                assert result is True
                assert len(validator.errors) == 0

    def test_error_accumulation_without_clear(self) -> None:
        """Test error accumulation when not using validate_all."""
        validator = StartupValidator()

        # Run individual validations without clearing
        with (
            patch("shutil.get_terminal_size", side_effect=OSError),
            patch.dict(os.environ, {}, clear=True),
        ):

            # Run terminal validation - adds error
            validator.validate_terminal_capabilities()
            assert len(validator.errors) == 1

            # Run environment validation - adds another error
            validator.validate_environment()
            assert len(validator.errors) == EXPECTED_TWO_ERRORS

            # Errors should accumulate
            assert "Unable to determine terminal size" in validator.errors[0]
            assert "TERM environment variable not set" in validator.errors[1]

    def test_constants_are_class_attributes(self) -> None:
        """Test that min dimensions are class attributes."""
        # Should be accessible as class attributes
        assert StartupValidator.MIN_TERMINAL_WIDTH == MIN_TERMINAL_WIDTH
        assert StartupValidator.MIN_TERMINAL_HEIGHT == MIN_TERMINAL_HEIGHT

        # Should also be accessible from instances
        validator = StartupValidator()
        assert validator.MIN_TERMINAL_WIDTH == MIN_TERMINAL_WIDTH
        assert validator.MIN_TERMINAL_HEIGHT == MIN_TERMINAL_HEIGHT
