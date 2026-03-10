"""Typed models for workspace operations."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class RollbackTarget(str, Enum):
    """Supported rollback targets."""

    pre_run = "pre_run"


class WorkspaceSnapshot(BaseModel):
    """Semantic snapshot of workspace state."""

    repo_root: Path
    branch_name: str | None = None
    is_dirty: bool = False
    staged_count: int = 0
    unstaged_count: int = 0
    diff_summary: str | None = None
