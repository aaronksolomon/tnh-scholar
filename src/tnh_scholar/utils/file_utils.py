import fcntl
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Generator, Union

PathLike = Union[str, Path]

DEFAULT_MAX_FILENAME_LENGTH = 25
class FileExistsWarning(UserWarning):
    pass


def ensure_directory_exists(dir_path: Path) -> bool:
    """
    Create directory if it doesn't exist.

    Args:
        dir_path (Path): Directory path to ensure exists.

    Returns:
        bool: True if the directory exists or was created successfully, False otherwise.
    """
    # No exception handling here. 
    # If exceptions occur let them propagate. 
    # Prototype code.
    
    dir_path.mkdir(parents=True, exist_ok=True)
    return True

def ensure_directory_writable(dir_path: Path) -> None:
    """
    Ensure the directory exists and is writable.
    Creates the directory if it does not exist.

    Args:
        dir_path (Path): Directory to verify or create.

    Raises:
        ValueError: If the directory cannot be created or is not writable.
        TypeError: If the provided path is not a Path instance.
    """
    if not isinstance(dir_path, Path):
        raise TypeError("dir_path must be a pathlib.Path instance")

    # Ensure directory exists first
    ensure_directory_exists(dir_path)

    # Check writability safely using NamedTemporaryFile
    try:
        with tempfile.NamedTemporaryFile(dir=dir_path, prefix=".writability_check_", delete=True) as tmp:
            tmp.write(b"test")
            tmp.flush()
    except Exception as e:
        raise ValueError(f"Directory is not writable: {dir_path}") from e
    
def iterate_subdir(
    directory: Path, recursive: bool = False
) -> Generator[Path, None, None]:
    """
    Iterates through subdirectories in the given directory.

    Args:
        directory (Path): The root directory to start the iteration.
        recursive (bool): If True, iterates recursively through all subdirectories.
                          If False, iterates only over the immediate subdirectories.

    Yields:
        Path: Paths to each subdirectory.

    Example:
        >>> for subdir in iterate_subdir(Path('/root'), recursive=False):
        ...     print(subdir)
    """
    if recursive:
        for subdirectory in directory.rglob("*"):
            if subdirectory.is_dir():
                yield subdirectory
    else:
        for subdirectory in directory.iterdir():
            if subdirectory.is_dir():
                yield subdirectory

def path_source_str(path: Path):
    return str(path.resolve())

def copy_files_with_regex(
    source_dir: Path,
    destination_dir: Path,
    regex_patterns: list[str],
    preserve_structure: bool = True,
) -> None:
    """
    Copies files from subdirectories one level down in the source directory to 
    the destination directory if they match any regex pattern. Optionally preserves the 
    directory structure.

    Args:
        source_dir (Path): Path to the source directory to search files in.
        destination_dir (Path): Path to the destination directory where files will be 
            copied.
        regex_patterns (list[str]): List of regex patterns to match file names.
        preserve_structure (bool): Whether to preserve the directory structure. 
            Defaults to True.

    Raises:
        ValueError: If the source directory does not exist or is not a directory.

    Example:
        >>> copy_files_with_regex(
        ...     source_dir=Path("/path/to/source"),
        ...     destination_dir=Path("/path/to/destination"),
        ...     regex_patterns=[r'.*\\.txt$', r'.*\\.log$'],
        ...     preserve_structure=True
        ... )
    """
    if not source_dir.is_dir():
        raise ValueError(
            f"The source directory {source_dir} does not exist or is not a directory."
        )

    if not destination_dir.exists():
        destination_dir.mkdir(parents=True, exist_ok=True)

    # Compile regex patterns for efficiency
    compiled_patterns = [re.compile(pattern) for pattern in regex_patterns]

    # Process only one level down
    for subdir in source_dir.iterdir():
        if subdir.is_dir():  # Only process subdirectories
            print(f"processing {subdir}:")
            for file_path in subdir.iterdir():  # Only files in this subdirectory
                if file_path.is_file():
                    print(f"checking file: {file_path.name}")
                    # Check if the file matches any of the regex patterns
                    if any(
                        pattern.match(file_path.name) for pattern in compiled_patterns
                    ):
                        if preserve_structure:
                            # Construct the target path, preserving relative structure
                            relative_path = (
                                subdir.relative_to(source_dir) / file_path.name
                            )
                            target_path = destination_dir / relative_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                        else:
                            # Put directly in destination without subdirectory structure
                            target_path = destination_dir / file_path.name

                        shutil.copy2(file_path, target_path)
                        print(f"Copied: {file_path} -> {target_path}")


def read_str_from_file(file_path: Path) -> str:
    """Reads the entire content of a text file.

    Args:
        file_path: The path to the text file.

    Returns:
        The content of the text file as a single string.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def write_str_to_file(file_path: PathLike, text: str, overwrite: bool = False):
    """Writes text to a file with file locking.

    Args:
        file_path: The path to the file to write.
        text: The text to write to the file.
        overwrite: Whether to overwrite the file if it exists.

    Raises:
        FileExistsError: If the file exists and overwrite is False.
        OSError: If there's an issue with file locking or writing.
    """
    file_path = Path(file_path)

    if file_path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}")

    try:
        with file_path.open("w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(text)
            fcntl.flock(f, fcntl.LOCK_UN)  # Release lock
    except OSError as e:
        raise OSError(f"Error writing to or locking file {file_path}: {e}") from e
    
def sanitize_filename(
    filename: str, 
    max_length: int = DEFAULT_MAX_FILENAME_LENGTH
    ) -> str:  
    """Sanitize filename for use unix use."""
    
    # Normalize Unicode to remove accents and convert to ASCII
    clean = (
        unicodedata.normalize(
            "NFKD", 
            filename).encode(
                "ascii", 
                "ignore").decode("ascii")
    )
    
    clean = clean.lower()
    clean = re.sub(r"[^a-z0-9\s]", " ", clean.strip())
    clean = clean.strip()
    
    # shorten
    clean = clean[:max_length].strip() 
    
    # convert spaces to _
    clean = re.sub(r"\s+", "_", clean)
        
    return clean

def to_slug(string: str) -> str:
    """
    Slugify a Unicode string.

    Converts a string to a strict URL-friendly slug format,
    allowing only lowercase letters, digits, and hyphens.

    Example:
        >>> slugify("Héllø_Wörld!")
        'hello-world'
    """
    # Normalize Unicode to remove accents and convert to ASCII
    string = (
        unicodedata.normalize("NFKD", string).encode("ascii", "ignore").decode("ascii")
    )

    # Replace all non-alphanumeric characters with spaces (only keep a-z and 0-9)
    string = re.sub(r"[^a-z0-9\s]", " ", string.lower().strip())

    # Replace any sequence of spaces with a single hyphen
    return re.sub(r"\s+", "-", string)

def path_as_str(path: Path) -> str:
    return str(path.resolve())

__all__ = [
    "DEFAULT_MAX_FILENAME_LENGTH",
    "FileExistsWarning",
    "ensure_directory_exists",
    "ensure_directory_writable",
    "iterate_subdir",
    "path_source_str",
    "copy_files_with_regex",
    "read_str_from_file",
    "write_str_to_file",
    "sanitize_filename",
    "to_slug",
    "path_as_str",
]