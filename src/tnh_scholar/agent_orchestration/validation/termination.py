"""Shared validation termination helpers."""

from __future__ import annotations

from tnh_scholar.agent_orchestration.execution.models import ExecutionTermination
from tnh_scholar.agent_orchestration.validation.models import ValidationTermination


def to_validation_termination(termination: ExecutionTermination) -> ValidationTermination:
    """Map subprocess termination into validation termination."""
    match termination:
        case ExecutionTermination.completed:
            return ValidationTermination.completed
        case ExecutionTermination.non_zero_exit | ExecutionTermination.startup_failure:
            return ValidationTermination.error
        case ExecutionTermination.wall_clock_timeout:
            return ValidationTermination.killed_timeout
        case ExecutionTermination.idle_timeout:
            return ValidationTermination.killed_idle
        case ExecutionTermination.policy_kill:
            return ValidationTermination.killed_policy
    raise ValueError(f"Unsupported execution termination: {termination.value}")


def merge_validation_termination(
    current: ValidationTermination,
    new_value: ValidationTermination,
) -> ValidationTermination:
    """Keep the more severe validation termination."""
    return max(current, new_value, key=validation_termination_rank)


def validation_termination_rank(value: ValidationTermination) -> int:
    """Rank validation terminations by severity."""
    match value:
        case ValidationTermination.completed:
            return 0
        case ValidationTermination.error:
            return 1
        case ValidationTermination.killed_policy:
            return 2
        case ValidationTermination.killed_idle:
            return 3
        case ValidationTermination.killed_timeout:
            return 4
    raise ValueError(f"Unsupported validation termination: {value}")
