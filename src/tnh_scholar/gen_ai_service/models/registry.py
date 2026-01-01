"""Registry domain models for provider metadata.

Defines strongly-typed registry schemas for provider capabilities, pricing,
context limits, and user overrides.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ModelCapabilities(BaseModel):
    """Model capability flags."""

    vision: bool = False
    structured_output: bool = False
    function_calling: bool = False
    streaming: bool = False
    audio_input: bool = False
    audio_output: bool = False


class ModelPricing(BaseModel):
    """Per-model pricing in dollars per 1K tokens for a specific tier."""

    input_per_1k: float = Field(ge=0, description="Input token price per 1K")
    output_per_1k: float = Field(ge=0, description="Output token price per 1K")
    cached_input_per_1k: float | None = Field(
        None, ge=0, description="Cached input price (if supported)"
    )


class ModelPricingTiers(BaseModel):
    """Multi-tier pricing for a model (batch, flex, standard, priority)."""

    batch: ModelPricing | None = Field(None, description="Batch API pricing (50% off)")
    flex: ModelPricing | None = Field(None, description="Flex tier pricing (lower cost, higher latency)")
    standard: ModelPricing = Field(description="Standard tier pricing (default)")
    priority: ModelPricing | None = Field(None, description="Priority tier pricing (faster, higher cost)")


class ModelInfo(BaseModel):
    """Complete model metadata with multi-tier pricing support."""

    display_name: str
    family: str
    capabilities: ModelCapabilities
    context_window: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    pricing_tiers: ModelPricingTiers
    training_cutoff: str | None = None
    released: date | None = None
    deprecated: bool = False
    aliases: list[str] = Field(default_factory=list)

    def get_pricing(
        self, tier: Literal["batch", "flex", "standard", "priority"] = "standard"
    ) -> ModelPricing:
        """Get pricing for a specific tier.

        Args:
            tier: Pricing tier to retrieve (default: standard)

        Returns:
            ModelPricing for the requested tier

        Raises:
            ValueError: If the tier is not available for this model
        """
        tier_pricing: ModelPricing | None = getattr(self.pricing_tiers, tier, None)
        if tier_pricing is None:
            raise ValueError(f"Tier '{tier}' not available for this model")
        return tier_pricing


class ProviderDefaults(BaseModel):
    """Provider-level defaults."""

    base_url: HttpUrl
    timeout_s: float = Field(gt=0, default=60.0)
    max_retries: int = Field(ge=0, default=3)


class RateLimitTier(BaseModel):
    """Rate limit configuration for a tier."""

    requests_per_minute: int = Field(gt=0)
    tokens_per_minute: int = Field(gt=0)


class PricingTierMetadata(BaseModel):
    """Metadata describing a pricing tier."""

    label: str | None = None
    description: str | None = None
    availability: Literal["public", "beta", "internal"] | None = None


class ProviderRegistry(BaseModel):
    """Root registry schema for a provider."""

    schema_ref: str | None = Field(None, alias="$schema")
    schema_version: Literal["1.0"] = "1.0"
    provider: str = Field(min_length=1)
    last_updated: date
    source_url: HttpUrl | None = None
    update_method: Literal["manual", "auto-scrape", "api"] = "manual"
    pricing_tier: Literal["batch", "flex", "standard", "priority"] | None = Field(
        None, description="Default pricing tier documented in this registry"
    )
    pricing_tier_metadata: Dict[str, "PricingTierMetadata"] = Field(default_factory=dict)
    defaults: ProviderDefaults
    models: Dict[str, ModelInfo]
    rate_limits: Dict[str, RateLimitTier] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class PricingOverride(BaseModel):
    """Override for a single tier's pricing."""

    input_per_1k: float | None = Field(None, ge=0)
    output_per_1k: float | None = Field(None, ge=0)
    cached_input_per_1k: float | None = Field(None, ge=0)


class PricingTiersOverride(BaseModel):
    """Override for multi-tier pricing."""

    batch: PricingOverride | None = None
    flex: PricingOverride | None = None
    standard: PricingOverride | None = None
    priority: PricingOverride | None = None


class ModelOverride(BaseModel):
    """Override for a single model's metadata."""

    pricing_tiers: PricingTiersOverride | None = None
    deprecated: bool | None = None


class RegistryOverrides(BaseModel):
    """User overrides for a provider registry."""

    schema_version: Literal["1.0"] = "1.0"
    provider: str
    models: Dict[str, ModelOverride] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
