from pathlib import Path
import shutil

def ensure_env_file_exists(root_dir: Path) -> None:
    """
    Ensure that a .env file exists at the root of the project.
    If it does not, prompt the user for an OPENAI_API_KEY and create the file.

    Example:
        >>> ensure_env_file_exists(Path("/path/to/tnh-scholar"))
        # If .env doesn't exist, user is prompted for key, file created with OPENAI_API_KEY.
    """
    env_path = root_dir / ".env"
    if not env_path.exists():
        print("No .env file found at project root. Creating one:")
        openai_key = input("Please enter your OPENAI_API_KEY: ").strip()
        if not openai_key:
            print("No key entered. Exiting without creating .env file.")
            return
        with env_path.open("w") as env_file:
            env_file.write(f"OPENAI_API_KEY={openai_key}\n")
        print(".env file created with your OPENAI_API_KEY.")


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
            print(f"WARNING: Could not import '{mod_name}' from '{pkg}'. Check that it is correctly installed.")


def check_env(root_dir: Path, requirements_file: Path) -> None:
    """
    Check the environment for necessary conditions:
    1. Verify that .env file exists or create it if not found.
    2. Check that all requirements from requirements.txt are importable.

    Example:
        >>> check_env(Path("/path/to/tnh-scholar"), Path("/path/to/tnh-scholar/requirements.txt"))
        # Ensures .env, checks requirements.
    """
    ensure_env_file_exists(root_dir)
    if shutil.which("ffmpeg") is None:
        print("WARNING: ffmpeg not found in PATH. Please install ffmpeg.")
    check_requirements(requirements_file)