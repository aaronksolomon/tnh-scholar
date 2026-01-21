"""Parse command confirmation prompts from agent output."""

from __future__ import annotations

import re
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import CommandPromptMatch
from tnh_scholar.agent_orchestration.spike.protocols import CommandPromptParserProtocol


@dataclass(frozen=True)
class RegexCommandPromptParser(CommandPromptParserProtocol):
    """Regex-based prompt parser."""

    patterns: tuple[str, ...]

    def parse(self, text: str) -> CommandPromptMatch | None:
        match = self._find_match(text)
        if match is None:
            return None
        command = match.group("command").strip()
        return CommandPromptMatch(command=command, prompt_text=text)

    def _find_match(self, text: str) -> re.Match[str] | None:
        for pattern in self.patterns:
            result = re.search(pattern, text, re.IGNORECASE)
            if result is not None:
                return result
        return None
