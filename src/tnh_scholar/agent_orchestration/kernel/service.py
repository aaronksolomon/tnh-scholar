"""Top-level maintained kernel service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.kernel.catalog import WorkflowCatalog
from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import (
    EvaluateStep,
    GateOutcome,
    GateStep,
    KernelRunResult,
    MechanicalOutcome,
    PlannerStatus,
    RollbackStep,
    RunAgentStep,
    RunValidationStep,
    StopStep,
    StepDefinition,
    WorkflowDefinition,
)
from tnh_scholar.agent_orchestration.kernel.protocols import (
    ClockProtocol,
    GateApproverProtocol,
    PlannerEvaluatorProtocol,
    RunArtifactStoreProtocol,
    RunIdGeneratorProtocol,
    RunnerServiceProtocol,
    WorkspaceServiceProtocol,
)
from tnh_scholar.agent_orchestration.kernel.state import KernelState
from tnh_scholar.agent_orchestration.kernel.validator import WorkflowValidator
from tnh_scholar.agent_orchestration.run_artifacts.models import RunEventRecord, RunMetadata
from tnh_scholar.agent_orchestration.runners.models import (
    AgentFamily,
    RunnerTaskRequest,
    RunnerTermination,
)
from tnh_scholar.agent_orchestration.validation.models import (
    ValidationStepRequest,
    ValidationTermination,
)
from tnh_scholar.agent_orchestration.validation.protocols import ValidationServiceProtocol


@dataclass(frozen=True)
class KernelRunService:
    """Execute a workflow deterministically."""

    clock: ClockProtocol
    run_id_generator: RunIdGeneratorProtocol
    artifact_store: RunArtifactStoreProtocol
    workspace: WorkspaceServiceProtocol
    runner_service: RunnerServiceProtocol
    validation_service: ValidationServiceProtocol
    planner_evaluator: PlannerEvaluatorProtocol
    gate_approver: GateApproverProtocol
    workflow_validator: WorkflowValidator

    def run(self, workflow: WorkflowDefinition, run_root: Path) -> KernelRunResult:
        """Execute a workflow and return summary."""
        self.workflow_validator.validate(workflow)
        started_at = self.clock.now()
        run_id = self.run_id_generator.next_id(started_at)
        paths = self.artifact_store.create_run(run_id, run_root)
        self.artifact_store.write_metadata(
            RunMetadata(run_id=run_id, workflow_id=workflow.workflow_id, started_at=started_at),
            paths,
        )
        self.workspace.capture_pre_run(run_id)
        state = KernelState(current_step_id=workflow.entry_step)
        catalog = WorkflowCatalog(workflow=workflow)
        while True:
            step = catalog.find_step(state.current_step_id)
            if isinstance(step, StopStep):
                ended_at = self.clock.now()
                self.artifact_store.write_text(paths.final_state_path, f"STOP:{step.id}")
                return KernelRunResult(
                    run_id=run_id,
                    workflow_id=workflow.workflow_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    status=MechanicalOutcome.completed,
                    last_step_id=step.id,
                    run_directory=paths.run_directory,
                )
            state = self._execute_step(step, state, paths.run_directory, catalog)
            if state.trace:
                last_step, next_step = state.trace[-1].split("->", maxsplit=1)
                self.artifact_store.append_event(
                    RunEventRecord(step_id=last_step, next_step_id=next_step),
                    paths,
                )

    def _execute_step(
        self,
        step: StepDefinition,
        state: KernelState,
        run_directory: Path,
        catalog: WorkflowCatalog,
    ) -> KernelState:
        if isinstance(step, RunAgentStep):
            result = self.runner_service.run(
                RunnerTaskRequest(
                    agent_family=self._map_agent_family(step.agent),
                    rendered_task_text=step.prompt,
                    working_directory=run_directory,
                    prompt_reference=step.prompt,
                )
            )
            target = catalog.route_target(
                step,
                self._to_mechanical_outcome(result.termination).value,
                context="No route for outcome",
            )
            return state.advance(step.id, target)
        if isinstance(step, RunValidationStep):
            result = self.validation_service.run(
                ValidationStepRequest(validators=step.run, run_directory=run_directory)
            )
            pending_gate = state.pending_golden_gate
            if result.harness_report is not None and result.harness_report.proposed_goldens:
                pending_gate = True
            target = catalog.route_target(step, result.termination.value, context="No route for outcome")
            return state.advance(step.id, target, pending_gate=pending_gate)
        if isinstance(step, EvaluateStep):
            decision = self.planner_evaluator.evaluate(step, run_directory)
            self._validate_planner_next_step(step, decision.next_step)
            target = catalog.route_target(step, decision.status.value, context="No route for outcome")
            self._enforce_runtime_golden_gate(state, decision.status, target)
            return state.advance(step.id, target)
        if isinstance(step, GateStep):
            outcome = self.gate_approver.decide(step, run_directory)
            target = catalog.route_target(step, outcome.value, context="No route for outcome")
            pending_gate = self._clear_pending_gate_if_approved(state.pending_golden_gate, outcome)
            return state.advance(step.id, target, pending_gate=pending_gate)
        if isinstance(step, RollbackStep):
            self.workspace.rollback_pre_run()
            target = catalog.route_target(
                step,
                MechanicalOutcome.completed.value,
                context="No route for outcome",
            )
            return state.advance(step.id, target)
        raise WorkflowValidationError(f"Unsupported step type: {step.id}")

    def _map_agent_family(self, agent: str) -> AgentFamily:
        return AgentFamily.codex_cli if agent == "codex" else AgentFamily.claude_cli

    def _to_mechanical_outcome(self, termination: RunnerTermination) -> MechanicalOutcome:
        return MechanicalOutcome(termination.value)

    def _validate_planner_next_step(self, step: EvaluateStep, next_step: str | None) -> None:
        if next_step is None:
            return
        if next_step not in step.allowed_next_steps:
            raise WorkflowValidationError(f"Planner next_step not allowed in {step.id}: {next_step}")

    def _enforce_runtime_golden_gate(self, state: KernelState, status: PlannerStatus, target: str) -> None:
        if not state.pending_golden_gate or status != PlannerStatus.success:
            return
        if target == "STOP":
            raise WorkflowValidationError(
                "Goldens proposed: success path must pass through GATE before STOP."
            )

    def _clear_pending_gate_if_approved(self, pending_gate: bool, outcome: GateOutcome) -> bool:
        if pending_gate and outcome == GateOutcome.gate_approved:
            return False
        return pending_gate
