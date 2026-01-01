"""Registry loader for provider metadata."""

from __future__ import annotations

import json
import logging
from datetime import date
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from pydantic import ValidationError as PydanticValidationError

from tnh_scholar.configuration.context import TNHContext
from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.gen_ai_service.adapters.registry.jsonc_parser import JsoncParser
from tnh_scholar.gen_ai_service.adapters.registry.override_merger import OverrideMerger
from tnh_scholar.gen_ai_service.config.settings import get_registry_staleness_config
from tnh_scholar.gen_ai_service.models.registry import ModelInfo, ProviderRegistry


@dataclass(frozen=True)
class RegistryPaths:
    """Resolved registry and override directories."""

    provider_dirs: tuple[Path, ...]
    override_dirs: tuple[Path, ...]


class RegistryPathResolver:
    """Resolves registry and override file paths."""

    def __init__(self, paths: RegistryPaths) -> None:
        self._paths = paths

    def provider_paths(self, provider: str) -> list[Path]:
        return [path / f"{provider}.jsonc" for path in self._paths.provider_dirs]

    def override_paths(self, provider: str) -> list[Path]:
        return [path / f"{provider}.jsonc" for path in self._paths.override_dirs]

    def find_provider_path(self, provider: str) -> Path | None:
        return next((path for path in self.provider_paths(provider) if path.exists()), None)


class RegistryCache:
    """In-memory cache for provider registries."""

    def __init__(self) -> None:
        self._items: dict[str, ProviderRegistry] = {}

    def get(self, provider: str) -> ProviderRegistry | None:
        return self._items.get(provider)

    def set(self, provider: str, registry: ProviderRegistry) -> None:
        self._items[provider] = registry


class RegistryProviderIndex:
    """Enumerates provider registries from search paths."""

    def __init__(self, provider_dirs: Iterable[Path]) -> None:
        self._provider_dirs = tuple(provider_dirs)

    def providers(self) -> list[str]:
        names: set[str] = set()
        for directory in self._provider_dirs:
            if directory.exists():
                names.update(self._provider_names(directory))
        return sorted(names)

    def _provider_names(self, directory: Path) -> Iterable[str]:
        for entry in directory.glob("*.jsonc"):
            yield entry.stem


class RegistryLoader:
    """Loads and caches provider registries from JSONC files."""

    def __init__(
        self,
        *,
        context: TNHContext | None = None,
        registry_paths: RegistryPaths | None = None,
        parser: JsoncParser | None = None,
        merger: OverrideMerger | None = None,
    ) -> None:
        self._context = context or TNHContext.discover()
        self._paths = registry_paths or self._resolve_paths(self._context)
        self._resolver = RegistryPathResolver(self._paths)
        self._parser = parser or JsoncParser()
        self._merger = merger or OverrideMerger()
        self._cache = RegistryCache()
        self._providers = RegistryProviderIndex(self._paths.provider_dirs)

    def get_provider(self, provider: str) -> ProviderRegistry:
        if cached := self._cache.get(provider):
            return cached
        registry = self._load_provider(provider)
        self._check_staleness(provider, registry)
        self._cache.set(provider, registry)
        return registry

    def get_model(self, provider: str, model: str) -> ModelInfo:
        registry = self.get_provider(provider)
        if model in registry.models:
            return registry.models[model]
        return self._resolve_alias(registry, provider, model)

    def list_providers(self) -> list[str]:
        return self._providers.providers()

    def find_model(self, model: str) -> ModelInfo:
        for provider in self.list_providers():
            if info := self._find_model_in_provider(provider, model):
                return info
        raise ConfigurationError(f"Model {model} not found in any provider registry.")

    def _load_provider(self, provider: str) -> ProviderRegistry:
        registry_path = self._registry_path(provider)
        registry = self._parse_registry(registry_path)
        overrides = self._resolver.override_paths(provider)
        return self._merger.apply_overrides(registry, overrides, self._parser)

    def _registry_path(self, provider: str) -> Path:
        path = self._resolver.find_provider_path(provider)
        if path is None:
            raise ConfigurationError(f"Provider registry not found: {provider}")
        return path

    def _parse_registry(self, registry_path: Path) -> ProviderRegistry:
        data = self._parse_jsonc(registry_path)
        try:
            return ProviderRegistry.model_validate(data)
        except PydanticValidationError as exc:
            message = f"Invalid provider registry {registry_path}: {exc}"
            raise ConfigurationError(message) from exc

    def _parse_jsonc(self, registry_path: Path) -> dict[str, object]:
        try:
            result: dict[str, object] = self._parser.parse_file(registry_path)
            return result
        except json.JSONDecodeError as exc:
            message = f"Invalid JSON in registry {registry_path}: {exc}"
            raise ConfigurationError(message) from exc

    def _resolve_alias(
        self,
        registry: ProviderRegistry,
        provider: str,
        model: str,
    ) -> ModelInfo:
        for model_name, info in registry.models.items():
            if model in info.aliases:
                return info
        available = ", ".join(registry.models.keys())
        raise ConfigurationError(
            f"Model {model} not found in {provider} registry. Available: {available}"
        )

    def _find_model_in_provider(self, provider: str, model: str) -> ModelInfo | None:
        registry = self.get_provider(provider)
        if model in registry.models:
            return registry.models[model]
        return next(
            (info for info in registry.models.values() if model in info.aliases),
            None,
        )

    def _resolve_paths(self, context: TNHContext) -> RegistryPaths:
        provider_dirs = tuple(context.get_registry_search_paths("providers"))
        override_dirs = tuple(context.get_registry_search_paths("overrides"))
        return RegistryPaths(provider_dirs=provider_dirs, override_dirs=override_dirs)

    def _check_staleness(self, provider: str, registry: ProviderRegistry) -> None:
        config = get_registry_staleness_config()
        if not config.warn or config.threshold_days <= 0:
            return
        age_days = (date.today() - registry.last_updated).days
        if age_days <= config.threshold_days:
            return
        logger = logging.getLogger(__name__)
        message = (
            f"Registry pricing for '{provider}' is {age_days} days old "
            f"(threshold: {config.threshold_days} days). Pricing may be inaccurate. "
            f"Update recommended: {registry.source_url or 'manual update required'}"
        )
        logger.warning(message)


@lru_cache(maxsize=1)
def get_registry_loader() -> RegistryLoader:
    """Get a singleton registry loader."""

    return RegistryLoader()


def get_model_info(provider: str, model: str) -> ModelInfo:
    """Get model info for a provider and model."""

    return get_registry_loader().get_model(provider, model)


def find_model_info(model: str) -> ModelInfo:
    """Get model info by searching across providers."""

    return get_registry_loader().find_model(model)


def list_models(provider: str) -> list[str]:
    """List available models for a provider."""

    registry = get_registry_loader().get_provider(provider)
    return list(registry.models.keys())
