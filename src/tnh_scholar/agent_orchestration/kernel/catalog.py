"""Workflow graph helpers."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import Opcode, StepDefinition, WorkflowDefinition


@dataclass(frozen=True)
class WorkflowCatalog:
    """Indexed workflow helper."""

    workflow: WorkflowDefinition

    def find_step(self, step_id: str) -> StepDefinition:
        """Find a step or raise."""
        for step in self.workflow.steps:
            if step.id == step_id:
                return step
        raise WorkflowValidationError(f"Unknown step target: {step_id}")

    def has_step_type(self, opcode: Opcode) -> bool:
        """Return whether workflow contains an opcode."""
        return any(step.opcode == opcode for step in self.workflow.steps)

    def has_step_id(self, step_id: str) -> bool:
        """Return whether workflow contains a step id."""
        return any(step.id == step_id for step in self.workflow.steps)

    def transition_targets(self, step: StepDefinition) -> list[str]:
        """Return declared transition targets."""
        return [route.target for route in step.routes]

    def route_target(self, step: StepDefinition, outcome_key: str, *, context: str) -> str:
        """Return one transition target."""
        for route in step.routes:
            if route.outcome == outcome_key:
                return route.target
        raise WorkflowValidationError(f"{context} '{outcome_key}' in step: {step.id}")
