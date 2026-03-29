"""Tests for maintained OA07 execution, validation, and kernel packages."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tnh_scholar.agent_orchestration.execution import (
    CliExecutableInvocation,
    ExecutionOutputCapturePolicy,
    ExecutionRequest,
    ExecutionTermination,
    ExplicitEnvironmentPolicy,
    SubprocessExecutionService,
    TimeoutPolicy,
)
from tnh_scholar.agent_orchestration.kernel import (
    EvaluateStep,
    GateOutcome,
    GateStep,
    KernelRunService,
    PlannerDecision,
    PlannerStatus,
    RollbackStep,
    RouteRule,
    RunAgentStep,
    RunValidationStep,
    StopStep,
    WorkflowDefinition,
    WorkflowValidationError,
    WorkflowValidator,
)
from tnh_scholar.agent_orchestration.kernel.adapters.workflow_loader import YamlWorkflowLoader
from tnh_scholar.agent_orchestration.run_artifacts import (
    ArtifactRole,
    FilesystemRunArtifactStore,
)
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


@dataclass
class RecordingWorkspace:
    """Workspace double that records rollback calls."""

    repo_root: Path
    captured_run_ids: list[str] | None = None
    rollback_calls: int = 0

    def __post_init__(self) -> None:
        if self.captured_run_ids is None:
            self.captured_run_ids = []

    def capture_pre_run(self, run_id: str) -> None:
        if self.captured_run_ids is None:
            self.captured_run_ids = []
        self.captured_run_ids.append(run_id)

    def rollback_pre_run(self) -> None:
        self.rollback_calls += 1


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


def test_execution_service_honors_output_capture_policy(tmp_path: Path) -> None:
    script = tmp_path / "echo.sh"
    script.write_text("#!/bin/sh\necho out\necho err 1>&2\n", encoding="utf-8")
    script.chmod(0o755)
    service = SubprocessExecutionService()
    result = service.run(
        ExecutionRequest(
            invocation=CliExecutableInvocation(executable=script),
            working_directory=tmp_path,
            environment_policy=ExplicitEnvironmentPolicy(values={}),
            output_capture_policy=ExecutionOutputCapturePolicy(capture_stderr=False),
        )
    )
    assert result.termination == ExecutionTermination.completed
    assert result.stdout_text.strip() == "out"
    assert result.stderr_text == ""


def test_execution_timeout_policy_idle_seconds_is_documented_only() -> None:
    policy = TimeoutPolicy(idle_seconds=5)
    assert "Reserved for future enforcement" in str(
        type(policy).model_fields["idle_seconds"].description
    )


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


def test_validation_service_preserves_killed_idle_outcome(tmp_path: Path) -> None:
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
    merged = service._merge_termination(
        ValidationTermination.completed,
        ValidationTermination.killed_idle,
    )
    assert merged == ValidationTermination.killed_idle


def test_validation_service_marks_invalid_harness_report_as_error(tmp_path: Path) -> None:
    script = tmp_path / "generated_harness.py"
    script.write_text(
        "from pathlib import Path\nPath('harness_report.json').write_text('{', encoding='utf-8')\n",
        encoding="utf-8",
    )
    service = ValidationService(
        resolver=StaticValidatorResolver(entries=[]),
        execution_service=SubprocessExecutionService(),
        report_loader=__import__(
            "tnh_scholar.agent_orchestration.validation.service",
            fromlist=["HarnessReportLoader"],
        ).HarnessReportLoader(),
    )
    result = service.run(
        ValidationStepRequest(
            validators=[
                HarnessValidationSpec(name=GeneratedHarnessValidatorId.generated_harness)
            ],
            run_directory=tmp_path,
        )
    )
    assert result.termination == ValidationTermination.error


def test_run_artifact_store_creates_parent_directories(tmp_path: Path) -> None:
    paths = FilesystemRunArtifactStore().create_run("run-1", tmp_path)
    entry = FilesystemRunArtifactStore().write_text_artifact(
        paths=paths,
        step_id="logs",
        role=ArtifactRole.runner_metadata,
        filename="nested/note.txt",
        content="ok",
        media_type="text/plain",
        required=True,
    )
    assert (paths.run_directory / entry.path).read_text(encoding="utf-8") == "ok"


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


def _read_events(run_directory: Path) -> list[dict[str, str | None]]:
    path = run_directory / "events.ndjson"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


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


def test_kernel_runtime_blocks_indirect_stop_until_gate_after_proposed_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-indirect",
        version=1,
        description="runtime gate indirect",
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
                allowed_next_steps=["finish", "gate"],
                routes=[
                    RouteRule(outcome=PlannerStatus.success.value, target="finish"),
                    RouteRule(outcome=PlannerStatus.partial.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.blocked.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.unsafe.value, target="STOP"),
                    RouteRule(outcome=PlannerStatus.needs_human.value, target="gate"),
                ],
            ),
            RunAgentStep(
                id="finish",
                agent="codex",
                prompt="finalize",
                routes=[RouteRule(outcome=RunnerTermination.completed.value, target="STOP")],
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
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="finish")),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    with raises(WorkflowValidationError, match="must pass through GATE"):
        service.run(workflow, tmp_path)


def test_kernel_runtime_completes_when_gate_approved_after_proposed_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-approved",
        version=1,
        description="runtime gate approved",
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
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-approved"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=NullWorkspaceService(repo_root=tmp_path),
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(
            ValidationResult(
                termination=ValidationTermination.completed,
                harness_report={"proposed_goldens": ["x.png"]},
            )
        ),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="gate")),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    result = service.run(workflow, tmp_path)
    assert result.status.value == "completed"
    assert result.last_step_id == "STOP"
    events = _read_events(result.run_directory)
    assert [event["step_id"] for event in events] == ["agent", "validate", "evaluate", "gate"]
    assert [event["next_step_id"] for event in events] == ["validate", "evaluate", "gate", "STOP"]
    assert all(event["run_id"] == "run-approved" for event in events)
    assert all(event["event_type"] == "step_completed" for event in events)
    assert all(event["timestamp"] for event in events)


def test_kernel_runtime_completes_when_gate_rejected_after_proposed_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-rejected",
        version=1,
        description="runtime gate rejected",
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
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-rejected"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=NullWorkspaceService(repo_root=tmp_path),
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(
            ValidationResult(
                termination=ValidationTermination.completed,
                harness_report={"proposed_goldens": ["x.png"]},
            )
        ),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="gate")),
        gate_approver=FixedGateApprover(GateOutcome.gate_rejected),
        workflow_validator=WorkflowValidator(),
    )
    result = service.run(workflow, tmp_path)
    assert result.status.value == "completed"
    assert result.last_step_id == "STOP"


def test_kernel_runtime_completes_when_gate_times_out_after_proposed_goldens(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-timed-out",
        version=1,
        description="runtime gate timed out",
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
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-timed-out"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=NullWorkspaceService(repo_root=tmp_path),
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(
            ValidationResult(
                termination=ValidationTermination.completed,
                harness_report={"proposed_goldens": ["x.png"]},
            )
        ),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="gate")),
        gate_approver=FixedGateApprover(GateOutcome.gate_timed_out),
        workflow_validator=WorkflowValidator(),
    )
    result = service.run(workflow, tmp_path)
    assert result.status.value == "completed"
    assert result.last_step_id == "STOP"


def test_kernel_runtime_rejects_unknown_agent_identifier(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-agent",
        version=1,
        description="unknown agent",
        entry_step="agent",
        steps=[
            RunAgentStep(
                id="agent",
                agent="codexx",
                prompt="task",
                routes=[RouteRule(outcome=RunnerTermination.completed.value, target="STOP")],
            ),
            StopStep(id="STOP"),
        ],
    )
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-agent"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=NullWorkspaceService(repo_root=tmp_path),
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(ValidationResult(termination=ValidationTermination.completed)),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success)),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    with raises(WorkflowValidationError, match="Unsupported agent identifier"):
        service.run(workflow, tmp_path)


def test_kernel_runtime_rejects_invalid_planner_next_step(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-invalid-next",
        version=1,
        description="invalid next step",
        entry_step="evaluate",
        steps=[
            EvaluateStep(
                id="evaluate",
                prompt="planner",
                allowed_next_steps=["gate"],
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
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-invalid-next"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=NullWorkspaceService(repo_root=tmp_path),
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(ValidationResult(termination=ValidationTermination.completed)),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success, next_step="STOP")),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    with raises(WorkflowValidationError, match="Planner next_step not allowed"):
        service.run(workflow, tmp_path)


def test_kernel_runtime_executes_rollback_step(tmp_path: Path) -> None:
    workflow = WorkflowDefinition(
        workflow_id="w-rollback",
        version=1,
        description="rollback runtime",
        entry_step="rollback",
        steps=[
            RollbackStep(
                id="rollback",
                target="restore",
                routes=[RouteRule(outcome="completed", target="STOP")],
            ),
            StopStep(id="STOP"),
        ],
    )
    workspace = RecordingWorkspace(repo_root=tmp_path)
    service = KernelRunService(
        clock=FixedClock(datetime(2026, 3, 7, tzinfo=timezone.utc)),
        run_id_generator=FixedRunId("run-rollback"),
        artifact_store=FilesystemRunArtifactStore(),
        workspace=workspace,
        runner_service=SuccessRunner(),
        validation_service=FixedValidationService(ValidationResult(termination=ValidationTermination.completed)),
        planner_evaluator=FixedEvaluator(PlannerDecision(status=PlannerStatus.success)),
        gate_approver=FixedGateApprover(GateOutcome.gate_approved),
        workflow_validator=WorkflowValidator(),
    )
    result = service.run(workflow, tmp_path)
    assert workspace.rollback_calls == 1
    assert result.status.value == "completed"
    assert result.last_step_id == "STOP"


def test_workflow_loader_rejects_unknown_validation_spec_kind(tmp_path: Path) -> None:
    path = tmp_path / "workflow.yaml"
    path.write_text(
        "\n".join(
            [
                "workflow_id: w1",
                "version: 1",
                "description: bad kind",
                "entry_step: validate",
                "steps:",
                "  - id: validate",
                "    opcode: RUN_VALIDATION",
                "    run:",
                "      - kind: mystery",
                "        name: nope",
                "    routes:",
                "      completed: STOP",
                "  - id: STOP",
                "    opcode: STOP",
            ]
        ),
        encoding="utf-8",
    )
    with raises(WorkflowValidationError, match="Unsupported validation spec kind"):
        YamlWorkflowLoader().load(path)
