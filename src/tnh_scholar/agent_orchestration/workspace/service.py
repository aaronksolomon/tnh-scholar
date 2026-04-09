"""Workspace services."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from tnh_scholar.agent_orchestration.workspace.models import WorkspaceContext, WorkspaceSnapshot
from tnh_scholar.agent_orchestration.workspace.protocols import WorkspaceServiceProtocol


@dataclass(frozen=True)
class NullWorkspaceService(WorkspaceServiceProtocol):
    """Workspace service for tests and explicit non-operational contexts."""

    repo_root: Path

    def planned_worktree_path(self, run_id: str) -> Path | None:
        """Return no managed worktree path."""
        del run_id
        return None

    def prepare_pre_run(self, run_id: str) -> WorkspaceContext:
        """Return a stable no-op workspace context."""
        return self._empty_context(run_id=run_id)

    def rollback_pre_run(self) -> WorkspaceContext:
        """Return the stable no-op workspace context."""
        return self._empty_context()

    def current_context(self) -> WorkspaceContext | None:
        """Return no managed workspace context."""
        return None

    def snapshot(self) -> WorkspaceSnapshot:
        """Return an empty semantic snapshot."""
        return WorkspaceSnapshot(repo_root=self.repo_root, worktree_path=self.repo_root)

    def diff_summary(self) -> str:
        """Return a stable empty diff summary."""
        return ""

    def _empty_context(self, run_id: str | None = None) -> WorkspaceContext:
        return WorkspaceContext(
            repo_root=self.repo_root,
            worktree_path=self.repo_root,
            branch_name="",
            base_ref="",
            base_sha="",
            run_id=run_id,
        )


@dataclass
class GitWorktreeWorkspaceService(WorkspaceServiceProtocol):
    """Manage one conductor-owned git worktree for a workflow run."""

    repo_root: Path
    workspace_root: Path
    base_ref: str = "HEAD"
    branch_prefix: str = "tnh/run-"
    current_context_value: WorkspaceContext | None = field(default=None, init=False)

    def planned_worktree_path(self, run_id: str) -> Path | None:
        """Return the managed worktree path for one run."""
        return self.workspace_root / run_id

    def prepare_pre_run(self, run_id: str) -> WorkspaceContext:
        """Create the managed worktree and record its base state."""
        base_sha = self._git_stdout("rev-parse", self.base_ref)
        branch_name = self._branch_name(run_id)
        worktree_path = self.planned_worktree_path(run_id)
        if worktree_path is None:
            raise RuntimeError("Managed worktree path is required for git worktree service.")
        self._ensure_workspace_root()
        self._create_worktree(branch_name=branch_name, worktree_path=worktree_path, base_ref=base_sha)
        context = WorkspaceContext(
            repo_root=self.repo_root,
            worktree_path=worktree_path,
            branch_name=branch_name,
            base_ref=self.base_ref,
            base_sha=base_sha,
            head_sha=self._git_stdout("rev-parse", "HEAD", cwd=worktree_path),
            run_id=run_id,
            created_at=datetime.now().astimezone(),
        )
        self.current_context_value = context
        return context

    def rollback_pre_run(self) -> WorkspaceContext:
        """Discard and recreate the managed worktree at the recorded base state."""
        context = self._require_context()
        self._remove_worktree(context.worktree_path)
        self._create_worktree(
            branch_name=context.branch_name,
            worktree_path=context.worktree_path,
            base_ref=context.base_sha,
        )
        updated = context.model_copy(
            update={"head_sha": self._git_stdout("rev-parse", "HEAD", cwd=context.worktree_path)}
        )
        self.current_context_value = updated
        return updated

    def current_context(self) -> WorkspaceContext | None:
        """Return the active managed workspace context."""
        return self.current_context_value

    def snapshot(self) -> WorkspaceSnapshot:
        """Return the current semantic snapshot for the active worktree."""
        context = self._require_context()
        staged_count = len(self._git_lines("diff", "--cached", "--name-only", cwd=context.worktree_path))
        unstaged_count = len(self._git_lines("diff", "--name-only", cwd=context.worktree_path))
        unstaged_count += len(
            self._git_lines("ls-files", "--others", "--exclude-standard", cwd=context.worktree_path)
        )
        diff_summary = self.diff_summary()
        return WorkspaceSnapshot(
            repo_root=context.repo_root,
            worktree_path=context.worktree_path,
            branch_name=context.branch_name,
            base_ref=context.base_ref,
            base_sha=context.base_sha,
            head_sha=self._git_stdout("rev-parse", "HEAD", cwd=context.worktree_path),
            is_dirty=bool(staged_count or unstaged_count),
            staged_count=staged_count,
            unstaged_count=unstaged_count,
            diff_summary=diff_summary or None,
        )

    def diff_summary(self) -> str:
        """Return the normalized diff for the active worktree."""
        context = self._require_context()
        result = self._git_completed("status", "--short", cwd=context.worktree_path)
        return result.stdout.strip()

    def _require_context(self) -> WorkspaceContext:
        if self.current_context_value is None:
            raise RuntimeError("Workspace context has not been prepared.")
        return self.current_context_value

    def _branch_name(self, run_id: str) -> str:
        return f"{self.branch_prefix}{run_id}"

    def _ensure_workspace_root(self) -> None:
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _create_worktree(
        self,
        *,
        branch_name: str,
        worktree_path: Path,
        base_ref: str,
    ) -> None:
        if worktree_path.exists():
            raise RuntimeError(f"Worktree path already exists: {worktree_path}")
        self._git_completed("worktree", "add", "-B", branch_name, str(worktree_path), base_ref)

    def _remove_worktree(self, worktree_path: Path) -> None:
        self._git_completed("worktree", "remove", "--force", str(worktree_path))
        if worktree_path.exists():
            shutil.rmtree(worktree_path)

    def _git_stdout(self, *args: str, cwd: Path | None = None) -> str:
        return self._git_completed(*args, cwd=cwd).stdout.strip()

    def _git_lines(self, *args: str, cwd: Path | None = None) -> list[str]:
        output = self._git_stdout(*args, cwd=cwd)
        if not output:
            return []
        return output.splitlines()

    def _git_completed(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        command = ("git", "-C", str(self.repo_root if cwd is None else cwd), *args)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result
        stderr = result.stderr.strip()
        raise RuntimeError(f"Git command failed ({' '.join(command)}): {stderr}")
