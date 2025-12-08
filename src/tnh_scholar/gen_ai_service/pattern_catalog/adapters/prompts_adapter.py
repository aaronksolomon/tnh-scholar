"""Prompts Adapter (ADR-A12 + ADR-PT04).

Bridges GenAI service to the new prompt_system package (catalog + renderer + validator).
Renders prompts, validates inputs, and produces fingerprints; provenance is assembled
later by GenAIService.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from tnh_scholar.gen_ai_service.infra.tracking.fingerprint import (
    hash_prompt_bytes,
    hash_user_string,
    hash_vars,
)
from tnh_scholar.gen_ai_service.models.domain import (
    Fingerprint,
    Message,
    RenderedPrompt,
    RenderRequest,
    Role,
)
from tnh_scholar.prompt_system.adapters.filesystem_catalog_adapter import (
    FilesystemPromptCatalog,
)
from tnh_scholar.prompt_system.config.policy import PromptRenderPolicy, ValidationPolicy
from tnh_scholar.prompt_system.config.prompt_catalog_config import PromptCatalogConfig
from tnh_scholar.prompt_system.config.settings import PromptSystemSettings
from tnh_scholar.prompt_system.domain.models import Prompt, PromptMetadata, RenderParams
from tnh_scholar.prompt_system.domain.protocols import (
    PromptCatalogPort,
    PromptRendererPort,
    PromptValidatorPort,
)
from tnh_scholar.prompt_system.mappers.prompt_mapper import PromptMapper
from tnh_scholar.prompt_system.service.loader import PromptLoader
from tnh_scholar.prompt_system.service.renderer import PromptRenderer
from tnh_scholar.prompt_system.service.validator import PromptValidator
from tnh_scholar.prompt_system.transport.cache import InMemoryCacheTransport

__all__ = [
    "PromptsAdapter",
]


class PromptsAdapter:
    """Render prompts and produce a Fingerprint per ADR-A12 using prompt_system."""

    def __init__(
        self,
        *,
        prompts_base: Path,
        catalog: PromptCatalogPort | None = None,
        renderer: PromptRendererPort | None = None,
        validator: PromptValidatorPort | None = None,
    ):
        self._base = Path(prompts_base)
        settings = PromptSystemSettings.from_env()

        render_policy = PromptRenderPolicy()
        validation_policy = ValidationPolicy()

        self._validator = validator or PromptValidator(validation_policy)
        self._renderer = renderer or PromptRenderer(
            render_policy, settings_defaults={}
        )

        mapper = PromptMapper()
        loader = PromptLoader(self._validator)
        catalog_config = PromptCatalogConfig(
            repository_path=self._base,
            enable_git_refresh=False,
            cache_ttl_s=settings.cache_ttl_seconds,
            validation_on_load=True,
        )
        self._catalog = catalog or FilesystemPromptCatalog(
            config=catalog_config,
            mapper=mapper,
            loader=loader,
            cache=InMemoryCacheTransport(default_ttl_s=catalog_config.cache_ttl_s),
        )

    # ---- Public API ----

    def render(self, request: RenderRequest) -> Tuple[RenderedPrompt, Fingerprint]:
        key = request.instruction_key
        prompt = self._catalog.get(key)

        params = RenderParams(
            variables=request.variables or {},
            user_input=request.user_input,
        )

        validation = self._validator.validate_render(prompt, params)
        if not validation.succeeded():
            raise ValueError(f"Validation failed: {validation.errors}")

        ps_rendered = self._renderer.render(prompt, params)
        rendered = RenderedPrompt(
            system=ps_rendered.system,
            messages=[
                Message(role=Role(msg.role), content=msg.content)
                for msg in ps_rendered.messages
            ],
        )
        fingerprint = self._build_fingerprint(prompt, request)
        return rendered, fingerprint

    def list_all(self) -> list[PromptMetadata]:
        """List all available prompts (ADR-VSC02 requirement for CLI/VS Code)."""
        return list(self._catalog.list())

    def introspect(self, prompt_key: str) -> PromptMetadata:
        """Get detailed metadata for a prompt (ADR-VSC02 requirement for CLI/VS Code)."""
        prompt = self._catalog.get(prompt_key)
        return prompt.metadata

    # ---- Internals ----

    def _build_fingerprint(
        self,
        prompt: Prompt,
        request: RenderRequest,
    ) -> Fingerprint:
        prompt_path = self._base / f"{request.instruction_key}.md"
        if prompt_path.exists():
            prompt_bytes = prompt_path.read_bytes()
        else:
            prompt_bytes = prompt.template.encode("utf-8")
        return Fingerprint(
            prompt_key=request.instruction_key,
            prompt_name=prompt.metadata.name,
            prompt_base_path=str(self._base),
            prompt_content_hash=hash_prompt_bytes(prompt_bytes),
            variables_hash=hash_vars(request.variables or {}),
            user_string_hash=hash_user_string(request.user_input),
        )
