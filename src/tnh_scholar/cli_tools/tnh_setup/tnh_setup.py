# setup.py

import io
import zipfile
from pathlib import Path

import click
import requests
from dotenv import load_dotenv

# Constants
from tnh_scholar import TNH_CONFIG_DIR, TNH_DEFAULT_PATTERN_DIR, TNH_LOG_DIR
from tnh_scholar.utils.validate import check_openai_env

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

PATTERNS_URL = "https://github.com/aaronksolomon/patterns/archive/main.zip"

def create_config_dirs():
    """Create required configuration directories."""
    TNH_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TNH_LOG_DIR.mkdir(exist_ok=True)
    TNH_DEFAULT_PATTERN_DIR.mkdir(exist_ok=True)

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
                    target_path = TNH_DEFAULT_PATTERN_DIR / rel_path
                    
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
def tnh_setup(skip_env: bool, skip_patterns: bool):
    """Set up TNH Scholar configuration."""
    click.echo("Setting up TNH Scholar...")
    
    # Create config directories
    create_config_dirs()
    click.echo(f"Created config directory: {TNH_CONFIG_DIR}")
    
    # Pattern download
    if not skip_patterns and click.confirm(
                "\nDownload pattern (markdown text) files from GitHub?\n"
                f"Source: {PATTERNS_URL}\n"
                f"Target: {TNH_DEFAULT_PATTERN_DIR}"
            ):
        if download_patterns():
            click.echo("Pattern files downloaded successfully")
        else:
            click.echo("Pattern download failed", err=True)
            
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

