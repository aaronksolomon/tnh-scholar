"""Typer entrypoint for the maintained tnh-conductor CLI."""

from __future__ import annotations

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


def main() -> None:
    """Dispatch to the Typer app."""
    app()
