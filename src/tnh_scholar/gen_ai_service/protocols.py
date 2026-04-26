from __future__ import annotations

from typing import Protocol

from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    Fingerprint,
    RenderedPrompt,
    RenderRequest,
)
from tnh_scholar.prompt_system.domain.models import PromptMetadata


class PromptCatalogProtocol(Protocol):
    """Protocol for prompt catalog access (decoupled from concrete adapter)."""

    def introspect(self, prompt_key: str) -> PromptMetadata:
        """Get metadata for a specific prompt."""
        ...

    def render(self, request: RenderRequest) -> tuple[RenderedPrompt, Fingerprint]:
        """Render prompt content and fingerprint for provider consumption."""
        ...


class GenAIServiceProtocol(Protocol):
    """Minimal protocol for GenAIService to support DI and testing."""

    catalog: PromptCatalogProtocol

    def generate(self, request: RenderRequest) -> CompletionEnvelope:
        """Generate completion from prompt and request."""
        ...
