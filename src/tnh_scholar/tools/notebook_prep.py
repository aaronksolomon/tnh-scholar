"""Utilities for maintaining paired *_local.ipynb notebooks."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Iterable

EXCLUDED_PARTS = {".ipynb_checkpoints"}


def _iter_source_notebooks(directory: Path) -> Iterable[Path]:
    """Yield notebooks that should receive a *_local copy."""
    for path in sorted(directory.rglob("*.ipynb")):
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.stem.endswith("_local"):
            continue
        yield path


def prep_notebooks(directory: Path | str, dry_run: bool = True) -> bool:
    """Create *_local notebooks and strip outputs from originals.

    Parameters
    ----------
    directory:
        Directory whose notebooks will be processed.
    dry_run:
        When ``True`` only report pending work without copying files or invoking
        ``nbconvert``.
    """

    directory = Path(directory).expanduser()
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return False

    notebooks = list(_iter_source_notebooks(directory))
    print(
        f"Found {len(notebooks)} notebooks to process in {directory}. "
        "Ignoring all checkpoint and *_local notebooks."
    )

    for nb_path in notebooks:
        local_path = nb_path.parent / f"{nb_path.stem}_local{nb_path.suffix}"

        if local_path.exists():
            print(f"No action required: local copy of notebook exists: {local_path}")
            continue
        if dry_run:
            print(f"Would copy: {nb_path} -> {local_path}")
        else:
            print(f"Copying: {nb_path} -> {local_path}")
            shutil.copy2(nb_path, local_path)

        if dry_run:
            print(f"Would strip outputs from: {nb_path}")
            continue

        print(f"Stripping outputs from: {nb_path}")
        subprocess.run(
            [
                "jupyter",
                "nbconvert",
                "--ClearOutputPreprocessor.enabled=True",
                "--inplace",
                str(nb_path),
            ],
            check=True,
        )

    return True
