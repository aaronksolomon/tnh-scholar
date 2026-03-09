"""Protocols required by the maintained kernel."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.kernel.models import (
    EvaluateStep,
    GateOutcome,
    GateStep,
    PlannerDecision,
    RollbackStep,
)
from tnh_scholar.agent_orchestration.run_artifacts.models import RunArtifactPaths
from tnh_scholar.agent_orchestration.run_artifacts.protocols import RunArtifactStoreProtocol
from tnh_scholar.agent_orchestration.runners.models import RunnerResult, RunnerTaskRequest
from tnh_scholar.agent_orchestration.runners.protocols import RunnerServiceProtocol
from tnh_scholar.agent_orchestration.validation.models import (
    ValidationResult,
    ValidationStepRequest,
)
from tnh_scholar.agent_orchestration.validation.protocols import ValidationServiceProtocol
from tnh_scholar.agent_orchestration.workspace.protocols import WorkspaceServiceProtocol


class ClockProtocol(Protocol):
    """Clock abstraction."""

    def now(self) -> datetime:
        """Return current timestamp."""


class RunIdGeneratorProtocol(Protocol):
    """Run id abstraction."""

    def next_id(self, now: datetime) -> str:
        """Generate next run id."""


class PlannerEvaluatorProtocol(Protocol):
    """Planner evaluator contract."""

    def evaluate(self, step: EvaluateStep, run_directory: Path) -> PlannerDecision:
        """Evaluate one step."""


class GateApproverProtocol(Protocol):
    """Gate approver contract."""

    def decide(self, step: GateStep, run_directory: Path) -> GateOutcome:
        """Resolve gate outcome."""


__all__ = [
    "ClockProtocol",
    "GateApproverProtocol",
    "PlannerEvaluatorProtocol",
    "RunArtifactPaths",
    "RunArtifactStoreProtocol",
    "RunIdGeneratorProtocol",
    "RunnerResult",
    "RunnerServiceProtocol",
    "RunnerTaskRequest",
    "RollbackStep",
    "ValidationResult",
    "ValidationServiceProtocol",
    "ValidationStepRequest",
    "WorkspaceServiceProtocol",
]
