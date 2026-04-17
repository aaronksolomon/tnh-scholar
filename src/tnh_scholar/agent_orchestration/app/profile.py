"""Explicit bootstrap profile assembly for the maintained headless app layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import which

from tnh_scholar.agent_orchestration.app.models import (
    HeadlessPolicyConfig,
    HeadlessValidationConfig,
)
from tnh_scholar.agent_orchestration.execution import InheritParentEnvironmentPolicy
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
                ),
                named_policies={
                    "step.review_assist": RequestedExecutionPolicy(
                        execution_posture=ExecutionPosture.workspace_write,
                        approval_posture=ApprovalPosture.bounded_auto_approve,
                    )
                },
            )
        ),
    )


def _bootstrap_builtin_commands() -> tuple[BuiltinCommandEntry, ...]:
    poetry_executable = _resolve_required_cli("poetry")
    return (
        BuiltinCommandEntry(
            name=BuiltinValidatorId.tests,
            executable=poetry_executable,
            arguments=("run", "pytest"),
            environment_policy=InheritParentEnvironmentPolicy(),
        ),
        BuiltinCommandEntry(
            name=BuiltinValidatorId.lint,
            executable=poetry_executable,
            arguments=("run", "ruff", "check", "."),
            environment_policy=InheritParentEnvironmentPolicy(),
        ),
        BuiltinCommandEntry(
            name=BuiltinValidatorId.typecheck,
            executable=poetry_executable,
            arguments=("run", "mypy", "src"),
            environment_policy=InheritParentEnvironmentPolicy(),
        ),
    )


def _resolve_required_cli(name: str) -> Path:
    resolved = which(name)
    if resolved is None:
        raise RuntimeError(f"Required CLI executable not found in PATH: {name}")
    return Path(resolved)
