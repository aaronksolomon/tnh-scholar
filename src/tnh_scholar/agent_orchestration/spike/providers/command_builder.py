"""Command builder for agent invocation."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import SpikeParams
from tnh_scholar.agent_orchestration.spike.protocols import AgentCommandBuilderProtocol


@dataclass(frozen=True)
class AgentCommandBuilder(AgentCommandBuilderProtocol):
    """Build commands for supported agents."""

    def build(self, params: SpikeParams) -> list[str]:
        if params.agent == "claude-code":
            return self._claude_command(params)
        if params.agent == "codex":
            return self._codex_command(params)
        raise ValueError(f"Unsupported agent: {params.agent}")

    def _claude_command(self, params: SpikeParams) -> list[str]:
        task = self._require_task(params)
        return ["claude", "--print", task]

    def _codex_command(self, params: SpikeParams) -> list[str]:
        raise NotImplementedError("codex CLI support is not implemented for the spike")

    def _require_task(self, params: SpikeParams) -> str:
        if params.task is None or not params.task.strip():
            raise ValueError("task is required for the spike runner")
        return params.task
