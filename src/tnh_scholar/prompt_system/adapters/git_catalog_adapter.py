"""Git-backed prompt catalog adapter."""

import logging
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from ..config.prompt_catalog_config import PromptCatalogConfig
from ..domain.models import (
    Prompt,
    PromptMetadata,
    PromptOutputContract,
    PromptOutputMode,
)
from ..domain.protocols import PromptCatalogPort
from ..mappers.prompt_mapper import PromptMapper
from ..service.loader import PromptLoader
from ..transport.cache import CacheTransport, InMemoryCacheTransport
from ..transport.git_client import GitTransportClient
from ..transport.models import PromptFileRequest
from .frontmatter_fallback import extract_best_effort_body

logger = logging.getLogger(__name__)


class GitPromptCatalog(PromptCatalogPort):
    """Git-backed prompt catalog adapter (implements PromptCatalogPort)."""

    _EXPECTED_FRONTMATTER = (
        "Expected prompt envelope keys include prompt_id/key, name, version, description, "
        "role/task_type, inputs/required_variables, and output_contract/output_mode."
    )

    def __init__(
        self,
        config: PromptCatalogConfig,
        transport: GitTransportClient,
        loader: PromptLoader,
        mapper: PromptMapper | None = None,
        cache: CacheTransport[Prompt] | None = None,
    ):
        self._config = config
        self._transport = transport
        self._loader = loader
        self._cache = cache or InMemoryCacheTransport(default_ttl_s=config.cache_ttl_s)
        self._mapper = mapper or PromptMapper()

    def get(self, key: str) -> Prompt:
        cache_key = self._make_cache_key(key)
        if cached := self._cache.get(cache_key):
            return cached

        file_req = self._build_file_request(key)
        file_resp = self._transport.read_file_at_commit(file_req)
        prompt, warnings = self._load_prompt_with_fallback(key, file_resp.content)

        if warnings:
            self._log_warnings(key, warnings)

        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def _build_file_request(self, key: str) -> PromptFileRequest:
        return PromptFileRequest(
            path=self._mapper.to_file_request(key, self._config.repository_path),
            commit_sha=None,
        )

    def _load_prompt_with_fallback(
        self,
        key: str,
        content: str,
    ) -> tuple[Prompt, list[str]]:
        try:
            prompt = self._mapper.to_domain_prompt(content, source_key=key)
        except (ValidationError, ValueError) as exc:
            return self._build_prompt_from_invalid_file(key, content, reason=str(exc))
        return self._apply_loader_validation(key, prompt)

    def _build_prompt_from_invalid_file(
        self,
        key: str,
        content: str,
        *,
        reason: str,
    ) -> tuple[Prompt, list[str]]:
        body = self._best_effort_body(content)
        fallback_metadata = self._fallback_metadata(key, reason=reason)
        prompt = Prompt(
            name=fallback_metadata.name,
            version=fallback_metadata.version,
            template=body,
            metadata=fallback_metadata,
        )
        return prompt, list(fallback_metadata.warnings)

    def _apply_loader_validation(self, key: str, prompt: Prompt) -> tuple[Prompt, list[str]]:
        if not (self._config.validation_on_load and self._loader is not None):
            return prompt, self._prompt_warnings(prompt)

        validation = self._loader.validate(prompt)
        if validation.succeeded():
            return prompt, self._prompt_warnings(prompt)

        fallback_metadata = self._fallback_metadata(
            key,
            reason=f"Invalid prompt: {validation.errors}",
        )
        updated_prompt = Prompt(
            name=fallback_metadata.name,
            version=fallback_metadata.version,
            template=prompt.template,
            metadata=prompt.metadata.model_copy(
                update={"warnings": fallback_metadata.warnings}
            ),
        )
        return updated_prompt, list(fallback_metadata.warnings)

    def _prompt_warnings(self, prompt: Prompt) -> list[str]:
        warnings = getattr(prompt.metadata, "warnings", []) or []
        return list(warnings)

    def list(self) -> list[PromptMetadata]:
        files = self._transport.list_files(pattern="**/*.md")
        prompts = []
        for path in files:
            key = self._mapper.to_key_from_path(path, self._config.repository_path)
            prompts.append(self.get(key))
        return [p.metadata for p in prompts]

    def refresh(self) -> None:
        refresh_resp = self._transport.pull_latest()
        for changed in refresh_resp.changed_files:
            changed_path = Path(changed)
            key = self._mapper.to_key_from_path(changed_path, self._config.repository_path)
            self._cache.invalidate(self._make_cache_key(key))

    def _make_cache_key(self, prompt_key: str) -> str:
        commit = self._transport.get_current_commit()
        return f"{prompt_key}@{commit[:8]}"

    def _fallback_metadata(self, key: str, *, reason: str) -> PromptMetadata:
        warning = f"Missing or invalid frontmatter for prompt '{key}': {reason}. {self._EXPECTED_FRONTMATTER}"
        return PromptMetadata(
            prompt_id=key,
            key=key,
            name=key,
            version="0.0.0-invalid",
            description="Auto-generated metadata for prompt without valid frontmatter.",
            role="task",
            task_type="unknown",
            required_variables=[],
            optional_variables=[],
            default_variables={},
            tags=["invalid-metadata"],
            output_contract=PromptOutputContract(mode=PromptOutputMode.text),
            warnings=[warning],
        )

    def _best_effort_body(self, content: str) -> str:
        return extract_best_effort_body(content)

    def _log_warnings(self, key: str, warnings: Sequence[str]) -> None:
        """Surface prompt warnings to help with diagnostics."""
        for warning in warnings:
            logger.warning("Prompt '%s' warning: %s", key, warning)
