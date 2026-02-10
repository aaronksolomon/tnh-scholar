"""Run id generator for Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

from tnh_scholar.agent_orchestration.codex_harness.protocols import RunIdGeneratorProtocol
from tnh_scholar.agent_orchestration.common.run_id import strftime_run_id


@dataclass(frozen=True)
class TimestampRunIdGenerator(RunIdGeneratorProtocol):
    """Timestamp-based run id generator."""

    def next_id(self, *, now: datetime) -> str:
        """Return a timestamp-based run id."""
        return cast(str, strftime_run_id(now, "%Y%m%d-%H%M%S"))
