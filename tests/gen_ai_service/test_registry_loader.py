from __future__ import annotations

from tnh_scholar.gen_ai_service.config.registry import get_registry_loader


def test_openai_registry_includes_gpt54():
    loader = get_registry_loader()

    model_info = loader.get_model("openai", "gpt-5.4")

    assert model_info.family == "gpt-5"
    assert model_info.max_output_tokens == 16384
