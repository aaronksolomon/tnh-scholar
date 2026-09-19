"""Override merging service for provider registries."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from tnh_scholar.gen_ai_service.adapters.registry.jsonc_parser import JsoncParser
from tnh_scholar.gen_ai_service.models.registry import (
    ModelInfo,
    ModelOverride,
    ModelPricing,
    PricingOverride,
    PricingTiersOverride,
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

        if model_override.pricing_tiers:
            self._apply_pricing_overrides(model_info, model_override.pricing_tiers)

        if model_override.request_profile is not None:
            model_info.request_profile = model_override.request_profile

        # Apply deprecated flag
        if model_override.deprecated is not None:
            model_info.deprecated = model_override.deprecated

    def _apply_pricing_overrides(self, model: ModelInfo, overrides: PricingTiersOverride) -> None:
        """Apply typed pricing overrides only to existing tiers."""
        for tier_name in PricingTiersOverride.model_fields:
            override = getattr(overrides, tier_name)
            pricing = getattr(model.pricing_tiers, tier_name)
            if override is not None and pricing is not None:
                self._apply_tier_override(pricing, override)

    @staticmethod
    def _apply_tier_override(pricing: ModelPricing, override: PricingOverride) -> None:
        """Copy explicitly supplied pricing values without clearing existing metadata."""
        if override.input_per_1k is not None:
            pricing.input_per_1k = override.input_per_1k
        if override.output_per_1k is not None:
            pricing.output_per_1k = override.output_per_1k
        if override.cached_input_per_1k is not None:
            pricing.cached_input_per_1k = override.cached_input_per_1k
        if override.cache_write_input_per_1k is not None:
            pricing.cache_write_input_per_1k = override.cache_write_input_per_1k
        if override.long_context is not None:
            pricing.long_context = override.long_context
