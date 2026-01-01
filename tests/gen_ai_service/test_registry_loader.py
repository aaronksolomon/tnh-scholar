from __future__ import annotations

from pathlib import Path

from tnh_scholar.gen_ai_service.config.registry import RegistryLoader, RegistryPaths


def test_registry_loader_reads_builtin_openai() -> None:
    loader = RegistryLoader()
    model_info = loader.get_model("openai", "gpt-5-mini")

    assert model_info.context_window > 0
    assert model_info.get_pricing("standard").input_per_1k >= 0


def test_registry_loader_applies_overrides(tmp_path: Path) -> None:
    provider_dir = tmp_path / "providers"
    override_dir = tmp_path / "overrides"
    provider_dir.mkdir()
    override_dir.mkdir()

    provider_path = provider_dir / "openai.jsonc"
    override_path = override_dir / "openai.jsonc"

    provider_path.write_text(
        """
        {
          "schema_version": "1.0",
          "provider": "openai",
          "last_updated": "2025-12-31",
          "defaults": {
            "base_url": "https://api.openai.com/v1",
            "timeout_s": 60.0,
            "max_retries": 3
          },
          "models": {
            "gpt-test": {
              "display_name": "GPT Test",
              "family": "gpt-test",
              "capabilities": {
                "vision": false,
                "structured_output": false,
                "function_calling": true,
                "streaming": true
              },
              "context_window": 1024,
              "max_output_tokens": 512,
              "pricing_tiers": {
                "standard": {
                  "input_per_1k": 0.01,
                  "output_per_1k": 0.02
                }
              },
              "deprecated": false
            }
          }
        }
        """,
        encoding="utf-8",
    )
    override_path.write_text(
        """
        {
          "schema_version": "1.0",
          "provider": "openai",
          "models": {
            "gpt-test": {
              "pricing_tiers": {
                "standard": {
                  "input_per_1k": 0.05
                }
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )

    paths = RegistryPaths(provider_dirs=(provider_dir,), override_dirs=(override_dir,))
    loader = RegistryLoader(registry_paths=paths)
    model_info = loader.get_model("openai", "gpt-test")

    pricing = model_info.get_pricing("standard")
    assert pricing.input_per_1k == 0.05
    assert pricing.output_per_1k == 0.02
