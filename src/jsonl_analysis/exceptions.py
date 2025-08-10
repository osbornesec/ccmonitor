"""Custom exceptions for JSONL analysis modules."""


class JSONLAnalysisError(Exception):
    """Base exception for JSONL analysis errors."""


class InvalidJSONLError(JSONLAnalysisError):
    """Raised when JSONL file structure is invalid."""


class MalformedEntryError(JSONLAnalysisError):
    """Raised when a JSONL entry is malformed."""


class InvalidMessageError(JSONLAnalysisError):
    """Raised when message structure is invalid for scoring."""


class PatternDetectionError(JSONLAnalysisError):
    """Raised when pattern detection fails."""


class ConversationFlowError(JSONLAnalysisError):
    """Raised when conversation flow analysis fails."""
