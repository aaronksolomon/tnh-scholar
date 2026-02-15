"""Tests for conductor MVP workflow validation and execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tnh_scholar.agent_orchestration.conductor_mvp.models import (
    AgentRunResult,
    BuiltinValidatorSpec,
    EvaluateStep,
    GateOutcome,
    GateStep,
    MechanicalOutcome,
    PlannerDecision,
    PlannerStatus,
    RouteRule,
    RunAgentStep,
    RunValidationStep,
    ScriptValidatorSpec,
    StopStep,
    ValidationRunResult,
    WorkflowDefinition,
)
from tnh_scholar.agent_orchestration.conductor_mvp.providers.artifact_store import (
    FileArtifactStore,
)
from tnh_scholar.agent_orchestration.conductor_mvp.service import (
    ConductorKernelService,
    WorkflowValidationError,
    WorkflowValidator,
)


@dataclass(frozen=True)
class FixedClock:
    """Clock returning a fixed timestamp."""

    now_value: datetime

    def now(self) -> datetime:
        return self.now_value


@dataclass(frozen=True)
class FixedRunId:
    """Run ID generator for deterministic tests."""

    run_id: str

    def next_id(self, now: datetime) -> str:
        return self.run_id


@dataclass(frozen=True)
class NoopWorkspace:
    """Workspace provider with no side effects."""

    def capture_pre_run(self, run_id: str) -> None:
        return None

    def rollback(self, step) -> None:
        return None


@dataclass(frozen=True)
class SuccessAgentRunner:
    """Agent runner returning completed outcome."""

    def run(self, step: RunAgentStep, run_dir: Path) -> AgentRunResult:
        return AgentRunResult(outcome=MechanicalOutcome.completed)


@dataclass(frozen=True)
class FixedValidationRunner:
    """Validation runner with fixed return payload."""

    result: ValidationRunResult

    def run(self, step: RunValidationStep, run_dir: Path) -> ValidationRunResult:
        return self.result


@dataclass(frozen=True)
class FixedEvaluator:
    """Planner evaluator with fixed decision."""

    decision: PlannerDecision

    def evaluate(self, step: EvaluateStep, run_dir: Path) -> PlannerDecision:
        return self.decision


@dataclass(frozen=True)
class FixedGateApprover:
    """Gate approver with fixed outcome."""

    outcome: GateOutcome

    def decide(self, step: GateStep, run_dir: Path) -> GateOutcome:
        return self.outcome


def _validation_step() -> RunValidationStep:
    return RunValidationStep(
        id="validate",
        run=[
            BuiltinValidatorSpec(name="tests"),
            ScriptValidatorSpec(
                id="generated_harness",
                entrypoint=Path("harness.py"),
                may_propose_goldens=True,
            ),
        ],
        routes=[
            RouteRule(outcome=MechanicalOutcome.completed.value, target="evaluate"),
            RouteRule(outcome=MechanicalOutcome.error.value, target="evaluate"),
            RouteRule(outcome=MechanicalOutcome.killed_timeout.value, target="evaluate"),
            RouteRule(outcome=MechanicalOutcome.killed_idle.value, target="evaluate"),
            RouteRule(outcome=MechanicalOutcome.killed_policy.value, target="evaluate"),
        ],
    )


def test_validator_rejects_golden_flow_without_gate() -> None:
    workflow = WorkflowDefinition(
        workflow_id="w1",
        version=1,
        description="missing gate",
        entry_step="agent",
        steps=[
            RunAgentStep(
                id="agent",
                agent="codex",
                prompt="task",
                routes=[RouteRule(outcome=MechanicalOutcome.completed.value, target="validate")],
            ),
            _validation_step(),
            EvaluateStep(
                id="evaluate",
                prompt="planner",
                allowed_next_steps=["STOP"],
                routes=[
                    RouteRule(outcome=PlannerStatus.success.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.partial.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.blocked.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.unsafe.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.needs_human.value, target="STOP"),
                ],
            ),
            StopStep(id="STOP"),
        ],
    )
    with pytest.raises(WorkflowValidationError, match="reachable GATE"):
        WorkflowValidator().validate(workflow)


def test_runtime_blocks_success_stop_until_gate_after_proposed_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w2",
        version=1,
        description="strong runtime check",
        entry_step="agent",
        steps=[
            RunAgentStep(
                id="agent",
                agent="codex",
                prompt="task",
                routes=[RouteRule(outcome=MechanicalOutcome.completed.value, target="validate")],
            ),
            _validation_step(),
            EvaluateStep(
                id="evaluate",
                prompt="planner",
                allowed_next_steps=["gate", "STOP"],
                routes=[
                    RouteRule(outcome=PlannerStatus.success.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.partial.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.blocked.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.unsafe.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.needs_human.value, target="gate"),
                ],
            ),
            GateStep(
                id="gate",
                gate="requires_approval",
                routes=[
                    RouteRule(outcome=GateOutcome.gate_approved.value, target="STOP"),
                    RouteRule(outcome=GateOutcome.gate_rejected.value, target="STOP"),
                    RouteRule(outcome=GateOutcome.gate_timed_out.value, target="STOP"),
                ],
            ),
            StopStep(id="STOP"),
        ],
    )
    service = ConductorKernelService(
        clock=FixedClock(datetime(2026, 2, 10, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-1"),
        artifact_store=FileArtifactStore(),
        workspace=NoopWorkspace(),
        agent_runner=SuccessAgentRunner(),
        validation_runner=FixedValidationRunner(
            ValidationRunResult.model_validate(
                {"outcome": "completed", "harness_report": {"proposed_goldens": ["x.png"]}}
            )
        ),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="STOP")),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    with pytest.raises(WorkflowValidationError, match="must pass through GATE"):
        service.run(workflow, tmp_path)


def test_runtime_allows_success_when_path_includes_gate_after_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w3",
        version=1,
        description="gate before success stop",
        entry_step="agent",
        steps=[
            RunAgentStep(
                id="agent",
                agent="codex",
                prompt="task",
                routes=[RouteRule(outcome=MechanicalOutcome.completed.value, target="validate")],
            ),
            _validation_step(),
            EvaluateStep(
                id="evaluate",
                prompt="planner",
                allowed_next_steps=["gate", "STOP"],
                routes=[
                    RouteRule(outcome=PlannerStatus.success.value, target="gate"),
                    RouteRule(outcome=PlannerStatus.partial.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.blocked.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.unsafe.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.needs_human.value, target="gate"),
                ],
            ),
            GateStep(
                id="gate",
                gate="requires_approval",
                routes=[
                    RouteRule(outcome=GateOutcome.gate_approved.value, target="STOP"),
                    RouteRule(outcome=GateOutcome.gate_rejected.value, target="STOP"),
                    RouteRule(outcome=GateOutcome.gate_timed_out.value, target="STOP"),
                ],
            ),
            StopStep(id="STOP"),
        ],
    )
    service = ConductorKernelService(
        clock=FixedClock(datetime(2026, 2, 10, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-2"),
        artifact_store=FileArtifactStore(),
        workspace=NoopWorkspace(),
        agent_runner=SuccessAgentRunner(),
        validation_runner=FixedValidationRunner(
            ValidationRunResult.model_validate(
                {"outcome": "completed", "harness_report": {"proposed_goldens": ["x.png"]}}
            )
        ),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="gate")),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    result = service.run(workflow, tmp_path)
    assert result.last_step_id == "STOP"
