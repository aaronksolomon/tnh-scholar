from __future__ import annotations

import platform
import sys
from uuid import uuid4

import typer

from tnh_scholar import __version__
from tnh_scholar.cli_tools.tnh_gen.errors import error_response
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx


def _python_version() -> str:
    return ".".join(map(str, sys.version_info[:3]))


def version(
    format: OutputFormat | None = typer.Option(
        None, "--format", help="json (default) or yaml.", case_sensitive=False
    ),
):
    correlation_id = uuid4().hex
    try:
        payload = {
            "tnh_scholar": __version__,
            "tnh_gen": __version__,
            "python": _python_version(),
            "platform": platform.system().lower(),
            "prompt_system_version": __version__,
            "genai_service_version": __version__,
            "correlation_id": correlation_id,
        }
        fmt = format or ctx.output_format
        typer.echo(render_output(payload, fmt))
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, OutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc
