"""Shared helpers for maintained runner adapters."""

from __future__ import annotations

import shutil
from pathlib import Path

from tnh_scholar.agent_orchestration.execution import ExecutionTermination
from tnh_scholar.agent_orchestration.shared_enums import RunnerTermination


def resolve_executable_path(configured: Path | None, command_name: str) -> Path:
    """Resolve one configured or PATH-backed executable to an absolute path."""
    if configured is not None:
        return configured
    resolved = shutil.which(command_name)
    if resolved is None:
        raise OSError(f"Runner executable not found on PATH: {command_name}")
    return Path(resolved)


def to_runner_termination(termination: ExecutionTermination) -> RunnerTermination:
    """Map one execution termination into the maintained runner enum."""
    match termination:
        case ExecutionTermination.completed:
            return RunnerTermination.completed
        case ExecutionTermination.non_zero_exit | ExecutionTermination.startup_failure:
            return RunnerTermination.error
        case ExecutionTermination.wall_clock_timeout:
            return RunnerTermination.killed_timeout
        case ExecutionTermination.idle_timeout:
            return RunnerTermination.killed_idle
        case ExecutionTermination.policy_kill:
            return RunnerTermination.killed_policy
    raise ValueError(f"Unsupported execution termination: {termination.value}")
