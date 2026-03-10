"""Workflow graph helpers."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import (
    STOP_STEP_ID,
    Opcode,
    StepDefinition,
    WorkflowDefinition,
)


@dataclass(frozen=True)
class WorkflowCatalog:
    """Indexed workflow helper."""

    workflow: WorkflowDefinition
    step_index: dict[str, StepDefinition] | None = None

    def __post_init__(self) -> None:
        index = {step.id: step for step in self.workflow.steps}
        object.__setattr__(self, "step_index", index)

    def find_step(self, step_id: str) -> StepDefinition:
        """Find a step or raise."""
        if self.step_index is None or step_id not in self.step_index:
            raise WorkflowValidationError(f"Unknown step target: {step_id}")
        return self.step_index[step_id]

    def has_step_type(self, opcode: Opcode) -> bool:
        """Return whether workflow contains an opcode."""
        return any(step.opcode == opcode for step in self.workflow.steps)

    def has_step_id(self, step_id: str) -> bool:
        """Return whether workflow contains a step id."""
        return self.step_index is not None and step_id in self.step_index

    def transition_targets(self, step: StepDefinition) -> list[str]:
        """Return declared transition targets."""
        return [route.target for route in step.routes]

    def route_target(self, step: StepDefinition, outcome_key: str, *, context: str) -> str:
        """Return one transition target."""
        for route in step.routes:
            if route.outcome == outcome_key:
                return route.target
        raise WorkflowValidationError(f"{context} '{outcome_key}' in step: {step.id}")

    def reachable_step_ids(self, start_id: str) -> set[str]:
        """Return the set of reachable step ids from one step."""
        queue: deque[str] = deque([start_id])
        visited: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            step = self.find_step(current)
            for target in self.transition_targets(step):
                if target == STOP_STEP_ID and self.has_step_id(STOP_STEP_ID):
                    queue.append(STOP_STEP_ID)
                    continue
                if target != STOP_STEP_ID:
                    queue.append(target)
        return visited

    def path_contains_gate(self, start_id: str) -> bool:
        """Return whether any reachable path contains a gate step."""
        return any(
            self.find_step(step_id).opcode == Opcode.gate for step_id in self.reachable_step_ids(start_id)
        )
