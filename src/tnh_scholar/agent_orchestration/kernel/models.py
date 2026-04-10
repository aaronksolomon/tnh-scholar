"""Typed models for the maintained kernel subsystem."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.kernel.enums import (
    GateOutcome,
    MechanicalOutcome,
    Opcode,
    PlannerStatus,
)
from tnh_scholar.agent_orchestration.validation.models import ValidationSpec


class RouteRule(BaseModel):
    """Outcome to target mapping."""

    outcome: str
    target: str


class WorkflowDefaults(BaseModel):
    """Workflow defaults block."""

    artifacts_dir: Path | None = None
    component_kind: str | None = None
    eval_profile: str | None = None
    policy: str | None = None


class BaseStep(BaseModel):
    """Common step shape."""

    id: str
    opcode: Opcode
    routes: list[RouteRule] = Field(default_factory=list)


class RunAgentStep(BaseStep):
    """RUN_AGENT step."""

    opcode: Literal["RUN_AGENT"] = "RUN_AGENT"
    agent: str
    prompt: str
    inputs: list[str] = Field(default_factory=list)
    policy: str | None = None


class RunValidationStep(BaseStep):
    """RUN_VALIDATION step."""

    opcode: Literal["RUN_VALIDATION"] = "RUN_VALIDATION"
    run: list[ValidationSpec]
    policy: str | None = None


class EvaluateStep(BaseStep):
    """EVALUATE step."""

    opcode: Literal["EVALUATE"] = "EVALUATE"
    prompt: str
    allowed_next_steps: list[str] = Field(default_factory=list)
    policy: str | None = None


class GateStep(BaseStep):
    """GATE step."""

    opcode: Literal["GATE"] = "GATE"
    gate: str
    timeout_seconds: int | None = None
    policy: str | None = None


class RollbackStep(BaseStep):
    """ROLLBACK step."""

    opcode: Literal["ROLLBACK"] = "ROLLBACK"
    target: str
    policy: str | None = None


class StopStep(BaseStep):
    """STOP step."""

    opcode: Literal["STOP"] = "STOP"
    reason: str | None = None


StepDefinition = Annotated[
    RunAgentStep | RunValidationStep | EvaluateStep | GateStep | RollbackStep | StopStep,
    Field(discriminator="opcode"),
]


class WorkflowDefinition(BaseModel):
    """Workflow document."""

    workflow_id: str
    version: int
    description: str
    entry_step: str
    defaults: WorkflowDefaults | None = None
    steps: list[StepDefinition]


class PlannerDecision(BaseModel):
    """Structured planner output."""

    status: PlannerStatus
    next_step: str | None = None
    fix_instructions: str | None = None
    blockers: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class KernelRunResult(BaseModel):
    """Kernel run summary."""

    run_id: str
    workflow_id: str
    started_at: datetime
    ended_at: datetime
    status: MechanicalOutcome
    last_step_id: str
    run_directory: Path
    metadata_path: Path
    final_state_path: Path


__all__ = [
    "BaseStep",
    "EvaluateStep",
    "GateOutcome",
    "GateStep",
    "KernelRunResult",
    "MechanicalOutcome",
    "Opcode",
    "PlannerDecision",
    "PlannerStatus",
    "RollbackStep",
    "RouteRule",
    "RunAgentStep",
    "RunValidationStep",
    "StepDefinition",
    "StopStep",
    "WorkflowDefaults",
    "WorkflowDefinition",
]
