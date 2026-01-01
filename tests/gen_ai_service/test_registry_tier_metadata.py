from __future__ import annotations

from tnh_scholar.gen_ai_service.config.registry import RegistryLoader


def test_registry_pricing_tier_metadata_loaded() -> None:
    loader = RegistryLoader()
    registry = loader.get_provider("openai")

    assert registry.pricing_tier == "standard"
    metadata = registry.pricing_tier_metadata
    assert "standard" in metadata
    assert metadata["standard"].availability == "public"
