"""Event stream writer for the spike."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.spike.models import RunEvent
from tnh_scholar.agent_orchestration.spike.protocols import EventWriterProtocol


@dataclass(frozen=True)
class NdjsonEventWriter(EventWriterProtocol):
    """Append events to an NDJSON file."""

    events_path: Path

    def write_event(self, event: RunEvent) -> None:
        payload = event.model_dump_json()
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
