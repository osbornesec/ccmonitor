"""Shared fixtures for integration testing."""

from __future__ import annotations

import asyncio
import contextlib
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from hypothesis import strategies as st

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create temporary project directory with realistic structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create realistic project structure
        (project_path / "logs").mkdir()
        (project_path / "data").mkdir()
        (project_path / "output").mkdir()

        yield project_path


@pytest.fixture
def sample_jsonl_files(temp_project_dir: Path) -> list[Path]:
    """Create sample JSONL files with varied content."""
    files = []

    # Large conversation file
    large_file = temp_project_dir / "logs" / "large_conversation.jsonl"
    with large_file.open("w") as f:
        for i in range(1000):
            entry = {
                "type": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i} with some content",
                "timestamp": f"2024-01-{(i % 30) + 1:02d}T10:00:00Z",
                "tokens": {"input": 50 + i, "output": 30 + i},
            }
            f.write(json.dumps(entry) + "\n")
    files.append(large_file)

    # Malformed JSONL file
    malformed_file = temp_project_dir / "logs" / "malformed.jsonl"
    with malformed_file.open("w") as f:
        f.write('{"valid": "json"}\n')
        f.write("invalid json line\n")
        f.write('{"partial": \n')
        f.write('{"another": "valid"}\n')
    files.append(malformed_file)

    # Empty file
    empty_file = temp_project_dir / "logs" / "empty.jsonl"
    empty_file.touch()
    files.append(empty_file)

    # Binary file (should be ignored)
    binary_file = temp_project_dir / "logs" / "binary.jsonl"
    with binary_file.open("wb") as f:
        f.write(b"\x00\x01\x02\x03")
    files.append(binary_file)

    return files


@pytest.fixture
def performance_test_data() -> dict[str, list[dict[str, object]]]:
    """Generate test data for performance testing."""
    return {
        "small_dataset": [{"id": i, "data": f"test_{i}"} for i in range(100)],
        "medium_dataset": [
            {"id": i, "data": f"test_{i}" * 10} for i in range(1000)
        ],
        "large_dataset": [
            {"id": i, "data": f"test_{i}" * 100} for i in range(5000)
        ],
    }


@pytest.fixture
def hypothesis_jsonl_strategy() -> object:
    """Generate hypothesis strategy for JSONL content."""
    return st.lists(
        st.fixed_dictionaries(
            {
                "type": st.sampled_from(["user", "assistant", "system"]),
                "content": st.text(min_size=1, max_size=1000),
                "timestamp": st.datetimes().map(lambda dt: dt.isoformat()),
                "tokens": st.dictionaries(
                    st.sampled_from(["input", "output", "total"]),
                    st.integers(min_value=1, max_value=10000),
                    min_size=1,
                    max_size=3,
                ),
            },
        ),
        min_size=0,
        max_size=100,
    )


class ErrorInjectionManager:
    """Manage error injection for testing failure scenarios."""

    def __init__(self) -> None:
        """Initialize error injection manager."""
        self.active_errors: set[tuple[str, Path | None]] = set()

    def inject_file_permission_error(self, file_path: Path) -> None:
        """Make file unreadable."""
        file_path.chmod(0o000)
        self.active_errors.add(("permission", file_path))

    def inject_disk_full_error(self) -> None:
        """Simulate disk full condition."""
        self.active_errors.add(("disk_full", None))

    def inject_memory_pressure(self) -> None:
        """Simulate memory pressure."""
        self.active_errors.add(("memory", None))

    def clear_errors(self) -> None:
        """Clear all injected errors."""
        for error_type, path in self.active_errors:
            if error_type == "permission" and path:
                with contextlib.suppress(FileNotFoundError):
                    path.chmod(0o644)
        self.active_errors.clear()

    def __del__(self) -> None:
        """Clean up errors on deletion."""
        self.clear_errors()


@pytest.fixture
def error_injection_manager() -> Generator[ErrorInjectionManager, None, None]:
    """Create error injection manager for testing failure scenarios."""
    manager = ErrorInjectionManager()
    yield manager
    manager.clear_errors()


@pytest.fixture
async def async_event_loop() -> (
    AsyncGenerator[asyncio.AbstractEventLoop, None]
):
    """Provide async event loop for integration tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()
