"""Domain models for the Phase 0 protocol layer spike."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class SpikeDefaults:
    """Default values for spike settings and policy."""

    runs_root: Path = Path(".tnh-gen/runs")
    work_branch_prefix: str = "work"
    default_timeout_seconds: int = 600
    default_idle_timeout_seconds: int = 600
    default_transcript_tail_lines: int = 200
    default_heartbeat_interval_seconds: int = 10
    default_output_event_max_chars: int = 2000
    allow_response: str = "y\n"
    block_response: str = "n\n"


class RunEventType(str, Enum):
    run_started = "RUN_STARTED"
    agent_started = "AGENT_STARTED"
    heartbeat = "HEARTBEAT"
    agent_output = "AGENT_OUTPUT"
    workspace_captured_pre = "WORKSPACE_CAPTURED_PRE"
    workspace_captured_post = "WORKSPACE_CAPTURED_POST"
    diff_emitted = "DIFF_EMITTED"
    run_blocked = "RUN_BLOCKED"
    run_completed = "RUN_COMPLETED"


class TerminationReason(str, Enum):
    completed = "completed"
    idle_timeout = "idle_timeout"
    interactive_prompt_detected = "interactive_prompt_detected"
    command_blocked = "command_blocked"
    nonzero_exit = "nonzero_exit"
    wall_clock_timeout = "wall_clock_timeout"
    killed = "killed"


class SpikeSettings(BaseSettings):
    """Environment-driven settings for the spike."""

    model_config = SettingsConfigDict(extra="ignore")

    runs_root: Path = Field(default_factory=lambda: SpikeDefaults().runs_root)
    work_branch_prefix: str = Field(default_factory=lambda: SpikeDefaults().work_branch_prefix)
    sandbox_root: Path | None = None

    @classmethod
    def from_env(cls) -> "SpikeSettings":
        """Create settings from environment."""
        return cls()


class SpikeConfig(BaseModel):
    """Construction-time configuration for the spike service."""

    runs_root: Path
    work_branch_prefix: str
    sandbox_root: Path | None = None


class SpikePolicy(BaseModel):
    """Behavioral policies for the spike."""

    blocked_command_patterns: list[str] = Field(default_factory=list)
    interactive_prompt_patterns: list[str] = Field(default_factory=list)
    command_capture_patterns: list[str] = Field(default_factory=list)
    allow_response: str = Field(default_factory=lambda: SpikeDefaults().allow_response)
    block_response: str = Field(default_factory=lambda: SpikeDefaults().block_response)
    output_event_max_chars: int = Field(default_factory=lambda: SpikeDefaults().default_output_event_max_chars)
    cleanup_on_failure: bool = True


class SpikeParams(BaseModel):
    """Per-run parameters for the spike."""

    agent: str
    task: str | None = None
    prompt_id: str | None = None
    response_path: Path | None = None
    timeout_seconds: int = Field(default_factory=lambda: SpikeDefaults().default_timeout_seconds)
    idle_timeout_seconds: int = Field(default_factory=lambda: SpikeDefaults().default_idle_timeout_seconds)
    transcript_tail_lines: int = Field(default_factory=lambda: SpikeDefaults().default_transcript_tail_lines)
    heartbeat_interval_seconds: int = Field(
        default_factory=lambda: SpikeDefaults().default_heartbeat_interval_seconds
    )
    work_branch: str | None = None


class GitStatusSnapshot(BaseModel):
    """Snapshot of git status for a workspace."""

    branch: str
    is_clean: bool
    staged: int
    unstaged: int
    lines: list[str] = Field(default_factory=list)


class CommandFilterDecision(BaseModel):
    """Result of applying the command filter."""

    command: str
    blocked: bool
    matched_pattern: str | None = None


class PromptAction(str, Enum):
    ignore = "ignore"
    allow = "allow"
    block = "block"


class CommandPromptMatch(BaseModel):
    """Parsed command confirmation prompt."""

    command: str
    prompt_text: str


class PromptHandlingOutcome(BaseModel):
    """Decision for a command confirmation prompt."""

    action: PromptAction
    decision: CommandFilterDecision | None = None
    response_text: str | None = None


class AgentRunResult(BaseModel):
    """Outcome of an agent execution."""

    exit_code: int | None = None
    termination_reason: TerminationReason
    transcript_raw: bytes
    transcript_text: str
    stdout_text: str | None = None
    stderr_text: str | None = None
    command_decision: CommandFilterDecision | None = None


class RunArtifactPaths(BaseModel):
    """Filesystem paths for run artifacts."""

    transcript_raw: Path
    transcript_normalized: Path
    stdout_log: Path
    stderr_log: Path
    response_path: Path
    git_pre: Path
    git_post: Path
    diff_patch: Path
    run_metadata: Path
    events: Path


class RunEvent(BaseModel):
    """Single provenance event entry for the spike."""

    run_id: str
    timestamp: datetime
    event_type: RunEventType
    agent: str | None = None
    work_branch: str | None = None
    artifact_paths: list[Path] = Field(default_factory=list)
    reason: str | None = None
    exit_code: int | None = None
    message: str | None = None


class RunMetadata(BaseModel):
    """Metadata for a spike run."""

    run_id: str
    started_at: datetime
    ended_at: datetime
    agent: str
    task: str | None = None
    prompt_id: str | None = None
    work_branch: str
    exit_code: int | None = None
    termination_reason: TerminationReason
    artifact_paths: RunArtifactPaths
    git_pre_summary: GitStatusSnapshot
    git_post_summary: GitStatusSnapshot


class SpikePreflightError(Exception):
    """Raised when preflight checks fail."""
