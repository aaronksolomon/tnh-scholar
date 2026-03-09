"""Workspace services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.workspace.models import WorkspaceSnapshot
from tnh_scholar.agent_orchestration.workspace.protocols import WorkspaceServiceProtocol


@dataclass(frozen=True)
class NullWorkspaceService(WorkspaceServiceProtocol):
    """Workspace service for tests and early migration."""

    repo_root: Path

    def capture_pre_run(self, run_id: str) -> None:
        """Capture pre-run state."""
        return None

    def rollback_pre_run(self) -> None:
        """Rollback pre-run state."""
        return None

    def snapshot(self, run_directory: Path) -> WorkspaceSnapshot:
        """Return an empty semantic snapshot."""
        return WorkspaceSnapshot(repo_root=self.repo_root)

    def diff_summary(self, run_directory: Path) -> str:
        """Return a stable empty diff summary."""
        return ""
