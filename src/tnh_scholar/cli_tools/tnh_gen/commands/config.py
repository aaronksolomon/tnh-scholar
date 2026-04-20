from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, cast
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import (
    available_keys,
    load_config,
    load_config_overrides,
    persist_config_value,
)
from tnh_scholar.cli_tools.tnh_gen.errors import exit_with_error
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.output.policy import (
    resolve_output_format,
    validate_global_format,
)
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx
from tnh_scholar.cli_tools.tnh_gen.types import (
    ConfigData,
    ConfigKey,
    ConfigKeysHumanPayload,
    ConfigKeysPayload,
    ConfigShowPayload,
    ConfigUpdateApiPayload,
    ConfigUpdatePayload,
    ConfigValuePayload,
)
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter

app = typer.Typer(help="Inspect and edit tnh-gen configuration.")

ConfigValue = str | Path | float | int | None


def _coerce_for_set(key: ConfigKey, raw: str) -> str | float | int:
    """Cast string CLI values into appropriate config types.

    Args:
        key: Configuration key being updated.
        raw: Raw string value from CLI.

    Returns:
        Value coerced into the expected type for the key.
    """
    if key == "prompt_catalog_dir":
        return str(Path(raw))
    if key in {"max_dollars", "default_temperature"}:
        return float(raw)
    return int(raw) if key == "max_input_chars" else raw


def _resolve_human_config_format(format_override: OutputFormat | None) -> OutputFormat:
    return format_override or ctx.output_format or OutputFormat.yaml


def _get_config_keys() -> tuple[ConfigKey, ...]:
    return cast(tuple[ConfigKey, ...], tuple(available_keys()))


def _format_config_text(overrides: ConfigData) -> str:
    if not overrides:
        return ""
    lines: list[str] = []
    for key in _get_config_keys():
        if key not in overrides:
            continue
        value = cast(ConfigValue, overrides.get(key))
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=True)
        else:
            value_str = str(value)
        lines.append(f"{key}: {value_str}")
    return "\n".join(lines)


def _build_config_data_entry(key: ConfigKey, value: ConfigValue) -> ConfigData:
    match key:
        case "prompt_catalog_dir":
            return {"prompt_catalog_dir": value}
        case "default_model":
            return {"default_model": value}
        case "max_dollars":
            return {"max_dollars": value}
        case "max_input_chars":
            return {"max_input_chars": value}
        case "default_temperature":
            return {"default_temperature": value}
        case "api_key":
            return {"api_key": value}
        case "cli_path":
            return {"cli_path": value}


def _build_config_value_payload(key: ConfigKey, value: ConfigValue, trace_id: str) -> ConfigValuePayload:
    payload: ConfigValuePayload = {"trace_id": trace_id}
    match key:
        case "prompt_catalog_dir":
            payload["prompt_catalog_dir"] = value
        case "default_model":
            payload["default_model"] = value
        case "max_dollars":
            payload["max_dollars"] = value
        case "max_input_chars":
            payload["max_input_chars"] = value
        case "default_temperature":
            payload["default_temperature"] = value
        case "api_key":
            payload["api_key"] = value
        case "cli_path":
            payload["cli_path"] = value
    return payload


def _build_config_update(key: ConfigKey, value: str | float | int) -> ConfigData:
    return _build_config_data_entry(key, value)


def _get_config_value(config: ConfigData, key: ConfigKey) -> ConfigValue:
    match key:
        case "prompt_catalog_dir":
            return config.get("prompt_catalog_dir")
        case "default_model":
            return config.get("default_model")
        case "max_dollars":
            return config.get("max_dollars")
        case "max_input_chars":
            return config.get("max_input_chars")
        case "default_temperature":
            return config.get("default_temperature")
        case "api_key":
            return config.get("api_key")
        case "cli_path":
            return config.get("cli_path")


def _render_config_response(
    *,
    api_payload: Mapping[str, object] | None,
    human_payload: object | None,
    text_fallback: str | None = None,
    format_override: OutputFormat | None = None,
) -> str:
    validate_global_format(ctx.api, format_override or ctx.output_format)
    if ctx.api:
        if api_payload is None:
            raise RuntimeError("API payload is required in API mode")
        fmt = resolve_output_format(
            api=True,
            format_override=format_override or ctx.output_format,
            default_format=OutputFormat.json,
        )
        return cast(str, render_output(api_payload, fmt))

    fmt = _resolve_human_config_format(format_override)
    if fmt == OutputFormat.text and text_fallback is not None:
        return text_fallback
    return cast(str, render_output(human_payload, fmt))


def _render_show_config(trace_id: str, format_override: OutputFormat | None) -> str:
    return _render_show_config_with_health(trace_id, format_override, catalog_health=False)


def _catalog_health_payload(prompts_base: Path | None) -> dict[str, object]:
    if prompts_base is None:
        raise ValueError("No prompt catalog directory configured (set TNH_PROMPT_DIR or config).")
    adapter = PromptsAdapter(prompts_base=prompts_base.expanduser())
    adapter.list_all()
    health = adapter.catalog_health()
    return {
        "errors": [issue.model_dump(mode="json") for issue in health.errors],
        "warnings": [issue.model_dump(mode="json") for issue in health.warnings],
        "error_count": health.error_count,
        "warning_count": health.warning_count,
    }


def _render_show_config_with_health(
    trace_id: str,
    format_override: OutputFormat | None,
    *,
    catalog_health: bool,
) -> str:
    config, meta = load_config(ctx.config_path)
    config_dump = cast(ConfigData, config.model_dump(mode="json"))
    api_payload: ConfigShowPayload = {
        "config": config_dump,
        "sources": meta["sources"],
        "config_files": meta["config_files"],
        "trace_id": trace_id,
    }
    overrides = load_config_overrides(ctx.config_path)
    human_payload: object = overrides
    text_fallback = _format_config_text(overrides)
    if catalog_health:
        health_payload = _catalog_health_payload(config.prompt_catalog_dir)
        api_payload["catalog_health"] = health_payload
        api_payload["catalog_errors"] = health_payload["error_count"]
        human_payload = api_payload
        text_fallback = None
    return _render_config_response(
        api_payload=cast(Mapping[str, object], api_payload),
        human_payload=human_payload,
        text_fallback=text_fallback,
        format_override=format_override,
    )


def _render_get_config_value(key: str, trace_id: str) -> str:
    if key not in available_keys():
        raise KeyError(f"Unknown config key: {key}")
    config_key = cast(ConfigKey, key)
    config, _ = load_config(ctx.config_path)
    config_dump = cast(ConfigData, config.model_dump())
    value = _get_config_value(config_dump, config_key)
    api_payload = _build_config_value_payload(config_key, value, trace_id)
    human_payload = _build_config_data_entry(config_key, value)
    return _render_config_response(
        api_payload=cast(Mapping[str, object], api_payload),
        human_payload=human_payload,
        text_fallback=f"{key}: {value}",
        format_override=ctx.output_format,
    )


def _render_set_config_value(
    key: ConfigKey,
    value: str | float | int,
    target: Path,
    trace_id: str,
) -> str:
    updated = _build_config_update(key, value)
    human_payload: ConfigUpdatePayload = {"updated": updated, "target": str(target)}
    api_payload: ConfigUpdateApiPayload = {
        "status": "succeeded",
        "updated": updated,
        "target": str(target),
        "trace_id": trace_id,
    }
    return _render_config_response(
        api_payload=cast(Mapping[str, object], api_payload),
        human_payload=human_payload,
        text_fallback=f"Updated {key} in {target}",
        format_override=ctx.output_format,
    )


def _render_config_keys(keys: list[str], trace_id: str) -> str:
    human_payload: ConfigKeysHumanPayload = {"keys": keys}
    api_payload: ConfigKeysPayload = {"keys": keys, "trace_id": trace_id}
    return _render_config_response(
        api_payload=cast(Mapping[str, object], api_payload),
        human_payload=human_payload,
        text_fallback="\n".join(keys),
        format_override=ctx.output_format,
    )


@app.command("show")
def show_config(
    catalog_health: bool = typer.Option(
        False,
        "--catalog-health",
        help="Include aggregated prompt catalog health in the response.",
    ),
    format: OutputFormat | None = typer.Option(
        None,
        "--format",
        help="Output format: json (requires --api), yaml, or text (human-only).",
        case_sensitive=False,
    ),
):
    """Show the effective configuration and its source precedence.

    Args:
        format: Optional output format override (json or yaml).
    """
    trace_id = uuid4().hex
    try:
        typer.echo(_render_show_config_with_health(trace_id, format, catalog_health=catalog_health))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id, format_override=format)


@app.command("get")
def get_config_value(
    key: str,
):
    """Retrieve a single config value by key.

    Args:
        key: Configuration key to fetch.
    """
    trace_id = uuid4().hex
    try:
        typer.echo(_render_get_config_value(key, trace_id))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id)


@app.command("set")
def set_config_value(
    key: str = typer.Argument(..., help=f"Config key. Supported: {', '.join(available_keys())}"),
    value: str = typer.Argument(..., help="New value for the config key."),
    workspace: bool = typer.Option(
        False,
        "--workspace",
        help="Persist to workspace config (.vscode/tnh-scholar.json or .tnh-gen.json).",
    ),
):
    """Persist a config value to user or workspace scope.

    Args:
        key: Configuration key to update.
        value: New value to store.
        workspace: Whether to persist to workspace scope.
    """
    trace_id = uuid4().hex
    try:
        if key not in available_keys():
            raise KeyError(f"Unknown config key: {key}")
        config_key = cast(ConfigKey, key)
        coerced = _coerce_for_set(config_key, value)
        target = persist_config_value(config_key, coerced, workspace=workspace)
        typer.echo(_render_set_config_value(config_key, coerced, target, trace_id))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id)


@app.command("list")
def list_config_keys(
):
    """List available configuration keys supported by the CLI."""
    trace_id = uuid4().hex
    try:
        keys = available_keys()
        typer.echo(_render_config_keys(keys, trace_id))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id)
