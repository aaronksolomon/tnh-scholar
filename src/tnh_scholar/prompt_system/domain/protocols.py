"""Protocols defining prompt system behavior contracts."""

from typing import Protocol

from .models import Prompt, PromptMetadata, PromptValidationResult, RenderedPrompt, RenderParams


class PromptCatalogPort(Protocol):
    """Repository interface for prompt storage and retrieval."""

    def get(self, key: str) -> Prompt:
        """Retrieve prompt by key."""
        ...

    def list(self) -> list[PromptMetadata]:
        """List available prompts."""
        ...


class PromptRendererPort(Protocol):
    """Renders prompts with variable substitution."""

    def render(self, prompt: Prompt, params: RenderParams) -> RenderedPrompt:
        """Render prompt with templating."""
        ...


class PromptValidatorPort(Protocol):
    """Validates prompt schema and render parameters."""

    def validate(self, prompt: Prompt) -> PromptValidationResult:
        """Validate prompt metadata and template."""
        ...

    def validate_render(self, prompt: Prompt, params: RenderParams) -> PromptValidationResult:
        """Validate render inputs against prompt requirements."""
        ...

