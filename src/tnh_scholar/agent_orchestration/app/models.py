"""Typed models for the maintained headless bootstrap app layer."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.execution_policy import ExecutionPolicySettings
from tnh_scholar.agent_orchestration.validation import BuiltinCommandEntry
from tnh_scholar.agent_orchestration.workspace.models import WorkspaceContext


class HeadlessStorageConfig(BaseModel):
    """Construction-time storage roots for headless bootstrap runs."""

    runs_root: Path
    workspace_root: Path

    @classmethod
    def for_repo_root(cls, repo_root: Path) -> "HeadlessStorageConfig":
        """Return the default storage layout rooted under one repository."""
        conductor_root = repo_root / ".tnh-conductor"
        return cls(
            runs_root=conductor_root / "runs",
            workspace_root=conductor_root / "worktrees",
        )


class HeadlessRunnerConfig(BaseModel):
    """Construction-time runner executable config."""

    codex_executable: Path | None = None
    claude_executable: Path | None = None


class HeadlessValidationConfig(BaseModel):
    """Construction-time builtin validator mapping config."""

    builtin_commands: tuple[BuiltinCommandEntry, ...] = Field(default_factory=tuple)


class HeadlessPolicyConfig(BaseModel):
    """Construction-time execution policy config."""

    execution_policy_settings: ExecutionPolicySettings


class HeadlessBootstrapConfig(BaseModel):
    """Construction-time config for the maintained headless bootstrap path."""

    repo_root: Path
    storage: HeadlessStorageConfig
    base_ref: str = "HEAD"
    branch_prefix: str = "tnh/run-"
    runner: HeadlessRunnerConfig = Field(default_factory=HeadlessRunnerConfig)
    validation: HeadlessValidationConfig
    policy: HeadlessPolicyConfig


class HeadlessBootstrapParams(BaseModel):
    """Per-run parameters for the maintained headless bootstrap path."""

    workflow_path: Path


class HeadlessBootstrapResult(BaseModel):
    """Stable summary returned by the maintained headless bootstrap path."""

    run_id: str
    workflow_id: str
    status: str
    run_directory: Path
    metadata_path: Path
    status_path: Path
    final_state_path: Path
    workspace_context: WorkspaceContext | None = None
