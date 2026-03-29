"""Static workflow validation."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.kernel.catalog import WorkflowCatalog
from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import (
    EvaluateStep,
    Opcode,
    PlannerStatus,
    RunValidationStep,
    StopStep,
    WorkflowDefinition,
)
from tnh_scholar.agent_orchestration.validation.models import HarnessValidationSpec


@dataclass(frozen=True)
class WorkflowValidator:
    """Validate static workflow invariants."""

    def validate(self, workflow: WorkflowDefinition) -> None:
        catalog = WorkflowCatalog(workflow=workflow)
        self._validate_entry_step(workflow, catalog)
        self._validate_unique_step_ids(workflow)
        self._validate_routes(workflow, catalog)
        self._validate_evaluate_constraints(workflow, catalog)
        self._validate_reachability(workflow, catalog)
        self._validate_weak_golden_gate_requirement(workflow, catalog)

    def _validate_entry_step(self, workflow: WorkflowDefinition, catalog: WorkflowCatalog) -> None:
        self._validate_target(catalog, workflow.entry_step)

    def _validate_unique_step_ids(self, workflow: WorkflowDefinition) -> None:
        seen: set[str] = set()
        for step in workflow.steps:
            if step.id in seen:
                raise WorkflowValidationError(f"Duplicate step id: {step.id}")
            seen.add(step.id)

    def _validate_routes(self, workflow: WorkflowDefinition, catalog: WorkflowCatalog) -> None:
        for step in workflow.steps:
            if isinstance(step, StopStep):
                continue
            if not step.routes:
                raise WorkflowValidationError(f"Step requires routes: {step.id}")
            for target in catalog.transition_targets(step):
                self._validate_target(catalog, target)

    def _validate_evaluate_constraints(
        self,
        workflow: WorkflowDefinition,
        catalog: WorkflowCatalog,
    ) -> None:
        for step in workflow.steps:
            if not isinstance(step, EvaluateStep):
                continue
            self._validate_evaluate_allowed_next_steps(step, catalog)
            self._validate_evaluate_status_coverage(step)
            self._validate_special_status_route(step, PlannerStatus.unsafe, Opcode.rollback, catalog)
            self._validate_special_status_route(step, PlannerStatus.needs_human, Opcode.gate, catalog)

    def _validate_evaluate_allowed_next_steps(
        self,
        step: EvaluateStep,
        catalog: WorkflowCatalog,
    ) -> None:
        if not step.allowed_next_steps:
            raise WorkflowValidationError(f"EVALUATE missing allowed_next_steps: {step.id}")
        for target in step.allowed_next_steps:
            self._validate_target(catalog, target)

    def _validate_evaluate_status_coverage(self, step: EvaluateStep) -> None:
        route_values = [route.outcome for route in step.routes]
        for value in [status.value for status in PlannerStatus]:
            if value not in route_values:
                raise WorkflowValidationError(f"EVALUATE route missing '{value}' in {step.id}")

    def _validate_special_status_route(
        self,
        step: EvaluateStep,
        status: PlannerStatus,
        expected_opcode: Opcode,
        catalog: WorkflowCatalog,
    ) -> None:
        target = catalog.route_target(step, status.value, context="Route missing")
        if target == Opcode.stop.value:
            return
        if target not in step.allowed_next_steps:
            raise WorkflowValidationError(f"Invalid {status.value} route in {step.id}: {target}")
        target_step = catalog.find_step(target)
        if target_step.opcode != expected_opcode:
            raise WorkflowValidationError(
                f"{status.value} route in {step.id} must target {expected_opcode.value}: {target}"
            )

    def _validate_reachability(self, workflow: WorkflowDefinition, catalog: WorkflowCatalog) -> None:
        visited = catalog.reachable_step_ids(workflow.entry_step)
        for step in workflow.steps:
            if step.id not in visited:
                raise WorkflowValidationError(f"Unreachable step: {step.id}")

    def _validate_weak_golden_gate_requirement(
        self,
        workflow: WorkflowDefinition,
        catalog: WorkflowCatalog,
    ) -> None:
        if not self._may_propose_goldens(workflow):
            return
        if not catalog.has_step_type(Opcode.gate):
            raise WorkflowValidationError("Generative harness flow requires a reachable GATE step.")
        for step in workflow.steps:
            if isinstance(step, EvaluateStep) and catalog.path_contains_gate(step.id):
                return
        raise WorkflowValidationError("No reachable GATE from evaluation path for golden proposals.")

    def _may_propose_goldens(self, workflow: WorkflowDefinition) -> bool:
        for step in workflow.steps:
            if not isinstance(step, RunValidationStep):
                continue
            for validator in step.run:
                if isinstance(validator, HarnessValidationSpec) and validator.may_propose_goldens:
                    return True
        return False

    def _validate_target(self, catalog: WorkflowCatalog, target: str) -> None:
        if target == Opcode.stop.value:
            return
        if not catalog.has_step_id(target):
            raise WorkflowValidationError(f"Missing step id: {target}")
