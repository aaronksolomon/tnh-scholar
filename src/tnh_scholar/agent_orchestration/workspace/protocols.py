"""Protocols for workspace operations."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.workspace.models import WorkspaceSnapshot


class WorkspaceServiceProtocol(Protocol):
    """Workspace safety and rollback operations."""

    def capture_pre_run(self, run_id: str) -> None:
        """Capture the pre-run state."""

    def rollback_pre_run(self) -> None:
        """Rollback to the pre-run state."""

    def snapshot(self, run_directory: Path) -> WorkspaceSnapshot:
        """Return current semantic snapshot."""

    def diff_summary(self, run_directory: Path) -> str:
        """Return normalized diff summary."""
