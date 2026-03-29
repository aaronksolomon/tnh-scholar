"""Typed models for maintained runners."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.kernel.enums import AgentFamily, RunnerTermination


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
