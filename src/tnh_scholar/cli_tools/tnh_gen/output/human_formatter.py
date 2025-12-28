from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from typer import style

from tnh_scholar.cli_tools.tnh_gen.state import ctx
from tnh_scholar.prompt_system.domain.models import PromptMetadata


class OutputColor(str, Enum):
    """ANSI color codes for human-friendly CLI output."""

    TITLE = "bright_blue"
    VARIABLES = "cyan"
    MODEL = "green"
    TAGS = "yellow"
    ERROR = "red"
    SUGGESTION = "yellow"


@dataclass(frozen=True)
class HumanOutputLabels:
    """Display labels for human-friendly CLI output."""

    no_variables: str = "(none)"
    no_default_model: str = "(no default)"
    no_tags: str = "(no tags)"
    header_template: str = "Available Prompts ({count})"
    variable_prefix: str = "  Variables: "
    metadata_separator: str = " | "
    error_prefix: str = "Error: "
    suggestion_prefix: str = "Suggestion: "


LABELS = HumanOutputLabels()


def _style_text(text: str, *, fg: str | None = None, bold: bool = False) -> str:
    """Apply color styling when enabled."""
    return text if ctx.no_color else style(text, fg=fg, bold=bold)


def format_human_friendly_list(prompts: Iterable[PromptMetadata]) -> str:
    """Format prompt metadata for human-readable CLI output."""
    prompt_list = list(prompts)
    lines = [LABELS.header_template.format(count=len(prompt_list)), ""]

    for prompt in prompt_list:
        title = _style_text(f"{prompt.key} - {prompt.name}", fg=OutputColor.TITLE, bold=True)
        lines.extend((title, f"  {prompt.description}"))

        req_vars = ", ".join(prompt.required_variables)
        opt_vars = ", ".join(f"[{var}]" for var in prompt.optional_variables)
        segments = [req_vars, opt_vars] if req_vars or opt_vars else []
        all_vars = ", ".join(filter(None, segments))

        if all_vars:
            vars_display = _style_text(all_vars, fg=OutputColor.VARIABLES)
            lines.append(f"{LABELS.variable_prefix}{vars_display}")
        else:
            lines.append(f"{LABELS.variable_prefix}{LABELS.no_variables}")

        model = prompt.default_model or LABELS.no_default_model
        tags = ", ".join(prompt.tags) if prompt.tags else LABELS.no_tags
        model_display = _style_text(model, fg=OutputColor.MODEL)
        tags_display = _style_text(tags, fg=OutputColor.TAGS) if prompt.tags else tags
        lines.extend((
            f"  Model: {model_display}{LABELS.metadata_separator}Tags: {tags_display}",
            ""
        ))
    return "\n".join(lines)


def format_human_friendly_error(error: Exception, suggestion: str | None = None) -> str:
    """Format errors for human-readable CLI output."""
    error_line = _style_text(f"{LABELS.error_prefix}{error}", fg=OutputColor.ERROR, bold=True)
    lines = [error_line, ""]

    if suggestion:
        suggestion_line = _style_text(
            f"{LABELS.suggestion_prefix}{suggestion}",
            fg=OutputColor.SUGGESTION
        )
        lines.extend((suggestion_line, ""))
    return "\n".join(lines)
