"""Tests for the maintained headless bootstrap service."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from textwrap import dedent

from tnh_scholar.agent_orchestration.app import (
    HeadlessBootstrapConfig,
    HeadlessBootstrapParams,
    HeadlessBootstrapService,
    HeadlessRunnerConfig,
    HeadlessStorageConfig,
    build_bootstrap_runtime_profile,
)
from tnh_scholar.agent_orchestration.run_artifacts.models import ArtifactRole, StepManifest


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
    (repo_root / "README.md").write_text("bootstrap repo\n", encoding="utf-8")
    _git(repo_root, "add", "README.md")
    _git(repo_root, "commit", "-m", "initial")
    return repo_root


def _write_workflow(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            workflow_id: bootstrap-workflow
            version: 1
            description: Maintained bootstrap test
            entry_step: agent
            steps:
              - id: agent
                opcode: RUN_AGENT
                agent: codex
                prompt: create validation harness
                routes:
                  completed: validate
              - id: validate
                opcode: RUN_VALIDATION
                run:
                  - kind: harness
                    name: generated_harness
                routes:
                  completed: STOP
              - id: STOP
                opcode: STOP
            """
        ),
        encoding="utf-8",
    )


def _write_evaluate_workflow(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            workflow_id: evaluate-bootstrap
            version: 1
            description: Unsupported evaluate test
            entry_step: evaluate
            steps:
              - id: evaluate
                opcode: EVALUATE
                prompt: assess evidence
                routes:
                  success: STOP
              - id: STOP
                opcode: STOP
            """
        ),
        encoding="utf-8",
    )


def _write_gate_workflow(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            workflow_id: gate-bootstrap
            version: 1
            description: Unsupported gate test
            entry_step: gate
            steps:
              - id: gate
                opcode: GATE
                gate: requires_approval
                routes:
                  gate_approved: STOP
              - id: STOP
                opcode: STOP
            """
        ),
        encoding="utf-8",
    )


def _write_rollback_workflow(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            workflow_id: rollback-bootstrap
            version: 1
            description: Rollback bootstrap test
            entry_step: agent
            steps:
              - id: agent
                opcode: RUN_AGENT
                agent: codex
                prompt: create mutable file
                routes:
                  completed: rollback
              - id: rollback
                opcode: ROLLBACK
                target: pre_run
                routes:
                  completed: STOP
              - id: STOP
                opcode: STOP
            """
        ),
        encoding="utf-8",
    )


def _write_agent_failure_workflow(path: Path) -> None:
    path.write_text(
        dedent(
            """\
            workflow_id: failure-bootstrap
            version: 1
            description: Agent failure bootstrap test
            entry_step: agent
            steps:
              - id: agent
                opcode: RUN_AGENT
                agent: codex
                prompt: fail the run
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
            cat <<'EOF' > bootstrap-output.txt
            changed by bootstrap stub
            EOF
            cat <<'EOF' > generated_harness.py
            from pathlib import Path
            Path("harness_report.json").write_text('{"proposed_goldens": []}', encoding="utf-8")
            print("validation ok")
            EOF
            printf 'done\\n' > "$response_path"
            printf '{"type":"message","text":"bootstrap stub transcript"}\\n'
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_mutating_codex_stub(path: Path) -> None:
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
            printf 'dirty\\n' > rollback-target.txt
            printf 'done\\n' > "$response_path"
            printf '{"type":"message","text":"rollback transcript"}\\n'
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_failing_codex_stub(path: Path) -> None:
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
            printf 'partial\\n' > "$response_path"
            printf '{"type":"message","text":"failure transcript"}\\n'
            exit 1
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _read_manifest(run_directory: Path, step_id: str) -> StepManifest:
    path = run_directory / "artifacts" / step_id / "manifest.json"
    return StepManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _bootstrap_config(
    *,
    repo_root: Path,
    runs_root: Path,
    workspace_root: Path,
    codex_executable: Path | None = None,
) -> HeadlessBootstrapConfig:
    runtime_profile = build_bootstrap_runtime_profile()
    return HeadlessBootstrapConfig(
        repo_root=repo_root,
        storage=HeadlessStorageConfig(
            runs_root=runs_root,
            workspace_root=workspace_root,
        ),
        base_ref="main",
        runner=HeadlessRunnerConfig(codex_executable=codex_executable),
        validation=runtime_profile.validation,
        policy=runtime_profile.policy,
    )


def test_headless_bootstrap_service_runs_workflow_in_managed_worktree(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow.yaml"
    codex_stub = tmp_path / "codex-stub.sh"
    _write_workflow(workflow_path)
    _write_codex_stub(codex_stub)

    service = HeadlessBootstrapService(
        config=_bootstrap_config(
            repo_root=repo_root,
            runs_root=tmp_path / "runs",
            workspace_root=tmp_path / "worktrees",
            codex_executable=codex_stub,
        ),
    )

    result = service.run(HeadlessBootstrapParams(workflow_path=workflow_path))

    assert result.status == "completed"
    assert result.metadata_path.exists()
    assert result.final_state_path.exists()
    assert result.workspace_context is not None
    assert result.workspace_context.worktree_path != result.run_directory
    assert result.workspace_context.worktree_path.parent == tmp_path / "worktrees"
    assert (result.workspace_context.worktree_path / "bootstrap-output.txt").read_text(
        encoding="utf-8"
    ) == "changed by bootstrap stub\n"
    assert not (result.run_directory / "bootstrap-output.txt").exists()

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["workflow_id"] == "bootstrap-workflow"
    assert metadata["termination"] == "completed"
    assert metadata["workspace_context"]["base_ref"] == "main"
    assert metadata["workspace_context"]["worktree_path"] == str(
        result.workspace_context.worktree_path
    )
    assert result.final_state_path.read_text(encoding="utf-8").strip() == "completed:STOP"

    agent_manifest = _read_manifest(result.run_directory, "agent")
    validate_manifest = _read_manifest(result.run_directory, "validate")
    assert agent_manifest.artifact_for_role(ArtifactRole.runner_transcript) is not None
    assert agent_manifest.artifact_for_role(ArtifactRole.runner_final_response) is not None
    assert validate_manifest.artifact_for_role(ArtifactRole.validation_report) is not None
    assert validate_manifest.artifact_for_role(ArtifactRole.validation_stdout) is not None


def test_headless_bootstrap_service_rejects_evaluate_and_gate_steps(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow-evaluate.yaml"
    _write_evaluate_workflow(workflow_path)
    service = HeadlessBootstrapService(
        config=_bootstrap_config(
            repo_root=repo_root,
            runs_root=tmp_path / "runs",
            workspace_root=tmp_path / "worktrees",
        ),
    )

    try:
        service.run(HeadlessBootstrapParams(workflow_path=workflow_path))
    except ValueError as error:
        assert "does not support semantic control steps yet" in str(error)
        assert "EVALUATE" in str(error)
        return
    raise AssertionError("Expected bootstrap service to reject EVALUATE step")


def test_headless_bootstrap_service_rejects_gate_steps(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow-gate.yaml"
    _write_gate_workflow(workflow_path)
    service = HeadlessBootstrapService(
        config=_bootstrap_config(
            repo_root=repo_root,
            runs_root=tmp_path / "runs",
            workspace_root=tmp_path / "worktrees",
        ),
    )

    try:
        service.run(HeadlessBootstrapParams(workflow_path=workflow_path))
    except ValueError as error:
        assert "does not support semantic control steps yet" in str(error)
        assert "GATE" in str(error)
        return
    raise AssertionError("Expected bootstrap service to reject GATE step")


def test_headless_bootstrap_service_supports_pre_run_rollback(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow-rollback.yaml"
    codex_stub = tmp_path / "codex-rollback-stub.sh"
    _write_rollback_workflow(workflow_path)
    _write_mutating_codex_stub(codex_stub)
    service = HeadlessBootstrapService(
        config=_bootstrap_config(
            repo_root=repo_root,
            runs_root=tmp_path / "runs",
            workspace_root=tmp_path / "worktrees",
            codex_executable=codex_stub,
        ),
    )

    result = service.run(HeadlessBootstrapParams(workflow_path=workflow_path))

    assert result.workspace_context is not None
    assert not (result.workspace_context.worktree_path / "rollback-target.txt").exists()


def test_headless_bootstrap_service_persists_terminal_metadata_on_agent_failure(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path)
    workflow_path = tmp_path / "workflow-failure.yaml"
    codex_stub = tmp_path / "codex-failure-stub.sh"
    runs_root = tmp_path / "runs"
    _write_agent_failure_workflow(workflow_path)
    _write_failing_codex_stub(codex_stub)
    service = HeadlessBootstrapService(
        config=_bootstrap_config(
            repo_root=repo_root,
            runs_root=runs_root,
            workspace_root=tmp_path / "worktrees",
            codex_executable=codex_stub,
        ),
    )

    try:
        service.run(HeadlessBootstrapParams(workflow_path=workflow_path))
    except Exception as error:
        assert "No route for outcome" in str(error)
    else:
        raise AssertionError("Expected bootstrap service to fail on unmapped runner error")

    run_directories = list(runs_root.iterdir())
    assert len(run_directories) == 1
    run_directory = run_directories[0]
    metadata = json.loads((run_directory / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["termination"] == "error"
    assert metadata["last_step_id"] == "agent"
    assert (run_directory / "final-state.txt").read_text(encoding="utf-8").strip() == "error:agent"
