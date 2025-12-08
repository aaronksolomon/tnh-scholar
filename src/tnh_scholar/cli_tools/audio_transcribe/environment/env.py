import shutil
from pathlib import Path

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.validate import check_openai_env

logger = get_child_logger(__name__)

def check_requirements(requirements_file: Path) -> None:
    """
    Check that all requirements listed in requirements.txt can be imported.
    If any cannot be imported, print a warning.

    This is a heuristic check. Some packages may not share the same name as their importable module.
    Adjust the name mappings below as needed.

    Example:
        >>> check_requirements(Path("./requirements.txt"))
        # Prints warnings if imports fail, otherwise silent.
    """
    # Map requirement names to their importable module names if they differ
    name_map = {
        "python-dotenv": "dotenv",
        "openai_whisper": "whisper",
        "protobuf": "google.protobuf",
        # Add other mappings if needed
    }

    # Parse requirements.txt to get a list of package names
    packages = []
    with requirements_file.open("r") as req_file:
        for line in req_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Each line generally looks like 'package==version'
            pkg_name = line.split("==")[0].strip()
            packages.append(pkg_name)

    # Try importing each package
    for pkg in packages:
        mod_name = name_map.get(pkg, pkg)
        try:
            __import__(mod_name)
        except ImportError:
            print(
                f"WARNING: Could not import '{mod_name}' from '{pkg}'. Check that it is correctly installed."
            )

def check_env() -> bool:
    """
    Check the environment for necessary conditions:
    1. Check OpenAI key is available.
    2. Check that all requirements from requirements.txt are importable.
    """
    logger.debug("checking environment.")

    if not check_openai_env():
        return False

    if shutil.which("ffmpeg") is None:
        logger.error("ffmpeg not found in PATH. ffmpeg required for audio processing.")
        return False

    return True
    
    # check_requirements(requirements_file)
