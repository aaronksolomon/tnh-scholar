"""Prompt loader orchestration service."""

from ..domain.models import Prompt, PromptValidationResult
from ..domain.protocols import PromptValidatorPort


class PromptLoader:
    """Responsible for preparing prompts (parse + validate)."""

    def __init__(self, validator: PromptValidatorPort):
        self._validator = validator

    def validate(self, prompt: Prompt) -> PromptValidationResult:
        """Validate prompt using configured validator."""
        return self._validator.validate(prompt)
