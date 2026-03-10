"""Protocols for the validation subsystem."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.execution.models import ExecutionRequest
from tnh_scholar.agent_orchestration.validation.models import (
    ValidationResult,
    ValidationSpec,
    ValidationStepRequest,
)


class ValidatorResolverProtocol(Protocol):
    """Resolve validation specs into execution requests."""

    def resolve(self, spec: ValidationSpec, run_directory: Path) -> ExecutionRequest:
        """Resolve one validator into a trusted execution request."""


class ValidationServiceProtocol(Protocol):
    """Execute a validation step."""

    def run(self, request: ValidationStepRequest) -> ValidationResult:
        """Execute validators and return normalized result."""
