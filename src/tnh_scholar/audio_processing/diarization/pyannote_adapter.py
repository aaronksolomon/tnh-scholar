from typing import Any, Dict, List, Optional

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs

from .config import DiarizationConfig
from .models import DiarizedSegment
from .protocols import SegmentAdapter
from .schemas import (
    DiarizationFailed,
    DiarizationPending,
    DiarizationResponse,
    DiarizationResult,
    DiarizationRunning,
    DiarizationSucceeded,
    ErrorCode,
    ErrorInfo,
    JobStatus,
    JobStatusResponse,
    PollOutcome,
)
from .types import PyannoteEntry

logger = get_child_logger(__name__)

class PyannoteAdapter(SegmentAdapter):
    def __init__(self, config: DiarizationConfig = DiarizationConfig()):
        self.config = config

    def to_segments(self, data: Dict[str, List['PyannoteEntry']]) -> List[DiarizedSegment]:
        """
        Convert a pyannoteai diarization result dict to list of DiarizationSegment objects.
        """
        entries = self._extract_entries(data)
        valid_entries = self._validate_pyannote_entries(entries)
        segments: List[DiarizedSegment] = []
        for e in valid_entries:
            segment = DiarizedSegment(
                speaker=str(e.get("speaker", "SPEAKER_00")),
                start=TimeMs.from_seconds(float(e["start"])),
                end=TimeMs.from_seconds(float(e["end"])),
                audio_map_start=None,
                gap_before=None,
                spacing_time=None,
            )
            segments.append(segment)
        return self._sort_and_normalize_segments(segments)

    def to_response(
        self, jsr: JobStatusResponse
    ) -> DiarizationResponse:
        """
        Convert a JobStatusResponse to a DiarizationResponse (domain layer).
        """
        if self._is_successful(jsr):
            return self._build_succeeded(jsr)
        if self._is_outcome_failure(jsr):
            return self._build_outcome_failure(jsr)
        if self._is_api_failure(jsr):
            return self._build_api_failed(jsr)
        if self._is_pending(jsr):
            return self._build_pending(jsr)
        if self._is_running(jsr):
            return self._build_running(jsr)
        return self._build_fallback(jsr)

    def _extract_entries(self, payload: Dict[str, Any] | None) -> List[dict[str, Any]]:
        raw = payload or {}
        if isinstance(raw.get("diarization"), list):
            return list(raw["diarization"])
        segments = raw.get("segments")
        if isinstance(segments, list):
            return list(segments)
        ann = raw.get("annotation")
        if isinstance(ann, dict) and isinstance(ann.get("segments"), list):
            return list(ann["segments"])
        logger.warning(
            "Unexpected payload shape in _extract_entries: %r", payload
        )
        return []

    def _validate_pyannote_entries(self, entries: List[dict[str, Any]]) -> List[dict[str, Any]]:
        valid = []
        for e in entries:
            if not isinstance(e, dict):
                logger.warning("Entry is not a dict: %r", e)
                continue
            if any(k not in e for k in ("start", "end")):
                logger.warning("Missing 'start' or 'end' in entry: %r", e)
                continue
            try:
                float(e["start"])
                float(e["end"])
            except (ValueError, TypeError):
                logger.warning("Non-numeric 'start' or 'end' in entry: %r", e)
                continue
            valid.append(e)
        return valid

    def _sort_and_normalize_segments(
        self, segments: List[DiarizedSegment]
        ) -> List[DiarizedSegment]:
        self._sort_by_start(segments)
        for segment in segments:
            segment.normalize()
        return segments

    def _sort_by_start(self, segments: List[DiarizedSegment]) -> None:
        segments.sort(key=lambda segment: segment.start)

    def _map_outcome_to_error(self, outcome: PollOutcome, status: Optional[JobStatus]) -> ErrorCode:
        if outcome == PollOutcome.SUCCEEDED:
            logger.warning(
                "PollOutcome.SUCCEEDED was mapped to ErrorCode.UNKNOWN in map_outcome_to_error. "
                "This indicates a logic error."
            )
            return ErrorCode.UNKNOWN
        if outcome == PollOutcome.FAILED:
            return ErrorCode.API_ERROR
        if outcome == PollOutcome.TIMEOUT:
            return ErrorCode.TIMEOUT
        if outcome == PollOutcome.NETWORK_ERROR:
            return ErrorCode.TRANSIENT
        if outcome == PollOutcome.INTERRUPTED:
            return ErrorCode.CANCELLED
        if outcome == PollOutcome.ERROR:
            if status in (JobStatus.PENDING, JobStatus.RUNNING):
                return ErrorCode.TRANSIENT
            return ErrorCode.UNKNOWN
        return ErrorCode.UNKNOWN

    def _is_successful(self, jsr: JobStatusResponse) -> bool:
        return jsr.outcome == PollOutcome.SUCCEEDED and jsr.status == JobStatus.SUCCEEDED

    def _is_outcome_failure(self, jsr: JobStatusResponse) -> bool:
        return jsr.outcome in (
            PollOutcome.TIMEOUT,
            PollOutcome.NETWORK_ERROR,
            PollOutcome.INTERRUPTED,
            PollOutcome.ERROR,
        )

    def _is_api_failure(self, jsr: JobStatusResponse) -> bool:
        return jsr.status == JobStatus.FAILED

    def _is_pending(self, jsr: JobStatusResponse) -> bool:
        return jsr.status == JobStatus.PENDING

    def _is_running(self, jsr: JobStatusResponse) -> bool:
        return jsr.status == JobStatus.RUNNING

    def _build_succeeded(self, jsr: JobStatusResponse) -> DiarizationSucceeded:
        payload = jsr.payload or {}
        segments = self.to_segments(payload)
        num_speakers = payload.get("numSpeakers", payload.get("num_speakers"))
        return DiarizationSucceeded(
            status="succeeded",
            job_id=jsr.job_id,
            result=DiarizationResult(segments=segments, num_speakers=num_speakers, metadata=None),
            raw=jsr.model_dump(mode="json"),
        )

    def _build_outcome_failure(self, jsr: JobStatusResponse) -> DiarizationFailed:
        code = self._map_outcome_to_error(jsr.outcome, jsr.status)
        message = jsr.server_error_msg or "Null Message"
        return DiarizationFailed(
            status="failed",
            job_id=jsr.job_id,
            error=ErrorInfo(
                code=code,
                message=message,
                details={
                    "outcome": jsr.outcome.value,
                    "status": jsr.status.value if jsr.status else None,
                    "polls": jsr.polls,
                    "elapsed_s": jsr.elapsed_s,
                },
            ),
            raw=jsr.model_dump(mode="json"),
        )

    def _build_api_failed(self, jsr: JobStatusResponse) -> DiarizationFailed:
        return DiarizationFailed(
            status="failed",
            job_id=jsr.job_id,
            error=ErrorInfo(
                code=ErrorCode.API_ERROR,
                message=jsr.server_error_msg or "Remote job failed",
                details={"status": jsr.status.value if jsr.status else None},
            ),
            raw=jsr.model_dump(mode="json"),
        )

    def _build_pending(self, jsr: JobStatusResponse) -> DiarizationPending:
        return DiarizationPending(status="pending", job_id=jsr.job_id, raw=jsr.model_dump(mode="json"))

    def _build_running(self, jsr: JobStatusResponse) -> DiarizationRunning:
        return DiarizationRunning(status="running", job_id=jsr.job_id, raw=jsr.model_dump(mode="json"))

    def _build_fallback(self, jsr: JobStatusResponse) -> DiarizationFailed:
        return DiarizationFailed(
            status="failed",
            job_id=jsr.job_id,
            error=ErrorInfo(
                code=ErrorCode.UNKNOWN,
                message=(
                    f"Unknown outcome/status combination: outcome={jsr.outcome.value}, "
                    f"status={getattr(jsr.status, 'value', None)}"
                ),
                details={
                    "outcome": jsr.outcome.value,
                    "status": jsr.status.value if jsr.status else None,
                    "polls": jsr.polls,
                    "elapsed_s": jsr.elapsed_s,
                },
            ),
            raw=jsr.model_dump(mode="json"),
        )

    def failed_start(self):
        return DiarizationFailed(
            status="failed",
            job_id=None,
            error=ErrorInfo(
                code=ErrorCode.TRANSIENT,
                message=("Job failed to upload or start."),
                details=None,
            )
            
        )