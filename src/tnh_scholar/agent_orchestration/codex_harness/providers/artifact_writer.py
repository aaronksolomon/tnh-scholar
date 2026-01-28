"""Artifact writer for Codex harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from tnh_scholar.agent_orchestration.codex_harness.protocols import ArtifactWriterProtocol


@dataclass(frozen=True)
class FileArtifactWriter(ArtifactWriterProtocol):
    """Write artifacts to disk."""

    runs_root: Path

    def ensure_run_dir(self, run_id: str) -> Path:
        """Ensure the run directory exists and return it."""
        run_dir = self.runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_text(self, path: Path, content: str) -> None:
        """Write text content to a file."""
        path.write_text(content, encoding="utf-8")

    def write_json(self, path: Path, payload: object) -> None:
        """Write JSON content to a file."""
        data = self._normalize_payload(payload)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")

    def _normalize_payload(self, payload: object) -> Any:
        if isinstance(payload, BaseModel):
            return payload.model_dump(mode="json")
        if isinstance(payload, dict):
            return payload
        return str(payload)
