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
