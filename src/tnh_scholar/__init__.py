from pathlib import Path

# Dynamically determine and set up paths for the project
TNH_ROOT_SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DIR = TNH_ROOT_SRC_DIR.resolve().parent.parent # always assume structure is: root_dir/src/TNH_BASE_DIR
CLI_TOOLS_DIR = TNH_ROOT_SRC_DIR / "cli_tools"
LOG_DIR = PROJECT_ROOT_DIR / "logs"
PATTERN_REPO = PROJECT_ROOT_DIR / "pattern_repo" 

if not TNH_ROOT_SRC_DIR.exists():
    raise FileNotFoundError(f"Base directory {TNH_ROOT_SRC_DIR} does not exist.")
if not CLI_TOOLS_DIR.exists():
    raise FileNotFoundError(f"CLI tools directory {CLI_TOOLS_DIR} does not exist.")

__version__ = "0.1.0"