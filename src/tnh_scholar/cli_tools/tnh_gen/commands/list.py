from __future__ import annotations

from pathlib import Path
from typing import Iterable
from uuid import uuid4

import typer

from tnh_scholar.cli_tools.tnh_gen.config_loader import load_config
from tnh_scholar.cli_tools.tnh_gen.errors import error_response
from tnh_scholar.cli_tools.tnh_gen.output.formatter import format_table, render_output
from tnh_scholar.cli_tools.tnh_gen.state import ListOutputFormat, ctx
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


def _apply_filters(prompts: Iterable[PromptMetadata], 
                   tags: list[str], 
                   search: str | None
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


@app.callback()
def list_prompts(
    tag: list[str] = typer.Option([], "--tag", help="Filter by tag (repeatable)."),
    search: str | None = typer.Option(None, "--search", help="Search prompt name/description."),
    keys_only: bool = typer.Option(False, "--keys-only", help="Output only prompt keys."),
    format: ListOutputFormat | None = typer.Option(
        None,
        "--format",
        help="Output format: json (default), yaml, text, table.",
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
    correlation_id = uuid4().hex
    try:
        config, meta = load_config(ctx.config_path)
        adapter = _build_adapter(config.prompt_catalog_dir)
        prompts = list(_apply_filters(adapter.list_all(), tag, search))

        if keys_only:
            typer.echo("\n".join(prompt.key for prompt in prompts))
            return

        entries = [
            {
                "key": prompt.key,
                "name": prompt.name,
                "description": prompt.description,
                "tags": prompt.tags,
                "required_variables": prompt.required_variables,
                "optional_variables": prompt.optional_variables,
                "default_model": prompt.default_model,
                "output_mode": prompt.output_mode,
                "version": prompt.version,
                "warnings": getattr(prompt, "warnings", []),
            }
            for prompt in prompts
        ]
        payload = {"prompts": entries, "count": len(entries), "sources": meta["sources"]}

        fmt = format or ListOutputFormat(
            ctx.output_format.value
            if ctx.output_format.value in ListOutputFormat._value2member_map_
            else ListOutputFormat.json.value
        )

        if fmt == ListOutputFormat.table:
            headers = ["KEY", "NAME", "TAGS", "MODEL"]
            rows = [
                [entry["key"], entry["name"], ", ".join(entry["tags"]), entry["default_model"] or ""]
                for entry in entries
            ]
            typer.echo(format_table(headers, rows))
        else:
            typer.echo(render_output(payload, fmt))
        # Emit warning hints to stderr for any prompts missing proper frontmatter.
        warn_entries = [entry for entry in entries if entry.get("warnings")]
        if warn_entries and not ctx.quiet:
            for entry in warn_entries:
                typer.echo(
                    f"[warn] Prompt '{entry['key']}' missing/invalid frontmatter. {_EXPECTED_FRONTMATTER}",
                    err=True,
                )
    except typer.Exit:
        raise
    except Exception as exc:  # noqa: BLE001
        payload, exit_code = error_response(exc, correlation_id=correlation_id)
        typer.echo(render_output(payload, ListOutputFormat.json))
        raise typer.Exit(code=int(exit_code)) from exc
