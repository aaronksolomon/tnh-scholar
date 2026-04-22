from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from tnh_scholar.agent_orchestration.kernel.enums import Opcode
from tnh_scholar.agent_orchestration.run_artifacts import RunLifecycleState, RunStatus
from tnh_scholar.cli_tools.tnh_conductor import tnh_conductor

runner = CliRunner(mix_stderr=False)


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    raise AssertionError(result.stderr.strip())


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


def _write_workflow(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            workflow_id: cli-bootstrap
            version: 1
            description: CLI bootstrap test
            entry_step: agent
            steps:
              - id: agent
                opcode: RUN_AGENT
                agent: codex
                prompt: write one file
                routes:
                  completed: STOP
              - id: STOP
                opcode: STOP
            """
        ),
        encoding="utf-8",
    )


def _write_codex_stub(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            #!/bin/sh
            response_path=""
            while [ "$#" -gt 0 ]; do
              if [ "$1" = "--output-last-message" ]; then
                response_path="$2"
                shift 2
                continue
              fi
              shift 1
            done
            cat <<'EOF' > cli-output.txt
            changed by cli stub
            EOF
            printf 'done\\n' > "$response_path"
            printf '{"type":"message","text":"cli transcript"}\\n'
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_tnh_conductor_run_outputs_bootstrap_summary(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow.yaml"
    runs_root = tmp_path / "runs"
    workspace_root = tmp_path / "worktrees"
    codex_stub = tmp_path / "codex-stub.sh"
    _write_workflow(workflow_path)
    _write_codex_stub(codex_stub)

    result = runner.invoke(
        tnh_conductor.app,
        [
            "run",
            "--workflow",
            str(workflow_path),
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
            "--workspace-root",
            str(workspace_root),
            "--base-ref",
            "main",
            "--codex-executable",
            str(codex_stub),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["workflow_id"] == "cli-bootstrap"
    assert payload["status"] == "completed"
    assert Path(payload["metadata_path"]).exists()
    assert Path(payload["status_path"]).exists()
    assert Path(payload["final_state_path"]).exists()
    assert Path(payload["workspace_context"]["worktree_path"]).parent == workspace_root


def test_tnh_conductor_run_uses_default_storage_roots(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow-defaults.yaml"
    codex_stub = tmp_path / "codex-default-stub.sh"
    _write_workflow(workflow_path)
    _write_codex_stub(codex_stub)

    result = runner.invoke(
        tnh_conductor.app,
        [
            "run",
            "--workflow",
            str(workflow_path),
            "--repo-root",
            str(repo_root),
            "--base-ref",
            "main",
            "--codex-executable",
            str(codex_stub),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert Path(payload["run_directory"]).parent == repo_root / ".tnh-conductor" / "runs"
    assert Path(payload["workspace_context"]["worktree_path"]).parent == (
        repo_root / ".tnh-conductor" / "worktrees"
    )


def test_tnh_conductor_status_outputs_live_run_status(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow-status.yaml"
    runs_root = tmp_path / "runs"
    workspace_root = tmp_path / "worktrees"
    codex_stub = tmp_path / "codex-status-stub.sh"
    _write_workflow(workflow_path)
    _write_codex_stub(codex_stub)

    run_result = runner.invoke(
        tnh_conductor.app,
        [
            "run",
            "--workflow",
            str(workflow_path),
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
            "--workspace-root",
            str(workspace_root),
            "--base-ref",
            "main",
            "--codex-executable",
            str(codex_stub),
        ],
    )
    assert run_result.exit_code == 0, run_result.output
    run_payload = json.loads(run_result.stdout)

    status_result = runner.invoke(
        tnh_conductor.app,
        [
            "status",
            run_payload["run_id"],
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
        ],
    )

    assert status_result.exit_code == 0, status_result.output
    status_payload = json.loads(status_result.stdout)
    assert status_payload["run_id"] == run_payload["run_id"]
    assert status_payload["workflow_id"] == "cli-bootstrap"
    assert status_payload["lifecycle_state"] == "completed"
    assert status_payload["termination"] == "completed"


def test_tnh_conductor_status_fails_for_missing_run(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    runs_root = tmp_path / "runs"

    result = runner.invoke(
        tnh_conductor.app,
        [
            "status",
            "missing-run",
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
        ],
    )

    assert result.exit_code == 1
    assert "Run status not found" in result.stderr


def test_tnh_conductor_status_watch_outputs_jsonl_until_completed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path)
    runs_root = tmp_path / "runs"
    run_id = "watch-run"
    paths = tnh_conductor.STATUS_STORE.create_run(run_id, runs_root)

    emitted_statuses = iter(
        (
            _build_status(
                run_id=run_id,
                workflow_id="watch-workflow",
                lifecycle_state=RunLifecycleState.running,
                updated_second=1,
            ),
            _build_status(
                run_id=run_id,
                workflow_id="watch-workflow",
                lifecycle_state=RunLifecycleState.waiting,
                updated_second=2,
            ),
            _build_status(
                run_id=run_id,
                workflow_id="watch-workflow",
                lifecycle_state=RunLifecycleState.completed,
                updated_second=3,
            ),
        )
    )
    sleep_calls: list[float] = []
    tnh_conductor.STATUS_STORE.write_status(
        _build_status(
            run_id=run_id,
            workflow_id="watch-workflow",
            lifecycle_state=RunLifecycleState.running,
            updated_second=0,
        ),
        paths,
    )

    monkeypatch.setattr(
        type(tnh_conductor.STATUS_STORE),
        "read_status",
        lambda _, requested_run_id, requested_root: _next_status(
            emitted_statuses,
            requested_run_id=requested_run_id,
            requested_root=requested_root,
            expected_run_id=run_id,
            expected_root=runs_root,
        ),
    )
    monkeypatch.setattr(tnh_conductor.time, "sleep", sleep_calls.append)

    result = runner.invoke(
        tnh_conductor.app,
        [
            "status",
            run_id,
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
            "--watch",
            "--poll-interval-seconds",
            "0.25",
        ],
    )

    assert result.exit_code == 0, result.output
    payloads = [json.loads(line) for line in result.stdout.splitlines()]
    assert [payload["lifecycle_state"] for payload in payloads] == [
        RunLifecycleState.running.value,
        RunLifecycleState.waiting.value,
        RunLifecycleState.completed.value,
    ]
    assert sleep_calls == [0.25, 0.25]


def test_tnh_conductor_status_watch_stops_when_blocked(monkeypatch, tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    runs_root = tmp_path / "runs"
    run_id = "blocked-run"
    paths = tnh_conductor.STATUS_STORE.create_run(run_id, runs_root)

    emitted_statuses = iter(
        (
            _build_status(
                run_id=run_id,
                workflow_id="watch-workflow",
                lifecycle_state=RunLifecycleState.running,
                updated_second=1,
            ),
            _build_status(
                run_id=run_id,
                workflow_id="watch-workflow",
                lifecycle_state=RunLifecycleState.blocked,
                updated_second=2,
                blocking_reason="needs_human",
            ),
        )
    )
    sleep_calls: list[float] = []
    tnh_conductor.STATUS_STORE.write_status(
        _build_status(
            run_id=run_id,
            workflow_id="watch-workflow",
            lifecycle_state=RunLifecycleState.running,
            updated_second=0,
        ),
        paths,
    )

    monkeypatch.setattr(
        type(tnh_conductor.STATUS_STORE),
        "read_status",
        lambda _, requested_run_id, requested_root: _next_status(
            emitted_statuses,
            requested_run_id=requested_run_id,
            requested_root=requested_root,
            expected_run_id=run_id,
            expected_root=runs_root,
        ),
    )
    monkeypatch.setattr(tnh_conductor.time, "sleep", sleep_calls.append)

    result = runner.invoke(
        tnh_conductor.app,
        [
            "status",
            run_id,
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
            "--watch",
        ],
    )

    assert result.exit_code == 0, result.output
    payloads = [json.loads(line) for line in result.stdout.splitlines()]
    assert [payload["lifecycle_state"] for payload in payloads] == [
        RunLifecycleState.running.value,
        RunLifecycleState.blocked.value,
    ]
    assert payloads[-1]["blocking_reason"] == "needs_human"
    assert sleep_calls == [1.0]


def _build_status(
    *,
    run_id: str,
    workflow_id: str,
    lifecycle_state: RunLifecycleState,
    updated_second: int,
    blocking_reason: str | None = None,
) -> RunStatus:
    """Build one typed CLI status snapshot fixture."""
    return RunStatus(
        run_id=run_id,
        workflow_id=workflow_id,
        started_at=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 20, 12, 0, updated_second, tzinfo=timezone.utc),
        lifecycle_state=lifecycle_state,
        current_step_id="implement",
        last_completed_step_id="design",
        active_opcode=Opcode.run_agent,
        elapsed_seconds=updated_second,
        blocking_reason=blocking_reason,
    )


def _next_status(
    statuses: Iterator[RunStatus],
    *,
    requested_run_id: str,
    requested_root: Path,
    expected_run_id: str,
    expected_root: Path,
) -> RunStatus:
    """Return the next mocked status and validate the CLI call contract."""
    assert requested_run_id == expected_run_id
    assert requested_root == expected_root
    return next(statuses)
