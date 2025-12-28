from __future__ import annotations

from pathlib import Path
from typing import Iterable, cast
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import load_config
from tnh_scholar.cli_tools.tnh_gen.errors import exit_with_error
from tnh_scholar.cli_tools.tnh_gen.output.formatter import format_table, render_output
from tnh_scholar.cli_tools.tnh_gen.output.human_formatter import format_human_friendly_list
from tnh_scholar.cli_tools.tnh_gen.output.policy import resolve_list_format, validate_list_format
from tnh_scholar.cli_tools.tnh_gen.state import ListOutputFormat, OutputFormat, ctx
from tnh_scholar.cli_tools.tnh_gen.types import (
    ListApiPayload,
    ListHumanPayload,
)
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from tnh_scholar.prompt_system.domain.models import PromptMetadata

app = typer.Typer(help="List available prompts with metadata.", invoke_without_command=True)

_EXPECTED_FRONTMATTER = (
    "Expected YAML frontmatter keys: key, name, version, description, task_type, "
    "required_variables, optional_variables, tags, default_variables"
)


def _build_adapter(prompts_base: Path | None) -> PromptsAdapter:
    """Build a prompts adapter rooted at the configured prompt directory.

    Args:
        prompts_base: Base path for prompt catalog content.

    Returns:
        PromptsAdapter configured for the provided directory.

    Raises:
        ValueError: If no prompt directory is configured.
    """
    if prompts_base is None:
        raise ValueError("No prompt catalog directory configured (set TNH_PROMPT_DIR or config).")
    base = prompts_base.expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return PromptsAdapter(prompts_base=base)


def _apply_filters(
    prompts: Iterable[PromptMetadata],
    tags: list[str],
    search: str | None,
) -> Iterable[PromptMetadata]:
    """Yield prompts that match provided tag and search filters.

    Args:
        prompts: Iterable of prompt metadata objects.
        tags: Tag filters (any match will include the prompt).
        search: Optional text search applied to name/description.

    Returns:
        Iterable of prompts that satisfy all filters.
    """
    lowered = search.lower() if search else None
    for prompt in prompts:
        if tags and all(tag not in prompt.tags for tag in tags):
            continue
        if lowered and lowered not in prompt.name.lower() and lowered not in prompt.description.lower():
            continue
        yield prompt


def _normalize_prompt(prompt: PromptMetadata) -> dict[str, object]:
    return {
        "key": prompt.key,
        "name": prompt.name,
        "description": prompt.description,
        "tags": prompt.tags,
        "required_variables": prompt.required_variables,
        "optional_variables": prompt.optional_variables,
        "default_variables": prompt.default_variables,
        "default_model": prompt.default_model,
        "output_mode": prompt.output_mode,
        "version": prompt.version,
        "warnings": getattr(prompt, "warnings", []),
    }


def _build_entries(prompts: Iterable[PromptMetadata]) -> list[dict[str, object]]:
    return [_normalize_prompt(prompt) for prompt in prompts]


def _to_api_payload(entries: list[dict[str, object]], sources: list[str]) -> ListApiPayload:
    return {
        "prompts": [
            {
                "key": cast(str, entry["key"]),
                "name": cast(str, entry["name"]),
                "description": cast(str, entry["description"]),
                "tags": cast(list[str], entry["tags"]),
                "required_variables": cast(list[str], entry["required_variables"]),
                "optional_variables": cast(list[str], entry["optional_variables"]),
                "default_variables": cast(dict[str, object], entry["default_variables"]),
                "default_model": cast(str | None, entry["default_model"]),
                "output_mode": cast(str | None, entry["output_mode"]),
                "version": cast(str, entry["version"]),
                "warnings": cast(list[str], entry["warnings"]),
            }
            for entry in entries
        ],
        "count": len(entries),
        "sources": sources,
    }


def _to_human_payload(entries: list[dict[str, object]]) -> ListHumanPayload:
    return {
        "prompts": [
            {
                "key": cast(str, entry["key"]),
                "name": cast(str, entry["name"]),
                "description": cast(str, entry["description"]),
                "variables": {
                    "required": cast(list[str], entry["required_variables"]),
                    "optional": cast(list[str], entry["optional_variables"]),
                },
                "default_model": cast(str | None, entry["default_model"]),
                "tags": cast(list[str], entry["tags"]),
            }
            for entry in entries
        ],
        "count": len(entries),
    }


def _emit_prompt_warnings(prompts: Iterable[PromptMetadata]) -> None:
    """Emit warning hints to stderr for prompts missing proper frontmatter."""
    if ctx.quiet:
        return
    for prompt in prompts:
        if getattr(prompt, "warnings", []):
            typer.echo(
                f"[warn] Prompt '{prompt.key}' missing/invalid frontmatter. {_EXPECTED_FRONTMATTER}",
                err=True,
            )


def _render_list(
    *,
    prompts: list[PromptMetadata],
    sources: list[str],
    fmt: ListOutputFormat,
    api: bool,
    keys_only: bool,
) -> None:
    if keys_only:
        typer.echo("\n".join(prompt.key for prompt in prompts))
        return
    if not api and fmt == ListOutputFormat.text:
        typer.echo(format_human_friendly_list(prompts))
        return

    entries = _build_entries(prompts)
    if not api and fmt == ListOutputFormat.table:
        rows = [
            [
                cast(str, entry["key"]),
                cast(str, entry["name"]),
                ", ".join(cast(list[str], entry["tags"])),
                cast(str | None, entry["default_model"]) or "",
            ]
            for entry in entries
        ]
        headers = ["KEY", "NAME", "TAGS", "MODEL"]
        typer.echo(format_table(headers, rows))
        return

    payload = _to_api_payload(entries, sources) if api else _to_human_payload(entries)
    typer.echo(render_output(payload, fmt))


def _resolve_list_output_format(format_override: ListOutputFormat | None) -> ListOutputFormat:
    fmt = resolve_list_format(api=ctx.api, format_override=format_override, ctx_format=ctx.output_format)
    validate_list_format(ctx.api, fmt)
    return fmt


def _error_output_format(api: bool, format_override: ListOutputFormat | None) -> OutputFormat | None:
    if not api:
        return None
    if format_override in (ListOutputFormat.json, ListOutputFormat.yaml):
        return OutputFormat(format_override.value)
    return None


def _list_prompts_impl(
    *,
    tag: list[str],
    search: str | None,
    keys_only: bool,
    format_override: ListOutputFormat | None,
) -> None:
    config, meta = load_config(ctx.config_path)
    adapter = _build_adapter(config.prompt_catalog_dir)
    prompts = list(_apply_filters(adapter.list_all(), tag, search))

    _emit_prompt_warnings(prompts)
    if keys_only:
        _render_list(
            prompts=prompts,
            sources=meta["sources"],
            fmt=ListOutputFormat.text,
            api=ctx.api,
            keys_only=True,
        )
        return

    fmt = _resolve_list_output_format(format_override)
    _render_list(
        prompts=prompts,
        sources=meta["sources"],
        fmt=fmt,
        api=ctx.api,
        keys_only=False,
    )


@app.callback()
def list_prompts(
    tag: list[str] = typer.Option([], "--tag", help="Filter by tag (repeatable)."),
    search: str | None = typer.Option(None, "--search", help="Search prompt name/description."),
    keys_only: bool = typer.Option(False, "--keys-only", help="Output only prompt keys."),
    format: ListOutputFormat | None = typer.Option(
        None,
        "--format",
        help="Output format: json (requires --api), yaml, text/table (human-only).",
        case_sensitive=False,
    ),
):
    """List prompts with optional filters and output formats.

    Args:
        tag: Filter prompts by tag (repeatable).
        search: Case-insensitive search across name/description.
        keys_only: Whether to output only prompt keys.
        format: Desired output format (defaults to global setting).
    """
    trace_id = uuid4().hex
    try:
        _list_prompts_impl(
            tag=tag,
            search=search,
            keys_only=keys_only,
            format_override=format,
        )
    except typer.Exit:
        raise
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, trace_id=trace_id, format_override=_error_output_format(ctx.api, format))
