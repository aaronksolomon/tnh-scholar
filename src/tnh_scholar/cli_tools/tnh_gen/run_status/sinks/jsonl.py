"""Exclusive, flushed JSONL event storage."""

from pathlib import Path
from typing import TextIO

from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusEvent


class JsonlRunStatusSink:
    """Write one invocation to a fresh caller-owned file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stream: TextIO | None = None

    def open(self) -> None:
        """Exclusive creation also rejects dangling symlinks and races."""
        self._stream = self._path.open("x", encoding="utf-8")

    def emit(self, event: RunStatusEvent) -> None:
        """Make each newline-terminated record visible to live readers."""
        if self._stream is None:
            raise RuntimeError("Status sink is not open")
        self._stream.write(event.model_dump_json() + "\n")
        self._stream.flush()

    def close(self) -> None:
        """Release the stream even when closing raises."""
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.close()
