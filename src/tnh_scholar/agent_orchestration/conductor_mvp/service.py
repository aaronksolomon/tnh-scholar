"""Deterministic conductor kernel service for MVP workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.conductor_mvp.models import (
    ArtifactPaths,
    EvaluateStep,
    GateOutcome,
    GateStep,
    KernelRunResult,
    MechanicalOutcome,
    Opcode,
    PlannerStatus,
    RollbackStep,
    RunAgentStep,
    RunValidationStep,
    StepDefinition,
    StopStep,
    WorkflowDefinition,
)
from tnh_scholar.agent_orchestration.conductor_mvp.protocols import (
    AgentRunnerProtocol,
    ArtifactStoreProtocol,
    ClockProtocol,
    GateApproverProtocol,
    PlannerEvaluatorProtocol,
    RunIdGeneratorProtocol,
    ValidationRunnerProtocol,
    WorkspaceProtocol,
)


class WorkflowValidationError(Exception):
    """Raised when a workflow fails static or runtime kernel validation."""


@dataclass(frozen=True)
class WorkflowCatalog:
    """Indexed workflow helper for step lookups."""

    workflow: WorkflowDefinition

    def find_step(self, step_id: str) -> StepDefinition:
        """Find a step by id or raise."""
        for step in self.workflow.steps:
            if step.id == step_id:
                return step
        raise WorkflowValidationError(f"Unknown step target: {step_id}")

    def has_step_type(self, opcode: Opcode) -> bool:
        """Return True if workflow contains at least one opcode."""
        return any(step.opcode == opcode for step in self.workflow.steps)

    def has_step_id(self, step_id: str) -> bool:
        """Return True if workflow contains provided step id."""
        return any(step.id == step_id for step in self.workflow.steps)

    def transition_targets(self, step: StepDefinition) -> list[str]:
        """Return all declared transition targets for a step."""
        return [route.target for route in step.routes]


@dataclass(frozen=True)
class WorkflowValidator:
    """Static validation for MVP workflow definitions."""

    def validate(self, workflow: WorkflowDefinition) -> None:
        """Validate schema-level and graph-level invariants."""
        catalog = WorkflowCatalog(workflow=workflow)
        self._validate_entry_step(workflow)
        self._validate_unique_step_ids(workflow)
        self._validate_routes(workflow, catalog)
        self._validate_evaluate_constraints(workflow, catalog)
        self._validate_reachability(workflow, catalog)
        self._validate_weak_golden_gate_requirement(workflow, catalog)

    def _validate_entry_step(self, workflow: WorkflowDefinition) -> None:
        self._step_exists(workflow, workflow.entry_step)

    def _validate_unique_step_ids(self, workflow: WorkflowDefinition) -> None:
        seen: set[str] = set()
        for step in workflow.steps:
            if step.id in seen:
                raise WorkflowValidationError(f"Duplicate step id: {step.id}")
            seen.add(step.id)

    def _validate_routes(self, workflow: WorkflowDefinition, catalog: WorkflowCatalog) -> None:
        for step in workflow.steps:
            if isinstance(step, StopStep):
                continue
            if not step.routes:
                raise WorkflowValidationError(f"Step requires routes: {step.id}")
            for target in catalog.transition_targets(step):
                self._validate_target(workflow, target)

    def _validate_evaluate_constraints(self, workflow: WorkflowDefinition, catalog: WorkflowCatalog) -> None:
        for step in workflow.steps:
            if not isinstance(step, EvaluateStep):
                continue
            self._validate_evaluate_next_steps(workflow, step)
            self._validate_evaluate_routes(step, catalog)

    def _validate_evaluate_next_steps(self, workflow: WorkflowDefinition, step: EvaluateStep) -> None:
        if not step.allowed_next_steps:
            raise WorkflowValidationError(f"EVALUATE missing allowed_next_steps: {step.id}")
        for target in step.allowed_next_steps:
            self._validate_target(workflow, target)

    def _validate_evaluate_routes(self, step: EvaluateStep, catalog: WorkflowCatalog) -> None:
        route_values = [route.outcome for route in step.routes]
        required = [status.value for status in PlannerStatus]
        for value in required:
            if value not in route_values:
                raise WorkflowValidationError(f"EVALUATE route missing '{value}' in {step.id}")
        for route in step.routes:
            if route.target == "STOP":
                continue
            if route.target not in step.allowed_next_steps:
                raise WorkflowValidationError(f"EVALUATE target not allowed in {step.id}: {route.target}")
        self._validate_special_status_route(step, PlannerStatus.unsafe, Opcode.rollback)
        self._validate_special_status_route(step, PlannerStatus.needs_human, Opcode.gate)

    def _validate_special_status_route(
        self,
        step: EvaluateStep,
        status: PlannerStatus,
        expected_opcode: Opcode,
    ) -> None:
        target = self._route_target(step, status.value)
        if target == "STOP":
            return
        if target in step.allowed_next_steps:
            return
        raise WorkflowValidationError(f"Invalid {status.value} route in {step.id}: {target}")

    def _validate_reachability(self, workflow: WorkflowDefinition, catalog: WorkflowCatalog) -> None:
        reachable = self._reachable_step_ids(workflow.entry_step, catalog)
        for step in workflow.steps:
            if step.id not in reachable:
                raise WorkflowValidationError(f"Unreachable step: {step.id}")

    def _reachable_step_ids(self, entry_step: str, catalog: WorkflowCatalog) -> set[str]:
        queue = [entry_step]
        visited: set[str] = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            step = catalog.find_step(current)
            for target in catalog.transition_targets(step):
                if target == "STOP" and catalog.has_step_id("STOP"):
                    queue.append("STOP")
                elif target != "STOP":
                    queue.append(target)
        return visited

    def _validate_weak_golden_gate_requirement(
        self,
        workflow: WorkflowDefinition,
        catalog: WorkflowCatalog,
    ) -> None:
        if not self._may_propose_goldens(workflow):
            return
        if not catalog.has_step_type(Opcode.gate):
            raise WorkflowValidationError("Generative harness flow requires a reachable GATE step.")
        if not self._has_gate_reachable_from_evaluate(workflow, catalog):
            raise WorkflowValidationError("No reachable GATE from evaluation path for golden proposals.")

    def _may_propose_goldens(self, workflow: WorkflowDefinition) -> bool:
        for step in workflow.steps:
            if not isinstance(step, RunValidationStep):
                continue
            for validator in step.run:
                if getattr(validator, "may_propose_goldens", False):
                    return True
        return False

    def _has_gate_reachable_from_evaluate(
        self,
        workflow: WorkflowDefinition,
        catalog: WorkflowCatalog,
    ) -> bool:
        for step in workflow.steps:
            if not isinstance(step, EvaluateStep):
                continue
            if self._step_path_contains_gate(step.id, catalog):
                return True
        return False

    def _step_path_contains_gate(self, start_step_id: str, catalog: WorkflowCatalog) -> bool:
        queue = [start_step_id]
        visited: set[str] = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            step = catalog.find_step(current)
            if isinstance(step, GateStep):
                return True
            for target in catalog.transition_targets(step):
                if target != "STOP":
                    queue.append(target)
        return False

    def _route_target(self, step: StepDefinition, outcome_key: str) -> str:
        for route in step.routes:
            if route.outcome == outcome_key:
                route_target: str = route.target
                return route_target
        raise WorkflowValidationError(f"Route missing '{outcome_key}' in step: {step.id}")

    def _validate_target(self, workflow: WorkflowDefinition, target: str) -> None:
        if target == "STOP":
            return
        self._step_exists(workflow, target)

    def _step_exists(self, workflow: WorkflowDefinition, step_id: str) -> None:
        for step in workflow.steps:
            if step.id == step_id:
                return
        raise WorkflowValidationError(f"Missing step id: {step_id}")


@dataclass(frozen=True)
class ConductorKernelService:
    """Execute a validated workflow deterministically."""

    clock: ClockProtocol
    run_id_generator: RunIdGeneratorProtocol
    artifact_store: ArtifactStoreProtocol
    workspace: WorkspaceProtocol
    agent_runner: AgentRunnerProtocol
    validation_runner: ValidationRunnerProtocol
    planner_evaluator: PlannerEvaluatorProtocol
    gate_approver: GateApproverProtocol
    workflow_validator: WorkflowValidator

    def run(self, workflow: WorkflowDefinition, run_root: Path) -> KernelRunResult:
        """Execute workflow and return run summary."""
        self.workflow_validator.validate(workflow)
        started_at = self.clock.now()
        run_id = self.run_id_generator.next_id(started_at)
        run_dir = self.artifact_store.ensure_run_dir(run_id, run_root)
        artifacts = self._artifact_paths(run_dir)
        self.workspace.capture_pre_run(run_id)
        state = KernelState(current_step_id=workflow.entry_step)
        catalog = WorkflowCatalog(workflow=workflow)
        while True:
            step = catalog.find_step(state.current_step_id)
            if isinstance(step, StopStep):
                return self._build_result(workflow, run_id, started_at, step.id, artifacts)
            state = self._execute_step(step, state, run_dir)
            self.artifact_store.write_text(artifacts.run_log, state.log_text())

    def _execute_step(self, step: StepDefinition, state: "KernelState", run_dir: Path) -> "KernelState":
        if isinstance(step, RunAgentStep):
            result = self.agent_runner.run(step, run_dir)
            target = self._route_target(step, result.outcome.value)
            return state.advance(step.id, target)
        if isinstance(step, RunValidationStep):
            result = self.validation_runner.run(step, run_dir)
            pending_gate = state.pending_golden_gate
            if result.harness_report is not None and result.harness_report.proposed_goldens:
                pending_gate = True
            target = self._route_target(step, result.outcome.value)
            return state.advance(step.id, target, pending_gate=pending_gate)
        if isinstance(step, EvaluateStep):
            decision = self.planner_evaluator.evaluate(step, run_dir)
            self._validate_planner_next_step(step, decision.next_step)
            target = self._route_target(step, decision.status.value)
            self._enforce_runtime_golden_gate(state, decision.status, target)
            return state.advance(step.id, target)
        if isinstance(step, GateStep):
            outcome = self.gate_approver.decide(step, run_dir)
            target = self._route_target(step, outcome.value)
            pending_gate = self._clear_pending_gate_if_approved(state.pending_golden_gate, outcome)
            return state.advance(step.id, target, pending_gate=pending_gate)
        if isinstance(step, RollbackStep):
            self.workspace.rollback(step)
            target = self._route_target(step, MechanicalOutcome.completed.value)
            return state.advance(step.id, target)
        raise WorkflowValidationError(f"Unsupported step type: {step.id}")

    def _validate_planner_next_step(self, step: EvaluateStep, next_step: str | None) -> None:
        if next_step is None:
            return
        if next_step not in step.allowed_next_steps:
            raise WorkflowValidationError(f"Planner next_step not allowed in {step.id}: {next_step}")

    def _enforce_runtime_golden_gate(self, state: "KernelState", status: PlannerStatus, target: str) -> None:
        if not state.pending_golden_gate:
            return
        if status != PlannerStatus.success:
            return
        if target == "STOP":
            raise WorkflowValidationError(
                "Goldens proposed: success path must pass through GATE before STOP."
            )

    def _clear_pending_gate_if_approved(self, pending_gate: bool, outcome: GateOutcome) -> bool:
        if pending_gate and outcome == GateOutcome.gate_approved:
            return False
        return pending_gate

    def _route_target(self, step: StepDefinition, outcome_key: str) -> str:
        for route in step.routes:
            if route.outcome == outcome_key:
                route_target: str = route.target
                return route_target
        raise WorkflowValidationError(f"No route for outcome '{outcome_key}' in {step.id}")

    def _build_result(
        self,
        workflow: WorkflowDefinition,
        run_id: str,
        started_at,
        last_step_id: str,
        artifacts: ArtifactPaths,
    ) -> KernelRunResult:
        ended_at = self.clock.now()
        self.artifact_store.write_text(artifacts.final_state, f"STOP:{last_step_id}")
        return KernelRunResult(
            run_id=run_id,
            workflow_id=workflow.workflow_id,
            started_at=started_at,
            ended_at=ended_at,
            status=MechanicalOutcome.completed,
            last_step_id=last_step_id,
            artifact_paths=artifacts,
        )

    def _artifact_paths(self, run_dir: Path) -> ArtifactPaths:
        return ArtifactPaths(
            run_dir=run_dir,
            run_log=run_dir / "run.log",
            final_state=run_dir / "final_state.txt",
        )


@dataclass(frozen=True)
class KernelState:
    """Mutable execution state represented immutably."""

    current_step_id: str
    pending_golden_gate: bool = False
    trace: list[str] | None = None

    def advance(self, step_id: str, next_step_id: str, pending_gate: bool | None = None) -> "KernelState":
        """Advance state with trace update."""
        trace = self.trace or []
        new_pending = self.pending_golden_gate if pending_gate is None else pending_gate
        return KernelState(
            current_step_id=next_step_id,
            pending_golden_gate=new_pending,
            trace=[*trace, f"{step_id}->{next_step_id}"],
        )

    def log_text(self) -> str:
        """Render trace log text."""
        return "\n".join(self.trace or [])
