"""Explicit bootstrap profile assembly for the maintained headless app layer."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from tnh_scholar.agent_orchestration.app.models import (
    HeadlessPolicyConfig,
    HeadlessValidationConfig,
)
from tnh_scholar.agent_orchestration.execution_policy import (
    ApprovalPosture,
    ExecutionPolicySettings,
    ExecutionPosture,
    RequestedExecutionPolicy,
)
from tnh_scholar.agent_orchestration.validation import BuiltinCommandEntry, BuiltinValidatorId


@dataclass(frozen=True)
class BootstrapRuntimeProfile:
    """Explicit temporary bootstrap profile for headless maintained runs."""

    validation: HeadlessValidationConfig
    policy: HeadlessPolicyConfig


def build_bootstrap_runtime_profile() -> BootstrapRuntimeProfile:
    """Return the explicit bootstrap profile used by the maintained CLI."""
    return BootstrapRuntimeProfile(
        validation=HeadlessValidationConfig(
            builtin_commands=_bootstrap_builtin_commands()
        ),
        policy=HeadlessPolicyConfig(
            execution_policy_settings=ExecutionPolicySettings(
                default_policy=RequestedExecutionPolicy(
                    execution_posture=ExecutionPosture.workspace_write,
                    approval_posture=ApprovalPosture.fail_on_prompt,
                )
            )
        ),
    )


def _bootstrap_builtin_commands() -> tuple[BuiltinCommandEntry, ...]:
    interpreter = Path(sys.executable)
    return (
        BuiltinCommandEntry(
            name=BuiltinValidatorId.tests,
            executable=interpreter,
            arguments=("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"),
        ),
        BuiltinCommandEntry(
            name=BuiltinValidatorId.lint,
            executable=interpreter,
            arguments=("-m", "ruff", "check", "."),
        ),
        BuiltinCommandEntry(
            name=BuiltinValidatorId.typecheck,
            executable=interpreter,
            arguments=("-m", "mypy", "src"),
        ),
    )
