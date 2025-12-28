from __future__ import annotations

import json
from pathlib import Path
from typing import cast
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

app = typer.Typer(help="Inspect and edit tnh-gen configuration.")

CONFIG_KEYS: tuple[ConfigKey, ...] = (
    "prompt_catalog_dir",
    "default_model",
    "max_dollars",
    "max_input_chars",
    "default_temperature",
    "api_key",
    "cli_path",
)
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


def _format_config_text(overrides: ConfigData) -> str:
    if not overrides:
        return ""
    lines = []
    for key in CONFIG_KEYS:
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
    payload: ConfigData = {}
    match key:
        case "prompt_catalog_dir":
            payload["prompt_catalog_dir"] = cast(str | Path | None, value)
        case "default_model":
            payload["default_model"] = cast(str | None, value)
        case "max_dollars":
            payload["max_dollars"] = cast(float | None, value)
        case "max_input_chars":
            payload["max_input_chars"] = cast(int | None, value)
        case "default_temperature":
            payload["default_temperature"] = cast(float | None, value)
        case "api_key":
            payload["api_key"] = cast(str | None, value)
        case "cli_path":
            payload["cli_path"] = cast(str | None, value)
    return payload


def _build_config_value_payload(key: ConfigKey, value: ConfigValue, trace_id: str) -> ConfigValuePayload:
    payload: ConfigValuePayload = {"trace_id": trace_id}
    match key:
        case "prompt_catalog_dir":
            payload["prompt_catalog_dir"] = cast(str | Path | None, value)
        case "default_model":
            payload["default_model"] = cast(str | None, value)
        case "max_dollars":
            payload["max_dollars"] = cast(float | None, value)
        case "max_input_chars":
            payload["max_input_chars"] = cast(int | None, value)
        case "default_temperature":
            payload["default_temperature"] = cast(float | None, value)
        case "api_key":
            payload["api_key"] = cast(str | None, value)
        case "cli_path":
            payload["cli_path"] = cast(str | None, value)
    return payload


def _build_config_update(key: ConfigKey, value: str | float | int) -> ConfigData:
    return _build_config_data_entry(key, value)


def _get_config_value(config: ConfigData, key: ConfigKey) -> ConfigValue:
    match key:
        case "prompt_catalog_dir":
            return cast(str | Path | None, config.get("prompt_catalog_dir"))
        case "default_model":
            return cast(str | None, config.get("default_model"))
        case "max_dollars":
            return cast(float | None, config.get("max_dollars"))
        case "max_input_chars":
            return cast(int | None, config.get("max_input_chars"))
        case "default_temperature":
            return cast(float | None, config.get("default_temperature"))
        case "api_key":
            return cast(str | None, config.get("api_key"))
        case "cli_path":
            return cast(str | None, config.get("cli_path"))
    return None


def _render_show_config(trace_id: str, format_override: OutputFormat | None) -> str:
    validate_global_format(ctx.api, format_override or ctx.output_format)
    if ctx.api:
        config, meta = load_config(ctx.config_path)
        config_dump = cast(ConfigData, config.model_dump(mode="json"))
        payload: ConfigShowPayload = {
            "config": config_dump,
            "sources": meta["sources"],
            "config_files": meta["config_files"],
            "trace_id": trace_id,
        }
        fmt = resolve_output_format(
            api=True,
            format_override=format_override or ctx.output_format,
            default_format=OutputFormat.json,
        )
        return cast(str, render_output(payload, fmt))

    overrides = load_config_overrides(ctx.config_path)
    fmt = _resolve_human_config_format(format_override)
    if fmt == OutputFormat.text:
        return _format_config_text(overrides)
    return cast(str, render_output(overrides, fmt))


def _render_get_config_value(key: str, trace_id: str) -> str:
    validate_global_format(ctx.api, ctx.output_format)
    if key not in available_keys():
        raise KeyError(f"Unknown config key: {key}")
    config_key = cast(ConfigKey, key)
    config, _ = load_config(ctx.config_path)
    config_dump = cast(ConfigData, config.model_dump())
    value = _get_config_value(config_dump, config_key)
    if ctx.api:
        payload = _build_config_value_payload(config_key, value, trace_id)
        fmt = resolve_output_format(
            api=True,
            format_override=ctx.output_format,
            default_format=OutputFormat.json,
        )
        return cast(str, render_output(payload, fmt))
    fmt = _resolve_human_config_format(ctx.output_format)
    if fmt == OutputFormat.text:
        return f"{key}: {value}"
    return cast(str, render_output(_build_config_data_entry(config_key, value), fmt))


def _render_set_config_value(
    key: ConfigKey,
    value: str | float | int,
    target: Path,
    trace_id: str,
) -> str:
    validate_global_format(ctx.api, ctx.output_format)
    updated = _build_config_update(key, value)
    if ctx.api:
        api_payload: ConfigUpdateApiPayload = {
            "status": "succeeded",
            "updated": updated,
            "target": str(target),
            "trace_id": trace_id,
        }
        fmt = resolve_output_format(
            api=True,
            format_override=ctx.output_format,
            default_format=OutputFormat.json,
        )
        return cast(str, render_output(api_payload, fmt))
    fmt = _resolve_human_config_format(ctx.output_format)
    if fmt == OutputFormat.text:
        return f"Updated {key} in {target}"
    human_payload: ConfigUpdatePayload = {"updated": updated, "target": str(target)}
    return cast(str, render_output(human_payload, fmt))


def _render_config_keys(keys: list[str], trace_id: str) -> str:
    validate_global_format(ctx.api, ctx.output_format)
    if ctx.api:
        api_payload: ConfigKeysPayload = {"keys": keys, "trace_id": trace_id}
        fmt = resolve_output_format(
            api=True,
            format_override=ctx.output_format,
            default_format=OutputFormat.json,
        )
        return cast(str, render_output(api_payload, fmt))
    fmt = _resolve_human_config_format(ctx.output_format)
    if fmt == OutputFormat.text:
        return "\n".join(keys)
    human_payload: ConfigKeysHumanPayload = {"keys": keys}
    return cast(str, render_output(human_payload, fmt))


@app.command("show")
def show_config(
    api: bool = typer.Option(False, "--api", help="Machine-readable API contract output."),
    format: OutputFormat | None = typer.Option(
        None, "--format", help="json or yaml.", case_sensitive=False
    ),
):
    """Show the effective configuration and its source precedence.

    Args:
        format: Optional output format override (json or yaml).
    """
    trace_id = uuid4().hex
    try:
        if api:
            ctx.api = True
        typer.echo(_render_show_config(trace_id, format))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id, format_override=format)


@app.command("get")
def get_config_value(
    key: str,
    api: bool = typer.Option(False, "--api", help="Machine-readable API contract output."),
):
    """Retrieve a single config value by key.

    Args:
        key: Configuration key to fetch.
    """
    trace_id = uuid4().hex
    try:
        if api:
            ctx.api = True
        typer.echo(_render_get_config_value(key, trace_id))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id)


@app.command("set")
def set_config_value(
    key: str = typer.Argument(..., help=f"Config key. Supported: {', '.join(available_keys())}"),
    value: str = typer.Argument(..., help="New value for the config key."),
    api: bool = typer.Option(False, "--api", help="Machine-readable API contract output."),
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
        if api:
            ctx.api = True
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
    api: bool = typer.Option(False, "--api", help="Machine-readable API contract output."),
):
    """List available configuration keys supported by the CLI."""
    trace_id = uuid4().hex
    try:
        if api:
            ctx.api = True
        keys = available_keys()
        typer.echo(_render_config_keys(keys, trace_id))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id)
