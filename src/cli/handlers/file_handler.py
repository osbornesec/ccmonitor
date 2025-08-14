"""File monitoring handler with state management."""

from __future__ import annotations

import json
import pickle
import time
import typing
from datetime import UTC, datetime
from pathlib import Path

import click
from colorama import Fore, Style

if typing.TYPE_CHECKING:
    from src.cli.types import MonitorConfig

# Note: imports from monitor are done locally to avoid circular imports


class FileMonitor:
    """Handles file monitoring operations with state management."""

    def __init__(
        self,
        config: MonitorConfig,
        *,
        verbose: bool = False,
    ) -> None:
        """Initialize file monitor with configuration."""
        self.config = config
        self.verbose = verbose
        # Place state file in monitor directory to avoid CWD conflicts
        monitor_dir = Path(str(self.config.directory)).expanduser().resolve()
        self.state_file = monitor_dir / ".ccmonitor_state.json"
        self.file_timestamps: dict[Path, float] = {}
        self.file_sizes: dict[Path, int] = {}
        self.malformed_lines_count = 0

    def execute_monitoring(self, monitor_dir: Path | None = None) -> None:
        """Execute monitoring based on configuration."""
        try:
            # Use provided monitor_dir or fallback to config directory
            if monitor_dir is None:
                monitor_dir = Path(str(self.config.directory)).expanduser()

            if self.config.since_last_run:
                self._load_previous_state()

            if self.config.process_all or self.config.since_last_run:
                self._process_existing_files(monitor_dir)
            else:
                self._start_realtime_monitoring(monitor_dir)

        except KeyboardInterrupt:
            click.echo(
                f"\n{Fore.YELLOW}Monitor stopped by user{Style.RESET_ALL}",
            )
            self._save_state()

    def _load_previous_state(self) -> None:
        """Load previous monitoring state."""
        self.file_timestamps, self.file_sizes = self._load_state()
        if not self.file_timestamps:
            click.echo(
                f"{Fore.YELLOW}No previous state found. "
                f"Use --process-all for initial run.{Style.RESET_ALL}",
            )

    def _process_existing_files(self, monitor_dir: Path) -> None:
        """Process existing files once."""
        current_files = self._scan_files(monitor_dir)

        for file_path in current_files:
            mtime, size = self._get_file_info(file_path)

            if self.config.process_all:
                self._process_entire_file(file_path)
            elif self._is_new_file(file_path):
                self._process_new_file(file_path)
            elif self._is_modified_file(file_path, mtime, size):
                self._process_modified_file(file_path, size)

            self.file_timestamps[file_path] = mtime
            self.file_sizes[file_path] = size

        self._save_state()
        click.echo(f"{Fore.GREEN}Processing complete{Style.RESET_ALL}")

    def _start_realtime_monitoring(self, monitor_dir: Path) -> None:
        """Start real-time monitoring loop."""
        while True:
            current_files = self._scan_files(monitor_dir)
            self._check_for_changes(current_files)
            self._check_for_deleted_files(current_files)
            self._save_state()
            time.sleep(self.config.interval)

    def _check_for_changes(self, current_files: set[Path]) -> None:
        """Check for file changes."""
        for file_path in current_files:
            mtime, size = self._get_file_info(file_path)

            if self._is_new_file(file_path):
                self._handle_new_file(file_path, mtime, size)
            elif self._is_modified_file(file_path, mtime, size):
                self._handle_modified_file(file_path, mtime, size)

    def _handle_new_file(
        self,
        file_path: Path,
        mtime: float,
        size: int,
    ) -> None:
        """Handle detection of new file."""
        click.echo(f"New file detected: {file_path}")
        self.file_timestamps[file_path] = mtime
        self.file_sizes[file_path] = size

    def _handle_modified_file(
        self,
        file_path: Path,
        mtime: float,
        size: int,
    ) -> None:
        """Handle detection of modified file."""
        click.echo(f"File modified: {file_path}")
        old_size = self.file_sizes.get(file_path, 0)

        if size > old_size:
            changes = self._read_new_content(file_path, old_size)
            if changes:
                self._write_changes(file_path, changes)
                click.echo(f"  Added {len(changes)} new entries")

        self.file_timestamps[file_path] = mtime
        self.file_sizes[file_path] = size

    def _check_for_deleted_files(self, current_files: set[Path]) -> None:
        """Check for deleted files."""
        tracked_files = set(self.file_timestamps.keys())
        deleted_files = tracked_files - current_files
        for deleted_file in deleted_files:
            click.echo(f"File deleted: {deleted_file}")
            del self.file_timestamps[deleted_file]
            if deleted_file in self.file_sizes:
                del self.file_sizes[deleted_file]

    def _process_entire_file(self, file_path: Path) -> None:
        """Process entire file."""
        changes = self._read_new_content(file_path, 0)
        if changes:
            self._write_changes(file_path, changes)
        click.echo(f"Processed: {file_path}")

    def _process_new_file(self, file_path: Path) -> None:
        """Process new file since last run."""
        changes = self._read_new_content(file_path, 0)
        if changes:
            self._write_changes(file_path, changes)
        click.echo(f"New file: {file_path}")

    def _process_modified_file(self, file_path: Path, size: int) -> None:
        """Process modified file."""
        old_size = self.file_sizes.get(file_path, 0)
        if size > old_size:
            changes = self._read_new_content(file_path, old_size)
            if changes:
                self._write_changes(file_path, changes)
        click.echo(f"Modified: {file_path}")

    def _is_new_file(self, file_path: Path) -> bool:
        """Check if file is new."""
        return file_path not in self.file_timestamps

    def _is_modified_file(
        self,
        file_path: Path,
        mtime: float,
        size: int,
    ) -> bool:
        """Check if file is modified."""
        return mtime > self.file_timestamps.get(
            file_path,
            0,
        ) or size != self.file_sizes.get(file_path, 0)

    def _scan_files(self, monitor_dir: Path) -> set[Path]:
        """Scan for files matching pattern."""
        files = set()
        for file_path in monitor_dir.rglob(self.config.pattern):
            if file_path.is_file():
                files.add(file_path)
        return files

    def _get_file_info(self, file_path: Path) -> tuple[float, int]:
        """Get file modification time and size."""
        try:
            stat = file_path.stat()
        except OSError:
            return 0, 0
        else:
            return stat.st_mtime, stat.st_size

    def _read_new_content(
        self,
        file_path: Path,
        old_size: int,
    ) -> list[dict[str, typing.Any]]:
        """Read new content from file."""
        try:
            with file_path.open(encoding="utf-8") as f:
                f.seek(old_size)
                return self._parse_file_lines(f)
        except OSError as e:
            if self.verbose:
                click.echo(f"Warning: Failed to read file content: {e}")
            return []

    def _parse_file_lines(
        self,
        file_handle: typing.TextIO,
    ) -> list[dict[str, typing.Any]]:
        """Parse lines from file handle."""
        new_lines = []
        for file_line in file_handle:
            stripped_line = file_line.strip()
            if stripped_line:
                parsed_line = self._parse_json_line(stripped_line)
                new_lines.append(parsed_line)
        return new_lines

    def _parse_json_line(self, line: str) -> dict[str, typing.Any]:
        """Parse single JSON line."""
        try:
            parsed_data: dict[str, typing.Any] = json.loads(line)
        except json.JSONDecodeError:
            self.malformed_lines_count += 1
            if self.verbose:
                truncated_line = line[:50]
                message = (
                    f"Warning: Malformed JSON (#{self.malformed_lines_count}): "
                    f"{truncated_line}..."
                )
                click.echo(message)
            return {"raw_line": line, "parse_error": True}
        else:
            return parsed_data

    def _write_changes(
        self,
        file_path: Path,
        changes: list[dict[str, typing.Any]],
    ) -> None:
        """Write changes to output file."""
        if not changes:
            return

        # Ensure parent directory exists
        self.config.output.parent.mkdir(parents=True, exist_ok=True)

        with self.config.output.open("a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"CHANGES DETECTED: {datetime.now(UTC).isoformat()}\n")
            f.write(f"FILE: {file_path}\n")
            f.write(f"NEW ENTRIES: {len(changes)}\n")
            f.write(f"{'=' * 80}\n")

            for i, change in enumerate(changes, 1):
                f.write(f"\n--- Entry {i} ---\n")
                f.write(
                    f"JSON Data: {json.dumps(change, indent=2, ensure_ascii=False)}\n",
                )

            f.write(f"\n{'=' * 80}\n\n")

    def _save_state(self) -> None:
        """Save monitoring state."""
        state = {
            "file_timestamps": {
                str(k): v for k, v in self.file_timestamps.items()
            },
            "file_sizes": {str(k): v for k, v in self.file_sizes.items()},
            "last_run": datetime.now(UTC).isoformat(),
        }
        try:
            with self.state_file.open("w") as f:
                json.dump(state, f)
        except (OSError, json.JSONDecodeError) as e:
            if self.verbose:
                click.echo(f"Warning: Failed to save state: {e}")

    def _load_state(self) -> tuple[dict[Path, float], dict[Path, int]]:
        """Load monitoring state."""
        # Try loading from JSON first
        json_result = self._load_json_state()
        if json_result is not None:
            return json_result

        # Fallback: migrate from legacy pickle format
        pickle_result = self._migrate_legacy_state()
        if pickle_result is not None:
            return pickle_result

        return {}, {}

    def _load_json_state(
        self,
    ) -> tuple[dict[Path, float], dict[Path, int]] | None:
        """Load state from JSON file."""
        try:
            if self.state_file.exists():
                with self.state_file.open() as f:
                    state = json.load(f)
                timestamps = {
                    Path(k): v
                    for k, v in state.get("file_timestamps", {}).items()
                }
                sizes = {
                    Path(k): v for k, v in state.get("file_sizes", {}).items()
                }
                return timestamps, sizes
        except (OSError, json.JSONDecodeError) as e:
            if self.verbose:
                click.echo(f"Warning: Failed to load JSON state: {e}")
        return None

    def _migrate_legacy_state(
        self,
    ) -> tuple[dict[Path, float], dict[Path, int]] | None:
        """Migrate legacy pickle state to JSON format."""
        # Check for legacy state file in the same directory as new state file
        monitor_dir = Path(str(self.config.directory)).expanduser().resolve()
        legacy_file = monitor_dir / ".ccmonitor_state.pkl"

        # Also check CWD for backward compatibility
        cwd_legacy_file = Path(".ccmonitor_state.pkl")

        # Prefer monitor directory, fall back to CWD
        if legacy_file.exists():
            source_file = legacy_file
        elif cwd_legacy_file.exists():
            source_file = cwd_legacy_file
        else:
            return None

        if self.verbose:
            click.echo(f"Migrating legacy state from: {source_file}")
            click.echo(f"Migrating legacy state to: {self.state_file}")

        old_state = self._load_pickle_file(source_file)
        if old_state is None:
            return None

        return self._convert_and_save_state(old_state)

    def _load_pickle_file(
        self,
        legacy_file: Path,
    ) -> dict[str, typing.Any] | None:
        """Load pickle file safely."""
        try:
            with legacy_file.open("rb") as f:
                return typing.cast(
                    "dict[str, typing.Any]",
                    pickle.load(f),  # noqa: S301
                )
        except (OSError, pickle.PickleError) as e:
            if self.verbose:
                click.echo(f"Warning: Failed to migrate legacy state: {e}")
            return None

    def _convert_and_save_state(
        self,
        old_state: dict[str, typing.Any],
    ) -> tuple[dict[Path, float], dict[Path, int]]:
        """Convert old state format and save as JSON."""
        timestamps = {
            Path(k): v for k, v in old_state.get("file_timestamps", {}).items()
        }
        sizes = {
            Path(k): v for k, v in old_state.get("file_sizes", {}).items()
        }

        # Save in new JSON format and update state
        self.file_timestamps, self.file_sizes = timestamps, sizes
        self._save_state()

        if self.verbose:
            click.echo("Migrated legacy state file to JSON format")

        return timestamps, sizes
