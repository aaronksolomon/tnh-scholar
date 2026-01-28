"""Artifact writer for spike runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.spike.models import RunMetadata
from tnh_scholar.agent_orchestration.spike.protocols import ArtifactWriterProtocol


@dataclass(frozen=True)
class FileArtifactWriter(ArtifactWriterProtocol):
    """Write run artifacts to disk."""

    runs_root: Path

    def ensure_run_dir(self, run_id: str) -> Path:
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_text(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def write_bytes(self, path: Path, content: bytes) -> None:
        path.write_bytes(content)

    def write_json(self, path: Path, payload: RunMetadata) -> None:
        path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
