"""
Batch processing system for ccmonitor CLI
Analysis-focused batch operations with parallel processing
"""

import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from threading import Lock

from .utils import format_size, format_duration, is_jsonl_file
from ..jsonl_analysis.analyzer import JSONLAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class BatchAnalysisResult:
    """Results from batch analysis processing"""

    directory: Path
    pattern: str
    recursive: bool
    files_analyzed: List[Path]
    failed_files: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    start_time: float
    end_time: float
    total_files_discovered: int = 0

    @property
    def processing_time(self) -> float:
        """Calculate total processing time"""
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = len(self.files_analyzed) + len(self.failed_files)
        return len(self.files_analyzed) / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export"""
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
                    self.processing_time / len(self.files_analyzed) if self.files_analyzed else 0
                ),
            },
        }


class BatchProcessor:
    """
    Batch processor for analyzing multiple JSONL files
    Focuses on analysis only - no file modification
    """

    def __init__(
        self,
        directory: Path,
        pattern: str = "*.jsonl",
        recursive: bool = False,
        parallel_workers: int = 4,
        verbose: bool = False,
    ):
        """
        Initialize batch processor

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

    def discover_files(self) -> List[Path]:
        """
        Discover JSONL files to process

        Returns:
            List of JSONL file paths
        """
        files = []

        if self.recursive:
            # Recursive search
            for file_path in self.directory.rglob(self.pattern):
                if file_path.is_file() and is_jsonl_file(file_path):
                    files.append(file_path)
        else:
            # Single directory search
            for file_path in self.directory.glob(self.pattern):
                if file_path.is_file() and is_jsonl_file(file_path):
                    files.append(file_path)

        # Sort files by size (process smaller files first)
        files.sort(key=lambda x: x.stat().st_size)

        if self.verbose:
            logger.debug(f"Discovered {len(files)} JSONL files")

        return files

    def analyze_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a single JSONL file

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
            conversation_info = self._analyzer.analyze_conversation_structure(messages)

            # Get message type distribution
            message_types = {}
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
            logger.error(f"Failed to analyze {file_path}: {e}")

            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
            }

    def analyze_directory(self) -> BatchAnalysisResult:
        """
        Analyze all JSONL files in the directory

        Returns:
            BatchAnalysisResult with comprehensive analysis
        """
        start_time = time.time()

        # Discover files
        files_to_analyze = self.discover_files()

        if not files_to_analyze:
            logger.warning(f"No JSONL files found in {self.directory}")
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

        # Process files with thread pool
        successful_results = []
        failed_files = []

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.analyze_single_file, file_path): file_path
                for file_path in files_to_analyze
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]

                try:
                    result = future.result()

                    if result["status"] == "success":
                        successful_results.append(result)
                        if self.verbose:
                            logger.info(f"✓ Analyzed {file_path}")
                    else:
                        failed_files.append(result)
                        logger.error(f"✗ Failed to analyze {file_path}: {result.get('error')}")

                except Exception as e:
                    error_result = {
                        "file_path": str(file_path),
                        "status": "failed",
                        "error": str(e),
                    }
                    failed_files.append(error_result)
                    logger.error(f"✗ Exception analyzing {file_path}: {e}")

        end_time = time.time()

        return BatchAnalysisResult(
            directory=self.directory,
            pattern=self.pattern,
            recursive=self.recursive,
            files_analyzed=[
                Path(r["file_path"]) for r in successful_results if r["status"] == "success"
            ],
            failed_files=failed_files,
            analysis_results=successful_results,
            start_time=start_time,
            end_time=end_time,
            total_files_discovered=len(files_to_analyze),
        )

    def export_results(
        self, result: BatchAnalysisResult, output_path: Path, format_type: str = "json"
    ):
        """
        Export analysis results to file

        Args:
            result: BatchAnalysisResult to export
            output_path: Output file path
            format_type: Export format ('json' or 'csv')
        """
        try:
            if format_type.lower() == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

            elif format_type.lower() == "csv":
                import csv

                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    if result.analysis_results:
                        writer = csv.DictWriter(f, fieldnames=result.analysis_results[0].keys())
                        writer.writeheader()
                        writer.writerows(result.analysis_results)

            else:
                raise ValueError(f"Unsupported format: {format_type}")

            logger.info(f"Results exported to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise

    def display_results(self, result: BatchAnalysisResult, format_type: str = "table"):
        """
        Display analysis results in the terminal

        Args:
            result: BatchAnalysisResult to display
            format_type: Display format ('table', 'json', or 'summary')
        """
        if format_type == "json":
            print(json.dumps(result.to_dict(), indent=2))
            return

        # Summary display
        print(f"\n{'='*60}")
        print(f"BATCH ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"Directory: {result.directory}")
        print(f"Pattern: {result.pattern}")
        print(f"Recursive: {result.recursive}")
        print(f"Processing time: {format_duration(result.processing_time)}")
        print(f"Success rate: {result.success_rate*100:.1f}%")
        print()

        print(f"Files discovered: {result.total_files_discovered}")
        print(f"Files analyzed successfully: {len(result.files_analyzed)}")
        print(f"Files failed: {len(result.failed_files)}")

        if result.analysis_results:
            total_messages = sum(r.get("total_messages", 0) for r in result.analysis_results)
            total_size = sum(r.get("file_size_bytes", 0) for r in result.analysis_results)
            avg_processing_time = sum(
                r.get("processing_time", 0) for r in result.analysis_results
            ) / len(result.analysis_results)

            print()
            print(f"Total messages analyzed: {total_messages:,}")
            print(f"Total file size: {format_size(total_size)}")
            print(f"Average processing time per file: {format_duration(avg_processing_time)}")

        if format_type == "table" and result.analysis_results:
            print(f"\n{'='*80}")
            print(f"{'File':<40} {'Messages':<10} {'Size':<10} {'Time':<8}")
            print(f"{'-'*80}")

            for analysis in result.analysis_results:
                file_name = Path(analysis["file_path"]).name
                if len(file_name) > 37:
                    file_name = file_name[:34] + "..."

                print(
                    f"{file_name:<40} {analysis.get('total_messages', 0):<10} "
                    f"{analysis.get('file_size_formatted', 'N/A'):<10} "
                    f"{analysis.get('processing_time_formatted', 'N/A'):<8}"
                )

        if result.failed_files:
            print(f"\n{'='*40}")
            print(f"FAILED FILES ({len(result.failed_files)})")
            print(f"{'='*40}")

            for failed in result.failed_files:
                print(f"✗ {Path(failed['file_path']).name}: {failed.get('error', 'Unknown error')}")

        print(f"\n{'='*60}")
