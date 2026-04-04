"""Typed models for run artifact persistence."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.kernel.enums import (
    GateOutcome,
    MechanicalOutcome,
    Opcode,
    PlannerStatus,
)
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily, RunnerTermination


class RunArtifactPaths(BaseModel):
    """Canonical run-scoped filesystem paths."""

    artifacts_root: Path
    run_directory: Path
    artifacts_directory: Path
    event_log_path: Path
    metadata_path: Path
    final_state_path: Path


class SchemaVersionRecord(BaseModel):
    """Version record for one cross-boundary schema."""

    name: str
    version: str


class RunMetadata(BaseModel):
    """Run-level metadata persisted for one workflow execution."""

    run_id: str
    workflow_id: str
    workflow_version: int
    started_at: datetime
    artifacts_root: Path
    entry_step: str
    ended_at: datetime | None = None
    last_step_id: str | None = None
    termination: MechanicalOutcome | None = None
    schema_versions: tuple[SchemaVersionRecord, ...] = Field(default_factory=tuple)


class RunEventType(str, Enum):
    """Canonical event types for one workflow run."""

    step_started = "step_started"
    step_completed = "step_completed"
    step_failed = "step_failed"
    artifact_recorded = "artifact_recorded"
    gate_requested = "gate_requested"
    gate_resolved = "gate_resolved"
    rollback_completed = "rollback_completed"


class ArtifactRole(str, Enum):
    """Canonical artifact roles reserved for maintained consumers."""

    runner_transcript = "runner_transcript"
    runner_final_response = "runner_final_response"
    runner_metadata = "runner_metadata"
    policy_summary = "policy_summary"
    validation_report = "validation_report"
    validation_stdout = "validation_stdout"
    validation_stderr = "validation_stderr"
    planner_decision = "planner_decision"
    gate_request = "gate_request"
    gate_outcome = "gate_outcome"
    workspace_diff = "workspace_diff"
    workspace_status = "workspace_status"


class StepArtifactEntry(BaseModel):
    """Canonical manifest entry for one persisted artifact."""

    role: ArtifactRole
    path: Path
    media_type: str
    required: bool
    important: bool = False


class EvidenceReference(BaseModel):
    """Compact evaluator-facing evidence reference."""

    role: ArtifactRole
    path: Path
    summary: str | None = None


class EvidenceSummary(BaseModel):
    """Thin summary of canonical evidence for one step."""

    references: tuple[EvidenceReference, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class StepManifest(BaseModel):
    """Canonical manifest for one executed step."""

    step_id: str
    opcode: Opcode
    started_at: datetime
    ended_at: datetime
    termination: MechanicalOutcome | PlannerStatus | GateOutcome
    evidence_summary: EvidenceSummary
    artifacts: tuple[StepArtifactEntry, ...] = Field(default_factory=tuple)

    def artifact_for_role(self, role: ArtifactRole) -> StepArtifactEntry | None:
        """Return the first artifact matching the requested role."""
        for artifact in self.artifacts:
            if artifact.role == role:
                return artifact
        return None


class RunnerMetadataArtifact(BaseModel):
    """Canonical maintained runner metadata artifact."""

    agent_family: AgentFamily
    invocation_mode: str | None = None
    command: tuple[str, ...] = Field(default_factory=tuple)
    working_directory: Path | None = None
    prompt_reference: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    exit_code: int | None = None
    termination: RunnerTermination
    capture_format: str | None = None


class GateRequestArtifact(BaseModel):
    """Canonical gate request artifact."""

    gate: str
    timeout_seconds: int | None = None


class GateOutcomeArtifact(BaseModel):
    """Canonical gate outcome artifact."""

    outcome: GateOutcome


class RunEventRecord(BaseModel):
    """Appendable runtime event record."""

    timestamp: datetime
    run_id: str
    step_id: str
    event_type: RunEventType
    next_step_id: str | None = None
    artifact_role: ArtifactRole | None = None
    artifact_path: Path | None = None
