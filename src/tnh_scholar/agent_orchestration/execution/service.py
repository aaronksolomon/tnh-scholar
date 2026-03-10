"""Trusted subprocess execution service."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.execution.models import (
    CliExecutableInvocation,
    EnvironmentPolicy,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTermination,
    ExplicitEnvironmentPolicy,
    InheritParentEnvironmentPolicy,
    IsolatedEnvironmentPolicy,
    PythonScriptInvocation,
)


@dataclass(frozen=True)
class SubprocessExecutionService:
    """Execute trusted subprocess requests.

    This boundary accepts only typed invocation models resolved by trusted
    orchestration code. It never uses ``shell=True`` and only renders argv from
    validated path-bearing invocation families.
    """

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute one typed request."""
        argv = self._render_argv(request)
        env = self._build_environment(request.environment_policy)
        stdout_target = self._stream_target(request.output_capture_policy.capture_stdout)
        stderr_target = self._stream_target(request.output_capture_policy.capture_stderr)
        try:
            # Trusted-only boundary: argv is rendered from typed invocation models,
            # validated paths, and always executed with shell=False.
            completed = subprocess.run(
                argv,
                cwd=request.working_directory,
                env=env,
                stdout=stdout_target,
                stderr=stderr_target,
                text=self._use_text_mode(request),
                encoding=self._encoding(request),
                check=False,
                shell=False,
                timeout=request.timeout_policy.wall_clock_seconds,
            )
        except subprocess.TimeoutExpired as error:
            return ExecutionResult(
                termination=ExecutionTermination.wall_clock_timeout,
                timed_out=True,
                stdout_text=self._normalize_stream(error.stdout),
                stderr_text=self._normalize_stream(error.stderr),
            )
        except OSError as error:
            return ExecutionResult(
                termination=ExecutionTermination.startup_failure,
                failure_message=str(error),
            )
        termination = (
            ExecutionTermination.completed
            if completed.returncode == 0
            else ExecutionTermination.non_zero_exit
        )
        return ExecutionResult(
            termination=termination,
            exit_code=completed.returncode,
            stdout_text=self._normalize_stream(completed.stdout),
            stderr_text=self._normalize_stream(completed.stderr),
        )

    def _render_argv(self, request: ExecutionRequest) -> list[str]:
        invocation = request.invocation
        if isinstance(invocation, CliExecutableInvocation):
            self._validate_path(invocation.executable, request.working_directory)
            return [str(invocation.executable), *invocation.arguments]
        self._validate_path(invocation.interpreter, request.working_directory)
        self._validate_path(invocation.script_path, request.working_directory)
        return [
            str(invocation.interpreter),
            str(invocation.script_path),
            *invocation.arguments,
        ]

    def _validate_path(self, path: Path, working_directory: Path) -> None:
        candidate = path if path.is_absolute() else working_directory / path
        if not candidate.exists():
            raise OSError(f"Execution path does not exist: {candidate}")

    def _build_environment(self, policy: EnvironmentPolicy) -> dict[str, str]:
        if isinstance(policy, InheritParentEnvironmentPolicy):
            return {**os.environ, **policy.overrides}
        if isinstance(policy, ExplicitEnvironmentPolicy):
            return dict(policy.values)
        if isinstance(policy, IsolatedEnvironmentPolicy):
            return dict(policy.allowlist)
        raise TypeError(f"Unsupported environment policy: {type(policy)!r}")

    def _stream_target(self, should_capture: bool) -> int | None:
        return subprocess.PIPE if should_capture else None

    def _use_text_mode(self, request: ExecutionRequest) -> bool:
        return request.output_capture_policy.encoding.value == "text"

    def _encoding(self, request: ExecutionRequest) -> str | None:
        return "utf-8" if self._use_text_mode(request) else None

    def _normalize_stream(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value
