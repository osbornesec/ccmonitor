"""
Comprehensive exception hierarchy for clean error handling
Following clean code principles for error management
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""

    VALIDATION = "validation"
    IO_OPERATION = "io_operation"
    PROCESSING = "processing"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass(frozen=True)
class ErrorContext:
    """Immutable error context information"""

    operation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = None


class CCMonitorError(Exception):
    """Base exception class for CCMonitor with enhanced error information"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.cause = cause
        self.suggestions = suggestions or []

    def __str__(self) -> str:
        """Enhanced string representation with context"""
        result = f"[{self.category.value.upper()}] {self.message}"

        if self.context:
            if self.context.file_path:
                result += f" (File: {self.context.file_path}"
                if self.context.line_number:
                    result += f", Line: {self.context.line_number}"
                result += ")"

        if self.cause:
            result += f" | Caused by: {str(self.cause)}"

        return result

    def get_user_friendly_message(self) -> str:
        """Get user-friendly error message with suggestions"""
        message = self.message

        if self.suggestions:
            message += "\n\nSuggestions:"
            for i, suggestion in enumerate(self.suggestions, 1):
                message += f"\n  {i}. {suggestion}"

        return message


# Validation Errors


class ValidationError(CCMonitorError):
    """Base class for validation errors"""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            suggestions=suggestions,
        )


class InvalidJSONLError(ValidationError):
    """Raised when JSONL file structure is invalid"""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        context = ErrorContext(
            operation="JSONL validation",
            file_path=file_path,
            line_number=line_number,
        )
        suggestions = [
            "Check file format - each line should contain valid JSON",
            "Verify file encoding is UTF-8",
            "Remove empty lines or invalid characters",
        ]
        super().__init__(message, context=context, suggestions=suggestions)


class MalformedEntryError(ValidationError):
    """Raised when an individual entry is malformed"""

    def __init__(
        self,
        message: str,
        entry_data: Optional[Dict[str, Any]] = None,
        line_number: Optional[int] = None,
    ):
        context = ErrorContext(
            operation="Entry validation",
            line_number=line_number,
            additional_info={"entry_data": entry_data} if entry_data else None,
        )
        suggestions = [
            "Ensure entry has required fields: uuid, type, message",
            "Check that message type is one of: user, assistant, tool_call, system",
            "Verify UUID is a non-empty string",
        ]
        super().__init__(message, context=context, suggestions=suggestions)


class ConversationFlowError(ValidationError):
    """Raised when conversation flow is invalid"""

    def __init__(
        self, message: str, problematic_uuids: Optional[List[str]] = None
    ):
        context = ErrorContext(
            operation="Conversation flow validation",
            additional_info=(
                {"problematic_uuids": problematic_uuids}
                if problematic_uuids
                else None
            ),
        )
        suggestions = [
            "Check parentUuid references point to existing messages",
            "Verify there are no circular references in conversation chain",
            "Ensure conversation has proper root messages",
        ]
        super().__init__(message, context=context, suggestions=suggestions)


# IO Operation Errors


class IOOperationError(CCMonitorError):
    """Base class for IO operation errors"""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        cause: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None,
    ):
        context = ErrorContext(operation="File operation", file_path=file_path)
        super().__init__(
            message=message,
            category=ErrorCategory.IO_OPERATION,
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause,
            suggestions=suggestions,
        )


class FileNotFoundError(IOOperationError):
    """Raised when a required file is not found"""

    def __init__(self, file_path: str):
        suggestions = [
            f"Verify the file path is correct: {file_path}",
            "Check file permissions and access rights",
            "Ensure the file hasn't been moved or deleted",
        ]
        super().__init__(
            message=f"File not found: {file_path}",
            file_path=file_path,
            suggestions=suggestions,
        )


class FilePermissionError(IOOperationError):
    """Raised when file permissions are insufficient"""

    def __init__(self, file_path: str, operation: str):
        suggestions = [
            f"Check read/write permissions for: {file_path}",
            "Run with appropriate user privileges",
            "Verify directory permissions for parent folder",
        ]
        super().__init__(
            message=f"Insufficient permissions for {operation}: {file_path}",
            file_path=file_path,
            suggestions=suggestions,
        )


class DiskSpaceError(IOOperationError):
    """Raised when there's insufficient disk space"""

    def __init__(self, required_space: Optional[int] = None):
        suggestions = [
            "Free up disk space on the target drive",
            "Choose a different output location with more space",
            "Clean up temporary files",
        ]
        message = "Insufficient disk space for operation"
        if required_space:
            message += f" (required: {required_space} bytes)"

        super().__init__(message=message, suggestions=suggestions)


# Processing Errors


class ProcessingError(CCMonitorError):
    """Base class for processing errors"""

    def __init__(
        self,
        message: str,
        operation: str,
        cause: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None,
    ):
        context = ErrorContext(operation=operation)
        super().__init__(
            message=message,
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause,
            suggestions=suggestions,
        )


class CompressionError(ProcessingError):
    """Raised when compression operation fails"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        suggestions = [
            "Disable compression and try again",
            "Check message content for unusual characters",
            "Verify sufficient memory for compression operation",
        ]
        super().__init__(
            message=message,
            operation="Message compression",
            cause=cause,
            suggestions=suggestions,
        )


class ConversationIntegrityError(ProcessingError):
    """Raised when conversation integrity is compromised"""

    def __init__(
        self, message: str, missing_uuids: Optional[List[str]] = None
    ):
        context = ErrorContext(
            operation="Conversation integrity check",
            additional_info=(
                {"missing_uuids": missing_uuids} if missing_uuids else None
            ),
        )
        suggestions = [
            "Review conversation analysis settings",
            "Check message dependency structure",
            "Verify conversation flow integrity",
        ]
        super().__init__(
            message=message,
            operation="Conversation integrity validation",
            suggestions=suggestions,
        )


# Configuration Errors


class ConfigurationError(CCMonitorError):
    """Base class for configuration errors"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
    ):
        context = ErrorContext(
            operation="Configuration validation",
            additional_info={"config_key": config_key} if config_key else None,
        )
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            suggestions=suggestions,
        )


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid"""

    def __init__(self, config_key: str, value: Any, expected_type: str):
        suggestions = [
            f"Set {config_key} to a valid {expected_type}",
            "Check configuration file syntax",
            "Use default configuration values",
        ]
        super().__init__(
            message=f"Invalid configuration for '{config_key}': expected {expected_type}, got {type(value).__name__}",
            config_key=config_key,
            suggestions=suggestions,
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing"""

    def __init__(self, config_key: str):
        suggestions = [
            f"Add required configuration key: {config_key}",
            "Use configuration template",
            "Run with default settings",
        ]
        super().__init__(
            message=f"Missing required configuration: {config_key}",
            config_key=config_key,
            suggestions=suggestions,
        )


# User Input Errors


class UserInputError(CCMonitorError):
    """Base class for user input errors"""

    def __init__(
        self,
        message: str,
        input_value: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
    ):
        context = ErrorContext(
            operation="User input validation",
            additional_info=(
                {"input_value": input_value} if input_value else None
            ),
        )
        super().__init__(
            message=message,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.LOW,
            context=context,
            suggestions=suggestions,
        )


class InvalidFilePathError(UserInputError):
    """Raised when an invalid file path is provided"""

    def __init__(self, file_path: str, reason: str):
        suggestions = [
            "Use absolute file paths when possible",
            "Check file path for special characters",
            "Verify directory structure exists",
        ]
        super().__init__(
            message=f"Invalid file path '{file_path}': {reason}",
            input_value=file_path,
            suggestions=suggestions,
        )


# System Errors


class SystemError(CCMonitorError):
    """Base class for system-level errors"""

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            cause=cause,
            suggestions=suggestions,
        )


class InsufficientMemoryError(SystemError):
    """Raised when system runs out of memory"""

    def __init__(self, required_memory: Optional[int] = None):
        suggestions = [
            "Close other applications to free memory",
            "Use streaming mode for large files",
            "Process files in smaller batches",
        ]
        message = "Insufficient memory for operation"
        if required_memory:
            message += f" (required: {required_memory} MB)"

        super().__init__(message=message, suggestions=suggestions)


class DependencyError(SystemError):
    """Raised when required dependencies are missing"""

    def __init__(
        self, dependency: str, required_version: Optional[str] = None
    ):
        suggestions = [
            f"Install required dependency: {dependency}",
            "Update package dependencies",
            "Check virtual environment activation",
        ]
        message = f"Missing required dependency: {dependency}"
        if required_version:
            message += f" (version {required_version} or higher)"

        super().__init__(message=message, suggestions=suggestions)


# Error Handler Utility


class ErrorHandler:
    """Utility class for consistent error handling"""

    @staticmethod
    def handle_file_operation_error(
        operation: str, file_path: str, original_error: Exception
    ) -> IOOperationError:
        """Convert generic file operation errors to specific CCMonitor errors"""
        if isinstance(original_error, FileNotFoundError):
            return FileNotFoundError(file_path)
        elif isinstance(original_error, PermissionError):
            return FilePermissionError(file_path, operation)
        elif "No space left on device" in str(original_error).lower():
            return DiskSpaceError()
        else:
            return IOOperationError(
                message=f"File operation failed: {original_error}",
                file_path=file_path,
                cause=original_error,
            )

    @staticmethod
    def handle_validation_error(
        entry: Dict[str, Any], line_number: int, validation_errors: List[str]
    ) -> MalformedEntryError:
        """Create appropriate validation error from validation results"""
        error_message = "; ".join(validation_errors)
        return MalformedEntryError(
            message=f"Entry validation failed: {error_message}",
            entry_data=entry,
            line_number=line_number,
        )

    @staticmethod
    def wrap_unexpected_error(
        operation: str, original_error: Exception
    ) -> CCMonitorError:
        """Wrap unexpected errors in CCMonitor error structure"""
        return CCMonitorError(
            message=f"Unexpected error during {operation}: {original_error}",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            context=ErrorContext(operation=operation),
            cause=original_error,
            suggestions=["Contact support if this error persists"],
        )
