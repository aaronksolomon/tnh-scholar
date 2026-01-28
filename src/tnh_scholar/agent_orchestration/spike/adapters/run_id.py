"""Run ID generation for the spike."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tnh_scholar.agent_orchestration.spike.protocols import RunIdGeneratorProtocol


@dataclass(frozen=True)
class TimestampRunIdGenerator(RunIdGeneratorProtocol):
    """Timestamp-based run id generator."""

    format_str: str = "%Y%m%d-%H%M%S"

    def next_id(self, *, now: datetime) -> str:
        return now.astimezone(timezone.utc).strftime(self.format_str)
