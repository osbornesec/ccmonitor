"""
Custom exceptions for JSONL analysis modules
"""


class JSONLAnalysisError(Exception):
    """Base exception for JSONL analysis errors"""
    pass


class InvalidJSONLError(JSONLAnalysisError):
    """Raised when JSONL file structure is invalid"""
    pass


class MalformedEntryError(JSONLAnalysisError):
    """Raised when a JSONL entry is malformed"""
    pass


class InvalidMessageError(JSONLAnalysisError):
    """Raised when message structure is invalid for scoring"""
    pass


class PatternDetectionError(JSONLAnalysisError):
    """Raised when pattern detection fails"""
    pass


class ConversationFlowError(JSONLAnalysisError):
    """Raised when conversation flow analysis fails"""
    pass