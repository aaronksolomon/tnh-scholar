"""Helpers for generating directory-tree text files."""
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def build_tree(root_dir: Path, src_dir: Optional[Path] = None) -> None:
    """Generate directory trees for the project and optionally its source directory."""
    if shutil.which("tree") is None:
        raise FileNotFoundError(
            "The 'tree' command is not found in the system PATH. Please install it first."
        )

    if not root_dir.exists() or not root_dir.is_dir():
        raise FileNotFoundError(
            f"The root directory '{root_dir}' does not exist or is not a directory."
        )

    project_tree_output = root_dir / "project_directory_tree.txt"
    # Run from the root so the tree uses relative paths (stable across environments).
    subprocess.run(
        ["tree", "--gitignore", ".", "-o", str(project_tree_output)],
        cwd=root_dir,
        check=True,
    )

    if src_dir:
        if not src_dir.exists() or not src_dir.is_dir():
            raise FileNotFoundError(
                f"The source directory '{src_dir}' does not exist or is not a directory."
            )
        src_tree_output = root_dir / "src_directory_tree.txt"
        subprocess.run(
            ["tree", "--gitignore", ".", "-o", str(src_tree_output)],
            cwd=src_dir,
            check=True,
        )
