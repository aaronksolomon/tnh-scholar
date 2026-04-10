"""Protocols for the execution subsystem."""

from __future__ import annotations

from typing import Protocol

from tnh_scholar.agent_orchestration.execution.models import ExecutionRequest, ExecutionResult


class ExecutionServiceProtocol(Protocol):
    """Execute one trusted execution request."""

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute one trusted request and return the normalized result."""
