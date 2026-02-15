"""Adapter for loading workflow YAML into typed models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tnh_scholar.agent_orchestration.conductor_mvp.models import (
    BuiltinValidatorSpec,
    RouteRule,
    ScriptValidatorSpec,
    WorkflowDefinition,
)


@dataclass(frozen=True)
class YamlWorkflowLoader:
    """Load workflow documents from YAML files."""

    def load(self, path: Path) -> WorkflowDefinition:
        """Parse and normalize a workflow definition."""
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        normalized = self._normalize_workflow(payload)
        return WorkflowDefinition.model_validate(normalized)

    def _normalize_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        steps = payload.get("steps", [])
        return {
            **payload,
            "steps": [self._normalize_step(step) for step in steps],
        }

    def _normalize_step(self, raw_step: dict[str, Any]) -> dict[str, Any]:
        routes = self._normalize_routes(raw_step.get("routes"))
        run_values = self._normalize_run_values(raw_step.get("run"))
        if run_values is None:
            return {**raw_step, "routes": routes}
        return {**raw_step, "routes": routes, "run": run_values}

    def _normalize_routes(self, raw_routes: Any) -> list[dict[str, str]]:
        if isinstance(raw_routes, list):
            return [RouteRule.model_validate(item).model_dump() for item in raw_routes]
        if isinstance(raw_routes, dict):
            return [RouteRule(outcome=key, target=value).model_dump() for key, value in raw_routes.items()]
        return []

    def _normalize_run_values(self, raw_run: Any) -> list[dict[str, Any]] | None:
        if raw_run is None:
            return None
        normalized: list[dict[str, Any]] = []
        for value in raw_run:
            if isinstance(value, str):
                normalized.append(BuiltinValidatorSpec(name=value).model_dump())
                continue
            if isinstance(value, dict):
                kind = value.get("kind")
                if kind == "script":
                    normalized.append(ScriptValidatorSpec.model_validate(value).model_dump())
                    continue
                if kind == "builtin":
                    normalized.append(BuiltinValidatorSpec.model_validate(value).model_dump())
                    continue
        return normalized
