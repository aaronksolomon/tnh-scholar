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
        prompt = self._mapper.to_domain_prompt(file_resp.content)

        if self._config.validation_on_load:
            validation = self._loader.validate(prompt)
            if not validation.succeeded():
                raise ValueError(f"Invalid prompt: {validation.errors}")

        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def list(self) -> list[PromptMetadata]:
        files = self._transport.list_files(self._config.repository_path, pattern="**/*.md")
        prompts = []
        for path in files:
            key = self._path_to_key(path)
            prompts.append(self.get(key))
        return [p.metadata for p in prompts]

    def _make_cache_key(self, prompt_key: str) -> str:
        return f"{prompt_key}@filesystem"

    def _path_to_key(self, path: Path) -> str:
        return path.stem

