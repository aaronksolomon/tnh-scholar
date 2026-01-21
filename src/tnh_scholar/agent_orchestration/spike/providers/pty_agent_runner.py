"""PTY-based agent runner for the spike."""

from __future__ import annotations

import os
import pty
import re
import select
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Callable

from tnh_scholar.agent_orchestration.spike.models import (
    AgentRunResult,
    CommandFilterDecision,
    PromptAction,
    TerminationReason,
)
from tnh_scholar.agent_orchestration.spike.protocols import (
    AgentRunnerProtocol,
    PromptHandlerProtocol,
)


@dataclass
class RunnerState:
    """Mutable state for PTY collection."""

    output: bytearray
    last_output: float
    last_heartbeat: float
    decision: CommandFilterDecision | None
    termination: TerminationReason


@dataclass(frozen=True)
class PtyAgentRunner(AgentRunnerProtocol):
    """Run agents in a PTY and capture output."""

    def run(
        self,
        *,
        command: list[str],
        timeout_seconds: int,
        idle_timeout_seconds: int,
        heartbeat_interval_seconds: int,
        prompt_handler: PromptHandlerProtocol,
        on_heartbeat: Callable[[], None] | None,
        on_output: Callable[[str], None] | None,
    ) -> AgentRunResult:
        start_time = time.monotonic()
        master_fd, slave_fd = pty.openpty()
        process = self._start_process(command, slave_fd)
        raw_output, decision, termination = self._collect_output(
            master_fd,
            process,
            prompt_handler,
            start_time,
            timeout_seconds,
            idle_timeout_seconds,
            heartbeat_interval_seconds,
            on_heartbeat,
            on_output,
        )
        return self._final_result(process, raw_output, termination, decision)

    def _start_process(self, command: list[str], slave_fd: int) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )

    def _collect_output(
        self,
        master_fd: int,
        process: subprocess.Popen[bytes],
        prompt_handler: PromptHandlerProtocol,
        start_time: float,
        timeout_seconds: int,
        idle_timeout_seconds: int,
        heartbeat_interval_seconds: int,
        on_heartbeat: Callable[[], None] | None,
        on_output: Callable[[str], None] | None,
    ) -> tuple[bytes, CommandFilterDecision | None, TerminationReason]:
        state = self._init_state()
        while True:
            state = self._apply_timeouts(process, start_time, timeout_seconds, idle_timeout_seconds, state)
            state = self._emit_heartbeat(state, heartbeat_interval_seconds, on_heartbeat)
            if self._should_break(process, state):
                break
            state = self._read_and_handle(master_fd, process, prompt_handler, state, on_output)
            if self._should_break(process, state):
                break
        return bytes(state.output), state.decision, state.termination

    def _read_chunk(self, master_fd: int) -> bytes:
        ready, _, _ = select.select([master_fd], [], [], 0.2)
        return os.read(master_fd, 4096) if ready else b""

    def _handle_prompt(
        self,
        chunk: bytes,
        prompt_handler: PromptHandlerProtocol,
        master_fd: int,
        process: subprocess.Popen[bytes],
    ) -> tuple[CommandFilterDecision | None, TerminationReason]:
        text = chunk.decode(errors="ignore")
        outcome = prompt_handler.handle_output(text)
        if outcome.action == PromptAction.ignore:
            return None, TerminationReason.completed
        if outcome.response_text is not None:
            os.write(master_fd, outcome.response_text.encode())
        if outcome.action == PromptAction.allow:
            return outcome.decision, TerminationReason.completed
        self._terminate(process)
        if outcome.decision is None:
            return outcome.decision, TerminationReason.interactive_prompt_detected
        return outcome.decision, TerminationReason.command_blocked

    def _final_result(
        self,
        process: subprocess.Popen[bytes],
        raw_output: bytes,
        termination: TerminationReason,
        decision: CommandFilterDecision | None,
    ) -> AgentRunResult:
        exit_code = process.poll()
        if exit_code is not None and exit_code != 0 and termination == TerminationReason.completed:
            termination = TerminationReason.nonzero_exit
        return AgentRunResult(
            exit_code=exit_code,
            termination_reason=termination,
            transcript_raw=raw_output,
            transcript_text=self._strip_ansi(raw_output),
            command_decision=decision,
        )

    def _strip_ansi(self, raw_output: bytes) -> str:
        text = raw_output.decode(errors="ignore")
        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    def _timed_out(self, start_time: float, timeout_seconds: int) -> bool:
        return time.monotonic() - start_time > timeout_seconds

    def _idle_timed_out(self, last_output: float, idle_timeout_seconds: int) -> bool:
        return time.monotonic() - last_output > idle_timeout_seconds

    def _init_state(self) -> RunnerState:
        now = time.monotonic()
        return RunnerState(
            output=bytearray(),
            last_output=now,
            last_heartbeat=now,
            decision=None,
            termination=TerminationReason.completed,
        )

    def _apply_timeouts(
        self,
        process: subprocess.Popen[bytes],
        start_time: float,
        timeout_seconds: int,
        idle_timeout_seconds: int,
        state: RunnerState,
    ) -> RunnerState:
        if process.poll() is not None:
            return state
        reason = self._timeout_reason(start_time, state.last_output, timeout_seconds, idle_timeout_seconds)
        if reason == TerminationReason.completed:
            return state
        self._terminate(process)
        return RunnerState(
            output=state.output,
            last_output=state.last_output,
            decision=state.decision,
            termination=reason,
        )

    def _should_break(self, process: subprocess.Popen[bytes], state: RunnerState) -> bool:
        if state.termination != TerminationReason.completed:
            return True
        return process.poll() is not None

    def _read_and_handle(
        self,
        master_fd: int,
        process: subprocess.Popen[bytes],
        prompt_handler: PromptHandlerProtocol,
        state: RunnerState,
        on_output: Callable[[str], None] | None,
    ) -> RunnerState:
        chunk = self._read_chunk(master_fd)
        if not chunk:
            return state
        state.output.extend(chunk)
        self._emit_output(chunk, on_output)
        decision, termination = self._handle_prompt(chunk, prompt_handler, master_fd, process)
        return RunnerState(
            output=state.output,
            last_output=time.monotonic(),
            last_heartbeat=state.last_heartbeat,
            decision=decision or state.decision,
            termination=termination,
        )

    def _timeout_reason(
        self,
        start_time: float,
        last_output: float,
        timeout_seconds: int,
        idle_timeout_seconds: int,
    ) -> TerminationReason:
        if self._timed_out(start_time, timeout_seconds):
            return TerminationReason.wall_clock_timeout
        if self._idle_timed_out(last_output, idle_timeout_seconds):
            return TerminationReason.idle_timeout
        return TerminationReason.completed

    def _terminate(self, process: subprocess.Popen[bytes]) -> None:
        process.send_signal(signal.SIGTERM)

    def _emit_heartbeat(
        self,
        state: RunnerState,
        heartbeat_interval_seconds: int,
        on_heartbeat: Callable[[], None] | None,
    ) -> RunnerState:
        if on_heartbeat is None:
            return state
        now = time.monotonic()
        if now - state.last_heartbeat < heartbeat_interval_seconds:
            return state
        on_heartbeat()
        return RunnerState(
            output=state.output,
            last_output=state.last_output,
            last_heartbeat=now,
            decision=state.decision,
            termination=state.termination,
        )

    def _emit_output(self, chunk: bytes, on_output: Callable[[str], None] | None) -> None:
        if on_output is None:
            return
        text = chunk.decode(errors="ignore")
        if not text:
            return
        on_output(text)
