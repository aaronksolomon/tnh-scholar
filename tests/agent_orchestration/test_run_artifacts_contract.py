"""Tests for the maintained OA04.3 run-artifact contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from tnh_scholar.agent_orchestration.kernel.models import MechanicalOutcome, Opcode
from tnh_scholar.agent_orchestration.run_artifacts import (
    ArtifactRole,
    EvidenceReference,
    EvidenceSummary,
    FilesystemRunArtifactStore,
    RunEventRecord,
    RunEventType,
    RunLifecycleState,
    RunMetadata,
    RunStatus,
    StepManifest,
)


class PolicyPayload(BaseModel):
    """Minimal typed payload for JSON artifact persistence coverage."""

    requested_policy: dict[str, str]


def test_run_artifact_store_writes_oa043_metadata_contract(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-1", tmp_path)
    metadata = RunMetadata(
        run_id="run-1",
        workflow_id="workflow-a",
        workflow_version=4,
        started_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
        artifacts_root=paths.artifacts_root,
        entry_step="design",
        last_step_id="validate",
        termination=MechanicalOutcome.completed,
    )

    store.write_metadata(metadata, paths)

    payload = json.loads(paths.metadata_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-1"
    assert payload["workflow_id"] == "workflow-a"
    assert payload["workflow_version"] == 4
    assert payload["entry_step"] == "design"
    assert payload["artifacts_root"] == str(tmp_path)
    assert payload["termination"] == MechanicalOutcome.completed.value


def test_run_artifact_store_writes_live_status_contract(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-status", tmp_path)
    status = RunStatus(
        run_id="run-status",
        workflow_id="workflow-a",
        started_at=datetime(2026, 4, 16, 1, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, 1, 1, tzinfo=timezone.utc),
        lifecycle_state=RunLifecycleState.running,
        current_step_id="implement",
        last_completed_step_id="design",
        active_opcode=Opcode.run_agent,
        worktree_path=tmp_path / "worktree",
        last_route_target="validate",
        elapsed_seconds=60,
    )

    store.write_status(status, paths)

    payload = json.loads(paths.status_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-status"
    assert payload["workflow_id"] == "workflow-a"
    assert payload["lifecycle_state"] == RunLifecycleState.running.value
    assert payload["current_step_id"] == "implement"
    assert payload["last_completed_step_id"] == "design"
    assert payload["active_opcode"] == Opcode.run_agent.value
    assert payload["worktree_path"] == str(tmp_path / "worktree")


def test_run_artifact_store_reads_live_status_via_canonical_path(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-status-read", tmp_path)
    status = RunStatus(
        run_id="run-status-read",
        workflow_id="workflow-b",
        started_at=datetime(2026, 4, 16, 2, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, 2, 1, tzinfo=timezone.utc),
        lifecycle_state=RunLifecycleState.completed,
        current_step_id="STOP",
        last_completed_step_id="validate",
        elapsed_seconds=60,
    )

    store.write_status(status, paths)

    assert store.status_path_for_run("run-status-read", tmp_path) == paths.status_path
    assert store.read_status("run-status-read", tmp_path) == status


def test_run_artifact_store_writes_canonical_event_stream_fields(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-2", tmp_path)

    store.append_event(
        RunEventRecord(
            timestamp=datetime(2026, 3, 28, 1, 2, 2, tzinfo=timezone.utc),
            run_id="run-2",
            step_id="implement",
            event_type=RunEventType.step_completed,
            next_step_id="validate",
        ),
        paths,
    )
    store.append_event(
        RunEventRecord(
            timestamp=datetime(2026, 3, 28, 1, 2, 3, tzinfo=timezone.utc),
            run_id="run-2",
            step_id="implement",
            event_type=RunEventType.artifact_recorded,
            artifact_role=ArtifactRole.runner_transcript,
            artifact_path=Path("artifacts/implement/transcript.jsonl"),
        ),
        paths,
    )

    raw_log = paths.event_log_path.read_text(encoding="utf-8").strip()
    lines = [line for line in raw_log.splitlines() if line.strip()]
    assert len(lines) == 2

    events = [json.loads(line) for line in lines]
    for event in events:
        assert event["run_id"] == "run-2"
        assert "timestamp" in event

    artifact_events = [
        event
        for event in events
        if event["event_type"] == RunEventType.artifact_recorded.value
        and event.get("artifact_role") == ArtifactRole.runner_transcript.value
    ]
    assert len(artifact_events) == 1

    artifact_event = artifact_events[0]
    assert artifact_event is events[-1]
    assert artifact_event["step_id"] == "implement"
    assert artifact_event["artifact_path"] == "artifacts/implement/transcript.jsonl"


def test_run_artifact_store_persists_manifest_and_canonical_artifacts(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-3", tmp_path)
    transcript_entry = store.write_text_artifact(
        paths=paths,
        step_id="implement",
        role=ArtifactRole.runner_transcript,
        filename="transcript.jsonl",
        content="{}\n",
        media_type="application/jsonl",
        required=True,
    )
    policy_entry = store.write_json_artifact(
        paths=paths,
        step_id="implement",
        role=ArtifactRole.policy_summary,
        filename="policy_summary.json",
        payload={"requested_policy": {"execution_posture": "workspace-write"}},
        required=True,
        important=True,
    )
    manifest = StepManifest(
        step_id="implement",
        opcode=Opcode.run_agent,
        started_at=datetime(2026, 3, 28, 1, 0, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 3, 28, 1, 5, 0, tzinfo=timezone.utc),
        termination=MechanicalOutcome.completed,
        evidence_summary=EvidenceSummary(
            references=(
                EvidenceReference(
                    role=ArtifactRole.runner_transcript,
                    path=transcript_entry.path,
                    summary="Primary runner transcript.",
                ),
                EvidenceReference(
                    role=ArtifactRole.policy_summary,
                    path=policy_entry.path,
                    summary="Requested/effective policy record.",
                ),
            )
        ),
        artifacts=(transcript_entry, policy_entry),
    )

    manifest_path = store.write_step_manifest(manifest, paths)

    persisted = StepManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    assert persisted.artifact_for_role(ArtifactRole.runner_transcript) == transcript_entry
    assert persisted.artifact_for_role(ArtifactRole.policy_summary) == policy_entry
    assert paths.artifacts_root == tmp_path
    assert transcript_entry.path == Path("artifacts/implement/transcript.jsonl")
    assert policy_entry.important is True
    assert paths.artifacts_directory == paths.run_directory / "artifacts"


def test_run_artifact_store_writes_final_state_file(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-4", tmp_path)

    store.write_final_state("STOP:STOP", paths)

    assert paths.final_state_path.read_text(encoding="utf-8") == "STOP:STOP"


def test_run_artifact_store_writes_json_artifact_from_pydantic_payload(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-5", tmp_path)

    entry = store.write_json_artifact(
        paths=paths,
        step_id="implement",
        role=ArtifactRole.policy_summary,
        filename="policy_summary.json",
        payload=PolicyPayload(requested_policy={"execution_posture": "workspace-write"}),
        required=True,
    )

    persisted = json.loads((paths.run_directory / entry.path).read_text(encoding="utf-8"))
    assert persisted["requested_policy"]["execution_posture"] == "workspace-write"
    assert entry.media_type == "application/json"


def test_run_artifact_store_copies_existing_file_artifact(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-6", tmp_path)
    source = tmp_path / "fixture.txt"
    source.write_text("fixture\n", encoding="utf-8")

    entry = store.copy_file_artifact(
        paths=paths,
        step_id="validate",
        role=ArtifactRole.harness_fixture,
        filename="fixtures/fixture.txt",
        source_path=source,
        media_type="text/plain",
        required=False,
    )

    assert entry.role == ArtifactRole.harness_fixture
    assert str(entry.path).endswith("fixtures/fixture.txt")
    assert entry.media_type == "text/plain"
    assert (paths.run_directory / entry.path).read_text(encoding="utf-8") == "fixture\n"
