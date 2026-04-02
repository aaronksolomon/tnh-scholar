"""Shared orchestration enums that must not depend on package initializers."""

from __future__ import annotations

from enum import Enum


class AgentFamily(str, Enum):
    """Supported maintained runner families."""

    claude_cli = "claude_cli"
    codex_cli = "codex_cli"


class RunnerTermination(str, Enum):
    """Mechanical outcomes exposed to the kernel by maintained runners."""

    completed = "completed"
    error = "error"
    killed_timeout = "killed_timeout"
    killed_idle = "killed_idle"
    killed_policy = "killed_policy"
