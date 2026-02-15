"""Artifact store provider for conductor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.conductor_mvp.protocols import ArtifactStoreProtocol


@dataclass(frozen=True)
class FileArtifactStore(ArtifactStoreProtocol):
    """Write run artifacts to local filesystem."""

    def ensure_run_dir(self, run_id: str, root_dir: Path) -> Path:
        """Create and return run directory."""
        run_dir = root_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_text(self, path: Path, content: str) -> None:
        """Write UTF-8 text content."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
