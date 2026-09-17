"""Event invariants, ordering, sink isolation, and live file visibility."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from tnh_scholar.cli_tools.tnh_gen.run_status.emitter import RunStatusEmitter, StatusClock
from tnh_scholar.cli_tools.tnh_gen.run_status.factory import create_emitter
from tnh_scholar.cli_tools.tnh_gen.run_status.models import (
    EventType,
    RunStage,
    RunStatusEvent,
    RunStatusMetadata,
    TerminalDecision,
)
from tnh_scholar.cli_tools.tnh_gen.run_status.policy import RunStatusConfig
from tnh_scholar.cli_tools.tnh_gen.run_status.sink import ManagedSink
from tnh_scholar.cli_tools.tnh_gen.run_status.sinks.jsonl import JsonlRunStatusSink


def test_order_timing_and_terminal_stop(metadata: RunStatusMetadata) -> None:
    timer = Mock(return_value=100.0)
    wall = Mock(return_value=datetime.now(UTC))
    sink = Mock()
    emitter = RunStatusEmitter(
        metadata, RunStatusConfig(), [ManagedSink(sink, Mock())], StatusClock(timer, wall)
    )
    emitter.open()
    timer.return_value = 102.0
    emitter.emit_stage(RunStage.GENERATING)
    timer.return_value = 112.0
    wall.return_value -= timedelta(days=1)
    emitter.heartbeat()
    emitter.finish(TerminalDecision())
    emitter.heartbeat()
    emitter.emit_stage(RunStage.EMITTING_OUTPUT)
    emitter.finish(TerminalDecision())
    events = [call.args[0] for call in sink.emit.call_args_list]
    assert [event.sequence for event in events] == [1, 2, 3, 4]
    assert events[2].event_type is EventType.HEARTBEAT
    assert (events[2].elapsed_ms, events[2].stage_elapsed_ms) == (12000, 10000)
    assert events[-1].event_type is EventType.TERMINAL
    sink.close.assert_called_once()


@pytest.mark.parametrize("phase", ["open", "emit", "close"])
def test_optional_sink_failure_isolated(metadata: RunStatusMetadata, phase: str) -> None:
    bad, good, diagnostic = Mock(), Mock(), Mock()
    getattr(bad, phase).side_effect = OSError("sensitive detail")
    emitter = RunStatusEmitter(
        metadata, RunStatusConfig(), [ManagedSink(bad, diagnostic), ManagedSink(good, diagnostic)]
    )
    emitter.open()
    emitter.emit_stage(RunStage.GENERATING)
    emitter.finish(TerminalDecision())
    assert good.emit.call_args.args[0].outcome.value == "completed"
    diagnostic.assert_called_once()
    assert "sensitive" not in diagnostic.call_args.args[0]
    bad.close.assert_called_once()


@pytest.mark.parametrize("phase", ["open", "emit"])
def test_required_sink_startup_fails_before_events(metadata: RunStatusMetadata, phase: str) -> None:
    sink = Mock()
    getattr(sink, phase).side_effect = OSError("no space")
    emitter = RunStatusEmitter(metadata, RunStatusConfig(), [ManagedSink(sink, Mock(), required=True)])
    with pytest.raises(ValueError, match="initialize"):
        emitter.open()
    sink.close.assert_called_once()


def test_live_file_and_truncated_tail(tmp_path: Path, metadata: RunStatusMetadata) -> None:
    path = tmp_path / "status.jsonl"
    emitter = create_emitter(metadata, RunStatusConfig(status_file=path))
    emitter.open()
    try:
        first = RunStatusEvent.model_validate_json(path.read_text())
        assert first.stage is RunStage.STARTING
        assert first.outcome is None
        emitter.emit_stage(RunStage.GENERATING)
    finally:
        emitter.close()  # Simulate interrupted history: no terminal outcome.
    with path.open("a") as stream:
        stream.write('{"schema_version":')
    records = [
        RunStatusEvent.model_validate_json(line)
        for line in path.read_text().splitlines(keepends=True)
        if line.endswith("\n")
    ]
    assert len(records) == 2
    assert all(record.event_type is not EventType.TERMINAL for record in records)


def test_event_validation_and_version(metadata: RunStatusMetadata) -> None:
    base = RunStatusEvent(
        sequence=1,
        event_type=EventType.STAGE_STARTED,
        stage=RunStage.STARTING,
        timestamp=datetime.now(UTC),
        elapsed_ms=0,
        stage_elapsed_ms=0,
        metadata=metadata,
        message="starting",
    )
    payload = json.loads(base.model_dump_json())
    payload["schema_version"], payload["future_field"] = "1.1", True
    assert RunStatusEvent.model_validate(payload).schema_version == "1.1"
    for change in (
        {"outcome": "completed"},
        {"event_type": "terminal"},
        {"schema_version": "2.0"},
        {"timestamp": "2026-01-01T00:00:00"},
        {"sequence": 0},
        {"stage_elapsed_ms": 1},
    ):
        with pytest.raises(ValidationError):
            RunStatusEvent.model_validate(payload | change)


@pytest.mark.parametrize(
    "api,quiet,tty,expected",
    [
        (False, False, True, True),
        (True, False, True, False),
        (False, True, True, False),
        (False, False, False, False),
    ],
)
def test_sink_selection(api: bool, quiet: bool, tty: bool, expected: bool) -> None:
    config = RunStatusConfig.resolve(
        status_file=Path("status"), api=api, quiet=quiet, is_tty=tty, no_color=True
    )
    assert config.interactive is expected
    assert config.status_file == Path("status")
    assert config.no_color


def test_jsonl_flush_failure_disables_without_replay(metadata: RunStatusMetadata) -> None:
    stream = Mock()
    stream.flush.side_effect = [None, OSError("disk full")]
    sink = JsonlRunStatusSink(Path("unused"))
    sink.open = lambda: setattr(sink, "_stream", stream)
    warning = Mock()
    emitter = RunStatusEmitter(metadata, RunStatusConfig(), [ManagedSink(sink, warning, required=True)])
    emitter.open()
    emitter.emit_stage(RunStage.GENERATING)
    emitter.finish(TerminalDecision())
    assert stream.write.call_count == 2
    stream.close.assert_called_once()
    warning.assert_called_once()


def test_rich_no_color_and_literal_labels(
    metadata: RunStatusMetadata, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tnh_scholar.cli_tools.tnh_gen.run_status.sinks.rich import RichRunStatusSink

    console = Mock()
    constructor = Mock(return_value=console)
    monkeypatch.setattr("tnh_scholar.cli_tools.tnh_gen.run_status.sinks.rich.Console", constructor)
    sink = RichRunStatusSink(no_color=True)
    sink.open()
    sink.emit(
        RunStatusEvent(
            sequence=1,
            event_type=EventType.STAGE_STARTED,
            stage=RunStage.STARTING,
            timestamp=datetime.now(UTC),
            elapsed_ms=0,
            stage_elapsed_ms=0,
            metadata=metadata.model_copy(update={"prompt_key": "[red]literal"}),
            message="starting",
        )
    )
    assert constructor.call_args.kwargs["stderr"] is True
    assert constructor.call_args.kwargs["no_color"] is True
    text = console.status.return_value.update.call_args.args[0]
    assert "[red]literal" in text.plain
    sink.close()
    sink.close()
    console.status.return_value.stop.assert_called_once()


def test_rich_constructor_failure_does_not_cancel_run(
    metadata: RunStatusMetadata, monkeypatch: pytest.MonkeyPatch
) -> None:
    constructor = Mock(side_effect=OSError("terminal unavailable"))
    monkeypatch.setattr("tnh_scholar.cli_tools.tnh_gen.run_status.sinks.rich.Console", constructor)
    emitter = create_emitter(metadata, RunStatusConfig(interactive=True))
    emitter.open()
    emitter.emit_stage(RunStage.GENERATING)
    emitter.finish(TerminalDecision())
    constructor.assert_called_once()
