"""Command outcome ownership separate from rendering and status delivery."""

import sys
from types import TracebackType
from typing import Callable, Literal, Self

import typer

from tnh_scholar.cli_tools.tnh_gen.run_status.decisions import (
    cancelled_decision,
    envelope_decision,
    exception_decision,
    exception_failure,
)
from tnh_scholar.cli_tools.tnh_gen.run_status.emitter import RunStatusEmitter
from tnh_scholar.cli_tools.tnh_gen.run_status.models import RunOutcome, RunStage, TerminalDecision
from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope


class RunLifecycle:
    """Finalize after output; preserve a known primary failure during reporting."""

    def __init__(self, emitter: RunStatusEmitter, render_exception: Callable[[Exception], None]) -> None:
        self.emitter = emitter
        self._render_exception = render_exception
        self._decision = TerminalDecision()

    def __enter__(self) -> Self:
        try:
            self.emitter.open()
        except Exception as exc:
            self._record_exception(exc)
            self._render_failure(exc)
            raise typer.Exit(self._decision.exit_code) from exc
        return self

    def classify(self, envelope: CompletionEnvelope) -> None:
        """Record generation outcome before output rendering can fail."""
        self._decision = envelope_decision(envelope)
        self.emitter.set_resolved_identity(envelope.provenance.model, envelope.provenance.provider)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> Literal[False]:
        try:
            if isinstance(exc, KeyboardInterrupt):
                self._decision = cancelled_decision(self.emitter.stage)
                return False
            if exc is not None and not isinstance(exc, Exception):
                return False
            self._complete_output(exc)
            return False
        except KeyboardInterrupt:
            self._decision = cancelled_decision(self.emitter.stage)
            raise
        finally:
            if exc is None or isinstance(exc, (Exception, KeyboardInterrupt)):
                self.emitter.finish(self._decision)
            else:
                self.emitter.close()

    def _complete_output(self, exc: Exception | None) -> None:
        """Render or flush before applying the terminal exit decision."""
        if exc is not None:
            self._record_exception(exc)
            self._render_failure(exc)
        else:
            self._flush_output()
        if self._decision.outcome is not RunOutcome.COMPLETED:
            raise typer.Exit(self._decision.exit_code) from exc

    def _record_exception(self, exc: Exception) -> None:
        if self._decision.failure is None:
            self._decision = exception_decision(exc, self.emitter.stage)
            return
        self._decision = TerminalDecision(
            outcome=self._decision.outcome,
            exit_code=self._decision.exit_code,
            failure=self._decision.failure,
            reporting_failure=exception_failure(exc, self.emitter.stage),
        )

    def _render_failure(self, exc: Exception) -> None:
        self.emitter.emit_stage(RunStage.EMITTING_OUTPUT)
        try:
            # Do not render twice when a failed envelope's renderer already failed.
            if self._decision.reporting_failure is None:
                self._render_exception(exc)
                sys.stdout.flush()
        except Exception as reporting_exc:
            self._record_exception(reporting_exc)

    def _flush_output(self) -> None:
        try:
            sys.stdout.flush()
        except Exception as exc:
            self._record_exception(exc)
            self._render_failure(exc)
