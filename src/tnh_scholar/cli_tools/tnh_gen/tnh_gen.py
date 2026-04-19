"""Typer entrypoint for the tnh-gen CLI."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import typer
from dotenv import find_dotenv, load_dotenv

from tnh_scholar.cli_tools.tnh_gen.commands import config as config_cmd
from tnh_scholar.cli_tools.tnh_gen.commands import list as list_cmd
from tnh_scholar.cli_tools.tnh_gen.commands import run as run_cmd
from tnh_scholar.cli_tools.tnh_gen.commands.version import version
from tnh_scholar.cli_tools.tnh_gen.state import OutputFormat, ctx

app = typer.Typer(
    name="tnh-gen",
    help="TNH-Gen: Unified CLI for TNH Scholar GenAI operations.",
    add_completion=False,
    no_args_is_help=True,
)


@contextmanager
def _override_prompt_dir_env(prompt_dir: Path | None):
    """Temporarily override `TNH_PROMPT_DIR` for the current CLI invocation."""
    if prompt_dir is None:
        yield
        return

    original_prompt_dir = os.environ.get("TNH_PROMPT_DIR")
    os.environ["TNH_PROMPT_DIR"] = str(prompt_dir)
    try:
        yield
    finally:
        if original_prompt_dir is None:
            os.environ.pop("TNH_PROMPT_DIR", None)
        else:
            os.environ["TNH_PROMPT_DIR"] = original_prompt_dir


@app.callback()
def cli_callback(
    click_ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file that overrides user/workspace config.",
    ),
    prompt_dir: Path | None = typer.Option(
        None,
        "--prompt-dir",
        help="Override the prompt catalog directory for this invocation.",
    ),
    format: OutputFormat | None = typer.Option(
        None,
        "--format",
        help="Output format for commands (json/yaml for API output; text/yaml for human output).",
        case_sensitive=False,
    ),
    api: bool = typer.Option(
        False,
        "--api",
        help="Machine-readable API contract output (JSON by default).",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output."),
):
    """Apply global options and initialize shared context.

    Default behavior: human-friendly output optimized for interactive CLI use.
    Use --api for machine-readable JSON contract output.

    Examples:
      tnh-gen list
      tnh-gen --api list
      tnh-gen --prompt-dir ./prompts list
      tnh-gen run --prompt daily --input-file notes.md
      tnh-gen --api run --prompt daily --input-file notes.md

    Args:
        config: Optional path to an explicit config file.
        prompt_dir: Optional prompt catalog directory override.
        format: Output format override for commands.
        api: Whether to emit machine-readable API contract output.
        quiet: Whether to suppress non-error output.
        no_color: Whether to disable colored terminal output.
    """
    from tnh_scholar.cli_tools.tnh_gen.state import _create_default_factory

    # Load environment variables from a .env file so settings (e.g., API keys)
    # are available before config and service initialization.
    load_dotenv(dotenv_path=find_dotenv(usecwd=True) or None)

    prompt_dir_scope = _override_prompt_dir_env(prompt_dir)
    prompt_dir_scope.__enter__()
    click_ctx.call_on_close(lambda: prompt_dir_scope.__exit__(None, None, None))

    ctx.config_path = config
    ctx.output_format = format
    ctx.api = api
    ctx.quiet = quiet
    ctx.no_color = no_color
    if ctx.service_factory is None:
        ctx.service_factory = _create_default_factory()


app.add_typer(list_cmd.app, name="list")
app.add_typer(run_cmd.app, name="run")
app.add_typer(config_cmd.app, name="config")
app.command()(version)


def main() -> None:
    """Dispatch execution to the Typer application."""
    app()


if __name__ == "__main__":
    main()
