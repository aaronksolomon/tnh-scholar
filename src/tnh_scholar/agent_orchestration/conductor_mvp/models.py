"""Typed domain models for conductor MVP workflow execution."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Opcode(str, Enum):
    """Kernel opcode names."""

    run_agent = "RUN_AGENT"
    run_validation = "RUN_VALIDATION"
    evaluate = "EVALUATE"
    gate = "GATE"
    rollback = "ROLLBACK"
    stop = "STOP"


class MechanicalOutcome(str, Enum):
    """Mechanical execution outcomes."""

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
    """Human gate outcomes as provenance events."""

    gate_approved = "gate_approved"
    gate_rejected = "gate_rejected"
    gate_timed_out = "gate_timed_out"


class RouteRule(BaseModel):
    """Mapping from an outcome key to a next step target."""

    outcome: str
    target: str


class WorkflowDefaults(BaseModel):
    """Workflow-level optional defaults."""

    artifacts_dir: Path | None = None
    component_kind: str | None = None
    eval_profile: str | None = None


class BaseStep(BaseModel):
    """Common step shape."""

    id: str
    opcode: Opcode
    routes: list[RouteRule] = Field(default_factory=list)


class RunAgentStep(BaseStep):
    """Step invoking an external agent runner."""

    opcode: Literal[Opcode.run_agent] = Opcode.run_agent
    agent: str
    prompt: str
    inputs: list[str] = Field(default_factory=list)
    policy: str | None = None


class BuiltinValidatorSpec(BaseModel):
    """Builtin validator reference resolved by a provider."""

    kind: Literal["builtin"] = "builtin"
    name: str


class ScriptValidatorSpec(BaseModel):
    """Script validator declaration."""

    kind: Literal["script"] = "script"
    id: str
    entrypoint: Path
    args: list[str] = Field(default_factory=list)
    cwd: Path | None = None
    artifacts: list[str] = Field(default_factory=list)
    timeout_seconds: int | None = None
    may_propose_goldens: bool = False


ValidatorSpec = Annotated[
    BuiltinValidatorSpec | ScriptValidatorSpec,
    Field(discriminator="kind"),
]


class RunValidationStep(BaseStep):
    """Step running deterministic validators."""

    opcode: Literal[Opcode.run_validation] = Opcode.run_validation
    run: list[ValidatorSpec]


class EvaluateStep(BaseStep):
    """Step running planner evaluation."""

    opcode: Literal[Opcode.evaluate] = Opcode.evaluate
    prompt: str
    allowed_next_steps: list[str] = Field(default_factory=list)


class GateStep(BaseStep):
    """Human gate step."""

    opcode: Literal[Opcode.gate] = Opcode.gate
    gate: str
    timeout_seconds: int | None = None


class RollbackStep(BaseStep):
    """Deterministic rollback step."""

    opcode: Literal[Opcode.rollback] = Opcode.rollback
    target: str


class StopStep(BaseStep):
    """Terminal step."""

    opcode: Literal[Opcode.stop] = Opcode.stop
    reason: str | None = None
    routes: list[RouteRule] = Field(default_factory=list)


StepDefinition = Annotated[
    RunAgentStep | RunValidationStep | EvaluateStep | GateStep | RollbackStep | StopStep,
    Field(discriminator="opcode"),
]


class WorkflowDefinition(BaseModel):
    """Workflow bytecode source document."""

    workflow_id: str
    version: int
    description: str
    entry_step: str
    defaults: WorkflowDefaults | None = None
    steps: list[StepDefinition]


class PlannerDecision(BaseModel):
    """Structured planner output consumed by EVALUATE."""

    status: PlannerStatus
    next_step: str | None = None
    fix_instructions: str | None = None
    blockers: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


class HarnessReport(BaseModel):
    """Minimal harness report fields used by kernel runtime checks."""

    proposed_goldens: list[str] = Field(default_factory=list)


class ValidationRunResult(BaseModel):
    """Deterministic validator execution result."""

    outcome: MechanicalOutcome
    harness_report: HarnessReport | None = None


class AgentRunResult(BaseModel):
    """Agent step result returned by runner implementations."""

    outcome: MechanicalOutcome


class ArtifactPaths(BaseModel):
    """MVP artifact outputs per run."""

    run_dir: Path
    run_log: Path
    final_state: Path


class KernelRunResult(BaseModel):
    """Kernel execution summary."""

    run_id: str
    workflow_id: str
    started_at: datetime
    ended_at: datetime
    status: MechanicalOutcome
    last_step_id: str
    artifact_paths: ArtifactPaths
