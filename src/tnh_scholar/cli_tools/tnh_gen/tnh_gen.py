"""Typer entrypoint for the tnh-gen CLI."""

from __future__ import annotations

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


@app.callback()
def cli_callback(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file that overrides user/workspace config.",
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
      tnh-gen run --prompt daily --input-file notes.md
      tnh-gen --api run --prompt daily --input-file notes.md

    Args:
        config: Optional path to an explicit config file.
        format: Output format override for commands.
        api: Whether to emit machine-readable API contract output.
        quiet: Whether to suppress non-error output.
        no_color: Whether to disable colored terminal output.
    """
    from tnh_scholar.cli_tools.tnh_gen.state import _create_default_factory

    # Load environment variables from a .env file so settings (e.g., API keys)
    # are available before config and service initialization.
    load_dotenv(dotenv_path=find_dotenv(usecwd=True) or None)

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
