"""Filesystem-backed prompt catalog adapter."""

from __future__ import annotations

from pydantic import ValidationError

from ..config.prompt_catalog_config import PromptCatalogConfig
from ..domain.models import (
    CatalogHealth,
    Prompt,
    PromptMetadata,
    PromptOutputContract,
    PromptOutputMode,
)
from ..domain.protocols import PromptCatalogPort
from ..mappers.prompt_mapper import PromptMapper
from ..service.loader import PromptLoader
from ..transport.cache import CacheTransport, InMemoryCacheTransport
from ..transport.filesystem import FilesystemTransport
from ..transport.models import PromptFileRequest
from .frontmatter_fallback import extract_best_effort_body


class FilesystemPromptCatalog(PromptCatalogPort):
    """Filesystem-backed catalog for offline/packaged distributions."""

    _EXPECTED_FRONTMATTER = (
        "Expected prompt envelope keys include prompt_id/key, name, version, description, "
        "role/task_type, inputs/required_variables, and output_contract/output_mode."
    )

    def __init__(
        self,
        config: PromptCatalogConfig,
        mapper: PromptMapper,
        loader: PromptLoader,
        cache: CacheTransport[Prompt] | None = None,
        transport: FilesystemTransport | None = None,
    ):
        self._config = config
        self._mapper = mapper
        self._loader = loader
        self._cache = cache or InMemoryCacheTransport(default_ttl_s=config.cache_ttl_s)
        self._transport = transport or FilesystemTransport(mapper)
        self._health = CatalogHealth()

    def get(self, key: str) -> Prompt:
        cache_key = self._make_cache_key(key)
        if cached := self._cache.get(cache_key):
            return cached

        file_path = self._mapper.to_file_request(key, self._config.repository_path)
        request = PromptFileRequest(path=file_path, commit_sha=None)
        file_resp = self._transport.read_file(request)
        prompt = self._load_prompt_from_content(key, file_resp.content, health=self._health)
        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def list(self) -> list[PromptMetadata]:
        files = self._transport.list_files(self._config.repository_path, pattern="**/*.md")
        health = CatalogHealth()
        prompts = []
        for path in files:
            key = self._mapper.to_key_from_path(path, self._config.repository_path)
            request = PromptFileRequest(
                path=self._mapper.to_file_request(key, self._config.repository_path),
                commit_sha=None,
            )
            file_resp = self._transport.read_file(request)
            prompt = self._load_prompt_from_content(key, file_resp.content, health=health)
            self._cache.set(self._make_cache_key(key), prompt, ttl_s=self._config.cache_ttl_s)
            prompts.append(prompt)
        self._health = health
        return [p.metadata for p in prompts]

    def _load_prompt_from_content(
        self,
        key: str,
        content: str,
        *,
        health: CatalogHealth,
    ) -> Prompt:
        try:
            prompt = self._mapper.to_domain_prompt(content, source_key=key)
        except (ValidationError, ValueError) as exc:
            body = self._best_effort_body(content)
            fallback_metadata = self._fallback_metadata(key, reason=str(exc))
            health.errors.append(self._loader.parse_error_issue(key, str(exc)))
            prompt = Prompt(
                name=fallback_metadata.name,
                version=fallback_metadata.version,
                template=body,
                metadata=fallback_metadata,
            )
            warnings = list(fallback_metadata.warnings)
        else:
            warnings = self._apply_validation_warnings(key, prompt, health)

        if warnings:
            health.warnings.extend(self._loader.warning_issues(key, warnings))
        return prompt

    def _apply_validation_warnings(
        self,
        key: str,
        prompt: Prompt,
        health: CatalogHealth,
    ) -> list[str]:
        if not self._config.validation_on_load:
            return list(getattr(prompt.metadata, "warnings", []) or [])

        validation = self._loader.validate(prompt)
        if validation.succeeded():
            return list(getattr(prompt.metadata, "warnings", []) or [])

        health.errors.extend(self._loader.validation_issues(key, validation))
        fallback_metadata = self._fallback_metadata(
            key,
            reason=f"Invalid prompt: {validation.errors}",
        )
        prompt.metadata = prompt.metadata.model_copy(
            update={"warnings": fallback_metadata.warnings}
        )
        return list(fallback_metadata.warnings)

    def _make_cache_key(self, prompt_key: str) -> str:
        return f"{prompt_key}@filesystem"

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

    def catalog_health(self) -> CatalogHealth:
        """Return the accumulated catalog health report."""
        return self._health.model_copy(deep=True)
