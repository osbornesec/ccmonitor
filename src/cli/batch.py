"""Batch processing system for ccmonitor CLI.

Analysis-focused batch operations with parallel processing.
"""

import csv
import json
import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from src.jsonl_analysis.analyzer import ConversationFlowAnalyzer, JSONLAnalyzer

from .constants import (
    DEFAULT_PARALLEL_WORKERS,
    FILENAME_TRUNCATE_LENGTH,
    MAX_FILENAME_DISPLAY_LENGTH,
)
from .utils import format_duration, format_size, is_jsonl_file

logger = logging.getLogger(__name__)


@dataclass
class BatchAnalysisResult:
    """Results from batch analysis processing."""

    directory: Path
    pattern: str
    recursive: bool
    files_analyzed: list[Path]
    failed_files: list[dict[str, Any]]
    analysis_results: list[dict[str, Any]]
    start_time: float
    end_time: float
    total_files_discovered: int = 0

    @property
    def processing_time(self) -> float:
        """Calculate total processing time."""
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = len(self.files_analyzed) + len(self.failed_files)
        return len(self.files_analyzed) / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            "directory": str(self.directory),
            "pattern": self.pattern,
            "recursive": self.recursive,
            "files_analyzed": [str(f) for f in self.files_analyzed],
            "failed_files": self.failed_files,
            "analysis_results": self.analysis_results,
            "processing_time": self.processing_time,
            "success_rate": self.success_rate,
            "total_files_discovered": self.total_files_discovered,
            "summary": {
                "total_files_found": self.total_files_discovered,
                "files_analyzed_successfully": len(self.files_analyzed),
                "files_failed": len(self.failed_files),
                "success_rate_percent": self.success_rate * 100,
                "average_processing_time_per_file": (
                    self.processing_time / len(self.files_analyzed)
                    if self.files_analyzed
                    else 0
                ),
            },
        }


class BatchProcessor:
    """Batch processor for analyzing multiple JSONL files.

    Focuses on analysis only - no file modification.
    """

    def __init__(
        self,
        directory: Path,
        pattern: str = "*.jsonl",
        *,
        recursive: bool = False,
        parallel_workers: int = DEFAULT_PARALLEL_WORKERS,
        verbose: bool = False,
    ) -> None:
        """Initialize batch processor.

        Args:
            directory: Root directory to process
            pattern: File pattern to match
            recursive: Whether to search recursively
            parallel_workers: Number of parallel processing threads
            verbose: Enable verbose logging

        """
        self.directory = Path(directory)
        self.pattern = pattern
        self.recursive = recursive
        self.parallel_workers = min(parallel_workers, 8)  # Cap at 8 workers
        self.verbose = verbose

        # Thread safety
        self._lock = Lock()
        self._analyzer = JSONLAnalyzer()

        if verbose:
            logger.setLevel(logging.DEBUG)

    def discover_files(self) -> list[Path]:
        """Discover JSONL files to process.

        Returns:
            List of JSONL file paths

        """
        files = self._find_files_by_pattern()
        files = self._filter_valid_jsonl_files(files)
        files = self._sort_files_by_size(files)

        if self.verbose:
            logger.debug("Discovered %d JSONL files", len(files))

        return files

    def _find_files_by_pattern(self) -> list[Path]:
        """Find files matching the pattern."""
        if self.recursive:
            return list(self.directory.rglob(self.pattern))
        return list(self.directory.glob(self.pattern))

    def _filter_valid_jsonl_files(self, files: list[Path]) -> list[Path]:
        """Filter for valid JSONL files."""
        return [f for f in files if f.is_file() and is_jsonl_file(f)]

    def _sort_files_by_size(self, files: list[Path]) -> list[Path]:
        """Sort files by size (process smaller files first)."""
        files.sort(key=lambda x: x.stat().st_size)
        return files

    def analyze_single_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze a single JSONL file.

        Args:
            file_path: Path to JSONL file

        Returns:
            Analysis results dictionary

        """
        start_time = time.time()

        try:
            # Parse the file
            messages = self._analyzer.parse_jsonl_file(file_path)

            # Get basic file stats
            file_stat = file_path.stat()

            # Analyze conversation structure
            flow_analyzer = ConversationFlowAnalyzer()
            conversation_info = flow_analyzer.map_conversation_dependencies(messages)

            # Get message type distribution
            message_types: dict[str, int] = {}
            for message in messages:
                msg_type = message.get("type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1

            # Calculate processing time
            processing_time = time.time() - start_time

            return {
                "file_path": str(file_path),
                "file_size_bytes": file_stat.st_size,
                "file_size_formatted": format_size(file_stat.st_size),
                "total_messages": len(messages),
                "message_types": message_types,
                "conversation_depth": conversation_info.get("max_depth", 0),
                "conversation_chains": conversation_info.get("chain_count", 0),
                "processing_time": processing_time,
                "processing_time_formatted": format_duration(processing_time),
                "status": "success",
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.exception("Failed to analyze %s", file_path)

            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
            }

    def analyze_directory(self) -> BatchAnalysisResult:
        """Analyze all JSONL files in the directory.

        Returns:
            BatchAnalysisResult with comprehensive analysis

        """
        start_time = time.time()
        files_to_analyze = self.discover_files()

        if not files_to_analyze:
            return self._create_empty_result(start_time)

        successful_results, failed_files = self._process_files_in_parallel(
            files_to_analyze,
        )
        end_time = time.time()

        return self._create_batch_result(
            start_time,
            end_time,
            successful_results,
            failed_files,
            len(files_to_analyze),
        )

    def _create_empty_result(self, start_time: float) -> BatchAnalysisResult:
        """Create empty result when no files are found."""
        logger.warning("No JSONL files found in %s", self.directory)
        return BatchAnalysisResult(
            directory=self.directory,
            pattern=self.pattern,
            recursive=self.recursive,
            files_analyzed=[],
            failed_files=[],
            analysis_results=[],
            start_time=start_time,
            end_time=time.time(),
            total_files_discovered=0,
        )

    def _process_files_in_parallel(
        self, files: list[Path],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process files using thread pool executor."""
        successful_results: list[dict[str, Any]] = []
        failed_files: list[dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            future_to_file = {
                executor.submit(self.analyze_single_file, file_path): file_path
                for file_path in files
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                self._process_completed_task(
                    future, file_path, successful_results, failed_files,
                )

        return successful_results, failed_files

    def _process_completed_task(
        self,
        future: Future[dict[str, Any]],
        file_path: Path,
        successful_results: list[dict[str, Any]],
        failed_files: list[dict[str, Any]],
    ) -> None:
        """Process a completed analysis task."""
        try:
            result = future.result()
            if result["status"] == "success":
                successful_results.append(result)
                if self.verbose:
                    logger.info("✓ Analyzed %s", file_path)
            else:
                failed_files.append(result)
                logger.error(
                    "✗ Failed to analyze %s: %s", file_path, result.get("error"),
                )
        except Exception as e:
            error_result = {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e),
            }
            failed_files.append(error_result)
            logger.exception("✗ Exception analyzing %s", file_path)

    def _create_batch_result(
        self,
        start_time: float,
        end_time: float,
        successful_results: list[dict[str, Any]],
        failed_files: list[dict[str, Any]],
        total_files: int,
    ) -> BatchAnalysisResult:
        """Create the final batch analysis result."""
        return BatchAnalysisResult(
            directory=self.directory,
            pattern=self.pattern,
            recursive=self.recursive,
            files_analyzed=[
                Path(r["file_path"])
                for r in successful_results
                if r["status"] == "success"
            ],
            failed_files=failed_files,
            analysis_results=successful_results,
            start_time=start_time,
            end_time=end_time,
            total_files_discovered=total_files,
        )

    def export_results(
        self,
        result: BatchAnalysisResult,
        output_path: Path,
        format_type: str = "json",
    ) -> None:
        """Export analysis results to file.

        Args:
            result: BatchAnalysisResult to export
            output_path: Output file path
            format_type: Export format ('json' or 'csv')

        """
        try:
            if format_type.lower() == "json":
                self._export_json(result, output_path)
            elif format_type.lower() == "csv":
                self._export_csv(result, output_path)
            else:
                self._raise_unsupported_format_error(format_type)

            logger.info("Results exported to %s", output_path)

        except Exception:
            logger.exception("Failed to export results")
            raise

    def _export_json(self, result: BatchAnalysisResult, output_path: Path) -> None:
        """Export results as JSON."""
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def _export_csv(self, result: BatchAnalysisResult, output_path: Path) -> None:
        """Export results as CSV."""
        with output_path.open("w", newline="", encoding="utf-8") as f:
            if result.analysis_results:
                writer = csv.DictWriter(
                    f, fieldnames=result.analysis_results[0].keys(),
                )
                writer.writeheader()
                writer.writerows(result.analysis_results)

    def _raise_unsupported_format_error(self, format_type: str) -> None:
        """Raise error for unsupported format."""
        msg = f"Unsupported format: {format_type}"
        raise ValueError(msg)

    def display_results(
        self, result: BatchAnalysisResult, format_type: str = "table",
    ) -> None:
        """Display analysis results in the terminal.

        Args:
            result: BatchAnalysisResult to display
            format_type: Display format ('table', 'json', or 'summary')

        """
        if format_type == "json":
            return

        self._display_summary_metrics(result)

        if format_type == "table":
            self._display_table_format(result)
        elif format_type == "summary":
            self._display_summary_format(result)

        self._display_failed_files(result)

    def _display_summary_metrics(self, result: BatchAnalysisResult) -> None:
        """Display summary metrics."""
        if not result.analysis_results:
            return

        total_messages = sum(
            r.get("total_messages", 0) for r in result.analysis_results
        )
        total_size = sum(r.get("file_size_bytes", 0) for r in result.analysis_results)
        avg_processing_time = (
            sum(r.get("processing_time", 0) for r in result.analysis_results) /
            len(result.analysis_results)
        )

        # Use the calculated metrics (placeholder for actual display logic)
        _ = total_messages, total_size, avg_processing_time

    def _display_table_format(self, result: BatchAnalysisResult) -> None:
        """Display results in table format."""
        if not result.analysis_results:
            return

        for analysis in result.analysis_results:
            file_name = self._truncate_filename(Path(analysis["file_path"]).name)
            # Placeholder for table display logic
            _ = file_name

    def _display_summary_format(self, result: BatchAnalysisResult) -> None:
        """Display results in summary format."""
        # Placeholder for summary display logic

    def _display_failed_files(self, result: BatchAnalysisResult) -> None:
        """Display information about failed files."""
        for failed in result.failed_files:
            # Placeholder for failed file display logic
            _ = failed

    def _truncate_filename(self, filename: str) -> str:
        """Truncate filename if too long."""
        if len(filename) > MAX_FILENAME_DISPLAY_LENGTH:
            return filename[:FILENAME_TRUNCATE_LENGTH] + "..."
        return filename
