"""Versioned runtime events and independent terminal decisions."""

from datetime import UTC, datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RunStage(str, Enum):
    """Observable command boundaries, not provider-internal milestones."""

    STARTING = "starting"
    PREPARING_RUN = "preparing_run"
    GENERATING = "generating"
    EMITTING_OUTPUT = "emitting_output"


class EventType(str, Enum):
    """Kinds of status records."""

    STAGE_STARTED = "stage_started"
    HEARTBEAT = "heartbeat"
    TERMINAL = "terminal"


class RunOutcome(str, Enum):
    """Terminal command outcomes."""

    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatusMetadata(BaseModel):
    """Immutable identity available before preparing the run."""

    model_config = ConfigDict(frozen=True)
    trace_id: str
    prompt_key: str
    input_file_name: str
    output_file_name: str | None = None
    api_mode: bool = False
    quiet: bool = False
    requested_model: str | None = None


class RunFailure(BaseModel):
    """A failure's origin, independent of subsequent diagnostic rendering."""

    model_config = ConfigDict(frozen=True)
    origin_stage: RunStage
    code: str = Field(min_length=1, max_length=128)


class TerminalDecision(BaseModel):
    """Primary task result plus an optional secondary reporting failure."""

    model_config = ConfigDict(frozen=True)
    outcome: RunOutcome = RunOutcome.COMPLETED
    exit_code: int = Field(default=0, ge=0)
    failure: RunFailure | None = None
    reporting_failure: RunFailure | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        """Prevent successful failures and terminal decisions without causes."""
        if self.outcome is RunOutcome.COMPLETED:
            if self.failure or self.reporting_failure or self.exit_code != 0:
                raise ValueError("Completed decisions cannot contain failures or a nonzero exit")
        elif self.failure is None or self.exit_code == 0:
            raise ValueError("Failed/cancelled decisions require a cause and nonzero exit")
        return self


class RunStatusEvent(BaseModel):
    """One JSONL record; additive fields are ignored by V1 readers."""

    model_config = ConfigDict(frozen=True)
    schema_version: str = Field(default="1.0", pattern=r"^1\.\d+$")
    sequence: int = Field(gt=0, strict=True)
    event_type: EventType
    stage: RunStage
    timestamp: datetime
    elapsed_ms: int = Field(ge=0)
    stage_elapsed_ms: int = Field(ge=0)
    metadata: RunStatusMetadata
    message: str = Field(max_length=256)
    outcome: RunOutcome | None = None
    exit_code: int | None = None
    failure: RunFailure | None = None
    reporting_failure: RunFailure | None = None
    model: str | None = None
    provider: str | None = None

    @model_validator(mode="after")
    def validate_terminal(self) -> Self:
        """Validate timing and the terminal-only payload."""
        if self.timestamp.utcoffset() != UTC.utcoffset(None):
            raise ValueError("Status timestamps must be UTC")
        if self.stage_elapsed_ms > self.elapsed_ms:
            raise ValueError("Stage duration cannot exceed invocation duration")
        fields = (self.outcome, self.exit_code, self.failure, self.reporting_failure)
        if self.event_type is not EventType.TERMINAL:
            if any(value is not None for value in fields):
                raise ValueError("Only terminal events contain outcome fields")
            return self
        if self.outcome is None or self.exit_code is None:
            raise ValueError("Terminal events require an outcome and exit code")
        TerminalDecision(
            outcome=self.outcome,
            exit_code=self.exit_code,
            failure=self.failure,
            reporting_failure=self.reporting_failure,
        )
        return self
