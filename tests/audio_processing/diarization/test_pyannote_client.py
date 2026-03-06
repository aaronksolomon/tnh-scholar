from __future__ import annotations

from typing import Any

from tnh_scholar.audio_processing.diarization.config import PollingConfig
from tnh_scholar.audio_processing.diarization.pyannote_client import PyannoteClient, _PollSignal
from tnh_scholar.audio_processing.diarization.schemas import JobStatus, JobStatusResponse


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def test_check_status_with_retry_normalizes_created_and_uses_timeout(monkeypatch) -> None:
    call_args: dict[str, Any] = {}

    def fake_get(url: str, *, headers: dict[str, str], timeout: int) -> _FakeResponse:
        call_args["url"] = url
        call_args["headers"] = headers
        call_args["timeout"] = timeout
        return _FakeResponse({"jobId": "job-123", "status": "created"})

    monkeypatch.setattr(
        "tnh_scholar.audio_processing.diarization.pyannote_client.requests.get",
        fake_get,
    )

    client = PyannoteClient(api_key="test-key")
    result = client.check_job_status("job-123")

    assert result is not None
    assert result.status == JobStatus.PENDING
    assert call_args["url"].endswith("/jobs/job-123")
    assert call_args["timeout"] == client.network_timeout


def test_send_payload_uses_network_timeout(monkeypatch) -> None:
    call_args: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: int,
    ) -> _FakeResponse:
        call_args["url"] = url
        call_args["headers"] = headers
        call_args["json"] = json
        call_args["timeout"] = timeout
        return _FakeResponse({"jobId": "job-789"})

    monkeypatch.setattr(
        "tnh_scholar.audio_processing.diarization.pyannote_client.requests.post",
        fake_post,
    )

    client = PyannoteClient(api_key="test-key")
    job_id = client.start_diarization("media://test-audio")

    assert job_id == "job-789"
    assert call_args["url"] == client.config.diarize_endpoint
    assert call_args["json"] == {"url": "media://test-audio"}
    assert call_args["timeout"] == client.network_timeout


def test_extract_response_info_raises_when_field_missing() -> None:
    client = PyannoteClient(api_key="test-key")

    try:
        client._extract_response_info(
            _FakeResponse({"other": "value"}),
            "jobId",
            "API response missing job ID",
        )
    except ValueError as error:
        assert str(error) == "API response missing job ID"
    else:
        raise AssertionError("Expected ValueError when response field is missing")


def test_extract_response_info_coerces_non_string_values_to_string() -> None:
    client = PyannoteClient(api_key="test-key")

    result = client._extract_response_info(
        _FakeResponse({"jobId": 12345}),
        "jobId",
        "API response missing job ID",
    )

    assert result == "12345"


def test_job_poller_continues_on_pending_status() -> None:
    def status_fn(_: str) -> JobStatusResponse:
        return JobStatusResponse(jobId="job-1", status="created")

    poller = PyannoteClient.JobPoller(
        status_fn=status_fn,
        job_id="job-1",
        polling_config=PollingConfig(),
    )

    result = poller._poll()

    assert result is _PollSignal.CONTINUE
    assert poller.last_status is not None
    assert poller.last_status.status == JobStatus.PENDING


def test_job_poller_returns_terminal_success_response() -> None:
    def status_fn(_: str) -> JobStatusResponse:
        return JobStatusResponse(jobId="job-2", status="succeeded")

    poller = PyannoteClient.JobPoller(
        status_fn=status_fn,
        job_id="job-2",
        polling_config=PollingConfig(),
    )

    result = poller._poll()

    assert isinstance(result, JobStatusResponse)
    assert result.status == JobStatus.SUCCEEDED
