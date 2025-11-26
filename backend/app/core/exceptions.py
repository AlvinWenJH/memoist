"""
Custom exceptions for the Vectorless RAG application.
"""

from typing import Any, Dict, Optional


class MemoistException(Exception):
    """Base exception for Memoist application."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class ValidationError(MemoistException):
    """Raised when input validation fails."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, detail=detail)


class NotFoundError(MemoistException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, detail=detail)


class ConflictError(MemoistException):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, detail=detail)


class UnauthorizedError(MemoistException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, detail=detail)


class ForbiddenError(MemoistException):
    """Raised when access is forbidden."""

    def __init__(
        self, message: str = "Access forbidden", detail: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=403, detail=detail)


class ProcessingError(MemoistException):
    """Raised when document processing fails."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, detail=detail)


class StorageError(MemoistException):
    """Raised when storage operations fail."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)


class DatabaseError(MemoistException):
    """Raised when database operations fail."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)


class ExternalServiceError(MemoistException):
    """Raised when external service calls fail."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, detail=detail)


class RateLimitError(MemoistException):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        detail: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=429, detail=detail)


class ConfigurationError(MemoistException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)
