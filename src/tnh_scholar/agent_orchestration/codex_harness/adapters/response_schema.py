"""Response schema builder for Codex structured output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from tnh_scholar.agent_orchestration.codex_harness.models import CodexStructuredOutput


class ResponseSchema(BaseModel):
    """Response schema wrapper for OpenAI response_format."""

    type: str = "json_schema"
    json_schema: dict[str, Any]

    def to_openai(self) -> dict[str, Any]:
        """Return payload for OpenAI response_format."""
        return {"type": self.type, "json_schema": self.json_schema}


@dataclass(frozen=True)
class ResponseSchemaBuilder:
    """Build response schema payloads."""

    name: str = "codex_harness_output"

    def build(self) -> ResponseSchema:
        """Build the schema for structured output."""
        schema = CodexStructuredOutput.model_json_schema()
        payload = {
            "name": self.name,
            "schema": schema,
            "strict": True,
        }
        return ResponseSchema(json_schema=payload)
