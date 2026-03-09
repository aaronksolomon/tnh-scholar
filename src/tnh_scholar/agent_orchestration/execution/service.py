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
    """Execute trusted subprocess requests."""

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute one typed request."""
        argv = self._render_argv(request)
        env = self._build_environment(request.environment_policy)
        try:
            completed = subprocess.run(
                argv,
                cwd=request.working_directory,
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=request.timeout_policy.wall_clock_seconds,
            )
        except subprocess.TimeoutExpired as error:
            return ExecutionResult(
                termination=ExecutionTermination.wall_clock_timeout,
                timed_out=True,
                stdout_text=error.stdout or "",
                stderr_text=error.stderr or "",
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
            stdout_text=completed.stdout,
            stderr_text=completed.stderr,
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
