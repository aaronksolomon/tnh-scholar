"""Prompt loader orchestration service."""

from collections.abc import Sequence

from ..domain.models import (
    CatalogIssue,
    CatalogIssueType,
    Prompt,
    PromptValidationResult,
)
from ..domain.protocols import PromptValidatorPort


class PromptLoader:
    """Responsible for preparing prompts (parse + validate)."""

    def __init__(self, validator: PromptValidatorPort):
        self._validator = validator

    def validate(self, prompt: Prompt) -> PromptValidationResult:
        """Validate prompt using configured validator."""
        return self._validator.validate(prompt)

    def warning_issues(self, prompt_key: str, warnings: Sequence[str]) -> list[CatalogIssue]:
        """Convert non-fatal prompt warnings into catalog issues."""
        return [
            CatalogIssue(
                prompt_key=prompt_key,
                issue_type=CatalogIssueType.METADATA_WARNING,
                message=warning,
            )
            for warning in warnings
        ]

    def validation_issues(
        self,
        prompt_key: str,
        validation: PromptValidationResult,
    ) -> list[CatalogIssue]:
        """Convert validation errors into fatal catalog issues."""
        return [
            CatalogIssue(
                prompt_key=prompt_key,
                issue_type=CatalogIssueType.VALIDATION_ERROR,
                message=issue.message,
            )
            for issue in validation.errors
        ]

    def parse_error_issue(self, prompt_key: str, message: str) -> CatalogIssue:
        """Build a fatal issue for unreadable or invalid frontmatter."""
        return CatalogIssue(
            prompt_key=prompt_key,
            issue_type=CatalogIssueType.FRONTMATTER_PARSE_ERROR,
            message=message,
        )
