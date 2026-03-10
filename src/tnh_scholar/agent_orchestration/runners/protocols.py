"""Protocols for maintained runners."""

from __future__ import annotations

from typing import Protocol

from tnh_scholar.agent_orchestration.runners.models import RunnerResult, RunnerTaskRequest


class RunnerServiceProtocol(Protocol):
    """Execute a maintained runner request."""

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        """Execute a runner request."""
