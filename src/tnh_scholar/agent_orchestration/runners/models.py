"""Typed models for maintained runners."""

from __future__ import annotations

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


class RunnerResult(BaseModel):
    """Kernel-facing runner result."""

    termination: RunnerTermination
    transcript_path: Path | None = None
    final_response_path: Path | None = None
