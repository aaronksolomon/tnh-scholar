# setup.py

import io
import subprocess
import sys
import zipfile
from pathlib import Path

import click
import requests
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

PROMPTS_URL = "https://github.com/aaronksolomon/patterns/archive/main.zip"


def _user_root() -> Path:
    return TNHContext.discover().user_root

def create_config_dirs():
    """Create required configuration directories."""
    config_dir = _user_root()
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "logs").mkdir(exist_ok=True)
    (config_dir / "prompts").mkdir(exist_ok=True)

def download_prompts() -> bool:
    """Download and extract prompt files from GitHub."""
    try:
        response = requests.get(PROMPTS_URL)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            root_dir = zip_ref.filelist[0].filename.split('/')[0]
            
            for zip_info in zip_ref.filelist:
                if zip_info.filename.endswith('.md'):
                    rel_path = Path(zip_info.filename).relative_to(root_dir)
                    target_path = _user_root() / "prompts" / rel_path
                    
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zip_ref.open(zip_info) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
        return True
        
    except Exception as e:
        click.echo(f"Prompt download failed: {e}", err=True)
        return False

@click.command()
@click.option('--skip-env', is_flag=True, help='Skip API key setup')
@click.option('--skip-prompts', is_flag=True, help='Skip prompt download')
@click.option('--skip-ytdlp-runtime', is_flag=True, help='Skip yt-dlp runtime setup')
def tnh_setup(skip_env: bool, skip_prompts: bool, skip_ytdlp_runtime: bool):
    """Set up TNH Scholar configuration."""
    click.echo("TNH Setup")
    
    # Create config directories
    create_config_dirs()
    click.echo(f"Created config directory: {_user_root()}")
    
    # Prompt download
    if not skip_prompts and click.confirm(
                "\nDownload prompt (markdown text) files from GitHub?\n"
                f"Source: {PROMPTS_URL}\n"
                f"Target: {_user_root() / 'prompts'}"
            ):
        if download_prompts():
            click.echo("Prompt files downloaded successfully")
        else:
            click.echo("Prompt download failed", err=True)

    if not skip_ytdlp_runtime and click.confirm(
        "\nSet up yt-dlp runtime dependencies (JS runtime + curl_cffi)?\n"
        "This improves YouTube download stability."
    ):
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
                click.echo(
                    f"  - {item.code}: {item.message}",
                    err=True,
                )
        else:
            click.echo("  ✅ runtime verified.")
            
    # Environment test:
    if not skip_env:
        load_dotenv()  # for development
        if not check_openai_env(output=False):
            print(OPENAI_ENV_HELP_MSG)
    
def main():
    """Entry point for setup CLI tool."""
    tnh_setup()

if __name__ == "__main__":
    main()
