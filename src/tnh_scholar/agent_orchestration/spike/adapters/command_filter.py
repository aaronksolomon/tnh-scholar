"""Command filter adapter for the spike."""

from __future__ import annotations

import re
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import CommandFilterDecision
from tnh_scholar.agent_orchestration.spike.protocols import CommandFilterProtocol


@dataclass(frozen=True)
class RegexCommandFilter(CommandFilterProtocol):
    """Regex-based command filter."""

    patterns: tuple[str, ...]

    def evaluate(self, command: str) -> CommandFilterDecision:
        match = self._match_pattern(command)
        if match is None:
            return CommandFilterDecision(command=command, blocked=False)
        return CommandFilterDecision(command=command, blocked=True, matched_pattern=match)

    def _match_pattern(self, command: str) -> str | None:
        return next(
            (pattern for pattern in self.patterns if re.search(pattern, command)),
            None,
        )
