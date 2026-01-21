"""Handle confirmation prompts in agent output."""

from __future__ import annotations

import re
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import (
    PromptAction,
    PromptHandlingOutcome,
)
from tnh_scholar.agent_orchestration.spike.protocols import (
    CommandFilterProtocol,
    CommandPromptParserProtocol,
    PromptHandlerProtocol,
)


@dataclass(frozen=True)
class RegexPromptHandler(PromptHandlerProtocol):
    """Handle command confirmation prompts using regex parsing."""

    parser: CommandPromptParserProtocol
    command_filter: CommandFilterProtocol
    interactive_patterns: tuple[str, ...]
    allow_response: str
    block_response: str

    def handle_output(self, text: str) -> PromptHandlingOutcome:
        command_match = self.parser.parse(text)
        if command_match is not None:
            return self._handle_command_prompt(command_match.command)
        if self._matches_interactive_prompt(text):
            return PromptHandlingOutcome(action=PromptAction.block)
        return PromptHandlingOutcome(action=PromptAction.ignore)

    def _handle_command_prompt(self, command: str) -> PromptHandlingOutcome:
        decision = self.command_filter.evaluate(command)
        if decision.blocked:
            return PromptHandlingOutcome(
                action=PromptAction.block,
                decision=decision,
                response_text=self.block_response,
            )
        return PromptHandlingOutcome(
            action=PromptAction.allow,
            decision=decision,
            response_text=self.allow_response,
        )

    def _matches_interactive_prompt(self, text: str) -> bool:
        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in self.interactive_patterns
        )
