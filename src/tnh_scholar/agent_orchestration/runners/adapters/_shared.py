"""Shared helpers for maintained runner adapters."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from tnh_scholar.agent_orchestration.execution import ExecutionTermination
from tnh_scholar.agent_orchestration.runners.models import RunnerTextArtifact
from tnh_scholar.agent_orchestration.shared_enums import RunnerTermination


def resolve_executable_path(configured: Path | None, command_name: str) -> Path:
    """Resolve one configured or PATH-backed executable to an absolute path."""
    if configured is not None:
        return _validate_configured_path(configured)
    resolved = shutil.which(command_name)
    if resolved is None:
        raise OSError(f"Runner executable not found on PATH: {command_name}")
    return Path(resolved).resolve()


def build_transcript_artifact(stdout_text: str) -> RunnerTextArtifact | None:
    """Normalize one stdout transcript into the canonical NDJSON text artifact."""
    content = stdout_text.strip()
    if not content:
        return None
    return RunnerTextArtifact(
        filename="transcript.ndjson",
        content=f"{content}\n",
        media_type="application/x-ndjson",
    )


def _validate_configured_path(configured: Path) -> Path:
    path = configured.expanduser()
    if not path.exists():
        raise OSError(f"Configured runner executable does not exist: {path}")
    if not path.is_file():
        raise OSError(f"Configured runner executable is not a file: {path}")
    if not os.access(path, os.X_OK):
        raise OSError(f"Configured runner executable is not executable: {path}")
    return path.resolve()


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
