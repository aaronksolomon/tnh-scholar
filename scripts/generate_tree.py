#!/usr/bin/env python3
"""Generate directory-tree text files for the project."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tnh_scholar.tools.tree_builder import build_tree  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write project_directory_tree.txt (and optionally src_directory_tree.txt)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Project root to scan (defaults to repository root).",
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=ROOT / "src",
        help="Source directory to scan for src_directory_tree.txt (optional).",
    )
    parser.add_argument(
        "--skip-src",
        action="store_true",
        help="Only build the project-level tree and skip the src tree.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    src_dir = None if args.skip_src else args.src
    try:
        build_tree(args.root, src_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Error: tree command failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
