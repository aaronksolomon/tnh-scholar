"""Domain models for the prompt system."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class PromptMetadata(BaseModel):
    """Prompt front matter metadata."""

    key: str
    name: str
    version: str
    description: str
    task_type: str
    required_variables: list[str]
    optional_variables: list[str] = Field(default_factory=list)
    default_variables: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    default_model: str | None = None
    output_mode: Literal["text", "json", "structured"] | None = None
    safety_level: Literal["safe", "moderate", "sensitive"] | None = None
    pii_handling: Literal["none", "anonymize", "explicit_consent"] | None = None
    content_flags: list[str] = Field(default_factory=list)
    schema_version: str = "1.0"
    created_at: str | None = None
    updated_at: str | None = None
    warnings: list[str] = Field(default_factory=list)


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
    """Result of prompt validation."""

    valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    fingerprint_data: dict[str, Any] = Field(default_factory=dict)

    def succeeded(self) -> bool:
        return self.valid and len(self.errors) == 0
