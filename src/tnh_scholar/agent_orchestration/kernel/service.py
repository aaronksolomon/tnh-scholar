"""Top-level maintained kernel service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from tnh_scholar.agent_orchestration.execution_policy import (
    ExecutionPolicyAssembler,
    ExecutionPolicyAssemblerProtocol,
    ExecutionPolicySettings,
    ExecutionPosture,
    PolicySummary,
    PolicyViolation,
    PolicyViolationClass,
)
from tnh_scholar.agent_orchestration.kernel.catalog import WorkflowCatalog
from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import (
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
from tnh_scholar.agent_orchestration.runners.models import RunnerTaskRequest
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily, RunnerTermination
from tnh_scholar.agent_orchestration.validation.models import (
    HarnessReport,
    ValidationStepRequest,
)
from tnh_scholar.agent_orchestration.validation.protocols import ValidationServiceProtocol


@dataclass(frozen=True)
class StepContext:
    """Per-run step execution context."""

    run_id: str
    paths: RunArtifactPaths
    run_directory: Path
    provenance: KernelProvenanceRecorder
    workflow_policy_ref: str | None = None


@dataclass(frozen=True)
class StepPolicyRecord:
    """Per-step persisted policy evidence."""

    summary: PolicySummary
    artifact: StepArtifactEntry
    note: str


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
    execution_policy_settings: ExecutionPolicySettings = field(default_factory=ExecutionPolicySettings)
    execution_policy_assembler: ExecutionPolicyAssemblerProtocol = field(
        default_factory=ExecutionPolicyAssembler
    )

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
        context = StepContext(
            run_id=run_id,
            paths=paths,
            run_directory=paths.run_directory,
            provenance=provenance,
            workflow_policy_ref=workflow.defaults.policy if workflow.defaults is not None else None,
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
                ended_at = self._terminate_run(
                    workflow=workflow,
                    context=context,
                    started_at=started_at,
                    last_step_id=step.id,
                    termination=MechanicalOutcome.completed,
                )
                return KernelRunResult(
                    run_id=run_id,
                    workflow_id=workflow.workflow_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    status=MechanicalOutcome.completed,
                    last_step_id=step.id,
                    run_directory=context.run_directory,
                )
            step_started_at = self.clock.now()
            policy_record = self._persist_step_policy(step=step, context=context)
            context.provenance.record_step_started(
                run_id=context.run_id,
                step_id=step.id,
                paths=context.paths,
            )
            try:
                state = self._execute_step(
                    step=step,
                    state=state,
                    context=context,
                    catalog=catalog,
                    step_started_at=step_started_at,
                    policy_record=policy_record,
                )
            except Exception as error:
                ended_at = self.clock.now()
                context.provenance.record_failed_step(
                    run_id=context.run_id,
                    step_id=step.id,
                    opcode=step.opcode,
                    started_at=step_started_at,
                    ended_at=ended_at,
                    paths=context.paths,
                    run_directory=context.run_directory,
                    extra_artifacts=(policy_record.artifact,),
                    notes=(policy_record.note, str(error)),
                )
                self._terminate_run(
                    workflow=workflow,
                    context=context,
                    started_at=started_at,
                    last_step_id=step.id,
                    termination=MechanicalOutcome.error,
                )
                raise

    def _execute_step(
        self,
        step: StepDefinition,
        state: KernelState,
        context: StepContext,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        policy_record: StepPolicyRecord,
    ) -> KernelState:
        self._enforce_policy(policy_record)
        if isinstance(step, RunAgentStep):
            return self._handle_run_agent_step(
                step=step,
                state=state,
                context=context,
                catalog=catalog,
                step_started_at=step_started_at,
                policy_record=policy_record,
            )
        if isinstance(step, RunValidationStep):
            return self._handle_run_validation_step(
                step=step,
                state=state,
                context=context,
                catalog=catalog,
                step_started_at=step_started_at,
                policy_record=policy_record,
            )
        if isinstance(step, EvaluateStep):
            return self._handle_evaluate_step(
                step=step,
                state=state,
                context=context,
                catalog=catalog,
                step_started_at=step_started_at,
                policy_record=policy_record,
            )
        if isinstance(step, GateStep):
            return self._handle_gate_step(
                step=step,
                state=state,
                context=context,
                catalog=catalog,
                step_started_at=step_started_at,
                policy_record=policy_record,
            )
        if isinstance(step, RollbackStep):
            return self._handle_rollback_step(
                step=step,
                state=state,
                context=context,
                catalog=catalog,
                step_started_at=step_started_at,
                policy_record=policy_record,
            )
        raise WorkflowValidationError(f"Unsupported step type: {step.id}")

    def _handle_run_agent_step(
        self,
        step: RunAgentStep,
        state: KernelState,
        context: StepContext,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        policy_record: StepPolicyRecord,
    ) -> KernelState:
        request = RunnerTaskRequest(
            agent_family=self._map_agent_family(step.agent),
            rendered_task_text=step.prompt,
            working_directory=context.run_directory,
            prompt_reference=step.prompt,
            requested_policy=policy_record.summary.requested_policy,
        )
        result = self.runner_service.run(request)
        target = catalog.route_target(
            step,
            self._to_mechanical_outcome(result.termination).value,
            context="No route for outcome",
        )
        runner_metadata = self.artifact_store.write_json_artifact(
            paths=context.paths,
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
        self._record_step_completion(
            step=step,
            context=context,
            target=target,
            termination=self._to_mechanical_outcome(result.termination),
            started_at=step_started_at,
            extra_artifacts=(policy_record.artifact, runner_metadata),
            notes=(policy_record.note,),
        )
        return state.advance(step.id, target)

    def _handle_run_validation_step(
        self,
        step: RunValidationStep,
        state: KernelState,
        context: StepContext,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        policy_record: StepPolicyRecord,
    ) -> KernelState:
        result = self.validation_service.run(
            ValidationStepRequest(validators=step.run, run_directory=context.run_directory)
        )
        next_state = state
        report = self._normalize_harness_report(result.harness_report)
        if report is not None and report.proposed_goldens:
            next_state = state.with_pending_gate()
        target = catalog.route_target(step, result.termination.value, context="No route for outcome")
        extra_artifacts = self._validation_artifacts(
            step_id=step.id,
            paths=context.paths,
            report=report,
        )
        self._record_step_completion(
            step=step,
            context=context,
            target=target,
            termination=MechanicalOutcome(result.termination.value),
            started_at=step_started_at,
            extra_artifacts=(policy_record.artifact, *extra_artifacts),
            notes=(policy_record.note,),
        )
        return next_state.advance(step.id, target, pending_gate=next_state.pending_golden_gate)

    def _handle_evaluate_step(
        self,
        step: EvaluateStep,
        state: KernelState,
        context: StepContext,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        policy_record: StepPolicyRecord,
    ) -> KernelState:
        decision = self.planner_evaluator.evaluate(step, context.run_directory)
        self._validate_planner_next_step(step, decision.next_step)
        target = catalog.route_target(step, decision.status.value, context="No route for outcome")
        self._enforce_runtime_golden_gate(state, decision.status, target, catalog)
        planner_artifact = self.artifact_store.write_json_artifact(
            paths=context.paths,
            step_id=step.id,
            role=ArtifactRole.planner_decision,
            filename="planner_decision.json",
            payload=decision,
            required=True,
        )
        self._record_step_completion(
            step=step,
            context=context,
            target=target,
            termination=decision.status,
            started_at=step_started_at,
            extra_artifacts=(policy_record.artifact, planner_artifact),
            notes=(policy_record.note,),
        )
        return state.advance(step.id, target)

    def _handle_gate_step(
        self,
        step: GateStep,
        state: KernelState,
        context: StepContext,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        policy_record: StepPolicyRecord,
    ) -> KernelState:
        context.provenance.record_gate_requested(
            run_id=context.run_id,
            step_id=step.id,
            paths=context.paths,
        )
        gate_request = self.artifact_store.write_json_artifact(
            paths=context.paths,
            step_id=step.id,
            role=ArtifactRole.gate_request,
            filename="gate_request.json",
            payload=GateRequestArtifact(
                gate=step.gate,
                timeout_seconds=step.timeout_seconds,
            ),
            required=True,
        )
        outcome = self.gate_approver.decide(step, context.run_directory)
        context.provenance.record_gate_resolved(
            run_id=context.run_id,
            step_id=step.id,
            paths=context.paths,
        )
        gate_outcome = self.artifact_store.write_json_artifact(
            paths=context.paths,
            step_id=step.id,
            role=ArtifactRole.gate_outcome,
            filename="gate_outcome.json",
            payload=GateOutcomeArtifact(outcome=outcome),
            required=True,
        )
        target = catalog.route_target(step, outcome.value, context="No route for outcome")
        self._record_step_completion(
            step=step,
            context=context,
            target=target,
            termination=outcome,
            started_at=step_started_at,
            extra_artifacts=(policy_record.artifact, gate_request, gate_outcome),
            notes=(policy_record.note,),
        )
        pending_gate = state.pending_gate_after_outcome(outcome)
        return state.advance(step.id, target, pending_gate=pending_gate)

    def _handle_rollback_step(
        self,
        step: RollbackStep,
        state: KernelState,
        context: StepContext,
        catalog: WorkflowCatalog,
        step_started_at: datetime,
        policy_record: StepPolicyRecord,
    ) -> KernelState:
        self.workspace.rollback_pre_run()
        context.provenance.record_rollback_completed(
            run_id=context.run_id,
            step_id=step.id,
            paths=context.paths,
        )
        target = catalog.route_target(
            step,
            MechanicalOutcome.completed.value,
            context="No route for outcome",
        )
        self._record_step_completion(
            step=step,
            context=context,
            target=target,
            termination=MechanicalOutcome.completed,
            started_at=step_started_at,
            extra_artifacts=(policy_record.artifact,),
            notes=(policy_record.note,),
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
        context: StepContext,
        started_at: datetime,
        ended_at: datetime,
        last_step_id: str,
        termination: MechanicalOutcome,
    ) -> None:
        self.artifact_store.write_metadata(
            RunMetadata(
                run_id=context.run_id,
                workflow_id=workflow.workflow_id,
                workflow_version=workflow.version,
                started_at=started_at,
                artifacts_root=context.paths.artifacts_root,
                entry_step=workflow.entry_step,
                ended_at=ended_at,
                last_step_id=last_step_id,
                termination=termination,
            ),
            context.paths,
        )

    def _record_step_completion(
        self,
        *,
        step: StepDefinition,
        context: StepContext,
        target: str,
        termination: MechanicalOutcome | PlannerStatus | GateOutcome,
        started_at: datetime,
        extra_artifacts: tuple[StepArtifactEntry, ...] = (),
        notes: tuple[str, ...] = (),
    ) -> None:
        context.provenance.record_step_manifest(
            run_id=context.run_id,
            step_id=step.id,
            opcode=step.opcode,
            termination=termination,
            started_at=started_at,
            ended_at=self.clock.now(),
            paths=context.paths,
            run_directory=context.run_directory,
            extra_artifacts=extra_artifacts,
            notes=notes,
            next_step_id=target,
        )

    def _persist_step_policy(
        self,
        *,
        step: StepDefinition,
        context: StepContext,
    ) -> StepPolicyRecord:
        summary = self.execution_policy_assembler.assemble(
            settings=self.execution_policy_settings,
            workflow_policy_ref=context.workflow_policy_ref,
            step_policy_ref=self._step_policy_ref(step),
        )
        summary = self._apply_runtime_policy_guards(summary=summary, context=context)
        artifact = self.artifact_store.write_json_artifact(
            paths=context.paths,
            step_id=step.id,
            role=ArtifactRole.policy_summary,
            filename="policy_summary.json",
            payload=summary,
            required=True,
            important=True,
        )
        return StepPolicyRecord(
            summary=summary,
            artifact=artifact,
            note=self._policy_note(summary),
        )

    def _step_policy_ref(self, step: StepDefinition) -> str | None:
        if isinstance(step, RunAgentStep):
            agent_policy: str | None = step.policy
            return agent_policy
        if isinstance(step, RunValidationStep):
            validation_policy: str | None = step.policy
            return validation_policy
        if isinstance(step, EvaluateStep):
            evaluate_policy: str | None = step.policy
            return evaluate_policy
        if isinstance(step, GateStep):
            gate_policy: str | None = step.policy
            return gate_policy
        if isinstance(step, RollbackStep):
            rollback_policy: str | None = step.policy
            return rollback_policy
        return None

    def _apply_runtime_policy_guards(
        self,
        *,
        summary: PolicySummary,
        context: StepContext,
    ) -> PolicySummary:
        snapshot = self.workspace.snapshot(context.run_directory)
        violations = list(summary.violations)
        if (
            summary.effective_policy.execution_posture == ExecutionPosture.workspace_write
            and snapshot.branch_name in {"main", "master"}
        ):
            violations.append(
                PolicyViolation(
                    violation_class=PolicyViolationClass.protected_branch_violation,
                    message=(
                        "Workspace-write policy is not allowed on protected branch "
                        f"{snapshot.branch_name}."
                    ),
                    hard_violation=True,
                )
            )
        return summary.model_copy(update={"violations": tuple(violations)})

    def _enforce_policy(self, policy_record: StepPolicyRecord) -> None:
        hard_violations = [
            violation for violation in policy_record.summary.violations if violation.hard_violation
        ]
        if not hard_violations:
            return
        message = "; ".join(violation.message for violation in hard_violations)
        raise WorkflowValidationError(f"Policy violation: {message}")

    def _policy_note(self, summary: PolicySummary) -> str:
        requested = summary.requested_policy
        effective = summary.effective_policy
        violation_count = len(summary.violations)
        return (
            "policy:"
            f" requested={requested.execution_posture or 'unset'}/{requested.network_posture or 'unset'}"
            f"/{requested.approval_posture or 'unset'}"
            f" effective={effective.execution_posture.value}/{effective.network_posture.value}"
            f"/{effective.approval_posture.value}"
            f" violations={violation_count}"
        )

    def _terminate_run(
        self,
        *,
        workflow: WorkflowDefinition,
        context: StepContext,
        started_at: datetime,
        last_step_id: str,
        termination: MechanicalOutcome,
    ) -> datetime:
        ended_at: datetime = self.clock.now()
        self._write_terminal_metadata(
            workflow=workflow,
            context=context,
            started_at=started_at,
            ended_at=ended_at,
            last_step_id=last_step_id,
            termination=termination,
        )
        self.artifact_store.write_final_state(f"{termination.value}:{last_step_id}", context.paths)
        return ended_at
