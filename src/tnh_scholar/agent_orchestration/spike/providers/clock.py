"""Clock provider for the spike."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tnh_scholar.agent_orchestration.spike.protocols import ClockProtocol


@dataclass(frozen=True)
class SystemClock(ClockProtocol):
    """System clock implementation."""

    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)
