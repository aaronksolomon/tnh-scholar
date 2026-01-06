# schemas.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


# -----------------------------
# Transport / API-mirroring layer
# -----------------------------
class PollOutcome(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    INTERRUPTED = "interrupted"
    ERROR = "error"

    
class JobStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"


@dataclass(frozen=True)
class JobHandle:
    job_id: str
    backend: Literal["pyannote"] = "pyannote"

    
class DiarizationParams(BaseModel):
    """
    Per-request diarization options; maps to pyannote API payload.
    Use .to_api_dict() to emit API field names.
    """

    model_config = ConfigDict(
        frozen=True,            # make instances immutable
        populate_by_name=True,  # allow using pythonic field names with aliases
        extra="forbid",         # catch accidental fields at construction
    )

    # Pythonic attribute -> API alias on dump
    num_speakers: int | Literal["auto"] | None = Field(
        default=None,
        alias="numSpeakers",
        description="Fixed number of speakers or 'auto' for detection.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for segments.",
    )
    webhook: AnyUrl | None = Field(
        default=None,
        description="Webhook URL for job status callbacks.",
    )

    def to_api_dict(self) -> dict[str, Any]:
        """Return payload dict using API field names (camelCase) and excluding Nones."""
        return self.model_dump(by_alias=True, exclude_none=True)


class StartDiarizationResponse(BaseModel):
    """
    Minimal typed view of the start-diarization response.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    job_id: str = Field(alias="jobId")


class JobStatusResponse(BaseModel):
    """
    Job Status Result (JSR): unified transport payload + client polling context.
    Combines transport-level fields with client-side polling metadata.

    Semantics:
    - `outcome` describes how polling concluded (terminal success/failure, timeout, network error, etc.).
    - `status` is the last known *server* job status (`SUCCEEDED`, `FAILED`, `RUNNING`, `PENDING`)
    - `server_error_msg` and `payload` mirror the remote payload when present.
    - `polls` and `elapsed_s` report client polling metrics.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        populate_by_name=True,
    )

    # The job id for connected to this response
    job_id: str = Field(alias="jobId")
    
    # How the client-side polling finished
    outcome: PollOutcome = PollOutcome.ERROR

    # Last known server-side status (may be None if never retrieved)
    status: Optional[JobStatus] = None

    # Transport-mirrored fields (when server responded with them)
    server_error_msg: Optional[str] = Field(default=None, alias="error")
    payload: Optional[dict[str, Any]] = Field(default=None, alias="output")

    # Client-side polling metadata
    polls: int = 0
    elapsed_s: float = 0.0


# -----------------------------
# Domain / App-level layer
# -----------------------------
class ErrorCode(str, Enum):
    """Client- and adapter-level error taxonomy (not server statuses)."""

    TIMEOUT = "timeout"        # client-side polling exceeded
    CANCELLED = "cancelled"      # user/client initiated cancellation
    TRANSIENT = "transient"      # retryable infra/network issue
    BAD_REQUEST = "bad_request"  # invalid params before hitting API
    API_ERROR = "api_error"      # remote API responded with error
    PARSE_ERROR = "parse_error"  # unexpected/invalid payload shape
    UNKNOWN = "unknown"


class ErrorInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None


class DiarizationResult(BaseModel):
    """
    Domain-level diarization payload used by the rest of the system.
    NOTE: `segments` is intentionally typed as `list[Any]` so that it can
    hold your project’s `DiarizedSegment` instances from `models.py` without
    creating an import cycle. You can tighten this typing later to
    `list[DiarizedSegment]` and import under TYPE_CHECKING if desired.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    segments: list[Any]
    num_speakers: int | None = None
    metadata: dict[str, Any] | None = None


# -----------------------------
# Discriminated union response envelope
# -----------------------------
class _BaseResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    job_id: str | None = None
    started_at: float | None = None  # epoch seconds, optional
    ended_at: float | None = None
    raw: dict[str, Any] | None = None  # optional raw server payload for debugging


class DiarizationSucceeded(_BaseResponse):
    status: Literal["succeeded"]
    result: DiarizationResult


class DiarizationFailed(_BaseResponse):
    status: Literal["failed"]
    error: ErrorInfo


class DiarizationPending(_BaseResponse):
    status: Literal["pending"]


class DiarizationRunning(_BaseResponse):
    status: Literal["running"]


# Pydantic v2-discriminated union (by `status` field)
DiarizationResponse = Annotated[
    Union[
        DiarizationSucceeded,
        DiarizationFailed,
        DiarizationPending,
        DiarizationRunning,
    ],
    Field(discriminator="status"),
]

__all__ = [
    # Transport layer
    "PollOutcome",
    "DiarizationParams",
    "StartDiarizationResponse",
    "JobStatus",
    "JobStatusResponse",
    # Domain layer
    "ErrorCode",
    "ErrorInfo",
    "DiarizationResult",
    # Envelope
    "DiarizationSucceeded",
    "DiarizationFailed",
    "DiarizationPending",
    "DiarizationRunning",
    "DiarizationResponse",
]
