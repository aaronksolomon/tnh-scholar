"""Protocols for run artifact persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from tnh_scholar.agent_orchestration.run_artifacts.models import (
    ArtifactRole,
    RunArtifactPaths,
    RunEventRecord,
    RunMetadata,
    RunStatus,
    StepArtifactEntry,
    StepManifest,
)


class RunArtifactStoreProtocol(Protocol):
    """Persist run-scoped artifacts."""

    def create_run(self, run_id: str, root_directory: Path) -> RunArtifactPaths:
        """Create and return canonical run paths."""

    def write_metadata(self, metadata: RunMetadata, paths: RunArtifactPaths) -> None:
        """Persist run metadata."""

    def status_path_for_run(self, run_id: str, root_directory: Path) -> Path:
        """Return the canonical status path for one run id."""

    def write_status(self, status: RunStatus, paths: RunArtifactPaths) -> None:
        """Persist live run status."""

    def read_status(self, run_id: str, root_directory: Path) -> RunStatus:
        """Read and validate live run status for one run id."""

    def append_event(self, event: RunEventRecord, paths: RunArtifactPaths) -> None:
        """Append one event record."""

    def artifact_step_dir(self, step_id: str, paths: RunArtifactPaths) -> Path:
        """Return the canonical artifact directory for one step."""

    def write_step_manifest(self, manifest: StepManifest, paths: RunArtifactPaths) -> Path:
        """Persist one step manifest and return its path."""

    def write_final_state(self, final_state: str, paths: RunArtifactPaths) -> None:
        """Persist the terminal workflow state summary."""

    def write_text_artifact(
        self,
        *,
        paths: RunArtifactPaths,
        step_id: str,
        role: ArtifactRole,
        filename: str,
        content: str,
        media_type: str,
        required: bool,
        important: bool = False,
    ) -> StepArtifactEntry:
        """Write and register one text artifact."""

    def write_json_artifact(
        self,
        *,
        paths: RunArtifactPaths,
        step_id: str,
        role: ArtifactRole,
        filename: str,
        payload: BaseModel | dict[str, object],
        required: bool,
        important: bool = False,
    ) -> StepArtifactEntry:
        """Write and register one JSON artifact."""

    def copy_file_artifact(
        self,
        *,
        paths: RunArtifactPaths,
        step_id: str,
        role: ArtifactRole,
        filename: str,
        source_path: Path,
        media_type: str,
        required: bool,
        important: bool = False,
    ) -> StepArtifactEntry:
        """Copy one existing file into canonical artifact storage."""
