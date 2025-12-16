from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import (
    CONFIG_KEYS,
    available_keys,
    load_config,
    persist_config_value,
)
from tnh_scholar.cli_tools.tnh_gen.errors import error_response
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx

app = typer.Typer(help="Inspect and edit tnh-gen configuration.")


def _coerce_for_set(key: str, raw: str) -> str | float | int:
    target = CONFIG_KEYS[key]
    if target is Path:
        return str(Path(raw))
    return target(raw)


@app.command("show")
def show_config(
    format: OutputFormat | None = typer.Option(
        None, "--format", help="json (default) or yaml.", case_sensitive=False
    ),
):
    correlation_id = uuid4().hex
    try:
        config, meta = load_config(ctx.config_path)
        payload = {"config": config.to_dict(), "sources": meta["sources"], "correlation_id": correlation_id}
        fmt = format or ctx.output_format
        typer.echo(render_output(payload, fmt))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc


@app.command("get")
def get_config_value(key: str):
    correlation_id = uuid4().hex
    try:
        if key not in available_keys():
            raise KeyError(f"Unknown config key: {key}")
        config, _ = load_config(ctx.config_path)
        payload = {key: config.to_dict().get(key), "correlation_id": correlation_id}
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
    correlation_id = uuid4().hex
    try:
        payload = {"keys": available_keys(), "correlation_id": correlation_id}
        typer.echo(render_output(payload, ctx.output_format))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc
