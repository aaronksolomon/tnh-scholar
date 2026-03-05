from __future__ import annotations

from typing import Any

from tnh_scholar.audio_processing.diarization.pyannote_diarize import PyannoteService
from tnh_scholar.audio_processing.diarization.schemas import (
    DiarizationPending,
    JobStatusResponse,
)


class _FakeClient:
    def __init__(self, response: JobStatusResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def poll_job_until_complete(self, job_id: str, **kwargs: Any) -> JobStatusResponse:
        self.calls.append({"job_id": job_id, **kwargs})
        return self.response


class _FakeAdapter:
    def __init__(self, response: DiarizationPending) -> None:
        self.response = response
        self.calls: list[JobStatusResponse] = []

    def to_response(self, jsr: JobStatusResponse) -> DiarizationPending:
        self.calls.append(jsr)
        return self.response


def test_pyannote_service_get_response_forwards_wait_flag() -> None:
    jsr = JobStatusResponse(jobId="job-123", status="running")
    diarization_response = DiarizationPending(status="pending", job_id="job-123")
    client = _FakeClient(response=jsr)
    adapter = _FakeAdapter(response=diarization_response)
    service = PyannoteService(client=client, adapter=adapter)

    result = service.get_response("job-123", wait_until_complete=True)

    assert result == diarization_response
    assert client.calls == [{"job_id": "job-123", "wait_until_complete": True}]
    assert adapter.calls == [jsr]
