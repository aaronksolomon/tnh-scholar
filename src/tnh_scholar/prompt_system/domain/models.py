"""Domain models for the prompt system."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PromptOutputMode(str, Enum):
    """Prompt output modes supported by the platform."""

    text = "text"
    json = "json"
    artifacts = "artifacts"


class InputStrictness(str, Enum):
    """Input declaration strictness."""

    loose = "loose"
    strict = "strict"


class PromptInputSpec(BaseModel):
    """Prompt input declaration."""

    name: str
    required: bool = False
    strictness: InputStrictness = InputStrictness.loose
    type: str | None = None
    source: str | None = None
    description: str | None = None


class PromptArtifactSpec(BaseModel):
    """Artifact declaration for artifact-producing prompts."""

    path: str
    required: bool = False


class PromptOutputContract(BaseModel):
    """Prompt output contract declaration."""

    mode: PromptOutputMode
    schema_ref: str | None = None
    artifacts: list[PromptArtifactSpec] = Field(default_factory=list)


class PromptMetadata(BaseModel):
    """Prompt front matter metadata."""

    prompt_id: str | None = None
    key: str = ""
    name: str
    version: str
    description: str
    role: str | None = None
    task_type: str = "unknown"
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: list[str] = Field(default_factory=list)
    default_variables: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    inputs: list[PromptInputSpec] = Field(default_factory=list)
    output_contract: PromptOutputContract | None = None
    input_contract_ref: str | None = None
    output_contract_ref: str | None = None
    default_model: str | None = None
    output_mode: PromptOutputMode | None = None
    safety_level: Literal["safe", "moderate", "sensitive"] | None = None
    pii_handling: Literal["none", "anonymize", "explicit_consent"] | None = None
    content_flags: list[str] = Field(default_factory=list)
    schema_version: str = "1.0"
    created_at: str | None = None
    updated_at: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @field_validator("version", mode="before")
    @classmethod
    def _coerce_version(cls, value: Any) -> str:
        """Coerce integer versions to string representation."""
        return str(value)

    @field_validator("output_mode", mode="before")
    @classmethod
    def _coerce_output_mode(cls, value: Any) -> Any:
        """Normalize legacy output_mode values before enum validation."""
        return "json" if value == "structured" else value

    @model_validator(mode="after")
    def _sync_legacy_and_v2_fields(self) -> "PromptMetadata":
        """Normalize key/output fields for legacy and v2 compatibility."""
        self._sync_key_fields()
        self._sync_role_fields()
        self._sync_output_fields()
        return self

    def _sync_key_fields(self) -> None:
        """Keep prompt_id and key synchronized for compatibility."""
        if self.prompt_id is None and self.key:
            self.prompt_id = self.key
        if not self.key and self.prompt_id:
            self.key = self.prompt_id

    def _sync_role_fields(self) -> None:
        """Keep role and legacy task_type synchronized for compatibility."""
        if self.role is None and self.task_type != "unknown":
            self.role = self.task_type
        if self.task_type == "unknown" and self.role is not None:
            self.task_type = self.role

    def _sync_output_fields(self) -> None:
        """Keep output_contract and legacy output_mode synchronized."""
        if self.output_contract is None:
            self.output_contract = self._output_contract_from_legacy_mode(self.output_mode)
        if self.output_mode is None and self.output_contract is not None:
            self.output_mode = self._legacy_mode_from_output_contract(self.output_contract)

    def canonical_key(self) -> str:
        """Return canonical key without version suffix."""
        return self.prompt_id or self.key

    def immutable_ref(self) -> str:
        """Return immutable prompt reference key.v<version>."""
        return f"{self.canonical_key()}.v{self.version}"

    def resolved_output_mode(self) -> PromptOutputMode:
        """Return normalized platform output mode."""
        if self.output_contract is not None:
            return self.output_contract.mode
        if self.output_mode == "json":
            return PromptOutputMode.json
        if self.output_mode == "artifacts":
            return PromptOutputMode.artifacts
        return PromptOutputMode.text

    def _output_contract_from_legacy_mode(
        self,
        legacy_mode: PromptOutputMode | None,
    ) -> PromptOutputContract:
        mode = self._mode_from_legacy_value(legacy_mode)
        return PromptOutputContract(mode=mode)

    def _legacy_mode_from_output_contract(
        self,
        contract: PromptOutputContract,
    ) -> PromptOutputMode:
        if contract.mode == PromptOutputMode.json:
            return PromptOutputMode.json
        if contract.mode == PromptOutputMode.artifacts:
            return PromptOutputMode.artifacts
        return PromptOutputMode.text

    def _mode_from_legacy_value(self, value: PromptOutputMode | None) -> PromptOutputMode:
        if value == PromptOutputMode.json:
            return PromptOutputMode.json
        if value == PromptOutputMode.artifacts:
            return PromptOutputMode.artifacts
        return PromptOutputMode.text


class Prompt(BaseModel):
    """Prompt domain model."""

    name: str
    version: str
    template: str
    metadata: PromptMetadata


class Message(BaseModel):
    """Single message in a conversation."""

    role: Literal["system", "user", "assistant"]
    content: str


class RenderedPrompt(BaseModel):
    """Rendered prompt ready for the provider."""

    system: str | None = None
    messages: list[Message] = Field(default_factory=list)


class RenderParams(BaseModel):
    """Per-call rendering parameters."""

    variables: dict[str, Any] = Field(default_factory=dict)
    strict_undefined: bool = True
    preserve_whitespace: bool = False
    user_input: str | None = None


class ValidationIssue(BaseModel):
    """Single validation issue."""

    level: Literal["error", "warning", "info"]
    code: str
    message: str
    field: str | None = None
    line: int | None = None


class PromptValidationResult(BaseModel):
    """Result of prompt validation.

    `valid` is maintained for API ergonomics and derived from `errors` to keep a
    single source of truth.
    """

    valid: bool = True
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    fingerprint_data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _sync_valid_with_errors(self) -> "PromptValidationResult":
        """Keep `valid` and `errors` semantically consistent."""
        self.valid = len(self.errors) == 0
        return self

    def succeeded(self) -> bool:
        return self.valid
