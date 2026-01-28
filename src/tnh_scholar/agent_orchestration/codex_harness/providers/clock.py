"""Clock provider for the Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tnh_scholar.agent_orchestration.codex_harness.protocols import ClockProtocol


@dataclass(frozen=True)
class SystemClock(ClockProtocol):
    """System clock implementation."""

    def now(self) -> datetime:
        """Return current time."""
        return datetime.now()
