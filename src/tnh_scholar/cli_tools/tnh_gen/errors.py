from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import IntEnum
from typing import Tuple

import typer
from click.exceptions import BadParameter

from tnh_scholar.cli_tools.tnh_gen.output.formatter import render_output
from tnh_scholar.cli_tools.tnh_gen.output.human_formatter import format_human_friendly_error
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx
from tnh_scholar.cli_tools.tnh_gen.types import ErrorDiagnostics, ErrorPayload
from tnh_scholar.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    RateLimitError,
    ValidationError,
)
from tnh_scholar.gen_ai_service.models.errors import ProviderError


class ExitCode(IntEnum):
    """CLI exit codes mapped to error classes."""

    SUCCESS = 0
    POLICY_ERROR = 1
    TRANSPORT_ERROR = 2
    PROVIDER_ERROR = 3
    FORMAT_ERROR = 4
    INPUT_ERROR = 5


def map_exception(exc: Exception) -> ExitCode:
    """Map a raised exception to a stable CLI exit code.

    Args:
        exc: Exception raised during CLI execution.

    Returns:
        ExitCode representing the failure category.
    """
    if isinstance(exc, ValidationError):
        return ExitCode.POLICY_ERROR
    if isinstance(exc, (ExternalServiceError, ConnectionError, TimeoutError)):
        return ExitCode.TRANSPORT_ERROR
    if isinstance(exc, (ProviderError, RateLimitError)):
        return ExitCode.PROVIDER_ERROR
    if isinstance(exc, (json.JSONDecodeError,)):
        return ExitCode.FORMAT_ERROR
    if isinstance(exc, (ConfigurationError, BadParameter, FileNotFoundError, KeyError, ValueError)):
        return ExitCode.INPUT_ERROR
    return ExitCode.PROVIDER_ERROR


def error_response(
    exc: Exception,
    *,
    error_code: str | None = None,
    suggestion: str | None = None,
    trace_id: str,
) -> Tuple[ErrorPayload, ExitCode]:
    """Construct a serialized error response and matching exit code.

    Args:
        exc: The caught exception.
        error_code: Optional explicit error code to surface in diagnostics.
        suggestion: Optional user-facing recovery suggestion.
        trace_id: Unique trace identifier for tracking this CLI request.

    Returns:
        A tuple containing the response payload and associated exit code.
    """
    exit_code = map_exception(exc)
    diagnostics: ErrorDiagnostics = {
        "error_type": exc.__class__.__name__,
        "error_code": error_code or exc.__class__.__name__.upper(),
    }
    if suggestion:
        diagnostics["suggestion"] = suggestion

    payload: ErrorPayload = {
        "status": "failed",
        "error": str(exc) or exc.__class__.__name__,
        "diagnostics": diagnostics,
        "trace_id": trace_id,
    }
    return payload, exit_code


def render_error(
    exc: Exception,
    *,
    trace_id: str,
    format_override: OutputFormat | None = None,
    suggestion: str | None = None,
) -> tuple[str, ExitCode, str]:
    """Render error output based on API vs human mode."""
    payload, exit_code = error_response(exc, suggestion=suggestion, trace_id=trace_id)
    error_code = payload["diagnostics"]["error_code"]
    if ctx.api:
        fmt = format_override or ctx.output_format or OutputFormat.json
        if fmt == OutputFormat.text:
            fmt = OutputFormat.json
        return render_output(payload, fmt), exit_code, error_code
    return (
        format_human_friendly_error(exc, suggestion=payload["diagnostics"].get("suggestion")),
        exit_code,
        error_code,
    )


def emit_trace_id(trace_id: str, error_code: str) -> None:
    """Emit a trace identifier to stderr for diagnostics."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    typer.echo(f"[{timestamp}] trace_id={trace_id} error_code={error_code}", err=True)


def exit_with_error(
    exc: Exception,
    *,
    trace_id: str,
    format_override: OutputFormat | None = None,
) -> None:
    """Render error output, emit trace, and exit with mapped status."""
    output, exit_code, error_code = render_error(
        exc,
        trace_id=trace_id,
        format_override=format_override,
    )
    emit_trace_id(trace_id, error_code)
    typer.echo(output)
    raise typer.Exit(code=int(exit_code)) from exc
