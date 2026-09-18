"""Serialized status emission and heartbeat lifecycle."""

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable

from tnh_scholar.cli_tools.tnh_gen.run_status.models import (
    EventType,
    RunStage,
    RunStatusEvent,
    RunStatusMetadata,
    TerminalDecision,
)
from tnh_scholar.cli_tools.tnh_gen.run_status.policy import RunStatusConfig
from tnh_scholar.cli_tools.tnh_gen.run_status.sink import ManagedSink


@dataclass(frozen=True)
class StatusClock:
    """Injectable monotonic and UTC clocks."""

    monotonic: Callable[[], float] = time.monotonic
    utcnow: Callable[[], datetime] = lambda: datetime.now(UTC)


class RunStatusEmitter:
    """Own ordered event construction; sinks never create lifecycle events."""

    def __init__(
        self,
        metadata: RunStatusMetadata,
        config: RunStatusConfig,
        sinks: list[ManagedSink],
        clock: StatusClock | None = None,
    ) -> None:
        self._metadata, self._config, self._sinks = metadata, config, sinks
        self._clock = clock or StatusClock()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._stage = RunStage.STARTING
        self._started = self._stage_started = self._last_event = self._clock.monotonic()
        self._sequence = 0
        self._finished = self._opened = False
        self._model: str | None = None
        self._provider: str | None = None

    @property
    def stage(self) -> RunStage:
        """Expose the operation boundary for primary failure attribution."""
        with self._lock:
            return self._stage

    def open(self) -> None:
        """Initialize required sinks before spawning the heartbeat worker."""
        with self._lock:
            event = self._event(EventType.STAGE_STARTED)
            try:
                for sink in self._sinks:
                    sink.start(event)
            except BaseException:
                self.close()
                raise
            self._opened = True
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        try:
            self._thread.start()
        except BaseException:
            self._thread = None
            self.close()
            raise

    def emit_stage(self, stage: RunStage) -> None:
        """Atomically transition stage and publish its first event."""
        with self._lock:
            if self._finished:
                return
            self._stage, self._stage_started = stage, self._clock.monotonic()
            self._publish(self._event(EventType.STAGE_STARTED))
            if stage is RunStage.EMITTING_OUTPUT:
                for sink in self._sinks:
                    if sink.transient:
                        sink.close()

    def set_resolved_identity(self, model: str, provider: str) -> None:
        """Record only identities supplied by the completed service envelope."""
        with self._lock:
            self._model, self._provider = model, provider

    def heartbeat(self) -> None:
        """Publish only after an interval with no event; also supports fake clocks."""
        with self._lock:
            if self._finished or not self._opened:
                return
            if self._clock.monotonic() - self._last_event >= self._config.heartbeat_seconds:
                self._publish(self._event(EventType.HEARTBEAT))

    def finish(self, decision: TerminalDecision) -> None:
        """Stop the worker before emitting the invocation's single terminal event."""
        with self._lock:
            if self._finished:
                return
            self._finished = True
        self._stop_worker()
        try:
            if self._opened:
                with self._lock:
                    self._publish(self._event(EventType.TERMINAL, decision))
        finally:
            self.close()

    def close(self) -> None:
        """Clean up partial initialization and normal completion alike."""
        with self._lock:
            self._finished = True
        self._stop_worker()
        for sink in self._sinks:
            sink.close()

    def _stop_worker(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(self._heartbeat_delay()):
            self.heartbeat()

    def _heartbeat_delay(self) -> float:
        """Wait only until the current deadline after any stage transition."""
        with self._lock:
            elapsed = self._clock.monotonic() - self._last_event
            remaining: float = self._config.heartbeat_seconds - elapsed
            return max(0.0, remaining)

    def _publish(self, event: RunStatusEvent) -> None:
        for sink in self._sinks:
            sink.emit(event)

    def _event(self, kind: EventType, decision: TerminalDecision | None = None) -> RunStatusEvent:
        now = self._clock.monotonic()
        self._last_event = now
        self._sequence += 1
        return RunStatusEvent(
            sequence=self._sequence,
            event_type=kind,
            stage=self._stage,
            timestamp=self._clock.utcnow(),
            elapsed_ms=max(0, int((now - self._started) * 1000)),
            stage_elapsed_ms=max(0, int((now - self._stage_started) * 1000)),
            metadata=self._metadata,
            message=self._stage.value.replace("_", " "),
            outcome=decision.outcome if decision else None,
            exit_code=decision.exit_code if decision else None,
            failure=decision.failure if decision else None,
            reporting_failure=decision.reporting_failure if decision else None,
            model=self._model,
            provider=self._provider,
        )
