"""Protocols for maintained runners."""

from __future__ import annotations

from typing import Protocol

from tnh_scholar.agent_orchestration.runners.models import (
    AdapterCapabilities,
    RunnerResult,
    RunnerTaskRequest,
)
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily


class RunnerAdapterProtocol(Protocol):
    """Execute requests for one concrete maintained runner family."""

    def agent_family(self) -> AgentFamily:
        """Return the family served by this adapter."""

    def capabilities(self) -> AdapterCapabilities:
        """Declare the native controls supported by this adapter."""

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        """Execute a request for this family."""


class RunnerServiceProtocol(Protocol):
    """Execute a maintained runner request."""

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        """Execute a runner request."""
