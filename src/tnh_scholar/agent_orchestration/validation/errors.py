"""Domain errors for the validation subsystem."""

from __future__ import annotations

from tnh_scholar.exceptions import TnhScholarError


class ValidationArtifactMergeError(TnhScholarError):
    """Raised when validation artifacts cannot be merged safely."""
