from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field, field_validator

from tnh_scholar.cli_tools.tnh_gen.types import ConfigData, ConfigKey, ConfigMeta
from tnh_scholar.gen_ai_service.config.settings import GenAISettings


class CLIConfig(BaseModel):
    """CLI configuration modeled with Pydantic for consistency with OS blueprint."""

    prompt_catalog_dir: Path | None = Field(default=None)
    default_model: str | None = None
    max_dollars: float | None = None
    max_input_chars: int | None = None
    default_temperature: float | None = None
    api_key: str | None = None
    cli_path: str | None = None

    @field_validator("prompt_catalog_dir", mode="before")
    @classmethod
    def _coerce_path(cls, value: Any) -> Any:
        """Normalize prompt catalog value into a Path when provided.

        Args:
            value: Raw value provided for the prompt catalog directory.

        Returns:
            Either the original value or a coerced Path.
        """
        return value if value is None or isinstance(value, Path) else Path(value)

    def with_overrides(self, overrides: ConfigData) -> "CLIConfig":
        """Return a new config with non-null override values applied.

        Args:
            overrides: Mapping of override keys to values.

        Returns:
            New `CLIConfig` instance with overrides applied.
        """
        payload = self.model_dump()
        for key, value in overrides.items():
            if key in payload and value is not None:
                payload[key] = value
        return CLIConfig.model_validate(payload)


def _user_config_path() -> Path:
    """Resolve the user-level config path (respects TNH_GEN_CONFIG_HOME).

    Returns:
        Path to the user config file.
    """
    base = Path(os.getenv("TNH_GEN_CONFIG_HOME", Path.home() / ".config" / "tnh-scholar"))
    return base / "tnh-gen.json"


def _workspace_config_path(cwd: Path | None = None) -> Path:
    """Resolve the workspace config path, preferring VS Code settings if present.

    Args:
        cwd: Optional working directory override.

    Returns:
        Path to the workspace config file.
    """
    root = cwd or Path.cwd()
    vscode_path = root / ".vscode" / "tnh-scholar.json"
    return vscode_path if vscode_path.exists() else root / ".tnh-gen.json"


def _load_json(path: Path) -> ConfigData:
    """Load JSON config data from a file, returning an empty dict when missing.

    Args:
        path: File path to load.

    Returns:
        Parsed JSON object or an empty dict if the file is absent.

    Raises:
        ValueError: If the file exists but does not contain a JSON object.
        json.JSONDecodeError: If the file contains malformed JSON.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Config file {path} must contain a JSON object, not {type(data).__name__}")
        return cast(ConfigData, data)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file {path}") from exc


def load_config(
    config_path: Path | None = None,
    *,
    cwd: Path | None = None,
    overrides: ConfigData | None = None,
) -> tuple[CLIConfig, ConfigMeta]:
    """Load CLI configuration with clear precedence and metadata.

    The effective config is built in this order: defaults/env → user config →
    workspace config → explicit config_path → CLI overrides. Overrides that are
    `None` are ignored to avoid clobbering previous values.

    Args:
        config_path: Optional explicit config file to load.
        cwd: Working directory for resolving workspace config paths.
        overrides: In-memory override values (e.g., CLI flags).

    Returns:
        Tuple of validated `CLIConfig` and metadata containing the source list.

    Raises:
        ValueError: If any referenced config file contains invalid JSON.
    """
    settings = GenAISettings(_env_file=None)  # type: ignore # not handled by pydantic mypy plugin

    base: ConfigData = {
        "prompt_catalog_dir": settings.prompt_dir,
        "default_model": settings.default_model,
        "max_dollars": settings.max_dollars,
        "max_input_chars": settings.max_input_chars,
        "default_temperature": settings.default_temperature,
        "api_key": settings.openai_api_key,
        "cli_path": None,
    }
    sources: list[str] = ["defaults+env"]
    config_files: list[str] = []
    user_config_path = _user_config_path()
    user_config = _load_json(user_config_path)
    if user_config:
        base |= user_config
        sources.append("user")
        config_files.append(str(user_config_path))

    workspace_config_path = _workspace_config_path(cwd)
    if workspace_config := _load_json(workspace_config_path):
        base.update(workspace_config)
        sources.append("workspace")
        config_files.append(str(workspace_config_path))

    if config_path is not None:
        if config_override := _load_json(config_path):
            base.update(config_override)
            sources.append(str(config_path))
            config_files.append(str(config_path))

    if overrides:
        for key, value in overrides.items():
            if key in base and value is not None:
                base[key] = value
        sources.append("cli-overrides")

    meta: ConfigMeta = {"sources": sources, "config_files": config_files}
    return CLIConfig.model_validate(base), meta


def load_config_overrides(
    config_path: Path | None = None,
    *,
    cwd: Path | None = None,
) -> ConfigData:
    """Load only user/workspace/explicit config overrides (no defaults)."""
    combined: ConfigData = {}
    if user_config := _load_json(_user_config_path()):
        combined |= user_config
    if workspace_config := _load_json(_workspace_config_path(cwd)):
        combined.update(workspace_config)
    if config_path is not None:
        if config_override := _load_json(config_path):
            combined.update(config_override)
    return combined


def persist_config_value(
    key: ConfigKey,
    value: Any,
    *,
    workspace: bool = False,
    cwd: Path | None = None,
) -> Path:
    """Persist a single config value to the user or workspace config file.

    Args:
        key: Configuration key to update.
        value: Value to persist.
        workspace: Whether to target workspace scope instead of user scope.
        cwd: Working directory for resolving workspace path.

    Returns:
        Path to the file that was written.

    Raises:
        KeyError: If the key is not supported.
    """
    if key not in CLIConfig.model_fields:
        raise KeyError(f"Unsupported config key: {key}")
    target = _workspace_config_path(cwd) if workspace else _user_config_path()
    current = _load_json(target)
    current[key] = value
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return target


def available_keys() -> list[str]:
    """Return the list of supported config keys.

    Returns:
        List of available configuration keys.
    """
    return list(CLIConfig.model_fields.keys())
