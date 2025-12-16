from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tnh_scholar.gen_ai_service.config.settings import Settings

# Config keys exposed by the CLI.
CONFIG_KEYS: dict[str, type] = {
    "prompt_catalog_dir": Path,
    "default_model": str,
    "max_dollars": float,
    "max_input_chars": int,
    "default_temperature": float,
    "api_key": str,
    "cli_path": str,
}


def _user_config_path() -> Path:
    base = Path(os.getenv("TNH_GEN_CONFIG_HOME", Path.home() / ".config" / "tnh-scholar"))
    return base / "tnh-gen.json"


def _workspace_config_path(cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    vscode_path = root / ".vscode" / "tnh-scholar.json"
    if vscode_path.exists():
        return vscode_path
    return root / ".tnh-gen.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file {path}") from exc


def _coerce_value(key: str, value: Any) -> Any:
    target_type = CONFIG_KEYS.get(key)
    if target_type is None:
        return value
    if value is None:
        return None
    if target_type is Path:
        return Path(value)
    try:
        return target_type(value)
    except Exception as exc:
        raise ValueError(f"Invalid value for {key}: {value!r}") from exc


@dataclass
class CLIConfig:
    prompt_catalog_dir: Path | None
    default_model: str | None
    max_dollars: float | None
    max_input_chars: int | None
    default_temperature: float | None
    api_key: str | None
    cli_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CLIConfig":
        coalesced: dict[str, Any] = {}
        for key in CONFIG_KEYS:
            coalesced[key] = _coerce_value(key, data.get(key))
        return cls(**coalesced)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_catalog_dir": str(self.prompt_catalog_dir) if self.prompt_catalog_dir else None,
            "default_model": self.default_model,
            "max_dollars": self.max_dollars,
            "max_input_chars": self.max_input_chars,
            "default_temperature": self.default_temperature,
            "api_key": self.api_key,
            "cli_path": self.cli_path,
        }

    def with_overrides(self, overrides: dict[str, Any]) -> "CLIConfig":
        payload = self.to_dict()
        for key, value in overrides.items():
            if key in CONFIG_KEYS and value is not None:
                payload[key] = value
        return CLIConfig.from_dict(payload)


def load_config(
    config_path: Path | None = None,
    *,
    cwd: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> tuple[CLIConfig, dict[str, Any]]:
    """
    Load configuration using precedence: CLI file override > workspace > user > env/defaults.

    Returns (config, meta) where meta contains the applied source list.
    """
    sources: list[str] = []
    settings = Settings(_env_file=None)

    base: dict[str, Any] = {
        "prompt_catalog_dir": settings.prompt_dir,
        "default_model": settings.default_model,
        "max_dollars": settings.max_dollars,
        "max_input_chars": settings.max_input_chars,
        "default_temperature": settings.default_temperature,
        "api_key": settings.openai_api_key,
        "cli_path": None,
    }
    sources.append("defaults+env")

    user_config = _load_json(_user_config_path())
    if user_config:
        base.update(user_config)
        sources.append("user")

    workspace_config = _load_json(_workspace_config_path(cwd))
    if workspace_config:
        base.update(workspace_config)
        sources.append("workspace")

    if config_path is not None:
        config_override = _load_json(config_path)
        if config_override:
            base.update(config_override)
            sources.append(str(config_path))

    if overrides:
        for key, value in overrides.items():
            if key in CONFIG_KEYS and value is not None:
                base[key] = value
        sources.append("cli-overrides")

    return CLIConfig.from_dict(base), {"sources": sources}


def persist_config_value(key: str, value: Any, *, workspace: bool = False, cwd: Path | None = None) -> Path:
    if key not in CONFIG_KEYS:
        raise KeyError(f"Unsupported config key: {key}")
    target = _workspace_config_path(cwd) if workspace else _user_config_path()
    current = _load_json(target)
    current[key] = value
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return target


def available_keys() -> list[str]:
    return list(CONFIG_KEYS.keys())
