"""Legacy Click-based tnh-setup entrypoint.

Prefer ``tnh_setup_typer.py`` for the maintained CLI implementation.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import click
from dotenv import load_dotenv

# Constants
from tnh_scholar.configuration.context import TNHContext
from tnh_scholar.utils.validate import check_openai_env
from tnh_scholar.video_processing.yt_environment import YTDLPEnvironmentInspector

OPENAI_ENV_HELP_MSG = """
>>>>>>>>>> OpenAI API key not found in environment. <<<<<<<<<

For AI processing with TNH-scholar:

1. Get an API key from https://platform.openai.com/api-keys
2. Set the OPENAI_API_KEY environment variable:

   export OPENAI_API_KEY='your-api-key-here'  # Linux/Mac
   set OPENAI_API_KEY=your-api-key-here       # Windows

For OpenAI API access help: https://platform.openai.com/

>>>>>>>>>>>>>>>>>>>>>>>>>>> -- <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
"""

@dataclass(frozen=True)
class SetupPaths:
    """Resolved filesystem paths used by setup."""

    config_dir: Path
    log_dir: Path
    prompt_dir: Path


def _build_setup_paths(context: TNHContext) -> SetupPaths:
    user_root = context.user_root
    return SetupPaths(
        config_dir=user_root,
        log_dir=user_root / "logs",
        prompt_dir=user_root / "prompts",
    )


def create_config_dirs(paths: SetupPaths) -> None:
    """Create required configuration directories."""
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(exist_ok=True)
    paths.prompt_dir.mkdir(exist_ok=True)


def report_prompt_setup(paths: SetupPaths, *, skip_prompts: bool) -> None:
    """Report prompt directory setup without external downloads."""
    if skip_prompts:
        return
    click.echo("\nPrompt setup")
    click.echo(f"User prompt directory: {paths.prompt_dir}")
    click.echo("Repo prompt workspace: tnh-prompts/ (repo-local default)")
    click.echo("Bundled prompts: src/tnh_scholar/runtime_assets/prompts/")
    click.echo("No external prompt download is performed.")


def maybe_setup_ytdlp_runtime(*, skip_ytdlp_runtime: bool) -> None:
    """Prompt for and run yt-dlp runtime setup."""
    if skip_ytdlp_runtime:
        return
    should_setup = click.confirm(
        "\nSet up yt-dlp runtime dependencies (JS runtime + curl_cffi)?\n"
        "This improves YouTube download stability."
    )
    if not should_setup:
        return

    click.echo("• yt-dlp runtime setup: running")
    script_path = Path(__file__).resolve().parents[4] / "scripts" / "setup_ytdlp_runtime.py"
    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path), "--yes"],
            check=False,
        )
        if result.returncode != 0:
            click.echo("  ⚠️  runtime setup reported errors. Review output above.", err=True)
    else:
        click.echo(
            f"  ⚠️  runtime setup script not found at {script_path}",
            err=True,
        )

    click.echo("• yt-dlp runtime verification")
    inspector = YTDLPEnvironmentInspector()
    report = inspector.inspect_report()
    if report.has_items():
        click.echo("  ⚠️  runtime incomplete. Some downloads may fail.", err=True)
        for item in report.items:
            click.echo(f"  - {item.code}: {item.message}", err=True)
        return
    click.echo("  ✅ runtime verified.")


def maybe_check_environment(*, skip_env: bool) -> None:
    """Load env and report missing OpenAI configuration."""
    if skip_env:
        return
    load_dotenv()
    if not check_openai_env(output=False):
        print(OPENAI_ENV_HELP_MSG)

@click.command()
@click.option('--skip-env', is_flag=True, help='Skip API key setup')
@click.option('--skip-prompts', is_flag=True, help='Skip prompt directory setup guidance')
@click.option('--skip-ytdlp-runtime', is_flag=True, help='Skip yt-dlp runtime setup')
def tnh_setup(skip_env: bool, skip_prompts: bool, skip_ytdlp_runtime: bool):
    """Set up TNH Scholar configuration."""
    context = TNHContext.discover()
    paths = _build_setup_paths(context)
    click.echo("TNH Setup")

    create_config_dirs(paths)
    click.echo(f"Created config directory: {paths.config_dir}")

    report_prompt_setup(paths, skip_prompts=skip_prompts)
    maybe_setup_ytdlp_runtime(skip_ytdlp_runtime=skip_ytdlp_runtime)
    maybe_check_environment(skip_env=skip_env)
    
def main():
    """Entry point for setup CLI tool."""
    tnh_setup()

if __name__ == "__main__":
    main()
