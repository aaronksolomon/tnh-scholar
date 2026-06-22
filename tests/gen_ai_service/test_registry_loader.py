from __future__ import annotations

from tnh_scholar.gen_ai_service.config.registry import get_registry_loader


def test_openai_registry_includes_gpt54():
    loader = get_registry_loader()

    model_info = loader.get_model("openai", "gpt-5.4")

    assert model_info.family == "gpt-5"
    assert model_info.context_window == 1_050_000
    assert model_info.max_output_tokens == 128_000


def test_openai_registry_includes_gpt55():
    loader = get_registry_loader()

    model_info = loader.get_model("openai", "gpt-5.5")

    assert model_info.family == "gpt-5"
    assert model_info.context_window == 1_050_000
    assert model_info.max_output_tokens == 128_000
    assert "gpt-5.5-latest" in model_info.aliases
