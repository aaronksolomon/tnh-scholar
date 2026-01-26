"""Tool registry for Codex harness."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.codex_harness.protocols import ToolExecutorProtocol
from tnh_scholar.agent_orchestration.codex_harness.tools import ToolCall, ToolDefinition, ToolSchemaFactory, ToolResult


@dataclass(frozen=True)
class CodexToolRegistry:
    """Register tool definitions and execute tool calls."""

    schema_factory: ToolSchemaFactory
    executor: ToolExecutorProtocol

    def definitions(self) -> list[ToolDefinition]:
        return self.schema_factory.all_definitions()

    def execute(self, call: ToolCall) -> ToolResult:
        return self.executor.execute(call)
