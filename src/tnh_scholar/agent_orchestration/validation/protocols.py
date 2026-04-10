"""Protocols for the validation subsystem."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from tnh_scholar.agent_orchestration.execution.models import ExecutionRequest
from tnh_scholar.agent_orchestration.validation.models import (
    BuiltinValidationSpec,
    HarnessBackendRequest,
    HarnessBackendResult,
    HarnessValidationSpec,
    ValidationResult,
    ValidationStepRequest,
)


class ValidatorResolverProtocol(Protocol):
    """Resolve builtin validators into execution requests."""

    def resolve(self, spec: BuiltinValidationSpec, working_directory: Path) -> ExecutionRequest:
        """Resolve one builtin validator into a trusted execution request."""


class HarnessBackendResolverProtocol(Protocol):
    """Resolve harness validators into backend requests."""

    def resolve(self, spec: HarnessValidationSpec, working_directory: Path) -> HarnessBackendRequest:
        """Resolve one harness validator into a trusted backend request."""


class HarnessBackendProtocol(Protocol):
    """Execute one normalized harness backend request."""

    def run(self, request: HarnessBackendRequest) -> HarnessBackendResult:
        """Execute one harness request and normalize outputs."""


class ValidationServiceProtocol(Protocol):
    """Execute a validation step."""

    def run(self, request: ValidationStepRequest) -> ValidationResult:
        """Execute validators and return normalized result."""
