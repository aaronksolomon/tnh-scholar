from __future__ import annotations

from pathlib import Path

import pytest

from tnh_scholar.configuration.context import TNHContext
from tnh_scholar.gen_ai_service.config.settings import GenAISettings

PROMPT_ENV_VARS = ("PROMPT_DIR", "TNH_PROMPT_DIR")


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

    settings = GenAISettings(_env_file=None)

    assert settings.prompt_dir == alias_dir
    assert settings.default_prompt_dir == alias_dir


def test_settings_alias_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    preferred = tmp_path / "prompt_dir"
    fallback = tmp_path / "tnh_prompt_dir"
    for path in (preferred, fallback):
        path.mkdir()

    # Set all aliases at once and ensure the declared order wins.
    monkeypatch.setenv("PROMPT_DIR", str(preferred))
    monkeypatch.setenv("TNH_PROMPT_DIR", str(fallback))

    settings = GenAISettings(_env_file=None)
    assert settings.prompt_dir == preferred

    # Removing the higher-priority alias should expose the next one.
    monkeypatch.delenv("PROMPT_DIR", raising=False)
    settings = GenAISettings(_env_file=None)
    assert settings.prompt_dir == fallback


def test_settings_prompt_dir_defaults_to_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_root = tmp_path / "workspace"
    user_root = tmp_path / "user"
    builtin_root = tmp_path / "builtin"

    (workspace_root / "prompts").mkdir(parents=True)
    (user_root / "prompts").mkdir(parents=True)
    (builtin_root / "prompts").mkdir(parents=True)

    context = TNHContext(
        builtin_root=builtin_root,
        workspace_root=workspace_root,
        user_root=user_root,
        correlation_id="corr",
        session_id="sess",
    )

    monkeypatch.setattr(
        TNHContext,
        "discover",
        classmethod(lambda cls, **kwargs: context),
    )

    settings = GenAISettings(_env_file=None)
    assert settings.prompt_dir == workspace_root / "prompts"
