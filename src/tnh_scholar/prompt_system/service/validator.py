"""Prompt validation service."""

import re

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError

from ..config.policy import ValidationPolicy
from ..domain.models import (
    Prompt,
    PromptValidationResult,
    RenderParams,
    ValidationIssue,
)
from ..domain.protocols import PromptValidatorPort

_SEMVER_PATTERN = re.compile(r"^\d+\.\d+(?:\.\d+)?$")
_ALWAYS_ALLOWED_VARIABLES = {"input_text"}


class PromptValidator(PromptValidatorPort):
    """Validates prompt metadata and render parameters."""

    def __init__(self, policy: ValidationPolicy):
        self._policy = policy

    def validate(self, prompt: Prompt) -> PromptValidationResult:
        """Validate prompt metadata and template syntax."""
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._validate_required_fields(prompt, errors)
        self._validate_version(prompt, errors)
        self._validate_template(prompt, errors)

        valid = len(errors) == 0
        return PromptValidationResult(valid=valid, errors=errors, warnings=warnings)

    def validate_render(
        self, prompt: Prompt, params: RenderParams
    ) -> PromptValidationResult:
        """Validate render inputs against prompt requirements."""
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._validate_required_variables(prompt, params, errors)
        self._validate_extra_variables(prompt, params, errors, warnings)

        valid = len(errors) == 0
        return PromptValidationResult(valid=valid, errors=errors, warnings=warnings)

    def _validate_required_fields(
        self, prompt: Prompt, errors: list[ValidationIssue]
    ) -> None:
        if not prompt.metadata.name:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_NAME",
                    message="Prompt name is required",
                    field="name",
                )
            )
        if not prompt.metadata.version:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_VERSION",
                    message="Prompt version is required",
                    field="version",
                )
            )
        if not prompt.template:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_TEMPLATE",
                    message="Prompt template content is required",
                    field="template",
                )
            )

    def _validate_version(self, prompt: Prompt, errors: list[ValidationIssue]) -> None:
        if prompt.metadata.version and not _SEMVER_PATTERN.match(
            prompt.metadata.version
        ):
            errors.append(
                ValidationIssue(
                    level="error",
                    code="INVALID_VERSION",
                    message="Version must be semver format (e.g., 1.0.0)",
                    field="version",
                )
            )

    def _validate_template(self, prompt: Prompt, errors: list[ValidationIssue]) -> None:
        env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        try:
            env.parse(prompt.template)
        except TemplateSyntaxError as exc:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="INVALID_TEMPLATE",
                    message=str(exc),
                    field="template",
                )
            )

    def _validate_required_variables(
        self, prompt: Prompt, params: RenderParams, errors: list[ValidationIssue]
    ) -> None:
        missing = set(prompt.metadata.required_variables) - set(
            params.variables.keys()
        )
        if missing and self._policy.fail_on_missing_required:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_REQUIRED_VARS",
                    message=f"Missing required variables: {sorted(missing)}",
                    field="variables",
                )
            )

    def _validate_extra_variables(
        self,
        prompt: Prompt,
        params: RenderParams,
        errors: list[ValidationIssue],
        warnings: list[ValidationIssue],
    ) -> None:
        if self._policy.allow_extra_variables:
            return

        allowed = (
            set(prompt.metadata.required_variables)
            | set(prompt.metadata.optional_variables)
            | _ALWAYS_ALLOWED_VARIABLES
        )
        extra = set(params.variables.keys()) - allowed
        if not extra:
            return

        issue = ValidationIssue(
            level="warning" if self._policy.mode == "warn" else "error",
            code="EXTRA_VARIABLES",
            message=f"Unexpected variables: {sorted(extra)}",
            field="variables",
        )

        if self._policy.mode == "warn":
            warnings.append(issue)
        else:
            errors.append(issue)
