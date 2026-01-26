"""Parse structured output from Codex."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from tnh_scholar.agent_orchestration.codex_harness.models import CodexStructuredOutput


@dataclass(frozen=True)
class CodexOutputParser:
    """Parse JSON output into structured domain models."""

    def parse(self, text: str) -> CodexStructuredOutput:
        """Parse the JSON response text into a CodexStructuredOutput."""
        try:
            return CodexStructuredOutput.model_validate_json(text)
        except ValidationError as exc:
            raise ValueError("Codex output did not match expected schema") from exc
