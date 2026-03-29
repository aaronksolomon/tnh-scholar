"""Top-level maintained kernel service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tnh_scholar.agent_orchestration.kernel.catalog import WorkflowCatalog
from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import (
    EvaluateStep,
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
from tnh_scholar.agent_orchestration.kernel.protocols import (
    ClockProtocol,
    GateApproverProtocol,
    PlannerEvaluatorProtocol,
    RunArtifactStoreProtocol,
    RunIdGeneratorProtocol,
    RunnerServiceProtocol,
    WorkspaceServiceProtocol,
)
from tnh_scholar.agent_orchestration.kernel.provenance import KernelProvenanceRecorder
from tnh_scholar.agent_orchestration.kernel.state import KernelState
from tnh_scholar.agent_orchestration.kernel.validator import WorkflowValidator
from tnh_scholar.agent_orchestration.run_artifacts.models import (
    ArtifactRole,
    GateOutcomeArtifact,
    GateRequestArtifact,
    RunArtifactPaths,
    RunMetadata,
    RunnerMetadataArtifact,
    StepArtifactEntry,
)
from tnh_scholar.agent_orchestration.runners.models import (
    AgentFamily,
    RunnerTaskRequest,
    RunnerTermination,
)
from tnh_scholar.agent_orchestration.validation.models import (
    HarnessReport,
    ValidationStepRequest,
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
        provenance = KernelProvenanceRecorder(
            artifact_store=self.artifact_store,
            workspace=self.workspace,
            clock=self.clock,
        )
        self.artifact_store.write_metadata(
            RunMetadata(
                run_id=run_id,
                workflow_id=workflow.workflow_id,
                workflow_version=workflow.version,
                started_at=started_at,
                artifacts_root=paths.artifacts_root,
                entry_step=workflow.entry_step,
            ),
            paths,
        )
        self.workspace.capture_pre_run(run_id)
        state = KernelState(current_step_id=workflow.entry_step)
        catalog = WorkflowCatalog(workflow=workflow)
        while True:
            step = catalog.find_step(state.current_step_id)
            if isinstance(step, StopStep):
                ended_at = self.clock.now()
                self._write_terminal_metadata(
                    workflow=workflow,
                    run_id=run_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    last_step_id=step.id,
                    termination=MechanicalOutcome.completed,
                    paths=paths,
                )
                self.artifact_store.write_final_state(f"{Opcode.stop.value}:{step.id}", paths)
                return KernelRunResult(
                    run_id=run_id,
                    workflow_id=workflow.workflow_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    status=MechanicalOutcome.completed,
                    last_step_id=step.id,
                    run_directory=paths.run_directory,
                )
            step_started_at = self.clock.now()
            provenance.record_step_started(run_id=run_id, step_id=step.id, paths=paths)
            try:
                state = self._execute_step(
                    step=step,
                    state=state,
                    run_id=run_id,
                    paths=paths,
                    run_directory=paths.run_directory,
                    catalog=catalog,
                    step_started_at=step_started_at,
                    provenance=provenance,
                )
            except Exception as error:
                ended_at = self.clock.now()
                provenance.record_failed_step(
                    run_id=run_id,
                    step_id=step.id,
                    opcode=step.opcode,
                    started_at=step_started_at,
                    ended_at=ended_at,
                    paths=paths,
                    run_directory=paths.run_directory,
                    notes=(str(error),),
                )
                self._write_terminal_metadata(
                    workflow=workflow,
                    run_id=run_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    last_step_id=step.id,
                    termination=MechanicalOutcome.error,
                    paths=paths,
                )
                self.artifact_store.write_final_state(
                    f"{MechanicalOutcome.error.value}:{step.id}",
                    paths,
                )
                raise

    def _execute_step(
        self,
        step: StepDefinition,
        state: KernelState,
        run_id: str,
        paths: RunArtifactPaths,
        run_directory: Path,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        provenance: KernelProvenanceRecorder,
    ) -> KernelState:
        if isinstance(step, RunAgentStep):
            return self._handle_run_agent_step(
                step=step,
                state=state,
                run_id=run_id,
                paths=paths,
                run_directory=run_directory,
                catalog=catalog,
                step_started_at=step_started_at,
                provenance=provenance,
            )
        if isinstance(step, RunValidationStep):
            return self._handle_run_validation_step(
                step=step,
                state=state,
                run_id=run_id,
                paths=paths,
                run_directory=run_directory,
                catalog=catalog,
                step_started_at=step_started_at,
                provenance=provenance,
            )
        if isinstance(step, EvaluateStep):
            return self._handle_evaluate_step(
                step=step,
                state=state,
                run_id=run_id,
                paths=paths,
                run_directory=run_directory,
                catalog=catalog,
                step_started_at=step_started_at,
                provenance=provenance,
            )
        if isinstance(step, GateStep):
            return self._handle_gate_step(
                step=step,
                state=state,
                run_id=run_id,
                paths=paths,
                run_directory=run_directory,
                catalog=catalog,
                step_started_at=step_started_at,
                provenance=provenance,
            )
        if isinstance(step, RollbackStep):
            return self._handle_rollback_step(
                step=step,
                state=state,
                run_id=run_id,
                paths=paths,
                run_directory=run_directory,
                catalog=catalog,
                step_started_at=step_started_at,
                provenance=provenance,
            )
        raise WorkflowValidationError(f"Unsupported step type: {step.id}")

    def _handle_run_agent_step(
        self,
        step: RunAgentStep,
        state: KernelState,
        run_id: str,
        paths: RunArtifactPaths,
        run_directory: Path,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        provenance: KernelProvenanceRecorder,
    ) -> KernelState:
        request = RunnerTaskRequest(
            agent_family=self._map_agent_family(step.agent),
            rendered_task_text=step.prompt,
            working_directory=run_directory,
            prompt_reference=step.prompt,
        )
        result = self.runner_service.run(request)
        target = catalog.route_target(
            step,
            self._to_mechanical_outcome(result.termination).value,
            context="No route for outcome",
        )
        runner_metadata = self.artifact_store.write_json_artifact(
            paths=paths,
            step_id=step.id,
            role=ArtifactRole.runner_metadata,
            filename="runner_metadata.json",
            payload=RunnerMetadataArtifact(
                agent_family=request.agent_family,
                prompt_reference=request.prompt_reference,
                termination=result.termination,
            ),
            required=True,
        )
        provenance.record_step_manifest(
            run_id=run_id,
            step_id=step.id,
            opcode=step.opcode,
            termination=self._to_mechanical_outcome(result.termination),
            started_at=step_started_at,
            ended_at=self.clock.now(),
            paths=paths,
            run_directory=run_directory,
            extra_artifacts=(runner_metadata,),
            next_step_id=target,
        )
        return state.advance(step.id, target)

    def _handle_run_validation_step(
        self,
        step: RunValidationStep,
        state: KernelState,
        run_id: str,
        paths: RunArtifactPaths,
        run_directory: Path,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        provenance: KernelProvenanceRecorder,
    ) -> KernelState:
        result = self.validation_service.run(
            ValidationStepRequest(validators=step.run, run_directory=run_directory)
        )
        next_state = state
        report = self._normalize_harness_report(result.harness_report)
        if report is not None and report.proposed_goldens:
            next_state = state.with_pending_gate()
        target = catalog.route_target(step, result.termination.value, context="No route for outcome")
        extra_artifacts = self._validation_artifacts(
            step_id=step.id,
            paths=paths,
            report=report,
        )
        provenance.record_step_manifest(
            run_id=run_id,
            step_id=step.id,
            opcode=step.opcode,
            termination=MechanicalOutcome(result.termination.value),
            started_at=step_started_at,
            ended_at=self.clock.now(),
            paths=paths,
            run_directory=run_directory,
            extra_artifacts=extra_artifacts,
            next_step_id=target,
        )
        return next_state.advance(step.id, target, pending_gate=next_state.pending_golden_gate)

    def _handle_evaluate_step(
        self,
        step: EvaluateStep,
        state: KernelState,
        run_id: str,
        paths: RunArtifactPaths,
        run_directory: Path,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        provenance: KernelProvenanceRecorder,
    ) -> KernelState:
        decision = self.planner_evaluator.evaluate(step, run_directory)
        self._validate_planner_next_step(step, decision.next_step)
        target = catalog.route_target(step, decision.status.value, context="No route for outcome")
        self._enforce_runtime_golden_gate(state, decision.status, target, catalog)
        planner_artifact = self.artifact_store.write_json_artifact(
            paths=paths,
            step_id=step.id,
            role=ArtifactRole.planner_decision,
            filename="planner_decision.json",
            payload=decision,
            required=True,
        )
        provenance.record_step_manifest(
            run_id=run_id,
            step_id=step.id,
            opcode=step.opcode,
            termination=decision.status,
            started_at=step_started_at,
            ended_at=self.clock.now(),
            paths=paths,
            run_directory=run_directory,
            extra_artifacts=(planner_artifact,),
            next_step_id=target,
        )
        return state.advance(step.id, target)

    def _handle_gate_step(
        self,
        step: GateStep,
        state: KernelState,
        run_id: str,
        paths: RunArtifactPaths,
        run_directory: Path,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        provenance: KernelProvenanceRecorder,
    ) -> KernelState:
        provenance.record_gate_requested(run_id=run_id, step_id=step.id, paths=paths)
        gate_request = self.artifact_store.write_json_artifact(
            paths=paths,
            step_id=step.id,
            role=ArtifactRole.gate_request,
            filename="gate_request.json",
            payload=GateRequestArtifact(
                gate=step.gate,
                timeout_seconds=step.timeout_seconds,
            ),
            required=True,
        )
        outcome = self.gate_approver.decide(step, run_directory)
        provenance.record_gate_resolved(run_id=run_id, step_id=step.id, paths=paths)
        gate_outcome = self.artifact_store.write_json_artifact(
            paths=paths,
            step_id=step.id,
            role=ArtifactRole.gate_outcome,
            filename="gate_outcome.json",
            payload=GateOutcomeArtifact(outcome=outcome),
            required=True,
        )
        target = catalog.route_target(step, outcome.value, context="No route for outcome")
        provenance.record_step_manifest(
            run_id=run_id,
            step_id=step.id,
            opcode=step.opcode,
            termination=outcome,
            started_at=step_started_at,
            ended_at=self.clock.now(),
            paths=paths,
            run_directory=run_directory,
            extra_artifacts=(gate_request, gate_outcome),
            next_step_id=target,
        )
        pending_gate = state.pending_gate_after_outcome(outcome)
        return state.advance(step.id, target, pending_gate=pending_gate)

    def _handle_rollback_step(
        self,
        step: RollbackStep,
        state: KernelState,
        run_id: str,
        paths: RunArtifactPaths,
        run_directory: Path,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        provenance: KernelProvenanceRecorder,
    ) -> KernelState:
        self.workspace.rollback_pre_run()
        provenance.record_rollback_completed(run_id=run_id, step_id=step.id, paths=paths)
        target = catalog.route_target(
            step,
            MechanicalOutcome.completed.value,
            context="No route for outcome",
        )
        provenance.record_step_manifest(
            run_id=run_id,
            step_id=step.id,
            opcode=step.opcode,
            termination=MechanicalOutcome.completed,
            started_at=step_started_at,
            ended_at=self.clock.now(),
            paths=paths,
            run_directory=run_directory,
            next_step_id=target,
        )
        return state.advance(step.id, target)

    def _map_agent_family(self, agent: str) -> AgentFamily:
        match agent:
            case "codex":
                return AgentFamily.codex_cli
            case "claude":
                return AgentFamily.claude_cli
        raise WorkflowValidationError(f"Unsupported agent identifier: {agent}")

    def _to_mechanical_outcome(self, termination: RunnerTermination) -> MechanicalOutcome:
        return MechanicalOutcome(termination.value)

    def _validate_planner_next_step(self, step: EvaluateStep, next_step: str | None) -> None:
        if next_step is None:
            return
        if next_step not in step.allowed_next_steps:
            raise WorkflowValidationError(f"Planner next_step not allowed in {step.id}: {next_step}")

    def _enforce_runtime_golden_gate(
        self,
        state: KernelState,
        status: PlannerStatus,
        target: str,
        catalog: WorkflowCatalog,
    ) -> None:
        if not state.pending_golden_gate or status != PlannerStatus.success:
            return
        if target == Opcode.stop.value or not catalog.path_contains_gate(target):
            raise WorkflowValidationError(
                "Goldens proposed: success path must pass through GATE before STOP."
            )

    def _normalize_harness_report(
        self,
        report: HarnessReport | dict[str, object] | None,
    ) -> HarnessReport | None:
        if report is None:
            return None
        return report if isinstance(report, HarnessReport) else HarnessReport.model_validate(report)

    def _validation_artifacts(
        self,
        *,
        step_id: str,
        paths: RunArtifactPaths,
        report: HarnessReport | None,
    ) -> tuple[StepArtifactEntry, ...]:
        if report is None:
            return ()
        artifact = self.artifact_store.write_json_artifact(
            paths=paths,
            step_id=step_id,
            role=ArtifactRole.validation_report,
            filename="validation_report.json",
            payload=report,
            required=True,
        )
        return (artifact,)

    def _write_terminal_metadata(
        self,
        *,
        workflow: WorkflowDefinition,
        run_id: str,
        started_at: datetime,
        ended_at: datetime,
        last_step_id: str,
        termination: MechanicalOutcome,
        paths: RunArtifactPaths,
    ) -> None:
        self.artifact_store.write_metadata(
            RunMetadata(
                run_id=run_id,
                workflow_id=workflow.workflow_id,
                workflow_version=workflow.version,
                started_at=started_at,
                artifacts_root=paths.artifacts_root,
                entry_step=workflow.entry_step,
                ended_at=ended_at,
                last_step_id=last_step_id,
                termination=termination,
            ),
            paths,
        )
