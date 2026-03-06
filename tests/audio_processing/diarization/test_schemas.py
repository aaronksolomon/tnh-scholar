from tnh_scholar.audio_processing.diarization.schemas import (
    JobStatus,
    JobStatusResponse,
    PollOutcome,
)


def test_job_status_response_aliases() -> None:
    payload = {
        "jobId": "job-123",
        "status": "running",
        "output": {"segments": []},
    }

    jsr = JobStatusResponse.model_validate(payload)

    assert jsr.job_id == "job-123"
    assert jsr.status == JobStatus.RUNNING
    assert jsr.payload == {"segments": []}
    assert jsr.outcome == PollOutcome.ERROR


def test_job_status_response_normalizes_created_to_pending() -> None:
    payload = {
        "jobId": "job-456",
        "status": "created",
    }

    jsr = JobStatusResponse.model_validate(payload)

    assert jsr.job_id == "job-456"
    assert jsr.status == JobStatus.PENDING


def test_job_status_response_normalizes_created_enum_to_pending() -> None:
    payload = {
        "jobId": "job-789",
        "status": JobStatus.CREATED,
    }

    jsr = JobStatusResponse.model_validate(payload)

    assert jsr.job_id == "job-789"
    assert jsr.status == JobStatus.PENDING
