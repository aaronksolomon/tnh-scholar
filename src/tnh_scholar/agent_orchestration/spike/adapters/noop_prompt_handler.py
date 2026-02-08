"""No-op prompt handler for headless CLI execution."""

from __future__ import annotations

from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import (
    PromptAction,
    PromptHandlingOutcome,
)
from tnh_scholar.agent_orchestration.spike.protocols import PromptHandlerProtocol


@dataclass(frozen=True)
class NoopPromptHandler(PromptHandlerProtocol):
    """Ignore all output as non-interactive in headless runs."""

    def handle_output(self, text: str) -> PromptHandlingOutcome:
        return PromptHandlingOutcome(action=PromptAction.ignore)
