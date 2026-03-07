"""Focused tests for the subprocess-based spike runner."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from tnh_scholar.agent_orchestration.spike.models import (
    PromptAction,
    PromptHandlingOutcome,
    TerminationReason,
)
from tnh_scholar.agent_orchestration.spike.providers.subprocess_agent_runner import (
    RunnerState,
    SubprocessAgentRunner,
)


@dataclass(frozen=True)
class _IgnorePromptHandler:
    def handle_output(self, text: str) -> PromptHandlingOutcome:
        return PromptHandlingOutcome(action=PromptAction.ignore)


@dataclass
class _BrokenPipeStdin:
    def write(self, payload: bytes) -> int:
        raise BrokenPipeError("pipe closed")

    def flush(self) -> None:
        return None


@dataclass
class _FakeProcess:
    stdin: _BrokenPipeStdin


def test_record_output_rejects_unknown_stream_name() -> None:
    runner = SubprocessAgentRunner()
    state = RunnerState(
        output=bytearray(),
        stdout=bytearray(),
        stderr=bytearray(),
        last_output=0.0,
        last_heartbeat=0.0,
        decision=None,
        termination=TerminationReason.completed,
    )

    try:
        runner._record_output(state, b"oops", "side-channel", None)
    except ValueError as exc:
        assert "Unexpected stream_name" in str(exc)
    else:
        raise AssertionError("Expected unknown stream_name to fail fast.")


def test_send_response_ignores_broken_pipe() -> None:
    runner = SubprocessAgentRunner()
    process = _FakeProcess(stdin=_BrokenPipeStdin())

    runner._send_response(process, "y\n")


def test_timeout_termination_returns_definitive_exit_code() -> None:
    runner = SubprocessAgentRunner()
    result = runner.run(
        command=[sys.executable, "-c", "import time; time.sleep(10)"],
        timeout_seconds=1,
        idle_timeout_seconds=20,
        heartbeat_interval_seconds=60,
        prompt_handler=_IgnorePromptHandler(),
        on_heartbeat=None,
        on_output=None,
    )

    assert result.termination_reason == TerminationReason.wall_clock_timeout
    assert result.exit_code is not None
