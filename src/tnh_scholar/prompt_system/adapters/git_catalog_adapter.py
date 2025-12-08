"""Git-backed prompt catalog adapter."""

from pathlib import Path

from ..config.prompt_catalog_config import PromptCatalogConfig
from ..domain.models import Prompt, PromptMetadata
from ..domain.protocols import PromptCatalogPort
from ..mappers.prompt_mapper import PromptMapper
from ..service.loader import PromptLoader
from ..transport.cache import CacheTransport, InMemoryCacheTransport
from ..transport.git_client import GitTransportClient
from ..transport.models import PromptFileRequest


class GitPromptCatalog(PromptCatalogPort):
    """Git-backed prompt catalog adapter (implements PromptCatalogPort)."""

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
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        file_req = PromptFileRequest(
            path=self._mapper.to_file_request(key, self._config.repository_path),
            commit_sha=None,
        )
        file_resp = self._transport.read_file_at_commit(file_req)
        prompt = self._mapper.to_domain_prompt(file_resp.content)

        if self._config.validation_on_load and self._loader is not None:
            validation = self._loader.validate(prompt)
            if not validation.succeeded():
                raise ValueError(f"Invalid prompt: {validation.errors}")

        self._cache.set(cache_key, prompt, ttl_s=self._config.cache_ttl_s)
        return prompt

    def list(self) -> list[PromptMetadata]:
        files = self._transport.list_files(pattern="**/*.md")
        prompts = []
        for path in files:
            key = self._path_to_key(path)
            prompts.append(self.get(key))
        return [p.metadata for p in prompts]

    def refresh(self) -> None:
        refresh_resp = self._transport.pull_latest()
        for changed in refresh_resp.changed_files:
            key = self._path_to_key(Path(changed))
            self._cache.invalidate(self._make_cache_key(key))

    def _make_cache_key(self, prompt_key: str) -> str:
        commit = self._transport.get_current_commit()
        return f"{prompt_key}@{commit[:8]}"

    def _path_to_key(self, path: Path) -> str:
        return path.stem
