"""Filesystem-backed prompt catalog adapter."""

from pathlib import Path

from ..config.prompt_catalog_config import PromptCatalogConfig
from ..domain.models import Prompt, PromptMetadata
from ..domain.protocols import PromptCatalogPort
from ..mappers.prompt_mapper import PromptMapper
from ..service.loader import PromptLoader
from ..transport.cache import CacheTransport, InMemoryCacheTransport
from ..transport.filesystem import FilesystemTransport
from ..transport.models import PromptFileRequest


class FilesystemPromptCatalog(PromptCatalogPort):
    """Filesystem-backed catalog for offline/packaged distributions."""

    _EXPECTED_FRONTMATTER = (
        "Expected YAML frontmatter keys: key, name, version, description, task_type, "
        "required_variables, optional_variables, tags, default_variables"
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

    def get(self, key: str) -> Prompt:
        cache_key = self._make_cache_key(key)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        file_path = self._mapper.to_file_request(key, self._config.repository_path)
        request = PromptFileRequest(path=file_path, commit_sha=None)
        file_resp = self._transport.read_file(request)
        try:
            prompt = self._mapper.to_domain_prompt(file_resp.content)
        except Exception as exc:  # noqa: BLE001
            body = self._best_effort_body(file_resp.content)
            fallback_metadata = self._fallback_metadata(key, reason=str(exc))
            prompt = Prompt(
                name=fallback_metadata.name,
                version=fallback_metadata.version,
                template=body,
                metadata=fallback_metadata,
            )
        else:
            if self._config.validation_on_load:
                validation = self._loader.validate(prompt)
                if not validation.succeeded():
                    fallback_metadata = self._fallback_metadata(
                        key,
                        reason=f"Invalid prompt: {validation.errors}",
                    )
                    prompt = Prompt(
                        name=fallback_metadata.name,
                        version=fallback_metadata.version,
                        template=prompt.template,
                        metadata=prompt.metadata.model_copy(update={"warnings": fallback_metadata.warnings}),
                    )

        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def list(self) -> list[PromptMetadata]:
        files = self._transport.list_files(self._config.repository_path, pattern="**/*.md")
        prompts = []
        for path in files:
            key = self._path_to_key(path)
            prompt = self.get(key)
            prompts.append(prompt)
        return [p.metadata for p in prompts]

    def _make_cache_key(self, prompt_key: str) -> str:
        return f"{prompt_key}@filesystem"

    def _path_to_key(self, path: Path) -> str:
        return path.stem

    def _fallback_metadata(self, key: str, *, reason: str) -> PromptMetadata:
        warning = f"Missing or invalid frontmatter for prompt '{key}': {reason}. {self._EXPECTED_FRONTMATTER}"
        return PromptMetadata(
            key=key,
            name=key,
            version="0.0.0-invalid",
            description="Auto-generated metadata for prompt without valid frontmatter.",
            task_type="unknown",
            required_variables=[],
            optional_variables=[],
            default_variables={},
            tags=["invalid-metadata"],
            warnings=[warning],
        )

    def _best_effort_body(self, content: str) -> str:
        cleaned = content.lstrip("\ufeff\n\r\t ")
        # Attempt to peel off frontmatter block even if metadata is empty/invalid.
        try:
            from tnh_scholar.metadata.metadata import Frontmatter

            _, body = Frontmatter.extract(cleaned)
            if body:
                return body.lstrip()
        except Exception:
            pass

        if cleaned.startswith("---"):
            parts = cleaned.split("---", 2)
            if len(parts) == 3:
                return parts[2].lstrip()
        return cleaned
