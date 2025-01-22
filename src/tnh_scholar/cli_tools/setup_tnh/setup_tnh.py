# setup.py

import os
from pathlib import Path
import click
import requests
import zipfile
import io
from dotenv import load_dotenv, set_key

# Constants
CONFIG_DIR = Path.home() / ".config" / "tnh_scholar"
PATTERNS_DIR = CONFIG_DIR / "patterns"
LOGS_DIR = CONFIG_DIR / "logs"
PATTERNS_URL = "https://github.com/aaronksolomon/patterns/archive/main.zip"

def create_config_dirs():
    """Create required configuration directories."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    PATTERNS_DIR.mkdir(exist_ok=True)

def check_env():
    """Check environment variables."""

    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        api_key = click.prompt("Enter your OpenAI API key", type=str)
        click.echo("OpenAI API key not found in Environment.")
        click.echo("Set your OPENAI_API_KEY in your shell environment variables.")
        

def download_patterns() -> bool:
    """Download and extract pattern files from GitHub."""
    try:
        response = requests.get(PATTERNS_URL)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            root_dir = zip_ref.filelist[0].filename.split('/')[0]
            
            for zip_info in zip_ref.filelist:
                if zip_info.filename.endswith('.md'):
                    rel_path = Path(zip_info.filename).relative_to(root_dir)
                    target_path = PATTERNS_DIR / rel_path
                    
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zip_ref.open(zip_info) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
        return True
        
    except Exception as e:
        click.echo(f"Pattern download failed: {e}", err=True)
        return False

@click.command()
@click.option('--skip-env', is_flag=True, help='Skip API key setup')
@click.option('--skip-patterns', is_flag=True, help='Skip pattern download')
def setup_tnh(skip_env: bool, skip_patterns: bool):
    """Set up TNH Scholar configuration."""
    click.echo("Setting up TNH Scholar...")
    
    # Create config directories
    create_config_dirs()
    click.echo(f"Created config directory: {CONFIG_DIR}")
    
    # Environment setup
    if not skip_env:
        check_env()
    
    # Pattern download
    if not skip_patterns and click.confirm(
                "\nDownload pattern (markdown text) files from GitHub?\n"
                f"Source: {PATTERNS_URL}\n"
                f"Target: {PATTERNS_DIR}"
            ):
        if download_patterns():
            click.echo("Pattern files downloaded successfully")
        else:
            click.echo("Pattern download failed", err=True)
    
    click.echo("\nSetup complete!")

def main():
    """Entry point for setup CLI tool."""
    setup_tnh()

if __name__ == "__main__":
    main()

