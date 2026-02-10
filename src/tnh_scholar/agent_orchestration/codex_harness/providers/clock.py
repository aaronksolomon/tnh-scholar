"""Clock provider for the Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

from tnh_scholar.agent_orchestration.codex_harness.protocols import ClockProtocol
from tnh_scholar.agent_orchestration.common.time import local_now


@dataclass(frozen=True)
class SystemClock(ClockProtocol):
    """System clock implementation."""

    def now(self) -> datetime:
        """Return current time."""
        return cast(datetime, local_now())
