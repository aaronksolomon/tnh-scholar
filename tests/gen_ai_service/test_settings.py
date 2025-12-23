from __future__ import annotations

from pathlib import Path

import pytest

from tnh_scholar.gen_ai_service.config.settings import GenAISettings

PROMPT_ENV_VARS = ("TNH_PATTERN_DIR", "PROMPT_DIR", "TNH_PROMPT_DIR")


@pytest.fixture(autouse=True)
def clear_prompt_env(monkeypatch):
    """Ensure prompt-dir aliases are unset for each test."""
    for var in PROMPT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.mark.parametrize("env_var", PROMPT_ENV_VARS)
def test_settings_prompt_dir_aliases(env_var: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    alias_dir = tmp_path / env_var.lower()
    alias_dir.mkdir()
    monkeypatch.setenv(env_var, str(alias_dir))

    settings = GenAISettings()

    assert settings.prompt_dir == alias_dir
    assert settings.default_prompt_dir == alias_dir


def test_settings_alias_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    preferred = tmp_path / "tnh_pattern_dir"
    fallback = tmp_path / "prompt_dir"
    legacy = tmp_path / "tnh_prompt_dir"
    for path in (preferred, fallback, legacy):
        path.mkdir()

    # Set all aliases at once and ensure the declared order wins.
    monkeypatch.setenv("TNH_PATTERN_DIR", str(preferred))
    monkeypatch.setenv("PROMPT_DIR", str(fallback))
    monkeypatch.setenv("TNH_PROMPT_DIR", str(legacy))

    settings = GenAISettings()
    assert settings.prompt_dir == preferred

    # Removing the higher-priority alias should expose the next one.
    monkeypatch.delenv("TNH_PATTERN_DIR", raising=False)
    settings = GenAISettings()
    assert settings.prompt_dir == fallback

    monkeypatch.delenv("PROMPT_DIR", raising=False)
    settings = GenAISettings()
    assert settings.prompt_dir == legacy
