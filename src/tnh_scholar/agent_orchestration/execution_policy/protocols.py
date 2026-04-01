"""Protocols for maintained execution policy assembly."""

from __future__ import annotations

from typing import Protocol

from tnh_scholar.agent_orchestration.execution_policy.models import (
    ExecutionPolicySettings,
    PolicySummary,
    RequestedExecutionPolicy,
)


class ExecutionPolicyAssemblerProtocol(Protocol):
    """Assemble requested and effective execution policy records."""

    def assemble(
        self,
        *,
        settings: ExecutionPolicySettings,
        workflow_policy_ref: str | None = None,
        step_policy_ref: str | None = None,
        runtime_overrides: RequestedExecutionPolicy | None = None,
    ) -> PolicySummary:
        """Assemble one canonical policy summary."""
