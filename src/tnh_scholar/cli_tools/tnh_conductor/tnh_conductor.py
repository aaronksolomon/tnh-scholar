"""Typer entrypoint for the maintained tnh-conductor CLI."""

from __future__ import annotations

import time
from pathlib import Path

import typer

from tnh_scholar.agent_orchestration.app import (
    HeadlessBootstrapConfig,
    HeadlessBootstrapParams,
    HeadlessBootstrapService,
    HeadlessRunnerConfig,
    HeadlessStorageConfig,
    build_bootstrap_runtime_profile,
)
from tnh_scholar.agent_orchestration.run_artifacts import (
    FilesystemRunArtifactStore,
    RunLifecycleState,
    RunStatus,
)

STATUS_STORE = FilesystemRunArtifactStore()

app = typer.Typer(
    name="tnh-conductor",
    help="Maintained local/headless workflow bootstrap runner.",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def conductor_app() -> None:
    """Expose `tnh-conductor` as a command group."""


@app.command("run")
def run_command(
    workflow: Path = typer.Option(
        ...,
        "--workflow",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Workflow YAML file to execute.",
    ),
    repo_root: Path = typer.Option(
        Path.cwd(),
        "--repo-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Repository root for the managed worktree run.",
    ),
    runs_root: Path | None = typer.Option(
        None,
        "--runs-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Optional override for the canonical runs root.",
    ),
    workspace_root: Path | None = typer.Option(
        None,
        "--workspace-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Optional override for the managed worktree root.",
    ),
    base_ref: str = typer.Option("HEAD", "--base-ref", help="Committed git base ref for the run."),
    codex_executable: Path | None = typer.Option(
        None,
        "--codex-executable",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Optional explicit path to the Codex executable.",
    ),
    claude_executable: Path | None = typer.Option(
        None,
        "--claude-executable",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Optional explicit path to the Claude executable.",
    ),
) -> None:
    """Execute one maintained local/headless bootstrap run."""
    resolved_repo_root = repo_root.resolve()
    default_storage = HeadlessStorageConfig.for_repo_root(resolved_repo_root)
    runtime_profile = build_bootstrap_runtime_profile()
    storage = HeadlessStorageConfig(
        runs_root=default_storage.runs_root if runs_root is None else runs_root,
        workspace_root=default_storage.workspace_root if workspace_root is None else workspace_root,
    )
    service = HeadlessBootstrapService(
        config=HeadlessBootstrapConfig(
            repo_root=resolved_repo_root,
            storage=storage,
            base_ref=base_ref,
            runner=HeadlessRunnerConfig(
                codex_executable=codex_executable,
                claude_executable=claude_executable,
            ),
            validation=runtime_profile.validation,
            policy=runtime_profile.policy,
        )
    )
    try:
        result = service.run(HeadlessBootstrapParams(workflow_path=workflow))
    except Exception as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(result.model_dump_json())


@app.command("status")
def status_command(
    run_id: str = typer.Argument(..., help="Run id to inspect."),
    repo_root: Path = typer.Option(
        Path.cwd(),
        "--repo-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Repository root used to resolve default storage roots.",
    ),
    runs_root: Path | None = typer.Option(
        None,
        "--runs-root",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Optional override for the canonical runs root.",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        help="Poll and print status snapshots until the run reaches a terminal state.",
    ),
    poll_interval_seconds: float = typer.Option(
        1.0,
        "--poll-interval-seconds",
        help="Polling interval in seconds when --watch is enabled.",
    ),
) -> None:
    """Read the maintained live status artifact for one run."""
    resolved_repo_root = repo_root.resolve()
    default_storage = HeadlessStorageConfig.for_repo_root(resolved_repo_root)
    resolved_runs_root = default_storage.runs_root if runs_root is None else runs_root
    _validate_poll_interval(poll_interval_seconds)
    _assert_status_exists(run_id, resolved_runs_root)
    if not watch:
        _emit_status_snapshot(_read_status_or_exit(run_id, resolved_runs_root))
        return
    _watch_status(
        run_id=run_id,
        resolved_runs_root=resolved_runs_root,
        poll_interval_seconds=poll_interval_seconds,
    )


def _validate_poll_interval(poll_interval_seconds: float) -> None:
    """Reject non-positive polling intervals."""
    if poll_interval_seconds > 0:
        return
    typer.echo("Poll interval must be greater than 0 seconds.", err=True)
    raise typer.Exit(code=1)


def _assert_status_exists(run_id: str, resolved_runs_root: Path) -> None:
    """Fail fast when the canonical status artifact does not exist."""
    status_path = STATUS_STORE.status_path_for_run(run_id, resolved_runs_root)
    if status_path.exists():
        return
    typer.echo(
        f"Run status not found for '{run_id}' at {status_path}.",
        err=True,
    )
    raise typer.Exit(code=1)


def _read_status_or_exit(run_id: str, resolved_runs_root: Path) -> RunStatus:
    """Read one live status snapshot or exit with a stable CLI error."""
    try:
        return STATUS_STORE.read_status(run_id, resolved_runs_root)
    except Exception as error:
        typer.echo(f"Failed to read run status for '{run_id}': {error}", err=True)
        raise typer.Exit(code=1) from error


def _emit_status_snapshot(status: RunStatus) -> None:
    """Print one machine-readable status snapshot."""
    typer.echo(status.model_dump_json())


def _watch_status(
    *,
    run_id: str,
    resolved_runs_root: Path,
    poll_interval_seconds: float,
) -> None:
    """Poll status until the run reaches a terminal lifecycle state."""
    while True:
        status = _read_status_or_exit(run_id, resolved_runs_root)
        _emit_status_snapshot(status)
        if _is_terminal_lifecycle_state(status.lifecycle_state):
            return
        time.sleep(poll_interval_seconds)


def _is_terminal_lifecycle_state(lifecycle_state: RunLifecycleState) -> bool:
    """Return whether a lifecycle state should stop watch mode."""
    return lifecycle_state in (
        RunLifecycleState.completed,
        RunLifecycleState.failed,
        RunLifecycleState.blocked,
    )


def main() -> None:
    """Dispatch to the Typer app."""
    app()
