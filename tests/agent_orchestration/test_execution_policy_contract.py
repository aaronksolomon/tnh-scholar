"""Tests for the maintained execution-policy contract."""

from __future__ import annotations

from pathlib import Path

from tnh_scholar.agent_orchestration.execution_policy import (
    ApprovalPosture,
    ExecutionPolicyAssembler,
    ExecutionPolicyAssemblyError,
    ExecutionPolicySettings,
    ExecutionPosture,
    NetworkPosture,
    RequestedExecutionPolicy,
)
from tnh_scholar.agent_orchestration.runners import RunnerTaskRequest


def test_execution_policy_assembler_applies_precedence_and_runtime_tightening() -> None:
    assembler = ExecutionPolicyAssembler()
    settings = ExecutionPolicySettings(
        default_policy=RequestedExecutionPolicy(
            execution_posture=ExecutionPosture.workspace_write,
            network_posture=NetworkPosture.allow,
            approval_posture=ApprovalPosture.bounded_auto_approve,
            allowed_paths=(Path("src"), Path("tests")),
        ),
        named_policies={
            "workflow.safe": RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.workspace_write,
                network_posture=NetworkPosture.allow,
                forbidden_operations=("git-push",),
            ),
            "step.review_only": RequestedExecutionPolicy(
                approval_posture=ApprovalPosture.deny_interactive,
                allowed_paths=(Path("src"),),
                forbidden_paths=(Path(".github"),),
            ),
        },
        runtime_overrides=RequestedExecutionPolicy(
            execution_posture=ExecutionPosture.read_only,
            network_posture=NetworkPosture.deny,
            forbidden_operations=("rm",),
        ),
    )

    summary = assembler.assemble(
        settings=settings,
        workflow_policy_ref="workflow.safe",
        step_policy_ref="step.review_only",
    )

    assert summary.requested_policy.policy_reference == "step.review_only"
    assert summary.requested_policy.execution_posture == ExecutionPosture.workspace_write
    assert summary.requested_policy.network_posture == NetworkPosture.allow
    assert summary.requested_policy.approval_posture == ApprovalPosture.deny_interactive
    assert summary.requested_policy.allowed_paths == (Path("src"),)
    assert summary.requested_policy.forbidden_paths == (Path(".github"),)
    assert summary.requested_policy.forbidden_operations == ("git-push",)
    assert summary.effective_policy.execution_posture == ExecutionPosture.read_only
    assert summary.effective_policy.network_posture == NetworkPosture.deny
    assert summary.effective_policy.approval_posture == ApprovalPosture.deny_interactive
    assert summary.effective_policy.allowed_paths == (Path("src"),)
    assert summary.effective_policy.forbidden_operations == ("git-push", "rm")


def test_execution_policy_assembler_uses_stricter_approval_posture_from_runtime_override() -> None:
    assembler = ExecutionPolicyAssembler()
    summary = assembler.assemble(
        settings=ExecutionPolicySettings(
            default_policy=RequestedExecutionPolicy(
                approval_posture=ApprovalPosture.bounded_auto_approve,
            )
        ),
        runtime_overrides=RequestedExecutionPolicy(
            approval_posture=ApprovalPosture.fail_on_prompt,
        ),
    )

    assert summary.requested_policy.approval_posture == ApprovalPosture.bounded_auto_approve
    assert summary.effective_policy.approval_posture == ApprovalPosture.fail_on_prompt


def test_execution_policy_assembler_allows_explicit_empty_allowed_paths_override() -> None:
    assembler = ExecutionPolicyAssembler()
    settings = ExecutionPolicySettings(
        default_policy=RequestedExecutionPolicy(
            execution_posture=ExecutionPosture.read_only,
            allowed_paths=(Path("src"),),
        ),
        named_policies={
            "step.no_paths": RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.read_only,
                allowed_paths=(),
            )
        },
    )

    summary = assembler.assemble(
        settings=settings,
        step_policy_ref="step.no_paths",
    )

    assert summary.requested_policy.allowed_paths == ()
    assert summary.effective_policy.allowed_paths == ()


def test_execution_policy_assembler_allows_runtime_override_to_empty_allowed_paths() -> None:
    assembler = ExecutionPolicyAssembler()
    summary = assembler.assemble(
        settings=ExecutionPolicySettings(
            default_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.read_only,
                allowed_paths=(Path("src"),),
            )
        ),
        runtime_overrides=RequestedExecutionPolicy(allowed_paths=()),
    )

    assert summary.requested_policy.allowed_paths == (Path("src"),)
    assert summary.effective_policy.allowed_paths == ()


def test_execution_policy_assembler_fails_fast_for_unknown_reference() -> None:
    assembler = ExecutionPolicyAssembler()

    try:
        assembler.assemble(
            settings=ExecutionPolicySettings(),
            step_policy_ref="missing.policy",
        )
    except ExecutionPolicyAssemblyError as error:
        assert "missing.policy" in str(error)
        return

    raise AssertionError("Expected ExecutionPolicyAssemblyError")


def test_runner_task_request_uses_requested_execution_policy() -> None:
    request = RunnerTaskRequest(
        agent_family="codex_cli",
        rendered_task_text="do the work",
        working_directory=Path.cwd(),
        requested_policy=RequestedExecutionPolicy(
            execution_posture=ExecutionPosture.workspace_write,
            approval_posture=ApprovalPosture.bounded_auto_approve,
        ),
    )

    assert request.requested_policy.execution_posture == ExecutionPosture.workspace_write
    assert request.requested_policy.approval_posture == ApprovalPosture.bounded_auto_approve


def test_execution_policy_assembler_marks_empty_write_scope_as_hard_violation() -> None:
    assembler = ExecutionPolicyAssembler()
    summary = assembler.assemble(
        settings=ExecutionPolicySettings(
            default_policy=RequestedExecutionPolicy(
                execution_posture=ExecutionPosture.workspace_write,
                allowed_paths=(),
            )
        )
    )

    assert len(summary.violations) == 1
    assert summary.violations[0].violation_class.value == "forbidden_path"
    assert summary.violations[0].hard_violation is True
