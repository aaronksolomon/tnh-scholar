"""Delegating maintained runner service."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.runners.models import RunnerResult, RunnerTaskRequest
from tnh_scholar.agent_orchestration.runners.protocols import (
    RunnerAdapterProtocol,
    RunnerServiceProtocol,
)
from tnh_scholar.agent_orchestration.shared_enums import AgentFamily


@dataclass(frozen=True)
class DelegatingRunnerService(RunnerServiceProtocol):
    """Dispatch runner requests to the matching maintained adapter."""

    adapters: tuple[RunnerAdapterProtocol, ...]

    def run(self, request: RunnerTaskRequest) -> RunnerResult:
        """Execute one runner request using the matching adapter."""
        adapter = self._find_adapter(request.agent_family)
        return adapter.run(request)

    def _find_adapter(self, agent_family: AgentFamily) -> RunnerAdapterProtocol:
        for adapter in self.adapters:
            if adapter.agent_family() == agent_family:
                return adapter
        raise ValueError(f"No maintained runner adapter for {agent_family.value}")
