"""Primary origin remains stable through rendering and output failures."""

from unittest.mock import Mock

import pytest
import typer

from tnh_scholar.cli_tools.tnh_gen.run_status.emitter import RunStatusEmitter
from tnh_scholar.cli_tools.tnh_gen.run_status.lifecycle import RunLifecycle
from tnh_scholar.cli_tools.tnh_gen.run_status.models import EventType, RunStage, RunStatusMetadata
from tnh_scholar.cli_tools.tnh_gen.run_status.policy import RunStatusConfig
from tnh_scholar.cli_tools.tnh_gen.run_status.sink import ManagedSink
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionFailure,
    CompletionOutcomeStatus,
    FailureReason,
)
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked


def test_failed_envelope_keeps_generation_origin(
    metadata: RunStatusMetadata, envelope: CompletionEnvelope
) -> None:
    sink, renderer = Mock(), Mock()
    emitter = RunStatusEmitter(metadata, RunStatusConfig(), [ManagedSink(sink, Mock())])
    failed = envelope.model_copy(
        update={
            "outcome": CompletionOutcomeStatus.FAILED,
            "result": None,
            "failure": CompletionFailure(
                reason=FailureReason.CONTRACT_VALIDATION_FAILED, message="bad", retryable=False
            ),
        }
    )
    with pytest.raises(typer.Exit) as caught:
        with RunLifecycle(emitter, renderer) as run:
            emitter.emit_stage(RunStage.GENERATING)
            run.classify(failed)
            emitter.emit_stage(RunStage.EMITTING_OUTPUT)
            raise OSError("cannot render failure")
    event = sink.emit.call_args.args[0]
    assert caught.value.exit_code == event.exit_code == 4
    assert event.failure.origin_stage is RunStage.GENERATING
    assert event.reporting_failure.origin_stage is RunStage.EMITTING_OUTPUT
    renderer.assert_not_called()


@pytest.mark.parametrize(
    "stage,error,code",
    [
        (RunStage.PREPARING_RUN, ValueError("invalid input"), 5),
        (
            RunStage.GENERATING,
            SafetyBlocked("budget", blocked_reason="budget", estimated_cost=1, max_dollars=0.1),
            1,
        ),
        (RunStage.EMITTING_OUTPUT, OSError("disk full"), 3),
    ],
)
def test_exception_origin_and_secondary_error(
    metadata: RunStatusMetadata, stage: RunStage, error: Exception, code: int
) -> None:
    sink = Mock()
    emitter = RunStatusEmitter(metadata, RunStatusConfig(), [ManagedSink(sink, Mock())])
    renderer = Mock(side_effect=RuntimeError("renderer failed"))
    with pytest.raises(typer.Exit) as caught:
        with RunLifecycle(emitter, renderer):
            emitter.emit_stage(stage)
            raise error
    terminal = sink.emit.call_args.args[0]
    assert terminal.event_type is EventType.TERMINAL
    assert terminal.failure.origin_stage is stage
    assert terminal.reporting_failure.origin_stage is RunStage.EMITTING_OUTPUT
    assert caught.value.exit_code == code == terminal.exit_code


def test_keyboard_interrupt_preserves_abort(metadata: RunStatusMetadata) -> None:
    sink = Mock()
    emitter = RunStatusEmitter(metadata, RunStatusConfig(), [ManagedSink(sink, Mock())])
    with pytest.raises(KeyboardInterrupt):
        with RunLifecycle(emitter, Mock()):
            emitter.emit_stage(RunStage.GENERATING)
            raise KeyboardInterrupt
    terminal = sink.emit.call_args.args[0]
    assert terminal.outcome.value == "cancelled"
    assert terminal.failure.origin_stage is RunStage.GENERATING
    sink.close.assert_called_once()


def test_terminal_after_flush_and_rich_cleanup(
    metadata: RunStatusMetadata, monkeypatch: pytest.MonkeyPatch
) -> None:
    file_sink, rich_sink, stream = Mock(), Mock(), Mock()
    emitter = RunStatusEmitter(
        metadata,
        RunStatusConfig(),
        [ManagedSink(file_sink, Mock()), ManagedSink(rich_sink, Mock(), transient=True)],
    )
    observed = []
    file_sink.emit.side_effect = (
        lambda event: observed.append(stream.flush.call_count)
        if event.event_type is EventType.TERMINAL
        else None
    )
    monkeypatch.setattr("tnh_scholar.cli_tools.tnh_gen.run_status.lifecycle.sys.stdout", stream)
    with RunLifecycle(emitter, Mock()):
        emitter.emit_stage(RunStage.EMITTING_OUTPUT)
        rich_sink.close.assert_called_once()
        assert not file_sink.close.called
    assert observed == [1]


def test_stdout_flush_failure_is_not_success(
    metadata: RunStatusMetadata, monkeypatch: pytest.MonkeyPatch
) -> None:
    sink, stream = Mock(), Mock()
    stream.flush.side_effect = BrokenPipeError()
    monkeypatch.setattr("tnh_scholar.cli_tools.tnh_gen.run_status.lifecycle.sys.stdout", stream)
    emitter = RunStatusEmitter(metadata, RunStatusConfig(), [ManagedSink(sink, Mock())])
    with pytest.raises(typer.Exit):
        with RunLifecycle(emitter, Mock()):
            emitter.emit_stage(RunStage.EMITTING_OUTPUT)
    assert sink.emit.call_args.args[0].failure.origin_stage is RunStage.EMITTING_OUTPUT
