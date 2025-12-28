from __future__ import annotations

import platform
import sys
from uuid import uuid4

import typer

from tnh_scholar import __version__
from tnh_scholar.cli_tools.tnh_gen.errors import exit_with_error
from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.output.policy import (
    resolve_output_format,
    validate_global_format,
)
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx
from tnh_scholar.cli_tools.tnh_gen.types import VersionHumanPayload, VersionPayload


def _python_version() -> str:
    """Return the current interpreter version as a string."""
    return ".".join(map(str, sys.version_info[:3]))


def version(
    format: OutputFormat | None = typer.Option(
        None,
        "--format",
        help="Output format: json (requires --api), yaml, or text (human-only).",
        case_sensitive=False,
    ),
):
    """Display version information for tnh-gen and dependencies.

    Args:
        format: Optional output format override (json or yaml).
    """
    trace_id = uuid4().hex
    try:
        payload: VersionPayload = {
            "tnh_scholar": __version__,
            "tnh_gen": __version__,
            "python": _python_version(),
            "platform": platform.system().lower(),
            "prompt_system_version": __version__,
            "genai_service_version": __version__,
            "trace_id": trace_id,
        }
        validate_global_format(ctx.api, format or ctx.output_format)
        if ctx.api:
            fmt = resolve_output_format(
                api=True,
                format_override=format or ctx.output_format,
                default_format=OutputFormat.json,
            )
            typer.echo(render_output(payload, fmt))
            return

        fmt = resolve_output_format(
            api=False,
            format_override=format or ctx.output_format,
            default_format=OutputFormat.text,
        )
        if fmt == OutputFormat.text:
            lines = [
                f"tnh-gen {__version__}",
                f"python {payload['python']}",
                f"platform {payload['platform']}",
            ]
            typer.echo("\n".join(lines))
        else:
            human_payload: VersionHumanPayload = {
                "tnh_scholar": payload["tnh_scholar"],
                "tnh_gen": payload["tnh_gen"],
                "python": payload["python"],
                "platform": payload["platform"],
                "prompt_system_version": payload["prompt_system_version"],
                "genai_service_version": payload["genai_service_version"],
            }
            typer.echo(render_output(human_payload, fmt))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id, format_override=format)
