"""Sink protocol and failure-isolated lifecycle ownership."""

from dataclasses import dataclass
from typing import Callable, Protocol

from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunStatusEvent


class RunStatusSink(Protocol):
    """Consume ordered status records without affecting task semantics."""

    def open(self) -> None: ...
    def emit(self, event: RunStatusEvent) -> None: ...
    def close(self) -> None: ...


@dataclass
class ManagedSink:
    """Disable a faulty sink and warn at most once, without exposing payloads."""

    sink: RunStatusSink
    diagnostic: Callable[[str], None]
    required: bool = False
    transient: bool = False
    active: bool = False
    closed: bool = False
    warned: bool = False

    def start(self, event: RunStatusEvent) -> None:
        """Require a first record only for explicitly requested file sinks."""
        try:
            self.sink.open()
            self.active = True
            self.sink.emit(event)
        except Exception as exc:
            self.close()
            if self.required:
                raise ValueError("Unable to initialize requested status file") from exc
            self._warn()

    def emit(self, event: RunStatusEvent) -> None:
        """Deliver one event or retire the sink after an operational failure."""
        if not self.active:
            return
        try:
            self.sink.emit(event)
        except Exception:
            self._warn()
            self.close()

    def close(self) -> None:
        """Close once, including resources partially opened during startup."""
        if self.closed:
            return
        self.closed, self.active = True, False
        try:
            self.sink.close()
        except Exception:
            self._warn()

    def _warn(self) -> None:
        if self.warned:
            return
        self.warned = True
        try:
            self.diagnostic("[tnh-gen] Runtime status sink unavailable.")
        except Exception:
            pass  # A broken diagnostic stream must not replace the task failure.
