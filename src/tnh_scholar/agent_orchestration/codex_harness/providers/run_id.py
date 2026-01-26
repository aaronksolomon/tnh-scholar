"""Run id generator for Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tnh_scholar.agent_orchestration.codex_harness.protocols import RunIdGeneratorProtocol


@dataclass(frozen=True)
class TimestampRunIdGenerator(RunIdGeneratorProtocol):
    """Timestamp-based run id generator."""

    def next_id(self, *, now: datetime) -> str:
        """Return a timestamp-based run id."""
        return now.strftime("%Y%m%d-%H%M%S")
