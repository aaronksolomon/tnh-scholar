"""Typed models for run artifact persistence."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class RunArtifactPaths(BaseModel):
    """Canonical run-scoped filesystem paths."""

    run_directory: Path
    event_log_path: Path
    metadata_path: Path
    final_state_path: Path


class RunMetadata(BaseModel):
    """Minimal run-level metadata."""

    run_id: str
    workflow_id: str
    started_at: datetime


class RunEventRecord(BaseModel):
    """Appendable runtime event record."""

    step_id: str
    next_step_id: str
