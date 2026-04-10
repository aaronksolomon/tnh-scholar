"""Typed models for workspace operations."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel


class RollbackTarget(str, Enum):
    """Supported rollback targets."""

    pre_run = "pre_run"


class WorkspaceContext(BaseModel):
    """Managed workspace identity for one mutable run."""

    repo_root: Path
    worktree_path: Path
    branch_name: str
    base_ref: str
    base_sha: str
    head_sha: str | None = None
    run_id: str | None = None
    created_at: datetime | None = None


class WorkspaceSnapshot(BaseModel):
    """Semantic snapshot of workspace state."""

    repo_root: Path
    worktree_path: Path | None = None
    branch_name: str | None = None
    base_ref: str | None = None
    base_sha: str | None = None
    head_sha: str | None = None
    is_dirty: bool = False
    staged_count: int = 0
    unstaged_count: int = 0
    diff_summary: str | None = None
