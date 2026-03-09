"""Typed models for the maintained kernel subsystem."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.validation.models import ValidationSpec


class Opcode(str, Enum):
    """Kernel opcode names."""

    run_agent = "RUN_AGENT"
    run_validation = "RUN_VALIDATION"
    evaluate = "EVALUATE"
    gate = "GATE"
    rollback = "ROLLBACK"
    stop = "STOP"


class MechanicalOutcome(str, Enum):
    """Mechanical outcomes used for kernel routing."""

    completed = "completed"
    error = "error"
    killed_timeout = "killed_timeout"
    killed_idle = "killed_idle"
    killed_policy = "killed_policy"


class PlannerStatus(str, Enum):
    """Semantic planner statuses."""

    success = "success"
    partial = "partial"
    blocked = "blocked"
    unsafe = "unsafe"
    needs_human = "needs_human"


class GateOutcome(str, Enum):
    """Human gate outcomes."""

    gate_approved = "gate_approved"
    gate_rejected = "gate_rejected"
    gate_timed_out = "gate_timed_out"


class RouteRule(BaseModel):
    """Outcome to target mapping."""

    outcome: str
    target: str


class WorkflowDefaults(BaseModel):
    """Workflow defaults block."""

    artifacts_dir: Path | None = None
    component_kind: str | None = None
    eval_profile: str | None = None


class BaseStep(BaseModel):
    """Common step shape."""

    id: str
    opcode: Opcode
    routes: list[RouteRule] = Field(default_factory=list)


class RunAgentStep(BaseStep):
    """RUN_AGENT step."""

    opcode: Literal[Opcode.run_agent] = Opcode.run_agent
    agent: str
    prompt: str
    inputs: list[str] = Field(default_factory=list)
    policy: str | None = None


class RunValidationStep(BaseStep):
    """RUN_VALIDATION step."""

    opcode: Literal[Opcode.run_validation] = Opcode.run_validation
    run: list[ValidationSpec]


class EvaluateStep(BaseStep):
    """EVALUATE step."""

    opcode: Literal[Opcode.evaluate] = Opcode.evaluate
    prompt: str
    allowed_next_steps: list[str] = Field(default_factory=list)


class GateStep(BaseStep):
    """GATE step."""

    opcode: Literal[Opcode.gate] = Opcode.gate
    gate: str
    timeout_seconds: int | None = None


class RollbackStep(BaseStep):
    """ROLLBACK step."""

    opcode: Literal[Opcode.rollback] = Opcode.rollback
    target: str


class StopStep(BaseStep):
    """STOP step."""

    opcode: Literal[Opcode.stop] = Opcode.stop
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
