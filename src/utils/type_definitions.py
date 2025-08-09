"""Comprehensive type definitions for CCMonitor.

Following Python typing best practices for clean code.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Final,
    Generic,
    Literal,
    Protocol,
    TypeVar,
    TypedDict,
    Union,
)

# Type aliases for better readability
UUID = str
FilePath = Union[str, Path]
JSONValue = Union[str, int, float, bool, None, dict[str, Any], list[Any]]
MessageContent = dict[str, Any]
ProcessingStatistics = dict[str, int | float | str]

# Literal types for constrained values
MessageType = Literal["user", "assistant", "tool_call", "system"]
OutputFormat = Literal["table", "json", "csv", "html"]
DecayMode = Literal[
    "none",
    "simple",
    "multi_stage",
    "content_aware",
    "adaptive",
]


# TypedDict for structured dictionaries
class MessageDict(TypedDict):
    """Type definition for message structure."""

    uuid: str
    type: MessageType
    message: MessageContent
    parentUuid: str | None
    timestamp: str | None


class ToolCallMessage(TypedDict):
    """Type definition for tool call message content."""

    tool: str
    parameters: dict[str, Any]
    result: Any


class ProcessingStatisticsDict(TypedDict):
    """Type definition for processing statistics."""

    messages_processed: int
    messages_preserved: int
    messages_removed: int
    messages_compressed: int
    malformed_entries: int
    processing_time: float
    compression_ratio: float
    importance_threshold: int


class ConversationGraphNode(TypedDict):
    """Type definition for conversation graph nodes."""

    parent: str | None
    children: list[str]
    entry: MessageDict
    depth: int


class DependencyGraphDict(TypedDict):
    """Type definition for conversation dependency graph."""

    dependency_map: dict[str, ConversationGraphNode]
    orphans: list[str]
    total_messages: int
    orphaned_messages: int


# Generic types
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

ResultType = TypeVar("ResultType")
ConfigType = TypeVar("ConfigType")
ProcessorType = TypeVar("ProcessorType")


# Protocol definitions for better interface contracts
class Serializable(Protocol):
    """Protocol for objects that can be serialized to JSON."""

    def to_dict(self) -> dict[str, Any]:
        """Convert object to dictionary representation."""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Serializable":
        """Create object from dictionary representation."""
        ...


class Validatable(Protocol):
    """Protocol for objects that can be validated."""

    def validate(self) -> bool:
        """Validate object state."""
        ...

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors."""
        ...


class Cacheable(Protocol):
    """Protocol for objects that can be cached."""

    def get_cache_key(self) -> str:
        """Get unique cache key for this object."""
        ...

    def is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached version is still valid."""
        ...


class Processable(Protocol[T]):
    """Protocol for objects that can be processed."""

    def process(self, input_data: T) -> T:
        """Process input data and return result."""
        ...

    def can_process(self, input_data: T) -> bool:
        """Check if this processor can handle the input."""
        ...


# Function type definitions
MessageValidator = Callable[[MessageDict], bool]
ImportanceCalculator = Callable[[MessageDict], float]
MessageTransformer = Callable[[MessageDict], MessageDict]
ProgressCallback = Callable[[int, int, str], None]
ErrorHandler = Callable[[Exception], None]

# Async function types
AsyncMessageProcessor = Callable[[MessageDict], Awaitable[MessageDict]]
AsyncBatchProcessor = Callable[
    [list[MessageDict]], Awaitable[list[MessageDict]]
]


# Generic result wrapper
@dataclass(frozen=True)
class Result(Generic[T]):
    """Generic result wrapper with success/error states."""

    success: bool
    value: T | None = None
    error: str | None = None
    error_code: str | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """Create successful result."""
        return cls(success=True, value=value)

    @classmethod
    def create_error(
        cls,
        error_msg: str,
        error_code: str | None = None,
    ) -> "Result[T]":
        """Create error result."""
        return cls(success=False, error=error_msg, error_code=error_code)

    def unwrap(self) -> T:
        """Unwrap value or raise exception."""
        if self.success and self.value is not None:
            return self.value
        error_msg = f"Result unwrap failed: {self.error}"
        msg = "Result unwrap failed"
        raise ValueError(error_msg if self.error else msg)

    def unwrap_or(self, default: T) -> T:
        """Unwrap value or return default."""
        return (
            self.value if self.success and self.value is not None else default
        )


# Configuration types with constraints
@dataclass(frozen=True)
class ProcessingConfiguration:
    """Type-safe processing configuration."""

    importance_threshold: int
    temporal_decay_enabled: bool = False
    backup_enabled: bool = True
    compression_enabled: bool = True
    max_memory_mb: int = 1024
    parallel_workers: int = 4

    def __post_init__(self) -> None:
        """Validate configuration values."""
        threshold_min, threshold_max = 0, 100
        if not threshold_min <= self.importance_threshold <= threshold_max:
            msg = f"Importance threshold must be between {threshold_min} and {threshold_max}"
            raise ValueError(msg)

        min_memory = 64
        if self.max_memory_mb < min_memory:
            msg = f"Maximum memory must be at least {min_memory}MB"
            raise ValueError(msg)

        min_workers, max_workers = 1, 16
        if not min_workers <= self.parallel_workers <= max_workers:
            msg = f"Parallel workers must be between {min_workers} and {max_workers}"
            raise ValueError(msg)


# Callback function types with specific signatures
class ProcessingCallbacks(TypedDict, total=False):
    """Type definition for processing callbacks."""

    on_start: Callable[[int], None]  # total_messages
    on_progress: Callable[[int, int], None]  # current, total
    on_message_processed: Callable[
        [MessageDict, bool],
        None,
    ]  # message, preserved
    on_complete: Callable[[ProcessingStatisticsDict], None]
    on_error: Callable[[Exception], None]


# Advanced generic types for framework extensibility
class Repository(Protocol, Generic[T, K]):
    """Generic repository pattern protocol."""

    def get(self, key: K) -> T | None:
        """Get entity by key."""
        ...

    def save(self, entity: T) -> K:
        """Save entity and return key."""
        ...

    def delete(self, key: K) -> bool:
        """Delete entity by key."""
        ...

    def list_all(self) -> list[T]:
        """List all entities."""
        ...


class Strategy(Protocol, Generic[T, ResultType]):
    """Generic strategy pattern protocol."""

    def execute(self, input_data: T) -> ResultType:
        """Execute strategy with input data."""
        ...

    def can_handle(self, input_data: T) -> bool:
        """Check if strategy can handle input."""
        ...


class Factory(Protocol, Generic[T, ConfigType]):
    """Generic factory pattern protocol."""

    def create(self, config: ConfigType) -> T:
        """Create instance with configuration."""
        ...

    def supports(self, config: ConfigType) -> bool:
        """Check if factory supports configuration."""
        ...


# Specialized type definitions for domain objects
class ConversationAnalysisResult(TypedDict):
    """Complete conversation analysis result type."""

    parsing: dict[str, int | float]
    message_types: dict[str, int]
    tool_usage: dict[str, Any]
    conversation_flow: dict[str, Any]
    processing_recommendations: list[str]
    estimated_compression_ratio: float


class BatchProcessingResult(TypedDict):
    """Batch processing result type."""

    files_processed: int
    files_successful: int
    files_failed: int
    total_time: float
    detailed_results: list[dict[str, Any]]
    summary_statistics: ProcessingStatisticsDict


# Union types for flexibility
MessageIdentifier = Union[str, int]  # UUID or index
ProcessingInput = Union[
    FilePath,
    list[MessageDict],
    str,
]  # File, messages, or JSON string
ProcessingOutput = Union[
    FilePath,
    list[MessageDict],
]  # File or in-memory result

# Constants with proper typing
SUPPORTED_MESSAGE_TYPES: Final[set[MessageType]] = {
    "user",
    "assistant",
    "tool_call",
    "system",
}

MAX_MESSAGE_SIZE: Final[int] = 1024 * 1024  # 1MB
DEFAULT_CHUNK_SIZE: Final[int] = 1000
DEFAULT_TIMEOUT_SECONDS: Final[int] = 300


# Type guards for runtime type checking
def is_message_dict(obj: object) -> bool:
    """Type guard for MessageDict."""
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("uuid"), str)
        and obj.get("type") in SUPPORTED_MESSAGE_TYPES
        and isinstance(obj.get("message"), dict)
    )


def is_processing_result(obj: object) -> bool:
    """Type guard for processing result."""
    required_keys = {
        "messages_processed",
        "messages_preserved",
        "messages_removed",
        "processing_time",
        "compression_ratio",
    }
    return (
        isinstance(obj, dict)
        and required_keys.issubset(obj.keys())
        and all(isinstance(obj[key], (int, float)) for key in required_keys)
    )


# Utility type functions
def create_empty_statistics() -> ProcessingStatisticsDict:
    """Create empty processing statistics with proper types."""
    return ProcessingStatisticsDict(
        messages_processed=0,
        messages_preserved=0,
        messages_removed=0,
        messages_compressed=0,
        malformed_entries=0,
        processing_time=0.0,
        compression_ratio=0.0,
        importance_threshold=40,
    )


def serialize_message_safely(message: MessageDict) -> str:
    """Safely serialize message to JSON string."""
    try:
        return json.dumps(message, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        error_msg = f"Cannot serialize message: {e}"
        raise ValueError(error_msg) from e


def parse_message_safely(json_str: str) -> Result[MessageDict]:
    """Safely parse JSON string to message."""
    try:
        data = json.loads(json_str)
        if is_message_dict(data):
            return Result.ok(data)
        return Result.create_error("Invalid message structure")
    except json.JSONDecodeError as e:
        return Result.create_error(f"JSON parse error: {e}")


# Type aliases for complex nested structures
ComplexAnalysisResult = dict[
    str,
    ProcessingStatisticsDict
    | ConversationAnalysisResult
    | list[MessageDict]
    | dict[str, Any],
]

ProcessingPipeline = list[Callable[[list[MessageDict]], list[MessageDict]]]

ConfigurationValidator = Callable[
    [dict[str, Any]],
    Result[ProcessingConfiguration],
]


# Export all public types
__all__ = [
    # Basic type aliases
    "AsyncBatchProcessor",
    "AsyncMessageProcessor",
    "BatchProcessingResult",
    "Cacheable",
    "ComplexAnalysisResult",
    "ConfigType",
    "ConfigurationValidator",
    "ConversationAnalysisResult",
    "ConversationGraphNode",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_TIMEOUT_SECONDS",
    "DecayMode",
    "DependencyGraphDict",
    "ErrorHandler",
    "Factory",
    "FilePath",
    "ImportanceCalculator",
    "JSONValue",
    "K",
    "MAX_MESSAGE_SIZE",
    "MessageContent",
    "MessageDict",
    "MessageIdentifier",
    "MessageTransformer",
    "MessageType",
    "MessageValidator",
    "OutputFormat",
    "Processable",
    "ProcessingCallbacks",
    "ProcessingConfiguration",
    "ProcessingInput",
    "ProcessingOutput",
    "ProcessingPipeline",
    "ProcessingStatistics",
    "ProcessingStatisticsDict",
    "ProcessorType",
    "ProgressCallback",
    "Repository",
    "Result",
    "ResultType",
    "SUPPORTED_MESSAGE_TYPES",
    "Serializable",
    "Strategy",
    "T",
    "ToolCallMessage",
    "UUID",
    "V",
    "Validatable",
    "create_empty_statistics",
    "is_message_dict",
    "is_processing_result",
    "parse_message_safely",
    "serialize_message_safely",
]
