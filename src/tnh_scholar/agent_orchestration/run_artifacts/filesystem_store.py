"""Filesystem-backed run artifact store."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.run_artifacts.models import (
    RunArtifactPaths,
    RunEventRecord,
    RunMetadata,
)
from tnh_scholar.agent_orchestration.run_artifacts.protocols import RunArtifactStoreProtocol


@dataclass(frozen=True)
class FilesystemRunArtifactStore(RunArtifactStoreProtocol):
    """Persist run artifacts to the local filesystem."""

    def create_run(self, run_id: str, root_directory: Path) -> RunArtifactPaths:
        run_directory = root_directory / run_id
        run_directory.mkdir(parents=True, exist_ok=True)
        return RunArtifactPaths(
            run_directory=run_directory,
            event_log_path=run_directory / "events.ndjson",
            metadata_path=run_directory / "metadata.json",
            final_state_path=run_directory / "final_state.txt",
        )

    def write_metadata(self, metadata: RunMetadata, paths: RunArtifactPaths) -> None:
        paths.metadata_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    def append_event(self, event: RunEventRecord, paths: RunArtifactPaths) -> None:
        line = json.dumps(event.model_dump())
        with paths.event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")

    def write_text(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
