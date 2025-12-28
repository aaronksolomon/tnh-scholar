from __future__ import annotations

import typer

from tnh_scholar.cli_tools.tnh_gen.state import ListOutputFormat, OutputFormat


def resolve_output_format(
    *,
    api: bool,
    format_override: OutputFormat | None,
    default_format: OutputFormat,
) -> OutputFormat:
    """Resolve output format with API-aware defaults."""
    if format_override is not None:
        return format_override
    return OutputFormat.json if api else default_format


def resolve_list_format(
    *,
    api: bool,
    format_override: ListOutputFormat | None,
    ctx_format: OutputFormat | None,
) -> ListOutputFormat:
    """Resolve list output format with API-aware defaults."""
    if format_override is not None:
        return format_override
    if ctx_format is not None:
        try:
            return ListOutputFormat(ctx_format.value)
        except ValueError:
            return ListOutputFormat.json if api else ListOutputFormat.text
    return ListOutputFormat.json if api else ListOutputFormat.text


def validate_global_format(api: bool, format_override: OutputFormat | None) -> None:
    """Validate global format flags shared across commands."""
    if api and format_override == OutputFormat.text:
        raise typer.BadParameter("--format text is only supported without --api (use json/yaml with --api)")
    if not api and format_override == OutputFormat.json:
        raise typer.BadParameter("--format json requires --api (use text/yaml without --api)")


def validate_list_format(api: bool, format_override: ListOutputFormat) -> None:
    """Validate list format combinations."""
    if api and format_override in (ListOutputFormat.text, ListOutputFormat.table):
        raise typer.BadParameter("--format text/table is only supported without --api (use json/yaml with --api)")
    if not api and format_override == ListOutputFormat.json:
        raise typer.BadParameter("--format json requires --api (use text/table/yaml without --api)")


def validate_run_format(api: bool, format_override: OutputFormat | None) -> None:
    """Validate run format combinations."""
    if api and format_override == OutputFormat.text:
        raise typer.BadParameter("--format text is only supported without --api (use json/yaml with --api)")
    if not api and format_override and format_override != OutputFormat.text:
        raise typer.BadParameter("--format json/yaml requires --api (use text without --api)")
