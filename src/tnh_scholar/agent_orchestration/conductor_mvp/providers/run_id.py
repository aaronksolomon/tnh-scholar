"""Run id generator provider for conductor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

from tnh_scholar.agent_orchestration.common.run_id import strftime_run_id
from tnh_scholar.agent_orchestration.conductor_mvp.protocols import RunIdGeneratorProtocol


@dataclass(frozen=True)
class TimestampRunIdGenerator(RunIdGeneratorProtocol):
    """Generate run IDs from UTC timestamps."""

    def next_id(self, now: datetime) -> str:
        """Return a compact timestamp run ID."""
        return cast(str, strftime_run_id(now, "%Y%m%dT%H%M%SZ"))
