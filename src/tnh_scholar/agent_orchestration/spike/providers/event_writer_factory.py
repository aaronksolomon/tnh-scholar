"""Factory for event writers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.spike.protocols import (
    EventWriterFactoryProtocol,
    EventWriterProtocol,
)
from tnh_scholar.agent_orchestration.spike.providers.event_writer import NdjsonEventWriter


@dataclass(frozen=True)
class NdjsonEventWriterFactory(EventWriterFactoryProtocol):
    """Create NDJSON event writers."""

    def create(self, events_path: Path) -> EventWriterProtocol:
        return NdjsonEventWriter(events_path=events_path)
