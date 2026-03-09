"""Protocols for run artifact persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.run_artifacts.models import (
    RunArtifactPaths,
    RunEventRecord,
    RunMetadata,
)


class RunArtifactStoreProtocol(Protocol):
    """Persist run-scoped artifacts."""

    def create_run(self, run_id: str, root_directory: Path) -> RunArtifactPaths:
        """Create and return canonical run paths."""

    def write_metadata(self, metadata: RunMetadata, paths: RunArtifactPaths) -> None:
        """Persist run metadata."""

    def append_event(self, event: RunEventRecord, paths: RunArtifactPaths) -> None:
        """Append one event record."""

    def write_text(self, path: Path, content: str) -> None:
        """Write arbitrary text artifact."""
