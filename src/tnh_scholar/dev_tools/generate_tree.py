"""
Generate directory trees for a project and optionally its source directory.

This standalone module provides a `generate_tree` function that generates directory
trees using the `tree` command-line utility. It outputs the results to
`project_directory_tree.txt` and, if a source directory is specified,
`src_directory_tree.txt` within the project root directory.

Usage as a script:
    python generate_tree.py --root /path/to/project [--src /path/to/src]

Requirements:
- The `tree` command must be installed and available in the system PATH.

If `--src` is omitted, only the project-level directory tree is generated.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def build_tree(root_dir: Path, src_dir: Optional[Path] = None):
    """
    Generate directory trees for the project and optionally the source directory.

    Args:
        root_dir (Path): The root directory of the project.
        src_dir (Path, optional): The source directory inside the project.

    Raises:
        FileNotFoundError: If the `tree` command is not found or if the specified directories do not exist.
        subprocess.CalledProcessError: If the `tree` command fails.
    """
    if shutil.which("tree") is None:
        raise FileNotFoundError(
            "The 'tree' command is not found in the system PATH. Please install it first."
            )

    if not root_dir.exists() or not root_dir.is_dir():
        raise FileNotFoundError(f"The root directory '{root_dir}' does not exist or is not a directory.")

    project_tree_output = root_dir / "project_directory_tree.txt"
    subprocess.run(
        ["tree", "--gitignore", str(root_dir), "-o", str(project_tree_output)],
        check=True,
    )

    if src_dir:
        if not src_dir.exists() or not src_dir.is_dir():
            raise FileNotFoundError(f"The source directory '{src_dir}' does not exist or is not a directory.")
        src_tree_output = root_dir / "src_directory_tree.txt"
        subprocess.run(
            ["tree", "--gitignore", str(src_dir), "-o", str(src_tree_output)],
            check=True,
        )

def generate_tree():
    parser = argparse.ArgumentParser(
        description="Generate directory trees for a project and optionally its source directory."
        )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Root directory of the project.",
    )
    parser.add_argument(
        "--src",
        type=Path,
        required=False,
        help="Source directory inside the project (optional).",
    )
    args = parser.parse_args()

    try:
        build_tree(args.root, args.src)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: 'tree' command failed with exit code {e.returncode}.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    generate_tree()