"""Protocols for workspace operations."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.workspace.models import WorkspaceContext, WorkspaceSnapshot


class WorkspaceServiceProtocol(Protocol):
    """Workspace safety and rollback operations."""

    def prepare_pre_run(self, run_id: str) -> WorkspaceContext:
        """Create and persist the pre-run workspace context."""

    def rollback_pre_run(self) -> WorkspaceContext:
        """Rollback to the pre-run state and return updated context."""

    def current_context(self) -> WorkspaceContext | None:
        """Return the current managed workspace context, if any."""

    def snapshot(self) -> WorkspaceSnapshot:
        """Return current semantic snapshot."""

    def diff_summary(self) -> str:
        """Return normalized diff summary."""
