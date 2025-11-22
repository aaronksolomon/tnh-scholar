#!/usr/bin/env python3
"""CLI wrapper around the notebook preparation utility."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tnh_scholar.tools.notebook_prep import prep_notebooks  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create *_local.ipynb versions of notebooks and strip outputs from "
            "the originals."
        )
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=ROOT / "notebooks",
        type=Path,
        help=(
            "Directory containing notebooks to process. "
            "Defaults to the repository's notebooks directory."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show the actions that would be performed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    success = prep_notebooks(args.directory, dry_run=args.dry_run)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
