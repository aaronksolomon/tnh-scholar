"""Filesystem-backed run artifact store."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from tnh_scholar.agent_orchestration.run_artifacts.models import (
    ArtifactRole,
    RunArtifactPaths,
    RunEventRecord,
    RunMetadata,
    StepArtifactEntry,
    StepManifest,
)
from tnh_scholar.agent_orchestration.run_artifacts.protocols import RunArtifactStoreProtocol


@dataclass(frozen=True)
class FilesystemRunArtifactStore(RunArtifactStoreProtocol):
    """Persist run artifacts to the local filesystem."""

    def create_run(self, run_id: str, root_directory: Path) -> RunArtifactPaths:
        run_directory = root_directory / run_id
        artifacts_directory = run_directory / "artifacts"
        run_directory.mkdir(parents=True, exist_ok=True)
        artifacts_directory.mkdir(parents=True, exist_ok=True)
        return RunArtifactPaths(
            artifacts_root=root_directory,
            run_directory=run_directory,
            artifacts_directory=artifacts_directory,
            event_log_path=run_directory / "events.ndjson",
            metadata_path=run_directory / "metadata.json",
            final_state_path=run_directory / "final-state.txt",
        )

    def write_metadata(self, metadata: RunMetadata, paths: RunArtifactPaths) -> None:
        self._write_json(paths.metadata_path, metadata)

    def append_event(self, event: RunEventRecord, paths: RunArtifactPaths) -> None:
        with paths.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json())
            handle.write("\n")

    def artifact_step_dir(self, step_id: str, paths: RunArtifactPaths) -> Path:
        artifacts_directory: Path = paths.artifacts_directory
        step_directory = artifacts_directory / step_id
        step_directory.mkdir(parents=True, exist_ok=True)
        return step_directory

    def write_step_manifest(self, manifest: StepManifest, paths: RunArtifactPaths) -> Path:
        manifest_path = self.artifact_step_dir(manifest.step_id, paths) / "manifest.json"
        self._write_json(manifest_path, manifest)
        return manifest_path

    def write_final_state(self, final_state: str, paths: RunArtifactPaths) -> None:
        self._write_text(paths.final_state_path, final_state)

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
        artifact_path = self.artifact_step_dir(step_id, paths) / filename
        self._write_text(artifact_path, content)
        return self._build_artifact_entry(
            paths=paths,
            artifact_path=artifact_path,
            role=role,
            media_type=media_type,
            required=required,
            important=important,
        )

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
        artifact_path = self.artifact_step_dir(step_id, paths) / filename
        self._write_json(artifact_path, payload)
        return self._build_artifact_entry(
            paths=paths,
            artifact_path=artifact_path,
            role=role,
            media_type="application/json",
            required=required,
            important=important,
        )

    def _build_artifact_entry(
        self,
        *,
        paths: RunArtifactPaths,
        artifact_path: Path,
        role: ArtifactRole,
        media_type: str,
        required: bool,
        important: bool,
    ) -> StepArtifactEntry:
        return StepArtifactEntry(
            role=role,
            path=artifact_path.relative_to(paths.run_directory),
            media_type=media_type,
            required=required,
            important=important,
        )

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_json(self, path: Path, payload: BaseModel | dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, BaseModel):
            rendered = payload.model_dump_json(indent=2)
        else:
            rendered = json.dumps(payload, indent=2, default=str)
        path.write_text(rendered, encoding="utf-8")
