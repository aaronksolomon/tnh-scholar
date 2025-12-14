# src/tnh_scholar/exceptions.py

from __future__ import annotations

from typing import Any, Mapping, Optional


class TnhScholarError(Exception):
    """Base exception for all tnh_scholar errors.

    Attributes:
        message: Human-readable summary.
        context: Optional structured context to aid logging/diagnostics.
                 Keep this JSON-serializable.
        cause:   Optional underlying exception.
    """

    def __init__(
        self,
        message: str = "",
        *,
        context: Optional[Mapping[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = dict(context) if context else {}
        self.__cause__ = cause  # preserves exception chaining

    def __str__(self) -> str:
        return self.message or self.__class__.__name__


class ConfigurationError(TnhScholarError):
    """Configuration-related errors (missing env vars, invalid settings, etc.)."""


class ValidationError(TnhScholarError):
    """Input/data validation errors (precondition failures before calling providers)."""


class ExternalServiceError(TnhScholarError):
    """Upstream/provider errors (HTTP 5xx, transport, transient provider issues)."""


class RateLimitError(ExternalServiceError):
    """Upstream rate limits; typically retryable after a backoff."""


class NotRetryable(TnhScholarError):
    """Marker for errors where retry is known to be pointless (e.g., bad auth)."""


class MetadataConflictError(ValidationError):
    """Raised when metadata merge encounters key conflicts in FAIL_ON_CONFLICT mode."""


class SectionBoundaryError(ValidationError):
    """Raised when section boundaries have gaps, overlaps, or out-of-bounds errors.

    Note: Implementation is in text_object.py to avoid circular imports.
    This entry exists for documentation and to reserve the error name.
    """


__all__ = [
    "TnhScholarError",
    "ConfigurationError",
    "ValidationError",
    "ExternalServiceError",
    "RateLimitError",
    "NotRetryable",
    "MetadataConflictError",
    "SectionBoundaryError",
]
