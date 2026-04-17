"""Kernel-side provenance recording helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tnh_scholar.agent_orchestration.kernel.enums import (
    GateOutcome,
    MechanicalOutcome,
    Opcode,
    PlannerStatus,
)
from tnh_scholar.agent_orchestration.kernel.protocols import (
    ClockProtocol,
    RunArtifactStoreProtocol,
    WorkspaceServiceProtocol,
)
from tnh_scholar.agent_orchestration.run_artifacts.models import (
    ArtifactRole,
    EvidenceReference,
    EvidenceSummary,
    RunArtifactPaths,
    RunEventRecord,
    RunEventType,
    RunLifecycleState,
    StepArtifactEntry,
    StepManifest,
)
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily


@dataclass(frozen=True)
class KernelProvenanceRecorder:
    """Persist kernel-side provenance artifacts, manifests, and events."""

    artifact_store: RunArtifactStoreProtocol
    workspace: WorkspaceServiceProtocol
    clock: ClockProtocol

    def record_status_updated(
        self,
        *,
        run_id: str,
        step_id: str,
        lifecycle_state: RunLifecycleState,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical status-updated event."""
        self._append_event(
            run_id=run_id,
            step_id=step_id,
            event_type=RunEventType.status_updated,
            lifecycle_state=lifecycle_state,
            paths=paths,
        )

    def record_step_started(
        self,
        *,
        run_id: str,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical step-started event."""
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=RunEventType.step_started,
            ),
            paths,
        )

    def record_gate_requested(
        self,
        *,
        run_id: str,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical gate-requested event."""
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=RunEventType.gate_requested,
            ),
            paths,
        )

    def record_gate_resolved(
        self,
        *,
        run_id: str,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical gate-resolved event."""
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=RunEventType.gate_resolved,
            ),
            paths,
        )

    def record_runner_started(
        self,
        *,
        run_id: str,
        step_id: str,
        runner_family: AgentFamily,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical runner-started event."""
        self._append_event(
            run_id=run_id,
            step_id=step_id,
            event_type=RunEventType.runner_started,
            runner_family=runner_family,
            paths=paths,
        )

    def record_runner_completed(
        self,
        *,
        run_id: str,
        step_id: str,
        runner_family: AgentFamily,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical runner-completed event."""
        self._append_event(
            run_id=run_id,
            step_id=step_id,
            event_type=RunEventType.runner_completed,
            runner_family=runner_family,
            paths=paths,
        )

    def record_route_selected(
        self,
        *,
        run_id: str,
        step_id: str,
        next_step_id: str,
        opcode: Opcode,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical route-selected event."""
        self._append_event(
            run_id=run_id,
            step_id=step_id,
            event_type=RunEventType.route_selected,
            next_step_id=next_step_id,
            opcode=opcode,
            paths=paths,
        )

    def record_step_waiting(
        self,
        *,
        run_id: str,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical step-waiting event."""
        self._append_event(
            run_id=run_id,
            step_id=step_id,
            event_type=RunEventType.step_waiting,
            lifecycle_state=RunLifecycleState.waiting,
            paths=paths,
        )

    def record_step_blocked(
        self,
        *,
        run_id: str,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical step-blocked event."""
        self._append_event(
            run_id=run_id,
            step_id=step_id,
            event_type=RunEventType.step_blocked,
            lifecycle_state=RunLifecycleState.blocked,
            paths=paths,
        )

    def record_rollback_completed(
        self,
        *,
        run_id: str,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> None:
        """Append the canonical rollback-completed event."""
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=RunEventType.rollback_completed,
            ),
            paths,
        )

    def record_step_manifest(
        self,
        *,
        run_id: str,
        step_id: str,
        opcode: Opcode,
        termination: MechanicalOutcome | PlannerStatus | GateOutcome,
        started_at: datetime,
        ended_at: datetime,
        paths: RunArtifactPaths,
        extra_artifacts: tuple[StepArtifactEntry, ...] = (),
        notes: tuple[str, ...] = (),
        next_step_id: str | None = None,
    ) -> None:
        """Persist the canonical manifest and completion events for one step."""
        workspace_artifacts = self._write_workspace_artifacts(
            step_id=step_id,
            paths=paths,
        )
        artifacts = (*extra_artifacts, *workspace_artifacts)
        self._build_and_write_manifest(
            step_id=step_id,
            opcode=opcode,
            termination=termination,
            started_at=started_at,
            ended_at=ended_at,
            artifacts=artifacts,
            notes=notes,
            paths=paths,
        )
        self._record_artifacts(run_id=run_id, step_id=step_id, artifacts=artifacts, paths=paths)
        self._record_completion(
            run_id=run_id,
            step_id=step_id,
            termination=termination,
            next_step_id=next_step_id,
            paths=paths,
        )

    def record_failed_step(
        self,
        *,
        run_id: str,
        step_id: str,
        opcode: Opcode,
        started_at: datetime,
        ended_at: datetime,
        paths: RunArtifactPaths,
        extra_artifacts: tuple[StepArtifactEntry, ...] = (),
        notes: tuple[str, ...],
    ) -> None:
        """Persist the canonical failure manifest and event for one step."""
        self.record_step_manifest(
            run_id=run_id,
            step_id=step_id,
            opcode=opcode,
            termination=MechanicalOutcome.error,
            started_at=started_at,
            ended_at=ended_at,
            paths=paths,
            extra_artifacts=extra_artifacts,
            notes=notes,
        )

    def _write_workspace_artifacts(
        self,
        *,
        step_id: str,
        paths: RunArtifactPaths,
    ) -> tuple[StepArtifactEntry, ...]:
        snapshot = self.workspace.snapshot()
        status_entry = self.artifact_store.write_json_artifact(
            paths=paths,
            step_id=step_id,
            role=ArtifactRole.workspace_status,
            filename="workspace_status.json",
            payload=snapshot,
            required=True,
        )
        diff_summary = snapshot.diff_summary or self.workspace.diff_summary()
        if not diff_summary:
            return (status_entry,)
        diff_entry = self.artifact_store.write_text_artifact(
            paths=paths,
            step_id=step_id,
            role=ArtifactRole.workspace_diff,
            filename="workspace_diff.txt",
            content=diff_summary,
            media_type="text/plain",
            required=False,
            important=True,
        )
        return status_entry, diff_entry

    def _record_artifact(
        self,
        *,
        run_id: str,
        step_id: str,
        artifact: StepArtifactEntry,
        paths: RunArtifactPaths,
    ) -> None:
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=RunEventType.artifact_recorded,
                artifact_role=artifact.role,
                artifact_path=artifact.path,
            ),
            paths,
        )

    def _build_and_write_manifest(
        self,
        *,
        step_id: str,
        opcode: Opcode,
        termination: MechanicalOutcome | PlannerStatus | GateOutcome,
        started_at: datetime,
        ended_at: datetime,
        artifacts: tuple[StepArtifactEntry, ...],
        notes: tuple[str, ...],
        paths: RunArtifactPaths,
    ) -> None:
        manifest = StepManifest(
            step_id=step_id,
            opcode=opcode,
            started_at=started_at,
            ended_at=ended_at,
            termination=termination,
            evidence_summary=EvidenceSummary(
                references=tuple(self._to_reference(artifact) for artifact in artifacts),
                notes=notes,
            ),
            artifacts=artifacts,
        )
        self.artifact_store.write_step_manifest(manifest, paths)

    def _record_artifacts(
        self,
        *,
        run_id: str,
        step_id: str,
        artifacts: tuple[StepArtifactEntry, ...],
        paths: RunArtifactPaths,
    ) -> None:
        for artifact in artifacts:
            self._record_artifact(run_id=run_id, step_id=step_id, artifact=artifact, paths=paths)

    def _record_completion(
        self,
        *,
        run_id: str,
        step_id: str,
        termination: MechanicalOutcome | PlannerStatus | GateOutcome,
        next_step_id: str | None,
        paths: RunArtifactPaths,
    ) -> None:
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=self._completion_event_type(termination),
                next_step_id=next_step_id,
            ),
            paths,
        )

    def _append_event(
        self,
        *,
        run_id: str,
        step_id: str,
        event_type: RunEventType,
        paths: RunArtifactPaths,
        next_step_id: str | None = None,
        opcode: Opcode | None = None,
        runner_family: AgentFamily | None = None,
        lifecycle_state: RunLifecycleState | None = None,
    ) -> None:
        self.artifact_store.append_event(
            RunEventRecord(
                timestamp=self.clock.now(),
                run_id=run_id,
                step_id=step_id,
                event_type=event_type,
                next_step_id=next_step_id,
                opcode=opcode,
                runner_family=runner_family,
                lifecycle_state=lifecycle_state,
            ),
            paths,
        )

    def _to_reference(self, artifact: StepArtifactEntry) -> EvidenceReference:
        return EvidenceReference(role=artifact.role, path=artifact.path)

    def _completion_event_type(
        self,
        termination: MechanicalOutcome | PlannerStatus | GateOutcome,
    ) -> RunEventType:
        if isinstance(termination, MechanicalOutcome) and termination != MechanicalOutcome.completed:
            return RunEventType.step_failed
        return RunEventType.step_completed
