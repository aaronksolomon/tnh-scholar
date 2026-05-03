"""Git-backed prompt catalog adapter."""

from __future__ import annotations

from pathlib import Path

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
from ..transport.git_client import GitTransportClient
from ..transport.models import PromptFileRequest
from .frontmatter_fallback import extract_best_effort_body


class GitPromptCatalog(PromptCatalogPort):
    """Git-backed prompt catalog adapter (implements PromptCatalogPort)."""

    _EXPECTED_FRONTMATTER = (
        "Expected prompt envelope keys include prompt_id/key, name, version, description, "
        "role/task_type, inputs/required_variables, and output_contract/output_mode."
    )
    _IGNORED_FILENAMES = frozenset({"readme.md"})

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
        self._health = CatalogHealth()

    def get(self, key: str) -> Prompt:
        cache_key = self._make_cache_key(key)
        if cached := self._cache.get(cache_key):
            return cached

        file_req = self._build_file_request(key)
        file_resp = self._transport.read_file_at_commit(file_req)
        prompt = self._load_prompt_from_content(key, file_resp.content, health=self._health)
        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def _build_file_request(self, key: str) -> PromptFileRequest:
        return PromptFileRequest(
            path=self._mapper.to_file_request(key, self._config.repository_path),
            commit_sha=None,
        )

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
            return self._build_prompt_from_invalid_file(key, content, reason=str(exc), health=health)
        warnings = self._apply_loader_validation(key, prompt, health=health)
        if warnings:
            health.warnings.extend(self._loader.warning_issues(key, warnings))
        return prompt

    def _build_prompt_from_invalid_file(
        self,
        key: str,
        content: str,
        *,
        reason: str,
        health: CatalogHealth,
    ) -> Prompt:
        body = self._best_effort_body(content)
        fallback_metadata = self._fallback_metadata(key, reason=reason)
        health.errors.append(self._loader.parse_error_issue(key, reason))
        prompt = Prompt(
            name=fallback_metadata.name,
            version=fallback_metadata.version,
            template=body,
            metadata=fallback_metadata,
        )
        health.warnings.extend(self._loader.warning_issues(key, list(fallback_metadata.warnings)))
        return prompt

    def _apply_loader_validation(
        self,
        key: str,
        prompt: Prompt,
        *,
        health: CatalogHealth,
    ) -> list[str]:
        if not (self._config.validation_on_load and self._loader is not None):
            return self._prompt_warnings(prompt)

        validation = self._loader.validate(prompt)
        if validation.succeeded():
            return self._prompt_warnings(prompt)

        health.errors.extend(self._loader.validation_issues(key, validation))
        fallback_metadata = self._fallback_metadata(
            key,
            reason=f"Invalid prompt: {validation.errors}",
        )
        prompt.metadata = prompt.metadata.model_copy(update={"warnings": fallback_metadata.warnings})
        return list(fallback_metadata.warnings)

    def _prompt_warnings(self, prompt: Prompt) -> list[str]:
        warnings = getattr(prompt.metadata, "warnings", []) or []
        return list(warnings)

    def list(self) -> list[PromptMetadata]:
        files = self._transport.list_files(pattern="**/*.md")
        health = CatalogHealth()
        prompts = []
        for path in files:
            if self._should_ignore_path(path):
                continue
            key = self._mapper.to_key_from_path(path, self._config.repository_path)
            file_req = self._build_file_request(key)
            file_resp = self._transport.read_file_at_commit(file_req)
            prompt = self._load_prompt_from_content(key, file_resp.content, health=health)
            self._cache.set(self._make_cache_key(key), prompt, ttl_s=self._config.cache_ttl_s)
            prompts.append(prompt)
        self._health = health
        return [p.metadata for p in prompts]

    def refresh(self) -> None:
        refresh_resp = self._transport.pull_latest()
        self._health = CatalogHealth()
        for changed in refresh_resp.changed_files:
            changed_path = Path(changed)
            key = self._mapper.to_key_from_path(changed_path, self._config.repository_path)
            self._cache.invalidate(self._make_cache_key(key))

    def catalog_health(self) -> CatalogHealth:
        """Return the accumulated catalog health report."""
        return self._health.model_copy(deep=True)

    def _make_cache_key(self, prompt_key: str) -> str:
        commit = self._transport.get_current_commit()
        return f"{prompt_key}@{commit[:8]}"

    def _fallback_metadata(self, key: str, *, reason: str) -> PromptMetadata:
        warning = (
            f"Missing or invalid frontmatter for prompt '{key}': {reason}. "
            f"{self._EXPECTED_FRONTMATTER}"
        )
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

    def _should_ignore_path(self, path: Path) -> bool:
        return path.name.lower() in self._IGNORED_FILENAMES
