"""Protocols for conductor MVP collaborators."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.conductor_mvp.models import (
    AgentRunResult,
    BuiltinValidatorSpec,
    EvaluateStep,
    GateOutcome,
    GateStep,
    PlannerDecision,
    RollbackStep,
    RunAgentStep,
    RunValidationStep,
    ValidationRunResult,
)


class ClockProtocol(Protocol):
    """Abstraction for current time."""

    def now(self) -> datetime:
        """Return current timestamp."""


class RunIdGeneratorProtocol(Protocol):
    """Abstraction for generating run identifiers."""

    def next_id(self, now: datetime) -> str:
        """Generate next run identifier."""


class ArtifactStoreProtocol(Protocol):
    """Persist run artifacts."""

    def ensure_run_dir(self, run_id: str, root_dir: Path) -> Path:
        """Create and return run directory."""

    def write_text(self, path: Path, content: str) -> None:
        """Write text artifact."""


class AgentRunnerProtocol(Protocol):
    """Execute RUN_AGENT steps."""

    def run(self, step: RunAgentStep, run_dir: Path) -> AgentRunResult:
        """Execute an agent step."""


class BuiltinValidatorResolverProtocol(Protocol):
    """Resolve builtin validator names to command lines."""

    def resolve(self, validator: BuiltinValidatorSpec) -> list[str]:
        """Resolve builtin validator command."""


class ValidationRunnerProtocol(Protocol):
    """Execute RUN_VALIDATION steps."""

    def run(self, step: RunValidationStep, run_dir: Path) -> ValidationRunResult:
        """Execute validation step."""


class PlannerEvaluatorProtocol(Protocol):
    """Execute EVALUATE steps."""

    def evaluate(self, step: EvaluateStep, run_dir: Path) -> PlannerDecision:
        """Return structured planner decision."""


class GateApproverProtocol(Protocol):
    """Resolve human gate outcomes."""

    def decide(self, step: GateStep, run_dir: Path) -> GateOutcome:
        """Return gate decision outcome."""


class WorkspaceProtocol(Protocol):
    """Worktree safety and rollback operations."""

    def capture_pre_run(self, run_id: str) -> None:
        """Capture pre-run checkpoint."""

    def rollback(self, step: RollbackStep) -> None:
        """Rollback to requested checkpoint."""
