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
    RunMetadata,
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


def test_run_artifact_store_writes_canonical_event_stream_fields(tmp_path: Path) -> None:
    store = FilesystemRunArtifactStore()
    paths = store.create_run("run-2", tmp_path)

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

    event = json.loads(paths.event_log_path.read_text(encoding="utf-8").strip())
    assert event["run_id"] == "run-2"
    assert event["step_id"] == "implement"
    assert event["event_type"] == RunEventType.artifact_recorded.value
    assert event["artifact_role"] == ArtifactRole.runner_transcript.value
    assert event["artifact_path"] == "artifacts/implement/transcript.jsonl"
    assert "timestamp" in event


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
