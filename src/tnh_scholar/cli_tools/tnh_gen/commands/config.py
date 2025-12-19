from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import (
    available_keys,
    load_config,
    persist_config_value,
)
from tnh_scholar.cli_tools.tnh_gen.errors import error_response
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx

app = typer.Typer(help="Inspect and edit tnh-gen configuration.")


def _coerce_for_set(key: str, raw: str) -> str | float | int:
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


@app.command("show")
def show_config(
    format: OutputFormat | None = typer.Option(
        None, "--format", help="json (default) or yaml.", case_sensitive=False
    ),
):
    """Show the effective configuration and its source precedence.

    Args:
        format: Optional output format override (json or yaml).
    """
    correlation_id = uuid4().hex
    try:
        config, meta = load_config(ctx.config_path)
        payload = {"config": config.model_dump(),
                   "sources": meta["sources"], 
                   "correlation_id": correlation_id,
                   }
        fmt = format or ctx.output_format
        typer.echo(render_output(payload, fmt))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc


@app.command("get")
def get_config_value(key: str):
    """Retrieve a single config value by key.

    Args:
        key: Configuration key to fetch.
    """
    correlation_id = uuid4().hex
    try:
        if key not in available_keys():
            raise KeyError(f"Unknown config key: {key}")
        config, _ = load_config(ctx.config_path)
        payload = {key: config.model_dump().get(key), "correlation_id": correlation_id}
        typer.echo(render_output(payload, ctx.output_format))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc


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
    correlation_id = uuid4().hex
    try:
        if key not in available_keys():
            raise KeyError(f"Unknown config key: {key}")
        coerced = _coerce_for_set(key, value)
        target = persist_config_value(key, coerced, workspace=workspace)
        payload = {
            "status": "succeeded",
            "updated": {key: coerced},
            "target": str(target),
            "correlation_id": correlation_id,
        }
        typer.echo(render_output(payload, ctx.output_format))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc


@app.command("list")
def list_config_keys():
    """List available configuration keys supported by the CLI."""
    correlation_id = uuid4().hex
    try:
        payload = {"keys": available_keys(), "correlation_id": correlation_id}
        typer.echo(render_output(payload, ctx.output_format))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc
