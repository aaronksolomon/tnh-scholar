"""Repository search provider for Codex harness tools."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RipgrepSearcher:
    """Use ripgrep to search the repository."""

    def search(self, query: str, root: Path) -> list[str]:
        result = subprocess.run(
            [
                "rg",
                "-n",
                "--no-messages",
                "--hidden",
                "-F",
                query,
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=root,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr.strip() or "ripgrep search failed")
        return [line for line in result.stdout.splitlines() if line.strip()]
