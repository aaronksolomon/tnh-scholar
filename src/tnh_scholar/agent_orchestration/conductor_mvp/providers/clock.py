"""Clock provider for conductor MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

from tnh_scholar.agent_orchestration.common.time import utc_now
from tnh_scholar.agent_orchestration.conductor_mvp.protocols import ClockProtocol


@dataclass(frozen=True)
class SystemClock(ClockProtocol):
    """System UTC clock."""

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
        return cast(datetime, utc_now())
