"""Error and Exception Models.

Defines typed exception classes used across GenAIService. Includes ProviderError,
ConfigurationError, SafetyError, and PolicyError, all of which can be raised or
wrapped by adapters and orchestrators.

Connected modules:
  - infra.issue_handler.IssueHandler
  - providers.*_adapter
  - safety.safety_gate
"""

from typing import Literal

from tnh_scholar.exceptions import TnhScholarError


class PatternNotFound(TnhScholarError):
    """Raised when a requested pattern or prompt is missing from the catalog."""


class SafetyBlocked(TnhScholarError):
    """Raised when content fails safety validation."""

    def __init__(
        self,
        message: str,
        *,
        blocked_reason: Literal["budget"] | None = None,
        estimated_cost: float | None = None,
        max_dollars: float | None = None,
    ) -> None:
        super().__init__(message)
        self.blocked_reason = blocked_reason
        self.estimated_cost = estimated_cost
        self.max_dollars = max_dollars


class RoutingError(TnhScholarError):
    """Raised when a model routing or provider dispatch decision fails."""


class ProviderError(TnhScholarError):
    """Raised when a provider returns an invalid or unexpected response."""
