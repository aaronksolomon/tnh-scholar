from __future__ import annotations

from pathlib import Path

from tnh_scholar.gen_ai_service.config.registry import RegistryLoader, RegistryPaths


def test_registry_staleness_warning_emitted(
    tmp_path: Path, caplog, monkeypatch
) -> None:
    provider_dir = tmp_path / "providers"
    override_dir = tmp_path / "overrides"
    provider_dir.mkdir()
    override_dir.mkdir()

    registry_path = provider_dir / "openai.jsonc"
    registry_path.write_text(
        """
        {
          "schema_version": "1.0",
          "provider": "openai",
          "last_updated": "2000-01-01",
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

    monkeypatch.setenv("REGISTRY_STALENESS_WARN", "true")
    monkeypatch.setenv("REGISTRY_STALENESS_THRESHOLD_DAYS", "1")

    caplog.set_level("WARNING")
    paths = RegistryPaths(provider_dirs=(provider_dir,), override_dirs=(override_dir,))
    loader = RegistryLoader(registry_paths=paths)
    loader.get_provider("openai")

    assert "Registry pricing for 'openai' is" in caplog.text
