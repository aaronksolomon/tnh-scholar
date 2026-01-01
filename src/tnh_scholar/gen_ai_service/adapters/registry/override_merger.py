"""Override merging service for provider registries."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from tnh_scholar.gen_ai_service.adapters.registry.jsonc_parser import JsoncParser
from tnh_scholar.gen_ai_service.models.registry import (
    ModelOverride,
    ProviderRegistry,
    RegistryOverrides,
)


class OverrideMerger:
    """Service for merging user overrides into provider registries."""

    def apply_overrides(
        self,
        registry: ProviderRegistry,
        override_paths: Iterable[Path],
        parser: JsoncParser,
    ) -> ProviderRegistry:
        """Apply overrides from one or more files to a registry.

        Args:
            registry: Base registry to apply overrides to.
            override_paths: Ordered override file paths.
            parser: JSONC parser for loading override files.

        Returns:
            Registry with overrides applied.
        """
        for override_path in override_paths:
            if override_path.exists():
                self._apply_override_file(registry, override_path, parser)
        return registry

    def _apply_override_file(
        self,
        registry: ProviderRegistry,
        override_path: Path,
        parser: JsoncParser,
    ) -> None:
        data = parser.parse_file(override_path)
        overrides = RegistryOverrides.model_validate(data)
        self._merge_models(registry, overrides)

    def _merge_models(
        self,
        registry: ProviderRegistry,
        overrides: RegistryOverrides,
    ) -> None:
        for model_name, model_override in overrides.models.items():
            if model_name not in registry.models:
                continue
            self._apply_model_override(registry, model_name, model_override)

    def _apply_model_override(
        self,
        registry: ProviderRegistry,
        model_name: str,
        model_override: ModelOverride,
    ) -> None:
        model_info = registry.models[model_name]

        # Apply pricing tier overrides
        if model_override.pricing_tiers:
            tiers_override = model_override.pricing_tiers
            for tier_name in ["batch", "flex", "standard", "priority"]:
                tier_override = getattr(tiers_override, tier_name, None)
                if tier_override is None:
                    continue

                # Get the existing tier pricing
                tier_pricing = getattr(model_info.pricing_tiers, tier_name, None)
                if tier_pricing is None:
                    continue

                # Apply overrides
                if tier_override.input_per_1k is not None:
                    tier_pricing.input_per_1k = tier_override.input_per_1k
                if tier_override.output_per_1k is not None:
                    tier_pricing.output_per_1k = tier_override.output_per_1k
                if tier_override.cached_input_per_1k is not None:
                    tier_pricing.cached_input_per_1k = tier_override.cached_input_per_1k

        # Apply deprecated flag
        if model_override.deprecated is not None:
            model_info.deprecated = model_override.deprecated
