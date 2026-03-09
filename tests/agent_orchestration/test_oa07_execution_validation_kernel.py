"""Tests for maintained OA07 execution, validation, and kernel packages."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tnh_scholar.agent_orchestration.execution import (
    CliExecutableInvocation,
    ExecutionRequest,
    ExecutionTermination,
    ExplicitEnvironmentPolicy,
    SubprocessExecutionService,
)
from tnh_scholar.agent_orchestration.kernel import (
    EvaluateStep,
    GateOutcome,
    GateStep,
    KernelRunService,
    PlannerDecision,
    PlannerStatus,
    RouteRule,
    RunAgentStep,
    RunValidationStep,
    StopStep,
    WorkflowDefinition,
    WorkflowValidationError,
    WorkflowValidator,
)
from tnh_scholar.agent_orchestration.run_artifacts import FilesystemRunArtifactStore
from tnh_scholar.agent_orchestration.runners import (
    RunnerResult,
    RunnerTaskRequest,
    RunnerTermination,
)
from tnh_scholar.agent_orchestration.validation import (
    BuiltinCommandEntry,
    BuiltinValidationSpec,
    BuiltinValidatorId,
    GeneratedHarnessValidatorId,
    HarnessValidationSpec,
    StaticValidatorResolver,
    ValidationResult,
    ValidationService,
    ValidationStepRequest,
    ValidationTermination,
)
from tnh_scholar.agent_orchestration.workspace import NullWorkspaceService


@contextmanager
def raises(expected_exception: type[Exception], match: str) -> None:
    """Minimal exception assertion helper without pytest dependency."""

    try:
        yield
    except expected_exception as error:
        if match not in str(error):
            raise AssertionError(f"Expected '{match}' in '{error}'") from error
        return
    raise AssertionError(f"Expected exception {expected_exception.__name__}")


@dataclass(frozen=True)
class FixedClock:
    """Clock returning a fixed timestamp."""

    now_value: datetime

    def now(self) -> datetime:
        return self.now_value


@dataclass(frozen=True)
class FixedRunId:
    """Deterministic run id generator."""

    run_id: str

    def next_id(self, now: datetime) -> str:
        return self.run_id


@dataclass(frozen=True)
class SuccessRunner:
    """Runner returning success."""

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        return RunnerResult(termination=RunnerTermination.completed)


@dataclass(frozen=True)
class FixedEvaluator:
    """Planner evaluator with fixed decision."""

    decision: PlannerDecision

    def evaluate(self, step: EvaluateStep, run_directory: Path) -> PlannerDecision:
        return self.decision


@dataclass(frozen=True)
class FixedGateApprover:
    """Gate approver with fixed outcome."""

    outcome: GateOutcome

    def decide(self, step: GateStep, run_directory: Path) -> GateOutcome:
        return self.outcome


def test_execution_service_runs_cli_process(tmp_path: Path) -> None:
    script = tmp_path / "echo.sh"
    script.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    script.chmod(0o755)
    service = SubprocessExecutionService()
    result = service.run(
        ExecutionRequest(
            invocation=CliExecutableInvocation(executable=script),
            working_directory=tmp_path,
            environment_policy=ExplicitEnvironmentPolicy(values={}),
        )
    )
    assert result.termination == ExecutionTermination.completed
    assert result.stdout_text.strip() == "ok"


def test_validation_service_executes_builtin_validator(tmp_path: Path) -> None:
    script = tmp_path / "validator.sh"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    script.chmod(0o755)
    service = ValidationService(
        resolver=StaticValidatorResolver(
            entries=[BuiltinCommandEntry(name=BuiltinValidatorId.tests, executable=script)]
        ),
        execution_service=SubprocessExecutionService(),
        report_loader=__import__(
            "tnh_scholar.agent_orchestration.validation.service",
            fromlist=["HarnessReportLoader"],
        ).HarnessReportLoader(),
    )
    result = service.run(
        ValidationStepRequest(
            validators=[BuiltinValidationSpec(name=BuiltinValidatorId.tests)],
            run_directory=tmp_path,
        )
    )
    assert result.termination == ValidationTermination.completed


def _validation_step() -> RunValidationStep:
    return RunValidationStep(
        id="validate",
        run=[
            BuiltinValidationSpec(name=BuiltinValidatorId.tests),
            HarnessValidationSpec(
                name=GeneratedHarnessValidatorId.generated_harness,
                may_propose_goldens=True,
            ),
        ],
        routes=[
            RouteRule(outcome=ValidationTermination.completed.value, target="evaluate"),
            RouteRule(outcome=ValidationTermination.error.value, target="evaluate"),
            RouteRule(outcome=ValidationTermination.killed_timeout.value, target="evaluate"),
            RouteRule(outcome=ValidationTermination.killed_idle.value, target="evaluate"),
            RouteRule(outcome=ValidationTermination.killed_policy.value, target="evaluate"),
        ],
    )


@dataclass(frozen=True)
class FixedValidationService:
    """Validation service with fixed result."""

    result: ValidationResult

    def run(self, request: ValidationStepRequest) -> ValidationResult:
        return self.result


def test_kernel_runtime_blocks_success_stop_until_gate_after_proposed_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w1",
        version=1,
        description="runtime gate",
        entry_step="agent",
        steps=[
            RunAgentStep(
                id="agent",
                agent="codex",
                prompt="task",
                routes=[RouteRule(outcome=RunnerTermination.completed.value, target="validate")],
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
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-1"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=NullWorkspaceService(repo_root=tmp_path),
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(
            ValidationResult(
                termination=ValidationTermination.completed,
                harness_report={"proposed_goldens": ["x.png"]},
            )
        ),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="STOP")),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    with raises(WorkflowValidationError, match="must pass through GATE"):
        service.run(workflow, tmp_path)
