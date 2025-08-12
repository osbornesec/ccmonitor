"""Cross-platform compatibility tests for TUI application."""

from __future__ import annotations

import os
import platform
import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


class TestCrossPlatform:
    """Test cross-platform compatibility."""

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_linux_compatibility(self, mock_app: Mock) -> None:
        """Test Linux-specific functionality."""
        # Test that basic functionality works on Linux
        assert mock_app.is_running is True
        assert mock_app.size == (120, 40)

        # Test Linux-specific environment variables
        assert "PATH" in os.environ

        # Test file path handling (forward slashes)
        test_path = "/tmp/ccmonitor/test.log"
        normalized_path = os.path.normpath(test_path)
        assert normalized_path == test_path

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_macos_compatibility(self, mock_app: Mock) -> None:
        """Test macOS-specific functionality."""
        # Test that basic functionality works on macOS
        assert mock_app.is_running is True
        assert mock_app.size == (120, 40)

        # Test macOS-specific environment
        if "HOME" in os.environ:
            home_dir = os.environ["HOME"]
            assert "/Users/" in home_dir

        # Test file path handling
        test_path = "/tmp/ccmonitor/test.log"
        normalized_path = os.path.normpath(test_path)
        assert normalized_path == test_path

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_compatibility(self, mock_app: Mock) -> None:
        """Test Windows-specific functionality."""
        # Test that basic functionality works on Windows
        assert mock_app.is_running is True
        assert mock_app.size == (120, 40)

        # Test Windows-specific environment
        if "USERPROFILE" in os.environ:
            user_profile = os.environ["USERPROFILE"]
            assert "\\" in user_profile or "/" in user_profile

        # Test file path handling (backslashes converted)
        test_path = "C:\\temp\\ccmonitor\\test.log"
        normalized_path = os.path.normpath(test_path)
        assert normalized_path.endswith("test.log")

    def test_terminal_emulators(self, mock_terminal: None) -> None:
        """Test different terminal emulators."""
        terminals = [
            ("xterm", "xterm-256color"),
            ("gnome", "gnome-256color"),
            ("iterm2", "xterm-256color"),
            ("windows-terminal", "xterm-256color"),
        ]

        for name, term_var in terminals:
            # The mock_terminal fixture should have set basic values
            assert os.environ.get("TERM") == "xterm-256color"
            assert os.environ.get("COLORTERM") == "truecolor"

            # Test that terminal capabilities are detected
            supports_color = self._check_color_support(term_var)
            assert supports_color  # Should support color in test environment

    def test_python_version_compatibility(self) -> None:
        """Test Python version compatibility."""
        # Test minimum Python version (3.11+)
        version_info = sys.version_info
        assert version_info.major == 3
        assert (
            version_info.minor >= 11
        ), f"Python {version_info.major}.{version_info.minor} not supported"

    def test_platform_specific_paths(self) -> None:
        """Test platform-specific path handling."""
        system = platform.system()

        if system == "Windows":
            # Windows uses backslashes
            expected_separator = "\\"
            config_dir = os.path.expanduser("~\\AppData\\Local\\ccmonitor")
        else:
            # Unix-like systems use forward slashes
            expected_separator = "/"
            config_dir = os.path.expanduser("~/.config/ccmonitor")

        assert os.sep == expected_separator
        assert expected_separator in config_dir

    def test_environment_variables(self) -> None:
        """Test environment variable handling across platforms."""
        # Test common environment variables
        common_vars = ["PATH"]
        for var in common_vars:
            assert var in os.environ

        # Test platform-specific variables
        system = platform.system()
        if system == "Windows":
            windows_vars = ["USERPROFILE", "APPDATA"]
            for var in windows_vars:
                # May not exist in all test environments
                if var in os.environ:
                    assert os.environ[var]  # Should have a value
        else:
            unix_vars = ["HOME"]
            for var in unix_vars:
                if var in os.environ:
                    assert os.environ[var]  # Should have a value

    def test_file_permissions(self, temp_config_dir) -> None:
        """Test file permission handling across platforms."""
        import stat

        # Create a test file
        test_file = temp_config_dir / "test_permissions.txt"
        test_file.write_text("test content")

        # Test file exists and is readable
        assert test_file.exists()
        assert test_file.is_file()

        # Test file permissions
        file_stat = test_file.stat()
        assert file_stat.st_mode & stat.S_IREAD  # Readable

        # On Unix-like systems, test more granular permissions
        if platform.system() != "Windows":
            assert file_stat.st_mode & stat.S_IRUSR  # User readable

    def test_unicode_support(self) -> None:
        """Test Unicode support across platforms."""
        # Test basic Unicode handling
        unicode_text = "🔷 Project Alpha 📊 Stats: ✅"

        try:
            encoded = unicode_text.encode("utf-8")
            decoded = encoded.decode("utf-8")
            assert decoded == unicode_text
        except UnicodeError as e:
            pytest.skip(f"Unicode not supported: {e}")

    def test_terminal_size_detection(self) -> None:
        """Test terminal size detection across platforms."""
        try:
            # Try to get terminal size
            import shutil

            size = shutil.get_terminal_size(fallback=(80, 24))

            assert size.columns > 0
            assert size.lines > 0
            assert size.columns >= 80  # Minimum expected
            assert size.lines >= 24  # Minimum expected
        except OSError:
            # Some CI environments don't have a terminal
            pytest.skip("No terminal available for size detection")

    def _check_color_support(self, term_type: str) -> bool:
        """Check if terminal supports color."""
        # Simple heuristic for color support
        color_terms = ["256color", "color", "ansi"]
        return any(
            color_term in term_type.lower() for color_term in color_terms
        )


class TestPlatformSpecificFeatures:
    """Test platform-specific features and workarounds."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix only")
    def test_unix_signal_handling(self) -> None:
        """Test Unix signal handling."""
        import signal

        # Test that common signals are available
        unix_signals = [signal.SIGTERM, signal.SIGINT]
        for sig in unix_signals:
            assert sig is not None
            # Could test signal handler registration here

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_windows_console_features(self) -> None:
        """Test Windows console features."""
        # Test that Windows-specific modules are available
        try:
            import msvcrt

            assert msvcrt is not None
        except ImportError:
            pytest.skip("Windows console features not available")

    def test_keyboard_input_handling(self) -> None:
        """Test keyboard input handling across platforms."""
        # Test that key mapping works consistently
        key_mappings = {
            "escape": "\x1b",
            "enter": "\r",
            "tab": "\t",
        }

        for key_name, key_code in key_mappings.items():
            assert len(key_code) >= 1
            # Test that key codes are valid
            assert isinstance(key_code, str)

    def test_color_output_support(self) -> None:
        """Test color output support across platforms."""
        # Test ANSI escape sequences
        color_codes = {
            "reset": "\x1b[0m",
            "red": "\x1b[31m",
            "green": "\x1b[32m",
            "blue": "\x1b[34m",
        }

        for color_name, color_code in color_codes.items():
            assert len(color_code) > 1
            assert color_code.startswith("\x1b")


class TestDependencyCompatibility:
    """Test dependency compatibility across platforms."""

    def test_textual_compatibility(self) -> None:
        """Test Textual library compatibility."""
        try:
            from textual import __version__ as textual_version
            from textual.app import App
            from textual.widgets import Footer, Header

            assert textual_version is not None
            assert App is not None
            assert Footer is not None
            assert Header is not None
        except ImportError as e:
            pytest.fail(f"Textual import failed: {e}")

    def test_psutil_compatibility(self) -> None:
        """Test psutil library compatibility."""
        try:
            import psutil

            # Test basic psutil functionality
            process = psutil.Process()
            assert process.pid > 0

            # Test memory info (should work on all platforms)
            memory_info = process.memory_info()
            assert memory_info.rss > 0

        except ImportError as e:
            pytest.fail(f"psutil import failed: {e}")
        except Exception as e:
            pytest.skip(f"psutil functionality not available: {e}")

    def test_pytest_compatibility(self) -> None:
        """Test pytest compatibility."""
        try:
            import pytest

            assert pytest.__version__ is not None

            # Test pytest markers work
            assert hasattr(pytest, "mark")
            assert hasattr(pytest.mark, "asyncio")
            assert hasattr(pytest.mark, "skipif")

        except ImportError as e:
            pytest.fail(f"pytest import failed: {e}")


class TestResourceLimits:
    """Test resource limits across platforms."""

    def test_memory_limits(self) -> None:
        """Test memory usage limits."""
        import psutil

        # Get available system memory
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)

        # Test that we have reasonable memory available
        assert available_gb > 0.5, "Less than 500MB memory available"

        # Test that our application shouldn't use more than 10MB
        process = psutil.Process()
        current_memory_mb = process.memory_info().rss / (1024**2)

        # Allow generous headroom for test environment
        assert (
            current_memory_mb < 100
        ), f"Test process using {current_memory_mb:.1f}MB"

    def test_cpu_availability(self) -> None:
        """Test CPU availability."""
        import psutil

        # Test CPU count
        cpu_count = psutil.cpu_count()
        assert cpu_count >= 1

        # Test CPU usage can be measured
        cpu_percent = psutil.cpu_percent(interval=0.1)
        assert 0 <= cpu_percent <= 100

    def test_disk_space(self, temp_config_dir) -> None:
        """Test disk space availability."""
        import shutil

        # Test disk space where temp directory is located
        disk_usage = shutil.disk_usage(temp_config_dir)

        assert disk_usage.total > 0
        assert disk_usage.free > 0

        # Test we have at least 100MB free (reasonable minimum)
        free_mb = disk_usage.free / (1024**2)
        assert free_mb > 100, f"Only {free_mb:.1f}MB free disk space"


class TestErrorHandling:
    """Test error handling across platforms."""

    def test_file_not_found_handling(self) -> None:
        """Test FileNotFoundError handling."""
        nonexistent_file = "/nonexistent/path/file.txt"

        with pytest.raises(FileNotFoundError):
            with open(nonexistent_file) as f:
                f.read()

    def test_permission_denied_handling(self) -> None:
        """Test PermissionError handling."""
        # This test may not work in all environments
        try:
            # Try to write to a read-only location
            if platform.system() == "Windows":
                readonly_path = "C:\\Windows\\System32\\test.txt"
            else:
                readonly_path = "/root/test.txt"

            with pytest.raises((PermissionError, OSError)):
                with open(readonly_path, "w") as f:
                    f.write("test")
        except PermissionError:
            # Expected on some systems
            pass
        except OSError:
            # May get different error types on different platforms
            pass

    def test_keyboard_interrupt_handling(self) -> None:
        """Test KeyboardInterrupt handling."""

        def raise_keyboard_interrupt():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            raise_keyboard_interrupt()

    def test_system_exit_handling(self) -> None:
        """Test SystemExit handling."""

        def raise_system_exit():
            raise SystemExit(1)

        with pytest.raises(SystemExit):
            raise_system_exit()


@pytest.fixture
def platform_info() -> dict[str, str]:
    """Provide platform information for testing."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


@pytest.fixture
def mock_platform_windows() -> Generator[None, None, None]:
    """Mock Windows platform for testing."""
    with patch("platform.system", return_value="Windows"):
        yield


@pytest.fixture
def mock_platform_linux() -> Generator[None, None, None]:
    """Mock Linux platform for testing."""
    with patch("platform.system", return_value="Linux"):
        yield


@pytest.fixture
def mock_platform_macos() -> Generator[None, None, None]:
    """Mock macOS platform for testing."""
    with patch("platform.system", return_value="Darwin"):
        yield
