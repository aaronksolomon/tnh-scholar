"""Typed models for maintained runners."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class AgentFamily(str, Enum):
    """Supported maintained runner families."""

    claude_cli = "claude_cli"
    codex_cli = "codex_cli"


class RunnerTermination(str, Enum):
    """Mechanical outcomes exposed to the kernel."""

    completed = "completed"
    error = "error"
    killed_timeout = "killed_timeout"
    killed_idle = "killed_idle"
    killed_policy = "killed_policy"


class PromptInteractionPolicy(BaseModel):
    """Prompt-handling policy for maintained runners."""

    auto_approve: bool = False


class RunnerTaskRequest(BaseModel):
    """Kernel-facing runner task request."""

    agent_family: AgentFamily
    rendered_task_text: str
    working_directory: Path
    prompt_reference: str | None = None
    prompt_interaction_policy: PromptInteractionPolicy = Field(
        default_factory=PromptInteractionPolicy
    )


class RunnerResult(BaseModel):
    """Kernel-facing runner result."""

    termination: RunnerTermination
    transcript_path: Path | None = None
    final_response_path: Path | None = None
