"""Tests for the maintained workspace service."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tnh_scholar.agent_orchestration.workspace import GitWorktreeWorkspaceService, NullWorkspaceService


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    stderr = result.stderr.strip()
    raise AssertionError(f"Git command failed ({' '.join(args)}): {stderr}")


def _init_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init", "-b", "main")
    _git(repo_root, "config", "user.name", "Test User")
    _git(repo_root, "config", "user.email", "test@example.com")
    (repo_root / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(repo_root, "add", "tracked.txt")
    _git(repo_root, "commit", "-m", "initial")
    return repo_root


def test_git_worktree_workspace_service_prepares_context_and_snapshot(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    service = GitWorktreeWorkspaceService(
        repo_root=repo_root,
        workspace_root=tmp_path / "worktrees",
        base_ref="main",
    )

    context = service.prepare_pre_run("run-1")

    assert context.repo_root == repo_root
    assert context.worktree_path == tmp_path / "worktrees" / "run-1"
    assert context.branch_name == "tnh/run-run-1"
    assert context.base_ref == "main"
    assert context.base_sha
    assert context.head_sha == context.base_sha
    assert (context.worktree_path / "tracked.txt").read_text(encoding="utf-8") == "base\n"

    snapshot = service.snapshot()
    assert snapshot.repo_root == repo_root
    assert snapshot.worktree_path == context.worktree_path
    assert snapshot.branch_name == context.branch_name
    assert snapshot.base_sha == context.base_sha
    assert snapshot.is_dirty is False
    assert service.diff_summary() == ""


def test_git_worktree_workspace_service_rolls_back_by_recreating_worktree(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    service = GitWorktreeWorkspaceService(
        repo_root=repo_root,
        workspace_root=tmp_path / "worktrees",
        base_ref="main",
    )

    context = service.prepare_pre_run("run-2")
    tracked_file = context.worktree_path / "tracked.txt"
    tracked_file.write_text("changed\n", encoding="utf-8")

    dirty_snapshot = service.snapshot()
    assert dirty_snapshot.is_dirty is True
    assert dirty_snapshot.unstaged_count == 1
    assert "tracked.txt" in service.diff_summary()

    rolled_back = service.rollback_pre_run()

    assert rolled_back.base_sha == context.base_sha
    assert rolled_back.head_sha == context.base_sha
    assert tracked_file.read_text(encoding="utf-8") == "base\n"
    clean_snapshot = service.snapshot()
    assert clean_snapshot.is_dirty is False
    assert service.diff_summary() == ""


def test_null_workspace_service_returns_stable_empty_rollback_context(tmp_path: Path) -> None:
    service = NullWorkspaceService(repo_root=tmp_path)

    context = service.rollback_pre_run()

    assert context.repo_root == tmp_path
    assert context.worktree_path == tmp_path
    assert context.branch_name == ""
    assert context.run_id is None
