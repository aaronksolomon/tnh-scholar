"""Prompt validation service."""

import re

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError

from ..config.policy import ValidationPolicy
from ..domain.models import (
    InputStrictness,
    Prompt,
    PromptOutputMode,
    PromptValidationResult,
    RenderParams,
    ValidationIssue,
)
from ..domain.protocols import PromptValidatorPort

_VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+){0,2}$")
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
        self._validate_inputs(prompt, errors)
        self._validate_output_contract(prompt, errors)

        valid = not errors
        return PromptValidationResult(valid=valid, errors=errors, warnings=warnings)

    def validate_render(
        self, prompt: Prompt, params: RenderParams
    ) -> PromptValidationResult:
        """Validate render inputs against prompt requirements."""
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._validate_required_variables(prompt, params, errors)
        self._validate_extra_variables(prompt, params, errors, warnings)

        valid = not errors
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
        if not prompt.metadata.role:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_ROLE",
                    message="Prompt role is required.",
                    field="role",
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
        if not prompt.metadata.canonical_key():
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_KEY",
                    message="Prompt key/prompt_id is required.",
                    field="key",
                )
            )

    def _validate_version(self, prompt: Prompt, errors: list[ValidationIssue]) -> None:
        if prompt.metadata.version and not _VERSION_PATTERN.match(
            prompt.metadata.version
        ):
            errors.append(
                ValidationIssue(
                    level="error",
                    code="INVALID_VERSION",
                    message="Version must be numeric version format (e.g., 1 or 1.0.0).",
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

    def _validate_inputs(self, prompt: Prompt, errors: list[ValidationIssue]) -> None:
        for input_spec in prompt.metadata.inputs:
            if input_spec.strictness != InputStrictness.strict:
                continue
            if input_spec.required:
                continue
            errors.append(
                ValidationIssue(
                    level="error",
                    code="INVALID_INPUT_STRICTNESS",
                    message=f"Input '{input_spec.name}' with strictness=strict must set required=true.",
                    field="inputs",
                )
            )

    def _validate_output_contract(self, prompt: Prompt, errors: list[ValidationIssue]) -> None:
        contract = prompt.metadata.output_contract
        if contract is None:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_OUTPUT_CONTRACT",
                    message="Prompt output_contract is required.",
                    field="output_contract",
                )
            )
            return

        if contract.mode == PromptOutputMode.json and not contract.schema_ref:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_SCHEMA_REF",
                    message="JSON output mode requires output_contract.schema_ref.",
                    field="output_contract.schema_ref",
                )
            )
        if contract.mode == PromptOutputMode.artifacts and not contract.artifacts:
            errors.append(
                ValidationIssue(
                    level="error",
                    code="MISSING_ARTIFACTS",
                    message="Artifacts output mode requires at least one artifact declaration.",
                    field="output_contract.artifacts",
                )
            )

    def _validate_required_variables(
        self, prompt: Prompt, params: RenderParams, errors: list[ValidationIssue]
    ) -> None:
        required_variables = set(prompt.metadata.required_variables)
        input_required = {
            input_spec.name
            for input_spec in prompt.metadata.inputs
            if input_spec.required or input_spec.strictness == InputStrictness.strict
        }
        missing = (required_variables | input_required) - set(params.variables.keys())
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
            | {input_spec.name for input_spec in prompt.metadata.inputs}
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
