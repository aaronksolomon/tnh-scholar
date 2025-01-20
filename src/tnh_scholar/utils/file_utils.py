import re
import shutil
import warnings
from pathlib import Path
from typing import Generator


class FileExistsWarning(UserWarning):
    pass


def ensure_directory_exists(dir_path: Path) -> bool:
    """
    Create directory if it doesn't exist.

    Args:
        dir_path (Path): Directory path to ensure exists.
    """
    # Stub Implementation
    return dir_path.exists()


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


def copy_files_with_regex(
    source_dir: Path,
    destination_dir: Path,
    regex_patterns: list[str],
    preserve_structure: bool = True,
) -> None:
    """
    Copies files from subdirectories one level down in the source directory to the destination directory
    if they match any regex pattern. Optionally preserves the directory structure.

    Args:
        source_dir (Path): Path to the source directory to search files in.
        destination_dir (Path): Path to the destination directory where files will be copied.
        regex_patterns (list[str]): List of regex patterns to match file names.
        preserve_structure (bool): Whether to preserve the directory structure. Defaults to True.

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
                            # Place directly in destination without subdirectory structure
                            target_path = destination_dir / file_path.name

                        shutil.copy2(file_path, target_path)
                        print(f"Copied: {file_path} -> {target_path}")


def get_text_from_file(file_path: Path) -> str:
    """Reads the entire content of a text file.

    Args:
        file_path: The path to the text file.

    Returns:
        The content of the text file as a single string.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def write_text_to_file(
    file_path: Path, content: str, overwrite: bool = False, append: bool = False
) -> None:
    """Writes text content to a file, handling overwriting and appending.

    Args:
        file_path: The path to the file.
        content: The text content to write.
        overwrite: If True, overwrites the file if it exists.
        append: If True, appends the content to the file if it exists.

    Raises:
        FileExistsWarning: If the file exists and neither overwrite nor append are True.
    """

    if file_path.exists():
        if not overwrite and not append:
            warnings.warn(
                f"File '{file_path}' already exists. Use overwrite or append.",
                FileExistsWarning,
            )
            return  # Do not write if neither flag is set
        mode = "a" if append else "w"  # Choose mode based on flags
    else:
        mode = "w"  # Default to write mode if file doesn't exist

    with open(file_path, mode, encoding="utf-8") as file:
        file.write(content)
