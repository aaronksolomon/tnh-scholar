"""Typed models for maintained runners."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.execution_policy.models import RequestedExecutionPolicy
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily, RunnerTermination


class RunnerTaskRequest(BaseModel):
    """Kernel-facing runner task request."""

    agent_family: AgentFamily
    rendered_task_text: str
    working_directory: Path
    prompt_reference: str | None = None
    requested_policy: RequestedExecutionPolicy = Field(default_factory=RequestedExecutionPolicy)


class RunnerInvocationMode(str, Enum):
    """Supported runner invocation modes."""

    claude_print = "claude_print"
    codex_exec = "codex_exec"


class RunnerCaptureFormat(str, Enum):
    """Supported normalized capture formats."""

    ndjson = "ndjson"
    text = "text"


class AdapterCapabilities(BaseModel):
    """Native controls that one runner adapter can honor."""

    agent_family: AgentFamily
    supports_workspace_write: bool
    supports_read_only: bool
    supports_structured_event_stream: bool
    supports_final_response_file: bool
    supports_native_approval_controls: bool
    supports_path_constraints: bool = False
    supports_network_controls: bool = False


class RunnerTextArtifact(BaseModel):
    """One normalized text artifact returned by a runner adapter."""

    filename: str
    content: str
    media_type: str


class RunnerInvocationMetadata(BaseModel):
    """Canonical normalized invocation metadata returned by adapters."""

    agent_family: AgentFamily
    invocation_mode: RunnerInvocationMode
    command: tuple[str, ...]
    working_directory: Path
    prompt_reference: str | None = None
    started_at: datetime
    ended_at: datetime
    exit_code: int | None = None
    termination: RunnerTermination
    capture_format: RunnerCaptureFormat


class RunnerResult(BaseModel):
    """Kernel-facing runner result."""

    termination: RunnerTermination
    metadata: RunnerInvocationMetadata | None = None
    transcript: RunnerTextArtifact | None = None
    final_response: RunnerTextArtifact | None = None
