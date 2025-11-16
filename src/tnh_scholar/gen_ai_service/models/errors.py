"""Error and Exception Models.

Defines typed exception classes used across GenAIService. Includes ProviderError,
ConfigurationError, SafetyError, and PolicyError, all of which can be raised or
wrapped by adapters and orchestrators.

Connected modules:
  - infra.issue_handler.IssueHandler
  - providers.*_adapter
  - safety.safety_gate
"""

from tnh_scholar.exceptions import TnhScholarError


class PatternNotFound(TnhScholarError):
    """Raised when a requested pattern or prompt is missing from the catalog."""


class SafetyBlocked(TnhScholarError):
    """Raised when content fails safety validation."""


class RoutingError(TnhScholarError):
    """Raised when a model routing or provider dispatch decision fails."""


class ProviderError(TnhScholarError):
    """Raised when a provider returns an invalid or unexpected response."""