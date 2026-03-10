"""YAML workflow loader for the maintained kernel."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tnh_scholar.agent_orchestration.kernel.errors import WorkflowValidationError
from tnh_scholar.agent_orchestration.kernel.models import RouteRule, WorkflowDefinition
from tnh_scholar.agent_orchestration.validation.models import (
    BuiltinValidationSpec,
    HarnessValidationSpec,
)


@dataclass(frozen=True)
class YamlWorkflowLoader:
    """Load workflow documents from YAML."""

    def load(self, path: Path) -> WorkflowDefinition:
        """Load and normalize one workflow document."""
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        normalized = self._normalize_workflow(payload)
        return WorkflowDefinition.model_validate(normalized)

    def _normalize_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            **payload,
            "steps": [self._normalize_step(step) for step in payload.get("steps", [])],
        }

    def _normalize_step(self, raw_step: dict[str, Any]) -> dict[str, Any]:
        normalized = {**raw_step, "routes": self._normalize_routes(raw_step.get("routes"))}
        if "run" in raw_step:
            normalized["run"] = self._normalize_run_values(raw_step["run"])
        return normalized

    def _normalize_routes(self, raw_routes: Any) -> list[dict[str, str]]:
        if raw_routes is None:
            return []
        if isinstance(raw_routes, list):
            return [RouteRule.model_validate(item).model_dump() for item in raw_routes]
        if isinstance(raw_routes, dict):
            return [RouteRule(outcome=key, target=value).model_dump() for key, value in raw_routes.items()]
        raise WorkflowValidationError(
            f"Invalid routes configuration: expected a list or dict, got {type(raw_routes).__name__}"
        )

    def _normalize_run_values(self, raw_run: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for value in raw_run:
            if isinstance(value, str):
                normalized.append(BuiltinValidationSpec(name=value).model_dump())
                continue
            if not isinstance(value, dict):
                continue
            if value.get("kind") == "harness":
                normalized.append(HarnessValidationSpec.model_validate(value).model_dump())
                continue
            if value.get("kind") == "builtin":
                normalized.append(BuiltinValidationSpec.model_validate(value).model_dump())
                continue
            raise WorkflowValidationError(f"Unsupported validation spec kind: {value.get('kind')}")
        return normalized
